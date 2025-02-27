import logging
import json
from bs4 import BeautifulSoup
import numpy as np
import requests
from urllib.parse import urlencode, quote
import time
from typing import Union

def get_listings(result:dict, neigh:str, source:str, Propertyinfo)->list:
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
    listingid = price = beds = sqft = baths = pets = url = addy = current_time = lat = long = None

    for res in result:
        active_keys = list(res.keys())
        current_time = time.strftime("%m-%d-%Y_%H-%M-%S")
        if "zpid" in active_keys:
            listingid = res["zpid"]
        else:
            #If it doesn't have an ID, don't store it
            continue
        if "detailUrl" in active_keys:
            url = res["detailUrl"]
        if "unformattedPrice" in active_keys:
            price = float(res["unformattedPrice"])
        if "beds" in active_keys:
            beds = float(res["beds"])
        if "baths" in active_keys:
            baths = float(res["baths"])
        if "address" in active_keys:
            addy = res["address"]
        if "area" in active_keys:
            sqft = float(res["area"])
        if res["latLong"].get("latitude"):
            lat = float(res["latLong"]["latitude"])
        if res["latLong"].get("longitude"):
            long = float(res["latLong"]["longitude"])
        # daysonZ = res["variableData"]["text"]
        pets = True
        
        listing = Propertyinfo(
            id=listingid,   
            source=source,
            price=price,    
            neigh=neigh,
            bed=beds,       
            sqft=sqft,      
            bath=baths,     
            dogs=pets,      
            link=url,
            lat=lat,
            long=long,
            address=addy,
            date_pulled=current_time    
        )
        listings.append(listing)
        listingid = price = beds = sqft = baths = pets = url = addy = current_time = lat = long = None
    return listings

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
    #Check for spaces in the search neighborhood
    CITY = srch_par[0].lower()
    STATE = srch_par[1].lower()
    MINBEDS = int(srch_par[2])
    MAXRENT = int(srch_par[3])

    #First grab the map coordinates update our next request
    BASE_HEADERS = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer':f'https://www.zillow.com/{CITY}-{STATE}/',
        'origin':'https://www.zillow.com',
    }
    #BUG - Getting errors here now.  Probably need to adjust the base_headers
    #Search by neighborhood
    if isinstance(neigh, str):
        neigh = neigh.lower()
        srch_terms = f"{neigh} {CITY} {STATE.upper()}"
        if " " in neigh:
            neigh = "-".join(neigh.split(" "))
        url_map = f'https://www.zillow.com/{neigh}-{CITY}-{STATE}/rentals/?'
        

    #Searchby ZipCode
    elif isinstance(neigh, int):
        url_map = f'https://www.zillow.com/{CITY}-{STATE}-{neigh}/rentals/?'
        srch_terms = f"{neigh} {CITY}, {STATE.upper()}"
    
    #Error Trapping
    else:
        logging.critical("Inproper input for area, moving to next site")
        return

    response = requests.get(url_map, headers=BASE_HEADERS)
    
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
            "isForRent"           :{"value":True},        #fr #"isForRent"
            "isForSaleByAgent"    :{"value":False},       #fsba #"isForSaleByAgent"
            "isForSaleByOwner"    :{"value":False},       #fsbo #"isForSaleByOwner"
            "isNewConstruction"   :{"value":False},       #nc #"isNewConstruction"
            "isComingSoon"        :{"value":False},       #cmsn #"isComingSoon"
            "isAuction"           :{"value":False},       #auc #"isAuction"
            "isForSaleForeclosure":{"value":False},       #fore #"isForSaleForeclosure"
            "mp"                  :{"max":str(MAXRENT)},  #mp #"mp"
            "beds"                :{"min":str(MINBEDS)},  #beds #"beds"
            "isManufactured"      :{"value":False},       #mf #"isManufactured"
            "isApartmentOrCondo"  :{"value":False},       #apco #"isApartmentOrCondo"
            "isApartment"         :{"value":False},       #apa #"isApartment"
            "isCondo"             :{"value":False},       #con #"isCondo"
            "ac"                  :{"value":True},        #ac #"ac"
            "onlyRentalLargeDogs" :{"value":True},        #ldog #"onlyRentalLargeDogs"
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