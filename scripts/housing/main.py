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
	'Lincoln Square',
	'Ravenswood',
	'North Center',
	'Roscoe Village'
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

def load_historical(fp:str)->json:
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


	if jsondata:
		j_ids = set(jsondata.keys())
		n_ids = set(new_dict.keys())
		newids = n_ids - j_ids
		if newids:
			#If we found new data, add it to the json file and save it. 
			updatedict = {idx:new_dict[idx] for idx in newids}
			#update main data container
			jsondata.update(**updatedict)
			#Grab the new urls for emailing
			newurls = [(updatedict[idx].get("link"), siteinfo[0].split(".")[1]) for idx in newids]
			#Extend the newlistings global
			newlistings.extend(newurls)

		else:
			logger.warning(f"No new listings on {siteinfo[0]} in {siteinfo[1]}")
			return		
	else:
		#Update global dict with the first few results
		save_data(new_dict)
		logger.info("JSON dict updated and saved")
		jsondata.update(**new_dict)

	logger.info(f"data added for {siteinfo[0]} in {siteinfo[1]}")

def save_data(jsond:dict):
	out_json = json.dumps(jsond, indent=2)
	with open("./data/housing.json", "w") as out_f:
		out_f.write(out_json)
	logger.info("JSON file saved")

def scrape(neigh:str):
	sources = ["apartments", "realtor", "craigs", "zillow"]  
	for source in sources:
		site = SOURCES.get(source)
		if site:
			if isinstance(neigh, str):
				#Because we can't search craigs by neighborhood, we only want to
				#scrape it once.  So this sets a boolean of if we've scraped
				#craigs, then flips the value to not scrape it again in the
				#future neighborhoods that will be searched. 
				global c_scrape
				if source=="craigs" and c_scrape==False:
						c_scrape = True
						logger.info(f"scraping {site[0]}")
						data = site[1].neighscrape(neigh, site[0], logger, Propertyinfo)

				elif source=="craigs" and c_scrape==True:
					continue
				
				else:
					logger.info(f"scraping {site[0]} for {neigh}")
					#every other site, scrape it normally
					data = site[1].neighscrape(neigh, site[0], logger, Propertyinfo)

				#Take a lil nap.  Be nice to servers!
				support.sleepspinner(np.random.randint(2,6))

			#If data was returned, pull the lat long, score it and store it. 
			if data:
				# geocode(data)
				# score(data) -> put geopy lat/long extraction in here too. (in support.py now)
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
		jsondata = load_historical(fp)
	else:
		jsondata = {}
	#Search the neighborhoods
	for neigh in AREAS:
		scrape(neigh)
	#Email any newlistings (one combined email.  not separate)
		#?Could try a rich table format here with embedded links
  
	if newlistings:
		save_data(jsondata)
		links_html = support.urlformat(newlistings)
		support.send_housing_email(links_html)
		logger.info("Listings email sent")
	else:
		logger.warning("No new listings were found")
	logger.info("Program shutting down")

if __name__ == "__main__":
	main()