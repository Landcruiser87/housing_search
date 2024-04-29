#Import libraries
import numpy as np
import pandas as pd
import logging
import time
from rich.logging import RichHandler
from dataclasses import dataclass, asdict, astuple, field
from os.path import exists

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

#input custom area's here. 
AREAS = [
	'Lincoln Square',
	'North Center',
	'Ravenswood',
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
	
	#https://kplauritzen.dk/2021/08/11/convert-dataclasss-np-array.html
	#TODO - Look at above link
		#might be an easier way to offload np arrays. 
  
	# def __array__(self):
	# 	return np.array(astuple(self))
	# def __len__(self):
	# 	return astuple(self).__len__()
	# def __getitem__(self, item):
	# 	return astuple(self).__getitem__(item)
 
def check_ids_at_the_door(data):
	#Reshape data to dict
	#Pull out the ids
	ids = [data[x].id for x in range(len(data))]
	#make a new dict that can be json serialized with the id as the key
	new_dict = {data[x].id : data[x].dict() for x in range(len(data))}
	#Pop the id from the dict underneath (no need to store it twice)
	[new_dict[x].pop("id") for x in ids]

	if jsondata:
		#Use sets for membership testing of old jsondata keys
  		#and new data keys (Looking for new listings)
		j_ids = set(jsondata.keys())
		n_ids = set(new_dict.keys())
		newids = n_ids - j_ids
		if newids:
			#Go through and remove existing listings so they're not searched twice
			updatedict = {idx:new_dict[idx] for idx in newids}

			
def add_data(data:dataclass, siteinfo:tuple):
	#Reshape data to dict
	#Pull out the ids
	ids = [data[x].id for x in range(len(data))]
	#make a new dict that can be json serialized with the id as the key
	new_dict = {data[x].id : data[x].dict() for x in range(len(data))}
	#Pop the id from the dict underneath (no need to store it twice)
	[new_dict[x].pop("id") for x in ids]

	if jsondata:
		#Use sets for membership testing of old jsondata keys
  		#and new data keys (Looking for new listings)
		j_ids = set(jsondata.keys())
		n_ids = set(new_dict.keys())
		newids = n_ids - j_ids
		if newids:
			#If we found new listings, extract the new listings and add them to
			#the JSON file.
			updatedict = {idx:new_dict[idx] for idx in newids}
			#update main data container
			jsondata.update(**updatedict)
			#Grab the new urls for emailing
			newurls = [(updatedict[idx].get("link"), siteinfo[0].split(".")[1]) for idx in newids]
			#Extend the newlistings global list
			newlistings.extend(newurls)

		else:
			logger.warning(f"No new listings on {siteinfo[0]} in {siteinfo[1]}")
			return		
	else:
		#Update global dict with the first few results
		support.save_data(new_dict)
		jsondata.update(**new_dict)
		logger.info("JSON file saved and global dict updated")
		
	logger.info(f"data added for {siteinfo[0]} in {siteinfo[1]}")

def scrape(neigh:str):
	sources = ["realtor", "apartments", "zillow", "craigs",]  
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
			support.sleepspinner(np.random.randint(2,6), f'{site[0]} takes a sleep')

			#If data was returned, pull the lat long, score it and store it. 
			if data:
				#TODO - Check the id's of the listings found first before submitting them to search.  
				#That way you don't repeat any requests made for search information
				# data = check_ids_at_the_door(data)
	
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
			logger.warning(f"source {source} no data found")

		else:
			logger.warning(f"source: {source} is not in validated search list")
	
#Driver code 
def main():
	#Global variable setup
	global newlistings, jsondata, c_scrape
	c_scrape = False
	newlistings = []
	fp = "./data/housing.json"
	if exists(fp):
		jsondata = support.load_historical(fp)
		logger.info("historical data loaded")
	else:
		logger.warning("No previous data found.")
		jsondata = {}

	#Search the neighborhoods
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