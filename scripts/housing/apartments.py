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
	for card in result.find_all("div", class_="BasePropertyCard_propertyCardWrap__MiBHq"):
		#Grab the id
		listingid = card.get("id")
		listingid = listingid.replace("placeholder_property_", "")

		#First grab the link.
		for link in card.find_all("a", class_="card-anchor"):
			if link.get("href"):
				url = source + link.get("href")
				break
		
		#grab the price
		for search in card.find_all("div", class_="price-wrapper"):
			for subsearch in search.find_all("div"):
				if subsearch.get("data-testid") == "card-price":
					price = money_launderer(subsearch.text)
					break
		
		#grab the beds, baths, pets
		for search in card.find_all("ul"):
			if search.get("data-testid") == "card-meta":
				for subsearch in search.find_all("li"):
					if subsearch.get("data-testid")=="property-meta-beds":
						beds = float(subsearch.find("span").text)
					elif subsearch.get("data-testid")=="property-meta-baths":
						baths = float(subsearch.find("span").text)
					elif subsearch.get("data-testid")=="property-meta-sqft":
						sqft = float(captain_comma(subsearch.find("span", class_="meta-value").text))
		
		#grab address
		for search in card.find_all("div", class_="card-address truncate-line"):
			if search.get("data-testid") == "card-address":
				addy = ""
				for subsearch in search.find_all("div", class_="truncate-line"):
					addy += subsearch.text + " "
				address = addy.strip()
		#Pets is already secured in the search query so we don't have to confirm it in the data.
		pets = True
	
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


def captain_comma(sqft:str)->float:
	"""[Strips comma from sqft]

	Args:
		sqft (str): square footage string

	Returns:
		sqft (float): removes comma so it can be a float!
	"""	
	if isinstance(sqft, str):
		return float(sqft.replace(",", ""))
	return sqft

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
	results = bs4ob.find("section", class_="PropertiesList_propertiesContainer__ncXi8 PropertiesList_listViewGrid__kkBix")
	if results:
		if results.attrs['data-testid']=='property-list':
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
	
