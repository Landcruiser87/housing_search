#%%

import requests
import numpy as np
import pandas as pd
import json
from datetime import date, datetime
import time
import sys
import os
from craigslist import CraigslistHousing

#Data pull from craigslist
response = CraigslistHousing(site='chicago', 
							area='chc', 
							filters={'max_price': 2300, 
									 'min_price': 500,
									 'min_bedrooms': 2,
									 'has_image': True,
									 'dogs_ok': True,
									 'laundry': {'w/d in unit','laundry in bldg', 'laundry on site'},
								})


#results are going to be huge, so probably need to chunk out the results. 

#Max record count. 
MAX_RECORDS = int(response.get_results_approx_count())


listings = response.get_results(sort_by='newest', geotagged=True, limit = 50)

with open('./data/total_search_area.txt', 'r') as search_coords:
	
for listing in listings:



#Chunk out the pages into probably 20 records, 
#Process the results that are within the serach area. 






























# cookies = {
#     'cl_b': '4|335be9d38652077f88e297d559c4e3ceddea7e6e|1640949278y5-qM',
#     'cl_def_hp': 'chicago',
#     'cl_tocmode': 'hhh%3Agrid',
# }

# headers = {
#     'Connection': 'keep-alive',
#     'Pragma': 'no-cache',
#     'Cache-Control': 'no-cache',
#     'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="96", "Google Chrome";v="96"',
#     'sec-ch-ua-mobile': '?0',
#     'sec-ch-ua-platform': '"Windows"',
#     'Upgrade-Insecure-Requests': '1',
#     'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
#     'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
#     'Sec-Fetch-Site': 'same-site',
#     'Sec-Fetch-Mode': 'navigate',
#     'Sec-Fetch-User': '?1',
#     'Sec-Fetch-Dest': 'document',
#     'Referer': 'https://nmi.craigslist.org/',
#     'Accept-Language': 'en-US,en;q=0.9',
# }

# params = (
#     ('availabilityMode', '0'),
#     ('pets_dog', '1'),
#     ('postal', '60640'),
#     ('search_distance', '3'),
# )

# response = requests.get('https://chicago.craigslist.org/d/apartments-housing-for-rent/search/apa', headers=headers, params=params, cookies=cookies)

#NB. Original query string below. It seems impossible to parse and
#reproduce query strings 100% accurately so the one below is given
#in case the reproduced version is not "correct".
# response = requests.get('https://chicago.craigslist.org/d/apartments-housing-for-rent/search/apa?availabilityMode=0&pets_dog=1&postal=60640&search_distance=3', headers=headers, cookies=cookies)
