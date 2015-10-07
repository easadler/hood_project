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
	def __init__(self, city, state, data):
		client = MongoClient('localhost', 27017)
		self.db = client['neighborhood_recommender']
		self.yelp_collection = self.db['yelp_data_new' + '_' + city + '_' + state]

		self.data = data
		
		self.state = state
		self.city = city


	def yelp_data(self, number, keyword):
		'''
		INPUT:
			df: pandas dataframe (dataframe with neighborhood meta info)
		OUTPUT:
			List of JSONs (every yelp business data for all neighborhoods)

		Takes a dataframe with row[1], row[2], row[3] corresponding to 
		lat, lon, neighborhood_name and calls the other functions in this file
		to return a list of up to 160 businesses for each neighborhood. 

		'''

		for key, coords in self.data.iteritems():
			for i in xrange(200,number, 20):
				stop = self.yelp_query(key, coords, i, keyword)
				if stop:
					break


	def yelp_query(self, key, coords, offset, keyword):
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
		p = self.get_search_parameters(coords, keyword, offset)
		r = self.get_results(p)

		try:
			bizzes = r['businesses']
			for i, biz in enumerate(bizzes):
				bizzes[i]['hood_id'] = key
				bizzes[i]['category'] = keyword
		except:
			print r
			return stop
		
		try:
			self.yelp_collection.insert(bizzes)
			stop = False
		except:
			stop = True
		return stop

	def get_search_parameters(self,coords, keyword, offset):
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
		params["bounds"] = ','.join(map(str, coords[0:2])) + '|' + ','.join(map(str, coords[2:4]))
		params["category_filter"] = keyword
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
	with open('yelp_json.json', 'r') as f:
   		dic = json.load(f)	
  	y = Yelp('Seattle','WA', dic)
  	y.yelp_data(400, 'homeservices')


