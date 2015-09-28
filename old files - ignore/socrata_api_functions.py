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


# SOCRATA API FUNCTIONS

def building_permit_query(params):
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
	return requests.get(url, params= params).json()

def crime_query(params):
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
	return requests.get(url, params= params).json()



def get_socrata_data(number, query_func):
	'''
	INPUT:
		number: int
		query_func function (crime_query or building_permit_query)
	OUTPUT:
		LIST (combination of multiple offset queries)

	This function calls a query_function multiple times in order
	to get a certain number of rows (number) from a socrata dataset. 
	'''
	crime_list = []
	for i in xrange(0,number, 50000):
	    params = {'$offset': i, '$limit': 50000, '$order': 'date_reported DESC'}
	    crime_list.extend(query_func(params))
	return crime_list    
    
# GEOLOCATION FUNCTIONS

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

def get_coordinates(df):
	'''
	INPUT:
		df: dataframe
	OUTPUT:
		List of "Points" as defined in shapley 

	This function takes an array of longitude and latitude points and 
	coverts them to type point to be used in get_hood in the add_neighborhood 
	function.
	'''
	points = []
	for lon,lat in zip(df['longitude'].astype(float), df['latitude'].astype(float)):
	    points.append(Point(lon,lat))
	return points
    


def get_hood(points):
	'''
	INPUT:
		points: List of Points (shapley)
	OUTPUT:
		List of cooresponding neighborhood names

	This function takes a list of points and calls the check_polys function
	to find the neighborhood name for each point.
	'''
	hoods = []
	with open('WA.json', 'r') as f:
	    js = json.load(f)
	for p in points:
	    hoods.append(check_polys(p,js))
	return hoods


def add_neighborhood(dfs):
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
	df_other, df_hood = dfs[0], dfs[1]
	df_other = df_other.copy()
	points = get_coordinates(df_other)
	hoods = get_hood(points)
	ids = []
	names = set(df['name'])
	for hood in hoods:
	    if hood in names:
	        ids.append(int(df_hood.ix[df['name'] == hood, 'id']))
	    else:
	        ids.append('NA')
	df_other['hood_id'] = ids
	df_other['hood_name'] = hoods
	return df_other



def parallel_add_neighborhood(dfs, number = 10000, processors = 4):
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
	results = pool.map(add_neighborhood, izip(np.array_split(dfs[0].ix[0:number, :],4), [dfs[1],dfs[1],dfs[1],dfs[1]]))
	df_joined = pd.concat(results, axis=0)
	pool.close()
	pool.join()
	return df_joined

if __name__ == '__main__':
	df = pd.read_csv('../basic.csv')
	list_c = get_socrata_data(300000, crime_query)
	df_c = pd.DataFrame(list_c)
	#df_c = pd.read_csv('../2010_and_later_crime_data.csv')
	x = parallel_add_neighborhood((df_c,df), number=len(df_c), processors=4)
	x.to_csv('crime_real.csv', index = False)
	# list_d = get_socrata_data(50000, building_permit_query)
	# df_d = pd.DataFrame(list_c)
	# df = pd.read_csv('basic.csv')
	# x = parallel_add_neighborhood((df_d,df),number=25000, processors=4)