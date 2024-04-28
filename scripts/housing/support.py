import datetime
import numpy as np
import pandas as pd
from sodapy import Socrata
import time
import json
from os.path import exists

#Progress bar fun
from rich.progress import (
	Progress,
	BarColumn,
	SpinnerColumn,
	TextColumn,
	TimeRemainingColumn,
)
from rich.console import Console
from geopy import Nominatim, ArcGIS

console = Console(color_system="truecolor")

class NumpyArrayEncoder(json.JSONEncoder):
	"""Custom numpy JSON Encoder.  Takes in any type from an array and formats it to something that can be JSON serialized.
	Source Code found here
		https://pynative.com/python-serialize-numpy-ndarray-into-json/
	Args:
		json (object): Json serialized format
	"""	
	def default(self, obj):
		if isinstance(obj, np.integer):
			return int(obj)
		elif isinstance(obj, np.floating):
			return float(obj)
		elif isinstance(obj, np.ndarray):
			return obj.tolist()
		else:
			return super(NumpyArrayEncoder, self).default(obj)
		
def save_data(jsond:dict):
	out_json = json.dumps(jsond, indent=2, cls=NumpyArrayEncoder)
	with open("./data/housing.json", "w") as out_f:
		out_f.write(out_json)

def load_historical(fp:str)->json:
	if exists(fp):
		with open(fp, "r") as f:
			jsondata = json.loads(f.read())
			return jsondata	

def closest_L_stop(data:list)->list:
	#Load up Lstop data
	stops = pd.read_csv(
		"./data/CTA_Lstops.csv",
		header=0,
		index_col="STOP_ID"
	)
	for listing in data:
		if listing.lat and listing.long:
			lat1 = listing.lat
			lon1 = listing.long

			min_dist = 20000
			for stop in stops.index:
				lat2, lon2 = stops.loc[stop, "Location"].strip("()").split(",")
				lat2, lon2 = float(lat2), float(lon2)
				dist = haversine_distance(lat1, lon1, lat2, lon2)
				if dist <= min_dist:
					min_dist = dist
			listing.L_dist = min_dist

	return data

def get_lat_long(data:list, citystate:tuple)->list:
	noma_params = {
		"user_agent":"myApp",
		"timeout":10,
	}
	geolocator = Nominatim(**noma_params)
	# arc_params = {
	# 	"exactly_one":True,
	# 	"timeout":10,
	# }
	# backupgeo = ArcGIS(**arc_params)

	#TODO.  Add backup geocoder?  Not getting alot of the addresses.  
 	#Don't want to use google because the maps API costs money. 
	#OpenMapquest, ARCGis, Yandex could be free alternatives.
		#ArcGIS has up to 20k free geocode requests a month.  That should be plenty
  
	for listing in data:
		sleepspinner(np.random.randint(2, 4), "searching lat/long")
		address = listing.address
		#If city and state aren't present, add them
			#?Could do this for zip code searches as well.
   
		if citystate[0].lower() not in address.lower():
			listing.address = address + " " + citystate[0]
		if citystate[1].lower() not in address.lower():
			listing.address = address + " " + citystate[1]

		srch_add = listing.address + " USA"
		#First search Novatim
		location = geolocator.geocode(srch_add)
		if location:
			lat, long = location.latitude, location.longitude
			listing.lat = lat
			listing.long = long
			continue
		#If that fails, search OpenMapquest
		# locatedos = backupgeo(srch_add)
		# if locatedos:
		# 	lat, long = location.latitude, location.longitude
		# 	listing.lat = lat
		# 	listing.long = long
		
		
	return data

def sleepspinner(naps:int, msg:str):
	my_progress_bar = Progress(
		TextColumn("{task.description}"),
		SpinnerColumn("moon"),
		BarColumn(),
		TextColumn("*"),
		"time remain:",
		TextColumn("*"),
		TimeRemainingColumn(),
		TextColumn("*"),
		TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
		transient=True,
		console=console
	)
	
	with my_progress_bar as progress:
		task = progress.add_task(msg, total=naps)
		for nap in range(naps):
			time.sleep(1)
			progress.advance(task)

def in_bounding_box(bounding_box:list, lat:float, lon:float)->bool:
	"""[Given two corners of a box on a map.  Determine if a point is
	 within said box.  Step 1.  You cut a hole in that box.]

	Args:
		bounding_box (list): [list of GPS coordinates of the box]
		lat (float): [lattitude of point]
		lon (float): [longitude of point]

	Returns:
		(bool): [Whether or not is within the given GPS ranges 
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

def haversine_distance(lat1:float, lon1:float, lat2:float, lon2:float)->float:
	"""[Uses the haversine formula to calculate the distance between 
	two points on a sphere]

	Args:
		lat1 (float): [latitude of first point]
		lon1 (float): [longitude of first point]
		lat2 (float): [latitude of second point]
		lon2 (float): [latitue of second point]

	Returns:
		dist (float): [Distance between two GPS points in miles]

	Source:https://stackoverflow.com/questions/42686300/how-to-check-if-coordinate-inside-certain-area-python
	"""	
	from math import radians, cos, sin, asin, sqrt
	# convert decimal degrees to radians 
	lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

	# haversine formula 
	dlon = lon2 - lon1 
	dlat = lat2 - lat1 
	a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
	c = 2 * asin(sqrt(a)) 
	r = 3956 # Radius of earth in miles. Use 6371 for kilometers
	return c * r


def urlformat(urls:list)->str:
	"""This formats each of the list items into an html list for easy ingestion into the email server

	Args:
		urls (list): List of new listings found

	Returns:
		str: HTML formatted string for emailing
	"""	
	
	links_html = "<ol>"
	if len(urls) > 1:
		for link, site in urls:
			links_html += f"<li><a href='{link}'> {site} link </a></li>"
	else:
		links_html = f"<li><a href='{urls[0]}'> link 1 </a></li>"
	links_html = links_html + "</ol>"
	return links_html

def send_housing_email(urls:str):
	"""[Function for sending an email.  Inputs the url into the docstrings 
	via decorator for easy formatting of the HTML body of an email.]

	Args:
		url (str): [url of the listing]

	Returns:
		[None]: [Just sends the email.  Doesn't return anything]
	"""	
	import smtplib, ssl
	from email.mime.text import MIMEText
	from email.mime.multipart import MIMEMultipart
	
	def inputdatlink(urls:str):
		html = """
		<html>
			<body>
				<p>Helloooooooooo!<br>
				You have new houses to look at!<br>
				""" + urls + """
				</p>
			</body>
		</html>
		"""
		return html

	with open('./secret/login.txt') as login_file:
		login = login_file.read().splitlines()
		sender_email = login[0].split(':')[1]
		password = login[1].split(':')[1]
		receiver_email = login[2].split(':')[1]
		
	# Establish a secure session with gmail's outgoing SMTP server using your gmail account
	smtp_server = "smtp.gmail.com"
	port = 465

	html = inputdatlink(urls)

	message = MIMEMultipart("alternative")
	message["Subject"] = "New Housing Found!"
	message["From"] = sender_email
	message["To"] = receiver_email

	attachment = MIMEText(html, "html")
	message.attach(attachment)
	context = ssl.create_default_context()

	with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
		server.login(sender_email, password)		
		server.sendmail(sender_email, receiver_email, message.as_string())

def date_convert(time_big:datetime)->datetime:
	dateOb = datetime.datetime.strptime(time_big,'%Y-%m-%dT%H:%M:%S.%f')
	return dateOb

def crime_score(data:list) -> list:
	"""[Connects to data.cityofchicago.org and pulls down all the 
	crime data for the last year, in a 1 mile radius.  It then recategorizes
	the crimes into scores based on the percentage of total crime in that area.]

	Args:
		lat1 (float): [Lattitude of the listing we want to check]
		lon1 (float): [Longitude of the listing we want to check]

	Raises:
		ValueError: [Check to make sure we got a years worth of data]

	Returns:
		list: [Listings with updated scores]
	"""	
	with open('./secret/chicagodata.txt') as login_file:
		login = login_file.read().splitlines()
		app_token = login[0].split(':')[1]
		
	client = Socrata("data.cityofchicago.org", app_token)

	#Search radius is 0.91 miles
	#Sets lookback to 1 year from today
	ze_date = str(datetime.datetime.today().date() - datetime.timedelta(days=365))
	c_dtypes = [
		("id"                   ,str, 60),
		("date"                 ,datetime.datetime),
		("iucr"                 ,str, 60),
		("fbi_code"             ,str, 60),
		("latitude"             ,float),
		("longitude"            ,float),
		("primary_type"         ,str, 240),
		("description"          ,str, 600),
		("arrest"               ,str, 20),
		("domestic"             ,str, 20),
	]

	for listing in data:
		lat1 = listing.lat
		lon1 = listing.long

		if lat1 and lon1:
			# If the listing has a lat / long, search the area within a 1 mile radius, over the past 365 days.  Pull back the select fields for analysis
			results = client.get("ijzp-q8t2",
				select="id, date, iucr, fbi_code, latitude, longitude, primary_type, description, arrest, domestic",
				where=f"latitude > {lat1-0.1} AND latitude < {lat1+0.1} AND longitude > {lon1-0.1} AND longitude < {lon1+0.1} AND date > '{ze_date}'",
				limit=800000
			)
			sleepspinner(np.random.randint(2, 6), "Be NICE to your sister")

			#NOTES
				#IDEA -Redo Scoring
				#I'd like to redo the crime scoring section becuase I think there's alot more valuable data there than previously
				#found.  I need a way to classify risk in a region.  Which is no easy task.  
					#Ideas for crime severity
	 				#1. Using arrest/domestic as simple scaling of importance
	  				#2. Make another requeset and use the IUCR codes
	   					#I'm betting this will be the better route though as
		 				#there will be a felony misdemeanor charge dilineation in there. 
					#So primary type and description are the results of the IUCR codes. Makes sense.
	 				#Don't really need to pull them but I could use the logic of how their structured. 
	  				#Looks like there's 5 different pages dilineated by crimes in the 1000's
	   				#page 1 is most frequent, 
					#page 2 is burglary and prostitution?  Wierd
	 				#page 3 is Narcotics.  Lots of different charges here. 
	  				#page 4 is other offenses.
	   
	   			#IDEA What about a week by week analysis up to a year back for each primary_type
	   
	   				#That could give a sense of seasonality and trend for important categories
					#Multi line chart with regressions? in that radius over the past year. 
	 					#This will be cool ^^^^^
					#Store those as an array for easy graphing and would be minimal data overhead if grouped by week instead,
	 					#NOTE -json storage.
							#If you want to save an array inside json.  we'll store it on the 3rd level of the dic so its 
	   						#format will look like {"array":[1,2,3,4,5,6]}
		  					#https://pynative.com/python-serialize-numpy-ndarray-into-json/
		  					#That way it won't indent the json at that level and make the json row count go bonkers
		 					#Maybe store the top 10 to 15?.  That should keep the dataset size fairly small
	   					#Score the scoring dict too, buy we'll still need to update that. 

			if results:
				#Set up array
				crime_arr = np.zeros(shape=(len(results)), dtype=c_dtypes)
				#Fill it in row by row
				for idx, res in enumerate(results):
					crime_arr[idx] = tuple(res.values())
				
				#Convert to datetimes
				func = np.vectorize(lambda x: date_convert(x))
				crime_arr["date"] = np.apply_along_axis(func, 0, crime_arr["date"])
				
				#Check the last dates record.  If its not within the last year, 
				#make another request until we hit that date. 
					# Don't forget to filter any data that may come in extra. 
				date_check = crime_arr["date"].min()
				if date_check > datetime.datetime.today() - datetime.timedelta(days=365):
					#Need to figure out how to remake the request if i hit the 800k limit. 
					raise ValueError('Yo Query needeth be BIGGER')

				#Checking memory consumption
				#sum(crime_df.memory_usage(deep=True) / 1_000_000)
				#Req 500k records costs you about 21.7 MB

				total_crimes = crime_arr.shape[0]

				scores = {
					'drug_score':0,
					'gun_score':0,
					'murder_score':0,
					'perv_score':0,
					'theft_score':0,
					'violence_score':0,
					'property_d_score':0
				}

				narcotics = ['NARCOTICS', 'OTHER NARCOTIC VIOLATION']
				guns = ['WEAPONS VIOLATION', 'CONCEALED CARRY LICENCE VIOLATION']
				theft = ['BURGLARY', 'ROBBERY', 'MOTOR VEHICLE THEFT', 'THEFT', 'DECEPTIVE PRACTICE']
				sex_crimes = ['CRIMINAL SEXUAL ASSAULT', 'SEX OFFENSE',  'PROSTITUTION', 'STALKING']
				human_violence = ['BATTERY', 'ASSAULT', 'OFFENSE INVOLVING CHILDREN', 'INTIMIDATION', 'KIDNAPPING']
				
				#TODO - Update all below comparison to set memberships.
				for idx in range(total_crimes):
					#Drugs
					if crime_arr[idx]['primary_type'] in narcotics:
						scores['drug_score'] += 1

					#Guns
					if crime_arr[idx]['primary_type'] in guns:
						scores['gun_score'] += 1
			
					#Gun description subsearch if primary_type doesn't catch it.
					elif set(crime_arr[idx]['description'].split()) & set(['HANDGUN', 'ARMOR', 'GUN', 'FIREARM', 'AMMO', 'AMMUNITION', 'RIFLE']):
						scores['gun_score'] += 1
					
					#Murder
					if crime_arr[idx]['primary_type'] == 'HOMICIDE':
						scores['murder_score'] += 10
					
					#Theft
					if crime_arr[idx]['primary_type'] in theft:
						scores['theft_score'] += 1

					#Sexual Crimes
					if crime_arr[idx]['primary_type'] in sex_crimes:
						scores['perv_score'] += 2

					#Sex Crimes subsearch
					elif set(crime_arr[idx]['description'].split()) & set(['PEEPING TOM']):
						scores['perv_score'] += 2

					#humanViolence
					if crime_arr[idx]['primary_type'] in human_violence:
						scores['violence_score'] += 1

					#humanviolence subsearch
					elif set(crime_arr[idx]['description'].split()) & set(['CHILDREN']):
						scores['violence_score'] += 5

					#property damage
					if crime_arr[idx]['primary_type'] == 'CRIMINAL DAMAGE':
						scores['property_d_score'] += 1
					
				scores = {k:round((v/total_crimes )*100, 2) for k, v in scores.items()}
				listing.crime_sc = scores
				del results
	return data
