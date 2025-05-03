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
    retailer = 'target'
    s3_key_prefix = f'ingestion/raw/year={ingestion_datetime.year}/month={ingestion_datetime.month}/day={ingestion_datetime.day}/'
    # TODO: see if I can populate tcins for categories in a better way than manually
    tcins = ['86918585', '87956594', '86918586', '14901126']

    session = Session()
    credentials = session.get_credentials()
    current_credentials = credentials.get_frozen_credentials()

    s3 = boto3.client('s3')

    # read existing Target stores file
    stores = {}
    stores_s3_filepath = f'ingestion/raw/year={ingestion_datetime.year}/month={ingestion_datetime.month}/day=1/country=US/target_stores.json'
    target_stores_data = s3.get_object(Bucket=s3_bucket_name, Key=stores_s3_filepath)
    target_stores_json = target_stores_data['Body'].readlines()
    print(f'Number of stores: {len(target_stores_json)}')

    for line in target_stores_json:
        stores = stores | json.loads(line)

    api_urls = []
    for store_id in list(stores.keys()):
        for tcin in tcins:
            api_urls.append({'store': stores[store_id], 'tcin': tcin, 'url': f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&is_bot=false&store_id={store_id}&pricing_store_id={store_id}&has_pricing_store_id=true&has_financing_options=true&include_obsolete=true&visitor_id=0196569BE874020187481D35502016A6&skip_personalized=true&skip_variation_hierarchy=true&channel=WEB&page=%2Fp%2FA-86918585'})
    print(f'Number of api urls: {len(api_urls)}')

    products = {}

    # pull data from API
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
            # organize products by country and state
            country = api_url['store']['country_code']
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
    print('finished retrieving product data')

    # write files to s3
    for country in products:
        for state in products[country]:        
            filename = f'{datetime.date.today()}_{country}_{state}_{retailer}.json'
            s3_key = s3_key_prefix + f'country={country}/state={state}/{filename}'
            file_content = json.dumps(products[country][state]).encode('utf-8')
            s3.put_object(Body=file_content, Bucket=s3_bucket_name, Key=s3_key)
            print(f'wrote {filename} to s3')
