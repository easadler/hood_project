from bp_features import BPFeatures 
from crime_features import CrimeFeatures 
from walkscore_features import WalkscoreFeatures 
from yelp_features import YelpFeatures 
from pymongo import MongoClient

import pandas as pd 
import numpy as np 


city = 'Seattle'
state = 'WA'

client = MongoClient()
db = client['neighborhood_recommender']
collection = db['hood_data' + '_' + city + '_' + state]

hood_zillow = [hood for hood in collection.find()]
df_z = pd.DataFrame(hood_zillow)


# Get ID's on crime and building permit datasets
# df_id = df_z[['id', 'name']]
# df_id.columns = ['id', 'hood']

# df_bp = BPFeatures(city, state).engineer_features()
# df_bp = pd.merge(df_id, df_bp , on = 'hood').head()

# df_c = CrimeFeatures(city, state).engineer_features()
# df_c = pd.merge(df_id, df_c , on = 'hood').head()


#df_y = YelpFeatures(city, state).engineer_features()
df_ws = WalkscoreFeatures(city, state).engineer_features()
df_z.index = df_z['id']

print df_ws.ix[, :]
# for df_temp in [df_c, df_bp]:
# 	df_temp.index = df_temp['id']
# 	cols_to_use = df_temp.columns.difference(df_z.columns)
# 	df_z = pd.merge(df_z, df_temp[cols_to_use], left_index=True, right_index=True, how='left')



for df_temp in [df_ws]:
	df_temp.index = df_temp['hood_id']
	cols_to_use = df_temp.columns.difference(df_z.columns)
	df_z = pd.merge(df_z, df_temp[cols_to_use], left_index=True, right_index=True, how='left')

#print df_z.head()



