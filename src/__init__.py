from flask import Flask, jsonify, render_template,request,send_file
from flask_cors import CORS
import json
import traceback
from flask import session,current_app
import os
from smtplib import SMTPException, SMTPServerDisconnected, SMTPAuthenticationError
from flask_assets import Bundle, Environment
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
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask_wtf.csrf import CSRFProtect
import matplotlib.backends.backend_agg as agg
from decouple import config
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import stripe
from flask_mailman import Mail

# Load environment variables from .env file
#load_dotenv() #!!! COMENT THIS FOR DEPLOYMENT
#pd.set_option('display.max_rows', None) 
#pd.set_option('display.max_columns', None)
# pd.set_option('display.width', 1000)
#pd.set_option('display.max_colwidth', None)

app = Flask(__name__)
app.config.from_object(config("APP_SETTINGS"))
csrf = CSRFProtect(app)
login_manager = LoginManager() # create and init the login manager
login_manager.init_app(app) 


js = Bundle('app.js','contact.js','functions.js','premium_modal.js','settings.js','stripe-handlers.js',output='gen/bundle.js')

assets = Environment(app)
assets.register('bundle__js',js)

def versioned_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path, endpoint, filename)
            values['v'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

app.jinja_env.globals['url_for'] = versioned_url_for

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

app.config.update(
    SESSION_COOKIE_SAMESITE='Lax', 
    SESSION_COOKIE_SECURE=True  # Ensure cookies are only sent over HTTPS
)
@app.after_request
def add_header(response):
    response.cache_control.no_store = True
    return response

bcrypt = Bcrypt(app)
test_global_var = None
dubai_areas_data = None

db = SQLAlchemy(app)
migrate = Migrate(app, db)
CORS(app)
limiter = Limiter(get_remote_address, app=app)#, default_limits=["3 per day"])

# Registering blueprints
from src.accounts.views import accounts_bp
from src.core.views import core_bp
from src.accounts.forms import LoginForm ,RegisterForm,ResetPasswordRequestForm,ResetPasswordForm
app.register_blueprint(accounts_bp)
app.register_blueprint(core_bp)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
if not app.config["SECRET_KEY"]:
    raise ValueError("No SECRET_KEY set for Flask application. Did you follow the setup instructions?")

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
    "price_promo_id": os.environ["STRIPE_PRICE_ID_PROMO"],
}

stripe.api_key = stripe_keys["secret_key"]


def get_dubai_areas_data():
    global dubai_areas_data
    return dubai_areas_data

def check_premium_user():
    if current_user.is_authenticated:
        stripe_customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()
        if stripe_customer:
            subscription = stripe.Subscription.retrieve(stripe_customer.stripeSubscriptionId)
            if subscription:
                # Check if the subscription is active or scheduled to cancel at the end of the period
                if subscription.status == "active" or (subscription.cancel_at_period_end and subscription.status == "canceled"):
                    return True
    return False


@app.route('/')
def index():
    login_form = LoginForm()  # Create an instance of the LoginForm
    register_form = RegisterForm()
    
    is_premium_user = check_premium_user()
    show_modal = request.args.get('show_modal', 'False') == 'True'
    last_billing_period = False
    if current_user.is_authenticated:
        stripe_customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()
        if(stripe_customer):
            last_billing_period = stripe_customer.cancel_at_period_end

    current_app.config['dubai_areas_data'] = fetch_dubai_areas_data()

    return render_template('index.html', dubai_areas_data= current_app.config['dubai_areas_data'],modal_open=False, login_form=login_form,register_form=register_form,show_modal=show_modal,message='',form_to_show="login",is_premium_user=is_premium_user,last_billing_period=last_billing_period)

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
    domain_url = os.environ.get('DOMAIN_URL', 'https://www.platformestatesnipers.com/')
    #domain_url = "http://localhost:5000/"
    stripe.api_key = stripe_keys["secret_key"]

    try:
        checkout_session = stripe.checkout.Session.create(
            # you should get the user id here and pass it along as 'client_reference_id'
            #
            # this will allow you to associate the Stripe session with
            # the user saved in your database
            #
            # example: client_reference_id=user.id,
            customer_email=current_user.email,  # Pre-fill the email field
            client_reference_id=current_user.id,  # Associate the session with the user
            success_url=domain_url + "success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=domain_url + "cancel",
            payment_method_types=["card"],
            mode="subscription",
            line_items=[
                {
                    "price": stripe_keys["price_id"],  # Use your regular price ID
                    "quantity": 1,
                }
            ],
            discounts=[
                {
                    "coupon": stripe_keys["price_promo_id"],  # Replace with your actual coupon ID
                }
            ],
        )
        return jsonify({"sessionId": checkout_session["id"]})
    except Exception as e:
        return jsonify(error=str(e)), 403
    
@app.route("/success")
def success():
    is_premium_user = check_premium_user()
    current_app.config['dubai_areas_data'] = fetch_dubai_areas_data()
    return render_template("index.html",dubai_areas_data= current_app.config['dubai_areas_data'],is_premium_user=is_premium_user)


@app.route("/cancel")
def cancelled():
    return render_template("index.html",dubai_areas_data= current_app.config['dubai_areas_data'])


@app.route("/webhook", methods=["POST"])
@csrf.exempt
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
    elif event["type"] == "customer.subscription.updated":
        subscription = event["data"]["object"]
        handle_subscription_updated(subscription)
    elif event["type"] == "customer.subscription.deleted":
        subscription = event["data"]["object"]
        handle_subscription_deleted(subscription)
    return "Success", 200

def handle_subscription_deleted(subscription):
    customer = StripeCustomer.query.filter_by(stripeSubscriptionId=subscription.id).first()
    if customer:
        db.session.delete(customer)
        db.session.commit()

def handle_subscription_updated(subscription):
    customer = StripeCustomer.query.filter_by(stripeSubscriptionId=subscription.id).first()
    if customer:
        customer.cancel_at_period_end = subscription.cancel_at_period_end
        db.session.commit()
        if subscription.status == 'canceled':
            # The subscription has ended, remove it from the database
            db.session.delete(customer)
            db.session.commit()

@app.route("/cancel-subscription", methods=["POST"])
@login_required
@csrf.exempt
def cancel_subscription():
    customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()
    
    if not customer:
        flash("No active subscription found.", "error")
        return redirect(url_for('manage_subscription'))
    
    try:
        updated_subscription = stripe.Subscription.modify(
            customer.stripeSubscriptionId,
            cancel_at_period_end=True
        )
        
        # Update the database to reflect the pending cancellation
        # customer.cancel_at_period_end = True
        # db.session.commit()

        #flash("Your subscription will be cancelled at the end of the current billing period.", "success")
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
    user_id_from_session = session['client_reference_id']
    # Find the user by email
    #user = User.query.filter_by(email=customer_email).first()
    # Find the user by id
    user = User.query.filter_by(id=user_id_from_session).first()
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


@app.route("/reset_password", methods=["GET", "POST"])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    form = ResetPasswordRequestForm()
    if form.validate_on_submit():

        user = User.query.filter_by(email=form.email.data).first()

        if user:
            send_reset_password_email(user)
        flash(
            "Instructions to reset your password were sent to your email address,"
            " if it exists in our system."
        )
        return redirect(url_for("reset_password_request"))

    return render_template(
        "reset_password_request.html", title="Reset Password", form=form
    )


def send_reset_password_email(user):
    reset_password_url = url_for(
        "reset_password",
        token=user.generate_reset_password_token(),
        user_id=user.id,
        _external=True,
    )

    email_body = render_template_string(
        reset_password_email_html_content, reset_password_url=reset_password_url
    )
    send_email(email_body, receiver =user.email,subject="Reset your password",message_type='html')
    

@app.route("/reset_password/<token>/<int:user_id>", methods=["GET", "POST"])
def reset_password(token, user_id):
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    user = User.validate_reset_password_token(token, user_id)
    if not user:
        return render_template(
            "reset_password_error.html", title="Reset Password error"
        )

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()

        return render_template(
            "reset_password_success.html", title="Reset Password success"
        )

    return render_template(
        "reset_password.html", title="Reset Password", form=form
    )

@app.route('/send_message', methods=['POST'])
@limiter.limit("10 per day")
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
@csrf.exempt
def manage_subscription():
    customer = StripeCustomer.query.filter_by(user_id=current_user.id).first()
    
    if customer:
        subscription = stripe.Subscription.retrieve(customer.stripeSubscriptionId)
        product = stripe.Product.retrieve(subscription.plan.product)
        context = {
            "subscription": subscription,
            "product": product,
            "cancel_at_period_end": subscription.cancel_at_period_end
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
def get_area_details():
    try:
        app.logger.info('we call get_area_details')
        is_premium_user = check_premium_user()
        if(is_premium_user):
            app.logger.info('the user is premium')
        else:
            app.logger.info('the user is not premium')
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
            
            avg_roi = df[df['instance_year'] >= 2023].groupby(group)['roi'].mean().rename('avg_roi')
            avg_transaction_value = df[df['instance_year'] >= 2023].groupby(group)['actual_worth'].mean().rename('avg_actual_worth')
            
            final_df = pd.concat([*avg_meter_prices.values(), avg_roi,avg_transaction_value], axis=1).reset_index()

            #concat the columns into an array : 
            final_df['avg_meter_price_2013_2023'] = final_df.apply(lambda row: [replace_nan_with_none(row[col]) for col in avg_meter_prices.keys()], axis=1)

            #print("Grouping {} Execution Time: {:.2f} seconds".format(group_index, time.time() - grouping_start_time))
            #avergae capital apperication calculation for that group:

            final_df['avgCapitalAppreciation2018'] = final_df.apply(lambda row: calculate_CA(row, 5), axis=1)
            final_df['avgCapitalAppreciation2013'] = final_df.apply(lambda row: calculate_CA(row, 10), axis=1)
            final_df['avgCapitalAppreciation2029'] = final_df.apply(lambda row: calculate_CA(row, 6,2029), axis=1)

            columns_containing_means = [col for col in final_df.columns if col.startswith('avg')]
            # Combine the columns : columns of the group + avg_cap_appreciation_columns
            combined_columns = group + list(set(columns_containing_means) - set(group))
            # Reorder and filter the DataFrame according to the combined list of columns
            final_df = final_df[combined_columns]
            # Drop rows where 'avgCapitalAppreciation2018' and 'avgCapitalAppreciation2013' and roi are all NaN

            final_df.dropna(subset=['avgCapitalAppreciation2018', 'avgCapitalAppreciation2013','avg_roi','avg_actual_worth'], how='all', inplace=True)

            final_df['avg_meter_price_2013_2023'] = final_df['avg_meter_price_2013_2023'].apply(interpolate_price_list)

            if 'grouped_project' in final_df.columns: # we drop empty proejct because we dont want to see blank projects in the ui
                final_df = final_df.dropna(subset=['grouped_project'])

            update_nested_dict(final_df, nested_dicts, group)

        is_premium_user = check_premium_user()

        if(nested_dicts):
            fetched_rows= remove_lonely_dash(nested_dicts)
            
            if(not is_premium_user):
                filtered_items = [
                    item for item in fetched_rows.items()
                    if item[1]['means'][0]['avg_meter_price_2013_2023'][-1] is not None
                ]
                # If filtered_items is empty, take the first two items from fetched_rows
                # Otherwise, take the first two items from filtered_items
                selected_items = filtered_items[:2] if filtered_items else list(fetched_rows.items())[:2]
                # Initialize the new dictionary with the first two pairs
                new_dict = dict(selected_items)
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
    SUM(CASE WHEN t.instance_year = 2023 THEN t.total ELSE 0 END)::float / (p.no_of_units+p.no_of_villas) AS internaldemand2023,
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
    t.project_number, p.no_of_units, no_of_villas,p.project_name_en;
    """
    try:
        cursor.execute(query, (area_id,))
        
        # Fetch and format the results
        fetched_rows = cursor.fetchall()
        fetched_rows = group_external_demand_in_array(fetched_rows)
        return fetched_rows
    except Exception as e:
        # Log the error securely
        #print(f"An error occurred: {str(e)}")  # Replace with proper logging
        return None  # Or handle the error appropriately
    finally:
        cursor.close()
        connection.close()

@app.route('/get-demand-per-project')
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

def execute_projectInfo_query(proejct_name):
    connection = get_db_connection()
    #cursor = connection.cursor(dictionary=True) mysql
    cursor = connection.cursor(cursor_factory=RealDictCursor) #postgresql

    query = """
    SELECT project_description_en,no_of_units,project_status,no_of_buildings,no_of_villas,percent_completed,completion_date,project_start_date 
    FROM projects
    WHERE project_name_en = %s;
    """
    cursor.execute(query, (proejct_name,))
    
    # Fetch and format the results
    fetched_rows = cursor.fetchall()
    return fetched_rows

def execute_unitsbyRooms_query(proejct_name):
    connection = get_db_connection()
    #cursor = connection.cursor(dictionary=True) mysql
    cursor = connection.cursor(cursor_factory=RealDictCursor) #postgresql

    query = """
    SELECT rooms_en, COUNT(*) AS count
    FROM units
    WHERE project_name_en = %s
    GROUP BY rooms_en;
    """
    cursor.execute(query, (proejct_name,))
    
    # Fetch and format the results
    fetched_rows = cursor.fetchall()
    return fetched_rows

@app.route('/get-lands-stats')
def get_lands_stats():
    is_premium_user = check_premium_user()
    if is_premium_user:
        area_id = request.args.get('area_id')
        fetched_rows = execute_land_query(area_id)
        fetched_rows_json = jsonify(fetched_rows)
        return fetched_rows_json
    else:
        return '', 204  # No Content response for non-premium users
    
@app.route('/save-list-order', methods=['POST'])
@csrf.exempt
def save_list_order():
    app.logger.info('Received request to save list order')
    # todo
    global list_order_in_memory  # Reference the global variable
    data = request.json
    if not data:
        app.logger.warning('Received empty JSON data in save-list-order request')
        return jsonify({'error': 'No data received'}), 400
    list_order_in_memory = data.get('listOrder', [])
    app.logger.debug(f'New list order: {list_order_in_memory}')
    session['hierarchy_keys'] = map_text_to_field(list_order_in_memory)
    return jsonify({'message': 'List order saved successfully!'})


@app.route('/get-list-order', methods=['GET'])
def get_list_order():
    hierarchy_keys = session.get('hierarchy_keys', ['grouped_project','property_usage_en','property_sub_type_en','rooms_en'])
    return jsonify({'listOrder': key_to_id(hierarchy_keys)})

    
def fetch_dubai_areas_data():
    is_premium_user = check_premium_user()
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
    return [legends, geojson, units]

# @app.before_request
# def initialize_dubai_areas_data():
#     print("initialize_dubai_areas_data")
#     global dubai_areas_data
#     if dubai_areas_data is None:
#         print("dubai_areas_data is none so we fatch it")
#         dubai_areas_data = fetch_dubai_areas_data()

@app.before_request
def initialize_dubai_areas_data():
    if 'dubai_areas_data' not in current_app.config:
        current_app.config['dubai_areas_data'] = fetch_dubai_areas_data()

@app.route('/dubai-areas')
def dubai_areas():
    try:
        app.logger.info('we call dubai areas')
        data_received = fetch_dubai_areas_data()
        return jsonify(data_received)
    except FileNotFoundError:
        return jsonify({'error': 'File not found'}), 404
    except Exception as e:
        return jsonify({'error': 'An error occurred', 'message': str(e)}), 500
    
def create_land_type_pie_chart(data,data_key = 'land_type_en',title = 'Land Type Distribution',legend_title='Land Types'):
    # Extract land types and counts
    land_types = [row[data_key] if row[data_key] else 'Unknown' for row in data]
    counts = [row['count'] for row in data]
    
    # Calculate percentages
    total = sum(counts)
    percentages = [(count / total) * 100 for count in counts]
    
    # Create the pie chart
    fig, ax = plt.subplots(figsize=(10, 6))  # Increased figure size to accommodate legend
    
    wedges, _, _ = ax.pie(counts, startangle=90, autopct='')
    
    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
    ax.set_title(title)
    
    # Create legend labels with percentages and counts
    legend_labels = [f'{land_type} - {percentage:.1f}% ({count})' 
                     for land_type, percentage, count in zip(land_types, percentages, counts)]
    
    # Add a legend
    ax.legend(wedges, legend_labels,
              title=legend_title,
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

    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    
    img_buffer = io.BytesIO()
    FigureCanvas(fig).print_png(img_buffer)
    img_buffer.seek(0)

    plt.close(fig)  # Close the figure to free up memory

    return img_buffer

def create_rooms_count_doughnut_chart(rooms_count_pairs):
    # Extract room types and counts from the query results
    room_types = [row['rooms_en'] for row in rooms_count_pairs]
    counts = [row['count'] for row in rooms_count_pairs]
    
    fig, ax = plt.subplots()
    
    # Create a pie chart with a hole in the middle
    wedges, texts, autotexts = ax.pie(counts, labels=room_types, autopct=lambda pct: "{:.0f}".format(pct * sum(counts) / 100), startangle=90, wedgeprops=dict(width=0.3))
    
    # Beautify the plot
    plt.setp(autotexts, size=8, weight="bold")
    ax.set_title('Room Count Distribution')
    
    # Save the plot to a buffer
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
    
    # Create a new figure
    fig, ax = plt.subplots(figsize=(18, 8))
    #plt.rcParams.update({'font.size': 26})

    # Plotting
    df['year'].value_counts().sort_index().plot(kind='bar', ax=ax, color='skyblue')
    plt.title('Number of Transactions per Year',fontsize=26)
    plt.xlabel('Year',fontsize=20)
    plt.ylabel('Number of Transactions',fontsize=22)
    plt.xticks(rotation=45,fontsize=20)
    plt.yticks(fontsize=20)
    plt.grid(True)
    plt.tight_layout()
    
    # Save the figure to a buffer
    img_buffer = io.BytesIO()
    FigureCanvas(fig).print_png(img_buffer)
    img_buffer.seek(0)
    
    # Close the figure
    plt.close(fig)
    
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


def send_email(message,mail_server='smtp.gmail.com',sender ="estatesniperhosting@gmail.com",receiver ="contact@estatesnipers.com",password="cxhj zutf hzrp hfcz",subject="New Contact Message",port=465,message_type='plain'):
    msg = MIMEMultipart()
    msg.set_unixfrom('author')
    msg['From'] = sender
    msg['To'] = receiver
    msg['Subject'] = subject
    
    #msg.attach(MIMEText(message, 'plain'))
    msg.attach(MIMEText(message, message_type))
    try:
        # Set up the SMTP server and login
        mailserver = smtplib.SMTP_SSL(mail_server, port)
        mailserver.ehlo()
        mailserver.login(sender, password)
        
        # Send the email
        mailserver.sendmail(sender, receiver, msg.as_string())
        
        # Quit the SMTP server
        mailserver.quit()
        
    except smtplib.SMTPAuthenticationError:
        app.logger.warning("SMTP Authentication Error: Unable to log in. Check the email and password.")
    except smtplib.SMTPConnectError:
        app.logger.warning("SMTP Connection Error: Unable to connect to the SMTP server.")
    except smtplib.SMTPServerDisconnected:
        app.logger.warning("SMTP Server Disconnected: The server unexpectedly disconnected.")
    except smtplib.SMTPException as e:
        app.logger.warning(f"SMTP error occurred: {e}")
    #s = smtplib.SMTP('localhost')
    #s.sendmail(sender_email, [receiver_email], msg.as_string())


def safe_get(dictionary, key, index, default="N/A"):
    try:
        return dictionary[key][index]
    except (KeyError, IndexError):
        return default
    
@app.route('/generate-pdf', methods=['POST'])
@csrf.exempt
def generate_pdf():
    try:
        app.logger.info('Received request for PDF generation')
        is_premium_user = False
        payload_size = request.content_length
        app.logger.info(f"Received payload size: {payload_size} bytes")
    
        is_premium_user = check_premium_user()
        
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
        if hierarchy_keys[0]=="grouped_project":
            dateprice_paires = execute_DATE_PRICE_pairs_query(area_data['area_id'], project=section)
            rooms_count_pairs = execute_unitsbyRooms_query(section)
            project_data = execute_projectInfo_query(section)

        # Loop through the project_demand_data to find the matching project
        project_internaldemand2023 = project_externaldemand2023 = None
        externalDemand_5Y = []
        for item in project_demand_data:
            if item['project_name_en'] == section:
                project_internaldemand2023 = item['internaldemand2023']
                project_externaldemand2023 = item['externaldemand2023']
                externalDemand_5Y = item['externalDemandYears']
                break

        # Create a PDF
        buffer = BytesIO()
        p = canvas.Canvas(buffer, pagesize=letter)

        helper = PDFHelper(p, 720, 750, 100)

        if hierarchy_keys[0]!="grouped_project":
            section+= f" ({area_data['name']})"
        helper.draw_Main_title(section,font_size=30)

    except Exception as e:
        app.logger.error(f'Error in generate_pdf: {str(e)}', exc_info=True)
        return jsonify({"error": "Internal server error"}), 500
    # Print means data
    # Data for the table
    general_means=[]
    footnotes=[]
    if hierarchy_keys[0]=="grouped_project":
        helper.draw_paragraph(project_data[0]['project_description_en'], font_size=10, font_name='Times-Roman')
        general_means = [
        ["Description", "Value"],
        ["Project status: ",str(project_data[0]['project_status'])]]

        if project_data[0]['no_of_buildings'] != 0:
            general_means.append(["Nbr of Buildings: ", str(project_data[0]['no_of_buildings'])])

        if project_data[0]['no_of_villas'] != 0:
            general_means.append(["Nbr of Villas: ", str(project_data[0]['no_of_villas'])])
            
        if project_data[0]['no_of_units'] != 0:
            general_means.append(["Nbr of Units: ", str(project_data[0]['no_of_units'])])

        if project_data[0]['project_start_date'] is not None:
            general_means.append(["Start Date: ", str(project_data[0]['project_start_date'])])

        if project_data[0]['completion_date'] is not None:
            general_means.append(["Completion Date: ", str(project_data[0]['completion_date'])])
        
        if project_data[0]['percent_completed'] >0:
            general_means.append(["Percent Completed: ", str(project_data[0]['percent_completed'])+" %"])


        general_means.extend([
            ["Average Capital Appreciation 10Y:", str(round_and_percentage(avg_capital_appreciation_2013,2))+" %"],
            ["Average Capital Appreciation 5Y:",  str(round_and_percentage(avg_capital_appreciation_2018,2))+" %"],
            ["Average Gross Rental Yield:",str(round_and_percentage(avg_roi,2))+" %"],
            ["Internal Demand¹:",str(round_and_percentage(project_internaldemand2023,2))+" %"],
            ["External Demand²:",str(round_and_percentage(project_externaldemand2023,2))+" %"]
        ])

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
    
    helper.y+=10
    # Draw the table
    helper.draw_table(general_means)
    

    # Draw the footnotes
    helper.draw_footnotes(footnotes)
    
    img_buffer = create_price_chart(avg_meter_price)
    # Insert the image into the PDF from the BytesIO object
    helper.y=240

    if hierarchy_keys[0]=="grouped_project":
        helper.y=220

    p.drawImage(ImageReader(img_buffer), 35, helper.y, width=270, height=200)
    # Update y position after the image
    #helper.y -= 160
    if hierarchy_keys[0]=="grouped_project":
        img_buffer_demand = create_price_chart(externalDemand_5Y,start_year=2018,title ='Evolution of Demand 2018-2023',y_axis='External Demand',contain_pred=False)
        p.drawImage(ImageReader(img_buffer_demand), 332, helper.y, width=270, height=200)
        
        helper.new_page()
        helper.y-=250

        img_buffer_scatter = create_scatterplot(dateprice_paires)
        
        p.drawImage(ImageReader(img_buffer_scatter), 32,  helper.y, width=270, height=200)

        img_buffer_historgram = create_histogram(dateprice_paires)
        p.drawImage(ImageReader(img_buffer_historgram), 329,  helper.y, width=270, height=200)

        helper.y-=440

        #units_repartition = create_rooms_count_doughnut_chart(rooms_count_pairs)
        units_repartition = create_land_type_pie_chart(rooms_count_pairs,data_key = 'rooms_en',title = 'Unit Type Distribution',legend_title='Types')
        p.drawImage(ImageReader(units_repartition), 50,  helper.y, width=500, height=300)

    if is_premium_user: 
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

        app.logger.info(f"length of area_data[variableValues] = {len(area_data['variableValues'])}")


        # Data for the table
        table_data = [
            ['Metric', 'Value'],
            ['Acquisition Demand 2023', f"{round_and_percentage(safe_get(area_data, 'variableValues', 7))} %"],
            ['Rental Demand 2023¹', str(round_and_percentage(safe_get(area_data, 'variableValues', 8)))+" %"],
            ['Average Sale Price', f"{safe_get(area_data, 'variableValues', 0, 0):,.2f} AED"],
            ['Average Capital Appreciation 10Y', str(round_and_percentage(safe_get(area_data, 'variableValues', 2)))+" %"],
            ['Average Capital Appreciation 5Y', str(round_and_percentage(safe_get(area_data, 'variableValues', 1)))+" %"],
            ['Average Gross Rental Yield', str(round_and_percentage(safe_get(area_data, 'variableValues', 3),2))+" %"],
            ['Supply of Finished Projects', safe_get(area_data, 'variableValues', 4)],
            ['Supply of Off-Plan Projects', safe_get(area_data, 'variableValues', 5)],
            ['Supply of Lands', safe_get(area_data, 'variableValues', 6)],
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
    else:
        helper.new_page()
        unlockpremiumtext = """The detailed report includes further insights on the project area and a detailed classification of units by property type and subtype.\n To access the full report, please upgrade to a Premium subscription.  """
        helper.draw_paragraph(unlockpremiumtext, font_size=14, font_name='Helvetica-Bold')
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
    app.run(debug=False)
