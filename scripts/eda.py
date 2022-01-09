import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

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

all_results = pd.read_csv('../data/craigs_all.csv', delimiter=',', index_col=0, header=0)

#Looking at prices
_ = plt.hist(all_results['price'], bins= 10, color='blue', edgecolor='black')
_ = plt.xlabel('Price')
_ = plt.ylabel('Count')
_ = plt.title('Price Distribution')
_ = plt.show()

#Looking at what neighborhoods have most available
top5 = all_results['hood'].value_counts()[:5]
_ = plt.barh(top5.index, top5.values, color='blue')
_ = plt.xlabel('Neighborhood')
_ = plt.ylabel('Count')
_ = plt.title('Top 5 Neighborhood Distribution')
_ = plt.show()


	