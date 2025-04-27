import json 
import requests
from random_header_generator import HeaderGenerator

generator = HeaderGenerator()

stores_filename = 'target_stores.json'
stores = {}
try: 
    with open(stores_filename) as f:
        for line in f:
            stores = stores | json.loads(line)
except FileNotFoundError:
    pass

with open(stores_filename, 'a') as local_file:
    for store_id in range(250, 2600):
        if str(store_id) not in stores.keys():
            headers = generator()
            stores_locations_api_url = f'https://redsky.target.com/redsky_aggregations/v1/web/store_location_v1?store_id={store_id}&key=9f36aeafbe60771e321a7cc95a78140772ab3e96&visitor_id=0196569BE874020187481D35502016A6&channel=WEB&page=%2Fp%2FA-14901126'
            stores_locations_response = requests.get(stores_locations_api_url, headers=headers)
            stores_data = stores_locations_response.json()
            if 'data' in stores_data and 'store' in stores_data['data']:
                local_file.write(json.dumps({stores_data['data']['store']['store_id']: stores_data['data']['store']['mailing_address']}))
                local_file.write('\n')
            elif 'errors' in stores_data:
                print(f'Request failed on store_id {store_id}')
                break