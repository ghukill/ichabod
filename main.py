# main module
import json
import requests
import sys
import datetime
import smtplib
import time
import traceback

# email
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# import checks module, containing all check Classes
import checks


class Page:	
	'''
	This class represents, in a Python object, the configurations set in config.json.
	The dot notation goes one level deep, more nested values are called like normal dicts.
	'''	

	# set level-1 attributes from config file
	def __init__(self, configDict):
		for k, v in configDict.items():
			setattr(self, k, v)		


# main function to run checks
def runChecks(page):
	# instantiate handle for Page instance
	phandle = Page(page)		

	# run each check in checks list
	for check_name in phandle.checks:
		print "\nRunning {check_name} for {name}".format(check_name=check_name,name=phandle.name)
		
		def checkLoop(attempt,phandle,check):

			# run function based on check name / expecting "check_result" dictionary, with 'result' key
			# create instance of check Class
			chandle = getattr(checks,check_name)()
			print "Firing",check_name,"check."

			# run checkMain
			check_result = chandle.checkMain(phandle, check_name)			
			
			# add attempt number to results
			check_result['attempt'] = attempt

			# get previous result
			prev_result = checkPrevResult(phandle.name, check_name)
		
			# did not pass test
			if check_result['result'] == False:					
				
				# log results always
				logResults(check_result)
				
				# enter retry loop
				if attempt < check['retries']:
					print "Retrying {check_name} for {name}: attempt {attempt}".format(check_name=check['name'],name=phandle.name,attempt=attempt)
					
					# sleep retry_wait_seconds * attempts - log increase in time
					time.sleep((check['retry_wait_seconds'] * attempt))
					
					attempt += 1
					checkLoop(attempt,phandle,check)

				else:
					# notify admins with check msg and page details				
					print "Max retries reached ({attempt}) for {check_name} on {name}.  Alerting.".format(check_name=check['name'],name=phandle.name,attempt=attempt)
					notify_dict = dict(page.items() + check_result.items())
					notify_dict['alert_msg'] = "Check failed, see details below"
					notifyAdmin( notify_dict )
			
			# passed test, log and move on
			else:
				logResults(check_result)


			# email All Clear if prev_result == False, current_result == True
			if prev_result['result'] == False and check_result['result'] == True:
				print "Successful check after previous failure(s), sending notification to admins."
				notify_dict = dict(page.items() + check_result.items())
				notify_dict['alert_msg'] = "//////////// ALL CLEAR //////////// -- Successful check after previous failures -- //////////// ALL CLEAR ////////////"
				notifyAdmin( notify_dict )




		# run checkLoop, 1st attempt
		# pass check dictionary, as pushed out from checks dict with check_name as key
		checkLoop(1,phandle,phandle.checks[check_name])


# main function to calibrate pages
def calibratePages(page):	
	# instantiate handle for Page instance
	phandle = Page(page)		

	# run each check in checks list
	for check_name in phandle.checks:

		# create instance of check Class
		chandle = getattr(checks,check_name)()
		print "Firing",check_name,"calibration."

		# run calibrateMain
		check_calibration = chandle.calibrateMain(phandle,check_name)
		logResults(check_calibration)


def checkPrevResult(page, check_name):

	# traverse logs backwards, looking for last instance of page check
	try:
		fhand = open(config_dict['logfile'],'r')
	except:
		print "Could not find previous log, skipping"
		return {'result':'could not find log'}
	rev_lines = reversed(fhand.readlines())
	while True:
		try:
			ich_trans = json.loads(rev_lines.next())
			if check_name == ich_trans['check_name'] and page == ich_trans['name']:
				return ich_trans
		except Exception, e:
			print str(e)
			return {'result':'could not find log'}


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
		<p>ichabod alert - {alert_msg}:</p>
		<p>{notify_dict}</p>
		</body>

		</html>
		""".format(alert_msg=notify_dict['alert_msg'], notify_dict=notify_dict)	

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


# send results to log file, expects dicitonary
# adheres to: http://jsonlines.org/
def logResults(msg):
	fhand = open(config_dict['logfile'],"a+")	
	msg['ichabod_instance'] = config_dict['ichabod_instance']
	msg['timestamp'] = str(datetime.datetime.now())
	msg = json.dumps(msg)
	log_string = str(msg)+"\n"	
	fhand.write(log_string)
	fhand.close()


# main loop
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
		# internal / external reporting
		print "ichabod failed - email sent to ichabod admins"		
		print str(e)
		ex_type, ex, tb = sys.exc_info()
		traceback_msg = traceback.format_exc()
		print traceback_msg

		# external
		notify_dict = {
			"name":"ichabod application failure",
			"alert_msg":"ichabod application failure",
			"error":str(e),		
			"traceback":traceback_msg,	
			"email_recipients":config_dict['ichabodApp_email_recipients'],
			"email_sender":config_dict['ichabodApp_email_sender']
		}
		notifyAdmin(notify_dict)
		

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

			


















