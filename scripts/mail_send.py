import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(url:str):
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
