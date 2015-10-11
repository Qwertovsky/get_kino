#!/usr/bin/python
from bs4 import BeautifulSoup
from requests import Session
import argparse
import sqlite3
import json
import urllib

parser = argparse.ArgumentParser(description='Get rates for movies from kinopoisk.')
parser.add_argument('inputfile', type=str, help='file from kinopoisk user ratings')
parser.add_argument('outputfile', type=str, help='SQLite DB file')
parser.add_argument('--from', dest="fromIndex", type=int, default=1, help='begin from film with this index in list', required=False)
parser.add_argument('-d', dest="dropBase", action="store_const", help='delete exists db', const=True)
args = parser.parse_args()

 

# Create database
conn = sqlite3.connect(args.outputfile)
c = conn.cursor()
if (args.dropBase or args.fromIndex == 1):
	sql = """drop table if exists kinopoisk"""
	c.execute(sql)
sql = """create table if not exists kinopoisk (
		 ID         INT  PRIMARY KEY,
		 IMDB_ID	TEXT,
		 NAME       TEXT NOT NULL,
		 ALTNAME    TEXT,
		 IMAGE      TEXT,
		 KINORATING REAL,
		 USERRATING REAL,
		 INFO       TEXT,
		 LINK       TEXT,
		 IMDB_LINK	TEXT,
		 IMDB_CREDITS	TEXT
)"""
c.execute(sql)

# Start initial session
session = Session()


def get_imdb(name, year):
	title = urllib.quote(name.encode('utf8'))
	imdbUrl = 'http://www.imdb.com/search/title?release_date=' + str(year) + ',' + str(year+2) \
		+ '&title=' + title
	print imdbUrl
	response = session.get(imdbUrl)
	return parse_imdb(response.text)
    
def parse_imdb(html):
	page = BeautifulSoup(html, 'html.parser')
	results = page.find('table', class_='results')
	if results is not None:
		title = results.find('td', class_='title')
		imdb['id'] = title.find('span', class_='wlb_wrapper')['data-tconst']
		imdb['credit'] = title.find('span', class_='credit').text.strip()
		imdb['link'] = 'http://www.imdb.com/title/' + imdb['id']
		return imdb
	return -1

# Open page
page = BeautifulSoup(open(args.inputfile), 'html.parser')
filmSnippets = page.body.select('div.film-snippet')
filmsCount = len(filmSnippets)
print 'Ratings: ' + str(len(filmSnippets))

if (args.fromIndex > filmsCount):
	print 'Start film index is out of range. Set value from 1 up to ' + str(filmsCount)
	exit(-1)

# Start parse movies
start = 1
if args.fromIndex > 1:
	start = args.fromIndex
print 'Start parsing from ' + str(start)
for index in range(start, filmsCount+1):
	print ''
	filmSnippet = filmSnippets[index-1]
	film = {}
	filmDataBem = json.loads(filmSnippet['data-bem'])
	film['movieId'] = filmDataBem.get('film-snippet').get('movieId')
	film['name'] = filmSnippet.find('meta', attrs={'itemprop': 'name'}).get('content')
	
	print str(index) + ': ' +  film['name']
	try:
	    film['altname'] = filmSnippet.find('meta', attrs={'itemprop': 'alternateName'}).get('content')
	except AttributeError:
	    film['altname'] = ''
	try:
	    film['image'] = filmSnippet.find('img', class_='film-snippet__image').get('src')
	except AttributeError:
	    film['image'] = ""
	try:
	    film['kinorating'] = filmSnippet.find('div', attrs={'itemprop': 'ratingValue'}).text
	except AttributeError:
	    film['kinorating'] = -1
	try:
		film['userrating'] = filmSnippet.find('div', attrs={'class': 'film-snippet__user-rating-rate'}).text
		if film['userrating'] == '':
			film['userrating'] = 0
	except AttributeError:
	    film['userrating'] = -1
	film['info'] = filmSnippet.find('div', attrs={'class': 'film-snippet__info'}).text
	film['link'] = "http://www.kinopoisk.ru/%s" % (film['movieId'])
	
	# Add IMDb data
	imdb = {"id":"", "link":"", "credit":""}
	if (len(film['altname']) > 0 and film['altname'] != film['name']):
		imdb_result = get_imdb(film['altname'], int(film['info'][-4:]))
		if imdb_result == -1:
			print 'Not found on IMDb: ' + film['link']
		else:
			imdb = imdb_result
			print 'Found IMDb: ' + imdb['link']
			print imdb['credit']
	else:
		print "Impossible find on IMDb: " + film['link']
		
	# Save data
	sql = """insert into kinopoisk (id, imdb_id, name, altname, image, 
		kinorating, userrating, info, link, imdb_link, imdb_credits)
		 values (%s, "%s", "%s", "%s", "%s", %s, %s, "%s", "%s", "%s", "%s");""" % (
		 film['movieId'], imdb['id'], film['name'], film['altname'], film['image'], 
		 film['kinorating'], film['userrating'], film['info'], film['link'], imdb['link'], imdb['credit'])
	c.execute(sql)
	conn.commit()


