import logging
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests

def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo)->list:
    """[Gets the list of links to the individual postings]

    Args:
        bs4ob ([BeautifulSoup object]): [html of realtor page]

    Returns:
        properties (list[Propertyinfo]): [all the links in the summary page]
    """

    listings = []
    #Set the outer loop over each card returned. 
    for card in result.find_all("article"):
        #Grab the id
        listingid = card.get("data-listingid")

        #First grab the link
        if card.get("data-url"):
            url = card.get("data-url")

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
                        beds, baths, sqft, extra = beds.split(",")
                        sqft = "".join([sqft, extra]).strip()
                    #BUG
                    #Found the problem.  Someone put a comma in the number for
                    #square footage so need improved logic for text extraction here. 

                else:
                    beds, baths = beds.split(",")
                if any(x.isnumeric() for x in beds):
                    beds = float("".join(x for x in beds if x.isnumeric()))
                if any(x.isnumeric() for x in baths):
                    baths = float("".join(x for x in baths if x.isnumeric()))

        #grab address
        for search in card.find_all("a", class_="property-link"):
            if search.get("aria-label"):
                addy = search.get("aria-label")
        
        pets = True

        #Janky way of making sure variables are filled if we missed any
        if not "listingid" in locals():
            listingid = None
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
            address=addy
        )
        listings.append(listing)

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

def neighscrape(neigh:str, source:str, logger:logging, Propertyinfo, citystate):
    CITY = citystate[0].lower()
    STATE = citystate[1].upper()
    #Search by neighborhood
    if isinstance(neigh, str):
        if " " in neigh:
            neigh = "-".join(neigh.lower().split(" "))
        url = f"https://www.apartments.com/houses-townhomes/{neigh}-{CITY}-{STATE}/min-2-bedrooms-under-2600-pet-friendly-dog/"
    
    #Searchby ZipCode
    elif isinstance(neigh, int):
        url = f"https://www.apartments.com/houses-townhomes/{CITY}-{STATE}-{neigh}/min-2-bedrooms-under-2600-pet-friendly-dog/"	
    
    #Error Trapping
    else:
        logging.critical("Inproper input for area, moving to next site")
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
    nores = bs4ob.find_all("article", class_="noPlacards")
    if not nores:
        results = bs4ob.find("div", class_="placardContainer")
        if results:
            if results.get("id") =='placardContainer':
                property_listings = get_listings(results, neigh, source, Propertyinfo)
                logger.info(f'{len(property_listings)} listings returned from {source}')
                return property_listings
            
    else:
        logger.warning("No listings returned on apartments.  Moving to next site")
