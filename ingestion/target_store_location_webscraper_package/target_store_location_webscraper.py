import boto3
import datetime 
import json 
import requests
from random_header_generator import HeaderGenerator

def lambda_handler(event, context):
    generator = HeaderGenerator()

    ingestion_datetime = datetime.datetime.utcnow()

    env = 'production'
    s3_bucket_name = f'inflation-price-tracker-{env}'

    s3 = boto3.client('s3')

    stores = {}
    s3_key_prefix = f'ingestion/raw/locations/country=US/'
    existing_locations_response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_key_prefix)
    target_stores_data = None
    target_stores_json = None
    if existing_locations_response['KeyCount'] > 0:
        target_locations_files = sorted([file['Key'] for file in existing_locations_response['Contents'] if 'target' in file['Key']])
        if len(target_locations_files) > 0:
            latest_target_locations_file = target_locations_files[-1]
            print(f'Found existing target locations file {latest_target_locations_file} in {s3_bucket_name} under {s3_key_prefix}.')
            target_stores_data = s3.get_object(Bucket=s3_bucket_name, Key=latest_target_locations_file)
            print(f'Read data from existing target locations file {latest_target_locations_file} in {s3_bucket_name} under {s3_key_prefix}.')
            target_stores_json = target_stores_data['Body'].readlines()
        else: 
            print(f'No existing target locations data found in {s3_bucket_name} under {s3_key_prefix}. Please investigate.')
    else:
        print(f'No existing target locations data found in {s3_bucket_name} under {s3_key_prefix}. Please investigate.')

    if target_stores_json is not None:
        stores = json.loads(target_stores_json[0])
        print(f'Read {len(stores.keys())} stores info.')
    else:
        print('No existing target stores data found.')

    for store_id in range(max(list(stores.keys())), 3600):
        if store_id % 100 == 0:
            print(f'Finished retrieving data for stores with id: {store_id}.')
        if str(store_id) not in stores.keys():
            headers = generator()
            stores_locations_api_url = f'https://redsky.target.com/redsky_aggregations/v1/web/store_location_v1?store_id={store_id}&key=9f36aeafbe60771e321a7cc95a78140772ab3e96&visitor_id=0196569BE874020187481D35502016A6&channel=WEB&page=%2Fp%2FA-14901126'
            stores_locations_response = requests.get(stores_locations_api_url, headers=headers)
            stores_data = stores_locations_response.json()
            if 'data' in stores_data and 'store' in stores_data['data']:
                stores[store_id] = stores_data['data']['store']
                stores[store_id]['ingestion_datetime'] = ingestion_datetime.isoformat()
            elif 'errors' in stores_data:
                print(f'Request failed on store_id {store_id}')
                break
    print("Finished retrieving stores data.")

    file_content = json.dumps(stores).encode('utf-8')
    stores_s3_output_filepath = s3_key_prefix + f'{datetime.date.today()}_target_stores.json'
    print(f'Writing {len(list(stores.keys()))} stores info to {stores_s3_output_filepath} now.')
    s3.put_object(Body=file_content, Bucket=s3_bucket_name, Key=stores_s3_output_filepath)
    print(f'Successfully wrote to {stores_s3_output_filepath}.')