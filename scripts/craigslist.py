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


# cookies = {
#     'cl_b': '4|01390574a6c854a2c021189123aa48e017cc4d1d|1641081102E_6YY',
#     'cl_tocmode': 'hhh%3Agrid',
# }

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
    ('max_price', '2400'),
    ('min_bedrooms', '2'),
    ('availabilityMode', '0'),
    ('pets_dog', '1'),
    ('laundry', ['1', '4', '2', '3']),
    ('sale_date', 'all dates'),
)

#! TODO - Once you get the sqllite database up, adjust the parameter to only search todays postings
#? Will cut down significantly on the number of requests you make. 



response = requests.get('https://chicago.craigslist.org/search/chc/apa', headers=headers, params=params)

if response.status_code != 200:
	print(f'Status code: {response.status_code}')
	print(f'Reason: {response.reason}')
        

#NB. Original query string below. It seems impossible to parse and
#reproduce query strings 100% accurately so the one below is given
#in case the reproduced version is not "correct".
# response = requests.get('https://chicago.craigslist.org/search/chc/apa?hasPic=1&min_price=500&max_price=2400&min_bedrooms=2&availabilityMode=0&pets_dog=1&laundry=1&laundry=4&laundry=2&laundry=3&sale_date=all+dates', headers=headers, cookies=cookies)

time.sleep(np.random.randint(5, 9))

#Get the HTML
bs4ob = BeautifulSoup(response.text, 'lxml')



#%%
# Need to iterate the total number of pages.  
totalcount = int(bs4ob.find('span', class_='totalcount').text)

def get_listings(bs4ob):
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
			price.append(meta_data.find('span', class_='result-price').text)
			title.append(meta_data.find('a', class_='result-title hdrlnk').text)
			hood.append(meta_data.find('span', class_='result-hood').text)
			#postdatetime.append(meta_data.find('time', class_='result-date').get('datetime'))
			# bedrooms.append(meta_data.find('span', class_='housing').text.strip())
	return price, title, hood


links, ids, price, hood, title, = [], [], [], [], []
links = get_listings(bs4ob)
ids = get_posting_ids(bs4ob, links)

price, title, hood = get_meta_data(bs4ob, ids)

#Need a check here on previous data to make sure i'm not looking at old listings. 
#TODO Still need to implement SQLLite DB to store results. 

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

#!Probably will have to fuck with datatypes at some point
results['amenities'] = results['amenities'].astype(object)

#Checkin nulls
# [print(col, ":\t", results[col].isnull().sum()) for col in results.columns]


#%%


for x in range(0, 30): #len(links)

	response = requests.get(links[x], headers=headers)
	bs4_home_ob = BeautifulSoup(response.text, 'lxml')

	#Easy one's to get
	results.loc[x, 'lat'] = bs4_home_ob.find('div', class_='viewposting').get('data-latitude')
	results.loc[x, 'lon'] = bs4_home_ob.find('div', class_='viewposting').get('data-longitude')
	
	#? Could put the bounding box check here to save the extra processing of shit below
	#Todo - Check the bounding box.  Makes sense. 



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
			amen = [amenity.text for amenity in amenities]
			results.at[x, 'amenities'] = amen

	print(f'{x} of {len(links)}')
	time.sleep(np.random.randint(5, 9))



#%%


with open('../data/total_search_area.txt', 'r') as search_coords:
	data = search_coords.read().splitlines()[0]
	lat1, lng1, lat2, lng2 = eval(data)


#? - get all listing links. 
#? - Get all the posting id's
#? - add function to extract geo coords. (might not be available)
#Todo - add function to extract price.
#Todo - add function to extract address (might not be available)
#Todo - add function to extract post creation date.
#Todo - add function to extract number of bedrooms.
#Todo - add function to extract number of bathrooms.







#%%


































# #Data pull from craigslist
# response = CraigslistHousing(
# 	site='chicago', 
# 	area='chc', 
# 	filters={
# 		'max_price': 2300, 
# 		'min_price': 500,
# 		'min_bedrooms': 2,
# 		'has_image': True,
# 		'dogs_ok': True,
# 		'laundry': {'w/d in unit','laundry in bldg', 'laundry on site'},
# 	}
# )


# #results are going to be huge, so probably need to chunk out the results. 

# #Max record count. 
# MAX_RECORDS = int(response.get_results_approx_count())

# #Don't want to piss off craigslist.  so put a limit. 
# if MAX_RECORDS > 3000:
# 	MAX_RECORDS = 100

# listings = response.get_results(sort_by='newest', geotagged=True, limit = 20)
