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

    # tcins = ['86918585', '87956594', '86918586', '14901126']

    session = Session()
    credentials = session.get_credentials()

    s3 = boto3.client('s3')
    s3_key_prefix = f'ingestion/raw/products/country=US/'
    
    products = {}
    invalid_product_ids = []

    existing_products_response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_key_prefix)
    target_products_data = None
    target_products_json = None
    target_invalid_product_ids_data = None
    target_invalid_product_ids_json = None
    if existing_products_response['KeyCount'] > 0:
        target_products_files = sorted([file['Key'] for file in existing_products_response['Contents'] if 'target_products' in file['Key']])
        target_invalid_product_ids_files = sorted([file['Key'] for file in existing_products_response['Contents'] if 'target_invalid_product_ids' in file['Key']])
        
        if len(target_products_files) > 0:
            latest_target_products_file = target_products_files[-1]
            print(f'Found existing target products file {latest_target_products_file} in {s3_bucket_name} under {s3_key_prefix}.')
            target_products_data = s3.get_object(Bucket=s3_bucket_name, Key=latest_target_products_file)
            print(f'Read data from existing target products file {latest_target_products_file} in {s3_bucket_name} under {s3_key_prefix}.')
            target_products_json = target_products_data['Body'].readlines()
        else: 
            print(f'No existing target products data found in {s3_bucket_name} under {s3_key_prefix}. Please investigate.')
        
        if len(target_invalid_product_ids_files) > 0:
            latest_target_invalid_product_ids_file = target_invalid_product_ids_files[-1]
            print(f'Found existing target invalid product ids file {latest_target_invalid_product_ids_file} in {s3_bucket_name} under {s3_key_prefix}.')
            target_invalid_product_ids_data = s3.get_object(Bucket=s3_bucket_name, Key=latest_target_invalid_product_ids_file)
            print(f'Read data from existing target invalid product ids file {latest_target_invalid_product_ids_file} in {s3_bucket_name} under {s3_key_prefix}.')
            target_invalid_product_ids_json = target_invalid_product_ids_data['Body'].readlines()
        else: 
            print(f'No existing target invalid product ids data found in {s3_bucket_name} under {s3_key_prefix}. Please investigate.')
    else:
        print(f'No existing target products (valid or invalid) data found in {s3_bucket_name} under {s3_key_prefix}. Please investigate.')

    if target_products_json is not None:
        products = json.loads(target_products_json[0])
        print(f'Read {len(products.keys())} products info.')
    else:
        print('No existing target products data found.')

    if target_invalid_product_ids_json is not None:
        invalid_product_ids = json.loads(target_invalid_product_ids_json[0])
        print(f'Read {len(invalid_product_ids)} invalid product ids info.')
    else:
        print('No existing target invalid product ids data found.')

    start_product_id = 14901126
    if len(products.keys()) > 0:
        start_product_id = max([int(product_id) for product_id in list(products.keys()) + list(invalid_product_ids)])

    tcin_batch_query_amount = 5
    # create the upper limit for testing and runtime considerations
    tcin_query_limit = 100
    tcin_query_count = 0
    # create an error limit to prevent running for too long when it isn't working
    tcin_error_limit = 50
    tcin_error_count = 0
    current_product_id = start_product_id
    # check if we've queried the amount of tcins we want
    while (tcin_query_count < tcin_query_limit) and (tcin_error_count < tcin_error_limit):
        tcins = []
        # query tcins in batches of tcin_batch_query_amount to speed up process
        while len(tcins) < tcin_batch_query_amount:
            # we don't want to query invalid product ids or product ids that we've already queried
            if str(current_product_id) not in invalid_product_ids and str(current_product_id) not in products.keys():
                tcins.append(str(current_product_id))
            current_product_id += 1
        # we should have a list of tcins to query, so we create the tcin portion of the query, then make the request
        tcin_string = '%2C'.join(tcins)
        products_api_url = f'https://redsky.target.com/redsky_aggregations/v1/web/product_summary_with_fulfillment_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcins={tcin_string}'
        headers = generator()
        products_response = requests.get(products_api_url, headers=headers)
        products_data = products_response.json()
        if 'data' in products_data and 'product_summaries' in products_data['data']:
            for product in products_data['data']['product_summaries']:
                products[product['tcin']] = product
                products[product['tcin']]['ingestion_datetime'] = ingestion_datetime.isoformat()
                tcin_query_count += 1
        if 'errors' in products_data:
            new_invalid_product_ids = [error['message'].split(' ')[-1] for error in products_data['errors']]
            print(f'Found {len(new_invalid_product_ids)} invalid product ids.')
            print(f'Invalid product ids: {new_invalid_product_ids}')
            invalid_product_ids.extend(new_invalid_product_ids)
            tcin_error_count += len(new_invalid_product_ids)
        if current_product_id % 100 == 0:
            print(f'Finished retrieving data for products with id: {current_product_id}.')
        current_product_id = max([int(tcin) for tcin in tcins]) + 1
    print("Finished retrieving products data.")

    file_content = json.dumps(products).encode('utf-8')
    products_s3_output_filepath = s3_key_prefix + f'{datetime.date.today()}_target_products.json'
    print(f'Writing {len(list(products.keys()))} products info to {products_s3_output_filepath} now.')
    s3.put_object(Body=file_content, Bucket=s3_bucket_name, Key=products_s3_output_filepath)
    print(f'Successfully wrote to {products_s3_output_filepath}.')

    invalid_product_id_file_content = json.dumps(sorted(list(set(invalid_product_ids)))).encode('utf-8')
    invalid_product_ids_s3_output_filepath = s3_key_prefix + f'{datetime.date.today()}_target_invalid_product_ids.json'
    print(f'Writing {len(invalid_product_ids)} invalid product ids to {invalid_product_ids_s3_output_filepath} now.')
    s3.put_object(Body=invalid_product_id_file_content, Bucket=s3_bucket_name, Key=invalid_product_ids_s3_output_filepath)
    print(f'Successfully wrote to {invalid_product_ids_s3_output_filepath}.')