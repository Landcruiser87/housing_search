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
    """[Gets the list of links to the individual postings]

    Args:
        bs4ob ([BeautifulSoup object]): [html of realtor page]

    Returns:
        properties (list[Propertyinfo]): [all the links in the summary page]
    """
    listings = []
    #Set the outer loop over each card returned. 
    # check the count
    count = result.find("span", class_="result-count")
    if count:
        count = int("".join(x for x in count.text if x.isnumeric()))
        if count < 1:
            return "No results found"
    
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
                        baths = float("".join(x for x in text if x.isnumeric()))
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

    return listings

def neighscrape(neigh:Union[str, int], source:str, logger:logging, Propertyinfo, citystate):
    #Check for spaces in the search neighborhood
    CITY = citystate[0].lower()
    STATE = citystate[1].lower()
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
    
    #Searchby ZipCode
    elif isinstance(neigh, int):
        url_map = f'https://www.zillow.com/{CITY}-{STATE}-{neigh}/rentals'
    
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
     
    #Stipulate subparameters of search
    subparams = {
        "usersSearchTerm":f"{neigh} {CITY}, {STATE.upper()}",
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
            "beds"                :{"min":2},
            "isApartmentOrCondo"  :{"value":False},
            "isApartment"         :{"value":False},
            "isCondo"             :{"value":False},
            "mp"                  :{"max":2600},
            "ac"                  :{"value":True},
            "parka"               :{"value":True},
            "onlyRentalLargeDogsAllowed":{"value":True},
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
                property_listings = get_listings(results, neigh, source, Propertyinfo)
                logger.info(f'{len(property_listings)} listings returned from {source}')
                return property_listings
        
    else:
        logger.warning("No listings returned on Zillow.  Moving to next site")