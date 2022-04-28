import avl
import credentials
import json
import logging
import requests
import redis
import webbrowser
import time
from multiprocessing import Process
from flask import Flask, render_template, request
from PIL import Image

app = Flask('Electric Charger Finder')
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

@app.route('/')
def index():
    loc = request.args.get('loc')
    locTitle = request.args.get('locTitle')
    locString = request.args.get('locString')
    return render_template('index.html',api_key=credentials.GMAP_API_KEY, loc=loc, locTitle=locTitle, locString=locString)

@app.route('/direction')
def direction():
    start = request.args.get('start')
    end = request.args.get('end')
    return render_template('direction.html',api_key=credentials.GMAP_API_KEY, start=start, end=end)


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


def get_results_from_cache(location):
    # see if cache is available and up to date
    try:
        data = r.get(location)
        if data is None:
            print("Cache miss, querying NREL API, please wait...")
            data = query_nrel_api(location)
            r.set(location, json.dumps(data), ex=604800)  # 604800 seconds before expire, cache for up to a week
            return data
        else:
            print("Cache hit, returning cached data...")
            return json.loads(data)
    except:
        print("Cache server down, querying NREL API, please wait...")
        data = query_nrel_api(location)
        return data


def query_nrel_api(location):
    # request data from NREL API
    base_url = 'https://developer.nrel.gov/api/alt-fuel-stations/v1/nearest.json?'
    params = {
        'api_key': credentials.NREL_API_KEY,
        'location': location,
        'radius': '50.0',
        'fuel_type': 'ELEC',    #
        'status': 'E',          # only show stations that are available
        'access': 'public',     # only show public stations
        'limit': '50'           # limit to 50 results
    }
    return requests.get(base_url, params).json()


def format_station_tree(results, connector_type):
    # filter for available stations
    available_stations = [x for x in results['fuel_stations'] if connector_type in x['ev_connector_types']]
    print(f"Found {len(available_stations)} available stations nearby.")

    # now construct tree structure for user access
    myTree = avl.AVLTree()
    root = None
    for station in available_stations[0:9]: # only show first 9 stations because of google static map api limit
        root = myTree.insert_node(root, station['distance'], station)

    # myTree.printHelper(root)
    return myTree, root


def select_station(myTree, root):
    while True:
        try:
            id = int(input("Please enter the id of preferred station: "))
            node = myTree.traverse_search(root, id)
            if node is None:
                raise ValueError
            return node
        except:
            print("Please enter a valid id!")
            continue


def show_map_static(myTree, root):
    coor = ''
    for node in myTree.traverse(root):
        coor += f"{node.data['latitude']},{node.data['longitude']}|"
    base_url = 'https://maps.googleapis.com/maps/api/staticmap?'
    params = {
        'key': credentials.GMAP_API_KEY,
        'size': '640x480',
        'format': 'png',
        'markers': [],
    }
    i = 1
    for node in myTree.traverse(root):
        params['markers'].append( f"color:red|label:{i}|{node.data['latitude']},{node.data['longitude']}|" )
        i += 1
    with open("staticmap.png", "wb") as f:
        f.write(requests.get(base_url, params).content)
    im = Image.open("staticmap.png")
    im.show()


def show_station_interactive(dest):
    base = 'http://127.0.0.1:5000/?'
    loc = 'loc=' + str(dest['latitude']) + ',' + str(dest['longitude']) + '&'
    locTitle = 'locTitle=' + dest['station_name'].replace('&','') + '&'
    locString = 'locString=' + '<p><b>Name: ' + dest['station_name'].replace('&','') + '</b></p>'\
                             + '<p>Address: ' + dest['street_address'] + '</p>'\
                             + '<p>City: ' + dest['city'] + '</p>'\
                             + '<p>ZIP: ' + dest['zip'] + '</p>'\
                             + '<p>Phone: ' + dest['station_phone'] + '</p>'\
                             + '<p>Hours of operation: ' + dest['access_days_time'] + '</p>'\
                             + '<p>Pricing: ' + dest['ev_pricing'] + '</p>'
    uri = base + loc + locTitle + locString
    webbrowser.open(uri)


def core_function():
    connector_type = 'TESLA' # default connector type to Tesla
    print("----------------------------------")
    print("Welcome to Electric Charger Finder")

    while True:
        print("----------------------------------")
        print("1. Get nearby EV charging stations")
        print("2. Set EV connector type (current: {})".format(connector_type))
        print("3. Quit")
        option = get_user_option()
        print("----------------------------------")

        if option == 1:
            
            location = get_user_location()
            results = get_results_from_cache(location)

            start = {'lat': results['latitude'], 'lng': results['longitude']}

            myTree, root = format_station_tree(results, connector_type)
            
            node = myTree.getMinValueNode(root)
            dest = node.data
            end = {'lat': dest['latitude'], 'lng': dest['longitude']}

            printed = False

            while True:
                print("----------------------------------")
                print("1. Show results in command line")
                print("2. Show results in picture")
                print("   Current selected: {}".format(dest['station_name']))
                print("3. Select a different station")
                print("4. Show detailed information of selected station")
                print("5. Show route to the selected station")
                print("6. Print tree data structure (debug)")
                print("7. Back")
                option = get_user_option()
                #print("----------------------------------")

                if option == 1:
                    myTree.traverse_print(root)
                    printed = True
                elif option == 2:
                    show_map_static(myTree, root)
                elif option == 3:
                    if not printed:
                        myTree.traverse_print(root)
                        printed = True
                    node = select_station(myTree, root)
                    dest = node.data
                    end = {'lat': dest['latitude'], 'lng': dest['longitude']}
                elif option == 4:
                    show_station_interactive(dest)
                elif option == 5:
                    webbrowser.open(f"http://127.0.0.1:5000/direction?start={start['lat']},{start['lng']}&end={end['lat']},{end['lng']}")
                elif option == 6:
                    myTree.printHelper(root)
                elif option == 7:
                    break
                else:
                    print("Please select a valid option!")
                    continue
        
        elif option == 2:
            connector_type = get_connector_type()
            print(f"EV connector type set to {connector_type}.")

        elif option == 3:
            r.save() # persist cache to disk before quitting
            break

        else:
            print("Please select a valid option!")
            continue
    

def start_server():
    # start flask server
    print('Starting Flask app', app.name)
    app.run(debug=True, use_reloader=False)

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def main():
    #app.run(debug=True)
    t = Process(target=start_server)
    t.start()
    time.sleep(1)
    core_function()
    print("Quitting...")
    print('Exiting Flask app', app.name)
    print("Goodbye!")
    t.terminate()
    t.join()

if __name__ == "__main__":
    main()
    #show_map_static()

