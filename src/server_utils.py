import math
from decimal import Decimal
import pandas as pd
import numpy as np
from scipy import interpolate
from scipy.interpolate import interp1d
from datetime import datetime
from scipy.interpolate import PchipInterpolator
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import io
from io import BytesIO
import smtplib
from sqlalchemy import create_engine, text
import os
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import psycopg2
from flask_mailman import EmailMessage
from flask import render_template_string,url_for
# Function to safely convert string to float or None
def safe_float(x):
    try:
        return float(x)
    except:
        return None
    
# Function to perform polynomial interpolation
def interpolate_price_list(lst):
    # Ensure we're working with the price list, not the column names
    if isinstance(lst[0], str):
        return lst  # Return column names as is
    
    # Convert to float, replacing 'None' strings with None
    values = [None if (x is None or (isinstance(x, str) and x.lower() == 'none')) 
              else float(x) for x in lst]
    
    # Find indices and values of non-None elements
    valid_indices = [i for i, x in enumerate(values) if x is not None]
    valid_values = [values[i] for i in valid_indices]
    
    if len(valid_indices) < 2:
        return values  # Not enough points for interpolation
    
    # Perform interpolation
    interpolator = PchipInterpolator(valid_indices, valid_values)
    
    # Interpolate only for None values between the first and last valid values
    for i in range(valid_indices[0], valid_indices[-1] + 1):
        if values[i] is None:
            values[i] = float(interpolator(i))
    
    return values

def get_min_median_max(valid_prices):
    if valid_prices:
        valid_prices_np = np.array(valid_prices)
        min_price = np.min(valid_prices_np)
        max_price = np.max(valid_prices_np)
        median = np.median(valid_prices_np)
        return min_price,median,max_price 
    else:
        return None, None, None

def custom_round(x):
    if abs(x) < 10:
        return round(x, 2)
    else:
        return round(x)
    
def get_color(price, min_price,med_price, max_price):
    # Normalize price to a 0-1 scale
    normalized_price = (price - min_price) / (max_price - min_price)
    normalized_med = (med_price - min_price) / (max_price - min_price)
    
    if normalized_price <= normalized_med/2.0:
        red = 0
        blue = 192
        green = 0 
    elif normalized_price <= normalized_med:
        red = 82
        blue = 223
        green = 82
    elif normalized_price < normalized_med+(1.0-normalized_med)/2.0:
        red = 223
        blue = 82
        green = 82
    else:
        red = 192
        blue = 0 
        green = 0
    
    # Construct the color string
    color_string = f"rgb({red}, {green}, {blue})"
    return color_string

def replace_emptyAndNone(none_value):
    if none_value == "" or none_value is None or pd.isna(none_value):
        return "-"
    elif isinstance(none_value, (int, float)):
        return str(none_value)
    else:
        return none_value


def replace_emptyAndNone_inList(list_of_dicts):
    for dictionary in list_of_dicts:
        for key, value in dictionary.items():
            dictionary[key] = replace_emptyAndNone(value)
    return list_of_dicts


# def remove_lonely_dash(d):
#     """
#     For each key in the dictionary d, if the value corresponding to the key is a dictionary
#     that contains only one key and that key is "-", update the value of the key to be the value
#     corresponding to "-".
#     """
#     for key, value in list(d.items()): 
#         if isinstance(value, dict):
#             remove_lonely_dash(value)
#         if isinstance(value, dict) and (len(value) == 1 or (len(value)==2 and 'means' in value)) and "-" in value:
#             d[key] = value["-"]
#     return d


def remove_lonely_dash(d):
    if "-" in d.keys() and len(d.keys())>2:
        del d['-']
    elif "-" in d.keys():
        while(len(d.keys())==2 and "-" in d.keys()) :# while it is 'means' and '-'
            if(len(d['-'])==1 ):
                del d['-']
            elif(len(d['-'])>2 and  "-" in d['-']):
                for c in d['-']:
                    if c != '-' and c !='means':
                        d[c]=d['-'][c]
                del d['-'] #now that we have some A type in the children we need to get rid of '-'
            else:
                for c in d['-']:
                    if c =='-' or c!= 'means':
                        d[c]=d['-'][c]
                        if c!='-':
                            del d['-']  
    for key, value in list(d.items()): 
        if isinstance(value, dict) and key != 'means':
            remove_lonely_dash(value)
    return d

# def remove_lonely_dash_old(d):
#     if d =={}:
#         return d
#     dash_present = any("-" in v for v in d.values())
#     first_layer_key = next(iter(d))  # Get the first key in the outermost dictionary
#     first_layer_keys = d[first_layer_key].keys()
#     if dash_present and len(first_layer_keys) > 2: # if '-' coexist with other node type
#         del d[first_layer_key]['-']
#         for key, value in d[first_layer_key].items():
#             if key != 'means':
#                 remove_lonely_dash({key: value})
#     elif dash_present: #if there is only a dash and a means in the children of the roo
#         while(len(first_layer_keys)==2 and "-" in first_layer_keys) :# while it is 'means' and '-'
#             if(len(d[first_layer_key]['-'])==1 ):
#                 del d[first_layer_key]['-']
#             elif(len(d[first_layer_key]['-'])>2 and  "-" in d[first_layer_key]['-']):
#                 for c in d[first_layer_key]['-']:
#                     if c != '-' and c !='means':
#                         d[first_layer_key][c]=d[first_layer_key]['-'][c]
#                 del d[first_layer_key]['-'] #now that we have some A type in the children we need to get rid of '-'
#             else:
#                 for c in d[first_layer_key]['-']:
#                     if c =='-' or c!= 'means':
#                         d[first_layer_key][c]=d[first_layer_key]['-'][c]
#                         if c!='-':
#                             del d[first_layer_key]['-']  
#                 first_layer_keys = d[first_layer_key].keys()
#         for key, value in d[first_layer_key].items():
#             if key != 'means':
#                 remove_lonely_dash({key: value}) 
#     else:
#         for key, value in d[first_layer_key].items():
#             if key != 'means':
#                 remove_lonely_dash({key: value})  
#     return d


# Function to replace NaN with None
def replace_nan_with_none(value):
    if pd.isna(value):
        return None
    else:
        return value

def calculate_CA(row, year_diff,last_year = 2023):
    # Capital Appreciattion calculation
    #calculate_CA(row, 5) to calculate the capital appr over 5 years

    price_new_key = f'AVG_meter_price_{last_year}'
    price_old_key = f'AVG_meter_price_{last_year-year_diff}'

    if price_new_key in row and price_old_key in row:
        price_new = row[price_new_key]
        price_old = row[price_old_key]
        if pd.notna(price_new) and pd.notna(price_old) and price_new != 0 and price_old != 0:
            return (price_new - price_old) / price_old
        else:
            return np.nan
    else:
        # If one or both keys are missing, return NaN
        return np.nan

    
def calculate_CA_from_array(row, year_diff):
    avg_meter_price = row['avg_meter_price_2014_2024']

    current_year_index = 2024 - 2014  # This is the index for the year 2023 in the array.
    target_year_index = current_year_index - year_diff  # Calculate the index for the target year.

    # If avg_meter_price is an array, check if all elements are NaN.
    # If so, or if avg_meter_price itself is NaN, return np.nan.
    if isinstance(avg_meter_price, np.ndarray) or isinstance(avg_meter_price, list):
        if np.isnan(avg_meter_price).all():
            return np.nan
        elif 0 <= target_year_index < len(avg_meter_price):
            price_new = row['avg_meter_price_2014_2024'][current_year_index]  # Price for 2023
            price_old = row['avg_meter_price_2014_2024'][target_year_index]  # Price for the target year
            
            # Check if both prices are available and not equal to 0
            if pd.notna(price_new) and pd.notna(price_old) and price_new != 0 and price_old != 0:
                return (price_new - price_old) / price_old
            else:
                return np.nan
        else:
            return np.nan  # Handle index out of range or other cases
    elif pd.isna(avg_meter_price):
        # This case handles when avg_meter_price is a scalar NaN value
        return np.nan
    else:
        # Additional handling for unexpected cases, you might adjust this part
        return np.nan  # Or some default value or error handling
    
def update_nested_dict(df, nested, grouped_by):
    n= len(grouped_by)
    for index, row in df.iterrows():
        #row is like : property_sub_type_en                  Flat
        # Initialize a reference to the nested dictionary
        temp = nested
        # Navigate through the grouped_by columns
        for i in range(n):
            key = row.iloc[i]
            #key is like "Flat"
            key=replace_emptyAndNone(key)
            
            if key not in temp:
                temp[key] = {}
            temp = temp[key]
            
        # Replace NaN with None in the remaining columns before converting to dict
        remaining_cols = row.iloc[n:].replace({np.nan: None}).to_dict()
        temp['means'] = [remaining_cols]

def aggregate_yearly(df):
    #https://pandas.pydata.org/pandas-docs/version/0.22/generated/pandas.core.groupby.GroupBy.apply.html
    # Ensure the dataframe contains the necessary columns
    if not {'meter_sale_price', 'instance_year'}.issubset(df.columns):
        raise ValueError("DataFrame must contain 'meter_sale_price' and 'instance_year' columns")

    # Initialize an array to hold the average values
    averages = []

    for year in range(2014, 2025):
        # Calculate the average for the current year
        yearly_average = df[df['instance_year'] == year]['meter_sale_price'].mean()
        # Handle case where there might be no data for a year, ensuring it's a float NaN
        if pd.isna(yearly_average):
            yearly_average = float('nan')
        averages.append(yearly_average)

    # Create a DataFrame with a single row containing the averages array
    result_df = pd.DataFrame([averages], columns=[f'Year_{year}' for year in range(2014, 2025)])
    return result_df

def conditional_avg(df, group,year, threshold=5):
    """Compute conditional average based on the year and a threshold for counts."""
    filtered_df = df[(df['instance_year'] == year) & df['meter_sale_price'].notnull()]
    
    result = filtered_df.groupby(group, dropna=False)['meter_sale_price'].agg(lambda x: x.mean() if len(x) > threshold else np.nan)
    
    return result

def weighted_avg(df, group, year):
    # Filter the DataFrame
    filtered_df = df[(df['instance_year'] == year) & df['meter_sale_price'].notnull()]
    # Calculate the weighted average of 'meter_sale_price' using 'total_rows' as weights
    result = filtered_df.groupby(group, dropna=False).apply(
        lambda x: (x['meter_sale_price'] * x['total_rows']).sum() / x['total_rows'].sum()
    )
    return result

from datetime import datetime, timedelta

from calendar import monthrange
from psycopg2.extras import RealDictCursor
def get_monthly_transaction_counts(connection, area_id):
    # Get the last day of the previous month
    today = datetime.now().date()
    first_of_this_month = today.replace(day=1)
    last_of_previous_month = first_of_this_month - timedelta(days=1)
    
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    
    results = []
    for i in range(12):
        year, month = (last_of_previous_month.year, last_of_previous_month.month)
        _, last_day = monthrange(year, month)
        
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, last_day).date()
        
        query = """
        SELECT COUNT(*) as count
        FROM transactions
        WHERE area_id = %s
          AND instance_date >= %s
          AND instance_date <= %s
        """
        
        cursor.execute(query, (area_id, start_date, end_date))
        count = cursor.fetchone()['count']
        
        results.append({
            'month': start_date.strftime('%Y-%m'),
            'count': count,
            'start_date': start_date,
            'end_date': end_date
        })
        
        # Move to the previous month
        last_of_previous_month = start_date - timedelta(days=1)
    
    cursor.close()
    return results[::-1]  # Reverse the list to have the oldest month first


def get_monthly_rents_counts(connection, area_id):
    # Get the last day of the previous month
    today = datetime.now().date()
    first_of_this_month = today.replace(day=1)
    last_of_previous_month = first_of_this_month - timedelta(days=1)
    
    cursor = connection.cursor(cursor_factory=RealDictCursor)
    
    results = []
    for i in range(12):
        year, month = (last_of_previous_month.year, last_of_previous_month.month)
        _, last_day = monthrange(year, month)
        
        start_date = datetime(year, month, 1).date()
        end_date = datetime(year, month, last_day).date()
        
        query = """
        SELECT COUNT(*) as count
        FROM rentcontracts
        WHERE area_id = %s
          AND contract_start_date >= %s
          AND contract_start_date <= %s
        """
        
        cursor.execute(query, (area_id, start_date, end_date))
        count = cursor.fetchone()['count']
        
        results.append({
            'month': start_date.strftime('%Y-%m'),
            'count': count,
            'start_date': start_date,
            'end_date': end_date
        })
        
        # Move to the previous month
        last_of_previous_month = start_date - timedelta(days=1)
    
    cursor.close()
    return results[::-1]  # Reverse the list to have the oldest month first

def get_db_connection():
    #connection = mysql.connector.connect(**db_config)
    #connection = psycopg2.connect(**db_config)
    #connection = psycopg2.connect(db_url) #here we use an url
    #DATABASE_URL = db_url #local database
    DATABASE_URL = os.environ.get('HEROKU_POSTGRESQL_NAVY_URL')  # Fetch the correct environment variable
    connection = psycopg2.connect(DATABASE_URL)
    return connection

def execute_monthly_transaction_counts(area_id):
    connection = get_db_connection()  # Assuming you have this function defined
    try:
        monthly_counts = get_monthly_transaction_counts(connection, area_id)
        return monthly_counts
    finally:
        connection.close()

def execute_monthly_RENTS_counts(area_id):
    connection = get_db_connection()  # Assuming you have this function defined
    try:
        monthly_counts = get_monthly_rents_counts(connection, area_id)
        return monthly_counts
    finally:
        connection.close()

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
def create_transaction_chart(data, title,chart_type='bar'):
    # Extract dates and counts
    dates = [datetime.strptime(item['month'], '%Y-%m') for item in data]
    counts = [item['count'] for item in data]

    # Create figure and axis
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot data
    if chart_type == 'bar':
        ax.bar(dates, counts, width=20, align='center')
    elif chart_type == 'line':
        ax.plot(dates, counts, marker='o')
    else:
        raise ValueError("Invalid chart type. Choose 'bar' or 'line'.")

    # Customize the chart
    ax.set_title(title, fontsize=16)
    ax.set_xlabel('Month', fontsize=12)
    ax.set_ylabel('Count', fontsize=12)

    # Format x-axis
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45, ha='right')

    # Add grid for better readability
    ax.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()

    img_buffer = io.BytesIO()
    FigureCanvas(fig).print_png(img_buffer)
    img_buffer.seek(0)

    plt.close(fig)  # Close the figure to free up memory

    return img_buffer


def conditional_avg_array(df, group, start_year=2014, end_year=2024, threshold=5):
    """
    Compute conditional averages for a range of years, returning an array of averages
    or a single None for each group if no year meets the criteria.
    """

    averages = []  # Initialize a list to store the yearly averages or NaNs
    for year in range(start_year, end_year + 1):
        # Filter rows for the specific year and valid meter_sale_price values
        filtered_df = df[(df['instance_year'] == year) & df['meter_sale_price'].notnull()]

        # Calculate the average if the count is above the threshold, else None
        yearly_avg = filtered_df.groupby(group, dropna=False)['meter_sale_price'].agg(
            lambda x: x.mean() if len(x) > threshold else None)
        # if a tuple (group) has less than threshold for year X then we will have avg price as None
        # if a tuple (group) is not in filtered_df (because all its meter_sale_price are null) , we will have Nan
        # Replace NaN values in the last column with a default value (e.g., 0)
        #yearly_avg = yearly_avg.fillna(-1)
        averages.append(yearly_avg)

    # Combine the yearly averages into a DataFrame to ensure alignment on the group index
    combined_averages_df = pd.DataFrame(averages)

    combined_averages_df_transposed  = combined_averages_df.transpose()
    
    result_series = combined_averages_df_transposed.apply(
        lambda x: [value if not np.isnan(value) else None for value in x.values] if not np.isnan(x.values).all() else None, 
        axis=1
    ).rename('avg_meter_price_2014_2024')

    return result_series

def round_and_percentage(number,decimals=2):
    return round(number * 100, decimals)if number is not None else "N/A"


reset_password_email_html_content = """
<p>Hello,</p>
<p>You are receiving this email because you requested a password reset for your account.</p>
<p>
    To reset your password
    <a href="{{ reset_password_url }}">click here</a>.
</p>
<p>
    Alternatively, you can paste the following link in your browser's address bar: <br>
    {{ reset_password_url }}
</p>
<p>If you have not requested a password reset please contact us at contact@estatesnipers.com</p>
<p>
    Thank you!
</p>
"""



def separate_last_part(input_string):
    # Find the last occurrence of " / "
    last_separator_index = input_string.rfind(" / ")
    
    if last_separator_index != -1:
        # Split the string into two parts
        first_part = input_string[:last_separator_index + 3]  # Include the last " / "
        last_part = input_string[last_separator_index + 3:]  # Start after the last " / "
        return first_part, last_part
    else:
        # If " / " is not found, return the original string and an empty string
        return input_string, ""
    
def key_to_id(list):
    mapping = {
        "grouped_project" : "2",
        "property_sub_type_en" : "1",
        "property_usage_en" : "3",
        "rooms_en" : "4"
    }

    output_list = [mapping[item] for item in list]
    return output_list

def map_text_to_field(input_list):
    #transform the hierarchy defined by the user in settings to a list
    mapping = {
        "2": "grouped_project",
        "1": "property_sub_type_en",
        "3": "property_usage_en",
        "4": "rooms_en"
    }
    
    # Sorting the input list based on the 'order' key
    sorted_input = sorted(input_list, key=lambda x: x['order'])
    
    # Mapping the 'text' in each item to its corresponding field using the 'mapping' dictionary
    output_list = [mapping[item['text']] for item in sorted_input]
    
    return output_list

def create_groupings(input_list):
    groupings = []
    
    # Iterate over the input list, reducing its length by one with each iteration
    for i in range(len(input_list), 0, -1):
        # Append a slice of the input list from the beginning up to the current iteration index
        groupings.append(input_list[:i])
    
    return groupings

def group_external_demand_in_array(sql_result):
    transformed_data = []
    for item in sql_result:
        project_data = {
            "project_name_en": item["project_name_en"],
            "internaldemand2024": float(item["internaldemand2024"]) if item["internaldemand2024"] is not None else 0.0,
            "externaldemand2024": float(item["externaldemand2024"]) if item["externaldemand2024"] is not None else 0.0,
            "externalDemandYears": []
        }

        for year in range(2019, 2025):
            key = f"externaldemand{year}"
            value = item.get(key)
            project_data["externalDemandYears"].append(float(value) if value is not None else 0.0)
        
        transformed_data.append(project_data)

    return transformed_data


def get_combined_data(connection_url, area=None, min_roi=None):
    base_query = """
    SELECT 
        ar.area_name_en,
        bt.grouped_project,
        bt.rooms_en,
        pdt.property_sub_type_en,
        bt.property_usage_en,
        AVG(bt.actual_worth) as avg_actual_worth,
        AVG(bt.projected_CA_5Y)*100 as avg_projected_ca,
        AVG(bt.roi)*100 as avg_roi,
        p.externaldemand2024*100 as external_demand,
        p.internaldemand2024*100 as internal_demand
    FROM 
        base_table bt
    LEFT JOIN 
        projects p ON bt.grouped_project = p.project_name_en
    LEFT JOIN 
        propertysubtype pdt ON bt.property_sub_type_id = pdt.property_sub_type_id
    LEFT JOIN 
        areas ar ON bt.area_id = ar.area_id
    WHERE 1=1
    AND bt.instance_year>=2021
    """

    

    
    params = {}

    if area:
        base_query += " AND ar.area_name_en = :area"
        params['area'] = area

    base_query += """
    GROUP BY 
        ar.area_name_en, bt.grouped_project, bt.rooms_en, pdt.property_sub_type_en, 
        bt.property_usage_en, p.externaldemand2024, p.internaldemand2024
    """
    if min_roi is not None:
        base_query += " HAVING AVG(bt.roi)*100 >= :min_roi"
        params['min_roi'] = min_roi

    engine = create_engine(connection_url)
    with engine.connect() as connection:
        df = pd.read_sql_query(text(base_query), connection, params=params)

    numeric_columns = ['avg_roi', 'external_demand', 'internal_demand', 'avg_actual_worth', 'avg_projected_ca']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].round(2)

    return df

def get_combined_data_old(connection_string,area=None, min_roi=None):
    # Create SQLAlchemy engine
    engine = create_engine(connection_string)

    # SQL query to join tables and aggregate data
    query = text("""
    SELECT 
        ar.area_name_en,
        bt.grouped_project,
        bt.rooms_en,
        pdt.property_sub_type_en,
        bt.property_usage_en,
        AVG(bt.actual_worth) as avg_actual_worth,
        AVG(bt.projected_ca_5Y)*100 as avg_projected_CA,
        AVG(bt.roi)*100 as avg_roi,
        p.externaldemand2024*100 as External_demand,
        p.internaldemand2024*100 as Internal_demand
    FROM 
        base_table bt
    LEFT JOIN 
        projects p ON bt.grouped_project = p.project_name_en
    LEFT JOIN 
        propertysubtype pdt ON bt.property_sub_type_id = pdt.property_sub_type_id
    LEFT JOIN 
        areas ar ON bt.area_id = ar.area_id 
    WHERE 1=1
        {% if area %}
        AND ar.area_name_en = :area
        {% endif %}
        {% if min_roi %}
        AND bt.roi >= :min_roi
        {% endif %}            
    GROUP BY 
        ar.area_name_en, bt.grouped_project, bt.rooms_en, pdt.property_sub_type_en, 
        bt.property_usage_en, p.externaldemand2024, p.internaldemand2024
    """)

    # Execute query and create DataFrame
    with engine.connect() as connection:
        params = {}
        if area:
            params['area'] = area
        if min_roi:
            params['min_roi'] = min_roi / 100  # Convert percentage to decimal

        df = pd.read_sql_query(query, connection, params=params)


    numeric_columns = ['avg_roi', 'external_demand', 'internal_demand', 'avg_actual_worth', 'avg_projected_ca']
    for col in numeric_columns:
        if col in df.columns:
            df[col] = df[col].round(2)

    return df