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

    Returns:
        listings (list): [List of dataclass objects]
    """

    listings = []
    listingid = price = beds = sqft = baths = pets = url = addy = current_time = extrafun = None
    #Set the outer loop over each card returned. 
    for card in result.find_all("article", class_=lambda x: x and x.startswith("placard")):
        # Time of pull
        current_time = time.strftime("%m-%d-%Y_%H-%M-%S")

        #Grab the id
        listingid = card.get("data-listingid")

        #First grab the link
        if card.get("data-url"):
            url = card.get("data-url")
            #If the listingid wasn't in the metadata (sometimes happens)
            #Pull it from the end of the URL
            if not listingid:
                listingid = url.split("/")[-2]
        else:
            logger.warning(f"missing url and id for card on {source} in {neigh}")
            continue

        #grab the property info
        for search in card.find_all("div", class_="propertyInfo"):
            #Grab price
            for subsearch in search.find_all("div", class_="priceRange left"):
                price = subsearch.text
                if any(x.isnumeric() for x in price):
                    price = money_launderer(price.split(" ")[0])
            #Grab address
            for subsearch in search.find_all("div", class_="propertyAddress"):
                addy = subsearch.text
            #Grab bed bath
            for subsearch in card.find_all("div", class_="bedRange"):
                extrafun = subsearch.text.lower()
                if "ft" in extrafun:#lol
                    #quick comma count
                    count = extrafun.count(",")
                    if count < 3:
                        beds, baths, sqft = extrafun.split(",")
                        sqft = sqft.strip()
                        sqft = float("".join(x for x in sqft if x.isnumeric()))
                    else:
                        #For if they put a comma in the square footage
                        beds, baths, sqft, extra = extrafun.split(",")
                        sqft = "".join([sqft, extra]).strip()
                        sqft = float("".join(x for x in sqft if x.isnumeric()))
                else:
                    #what edge case were you trying to fix here....  ehhh.  weird code dude
                    if ("bed" in extrafun) & ("bath" in extrafun):
                        beds, baths = extrafun.split(",")
                        #Because some toolbag didn't put the baths in 
                        #their listing.  smh.  
                    elif "bed" in extrafun:
                        beds = float(extrafun)
                    elif "bath" in extrafun:
                        baths = float(extrafun)

                if beds:
                    if any(x.isnumeric() for x in beds):
                        beds = float("".join(x for x in beds if x.isnumeric()))
                if baths:
                    if any(x.isnumeric() for x in baths):
                        baths = float("".join(x for x in baths if x.isnumeric() or x == "."))

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
        if PETS:
            url = f"https://www.apartments.com/houses-townhomes/{neigh}-{CITY}-{STATE}/min-{MINBEDS}-bedrooms-1000-to-{MAXRENT}-pet-friendly-dog/air-conditioning/"#
        else:
            url = f"https://www.apartments.com/houses-townhomes/{neigh}-{CITY}-{STATE}/min-{MINBEDS}-bedrooms-1000-to-{MAXRENT}/air-conditioning/"#
    
    #Searchby ZipCode
    elif isinstance(neigh, int):
        if PETS:
            url = f"https://www.apartments.com/houses-townhomes/{CITY}-{STATE}-{neigh}/min-{MINBEDS}-bedrooms-1000-to-{MAXRENT}-pet-friendly-dog/air-conditioning/"#air-conditioning/-garage
        else:
            url = f"https://www.apartments.com/houses-townhomes/{CITY}-{STATE}-{neigh}/min-{MINBEDS}-bedrooms-1000-to-{MAXRENT}/air-conditioning/"#air-conditioning/-garage
    #Error Trapping
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
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36',
        'referer': url,
        'origin':'https://www.apartments.com',
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
    nores = bs4ob.find_all("div", class_="no-results")
    if not nores:
        results = bs4ob.find("div", id="placardContainer")
        if results:
            property_listings = get_listings(results, neigh, source, logger, Propertyinfo, PETS)
            logger.info(f'{len(property_listings)} listings returned from {source}')
            return property_listings
            
    else:
        logger.warning("No listings returned on apartments.  Moving to next site")
