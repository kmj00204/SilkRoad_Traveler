import math
from decimal import Decimal
import datetime
import matplotlib.pyplot as plt
import base64
from concurrent.futures import ThreadPoolExecutor
from opencage.geocoder import OpenCageGeocode
from geopy.exc import GeocoderTimedOut
from geopy.geocoders import Nominatim
from googletrans import Translator
from flask import redirect, url_for
import mysql.connector
from flask import Flask, render_template, request, jsonify, session, send_file
import os
import re
from mtranslate import translate
import folium
from sklearn.preprocessing import StandardScaler
import json
import requests
from bs4 import BeautifulSoup
from _use_cluster import cluster
import asyncio
import aiohttp
import googlemaps
import time
from io import BytesIO
import pandas as pd
from sklearn.cluster import KMeans
import numpy as np
import matplotlib.pyplot as plt
import matplotlib
import random
import csv
matplotlib.use('Agg')


app = Flask(__name__)
app.secret_key = 'password'

reserves = [
    "https://www.expedia.co.kr/Hotel-Search?destination={}&flexibility=0_DAY",
    "https://www.booking.com/searchresults.ko.html?ss={}",
    "https://www.airbnb.co.kr/s/{}/homes?tab_id%20 =home_tab"
]


def get_db_connection():
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='1234',
        database='db_silkroad'
    )
    return conn


def create_map(latitude, longitude):
    map = folium.Map(location=[latitude, longitude],
                     zoom_start=12)

    folium.Marker([latitude, longitude], popup="위도: {}, 경도: {}".format(
        latitude, longitude)).add_to(map)

    map_html = map._repr_html_()
    return map_html


def get_city_images(city_name):
    api_key = "46949505-039063355171531e5770aa181"

    url = f"https://pixabay.com/api/?key={api_key}&q={city_name}&image_type=photo&per_page=5"

    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()

        if 'hits' in data and len(data['hits']) > 0:
            image_urls = [hit['webformatURL'] for hit in data['hits'][:2]]
            return image_urls
        else:
            return None
    else:
        return None


def get_lat_lon_opencage(city_name):
    geolocator = Nominatim(user_agent="city_locator")
    try:
        location = geolocator.geocode(city_name)
        if location:
            return (location.latitude, location.longitude)
        else:
            return -1, -1
    except Exception as e:
        return -1, -1
    return -1, -1


def get_lat_lon(city_name):
    # api_key = '6d3f91fcd38a4c5e9fe47bb8c9947122'
    api_key = '1ed849e4ec824bda81e2084f074206b0'
    geocoder = OpenCageGeocode(api_key)
    result = geocoder.geocode(city_name)
    if result:
        latitude = result[0]['geometry']['lat']
        longitude = result[0]['geometry']['lng']
        return latitude, longitude
    else:
        return get_lat_lon_opencage(city_name)
    return get_lat_lon_opencage(city_name)


def translate2_ko_to_en(city_name):
    try:
        translator = Translator()
        translation = translator.translate(
            city_name, src='ko', dest='en')
        if translation.text:
            return translation.text
    except Exception as e:
        return city_name


def translate2_en_to_ko(city_name):
    try:
        translator = Translator()
        translation = translator.translate(
            city_name, src='en', dest='ko')
        if translation.text:
            return translation.text
    except Exception as e:
        return city_name


def translate1_en_to_ko(city_name):
    try:
        translated_text = translate(city_name, 'ko', 'en')
        return translated_text
    except Exception as e:
        return city_name


def translate1_ko_to_en(city_name):
    try:
        translated_text = translate(city_name, 'en', 'ko')
        return translated_text
    except Exception as e:
        return city_name


def translate_city_name_ko_to_en(city_name):
    result = translate1_ko_to_en(city_name)
    if result == city_name:
        result = translate2_ko_to_en(city_name)
    return result


def translate_city_name_en_to_ko(city_name):
    result = translate1_en_to_ko(city_name)
    if result == city_name:
        result = translate2_en_to_ko(city_name)
    return result


def translate_and_search(city_name):
    if not city_name:
        city_name = 'None'
    name = translate_city_name_ko_to_en(city_name)
    latitude, longitude = get_lat_lon(name)
    return latitude, longitude


def no_translate_search(city_name):
    if not city_name:
        city_name = 'None'
    latitude, longitude = get_lat_lon(city_name)
    return latitude, longitude


def get_cities_in_cluster_only_str(cluster_number):
    df = pd.read_csv('contents/city_clusters_v.csv', low_memory=False)
    cluster_cities = df[df['cluster'] == int(cluster_number)]
    cities_str = '@'.join(cluster_cities['city'].tolist())
    return cities_str


def cluster_map():
    df = pd.read_csv('contents/city_clusters_v.csv', low_memory=False)

    plt.figure(figsize=(10, 8))
    plt.scatter(df['longitude'], df['latitude'],
                c=df['cluster'], cmap='rainbow', s=5)
    plt.title('All Clusters Map')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    plt.colorbar(label='Cluster ID')

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    plt.close()

    return img_base64


@app.route('/get_map_url', methods=['GET'])
def get_map_url():
    city = request.args.get('city')

    connection = get_db_connection()
    cursor = connection.cursor()

    query = "SELECT * FROM locationdatas WHERE id=%s"
    cursor.execute(query, (city,))
    result = cursor.fetchone()

    map_html = None

    if result:
        latitude = result[1]
        longitude = result[2]
        closest_cluster_id = result[3]
        cities_in_cluster = result[4]
        map_html = result[5]
        image_urls = result[6]
        return jsonify({
            'latitude': latitude,
            'longitude': longitude,
            'cluster_id': closest_cluster_id,
            'cities_in_cluster': cities_in_cluster,
            'map_html': map_html,
            'image_urls': image_urls
        })

    rec = "https://kr.trip.com/global-gssearch/searchlist/search?keyword={}&locale=ko-KR&curr=KRW"
    r = requests.get(rec.format(city))
    soup = BeautifulSoup(r.text, 'html.parser')
    url = None
    script_tag = soup.find('script', attrs={'id': '__NEXT_DATA__'})
    script_tag = json.loads(script_tag.string)
    for data_item in script_tag["props"]["pageProps"]["resnew"]["data"]:
        for item in data_item["itemList"]:
            url = item["url"]
            break
    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as e:
        if (url):
            r = requests.get('https://kr.trip.com'+str(url))

    soup = BeautifulSoup(r.text, 'html.parser')
    script_tag = soup.find('script', attrs={'id': '__NEXT_DATA__'})

    if script_tag:
        json_data = json.loads(script_tag.string)

    module_list = None

    if script_tag and script_tag.get("props") and script_tag["props"].get("pageProps"):
        module_list = script_tag["props"]["pageProps"].get("moduleList", [])

    if module_list:
        for module in module_list:
            if isinstance(module, list):
                for sub_module in module:
                    entry_module = sub_module.get("entryModule")
                    if entry_module:
                        for entry in entry_module.get("entryList", []):
                            if entry.get("type") == "sight":
                                url = entry.get("jumpUrl")
            else:
                entry_module = module.get("entryModule")
                if entry_module:
                    for entry in entry_module.get("entryList", []):
                        if entry.get("type") == "sight":
                            url = entry.get("jumpUrl")

    try:
        r = requests.get(url)
    except requests.exceptions.RequestException as e:
        if (url):
            r = requests.get('https://kr.trip.com'+str(url))

    soup = BeautifulSoup(r.text, 'html.parser')
    latitude = None
    longitude = None
    script = soup.find_all('script', attrs={'type': 'application/ld+json'})
    if result:
        latitude, longitude = no_translate_search(result)
        if (latitude == -1 and longitude == -1):
            latitude, longitude = translate_and_search(result)

    closest_cluster_id = None
    cities_in_cluster_str = None
    image_urls_str = None
    map_url = None
    if latitude and longitude and (latitude != -1) and (longitude != -1):
        map_url = create_map(float(latitude), float(longitude))

        closest_cluster_id, cities_in_cluster = cluster(
            float(latitude), float(longitude))
        cities_in_cluster_str = ','.join(map(str, cities_in_cluster[:10]))
    image_urls = get_city_images(city)
    mage_urls = get_city_images(city)
    image_urls_str = None
    if image_urls:
        image_urls_str = ','.join(map(str, image_urls))

    if latitude and closest_cluster_id and cities_in_cluster_str and map_url and image_urls_str:
        query = "INSERT INTO locationdatas (id, latitude, longitude, closest_cluster_id , cities_in_cluster ,map_html  , image_urls ) VALUES (%s,%s,%s, %s, %s, %s, %s)"
        cursor.execute(query, (city, latitude, longitude, closest_cluster_id,
                               cities_in_cluster_str, map_url, image_urls_str))
        connection.commit()

    connection.close()
    cursor.close()

    return jsonify({
        'latitude': latitude,
        'longitude': longitude,
        'cluster_id': closest_cluster_id,
        'cities_in_cluster': cities_in_cluster_str,
        'map_html': map_url,
        'image_urls': image_urls_str
    })


def make_response(city):
    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT * FROM cityviews WHERE id=%s"
    cursor.execute(query, (city,))
    jpg_images_with_words = []
    results = cursor.fetchall()
    if results:
        for result in results:
            jpg_images_with_words.append([result[1],
                                          result[2], result[3], result[4], result[5], result[6]])
        return jpg_images_with_words

    rec = "https://kr.trip.com/global-gssearch/searchlist/search?keyword={}&locale=ko-KR&curr=KRW"
    r = requests.get(rec.format(city))
    soup = BeautifulSoup(r.text, 'html.parser')

    script_tag = soup.find('script', attrs={'id': '__NEXT_DATA__'})
    tags = soup.find_all(
        'div', attrs={'class': 'gl-search-result_list-position'})
    locations = None
    locations = [tag.text.strip() for tag in tags]
    location = None
    jpg_images_with_words = []
    if script_tag:
        json_data = json.loads(script_tag.string)

        resnew_data = json_data.get('props', {}).get(
            'pageProps', {}).get('resnew', None)

        if resnew_data:
            items = resnew_data['data']
            for entry in items:
                if not entry['resultTab']['word'].startswith("호텔"):
                    for item in entry['itemList']:
                        if 'imageUrl' in item and item['imageUrl'].endswith('.jpg'):
                            word = item['word'].split('/')[0]
                            if word != city:
                                image_url = item['imageUrl']
                                formatted_reserves = (
                                    reserves[0].format(word),
                                    reserves[1].format(word),
                                    reserves[2].format(word),
                                )
                                if (len(locations) != 0):
                                    location = locations[len(
                                        jpg_images_with_words) % len(locations)]

                                if not any(existing[0] == word for existing in jpg_images_with_words):
                                    if location:
                                        jpg_images_with_words.append(
                                            (word, image_url, *
                                             formatted_reserves, location)
                                        )

    if jpg_images_with_words:
        for jpg_images_with_word in jpg_images_with_words:
            query = "INSERT INTO cityviews (id,name, url0, url1, url2, url3, name_sub) VALUES (%s,%s,%s, %s, %s, %s, %s)"
            cursor.execute(query, (city, jpg_images_with_word[0], jpg_images_with_word[1], jpg_images_with_word[2],
                           jpg_images_with_word[3], jpg_images_with_word[4], jpg_images_with_word[5]))
            connection.commit()

    connection.close()
    cursor.close()

    return jpg_images_with_words


@app.route('/')
def index():
    username = session.get('user_id')
    if username:
        welcome_message = f'어서오세요, {username}님'
    else:
        welcome_message = '로그인이 필요합니다.'

    return render_template('index.html', welcome_message=welcome_message)


@app.route('/search', methods=['POST'])
def search():
    city = request.form.get('city')
    hotels = make_response(city)
    username = session.get('user_id')
    if username:
        welcome_message = f'어서오세요, {username}님'
    else:
        welcome_message = '로그인이 필요합니다.'

    connection = get_db_connection()
    cursor = connection.cursor()

    query = "INSERT INTO up_searching (city_name) VALUES (%s)"
    cursor.execute(query, (city,))
    connection.commit()
    city_en = translate_city_name_ko_to_en(city)
    return render_template('hotels.html', hotels=hotels, city=city, welcome_message=welcome_message, city_en=city_en)


@app.route('/get-image-path/<city>')
def get_image_path(city):
    connection = get_db_connection()
    cursor = connection.cursor()

    query = "SELECT url FROM images WHERE city_name = %s"
    cursor.execute(query, (city,))

    result = cursor.fetchone()
    if result:
        image_url = result[0]
        return jsonify({'imagePath': image_url})

    rec = "https://kr.trip.com/global-gssearch/searchlist/search?keyword={}&locale=ko-KR&curr=KRW"

    r = requests.get(rec.format(city))
    soup = BeautifulSoup(r.text, 'html.parser')

    script_tag = soup.find('script', attrs={'id': '__NEXT_DATA__'})
    image_url = None

    if script_tag:
        json_data = json.loads(script_tag.string)

        resnew_data = json_data.get('props', {}).get(
            'pageProps', {}).get('resnew', None)

        if resnew_data:
            image_url = None
            for entry in resnew_data['data']:
                for item in entry['itemList']:
                    if 'imageUrl' in item and item['imageUrl'].endswith('.jpg'):
                        image_url = item['imageUrl']
                        break
                if image_url:
                    break
        else:
            print(f"No 'resnew' data found for city: {city}")
    if image_url:
        query = "INSERT INTO images (city_name, url) VALUES (%s, %s)"
        cursor.execute(query, (city, image_url))
        connection.commit()
    else:
        image_url = "default_image.jpg"
    cursor.close()
    connection.close()

    return jsonify({'imagePath': image_url})


@app.route('/cluster_info')
def contact():
    map = cluster_map()
    username = session.get('user_id')
    if username:
        welcome_message = f'어서오세요, {username}님'
    else:
        welcome_message = '로그인이 필요합니다.'
    return render_template('cluster_info.html', welcome_message=welcome_message, map=map)


@app.route('/tour_city/<city>')
def tour_city(city):
    hotels = make_response(city)
    username = session.get('user_id')
    if username:
        welcome_message = f'어서오세요, {username}님'
    else:
        welcome_message = '로그인이 필요합니다.'

    connection = get_db_connection()
    cursor = connection.cursor()

    query = "INSERT INTO up_searching (city_name) VALUES (%s)"
    cursor.execute(query, (city,))
    connection.commit()
    city_en = translate_city_name_ko_to_en(city)
    return render_template('hotels.html', hotels=hotels, city=city, welcome_message=welcome_message, city_en=city_en)


@app.route('/tour_info')
def tour_info():
    username = session.get('user_id')
    if username:
        welcome_message = f'어서오세요, {username}님'
    else:
        welcome_message = '로그인이 필요합니다.'

    src = request.args.get('src')
    sname = request.args.get('sname')
    nname = request.args.get('nname')
    city_name = request.args.get('city_name')
    return render_template('tour_info.html', welcome_message=welcome_message, src=src, sname=sname, nname=nname, username=username, city_name=city_name)


@app.route('/submit_rating', methods=['POST'])
def submit_rating():
    data = request.json

    hotel_name = data['hotel_name']
    city_name = data['city_name']
    rating1 = data['rating1']
    rating2 = data['rating2']
    rating3 = data['rating3']
    rating4 = data['rating4']
    rating5 = data['rating5']

    user_id = session.get('user_id')

    if not user_id:
        return jsonify({'status': 'error', 'message': '로그인이 필요합니다.'}), 403

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM ratings WHERE id = %s AND name = %s", (user_id, hotel_name))
    count = cursor.fetchone()[0]

    if (user_id != 'admin'):
        if count > 0:
            cursor.close()
            conn.close()
            return jsonify({'status': 'error', 'message': '이미 별점을 주셨습니다.'}), 400

    cursor.execute(
        "INSERT INTO ratings (id, city_name,name, rating1,rating2,rating3,rating4,rating5) VALUES (%s, %s, %s, %s, %s, %s, %s,%s)", (user_id, city_name, hotel_name, rating1, rating2, rating3, rating4, rating5))
    conn.commit()

    cursor.close()
    conn.close()

    return jsonify({'status': 'success'})


@app.route('/get_average_rating', methods=['GET'])
def get_average_rating():
    hotel_name = request.args.get('hotel_name')

    connection = get_db_connection()
    cursor = connection.cursor()

    query = "SELECT (rating1 + rating2 + rating3 + rating4 + rating5) / 5 AS average_rating FROM ratings WHERE name = %s"
    cursor.execute(query, (hotel_name,))

    avg_rating = cursor.fetchall()

    rating = 0
    cnt = 0
    result_rating = 0

    if avg_rating:
        for avg in avg_rating:
            avg = round(avg[0], 1)
            rating += avg
            cnt += 1
    if cnt != 0:
        result_rating = round(rating/cnt, 1)

    cursor.close()
    connection.close()

    return jsonify({'rating': result_rating})


@app.route('/get_indi_rating', methods=['GET'])
def get_indi_rating():
    city_name = request.args.get('city_name')
    connection = get_db_connection()
    cursor = connection.cursor()

    query = "SELECT rating1, rating2 , rating3 , rating4 , rating5 FROM ratings WHERE city_name = %s"
    cursor.execute(query, (city_name,))

    result = cursor.fetchall()
    averages = [sum(values) / len(values) for values in zip(*result)]

    plt.figure()
    plt.bar(range(len(averages)), averages, color='#FFCC00')
    plt.xticks([])
    plt.ylim(0, 5)

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)

    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    plt.close()

    cursor.close()
    connection.close()

    return jsonify({'averages': averages, 'image': img_base64})


@app.route('/get_rating', methods=['GET'])
def get_rating():
    hotel_name = request.args.get('hotel_name')
    username = session.get('user_id')

    connection = get_db_connection()
    cursor = connection.cursor()

    query = "SELECT * FROM ratings WHERE id = %s"
    cursor.execute(query, (username,))

    result = cursor.fetchall()

    return jsonify({'result': result})


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()

        if user and user['password'] == password:
            session['user_id'] = user['username']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error_message="사용자 이름 또는 비밀번호가 잘못되었습니다.")

    return render_template('login.html')


@app.route('/logout', methods=['GET'])
def logout():
    session.pop('user_id', None)
    return redirect(url_for('index'))


@app.route('/user_info', methods=['GET'])
def user_info():
    username = session.get('user_id')
    if username:
        welcome_message = f'어서오세요, {username}님'
    else:
        welcome_message = '로그인이 필요합니다.'

    if not username:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if username == 'admin':
        cursor.execute("SELECT * from ratings")
        datas = cursor.fetchall()
        hotel_data = []

        for data in datas[:100]:
            id = data[0]
            city_name = data[1]
            name = data[2]
            rating1 = data[3]
            rating2 = data[4]
            rating3 = data[5]
            rating4 = data[6]
            rating5 = data[7]
            time = data[8]

            query = "SELECT (rating1 + rating2 + rating3 + rating4 + rating5) / 5 AS average_rating FROM ratings WHERE name = %s"
            cursor.execute(query, (name,))

            avg_rating = cursor.fetchall()

            rating = 0
            cnt = 0
            result_rating = 0

            if avg_rating:
                for avg in avg_rating:
                    avg = round(avg[0], 1)
                    rating += avg
                    cnt += 1
            if cnt != 0:
                result_rating = round(rating/cnt, 1)
            hotel_data.append({
                'username': id,
                'name': name,
                'city_name': city_name,
                'rating1': rating1,
                'rating2': rating2,
                'rating3': rating3,
                'rating4': rating4,
                'rating5': rating5,
                'time': time,
                'avg_rating': result_rating
            })

        cursor.close()
        conn.close()

        return render_template('user_info.html', hotel_data=hotel_data, welcome_message=welcome_message, username=username)

    cursor.execute(
        "SELECT name, city_name,rating1, rating2, rating3, rating4, rating5, time FROM ratings WHERE id = %s", (
            username,)
    )

    datas = cursor.fetchall()

    hotel_data = []

    for data in datas:
        name = data[0]
        city_name = data[1]
        rating1 = data[2]
        rating2 = data[3]
        rating3 = data[4]
        rating4 = data[5]
        rating5 = data[6]
        time = data[7]

        query = "SELECT (rating1 + rating2 + rating3 + rating4 + rating5) / 5 AS average_rating FROM ratings WHERE name = %s"
        cursor.execute(query, (name,))

        avg_rating = cursor.fetchall()

        rating = 0
        cnt = 0
        result_rating = 0

        if avg_rating:
            for avg in avg_rating:
                avg = round(avg[0], 1)
                rating += avg
                cnt += 1
        if cnt != 0:
            result_rating = round(rating/cnt, 1)
        hotel_data.append({
            'username': username,
            'name': name,
            'city_name': city_name,
            'rating1': rating1,
            'rating2': rating2,
            'rating3': rating3,
            'rating4': rating4,
            'rating5': rating5,
            'time': time,
            'avg_rating': result_rating
        })

    cursor.close()
    conn.close()

    return render_template('user_info.html', hotel_data=hotel_data, welcome_message=welcome_message, username=username)


@app.route('/get_cities_in_cluster', methods=['GET'])
def get_cities_in_cluster():
    city = request.args.get('city')

    connection = get_db_connection()
    cursor = connection.cursor()
    query = "SELECT * FROM locationdatas WHERE id=%s"
    cursor.execute(query, (city,))
    result = cursor.fetchone()

    map_html = None
    if result:
        latitude = result[1]
        longitude = result[2]
        closest_cluster_id = result[3]
        cities_in_cluster = result[4]
        map_html = result[5]
        image_urls = result[6]

        return jsonify({
            'latitude': latitude,
            'longitude': longitude,
            'cluster_id': closest_cluster_id,
            'cities_in_cluster': cities_in_cluster,
            'map_html': map_html,
            'image_urls': image_urls
        })

    latitude, longitude = no_translate_search(city)
    if (latitude == -1 and longitude == -1):
        latitude, longitude = translate_and_search(city)

    if (latitude == -1 and longitude == -1):
        url = 'https://www.google.co.kr/maps/search/{}'
        r = requests.get(url.format(city))
        soup = BeautifulSoup(r.text, 'html.parser')
        match = re.search(r"@(-?\d+\.\d+),(-?\d+\.\d+)", r.text)

        if match:
            latitude = match.group(1)
            longitude = match.group(2)

    if (latitude != -1 and longitude != -1):
        map_html = create_map(latitude, longitude)

    closest_cluster_id, cities_in_cluster = cluster(
        float(latitude), float(longitude))
    ###########
    image_urls = get_city_images(city)
    image_urls_str = None
    cities_in_cluster_str = ','.join(map(str, cities_in_cluster[:10]))
    if image_urls:
        image_urls_str = ','.join(map(str, image_urls))

    if latitude != -1 and closest_cluster_id and cities_in_cluster_str and map_html and image_urls_str:
        query = "INSERT INTO locationdatas (id, latitude, longitude, closest_cluster_id , cities_in_cluster ,map_html  , image_urls ) VALUES (%s,%s,%s, %s, %s, %s, %s)"
        cursor.execute(query, (city, latitude, longitude, closest_cluster_id,
                               cities_in_cluster_str, map_html, image_urls_str))
        connection.commit()

    connection.close()
    cursor.close()

    return jsonify({
        'latitude': latitude,
        'longitude': longitude,
        'cluster_id': closest_cluster_id,
        'cities_in_cluster': cities_in_cluster_str,
        'map_html': map_html,
        'image_urls': image_urls_str
    })


@app.route('/cluster/<number>')
def clusters(number):
    username = session.get('user_id')
    if username:
        welcome_message = f'어서오세요, {username}님'
    else:
        welcome_message = '로그인이 필요합니다.'

    df = pd.read_csv('contents/city_clusters_v.csv',
                     low_memory=False, encoding='ISO-8859-1')

    plt.figure(figsize=(10, 8))
    colors = np.where(df['cluster'] == int(number), '#ff0000', '#808080')
    sizes = np.where(df['cluster'] == int(number), 100, 5)
    plt.scatter(df['longitude'], df['latitude'], c=colors, s=sizes)
    plt.title(f'Cluster Number = {number}')

    cluster_data = df[df['cluster'] == int(number)]
    avg_traditionality = round(cluster_data['traditionality'].mean(), 3)
    avg_cleanliness = round(cluster_data['cleanliness'].mean(), 3)
    avg_security = round(cluster_data['security'].mean(), 3)
    avg_transportation = round(cluster_data['transportation'].mean(), 3)
    avg_low_cost = round(cluster_data['low_cost'].mean(), 3)

    std_traditionality = round(cluster_data['traditionality'].std(), 3)
    std_cleanliness = round(cluster_data['cleanliness'].std(), 3)
    std_security = round(cluster_data['security'].std(), 3)
    std_transportation = round(cluster_data['transportation'].std(), 3)
    std_low_cost = round(cluster_data['low_cost'].std(), 3)

    def plot_to_base64(data, title):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(data)
        ax.set_ylim(0, 5)
        ax.set_xticks([])

        img = BytesIO()
        plt.savefig(img, format='png')
        img.seek(0)
        img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')
        plt.close(fig)
        return img_base64

    img_traditionality = plot_to_base64(
        cluster_data['traditionality'], 'Traditionality')
    img_cleanliness = plot_to_base64(
        cluster_data['cleanliness'], 'Cleanliness')
    img_security = plot_to_base64(cluster_data['security'], 'Security')
    img_transportation = plot_to_base64(
        cluster_data['transportation'], 'Transportation')
    img_low_cost = plot_to_base64(cluster_data['low_cost'], 'Low Cost')

    img = BytesIO()
    plt.savefig(img, format='png')
    img.seek(0)
    img_base64 = base64.b64encode(img.getvalue()).decode('utf-8')

    cities_in_cluster = get_cities_in_cluster_only_str(number)

    return render_template(
        'cluster.html',
        img_data=img_base64,
        img_traditionality=img_traditionality,
        img_cleanliness=img_cleanliness,
        img_security=img_security,
        img_transportation=img_transportation,
        img_low_cost=img_low_cost,
        cluster_number=number,
        welcome_message=welcome_message,
        cities_in_cluster=cities_in_cluster,
        avg_traditionality=avg_traditionality,
        avg_cleanliness=avg_cleanliness,
        avg_security=avg_security,
        avg_transportation=avg_transportation,
        avg_low_cost=avg_low_cost,
        std_traditionality=std_traditionality,
        std_cleanliness=std_cleanliness,
        std_security=std_security,
        std_transportation=std_transportation,
        std_low_cost=std_low_cost
    )


@app.route('/userinfo/<number>', methods=['GET'])
def more(number):
    username = session.get('user_id')
    if username:
        welcome_message = f'어서오세요, {username}님'
    else:
        welcome_message = '로그인이 필요합니다.'

    if not username:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    if username != 'admin':
        return

    cursor.execute("SELECT * from ratings")
    datas = cursor.fetchall()
    hotel_data = []

    for data in datas[number:number+100]:
        id = data[0]
        name = data[1]
        rating1 = data[2]
        rating2 = data[3]
        rating3 = data[4]
        rating4 = data[5]
        rating5 = data[6]
        time = data[7]

        query = "SELECT (rating1 + rating2 + rating3 + rating4 + rating5) / 5 AS average_rating FROM ratings WHERE name = %s"
        cursor.execute(query, (name,))

        avg_rating = cursor.fetchall()

        rating = 0
        cnt = 0
        result_rating = 0

        if avg_rating:
            for avg in avg_rating:
                avg = round(avg[0], 1)
                rating += avg
                cnt += 1
        if cnt != 0:
            result_rating = round(rating/cnt, 1)
        hotel_data.append({
            'username': id,
            'name': name,
            'rating1': rating1,
            'rating2': rating2,
            'rating3': rating3,
            'rating4': rating4,
            'rating5': rating5,
            'time': time,
            'avg_rating': result_rating
        })

    cursor.close()
    conn.close()

    return render_template('user_info.html', hotel_data=hotel_data, welcome_message=welcome_message, username=username)


@app.route('/recommend_cluster', methods=['GET'])
def recommend_cluster():
    username = session.get('user_id')
    if username:
        welcome_message = f'어서오세요, {username}님'
    else:
        welcome_message = '로그인이 필요합니다.'

    return render_template('recommend_cluster.html', welcome_message=welcome_message)


@app.route('/get_cluster_weight', methods=['POST'])
def get_cluster_weight():
    data = request.get_json()
    username = session.get('user_id')

    bias = data.get('weight_bias')

    user_bias = []
    for bia in bias:
        user_bias.append(float(bia))

    df = pd.read_csv('contents/city_clusters_v.csv',
                     encoding='utf-8', low_memory=False)

    u0 = user_bias[0]
    u1 = user_bias[1]

    if float(user_bias[0]) < 0:
        user_bias[0] = -math.sqrt(abs(float(user_bias[0])))
    else:
        user_bias[0] = math.sqrt(float(user_bias[0]))

    if float(user_bias[1]) < 0:
        user_bias[1] = -math.sqrt(abs(float(user_bias[1])))
    else:
        user_bias[1] = math.sqrt(float(user_bias[1]))

    scaler = StandardScaler()
    latitude_longitude = df[['latitude', 'longitude']].copy()

    df[['latitude', 'longitude']] = scaler.fit_transform(
        df[['latitude', 'longitude']])

    def safe_sqrt(x):
        sign = np.sign(x)
        return sign * np.sqrt(np.abs(x))

    df['latitude'] = df['latitude'].map(safe_sqrt)
    df['longitude'] = df['longitude'].map(safe_sqrt)

    df_weighted = df.copy()

    cluster_means = df_weighted.groupby('cluster')[
        ['latitude', 'longitude', 'traditionality', 'cleanliness', 'security', 'transportation', 'low_cost']].mean()

    distances = np.linalg.norm(cluster_means - user_bias, axis=1)

    df[['latitude', 'longitude']] = latitude_longitude
    user_bias[0] = u0
    user_bias[1] = u1
    top_5_clusters = distances.argsort()[:5].tolist()

    connection = get_db_connection()
    cursor = connection.cursor()
    if (username):
        query = "INSERT  INTO user_like (id,lat,lon,bias0,bias1,bias2,bias3,bias4,cluster1,cluster2,cluster3,cluster4,cluster5) VALUES ( %s, %s, %s, %s, %s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(
            query, (username, user_bias[0], user_bias[1], user_bias[2], user_bias[3], user_bias[4], user_bias[5], user_bias[6], top_5_clusters[0], top_5_clusters[1], top_5_clusters[2], top_5_clusters[3], top_5_clusters[4]))
        connection.commit()

    connection.close()
    cursor.close()

    return jsonify(top_5_clusters)


@app.route('/user_like', methods=['GET', 'POST'])
def user_like():
    username = session.get('user_id')
    if username:
        welcome_message = f'어서오세요, {username}님'
    else:
        welcome_message = '로그인이 필요합니다.'

    if not username:
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM user_like WHERE id = %s", (
            username,)
    )

    datas = cursor.fetchall()

    results = []

    for data in datas:
        result = []
        for i in range(len(data)):
            if 13 > i and i > 7:
                result.append('.'+str(data[i]))
            else:
                result.append(data[i])
        results.append(result)

    cursor.close()
    conn.close()

    return render_template('user_like.html', welcome_message=welcome_message, results=results, username=username)


@app.route('/clear_user_like', methods=['GET'])
def clear_user_like():
    username = request.args.get('name')
    connection = get_db_connection()
    cursor = connection.cursor()

    query = "DELETE FROM user_like WHERE id = (%s);"
    cursor.execute(query, (username,))
    connection.commit()

    return jsonify()


@app.route('/up_searching', methods=['GET'])
def up_searching():
    username = session.get('user_id')
    if username:
        welcome_message = f'어서오세요, {username}님'
    else:
        welcome_message = '로그인이 필요합니다.'

    connection = get_db_connection()
    cursor = connection.cursor()
    query = "select * from up_searching;"

    df = pd.read_sql(query, connection)
    top_10_cities = df['city_name'].value_counts().head(20)
    a = top_10_cities.tolist()
    b = top_10_cities.index.tolist()
    result = [[city, number] for city, number in zip(b, a)]

    query = "SELECT city_name, MAX(time) AS latest_time FROM up_searching GROUP BY city_name ORDER BY latest_time DESC LIMIT 20"
    cursor.execute(query)
    recent = cursor.fetchall()

    return render_template('up_searching.html', welcome_message=welcome_message, results=result, recents=recent)


@app.route('/get_translate_en_to_ko', methods=['GET'])
def get_translate_en_to_ko():
    city_names = request.args.get('city_names').split('@')
    result = []
    for city_name in city_names:
        city_tr = translate_city_name_en_to_ko(city_name)
        result.append(city_tr)
    return (jsonify(result))


@app.route('/get_translate_en_to_ko_just', methods=['GET'])
def get_translate_en_to_ko_just():
    city_names = request.args.get('city_names').split(',')
    result = []
    for city_name in city_names:
        city_tr = translate_city_name_en_to_ko(city_name)
        result.append(city_tr)
    return (jsonify(result))


@app.route('/get_map_only', methods=['GET'])
def get_map_only():
    city_name = request.args.get('city_name')

    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT map_url from get_map WHERE city_name = %s"
    cursor.execute(query, (city_name,))
    result = cursor.fetchone()

    if result:
        return jsonify({'url': result})

    city_en = translate_city_name_ko_to_en(city_name)
    lat, lon = get_lat_lon(city_en)
    if (lat == -1 and lon == -1):
        lat, lon = get_lat_lon(city_name)
    url = create_map(lat, lon)

    query = "INSERT INTO get_map (city_name,map_url) VALUES (%s,%s)"
    cursor.execute(query, (city_name, url))
    conn.commit()

    return jsonify({
        'url': url
    })


if __name__ == '__main__':
    app.run(debug=True)
