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



def get_connector_type():
    while True:
        try:
            connector_type = int(input("Select your EV connector type (1: TESLA  2: J1772): "))
            if connector_type == 1:
                return 'TESLA'
            elif connector_type == 2:
                return 'J1772'
            else:
                raise ValueError
        except:
            print("Please enter 1 or 2!")
            continue


def get_user_option():
    while True:
        try:
            return int(input("Enter your option: "))
        except:
            print("Please enter a valid number!")
            continue


def get_user_location():
    while True:
        try:
            location = input("Please enter your location or ZIP code: ")
            if location == '':
                raise ValueError
            return location
        except:
            print("Please enter a valid location!")
            continue


def get_results_from_cache(location, limit='50'):
    # see if cache is available and up to date
    data = r.get(location)
    if data is None:
        print("Cache miss, querying NREL API, please wait...")
        data = query_nrel_api(location, limit)
        r.set(location, json.dumps(data), ex=120)  # 604800 seconds, cache for up to a week
        return data
    else:
        print("Cache hit, returning cached data...")
        return json.loads(data)


def query_nrel_api(location, limit):
    # request data from NREL API
    base_url = 'https://developer.nrel.gov/api/alt-fuel-stations/v1/nearest.json?'
    params = {
        'api_key': credentials.NREL_API_KEY,
        'location': location,
        'radius': '50.0',
        'fuel_type': 'ELEC',    #
        'status': 'E',          # only show stations that are available
        'access': 'public',     # only show public stations
        'limit': limit
    }
    return requests.get(base_url, params).json()


def format_station_tree(station, connector_type):
    # filter for available stations
    available_station = [x for x in station['fuel_stations'] if connector_type in x['ev_connector_types']]
    print(f"Found {len(available_station)} available stations nearby.")

    # now construct tree structure for user access
    myTree = avl.AVLTree()
    root = None
    for available_station in available_station['fuel_stations']:
        root = myTree.insert_node(root, available_station['distance'], available_station)

    # myTree.printHelper(root)
    return myTree, root


def show_result_command_line(myTree, root):
    myTree.printHelper(root)


def show_map_interactive():
    pass

def show_map_static():
    pass

def show_route_static():
    pass


def main():
    connector_type = 'TESLA' # default connector type to Tesla
    print("----------------------------------")
    print("Welcome to Electric Charger Finder")

    while True:
        print("----------------------------------")
        print("1. Get nearby EV charging stations")
        print(f"2. Set EV connector type (current: {connector_type})")
        print("3. Quit")
        option = get_user_option()
        print("----------------------------------")

        if option == 1:
            
            location = get_user_location()
            results = get_results_from_cache(location)
            myTree, root = format_station_tree(results, connector_type)
            
            while True:
                print("----------------------------------")
                print("1. Show stations in command line")
                print("2. Show result in interactive map")
                print("3. Show route to nearest station")
                print("4. Print result tree (debug)")
                print("5. Back")
                option = get_user_option()
                print("----------------------------------")

                if option == 1:
                    show_result_command_line(myTree, root)
                elif option == 2:
                    show_map_interactive()
                elif option == 3:
                    show_route_static()
                elif option == 4:
                    myTree.printHelper(root)
                elif option == 5:
                    break
                else:
                    print("Please select a valid option!")
                    continue

        
        elif option == 2:
            connector_type = get_connector_type()
            print(f"EV connector type set to {connector_type}.")

        elif option == 3:
            print("Quitting...")
            r.save() # persist cache to disk before quitting
            print("Goodbye!")
            break

        else:
            print("Please select a valid option!")
            continue
    

if __name__ == "__main__":
    #print('starting Flask app', app.name)  
    #app.run(debug=True)
    main()
    
