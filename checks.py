# checks module for ichabod

# main module
import json
import requests
import sys
import datetime
import smtplib
import time

# fuzzy matching
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

'''
NOTES: How to create 'calibrate' method for each check?  Should each check be a class?
'''

class Checks:

	'''
	NOTE: for each function, check_result dictionary requires 'result" key ot trigger decision in runChecks() from main.py
	'''

	# CHECKING FUNCTION TEMPLATE
	def checkTemplate(self, config_dict):
		'''
		template of check function

		Requires config in config.json:
		{
			"name":"checkHTML", // name of function (REQUIRED)
			"retries":3, // max number of retries (REQUIRED)
			"retry_wait_seconds":20 // retry wait in seconds, multiplies by attempt number each loop through (REQUIRED)
		}
		'''					

		# WORK DONE HERE
		print "The results of the template test are extraordinary."
		
		# build and return check result dictionary
		check_result = {
			"msg":"This template test performed admirably.",	
			"result":True, # REQUIRED
			"name":self.name,
			"page_url":self.page_url			
		}

		return check_result


	# function to render page, and check saved version of HTML against current version
	def checkHTML(self, check_dict):
		'''
		Uses splash server's "render.html" function, paired with fuzzy wuzzy matching.

		Requires config in config.json:
		{
			"name":"checkHTML", // name of function
			"splash_server":"example.com:8050", // location of active, accessible splash server
			"wait_time":1.5, // time given to Splash to headlessly render page				
			"retries":3, // max number of retries
			"retry_wait_seconds":20 // retry wait in seconds, multiplies by attempt number each loop through
		}
		'''

		# Download rendered HTML, check against tare version
		page_html = requests.get("http://{splash_server}/render.html?url={page_url}&wait={wait_time}".format(splash_server=check_dict['splash_server'],page_url=self.page_url,wait_time=check_dict['wait_time'])).content

		# retrieve tare HTML
		fhand = open("output/"+self.name+"_tare.html",'r')
		tare_html = fhand.read()
		fhand.close()

		# test
		fuzz_ratio = fuzz.ratio(page_html,tare_html)
		result = fuzz_ratio > check_dict['similarity_threshold']
		print "Fuzz ratio for {name}: {ratio}.  Result is {result}".format(name=self.name,ratio=str(fuzz_ratio),result=result)		

		# build and return check_result
		check_result = {
			"msg":"checkHTML result is: {result}".format(result=result),
			"result":result,
			"fuzz_ratio":fuzz_ratio,
			"similarity_threshold":check_dict['similarity_threshold'],
			"name":self.name,
			"page_url":self.page_url			
		}

		return check_result

