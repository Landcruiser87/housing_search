import smtplib
carriers = {
	'att':    '@mms.att.net',
	'tmobile':' @tmomail.net',
	'verizon':  '@vtext.com',
	'sprint':   '@page.nextel.com'
}

def send(message):
        # Replace the number with your own, or consider using an argument\dict for multiple people.
	to_number = '260-312-7402' + carriers['verizon']
	with open('../secret/sms_login.txt') as login_file:
		login = login_file.read().splitlines()
		username = login[0].split(':')[1]
		password = login[1].split(':')[1]

	auth = (username, password)

	# Establish a secure session with gmail's outgoing SMTP server using your gmail account
	server = smtplib.SMTP("smtp.gmail.com", 587 )
	server.starttls()
	server.login(auth[0], auth[1])

	# Send text message through SMS gateway of destination number
	server.sendmail(auth[0], to_number, message)
	server.quit()
	print(f'message sent to {to_number}')
send('I HAS THE POWER')