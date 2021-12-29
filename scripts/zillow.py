#%%

import requests
import numpy as np
import json
from datetime import date, datetime
import time
import sys
import re
import os



#Before we start requesting , lets setup what neighborhoods we want to look in. 
cities = [
	'Ravenswood',
	'Lincoln Square',
	'Ravenswood Gardens',
	'Budlong Woods',
	'Bowmanville',
	'Winnemac'
]

#Set the header for pulling
header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36" }

#Results list
results = []

for city in cities:
	time.sleep(3)
	base_url = f'https://www.zillow.com/homes/{city},-Chicago,-IL_rb/'
	response = requests.get(base_url, headers = header )

	resp_json = response.json()
	results.append(resp_json)
	# print(resp_json)
	# print(resp_json['searchResults']['listResults'][0]['hdpUrl'])

#%%
