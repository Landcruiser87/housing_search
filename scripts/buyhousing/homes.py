import time
import json
import requests
import numpy as np
from typing import Union
from support import logger
from bs4 import BeautifulSoup

def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo, PETS)->list:
    """[Ingest HTML of summary page for listings info]

    Args:
        result (BeautifulSoup object): html of apartments page
        neigh (str): neighorhood being searched
        source (str): Source website
        Propertyinfo (dataclass) : Dataclass for housing individual listings
        Pets (bool) : Whether or not you are searching for a furry friend

    Returns:
        listings (list): [List of dataclass objects]
    """
    listings = []
    listingid = price = beds = sqft = baths = pets = url = addy = current_time = lat = long = None
    if isinstance(neigh, str):
        neigh = neigh.lower()

    #Set the outer loop over each card returned. 
    for subsearch in card.find_all("script", {"type":"application/ld+json"}):
        listinginfo = json.loads(subsearch.text)
        url = listinginfo[0].get("url")
        listingid = url.split("/")[-1]
        addy = listinginfo[0].get("name")
        lat = float(listinginfo[0]["geo"].get("latitude"))
        long = float(listinginfo[0]["geo"].get("longitude"))
        beds = listinginfo[0].get("numberOfRooms")


    #Set the outer loop over each card returned. 
    for card in result.find_all("li", class_="placard-container"):
        # Time of pull
        current_time = time.strftime("%m-%d-%Y_%H-%M-%S")

        #Grab the id
        search = card.find("article", class_=lambda x: x and x.startswith("search-placard for-rent"))
        if search:
            try:
                listingid = search["data-pk"]
            except Exception as e:
                logger.warning(f"id extraction error on {source} in {neigh}")
                continue
        else:
            logger.warning(f"missing id for card on {source} in {neigh}")
            continue

        details = card.find("div", class_=lambda x: x and x.startswith("for-rent-content-container"))
        if details:
            #grab address
            res = card.find("address")
            if res:
                addy = " ".join(res.text.strip("\n").split())
            #grab price
            res = card.find("p", class_="current-price")
            if res:
                price = float("".join(x for x in res.text if x.isnumeric()))
            #grab url
            res = card.find("a")
            if res:
                url = "https://" + source + res.get("href")

            search = card.find("ul", class_="detailed-info-container")
            for subsearch in search.find_all("li"):
                testval = subsearch.text
                if testval:
                    #Grab Beds
                    if "beds" in testval.lower():
                        beds = float("".join(x for x in testval if x.isnumeric()))
                    #Grab baths
                    elif "bath" in testval.lower():
                        baths = float("".join(x for x in testval if x.isnumeric() or x == "."))
                    
                    elif ("sq" in testval.lower()) | ("ft" in testval.lower()):
                        sqft = float("".join(x for x in testval if x.isnumeric()))

        pets = PETS

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
            address=addy,
            date_pulled=current_time
        )
        listings.append(listing)
        listingid = price = beds = sqft = baths = pets = url = addy = current_time = None

    return listings

def neighscrape(neigh:Union[str, int], source:str, Propertyinfo, srch_par)->list:
    """[Outer scraping function to set up request pulls]

    Args:
        neigh (Union[str,int]): Neighborhood or zipcode searched
        source (str): What site is being scraped
        Propertyinfo (dataclass): Custom data object
        srch_par (tuple): Tuple of search parameters

    Returns:
        property_listings (list): List of dataclass objects
    """    
    CITY = neigh[0].lower()
    STATE = neigh[1].lower()
    MAXPRICE = int(srch_par[0])
    MINBATHS = int(srch_par[1])
    MINBEDS = int(srch_par[2])
    
    #Search by neighborhood
    if isinstance(neigh, tuple):
        if " " in CITY:
            CITY = "-".join(neigh.lower().split(" "))
        url = f"https://www.homes.com/{CITY}-{STATE}/{MINBEDS}-{5}-bedroom/?property_type=1,2,32,8&bath-min={MINBATHS}&bath-max=5&price-max{MAXPRICE}"
            
    #Searchby ZipCode
    elif isinstance(neigh, int):
        #BUG - here they need city state and zip to search by zip.  Might need a way to generate that eventually
        ZIPCODE = neigh
        url = f"https://www.homes.com/{CITY}-{STATE}/{ZIPCODE}/{MINBEDS}-{5}-bedroom/?property_type=1,2,32,8&bath-min={MINBATHS}&bath-max=5&price-max{MAXPRICE}"

    #Error Trapping
    else:
        logger.critical("Inproper input for area, moving to next site")
        return

    chrome_version = np.random.randint(120, 137)
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'content-type': 'application/json',        
        # 'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        # 'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': f'"Not)A;Brand";v="99", "Google Chrome";v={chrome_version}, "Chromium";v={chrome_version}',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'iframe',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'cross-site',
        'upgrade-insecure-requests': '1',
        'user-agent': f'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Mobile Safari/537.36',
        'referer': url,
        'origin':'https://www.homes.com',
    }

    response = requests.get(url, headers=headers)

    #Just in case we piss someone off
    if response.status_code != 200:
        # If there's an error, log it and return no data for that site
        logger.warning(f'Status code: {response.status_code}')
        logger.warning(f'Reason: {response.reason}')
        return None

    #Get the HTML
    bs4ob = BeautifulSoup(response.text, 'lxml')

    # Isolate the property-list from the expanded one (I don't want the 3 mile
    # surrounding.  Just the neighborhood)
    nores = bs4ob.find_all("div", class_="no-results-container")
    errorres = bs4ob.find_all("div", class_="error-results-container")
    if not nores and not errorres:
        results = bs4ob.find("ul", class_="placards-list")
        if results:
            property_listings = get_listings(bs4ob, neigh, source, Propertyinfo)
            logger.info(f'{len(property_listings)} listings returned from {source}')
            return property_listings
            
    else:
        logger.warning("No listings returned on homes.  Moving to next site")
