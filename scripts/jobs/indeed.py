import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import datetime
import time
import logging
from rich.logging import RichHandler

FORMAT = "%(message)s" 
# FORMAT = "[%(asctime)s]|[%(levelname)s]|[%(message)s]" #[%(name)s]
 
logging.basicConfig(#filename=f"./data/logs/peaks_{current_date}.log", 
					#filemode='w',
					level="INFO", 
					format=FORMAT, 
					datefmt="[%X]",
					handlers=[RichHandler()] 
)

logger = logging.getLogger(__name__) 

def log_time(fn):
	def inner(*args, **kwargs):
		tnow = time.time()
		out = fn(*args, **kwargs)
		te = time.time()
		took = round(te - tnow, 2)
		if took <= 60:
			logging.warning(f"{fn.__name__} ran in {took:.2f}s")
		elif took <= 3600:
			logging.warning(f"{fn.__name__} ran in {(took)/60:.2f}m")		
		else:
			logging.warning(f"{fn.__name__} ran in {(took)/3600:.2f}h")
		return out
	return inner



#NOTE Post info extraction
def get_posting_info(post:BeautifulSoup)->list:
	"""This function extracts the individual listing info from each slider-item

	Args:
		post (BeautifulSoup): The bs4 object of the slider-item

	Returns:
		list: [job_title, job_id, company, location, post_date, job_description, job_url, salary]
	"""
	
	job_title = post.find('h2', 'jobTitle', 'title').text.strip()
	job_id = post.find('a', 'jcs-JobTitle').get('id').split('_')[1]
	company = post.find('span', 'companyName').text.strip()
	location = post.find('div', 'companyLocation').text.strip()
	job_description = post.find('div', 'job-snippet').text.strip()
	post_date = post.find('span', 'date').text.strip()[6:]
	job_url = "https://www.indeed.com" + post.find('a', 'jcs-JobTitle').get('href')


	try:
		salary = post.find('span', 'estimated-salary').text.strip()
	except:
		salary = ""
	#[x] you returned that data.  Nice work
	return [job_title, job_id, company, location, post_date, job_description, job_url, salary]

#NOTE Main function run
@log_time
def main():
	logger.warning(f"I'M A LOG.  A REAL LOG")
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
	#You can submit more filtering options to the query here
	#In the form of extra parameters.  Play around with https://curlconverter.com/HEY LETS MEET FOR LUCNH AND THINGS STUFF UNICORNS CANDY. IDON'T KNOW
	#to see what you're filtering when you copy the curl bash command of the data you want

		
	# params = (
	# 	('hasPic', '1'),
	# 	('srchType','T')
	# )

	#Your search terms go here. 
	srch_term = "Data Scientist"
	location = "Chicago, IL"

	#change this to whatever you want.  Or change the `while page_limit > 0` to a `while True`
	page_limit = 5

	#Data Container
	results = []

	#Fire the first request
	url =f"https://www.indeed.com/jobs?q={srch_term}&l={location}&"
	response = requests.get(url, headers=headers) #, params=params)

	while page_limit > 0:

		#Get the HTML
		bs4ob = BeautifulSoup(response.text, 'lxml')

		#Just in case we piss someone off
		if response.status_code != 200:
			print(f'Status code: {response.status_code}')
			print(f'Reason: {response.reason}')
			break

		#Get the posts for that page. 
		posts = bs4ob.find_all('div', 'slider_item')

		#iterate through the posts and extract job information
		for post in posts:
			job_info = get_posting_info(post)
			results.append(job_info)

		#Finds the next page, takes a little nap, then restarts the loop
		#with the next URL link if it can find it.  If not, it exits the loop
		try:
			next_page = bs4ob.find('a', {"aria-label": "Next"}).get("href")
			url = "https://www.indeed.com" + next_page
			time.sleep(2)
			response = requests.get(url, headers=headers)
			page_limit -= 1

		except AttributeError:
			print("No more pages")
			break

	#make a panda!
	#FIXME WHY DID YOU USE PANDAAAAAS NOOOOOOOOO

	df_results = pd.DataFrame(results, columns=['job_title', 'job_id', 'company', 'location', 'post_date', 'job_description', 'job_url', 'salary'])

	#add a column with the count of each job_id for looking at duplicates
	df_results['job_id_count'] = df_results.apply(lambda x: df_results.job_id.value_counts()[x.job_id], axis=1)

	logger.info(f'Your results are ready!  Shape of dataframe = {df_results.shape}')
	
	return df_results
df_results = main()
