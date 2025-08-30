import time
import json
import requests
import numpy as np
from typing import Union
from support import logger, get_time
from bs4 import BeautifulSoup

def get_listings(result:BeautifulSoup, neigh:tuple, source:str, Propertyinfo)->list:
    """[Ingest HTML of summary page for listings info]

    Args:
        result (BeautifulSoup object): html of apartments page
        neigh (tuple|str): area being searched
        source (str): Source website
        Propertyinfo (dataclass) : Dataclass for housing individual listings

    Returns:
        listings (list): [List of dataclass objects]
    """
    listings = []
    defaultval = None
    seller_keys = ["offeredBy"]
    #Set the outer loop over each card returned. 
    for search_results in result.find_all("script", {"type":"application/ld+json"}):
        if search_results:
            listinginfo = json.loads(search_results.text)
            k1 = "mainEntity"
            k2 = "itemListElement"
            if "@graph" not in listinginfo.keys():
                continue
            listinginfo = listinginfo["@graph"][0]
            numlistings = listinginfo[k1]["numberOfItems"]
            for idx in range(numlistings):
                listing = Propertyinfo()
                listing.url = listinginfo[k1][k2][idx].get("url", defaultval)
                if listing.url.endswith("/"):
                    listing.id       = listing.url.split("/")[-2]
                else:
                    listing.id       = listing.url.split("/")[-1]
                if listing.id == None:
                    logger.warning("id not found")
                    continue
                listing.img_url      = listinginfo[k1][k2][idx][k1].get("image", defaultval) 
                listing.htype        = listinginfo[k1][k2][idx][k1].get("@type", defaultval)
                listing.address      = listinginfo[k1][k2][idx].get("name", defaultval)
                listing.city         = listinginfo[k1][k2][idx][k1]["address"].get("addressLocality", defaultval)
                listing.state        = listinginfo[k1][k2][idx][k1]["address"].get("addressRegion", defaultval)
                listing.zipc         = int(listinginfo[k1][k2][idx][k1]["address"].get("postalCode", defaultval))
                listing.beds         = listinginfo[k1][k2][idx][k1].get("numberOfBedrooms", defaultval)
                listing.baths        = listinginfo[k1][k2][idx][k1].get("numberOfBathroomsTotal", defaultval)
                listing.sqft         = int("".join([x for x in str(listinginfo[k1][k2][idx][k1]["floorSize"].get("value", defaultval)) if x.isnumeric()]))
                listing.source       = source
                listing.status       = listinginfo[k1][k2][idx]["offers"].get("@type", defaultval)
                listing.price        = int(listinginfo[k1][k2][idx]["offers"].get("price", defaultval))
                if (listing.price !=None) & (listing.sqft != None):
                    listing.price_sqft   = listing.price // int(listing.sqft)
                listing.description  = listinginfo[k1][k2][idx].get("description", defaultval)
                listing.date_pulled  = get_time().strftime("%m-%d-%Y_%H-%M-%S")
                listing.seller       = listinginfo[k1][k2][idx]["offers"].get("seller", defaultval)
                listing.sellerinfo   = listinginfo[k1][k2][idx]["offers"].get("offeredBy", defaultval)
                # listing.last_s_date  = None
                # listing.last_s_price = None
                # listing.list_dt      = None
                # listing.lotsqft      = None
                # listing.extras       = None
                # listing.lat = float(listinginfo[k1][idx]["geo"].get("latitude", defaultval))
                # listing.long = float(listinginfo[k1][idx]["geo"].get("longitude", defaultval))
                listings.append(listing)

    return listings

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
    CITY = neigh[0].lower()
    STATE = neigh[1].lower()
    MAXPRICE = int(srch_par[0])
    MINBATHS = int(srch_par[1])
    MINBEDS = int(srch_par[2])
    
    #Search by CITY/State
    if isinstance(neigh, tuple):
        if " " in CITY:
            CITY = "-".join(neigh.lower().split(" "))
        url = f"https://www.homes.com/{CITY}-{STATE}/{MINBEDS}-{5}-bedroom/?property_type=1,2,32,8&bath-min={MINBATHS}&bath-max=5&price-max{MAXPRICE}"
            
    
    #TODO - Update this for zip search
    #Searchby ZipCode
    elif isinstance(neigh, int):
        #BUG - here they need city state and zip to search by zip.  Might need a way to generate that eventually, free api call?
        ZIPCODE = neigh
        url = f"https://www.homes.com/{CITY}-{STATE}/{ZIPCODE}/{MINBEDS}-{5}-bedroom/?property_type=1,2,32,8&bath-min={MINBATHS}&bath-max=5&price-max{MAXPRICE}"

    #Error Trapping
    else:
        logger.critical("Inproper input for homes, moving to next site")
        return None

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
    #Look for no evidence of no results
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
        return None
