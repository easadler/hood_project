from bp_features import BPFeatures 
from crime_features import CrimeFeatures 
from walkscore_features import WalkscoreFeatures 
from yelp_features import YelpFeatures 
from pymongo import MongoClient

import pandas as pd 
import numpy as np 


class CombineData(object):
	def __init__(self, city, state):
		self.city = city
		self.state = state

		client = MongoClient()
		db = client['neighborhood_recommender']
		collection = db['hood_data' + '_' + city + '_' + state]

		hood_zillow = [hood for hood in collection.find()]
		self.df_z = pd.DataFrame(hood_zillow)

	def load_data_and_engineer_features(self):
		df_id = self.df_z[['id', 'name']]
		df_id.columns = ['id', 'hood']

		df_bp = BPFeatures(self.city, self.state).engineer_features()
		self.df_bp = pd.merge(df_id, df_bp , on = 'hood')

		df_c = CrimeFeatures(self.city, self.state).engineer_features()
		self.df_c = pd.merge(df_id, df_c , on = 'hood')


		self.df_y = YelpFeatures(self.city, self.state).engineer_features()
		self.df_ws = WalkscoreFeatures(self.city, self.state).engineer_features()


	def combine_datasets(self):
		self.df_z.index = self.df_z['id']
		for df_temp in [self.df_c, self.df_bp, self.df_ws, self.df_y]:
			df_temp.index = df_temp['id']
			cols_to_use = df_temp.columns.difference(self.df_z.columns)
			self.df_z = pd.merge(self.df_z, df_temp[cols_to_use], left_index=True, right_index=True, how='inner')
		return self.df_z



if __name__ == '__main__':
	cb = CombineData('Seattle', 'WA')
	cb.load_data_and_engineer_features()
	df = cb.combine_datasets()
	df.to_csv('final.csv', index = False)





