
import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
from datetime import date, datetime
import time


#plan

#Update craigs query that pulls just today's posts.  
#Checks csv for listings id to see if it is already in there. 
#If it is, skip it.  If not, add it to the csv.

#Implement text notifcation or email notification. 

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


def get_listings(bs4ob)->list:
	"""[summary]

	Args:
		bs4ob ([BeautifulSoup object]): [html of craigslist summary page]

	Returns:
		list: [all the links in the summary page]
	"""	
	for link in bs4ob.find_all('a', class_='result-title hdrlnk'):
		if link.get('href').startswith("https://chicago.craigslist.org/chc"):
			links.append(link.get('href'))
	return links

def get_posting_ids(bs4ob, links:list)->list:
	"""[Get the posting id's from the link list]

	Args:
		bs4ob ([Beautiful Soup Object]): [html of the craigslist summary page]
		links (list): [list of links to the individual postings]

	Returns:
		ids([list]): [List of the posting id's]
	"""	
	for link in links:
		ids.append(int(link.split("/")[-1].strip(".html")))
	return ids

def get_meta_data(bs4ob, ids:list)->(list, list, list):
	"""[Extract the meta data from the craiglist summary page]

	Args:
		bs4ob ([BeautifulSoup object]): [html of craigslist summary page]
		ids ([list]): [id list of the listings]

	Returns:
		price, title, hood [list, list , list]: [returns the basic info of posting on summary page]
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
		[list]: [list of prices as floats]
	"""	
	if isinstance(price, str):
		return float(price.replace("$", "").replace(",", ""))
	return price


def in_bounding_box(bounding_box:list, lat:float, lon:float)->bool:
	"""[Given two corners of a box on a map.  Determine if a point is
	 within said box.  Step 1.  You cut a hole in that box.]

	Args:
		bounding_box (list): [list of GPS coordinates of the box]
		lat (float): [lattitude of point]
		lon (float): [longitude of point]

	Returns:
		bool: [Whether or not is within the given GPS ranges 
		in the bounding box]
	"""		
	bb_lat_low = bounding_box[0]
	bb_lat_up = bounding_box[2]
	bb_lon_low = bounding_box[1]
	bb_lon_up = bounding_box[3]

	if bb_lat_low < lat < bb_lat_up:
		if bb_lon_low < lon < bb_lon_up:
			return True

	return False

def inner_neighborhood(lat:float, lon:float)->str:
	"""[Function to determine the smaller neighborhood within a given boundary.
		Current boundaries are located in neighborhoods.txt file. Amend to fit 
		your own purposes.  I manually went through google maps to extract them]

	Args:
		lat ([type]): [lattitude of point]
		lon ([type]): [longitude of point]

	Returns:
		[str]: [If found within the neighborhood.txt file, 
		returns the name of the neighborhood. If not, returns np.nan]
	"""	
	with open('../data/neighborhoods.txt', 'r') as nbh:
		neighborhoods = nbh.read().splitlines()
		inner_hood_dict = {hood.split(':')[0].strip() : eval(hood.split(':')[1]) for hood in neighborhoods[:5]}

		for hood, coords in inner_hood_dict.items():
			if in_bounding_box(coords, lat, lon):
				return hood
		return np.nan

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
    ('postedToday', '1'),
    ('min_price', '500'),
    ('max_price', '2600'),
    ('min_bedrooms', '2'),
    ('availabilityMode', '0'),
    ('pets_dog', '1'),
    ('laundry', ['1', '4', '2', '3']),
    ('sale_date', 'all dates'),
)

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

#establish boundary of interest (GPS coordinates)
with open('./data/total_search_area.txt', 'r') as search_coords:
	bounding_box = eval(search_coords.read().splitlines()[0])

#Previous listings
all_results = pd.read_csv("./data/craigs_all.csv", delimiter=',' , index_col=0)
#Load L stops
L_stops = pd.read_csv('./data/CTA_Lstops.csv', delimiter=',')

for x in range(0, results.shape[0]):
	#Quick check to see if we've already scraped the listing.
	if results.loc[x, 'id'] in all_results['id'].values:
		continue

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
			amen = [amenity.text for amenity in amenities]
			results.at[x, 'amenities'] = amen
	
	#Get the date posted
	posting_info = bs4_home_ob.find('div', class_='postinginfos')
	if posting_info:
		results.loc[x, 'postdate'] = posting_info.find('p', class_='postinginfo reveal').text[8:]
	
	#Get the distance to the closest L stop
	min_dist = np.inf
	min_idx = 0

	lat1 = float(results.loc[x, 'lat'])
	lon1 = float(results.loc[x, 'lon'])
	for L_stop_idx in L_stops.index:
		lat2 = float(L_stops.loc[L_stop_idx, "Location"].strip("()").split(',')[0])
		lon2 = float(L_stops.loc[L_stop_idx, "Location"].strip("()").split(',')[1])
		dist = haversine_distance(lat1, lon1, lat2, lon2)
		if dist < min_dist:
			min_dist = round(dist, 2)
			min_L_stop = L_stops.loc[L_stop_idx, "STATION_NAME"]

		results.loc[x, 'closest_L_stop'] = min_L_stop
		results.loc[x, 'L_min_dist'] = min_dist
		
	#If its in the search area, add it to the csv
	if results.loc[x, 'in_search_area'] == True:
		print(f'New home found at {results.loc[x, "link"]}')
		#Insert new record into all_results
		all_results = all_results.append(results.loc[x, :])
		#Save the new record
		all_results.to_csv("./data/craigs_all.csv", index=False)
		#TODO - Implement a way to send a text to the user. 


	time.sleep(np.random.randint(5, 13))
