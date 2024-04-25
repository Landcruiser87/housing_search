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
	fp = "./data/housing.json"
	if exists(fp):
		with open(fp, "r") as f:
			jsondata = json.loads(f.read())
			return jsondata
	else:
		logger.warning("No previous data found.")

def add_data(data:dataclass, siteinfo:tuple):
	#Reshape data to dict
	#Pull out the ids
	ids = [data[x].id for x in range(len(data))]
	#make a new dict that can be json serialized with the id as the key
	new_dict = {data[x].id : data[x].dict() for x in range(len(data))}
	#Pop the id from the dict underneath (no need to store it twice)
	[new_dict[x].pop("id") for x in ids]

	#If there is historical data.  Check the keys and see if they have already
	#been scraped
	fp = "./data/housing.json"

	if exists(fp):
		if not "jsondata" in globals():
			global jsondata
			jsondata = load_historical()
		
		j_ids = set(jsondata.keys())
		n_ids = set(new_dict.keys())
		newids = n_ids - j_ids
		if newids:
			#If we found new data, add it to the json file and save it. 
			updatedict = {idx:new_dict[idx] for idx in newids}
			jsondata.update(**updatedict)
			newurls = [jsondata[idx].get("url") for idx in newids]
			newlistings.extend(newurls)

		else:
			logger.warning(f"No new listings on {siteinfo[0]} in {siteinfo[1]}")			
	else:
		
		#Dump it to json and save it
		out_json = json.dumps(new_dict, indent=2)
		with open("./data/housing.json", "w") as out_f:
			out_f.write(out_json)

	logger.info(f"data added for {siteinfo[0]} in {siteinfo[1]}")

def save_data(jsond:dict):
	out_json = json.dumps(jsond, indent=2)
	with open("./data/housing.json", "w") as out_f:
		out_f.write(out_json)

def scrape(neigh:str):
	sources = ["apartments", "realtor", "craigs", "zillow", ]
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
				jsond = add_data(data, (site[0], neigh))
				
		else:
			logger.warning(f"source: {source} is not in validated search list")
	save_data(jsond)

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