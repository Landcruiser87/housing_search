#Import libraries
import numpy as np
import pandas as pd
import logging
import datetime
import time
from rich.logging import RichHandler
from dataclasses import dataclass

#Import supporting files
import craigslist_all_listings as craigs
import realtor, zillow, apartments, support

FORMAT = "%(message)s" 
# FORMAT = "[%(asctime)s]|[%(levelname)s]|[%(message)s]" #[%(name)s]

logging.basicConfig(
	#filename=f"./data/logs/{current_date}.log", 
	#filemode='w',
	level="INFO", 
	format=FORMAT, 
	datefmt="%m-%d-%Y %H:%M:%S",
	handlers=[RichHandler()] 
)

logger = logging.getLogger(__name__) 

AREAS = [
	'Ravenswood',
	# 'Lincoln Square',
	# 'Ravenswood Gardens',
	# 'Budlong Woods',
	# 'Bowmanville',
]

#Uncomment if you want to search by zip. 
# AREAS = [
# 	# 60613,
# 	# 60625,
# 	# 60624,
# 	# 60623,
# 	# 60626,
# ]

SOURCES = {
	"realtor"   :("www.realtor.com", realtor),
	"apartments":("www.apartments.com", apartments),
	"craigs"    :("www.craiglist.com", craigs),
	"zillow"    :("www.zillow.com", zillow),
	
}

@dataclass
class Propertyinfo():
	id       : str
	source   : str
	price    : str
	neigh    : str
	bed      : float
	bath     : float
	dogs     : bool
	link     : str
	address  : str
	title    : str = None
	sqft     : float = None
	# dt_listed: datetime.datetime
	# amenities: object


def add_data(data:pd.DataFrame, siteinfo:tuple):
	#Add new dataset
	logger.info(f"data added for {siteinfo[0]} in {siteinfo[1]}")

def score(data):
	#todo -Come up with system of scoring any listing against chicago data
 	pass

def scrape(neigh:str):
	sources = ["realtor","apartments", "zillow", "craigs"]
	for source in sources:
		site = SOURCES.get(source)
		if site:
			logger.info(f"scraping {site[0]} for {neigh}")
			
			if isinstance(neigh, str):
				data = site[1].neighscrape(neigh, site[0], logger, Propertyinfo)
				time.sleep(2)
			# elif isinstance(neigh, int):
			# 	data = site[1].zipscrape(neigh, logger, Propertyinfo)
				# time.sleep(2)
	
			#TODO - Need a way to score the listings
			# score(data)
   
			#check for new results to add
			add_data(data, (site[0], neigh))
		else:
			logger.warning(f"source: {source} is invalid")
			raise ValueError(f"site for {source} not loaded")

#Driver code 
def main():
	global newlistings
	newlistings = []
	for neigh in AREAS:
		scrape(neigh)
	# for listing in newlistings:
		# support.send_housing_email(listing)

if __name__ == "__main__":
	main()
