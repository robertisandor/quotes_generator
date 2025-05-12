import json 
import requests
from random_header_generator import HeaderGenerator

# safeway api for stores
# https://www.safeway.com/abs/pub/xapi/storeresolver/storeaddress?storeid=3132
# safeway product api?
# https://www.safeway.com/abs/pub/xapi/pgmsearch/v1/search/products?request-id=2471746771000191511&url=https://www.safeway.com&pageurl=https://www.safeway.com&pagename=search&rows=30&start=0&search-type=keyword&storeid=3132&featured=true&q=baby%20formula&sort=&dvid=web-4.1search&channel=instore&wineshopstoreid=5799&timezone=America/Los_Angeles&zipcode=94611&visitorId=&pgm=intg-search,wineshop,merch-banner&banner=safeway

generator = HeaderGenerator()

stores_filename = 'albertsons_stores.json'
stores = {}
try: 
    with open(stores_filename) as f:
        for line in f:
            stores = stores | json.loads(line)
except FileNotFoundError:
    pass

with open(stores_filename, 'a') as local_file:
    for store_id in range(1, 5):
        if str(store_id) not in stores.keys():
            headers = generator()
            stores_locations_api_url = f'https://www.safeway.com/abs/pub/xapi/storeresolver/storeaddress?storeid={store_id}'
            stores_locations_response = requests.get(stores_locations_api_url, headers=headers)
            stores_data = stores_locations_response.json()
            if 'storeAddressModel' in stores_data:
                local_file.write(json.dumps({store_id: stores_data['storeAddressModel']['address'], 'retailer_name': stores_data['storeAddressModel']['storeRewards']['storeName']}))
                local_file.write('\n')
            elif 'errors' in stores_data:
                print(f'Request failed on store_id {store_id}')
                break