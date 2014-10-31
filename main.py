# main module
import json
import requests
import sys
import datetime
import smtplib
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# fuzzy matching
from fuzzywuzzy import fuzz
from fuzzywuzzy import process


class Page:	
	'''
	This class represents, in a Python object, the configurations set in config.json.
	The dot notation goes one level deep, more nested values are called like normal dicts.
	'''	

	# new
	def __init__(self, configDict):
		for k, v in configDict.items():
			setattr(self, k, v)		


	# function to set default / ideal rendering
	def calibrate(self):

		print "Setting calibration tare for {name}...".format(name=self.name)

		# Download rendered HTML, save to tare
		fhand = open("output/"+self.name+"_tare.html",'w')
		page_html = requests.get("http://{splash_server}/render.html?url={page_url}&wait={wait_time}".format(splash_server=config_dict['splash_server'],page_url=self.page_url,wait_time=config_dict['wait_time'])).content
		fhand.write(page_html)
		fhand.close()
		print "HTML tare written."

		# log
		log_dict = {
			"msg":"Calibration tare created",
			"name":self.name,
			"page_url":self.page_url

		}			
		logResults(log_dict)


	# function to render and check
	def checkHTML(self):		
		
		# Download rendered HTML, check against tare version
		page_html = requests.get("http://{splash_server}/render.html?url={page_url}&wait={wait_time}".format(splash_server=config_dict['splash_server'],page_url=self.page_url,wait_time=config_dict['wait_time'])).content

		# retrieve tare HTML
		fhand = open("output/"+self.name+"_tare.html",'r')
		tare_html = fhand.read()
		fhand.close()

		# test
		fuzz_ratio = fuzz.ratio(page_html,tare_html)
		result = fuzz_ratio > self.similarity_threshold
		print "Fuzz ratio for {name}: {ratio}.  Result is {result}".format(name=self.name,ratio=str(fuzz_ratio),result=result)		

		# build and return checkHTML_result
		checkHTML_result = {
			"msg":"checkHTML result is: {result}".format(result=result),
			"result":result,
			"fuzz_ratio":fuzz_ratio,
			"similarity_threshold":self.similarity_threshold,
			"name":self.name,
			"page_url":self.page_url			
		}

		return checkHTML_result


# main function to run checks
def runChecks(page):
	# instantiate handle for Page instance
	phandle = Page(page)		

	# run each check in checks list
	for check in phandle.checks:
		print "Running {check_name} for {name}".format(check_name=check['name'],name=phandle.name)
		
		def checkLoop(attempt,phandle,check):

			# run function based on check name / expecting "check_result" dictionary, with 'result' key		
			check_result = getattr(phandle,check['name'])()
			check_result['attempt'] = attempt		
		
			# did not pass test
			if check_result['result'] == False:					
				
				# log results always
				logResults(check_result)
				
				# enter retry loop
				if attempt < check['retry_wait_seconds']:
					print "Retrying {check_name} for {name}: attempt {attempt}".format(check_name=check['name'],name=phandle.name,attempt=attempt)
					time.sleep(check['retry_wait_seconds'])		
					attempt += 1
					checkLoop(attempt,phandle,check)				

				else:
					# notify admins with check msg and page details				
					print "Max retries reached ({attempt}) for {check_name} on {name}.  Alerting.".format(check_name=check['name'],name=phandle.name,attempt=attempt)
					notifyAdmin( dict(page.items() + check_result.items())  )
			
			# passed test, log and move on
			else:
				logResults(check_result)

		# run checkLoop, 1st attempt
		checkLoop(1,phandle,check)


# main function to calibrate pages
def calibratePages(page):	
	Page_Handle = Page(page)
	Page_Handle.calibrate()


def notifyAdmin(notify_dict):

	for recipient in notify_dict['email_recipients']:

		# get admin emails from config		
		you = recipient
		me = notify_dict['email_sender'] 	

		# Create message container - the correct MIME type is multipart/alternative.
		msg = MIMEMultipart('alternative')
		msg['Subject'] = "ichabod - alert for {notify_dict}".format(notify_dict=notify_dict['name'])
		msg['From'] = me
		msg['To'] = you

		# Create the body of the message (a plain-text and an HTML version).
		text = "ichabod - alert for {notify_dict}".format(notify_dict=notify_dict)
		html = """
		<html>
		<head>
		<title>ichabod - alert</title>	
		</head>

		<body>
		<p>ichabod - alert / similarity check failed for: {notify_dict}</p>
		</body>

		</html>
		""".format(notify_dict=notify_dict)	

		# Record the MIME types of both parts - text/plain and text/html.
		part1 = MIMEText(text, 'plain')
		part2 = MIMEText(html, 'html')

		# Attach parts into message container.		
		msg.attach(part1)
		msg.attach(part2)
		
		s = smtplib.SMTP(config_dict['mail_server'])		
		s.sendmail(me, [you], msg.as_string())	
		s.quit()	
		print "Email successfully sent to",you


# send results to log file
# expects dicitonary
# adheres to: http://jsonlines.org/
def logResults(msg):
	fhand = open(config_dict['logfile'],"a")	
	msg['ichabod_instance'] = config_dict['ichabod_instance']
	msg['timestamp'] = str(datetime.datetime.now())
	log_string = str(msg)+"\n"	
	fhand.write(log_string)
	fhand.close()


# main function
def main(action):
	try:
		if action == "calibrate":		
			for page in config_dict['pages']:
				calibratePages(page)

		elif action == "check":
			for page in config_dict['pages']:
				runChecks(page)

		else:
			print "Action '{action}' not found, try 'calibrate' to record baseline for pages, or 'check' to runs checks.".format(action=action)

	except Exception as e:
		print "ichabod failed - email sent to ichabod admins"
		print str(e)
		msg = {
			"name":"ichabod application failure",
			"error":str(e),
			"email_recipients":config_dict['ichabodApp_email_recipients'],
			"email_sender":config_dict['ichabodApp_email_sender']
		}
		notifyAdmin(msg)
		

# take command line arguments
if __name__ == "__main__":
	if len(sys.argv) < 2:
		print "ichabod needs an argument to run. Try 'calibrate' to record baseline for pages, or 'check' to runs checks."
		exit
	else:
		# load config
		try:
			config_dict = json.loads(open("config.json","r").read())
			print "Config loaded."
			action = sys.argv[1]
			main(action)
		except Exception as e:
			print "Could not load config.json.  Exiting."

			


















