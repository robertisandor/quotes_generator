
import boto3 
from datetime import datetime
import io
import json 
import pyarrow as pa
import pyarrow.parquet as pq

def lambda_handler(event, context):
    env = 'production'
    s3_bucket_name = f'inflation-price-tracker-{env}'

    s3 = boto3.client('s3')

    products = {}
    s3_key_input_prefix = f'ingestion/raw/products/country=US/'
    s3_key_output_prefix = f'ingestion/transformed/products/country=US/'
    existing_locations_response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_key_input_prefix)
    target_products_data = None
    target_products_json = None
    if existing_locations_response['KeyCount'] > 0:
        target_products_files = sorted([file['Key'] for file in existing_locations_response['Contents'] if 'target' in file['Key']])
        if len(target_products_files) > 0:
            latest_target_products_files = target_products_files[-1]
            print(f'Found existing target locations file {latest_target_products_files} in {s3_bucket_name} under {s3_key_input_prefix}.')
            target_products_data = s3.get_object(Bucket=s3_bucket_name, Key=latest_target_products_files)
            print(f'Read data from existing target locations file {latest_target_products_files} in {s3_bucket_name} under {s3_key_input_prefix}.')
            target_products_json = target_products_data['Body'].readlines()
        else: 
            print(f'No existing target products data found in {s3_bucket_name} under {s3_key_input_prefix}. Please investigate.')
    else:
        print(f'No existing target products data found in {s3_bucket_name} under {s3_key_input_prefix}. Please investigate.')

    if target_products_json is not None:
        products = json.loads(target_products_json[0])
        print(f'Read {len(products.keys())} products info.')
    else:
        print('No existing target products data found.')

    products_output = {
        'product_id': [],
        'company_product_id': [],
        'product_title': [],
        'url': [],
        'company_product_id_alternative': [],
        'product_title_alternative': [],
        'url_alternative': [],
        'retailer_name': [],
        'parent_retailer_company_name': [],
        'ingestion_datetime': []
    }

    schema = pa.schema([
        pa.field('product_id', pa.int64()),
        pa.field('company_product_id', pa.int64()),
        pa.field('product_title', pa.string()),
        pa.field('url', pa.string()),
        pa.field('company_product_id_alternative', pa.int64()),
        pa.field('product_title_alternative', pa.string()),
        pa.field('url_alternative', pa.string()),
        pa.field('retailer_name', pa.string()),
        pa.field('parent_retailer_company_name', pa.string()),
        pa.field('ingestion_datetime', pa.timestamp('ms', tz='UTC'))
    ])
    print(f'schema: {schema}')

    counter = 0
    for product_id in products.keys():
        ingestion_datetime = datetime.strptime(products[product_id]['ingestion_datetime'], '%Y-%m-%dT%H:%M:%S.%f')

        products_output['product_id'].append(counter)
        products_output['product_title'].append(products[product_id]['item']['product_description']['title'])
        products_output['company_product_id'].append(int(product_id))
        products_output['url'].append(products[product_id]['item']['enrichment']['buy_url'])

        if 'parent' not in products[product_id]:
            products_output['company_product_id_alternative'].append(None)
            products_output['product_title_alternative'].append(None)
            products_output['url_alternative'].append(None)
        else:
            products_output['company_product_id_alternative'].append(int(products[product_id]['parent']['tcin']))
            products_output['product_title_alternative'].append(products[product_id]['parent']['item']['product_description']['title'])
            products_output['url_alternative'].append(products[product_id]['parent']['item']['enrichment']['buy_url'])

        products_output['retailer_name'].append('Target')
        products_output['parent_retailer_company_name'].append('Target')
        products_output['ingestion_datetime'].append(ingestion_datetime)

        counter += 1
        if counter % 100 == 0:
            print(f'Finished transforming data for store with product_id: {product_id}. counter: {counter}')
            
    print("Finished transforming products data.")

    target_products_table = pa.Table.from_pydict(products_output, schema)
    print(f'Created table of {len(products.keys())} products info.')
    parquet_buffer = io.BytesIO()
    pq.write_table(target_products_table, parquet_buffer)
    parquet_buffer.seek(0)
    print(f'Wrote table to parquet buffer.')
    products_s3_output_filepath = s3_key_output_prefix + f'target_products.parquet'
    print(f'Writing {len(products_output["product_id"])} products info to {products_s3_output_filepath} now.')
    s3.put_object(Body=parquet_buffer, Bucket=s3_bucket_name, Key=products_s3_output_filepath)
    print(f'Successfully wrote to {products_s3_output_filepath}.')