#%%
# Resources
# https://betterprogramming.pub/how-i-built-a-python-scraper-to-analyze-housing-locations-on-craigslist-part-1-18d264b0ec4b
# https://www.dataquest.io/blog/apartment-finding-slackbot/
# https://github.com/lewi0622/Housing_Search


import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import json
from datetime import date, datetime
import time
import sys
import os


cookies = {
    'cl_b': '4|01390574a6c854a2c021189123aa48e017cc4d1d|1641081102E_6YY',
    'cl_tocmode': 'hhh%3Agrid',
}

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

response = requests.get('https://chicago.craigslist.org/search/chc/apa', headers=headers, params=params, cookies=cookies)

#NB. Original query string below. It seems impossible to parse and
#reproduce query strings 100% accurately so the one below is given
#in case the reproduced version is not "correct".
# response = requests.get('https://chicago.craigslist.org/search/chc/apa?hasPic=1&min_price=500&max_price=2400&min_bedrooms=2&availabilityMode=0&pets_dog=1&laundry=1&laundry=4&laundry=2&laundry=3&sale_date=all+dates', headers=headers, cookies=cookies)

bs4ob = BeautifulSoup(response.text, 'lxml')
links = []

for link in bs4ob.find_all('li', {'class': 'result-row'}):
	links.append(link.get('href'))

#Todo - add function to extract geo coords.
#Todo - add function to extract price.
#Todo - add function to extract address.
#Todo - add function to extract date.
#Todo - add function to extract number of bedrooms.
#Todo - add function to extract number of bathrooms.






with open('../data/total_search_area.txt', 'r') as search_coords:
	data = search_coords.read().splitlines()[0]
	lat1, lng1, lat2, lng2 = eval(data)





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
