import logging
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import requests

# AREAS = [
# 	'Ravenswood',
# 	# 'Lincoln Square',
# 	# 'Ravenswood Gardens',
# 	# 'Budlong Woods',
# 	# 'Bowmanville',
# ]

def get_listings(bs4ob, links:list)->list:
	"""[Gets the list of links to the individual postings]

	Args:
		bs4ob ([BeautifulSoup object]): [html of craigslist summary page]

	Returns:
		links (list): [all the links in the summary page]
	"""	

	for link in bs4ob.find_all('a', class_='result-title hdrlnk'):
		if link.get('href').startswith("https://chicago.craigslist.org/chc"):
			links.append(link.get('href'))
	return links

def get_posting_ids(bs4ob, links:list, ids:list)->list:
	"""[Strips the posting id's from the link list]

	Args:
		bs4ob ([Beautiful Soup Object]): [html of the craigslist summary page]
		links (list): [list of links to the individual postings]

	Returns:
		ids (list): [List of the posting id's]
	"""	
	for link in links:
		ids.append(int(link.split("/")[-1].strip(".html")))
	return ids

def get_meta_data(bs4ob, ids:list, price, title, hood):
	"""[Extract the meta data from the craiglist summary page]

	Args:
		bs4ob (BeautifulSoup object): [html of page]
		ids (list): [id list of the listings]

	Returns:
		price, title, hood (list, list , list): [returns the basic info of posting on summary page]
	"""
	for meta_data in bs4ob.find_all('div', class_='result-info'):
		_tempid = int(meta_data.find('a', class_='result-title hdrlnk').get('data-id'))
		if _tempid in ids:
			price.append(money_launderer(meta_data.find('span', class_='result-price').text))
			title.append(meta_data.find('a', class_='result-title hdrlnk').text)
			hood.append(meta_data.find('span', class_='result-hood').text)
			# postdatetime.append(meta_data.find('time', class_='result-date').get('datetime'))
			# bedrooms.append(meta_data.find('span', class_='housing').text.strip())
	return price, title, hood
	
def money_launderer(price:list)->list:
	"""[Strips dollar signs and comma from the price]

	Args:
		price (list): [list of prices as strs]

	Returns:
		price (list): [list of prices as floats]
	"""	
	if isinstance(price, str):
		return float(price.replace("$", "").replace(",", ""))
	return price


def neighscrape(neigh:str, logger:logging, Propertyinfo):
	#TODO dict of neighborthoods exact mapping
 

	if " " in neigh:
		neigh = "-".join(neigh.split(" "))

	headers = {
		'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
		'referer': 'https://www.realtor.com/apartments/Chicago_IL',
		'origin':'https://www.realtor.com',
	}

	url = f"https://www.realtor.com/apartments/{neigh}_Chicago_IL/type-townhome,single-family-home/price-na-2600/dog-friendly"
          
	response = requests.get(url, headers=headers)

	#Just in case we piss someone off
	if response.status_code != 200:
		logger.warning(f'Status code: {response.status_code}')
		logger.warning(f'Reason: {response.reason}')
		return "Error in scraping"

	#Get the HTML
	bs4ob = BeautifulSoup(response.text, 'lxml')

	# Get the total number of pages.  
	totalcount = bs4ob.find('div', class_='MatchProperties_totalMatchingProperties__a1MwL').text
	totalcount = int(totalcount.split(" ")[0])

	links, ids, price, hood, title, = [], [], [], [], []
	links = get_listings(bs4ob)
	ids = get_posting_ids(bs4ob, links)
	price, title, hood = get_meta_data(bs4ob, ids, price, title, hood)

	logger.info("realtor!!")


def zipscrape():
	pass
	#TODO build separate extraction for zip codes. 