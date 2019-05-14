import argparse
import os
import time

import dateutil.parser
import feedparser
from pymongo import MongoClient

mongo_host = os.getenv('MONGO_HOST') or 'localhost'
polling_period = int(os.getenv('POSTS_POLLING_PERIOD') or '600')


def delete_older_than(hours, db):
    t = time.time()
    db['posts'].delete_many({'posted_at': {'$lt': t - (3600 * hours)}})
    mongo.close()


# logging.basicConfig(
#    filename='rss-client.log',
#    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
#    level=logging.DEBUG
#    )
parser = argparse.ArgumentParser()

parser.add_argument("--purge", help="Delete all stored posts", action='store_true')

args = parser.parse_args()

if args.purge:
    mongo = MongoClient(mongo_host)
    db = mongo['elmundoes-bot']
    db['posts'].delete_many({})
    db['comments'].delete_many({})
    mongo.close()

while True:
    mongo = MongoClient(mongo_host)
    db = mongo['elmundoes-bot']

    delete_older_than(12, db)

    feed = feedparser.parse('https://e00-elmundo.uecdn.es/elmundo/rss/portada.xml')
    for item in feed.entries:
        post = db['posts'].find_one({'url': item.link})
        if post is None:
            post = {
                'title': item.title,
                'url': item.link,
                'comment_count': 0,
                'posted_at': int(dateutil.parser.parse(item.published).timestamp())
            }
            print(post['url'])
            if post['posted_at'] > (time.time() - 12 * 3600):
                db['posts'].insert_one(post)
    mongo.close()
    time.sleep(polling_period)
