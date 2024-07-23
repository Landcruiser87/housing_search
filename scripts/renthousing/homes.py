import logging
from bs4 import BeautifulSoup
import requests
import time
from typing import Union

def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo)->list:
    """[Ingest HTML of summary page for listings info]

    Args:
        result (BeautifulSoup object): html of apartments page
        neigh (str): neighorhood being searched
        source (str): Source website
        Propertyinfo (dataclass) : Dataclass for housing individual listings

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
        search = card.find("article", "search-placard for-rent-mls-placard")
        if search:
            listingid = search.get("data-pk")
        else:
            continue
        details = card.find("div", class_="for-rent-content-container")
        if details:
            #grab address
            res = card.find("p", class_="address")
            if res:
                addy = res.text
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
                        price = int("".join(x for x in testval if x.isnumeric()))
                    #Grab Beds
                    elif "beds" in testval.lower():
                        beds = int("".join(x for x in testval if x.isnumeric()))
                    #Grab baths
                    elif "baths" in testval.lower():
                        baths = int("".join(x for x in testval if x.isnumeric()))
                    #! SQFT is available on the individual links, but not worth
                    #! the extra call to grab it

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
        url = f"https://www.homes.com/{CITY}-{STATE}/{neigh}-neighborhood/homes-for-rent/{MINBEDS}-{5}-bedroom/?property_type=1,2&am=31,16&price-min=1000&price-max={MAXRENT}"
    #Searchby ZipCode
    elif isinstance(neigh, int):
        url = f"https://www.homes.com/{CITY}-{STATE}/{neigh}/homes-for-rent/{MINBEDS}-to-5-bedroom/?property_type=1,2&am=31,16&price-min=1000&price-max={MAXRENT}"

    #Error Trapping
    else:
        logging.critical("Inproper input for area, moving to next site")
        return

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
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
    if not nores:
        results = bs4ob.find("section", class_="placards")
        if results:
            if results.get("id") =='placardContainer':
                property_listings = get_listings(results, neigh, source, Propertyinfo)
                logger.info(f'{len(property_listings)} listings returned from {source}')
                return property_listings
            
    else:
        logger.warning("No listings returned on apartments.  Moving to next site")
