import cache
import datetime
import requests
import secrets

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

def get_nearest_stations(location):
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
        'api_key': secrets.NREL_API_KEY,
        'location': location,
        'fuel_type': 'ELEC',    #
        'status': 'E',          # only show stations that are available
        'access': 'public',     # only show public stations
        'limit': '3'
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
    cache.save_cache(CACHE_DICT)

if __name__ == "__main__":
    main()