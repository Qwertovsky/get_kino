#!/usr/bin/python
from BeautifulSoup import BeautifulSoup
from requests import Session
from random import randint
from time import sleep
import argparse
import sqlite3

parser = argparse.ArgumentParser(description='Get rates for movies from kinopoisk.')
parser.add_argument('user_id', type=int, help='user_id for kinopoisk home page')
args = parser.parse_args()

# Preparations
user_url = 'http://www.kinopoisk.ru/user/' + str(args.user_id) + '/'
initial = 0

# Create database if doesn't exist
conn = sqlite3.connect('kinopoisk.db')
c = conn.cursor()
sql = """create table if not exists kinopoisk (
         ID         INT  PRIMARY KEY,
         NAME       TEXT NOT NULL,
         ALTNAME    TEXT,
         IMAGE      TEXT,
         KINORATING REAL,
         USERRATING REAL,
         INFO       TEXT,
         LINK       TEXT
)"""
c.execute(sql)

# Headres for Session
headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'deflate',
    'Host': 'www.kinopoisk.ru',
    'Referer': user_url,
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:38.0) Gecko/20100101 Firefox/38.0 Iceweasel/38.0.1',
    'X-Requested-With': 'XMLHttpRequest'
    }

# Start initial session
session = Session()


def get_page(num):
    '''function to retrieve page'''
    session.head(user_url)
    session.get('http://www.kinopoisk.ru/user/activity-status/?_=1444396565940')
    response = session.get(
        url=user_url + '?page=' + str(num) + '&chunkOnly=1&_=1444396565941',
        headers={'Referer': user_url}
    )
    return response.text

# Start retrieving pages until it will return no info about movies
while next:
    next = False
    initial = initial + 1
    if initial > 1:
        sleep(randint(3, 10))
    page = BeautifulSoup(get_page(initial))
    for film in page.body.findAll('div', attrs={'itemtype': 'http://schema.org/Movie'}):
        name = film.find('meta', attrs={'itemprop': 'name'}).get('content')
        altname = film.find('meta', attrs={'itemprop': 'alternateName'}).get('content')
        # sometimes image is missing :)
        try:
            image = film.find('img', attrs={'class': 'image image_picture film-snippet__image i-bem'}).get('src')
        except AttributeError:
            image = ""
        # sometimes there is movies without rating. strange but we need to
        # process exception here
        try:
            kinorating = film.find('div', attrs={'itemprop': 'ratingValue'}).text
        except AttributeError:
            kinorating = 0
        userrating = film.find('div', attrs={'class': 'film-snippet__user-rating-rate'}).text
        info = film.find('div', attrs={'class': 'film-snippet__info'}).text
        link = film.find('a', attrs={'class': 'link film-snippet__media-content'}).get('href')
        sql = """insert into kinopoisk (name, altname, image, kinorating, userrating, info, link)
                 values ("%s", "%s", "%s", %s, %s, "%s", "%s");""" % (name, altname, image, kinorating, userrating, info, link)
        c.execute(sql)
        # we need to have some rest. it's gonna be a long way :)
        next = True

conn.commit()
c.execute("select count(id) from kinopoisk;")
