#%%

import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from datetime import date, datetime
import time


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

def inner_neighborhood(lat, lon):
	with open('../data/neighborhoods.txt', 'r') as nbh:
		neighborhoods = nbh.read().splitlines()
		inner_hood_dict = {hood.split(':')[0].strip() : eval(hood.split(':')[1]) for hood in neighborhoods[:5]}

		for hood, coords in inner_hood_dict.items():
			if in_bounding_box(coords, lat, lon):
				return hood
		return np.nan

# for i in in_ravens.index:
# 	lat = in_ravens.loc[i, 'lat']	
# 	lon = in_ravens.loc[i, 'lon']

# 	print(inner_neighborhood(lat, lon))

#%%

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

for x in range(0, results.shape[0]+1):

	response = requests.get(results.loc[x, 'link'], headers=headers)
	#Just in case we piss someone off
	if response.status_code != 200:
		print(f'Status code: {response.status_code}')
		print(f'Reason: {response.reason}')
	bs4_home_ob = BeautifulSoup(response.text, 'lxml')

	#Easy one's to get
	lat = bs4_home_ob.find('div', class_='viewposting').get('data-latitude')
	if lat:
		results.loc[x, 'lat'] = lat
	else:
		results.loc[x, 'lat'] = np.nan

	lon = bs4_home_ob.find('div', class_='viewposting').get('data-longitude')
	if lon:
		results.loc[x, 'lon'] = lon
	else:
		results.loc[x, 'lon'] = np.nan

	#Checking if home is in the bounding box of search area.
	results.loc[x, 'in_search_area'] = in_bounding_box(bounding_box, 
														float(results.loc[x,'lat']), 
														float(results.loc[x, 'lon']))

	#Get the address
	address = bs4_home_ob.find('div', class_='mapaddress')
	if address:
		results.loc[x, 'address'] = bs4_home_ob.find('div', class_='mapaddress').text
	else:
		results.loc[x, 'address'] = np.nan

	#Get the property details
	#Note:These next two groups almost always exist.  Hard coded group order. 

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

		#Group2 - Random amenities
		amenities = groups[1].find_all('span')
		if amenities:
			#!Cleanup
			amen = [amenity.text for amenity in amenities]
			results.at[x, 'amenities'] = amen
	
	#Get the date posted
	posting_info = bs4_home_ob.find('div', class_='postinginfos')
	if posting_info:
		results.loc[x, 'postdate'] = posting_info.find('p', class_='postinginfo reveal').text[8:]

	print(f'{x} of {results.shape[0]}')
	time.sleep(np.random.randint(5, 13))



#%%
def haversine_distance(lat1:float, lon1:float, lat2:float, lon2:float)->float:
	from math import radians, cos, sin, asin, sqrt
	"""[Uses the haversine formula to calculate the distance between 
	two points on a sphere]

	Args:
		lat1 (float): [latitude of first point]
		lon1 (float): [longitude of first point]
		lat2 (float): [latitude of second point]
		lon2 (float): [latitue of second point]

	Returns:
		float: [Distance between two GPS points in miles]

	Source:https://stackoverflow.com/questions/42686300/how-to-check-if-coordinate-inside-certain-area-python
	"""	
	# convert decimal degrees to radians 
	lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

	# haversine formula 
	dlon = lon2 - lon1 
	dlat = lat2 - lat1 
	a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
	c = 2 * asin(sqrt(a)) 
	r = 3956 # Radius of earth in miles. Use 6371 for kilometers
	return c * r


#Load data	
# in_outer_area = pd.read_csv('../data/craigs_all.csv', delimiter=',')
in_outer_area = results[results['in_search_area']==True]
in_outer_area  = in_outer_area.astype(
	{
	'lat': float, 
	'lon': float, 
	'price': float, 
	'bedrooms': int, 
	'bathrooms': int
	}
)

#Load L stops
L_stops = pd.read_csv('../data/CTA_Lstops.csv', delimiter=',')


min_dist = np.inf
min_idx = 0



for idx in in_outer_area.index:
	lat1 = in_outer_area.loc[idx, 'lat']
	lon1 = in_outer_area.loc[idx, 'lon']
	for L_stop_idx in L_stops.index:
		lat2 = float(L_stops.loc[L_stop_idx, "Location"].strip("()").split(',')[0])
		lon2 = float(L_stops.loc[L_stop_idx, "Location"].strip("()").split(',')[1])
		dist = haversine_distance(lat1, lon1, lat2, lon2)
		if dist < min_dist:
			min_dist = round(dist, 2)
			min_idx = idx
			min_L_stop = L_stops.loc[L_stop_idx, "STATION_NAME"]
	
	in_outer_area.loc[idx, 'closest_L_stop'] = min_L_stop
	in_outer_area.loc[idx, 'L_min_dist'] = min_dist


	# print(f'The closest station for property {in_outer_area.loc[idx, "address"]}') 
	# print(f'Station {min_L_stop}: {min_dist} miles away')


#? - get all listing links. 
#? - Get all the posting id's
#? - add function to extract geo coords. (might not be available)
#? - add function to extract price.
#? - add function to extract address (might not be available)
#? - add function to extract post creation date.
#? - add function to extract number of bedrooms.
#? - add function to extract number of bathrooms.
#? - Check bounding box area search. 
#? - Clean/add variables: money, nearest L stop, distance to nearest L stop
#? - True values for outer search area, assign to neighborhood GPS coords.
#? - Change location of postdate extraction

#TODO - Connect to RapidAPI and pull Walkscore, Crimescore, and Transit score.

#TODO - Implement SQLLite DB to store results. 

# df.groupby(['web_Product_Desc']).agg({"price_Orig":[min,max,"count",np.mean],"quantity_On_Hand":[np.sum]})





# Resources
# https://betterprogramming.pub/how-i-built-a-python-scraper-to-analyze-housing-locations-on-craigslist-part-1-18d264b0ec4b
# https://www.dataquest.io/blog/apartment-finding-slackbot/
# https://github.com/lewi0622/Housing_Search



# %%
