import boto3
import datetime 
import json 
import requests
from random_header_generator import HeaderGenerator

# safeway api for stores
# https://www.safeway.com/abs/pub/xapi/storeresolver/storeaddress?storeid=3132
# safeway product api?
# https://www.safeway.com/abs/pub/xapi/pgmsearch/v1/search/products?request-id=2471746771000191511&url=https://www.safeway.com&pageurl=https://www.safeway.com&pagename=search&rows=30&start=0&search-type=keyword&storeid=3132&featured=true&q=baby%20formula&sort=&dvid=web-4.1search&channel=instore&wineshopstoreid=5799&timezone=America/Los_Angeles&zipcode=94611&visitorId=&pgm=intg-search,wineshop,merch-banner&banner=safeway

generator = HeaderGenerator()

ingestion_datetime = datetime.datetime.utcnow()

env = 'production'
s3_bucket_name = f'inflation-price-tracker-{env}'

s3 = boto3.client('s3')

# read existing Albertsons stores file
stores = {}
s3_key_prefix = f'ingestion/raw/year={ingestion_datetime.year}/month={ingestion_datetime.month}/day=1/country=US/'
stores_s3_filepath = s3_key_prefix + 'albertsons_stores.json'
albertsons_stores_data = s3.get_object(Bucket=s3_bucket_name, Key=stores_s3_filepath)
albertsons_stores_json = albertsons_stores_data['Body'].readlines()

for line in albertsons_stores_json:
    stores = stores | json.loads(line)
# stores_filename = 'albertsons_stores.json'
# stores = {}
# try: 
#     with open(stores_filename) as f:
#         for line in f:
#             stores = stores | json.loads(line)
# except FileNotFoundError:
#     pass

# with open(stores_filename, 'a') as local_file:
#     for store_id in range(1, 5):
#         if str(store_id) not in stores.keys():
#             headers = generator()
#             stores_locations_api_url = f'https://www.safeway.com/abs/pub/xapi/storeresolver/storeaddress?storeid={store_id}'
#             stores_locations_response = requests.get(stores_locations_api_url, headers=headers)
#             stores_data = stores_locations_response.json()
#             if 'storeAddressModel' in stores_data:
#                 local_file.write(json.dumps({store_id: stores_data['storeAddressModel']['address'], 'parent_retailer_company_name': 'Albertsons', 'retailer_name': stores_data['storeAddressModel']['storeRewards']['storeName']}))
#                 local_file.write('\n')
#             elif 'errors' in stores_data:
#                 print(f'Request failed on store_id {store_id}')
#                 break


for store_id in range(1, 5):
    if str(store_id) not in stores.keys():
        headers = generator()
        stores_locations_api_url = f'https://www.safeway.com/abs/pub/xapi/storeresolver/storeaddress?storeid={store_id}'
        stores_locations_response = requests.get(stores_locations_api_url, headers=headers)
        stores_data = stores_locations_response.json()
        if 'storeAddressModel' in stores_data:
            stores.add({store_id: stores_data['storeAddressModel']['address'], 'parent_retailer_company_name': 'Albertsons', 'retailer_name': stores_data['storeAddressModel']['storeRewards']['storeName']})
        elif 'errors' in stores_data:
            print(f'Request failed on store_id {store_id}')
            break

file_content = json.dumps(stores).encode('utf-8')
stores_s3_output_filepath = f'{datetime.date.today()}_albertsons_stores.json'
s3.put_object(Body=file_content, Bucket=s3_bucket_name, Key=stores_s3_output_filepath)
