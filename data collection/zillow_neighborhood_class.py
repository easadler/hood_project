import site
site.addsitedir('/anaconda/lib/python2.7/site-packages')
import json
import requests
from bs4 import BeautifulSoup, UnicodeDammit
import xmltodict
from collections import defaultdict
from pymongo import MongoClient

class Neighborhoods(object):
	def __init__(self, city, state):
		client = MongoClient()
		self.db = client['neighborhood_recommender']
		self.hoods = self.db['hood_data' + '_' + city + '_' + state]
		self.state = state
		self.city = city

	def get_data(self):
		xml_text = self.zillow_hoods()
		print xml_text
		self.save_zillow_metadata(xml_text)

	def zillow_hoods(self):
		'''
		INPUT:
			state: string (state to get neighborhoods from)
			childtype: string (neighborhood, county, ....)
		OUTPUT:
			xml response from Zillow

		This function returns meta information for every neighborhood in 
		seattle.

		'''
		zid = 'X1-ZWz1ex0z87wqh7_7c2wf'
		payload = {'zws-id': zid, 'state': self.state, 'city': self.city, 'childtype': 'neighborhood'}
		url = 'http://www.zillow.com/webservice/GetRegionChildren.htm'
		return requests.get(url, params=payload).text

	def save_zillow_metadata(self, xml_text):
		'''
		INPUT: 
			xml (neighborhood metadata for all of Seattle)
		OUTPUT:
			dataframe of parsed xml data

		This function parses through the xml file returned by the
		function zillow_hoods and creates a pandas dataframe of it,
		which is returned.
		'''
		soup = BeautifulSoup(xml_text, 'xml')

		regions = soup.findAll('region')


		for region in regions[1:]:
		    dic = dict(xmltodict.parse(str(region))['region'])
		    if 'zindex' in dic:
		        dic['zindex'] = dic['zindex']['#text']
		    self.hoods.insert(dic)


if __name__ == '__main__':
	h = Neighborhoods('Seattle', 'WA')
	h.get_data()