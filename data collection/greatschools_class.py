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
from bs4 import BeautifulSoup

def check_polys(point, js):
	'''
	INPUT:
		point: Point (shapley)
		js: GeoJSON file
	OUTPUT:
		Neighborhood Name

	This function takes a point and GeoJSON file and searches
	the GeoJSON file to see if the point is contained by any of the
	polygons, which are neighborhoods in this case. 
	'''
	for feature in js['features']:
	    polygon = shape(feature['geometry'])
	    if polygon.contains(point):
	        return feature['properties']['NAME']
	return 'NA'

def add_neighborhood(split_data):
	'''
	INPUT:
		dfs: Tuple of DataFrames
			0: DataFrame containing lat, longs
			1: DataFrame containing neighborhood names
	OUTPUT:
		DataFrame with added hood_name and hood_id column

	This function takes a DataFrame of neighborhood information and 
	a DataFrame with latitude and longitude pairs and figures out if coordinates 
	are contained inside a neighborhood. 
	'''

	with open('Seattle.json', 'r') as f:
		js = json.load(f)
		updated_data = []
		for row in split_data:
			try:
				p = Point(float(row['longitude']), float(row['latitude']))
				hood = check_polys(p,js)
				row['hood'] = hood
			except:
				row['hood'] = 'NA'

			updated_data.append(row)
		return updated_data



class GreatSchools(object):
	def __init__(self, city, state):
		client = MongoClient('localhost', 27017)
		self.db = client['neighborhood_recommender']
		self.gs_collection = self.db['gs_' + '_' + city + '_' + state]
		self.state = state
		self.city = city

	def get_data(self):
		params = {'limit': -1, 'sort': 'gs_rating'}
		data = self.gs_query(params)
		self.parse_data(data)

	def parse_data(self, data):
		soup = BeautifulSoup(data, 'xml')

		for school in soup.findAll('school'):
			name = school.find('name').text
			try: 
				gsRating = school.find('gsRating').text
			except:
				gsRating = 'NA'
			try:
				parRating = school.find('parentRating').text
			except:
				parRating = 'NA'
			try:
				gradeRange = school.find('gradeRange').text
			except:
				gradeRange = 'NA'
			try:
				s_type = school.find('type').text
			except:
				s_type = 'NA'

			latitude = school.find('lat').text
			longitude = school.find('lon').text
			row = {'name': name, 'gsRating': gsRating, 'type': s_type ,'gradeRange': gradeRange,'parRating': parRating, 'latitude': latitude, 'longitude': longitude}
			self.gs_collection.insert(row)


	def gs_query(self, params):
		'''
		INPUT:
			params: DICT
		OUTPUT:
			Requested crime data from socrata

		This function queries Seattle's crime dataset 
		on their open data portal. The two parameters passes are $limit
		and $Offset. 
		'''
		url = 'http://api.greatschools.org/schools/' + self.state + '/' + self.city
		params['key'] = 'r4tchr82jlck3rxafgfdxqxx'
		r = requests.get(url, params= params).content
		return r


	def add_hood(self):
		self.data = [school for school in self.gs_collection.find()]
		self.parallel_add_neighborhood()

	def parallel_add_neighborhood(self, processors = 4):
		'''
		INPUT:
			dfs: Tuple of DataFrames
				0: DataFrame containing lat, longs
				1: DataFrame containing neighborhood names
			number: int
			processors: int 
		OUTPUT:
			List of 4 DataFrames created in parallel

		This function takes a DataFrame of neighborhood information and 
		a DataFrame with latitude and longitude pairs and figures out if coordinates 
		are contained inside a neighborhood IN PARALLEL. You can specify the number of 
		processors used and the number of observations. 
		'''
		pool = Pool(processes=4)
		results = pool.map(add_neighborhood, np.array_split(self.data,4))
		for split in results:
			for row in split:
					self.gs_collection.update({"_id": row['_id']}, row)
		pool.close()
		pool.join()
