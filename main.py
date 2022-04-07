import cache
import credentials
import datetime
import requests
from flask import Flask

app = Flask('Electric Charger Finder')

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

CACHE_DICT = {}

def get_user_input_zipcode():
    while True:
        try:
            zipcode = str(int(input("Enter your ZIP code to get the nearest gas stations: ")))
            if len(zipcode) != 5:
                raise ValueError
            return zipcode
        except:
            print("Please enter a valid 5 digits ZIP code!")
            continue

def get_nearest_stations(location, limit='10'):
    # see if cache is available and up to date(with in a week)
    if location in CACHE_DICT.keys():
        last_update = datetime.datetime.fromtimestamp(CACHE_DICT[location]['last_update'])
        now = datetime.datetime.now()
        if (now - last_update).days < 7:
            print("Using cached data")
            return CACHE_DICT[location]
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
    response = requests.get(base_url, params)
    data = response.json()
    data['last_update'] = datetime.datetime.now().timestamp()
    CACHE_DICT[location] = data
    return CACHE_DICT[location]

def request_googlemap_api(term):
    pass

def format_station_data(station):
    pass

def main():
    global CACHE_DICT
    CACHE_DICT = cache.open_cache()
    zipcode = get_user_input_zipcode()
    station = get_nearest_stations(zipcode)
    results = format_station_data(station)
    cache.save_cache(CACHE_DICT)

if __name__ == "__main__":
    #main()
    #print('starting Flask app', app.name)  
    app.run(debug=True)
