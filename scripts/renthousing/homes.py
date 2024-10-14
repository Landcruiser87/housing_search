import logging
from bs4 import BeautifulSoup
import requests
import time
from typing import Union

def get_listings(result:BeautifulSoup, neigh:str, source:str, logger:logging, Propertyinfo, PETS)->list:
    """[Ingest HTML of summary page for listings info]

    Args:
        result (BeautifulSoup object): html of apartments page
        neigh (str): neighorhood being searched
        source (str): Source website
        logger (logging.logger): logger for Kenny loggin
        Propertyinfo (dataclass) : Dataclass for housing individual listings
        Pets (bool) : Whether or not you are searching for a furry friend

    Returns:
        listings (list): [List of dataclass objects]
    """

    listings = []
    listingid = price = beds = sqft = baths = pets = url = addy = current_time = None

    #Set the outer loop over each card returned. 
    for card in result.find_all("li", class_="placard-container"):
        # Time of pull
        current_time = time.strftime("%m-%d-%Y_%H-%M-%S")

        #Grab the id
        search = card.find("article", class_=lambda x: x and x.startswith("search-placard for-rent"))
        if search:  
            listingid = search.get("data-pk")
        else:
            logger.warning(f"missing id for card on {source} in {neigh}")
            continue

        details = card.find("div", class_="for-rent-content-container")
        if details:
            #grab address
            res = card.find("address")
            if res:
                addy = " ".join(card.find("address").text.strip("\n").split())
            #grab url
            res = card.find("a")
            if res:
                url = "https://" + source + res.get("href")

            search = card.find("ul", class_="detailed-info-container")
            for subsearch in search.find_all("li"):
                testval = subsearch.text
                if testval:
                    #Grab price
                    if "$" in testval:
                        price = float("".join(x for x in testval if x.isnumeric()))
                    #Grab Beds
                    elif "beds" in testval.lower():
                        beds = float("".join(x for x in testval if x.isnumeric()))
                    #Grab baths
                    elif "baths" in testval.lower():
                        baths = float("".join(x for x in testval if x.isnumeric() or x == "."))
                    #! SQFT is available on the individual links, but not worth
                    #! the extra call to grab it

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
    CITY = srch_par[0].lower()
    STATE = srch_par[1].lower()
    MINBEDS = int(srch_par[2])
    MAXRENT = int(srch_par[3])
    PETS = srch_par[4]
    #Search by neighborhood
    if isinstance(neigh, str):
        if " " in neigh:
            neigh = "-".join(neigh.lower().split(" "))
        else:
            neigh = neigh.lower()
        url = f"https://www.homes.com/{CITY}-{STATE}/{neigh}-neighborhood/homes-for-rent/studio-to-{MINBEDS}-bedoom/under-{MAXRENT}/?property_type=4,16"
        
    #Searchby ZipCode
    elif isinstance(neigh, int):
        url = f"https://www.homes.com/{CITY}-{STATE}/{neigh}/homes-for-rent/studio-to-{MINBEDS}-bedroom/under-{MAXRENT}/?"    #Error Trapping
        
    else:
        logger.critical("Inproper input for area, moving to next site")
        return

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="122", "Chromium";v="122"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'iframe',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'cross-site',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
        'referer': url,
        'origin':'https://www.homes.com',
        # 'Content-Type': 'text/html',
        # 'Content-Encoding':'gzip'
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
    # surrounding.  Just the neighborhood) #BUG Add me
    nores = bs4ob.find_all("div", class_="no-results-container")
    errorres = bs4ob.find_all("div", class_="error-results-container")
    #BUG Edge case
        #Keeps getting through where its showing similar properties but no result.  Noooot sure why. 
    if not nores or not errorres:
        results = bs4ob.find("ul", class_="placards-list")
        if results:
            property_listings = get_listings(results, neigh, source, logger, Propertyinfo, PETS)
            logger.info(f'{len(property_listings)} listings returned from {source}')
            return property_listings
            
    else:
        logger.warning("No listings returned on apartments.  Moving to next site")
