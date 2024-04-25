#Import libraries
import numpy as np
import pandas as pd
import logging
import datetime
import time
from rich.logging import RichHandler
from dataclasses import dataclass, asdict
from os.path import exists
import json


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
	id     : str
	source : str
	price  : str
	neigh  : str
	dogs   : bool
	link   : str
	address: str
	bed    : float = None
	bath   : float = None
	sqft   : float = None
	# lat    : float = None
	# long   : float = None
	# dt_listed: datetime.datetime = None
	# amenities: object
	def dict(self):
		return {k: str(v) for k, v in asdict(self).items()}

def load_historical()->json:
	fp = "..\..\data\housing.json"
	if exists(fp):
		with open("..\..\data\housing.json", "r") as f:
			jsondata = json.loads(f.read())
			return jsondata
	else:
		logger.warning("No previous data found.")

def add_data(data:dataclass, siteinfo:tuple):
	fp = "..\..\data\housing.json"
	#If there is historical data.  Check the keys and see if they have already
	#been scraped

	#flow
	#data = list of dataclasses
	#storage is such
	#id = main key
		#all the other keys nested underneath that key

	if exists(fp):
		with open("..\..\data\housing.json", "a") as f:
			jsondata = load_historical()
			j_ids = [jsondata[x].get("id") for x in range(len(jsondata))]
			n_ids = [data[x].get("id") for x in range(len(data))]
			updatedict = {}
			jsondata.update(**updatedict)
			
	else:
		ids = [data[x].id for x in range(len(data))]
		histdict = {data[x].id : data[x].dict() for x in range(len(data))}
		[histdict[x].pop("id") for x in ids]
		out_json = json.dumps(histdict, indent=2)
		with open("..\..\data\housing.json", "w") as out_f:
			out_f.write(out_json)

	# #Moving the id key to the outer dict
	# ids = [data[x].id for x in range(len(data))]
	# histids = [{data[x].id : data[x].dict()} for x in range(len(data))]
	# update = [updatedict[id].pop("id") for id in ids]


	logger.info(f"data added for {siteinfo[0]} in {siteinfo[1]}")


def scrape(neigh:str):
	sources = ["apartments", "craigs", "zillow", "realtor", ]
	for source in sources:
		site = SOURCES.get(source)
		if site:
			logger.info(f"scraping {site[0]} for {neigh}")
			
			if isinstance(neigh, str):
				data = site[1].neighscrape(neigh, site[0], logger, Propertyinfo)
				time.sleep(2)

			#If data was returned, pull the lat long, score it and store it. 
			if data:
				# geocode(data)
				# score(data) -> put geopy lat/long extraction in here too. (in support.py now)
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