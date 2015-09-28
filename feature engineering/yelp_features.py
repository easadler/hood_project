import site
site.addsitedir('/anaconda/lib/python2.7/site-packages')
import pandas as pd 
import numpy as np 
from pymongo import MongoClient
import re


class YelpFeatures(object):
	def __init__(self, city, state):
		city = 'Seattle'
		state = 'WA'
		client = MongoClient('localhost', 27017)
		db = client['neighborhood_recommender']
		yelp_collection = db['yelp_data' + '_' + city + '_' + state]
		cursor = yelp_collection.find()
		data = [hood for hood in cursor]
		self.df = pd.DataFrame(data)

		restaurants = ["[u'Pizza']","[u'Mexican']","[u'Vietnamese']","[u'American (New)']",
		"[u'Thai']","[u'Japanese']","[u'Italian']","[u'Sandwiches']","[u'American (Traditional)']","[u'Chinese']",
		"[u'Seafood']","[u'Burgers']","[u'Breakfast & Brunch']","[u'Barbeque']","[u'Indian']","[u'Greek']","[u'Ethiopian']","[u'Korean']","[u'Asian Fusion']","[u'French']",
		"[u'Food Trucks']","[u'Mediterranean']","[u'Veterinarians']","[u'Bakeries']","[u'Desserts']","[u'Donuts']","[u'Fast Food']","[u'Ice Cream & Frozen Yogurt']"]

		nightlife = ["[u'Bars']","[u'Pubs']","[u'Sushi Bars']","[u'Dive Bars']","[u'Beer']","[u'Lounges']","[u'Sports Bars']","[u'Breweries']","[u'Venues & Event Spaces']",
		"[u'Performing Arts']"]

		workout = ["[u'Yoga']", "[u'Trainers']", "[u'Gyms']",]

		Essentials = ["[u'Coffee & Tea']","[u'Hair Salons']","[u'Delis']","[u'Dry Cleaning & Laundry']",
		"[u'Barbers']","[u'Convenience Stores']","[u'Gas & Service Stations']",
		"[u'Hair Stylists']","[u'Grocery']","[u'Cafes']","[u'Banks & Credit Unions']","[u'Drugstores']","[u'Nail Salons']"]

		business = ["[u'Auto Repair']","[u'Real Estate Agents']","[u'General Dentistry']","[u'Contractors']","[u'Plumbing']","[u'Jewelry']","[u'Painters']","[u'Landscaping']",
		"[u'Caterers']","[u'Keys & Locksmiths']","[u'Heating & Air Conditioning/HVAC']","[u'Pet Stores']","[u'Women's Clothing']","[u'Carpet Cleaning']",
		"[u'Body Shops']","[u'Tours']","[u'Electricians']","[u'IT Services & Computer Repair']","[u'Insurance']","[u'Optometrists']","[u'Home Inspectors']","[u'Tires']",
		"[u'Mortgage Brokers']","[u'Car Dealers']","[u'Photographers']","[u'Chiropractors']","[u'Movers']","[u'Dog Walkers']","[u'Day Spas']","[u'Massage Therapy']",
		"[u'Skin Care']","[u'Acupuncture']","[u'Massage']"]

		character = ["[u'Bookstores']","[u'Landmarks & Historical Buildings']","[u'Parks']",
		             "[u'Florists']","[u'Churches']","[u'Pet Boarding/Pet Sitting']","[u'Tattoo']"]	

		self.categories = {'nightlife': nightlife, 'business': business, 'character': character, 'restaurants': restaurants, 'workout': workout, 'essentials': Essentials}


	def engineer_features(self):
		self.clean_data()
		self.get_counts()
		self.get_percentages()
		self.df = self.df.rename(columns={'hood_id':'id'})
		return self.df

	def clean_data(self):
		self.df = self.df.ix[~self.df['categories'].isnull(), :]
		#category_list = self.df['categories'].apply(lambda x: self.convert_to_list(x))
		category_list = self.df['categories'].apply(lambda x: x[0][:1])
		for c in category_list:
		    c.sort()
		self.df['c'] = category_list
		self.df['c'] = self.df['c'].astype(str)


	def convert_to_list(self, string):
	    strs = string.split('], [')
	    for i, st in enumerate(strs):
	        strs[i] = self.remove_braces(st)
	    return strs



	def remove_braces(self, string):
	    return re.sub('\[|, .*$','',string)


	def get_counts(self):

		for k,v in self.categories.iteritems():
		    self.df[k] = 0
		    self.df.ix[self.df['c'].isin(v), k] = 1

		counts = self.df.groupby('hood_id')[self.categories.keys()].sum()
		self.df = pd.DataFrame(counts).reset_index()

	def get_percentages(self):
		self.df['yelp_total'] = 0

		for col in self.categories.keys():
			self.df['yelp_total'] += self.df[col]

		for col in self.categories.keys():
			self.df[col + '_perc'] = self.df[col] / self.df['yelp_total'].astype(float)

		print self.df


if __name__ == '__main__':
	y = YelpFeatures('Seattle', 'WA')
	y.engineer_features()




