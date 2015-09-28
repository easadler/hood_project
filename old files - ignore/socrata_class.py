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

class Socrata(object):
	def __init__(self, city, state):
		client = MongoClient('localhost', 27017)
		self.db = client['neighborhood_recommender']
		self.crime_collection = self.db['crime' + '_' + city + '_' + state]
		self.bp_collection = self.db['building_perm' + '_' + city + '_' + state]
		self.state = state
		self.city = city

	def get_data(self, data_type):
		if data_type == 'crime':
			self.query = self.crime_query
			self.get_socrata_data(300000, 'date_reported DESC')
		elif data_type == 'bp':
			self.query = self.building_permit_query
			self.get_socrata_data(50001, 'application_permit_number DESC')

	def add_hood(self, data_type):
		if data_type == 'crime':
			self.data_type = 'crime'
			self.data = [crime for crime in self.crime_collection.find()]
			self.parallel_add_neighborhood()
		elif data_type == 'bp':
			self.data_type = 'bp'
			self.data = [bp for bp in self.bp_collection.find()]
			self.parallel_add_neighborhood()

	def get_socrata_data(self, number, order):
		'''
		INPUT:
			number: int
			query_func function (crime_query or building_permit_query)
		OUTPUT:
			LIST (combination of multiple offset queries)

		This function calls a query_function multiple times in order
		to get a certain number of rows (number) from a socrata dataset. 
		'''
		for i in xrange(0,number, 50000):
		    params = {'$offset': i, '$limit': 50000, '$order': order}
		    self.query(params)

	def building_permit_query(self, params):
		'''
		INPUT:
			params: DICT
		OUTPUT:
			Requested building permit data from socrata

		This function queries Seattle's building permit dataset 
		on their open data portal. The two parameters passes are $limit
		and $Offset. 
		'''
		url = 'https://data.seattle.gov/resource/mags-97de.json'
		r = requests.get(url, params= params).json()
		self.bp_collection.insert(r)

	def crime_query(self, params):
		'''
		INPUT:
			params: DICT
		OUTPUT:
			Requested crime data from socrata

		This function queries Seattle's crime dataset 
		on their open data portal. The two parameters passes are $limit
		and $Offset. 
		'''
		url = 'https://data.seattle.gov/resource/7ais-f98f.json'
		r = requests.get(url, params= params).json()
		self.crime_collection.insert(r)

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
				if self.data_type == 'crime':
					self.crime_collection.update({"_id": row['_id']}, row)
				elif self.data_type == 'bp':
					self.bp_collection.update({"_id": row['_id']}, row)
		pool.close()
		pool.join()

if __name__ == '__main__':
	s = Socrata('Seattle', 'WA')
	s.add_hood('bp')
