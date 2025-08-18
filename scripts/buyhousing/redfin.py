import time
import json
import requests
import numpy as np
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from support import logger, state_dict, get_time
from typing import Union

def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo)->list:
    """[Ingest HTML of summary page for listings info]

    Args:
        result (BeautifulSoup object): html of redfin page
        neigh (str): neighorhood being searched
        source (str): Source website
        Propertyinfo (dataclass) : Dataclass for housing individual listings

    Returns:
        listings (list): [List of dataclass objects]
    """
    listings = []
    defaultval = None
    #Set the outer loop over each card returned. 

    for card in result.find_all("div", _class=lambda x: x and x.startswith("HomeCardsContainer")):
        # for subsearch in card.find_all("script", {"type":"application/ld+json"}):
        for search_results in card.find_all("script", {"type":"application/ld+json"}):
            if search_results:
                listinginfo = json.loads(search_results.text)
                listing         = Propertyinfo()
                listing.url     = listinginfo[0].get("url", defaultval)
                listing.id      = listing.url.split("/")[-1]
                listing.address = listinginfo[0].get("name")
                listing.lat     = float(listinginfo[0]["geo"].get("latitude"))
                listing.long    = float(listinginfo[0]["geo"].get("longitude"))
                listing.beds    = listinginfo[0].get("numberOfRooms")
                listing.price = float("".join(x for x in listinginfo[1]["offers"]["price"] if x.isnumeric()))

                # listing.id           = search_result.get("listing_id", defaultval)
                # listing.url          = "https://" + source + "/realestateandhomes-detail/" + search_result.get("permalink")
                # listing.img_url      = search_result.get("photos", defaultval)
                # listing.status       = search_result.get("status", defaultval)
                # listing.source       = source
                # listing.city         = search_result["location"]["address"].get("city", defaultval)
                # listing.state        = search_result["location"]["address"].get("state_code", defaultval)
                # listing.zipc         = search_result["location"]["address"].get("postal_code", defaultval)
                # listing.address      = search_result["location"]["address"]["line"] + ", " + listing.city + ", " + listing.state + " " + listing.zipc 
                # listing.htype        = search_result["description"].get("type", defaultval)
                # listing.baths        = bedbath_format(search_result["description"].get("baths_consolidated", defaultval))
                # listing.beds         = bedbath_format(search_result["description"].get("beds", defaultval))
                # listing.sqft         = search_result["description"].get("sqft", defaultval)
                # listing.lotsqft      = search_result["description"].get("lotsqft", defaultval)
                # listing.price        = search_result.get("list_price", defaultval)
                # listing.date_pulled  = get_time().strftime("%m-%d-%Y_%H-%M-%S")
                # listing.lat          = search_result["location"]["address"]["coordinate"].get("lat", defaultval)
                # listing.long         = search_result["location"]["address"]["coordinate"].get("lat", defaultval)
                # listing.list_dt      = date_format(search_result.get("list_date", defaultval), True)
                # listing.last_pri_cha = search_result.get("last_price_change_amount", defaultval)
                # listing.last_pri_dat = date_format(search_result.get("last_status_change_date", defaultval))
                # listing.seller       = search_result["branding"][0].get("name", defaultval)
                # listing.sellerinfo   = search_result.get("advertisers", defaultval)
            listings.append(listing)

    return listings

def money_launderer(price:int)->str:
    """[Formats price to a single decimal k format.  This is redfins weird encoding nonsense]

    Args:
        price (int): [price as an int]

    Returns:
        price (str): [price as a str]
    """
    if isinstance(price, int):
        sprice = str(price)
        if len(sprice) < 4:
            fprice = sprice
        elif sprice[1] != "0":
            fprice = sprice[0] + "." + sprice[1] + "k"
        else:
            fprice = sprice[0] + "k"
        return fprice
    
    else:
        return price

def neighscrape(neigh:Union[tuple, int], source:str, Propertyinfo, srch_par)->list:
    """[Outer scraping function to set up request pulls]

    Args:
        neigh (Union[str,int]): Neighborhood or zipcode searched
        source (str): What site is being scraped
        Propertyinfo (dataclass): Custom data object
        srch_par (tuple): Tuple of search parameters

    Returns:
        property_listings (list): List of dataclass objects
    """    
    #Check for spaces in the search neighborhood
    CITY = neigh[0].lower()
    STATE = neigh[1].lower()
    MAXPRICE = int(srch_par[0])
    MINBATHS = int(srch_par[1])
    MINBEDS = int(srch_par[2])
    chrome_version = np.random.randint(120, 137)

    BASE_HEADERS = {
        'user-agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36',
        'origin':'https://www.redfin.com',
    }

    #Search by neighborhood
    if isinstance(neigh, tuple):
        # First grab the map coordinates update our next request
        #BUG stupid neighborhood encodings. 
            #Beecause redfin dumps their own numerical zip for neighborhoods, I need to make
            #two requests when searching redfin by string
            #1. Make a request to see what neighborhood code goes with the search term. 
            #2. Request the appropriate neigh with paramaterized search. 

        SH_PARAMS = {
            "location":"",
            "start": 0,
            "count": 10,
            "v": 2,
            "market": f"{state_dict[STATE]}",
            "al": 1,
            "iss": "false",
            "ooa": "true",
            "mrs": "false",
            "region_id": 4433,
            "region_type": 6,
            "lat": 41.833670000000005,
            "lng": -87.73184,
            "includeAddressInfo": "false",
            "lastSearches":""
        }

        # https://www.redfin.com/stingray/api/v1/search/rentals
    
        #Search by neighborhood
        if isinstance(neigh, tuple):
            url_map = "https://www.redfin.com/stingray/do/location-autocomplete?" + urlencode(SH_PARAMS)
            # url_map = f'https://www.redfin.com/stingray/do/gis-search/' + urlencode(SH_PARAMS)

        #Error Trapping
        else:
            logger.critical("Inproper input for redfin, moving to next site")
            return

        response = requests.get(url_map, headers=BASE_HEADERS)
        
        # If there's an error, log it and return no data for that site
        if response.status_code != 200:
            logger.warning("redfin prefetch request failed!")
            logger.warning(f'Status code: {response.status_code}')
            logger.warning(f'Reason: {response.reason}')
            return None

        #Always take naps
        time.sleep(np.random.randint(3, 5))
        
        #Look up neighborhood id from autocomplete search query
        temp_dict = json.loads(response.text[4:])
        for neighborhood in temp_dict["payload"]['sections'][0]["rows"]:
            if neighborhood.get("name").lower() == neigh.lower():
                neighid = neighborhood.get("id")[2:]
                break

        if " " in neigh:
            neigh = "-".join(neigh.split(" "))
        url_search = f'https://www.redfin.com/neighborhood/{neighid}/{STATE}/{CITY}/filter/property-type=house+townhouse+multifamily+land,max-price={MAXPRICE},min-beds={MINBEDS}'
        response = requests.get(url_search, headers = BASE_HEADERS)

    #Searchby ZipCode
    elif isinstance(neigh, int):
        #TODO - Update these headers and URL when you get to zipcodes
        INT_HEADERS = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9',
            'cache-control': 'max-age=0',
            'priority': 'u=0, i',
            'referer': f'{source}',
            'sec-ch-ua': f"'Google Chrome';v={chrome_version}, 'Not-A.Brand';v='8', 'Chromium';v={chrome_version}",
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
            'user-agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36',
        }
        url_search = f'https://www.redfin.com/zipcode/{neigh}/rentals/filter/property-type=house+townhouse,max-price={MAXPRICE},min-beds={MINBEDS},air-conditioning' #,has-parking
        response = requests.get(url_search, headers = INT_HEADERS)

    #Error Trapping
    else:
        logger.critical("Inproper input for redfin, moving to next site")
        return None

    #Just in case we piss someone off
    if response.status_code != 200:
        # If there's an error, log it and return no data for that site
        logger.warning(f'Status code: {response.status_code}')
        logger.warning(f'Reason: {response.reason}')
        return None

    #Get the HTML
    bs4ob = BeautifulSoup(response.text, 'lxml')

    # Find how many results there were
    housecount = bs4ob.find("div", class_="homes summary reversePosition")
    if housecount != None:
        lcount = housecount.text.split()[0]
        lcount = int("".join(x for x in lcount if x.isnumeric()))
    else:
        logger.warning("No count found on redfin.  Moving to next site")
        return None

    if lcount > 0:
        property_listings = get_listings(bs4ob, neigh, source, Propertyinfo)
        logger.info(f'{len(property_listings)} listings returned from {source}')
        return property_listings

    else:
        logger.warning("No listings returned on Redfin.  Moving to next site")
        return None

#Notes
# https://github.com/ryansherby/RedfinScraper/blob/main/redfin_scraper/core/redfin_scraper.py