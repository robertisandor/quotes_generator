import requests
import datetime 
import json 
import boto3
from boto3 import Session
from random_header_generator import HeaderGenerator

generator = HeaderGenerator()
headers = generator()

env = 'production'
s3_bucket_name = f'inflation-price-tracker-{env}'

ingestion_datetime = datetime.datetime.utcnow()
retailer = 'target'
s3_key_prefix = f'ingestion/raw/year={ingestion_datetime.year}/month={ingestion_datetime.month}/day={ingestion_datetime.day}/'
# TODO: see if I can populate tcins for categories in a better way than manually
tcins = ['86918585', '87956594', '86918586', '14901126']

session = Session()
credentials = session.get_credentials()
current_credentials = credentials.get_frozen_credentials()

s3 = boto3.client('s3', 
                  aws_access_key_id=current_credentials.access_key, 
                  aws_secret_access_key=current_credentials.secret_key)

# read existing Target stores file
stores = {}
stores_s3_filepath = 'ingestion/raw/year=2025/month=5/day=1/country=US/target_stores.json'
target_stores_data = s3.get_object(Bucket=s3_bucket_name, Key=stores_s3_filepath)
target_stores_json = target_stores_data['Body'].readlines()

for line in target_stores_json:
    stores = stores | json.loads(line)

api_urls = []
for store_id in list(stores.keys())[:3]:
    for tcin in tcins:
        api_urls.append({'store': stores[store_id], 'tcin': tcin, 'url': f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&is_bot=false&store_id={store_id}&pricing_store_id={store_id}&has_pricing_store_id=true&has_financing_options=true&include_obsolete=true&visitor_id=0196569BE874020187481D35502016A6&skip_personalized=true&skip_variation_hierarchy=true&channel=WEB&page=%2Fp%2FA-86918585'})

products = {}

for api_url in api_urls:
    # Send GET request to the API
    response = requests.get(api_url['url'], headers=headers)
    data = response.json()
    country = api_url['store']['country_code']
    state = api_url['store']['region']

    if 'data' in data and 'product' in data['data']:
        # Extract relevant product data
        product = {
            'price': data["data"]["product"]["price"]["current_retail"],
            'regular_price': data["data"]["product"]["price"]["reg_retail"],
            'retailer_name': 'target',
            'retailer_store_location_address_line1': api_url['store']['address_line1'],
            'retailer_store_location_postal_code': api_url['store']['postal_code'],
            'retailer_store_location_city': api_url['store']['city'],
            'retailer_store_location_state': state,
            'retailer_store_location_country_code': country, 
            'retailer_store_location_id': data["data"]["product"]["price"]["location_id"],
            'url': data["data"]["product"]["item"]["enrichment"]["buy_url"],
            'weight': data["data"]["product"]["item"]["package_dimensions"]["weight"],
            'weight_unit_of_measure': data["data"]["product"]["item"]["package_dimensions"]["weight_unit_of_measure"],
            'brand': data["data"]["product"]["item"]["primary_brand"]["name"],
            'title': data["data"]["product"]["item"]["product_description"]["title"],
            'upc_barcode': data["data"]["product"]["item"]['primary_barcode'],
            'category': data["data"]["product"]["category"]["name"],
            'timestamp': datetime.datetime.utcnow().isoformat()
        }
        if country not in products:
            products[country] = {}
        if state not in products[country]:
            products[country][state] = []
        products[country][state].append(product)
    elif 'errors' in data and data['errors'][0]['message'] == 'Not Found':
        # this likely pops up because i'm being rate-limited by the store location api
        print(f"tcin: {api_url['tcin']} not available in store with store_id: {api_url['store']}")
        continue
    else:
        print(data)
        break

filenames = {}

for country in products:
    for state in products[country]:
        # write files locally
        filename = f'{datetime.date.today()}_{country}_{state}_{retailer}.json'
        with open(filename, 'w') as local_file:
            for product in products[country][state]:
                json.dump(product, local_file)
                local_file.write('\n')
        filenames[filename] = s3_key_prefix + f'country={country}/state={state}/{filename}'
print(filenames)

for filename in filenames.keys():
    s3_key = filenames[filename]
    response = s3.upload_file(filename, s3_bucket_name, s3_key)