import requests
import json

def fetch_geojson(city):
    """Fetch the geojson data for a given city."""
    api_url = f"https://nominatim.openstreetmap.org/search.php?q={city}&polygon_geojson=1&format=jsonv2"
    headers = {
        'User-Agent': 'YourApp/1.0 (YourEmail@example.com)'
    }
    response = requests.get(api_url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        if data:
            for i in range(len(data)):  
                if data[i].get('geojson', None) and data[i].get('geojson', None)["type"] in {"MultiPolygon" , "Polygon"}:
                    return data[i].get('geojson', None)
    return None

with open('dubaiAreas.geojson', 'r') as dubai_file:
    dubai_areas = json.load(dubai_file)
    dubai_city_ids = {area["area_id"].lower() for area in dubai_areas}

cities_data = []
counter = 0
# Read city names from the file
with open('area_id_name.txt', 'r') as file:
    for line in file:
        # Split the line into components based on commas
        parts = line.strip().split(',')
        # Extract the city name, latitude, and longitude
        id = parts[0]
        city = parts[1].strip().lower()
        if id and id not in dubai_city_ids :
            geojson = fetch_geojson(city)
            if geojson and geojson["type"] in {"MultiPolygon" , "Polygon"}:
                print(counter)
                cities_data.append({
                    "area_id": id,
                    "name": city,
                    "geometry": geojson
                })
            else:
                print(city)

# Merge the new cities data with the existing Dubai areas data
dubai_areas.extend(cities_data)

with open('dubaiAreas.geojson', 'w') as outfile:
    json.dump(dubai_areas, outfile, indent=4)