import logging
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests
import time
import support

def get_links(bs4ob:BeautifulSoup, CITY:str)->list:
	"""[Gets the list of links to the individual postings]

	Args:
		bs4ob ([BeautifulSoup object]): [html of craigslist summary page]

	Returns:
		links (list): [all the links in the summary page]
	"""	
	links = []
	for link in bs4ob.find_all('a'):
		url = link.get("href")
		if url.startswith(f"https://{CITY}.craigslist.org/chc"):
			links.append(url)
	return links
	
def get_listings(result:BeautifulSoup, neigh:str, source:str, Propertyinfo, logger, citystate:tuple)->list:
	"""[Gets the list of links to the individual postings]

	Args:
		bs4ob ([BeautifulSoup object]): [html of realtor page]

	Returns:
		properties (list[Propertyinfo]): [all the links in the summary page]
	"""
	CITY = citystate[0].lower()
	STATE = citystate[1].lower()

	HEADERS = {
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
		'Accept-Language': 'en-US,en;q=0.9',
		'Cache-Control': 'max-age=0',
		'Connection': 'keep-alive',
		'Origin': f'https://{CITY}.craigslist.org',
		'Referer': f'https://{CITY}.craigslist.org/',
		'Sec-Fetch-Dest': 'document',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'same-origin',
		'Sec-Fetch-User': '?1',
		'Upgrade-Insecure-Requests': '1',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
		'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
		'sec-ch-ua-mobile': '?0',
		'sec-ch-ua-platform': '"Windows"',
	}

	listings = []
	
	#lat long info is in here.  Could merge them with the search. 
	#result.select_one('script[id*="ld_searchpage_results"]')
	# contents = json.loads(card.contents[0].strip("\n").strip())
	links = get_links(result, CITY)
	
	for link in links: 
		
		#Being that craigs doesn't put all the info in the search page card,
		#we've gotta Dig for the details like we did last time by scraping each
		#listing.  Meaning more requests and longer wait times. 

		response = requests.get(link, headers=HEADERS)
		support.sleepspinner(np.random.randint(2, 6), f'Craigs {neigh} request nap')
		bs4ob = BeautifulSoup(response.text, "lxml")

		#Just in case we piss someone off
		if response.status_code != 200:
			# If there's an error, log it and return no data for that site
			logger.warning(f'Status code: {response.status_code}')
			logger.warning(f'Reason: {response.reason}')
			continue

		#Get posting id from the url.
		listingid = link.split('/')[-1].strip(".html")
		url = link

		# Grab the price.
		for search in bs4ob.find_all("span", class_="price"):
			price = search.text
			if any(x.isnumeric() for x in price):
				price = money_launderer(search.text)
			break

		#grab bed / bath
		for search in bs4ob.find_all("span", class_="attr important"):
			text = search.text.lower()
			if "ft" in text:
				sqft = search.text.strip("\n").strip()
				#bug, maybe remove ft
			elif "br" in text:
				beds, baths = search.text.strip("\n").strip().split("/")
				if any(x.isnumeric() for x in beds):
					beds = float("".join(x for x in beds if x.isnumeric()))
				if any(x.isnumeric() for x in baths):
					baths = float("".join(x for x in baths if x.isnumeric()))

		#grab addy
		for search in bs4ob.find_all("h2", class_="street-address"):
			addy = search.text
			break
			
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
		
		pets = True

		#IDEA Since we can't search by neighborhood on craigs we have to just assign
		#it to chicago as that's Where the base search is..  Although.. I do
		#have lat / longs and the boundaries of the neighborhoods I want to
		#search.  So I could use the bounding box formula to see if they were in
		#that area. 
  
		listing = Propertyinfo(
			id=listingid,
			source=source,
			price=price,
			neigh=CITY,
			bed=beds,
			sqft=sqft,
			bath=baths,
			dogs=pets,
			link=url,
			address=addy
		)
		listings.append(listing)

	return listings

def neighscrape(neigh:str, source:str, logger:logging, Propertyinfo, citystate:tuple):
	CITY = citystate[0].lower()
	STATE = citystate[1].lower()

	HEADERS = {
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
		'Accept-Language': 'en-US,en;q=0.9',
		'Cache-Control': 'max-age=0',
		'Connection': 'keep-alive',
		'Origin': f'https://{CITY}.craigslist.org',
		'Referer': f'https://{CITY}.craigslist.org/',
		'Sec-Fetch-Dest': 'document',
		'Sec-Fetch-Mode': 'navigate',
		'Sec-Fetch-Site': 'same-origin',
		'Sec-Fetch-User': '?1',
		'Upgrade-Insecure-Requests': '1',
		'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
		'sec-ch-ua': '"Chromium";v="124", "Google Chrome";v="124", "Not-A.Brand";v="99"',
		'sec-ch-ua-mobile': '?0',
		'sec-ch-ua-platform': '"Windows"',
	}
	#Change these to suit your housing requirements
	params = (
		("hasPic", "1"),
		# ("postedToday", "1"),
		("housing_type",["10", "2", "3", "4", "5", "6", "8", "9"]),
		("min_price", "500"),
		("max_price", "2600"),
		("min_bedrooms", "2"),
		("min_bathrooms", "1"),
		("availabilityMode", "0"),
		("pets_dog", "1"),
		("laundry", ["1", "4", "2", "3"]),
		("parking", ["2", "3", "5"]),
		("sale_date", "all dates"),
	)

	url = f'https://{CITY}.craigslist.org/search/chc/apa'
	#BUG.  So....  craigs encodes
	#region into their URl.  So you'll have to change that
	#You can remove the chc from the search link to search an entire city, 
	#But that will likely generate too many results. 
 
	response = requests.get(url, headers=HEADERS, params=params)

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
	results = bs4ob.find_all("li", class_="cl-static-search-result")
	if results:
		if len(results) > 0:
			property_listings = get_listings(bs4ob, neigh, source, Propertyinfo, logger, citystate)
			logger.info(f'{len(property_listings)} listings returned from {source}')
			return property_listings
	
	else:
		logger.warning("No listings returned on craigs.  Moving to next site")


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
