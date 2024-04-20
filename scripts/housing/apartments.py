import logging
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
	for card in result.find_all("article"):
		#Grab the id
		listingid = card.get("data-listingid")

		#First grab the link.
		if card.get("data-url"):
			url = card.get("data-url")
		
		#grab the property info
		for search in card.find_all("div", class_="property-info"):
			#Grab price
			for subsearch in search.find_all("div", class_="price-range"):
				price = subsearch.text
				price = money_launderer(price.split(" ")[0])
			#Grab bed bath
			for subsearch in search.find_all("div", class_="bed-range"):
				beds = subsearch.text
				beds, baths = beds.split(",")
				beds = float(beds.replace(" Beds", ""))
				if "Baths" in baths:
					baths = float(baths.replace(" Baths", ""))
				elif "Bath" in baths:
					baths = float(baths.replace(" Bath", ""))

		#grab address
		for search in card.find_all("a", class_="property-link"):
			if search.get("aria-label"):
				addy = search.get("aria-label")
			
		pets = True
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

def money_launderer(price:list)->float:
	"""[Strips dollar signs and comma from the price]

	Args:
		price (list): [list of prices as strs]

	Returns:
		price (list): [list of prices as floats]
	"""	
	if isinstance(price, str):
		return float(price.replace("$", "").replace(",", ""))
	return price

def neighscrape(neigh:str, source:str, logger:logging, Propertyinfo):
	#Return a list of dataclasses
	#TODO dict of neighborthoods exact mapping
 

	if " " in neigh:
		neigh = "".join(neigh.split(" "))

	headers = {
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
		'referer': 'https://www.apartments.com/houses-townhomes/chicago-il',
		'origin':'https://www.apartments.com',
	}

	url = f"https://www.apartments.com/houses-townhomes/{neigh}-chicago-il/min-2-bedrooms-pet-friendly-dog/"
          
	response = requests.get(url, headers=headers)

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
	results = bs4ob.find("div", class_="placardContainer")
	if results:
		if results.get("id") =='placardContainer':
			property_listings = get_listings(results, neigh, source, Propertyinfo)
			return property_listings
		
	else:
		logger.warning("No listings returned.  Moving to next site")
	
	logger.info("apartments!")
	#If it gets to here, then it didn't find any results
	return None



def zipscrape():
	logger.info("apartments!")
	#TODO build separate extraction for zip codes. 
	
