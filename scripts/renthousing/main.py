#Import libraries
import numpy as np
import logging
import time
from rich.logging import RichHandler
from logging import Formatter
from rich.console import Console
from dataclasses import dataclass, field
from os.path import exists
from random import shuffle

#Import supporting files
import realtor, zillow, apartments, craigs, redfin, support

#Format logger and load configuration
current_date = time.strftime("%m-%d-%Y_%H-%M-%S")
FORMAT = "%(asctime)s|%(levelname)-8s|%(lineno)-3d|%(funcName)-18s|%(message)s|" #[%(name)s]
FORMAT_RICH = "| %(lineno)-3d | %(funcName)-18s | %(message)s "

console = Console(color_system="truecolor")
rh = RichHandler(level = logging.INFO, console=console)
rh.setFormatter(Formatter(FORMAT_RICH))

logging.basicConfig(
    level=logging.INFO, 
    format=FORMAT, 
    datefmt="[%X]",
    handlers=[
        rh, #Rich formatted logger sent to terminal
        logging.FileHandler(f'./data/logs/{current_date}.log', mode='w') #To send log messages to log file
    ]
)

#Load logger
logger = logging.getLogger(__name__) 

#input custom area's here. Uncomment whichever way you want to search
# sign to the right of neighborhood means its a  city of chicago neighborhood, if not its a smaller neighborhood.

# AREAS = [
# 20003, 20007, 20008, #20009, 22201, 22207, 22101, 200057, 20015, 20016
# ]


AREAS = [
    'Mayfair',
    'Portage Park',    #
    'North Center',    #
    'North Park',      #
    'Albany Park',     #
    'Ravenswood',
    'Roscoe Village',
    'Lincoln Square',  #
    'Irving Park',     #
    'Budlong Woods',
    'Avondale',        #    #New add
    'Wicker Park'      #    #New add
    # 'Jefferson Park',   #too far out
    # 'West Ridge',       #too far out

    # 'Rogers Park',
    # 'West Town', 
    # 'Humboldt Park'
    # 'Ravenswood Gardens',
]

SOURCES = {
    "realtor"   :("www.realtor.com"   , realtor),
    "apartments":("www.apartments.com", apartments),
    "craigs"    :("www.craiglist.org" , craigs),
    "zillow"    :("www.zillow.com"    , zillow),
    "redfin"    :("www.redfin.com"    , redfin)
}

# 
# DC test data notes
# minbed = 2
# top_price = 4000
# home = "home/townhome"
# CITY    = "Washington"
# STATE   = "DC"
# MINBEDS = 2
# MAXRENT = 4000
# DOGS    = True

# Define City / State / Minimum beds, Max rent, and whether you have a dog (sorry cat people.  You're on your own.  Lol)
CITY    = "Chicago"
STATE   = "IL"
MINBEDS = 2
MAXRENT = 2600
DOGS    = True

SEARCH_PARAMS = (
    CITY,
    STATE,
    MINBEDS,
    MAXRENT,
    DOGS
)

#Define dataclass container
@dataclass
class Propertyinfo():
    id          : str
    source      : str
    price       : str
    neigh       : str
    dogs        : bool
    link        : str
    address     : str
    date_pulled : np.datetime64
    bed         : float = None
    bath        : float = None
    sqft        : float = None
    lat         : float = ""
    long        : float = ""
    L_dist      : float = ""
    crime_sc    : dict = field(default_factory=lambda:{})
    # cri_dat : np.ndarray #Eventually to store week to week crime data here for each listing
    # def dict(self):
    #     return {k: str(v) for k, v in asdict(self).items()}

#FUNCTION Add Data
def add_data(data:list, siteinfo:tuple):
    """Adds Data to JSON Historical file

    Args:
        data (list): List of Propertyinfo objects that are new (not in the historical)
        siteinfo (tuple): Tuple of website and neighborhood/zip
    """	
    ids = [data[x].id for x in range(len(data))]
    #Reshape data to dict
    #make a new dict that can be json serialized with the id as the key
    new_dict = {data[x].id : data[x].__dict__ for x in range(len(data))}
    #Pop the id from the dict underneath (no need to store it twice)
    [new_dict[x].pop("id") for x in ids]

    #update main data container
    jsondata.update(new_dict)
    
    #make tuples of (urls, site, neighborhood) for emailing
    newurls = [(new_dict[idx].get("link"), siteinfo[0].split(".")[1], (new_dict[idx].get("neigh"))) for idx in new_dict.keys()]
    #Extend the newlistings global list
    newlistings.extend(newurls)

    logger.info("Global dict updated")
    logger.info(f"data added for {siteinfo[0]} in {siteinfo[1]}")

#FUNCTION Check IDs
def check_ids(data:list):
    """This function takes in a list of Propertyinfo objects, reformats them to
    a dictionary, compares the property id's to existing JSON historical
    property id keys, finds any new ones via set comparison. Then returns a list
    of Propertyinfo objects that have those new id's (if any)

    Args:
        data (list): List of Propertyinfo objects

    Returns:
        data (list): List of only new Propertyinfo objects
    """	
    j_ids = set(jsondata.keys())
    n_ids = set([data[x].id for x in range(len(data))])
    newids = n_ids - j_ids
    if newids:
        #Only add the listings that are new.  
        newdata = []
        [newdata.append(data[idx]) for idx, _ in enumerate(data) if data[idx].id in newids]
        return newdata
    else:
        logger.info("Listing(s) already stored in rental_list.json") 
        return None

#FUNCTION Scrape data
def scrape(neigh:str):
    """This function will iterate through different resources scraping necessary information for ingestion. 

    Args:
        neigh (str): Neighborhood or Zipcode
    """	
    sites = ["apartments", "zillow", "redfin", "realtor", "craigs"]
    shuffle(sites) #Keep em guessin!
    for source in sites:
        site = SOURCES.get(source)
        if site:
            #Because we can't search craigs by neighborhood, we only want to
            #scrape it once.  So this sets a boolean of if we've scraped
            #craigs, then flips the value to not scrape it again in the
            #future neighborhoods that will be searched. 
            global c_scrape
            if source=="craigs" and c_scrape==False:
                c_scrape = True
                logger.info(f"scraping {site[0]}")
                data = site[1].neighscrape(neigh, site[0], logger, Propertyinfo, SEARCH_PARAMS, jsondata)

            elif source=="craigs" and c_scrape==True:
                continue
            
            else:
                #every other site, scrape it normally
                logger.info(f"scraping {site[0]} for {neigh}")
                data = site[1].neighscrape(neigh, site[0], logger, Propertyinfo, SEARCH_PARAMS)

            #Take a lil nap.  Be nice to the servers!
            support.sleepspinner(np.random.randint(3,8), f'taking a nap at {site[0]}')

            #If data was returned
            if data:
                #This function will isolate new id's that aren't in the historical JSON
                datacheck = check_ids(data)
                if datacheck:
                    logger.info("New data found, adding lat/lon/Lstop/crime")
                    #pull the lat long, score it and store it. 
                    data = datacheck
                    del datacheck
                    #Get lat longs for the address's    
                    data = support.get_lat_long(data, (CITY, STATE), logger)

                    #If its chicago, do chicago things. 
                    if CITY == 'Chicago':
                        #Calculate the distance to closest L stop 
                        #(haversine/as crow flies)
                        data = support.closest_L_stop(data)

                        #Score them according to chicago crime data
                        data = support.crime_score(data, logger)
                    # elif CITY == 'DC':
                        # pass
                        #TODO - Build DC search for 
                        #closets train stop and 
                        #crime score if you can find any data
                    #Add the listings to the jsondata dict. 
                    add_data(data, (site[0], neigh))
                    del data
            else:
                logger.info(f"No new data found on {source}")

        else:
            logger.warning(f"{source} is not in validated search list")

#Driver code
#FUNCTION Main start
def main():
    #Global variable setup
    global newlistings, jsondata, c_scrape
    c_scrape = False
    newlistings = []
    fp = "./data/rental_list.json"
    #Load historical listings JSON

    if exists(fp):
        jsondata = support.load_historical(fp)
        logger.info("historical data loaded")
    else:
        jsondata = {}
        logger.warning("No historical data found")
        
    #Shuffle and search the neighborhoods/zips
    shuffle(AREAS)
    for neigh in AREAS:
        scrape(neigh)

    # If new listings are found, save the data to the json file, 
    # format the list of dataclassses to a url 
    # Send gmail alerting of new properties
 
    if newlistings:
        # support.save_data(jsondata)
        links_html = support.urlformat(newlistings)
        support.send_housing_email(links_html)
        logger.info(f"{len(newlistings)} new listings found.  Email sent")

    else:
        logger.critical("No new listings were found")

    logger.info("Program shutting down")

if __name__ == "__main__":
    main()


#Notes
# import json
# fp = "../../data/rental_list.json"
# with open(fp, "r") as readf:
# 	results = json.load(readf)	
# sorted(results.items(), key=lambda x:x[1]["price"], reverse=True)[10:15]
