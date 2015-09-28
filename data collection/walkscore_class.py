import site
site.addsitedir('/anaconda/lib/python2.7/site-packages')
import json
from shapely.geometry import Point, shape
import requests
import pandas as pd
import numpy as np
from bs4 import BeautifulSoup as BS
import re
import time
from pymongo import MongoClient
from numpy.random import exponential
import socks
import socket

class Walkscore(object):
	def __init__(self, city, state):
		client = MongoClient('localhost', 27017)
		socks.setdefaultproxy(socks.PROXY_TYPE_SOCKS5, "127.0.0.1",  9150)
		socket.socket = socks.socksocket

		
		self.db = client['neighborhood_recommender']
		self.hoods = self.db['hood_data' + '_' + city + '_' + state]
		cursor = self.hoods.find()
		self.data = [hood for hood in cursor]
		self.state = state
		self.city = city
		self.temp = []

	def get_homes(self):
		self.get_addresses()
		self.add_geolocations()
		homes_collection = self.db['homes'  + '_' + self.city + '_' + self.state]

	def get_scores(self):
		self.add_walkscores('walkscore')
		self.add_walkscores('transit_score')
		self.ws_collection.insert(self.homes)

	def get_addresses(self):
	    '''
	    Input: 
	    	df: dataframe
	    Output:
	    	list of dictionaries

	    This function iterates through a list of neighborhood names and calls
	    a zillow search for each neighborhood (scrape_zillow function). It returns
	    a combined list of all the homes from every neighborhood.
	    '''
	    homes = []
	    for hood in self.data:
	        content = self.scrape_zillow(hood['name'])
	        hood_homes = self.extract_address_and_zpid(content, hood['name'], hood['id'])
	        homes.extend(hood_homes)
	    self.homes = homes


	def extract_address_and_zpid(self, html_doc, name, hood_id):
	    '''
	    Input: 
	    	html source: request.content 
	    Output:
	    	list of dictionaries

	    This function parses HTML from a zillow search of a given neighborhood
	    and then finds the address from the posting. It will return a list of 
	    dictionaries containing the neighborhood name, neighborhood id, and 
	    address.
	    '''
	    homes = []

	    soup = BS(html_doc, 'html.parser')
	    indices = [m.start() for m in re.finditer('_zpid', html_doc)]

	    zids = []

	    for index in indices:
	        string = html_doc[index - 10: index]
	        if "/" in string:
	            string = string[string.find('/') + 1 : index]
	        if string not in zids:
	            zids.append(string)
	            
	    
	    # builds a list of links from the html_source 

	    links =  [res['href'] for res in soup.find_all('a', attrs={"href": True})]
	    # Takes links and zids and returns the address of a specific zid
	    address_set = set()
	    for link in links:
	        if ('homedetails' in link):
	            home = {}
	            
	            start_index = link.find('/', 1)
	            stop_index = link.find('/', start_index + 1)
	            address = link[start_index + 1 : stop_index]
	            if address not in address_set:
	                home['address'] = address
	                home['hood_id'] = hood_id
	                home['hood_name'] = name
	                homes.append(home)
	                address_set.add(address)
	    return homes

	def scrape_zillow(self, name):
	    split_name = name.split()
	    encoded_name = '-'.join(split_name)
	    r = requests.get('http://www.zillow.com/homes/' + encoded_name + '-' + self.city + '-'+ self.state + '_rb/?fromHomePage=true', params={'user-agent': 'Mozilla/5.0'})
	    return r.content

	        



	def query_google(self, address):
	    '''
	    Input: 
	    	adress: string
	    Output:
	    	response

	    This function finds the latitude and longide from a given address
	    using the google maps api.
	    '''
	    key = 'AIzaSyCFTFhN8Ox8653xiePTnahjnbv9dxqYpyA'
	    address = re.sub('-', ' ',address)
	    url = 'https://maps.googleapis.com/maps/api/geocode/json'
	    params = {'address': address, 'key': key}
	    return requests.get(url, params = params).json()



	def add_geolocations(self):
	    '''
	    Input: 
	    	df: dataframe
	    Output:
	    	dataframe with lat, lng columns

	    This function iterates through a list of addresses and then
	    call query_google to find the latitude and longitude coordinates for each
	    address. It returns a dataframe with the lat, lng coordinates included.
	    '''
	    
	    for i, home in enumerate(self.homes):
	        r_json = self.query_google(home['address'])
	        try:
	            geo = r_json['results'][0]['geometry']['location']
	            lat = geo['lat']
	            lon = geo['lng']
	        except:
	            lat, lon = 'NA', 'NA'
	        self.homes[i]['latitude'] = lat
	        self.homes[i]['longitude'] = lon      
	        time.sleep(1)

	        
	def query_walkscore(self, address, lat, lon, kind):
	    '''
	    Input: 
	    	address: string
	    	lat: int 
	    	lon: int
	    Output:
	    	dictionary

	    This function queries walkscore and returns a dictionary of the response.
	    '''
	    key = '0390f56f90275108bcb222e683ee33d9'
	    address = re.sub('-', ' ', address)
	    if kind == 'walkscore':
	    	url = 'http://api.walkscore.com/score?format=json'
	    	params = {'lat': lat, 'lon': lon, 'address': address, 'wsapikey': key}
	    elif kind == 'transit_score':
	    	url = 'http://transit.walkscore.com/transit/score/?format=json'
	    	params = {'lat': lat, 'lon': lon, 'wsapikey': key, 'research': 'yes'}
	    
	    r =  requests.get(url, params = params)
	    try: 
	    	d = r.json()
	    except:
			d = {'error': 'error'}
			self.temp.append((r.content, address, lat, lon, kind))
	    return d

	def add_walkscores(self, kind):
	    '''
	    Input: 
	    	df: dataframe
	    Output:
	    	dataframe with walkscores

	    This function adds walkscore and walkscore description to dataframe.
	    '''
	    for i, home in enumerate(self.homes):
	        r = self.query_walkscore(home['address'], home['latitude'], home['longitude'], kind)
	        try:
	            walkscore = r[kind]
	            description = r['description']
	        except:
	            walkscore, description = 'NA', 'NA'
	            
	        self.homes[i][kind] = walkscore  
	        self.homes[i][kind + '_description'] = description  

if __name__ == '__main__':
	ws = Walkscore('Seattle', 'WA')
	ws.get_homes()
	ws.get_scores()