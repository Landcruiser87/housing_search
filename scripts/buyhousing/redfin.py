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
    for card in result.find_all("script", {"type":"application/ld+json"}):
        listinginfo = json.loads(card.text)
        if isinstance(listinginfo, list):
            listing              = Propertyinfo()
            listing.url          = listinginfo[1].get("url", defaultval)
            if listing.url.endswith("/"):
                listing.id       = listing.url.split("/")[-2]
            else:
                listing.id       = listing.url.split("/")[-1]
            if listing.id == None:
                logger.warning("id not found")
                continue
            listing.status       = "For_Sale"
            listing.source       = source
            listing.city         = listinginfo[0]["address"].get("addressLocality", defaultval)
            listing.state        = listinginfo[0]["address"].get("addressRegion", defaultval)
            listing.zipc         = listinginfo[0]["address"].get("postalCode", defaultval)
            listing.address      = listinginfo[0].get("name", defaultval)
            listing.htype        = listinginfo[0].get("@type", defaultval)
            listing.sqft         = listinginfo[0]["floorSize"].get("value", defaultval)
            listing.price        = int(listinginfo[1]["offers"].get("price", 0))
            listing.date_pulled  = get_time().strftime("%m-%d-%Y_%H-%M-%S")
            listing.lat          = float(listinginfo[0]["geo"].get("latitude", defaultval))
            listing.long         = float(listinginfo[0]["geo"].get("longitude", defaultval))
            if "numberOfBaths" in listinginfo[0].keys():
                listing.baths    = bedbath_format(listinginfo[0].get("numberOfBaths", defaultval))
            if "numberOfRooms" in listinginfo[0].keys():
                listing.beds     = bedbath_format(listinginfo[0].get("numberOfRooms", defaultval))
            #Vars not on the page scan below
            # listing.list_dt      = date_format(search_result.get("list_date", defaultval), True)
            # listing.last_pri_cha = search_result.get("last_price_change_amount", defaultval)
            # listing.last_pri_dat = date_format(search_result.get("last_status_change_date", defaultval))
            # listing.seller       = search_result["branding"][0].get("name", defaultval)
            # listing.sellerinfo   = search_result.get("advertisers", defaultval)
            # listing.img_url = listinginfo.get("photos", defaultval)
            # listing.lotsqft      = search_result["description"].get("lotsqft", defaultval)
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
    CITY = neigh[0]
    STATE = neigh[1]
    MAXPRICE = int(srch_par[0])
    MINBATHS = int(srch_par[1])
    MINBEDS = int(srch_par[2])
    chrome_version = np.random.randint(120, 137)
    neighid = None
    BASE_HEADERS = {
        'origin':'https://www.redfin.com',
        'user-agent': f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{chrome_version}.0.0.0 Safari/537.36',
    }

    #Search by CITY/State
    if isinstance(neigh, tuple):
        # First grab the map coordinates update our next request
        #Because redfin dumps their own numerical zip for neighborhoods, I need to make
        #two requests when searching redfin by string
            #1. Make a request to see what neighborhood code goes with the search term. 
            #2. Request the appropriate neigh with paramaterized search. 

        SH_PARAMS = {
            "location":f"{CITY.lower()}, {STATE.lower()}",
            "start": 0,
            "count": 10,
            "v": 2,
            "market": f"{state_dict[STATE].lower()}",
            "al": 1,
            "iss": "false",
            "ooa": "true",
            "mrs": "false",
            "region_id": "NaN",
            "region_type": "NaN",
            "lat": 41.833670000000005,
            "lng": -85.01138,
            "includeAddressInfo":"false",
            "lastSearches":""
        }

        #Search by neighborhood
        url_map = "https://www.redfin.com/stingray/do/rental-location-autocomplete?" + urlencode(SH_PARAMS)
            #NOTE - For some reason this works on the rentals, but not on the house buying endpoint? 
                # ¯\_(ツ)_/¯
            # BASE_HEADERS["referer"] = url_map
            # url_map = f'https://www.redfin.com/stingray/do/gis-search/' + urlencode(SH_PARAMS)

        response = requests.get(url_map[:-1], headers=BASE_HEADERS)
        
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
            if neighborhood.get("name").lower() == CITY.lower():
                neighid = neighborhood.get("id")[2:]
                break
        if neighid != None:
            url_search = f'https://www.redfin.com/city/{neighid}/{STATE}/{CITY}/filter/property-type=house+townhouse+multifamily+land,max-price={MAXPRICE},min-beds={MINBEDS},min-baths={MINBATHS}'
            response = requests.get(url_search, headers = BASE_HEADERS)
        else:
            logger.warning("Missing neighID")
            return None
    
    #TODO - Update zipcode selection
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