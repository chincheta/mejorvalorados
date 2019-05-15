import json
import logging
import os
import random
import time
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

import common


def delete_older_than(hours, db):
    t = time.time()
    db['comments'].delete_many({'posted_at': {'$lt': t - 3600 * hours}})


def get_comments(url, session):
    comments = []
    response = session.get(url)
    soup = BeautifulSoup(response.content, "html.parser")
    element = soup.find('strong', attrs={"data-commentid": True})
    if element is not None:
        post_id = element["data-commentid"]
        comments_url = "https://www.elmundo.es/servicios/noticias/scroll/comentarios/comunidad/listarMejorValorados.html?noticia=" + post_id + "&version=v2"
        response = session.get(comments_url)
        raw_comments = json.loads(response.text)

        for raw_comment in raw_comments['items']:
            if common.is_comment_ok_for_twitter(raw_comment['body']):
                comment = {
                    'comment_id': raw_comment['id'],
                    'url': url,
                    'post_id': post_id,
                    'posted_at': common.dt2ts(
                        datetime.strptime(raw_comment['date'] + ' ' + raw_comment['time'], '%d/%m/%Y %H:%M')),
                    'ups': 0,
                    'downs': 0,
                    'heat': 0,
                    'body': raw_comment['body']
                }
                comments.append(comment)
                return comments
    return comments


mongo_host = os.getenv('MONGO_HOST') or 'localhost'

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO
)

while True:
    with requests.Session() as session:
        mongo = MongoClient(mongo_host)
        db = mongo['elmundoes-bot']
        delete_older_than(12, db)

        user_agent = random.choice(common.user_agents)
        session.headers = {'User-Agent': user_agent}

        new_comment_count = 0
        post_count = 0
        for post in db['posts'].find():
            post_count = post_count + 1
            comments = get_comments(post['url'], session)

            for comment in comments:
                query = db['comments'].find_one({'comment_id': comment['comment_id'], 'post_id': comment['post_id']})
                if query is None:
                    if comment['posted_at'] > (time.time() - 12 * 3600):
                        db['comments'].insert_one(comment)
                        new_comment_count = new_comment_count + 1
            time.sleep(1)
        mongo.close()
        logging.info(str(new_comment_count) + ' new comments found. ' + str(post_count) + ' posts processed.')
    time.sleep(900)
