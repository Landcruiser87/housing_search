import logging
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests
import time


def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo)->list:
    """[Gets the list of links to the individual postings]

    Args:
        bs4ob ([BeautifulSoup object]): [html of realtor page]

    Returns:
        properties (list[Propertyinfo]): [all the links in the summary page]
    """

    listings = []
    #Set the outer loop over each card returned. 

    for card in result.select('div[class*="BasePropertyCard"]'):
        filtertest = card.get("id")
        if "placeholder_property" in filtertest:
            continue
        #Grab the id
        listingid = card.get("id")
        listingid = listingid.replace("property_id_", "")

        # Time of pull
        current_time = time.strftime("%m-%d-%Y_%H-%M-%S")

        #First grab the link.
        for link in card.find_all("a", class_="card-anchor"):
            if link.get("href"):
                url = "https://" + source + link.get("href")
                break
        
        #grab the price
        for search in card.find_all("div", class_="price-wrapper"):
            for subsearch in search.find_all("div"):
                if subsearch.get("data-testid") == "card-price":
                    price = subsearch.text
                    if any(x.isnumeric() for x in price):
                        price = money_launderer(subsearch.text)
                    break
        
        #grab the beds, baths, pets
        for search in card.find_all("ul"):
            if search.get("data-testid") == "card-meta":
                sqft = None
                for subsearch in search.find_all("li"):
                    if subsearch.get("data-testid")=="property-meta-beds":
                        beds = subsearch.find("span").text
                        if any(x.isnumeric() for x in beds):
                            beds = float("".join(x for x in beds if x.isnumeric()))

                    elif subsearch.get("data-testid")=="property-meta-baths":
                        baths = subsearch.find("span").text
                        if any(x.isnumeric() for x in baths):
                            baths = float("".join(x for x in baths if x.isnumeric()))

                    elif subsearch.get("data-testid")=="property-meta-sqft":
                        sqft = subsearch.find("span", class_="meta-value").text
                        if sqft:
                            if any(x.isnumeric() for x in sqft):
                                sqft = float("".join(x for x in sqft if x.isnumeric()))
            
    

        #grab address
        for search in card.find_all("div", class_="card-address truncate-line"):
            if search.get("data-testid") == "card-address":
                addy = ""
                for subsearch in search.find_all("div", class_="truncate-line"):
                    addy += subsearch.text + " "
                address = addy.strip()
        #Pets is already secured in the search query so we don't have to confirm it in the data.
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
            address=address,
            date_pulled=current_time
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
    CITY = citystate[0]
    STATE = citystate[1].upper()
    #Search by neighborhood
    if isinstance(neigh, str):
        if " " in neigh:
            neigh = "-".join(neigh.split(" "))
        url = f"https://www.realtor.com/apartments/{neigh}_{CITY}_{STATE}/type-townhome,single-family-home/beds-2/price-na-2600/dog-friendly"

    #Searchby ZipCode
    elif isinstance(neigh, int):
        url = f"https://www.realtor.com/apartments/{neigh}/type-townhome,single-family-home/beds-2/price-na-2600/dog-friendly"
    
    #Error Trapping
    else:
        logging.critical("Inproper input for area, moving to next site")
        return
    
    BASE_HEADERS = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'referer': url,
        'origin':'https://www.realtor.com',
    }

          
    response = requests.get(url, headers=BASE_HEADERS)

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
    results = bs4ob.find("section", {"data-testid":"property-list"})
    if results:
        property_listings = get_listings(results, neigh, source, Propertyinfo)
        logger.info(f'{len(property_listings)} listings returned from {source}')
        return property_listings
        
    else:
        logger.warning("No listings returned on realtor.  Moving to next site")
    