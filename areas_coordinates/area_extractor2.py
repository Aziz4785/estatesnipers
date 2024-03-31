import requests
from bs4 import BeautifulSoup
import json
import time

def fetch_geojson(city,coord1,coord2):
    url = f'https://global.mapit.mysociety.org/point/4326/{coord1},{coord2}.html'
    response = requests.get(url)

    if response.status_code == 200:
        # # Find the second <li> in <ol class="area_list">
        # second_li = soup.select_one('ol.area_list > li:nth-of-type(2) a')
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find all <li> elements within <ol class="area_list">, then filter for the one containing the specific <p> text
        li_with_boundary_level_8 = soup.find('ol', class_='area_list').find(lambda tag: tag.name == 'li' and 'Boundary Level 8' in tag.text)

        if li_with_boundary_level_8:
            a_tag = li_with_boundary_level_8.find('a')
            href = a_tag['href']
            full_url = f'https://global.mapit.mysociety.org{href[:-5]}.geojson?simplify_tolerance=0.0001'

            geojson_response = requests.get(full_url)

            if geojson_response.status_code == 200:
                data = geojson_response.json()
                if data:
                    return data
            else:
                print('Failed to fetch the GeoJSON data. Please check the URL and try again.')
                return None
        else:
            print('cant find second li')
            return None
    else:
        print("status code error")
        return None


with open('dubaiAreas.geojson', 'r') as dubai_file:
    dubai_areas = json.load(dubai_file)
    dubai_city_ids = {area["area_id"].lower() for area in dubai_areas}

cities_data = []
counter= 0
with open('area_id_name.txt', 'r') as file:
    for line in file:
        parts = line.strip().split(',')
        # Extract the city name, latitude, and longitude
        id = parts[0]
        city = parts[1].lower()
        if(len(parts)>=4):
            latitude = parts[2]
            longitude = parts[3]
            if id and id not in dubai_city_ids :
                geojson = fetch_geojson(city,longitude,latitude)
                if geojson and geojson["type"] in {"MultiPolygon" , "Polygon"}:
                    print("found : "+str(city))
                    counter+=1
                    cities_data.append({
                        "area_id":id,
                        "name": city,
                        "geometry": geojson
                    })
                else:
                    print(city)
        time.sleep(3)


# Merge the new cities data with the existing Dubai areas data
dubai_areas.extend(cities_data)

with open('dubaiAreas.geojson', 'w') as outfile:
    json.dump(dubai_areas, outfile, indent=4)