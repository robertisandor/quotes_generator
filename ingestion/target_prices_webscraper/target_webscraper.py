import json
import requests
import datetime 
import boto3
from boto3 import Session
from random_header_generator import HeaderGenerator

def lambda_handler(event, context):
    generator = HeaderGenerator()
    headers = generator()

    env = 'production'
    s3_bucket_name = f'inflation-price-tracker-{env}'

    ingestion_datetime = datetime.datetime.utcnow()
    ingestion_date = str(datetime.date.today())
    retailer = 'target'
    s3_prices_key_prefix = f'ingestion/raw/prices/ingestion_date={ingestion_date}/country=US/'

    session = Session()
    credentials = session.get_credentials()
    current_credentials = credentials.get_frozen_credentials()

    s3 = boto3.client('s3')

    # assumption is that there is an existing target store file that has already been populated
    # read existing Target stores file
    stores = {}
    s3_locations_key_prefix = f'ingestion/raw/locations/country=US/'
    existing_locations_response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_locations_key_prefix)
    target_stores_data = None
    target_stores_json = None
    if existing_locations_response['KeyCount'] > 0:
        target_locations_files = sorted([file['Key'] for file in existing_locations_response['Contents'] if 'target' in file['Key']])
        if len(target_locations_files) > 0:
            latest_target_locations_file = target_locations_files[-1]
            print(f'Found existing target locations file {latest_target_locations_file} in {s3_bucket_name} under {s3_locations_key_prefix}.')
            target_stores_data = s3.get_object(Bucket=s3_bucket_name, Key=latest_target_locations_file)
            print(f'Read data from existing target locations file {latest_target_locations_file} in {s3_bucket_name} under {s3_locations_key_prefix}.')
            target_stores_json = target_stores_data['Body'].readlines()
        else: 
            print(f'No existing target locations data found in {s3_bucket_name} under {s3_locations_key_prefix}. Please investigate.')
    else:
        print(f'No existing target locations data found in {s3_bucket_name} under {s3_locations_key_prefix}. Please investigate.')

    if target_stores_json is not None:
        stores = json.loads(target_stores_json[0])
        print(f'Read {len(stores.keys())} stores info.')
    else:
        print('No existing target stores data found.')

    uploaded_states = set()
    for store_dict in stores:
        state = stores[store_dict]['mailing_address']['region']
        uploaded_states.add(state)
    if len(uploaded_states) > 0:
        print(f'States already uploaded: {uploaded_states}')
    else:
        print('No existing states')
           
    # assumption is that there is an existing target products file that has already been populated
    s3_products_key_prefix = f'ingestion/raw/products/country=US/'
    existing_products_response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_products_key_prefix)
    target_products_data = None
    target_products_json = None
    if existing_products_response['KeyCount'] > 0:
        target_products_files = sorted([file['Key'] for file in existing_products_response['Contents'] if 'target_products' in file['Key']])
        
        if len(target_products_files) > 0:
            latest_target_products_file = target_products_files[-1]
            print(f'Found existing target products file {latest_target_products_file} in {s3_bucket_name} under {s3_products_key_prefix}.')
            target_products_data = s3.get_object(Bucket=s3_bucket_name, Key=latest_target_products_file)
            print(f'Read data from existing target products file {latest_target_products_file} in {s3_bucket_name} under {s3_products_key_prefix}.')
            target_products_json = target_products_data['Body'].readlines()
        else: 
            print(f'No existing target products data found in {s3_bucket_name} under {s3_products_key_prefix}. Please investigate.')
    else:
        print(f'No existing target products data found in {s3_bucket_name} under {s3_products_key_prefix}. Please investigate.')

    products = {}
    if target_products_json is not None:
        products = json.loads(target_products_json[0])
        print(f'Read {len(products.keys())} products info.')
    else:
        print('No existing target products data found.')

    

    prices_output = {}
    for store_id in stores:
        state = stores[store_id]['mailing_address']['region']

        # look for existing prices files so I can append to them rather than overwrite them and not waste api calls
        s3_prices_key_prefix = f'ingestion/raw/prices/ingestion_date={ingestion_date}/country=US/region={state}/'
        existing_prices_response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_prices_key_prefix)
        target_prices_data = None
        target_prices_json = None
        if existing_prices_response['KeyCount'] > 0:
            target_prices_files = sorted([file['Key'] for file in existing_prices_response['Contents'] if f'_{store_id}_' in file['Key']])
            
            if len(target_prices_files) > 0:
                target_prices_data = s3.get_object(Bucket=s3_bucket_name, Key=target_prices_files[-1])
                print(f'Read data from existing target prices file {target_prices_files[-1]} in {s3_bucket_name} under {s3_prices_key_prefix}.')
                target_prices_json = target_prices_data['Body'].readlines()
            else: 
                print(f'No existing target prices data found in {s3_bucket_name} under {s3_prices_key_prefix}. Please investigate.')
        else:
            print(f'No existing target prices data found in {s3_bucket_name} under {s3_prices_key_prefix}. Please investigate.')

        prices = []
        if target_prices_json is not None:
            prices = json.loads(target_prices_json[0])
            print(f'Read {len(prices.keys())} prices info.')
        else:
            print('No existing target prices data found.')

        # get prices info 
        # prices_output = {3: {product_1, product_2}, 4: {}}
        prices_output[store_id] = {}
        prices_output[store_id].update(prices)
        counter = 0
        for product_id, product in list(products.items()):
            # I want to be able to determine this condition easily;
            # to do that, I need to make 
            if product_id not in prices_output[store_id]:
                tcin = product['tcin']
                url = f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&is_bot=false&store_id={store_id}&pricing_store_id={store_id}&has_pricing_store_id=true&has_financing_options=true&include_obsolete=true&visitor_id=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX&skip_personalized=true&skip_variation_hierarchy=true&channel=WEB&page=%2Fp%2FA-86918585'
                headers = generator()
                response = requests.get(url, headers=headers)
                if 'data' in response.json():
                    prices_output[store_id][product_id] = response.json()
                else:
                    print(f'no data for product {product_id} in store {store_id}')
                    print(response.json())
                counter += 1
            if counter > 0 and counter % 100 == 0:
                print(f'processed {counter} products for store {store_id}')
            if counter > 0 and counter % 2000 == 0:
                break

        # write output of the store's prices to S3 
        filename = f'{ingestion_date}_US_{state}_{store_id}_{retailer}.json'
        s3_prices_key = s3_prices_key_prefix + f'{filename}'
        print(f'writing {len(prices_output[store_id])} price(s) info to s3 at {s3_prices_key}')
        file_content = json.dumps(prices_output[store_id]).encode('utf-8')
        s3.put_object(Body=file_content, Bucket=s3_bucket_name, Key=s3_prices_key)
        print(f'wrote {filename} to s3 at location {s3_prices_key}')
