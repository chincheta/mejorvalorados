import collections
import logging
import os
import time
from datetime import datetime

from pymongo import MongoClient

import common
from secrets import get_secret
from bs4 import BeautifulSoup


def delete_older_than(hours, db):
    t = time.time()
    db['comments'].delete_many({'posted_at': {'$lt': t - 3600 * hours}})


def get_comments(url):
    comments = []

    disqus_comments = common.fetch_okdiariocom_comments(url, disqus_key)

    for disqus_comment in disqus_comments:
        # Workaround to stop bug. TODO: Fix it!
        if isinstance(disqus_comment, collections.Mapping):
            if disqus_comment['parent'] is None:
                body = ' '.join(disqus_comment['raw_message'].replace('\n', ' ').replace('\r', '').split())
                body = BeautifulSoup(body, "html.parser").text
                if common.is_comment_ok_for_twitter(body):
                    comment = {
                        'comment_id': disqus_comment['id'],
                        'url': url,
                        'post_id': disqus_comment['thread'],
                        'posted_at': common.dt2ts(datetime.fromisoformat(disqus_comment['createdAt'])),
                        'ups': disqus_comment['likes'],
                        'downs': disqus_comment['dislikes'],
                        'heat': 0,
                        'body': body
                    }
                    comments.append(comment)
    return comments


disqus_key = get_secret('DISQUS_API_KEY')

mongo_host = os.getenv('MONGO_HOST') or 'localhost'

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO
)

while True:
    mongo = MongoClient(mongo_host)
    db = mongo['okdiariocom-bot']
    delete_older_than(12, db)

    new_comment_count = 0
    post_count = 0
    for post in db['posts'].find():
        post_count = post_count + 1
        comments = get_comments(post['url'])

        for comment in comments:
            query = db['comments'].find_one({'comment_id': comment['comment_id'], 'post_id': comment['post_id']})
            if query is None:
                if comment['posted_at'] > (time.time() - 12 * 3600):
                    logging.info('New comment: ' + comment['body'])
                    db['comments'].insert_one(comment)
                    new_comment_count = new_comment_count + 1
    mongo.close()
    logging.info(str(new_comment_count) + ' new comments found. ' + str(post_count) + ' posts processed.')
    time.sleep(13 * 60)
