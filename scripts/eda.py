import requests
from bs4 import BeautifulSoup
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

all_results = pd.read_csv('../data/craigs_all.csv', delimiter=',', index_col=0, header=0)

#Looking at prices
_ = plt.hist(all_results['price'], bins= 8, color='blue', edgecolor='black')
_ = plt.xlabel('Price')
_ = plt.ylabel('Count')
_ = plt.title('Price Distribution')
_ = plt.show()

#Looking at what neighborhoods have most available
top10 = all_results['hood'].value_counts()[:10]
_ = plt.barh(top10.index, top10.values, color='blue')
_ = plt.xlabel('Count')
_ = plt.ylabel('Neighborhood')
_ = plt.title('Top 10 Neighborhood Counts')
_ = plt.gca().invert_yaxis()
_ = plt.show()


	