import site
site.addsitedir('/anaconda/lib/python2.7/site-packages')
import json
import requests
from bs4 import BeautifulSoup, UnicodeDammit
import xmltodict
from collections import defaultdict
from pymongo import MongoClient


class Demographics(object):
	def __init__(self, city, state):
		client = MongoClient()
		self.db = client['neighborhood_recommender']
		self.hoods = self.db['hood_data' + '_' + city + '_' + state]
		self.state = state
		self.city = city
		fields = ['Census Summary-RelationshipStatus: Divorced-Female', 'Census Summary-AgeDecade: 60s', 'Census Summary-RelationshipStatus: Married-Female','Affordability Data: Percent Listing Price Reduction','Census Summary-CommuteTime: 30-45min','Affordability Data: Foreclosures','Affordability Data: Median Sale Price','People Data: Single Females','Census Summary-HomeType: Condo','Census Summary-Occupancy: Own','Homes & Real Estate Data: Owners','Affordability Data: Homes For Sale By Owner','BuiltYear: 1980-1999','Census Summary-Occupancy: Rent','Census Summary-AgeDecade: 30s','Census Summary-HomeSize: 1800-2400sqft','Affordability Data: Median List Price Per Sq Ft','People Data: Homes With Kids','Census Summary-Household: WithKids','Census Summary-RelationshipStatus: Married-Male','Affordability Data: Zillow Home Value Index','city','Census Summary-AgeDecade: >=70s','Homes & Real Estate Data: Renters','People Data: Average Commute Time (Minutes)','Census Summary-AgeDecade: 20s','People Data: Median Age','People Data: Single Males','Affordability Data: Percent Homes Decreasing','BuiltYear: >2000','Census Summary-HomeType: SingleFamily','Homes & Real Estate Data: Median Home Size (Sq. Ft.)','state','Affordability Data: Median Single Family Home Value','Affordability Data: Median List Price','Census Summary-RelationshipStatus: Single-Female', 'Homes & Real Estate Data: Single-Family Homes','Census Summary-RelationshipStatus: Divorced-Male','Census Summary-RelationshipStatus: Widowed-Female','Census Summary-AgeDecade: 10s','Affordability Data: Median 2-Bedroom Home Value','Census Summary-HomeSize: <1000sqft','Affordability Data: Median 4-Bedroom Home Value','Affordability Data: Median Condo Value','Census Summary-CommuteTime: 10-20min','Homes & Real Estate Data: Avg. Year Built','Census Summary-HomeType: Other','Homes & Real Estate Data: Condos','Census Summary-HomeSize: >3600sqft','Census Summary-RelationshipStatus: Widowed-Male','People Data: Median Household Income','Affordability Data: Homes For Sale','Census Summary-CommuteTime: 45-60min','BuiltYear: 1900-1919','BuiltYear: 1920-1939','People Data: Average Household Size','Census Summary-HomeSize: 2400-3600sqft','Census Summary-AgeDecade: 0s','BuiltYear: 1960-1979','Census Summary-CommuteTime: >=60min','Census Summary-RelationshipStatus: Single-Male','Affordability Data: Property Tax','Census Summary-HomeSize: 1000-1400sqft','BuiltYear: 1940-1959','Affordability Data: Median 3-Bedroom Home Value','Affordability Data: 1-Yr. Change','Census Summary-CommuteTime: <10min','Affordability Data: Turnover (Sold Within Last Yr.)','Affordability Data: Median Value Per Sq Ft','BuiltYear: <1900','Census Summary-AgeDecade: 40s','Affordability Data: New Construction','Census Summary-AgeDecade: 50s','Census Summary-Household: NoKids','Affordability Data: Homes Recently Sold','Census Summary-HomeSize: 1400-1800sqft','Census Summary-CommuteTime: 20-30min']
		self.fields = [f.replace('.', '') for f in fields]

	def get_data(self):

		cursor = self.hoods.find()
		data = [hood for hood in cursor]
		self.get_demographic_data(data)

	def zillow_query(self,regid, name):
		'''
		INPUTS:
			regid: string (regionid of neighborhood)
			name: string (name of neighborhood)
		OUTPUTS:
			xml response from Zillow

		This function queries the zillow api for demographic information
		about a specific neighborhood by using its region id and name.
		'''
		zid = 'X1-ZWz1ex0z87wqh7_7c2wf'
		payload = {'zws-id': zid, 'neighborhood': name, 'regionid': regid}
		url = 'http://www.zillow.com/webservice/GetDemographics.htm'
		return requests.get(url, params= dict(payload)).text

	def strType(self, var):
		'''
		INPUT: 
			var: primitive type variable
		OUTPUT:
			var's type

		This funciton returns whether or not a variable can be converted
		to type float.
		'''
		try:
		    float(var)
		    return 'float'
		except:
		    return 'str'

	def demographic_data_todict(self, r):
		'''
		INPUT:
			r: xml (zml from a Zillow demographic api response)
		OUTPUT:
			dictionary of key values from the xml text

		This function takes xml from Zillow's demographic api and
		store the data returned in a dictionary.
		'''
		s = BeautifulSoup(r, 'xml')
		dic = dict()
		dic['city'] = s.find('city').text
		dic['state'] = s.find('state').text
		for t in s.findAll('table'):
		    table_name = t.find('name').text
		    for a in t.findAll('attribute'):
		        name = a.find('name').text
		        value = a.find('value').text

		        key = table_name + ': ' + name
		        key = key.replace('.', '')
		        dic[key] = value
		return dic



	def get_demographic_data(self,data):
		'''
		INPUT:
			df: dataframe (dataframe of zillow neighborhood meta data)
		OUTPUT:
			dataframe with demographic data added

		This function gets demographic data for each neighborhood and
		returns a new dataframe with added features for demographic data.
		'''
	
		hoods_dict = defaultdict(list)

		for hood in data:
			field_set = set(self.fields)
			r = self.zillow_query(hood['id'], hood['name'])
			hood_dict = self.demographic_data_todict(r)
		    
			for k,v in hood_dict.iteritems():
				hood[k] = v
				field_set.remove(k)

			if len(field_set) > 0:
				for missing_field in field_set:
					hood[missing_field] = 'NA'       
			self.hoods.update({"_id": hood["_id"]}, hood)
		

if __name__ == '__main__':
	d = Demographics('Seattle', 'WA')
	d.get_data()