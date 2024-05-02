import logging
import json
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests
from urllib.parse import urlencode
import time
import support
from urllib.parse import urlencode

def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo)->list:
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
			listid = subsearch.get("href")
			listingid = listid.split("/")[-1]

		for subsearch in card.find_all("script", {"type":"application/ld+json"}):
			listinginfo = json.loads(subsearch.text)
			url = listinginfo[0].get("url")
			addy = listinginfo[0].get("name")
			lat = float(listinginfo[0]["geo"].get("latitude"))
			long = float(listinginfo[0]["geo"].get("longitude"))
			beds = listinginfo[0].get("numberOfRooms")
			if "value" in listinginfo[0]["floorSize"].keys():
				sqft = listinginfo[0].get("floorSize")["value"]
				if "," in sqft:
					sqft = sqft.replace(",", "")
			price = float(listinginfo[1]["offers"]["price"])

		#Bathrooms weren't in the json.  So we'll grab those manually
		for subsearch in card.find_all("span", class_=lambda x: x and "bath" in x):
			baths = subsearch.text
			baths = "".join(x for x in baths if x.isnumeric())
			break
		
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
			lat=lat,
			long=long,
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
	
	#Don't have a way to set these programatically.  You need to search for the
	#neighborhood id so you need to set the market, region_id, region_type, and
	#lat long to use this
	SH_PARAMS = {
		"location": f"{neigh}",
		"start": 0,
		"count": 10,
		"v": 2,
		"market": f"{CITY.lower()}",
		"al": 1,
		"iss": "false",
		"ooa": "true",
		"mrs": "false",
		"region_id": 29470,
		"region_type": 6,
		"lat": 41.833670000000005,
		"lng": -87.73184,
		"includeAddressInfo": "false"
	}
	# DL_URL = 'https://www.redfin.com/stingray/do/gis-search'
	# SH_PARAMS = {
	# 	'al': 1,
	# 	'isSearchFormParamsDefault': 'false',
	# 	'isRentals': 'true',
	# 	'lpp': 50,
	# 	'market': 'Chicago',
	# 	'mpt': 99,
	# 	'no_outline': 'false',
	# 	'num_homes': 500,
	# 	'page_number': 1,
	# 	'region_id': 29470,  #Replace this with your city
	# 	'region_type': 6,	 #I think 6 means neighborhood?
	# 	'sf': [1,2,5,6,7],
	# 	'sp': 'true',
	# 	'status': 1,
	# 	'uipt': [1,3],
	# 	'v': 8,
	# 	# 'render': 'csv'			#
	# }
  
	BASE_HEADERS = {
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
		'origin':'https://www.redfin.com',
	}
	# https://www.redfin.com/stingray/api/v1/search/rentals
 
	#Search by neighborhood
	if isinstance(neigh, str):
		url_map = "https://www.redfin.com/stingray/do/rental-location-autocomplete?" + urlencode(SH_PARAMS)
		# url_map = f'https://www.redfin.com/stingray/do/gis-search/' + urlencode(SH_PARAMS)

	#BUG - Zipcode search not functional yet
	# #Searchby ZipCode
	# elif isinstance(neigh, int):
	# 	url_map = f'https://www.redfin.com/stingray/do/gis-search/' + urlencode(SH_PARAMS)

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

	#Always take naps
	support.sleepspinner(np.random.randint(4, 8), "Mapping request nap")
	 
	#Search by neighborhood
	if isinstance(neigh, str):
		#Look up neighborhood id from autocomplete search query
		temp_dict = json.loads(response.text[4:])
		for neighborhood in temp_dict["payload"]['sections'][0]["rows"]:
			if neighborhood.get("name").lower() == neigh.lower():
				neighid = neighborhood.get("id")[2:]
				break

		if " " in neigh:
			neigh = "-".join(neigh.split(" "))

		url_search = f'https://www.redfin.com/neighborhood/{neighid}/{STATE}/{CITY}/{neigh}/apartments-for-rent/filter/property-type=house+townhouse,max-price=2.6k,min-beds=2,dogs-allowed'

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
	lcount = bs4ob.find("div", class_="homes summary").text
	lcount = int("".join(x for x in lcount if x.isnumeric()))

	if lcount > 0:
		results = bs4ob.find("div", class_="PhotosView")
		if results:
			if results.get("data-rf-test-id") =='photos-view':
				property_listings = get_listings(results, neigh, source, Propertyinfo)
				logger.info(f'{len(property_listings)} listings returned from {source}')
				return property_listings
			else:
				logger.warning("The soups failed you")		
	else:
		logger.warning("No listings returned on Redfin.  Moving to next site")


#Notes
# https://github.com/ryansherby/RedfinScraper/blob/main/redfin_scraper/core/redfin_scraper.py