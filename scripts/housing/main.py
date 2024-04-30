#Import libraries
import numpy as np
import pandas as pd
import logging
import time
from rich.logging import RichHandler
from dataclasses import dataclass, asdict, astuple, field
from os.path import exists
from random import shuffle

#Import supporting files
import realtor, zillow, apartments, craigs, support

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

#input custom area's here. Uncomment whichever way you want to search
AREAS = [
	# 'Lincoln Square',
	'Ravenswood',
	'North Center',
	'Bowmanville',
	'Roscoe Village',
	# 'Ravenswood Gardens',
	# 'Budlong Woods',
]

# AREAS = [
# 	60613,
# 	60614,
# 	# 60657,
# # 	# 60610,
# # 	# 60618,
# # 	# 60647,
# # 	# 60622,
# # 	# 60625,
# # 	# 60641,
# # 	# 60651
# ]

SOURCES = {
	"realtor"   :("www.realtor.com", realtor),
	"apartments":("www.apartments.com", apartments),
	"craigs"    :("www.craiglist.org", craigs),
	"zillow"    :("www.zillow.com", zillow),
}

# Define City / State
CITY = "Chicago"
STATE = "IL"


#Define dataclass container
@dataclass
class Propertyinfo():
	id      : str
	source  : str
	price   : str
	neigh   : str
	dogs    : bool
	link    : str
	address : str
	bed     : float = None
	bath    : float = None
	sqft    : float = None
	lat     : float = ""
	long    : float = ""
	L_dist  : float = ""
	crime_sc: dict = field(default_factory=lambda:{})
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
		#Only add the listings that are new
		newdata = []
		[newdata.append(data[idx]) for idx, _ in enumerate(data) if data[idx].id in newids]
		return newdata
	else:
		logger.info("Listing(s) already stored in housing.json") 
		return None
		
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
	newurls = [(new_dict[idx].get("link"), siteinfo[0].split(".")[1]) for idx in ids]
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
	sources = ["realtor", "apartments", "zillow", "craigs"]
	shuffle(sources) #Keep em guessin!
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
				data = site[1].neighscrape(neigh, site[0], logger, Propertyinfo, (CITY, STATE))

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
					data = support.get_lat_long(data, (CITY, STATE))

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
	fp = "./data/housing.json"
	#Load historical listings JSON
	if exists(fp):
		jsondata = support.load_historical(fp)
		logger.info("historical data loaded")
	else:
		logger.warning("No previous data found.")
		jsondata = {}

	#Shuffle and search the neighborhoods
	shuffle(AREAS)
	for neigh in AREAS:
		scrape(neigh)

	# If new listings are found, save the data to the json file, 
	# format the list of dataclasesses to a url 
	# Send gmail alerting of new properties
	if newlistings:
		support.save_data(jsondata)
		links_html = support.urlformat(newlistings)
		support.send_housing_email(links_html)
		logger.info("Listings email sent")
	else:
		logger.critical("No new listings were found")

	logger.info("Program shutting down")

if __name__ == "__main__":
	main()