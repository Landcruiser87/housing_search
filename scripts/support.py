import smtplib, ssl

def send(message):
        # Replace the number with your own, or consider using an argument\dict for multiple people.
	
	with open('../secret/sms_login.txt') as login_file:
		login = login_file.read().splitlines()
		username = login[0].split(':')[1]
		password = login[1].split(':')[1]
		to_email = login[2].split(':')[1] + carriers['verizon']
		
	auth = (username, password)

	# Establish a secure session with gmail's outgoing SMTP server using your gmail account
	server = smtplib.SMTP("smtp.gmail.com", 587 )
	server.starttls()
	server.login(auth[0], auth[1])
	message = f'From: {auth[0]} To: {to_email} Subject: {message}'

	# Send text message through SMS gateway of destination number
	server.sendmail(auth[0], to_email, message)
	server.quit()
	print(f'message sent to {to_email}')

send('I HAS THE POWER')