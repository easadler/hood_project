import site
site.addsitedir('/anaconda/lib/python2.7/site-packages')
import pandas as pd 
import numpy as np 
from pymongo import MongoClient
import re


class CrimeFeatures(object):
	def __init__(self, city, state):
		city = 'Seattle'
		state = 'WA'
		client = MongoClient('localhost', 27017)
		db = client['neighborhood_recommender']
		collection = db['crime' + '_' + city + '_' + state]
		cursor = collection.find()
		data = [crime for crime in cursor]
		self.df = pd.DataFrame(data)

		violent = ['ASSAULT','WEAPON', 'HOMICIDE']

		theft = ['CAR PROWL','BURGLARY','STOLEN PROPERTY','BIKE THEFT',
		'BURGLARY-SECURE PARKING-RES','ROBBERY','MAIL THEFT',
		'VEHICLE THEFT','SHOPLIFTING','PICKPOCKET','PURSE SNATCH',
		'TRESPASS']

		drugs_alc = ['NARCOTICS','LIQUOR VIOLATION','DUI',
		'STAY OUT OF AREA OF DRUGS']

		prostitution = ['PROSTITUTION','PORNOGRAPHY', 'STAY OUT OF AREA OF PROSTITUTION']

		self.categories = {'violent': violent, 'theft': theft, 'drugs_alc': drugs_alc, 'prostitution': prostitution}


	def engineer_features(self):
		self.clean_data()
		self.get_counts()
		return self.df

	def clean_data(self):
		self.df = self.df.ix[~self.df['hood'].isnull(), :]
		

	def get_counts(self):

		for k,v in self.categories.iteritems():
		    self.df[k] = 0
		    self.df.ix[self.df['summarized_offense_description'].isin(v), k] = 1

		counts = self.df.groupby('hood')[self.categories.keys()].sum()
		self.df = pd.DataFrame(counts).reset_index()

if __name__ == '__main__':
	c = CrimeFeatures('Seattle', 'WA')
	print c.engineer_features()

