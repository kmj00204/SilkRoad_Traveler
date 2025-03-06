import pandas as pd
import numpy as np
from sklearn.cluster import KMeans

df = pd.read_csv('contents/city_clusters_scale_v.csv', low_memory=False)

kmeans = KMeans(n_clusters=1000, random_state=42)
df['cluster'] = kmeans.fit_predict(df[['latitude', 'longitude']])

np.save('contents/total_clusters_centers.npy', kmeans.cluster_centers_)
