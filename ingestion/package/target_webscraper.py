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
    # https://redsky.target.com/redsky_aggregations/v1/web/product_summary_with_fulfillment_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcins=86918585%2C86918586%2C88379079%2C88392075%2C88379077%2C91113072%2C91113074%2C91113073%2C92274834%2C88198408%2C90780399&store_id=299&zip=91335&state=CA&latitude=34.200&longitude=-118.540&scheduled_delivery_store_id=288&paid_membership=false&base_membership=false&card_membership=false&required_store_id=299&skip_price_promo=true&visitor_id=0196B3A112720201A125BFE3266679FE&channel=WEB&page=%2Fs%2Fkendamil+formula
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

    uploaded_states = set()
    existing_states_response = s3.list_objects_v2(Bucket=s3_bucket_name, Prefix=s3_key_prefix)
    if existing_states_response['KeyCount'] > 0:
        for filename in [file['Key'] for file in existing_states_response['Contents']]:
            partitions = filename.split('_')
            country = partitions[1] 
            state = partitions[2]
            uploaded_states.add(state)
        print(f'States already uploaded: {uploaded_states}')
    else:
        print('No existing states')

    stores_by_state = {}
    for store in stores:
        stores[store]['store_id'] = store
        # check if the state is an existing key 
        if stores[store]['region'] not in stores_by_state and stores[store]['region'] not in uploaded_states:
            stores_by_state[stores[store]['region']] = {'stores': [stores[store]], 'api_urls': []}
        elif stores[store]['region'] in stores_by_state:
            stores_by_state[stores[store]['region']]['stores'].append(stores[store])
    print(f'Stores in each state: {stores_by_state}')
    # {'CA': {'stores': [{1: address_info, 2: address_info}]} }
           

    for state in stores_by_state:
        if state not in uploaded_states:
            for store in stores_by_state[state]['stores']:
                for tcin in tcins:
                    stores_by_state[state]['api_urls'].append({'store': store, 'tcin': tcin, 'url': f'https://redsky.target.com/redsky_aggregations/v1/web/pdp_client_v1?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&tcin={tcin}&is_bot=false&store_id={store["store_id"]}&pricing_store_id={store["store_id"]}&has_pricing_store_id=true&has_financing_options=true&include_obsolete=true&visitor_id=XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX&skip_personalized=true&skip_variation_hierarchy=true&channel=WEB&page=%2Fp%2FA-86918585'})

    products = {}

    # pull data from API
    for state in list(stores_by_state.keys()):
        if state not in uploaded_states:
            print(f'State: {state}, # of api urls: {len(stores_by_state[state]["api_urls"])}')
            for api_url in stores_by_state[state]['api_urls']:
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
