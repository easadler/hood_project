import site
site.addsitedir('/anaconda/lib/python2.7/site-packages')
import pandas as pd 
import numpy as np
from bs4 import BeautifulSoup
import requests
from pymongo import MongoClient
import socks
import socket
import nose
from fake_useragent import UserAgent
import time
from numpy.random import poisson

class ScrapeYelp(object):
	def __init__(self, hoods, ids, categories, prices):
		self.hoods = hoods
		self.categories = categories
		self.prices = prices
		self.ids = ids
		self.errors = []

		client = MongoClient('localhost', 27017)
		db = client['hood_app']
		self.collection = db['yelp_scrape']

	def scrape_GS(self):
		arr = []
		pois = poisson(lam = 5)
		for hood, idd in zip(self.hoods,self.ids):
		    for category in self.categories:
		        for price in self.prices:
		            r = self._scrape_yelp(hood, category, price)
		            pages = self._extract(r)

		            # if pages == 0:
		            # 	self.errors.append({'id': idd, 'content': r.content, 'hood': hood, 'category': category, 'price': price})

		            row = {'id': idd, 'pages': pages, 'hood': hood, 'category': category, 'price': price}
		            self.collection.insert(row)
		            time.sleep(pois)
		            arr.append(row)
       		#time.sleep(10)
	def _scrape_yelp(self, hood, category, price):
	    p = self._params(hood, category, price)
	    p_str = "&".join("%s=%s" % (k,v) for k,v in p.items())
	    ua = UserAgent()
	    headers = {'User-Agent': ua.random}
	    url = 'http://www.yelp.com/search'
	    r = requests.get(url, params = p_str)
	    return r

	def _extract(self, r):
		bs = BeautifulSoup(r.content)
		try:
		    pages = str(bs.find('div', {'class': 'page-of-pages arrange_unit arrange_unit--fill'}).text.split()[-1].strip())
		except:
		    pages = 0
		if pages == '1':
		    pages = len(bs.find_all('li', {'class': 'regular-search-result'})) / 10.
		return pages
	def _params(self, hood, category, price):
		p= {}
		p['find_loc'] =  '+'.join(hood.split(' ')) +',+Seattle,+WA'
		p['start'] = 0
		p['cflt'] = category
		if price != 'all':
			p['attrs'] = 'RestaurantsPriceRange2.' + str(price)
		p['l'] = 'p:WA:Seattle::' + '_'.join(hood.split(' '))
		return p



