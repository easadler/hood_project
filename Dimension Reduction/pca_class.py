import site
site.addsitedir('/anaconda/lib/python2.7/site-packages')
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import ast
import re

from sklearn.decomposition import PCA, SparsePCA
from sklearn import preprocessing
from sklearn.cluster import KMeans
from mpl_toolkits.mplot3d import Axes3D
from sklearn.metrics import silhouette_samples, silhouette_score
from pymongo import MongoClient
import re

from scipy.spatial.distance import pdist, squareform
import matplotlib.pyplot as plt
from scipy.cluster.hierarchy import linkage, dendrogram, fcluster


class ReduceFeatures(object):
	def __init__(self, df, names):
		'''
			Set self.names and do preprocess data for dimension
			reduction.
		'''
		self.df = df
		self.crimes = df.columns
		self.names = names

	def fit_pca(self, n_components):
		pca = PCA(n_components = n_components)
		self.X = pca.fit_transform(self.X)
		self.df_c = pd.DataFrame(pca.components_.T, index = self.crimes, columns = [1,2,3])
		print pca.explained_variance_ratio_
		return self.df_c


	def sparse_pca(self, n_components, alpha):
		pca = SparsePCA(n_components = 3, alpha = alpha)
		self.X = pca.fit_transform(self.X)
		self.df_c = pd.DataFrame(pca.components_.T, index = self.crimes, columns = [1,2,3])
		return self.df_c

	def preprocessing(self, non_na_thresh = None):
		if non_na_thresh == None:
			non_na_thresh = len(self.df) * 0.9
		mask = (self.df.dtypes == np.float64) | (self.df.dtypes == np.int)
		df_sub = self.df.ix[:, mask]
		df_sub = df_sub.dropna(axis = 1, thresh = non_na_thresh)
		#df_sub = df_sub.fillna(0)
		imp = preprocessing.Imputer(axis=0)
		X = imp.fit_transform(df_sub)
		X_centered = preprocessing.scale(X)

		self.X = X_centered
		self.crimes = df_sub.columns.values


	def hcluster_cols(self, thresh):
		try:
			link = linkage(self.X.T, method='complete', metric = 'cosine')
			assignments = fcluster(link, thresh, 'distance')

		except:
			link = linkage(self.X.T, method='complete', metric = 'euclidean')
			assignments = fcluster(link, thresh, 'distance')

		col_ind = np.arange(len(self.crimes))
		d = pd.DataFrame(zip(col_ind, assignments)).groupby(1)[0].aggregate(lambda x: tuple(x))
		df_new = pd.DataFrame(index = np.arange(len(self.names)))
		for i in d:
			cols = []
			for w in i:
			    cols.append(w)
			if len(cols) > 1:
				df_new[str(self.crimes[cols])] = np.mean(self.X[:,cols], axis = 1)
			else:
			    df_new[str(self.crimes[cols[0]])] = self.X[:,cols[0]]

		# plt.figure(figsize=(10,20))
		# dendro = dendrogram(link, color_threshold=thresh, leaf_font_size=13, labels = self.crimes, orientation = 'left')
		# plt.subplots_adjust(top=.99, bottom=0.5, left=0.05, right=0.99)
		# plt.show()

		self.df = df_new
		self.crimes = df_new.columns.values

	def best_cluster(self):
		best = (0,0, 0)
		for i in [3,4,5,6,7,8,9,10]:
		    clusterer = KMeans(n_clusters=i)
		    cluster_labels = clusterer.fit_predict(self.X)
		    silhouette_avg = silhouette_score(self.X, cluster_labels)
		    if abs(silhouette_avg) > best[1]:
		    	best = i, silhouette_avg, cluster_labels
		    print "For n_clusters =", i, "The average silhouette_score is :", silhouette_avg
		self.best = best


	def plot_embedding(self):
		y = self.best[2]
		x_min, x_max = np.min(self.X, 0), np.max(self.X, 0)
		X = (self.X - x_min) / (x_max - x_min)
		plt.figure(figsize=(6, 6), dpi=250)
		ax = plt.subplot(111, projection='3d')

		for i in range(X.shape[0]):
			ax.text(X[i, 0], X[i, 1],X[i,2], str(self.names[i]), color=plt.cm.Set1(y[i] / 10.), fontsize = 6)
		
		ax.set_xlabel('X Label')
		ax.set_ylabel('Y Label')
		ax.set_zlabel('Z Label')
		plt.show()


if __name__ == '__main__':
	city = 'Seattle'
	state = 'WA'
	client = MongoClient('localhost', 27017)
	db = client['neighborhood_recommender']
	collection = db['crime' + '_' + city + '_' + state]
	cursor = collection.find()
	data = [crime for crime in cursor]
	df = pd.DataFrame(data)
	counts = df.groupby(['hood','summarized_offense_description'])['offense_type'].count()
	df = pd.DataFrame(counts).reset_index()
	df = df.pivot(index = 'hood', values = 'offense_type', columns = 'summarized_offense_description')

	cols_to_drop = ['PORNOGRAPHY','HARBOR CALLs','EXTORTION','METRO','FRAUD AND FINANCIAL', 'LOITERING', 'LOST PROPERTY', 'OBSTRUCT', '[INC - CASE DC USE ONLY]', 'ESCAPE', 'FALSE REPORT', 'FORGERY', 'COUNTERFEIT', 'ELUDING', 'EMBEZZLE', 'FRAUD', 'INJURY', 'SHOPLIFTING', 'TRAFFIC', 'VIOLATION OF COURT ORDER', 'FIREWORK','ANIMAL COMPLAINT', 'DISPUTE', 'ILLEGAL DUMPING','RECKLESS BURNING', 'RECOVERED PROPERTY', 'BIAS INCIDENT', 'GAMBLE']
	df = df[df.columns.difference(cols_to_drop)]	
	names = df.index


	rf = ReduceFeatures(df, names)
	rf.preprocessing(0)
	rf.hcluster_cols(0.3)
	rf.preprocessing()
	#rf.best_cluster()
	# for c in rf.crimes:
	# 	print c
	# rf.fit_pca(n_components = 3)
	# rf.best_cluster()
	print rf.fit_pca(n_components = 3)
	rf.best_cluster()

	#rf.plot_embedding()

	#rf.sparse_pca(n_components = 3)




