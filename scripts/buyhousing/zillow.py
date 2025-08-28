import time
import json
import requests
import numpy as np
from typing import Union
from bs4 import BeautifulSoup
from support import logger, get_time

def get_listings(result:list, neigh:str, source:str, Propertyinfo)->list:
    """[Ingest HTML of summary page for listings info]

    Args:
        result (BeautifulSoup object): html of zillow page
        neigh (str): neighorhood being searched
        source (str): Source website
        Propertyinfo (dataclass) : Dataclass for housing individual listings

    Returns:
        listings (list): [List of dataclass objects]
    """
    listings = []
    defaultval = None
    seller_keys = ["isZillowOwned", "pgapt", "info2String", "info6String", "brokerName", "marketingStatusSimplifiedCd"]
    #Set the outer loop over each card returned. 
    for listinginfo in result:
        listing              = Propertyinfo()
        listing.id           = listinginfo.get("zpid", defaultval)
        if listing.id == None:
            logger.warning("id not found")
            continue
        listing.url          = listinginfo.get("detailUrl", defaultval)
        listing.img_url      = listinginfo.get("imgSrc", defaultval)
        listing.status       = listinginfo.get("statusType", defaultval)
        if listing.status:
            listing.status = listing.status.lower()
        listing.source       = source
        listing.city         = listinginfo.get("addressCity", defaultval)
        listing.state        = listinginfo.get("addressState", defaultval)
        listing.zipc         = listinginfo.get("addressZipcode", defaultval)
        listing.address      = listinginfo.get("address", defaultval)
        listing.htype        = listinginfo["hdpData"]["homeInfo"].get("homeType", defaultval)
        listing.sqft         = "".join([x for x in str(listinginfo.get("area", defaultval)) if x.isnumeric()])
        listing.price        = int(listinginfo.get("unformattedPrice", defaultval))
        if (listing.price !=None) & (listing.sqft != None):
            listing.price_sqft   = listing.price // int(listing.sqft)
        listing.date_pulled  = get_time().strftime("%m-%d-%Y_%H-%M-%S")
        listing.description  = listinginfo.get("flexFieldText", defaultval)
        listing.daysOnZillow = listinginfo["hdpData"]["homeInfo"].get("daysOnZillow", defaultval)
        listing.lat          = float(listinginfo["latLong"].get("latitude", defaultval))
        listing.long         = float(listinginfo["latLong"].get("longitude", defaultval))
        listing.baths        = bedbath_format(listinginfo.get("beds", defaultval))
        listing.beds         = bedbath_format(listinginfo.get("baths", defaultval))
        listing.seller       = listinginfo.get("brokerName", defaultval)
        listing.sellerinfo   = {k:listinginfo.get(k, defaultval) for k in seller_keys}
        lot_val              = listinginfo["hdpData"]["homeInfo"].get("lotAreaValue", defaultval)
        lot_unit             = listinginfo["hdpData"]["homeInfo"].get("lotAreaUnit", defaultval)
        if "zestimate" in listinginfo.keys():
            listing.zestimate= int(listinginfo.get("zestimate", defaultval))
        if (lot_val!=None) & (lot_unit!=None):
            if isinstance(lot_val, float):
                lot_val = round(lot_val, 2)
            listing.lotsqft  = str(lot_val) + " " + lot_unit
        #Vars not on the page scan below
        # listing.list_dt      = date_format(search_result.get("list_date", defaultval), True)
        # listing.last_pri_cha = search_result.get("last_price_change_amount", defaultval)
        # listing.last_pri_dat = date_format(search_result.get("last_status_change_date", defaultval))
        
        listings.append(listing)
    return listings

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
    
def area_search(neigh:Union[str, int], source:str, Propertyinfo, srch_par)->list:
    """[Outer scraping function to set up request pulls]

    Args:
        neigh (Union[str,int]): City or zipcode searched
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
    chrome_version = np.random.randint(120, 137)

    BASE_HEADERS = {
        'user-agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36',
        'origin':'https://www.zillow.com',
    }

    #Search by CITY/State
    if isinstance(neigh, tuple):
        srch_terms = f"{CITY} {STATE.upper()}"
        if " " in CITY:
            CITY = "-".join(CITY.split(" "))
        url_map = f'https://www.zillow.com/{CITY}-{STATE}/for_sale/?'
        response = requests.get(url_map, headers=BASE_HEADERS)
    
    #Search by ZipCode
    elif isinstance(neigh, int):
        headers = {
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://www.zillow.com',
            'sec-ch-ua': f'"Google Chrome";v={chrome_version}, "Not-A.Brand";v="8", "Chromium";v={chrome_version}',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36',
            'x-caller-id': 'static-search-page-graphql',
        }

        params = {
            'query': f'{neigh}',
            'queryOptions': '',
            'resultType': [
                'REGIONS',
                'FORSALE',
                'RENTALS',
                'SOLD',
                'COMMUNITIES',
                'SEMANTIC_REGIONS',
            ],
            'querySource': 'MANUAL',
            'shouldSpellCorrect': 'false',
            'operationName': 'getQueryUnderstandingResults',
        }

        json_data = {
            'operationName': 'getQueryUnderstandingResults',
            'variables': {
                'query': f'{neigh}',
                'queryOptions': {
                    'maxResults': 2,
                    'userSearchContext': 'FOR_RENT',
                    'spellCheck': False,
                },
                'resultType': [
                    'REGIONS',
                    'FORSALE',
                    'RENTALS',
                    'SOLD',
                    'COMMUNITIES',
                    'SEMANTIC_REGIONS',
                ],
                'querySource': 'MANUAL',
                'shouldSpellCorrect': False,
            },
            'query': 'query getQueryUnderstandingResults($query: String!, $queryOptions: SearchAssistanceQueryOptions, $querySource: SearchAssistanceQuerySource = UNKNOWN, $resultType: [SearchAssistanceResultType], $shouldSpellCorrect: Boolean = false) {\n  searchAssistanceResult: zgsQueryUnderstandingRequest(\n    query: $query\n    queryOptions: $queryOptions\n    querySource: $querySource\n    resultType: $resultType\n  ) {\n    requestId\n    results {\n      ...SearchAssistanceResultFields\n      ...RegionResultFields\n      ...SemanticResultFields\n      ...RentalCommunityResultFields\n      ...SchoolResultFields\n      ...AddressResultFields\n    }\n  }\n}\n\nfragment SearchAssistanceResultFields on SearchAssistanceResult {\n  __typename\n  id\n  spellCorrectedMetadata @include(if: $shouldSpellCorrect) {\n    ...SpellCorrectedFields\n  }\n}\n\nfragment SpellCorrectedFields on SpellCorrectedMetadata {\n  isSpellCorrected\n  spellCorrectedQuery\n  userQuery\n}\n\nfragment RegionResultFields on SearchAssistanceRegionResult {\n  regionId\n  subType\n}\n\nfragment SemanticResultFields on SearchAssistanceSemanticResult {\n  nearMe\n  regionIds\n  regionTypes\n  regionDisplayIds\n  queryResolutionStatus\n  schoolDistrictIds\n  schoolIds\n  viewLatitudeDelta\n  filters {\n    basementStatusType\n    baths {\n      min\n      max\n    }\n    beds {\n      min\n      max\n    }\n    excludeTypes\n    hoaFeesPerMonth {\n      min\n      max\n    }\n    homeType\n    keywords\n    listingStatusType\n    livingAreaSqft {\n      min\n      max\n    }\n    lotSizeSqft {\n      min\n      max\n    }\n    parkingSpots {\n      min\n      max\n    }\n    price {\n      min\n      max\n    }\n    searchRentalFilters {\n      monthlyPayment {\n        min\n        max\n      }\n      petsAllowed\n      rentalAvailabilityDate {\n        min\n        max\n      }\n    }\n    searchSaleFilters {\n      daysOnZillow {\n        min\n        max\n      }\n    }\n    showOnlyType\n    view\n    yearBuilt {\n      min\n      max\n    }\n  }\n}\n\nfragment RentalCommunityResultFields on SearchAssistanceRentalCommunityResult {\n  location {\n    latitude\n    longitude\n  }\n}\n\nfragment SchoolResultFields on SearchAssistanceSchoolResult {\n  id\n  schoolDistrictId\n  schoolId\n}\n\nfragment AddressResultFields on SearchAssistanceAddressResult {\n  zpid\n  addressSubType: subType\n  location {\n    latitude\n    longitude\n  }\n}\n',
        }

        response = requests.post('https://www.zillow.com/zg-graph', params=params, headers=headers, json=json_data)

        #BUG - Unfortunately this request only returns the region id. 
        # I need the map coordinates as well to be able to query 
        # the async site.  

    #Error Trapping
    else:
        logger.critical("Inproper input for Zillow, moving to next site")
        return None

    # If there's an error, log it and return no data for that site
    if response.status_code != 200:
        logger.warning("The way is shut!")
        logger.warning(f'Status code: {response.status_code}')
        logger.warning(f'Reason: {response.reason}')
        return None

    bs4ob = BeautifulSoup(response.text, 'lxml')
    scripts = bs4ob.find_all("script")
    #Get the map coordinates
    coords = [x.text for x in scripts if "window.mapBounds" in x.text]
    start = coords[0].index("mapBounds")
    end = start + coords[0][start:].index(";\n")
    mapcords = coords[0][start:end].split(" = ")[1]
    map_coords = json.loads(mapcords)

    #Region ID and Type is next
    region = [x.text for x in scripts if "regionId" in x.text]
    start = region[0].index("regionId")
    end = start + region[0][start:].index("]") - 1
    regionID, regionType = region[0][start:end].split(",")
    regionID = int("".join([x for x in regionID if x.isnumeric()]))
    regionType = int("".join([x for x in regionType if x.isnumeric()]))
    
    #Take a nap
    time.sleep(np.random.randint(2, 6))

    # Stipulate subparameters of search
    subparams = {
        "pagination"     : {"currentPage":1},
        "isMapVisible"   :True,
        "mapBounds"      :map_coords,
        "filterState"    :{
            "isForRent"           :{"value":False},       #fr #"isForRent"
            "isForSaleByAgent"    :{"value":True},        #fsba #"isForSaleByAgent"
            "isForSaleByOwner"    :{"value":True},        #fsbo #"isForSaleByOwner"
            "isNewConstruction"   :{"value":False},       #nc #"isNewConstruction"
            "isComingSoon"        :{"value":True},        #cmsn #"isComingSoon"
            "isAuction"           :{"value":True},        #auc #"isAuction"
            "isForSaleForeclosure":{"value":True},        #fore #"isForSaleForeclosure"
            "mp"                  :{"max":str(MAXPRICE)}, #mp #"mp"
            "baths"               :{"min":str(MINBATHS)}, #baths #baths
            "beds"                :{"min":str(MINBEDS)},  #beds #"beds"
            "isManufactured"      :{"value":False},       #mf #"isManufactured"
            "isApartmentOrCondo"  :{"value":False},       #apco #"isApartmentOrCondo"
            "isApartment"         :{"value":False},       #apa #"isApartment"
            "isCondo"             :{"value":False},       #con #"isCondo"
            "ac"                  :{"value":True},        #ac #"ac"
        },
        "isListVisible"  :True,
        "mapZoom"        :15,
        "regionSelection":[{'regionId':regionID, "regionType":regionType}],
        "usersSearchTerm":srch_terms
    }
    params = {
        "searchQueryState": subparams,
        "wants": {"cat1": ["listResults", "mapResults"], "cat2": ["total"]},
        "requestId": np.random.randint(2, 10),
        "isDebugrequest":"false"
    }

    RUN_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "en",
        "Content-Type": "application/json",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
        "Sec-Ch-Ua-Mobile": "?0",
        "Sec-Ch-Ua-Platform": '"Windows"',
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    }
    url_search = "https://www.zillow.com/async-create-search-page-state"
    #Example
    # https://github.com/johnbalvin/pyzill
    response = requests.put(url_search, json = params, headers = RUN_HEADERS)

    #Just in case we piss someone off
    if response.status_code != 200:
        # If there's an error, log it and return no data for that site
        logger.warning(f'Status code: {response.status_code}')
        logger.warning(f'Reason: {response.reason}')
        return None

    resp_json = response.json()
    results = resp_json.get("cat1")["searchResults"]["listResults"]

    if results:
        counttest = 0
        for res in range(len(results)):
            #Sometimes they include listings that don't fit the search, but are encoded
            #with their lat long as the ZPID.  No idea why, but ain't nobody got time for that. 
            if not "-" in results[res]["zpid"]:
                counttest += 1
                results[res]["nonresult"] = False
            else:
                results[res]["nonresult"] = True
    else:
        logger.warning("No listings on Zillow. Count test fail")
        return None
    
    if counttest > 0:
        resultlist = [res for res in results if not res["nonresult"]]
        property_listings = get_listings(resultlist, neigh, source, Propertyinfo)
        logger.info(f'{len(property_listings)} listings returned from {source}')
        return property_listings
        
    else:
        logger.warning("No listings returned on Zillow.  Moving to next site")
        return None