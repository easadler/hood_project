import site
site.addsitedir('/anaconda/lib/python2.7/site-packages')
import json
from shapely.geometry import Point, shape
import requests
import pandas as pd
import numpy as np
from multiprocessing import Pool
from itertools import izip
from pymongo import MongoClient
import rauth

class Yelp(object):
	def __init__(self, city, state):
		client = MongoClient('localhost', 27017)
		self.db = client['neighborhood_recommender']
		self.yelp_collection = self.db['yelp_data' + '_' + city + '_' + state]
		self.hoods = self.db['hood_data' + '_' + city + '_' + state]

		cursor = self.hoods.find()
		self.data = [hood for hood in cursor]
		self.state = state
		self.city = city


	def yelp_data(self, number):
		'''
		INPUT:
			df: pandas dataframe (dataframe with neighborhood meta info)
		OUTPUT:
			List of JSONs (every yelp business data for all neighborhoods)

		Takes a dataframe with row[1], row[2], row[3] corresponding to 
		lat, lon, neighborhood_name and calls the other functions in this file
		to return a list of up to 160 businesses for each neighborhood. 

		'''

		for hood in self.data:
			for i in xrange(0,number, 20):
				stop = self.yelp_query(hood, i)
				if stop:
					break


	def yelp_query(self, hood, offset):
		'''
		INPUT:
			x: numpy array (row from dataframe)
			offset: int (offset for yelp query)
		OUTPUT:
			List of JSONs

		This function combines get_search_parameters amd get_results and
		returns a list of 20 business json's to get_hood_yelp_data, which will
		be concatenated to the rest of the businesses for a given hood.
		'''
		p = self.get_search_parameters(hood['latitude'], hood['longitude'], hood['name'], offset)
		r = self.get_results(p)

		bizzes = r['businesses']
		for i, biz in enumerate(bizzes):
			bizzes[i]['hood_id'] = hood['id']
		try:
			self.yelp_collection.insert(bizzes)
			stop = False
		except:
			stop = True
		return stop

	def get_search_parameters(self,lat,lon, neighborhood, offset):
		'''
		INPUT:
		lat: int
		lon: int
		neighborhood: string
		offset:
		OUTPUT:
		dictionary of parameters

		This function takes in search parameters and converts them
		to a dictionary that will be digested by get_results.

		'''
		#See the Yelp API for more details
		params = {}
		params["cll"] = str(lat) + ',' + str(lon)
		params["location"] = neighborhood + ',' + self.city + ',' + self.state
		params['offset'] = offset
		return params 

	def get_results(self,params):
		'''
		INPUT:
			params: dict (dict of parameters)
		OUTPUT:
			JSON containing businesses data

		This function queries the yelp api for 20 businesses
		for a specific neighborhood. This function encapsulates 
		all of the oauth stuff required by yelp.
		'''

		consumer_key = "qJEg7amAswZXSS5FuCk_hw"
		consumer_secret = "tqQcsIUE2A4Z4POJQDJNgz7RvdA"
		token = "V9jFtdX6V9PweZm7dAioEPbitM1WNfbo"
		token_secret = "nA3b5R6bU99wQoTmgk3M2epKit0"

		session = rauth.OAuth1Session(
		consumer_key = consumer_key
		,consumer_secret = consumer_secret
		,access_token = token
		,access_token_secret = token_secret)

		request = session.get("http://api.yelp.com/v2/search",params=params)

		data = request.json()
		session.close()

		return data	
  
if __name__ == '__main__':
  	y = Yelp('Seattle',"WA")
  	y.yelp_data(160)