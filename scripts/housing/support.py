import datetime
import numpy as np
import pandas as pd
from sodapy import Socrata

def date_convert(time_big:pd.Series)->datetime:
	dateOb = datetime.datetime.strptime(time_big,'%Y-%m-%dT%H:%M:%S.%f')
	return dateOb

def crime_score(lat1:float, lon1:float) -> pd.Series:
	"""[Connects to data.cityofchicago.org and pulls down all the 
	crime data for the last year, in a 1 mile radius.  It then recategorizes
	the crimes into scores based on the percentage of total crime in that area.]

	Args:
		lat1 (float): [Lattitude of the listing we want to check]
		lon1 (float): [Longitude of the listing we want to check]

	Raises:
		ValueError: [Check to make sure we got a years worth of data]

	Returns:
		pd.Series: [Scores for each listing]
	"""	
	with open('../../secret/chicagodata.txt') as login_file:
		login = login_file.read().splitlines()
		app_token = login[0].split(':')[1]
		
	client = Socrata("data.cityofchicago.org", app_token)

	#Search radius is 0.91 miles
	#Sets lookback to 1 year from today

	ze_date = str(datetime.datetime.today().date() - datetime.timedelta(days=365))

	results = client.get("ijzp-q8t2",
						select="id, date, description, latitude, longitude, primary_type ",
						where=f"latitude > {lat1-0.1} AND latitude < {lat1+0.1} AND longitude > {lon1-0.1} AND longitude < {lon1+0.1} AND date > '{ze_date}'",
						limit=800000)

	#redo this in numpy
	crime_df = pd.DataFrame.from_dict(results)
	crime_df['date_conv'] = crime_df.apply(lambda x: date_convert(x.date), axis=1)
	crime_df['date_short'] = crime_df.apply(lambda x: x.date_conv.date(), axis=1)
	crime_df['crime_time'] = crime_df.apply(lambda x: x.date_conv.time(), axis=1)
	crime_df.drop(['date_conv', 'date'], axis=1, inplace=True)
	
	#?Keep
	#Just realized i don't need this.  Keeping in case i want to do a metric of danger by distance metric
	#crime_df['distance'] = crime_df.apply(lambda x: haversine_distance(lat1, lon1, float(x.latitude), float(x.longitude)), axis=1)
	
	#Check the last dates record.  If its not within the last year, 
	#make another request until we hit that date. 
		# Don't forget to filter any data that may come in extra. 

	date_check = crime_df.date_short.min()
	if date_check > datetime.date.today() - datetime.timedelta(days=365):
		#TODO Need to figure out how to remake the request if i hit the 800k limit. 
		raise ValueError('Yo Query needeth be BIGGER')

	#Checking memory consumption
	#sum(crime_df.memory_usage(deep=True) / 1_000_000)
	#Req 500k records costs you about 21.7 MB

	total_crimes = crime_df.shape[0]

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

	for idx in crime_df.index:
		#Drugs
		if crime_df.loc[idx, 'primary_type'] in narcotics:
			scores['drug_score'] += 1

		#Guns
		if crime_df.loc[idx, 'primary_type'] in guns:
			scores['gun_score'] += 1
 
		#Gun description subsearch if primary_type doesn't catch it.
		elif set(crime_df.loc[idx, 'description'].split()) & set(['HANDGUN', 'ARMOR', 'GUN', 'FIREARM', 'AMMO', 'AMMUNITION', 'RIFLE']):
			scores['gun_score'] += 1
		
		#Murder
		if crime_df.loc[idx, 'primary_type'] in ['HOMICIDE']:
			scores['murder_score'] += 1
		
		#Theft
		if crime_df.loc[idx, 'primary_type'] in theft:
			scores['theft_score'] += 1

		#Sexual Crimes
		if crime_df.loc[idx, 'primary_type'] in sex_crimes:
			scores['perv_score'] += 1

		#Sex Crimes subsearch
		elif set(crime_df.loc[idx, 'description'].split()) & set(['PEEPING TOM']):
			scores['perv_score'] += 1

		#humanViolence
		if crime_df.loc[idx, 'primary_type'] in human_violence:
			scores['violence_score'] += 1

		#humanviolence subsearch
		elif set(crime_df.loc[idx, 'description'].split()) & set(['CHILDREN']):
			scores['violence_score'] += 1

		#property damage
		if crime_df.loc[idx, 'primary_type'] in ['CRIMINAL DAMAGE']:
			scores['property_d_score'] += 1
		
		
	scores = {k:round((v/total_crimes )*100, 2) for k, v in scores.items()}
	return pd.DataFrame.from_dict(scores, orient='index').T

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

def send_housing_email(urls:list):
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

	def docstring_parameter(*sub):
		def dec(obj):
			obj.__doc__ = obj.__doc__.format(*sub)
			return obj
		return dec

	@docstring_parameter(urls)
	def inputdatlink():
		"""
		<html>
			<body>
				<p>Helloooooooooo!
					<br>
					You have a new house to look at!<br>
					%for url in urls:
						<a href={0}</a>
					%endfor
				</p>
			</body>
		</html>
		"""
		pass
	#<a href={0}>Click on that link</a> 
 
	with open('./secret/login.txt') as login_file:
		login = login_file.read().splitlines()
		sender_email = login[0].split(':')[1]
		password = login[1].split(':')[1]
		receiver_email = login[2].split(':')[1]
		
	# Establish a secure session with gmail's outgoing SMTP server using your gmail account
	smtp_server = "smtp.gmail.com"
	port = 465

	message = MIMEMultipart("alternative")
	message["Subject"] = "New Housing Found!"
	message["From"] = sender_email
	message["To"] = receiver_email

	html = inputdatlink.__doc__

	attachment = MIMEText(html, "html")
	message.attach(attachment)
	context = ssl.create_default_context()

	with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
		server.login(sender_email, password)		
		server.sendmail(sender_email, receiver_email, message.as_string())
