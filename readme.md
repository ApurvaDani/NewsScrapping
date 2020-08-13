# News Feed System

# Get Started:

## Directory Structure:

```
newsfeed
	|
	|-----scrapenews.py
	|-----newsapp.py
	|-----app.log
	|-----newsfeed.sh
	|-----news_server.sh
	|-----readme.md
	|-----symbols.csv
	|-----statistics.txt
```

```
pip install -r requirements.txt
```

## To scrape news and store json files in your output directory and MongoDB
```
sh newsfeed.sh
```

Configuration Available:
```
output_dir="./newsoutput"
source_dir="./news_source.txt"
total_symbols=4
```

To change your output directory change the output_dir variable in newsfeed.sh.
To change news sources modify the file news_source.txt from the below options.
To modify the number of symbols for which you want to scrape data, modify total_symbols variable in newsfeed.sh.

Note: App is compatible to scrape news from three websites:
```
Reuters
CNN
Yahoo
```

It will store json files in the output directory provided.
And will store data in MongoDB in database 'news_db' and container 'news'

## Start Flask Server
```
sh news_server.sh
``` 

Api hosted at:
```
http://localhost:5000/getnews
```

You can send requests to the above link to check the output.


