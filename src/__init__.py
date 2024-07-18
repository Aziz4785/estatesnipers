from flask import Flask, jsonify, render_template,request,send_file
from flask_cors import CORS
import json
import traceback
from flask import session,current_app
import os
from wtforms import TextAreaField, SubmitField
from wtforms.validators import DataRequired
from collections import defaultdict
from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from marshmallow import Schema, fields, ValidationError, validates, validates_schema
from marshmallow.validate import Length
from .pdfHelper import PDFHelper
import logging
from .server_utils import * 
from reportlab.lib.utils import ImageReader
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from sqlalchemy import create_engine,text
from flask_login import LoginManager
from flask_wtf import FlaskForm, CSRFProtect
from wtforms import StringField, SubmitField
from flask import redirect, url_for, flash
from flask_httpauth import HTTPBasicAuth
import psycopg2
from flask import jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from reportlab.lib.colors import blue,black
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from reportlab.lib.pagesizes import letter
from flask_login import login_required,current_user
from reportlab.pdfgen import canvas
import io
from io import BytesIO
import matplotlib.pyplot as plt
from flask_wtf.csrf import CSRFProtect
import matplotlib.backends.backend_agg as agg
from decouple import config
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import stripe

# Load environment variables from .env file
load_dotenv() #!!! COMENT THIS FOR DEPLOYMENT
#pd.set_option('display.max_rows', None) 
#pd.set_option('display.max_columns', None)
# pd.set_option('display.width', 1000)
#pd.set_option('display.max_colwidth', None)

app = Flask(__name__)
app.config.from_object(config("APP_SETTINGS"))
csrf = CSRFProtect(app)
login_manager = LoginManager() # create and init the login manager
login_manager.init_app(app) 


app.config.update(
    SESSION_COOKIE_SAMESITE='Lax',  # Or 'Strict'
    SESSION_COOKIE_SECURE=True  # Ensure cookies are only sent over HTTPS
)

bcrypt = Bcrypt(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)

limiter = Limiter(get_remote_address, app=app)#, default_limits=["3 per day"])

#with app.app_context(): 
    #This will create model classes for all tables in your database. 
    # You can then access them via db.metadata.tables['table_name'].
    #db.reflect()

# Registering blueprints
from src.accounts.views import accounts_bp
from src.core.views import core_bp
from src.accounts.forms import LoginForm ,RegisterForm
app.register_blueprint(accounts_bp)
app.register_blueprint(core_bp)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
if not app.config["SECRET_KEY"]:
    raise ValueError("No SECRET_KEY set for Flask application. Did you follow the setup instructions?")

auth = HTTPBasicAuth()
users = {
    os.environ['ADMIN_USER']: os.environ['ADMIN_PASSWORD']
}

@auth.verify_password
def verify_password(username, password):
    if username in users and users[username] == password:
        return username


from src.accounts.models import User,StripeCustomer

@login_manager.user_loader
def load_user(user_id):
    #It should take the ID of a user, and return the corresponding user object.
    return User.query.filter(User.id == int(user_id)).first()

login_manager.login_view = "accounts.login" #name of the login view
login_manager.login_message_category = "danger"

stripe_keys = {
    "secret_key": os.environ["STRIPE_SECRET_KEY"],
    "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"],
    "price_id": os.environ["STRIPE_PRICE_ID"],
    "endpoint_secret": os.environ["STRIPE_ENDPOINT_SECRET"], #Stripe will now forward events to our endpoint
}

stripe.api_key = stripe_keys["secret_key"]


# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'DubaiBelgiumAnalytics_123',
#     'database': 'sniperdb'
# }
# db_config = {
#     'host': 'localhost',
#     'dbname': 'SNIPERDB',  # 'database' in MySQL is 'dbname' in PostgreSQL
#     'user': 'postgres',
#     'password': r'DubaiAnalytics_123',
#     'port': '5432'  # Default PostgreSQL port
# }
#db_url = "postgres://uaovl716s190an:p785b9fb819ee0e2fa3fb5eaae6550ed481578e5f782c0287d2e8b5d846934059@ec2-52-7-195-158.compute-1.amazonaws.com:5432/df4dm8ak5du5r"
#db_url = "postgresql://postgres:DubaiAnalytics_123@localhost:5432/SNIPERDB"


def check_premium_user():
    if current_user.is_authenticated:
        stripe_customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()
        if stripe_customer:
            subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
            if subscription and subscription.status == "active":
                return True
    return False


@app.route('/')
@auth.login_required
def index():
    login_form = LoginForm()  # Create an instance of the LoginForm
    register_form = RegisterForm()
    
    is_premium_user = check_premium_user()
    return render_template('index.html', modal_open=False, login_form=login_form,register_form=register_form,show_modal=False,message='',form_to_show="login",is_premium_user=is_premium_user)

@app.route("/config")
def get_publishable_key():
    stripe_config = {"publicKey": stripe_keys["publishable_key"]}
    return jsonify(stripe_config)

@app.route('/check-auth')
def check_auth():
    return jsonify({
        'isAuthenticated': current_user.is_authenticated
    })

@app.route("/create-checkout-session")
def create_checkout_session():
    #for deployment use this (maybe ?): 
    domain_url = os.environ.get('DOMAIN_URL', 'https://your-app-name.herokuapp.com/')
    stripe.api_key = stripe_keys["secret_key"]

    try:
        checkout_session = stripe.checkout.Session.create(
            # you should get the user id here and pass it along as 'client_reference_id'
            #
            # this will allow you to associate the Stripe session with
            # the user saved in your database
            #
            # example: client_reference_id=user.id,
            success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=domain_url + "cancel",
            payment_method_types=["card"],
            mode="subscription",
            line_items=[
                {
                    "price": stripe_keys["price_id"],
                    "quantity": 1,
                }
            ]
        )
        return jsonify({"sessionId": checkout_session["id"]})
    except Exception as e:
        return jsonify(error=str(e)), 403
    
@app.route("/success")
def success():
    is_premium_user = check_premium_user()
    return render_template("index.html",is_premium_user=is_premium_user)


@app.route("/cancel")
def cancelled():
    return render_template("index.html")


@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    """
    There are two types of events in Stripe and programming in general. Synchronous events, 
    which have an immediate effect and results (e.g., creating a customer), and asynchronous events, 
    which don't have an immediate result (e.g., confirming payments).
      Because payment confirmation is done asynchronously, we cannot set the premium to active right after the payment is made..
      so we need to wait for stripe response , and so we will receive the stripe response on this webhook

      "One of the easiest ways to get notified when the payment goes through is to use a callback 
      or so-called Stripe webhook. We'll need to create a simple endpoint in our application, which Stripe will call whenever an event occurs (e.g., when a user subscribes). 
      By using webhooks, we can be absolutely sure that the payment went through successfully."
    """
    payload = request.get_data(as_text=True)
    sig_header = request.headers.get("Stripe-Signature")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, stripe_keys["endpoint_secret"]
        )

    except ValueError as e:
        # Invalid payload
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return "Invalid signature", 400

    # Handle the checkout.session.completed event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]

        # Fulfill the purchase...
        handle_checkout_session(session)

    return "Success", 200

@app.route("/cancel-subscription", methods=["POST"])
@login_required
def cancel_subscription():
    customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()
    
    if not customer:
        flash("No active subscription found.", "error")
        return redirect(url_for('manage_subscription'))
    
    try:
        subscription = stripe.Subscription.retrieve(customer.stripeSubscriptionId)
        stripe.Subscription.delete(customer.stripeSubscriptionId)
        
        # Update the database
        db.session.delete(customer)
        db.session.commit()
        
        flash("Your subscription has been cancelled successfully.", "success")
    except stripe.error.StripeError as e:
        flash(f"An error occurred while cancelling your subscription: {str(e)}", "error")
    
    return redirect(url_for('manage_subscription'))

def handle_checkout_session(session):
    # here you should fetch the details from the session and save the relevant information
    # to the database (e.g. associate the user with their subscription)
    # Extract relevant information from the session
    customer_email = session['customer_details']['email']
    stripe_customer_id = session['customer']
    stripe_subscription_id = session['subscription']

    # Find the user by email
    user = User.query.filter_by(email=customer_email).first()

    if user:
        # Check if the user already has a StripeCustomer record
        existing_stripe_customer = StripeCustomer.query.filter_by(user_id=user.id).first()

        if existing_stripe_customer:
            # Update existing StripeCustomer record
            existing_stripe_customer.stripeCustomerId = stripe_customer_id
            existing_stripe_customer.stripeSubscriptionId = stripe_subscription_id
        else:
            # Create new StripeCustomer record
            new_stripe_customer = StripeCustomer(
                user_id=user.id,
                stripeCustomerId=stripe_customer_id,
                stripeSubscriptionId=stripe_subscription_id
            )
            db.session.add(new_stripe_customer)

        # Commit the changes to the database
        db.session.commit()

        current_app.logger.info(f"Subscription successful for user {user.email}")
    else:
        current_app.logger.warning(f"User with email {customer_email} not found in database")


class MessageSchema(Schema):
    message = fields.Str(required=True, validate=Length(min=1, max=2000))  


@app.route('/send_message', methods=['POST'])
@limiter.limit("10 per day")
@auth.login_required
@csrf.exempt
def send_message():
    app.logger.info('Received request send_message()')
    app.logger.debug(f'the request : : {request.json}')
    data = request.json
    schema = MessageSchema()

    try:
        validated_data = schema.load(data)
    except ValidationError as err:
        app.logger.info('The message is not validated correctly)')
        return jsonify({"errors": err.messages}), 400
    message = validated_data['message']
    app.logger.debug(f'the message : : {message}')
    # Send email
    try:
        send_email(message)
        
        response = jsonify({"message": "Message sent successfully"})
        response.headers['Content-Type'] = 'application/json'
        return response, 200
    except Exception as e:
        return jsonify({"message": "Failed to send message"}), 500
    

@app.route("/manage-subscription")
@login_required
def manage_subscription():
    customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()
    
    if customer:
        subscription = stripe.Subscription.retrieve(customer.stripeSubscriptionId)
        product = stripe.Product.retrieve(subscription.plan.product)
        context = {
            "subscription": subscription,
            "product": product,
        }
        return render_template("manage_subscription.html", **context)
    
    return render_template("manage_subscription.html")


@app.template_filter('datetime')
def format_datetime(value, format='%Y-%m-%d %H:%M:%S'):
    if value is None:
        return ""
    return datetime.utcfromtimestamp(value).strftime(format)

def get_db_connection():
    #connection = mysql.connector.connect(**db_config)
    #connection = psycopg2.connect(**db_config)
    #connection = psycopg2.connect(db_url) #here we use an url
    #DATABASE_URL = db_url #local database
    DATABASE_URL = os.environ.get('HEROKU_POSTGRESQL_NAVY_URL')  # Fetch the correct environment variable
    connection = psycopg2.connect(DATABASE_URL)
    return connection


list_order_in_memory = []

@app.route('/get-area-details')
@auth.login_required
def get_area_details():
    try:
        is_premium_user = check_premium_user()

        hierarchy_keys = ['grouped_project','property_usage_en','property_sub_type_en','rooms_en']
        if is_premium_user:   
            hierarchy_keys = session.get('hierarchy_keys', ['grouped_project','property_usage_en','property_sub_type_en','rooms_en'])
        area_id = request.args.get('area_id')
        if not area_id:
            return jsonify({'error': 'Area ID is required'}), 400
        #connection_url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
        #connection_url = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
        connection_url = os.environ.get('HEROKU_POSTGRESQL_NAVY_URL')
        if connection_url.startswith("postgres://"):
           connection_url = connection_url.replace("postgres://", "postgresql://", 1)

        if not connection_url:
            return jsonify({'error': 'Database connection URL not found'}), 500

        engine = create_engine(connection_url)
        
        
        sql_query = text("""
        SELECT 
            pst.property_sub_type_en, 
            grouped_project, 
            rooms_en, 
            property_usage_en,
            instance_year,
            meter_sale_price,
            roi,
            actual_worth
        FROM 
            base_table t
        LEFT JOIN
            propertysubtype pst 
        ON 
            t.property_sub_type_id = pst.property_sub_type_id
        WHERE area_id = :area_id AND instance_year >= 2013;
        """)

        with engine.connect() as connection:
            df = pd.read_sql_query(sql_query, connection, params={"area_id": area_id})

        #print("SQL Query Execution Time: {:.2f} seconds".format(time.time() - start_time))
        prediction_query = text("""SELECT
                        pst.property_sub_type_en, 
                        proj.project_name_en AS grouped_project, 
                        rooms_en, 
                        property_usage_en,
                        instance_year,
                        SUM(avg_price * total_rows) / SUM(total_rows) AS meter_sale_price,
                        SUM(total_rows) AS total_rows
                    FROM
                        predictions
                    LEFT JOIN
                        propertysubtype pst 
                    ON 
                        predictions.property_sub_type_id = pst.property_sub_type_id
                    LEFT JOIN
                        projects proj
                    ON
                        predictions.project_number = proj.project_number
                    WHERE
                        predictions.area_id = :area_id
                    GROUP BY
                        pst.property_sub_type_en,proj.project_name_en, rooms_en, property_usage_en,instance_year;""")
        
        with engine.connect() as connection:
            df_prediction = pd.read_sql_query(prediction_query, connection, params={"area_id": area_id})

        df_prediction_filtered = df_prediction[df_prediction['instance_year'] == 2024]
        df_2024 = df[df['instance_year'] == 2024].copy()
        df_2024['total_rows'] = 1
        df_combined_2024 = pd.concat([df_2024, df_prediction_filtered], ignore_index=True)

        nested_dicts = {}
        groupings = create_groupings(hierarchy_keys)
        
        for group_index,group in enumerate(groupings):
            # # Apply the custom aggregation function for each year of interest
            avg_meter_prices = {}
            for year in range(2013, 2024):
                avg_meter_prices[f'AVG_meter_price_{year}'] = conditional_avg(df, group, year).rename(f'AVG_meter_price_{year}')
            avg_meter_prices[f'AVG_meter_price_2024'] = weighted_avg(df_combined_2024, group, 2024).rename(f'AVG_meter_price_2024')

            for year in range(2025, 2030):
                avg_meter_prices[f'AVG_meter_price_{year}'] = weighted_avg(df_prediction, group, year).rename(f'AVG_meter_price_{year}')
            
            avg_roi = df[df['instance_year'] == 2023].groupby(group)['roi'].mean().rename('avg_roi')
            avg_transaction_value = df[df['instance_year'] >= 2023].groupby(group)['actual_worth'].mean().rename('avg_actual_worth')
            
            final_df = pd.concat([*avg_meter_prices.values(), avg_roi,avg_transaction_value], axis=1).reset_index()

            #concat the columns into an array : 
            final_df['avg_meter_price_2013_2023'] = final_df.apply(lambda row: [replace_nan_with_none(row[col]) for col in avg_meter_prices.keys()], axis=1)

            #print("Grouping {} Execution Time: {:.2f} seconds".format(group_index, time.time() - grouping_start_time))
            #avergae capital apperication calculation for that group:

            final_df['avgCapitalAppreciation2018'] = final_df.apply(lambda row: calculate_CA(row, 5), axis=1)
            final_df['avgCapitalAppreciation2013'] = final_df.apply(lambda row: calculate_CA(row, 10), axis=1)

            columns_containing_means = [col for col in final_df.columns if col.startswith('avg')]
            # Combine the columns : columns of the group + avg_cap_appreciation_columns
            combined_columns = group + list(set(columns_containing_means) - set(group))
            # Reorder and filter the DataFrame according to the combined list of columns
            final_df = final_df[combined_columns]
            # Drop rows where 'avgCapitalAppreciation2018' and 'avgCapitalAppreciation2013' and roi are all NaN

            final_df.dropna(subset=['avgCapitalAppreciation2018', 'avgCapitalAppreciation2013','avg_roi','avg_actual_worth'], how='all', inplace=True)

            final_df['avg_meter_price_2013_2023'] = final_df['avg_meter_price_2013_2023'].apply(interpolate_price_list)

            if 'grouped_project' in df.columns: # we drop empty proejct because we dont want to see blank projects in the ui
                final_df = final_df.dropna(subset=['grouped_project'])

            update_nested_dict(final_df, nested_dicts, group)

        is_premium_user = False 
        if current_user.is_authenticated:
            #Query the StripeCustomer table to check subscription status
            stripe_customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()

            if stripe_customer:
                # Fetch the subscription details from Stripe
                subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
                if subscription and subscription.status == "active":
                    is_premium_user = True

        if(nested_dicts):
            fetched_rows= remove_lonely_dash(nested_dicts)

            if(not is_premium_user):
                # Get the first two (key, value) pairs
                first_two_pairs = list(fetched_rows.items())[:2]
                # Initialize the new dictionary with the first two pairs
                new_dict = dict(first_two_pairs)
                # Replace all other keys with "locked project X:" and value 99
                count = 1
                while count<7:
                    new_key = f"locked project {count}:"
                    new_dict[new_key] = 99
                    count += 1
                fetched_rows = new_dict

            json_response = jsonify(fetched_rows)
            return json_response
        else:
            return jsonify({'message': 'No data found'}), 404
    except Exception as e:
        app.logger.error(f'An unexpected error occurred: {str(e)}')
        return jsonify({'error': 'An error occurred', 'message': str(e)}), 500
    finally:
        # Always ensure the connection is closed even if an error occurs
        if 'engine' in locals():
            engine.dispose()


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('q', '')
    if not query:
        return jsonify({'error': 'Search query is required'}), 400
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        # Search for projects
        cur.execute("""
            SELECT a.area_id, p.project_name_en, a.area_name_en
            FROM projects p
            JOIN areas a ON p.area_id = a.area_id
            WHERE p.project_name_en ILIKE %s
            LIMIT 6
        """, (f'%{query}%',))
        projects = cur.fetchall()
        
        # Search for areas
        cur.execute("""
            SELECT area_id, area_name_en
            FROM areas
            WHERE area_name_en ILIKE %s
            LIMIT 6
        """, (f'%{query}%',))
        areas = cur.fetchall()
        
        cur.close()
        conn.close()
        
        results = [
            {'type': 'project', 'id': p[0], 'name': f"{p[1]} ({p[2]})"} for p in projects
        ] + [
            {'type': 'area', 'id': a[0], 'name': a[1]} for a in areas
        ]
        
        return jsonify(results), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

    finally:
        cur.close()
        conn.close()

def execute_DATE_PRICE_pairs_query(area_id, project=None, Usage=None, subtype=None, rooms=None):
    connection = get_db_connection()
    cursor = connection.cursor(cursor_factory=RealDictCursor)  # postgresql

    base_query = """
       SELECT instance_date, meter_sale_price
       FROM transactions t
       WHERE t.area_id = %s AND t.instance_year >= 2013
    """
    
    conditions = []
    params = [area_id]

    if Usage is not None:
        conditions.append("t.property_usage_en = %s")
        params.append(Usage)
    if subtype is not None:
        conditions.append("t.property_sub_type_en = %s")
        params.append(subtype)
    if rooms is not None:
        conditions.append("t.rooms_en = %s")
        params.append(rooms)
    if project is not None:
        conditions.append("t.grouped_project = %s")
        params.append(project)

    if conditions:
        query = base_query + " AND " + " AND ".join(conditions)
    else:
        query = base_query

    cursor.execute(query, tuple(params))
    
    # Fetch and format the results
    fetched_rows = cursor.fetchall()
    return fetched_rows

def execute_project_demand_query(area_id):
    connection = get_db_connection()
    #cursor = connection.cursor(dictionary=True) mysql
    cursor = connection.cursor(cursor_factory=RealDictCursor) #postgresql
    
    query = """
       SELECT 
    MAX(p.project_name_en) AS project_name_en,
    SUM(CASE WHEN t.instance_year = 2023 THEN t.total ELSE 0 END)::float / p.no_of_units AS internaldemand2023,
    (SUM(CASE WHEN t.instance_year = 2023 THEN t.total ELSE 0 END)::float / (SELECT COUNT(*) FROM transactions_per_year WHERE instance_year = 2023)) AS externaldemand2023,
    (SUM(CASE WHEN t.instance_year = 2022 THEN t.total ELSE 0 END)::float / (SELECT COUNT(*) FROM transactions_per_year WHERE instance_year = 2022))  AS externalDemand2022,
    (SUM(CASE WHEN t.instance_year = 2021 THEN t.total ELSE 0 END)::float / (SELECT COUNT(*) FROM transactions_per_year WHERE instance_year = 2021))  AS externalDemand2021,
    (SUM(CASE WHEN t.instance_year = 2020 THEN t.total ELSE 0 END)::float / (SELECT COUNT(*) FROM transactions_per_year WHERE instance_year = 2020))  AS externalDemand2020,
    (SUM(CASE WHEN t.instance_year = 2019 THEN t.total ELSE 0 END)::float / (SELECT COUNT(*) FROM transactions_per_year WHERE instance_year = 2019))  AS externalDemand2019,
    (SUM(CASE WHEN t.instance_year = 2018 THEN t.total ELSE 0 END)::float / (SELECT COUNT(*) FROM transactions_per_year WHERE instance_year = 2018))  AS externalDemand2018
FROM 
    transactions_per_year t
JOIN 
    projects p ON t.project_number = p.project_number
WHERE 
    t.area_id = %s
    AND p.no_of_units > 80
GROUP BY 
    t.project_number, p.no_of_units, p.project_name_en;
    """
    try:
        cursor.execute(query, (area_id,))
        
        # Fetch and format the results
        fetched_rows = cursor.fetchall()
        fetched_rows = group_external_demand_in_array(fetched_rows)
        return fetched_rows
    except Exception as e:
        # Log the error securely
        print(f"An error occurred: {str(e)}")  # Replace with proper logging
        return None  # Or handle the error appropriately
    finally:
        cursor.close()
        connection.close()

@app.route('/get-demand-per-project')
@auth.login_required
def get_demand_per_project():
    area_id = request.args.get('area_id')
    fetched_rows = execute_project_demand_query(area_id)
    fetched_rows_json = jsonify(fetched_rows)
    return fetched_rows_json

def execute_land_query(area_id):
    connection = get_db_connection()
    #cursor = connection.cursor(dictionary=True) mysql
    cursor = connection.cursor(cursor_factory=RealDictCursor) #postgresql

    query = """
    SELECT land_type_en, COUNT(*) AS count
    FROM lands
    WHERE area_id = %s
    GROUP BY land_type_en;
    """
    cursor.execute(query, (area_id,))
    
    # Fetch and format the results
    fetched_rows = cursor.fetchall()
    return fetched_rows

@app.route('/get-lands-stats')
@auth.login_required
def get_lands_stats():
    area_id = request.args.get('area_id')
    fetched_rows = execute_land_query(area_id)
    fetched_rows_json = jsonify(fetched_rows)
    return fetched_rows_json

@app.route('/save-list-order', methods=['POST'])
@auth.login_required
def save_list_order():
    # todo
    global list_order_in_memory  # Reference the global variable
    data = request.json
    list_order_in_memory = data.get('listOrder', [])
    session['hierarchy_keys'] = map_text_to_field(list_order_in_memory)

    return jsonify({'message': 'List order saved successfully!'})


@app.route('/get-list-order', methods=['GET'])
@auth.login_required
def get_list_order():
    hierarchy_keys = session.get('hierarchy_keys', ['grouped_project','property_usage_en','property_sub_type_en','rooms_en'])
    return jsonify({'listOrder': key_to_id(hierarchy_keys)})

    
@app.route('/dubai-areas')
@auth.login_required
def dubai_areas():
    try:
        app.logger.info('we call dubai areas')
        is_premium_user = False 
        if current_user.is_authenticated:
            #Query the StripeCustomer table to check subscription status
            stripe_customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()

            if stripe_customer:
                # Fetch the subscription details from Stripe
                subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
                if subscription and subscription.status == "active":
                    is_premium_user = True

        connection = get_db_connection()
        #cursor = connection.cursor(dictionary=True) mysql
        cursor = connection.cursor(cursor_factory=RealDictCursor) #postgresql
        cursor.execute('SELECT area_id, average_sale_price, avg_ca_5, avg_ca_10, avg_roi, supply_finished_pro, supply_offplan_pro, supply_lands, aquisitiondemand_2023,rentaldemand_2023 FROM areas')
        fetched_rows = cursor.fetchall() 

        # Data processing functions for each key
        # Each function is responsible for converting the row entry to the desired type
        process_funcs = {
            'average_sale_price': float,
            'avg_ca_5': float,
            'avg_ca_10': float,  
            'avg_roi': float,
            'supply_finished_pro': int,
            'supply_offplan_pro': int,
            'supply_lands': int,
            'aquisitiondemand_2023' : float,
            'rentaldemand_2023' : float
        }

        # Data storage dictionaries, keyed by type
        data_stores = {
            'average_sale_price': {},
            'avg_ca_5': {},
            'avg_ca_10': {},
            'avg_roi': {},
            'supply_finished_pro': {},
            'supply_offplan_pro': {},
            'supply_lands': {},
            'aquisitiondemand_2023' : {},
            'rentaldemand_2023' : {}
        }

        # Process all rows in one loop
        for row in fetched_rows:
            area_id = row['area_id']
            for column, changetype in process_funcs.items():
                if row.get(column) is not None:  # Use .get to avoid KeyError if key doesn't exist
                    data_stores[column][area_id] = changetype(row[column])

        valid_prices = [price for price in data_stores['average_sale_price'].values() if price is not None]
        valid_CA = [ca for ca in data_stores['avg_ca_5'].values() if ca is not None]
        valid_roi = [ro for ro in data_stores['avg_roi'].values() if ro is not None]
        valid_aquDemand = [aqd for aqd in data_stores['aquisitiondemand_2023'].values() if aqd is not None]
        valid_rentDemand = [rd for rd in data_stores['rentaldemand_2023'].values() if rd is not None]
        min_price, med_price, max_price = get_min_median_max(valid_prices)
        min_ca, med_ca, max_ca = get_min_median_max(valid_CA)
        min_roi, med_roi, max_roi = get_min_median_max(valid_roi)
        min_aqDemand,med_aqDemand, max_asDemand = get_min_median_max(valid_aquDemand)
        min_rentDemand,med_rentDemand, max_rentDemand = get_min_median_max(valid_rentDemand)

        legends = {
            "averageSalePrice": [round((med_price+min_price)/2), round(med_price), round(med_price+(max_price-med_price)/2.0)],
            "avgCA_5Y": [round((min_ca+med_ca)*100/2), round(med_ca*100), round((med_ca+(max_ca-med_ca)/2.0)*100)],
            "avg_roi": [custom_round((min_roi+med_roi)*100/2), custom_round(med_roi*100), custom_round((med_roi+(max_roi-med_roi)/2.0)*100)],
            "aquisitiondemand_2023" : [
                custom_round((med_aqDemand+min_aqDemand)*100/2) if med_aqDemand is not None else 0,
                custom_round(med_aqDemand*100) if med_aqDemand is not None else 0,
                custom_round((med_aqDemand+(max_asDemand-med_aqDemand)/2.0)*100) if med_aqDemand is not None else 0
            ]
        }

        units = {
            "averageSalePrice": "AED",
            "avgCA_5Y": "%",
            "avg_roi": "%",
            "aquisitiondemand_2023" : "%"
        }
        
        # Load the GeoJSON file
        with open('areas_coordinates/dubaiAreas.geojson', 'r') as file:
            geojson = json.load(file)
    
        # Here is the order :
        # average_sale_price
        # avg_ca_5
        # avgCA_10Y
        # avg_roi
        # supply_finished_pro
        # supply_offplan_pro
        # supply_lands
        # aquisitiondemand_2023
        # rentaldemand_2023

        # Enrich GeoJSON with price data and calculate fill colors
        for feature in geojson:
            area_id = int(feature['area_id'])
            variable_names = []
            variable_values = []
            variables_units = []
            variables_special = []  #(variables that have speical info-card) 0 for no special, 1 for projects, 2 for lands

            variable_names.append("Avg. Meter Sale Price:")
            if area_id in data_stores['average_sale_price']:
                price = data_stores['average_sale_price'][area_id]
                variable_values.append(price)   
                feature['fillColorPrice'] = get_color(price, min_price, med_price, max_price)
            else:
                variable_values.append(None)
                feature['fillColorPrice'] = 'rgb(95,95,95)'  # grey
            variables_units.append('AED')
            variables_special.append(0)

            # Process avg_ca_5
            variable_names.append("Avg. Capital Appr. 5Y:")
            if area_id in data_stores['avg_ca_5']:
                ca = data_stores['avg_ca_5'][area_id]
                variable_values.append(ca)
                feature['fillColorCA5'] = get_color(ca, min_ca, med_ca, max_ca)
            else:
                variable_values.append(None)
                feature['fillColorCA5'] = 'rgb(95,95,95)'  # grey
            variables_units.append('%')
            variables_special.append(0)

            # Process avg_ca_10
            variable_names.append("Avg. Capital Appr. 10Y:")
            if area_id in data_stores['avg_ca_10']:
                variable_values.append(data_stores['avg_ca_10'][area_id])
            else:
                variable_values.append(None)
            variables_units.append('%')
            variables_special.append(0)

            # Process avg_roi
            variable_names.append("Avg. Gross Rental Yield:")
            if area_id in data_stores['avg_roi']:
                
                roi = data_stores['avg_roi'][area_id]
                variable_values.append(roi)
                feature['fillColorRoi'] = get_color(roi, min_roi, med_roi, max_roi)
            else:
                variable_values.append(None)
                feature['fillColorRoi'] = 'rgb(95,95,95)'
            variables_units.append('%')
            variables_special.append(0)

            if is_premium_user:
                # Process supply_finished_pro
                variable_names.append("supply_finished_pro")
                if area_id in data_stores['supply_finished_pro']:
                    variable_values.append(data_stores['supply_finished_pro'][area_id])
                else:
                    variable_values.append(None)
                variables_units.append('-')
                variables_special.append(1)

                # Process supply_offplan_pro
                variable_names.append("supply_offplan_pro")
                if area_id in data_stores['supply_offplan_pro']:
                    variable_values.append(data_stores['supply_offplan_pro'][area_id])
                else:
                    variable_values.append(None)
                variables_units.append('-')
                variables_special.append(1)

                # Process supply_lands
                variable_names.append("supply_lands")
                if area_id in data_stores['supply_lands']:
                    variable_values.append(data_stores['supply_lands'][area_id])
                else:
                    variable_values.append(None)
                variables_units.append('-')
                variables_special.append(2)

                # Process aquisitiondemand_2023
                variable_names.append("Acquisition Demand 2023:")
                if area_id in data_stores['aquisitiondemand_2023']:
                    ademand = data_stores['aquisitiondemand_2023'][area_id]
                    variable_values.append(ademand)
                    feature['fillColorAquDemand'] = get_color(ademand, min_aqDemand, med_aqDemand, max_asDemand)
                else:
                    variable_values.append(None)
                    feature['fillColorAquDemand'] = 'rgb(95,95,95)'
                variables_units.append('%')
                variables_special.append(0)

                # Process rentaldemand_2023
                variable_names.append("Rental Demand 2023:")
                if area_id in data_stores['rentaldemand_2023']:
                    rdemand = data_stores['rentaldemand_2023'][area_id]
                    variable_values.append(rdemand)
                    feature['fillColorrentDemand'] = get_color(rdemand, min_rentDemand, med_rentDemand, max_rentDemand)
                else:
                    variable_values.append(None)
                    feature['fillColorrentDemand'] = 'rgb(95,95,95)'
                variables_units.append('%')
                variables_special.append(0)

            feature["variableNames"] = variable_names
            feature["variableValues"] = variable_values
            feature["variableUnits"] = variables_units
            feature["variableSpecial"] = variables_special

        cursor.close()
        connection.close()

        return jsonify([legends, geojson, units])
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': 'An error occurred', 'message': str(e)}), 500
    
def create_land_type_pie_chart(data):
    # Extract land types and counts
    land_types = [row['land_type_en'] if row['land_type_en'] else 'Unknown' for row in data]
    counts = [row['count'] for row in data]
    
    # Calculate percentages
    total = sum(counts)
    percentages = [(count / total) * 100 for count in counts]
    
    # Create the pie chart
    fig, ax = plt.subplots(figsize=(10, 6))  # Increased figure size to accommodate legend
    
    wedges, _, _ = ax.pie(counts, startangle=90, autopct='')
    
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    ax.set_title('Land Type Distribution')
    
    # Create legend labels with percentages and counts
    legend_labels = [f'{land_type} - {percentage:.1f}% ({count})' 
                     for land_type, percentage, count in zip(land_types, percentages, counts)]
    
    # Add a legend
    ax.legend(wedges, legend_labels,
              title="Land Types",
              loc="center left",
              bbox_to_anchor=(1, 0, 0.5, 1))
    
    # Adjust the layout to prevent the legend from being cut off
    plt.tight_layout()
    
    # Save the chart to a buffer
    img_buffer = io.BytesIO()
    FigureCanvas(fig).print_png(img_buffer)
    img_buffer.seek(0)
    plt.close(fig)  # Close the figure to free up memory
    
    return img_buffer

def create_land_type_donut_chart(data):
    # Extract land types and counts
    land_types = [row['land_type_en'] if row['land_type_en'] else 'Unknown' for row in data]
    counts = [row['count'] for row in data]

    # Create the donut chart
    fig, ax = plt.subplots(figsize=(12, 8))
    
    # Colors for the chart
    colors = plt.cm.Set3(np.linspace(0, 1, len(land_types)))
    
    # Create donut chart
    wedges, texts, autotexts = ax.pie(counts, autopct='%1.1f%%', pctdistance=0.85,
                                      wedgeprops=dict(width=0.5), startangle=-40, colors=colors)
    
    # Equal aspect ratio ensures that pie is drawn as a circle
    ax.axis('equal')
    
    # Set title
    plt.title('Land Type Distribution', fontsize=16, pad=20)

    # Add legend
    legend_labels = [f'{lt} ({count})' for lt, count in zip(land_types, counts)]
    ax.legend(wedges, legend_labels, title="Land Types", loc="center left", bbox_to_anchor=(1, 0, 0.5, 1))

    # Adjust layout
    plt.tight_layout()

    # Save the chart to a buffer
    img_buffer = io.BytesIO()
    FigureCanvas(fig).print_png(img_buffer)
    img_buffer.seek(0)
    plt.close(fig)  # Close the figure to free up memory

    return img_buffer

def create_price_chart(avg_meter_price,start_year=2013,title ='Average Meter Sale Price 2013-2023',y_axis='Average Meter Price',contain_pred=True):
    years = list(range(start_year, start_year + len(avg_meter_price)))
    
    fig, ax = plt.subplots()
    
    if contain_pred:
        # Plot the first part of the line with blue
        ax.plot(years[:-5], avg_meter_price[:-5], color='blue', marker='o')
        # Plot the last 6 lines and 5 points with red
        ax.plot(years[-6:], avg_meter_price[-6:], color='red', marker='o')
    else:
        ax.plot(years, avg_meter_price, color='blue', marker='o')
    
    ax.set_title(title)
    ax.set_xlabel('Year')
    ax.set_ylabel(y_axis)
    ax.grid(True)

    img_buffer = io.BytesIO()
    FigureCanvas(fig).print_png(img_buffer)
    img_buffer.seek(0)

    plt.close(fig)  # Close the figure to free up memory

    return img_buffer

def create_histogram(data):
    # Convert data to DataFrame
    df = pd.DataFrame(data)
    
    # Ensure the instance_date column is in datetime format
    df['instance_date'] = pd.to_datetime(df['instance_date'])
    
    # Extract the year from the instance_date
    df['year'] = df['instance_date'].dt.year
    
    # Plotting
    plt.figure(figsize=(14, 7))
    fig, ax = plt.subplots()
    df['year'].value_counts().sort_index().plot(kind='bar', ax=ax, color='skyblue')
    plt.title('Number of Transactions per Year')
    plt.xlabel('Year')
    plt.ylabel('Number of Transactions')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()

    img_buffer = io.BytesIO()
    FigureCanvas(fig).print_png(img_buffer)
    img_buffer.seek(0)

    plt.close(fig)  # Close the figure to free up memory

    return img_buffer

def create_scatterplot(data):
    # Convert data to DataFrame
    df = pd.DataFrame(data)

    # Plotting
    plt.figure(figsize=(14, 7))
    fig, ax = plt.subplots()
    plt.scatter(df['instance_date'], df['meter_sale_price'], alpha=0.6)
    plt.title('Meter Sale Price Over Time')
    plt.xlabel('Instance Date')
    plt.ylabel('Meter Sale Price')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()

    img_buffer = io.BytesIO()
    FigureCanvas(fig).print_png(img_buffer)
    img_buffer.seek(0)

    plt.close(fig)  # Close the figure to free up memory

    return img_buffer

@app.route('/generate-pdf', methods=['POST'])
@csrf.exempt
@auth.login_required
def generate_pdf():
    try:
        app.logger.info('Received request for PDF generation')
        is_premium_user = False
        payload_size = request.content_length
        app.logger.info(f"Received payload size: {payload_size} bytes")
    
        if current_user.is_authenticated:
            app.logger.debug(f'User authenticated: {current_user.id}')
            # Query the StripeCustomer table to check subscription status
            stripe_customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()

            if stripe_customer:
                app.logger.debug(f'Stripe customer found: {stripe_customer.id}')
                try:
                    subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
                    app.logger.debug(f'Subscription status: {subscription.status}')
                    if subscription and subscription.status == "active":
                        is_premium_user = True
                except Exception as e:
                    app.logger.error(f'Error retrieving Stripe subscription: {str(e)}')
                    return jsonify({"error": "error"}), 404

        if not is_premium_user:
            app.logger.warning('Non-premium user attempted to generate PDF')
            response = jsonify({"error": "Premium subscription required"})
            response.status_code = 403
            app.logger.info('Sending 403 response')
            return response
        
        hierarchy_keys = ['grouped_project','property_usage_en','property_sub_type_en','rooms_en']
        if is_premium_user:   
            hierarchy_keys = session.get('hierarchy_keys', ['grouped_project','property_usage_en','property_sub_type_en','rooms_en'])
            
        request_data = request.get_json()
        section = request_data['section']
        data = request_data['data']

        area_data = request_data['area_data']

        means_data = request_data['data'].get('means', [{}])[0]
        avg_capital_appreciation_2013 = means_data.get('avgCapitalAppreciation2013', 'N/A')
        avg_capital_appreciation_2018 = means_data.get('avgCapitalAppreciation2018', 'N/A')
        avg_roi = means_data.get('avg_roi', 'N/A')
        avg_meter_price = means_data.get('avg_meter_price_2013_2023', [])
        project_demand_data = execute_project_demand_query(area_data['area_id'])
        firstkeys = list(data.keys())
        dateprice_paires = execute_DATE_PRICE_pairs_query(area_data['area_id'], project=section)

        # Loop through the project_demand_data to find the matching project
        project_internaldemand2023 = project_externaldemand2023 = None
        externalDemand_5Y = []
        for item in project_demand_data:
            if item['project_name_en'] == section:
                project_internaldemand2023 = item['internaldemand2023']
                project_externaldemand2023 = item['externaldemand2023']
                externalDemand_5Y = item['externalDemandYears']
                break

    except Exception as e:
        app.logger.error(f'Error in generate_pdf: {str(e)}', exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    # Create a PDF
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)

    helper = PDFHelper(p, 720, 750, 100)

    helper.draw_Main_title(section,font_size=30)
    # Print means data
    # Data for the table
    general_means=[]
    footnotes=[]
    if hierarchy_keys[0]=="grouped_project":
        general_means = [
            ["Description", "Value"],
            ["Average Capital Appreciation 10Y:", str(round_and_percentage(avg_capital_appreciation_2013,2))+" %"],
            ["Average Capital Appreciation 5Y:",  str(round_and_percentage(avg_capital_appreciation_2018,2))+" %"],
            ["Average Gross Rental Yield:",str(round_and_percentage(avg_roi,2))+" %"],
            ["Internal Demand¹:",str(round_and_percentage(project_internaldemand2023,2))+" %"],
            ["External Demand²:",str(round_and_percentage(project_externaldemand2023,2))+" %"]
        ]
        footnotes = [
        "¹: (Number of transaction in the project in year 2023) / (Number of units in the project) * 100",
        "²: (Number of transaction in the project in year 2023) /(Total number of transactions in 2023) * 100"
        ]
    else :
         general_means = [
            ["Description", "Value"],
            ["Average Capital Appreciation 10Y:", str(round_and_percentage(avg_capital_appreciation_2013,2))+" %"],
            ["Average Capital Appreciation 5Y:",  str(round_and_percentage(avg_capital_appreciation_2018,2))+" %"],
            ["Average Gross Rental Yield:",str(round_and_percentage(avg_roi,2))+" %"]
        ]
    # Draw the table
    helper.draw_table(general_means)
    

    # Draw the footnotes
    helper.draw_footnotes(footnotes)
    
    img_buffer = create_price_chart(avg_meter_price)
    # Insert the image into the PDF from the BytesIO object
    helper.y=350
    p.drawImage(ImageReader(img_buffer), 35, helper.y, width=270, height=200)
    # Update y position after the image
    #helper.y -= 160
    if hierarchy_keys[0]=="grouped_project":
        img_buffer_demand = create_price_chart(externalDemand_5Y,start_year=2018,title ='Evolution of Demand 2018-2023',y_axis='External Demand',contain_pred=False)
        p.drawImage(ImageReader(img_buffer_demand), 332, helper.y, width=270, height=200)

    img_buffer_scatter = create_scatterplot(dateprice_paires)
    helper.y-=220
    p.drawImage(ImageReader(img_buffer_scatter), 35, helper.y, width=270, height=200)

    img_buffer_historgram = create_histogram(dateprice_paires)
    p.drawImage(ImageReader(img_buffer_historgram), 332, helper.y, width=270, height=200)

    for k in firstkeys:
        if k !="means":
            parent_name = section
            render_pdf({k: data[k]},parent_name,helper,p)

    helper.new_page()

    #AREA SECTION 
    # Set the font and size for the title
    p.setFont("Helvetica-Bold", 24)
    p.setFillColor(blue)
    area_name = area_data["name"]
    title = f"Area : {area_name}"
    title_width = p.stringWidth(title, "Helvetica-Bold", 24)
    page_width = letter[0]
    title_x = (page_width - title_width) / 2

    # Draw the title
    #p.drawString(title_x, 750, title)
    helper.draw_Main_title(title,font_size=30)
    # Move to next line for the table
    p.setFont("Helvetica", 12)
    p.setFillColor(colors.black)

    # Data for the table
    table_data = [
        ['Metric', 'Value'],
        ['Acquisition Demand 2023', f"{round_and_percentage(area_data['variableValues'][7])} %"],
        ['Rental Demand 2023¹', str(round_and_percentage(area_data['variableValues'][8]))+" %"],
        ['Average Sale Price', f"{area_data['variableValues'][0]:,.2f} AED"],
        ['Average Capital Appreciation 10Y', str(round_and_percentage(area_data['variableValues'][2]))+" %"],
        ['Average Capital Appreciation 5Y', str(round_and_percentage(area_data['variableValues'][1]))+" %"],
        ['Average Gross Rental Yield', str(round_and_percentage(area_data['variableValues'][3],2))+" %"],
        ['Supply of Finished Projects', area_data['variableValues'][4]],
        ['Supply of Off-Plan Projects', area_data['variableValues'][5]],
        ['Supply of Lands', area_data['variableValues'][6]],
    ]
    footnotes = [
        "¹: (Number of rental contracts in year 2023) / (Number of units in the area) * 100"]
    # Create a table
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    # Build the table on canvas
    table.wrapOn(p, 175, 500)
    table.drawOn(p, 175, 500)
    helper.draw_footnotes(footnotes)
    helper.y -= 100
    land_data=execute_land_query(area_data['area_id'])
    img_buffer = create_land_type_pie_chart(land_data)
    p.drawImage(ImageReader(img_buffer), 50, 180, width=500, height=300)
    helper.new_page()
    helper.draw_contact_info()
    #p.showPage()
    p.save()

    buffer.seek(0)
    
    return send_file(buffer, as_attachment=True, download_name=f"{section}_report.pdf", mimetype='application/pdf')

def render_pdf(node,parent_name,helper,p):
    helper.new_page()
    key, data = next(iter(node.items()))
    node_name = str(key)+" / "+parent_name
    helper.draw_Main_title(node_name,font_size=26)
    means_data2 = data.get('means', [{}])[0]
    avg_capital_appreciation_2013 = means_data2.get('avgCapitalAppreciation2013', 'N/A')
    avg_capital_appreciation_2018 = means_data2.get('avgCapitalAppreciation2018', 'N/A')
    avg_roi = means_data2.get('avg_roi', 'N/A')
    avg_meter_price = means_data2.get('avg_meter_price_2013_2023', [])
    # helper.draw_info_line("Average Capital Appreciation 10Y:", round(avg_capital_appreciation_2013 * 100, 2)if avg_capital_appreciation_2013 is not None else None)
    # helper.draw_info_line("Average Capital Appreciation 5Y :", round(avg_capital_appreciation_2018 * 100, 2)if avg_capital_appreciation_2018 is not None else None)
    # helper.draw_info_line("Average ROI:", round(avg_roi * 100,2)if avg_roi is not None else None, extra_space=20)
    general_means = [
        ["Description", "Value"],
        ["Average Capital Appreciation 10Y:", str(round_and_percentage(avg_capital_appreciation_2013,2))+" %"],
        ["Average Capital Appreciation 5Y:",  str(round_and_percentage(avg_capital_appreciation_2018,2))+" %"],
        ["Average Gross Rental Yield:",str(round_and_percentage(avg_roi,2))+" %"]
    ]
    helper.draw_table(general_means)
    img_buffer = create_price_chart(avg_meter_price)
    helper.y =260
    p.drawImage(ImageReader(img_buffer), 95, helper.y, width=400, height=300)
    # Update y position after the image
    helper.y -= 200
    firstkeys = list(data.keys())
    for key in firstkeys:
        if key !="means":
            render_pdf({key: data[key]},node_name,helper,p)

if __name__ != '__main__':
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)

if __name__ == '__main__':
    app.run(debug=True)
