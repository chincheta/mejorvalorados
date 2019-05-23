import argparse
import logging
import os
import time

import dateutil.parser
import feedparser
from pymongo import MongoClient

mongo_host = os.getenv('MONGO_HOST') or 'localhost'


def delete_older_than(hours, db):
    t = time.time()
    db['posts'].delete_many({'posted_at': {'$lt': t - (3600 * hours)}})


logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO
)

parser = argparse.ArgumentParser()

parser.add_argument("--purge", help="Delete all stored posts", action='store_true')

args = parser.parse_args()

if args.purge:
    mongo = MongoClient(mongo_host)
    db = mongo['elpaiscom-bot']
    db['posts'].delete_many({})
    db['comments'].delete_many({})
    mongo.close()

while True:
    mongo = MongoClient(mongo_host)
    db = mongo['elpaiscom-bot']

    delete_older_than(12, db)

    feed = feedparser.parse('http://elpais.com/rss/elpais/portada.xml')
    post_count = len(feed.entries)
    new_post_count = 0
    for item in feed.entries:
        head, sep, tail = item.link.partition('?')
        url = head.replace('#', '')
        post = db['posts'].find_one({'url': url})
        if post is None:
            post = {
                'title': item.title,
                'url': url,
                'comment_count': 0,
                'posted_at': int(dateutil.parser.parse(item.published).timestamp())
            }
            if post['posted_at'] > (time.time() - 12 * 3600):
                db['posts'].insert_one(post)
                new_post_count = new_post_count + 1
                logging.info('New post: ' + url)
    mongo.close()
    logging.info(str(post_count) + ' posts processed. ' + str(new_post_count) + ' new.')
    time.sleep(15 * 60)
