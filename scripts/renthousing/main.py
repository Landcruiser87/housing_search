#Import libraries
import numpy as np
import logging
import time
# from rich.logging import RichHandler
from rich.console import Console
from rich.live import Live
from dataclasses import dataclass, field
from os.path import exists
from random import shuffle  
from pathlib import Path, PurePath

#Import supporting files
import realtor, zillow, apartments, craigs, redfin, homes, support

################################# Variable Setup ####################################
# input custom area's here. Uncomment whichever way you want to search
# AREAS = [
# 20003, 20007, 20008, 20009, 20057, 20015, 20016
# #Problem zips 22201,22101, 22207 - In Arlington.  Need to run arlington separately
# ]

# pound sign to the right of neighborhood means its a city of chicago neighborhood, 
# if doesn't have one, its a smaller targeted neighborhood.
AREAS = [
    'Portage Park',    #
    'Ravenswood',
    'Irving Park',     #
    'Albany Park',     #
    'North Center',    #
    'North Park',      #
    'Lincoln Square',  #    
    'Avondale',        #    #New add
    'Wicker Park',     #    #New add
    'Roscoe Village',
    'Budlong Woods',
    'Mayfair',
    # 'Jefferson Park',   #too far out
    # 'West Ridge',       #too far out
    # 'Rogers Park',
    # 'West Town', 
    # 'Humboldt Park'
    # 'Ravenswood Gardens',
]

# SF Testing
# AREAS = [
#     "Mission District",
#     "Sunset District",
#     "Chinatown",
#     "Nob Hill"
# ]

SOURCES = {
    "realtor"   :("www.realtor.com"   , realtor),
    "apartments":("www.apartments.com", apartments),
    "craigs"    :("www.craigslist.org" , craigs),
    "zillow"    :("www.zillow.com"    , zillow),
    "redfin"    :("www.redfin.com"    , redfin),
    "homes"     :("www.homes.com"     , homes)
}

SITES = ["homes", "apartments", "realtor", "redfin", "zillow", "craigs"]

# Define City / State / Minimum beds, Max rent, and whether you have a dog (sorry cat people.  You're on your own.  Lol)
CITY    = "Chicago"
STATE   = "IL"
MINBEDS = 2
MAXRENT = 2600
DOGS    = True


# DC test data notes
# CITY    = "Washington"
# STATE   = "DC"
# MINBEDS = 2
# MAXRENT = 4000
# DOGS    = True

# SF Testing
# CITY    = "San Francisco"
# STATE   = "CA"
# MINBEDS = 2
# MAXRENT = 3000
# DOGS    = True

SEARCH_PARAMS = (
    CITY,
    STATE,
    MINBEDS,
    MAXRENT,
    DOGS
)

LOST_N_FOUND = {
    "apartments":False,
    "craigs"    :False,
    "homes"     :False,
    "redfin"    :False,
    "realtor"   :False,
    "zillow"    :False
}

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
#FUNCTION Log time
################################# Timing Func ####################################
def log_time(fn):
    """Decorator timing function.  Accepts any function and returns a logging
    statement with the amount of time it took to run. DJ, I use this code everywhere still.  Thank you bud!

    Args:
        fn (function): Input function you want to time
    """	
    def inner(*args, **kwargs):
        tnow = time.time()
        out = fn(*args, **kwargs)
        te = time.time()
        took = round(te - tnow, 2)
        if took <= 60:
            logging.warning(f"{fn.__name__} ran in {took:.2f}s")
        elif took <= 3600:
            logging.warning(f"{fn.__name__} ran in {(took)/60:.2f}m")		
        else:
            logging.warning(f"{fn.__name__} ran in {(took)/3600:.2f}h")
        return out
    return inner

################################# Main Funcs ####################################
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

    logger.info(f"data added for {siteinfo[0]} in {siteinfo[1]}")
    logger.info(f"These ids were added to storage: {ids}")

#FUNCTION Check IDs
def check_ids(data:list)->list:
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
def scrape(neigh:str, progbar, task, layout):
    """This function will iterate through different resources scraping necessary information for ingestion. 

    Args:
        neigh (str): Neighborhood or Zipcode
    # """	
    shuffle(SITES) #Keep em guessin!
    for source in SITES:
        site = SOURCES.get(source)
        if site:
            #Update and advance the overall progressbar
            progbar.advance(task)
            progbar.update(task_id=task, description=f"{neigh}:{site[0]}")
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
            support.run_sleep(np.random.randint(3,8), f'Napping at {site[0]}', layout)

            #If data was returned
            if data:
                #If there was data found on a site, Update the site counter's border to 
                #magenta.  Letting me know the site is still successfully returning data.
                    #NOTE: Some sites will still return a 200 but change a variable name in the DOM
                    # which leads to missing data.
                res_test = LOST_N_FOUND[source]
                if not res_test:
                    layout[source].update(support.update_border(layout, source))
                    LOST_N_FOUND[source] = True

                #This function will isolate new id's that aren't in the historical JSON
                datacheck = check_ids(data)
                if datacheck:
                    logger.info("New data found, adding lat/lon/Lstop/crime")
                    data = datacheck
                    del datacheck

                    #update the total counter
                    layout["total"].update(support.update_count(len(data), layout, "total"))

                    #Update other counters
                    for row in data:
                        for website in SITES:
                            if website in row.source:
                                layout[website].update(support.update_count(1, layout, website))
                                break
                        
                    #pull the lat long, score it and store it. 
                    data = support.get_lat_long(data, (CITY, STATE), logger, layout)

                    #If its chicago, do chicago things. 
                    if CITY == 'Chicago':
                        #Calculate the distance to closest L stop 
                        #(haversine/as crow flies)
                        data = support.closest_L_stop(data)

                        #Score them according to chicago crime data
                        data = support.crime_score(data, logger, layout)
                        
                    # elif CITY == 'DC':
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
################################# Start Program ####################################
#Driver code
#FUNCTION Main start
@log_time
def main():
    #Global variables setup
    global newlistings, jsondata, c_scrape
    c_scrape = False
    newlistings = []
    fp = "./data/rental_list.json"
    totalstops = len(AREAS) * len(SITES)

    global logger, console
    console = Console(color_system="auto")
    log_path = PurePath(Path.cwd(), Path("./data/logs"))
    logger = support.get_logger(log_path, console=console)
    layout, progbar, task, main_table = support.make_rich_display(totalstops)

    #Load rental_list.json
    if exists(fp):
        jsondata = support.load_historical(fp)
        logger.info("historical data loaded")
    else:
        jsondata = {}
        logger.warning("No historical data found")

    #Shuffle and search the neighborhoods/zips
    shuffle(AREAS)

    with Live(layout, refresh_per_second=30, screen=True, transient=True):
        logger.addHandler(support.MainTableHandler(main_table, layout, logger.level))
        for neigh in AREAS:
            scrape(neigh, progbar, task, layout)
        
        # If new listings are found, save the data to the json file, 
        # format the list of dataclassses to a url 
        # Send gmail alerting of new properties
        if newlistings:
            support.save_data(jsondata)
            links_html = support.urlformat(newlistings)
            # support.send_housing_email(links_html)
            logger.info(f"{len(newlistings)} new listings found.  Email sent")
            
        else:
            logger.critical("No new listings were found")

        logger.info("Site functionality summary")
        logger.info(f"{list(LOST_N_FOUND.items())}")
        logger.info("Program shutting down")

if __name__ == "__main__":
    main()

    #TODO Add rotating proxy's
        #https://www.scrapehero.com/how-to-rotate-proxies-and-ip-addresses-using-python-3/
    #TODO Add rotating headers
        #https://www.scrapehero.com/how-to-fake-and-rotate-user-agents-using-python-3/
        #https://www.scrapehero.com/essential-http-headers-for-web-scraping/

#Notes
# import json
# fp = "../../data/rental_list.json"
# with open(fp, "r") as readf:
# 	results = json.load(readf)	
# sorted(results.items(), key=lambda x:x[1]["price"], reverse=True)[10:15]