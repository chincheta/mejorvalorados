import os
import random
import time

import common
import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient


def get_comment_votes(comment_id, post_id, session):
    response = session.post(
        "https://www.elmundo.es/servicios/noticias/scroll/comentarios/comunidad/valorar.html",
        data={
            "comentario": comment_id,
            "noticia": post_id,
            "version": "v2",
            "voto": "1"
        }
    )
    soup = BeautifulSoup(response.content, "html.parser")
    spans = soup.find_all("span")
    return {'ups': int(spans[0].text.replace('.', '').replace(',', '')),
            'downs': int(spans[1].text.replace('.', '').replace(',', ''))}


mongo_host = os.getenv('MONGO_HOST') or 'localhost'

while True:
    mongo = MongoClient(mongo_host)
    db = mongo['elmundoes-bot']
    with requests.Session() as session:
        user_agent = random.choice(common.user_agents)
        session.headers = {'User-Agent': user_agent}
        for comment in db['comments'].find():
            session.get(comment['url'])
            time.sleep(1)
            votes = get_comment_votes(comment['comment_id'], comment['post_id'], session)

            query = {'comment_id': comment['comment_id'], 'post_id': comment['post_id']}
            values = {'$set': {'ups': votes['ups'], 'downs': votes['downs']}}

            db['comments'].update_one(query, values)
            time.sleep(1)
    mongo.close()
    time.sleep(600)