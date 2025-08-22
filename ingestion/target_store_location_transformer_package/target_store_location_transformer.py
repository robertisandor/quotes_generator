
import boto3 
import io
import json 
import pyarrow as pa
import pyarrow.parquet as pq

def lambda_handler(event, context):
    env = 'production'
    s3_bucket_name = f'inflation-price-tracker-{env}'

    s3 = boto3.client('s3')

    stores = {}
    s3_key_input_prefix = f'ingestion/raw/locations/country=US/'
    s3_key_output_prefix = f'ingestion/transformed/targets/country=US/'
    existing_locations_response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_key_input_prefix)
    target_stores_data = None
    target_stores_json = None
    if existing_locations_response['KeyCount'] > 0:
        target_locations_files = sorted([file['Key'] for file in existing_locations_response['Contents'] if 'target' in file['Key']])
        if len(target_locations_files) > 0:
            latest_target_locations_file = target_locations_files[-1]
            print(f'Found existing target locations file {latest_target_locations_file} in {s3_bucket_name} under {s3_key_input_prefix}.')
            target_stores_data = s3.get_object(Bucket=s3_bucket_name, Key=latest_target_locations_file)
            print(f'Read data from existing target locations file {latest_target_locations_file} in {s3_bucket_name} under {s3_key_input_prefix}.')
            target_stores_json = target_stores_data['Body'].readlines()
        else: 
            print(f'No existing target locations data found in {s3_bucket_name} under {s3_key_input_prefix}. Please investigate.')
    else:
        print(f'No existing target locations data found in {s3_bucket_name} under {s3_key_input_prefix}. Please investigate.')

    if target_stores_json is not None:
        stores = json.loads(target_stores_json[0])
        print(f'Read {len(stores.keys())} stores info.')
    else:
        print('No existing target stores data found.')

    stores_output = {
        'store_id': [],
        'address_line1': [],
        'city': [],
        'region': [],
        'country_code': [],
        'postal_code': [],
        'retailer_name': [],
        'parent_retailer_company_name': [],
        'ingestion_datetime': []
    }
    counter = 0
    for store_id in stores.keys():
        stores_output['store_id'].append(store_id)
        stores_output['address_line1'].append(stores[store_id]['mailing_address']['address_line1'])
        stores_output['city'].append(stores[store_id]['mailing_address']['city'])
        stores_output['region'].append(stores[store_id]['mailing_address']['region'])
        stores_output['country_code'].append(stores[store_id]['mailing_address']['country_code'])
        stores_output['postal_code'].append(stores[store_id]['mailing_address']['postal_code'])
        stores_output['retailer_name'].append('Target')
        stores_output['parent_retailer_company_name'].append('Target')
        stores_output['ingestion_datetime'].append(stores[store_id]['ingestion_datetime'])
        counter += 1
        if counter % 100 == 0:
            print(f'Finished transforming data for store with store_id: {store_id}.')
            
    print("Finished transforming stores data.")

    target_stores_table = pa.Table.from_pydict(stores_output)
    print(f'Created table of {len(stores.keys())} stores info.')
    parquet_buffer = io.BytesIO()
    pq.write_table(target_stores_table, parquet_buffer)
    parquet_buffer.seek(0)
    print(f'Wrpte table to parquet buffer.')
    stores_s3_output_filepath = s3_key_output_prefix + f'target_stores.parquet'
    print(f'Writing {len(stores_output)} stores info to {stores_s3_output_filepath} now.')
    s3.put_object(Body=parquet_buffer, Bucket=s3_bucket_name, Key=stores_s3_output_filepath)
    print(f'Successfully wrote to {stores_s3_output_filepath}.')