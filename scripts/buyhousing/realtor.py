import logging
from bs4 import BeautifulSoup
import numpy as np
import requests
import json

def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo)->list:
	"""[Gets the list of links to the individual postings]

	Args:
		bs4ob ([BeautifulSoup object]): [html of realtor page]

	Returns:
		properties (list[Propertyinfo]): [all the links in the summary page]
	"""

	listings = []
	#Load the json data
	listing_dict = json.loads(result.text)
	varnames = [
		"listingid", "price", "status", "url", "beds", "baths", "sqft", "lotsqft",
		"htype", "listdate", "lat", "long", "address", "last_s_price", "last_s_date"
	]

	for listing in listing_dict["props"]["pageProps"]["properties"]:
		listingid = listing.get("property_id")
		price = listing.get("list_price")
		status = listing.get("status")
		url = "https://" + source + "/realestateandhomes-detail/" + listing.get("permalink")
		#Janky way of making sure variables are filled if we missed any
		beds = listing["description"].get("beds")
		baths = listing["description"].get("baths_consolidated")
		sqft = listing["description"].get("sqft")
		lotsqft = listing["description"].get("lot_sqft")
		htype = listing["description"].get("type")
		#TODO - Need a funciton to convert the datetimes
		listdate = listing["description"].get("list_date")
		lat = listing["location"]["address"]["coordinate"]["lat"]
		long = listing["location"]["address"]["coordinate"]["lon"]
		#Address
		add_list = ["line", "city", "state_code", "postal_code"]
		addy = ""
		for key in add_list:
			if key == "city":
				addy += listing["location"]["address"][key] + ", "
			else:
				addy += listing["location"]["address"][key] + " "
		address = addy
		last_s_price = listing["description"].get("sold_price")
		last_s_date = listing["description"].get("sold_date")
		extras = {"price_reduced_amount":listing.get("price_reduced_amount")}
		flags = listing.get("flags")
		extras.update(**flags)

		for var in varnames:
			if var not in locals():
				locals()[var] = None

		listing = Propertyinfo(
			id=listingid,
			source=source,
			price=price,
			zipc=neigh,
			status=status,
			htype=htype,
			bed=beds,
			bath=baths,
			link=url,
			address=address,
			lat=lat,
			long=long,
			last_s_date = last_s_date,
			last_s_price = last_s_price,
			listdate=listdate,
			sqft=sqft,
			lotsqft=lotsqft,
			extras=extras,
		)

		listings.append(listing)

		#cleanup variables so no carryover
		for var in varnames:
			del locals()[var]

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

def neighscrape(neigh:str, source:str, logger:logging, Propertyinfo, citystate):
	CITY = citystate[0]
	STATE = citystate[1].upper()
	
	#TODO - Rebuild so you don't need a neighbborhood to search, just city state
	# #Search by neighborhood
	# if isinstance(neigh, str):
	# 	if " " in neigh:
	# 		neigh = "-".join(neigh.split(" "))
	# 	url = f"https://www.realtor.com/realestateandhomes-search/{CITY}_{STATE}/type-townhome,single-family-home/beds-2/price-na-2600/dog-friendly"

	#Searchby ZipCode
	if isinstance(neigh, int):
		url = f"https://www.realtor.com/realestateandhomes-search/{neigh}/type-single-family-home,townhome,farms-ranches,land/beds-2/price-na-600000"
	
	#Error Trapping
	else:
		logging.critical("Inproper input for area, moving to next site")
		return
	
	# BASE_HEADERS = {
	# 	'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
	# 	'referer': url,
	# 	'origin':'https://www.realtor.com',
	# }
	
	JSON_HEADERS = {
    'accept': 'application/json, text/javascript',
    'accept-language': 'en-US,en;q=0.9',
    'content-type': 'application/json',
	'origin': 'https://www.realtor.com',
	'referer': url,
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
	}
          
	response = requests.get(url, headers=JSON_HEADERS)

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
	lcount = bs4ob.find("div", {"data-testid":"total-results"}).text
	lcount = int("".join(x for x in lcount if x.isnumeric()))
	if lcount > 0:
		results = bs4ob.find("script", {"type":"application/json"})
		property_listings = get_listings(results, neigh, source, Propertyinfo)
		logger.info(f'{len(property_listings)} listings returned from {source}')
		return property_listings
		
	else:
		logger.warning("No listings returned on realtor.  Moving to next site")
	


#Old code, Sadly it won't load past 8 results with a headless browser
#and i vowed never to use those pieces of shit.  Instead we'll grab the application
# json nested at the end of the html for each page

	# for card in result.find_all("div", class_=lambda x: x and x.startswith("BasePropertyCard"), id=lambda x: x and x.startswith("property_id")):
	# 	listingid = card.get("id")
	# 	listingid = listingid.replace("property_id_", "")

	# 	#First grab the link.
	# 	for link in card.find_all("a", class_=lambda x: x and x.startswith("LinkComponent")):
	# 		if link.get("href"):
	# 			url = "https://" + source + link.get("href")
	# 			break
		
	# 	#TODO - Might want house status too as an input. 
		
	# 	for search in card.find_all("div", {"data-testid":"card-content"}):
	# 		#grab the price
	# 		for subsearch in search.find_all("div"):
	# 			if subsearch.get("data-testid") == "card-price":
	# 				price = subsearch.text
	# 				if any(x.isnumeric() for x in price):
	# 					price = money_launderer(subsearch.text)
	# 					break
	# 		#Grab home status
	# 		for subsearch in search.find_all("div", class_=lambda x: x and x.startswith("base__StyledType")):
	# 			status = subsearch.text
	# 			break
		
	# 	#grab the beds, baths, pets
	# 	for search in card.find_all("ul"):
	# 		if search.get("data-testid") == "card-meta":
	# 			sqft = None
	# 			for subsearch in search.find_all("li"):
	# 				if subsearch.get("data-testid")=="property-meta-beds":
	# 					beds = subsearch.find("span").text
	# 					if any(x.isnumeric() for x in beds):
	# 						beds = float("".join(x for x in beds if x.isnumeric()))

	# 				elif subsearch.get("data-testid")=="property-meta-baths":
	# 					baths = subsearch.find("span").text
	# 					if any(x.isnumeric() for x in baths):
	# 						baths = float("".join(x for x in baths if x.isnumeric()))

	# 				elif subsearch.get("data-testid")=="property-meta-sqft":
	# 					sqft = subsearch.find("span", class_="meta-value").text
	# 					if sqft:
	# 						if any(x.isnumeric() for x in sqft):
	# 							sqft = float("".join(x for x in sqft if x.isnumeric()))

	# 				elif subsearch.get("data-testid")=="property-meta-lot-size":
	# 					lotsqft = subsearch.find("span", class_="meta-value").text
	# 					if lotsqft:
	# 						if any(x.isnumeric() for x in lotsqft):
	# 							lotsqft = float("".join(x for x in lotsqft if x.isnumeric()))
	

	# 	#grab address
	# 	for search in card.find_all("div", class_="card-address truncate-line"):
	# 		if search.get("data-testid") == "card-address":
	# 			addy = ""
	# 			for subsearch in search.find_all("div", class_="truncate-line"):
	# 				addy += subsearch.text + " "
	# 			address = addy.strip()