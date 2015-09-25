from bp_features import BPFeatures 
from crime_features import CrimeFeatures 
from walkscore_features import WalkscoreFeatures 
from yelp_features import YelpFeatures 

import pandas as pd 
import numpy as np 

city = 'Seattle'
state = 'WA'

df_bp = BPFeatures(city, state)
df_c = CrimeFeatures(city, state)
df_y = YelpFeatures(city, state)
df_ws = WalkscoreFeatures(city, state)



