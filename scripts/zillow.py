#%%

import requests
import numpy as np
import json
from datetime import date, datetime
import time
import sys
import re
import os

header = {"User-Agent":"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36" }

response = requests.get(u, headers = header )
#NB. Original query string below. It seems impossible to parse and
#reproduce query strings 100% accurately so the one below is given
#in case the reproduced version is not "correct".
# response = requests.get('https://www.zillow.com/chicago-il-60640/rentals/?searchQueryState=%7B%22pagination%22%3A%7B%7D%2C%22usersSearchTerm%22%3A%2260640%22%2C%22mapBounds%22%3A%7B%22west%22%3A-87.68338918273926%2C%22east%22%3A-87.63034581726075%2C%22south%22%3A41.95261795178509%2C%22north%22%3A41.99307465809032%7D%2C%22regionSelection%22%3A%5B%7B%22regionId%22%3A84640%2C%22regionType%22%3A7%7D%5D%2C%22isMapVisible%22%3Afalse%2C%22filterState%22%3A%7B%22fsba%22%3A%7B%22value%22%3Afalse%7D%2C%22fsbo%22%3A%7B%22value%22%3Afalse%7D%2C%22nc%22%3A%7B%22value%22%3Afalse%7D%2C%22fore%22%3A%7B%22value%22%3Afalse%7D%2C%22cmsn%22%3A%7B%22value%22%3Afalse%7D%2C%22auc%22%3A%7B%22value%22%3Afalse%7D%2C%22fr%22%3A%7B%22value%22%3Atrue%7D%2C%22ah%22%3A%7B%22value%22%3Atrue%7D%7D%2C%22isListVisible%22%3Atrue%2C%22mapZoom%22%3A14%7D', headers=headers)


#%%
