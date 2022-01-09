
def haversine_distance(lat1:float, lon1:float, lat2:float, lon2:float)->float:
	from math import radians, cos, sin, asin, sqrt
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
	# convert decimal degrees to radians 
	lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])

	# haversine formula 
	dlon = lon2 - lon1 
	dlat = lat2 - lat1 
	a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
	c = 2 * asin(sqrt(a)) 
	r = 3956 # Radius of earth in miles. Use 6371 for kilometers
	return c * r

def send_email(url:str):
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

	@docstring_parameter(url)
	def inputdatlink():
		"""
		<html>
			<body>
				<p>Oh haroo,<br>
				You have a new house to look at! <br>
				<a href={0}>Click on that craig link</a> 
				</p>
			</body>
		</html>
		"""
		pass

	with open('./secret/login.txt') as login_file:
		login = login_file.read().splitlines()
		sender_email = login[0].split(':')[1]
		password = login[1].split(':')[1]
		receiver_email = login[2].split(':')[1]
		
	# Establish a secure session with gmail's outgoing SMTP server using your gmail account
	smtp_server = "smtp.gmail.com"
	port = 465

	message = MIMEMultipart("alternative")
	message["Subject"] = "New House Found!"
	message["From"] = sender_email
	message["To"] = receiver_email

	html = inputdatlink.__doc__

	attachment = MIMEText(html, "html")
	message.attach(attachment)
	context = ssl.create_default_context()

	with smtplib.SMTP_SSL(smtp_server, port, context=context) as server:
		server.login(sender_email, password)		
		server.sendmail(sender_email, receiver_email, message.as_string())
		print("Email sent!")
