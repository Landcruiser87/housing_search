import logging
import json
from bs4 import BeautifulSoup
import numpy as np
import requests
from urllib.parse import urlencode
import time
import support
from typing import Union

def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo)->list:
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
    #Set the outer loop over each card returned. 
    # check the count
        #update - Don't need to check count anymore. Doing so beforehand
        #Saving in case i'm wrong
    # if pcount < 1:
    #     return "No results found"
    
    for jres in result.find_all("li", class_=(lambda x:x and x.startswith("ListItem"))):
        #early terminate if the data-test key is in the underlying object
        if jres.get("data-test"):
            continue

        # Time of pull
        current_time = time.strftime("%m-%d-%Y_%H-%M-%S")

        #grab lat / long
        latlong = jres.find("script", {"type":"application/ld+json"})
        if latlong:
            res = json.loads(latlong.text)
            lat = res["geo"]["latitude"]
            long = res["geo"]["longitude"]
            url = res["url"]
            addy = res["name"]
        else:
            lat  = ""
            long = ""
            card = jres.find("a")
            if card:
                url = card.get("href")
                addy = card.next_element.contents[0]
            else:
                url, addy = "", ""

        for card in jres.find_all("article"):
            #Grab the id
            if card.get("data-test")=="property-card":
                listingid = card.get("id")
            
            #grab the price
            for search in card.find_all("span"):
                if search.get("data-test")=="property-card-price":
                    text = search.text
                    #Sometimes these jokers put the beds in with the price just annoy people like me
                    if "+" in text:
                        price = text[:text.index("+")]

                    price = float("".join(x for x in text if x.isnumeric()))
                    break

            #Grab bed bath
            for search in card.find_all("ul"):
                for subsearch in search.find_all("li"):
                    text = str(subsearch)
                    numtest = any(x.isnumeric() for x in text)

                    if "bd" in text and numtest:
                        beds = float("".join(x for x in text if x.isnumeric()))
                    elif "ba" in text and numtest:
                        baths = str("".join(x for x in text if x.isnumeric() or x == "."))
                    elif "sqft" in text and numtest:
                        sqft = float("".join(x for x in text if x.isnumeric()))
        pets = True

        #Janky way of making sure variables are filled if we missed any
        if not "listingid" in locals():
            raise ValueError(f"Missing listing id for {url}")
        if not "price" in locals():
            price = None
        if not "beds" in locals():
            beds = None
        if not "baths" in locals():
            baths = None
        if not "url" in locals():
            url = None
        if not "addy" in locals():
            addy = None
        if not "sqft" in locals():
            sqft = None
        if not "lat" in locals():
            lat = None
        if not "long" in locals():
            long = None
        
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

def neighscrape(neigh:Union[str, int], source:str, logger:logging, Propertyinfo, srch_par):
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
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'referer':f'https://www.zillow.com/{CITY}-{STATE}/rentals',
        'origin':'https://www.zillow.com',
    }
    #Search by neighborhood
    if isinstance(neigh, str):
        if " " in neigh:
            neigh = "-".join(neigh.split(" "))
        neigh = neigh.lower()
        url_map = f'https://www.zillow.com/{neigh}-{CITY}-{STATE}/rentals'
        srch_terms = f"{neigh} {CITY}, {STATE.upper()}"

    #Searchby ZipCode
    elif isinstance(neigh, int):
        url_map = f'https://www.zillow.com/{CITY}-{STATE}-{neigh}/rentals'
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
    coords = [x.text for x in scripts if "window.mapBounds" in x.text]
    start = coords[0].index("mapBounds")
    end = start + coords[0][start:].index(";\n")
    mapcords = coords[0][start:end].split(" = ")[1]

    #Get the map coordinates
    map_coords = json.loads(mapcords)
    support.sleepspinner(np.random.randint(2, 8), "Map Request Nap")
    
    #! Update tprice and min beds
    #Stipulate subparameters of search
    subparams = {
        "usersSearchTerm":srch_terms,
        "mapBounds":map_coords,
        "filterState":{
            "isForRent"           :{"value":True},
            "isForSaleByAgent"    :{"value":False},
            "isForSaleByOwner"    :{"value":False},
            "isNewConstruction"   :{"value":False},
            "isComingSoon"        :{"value":False},
            "isAuction"           :{"value":False},
            "isForSaleForeclosure":{"value":False},
            "isAllHomes"          :{"value":True},
            "beds"                :{"min":MINBEDS},
            "isApartmentOrCondo"  :{"value":False},
            "isApartment"         :{"value":False},
            "isCondo"             :{"value":False},
            "mp"                  :{"max":MAXRENT},
            "ac"                  :{"value":True},
            # "parka"               :{"value":True},#I think searching by parking too is limiting my results.  Taking it off for now
            "onlyRentalLargeDogsAllowed":{"value":True}, #Uncomment depending on doggo preference
            "onlyRentalSmallDogsAllowed":{"value":True}
        },
        "isListVisible":True,
        # "regionSelection": [{"regionId": 33597, "regionType": 8}], #!might not need this?
        "pagination" : {},
        "mapZoom":11
    }
    params = {
        "searchQueryState": subparams,
        "wants": {"cat1": ["listResults"]},
        "requestId": 2 #np.random.randint(2, 3)
    }
    url_search = url_map + "?" + urlencode(params)
    response = requests.get(url_search, headers = BASE_HEADERS)

    #Just in case we piss someone off
    if response.status_code != 200:
        # If there's an error, log it and return no data for that site
        logger.warning(f'Status code: {response.status_code}')
        logger.warning(f'Reason: {response.reason}')
        return None

    #Get the HTML
    bs4ob = BeautifulSoup(response.text, 'lxml')

    # Isolate the property-list from the expanded one (I don't want the 3 mile
    # surrounding.  Just the neighborhood). 
    #First look for the results count, 
    #Then look for the results container if you've found the count

    counts = bs4ob.find("span", class_="result-count")
    if counts:
        counttest = int("".join(x for x in counts.text if x.isnumeric()))
    else:
        logger.warning("No listings on Zillow. Count test fail")
        return None
    
    if counttest > 0:
        results = bs4ob.find("div", class_="result-list-container")
        if results:
            if results.get("id") =='grid-search-results':
                resultlist = results.find("ul", class_=(lambda x:x and x.startswith("List")))
                property_listings = get_listings(resultlist, neigh, source, Propertyinfo)
                logger.info(f'{len(property_listings)} listings returned from {source}')
                return property_listings
        
    else:
        logger.warning("No listings returned on Zillow.  Moving to next site")