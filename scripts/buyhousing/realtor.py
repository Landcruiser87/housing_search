import time
import requests
import numpy as np
from typing import Union
import datetime
from support import logger, get_time
from dataclasses import dataclass
from main import P_LIST

def get_listings(resp_json:dict, neigh:Union[str, int], source:str, Propertyinfo)->list:
    """[Ingest HTML of summary page for listings info]

    Args:
        resp_json (dict): dictionary of neighborhoods
        neigh (str): neighorhood being searched
        source (str): Source website
        Propertyinfo (dataclass) : Dataclass for housing individual listings

    Returns:
        listings (list): [List of dataclass objects]
    """

    listings = []
    defaultval = None
    seller_keys = ["advertisers", "offeredBy", "flags", "branding"]
    #Set the outer loop over each card returned. 
    for search_result in resp_json["data"]["home_search"]["properties"]:
        listing              = Propertyinfo()
        listing.id           = search_result.get("listing_id", defaultval)
        if listing.id == None:
            logger.warning("id not found")
            continue
        
        listing.url          = "https://" + source + "/realestateandhomes-detail/" + search_result.get("permalink")
        listing.img_url      = search_result.get("primary_photo", defaultval)
        listing.status       = search_result.get("status", defaultval)
        listing.source       = source
        listing.city         = search_result["location"]["address"].get("city", defaultval)
        listing.state        = search_result["location"]["address"].get("state_code", defaultval)
        listing.zipc         = search_result["location"]["address"].get("postal_code", defaultval)
        listing.address      = search_result["location"]["address"]["line"] + ", " + listing.city + ", " + listing.state + " " + listing.zipc 
        listing.htype        = search_result["description"].get("type", defaultval)
        listing.baths        = bedbath_format(search_result["description"].get("baths_consolidated", defaultval))
        listing.beds         = bedbath_format(search_result["description"].get("beds", defaultval))
        listing.sqft         = int("".join([x for x in str(search_result["description"].get("sqft", defaultval)) if x.isnumeric()]))
        listing.lotsqft      = search_result["description"].get("lotsqft", defaultval)
        listing.year_built   = search_result["description"].get("year_built", defaultval)
        listing.price        = int(search_result.get("list_price", defaultval))
        if (listing.price !=None) & (listing.sqft != None):
            listing.price_sqft   = listing.price // int(listing.sqft)
        listing.date_pulled  = get_time().strftime("%m-%d-%Y_%H-%M-%S")
        listing.lat          = search_result["location"]["address"]["coordinate"].get("lat", defaultval)
        listing.long         = search_result["location"]["address"]["coordinate"].get("lat", defaultval)
        listing.list_dt      = date_format(search_result.get("list_date", defaultval), True)
        listing.seller       = search_result["branding"][0].get("name", defaultval)
        listing.sellerinfo   = {k:search_result.get(k, defaultval) for k in seller_keys}
        dp = listing.date_pulled.split("_")[0]
        listing.price_hist[dp] = {k:None for k in P_LIST}
        listing.price_hist[dp]["price_ch_amt"] = search_result.get("last_price_change_amount", defaultval)
        listing.price_hist[dp]["price_c_dat"] = date_format(search_result.get("last_status_change_date", defaultval))
        if isinstance(listing.price, int) & isinstance(listing.price_hist[dp]["price_ch_amt"], int):
            listing.price_hist[dp]["last_price"] = listing.price + listing.price_hist[dp]["price_ch_amt"]
            listing.price_hist[dp]["perc_change"] = (listing.price_hist[dp]["price_ch_amt"] / listing.price ) * 100
        #Previous structure
        # listing.price_ch_amt = search_result.get("last_price_change_amount", defaultval)
        # listing.price_c_dat  = date_format(search_result.get("last_status_change_date", defaultval))
        listings.append(listing)

    return listings

def date_format(sample:str, decimals:bool=False):
    if sample != None:
        if decimals:
            dt_obj = datetime.datetime.strptime(sample, "%Y-%m-%dT%H:%M:%S.%fZ")
        else:
            dt_obj = datetime.datetime.strptime(sample, "%Y-%m-%dT%H:%M:%SZ")
        return dt_obj.strftime("%m-%d-%Y_%H-%M-%S")
    else:
        return None
    
def bedbath_format(sample:str):
    if isinstance(sample, (int, float)):
        return float(sample)
    clean = "".join([x for x in sample if (x.isnumeric()) | (x == ".")])
    try:
        number = float(clean)
        return number

    except (ValueError, TypeError) as e:
        logger.warning(f"Error: Invalid input. The input must be a an int or float:\n {e}")
        return None

def money_launderer(price:list)->float:
    """[Strips dollar signs and comma from the price]

    Args:
        price (list): [list of prices as strs]

    Returns:
        price (list): [list of prices as floats]
    """	
    if isinstance(price, str):
        return float(price.replace("$", "").replace(",", ""))
    return price

def area_search(neigh:tuple|int, source:str, Propertyinfo:dataclass, srch_par:tuple)->list:
    """[Outer scraping function to set up request pulls]

    Args:
        neigh (Union[str,int]): Neighborhood or zipcode searched
        source (str): What site is being scraped
        Propertyinfo (dataclass): Custom data object
        srch_par (tuple): Tuple of search parameters

    Returns:
        property_listings (list): List of dataclass objects
    """    
    CITY = neigh[0]
    STATE = neigh[1]
    MAXPRICE = int(srch_par[0])
    MINBATHS = int(srch_par[1])
    MINBEDS = int(srch_par[2])
    
    #Search by City/State
    if isinstance(neigh, tuple):
        url = f"https://www.realtor.com/realestateandhomes-search/{CITY}_{STATE}/type-single-family-home,townhome,farms-ranches,land/beds-{MINBEDS}/baths-{MINBATHS}/price-na-{MAXPRICE}"#g1

    #TODO - Update this for zip search
    #Searchby ZipCode
    elif isinstance(neigh, int):
        url = f"https://www.realtor.com/realestateandhomes-search/{CITY}_{STATE}/type-single-family-home,townhome,farms-ranches,land/beds-{MINBEDS}/baths-{MINBATHS}/price-na-{MAXPRICE}"#g1
    
    #Error Trapping
    else:
        logger.critical("Inproper input for area, moving to next site")
        return None
    
    chrome_version = np.random.randint(120, 137)
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.realtor.com',
        'priority': 'u=1, i',
        'rdc-client-name': 'RDC_WEB_SRP_FS_PAGE',
        'rdc-client-version': '3.x.x',
        'referer': url,
        'sec-ch-ua': f'"Chromium";v={chrome_version}, "Not:A-Brand";v="24", "Google Chrome";v={chrome_version}',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'srp-consumer-triggered-request': 'rdc-search-for-sale',
        'user-agent': f'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Mobile Safari/537.36',
        'x-is-bot': 'false',
    }

    json_data = {
        'operationName': 'ConsumerSearchQuery',
        'variables': {
            'query': {
                'primary': True,
                'status': [
                    'for_sale',
                    'ready_to_build',
                ],
                'search_location': {
                    'location': f'{CITY}, {STATE}', #BUG Need ability to zip search here
                },
                'beds': {
                    'min': MINBEDS,
                },
                'baths': {
                    'max': MINBEDS,
                },
                'type': [
                    'single_family',
                    'townhomes',
                    'duplex_triplex',
                    'condo_townhome',
                    'farm',
                    'land'
                    ]
                ,
                'list_price': {
                    'max': MAXPRICE,
                },
            },
            'limit': 100,
            'offset': 0,
            'sort_type': 'relevant',
            'bucket': {
                'sort': 'fractal_v6.2.0',
            },
        },
        'query': 'query ConsumerSearchQuery($query: HomeSearchCriteria!, $limit: Int, $offset: Int, $search_promotion: SearchPromotionInput, $sort: [SearchAPISort], $sort_type: SearchSortType, $client_data: JSON, $bucket: SearchAPIBucket, $mortgage_params: MortgageParamsInput, $photosLimit: Int) {\n  home_search: home_search(\n    query: $query\n    sort: $sort\n    limit: $limit\n    offset: $offset\n    sort_type: $sort_type\n    client_data: $client_data\n    bucket: $bucket\n    search_promotion: $search_promotion\n    mortgage_params: $mortgage_params\n  ) {\n    count\n    total\n    search_promotion {\n      names\n      slots\n      promoted_properties {\n        id\n        from_other_page\n        __typename\n      }\n      __typename\n    }\n    mortgage_params {\n      interest_rate\n      __typename\n    }\n    properties: results {\n      property_id\n      list_price\n      rmn_listing_attribution\n      search_promotions {\n        name\n        asset_id\n        __typename\n      }\n      primary_photo(https: true) {\n        href\n        __typename\n      }\n      listing_id\n      matterport\n      virtual_tours {\n        href\n        type\n        __typename\n      }\n      status\n      products {\n        products\n        brand_name\n        __typename\n      }\n      source {\n        id\n        name\n        type\n        spec_id\n        plan_id\n        agents {\n          office_name\n          __typename\n        }\n        listing_id\n        __typename\n      }\n      lead_attributes {\n        show_contact_an_agent\n        market_type\n        opcity_lead_attributes {\n          cashback_enabled\n          flip_the_market_enabled\n          __typename\n        }\n        lead_type\n        ready_connect_mortgage {\n          show_contact_a_lender\n          show_veterans_united\n          __typename\n        }\n        __typename\n      }\n      community {\n        description {\n          name\n          __typename\n        }\n        property_id\n        permalink\n        advertisers {\n          office {\n            hours\n            phones {\n              type\n              number\n              primary\n              trackable\n              __typename\n            }\n            __typename\n          }\n          __typename\n        }\n        promotions {\n          description\n          href\n          headline\n          __typename\n        }\n        __typename\n      }\n      permalink\n      price_reduced_amount\n      description {\n        name\n        beds\n        baths_consolidated\n        sqft\n        lot_sqft\n        baths_max\n        baths_min\n        beds_min\n        beds_max\n        sqft_min\n        sqft_max\n        type\n        sub_type\n        sold_price\n        sold_date\n        year_built\n        garage\n        __typename\n      }\n      location {\n        street_view_url\n        address {\n          line\n          postal_code\n          state\n          state_code\n          city\n          coordinate {\n            lat\n            lon\n            __typename\n          }\n          __typename\n        }\n        county {\n          name\n          fips_code\n          __typename\n        }\n        __typename\n      }\n      open_houses {\n        start_date\n        end_date\n        __typename\n      }\n      branding {\n        type\n        name\n        photo\n        __typename\n      }\n      flags {\n        is_coming_soon\n        is_new_listing(days: 14)\n        is_price_reduced(days: 30)\n        is_foreclosure\n        is_new_construction\n        is_pending\n        is_contingent\n        __typename\n      }\n      list_date\n      photos(limit: $photosLimit, https: true) {\n        href\n        __typename\n      }\n      advertisers {\n        type\n        fulfillment_id\n        name\n        builder {\n          name\n          href\n          logo\n          fulfillment_id\n          __typename\n        }\n        email\n        office {\n          name\n          __typename\n        }\n        phones {\n          number\n          __typename\n        }\n        __typename\n      }\n      consumer_advertisers {\n        type\n        agent_id\n        name\n        __typename\n      }\n      last_status_change_date\n      last_price_change_amount\n      __typename\n    }\n    __typename\n  }\n  commute_polygon: get_commute_polygon(query: $query) {\n    areas {\n      id\n      breakpoints {\n        width\n        height\n        zoom\n        __typename\n      }\n      radius\n      center {\n        lat\n        lng\n        __typename\n      }\n      __typename\n    }\n    boundary\n    __typename\n  }\n}',
    }

    response = requests.post('https://www.realtor.com/frontdoor/graphql', headers=headers, json=json_data)

    #Just in case we piss someone off
    if response.status_code != 200:
        # If there's an error, log it and return no data for that site
        logger.warning(f'Status code: {response.status_code}')
        logger.warning(f'Reason: {response.reason}')
        return None

    #Get the JSON data
    resp_json = response.json()

    # Isolate the property-list from the expanded one (I don't want the 3 mile
    # surrounding.  Just the neighborhood)
    #Not going to expand to multi page because there probably
    #will never be more than 100 listings at at time
    count = resp_json["data"]["home_search"].get("total", 0)
    if count > 0:
        property_listings = get_listings(resp_json, neigh, source, Propertyinfo)
        logger.info(f'{len(property_listings)} listings returned from {source}')
        return property_listings
        
    else:
        logger.warning("No listings returned on realtor.  Moving to next site")
        return None