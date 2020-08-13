from flask import Flask
from scrapenews import news_scrape_pipeline
import logging

app = Flask(__name__)
app.secret_key ="IntelliMind_News"



@app.route('/getnews', methods=["GET", "POST"])
def getnews():
	logging.info("Server Hit")
	all_articles = news_scrape_pipeline()
	return all_articles





if __name__ == '__main__':
   app.run(debug = True)
