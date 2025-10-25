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
    # data.product_summaries[x].tcin
    # potential alternative
    # https://redsky.target.com/redsky_aggregations/v1/web/plp_search_v2?key=9f36aeafbe60771e321a7cc95a78140772ab3e96&channel=WEB&count=24&default_purchasability_filter=true&include_dmc_dmr=true&include_sponsored=true&include_review_summarization=false&keyword=baby+formula&new_search=true&offset=0&page=%2Fs%2Fbaby+formula&platform=desktop&pricing_store_id=321&scheduled_delivery_store_id=321&spellcheck=true&store_ids=321%2C1122%2C322%2C1472%2C2584&useragent=Mozilla%2F5.0+%28Macintosh%3B+Intel+Mac+OS+X+10_15_7%29+AppleWebKit%2F537.36+%28KHTML%2C+like+Gecko%29+Chrome%2F136.0.0.0+Safari%2F537.36&visitor_id=0196D611DAF202018C6B162B6F6FDA42&zip=94070
    # data.search.products[x].tcin
    tcins = ['86918585', '87956594', '86918586', '14901126']

    session = Session()
    credentials = session.get_credentials()
    current_credentials = credentials.get_frozen_credentials()

    s3 = boto3.client('s3')

    # read existing Target stores file
    # stores = {}
    # stores_s3_filepath = f'ingestion/raw/locations/country=US/target_stores.json'
    # target_stores_data = s3.get_object(Bucket=s3_bucket_name, Key=stores_s3_filepath)
    # target_stores_json = target_stores_data['Body'].readlines()
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

    for store_dict in json.loads(target_stores_json[0]):
        stores.update(store_dict)
    print(f'Number of stores: {len(list(stores.keys()))}')

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
        if 'region' not in stores[store]:
            print(f'No region for store: {store}')
            break
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
    total_error_count = 0
    # pull data from API
    for state in list(stores_by_state.keys()):
        state_error_count = 0
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
                    state_error_count += 1
                    print(f"tcin: {api_url['tcin']} not available in store with store_id: {api_url['store']['store_id']}")
                    continue
                else:
                    print(data)
                    break
        print(f'error count for {state}: {state_error_count}')
        total_error_count += state_error_count
    print('finished retrieving product data')
    print(f'total error count: {total_error_count}')

    # write files to s3
    for country in products:
        for state in products[country]:        
            filename = f'{datetime.date.today()}_{country}_{state}_{retailer}.json'
            s3_key = s3_key_prefix + f'country={country}/region={state}/{filename}'
            file_content = json.dumps(products[country][state]).encode('utf-8')
            s3.put_object(Body=file_content, Bucket=s3_bucket_name, Key=s3_key)
            print(f'wrote {filename} to s3')
