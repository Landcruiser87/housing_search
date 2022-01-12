#%%

import requests
from bs4 import BeautifulSoup
from sodapy import Socrata
import numpy as np
import pandas as pd
import datetime
import time

def get_listings(bs4ob)->list:
	"""[summary]

	Args:
		bs4ob ([BeautifulSoup object]): [html of craigslist summary page]

	Returns:
		list: [all the links in the summary page]
	"""	
	for link in bs4ob.find_all('a', class_='result-title hdrlnk'):
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
#Request order
	# 1. Request first page to get total count of listings. 
	# 2. Iterate through all summary pages and scrape their links
	# 3. Iterate through each link and scrape the individual posting 


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

for x in range(0, results.shape[0]):

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
in_outer_area = results.copy()
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


for idx in in_outer_area.index:
	min_dist = np.inf
	min_idx = 0
	lat1 = in_outer_area.loc[idx, 'lat']
	lon1 = in_outer_area.loc[idx, 'lon']
	for L_stop_idx in L_stops.index:
		lat2 = float(L_stops.loc[L_stop_idx, "Location"].strip("()").split(',')[0]) 
		lon2 = float(L_stops.loc[L_stop_idx, "Location"].strip("()").split(',')[1])
		dist = haversine_distance(lat1, lon1, lat2, lon2)
		if dist < min_dist:
			min_dist = round(dist, 2)
			min_L_stop = L_stops.loc[L_stop_idx, "STATION_NAME"]
			continue

	in_outer_area.loc[idx, 'closest_L_stop'] = min_L_stop
	in_outer_area.loc[idx, 'L_min_dist'] = min_dist

	# print(f'The closest station for property {in_outer_area.loc[idx, "address"]}') 
	# print(f'Station {min_L_stop}: {min_dist} miles away')



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
#? - Clean/add variables: money, nearest L stop, distance to nearest L stop
#? - True values for outer search area, assign to neighborhood GPS coords.
#? - Change location of postdate extraction
#? - Pull crime data from data.cityofchicago.org
#? - Aggregate a crime scoring for each property based on previous crimes that were
	#? - Within a mile radius
		#? = Use haversine 
	#? - Isolate serious crimes (Felonies, guncrimes, domestic violence)


#TODO - Connect to RapidAPI and pull Walkscore, Crimescore, and Transit score.

# df.groupby(['web_Product_Desc']).agg({"price_Orig":[min,max,"count",np.mean],"quantity_On_Hand":[np.sum]})





# Resources
# https://betterprogramming.pub/how-i-built-a-python-scraper-to-analyze-housing-locations-on-craigslist-part-1-18d264b0ec4b
# https://www.dataquest.io/blog/apartment-finding-slackbot/
# https://github.com/lewi0622/Housing_Search



# %%
#Testing Socrata API

#! DELETE ME AFTER YOU'RE DONE PLAYING AROUND YOU WHACKO
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

def date_convert(time_big:pd.Series)->(datetime, datetime):
	dateOb = datetime.datetime.strptime(time_big,'%Y-%m-%dT%H:%M:%S.%f')
	return dateOb


def crime_score(lat1:float, lon1:float) -> dict:
	with open('../secret/chicagodata.txt') as login_file:
		login = login_file.read().splitlines()
		app_token = login[0].split(':')[1]
		
	client = Socrata("data.cityofchicago.org", app_token)

	#Search radius is 0.91 miles
	#Sets lookback to 1 year from today

	ze_date = str(datetime.datetime.today().date() - datetime.timedelta(days=365))

	results = client.get("ijzp-q8t2",
						select="id, date, description, latitude, longitude, primary_type ",
						where=f"latitude > {lat1-0.1} AND latitude < {lat1+0.1} AND longitude > {lon1-0.1} AND longitude < {lon1+0.1} AND date > '{ze_date}'",
						limit=800000)

	crime_df = pd.DataFrame.from_dict(results)
	crime_df['date_conv'] = crime_df.apply(lambda x: date_convert(x.date), axis=1)
	crime_df['date_short'] = crime_df.apply(lambda x: x.date_conv.date(), axis=1)
	crime_df['crime_time'] = crime_df.apply(lambda x: x.date_conv.time(), axis=1)
	crime_df.drop(['date_conv', 'date'], axis=1, inplace=True)

	crime_df['distance'] = crime_df.apply(lambda x: haversine_distance(lat1, lon1, x.latitude, x.longitude), axis=1)
	
	#Check the last dates record.  If its not within the last year, 
	#make another request until we hit that date. 
		# Don't forget to filter any data that may come in extra. 

	date_check = crime_df.date_short.min()
	if date_check > datetime.date.today() - datetime.timedelta(days=365):
		#TODO Need to figure out how to remake the request if i hit the 800k limit. 
		raise ValueError('Yo Query needeth be BIGGER')

	#Checking memory consumption
	#sum(crime_df.memory_usage(deep=True) / 1_000_000)
	#Req 500k records costs you about 21.7 MB

	total_crimes = crime_df.shape[0]

	scores = {
		'drug_score':0,
		'gun_score':0,
		'murder_score':0,
		'perv_score':0,
		'theft_score':0,
		'violence_score':0,
		'property_d_score':0
	}
	#Example of primary_type categories
	# THEFT                                918
	# BATTERY                              787
	# DECEPTIVE PRACTICE                   760
	# CRIMINAL DAMAGE                      552z
	# ASSAULT                              370
	# OTHER OFFENSE                        285z
	# MOTOR VEHICLE THEFT                  246
	# ROBBERY                              243
	# WEAPONS VIOLATION                    214
	# NARCOTICS                            191
	# BURGLARY                             166
	# CRIMINAL TRESPASS                     92z
	# OFFENSE INVOLVING CHILDREN            37
	# CRIMINAL SEXUAL ASSAULT               27
	# PUBLIC PEACE VIOLATION                20
	# SEX OFFENSE                           20
	# INTERFERENCE WITH PUBLIC OFFICER      18
	# STALKING                              15
	# HOMICIDE                              14
	# ARSON                                 12
	# LIQUOR LAW VIOLATION                   4
	# PROSTITUTION                           3
	# INTIMIDATION                           3
	# CONCEALED CARRY LICENSE VIOLATION      1
	# OBSCENITY                              1
	# KIDNAPPING                             1

	narcotics = ['NARCOTICS', 'OTHER NARCOTIC VIOLATION']
	guns = ['WEAPONS VIOLATION', 'CONCEALED CARRY LICENCE VIOLATION']
	theft = ['BURGLARY', 'ROBBERY', 'MOTOR VEHICLE THEFT', 'THEFT', 'DECEPTIVE PRACTICE']
	sex_crimes = ['CRIMINAL SEXUAL ASSAULT', 'SEX OFFENSE',  'PROSTITUTION', 'STALKING']
	human_violence = ['BATTERY', 'ASSAULT', 'OFFENSE INVOLVING CHILDREN', 'INTIMIDATION', 'KIDNAPPING']

	for idx in crime_df.index:
		#Drugs
		if crime_df.loc[idx, 'primary_type'] in narcotics:
			scores['drug_score'] += 1

		#Guns
		if crime_df.loc[idx, 'primary_type'] in guns:
			scores['gun_score'] += 1
 
		#Gun description subsearch if primary_type doesn't catch it.
		elif set(crime_df.loc[idx, 'description'].split()) & set(['HANDGUN', 'ARMOR', 'GUN', 'FIREARM', 'AMMO', 'AMMUNITION', 'RIFLE']):
			scores['gun_score'] += 1
		
		#Murder
		if crime_df.loc[idx, 'primary_type'] in ['HOMICIDE']:
			scores['murder_score'] += 1
		
		#Theft
		if crime_df.loc[idx, 'primary_type'] in theft:
			scores['theft_score'] =+ 1

		#Sexual Crimes
		if crime_df.loc[idx, 'primary_type'] in sex_crimes:
			scores['perv_score'] += 1

		#Sex Crimes subsearch
		elif set(crime_df.loc[idx, 'description'].split()) & set(['PEEPING TOM']):
			scores['perv_score'] += 1

		#humanViolence
		if crime_df.loc[idx, 'primary_type'] in human_violence:
			scores['violence_score'] += 1

		#humanviolence subsearch
		elif set(crime_df.loc[idx, 'description'].split()) & set(['CHILDREN']):
			scores['violence_score'] += 1

		#property damage
		if crime_df.loc[idx, 'primary_type'] in ['CRIMINAL DAMAGE']:
			scores['property_d_score'] += 1
		
		time.sleep(2)
		
	scores = {k:(v/total_count)*100 for k, v in scores.items()}
	return scores


all_results = pd.read_csv("../data/craigs_all.csv", delimiter=',', index_col=0, header=-0)

all_results['scores'] = all_results.apply(lambda x: crime_score(x.lat, x.lon), axis=1)



#For crime score lets aggregate the types of crimes and assign them with a point value. 
#guns, drugs, murder, theft, human





































# # %%
# def date_convert(time_big:pd.Series)->(datetime, datetime):
# 	dateOb = datetime.datetime.strptime(time_big,'%Y-%m-%dT%H:%M:%S.%f')
# 	return dateOb


# with open('../secret/chicagodata.txt') as login_file:
# 	login = login_file.read().splitlines()
# 	app_token = login[0].split(':')[1]

# lat1 = 41.911232
# lon1 = -87.682455
# client = Socrata("data.cityofchicago.org", app_token)
# #TODO: Format the date correctly for the SQL.  Means i need the date in single quotes. '2021-01-01'

# ze_date = str(datetime.datetime.today().date() - datetime.timedelta(days=365)).replace("'", '"')



# results = client.get("ijzp-q8t2",
# 	select="id, date, description, latitude, longitude, primary_type ",
# 	where=f"latitude > {lat1-0.1} AND latitude < {lat1+0.1} AND longitude > {lon1-0.1} AND longitude < {lon1+0.1} AND date > '{ze_date}'",
# 	limit=800000)


# crime_df = pd.DataFrame.from_dict(results)
# crime_df['date_conv'] = crime_df.apply(lambda x: date_convert(x.date), axis=1)
# crime_df['date_short'] = crime_df.apply(lambda x: x.date_conv.date(), axis=1)
# crime_df['crime_time'] = crime_df.apply(lambda x: x.date_conv.time(), axis=1)
# crime_df.drop(['date_conv', 'date'], axis=1, inplace=True)

# %%
