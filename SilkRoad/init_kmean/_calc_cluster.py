from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

df = pd.read_csv('contents/city_various_values.csv',
                 low_memory=False, encoding='ISO-8859-1')

scaler = StandardScaler()
latitude_longitude = df[['latitude', 'longitude']].copy()

df[['latitude', 'longitude']] = scaler.fit_transform(
    df[['latitude', 'longitude']])

X = df[['latitude', 'longitude', 'traditionality',
        'cleanliness', 'security', 'transportation', 'low_cost']]

kmeans = KMeans(n_clusters=1001, random_state=42)
df['cluster'] = kmeans.fit_predict(X)


df[['latitude', 'longitude']] = latitude_longitude
df.to_csv('contents/city_clusters_scale_v.csv', index=False)
print("저장성공")

'''
plt.figure(figsize=(10, 8))
plt.scatter(df['longitude'], df['latitude'],
            c=df['cluster'], cmap='rainbow', s=5)
plt.title('City Clusters with K=1000')
plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.colorbar(label='Cluster ID')
plt.show()
'''
