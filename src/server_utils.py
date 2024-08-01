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
import smtplib
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


def remove_lonely_dash(d):
    """
    For each key in the dictionary d, if the value corresponding to the key is a dictionary
    that contains only one key and that key is "-", update the value of the key to be the value
    corresponding to "-".
    """
    for key, value in list(d.items()): 
        if isinstance(value, dict):
            remove_lonely_dash(value)
        if isinstance(value, dict) and (len(value) == 1 or (len(value)==2 and 'means' in value)) and "-" in value:
            d[key] = value["-"]
    return d

# Function to replace NaN with None
def replace_nan_with_none(value):
    if pd.isna(value):
        return None
    else:
        return value

def calculate_CA(row, year_diff,last_year = 2023):
    # Capital Appreciattion calculation
    #calculate_CA(row, 5) to calculate the capital appr over 5 years
    price_new = row[f'AVG_meter_price_{last_year}']
    price_old = row[f'AVG_meter_price_{last_year-year_diff}']
    if pd.notna(price_new) and pd.notna(price_old) and price_new != 0 and price_old != 0:
        return (price_new - price_old) / price_old
    else:
        return np.nan


    
def calculate_CA_from_array(row, year_diff):
    avg_meter_price = row['avg_meter_price_2013_2023']

    current_year_index = 2023 - 2013  # This is the index for the year 2023 in the array.
    target_year_index = current_year_index - year_diff  # Calculate the index for the target year.

    # If avg_meter_price is an array, check if all elements are NaN.
    # If so, or if avg_meter_price itself is NaN, return np.nan.
    if isinstance(avg_meter_price, np.ndarray) or isinstance(avg_meter_price, list):
        if np.isnan(avg_meter_price).all():
            return np.nan
        elif 0 <= target_year_index < len(avg_meter_price):
            price_new = row['avg_meter_price_2013_2023'][current_year_index]  # Price for 2023
            price_old = row['avg_meter_price_2013_2023'][target_year_index]  # Price for the target year
            
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

    # Iterate over the years from 2013 to 2023
    for year in range(2013, 2024):
        # Calculate the average for the current year
        yearly_average = df[df['instance_year'] == year]['meter_sale_price'].mean()
        # Handle case where there might be no data for a year, ensuring it's a float NaN
        if pd.isna(yearly_average):
            yearly_average = float('nan')
        averages.append(yearly_average)

    # Create a DataFrame with a single row containing the averages array
    result_df = pd.DataFrame([averages], columns=[f'Year_{year}' for year in range(2013, 2024)])
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

def conditional_avg_array(df, group, start_year=2013, end_year=2023, threshold=5):
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

    # Replace all NaN values with None
    #combined_averages_df_transposed = combined_averages_df_transposed.replace(np.nan, None)

    # Convert rows to arrays or None
    # Convert rows to arrays, replacing NaN with None in the process
    # result_series = combined_averages_df.apply(
    #     lambda x: [value if not pd.isnull(value) else None for value in x.values] if not all(x.isnull()) else None, axis=1
    # ).rename('avg_meter_price_2013_2023')
    
    result_series = combined_averages_df_transposed.apply(
        lambda x: [value if not np.isnan(value) else None for value in x.values] if not np.isnan(x.values).all() else None, 
        axis=1
    ).rename('avg_meter_price_2013_2023')

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
            "internaldemand2023" : float(item["internaldemand2023"]),
            "externaldemand2023" : float(item["externaldemand2023"]),
            "externalDemandYears": []
        }
        
        # Assuming the years go from 2018 to 2023 for each project
        # Also assuming there's no data for years before 2018, so they will be filled with 0.0
        for year in range(2018, 2024):
            key = f"externaldemand{year}"
            project_data["externalDemandYears"].append(float(item.get(key, 0.0)))
            
        transformed_data.append(project_data)
    return transformed_data