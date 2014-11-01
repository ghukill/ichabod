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


class CheckTemplate:
	# CHECKING FUNCTION TEMPLATE
	def checkMain(self, phandle, check_name):
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
		check_dict = phandle.checks[check_name]
		print "The results of the template test are extraordinary."
		
		# build and return check result dictionary
		check_result = {
			"msg":"This template test performed admirably.",	
			"result":True, # REQUIRED
			"name":phandle.name,
			"page_url":phandle.page_url			
		}

		return check_result

	# main calibration function
	def calibrateMain(self, phandle, check_name):
		print "Calibration for {name}".format(name=phandle.name)
		check_dict = phandle.checks[check_name]

		# log
		log_dict = {
		"msg":"CheckTemplate calibration did nothing, but finished with aplomb",
		"name":phandle.name,
		"page_url":phandle.page_url

		}
		return log_dict



class CheckHTML:
	# function to render page, and check saved version of HTML against current version
	def checkMain(self, phandle, check_name):
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
		# gen check_dict
		check_dict = phandle.checks[check_name]

		# Download rendered HTML, check against tare version
		page_html = requests.get("http://{splash_server}/render.html?url={page_url}&wait={wait_time}".format(splash_server=check_dict['splash_server'],page_url=phandle.page_url,wait_time=check_dict['wait_time'])).content

		# retrieve tare HTML
		fhand = open("output/"+phandle.name+"_tare.html",'r')
		tare_html = fhand.read()
		fhand.close()

		# test
		fuzz_ratio = fuzz.ratio(page_html,tare_html)
		result = fuzz_ratio > check_dict['similarity_threshold']

		print "Fuzz ratio for {name}: {ratio}.  Result is {result}".format(name=phandle.name,ratio=str(fuzz_ratio),result=result)		

		# build and return check_result
		check_result = {
			"msg":"checkHTML result is: {result}".format(result=result),
			"result":result,
			"fuzz_ratio":fuzz_ratio,
			"similarity_threshold":check_dict['similarity_threshold'],
			"name":phandle.name,
			"page_url":phandle.page_url			
		}

		return check_result


	# main calibration function
	def calibrateMain(self, phandle, check_name):
		
		print "Setting calibration tare for {name}".format(name=phandle.name)
		
		# gen check_dict from phandle and check_name
		check_dict = phandle.checks[check_name]

		# Download rendered HTML, save to tare
		fhand = open("output/"+phandle.name+"_tare.html",'w')
		page_html = requests.get("http://{splash_server}/render.html?url={page_url}&wait={wait_time}".format(splash_server=check_dict['splash_server'],page_url=phandle.page_url,wait_time=check_dict['wait_time'])).content
		fhand.write(page_html)
		fhand.close()
		print "HTML tare written."

		# log
		log_dict = {
		"msg":"Calibration tare created",
		"name":phandle.name,
		"page_url":phandle.page_url

		}
		return log_dict

