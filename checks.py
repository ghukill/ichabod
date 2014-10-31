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
	

class Checks:

	'''
	NOTE: for each function, check_result dictionary requires 'result" key ot trigger decision in runChecks() from main.py
	'''

	# CHECKING FUNCTION TEMPLATE
	def checkTemplate(self, config_dict):
		'''
		template of check function
		'''					

		# WORK DONE HERE
		
		# build and return check result dictionary
		check_result = {
			"msg":"This test performed admirably.",	
			"result":True,		
			"name":self.name,
			"page_url":self.page_url			
		}

		return check_result


	# function to render page, and check saved version of HTML against current version
	def checkHTML(self, config_dict):
		'''
		Uses splash server's "render.html" function, paired with fuzzy wuzzy matching
		'''
		
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

		# build and return check_result
		check_result = {
			"msg":"checkHTML result is: {result}".format(result=result),
			"result":result,
			"fuzz_ratio":fuzz_ratio,
			"similarity_threshold":self.similarity_threshold,
			"name":self.name,
			"page_url":self.page_url			
		}

		return check_result

