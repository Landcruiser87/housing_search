import logging
import json
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests
from urllib.parse import urlencode
import time
import support

def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo, lcount:int)->list:
	"""[Gets the list of links to the individual postings]

	Args:
		bs4ob ([BeautifulSoup object]): [html of realtor page]

	Returns:
		properties (list[Propertyinfo]): [all the links in the summary page]
	"""
	listings = []
	#Set the outer loop over each card returned. 
	for card in result.find_all("div", id=lambda x: x and x.startswith("MapHomeCard")):
		
		for subsearch in card.find_all("a", class_="link-and-anchor visuallyHidden"):
			url = subsearch.get("href")
			listingid = url.split("/")[-1]

		# for subsearch in card.find_all("span", class_=lambda x: x and x.startswith("bp-Homecard__Stats")):
		# 	if "bed" in card.__class__:
		# 		beds = [x for x in subsearch.text if x.isnumeric()]
		# 	if "bath" in card.__class__:
		# 		baths = [x for x in subsearch.text if x.isnumeric()]
		# 	if "sqft" in card.__class__:
		# 		sqft = [x for x in subsearch.text if x.isnumeric()]
		for subsearch in card.find_all("script", {"type":"application/ld+json"}):
			json.loads(subsearch.text)			

	for card in result.find_all("article"):
		#Grab the id
		if card.get("data-test")=="property-card":
			listingid = card.get("id")
		
		#First grab the link.
		for search in card.find_all("a"):
			#maybe check if the class ends with that. 
			if search.get("data-test")=="property-card-link":
				url = search.get("href")
				#Grab the address from below the ref link
				if source not in url:
					url = source + url
				addy = search.next.text
				break
		
		#grab the price
		for search in card.find_all("span"):
			if search.get("data-test")=="property-card-price":
				text = search.text
				#Sometimes these jokers put the beds in with the price just annoy people like me
				if "+" in text:
					price = text[:text.index("+")]

				price = float("".join(x for x in text if x.isnumeric()))
				break

		#Grab bed bath
		for search in card.find_all("ul"):
			for subsearch in search.find_all("li"):
				text = str(subsearch)
				numtest = any(x.isnumeric() for x in text)

				if "bd" in text and numtest:
					beds = float("".join(x for x in text if x.isnumeric()))
				elif "ba" in text and numtest:
					baths = float("".join(x for x in text if x.isnumeric()))
				elif "sqft" in text and numtest:
					sqft = float("".join(x for x in text if x.isnumeric()))
		pets = True

		#Janky way of making sure variables are filled if we missed any
		if not "listingid" in locals():
			listingid = None
		if not "price" in locals():
			price = None
		if not "beds" in locals():
			beds = None
		if not "baths" in locals():
			baths = None
		if not "url" in locals():
			url = None
		if not "addy" in locals():
			addy = None
		if not "sqft" in locals():
			sqft = None
		
		listing = Propertyinfo(
			id=listingid,   
			source=source,
			price=price,    
			neigh=neigh,
			bed=beds,       
			sqft=sqft,      
			bath=baths,     
			dogs=pets,      
			link=url,		
			address=addy    
		)

		listings.append(listing)

	return listings

def neighscrape(neigh:str, source:str, logger:logging, Propertyinfo, citystate):
	#Check for spaces in the search neighborhood
	CITY = citystate[0]
	STATE = citystate[1]
	#First grab the map coordinates update our next request
 
	#BUG stupid neighborhood encodings. 
		#Beeeeecause redfin dumps their own numerical zip for neighborhoods, I need to make
		#two requests when searching redfin.  
		#1. Make a request to see what neighborhood code goes with the search term. 
		#2. Request the appropriate neigh with paramaterized search. 
  
  
	BASE_HEADERS = {
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
		'referer':f'https://www.redfin.com/{CITY}-{STATE}/rentals',
		'origin':'https://www.redfin.com',
	}
	
	#Search by neighborhood
	if isinstance(neigh, str):
		if " " in neigh:
			neigh = "-".join(neigh.split(" "))

		url_map = f'https://www.redfin.com/neighborhood/{customid}-{STATE}-{CITY}/{neigh}/apartments-for-rent/filter/property-type=house+townhouse,max-price=2.6k,min-beds=2,dogs-allowed'

	#Searchby ZipCode
	elif isinstance(neigh, int):
		url_map = f'https://www.redfin.com/zipcode/{neigh}/apartments-for-rent/filter/property-type=house+townhouse,max-price=2.6k,min-beds=2,min-baths=2,dogs-allowed'

	#Error Trapping
	else:
		logging.critical("Inproper input for redfin, moving to next site")
		return

	response = requests.get(url_map, headers=BASE_HEADERS)
	
	# If there's an error, log it and return no data for that site
	if response.status_code != 200:
		logger.warning("The way is shut!")
		logger.warning(f'Status code: {response.status_code}')
		logger.warning(f'Reason: {response.reason}')
		return None

	bs4ob = BeautifulSoup(response.text, 'lxml')
	scripts = bs4ob.find_all("script")
	coords = [x.text for x in scripts if "window.mapBounds" in x.text]
	start = coords[0].index("mapBounds")
	end = start + coords[0][start:].index(";\n")
	mapcords = coords[0][start:end].split(" = ")[1]

	#Get the map coordinates
	map_coords = json.loads(mapcords)
	support.sleepspinner(np.random.randint(2, 8), "Map Request Nap")
	 
	# #Stipulate subparameters of search
	# subparams = {
	# 	"usersSearchTerm":f"{neigh} {CITY}, {STATE.upper()}",
	# 	"mapBounds":map_coords,
	# 	"filterState":{
	# 		"isForRent"           :{"value":True},
	# 		"isForSaleByAgent"    :{"value":False},
	# 		"isForSaleByOwner"    :{"value":False},
	# 		"isNewConstruction"   :{"value":False},
	# 		"isComingSoon"        :{"value":False},
	# 		"isAuction"           :{"value":False},
	# 		"isForSaleForeclosure":{"value":False},
	# 		"isAllHomes"          :{"value":True},
	# 		"beds"                :{"min":2},
	# 		"isApartmentOrCondo"  :{"value":False},
	# 		"isApartment"         :{"value":False},
	# 		"isCondo"             :{"value":False},
	# 		"mp"                  :{"max":2600},
	# 		"onlyRentalLargeDogsAllowed":{"value":True},
	# 		"onlyRentalSmallDogsAllowed":{"value":True}
	# 	},
	# 	"isListVisible":True,
	# 	# "regionSelection": [{"regionId": 33597, "regionType": 8}], #!might not need this?
	# 	"pagination" : {},
	# 	"mapZoom":11
	# }
	# params = {
	# 	"searchQueryState": subparams,
	# 	"wants": {"cat1": ["listResults"]},
    # 	"requestId": 2 #np.random.randint(2, 3)
	# }

	#Search by neighborhood
	if isinstance(neigh, str):
		if " " in neigh:
			neigh = "-".join(neigh.split(" "))

		url_search = f'https://www.redfin.com/neighborhood/{customid}-{STATE}-{CITY}/{neigh}/apartments-for-rent/filter/property-type=house+townhouse,max-price=2.6k,min-beds=2,dogs-allowed'

	#Searchby ZipCode
	elif isinstance(neigh, int):
		url_search = f'https://www.redfin.com/zipcode/{neigh}/apartments-for-rent/filter/property-type=house+townhouse,max-price=2.6k,min-beds=2,min-baths=2,dogs-allowed'

	#Error Trapping
	else:
		logging.critical("Inproper input for redfin, moving to next site")
		return
		
	response = requests.get(url_search, headers = BASE_HEADERS)

	#Just in case we piss someone off
	if response.status_code != 200:
		# If there's an error, log it and return no data for that site
		logger.warning(f'Status code: {response.status_code}')
		logger.warning(f'Reason: {response.reason}')
		return None

	#Get the HTML
	bs4ob = BeautifulSoup(response.text, 'lxml')

	# Isolate the property-list from the expanded one (I don't want the 3 mile
	# surrounding.  Just the neighborhood)
	lcount = int(bs4ob.find("div", class_="homes summary").text)
	
	if lcount > 0:
		results = bs4ob.find("div", class_="PhotosView")
		if results:
			if results.get("data-rf-test-id") =='photos-view':
				property_listings = get_listings(results, neigh, source, Propertyinfo, lcount)
				logger.info(f'{len(property_listings)} listings returned from {source}')
				return property_listings
			else:
				logger.warning("The soups failed you")		
	else:
		logger.warning("No listings returned on Redfin.  Moving to next site")


#Notes
# https://github.com/ryansherby/RedfinScraper/blob/main/redfin_scraper/core/redfin_scraper.py