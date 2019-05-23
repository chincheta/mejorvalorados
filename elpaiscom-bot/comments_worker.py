import logging
import os
import random
import time

import requests
from pymongo import MongoClient

import common

random.seed(time.time())


def delete_older_than(hours, db):
    t = time.time()
    db['comments'].delete_many({'posted_at': {'$lt': t - 3600 * hours}})


mongo_host = os.getenv('MONGO_HOST') or 'localhost'

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO
)

while True:
    with requests.Session() as session:
        mongo = MongoClient(mongo_host)
        db = mongo['elpaiscom-bot']
        delete_older_than(12, db)

        user_agent = random.choice(common.user_agents)
        session.headers = {'User-Agent': user_agent}

        new_comment_count = 0
        post_count = 0
        for post in db['posts'].find():
            post_count = post_count + 1
            comments = common.fetch_elpaiscom_comments(post['url'], session)

            for comment in comments:
                query = db['comments'].find_one({'comment_id': comment['comment_id'], 'post_id': comment['post_id']})
                if query is None:
                    if comment['posted_at'] > (time.time() - 12 * 3600):
                        db['comments'].insert_one(comment)
                        new_comment_count = new_comment_count + 1
            time.sleep(1)
        mongo.close()
        logging.info(str(new_comment_count) + ' new comments found. ' + str(post_count) + ' posts processed.')
    time.sleep(13 * 60)
