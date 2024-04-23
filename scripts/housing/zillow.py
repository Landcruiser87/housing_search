import logging
import json
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests

def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo)->list:
	"""[Gets the list of links to the individual postings]

	Args:
		bs4ob ([BeautifulSoup object]): [html of realtor page]

	Returns:
		properties (list[Propertyinfo]): [all the links in the summary page]
	"""
	listings = []
	#Set the outer loop over each card returned. 
	# check the count
	count = result.find("span", class_="result-count")
	if count:
		count = int("".join(x for x in count.text if x.isnumeric()))
		if count < 1:
			return "No results found"
	
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

def neighscrape(neigh:str, source:str, logger:logging, Propertyinfo):
	#Check for spaces in the search neighborhood
	if " " in neigh:
		neigh = "-".join(neigh.split(" "))
	neigh = neigh.lower()
	#First grab the coordinates to match the zone we want
	header_uno = {
  		"accept-language": "en-US,en;q=0.9",
		"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
		"accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
		"accept-language": "en-US;en;q=0.9",
		"accept-encoding": "gzip, deflate, br",
	}

	params = {
	"searchQueryState":{
		"pagination":{},
		"usersSearchTerm":neigh + " Chicago, IL",
		"mapBounds":
		{
			"north":41.98122913701513,
			"south":41.95621327508874,
			"east":-87.6601700236206,
			"west":-87.71038097637938
		},
		},
	"wants": {
		"cat1":["mapResults"]
	},
	"requestId": 2
	}

	url_map = "https://www.zillow.com/async-create-search-page-state"
	response = requests.put(url_map, headers=header_uno, data = json.dumps(params))

	if response.status_code != 200:
		# If there's an error, log it and return no data for that site
		logger.warning(f'Status code: {response.status_code}')
		logger.warning(f'Reason: {response.reason}')
		return None


	header_dos = {
    	'accept-language': 'en-US,en;q=0.9',
		'origin':'https://www.zillow.com',
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36',
		'referer':f'https://www.zillow.com/homes/{neigh},-Chicago,-IL_rb/'
	}

	#Now realizing I need to make two requests for acccessing zillow data.  It requires map boundaries for a search area otherwise you just get
 	#for sale homes which kind of blows. What you need to do is hit the static search page
  	#"https://www.zillow.com/async-create-search-page-state" to extract geographical boundaries
    #and then you can go request what you want from the referer page.  So i'll need two requests here. 
  	#https://scrapfly.io/blog/how-to-scrape-zillow/#scraping-properties
   
	# 
	# subparams = {"usersSearchTerm":neigh + " Chicago, IL",
	# 			"filterState":{
	# 				"fr"   :{"value":"true"},
	# 				"fsba" :{"value":"false"},
	# 				"fsbo" :{"value":"false"},
	# 				"nc"   :{"value":"false"},
	# 				"cmsn" :{"value":"false"},
	# 				"auc"  :{"value":"false"},
	# 				"fore" :{"value":"false"},
	# 				"ah"   :{"value":"true"},
	# 				"beds" :{"min":"2"},
	# 				"apco" :{"value":"false"},
	# 				"apa"  :{"value":"false"},
	# 				"con"  :{"value":"false"},
	# 				"ldog" :{"value":"true"},
	# 				"sdog" :{"value":"true"}
	# 			},
	# 			"isListVisible":"true",
	# 			}
 				# "usersSearchTerm":neigh + " Chicago, IL",
	subparams = {"pagination" : {},
			    "mapBounds":{
					"north":41.98122913701513,
					"south":41.95621327508874,
					"east":-87.6601700236206,
					"west":-87.71038097637938
				},
				"filterState":{
					"isForRent"           :{"value":True},
					"isForSaleByAgent"    :{"value":False},
					"isForSaleByOwner"    :{"value":False},
					"isNewConstruction"   :{"value":False},
					"isComingSoon"        :{"value":False},
					"isAuction"           :{"value":False},
					"isForSaleForeclosure":{"value":False},
					"isAllHomes"          :{"value":True},
					"beds"                :{"min":2},
					"isApartmentOrCondo"  :{"value":False},
					"isApartment"         :{"value":False},
					"isCondo"             :{"value":False},
					"onlyRentalLargeDogsAllowed":{"value":True},
					"onlyRentalSmallDogsAllowed":{"value":True}
				},
				"isListVisible":True,
				}
	params = {"searchQueryState": subparams}

	url = f"https://www.zillow.com/{neigh}-chicago-il/rentals"
		  
	response = requests.get(url, headers=header_dos, params=params)

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
	results = bs4ob.find("div", class_="result-list-container")
	if results:
		if results.get("id") =='grid-search-results':
			property_listings = get_listings(results, neigh, source, Propertyinfo)
			return property_listings
		
	else:
		logger.warning("No listings returned.  Moving to next site")
	
	logger.info("zillow!")
	#If it gets to here, then it didn't find any results
	return None

# def zipscrape():
# 	logger.info("zillow!")
# 	#TODO build separate extraction for zip codes. 
	
