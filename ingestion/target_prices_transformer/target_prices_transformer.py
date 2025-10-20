
import boto3 
from datetime import datetime
from decimal import Decimal
import io
import json 
import pyarrow as pa
import pyarrow.parquet as pq

def lambda_handler(event, context):
    env = 'production'
    s3_bucket_name = f'inflation-price-tracker-{env}'

    s3 = boto3.client('s3')

    year = event.get('year')
    month = event.get('month')
    day = event.get('day')
    country = event.get('country')
    region = event.get('region')
    store_id = event.get('store_id')

    day_formatted = day.zfill(2)
    month_formatted = month.zfill(2)

    prices = {}
    s3_key_input_prefix = f'ingestion/raw/prices/year={year}/month={month}/day={day}/country={country}/region={region}/{year}-{month_formatted}-{day_formatted}_{country}_{region}_{store_id}'
    s3_key_output_prefix = f'ingestion/transformed/prices/ingestion_date={year}-{month_formatted}-{day_formatted}/country={country}/region={region}/{year}-{month_formatted}-{day_formatted}_{country}_{region}_{store_id}_'
    existing_prices_response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_key_input_prefix)
    target_prices_data = None
    target_prices_json = None
    if existing_prices_response['KeyCount'] > 0:
        target_prices_files = sorted([file['Key'] for file in existing_prices_response['Contents'] if 'target' in file['Key']])
        if len(target_prices_files) > 0:
            latest_target_prices_files = target_prices_files[-1]
            print(f'Found existing target prices file {latest_target_prices_files} in {s3_bucket_name} under {s3_key_input_prefix}.')
            target_prices_data = s3.get_object(Bucket=s3_bucket_name, Key=latest_target_prices_files)
            print(f'Read data from existing target prices file {latest_target_prices_files} in {s3_bucket_name} under {s3_key_input_prefix}.')
            target_prices_json = target_prices_data['Body'].readlines()
        else: 
            print(f'No existing target prices data found in {s3_bucket_name} under {s3_key_input_prefix}. Please investigate.')
    else:
        print(f'No existing target prices data found in {s3_bucket_name} under {s3_key_input_prefix}. Please investigate.')

    if target_prices_json is not None:
        prices = json.loads(target_prices_json[0])
        print(f'Read {len(prices)} prices info.')
    else:
        print('No existing target prices data found.')

    prices_output = {
        'store_id': [],
        'company_product_id': [],
        'parent_company_product_id': [],
        'url': [],
        'current_retail_price': [],
        'regular_retail_price': [],
        'dimension_unit_of_measure': [],
        'depth': [],
        'height': [],
        'width': [],
        'weight_unit_of_measure': [],
        'weight': [],
        'product_vendors': [],
        'retailer_name': [],
        'parent_retailer_company_name': [],
    }

    schema = pa.schema([
        pa.field('store_id', pa.int64()),
        pa.field('company_product_id', pa.int64()),
        pa.field('parent_company_product_id', pa.int64()),
        pa.field('url', pa.string()),
        pa.field('current_retail_price', pa.decimal128(7, 2)),
        pa.field('regular_retail_price', pa.decimal128(7, 2)),
        pa.field('dimension_unit_of_measure', pa.string()),
        pa.field('depth', pa.float32()),
        pa.field('height', pa.float32()),
        pa.field('width', pa.float32()),
        pa.field('weight_unit_of_measure', pa.string()),
        pa.field('weight', pa.float32()),
        pa.field('product_vendors', pa.string()),
        pa.field('retailer_name', pa.string()),
        pa.field('parent_retailer_company_name', pa.string())
    ])
    print(f'schema: {schema}')

    counter = 0
    for product in prices:
        ingestion_date = datetime.strptime(f'{year}-{month_formatted}-{day_formatted}', '%Y-%m-%d').date()

        if 'children' in product:
            for child in product['children']:
                prices_output['store_id'].append(int(store_id))
                prices_output['company_product_id'].append(int(child['tcin']))
                prices_output['parent_company_product_id'].append(int(product['tcin']))
                prices_output['url'].append(child['item']['enrichment']['buy_url'])
                if 'price' in child:
                    prices_output['current_retail_price'].append(round(Decimal(child['price']['current_retail']), 2))
                    prices_output['regular_retail_price'].append(round(Decimal(child['price']['reg_retail']), 2))
                else:
                    prices_output['current_retail_price'].append(None)
                    prices_output['regular_retail_price'].append(None)
                prices_output['dimension_unit_of_measure'].append(child['item']['package_dimensions']['dimension_unit_of_measure'])
                prices_output['depth'].append(child['item']['package_dimensions']['depth'])
                prices_output['height'].append(child['item']['package_dimensions']['height'])
                prices_output['width'].append(child['item']['package_dimensions']['width'])
                prices_output['weight_unit_of_measure'].append(child['item']['package_dimensions']['weight_unit_of_measure'])
                prices_output['weight'].append(child['item']['package_dimensions']['weight'])
                if 'product_vendors' in child['item']:
                    prices_output['product_vendors'].append('|'.join([vendor['vendor_name'] for vendor in child['item']['product_vendors']]))
                else:
                    prices_output['product_vendors'].append(None)
                prices_output['retailer_name'].append('Target')
                prices_output['parent_retailer_company_name'].append('Target')
                counter += 1
        else:
            prices_output['store_id'].append(int(store_id))
            prices_output['company_product_id'].append(int(product['tcin']))
            prices_output['parent_company_product_id'].append(None)
            prices_output['url'].append(product['item']['enrichment']['buy_url'])
            if 'price' in product:
                prices_output['current_retail_price'].append(round(Decimal(product['price']['current_retail']), 2))
                prices_output['regular_retail_price'].append(round(Decimal(product['price']['reg_retail']), 2))
            else:
                prices_output['current_retail_price'].append(None)
                prices_output['regular_retail_price'].append(None)
            prices_output['dimension_unit_of_measure'].append(product['item']['package_dimensions']['dimension_unit_of_measure'])
            prices_output['depth'].append(product['item']['package_dimensions']['depth'])
            prices_output['height'].append(product['item']['package_dimensions']['height'])
            prices_output['width'].append(product['item']['package_dimensions']['width'])
            prices_output['weight_unit_of_measure'].append(product['item']['package_dimensions']['weight_unit_of_measure'])
            prices_output['weight'].append(product['item']['package_dimensions']['weight'])
            if 'product_vendors' in product['item']:
                prices_output['product_vendors'].append('|'.join([vendor['vendor_name'] for vendor in product['item']['product_vendors']]))
            else:
                prices_output['product_vendors'].append(None)
            prices_output['retailer_name'].append('Target')
            prices_output['parent_retailer_company_name'].append('Target')
            counter += 1

        if counter % 100 == 0:
            print(f'Finished transforming data for price. counter: {counter}')
            
    print("Finished transforming prices data.")

    target_prices_table = pa.Table.from_pydict(prices_output, schema=schema)
    print(f'Created table of {len(prices_output["store_id"])} prices info.')
    parquet_buffer = io.BytesIO()
    pq.write_table(target_prices_table, parquet_buffer)
    parquet_buffer.seek(0)
    print(f'Wrote table to parquet buffer.')
    prices_s3_output_filepath = s3_key_output_prefix + f'target_prices.parquet'
    print(f'Writing {len(prices_output["company_product_id"])} prices info to {prices_s3_output_filepath} now.')
    s3.put_object(Body=parquet_buffer, Bucket=s3_bucket_name, Key=prices_s3_output_filepath)
    print(f'Successfully wrote to {prices_s3_output_filepath}.')