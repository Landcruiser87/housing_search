def scrape():
	print("zillow!")

# #%%

# import requests
# import numpy as np
# import pandas as pd
# import json
# from datetime import date, datetime
# import time
# import sys
# import os

# #%%



# state = 'IL'
# zip = '60640'

# #Before we start requesting , lets setup what neighborhoods we want to look in. 
# url = 'https://www.zillow.com/homes/for_rent/Ravenswood,-Chicago,-IL_rb'

# header = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36',
#   'referer': 'https://www.zillow.com/homes/for_rent/Ravenswood,-Chicago,-IL_rb/?searchQueryState=%7B%22pagination'
  
# }

# response_html = requests.get(url, headers=header)

# from lxml import html

# resp_html = html.fromstring(response_html.text)
# html.open_in_browser(doc=resp_html, encoding='UTF-8')



# #Notes on request.
# # html format
# # encoding - UTF-8


# #%%


























# # #Results list
# # results = []

# # base_url = f'https://www.zillow.com/homes/Ravenswood,-Chicago,-IL_rb/'
# # response = requests.get(base_url, headers = header )
# # print(response.status_code)

# # for city in cities:
# # 	time.sleep(3)
# # 	base_url = f'https://www.zillow.com/homes/{city},-Chicago,-IL_rb/'
# # 	response = requests.get(base_url, headers = header )

# # 	resp_json = response.json()
# # 	results.append(resp_json)
# # 	# print(resp_json)
# # 	# print(resp_json['searchResults']['listResults'][0]['hdpUrl'])

# #%%
