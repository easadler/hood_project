import site
site.addsitedir('/anaconda/lib/python2.7/site-packages')
import pandas as pd 
import numpy as np 
from pymongo import MongoClient
import re



class WalkscoreFeatures(object):
	def __init__(self, city, state):
		city = 'Seattle'
		state = 'WA'
		client = MongoClient('localhost', 27017)
		db = client['neighborhood_recommender']
		yelp_collection = db['ws_final' + '_' + city + '_' + state]
		cursor = yelp_collection.find()
		data = [score for score in cursor]
		self.df = pd.DataFrame(data)

	def engineer_features(self):
		means = self.df.groupby('hood_name')['transit_score','walkscore'].mean()
		self.df = pd.DataFrame(means).reset_index()
		self.df = self.df.rename(columns={'hood_name':'hood'})
		return self.df

if __name__ == '__main__':
	w = WalkscoreFeatures('Seattle', 'WA')
	print w.engineer_features()
