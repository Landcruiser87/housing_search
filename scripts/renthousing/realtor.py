import logging
from bs4 import BeautifulSoup
import json
import requests
import time
from typing import Union

def get_listings(resp_json:dict, neigh:str, source:str, Propertyinfo)->list:
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
    listingid = price = beds = sqft = lat = long = baths = pets = url = address = current_time = None
    #Set the outer loop over each card returned. 
    for rental in resp_json["data"]["home_search"]["properties"]:
        #Get the propertyid
        listingid = rental.get("property_id")

        # Time of pull
        current_time = time.strftime("%m-%d-%Y_%H-%M-%S")

        #First grab the link.
        url = "https://" + source + "/rentals/details/" + rental.get("permalink")

        price = rental.get("list_price")
        
        #well shit.  Looks like beds and bath is nested in any number of different fields.  Will need to scan them, isolate values and return the highest
        for category in ["bed", "bath", "sqft"]: #my hands wanted to type bed bath and beyond.  Lol
            res = []
            for key in rental["description"].keys():
                if category in key and rental["description"].get(key) is not None:
                    res.append(rental["description"].get(key))
            if category == "bed":
                if res:
                    beds = float(sorted(res)[0], reverse=True)
            elif category == "bath":
                if res:
                    baths = float(sorted(res)[0], reverse=True)
            elif category == "sqft":
                if res:
                    sqft = float(sorted(res)[0], reverse=True)
        
        lat = rental["location"]["address"]["coordinate"]["lat"]
        long = rental["location"]["address"]["coordinate"]["lon"]
        addy = rental["location"]["address"].get("line") + " " + rental["location"]["address"].get("city") + ", " + rental["location"]["address"].get("state_code") + " " + rental["location"]["address"].get("postal_code")
        address = addy.strip()

        #Pets is already secured in the search query so we don't have to confirm it in the data.
        pets = True

        listing = Propertyinfo(
            id=listingid,
            source=source,
            price=price,
            neigh=neigh.lower(),
            bed=beds,
            sqft=sqft,
            lat=lat,
            long=long,
            bath=baths,
            dogs=pets,
            link=url,
            address=address,
            date_pulled=current_time
        )
        listings.append(listing)
        listingid = price = beds = sqft = lat = long = baths = pets = url = address = current_time = None
    return listings

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

def neighscrape(neigh:Union[str, int], source:str, logger:logging, Propertyinfo, srch_par)->list:
    """[Outer scraping function to set up request pulls]

    Args:
        neigh (Union[str,int]): Neighborhood or zipcode searched
        source (str): What site is being scraped
        logger (logging.logger): logger for Kenny loggin
        Propertyinfo (dataclass): Custom data object
        srch_par (tuple): Tuple of search parameters

    Returns:
        property_listings (list): List of dataclass objects
    """    
    CITY = srch_par[0]
    STATE = srch_par[1].upper()
    MINBEDS = int(srch_par[2])
    MAXRENT = int(srch_par[3])
    PETS = srch_par[4]
    #Search by neighborhood
    if isinstance(neigh, str):
        if " " in neigh:
            neigh = "-".join(neigh.split(" "))
        if PETS:
            url = f"https://www.realtor.com/apartments/{neigh}_{CITY}_{STATE}/type-townhome,single-family-home/beds-{MINBEDS}/price-na-{MAXRENT}/dog-friendly"#g1
        else:
            url = f"https://www.realtor.com/apartments/{neigh}_{CITY}_{STATE}/type-townhome,single-family-home/beds-{MINBEDS}/price-na-{MAXRENT}"#g1

    #Searchby ZipCode
    elif isinstance(neigh, int):
        if PETS:
            url = f"https://www.realtor.com/apartments/{neigh}/type-townhome,single-family-home/beds-{MINBEDS}/price-na-{MAXRENT}/dog-friendly"#g1
        else:
            url = f"https://www.realtor.com/apartments/{neigh}/type-townhome,single-family-home/beds-{MINBEDS}/price-na-{MAXRENT}"#g1
    
    #Error Trapping
    else:
        logging.critical("Inproper input for area, moving to next site")
        return None
    
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',
        'origin': 'https://www.realtor.com',
        'priority': 'u=1, i',
        'rdc-client-name': 'RDC_WEB_SRP_FR_PAGE',
        'rdc-client-version': '3.x.x',
        'referer': url,
        'sec-ch-ua': '"Chromium";v="120", "Not:A-Brand";v="24", "Google Chrome";v="120"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'srp-consumer-triggered-request': 'rdc-search-for-rent',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
        'x-is-bot': 'false',
    }

    json_data = {
        'operationName': 'ConsumerSearchQuery',
        'variables': {
            'query': {
                'primary': True,
                'status': [
                    'for_rent',
                ],
                'search_location': {
                    'location': f'{neigh}, {CITY}, {STATE}',
                },
                'beds': {
                    'min': MINBEDS,
                },
                'type': [
                    'townhomes',
                    'condo_townhome_rowhome_coop',
                    'duplex_triplex',
                    'condo_townhome',
                    'single_family']
                ,
                'dogs': True,
                'list_price': {
                    'max': MAXRENT,
                },
            },
            'limit': 42,
            'offset': 0,
            'bucket': {
                'sort': 'fractal_v1.1.3_fr',
            },
        },
        'query': 'query ConsumerSearchQuery($query: HomeSearchCriteria!, $limit: Int, $offset: Int, $sort: [SearchAPISort], $bucket: SearchAPIBucket, $search_promotion: SearchPromotionInput) {\n  home_search(\n    query: $query\n    sort: $sort\n    limit: $limit\n    offset: $offset\n    bucket: $bucket\n    search_promotion: $search_promotion\n  ) {\n    costar_counts {\n      costar_total\n      non_costar_total\n      __typename\n    }\n    total\n    count\n    search_promotion {\n      name\n      names\n      slots\n      promoted_properties {\n        id\n        from_other_page\n        __typename\n      }\n      __typename\n    }\n    properties: results {\n      property_id\n      listing_id\n      list_price\n      list_price_max\n      list_price_min\n      permalink\n      price_reduced_amount\n      matterport\n      has_specials\n      application_url\n      rentals_application_eligibility {\n        accepts_applications\n        __typename\n      }\n      search_promotions {\n        name\n        asset_id\n        __typename\n      }\n      virtual_tours {\n        href\n        __typename\n      }\n      status\n      list_date\n      lead_attributes {\n        lead_type\n        is_premium_ldp\n        is_schedule_a_tour\n        __typename\n      }\n      pet_policy {\n        cats\n        dogs\n        dogs_small\n        dogs_large\n        __typename\n      }\n      other_listings {\n        rdc {\n          listing_id\n          status\n          __typename\n        }\n        __typename\n      }\n      flags {\n        is_pending\n        __typename\n      }\n      photos(limit: 3, https: true) {\n        href\n        __typename\n      }\n      primary_photo(https: true) {\n        href\n        __typename\n      }\n      advertisers {\n        type\n        office {\n          name\n          phones {\n            number\n            type\n            primary\n            trackable\n            ext\n            __typename\n          }\n          __typename\n        }\n        phones {\n          number\n          type\n          primary\n          trackable\n          ext\n          __typename\n        }\n        rental_management {\n          fulfillment_id\n          customer_set\n          name\n          logo\n          href\n          __typename\n        }\n        __typename\n      }\n      flags {\n        is_new_listing\n        __typename\n      }\n      location {\n        address {\n          line\n          city\n          coordinate {\n            lat\n            lon\n            __typename\n          }\n          country\n          state_code\n          postal_code\n          __typename\n        }\n        county {\n          name\n          fips_code\n          __typename\n        }\n        __typename\n      }\n      description {\n        beds\n        beds_max\n        beds_min\n        baths_min\n        baths_max\n        baths_consolidated\n        garage\n        garage_min\n        garage_max\n        sqft\n        sqft_max\n        sqft_min\n        name\n        sub_type\n        type\n        year_built\n        __typename\n      }\n      units {\n        availability {\n          date\n          __typename\n        }\n        description {\n          baths_consolidated\n          baths\n          beds\n          sqft\n          __typename\n        }\n        list_price\n        __typename\n      }\n      branding {\n        type\n        photo\n        name\n        __typename\n      }\n      source {\n        id\n        community_id\n        type\n        feed_type\n        __typename\n      }\n      details {\n        category\n        text\n        parent_category\n        __typename\n      }\n      products {\n        products\n        brand_name\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}',
}

    response = requests.post('https://www.realtor.com/frontdoor/graphql', headers=headers, json=json_data)

    #BUG - 
        #I think some apts might be getting in.  Check tomorrow. 

    # BASE_HEADERS = {
    #     'accept': '*/*',
    #     'accept-language': 'en-US,en;q=0.9',
    #     'referer': url,
    #     'origin':'https://www.realtor.com',
    #     'priority': 'u=1, i',
    #     'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="120", "Chromium";v="120"',
    #     'sec-ch-ua-mobile': '?1',
    #     'sec-ch-ua-platform': '"Android"',
    #     'sec-fetch-dest': 'empty',
    #     'sec-fetch-mode': 'cors',
    #     'sec-fetch-site': 'cross-site',
    #     'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
    # }
          
    # response = requests.get(url, headers=BASE_HEADERS)

    #Just in case we piss someone off
    if response.status_code != 200:
        # If there's an error, log it and return no data for that site
        logger.warning(f'Status code: {response.status_code}')
        logger.warning(f'Reason: {response.reason}')
        return None

    #Get the HTML
    resp_json = response.json()

    # Isolate the property-list from the expanded one (I don't want the 3 mile
    # surrounding.  Just the neighborhood)
    count = resp_json["data"]["home_search"].get("total", "")
    if count > 0:
        property_listings = get_listings(resp_json, neigh, source, Propertyinfo)
        logger.info(f'{len(property_listings)} listings returned from {source}')
        return property_listings
        
    else:
        logger.warning("No listings returned on realtor.  Moving to next site")
    