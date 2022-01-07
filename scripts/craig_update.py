
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
