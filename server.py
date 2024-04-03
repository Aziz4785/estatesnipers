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


pd.set_option('display.max_rows', None) 
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)
pd.set_option('display.max_colwidth', None)

app = Flask(__name__)
CORS(app)
app.secret_key = 'some_secret_key'
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': 'DubaiBelgiumAnalytics_123',
    'database': 'sniperdb'
}

@app.route('/')
def index():
    return render_template('index.html') 

def get_db_connection():
    connection = mysql.connector.connect(**db_config)
    return connection


list_order_in_memory = []

@app.route('/get-area-details')
def get_area_details():
    hierarchy_keys = session.get('hierarchy_keys', ['grouped_project','property_sub_type_en','property_usage_en', 'rooms_en'])
    area_id = request.args.get('area_id')
    connection_url = f"mysql+pymysql://{db_config['user']}:{db_config['password']}@{db_config['host']}/{db_config['database']}"
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
    WHERE area_id = {area_id} AND instance_year IN (2023, 2018, 2013);
    """

    start_time = time.time()
    df = pd.read_sql_query(sql_query, engine)
    print("SQL Query Execution Time: {:.2f} seconds".format(time.time() - start_time))

    nested_dicts = {}
    groupings = create_groupings(hierarchy_keys)
    list_of_dicts = []
    for group_index,group in enumerate(groupings):
        grouping_start_time = time.time()
        
        # # Apply the custom aggregation function for each year of interest
        avg_meter_price_2013 = conditional_avg(df,group ,2013).rename('AVG_meter_price_2013')
        avg_meter_price_2018 = conditional_avg(df,group ,2018).rename('AVG_meter_price_2018')
        avg_meter_price_2023 = conditional_avg(df, group,2023).rename('AVG_meter_price_2023')
        # For avg_roi, we can apply a simpler aggregation since it only pertains to 2023 without the custom logic
        avg_roi = df[df['instance_year'] == 2023].groupby(group)['roi'].mean().rename('avg_roi')

        final_df = pd.concat([avg_meter_price_2013, avg_meter_price_2018, avg_meter_price_2023, avg_roi], axis=1).reset_index()
#         final_df = df.groupby(group, dropna=False).agg(
#             AVG_meter_price_2013=pd.NamedAgg(column='meter_sale_price', aggfunc=lambda x: np.mean(x[(df['instance_year'] == 2013) & (x.notnull())]) if x[(df['instance_year'] == 2013) & (x.notnull())].count() > 5 else np.nan),
#             AVG_meter_price_2018=pd.NamedAgg(column='meter_sale_price', aggfunc=lambda x: np.mean(x[(df['instance_year'] == 2018) & (x.notnull())]) if x[(df['instance_year'] == 2018) & (x.notnull())].count() > 5 else np.nan),
#             AVG_meter_price_2023=pd.NamedAgg(column='meter_sale_price', aggfunc=lambda x: np.mean(x[(df['instance_year'] == 2023) & (x.notnull())]) if x[(df['instance_year'] == 2023) & (x.notnull())].count() > 5 else np.nan),
#             avg_roi=pd.NamedAgg(column='roi', aggfunc=lambda x: np.mean(x[(df['instance_year'] == 2023) & (x.notnull())]))
# ).reset_index()
        print("Grouping {} Execution Time: {:.2f} seconds".format(group_index, time.time() - grouping_start_time))
        #avergae capital apperication calculation for that group:
        final_df['avgCapitalAppreciation2018'] = final_df.apply(lambda row: calculate_CA(row, 5), axis=1)
        final_df['avgCapitalAppreciation2013'] = final_df.apply(lambda row: calculate_CA(row, 10), axis=1)

        # Identify all columns starting with 'avg'

        avg_cap_appreciation_columns = [col for col in final_df.columns if col.startswith('avg')]
        # Combine the columns : columns of the group + avg_cap_appreciation_columns
        combined_columns = group + list(set(avg_cap_appreciation_columns) - set(group))
        # Reorder and filter the DataFrame according to the combined list of columns
        final_df = final_df[combined_columns]

        # Drop rows where 'avgCapitalAppreciation2018' and 'avgCapitalAppreciation2013' and roi are all NaN
        final_df.dropna(subset=['avgCapitalAppreciation2018', 'avgCapitalAppreciation2013','avg_roi'], how='all', inplace=True)
        
        # if(group_index ==0):
        #     list_of_dicts = final_df.to_dict(orient='records')
        #     if list_of_dicts:
        #         #we replace empty and None value with "-" because those values will be used as keys in the function transform_generic_aggregate
        #         nested_dicts = replace_emptyAndNone_inList(list_of_dicts)
        #         nested_dicts =transform_generic_aggregate(nested_dicts,hierarchy_keys)
        #     else:
        #         print("error !!! canot create list of dict")
        #else :
        #    update_nested_dict(final_df, nested_dicts, group)
        update_nested_dict(final_df, nested_dicts, group)
    print()
    
    # Close the connection
    engine.dispose()
    

    if(nested_dicts):
        fetched_rows= remove_lonely_dash(nested_dicts)
        json_response = jsonify(fetched_rows)
        return json_response
    else:
        return jsonify({'message': 'No data found'}), 404
    

@app.route('/get-lands-stats')
def get_lands_stats():
    area_id = request.args.get('area_id')
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    
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
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT area_id, average_sale_price, avg_ca_5, avg_ca_10, avg_roi, Supply_Finished_Pro, Supply_OffPlan_Pro, Supply_Lands FROM areas')
    fetched_rows = cursor.fetchall()  # Fetch all rows once

    price_data = {}
    capAp_5Y_data = {}
    capAp_10Y_data = {}
    avg_roi_data = {}
    Supply_Finished_Pro_data = {}
    Supply_OffPlan_Pro_data = {}
    Supply_lands_data ={}

    for row in fetched_rows:
        if row['average_sale_price'] is not None:
            price_data[row['area_id']] = float(row['average_sale_price'])
        if row['avg_ca_5'] is not None:
            capAp_5Y_data[row['area_id']] = float(row['avg_ca_5'])
        if row['avg_ca_10'] is not None:
            capAp_10Y_data[row['area_id']] = row['avg_ca_10']
        if row['avg_roi'] is not None:
            avg_roi_data[row['area_id']] = float(row['avg_roi'])
        if row['Supply_Finished_Pro'] is not None:
            Supply_Finished_Pro_data[row['area_id']] = int(row['Supply_Finished_Pro'])
        if row['Supply_OffPlan_Pro'] is not None:
            Supply_OffPlan_Pro_data[row['area_id']] = int(row['Supply_OffPlan_Pro'])
        if row['Supply_Lands'] is not None:
            Supply_lands_data[row['area_id']] = int(row['Supply_Lands'])

    valid_prices = [price for price in price_data.values() if price is not None]
    valid_CA = [ca for ca in capAp_5Y_data.values() if ca is not None]
    valid_roi = [ro for ro in avg_roi_data.values() if ro is not None]
    min_price, med_price, max_price = get_min_median_max(valid_prices)
    min_ca, med_ca, max_ca = get_min_median_max(valid_CA)
    min_roi, med_roi, max_roi = get_min_median_max(valid_roi)

    # Load the GeoJSON file
    with open('areas_coordinates/DubaiAreas.geojson', 'r') as file:
        geojson = json.load(file)

    # Enrich GeoJSON with price data and calculate fill colors
    for feature in geojson:
        area_id = int(feature['area_id'])
        if area_id in price_data:
            price = price_data[area_id]
            feature['fillColorPrice'] = get_color(price, min_price, med_price, max_price)
        else:
            # Default color if no price data is available
            feature['fillColorPrice'] = 'rgb(95,95,95)'  #  grey

        if area_id in capAp_5Y_data:
            ca = capAp_5Y_data[area_id]
            feature["avgCA_5Y"] = capAp_5Y_data[area_id]
            feature['fillColorCA5'] = get_color(ca, min_ca, med_ca, max_ca)
        else:
            feature["avgCA_5Y"] = None
            feature['fillColorCA5'] = 'rgb(95,95,95)'  #  grey

        if area_id in capAp_10Y_data:
            feature["avgCA_10Y"] = capAp_10Y_data[area_id]
        else:
            feature["avgCA_10Y"] = None
        
        if area_id in avg_roi_data:
            roi = avg_roi_data[area_id]
            feature["avg_roi"] = avg_roi_data[area_id]
            feature['fillColorRoi'] = get_color(roi, min_roi,med_roi, max_roi)
        else:
            feature["avg_roi"] = None
            feature['fillColorRoi'] = 'rgb(95,95,95)'
        
        if area_id in Supply_Finished_Pro_data:
            feature["Supply_Finished_Pro"] = Supply_Finished_Pro_data[area_id]
        else:
            feature["Supply_Finished_Pro"] = None
        
        if area_id in Supply_OffPlan_Pro_data:
            feature["Supply_OffPlan_Pro"] = Supply_OffPlan_Pro_data[area_id]
        else:
            feature["Supply_OffPlan_Pro"] = None

        if area_id in Supply_lands_data:
            feature["Supply_lands"] = Supply_lands_data[area_id]
        else:
            feature["Supply_lands"] = None
    cursor.close()
    connection.close()
    return jsonify(geojson)

if __name__ == '__main__':
    app.run(debug=True)
