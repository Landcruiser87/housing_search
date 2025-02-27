import logging
from bs4 import BeautifulSoup
import requests
import time
from typing import Union

def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo)->list:
    """[Ingest HTML of summary page for listings info]

    Args:
        result [BeautifulSoup object]: html of realtor page
        neigh (str): neighorhood being searched
        source (str): Source website
        Propertyinfo (dataclass) : Dataclass for housing individual listings

    Returns:
        listings (list): [List of dataclass objects]
    """

    listings = []
    listingid = price = beds = sqft = baths = pets = url = address = current_time = None
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
        for search in card.find_all("div"):
            if search.get("data-testid") == "card-price":
                price = search.text
                if any(x.isnumeric() for x in price):
                    price = money_launderer(search.text)
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
                            baths = float("".join(x for x in baths if x.isnumeric() or x == "."))

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

        listing = Propertyinfo(
            id=listingid,
            source=source,
            price=price,
            neigh=neigh.lower(),
            bed=beds,
            sqft=sqft,
            bath=baths,
            dogs=pets,
            link=url,
            address=address,
            date_pulled=current_time
        )
        listings.append(listing)
        listingid = price = beds = sqft = baths = pets = url = address = current_time = None
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
    CITY = srch_par[0]
    STATE = srch_par[1].upper()
    MINBEDS = int(srch_par[2])
    MAXRENT = int(srch_par[3])
    PETS = srch_par[4]
    #Search by neighborhood
    if isinstance(neigh, str):
        if " " in neigh:
            neigh = "-".join(neigh.split(" "))
        if PETS:
            url = f"https://www.realtor.com/apartments/{neigh}_{CITY}_{STATE}/type-townhome,single-family-home/beds-{MINBEDS}/price-na-{MAXRENT}/dog-friendly"#g1
        else:
            url = f"https://www.realtor.com/apartments/{neigh}_{CITY}_{STATE}/type-townhome,single-family-home/beds-{MINBEDS}/price-na-{MAXRENT}"#g1

    #Searchby ZipCode
    elif isinstance(neigh, int):
        if PETS:
            url = f"https://www.realtor.com/apartments/{neigh}/type-townhome,single-family-home/beds-{MINBEDS}/price-na-{MAXRENT}/dog-friendly"#g1
        else:
            url = f"https://www.realtor.com/apartments/{neigh}/type-townhome,single-family-home/beds-{MINBEDS}/price-na-{MAXRENT}"#g1
    
    #Error Trapping
    else:
        logging.critical("Inproper input for area, moving to next site")
        return None
    
    # BASE_HEADERS = {
    #     'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    #     'accept-language': 'en-US,en;q=0.9',
    #     'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="122", "Chromium";v="122"',
    #     'sec-ch-ua-mobile': '?1',
    #     'sec-ch-ua-platform': '"Android"',
    #     'sec-fetch-dest': 'iframe',
    #     'sec-fetch-mode': 'navigate',
    #     'sec-fetch-site': 'cross-site',
    #     'sec-fetch-user': '?1',
    #     'upgrade-insecure-requests': '1',
    #     'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    #     'referer': url,
    #     'origin':'https://www.realtor.com',
    # }

    BASE_HEADERS = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'referer': url,
        'origin':'https://www.realtor.com',
        'priority': 'u=1, i',
        'sec-ch-ua': '"Not(A:Brand";v="99", "Google Chrome";v="120", "Chromium";v="120"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'cross-site',
        'user-agent': 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36',
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
    