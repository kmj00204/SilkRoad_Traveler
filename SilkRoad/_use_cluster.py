import numpy as np
import pandas as pd

cluster_centers = np.load('contents/total_clusters_centers.npy')

df = pd.read_csv('contents/city_clusters_scale_v.csv', low_memory=False)

'''
def cluster(input_latitude, input_longitude):
    input_coords = np.array([[input_latitude, input_longitude]])

    closest_cluster_id = np.argmin(np.linalg.norm(
        cluster_centers - input_coords, axis=1))

    cities_in_cluster = df[df['cluster'] ==
                           closest_cluster_id]['city'].tolist()
    return int(closest_cluster_id), cities_in_cluster

'''


def cluster(input_latitude, input_longitude):
    input_coords = np.array([input_latitude, input_longitude])

    cluster_avg_coords = df.groupby(
        'cluster')[['latitude', 'longitude']].mean().values

    distances = np.linalg.norm(cluster_avg_coords - input_coords, axis=1)

    closest_cluster_id = np.argmin(distances)

    cities_in_cluster = df[df['cluster'] ==
                           closest_cluster_id]['city'].tolist()

    return int(closest_cluster_id), cities_in_cluster
