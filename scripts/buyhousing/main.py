#Import libraries
import numpy as np
from random import shuffle
from rich.live import Live
from rich.progress import Progress
from rich.layout import Layout
from os.path import exists
from dataclasses import dataclass, field
from collections import Counter

#Import supporting files
import realtor, zillow, redfin, homes, support
#Import logger and console from support
from support import logger, console, log_time, get_time

################################# Variable Setup ####################################
# input custom area's here. Uncomment whichever way you want to search

#NOTE - Be sure to run these as a list of ints.  This software uses the datatype to dictate logic
# AREAS = [80108, 80110, 80111, 80112, 80120, 80121, 80122,
#     80124, 80126, 80129, 80130, 80236, 80237
# ]

# pound sign to the right of neighborhood means its a city of chicago neighborhood, 
# if doesn't have one, its a smaller targeted neighborhood.

AREAS = [
    ('Angola'   ,'IN'),
    ('Auburn'   ,'IN'),
    ('Fremont'  ,'IN'),
    ('Orland'   ,'IN'),
    ('Coldwater','MI'),    #guuuurl.  You gots lots of housing price cuts.  No bueno market!
    ('Marshall' ,'MI'),
    ('Tekonsha' ,'MI'),
    # ('Portage'  ,'MI'),
]

SOURCES = {
    "homes"  :("www.homes.com"  , homes),
    "realtor":("www.realtor.com", realtor),
    "redfin" :("www.redfin.com" , redfin),
    "zillow" :("www.zillow.com" , zillow),
}

SITES = ["zillow", "homes", "realtor", "redfin"] 

#Define search parameters
MAXPRICE = 900_000
MINBATHS = 2
MINBEDS  = 4

SEARCH_PARAMS = (
    MAXPRICE,
    MINBATHS,
    MINBEDS,
)

#Dictionary to keep track of which sites return data in a singular run
LOST_N_FOUND = {
    "homes"   :False,
    "realtor" :False,
    "redfin"  :False,
    "zillow"  :False
}


#Define dataclass container
@dataclass
class Propertyinfo():
    id          : str = None
    address     : str = None
    city        : str = None
    state       : str = None
    url         : str = None
    price       : int = None
    source      : str = None
    status      : str = None
    img_url     : str = None
    date_pulled : str = None
    description : str = None
    htype       : str = None
    beds        : float = None
    baths       : float = None
    lotsqft     : float = None
    sqft        : float = None
    price_sqft  : int = None
    lat         : float = None
    long        : float = None
    zipc        : int = None
    list_dt     : str = None
    price_ch_amt: int = None #last_pri_cha
    last_price  : int = None
    price_c_dat : str = None
    seller      : dict = field(default_factory=lambda:{})
    sellerinfo  : dict = field(default_factory=lambda:{})    
    extras      : dict = field(default_factory=lambda:{})
    
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
    newurls = [(new_dict[idx].get("url"), siteinfo[0].split(".")[1], new_dict[idx].get("city"), new_dict[idx].get("address"), new_dict[idx].get("price_ch_amt"), new_dict[idx].get("price")) for idx in new_dict.keys()]
    
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
    
    #Look for new ids (difference)
    newids = n_ids - j_ids
    newdata, pricechanges = None, None

    #Look for same ids in the new and old (intersection)
    common_ids = n_ids & j_ids
    p_chn_ids = set()
    for ids in common_ids:
        idx = [data[x].id == ids for x in range(len(data))]
        idx = idx.index(True)
        if jsondata[ids].get("price") != data[idx].price:
            data[idx].price_ch_amt = data[idx].price - jsondata[ids]["price"]
            data[idx].price_c_dat = get_time().strftime("%m-%d-%Y_%H-%M-%S")
            data[idx].last_price = jsondata[ids]["price"]
            p_chn_ids.add(ids)
        
    if newids:
        # Filter the list of properties by id
        newdata = list(filter(lambda listing : listing.id in newids, data))

    if p_chn_ids:
        #Filter the saved jsondata for price changes
        pricechanges = list(filter(lambda listing : listing.id in p_chn_ids, data))
        logger.info(f"Price changes on {p_chn_ids}")

    newcheck = isinstance(newdata, list)
    pricecheck = isinstance(pricechanges, list)

    if newcheck & pricecheck:
        newdata.extend(pricechanges)
        return newdata

    elif newcheck:
        return newdata
    
    elif pricecheck:
        return pricechanges
    else:
        logger.info("Listing(s) already stored in buy_list.json") 
        return None
    
    #Old code keeping for now
    # newdata = []
    # data_ids = [(idx, data[idx].id) for idx in range(len(data))]
    # #Only add the listings that are new.  
    # for ids in newids:
    #    indx = [x[0] for x in data_ids if x[1]==ids][0]
    #    newdata.append(data[indx]) 
    # return newdata

#FUNCTION Scrape data
def scrape(area:tuple|str, progbar:Progress, task:int, layout:Layout):
    """This function will iterate through different resources scraping necessary information for ingestion. 

    Args:
        area (str): City or or Zipcode
    # """	
    #Keep em guessin!
    # shuffle(SITES) 
    for source in SITES:
        site = SOURCES.get(source)
        if site:
            #Update and advance the overall progressbar
            progbar.advance(task)
            progbar.update(task_id=task, description=f"{area[0]}:{site[0]}")
            logger.info(f"scraping {site[0]} for {area[0]}")
            data = site[1].area_search(area, site[0], Propertyinfo, SEARCH_PARAMS)

            #Take a lil nap.  Be nice to the servers!
            support.run_sleep(np.random.randint(3,8), f'Napping at {site[0]}', layout)

            #If data was returned
            if data:
                #If there was data found on a site, Update the site counter's border to 
                #magenta.  Letting me know the site is still successfully returning data.
                res_test = LOST_N_FOUND[source]
                if not res_test:
                    layout[source].update(support.update_border(layout, source))
                    LOST_N_FOUND[source] = True

                #This function will isolate new id's that aren't in the historical JSON
                datacheck = check_ids(data)
                if datacheck:
                    logger.info("New data found, checking lat/lon")
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
                        
                    #pull the lat long
                    data = support.get_lat_long(data, area, layout)
                    
                    # Add the listings to the jsondata dict. 
                    add_data(data, (site[0], area[0]))
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
    global newlistings, jsondata
    newlistings = []
    fp = "./data/buy_list.json"
    totalstops = len(AREAS) * len(SITES) + 1
    layout, progbar, task, main_table = support.make_rich_display(totalstops)

    #Load rental_list.json
    if exists(fp):
        jsondata = support.load_historical(fp)
        logger.info("historical data loaded")
    else:
        jsondata = {}
        logger.warning("No historical data found")

    #Shuffle and search the neighborhoods/zips
    # shuffle(AREAS)

    with Live(layout, refresh_per_second=30, screen=True, transient=True):
        logger.addHandler(support.MainTableHandler(main_table, layout, logger.level))
        for area in AREAS:
            scrape(area, progbar, task, layout)
        
        # If new listings are found, save the data to the json file, 
        # format the list of dataclassses to a url, send gmail alerting of new properties
        if newlistings:
            # support.save_data(jsondata)
            links_html = support.urlformat(newlistings)
            support.send_housing_email(links_html)
            logger.info(f"{len(newlistings)} new listings found.  Email sent")
            
        else:
            logger.critical("No new listings were found")

        logger.info("Site functionality summary")
        logger.info(f"{list(LOST_N_FOUND.items())}")
        logger.info(f"Site counts {list(Counter([x[1] for x in newlistings]).items())}")
        logger.info("Program shutting down")

if __name__ == "__main__":
    main()

#IDEA
#What about using census data to survey area's of older populations.  
#might be able to do some cool clustering with that. 
