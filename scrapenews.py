'''
App for scraping news articles.
Saves Json Files In Output Directory
Saves Data In MongoDB in news_db --> news
'''

#Imports & Basic Config
import pandas as pd
from newspaper import Article
from bs4 import BeautifulSoup
import requests
import re
from datetime import datetime, date
import time
from pathlib import Path
import argparse
import json
from pymongo import MongoClient
import logging

parser = argparse.ArgumentParser(description='News Paper Scrapping Script')
parser.add_argument('--output_dir', default='output/', type=Path, help='save json file here')
parser.add_argument('--source_path', default='./news_source.txt', type=Path, help='Sources to be scrapped')
parser.add_argument('--total_symbols', default=5, type=int, help='Total Symbols to be scraped')
args = parser.parse_args()
logging.basicConfig(filename='app.log', filemode='a', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',level=logging.DEBUG,datefmt='%d-%b-%y %H:%M:%S')


def initialize_app():

	'''
	Setting up app configuration
	Returns output directory, pymongo objects, save directory and sources to scrape from
	'''
	
	output_dir = args.output_dir
	source_path = args.source_path
	total_symbols = args.total_symbols
	output_dir.mkdir(parents=True, exist_ok=True)
	with open (source_path, 'r') as f:
		source_temp_file = f.readlines()
	source_file = []
	for source_names in source_temp_file:
		source_file.append(str(source_names).strip().lower())

	client = MongoClient('localhost', 27017)
	db = client['news_db']
	collection_news = db['news']
	today = date.today()
	today.strftime("%m/%d/%y")
	today = ''.join(str(today).split('/'))
	savedir = output_dir.joinpath(today)
	savedir.mkdir(parents=True, exist_ok=True)
	news_id = 0
	all_articles = {}
	return output_dir, client, collection_news, savedir, news_id, all_articles, source_file


def get_symbols():

	'''
	Loads symbol file
	Returns list of all the symbols
	'''
	
	try:
		total_symbols = args.total_symbols
		symboldf = pd.read_csv('symbols.csv')
		news_to_scrape = {}
		symbols = symboldf['symbol'].tolist()
		if(total_symbols > len(symbols)):
			total_symbols = len(symbols)
		symbols = symbols[0:total_symbols]
		logging.debug('Total Symbols to be scrapped '+ str(len(symbols)))
		return symbols
	except:
		logging.exception('Reading Symbol File Failed!')

def getlink(extension, source):

	'''
	Returns the link to scrape
	Input: security, source
	Output: Link to scrape
	'''

	try:
		if(source == 'yahoo'):
			link = 'https://in.finance.yahoo.com/quote/'+extension+'/news?p='+extension
		elif(source == 'cnn'):
			link = 'https://money.cnn.com/quote/news/news.html?symb='+extension
		elif(source == 'reuters'):
			link = 'https://www.reuters.com/companies/'+extension+'.N/news'
		return link

	except:
		logging.exception('Scrapping News Link Failed!')



def parse_html(soup, source):

	'''
	Extracts the links from HTML page
	Input: BS4 object, news source
	Output: List of links to scrape
	'''

	symbol_link = []
	if(source == 'yahoo'):
		h3divs = soup.findAll("h3", {"class": "Mb(5px)"})
		for tag in h3divs:
			links = [a.attrs.get('href') for a in tag.select('a')]
			symbol_link.append(links[0])

	if(source == 'cnn'):
		table_div = soup.findAll("table", {"class": "wsod_newsTable"})[0]
		symbol_link = [a.attrs.get('href') for a in table_div.select('a')]

	if(source == 'reuters'):
		news_div = soup.findAll("div", {"class": "MarketStoryItem-container-3rpwz"})
		for tag in news_div:
			links = [a.attrs.get('href') for a in tag.select('a')]
			for ind_link in links:
				symbol_link.append(ind_link)
	return symbol_link


def get_links_to_scrape(symbols, source):
	
	'''
	Scrapes the page to get the article links
	Input: List of symbols to scrape
	Returns dictionary with symbols as keys and links as value
	'''
	news_to_scrape = {}
	for extension in symbols:
		try:
			symbol_link = []
			link_to_scrape = getlink(extension, source)
			# link_to_scrape =  'https://in.finance.yahoo.com/quote/'+extension+'/news?p='+extension
			response = requests.get(link_to_scrape)
			soup = BeautifulSoup(response.text, 'lxml')
			symbol_link = parse_html(soup, source)
			# h3divs = soup.findAll("h3", {"class": "Mb(5px)"})
			# for tag in h3divs:
			# 	links = [a.attrs.get('href') for a in tag.select('a')]
			# 	symbol_link.append(links[0])
			news_to_scrape[extension] = symbol_link
		except:
			logging.exception('Finding links to srape for security Failed!')
			continue
	return news_to_scrape


def scrape_articles(news_to_scrape, client, collection_news, savedir, news_id, all_articles, source):

	'''
	Scrapes Articles
	Input: dictionary of links, pymongo objects, save directory
	'''

	try:
		if source == 'yahoo':
			base_link = 'https://in.finance.yahoo.com/'
		elif source == 'cnn':
			base_link = ''
		elif source == 'reuters':
			base_link = ''
		jsonfile = {}
		for extension, news_articles_symbols in news_to_scrape.items():
			for news_article in news_articles_symbols:
				try:
					news_id+=1
					jsonfile = {}
					to_scrape = base_link+news_article
					article = Article(to_scrape)
					article.download()
					article.parse()
					jsonfile['security'] = extension
					jsonfile['_id'] = str(time.time()).split('.')[1]
					jsonfile['current_date'] = str(datetime.now())
					jsonfile['source'] = source
					jsonfile['authors'] =  article.authors
					jsonfile['published_date_time'] = str(article.publish_date)
					jsonfile['title'] = article.title
					# jsonfile['text'] = article.text
					article.nlp()
					jsonfile['keywords'] = article.keywords
					all_articles[news_id] = jsonfile
					dump_file_path = savedir.joinpath(extension+'_'+str(time.time()).split('.')[0]+'_'+str(time.time()).split('.')[1]+'.json')	
				except:
					logging.info('--------Source - '+source+str(news_id)+'-------')
					logging.warning('Link could not be scrapped - '+to_scrape)
					continue

				try:
					with open(dump_file_path, 'w') as f:
						json.dump(jsonfile, f)
				except:
					logging.exception('Storing json file to output directory failed!')


				try:
					_id = collection_news.insert_one(jsonfile)
				except:
					logging.exception('Storing to mongodb failed!')
		return all_articles, news_id

	except:
		logging.exception('Scrapping News Link Failed')

def getstatistics(all_articles):

	'''
	Saves the statistics in statistics.txt file
	Input: All the scrapped articles
	'''

	total_articles = len(all_articles.keys())
	source_count = {}
	security_count = {}
	for key, article in all_articles.items():
		try:
			source = article['source']
			if(source in source_count):
				source_count[source] += 1
			else:
				source_count[source] = 1

			security = article['security']
			if(security in security_count):
				security_count[security] += 1
			else:
				security_count[security] = 1
		except:
			logging.exception('Could Not Find Statistics For Key - '+str(key))

	try:
		today = date.today()
		today.strftime("%m/%d/%y")
		today = ''.join(str(today).split('/'))
		with open('./statistics.txt', 'a') as f:
			f.write('----------------------------------------'+'\n')
			f.write('Statistics - '+today+'\n')
			f.write('----------------------------------------'+'\n')
			f.write('Source Statistics: \n')
			for key, value in source_count.items():
				f.write(str(key)+': '+str(value)+'\n')

			f.write('Security Statistics: \n')
			for key, value in security_count.items():
				f.write(str(key)+': '+str(value)+'\n')
	except:
		logging.exception('Could Not Write Statistics!')







def news_scrape_pipeline():
	
	'''
	Main Pipeline
	'''
	
	logging.info('Started Configuration...')
	output_dir, client, collection_news, savedir, news_id, all_articles, source_file = initialize_app()
	logging.info('Configuration Done')
	symbols = get_symbols()
	logging.info('Symbol File Read')

	#Yahoo
	if('yahoo' in source_file):
		news_to_scrape = get_links_to_scrape(symbols, 'yahoo')
		logging.info('Links to be scrapped Ready')
		all_articles, news_id = scrape_articles(news_to_scrape, client, collection_news, savedir, news_id, all_articles, 'yahoo')

	#Reuters
	if('reuters' in source_file):
		news_to_scrape = get_links_to_scrape(symbols, 'reuters')
		logging.info('Links to be scrapped Ready')
		all_articles, news_id = scrape_articles(news_to_scrape, client, collection_news, savedir, news_id, all_articles, 'reuters')

	#CNN
	if('cnn' in source_file):
		news_to_scrape = get_links_to_scrape(symbols, 'cnn')
		logging.info('Links to be scrapped Ready CNN')
		all_articles, news_id = scrape_articles(news_to_scrape, client, collection_news, savedir, news_id, all_articles, 'cnn')

	getstatistics(all_articles)
	logging.info('Process Completed!')
	return json.dumps(all_articles)


if __name__ == '__main__':
	print("Writing Logs to app.log, Please refer the logs for checking the progress!")
	all_articles = news_scrape_pipeline()