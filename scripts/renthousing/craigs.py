import logging
from bs4 import BeautifulSoup
import numpy as np
import requests
import time
import support

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

def get_links(bs4ob:BeautifulSoup, CITY:str)->list:
    """[Gets the list of links to the individual postings]

    Args:
        bs4ob ([BeautifulSoup object]): [html of craigslist summary page]

    Returns:
        links (list): [all the links in the summary page]
    """	
    #TODO - craig update city
        #Need a base dictionary of craiglist citys and the city codes they use. 
        #That way we can format the links properly by city. 
    
    links = []
    if CITY =='chicago':
        url_pref = f"https://{CITY}.craigslist.org/chc"
    elif CITY == 'washingtondc':
        url_pref = f"https://washingtondc.craigslist.org/doc"
    else:
        url_pref = f"https://{CITY}.craigslist.org/"

    for link in bs4ob.find_all('a'):
        url = link.get("href")
        if url.startswith(url_pref):
            links.append(url)
    return links
    
def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo, logger, srch_par:tuple, jsondata:dict)->list:
    """_summary_

    Args:
        result (BeautifulSoup): Search Result
        neigh (Union[str,int]): Neighborhood or zipcode searched
        source (str): What site is being scraped
        Propertyinfo (dataclass): Custom data object
        logger (logging.logger): logger for logging
        citystate (tuple): Tuple of city/state
        jsondata (dict): Data uploaded from rental_list.json

    Returns:
        properties (list[Propertyinfo]): [all the links in the summary page]
    """			

    CITY = srch_par[0].lower()
    if CITY == "washington":
        CITY = "washingtondc"
    
    HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Origin': f'https://{CITY}.craigslist.org',
        'Referer': f'https://{CITY}.craigslist.org/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }

    listings = []
    
    #lat long info is in here.  Could merge them with the search. 
    #result.select_one('script[id*="ld_searchpage_results"]')
    # contents = json.loads(card.contents[0].strip("\n").strip())
    links = get_links(result, CITY)
    
    for link in links: 
        #Get posting id from the url.
        listingid = link.split('/')[-1].strip(".html")
        
        if listingid in jsondata.keys():
            logger.info("listing already exists in json container")		
            continue

        #Being that craigs doesn't put all the info in the search page cards,
        #we've gotta Dig for the details like we did last time by scraping each
        #listing.  Meaning more requests and longer wait times. 

        response = requests.get(link, headers=HEADERS)
        support.sleepspinner(np.random.randint(4, 6), f'Craigs {neigh} request nap')
        bs4ob = BeautifulSoup(response.text, "lxml")

        #Just in case we piss someone off
        if response.status_code != 200:
            # If there's an error, log it and return no data for that site
            logger.warning(f'Status code: {response.status_code}')
            logger.warning(f'Reason: {response.reason}')
            continue
        
        #assign the url
        url = link

        # Time of pull
        current_time = time.strftime("%m-%d-%Y_%H-%M-%S")

        # Grab the price.
        for search in bs4ob.find_all("span", class_="price"):
            price = search.text
            if any(x.isnumeric() for x in price):
                price = money_launderer(search.text)
            break

        #grab bed / bath
        for search in bs4ob.find_all("span", class_="attr important"):
            text = search.text.lower()
            if "ft" in text:
                sqft = search.text.strip("\n").strip()
                #bug, maybe remove ft
            elif "br" in text:
                beds, baths = search.text.strip("\n").strip().split("/")
                if any(x.isnumeric() for x in beds):
                    beds = float("".join(x for x in beds if x.isnumeric()))
                if any(x.isnumeric() for x in baths):
                    baths = float("".join(x for x in baths if x.isnumeric()))

        #grab addy
        for search in bs4ob.find_all("h2", class_="street-address"):
            addy = search.text
            break

        #grab lat / long
        for search in bs4ob.find_all("div", {"id":"map"}):
            try:
                lat = float(search.get("data-latitude"))
            except:
                lat = None
                logger.warning("Lat not a float")
            try:
                long = float(search.get("data-longitude"))
            except:
                long = None
                logger.warning("Long not a float")

            

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
        
        pets = True

        listing = Propertyinfo(
            id=listingid,
            source=source,
            price=price,
            neigh=CITY,
            bed=beds,
            sqft=sqft,
            bath=baths,
            dogs=pets,
            link=url,
            address=addy,
            lat=lat,
            long=long,
            date_pulled=current_time
        )
        listings.append(listing)
        listingid = price = beds = sqft = baths = pets = url = addy = current_time = lat = long =  None
    return listings

def neighscrape(neigh:str, source:str, logger:logging, Propertyinfo, srch_par:tuple, jsondata:dict):
    CITY = srch_par[0].lower()
    if CITY == "washington":
        CITY = "washingtondc"

    minbeds = int(srch_par[2])
    maxrent = int(srch_par[3])

    HEADERS = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Connection': 'keep-alive',
        'Origin': f'https://{CITY}.craigslist.org',
        'Referer': f'https://{CITY}.craigslist.org/',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'same-origin',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
    }
    #Change these to suit your housing requirements
    #!Update tprice and min bed
    params = (
        ("airconditioning","1"),
        ("hasPic", "1"),
        # ("postedToday", "1"),
        ("housing_type",["10", "3", "4", "5", "6", "8", "9"]),
        ("min_price", "500"),
        ("max_price", maxrent),
        ("min_bedrooms", minbeds),
        ("min_bathrooms", "1"),
        ("availabilityMode", "0"), #can't seem to verify this parameter in the url
        ("pets_dog", "1"),
        ("laundry", ["1", "2", "3"]),
        ("parking", ["2", "3", "4", "5"]),
        # ("sale_date", "all dates"), #left over param for buying 
    )

    #[x] - craig update city
        #Need a base dictionary of craiglist citys and the city codes they use. 
        #That way we can format the links properly by city. 
        #Or just hardcode DC because that dictionary would be huge.
        #?Could input it as a separate function in the script. 

    if CITY == 'chicago':
        url = f'https://{CITY}.craigslist.org/search/chc/apa'
    
    elif CITY == 'washingtondc':
        url = f'https://washingtondc.craigslist.org/search/doc/apa'

    else:
        url = f'https://{CITY}.craigslist.org/search/apa'

    #BUG
    # So....  craigs encodes region into their URL.  So you'll have to change
    #that. You can remove the chc from the search link to search an entire city,
    #But that will likely generate too many results. 
 
    response = requests.get(url, headers=HEADERS, params=params)

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
    results = bs4ob.find_all("li", class_="cl-static-search-result")
    if results:
        if len(results) > 0:
            property_listings = get_listings(bs4ob, neigh, source, Propertyinfo, logger, srch_par, jsondata)
            logger.info(f'{len(property_listings)} listings returned from {source}')
            return property_listings
    
    else:
        logger.warning("No listings returned on craigs.  Moving to next site")

