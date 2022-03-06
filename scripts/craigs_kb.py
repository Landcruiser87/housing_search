import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import datetime
import time
import support

def get_listings(bs4ob, totalcount:int)->list:
	"""[summary]

	Args:
		bs4ob ([type]): [description]
		list ([type]): [description]

	Returns:
		[type]: [description]
	"""

	for link in bs4ob.find_all('a', class_='result-title hdrlnk'):
		links.append(link.get('href'))
	return links[:totalcount]

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
	('srchType','T')
)


srch_term = "kettlebell"
url = f"https://chicago.craigslist.org/search/sss?query={srch_term}"

response = requests.get(url, headers=headers, params=params)

#Just in case we piss someone off
if response.status_code != 200:
	print(f'Status code: {response.status_code}')
	print(f'Reason: {response.reason}')

#Request order
	# 1. Request first page to get total count of listings. 
	# 2. Iterate through all summary pages and scrape their links
	# 3. Iterate through each link and scrape the individual posting 


#Get the HTML
bs4ob = BeautifulSoup(response.text, 'lxml')

# Need to iterate the total number of pages.  
totalcount = int(bs4ob.find('span', class_='totalcount').text)
totalpages = int(round(totalcount//120)) + 1

links, ids, price, hood, title, = [], [], [], [], []
links = get_listings(bs4ob, totalcount)
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
	"id": "int64",
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

#Load previous listings. 
all_results = pd.read_csv('./data/craigs_kb.csv', delimiter=',', header=0, index_col=0)

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

	#lat / long
	lat = bs4_home_ob.find('div', class_='viewposting')
	if lat:
		results.loc[x, 'lat'] = lat.get('data-latitude')
	else:
		results.loc[x, 'lat'] = np.nan

	lon = bs4_home_ob.find('div', class_='viewposting')
	if lon:
		results.loc[x, 'lon'] = lon.get('data-longitude')
	else:
		results.loc[x, 'lon'] = np.nan

	#Get the amenities
	groups = bs4_home_ob.find_all('p', class_='attrgroup')
	if groups:
		#Group1 - Random amenities
		amenities = groups[0].find_all('span')
		if amenities:
			amen = [amenity.text for amenity in amenities]
			results.at[x, 'amenities'] = amen
	
	#Posting body
	post_body = bs4_home_ob.find('section', {'id':'postingbody'})
	if post_body:
		results.at[x, 'post_body'] = post_body.text[30:].strip()
	else:
		results.at[x, 'post_body'] = np.nan
	
	#Get the date posted
	posting_info = bs4_home_ob.find('div', class_='postinginfos')
	if posting_info:
		results.loc[x, 'postdate'] = posting_info.find('p', class_='postinginfo reveal').text[8:]

	print(f'New KB found at {results.loc[x, "link"]}')

	#Insert new record into all_results
	all_results = all_results.append(results.loc[x, :])
	
	#Send the email
	support.send_search_email(results.loc[x, 'link'])

	#take a nap
	time.sleep(np.random.randint(5, 13))


#Reset the index
all_results = all_results.reset_index(drop=True)

#Save the new record
all_results.to_csv("./data/craigs_kb.csv")


print('Update complete!')
time.sleep(5)
