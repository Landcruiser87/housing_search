import logging
from bs4 import BeautifulSoup
import requests
import time
from typing import Union

def get_listings(result:BeautifulSoup, neigh:str, source:str, logger:logging, Propertyinfo)->list:
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
    listingid = price = beds = sqft = baths = pets = url = addy = current_time = None
    #Set the outer loop over each card returned. 
    for card in result.find_all("article"):
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
        for search in card.find_all("div", class_="property-info"):
            #Grab price
            for subsearch in search.find_all("div", class_="price-range"):
                price = subsearch.text
                if any(x.isnumeric() for x in price):
                    price = money_launderer(price.split(" ")[0])
                    
            #Grab bed bath
            for subsearch in search.find_all("div", class_="bed-range"):
                beds = subsearch.text
                if "ft" in beds:#lol
                    #quick comma count
                    count = beds.count(",")
                    if count < 3:
                        beds, baths, sqft = beds.split(",")
                        sqft = sqft.strip()
                    else:
                        #For if they put a comma in the square footage
                        beds, baths, sqft, extra = beds.split(",")
                        sqft = "".join([sqft, extra]).strip()
                    
                else:
                    beds, baths = beds.split(",")
                if any(x.isnumeric() for x in beds):
                    beds = float("".join(x for x in beds if x.isnumeric()))
                if any(x.isnumeric() for x in baths):
                    baths = float("".join(x for x in baths if x.isnumeric()))

        #grab address
        #BUG - might want to update the below.  Janky coding
        for search in card.find_all("a", class_="property-link"):
            if search.get("aria-label"):
                addy = search.get("aria-label")
            
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
    CITY = srch_par[0].lower()
    STATE = srch_par[1].lower()
    MINBEDS = int(srch_par[2])
    MAXRENT = int(srch_par[3])

    #Search by neighborhood
    if isinstance(neigh, str):
        if " " in neigh:
            neigh = "-".join(neigh.lower().split(" "))
        else:
            neigh = neigh.lower()
        url = f"https://www.apartments.com/houses-townhomes/{neigh}-{CITY}-{STATE}/min-{MINBEDS}-bedrooms-1000-to-{MAXRENT}-pet-friendly-dog/air-conditioning/"#-garage
    
    #Searchby ZipCode
    elif isinstance(neigh, int):
        url = f"https://www.apartments.com/houses-townhomes/{CITY}-{STATE}-{neigh}/min-{MINBEDS}-bedrooms-1000-to-{MAXRENT}-pet-friendly-dog/air-conditioning/"#-garage
    
    #Error Trapping
    else:
        logger.critical("Inproper input for area, moving to next site")
        return

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
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
        results = bs4ob.find("div", class_="placardContainer")
        if results:
            if results.get("id") =='placardContainer':
                property_listings = get_listings(results, neigh, source, logger, Propertyinfo)
                logger.info(f'{len(property_listings)} listings returned from {source}')
                return property_listings
            
    else:
        logger.warning("No listings returned on apartments.  Moving to next site")
