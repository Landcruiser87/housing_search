#Import libraries
from datetime import datetime
import numpy as np
import pandas as pd
import logging
import time
from rich.logging import RichHandler
from dataclasses import dataclass, asdict, astuple, field
from os.path import exists
from random import shuffle

#Import supporting files
import realtor, support, zillow #, apartments, craigs, redfin, 

#Format logger and load configuration
FORMAT = "%(message)s" 
# FORMAT = "[%(asctime)s]|[%(levelname)s]|[%(message)s]" #[%(name)s]
current_date = time.strftime("%m-%d-%Y_%H-%M-%S")
logging.basicConfig(
	#filename=f"./data/logs/{current_date}.log",  
	#filemode='w',
	level="INFO", 
	format=FORMAT, 
	datefmt="%m-%d-%Y %H:%M:%S",
	handlers=[RichHandler()] 
)

#Load logger
logger = logging.getLogger(__name__) 

AREAS = [
	46703, #Atown
	46737, #Fremont
	# 46779, #Pleasant Lake
	# 46776, #Orland
	# 46746, #MONGOOOOOO
]

SOURCES = {
	"realtor"   :("www.realtor.com", realtor),
	"zillow"    :("www.zillow.com", zillow),
	# "craigs"    :("www.craiglist.org", craigs),
	# "redfin"    :("www.redfin.com", redfin)
}

# Define City / State
CITY = "Angola"
STATE = "IN"

#Define dataclass container
@dataclass
class Propertyinfo():
	id           : str
	source       : str
	status       : str
	price        : str
	link         : str
	address      : str
	htype        : str = None
	zipc         : int = None
	listdate     : datetime = None
	last_s_date  : datetime = None
	last_s_price : float = ""
	bed          : float = None
	bath         : float = None
	sqft         : float = None
	lotsqft      : float = None
	lat          : float = ""
	long         : float = ""
	extras       : dict = field(default_factory=lambda:{})
	# L_dist  : float = ""
	# crime_sc: dict = field(default_factory=lambda:{})
	# cri_dat : np.ndarray #Eventually to store week to week crime data here for each listing

	def dict(self):
		return {k: str(v) for k, v in asdict(self).items()}

#FUNCTION Check IDs
def check_ids_at_the_door(data:list):
	"""This function takes in a list of Propertyinfo objects, reformats them to
	a dictionary, compares the property id's to existing JSON historical
	property id keys, finds any new ones via set comparison. Then returns a list
	of Propertyinfo objects that have those new id's (if any)

	Args:
		data (list): List of Propertyinfo objects

	Returns:
		data (list): List of only new Propertyinfo objects
	"""	
	#Reshape data to dict
	#Pull out the ids
	ids = [data[x].id for x in range(len(data))]
	#make a new dict that can be json serialized with the id as the key
	new_dict = {data[x].id : data[x].dict() for x in range(len(data))}
	#Pop the id from the dict underneath (no need to store it twice)
	[new_dict[x].pop("id") for x in ids]

	#Use sets for membership testing of old jsondata keys
	#and new data keys (Looking for new listings)
	j_ids = set(jsondata.keys())
	n_ids = set(new_dict.keys())
	newids = n_ids - j_ids
	if newids:
		#Only add the listings that are new.  
		newdata = []
		[newdata.append(data[idx]) for idx, _ in enumerate(data) if data[idx].id in newids]
		return newdata
	else:
		logger.info("Listing(s) already stored in rental_list.json") 
		return None
	#TODO - Check old listings. 
		#Eventually I will want this to check the older listings and 
		#look for price change

#FUNCTION Add Data
def add_data(data:list, siteinfo:tuple):
	"""Adds Data to JSON Historical file

	Args:
		data (list): List of Propertyinfo objects that are new (not in the historical)
		siteinfo (tuple): Tuple of website and neighborhood/zip
	"""	
	#Reshape data to dict
	#Pull out the ids
	ids = [data[x].id for x in range(len(data))]
	#make a new dict that can be json serialized with the id as the key
	new_dict = {data[x].id : data[x].dict() for x in range(len(data))}
	#Pop the id from the dict underneath (no need to store it twice)
	[new_dict[x].pop("id") for x in ids]

	#update main data container
	jsondata.update(**new_dict)
	#Grab the new urls for emailing
	newurls = [(new_dict[idx].get("link"), siteinfo[0].split(".")[1], (new_dict[idx].get("zipc")), (new_dict[idx].get("price"))) for idx in ids]
	#Extend the newlistings global list
	newlistings.extend(newurls)

	logger.info("Global dict updated")
	logger.info(f"data added for {siteinfo[0]} in {siteinfo[1]}")

#FUNCTION Scrape data
def scrape(neigh:str):
	"""This function will iterate through different resources scraping necessary information for ingestion. 

	Args:
		neigh (str): Neighborhood or Zipcode
	"""	
	sources = ["zillow", "realtor", "redfin", "craigs"]
	# shuffle(sources) #Keep em guessin!
	for source in sources:
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
				data = site[1].neighscrape(neigh, site[0], logger, Propertyinfo, (CITY, STATE), jsondata)

			elif source=="craigs" and c_scrape==True:
				continue
			
			else:
				#every other site, scrape it normally
				logger.info(f"scraping {site[0]} for {neigh}")
				data = site[1].neighscrape(neigh, site[0], logger, Propertyinfo, (CITY, STATE))

			#Take a lil nap.  Be nice to the servers!
			support.sleepspinner(np.random.randint(3,8), f'taking a nap at {site[0]}')

			#If data was returned
			if data:
				#This function will isolate new id's that aren't in the historical JSON
				datacheck = check_ids_at_the_door(data)
				if datacheck:
					#  pull the lat long, score it and store it. 
					data = datacheck
					del datacheck
					#Get lat longs for the address's
						#BUG - Need this on an individual ID level. 
						#Might call it somwhere else. 
					# data = support.get_lat_long(data, (CITY, STATE), logger)

					if CITY == "Chicago":
						#Calculate the distance to closest L stop 
						#(haversine/as crow flies)
						data = support.closest_L_stop(data)

						#Score them according to chicago crime data
						data = support.crime_score(data)

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
	fp = "./data/buy_list.json"
	#Load historical listings JSON
	if exists(fp):
		jsondata = support.load_historical(fp)
		logger.info("historical data loaded")
	else:
		jsondata = {}
		logger.warning("No historical data found")
		
	#Shuffle and search the neighborhoods/zips
	# shuffle(AREAS)
	for neigh in AREAS:
		scrape(neigh)

	# If new listings are found, save the data to the json file, 
	# format the list of dataclasesses to a url 
	# Send gmail alerting of new properties
 
	if newlistings:
		support.save_data(jsondata)
		links_html = support.urlformat(newlistings)
		# support.send_housing_email(links_html)
		logger.info(f"{len(newlistings)} new listings found.  Email sent")
	else:
		logger.critical("No new listings were found")

	logger.info("Program shutting down")

if __name__ == "__main__":
	main()


#Notes
# fp = "../../data/buy_list.json"
# with open(fp, "r") as readf:
# 	results = json.load(readf)	

#IDEA
#What about using census data to survey area's of older populations.  
#might be able to do some cool clustering with that. 
