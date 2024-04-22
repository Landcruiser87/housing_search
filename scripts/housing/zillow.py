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
	# check the count
	count = result.find("span", class_="result-count")
	if count:
		count = int("".join(x for x in count.text if x.isnumeric()))
		if count < 1:
			return "No results found"
	
	for card in result.find_all("article"):
		#don't always get this one. 
		sqft = None
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
	#Check for spaces in the name
	if " " in neigh:
		neigh = "-".join(neigh.split(" "))
	neigh = neigh.lower()

	headers = {
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
		'referer': 'https://www.zillow.com/apartments/chicago-il/',
		'origin':'https://www.zillow.com',
	}
	params = (
    ('usersSearchTerm', neigh),
	# ('region', neigh)
	('fr',     True),
	('fsba',   False),
	('fsbo',   False),
	('nc',     False),
	('cmsn',   False),
	('auc',    False),
	('fore',   False),
    ('ah',     True),
	('apco',   False),
	('apa',    False),
	('con',    False),
    ('ldog',   True),
    ('sdog',   True),
	('isEntirePlaceForRent', True)
	('isRoomForRent', False)
	('beds', 'min2')
)
	url = f"https://www.zillow.com/{neigh}-chicago-il/rentals/"
          
	response = requests.get(url, headers=headers, params=params)

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
	
