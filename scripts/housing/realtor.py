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

	for card in result.select('div[class*="BasePropertyCard"]'):
		filtertest = card.get("id")
		if "placeholder_property" in filtertest:
			continue
		#Grab the id
		listingid = card.get("id")
		listingid = listingid.replace("property_id_", "")

		#First grab the link.
		for link in card.find_all("a", class_="card-anchor"):
			if link.get("href"):
				url = source + link.get("href")
				break
		
		#grab the price
		for search in card.find_all("div", class_="price-wrapper"):
			for subsearch in search.find_all("div"):
				if subsearch.get("data-testid") == "card-price":
					price = subsearch.text
					if any(x.isnumeric() for x in price):
						price = money_launderer(subsearch.text)
					break
		
		#grab the beds, baths, pets
		for search in card.find_all("ul"):
			if search.get("data-testid") == "card-meta":
				sqft = None
				for subsearch in search.find_all("li"):
					if subsearch.get("data-testid")=="property-meta-beds":
						beds = subsearch.find("span").text
						if any(x.isnumeric() for x in beds):
							beds = float("".join(x for x in beds if x.isnumeric()))

					elif subsearch.get("data-testid")=="property-meta-baths":
						baths = subsearch.find("span").text
						if any(x.isnumeric() for x in baths):
							baths = float("".join(x for x in baths if x.isnumeric()))

					elif subsearch.get("data-testid")=="property-meta-sqft":
						sqft = subsearch.find("span", class_="meta-value").text
						if sqft:
							if any(x.isnumeric() for x in sqft):
								sqft = float("".join(x for x in sqft if x.isnumeric()))
			
	

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
			address=address
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
		neigh = "-".join(neigh.split(" "))

	headers = {
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
		'referer': 'https://www.realtor.com/apartments/Chicago_IL',
		'origin':'https://www.realtor.com',
	}

	url = f"https://www.realtor.com/apartments/{neigh}_Chicago_IL/type-townhome,single-family-home/beds-2/dog-friendly"
          
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
	results = bs4ob.find("section", {"data-testid":"property-list"})
	if results:
		property_listings = get_listings(results, neigh, source, Propertyinfo)
		logger.info(f'{len(property_listings)} listings returned from {source}')
		return property_listings
		
	else:
		logger.warning("No listings returned on realtor.  Moving to next site")
	
	#If it gets to here, then it didn't find any results
	return None

#Notes
#If updating to zips, realtor does this. 
# https://www.realtor.com/apartments/60613