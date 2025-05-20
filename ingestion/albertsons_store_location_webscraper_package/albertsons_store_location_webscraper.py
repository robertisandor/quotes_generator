import boto3
import datetime 
import json 
import requests
from random_header_generator import HeaderGenerator

def lambda_handler(event, context):
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
    s3_key_prefix = f'ingestion/raw/locations/country=US/'
    existing_locations_response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_key_prefix)
    albertsons_stores_data = None
    albertsons_stores_json = None
    if existing_locations_response['KeyCount'] > 0:
        albertsons_locations_files = sorted([file['Key'] for file in existing_locations_response['Contents'] if 'albertsons' in file['Key']])
        if len(albertsons_locations_files) > 0:
            latest_albertsons_locations_file = albertsons_locations_files[-1]
            print(f'Found existing albertsons locations file {latest_albertsons_locations_file} in {s3_bucket_name} under {s3_key_prefix}.')
            albertsons_stores_data = s3.get_object(Bucket=s3_bucket_name, Key=latest_albertsons_locations_file)
            print(f'Read data from existing albertsons locations file {latest_albertsons_locations_file} in {s3_bucket_name} under {s3_key_prefix}.')
            albertsons_stores_json = albertsons_stores_data['Body'].readlines()
        else: 
            print(f'No existing albertsons locations data found in {s3_bucket_name} under {s3_key_prefix}. Please investigate.')
    else:
        print(f'No existing albertsons locations data found in {s3_bucket_name} under {s3_key_prefix}. Please investigate.')

    if albertsons_stores_json is not None:
        stores = json.loads(albertsons_stores_json[0])
        print(f'Read {len(stores.keys())} stores info.')
    else:
        print('No existing albertsons stores data found.')

    start_store_id = 1
    if len(stores.keys()) > 0:
        start_store_id = max([int(store_id) for store_id in list(stores.keys())])
        
    for store_id in range(start_store_id, start_store_id + 2000):
        if store_id % 100 == 0:
            print(f'Finished retrieving data for stores with id: {store_id}.')
        if str(store_id) not in stores.keys():
            headers = generator()
            stores_locations_api_url = f'https://www.safeway.com/abs/pub/xapi/storeresolver/storeaddress?storeid={store_id}'
            stores_locations_response = requests.get(stores_locations_api_url, headers=headers)
            stores_data = stores_locations_response.json()
            if 'storeAddressModel' in stores_data:
                # stores[store_id] = {'address': stores_data['storeAddressModel']['address'], 'parent_retailer_company_name': 'Albertsons', 'retailer_name': stores_data['storeAddressModel']['storeRewards']['storeName']}
                stores[store_id] = stores_data['storeAddressModel']
                stores[store_id]['ingestion_datetime'] = ingestion_datetime.isoformat()
            elif 'errors' in stores_data:
                print(f'Request failed on store_id {store_id}')
                break
    print("Finished retrieving stores data.")

    file_content = json.dumps(stores).encode('utf-8')
    stores_s3_output_filepath = s3_key_prefix + f'{datetime.date.today()}_albertsons_stores.json'
    print(f'Writing {len(list(stores.keys()))} stores info to {stores_s3_output_filepath} now.')
    s3.put_object(Body=file_content, Bucket=s3_bucket_name, Key=stores_s3_output_filepath)
    print(f'Successfully wrote to {stores_s3_output_filepath}.')