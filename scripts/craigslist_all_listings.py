#%%
# Resources
# https://betterprogramming.pub/how-i-built-a-python-scraper-to-analyze-housing-locations-on-craigslist-part-1-18d264b0ec4b
# https://www.dataquest.io/blog/apartment-finding-slackbot/
# https://github.com/lewi0622/Housing_Search


import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from datetime import date, datetime
import time
import sys
import os

def get_listings(bs4ob)->list:
	for link in bs4ob.find_all('a', class_='result-title hdrlnk'):
		links.append(link.get('href'))
	return links

def get_posting_ids(bs4ob, links:list)->list:
	for link in links:
		ids.append(int(link.split("/")[-1].strip(".html")))
	return ids

def get_meta_data(bs4ob, ids:list)->(list, list, list):

	#Maybe do a quick check to make sure the listing is the same as the find_all
	#They also include commas in the price.  Might want to remove.  But can process all that after
	for meta_data in bs4ob.find_all('div', class_='result-info'):
		#Probably unecessary to check, but want to make sure i'm lined up on the right listing
		_tempid = int(meta_data.find('a', class_='result-title hdrlnk').get('data-id'))
		if _tempid in ids:
			price.append(money_launderer(meta_data.find('span', class_='result-price').text))
			title.append(meta_data.find('a', class_='result-title hdrlnk').text)
			hood.append(meta_data.find('span', class_='result-hood').text)
			# postdatetime.append(meta_data.find('time', class_='result-date').get('datetime'))
			# bedrooms.append(meta_data.find('span', class_='housing').text.strip())
	return price, title, hood
	
def money_launderer(price:list):
	# Strip dollar signs and commas
	if isinstance(price, str):
		return float(price.replace("$", "").replace(",", ""))
	return price


def in_bounding_box(bounding_box:list, lat:float, lon:float)->bool:
	"""
	Check if location is in the bounding box for an area
	"""
		
	bb_lat_low = bounding_box[0]
	bb_lat_up = bounding_box[2]
	bb_lon_low = bounding_box[1]
	bb_lon_up = bounding_box[3]

	if bb_lat_low < lat < bb_lat_up:
		if bb_lon_low < lon < bb_lon_up:
			return True

	return False


headers = {
	'Connection': 'keep-alive',
	'Pragma': 'no-cache',
	'Cache-Control': 'no-cache',
	'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
	'sec-ch-ua-mobile': '?0',
	'sec-ch-ua-platform': '"Windows"',
	'Upgrade-Insecure-Requests': '1',
	'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
	'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
	'Sec-Fetch-Site': 'none',
	'Sec-Fetch-Mode': 'navigate',
	'Sec-Fetch-User': '?1',
	'Sec-Fetch-Dest': 'document',
	'Accept-Language': 'en-US,en;q=0.9',
}

params = (
	('hasPic', '1'),
	('min_price', '500'),
	('max_price', '2600'),
	('min_bedrooms', '2'),
	('availabilityMode', '0'),
	('pets_dog', '1'),
	('laundry', ['1', '4', '2', '3']),
	('sale_date', 'all dates'),
)

#! TODO - Once you get the sqllite database up, adjust the parameter to only search todays postings
#? Will cut down significantly on the number of requests you make. 
# Request order
	# 1. Request first page to get total count of listings. 
	# 2. Iterate through all summary pages and scrape their links
	# 3. Iterate through each link and 


url = 'https://chicago.craigslist.org/search/chc/apa'

response = requests.get(url, headers=headers, params=params)

#Just in case we piss someone off
if response.status_code != 200:
	print(f'Status code: {response.status_code}')
	print(f'Reason: {response.reason}')

#Get the HTML
bs4ob = BeautifulSoup(response.text, 'lxml')

# Need to iterate the total number of pages.  
totalcount = int(bs4ob.find('span', class_='totalcount').text)
totalpages = int(round(totalcount//120)) + 1

links, ids, price, hood, title, = [], [], [], [], []
links = get_listings(bs4ob)
ids = get_posting_ids(bs4ob, links)

price, title, hood = get_meta_data(bs4ob, ids)

#Create results DF
results = pd.DataFrame(
	{
		"id": ids, 
		"title": title,
		"price": price,
		"hood": hood,	
		"link": links, 
		"source": "craigslist", 
		"amenities": np.nan,
	}
)

#set the dtypes
data_types = {
	"id": "Int64",
	"title": str,
	"price": str,
	"hood": str,
	"link": str,
	"source": str,
	"amenities": object,
}

results = results.astype(data_types)


if totalpages > 1:
	for page in range(1, totalpages):
		links, ids, price, hood, title, = [], [], [], [], []
		url_page = url + '?s=' + str(page*120)
		response = requests.get(url_page, headers=headers, params=params)
		
		#Get the HTML
		bs4ob = BeautifulSoup(response.text, 'lxml')

		links = get_listings(bs4ob)
		ids = get_posting_ids(bs4ob, links)

		price, title, hood = get_meta_data(bs4ob, ids)

		#Append to results DF
		add_results = pd.DataFrame(
				{
		"id": ids, 
		"title": title,
		"price": price,
		"hood": hood,	
		"link": links, 
		"source": "craigslist", 
		"amenities": np.nan,
				}
		).astype(data_types)

		results = pd.concat([results, add_results], ignore_index=True)

		time.sleep(np.random.randint(5, 9))

#Checkin nulls
# [print(col, ":\t", results[col].isnull().sum()) for col in results.columns]


#%%
#establish boundary of interest (GPS coordinates)
with open('../data/total_search_area.txt', 'r') as search_coords:
	bounding_box = eval(search_coords.read().splitlines()[0])

for x in range(0, len(links)): #len(links)

	response = requests.get(links[x], headers=headers)
	#Just in case we piss someone off
	if response.status_code != 200:
		print(f'Status code: {response.status_code}')
		print(f'Reason: {response.reason}')
	bs4_home_ob = BeautifulSoup(response.text, 'lxml')

	#Easy one's to get
	results.loc[x, 'lat'] = bs4_home_ob.find('div', class_='viewposting').get('data-latitude')
	results.loc[x, 'lon'] = bs4_home_ob.find('div', class_='viewposting').get('data-longitude')

	#Todo - Check the bounding box.  Makes sense. 
		#Might want to just boolean if its in the area.  Can drop it later too.  
		#Worried indexes might get fucked if i drop rows mid row.  
			#Or just put a continue in to the next iteration.
	results.loc[x, 'in_search_area'] = in_bounding_box(bounding_box, 
														float(results.loc[x,'lat']), 
														float(results.loc[x, 'lon']))

	#!Cleanup
	address = bs4_home_ob.find('div', class_='mapaddress')
	if address:
		results.loc[x, 'address'] = bs4_home_ob.find('div', class_='mapaddress').text
	else:
		results.loc[x, 'address'] = np.nan

	#Pulling property details.
	#These two groups almost always exist.  Hard coded group order. 
	groups = bs4_home_ob.find_all('p', class_='attrgroup')
	if groups:
		#Group1 - beds/baths + sqft + available
		hous_stats = groups[0].find_all('span')
		if hous_stats:
			for stat in hous_stats:
				if 'ft' in stat.text:
					results.loc[x, 'sqft'] = stat.text

				elif 'BR' in stat.text or 'Ba' in stat.text:
					for b_tag in stat.find_all('b'):
						if b_tag.text.endswith('BR'):
							results.loc[x, 'bedrooms'] = stat.text.split(' / ')[0][0]
						elif b_tag.text.endswith('Ba'):
							results.loc[x, 'bathrooms'] = stat.text.split(' / ')[1][0]

				elif stat.has_attr('data-date'):		
					results.loc[x, 'postdate'] = stat.get('data-date')
					
		#Group2 - Random amenities
		amenities = groups[1].find_all('span')
		if amenities:
			#!Cleanup
			amen = [amenity.text for amenity in amenities]
			results.at[x, 'amenities'] = amen

	print(f'{x} of {len(links)}')
	time.sleep(np.random.randint(5, 13))

#%%


#? - get all listing links. 
#? - Get all the posting id's
#? - add function to extract geo coords. (might not be available)
#? - add function to extract price.
#? - add function to extract address (might not be available)
#? - add function to extract post creation date.
#? - add function to extract number of bedrooms.
#? - add function to extract number of bathrooms.
#? - Check bounding box area search. 
#TODO - Clean/add variables: money, nearest L stop, distance to nearest L stop
#TODO - True values for outer search area, assign to neighborhood GPS coords.
#TODO - Implement SQLLite DB to store results. 


# df.groupby(['web_Product_Desc']).agg({"price_Orig":[min,max,"count",np.mean],"quantity_On_Hand":[np.sum]})

#Program overview
#1. Pull the first page to get a total count for search
#2. Iterate through each page creating a df for each page
#3. Merge all those bastards into one big df


