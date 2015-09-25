import site
site.addsitedir('/anaconda/lib/python2.7/site-packages')
import pandas as pd 
import numpy as np 
from pymongo import MongoClient
import re

class BPFeatures(object):
	def __init__(self, city, state):
		city = 'Seattle'
		state = 'WA'
		client = MongoClient('localhost', 27017)
		db = client['neighborhood_recommender']
		collection = db['building_perm' + '_' + city + '_' + state]
		cursor = collection.find()
		data = [bp for bp in cursor]
		self.df = pd.DataFrame(data)

		

	def engineer_features(self):
		self.clean_data()
		self.get_counts()
		return self.df

	def clean_data(self):
		self.df = self.df.ix[~self.df['hood'].isnull(), :]
		self.df['application_date'] = pd.to_datetime(self.df['application_date'])
		self.df['year'] = self.df['application_date'].map(lambda x: str(x.year))
		self.df = self.df.ix[self.df['year'] != np.nan, :]
		self.df['year'] = self.df['year'].astype(float)

	def get_counts(self):
		year_counts = self.df.groupby(['hood','year'])['action_type'].count()
		self.df = pd.DataFrame(year_counts).reset_index()
		self.df = self.df.ix[self.df['year'] >= 2011, :]
		
		self.df = self.df.pivot(columns = 'year', values = 'action_type', index = 'hood')

		self.df = self.df.reset_index()

		years = [2012,2013,2014]
		
		for y in years:
			self.df['chg_' + str(y - 1) + '_' + str(y)] = self.df[y] / self.df[y-1] - 1
			

		

if __name__ == '__main__':
	c = BPFeatures('Seattle', 'WA')
	print c.engineer_features()
