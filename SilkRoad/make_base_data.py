import matplotlib.pyplot as plt
from flask import Flask, render_template
import base64
import folium
from concurrent.futures import ThreadPoolExecutor
from googletrans import Translator
from opencage.geocoder import OpenCageGeocode
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
from flask import redirect, url_for
import mysql.connector
from flask import Flask, render_template, request, jsonify, session
import json
import requests
from bs4 import BeautifulSoup
import os
from _use_cluster import cluster
import re
import googlemaps
import time
from io import BytesIO
import pandas as pd
import numpy as np
import matplotlib
import random
matplotlib.use('Agg')

conn = mysql.connector.connect(
    host='localhost',
    user='root',
    password='1234',
    database='db_silkroad'
)
cursor = conn.cursor()


query = "insert into ratings (id,city_name,name,rating1,rating2,rating3,rating4,rating5) values (%s,%s,%s,%s,%s,%s,%s,%s)"
for _ in range(3):
    with open('contents/peshawar_places.csv', 'r', encoding='utf-8') as file:
        z = file.read()
        zz = z.split('\n')
        for x in zz:
            y = x.split(',')
            if len(y) < 2:
                break
            a = random.randint(1, 6)
            b = random.randint(1, 6)
            c = random.randint(1, 6)
            d = random.randint(1, 6)
            e = random.randint(1, 6)
            cursor.execute(query, ('random', y[0], y[1], a, b, c, d, e))


query = "insert into up_searching (city_name)values (%s)"
with open('contents/main_city.txt', 'r', encoding='utf-8') as file:
    a = file.read()
    b = a.split(',')
    for _ in range(100):
        for c in b:
            z = random.random()
            if z < 0.5:
                cursor.execute(query, (c,))
                conn.commit()

query = "insert into users (username,password)values (%s,%s)"
cursor.execute(query, ('user1', 1234))
conn.commit()
cursor.execute(query, ('user2', 1234))
conn.commit()
cursor.execute(query, ('admin', 0000))
conn.commit()
