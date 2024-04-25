#Import libraries
import numpy as np
import pandas as pd
import logging
import datetime
import time
from rich.logging import RichHandler
from dataclasses import dataclass, asdict
from sodapy import Socrata

#Import supporting files
import realtor, zillow, apartments, craigs, support

#Format logger and load
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

SOURCES = {
	"realtor"   :("www.realtor.com", realtor),
	"apartments":("www.apartments.com", apartments),
	"craigs"    :("www.craiglist.org", craigs),
	"zillow"    :("www.zillow.com", zillow),
	
}

@dataclass
class Propertyinfo():
	id       : str
	source   : str
	price    : str
	neigh    : str
	dogs     : bool
	link     : str
	address  : str
	bed      : float = None
	bath     : float = None
	sqft     : float = None
	# title    : str = None
	# dt_listed: datetime.datetime
	# amenities: object
	def dict(self):
		return {k: str(v) for k, v in asdict(self).items()}
	
def add_data(data:pd.DataFrame, siteinfo:tuple):
	#Add new dataset
	logger.info(f"data added for {siteinfo[0]} in {siteinfo[1]}")

def score(data):
	#todo -Come up with system of scoring any listing against chicago data
 	pass

def scrape(neigh:str):
	sources = ["apartments", "craigs", "zillow", "realtor", ]
	for source in sources:
		site = SOURCES.get(source)
		if site:
			logger.info(f"scraping {site[0]} for {neigh}")
			
			if isinstance(neigh, str):
				data = site[1].neighscrape(neigh, site[0], logger, Propertyinfo)
				time.sleep(2)

			#TODO - Check previous listings. 
				#Need a function to go through the JSON id's and find / add any
				#new ones to newlistings gb variable

			#TODO - Need a way to score the listings
			# score(data)
   
			#add new data to storage json
			add_data(data, (site[0], neigh))
		else:
			logger.warning(f"source: {source} is invalid")

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