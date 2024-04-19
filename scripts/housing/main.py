import numpy as np
import pandas as pd
from collections import Counter
import logging
from rich.logging import RichHandler
from itertools import chain
import craigslist_all_listings as craigs
import realtor
import support
import zillow
import apartments

FORMAT = "%(message)s" 
# FORMAT = "[%(asctime)s]|[%(levelname)s]|[%(message)s]" #[%(name)s]

logging.basicConfig(
	#filename=f"./data/logs/models_{current_date}.log", 
	#filemode='w',
	level="INFO", 
	format=FORMAT, 
	datefmt="%m-%d-%Y %H:%M:%S",
	handlers=[RichHandler()] 
)

logger = logging.getLogger(__name__) 

AREAS = [
	'Ravenswood',
	'Lincoln Square',
	'Ravenswood Gardens',
	'Budlong Woods',
	'Bowmanville',
]
SOURCES = {
	"craigs"    :("www.craiglist.com", craigs),
	"realtor"   :("www.realtor.com", realtor),
	"zillow"    :("www.zillow.com", zillow),
	"apartments":("www.apartments.com", apartments)
}
def add_data(data:pd.DataFrame):
	#Add new dataset
	pass


def scrapeall(neigh:str):
	#Create results DF
	results = pd.DataFrame()

	#set the dtypes
	data_types = {
		"id": "Int64",
		"title": str,
		"price": str,
		"hood": str,
		"link": str,
		"source": str,
		"amenities": object,
	}
	sources = ["craigs","realtor","zillow", "apartments"]
	for source in sources:
		site = SOURCES.get(source)
		if site:
			logger.info(f"scraping {site[0]} for {neigh}")
			data = site[1].scrape(neigh)
			add_data(data)
		else:
			logger.warning(f"source: {source} is invalid")
			raise ValueError(f"site for {source} not loaded")

#Driver code for data pull. 
def main():
	for neigh in AREAS:
		scrapeall(neigh)
	
	# support.send_housing_email()

if __name__ == "__main__":
	main()
