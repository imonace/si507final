import avl
import credentials
import json
import requests
import redis
from flask import Flask

app = Flask('Electric Charger Finder')
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.route('/')
def index():
    return f'''<!DOCTYPE html>
<html>
  <head>
    <title>ECF</title>

    <link rel="stylesheet" type="text/css" href="/static/style.css" />
    <script src="/static/index.js"></script>
  </head>
  <body>
    <h3>Electric Charger Finder</h3>
    <!--The div element for the map -->
    <div id="map"></div>

    <!-- Async script executes immediately and must be after any DOM elements used in callback. -->
    <script
      src="https://maps.googleapis.com/maps/api/js?key={credentials.GMAP_API_KEY}&callback=initMap&v=weekly"
      async
    ></script>
  </body>
</html>'''



def get_user_location():
    while True:
        try:
            location = input("Enter your location or ZIP code to get the nearest gas stations: ")
            if location == '':
                raise ValueError
            return location
        except:
            print("Please enter a valid location!")
            continue


def get_stations_from_cache(location, limit='10'):
    # see if cache is available and up to date
    data = r.get(location)
    if data is None:
        data = query_nrel_api(location, limit)
        status = r.set(location, json.dumps(data), ex=120)  # 604800 cache for up to a week
        print("Cache miss, querying NREL API, caching results status:", status)
        return data
    else:
        return json.loads(data)


def query_nrel_api(location, limit='10'):
    # request data from NREL API
    base_url = 'https://developer.nrel.gov/api/alt-fuel-stations/v1/nearest.json?'
    params = {
        'api_key': credentials.NREL_API_KEY,
        'location': location,
        'fuel_type': 'ELEC',    #
        'status': 'E',          # only show stations that are available
        'access': 'public',     # only show public stations
        'limit': limit
    }
    return requests.get(base_url, params).json()


def get_connector_type():
    while True:
        try:
            connector_type = int(input("Select your EV connector type (1: Tesla  2: J1772): "))
            if connector_type == 1:
                return 'TESLA'
            elif connector_type == 2:
                return 'J1772'
            else:
                raise ValueError
        except:
            print("Please enter 1 or 2!")
            continue


def format_station_data(station):
    # get user connector type first
    connector_type = get_connector_type()
    # then filter for available stations
    # available_station = [x for x in station['fuel_stations'] if connector_type in x['ev_connector_types']]
    # available_station.sort(key=lambda x: x['distance'])
    # now construct tree structure for user access
    myTree = avl.AVLTree()
    root = None
    for station in station['fuel_stations']:
        root = myTree.insert_node(root, station['distance'], station)
    # myTree.printHelper(root)


def show_command_line():
    print("Electric Charger Finder")
    print("Command Line Interface")
    print("-----------------------")
    print("1. Get nearest stations")
    print("2. Quit")
    print("-----------------------")


def show_map_interactive():
    pass

def show_map_static():
    pass

def show_route_static():
    pass


def main():

    
    location = get_user_location()
    station = get_stations_from_cache(location)
    results = format_station_data(station)

    r.save() # persist cache to disk before exiting
    

if __name__ == "__main__":
    main()
    #print('starting Flask app', app.name)  
    #app.run(debug=True)
