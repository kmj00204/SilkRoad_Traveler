pip install math decimal datetime matplotlib base64 geopy googletrans Flask mysql-connector-python mtranslate folium scikit-learn requests beautifulsoup4 aiohttp googlemaps pandas numpy



CREATE TABLE cityviews (
    id VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    url0 TEXT,
    url1 TEXT,
    url2 TEXT,
    url3 TEXT,
    name_sub VARCHAR(255)
);

CREATE TABLE images (
    city_name VARCHAR(255) NOT NULL,
    url VARCHAR(255) NOT NULL
);

CREATE TABLE locationdatas (
    id VARCHAR(255) DEFAULT NULL,
    latitude FLOAT DEFAULT NULL,
    longitude FLOAT DEFAULT NULL,
    closest_cluster_id INT DEFAULT NULL,
    cities_in_cluster TEXT DEFAULT NULL,
    map_html TEXT DEFAULT NULL,
    image_urls TEXT DEFAULT NULL
);

CREATE TABLE ratings (
    id VARCHAR(255) DEFAULT NULL,
    city_name VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    rating1 INT DEFAULT NULL,
    rating2 INT DEFAULT NULL,
    rating3 INT DEFAULT NULL,
    rating4 INT DEFAULT NULL,
    rating5 INT DEFAULT NULL,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE up_searching (
    city_name VARCHAR(255) DEFAULT NULL,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE user_like (
    id VARCHAR(255) NOT NULL,
    lat FLOAT DEFAULT NULL,
    lon FLOAT DEFAULT NULL,
    bias0 FLOAT DEFAULT NULL,
    bias1 FLOAT DEFAULT NULL,
    bias2 FLOAT DEFAULT NULL,
    bias3 FLOAT DEFAULT NULL,
    bias4 FLOAT DEFAULT NULL,
    cluster1 INT DEFAULT NULL,
    cluster2 INT DEFAULT NULL,
    cluster3 INT DEFAULT NULL,
    cluster4 INT DEFAULT NULL,
    cluster5 INT DEFAULT NULL,
    time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);


CREATE TABLE users (
    id INT NOT NULL AUTO_INCREMENT,
    username VARCHAR(255) NOT NULL,
    password VARCHAR(255) NOT NULL,
    PRIMARY KEY (id),
    UNIQUE KEY unique_username (username)
);
