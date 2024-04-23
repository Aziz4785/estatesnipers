from flask import Flask, jsonify, render_template,request
from flask_cors import CORS
import pymysql
import mysql.connector
import json
from flask import session
import time
import datetime
import math
from server_utils import * 
from sqlalchemy import create_engine
import psycopg2
from flask import jsonify
from psycopg2.extras import RealDictCursor

pd.set_option('display.max_rows', None) 
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', None)

app = Flask(__name__)
CORS(app)
app.secret_key = 'some_secret_key'
# db_config = {
#     'host': 'localhost',
#     'user': 'root',
#     'password': 'DubaiBelgiumAnalytics_123',
#     'database': 'sniperdb'
# }
db_config = {
    'host': 'localhost',
    'dbname': 'SNIPERDB',  # 'database' in MySQL is 'dbname' in PostgreSQL
    'user': 'postgres',
    'password': r'DubaiAnalytics_123',
    'port': '5432'  # Default PostgreSQL port
}
db_url = "postgres://uaovl716s190an:p785b9fb819ee0e2fa3fb5eaae6550ed481578e5f782c0287d2e8b5d846934059@ec2-52-7-195-158.compute-1.amazonaws.com:5432/df4dm8ak5du5r"
#db_url = "postgresql://postgres:DubaiAnalytics_123@localhost:5432/SNIPERDB"

@app.route('/')
def index():
    return render_template('index.html') 

def get_db_connection():
    #connection = mysql.connector.connect(**db_config)
    #connection = psycopg2.connect(**db_config)
    connection = psycopg2.connect(db_url) #here we use an url
    return connection


list_order_in_memory = []

@app.route('/get-area-details')
def get_area_details():
    hierarchy_keys = session.get('hierarchy_keys', ['grouped_project','property_sub_type_en','property_usage_en', 'rooms_en'])
    area_id = request.args.get('area_id')
    #connection_url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
    #connection_url = f"postgresql+psycopg2://{db_config['user']}:{db_config['password']}@{db_config['host']}:{db_config['port']}/{db_config['dbname']}"
    connection_url = db_url
    engine = create_engine(connection_url)
    
    sql_query = f"""
    SELECT 
        pst.property_sub_type_en, 
        grouped_project, 
        rooms_en, 
        property_usage_en,
        instance_year,
        meter_sale_price,
        roi
    FROM 
        base_table t
    LEFT JOIN
        propertysubtype pst 
    ON 
        t.property_sub_type_id = pst.property_sub_type_id
    WHERE area_id = {area_id} AND instance_year >=2013;
    """

    start_time = time.time()
    df = pd.read_sql_query(sql_query, engine)
    print("SQL Query Execution Time: {:.2f} seconds".format(time.time() - start_time))

    nested_dicts = {}
    groupings = create_groupings(hierarchy_keys)
    
    for group_index,group in enumerate(groupings):
        grouping_start_time = time.time()
        print("grouping by : "+str(group))

        # # Apply the custom aggregation function for each year of interest
        avg_meter_price_2013 = conditional_avg(df,group ,2013).rename('AVG_meter_price_2013')
        avg_meter_price_2014 = conditional_avg(df,group ,2014).rename('AVG_meter_price_2014')
        avg_meter_price_2015 = conditional_avg(df,group ,2015).rename('AVG_meter_price_2015')
        avg_meter_price_2016 = conditional_avg(df,group ,2016).rename('AVG_meter_price_2016')
        avg_meter_price_2017 = conditional_avg(df,group ,2017).rename('AVG_meter_price_2017')
        avg_meter_price_2018 = conditional_avg(df,group ,2018).rename('AVG_meter_price_2018')
        avg_meter_price_2019 = conditional_avg(df,group ,2019).rename('AVG_meter_price_2019')
        avg_meter_price_2020 = conditional_avg(df,group ,2020).rename('AVG_meter_price_2020')
        avg_meter_price_2021 = conditional_avg(df,group ,2021).rename('AVG_meter_price_2021')
        avg_meter_price_2022 = conditional_avg(df,group ,2022).rename('AVG_meter_price_2022')
        avg_meter_price_2023 = conditional_avg(df, group,2023).rename('AVG_meter_price_2023')

        avg_roi = df[df['instance_year'] == 2023].groupby(group)['roi'].mean().rename('avg_roi')

        final_df = pd.concat([avg_meter_price_2013,avg_meter_price_2014,avg_meter_price_2015,avg_meter_price_2016, avg_meter_price_2017,avg_meter_price_2018,avg_meter_price_2019, avg_meter_price_2020,avg_meter_price_2021,avg_meter_price_2022,avg_meter_price_2023, avg_roi], axis=1).reset_index()

        final_df['avg_meter_price_2013_2023'] = final_df.apply(lambda row: [replace_nan_with_none(row[col]) for col in ['AVG_meter_price_2013','AVG_meter_price_2014','AVG_meter_price_2015','AVG_meter_price_2016', 'AVG_meter_price_2017','AVG_meter_price_2018','AVG_meter_price_2019', 'AVG_meter_price_2020','AVG_meter_price_2021','AVG_meter_price_2022','AVG_meter_price_2023']], axis=1)

        print("Grouping {} Execution Time: {:.2f} seconds".format(group_index, time.time() - grouping_start_time))
        #avergae capital apperication calculation for that group:

        final_df['avgCapitalAppreciation2018'] = final_df.apply(lambda row: calculate_CA(row, 5), axis=1)
        final_df['avgCapitalAppreciation2013'] = final_df.apply(lambda row: calculate_CA(row, 10), axis=1)

        # Identify all columns starting with 'avg'

        columns_containing_means = [col for col in final_df.columns if col.startswith('avg')]
        # Combine the columns : columns of the group + avg_cap_appreciation_columns
        combined_columns = group + list(set(columns_containing_means) - set(group))
        # Reorder and filter the DataFrame according to the combined list of columns
        final_df = final_df[combined_columns]
        # Drop rows where 'avgCapitalAppreciation2018' and 'avgCapitalAppreciation2013' and roi are all NaN
        final_df.dropna(subset=['avgCapitalAppreciation2018', 'avgCapitalAppreciation2013','avg_roi'], how='all', inplace=True)
        update_nested_dict(final_df, nested_dicts, group)

    # Close the connection
    engine.dispose()
    

    if(nested_dicts):
        fetched_rows= remove_lonely_dash(nested_dicts)
        json_response = jsonify(fetched_rows)
        return json_response
    else:
        return jsonify({'message': 'No data found'}), 404
    
@app.route('/get-demand-per-project')
def get_demand_per_project():
    area_id = request.args.get('area_id')
    connection = get_db_connection()
    #cursor = connection.cursor(dictionary=True) mysql
    cursor = connection.cursor(cursor_factory=RealDictCursor) #postgresql
    
    query = """
       SELECT 
    p.project_name_en,
    SUM(CASE WHEN t.instance_year = 2023 THEN t.total ELSE 0 END) / p.no_of_units AS internalDemand2023,
    (SUM(CASE WHEN t.instance_year = 2023 THEN t.total ELSE 0 END) / (SELECT COUNT(*) FROM transactions_per_year WHERE instance_year = 2023)) AS externalDemand2023,
    (SUM(CASE WHEN t.instance_year = 2022 THEN t.total ELSE 0 END) / (SELECT COUNT(*) FROM transactions_per_year WHERE instance_year = 2022))  AS externalDemand2022,
    (SUM(CASE WHEN t.instance_year = 2021 THEN t.total ELSE 0 END) / (SELECT COUNT(*) FROM transactions_per_year WHERE instance_year = 2021))  AS externalDemand2021,
    (SUM(CASE WHEN t.instance_year = 2020 THEN t.total ELSE 0 END) / (SELECT COUNT(*) FROM transactions_per_year WHERE instance_year = 2020))  AS externalDemand2020,
    (SUM(CASE WHEN t.instance_year = 2019 THEN t.total ELSE 0 END) / (SELECT COUNT(*) FROM transactions_per_year WHERE instance_year = 2019))  AS externalDemand2019,
    (SUM(CASE WHEN t.instance_year = 2018 THEN t.total ELSE 0 END) / (SELECT COUNT(*) FROM transactions_per_year WHERE instance_year = 2018))  AS externalDemand2018
FROM 
    transactions_per_year t
JOIN 
    projects p ON t.project_number = p.project_number
WHERE 
    t.area_id = %s
    AND p.no_of_units > 80
GROUP BY 
    t.project_number, p.no_of_units;
    """
    cursor.execute(query, (area_id,))
    
    # Fetch and format the results
    fetched_rows = cursor.fetchall()
    fetched_rows = group_external_demand_in_array(fetched_rows)

    fetched_rows_json = jsonify(fetched_rows)
    return fetched_rows_json

@app.route('/get-lands-stats')
def get_lands_stats():
    area_id = request.args.get('area_id')
    connection = get_db_connection()
    #cursor = connection.cursor(dictionary=True) mysql
    cursor = connection.cursor(cursor_factory=RealDictCursor) #postgresql
    
    # Use a parameterized query to safely include user input
    query = """
    SELECT land_type_en, COUNT(*) AS count
    FROM lands
    WHERE area_id = %s
    GROUP BY land_type_en;
    """
    cursor.execute(query, (area_id,))
    
    # Fetch and format the results
    fetched_rows = cursor.fetchall()
    fetched_rows_json = jsonify(fetched_rows)
    return fetched_rows_json
@app.route('/save-list-order', methods=['POST'])
def save_list_order():
    # todo
    global list_order_in_memory  # Reference the global variable
    data = request.json
    list_order_in_memory = data.get('listOrder', [])
    session['hierarchy_keys'] = map_text_to_field(list_order_in_memory)

    return jsonify({'message': 'List order saved successfully!'})

@app.route('/get-list-order', methods=['GET'])
def get_list_order():
    return jsonify({'listOrder': list_order_in_memory})

    
@app.route('/dubai-areas')
def dubai_areas():
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
        "averageSalePrice": [round(med_price/2), round(med_price), round(med_price+(max_price-med_price)/2.0)],
        "avgCA_5Y": [round(med_ca*100/2), round(med_ca*100), round((med_ca+(max_ca-med_ca)/2.0)*100)],
        "avg_roi": [round(med_roi*100/2), round(med_roi*100), round((med_roi+(max_roi-med_roi)/2.0)*100)],
        "aquisitiondemand_2023" : [
        round(med_aqDemand*100/2) if med_aqDemand is not None else 0,
        round(med_aqDemand*100) if med_aqDemand is not None else 0,
        round((med_aqDemand+(max_asDemand-med_aqDemand)/2.0)*100) if med_aqDemand is not None else 0
    ]
    }
    
    # Load the GeoJSON file
    with open('areas_coordinates/DubaiAreas.geojson', 'r') as file:
        geojson = json.load(file)
   
    # Enrich GeoJSON with price data and calculate fill colors
    for feature in geojson:
        area_id = int(feature['area_id'])
        if area_id in data_stores['average_sale_price']:
            price = data_stores['average_sale_price'][area_id]
            feature["averageSalePrice"] = price
            feature['fillColorPrice'] = get_color(price, min_price, med_price, max_price)
        else:
            # Default color if no price data is available
            feature['fillColorPrice'] = 'rgb(95,95,95)'  #  grey

        if area_id in data_stores['avg_ca_5']:
            ca = data_stores['avg_ca_5'][area_id]
            feature["avgCA_5Y"] = data_stores['avg_ca_5'][area_id]
            feature['fillColorCA5'] = get_color(ca, min_ca, med_ca, max_ca)
        else:
            feature["avgCA_5Y"] = None
            feature['fillColorCA5'] = 'rgb(95,95,95)'  #  grey

        if area_id in data_stores['avg_ca_10']:
            feature["avgCA_10Y"] = data_stores['avg_ca_10'][area_id]
        else:
            feature["avgCA_10Y"] = None
        
        if area_id in data_stores['avg_roi']:
            roi = data_stores['avg_roi'][area_id]
            feature["avg_roi"] = data_stores['avg_roi'][area_id]
            feature['fillColorRoi'] = get_color(roi, min_roi,med_roi, max_roi)
        else:
            feature["avg_roi"] = None
            feature['fillColorRoi'] = 'rgb(95,95,95)'
        
        if area_id in data_stores['supply_finished_pro']:
            feature["supply_finished_pro"] = data_stores['supply_finished_pro'][area_id]
        else:
            feature["supply_finished_pro"] = None
        
        if area_id in data_stores['supply_offplan_pro']:
            feature["supply_offplan_pro"] = data_stores['supply_offplan_pro'][area_id]
        else:
            feature["supply_offplan_pro"] = None

        if area_id in data_stores['supply_lands']:
            feature["supply_lands"] = data_stores['supply_lands'][area_id]
        else:
            feature["supply_lands"] = None

        if area_id in data_stores['aquisitiondemand_2023']:
            feature["aquisitiondemand_2023"] = data_stores['aquisitiondemand_2023'][area_id]
            feature['fillColorAquDemand'] = get_color(feature["aquisitiondemand_2023"], min_aqDemand,med_aqDemand, max_asDemand)
            #print(f"{area_id} is  in data_stores['aquisitiondemand_2023'] so fill color = {feature['fillColorAquDemand']}")
        else:
            #print(f"{area_id} is not in data_stores['aquisitiondemand_2023']")
            feature['fillColorAquDemand'] = 'rgb(95,95,95)'
            feature["aquisitiondemand_2023"] = None
            
        if area_id in data_stores['rentaldemand_2023']:
            feature["rentaldemand_2023"] = data_stores['rentaldemand_2023'][area_id]
            feature['fillColorrentDemand'] = get_color(feature["rentaldemand_2023"], min_rentDemand,med_rentDemand, max_rentDemand)
        else:
            feature['fillColorrentDemand'] = 'rgb(95,95,95)'
            feature["rentaldemand_2023"] = None
 

    cursor.close()
    connection.close()
    #print("data beofre sending : ")
    #print([legends, geojson])
    return jsonify([legends, geojson])

if __name__ == '__main__':
    app.run(debug=True)
