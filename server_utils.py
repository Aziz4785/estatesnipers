import math
from decimal import Decimal
import pandas as pd
import numpy as np

def get_min_max(valid_prices):
    if valid_prices:
        min_price, max_price = min(valid_prices), max(valid_prices)
    else:
        min_price, max_price = None, None 
    return min_price,max_price

def get_color(price, min_price, max_price):
    # Normalize price to a 0-1 scale
    normalized_price = (price - min_price) / (max_price - min_price)
    
    if normalized_price < 0.4:
        # Gradient from (0, 0, 255) to (185, 185, 255)
        a= (0-185)/(0-0.4)
        red = green = int(a*normalized_price)
        blue = 255
    else:
        # Gradient from (255, 185, 185) to (255, 0, 0)
        a= (185-0)/(0.4-1)
        blue = green = int(a*normalized_price +(185 - a*0.4))
        red = 255
    
    # Construct the color string
    color_string = f"rgb({red}, {green}, {blue})"
    return color_string


def transform_generic_aggregate(data, hierarchy_keys):
    # this function is not used
    def insert_into_dict(target_dict, keys, value):
        """Recursively insert value into target_dict based on the given keys."""
        if len(keys) == 0: #new
            target_dict["means"]=[value] #new
        elif len(keys) == 1:
            key = keys[0]
            # Ensure the final value is stored in a list to aggregate multiple entries
            if key not in target_dict:
                #target_dict[key] = [value]  # Initialize as a list with one dict
                target_dict[key] = {}
                insert_into_dict(target_dict[key], keys[1:], value) #new
            else:
                target_dict[key].append(value)  # Append to the existing list
        else:
            key = keys[0]
            if key not in target_dict:
                target_dict[key] = {}
            # Recursive call with the next level of the hierarchy
            insert_into_dict(target_dict[key], keys[1:], value)
    
    result = {}

    #data is a list of dict
    for item in data:
        #value_dict contains the metrics we want , it could be : {'avgCapitalAppreciation2018': '0.10', 'avg_roi': '-', 'avgCapitalAppreciation2013': '0.47'} 
        value_dict = {k: v for k, v in item.items() if k not in hierarchy_keys}
        hierarchy_values = [item.get(key) for key in hierarchy_keys if key in item]
        insert_into_dict(result, hierarchy_values, value_dict)
    
    return result

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

def calculate_CA(row, year_diff):
    # Capital Appreciattion calculation
    #calculate_CA(row, 5) to calculate the capital appr over 5 years
    price_new = row[f'AVG_meter_price_2023']
    price_old = row[f'AVG_meter_price_{2023-year_diff}']
    if pd.notna(price_new) and pd.notna(price_old) and price_new != 0 and price_old != 0:
        return (price_new - price_old) / price_old
    else:
        return np.nan


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

def conditional_avg(df, group,year, threshold=5):
    """Compute conditional average based on the year and a threshold for counts."""
    # Filter rows for the specified year with valid meter_sale_price values
    filtered_df = df[(df['instance_year'] == year) & df['meter_sale_price'].notnull()]
    
    result = filtered_df.groupby(group, dropna=False)['meter_sale_price'].agg(lambda x: x.mean() if len(x) > threshold else np.nan)
    
    return result