import logging
import os
import random
import time

import pika
import requests
from pymongo import MongoClient

import common


def get_tally(urls, session):
    tally = []
    for url in urls:
        comments = common.fetch_elpaiscom_comments(url, session)
        for comment in comments:
            heat = common.heat(
                comment['ups'],
                comment['downs'],
                comment['posted_at'])
            votes = {
                'comment_id': comment['comment_id'],
                'post_id': comment['post_id'],
                'ups': comment['ups'],
                'downs': comment['downs'],
                'heat': heat}
            tally.append(votes)
    time.sleep(1)
    return tally


mongo_host = os.getenv('MONGO_HOST') or 'localhost'
rabbitmq_host = os.getenv('RABBITMQ_HOST') or 'localhost'

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO
)

while True:
    mongo = MongoClient(mongo_host)
    db = mongo['elpaiscom-bot']
    comment_count = 0
    urls = []
    for comment in db['comments'].find():
        if comment['url'] not in urls:
            urls.append(comment['url'])
    with requests.Session() as session:
        user_agent = random.choice(common.user_agents)
        session.headers = {'User-Agent': user_agent}
        tally = get_tally(urls, session)

    updated_count = 0
    processed_count = 0
    for votes in tally:
        query = {'comment_id': votes['comment_id'], 'post_id': votes['post_id']}
        values = {'$set': {'ups': votes['ups'], 'downs': votes['downs'], 'heat': votes['heat']}}
        updated_count = db['comments'].update_one(query, values).modified_count + updated_count
        processed_count = processed_count + 1

    logging.info('Updated votes of ' + str(updated_count) + ' comments. ' + str(processed_count) + ' processed.')

    # Post if new best
    for comment in db['comments'].find().sort('heat', -1).limit(1):
        if 'posted' not in comment:
            logging.info('New best: ' + comment['body'])
            logging.info(comment['url'])
            connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
            channel = connection.channel()
            channel.queue_declare(queue='post.event.screening_passed')
            channel.basic_publish(
                exchange='',
                routing_key='post.event.screening_passed',
                body=comment['body'] + ' ' + comment['url'])

            query = {'comment_id': comment['comment_id'], 'post_id': comment['post_id']}
            values = {'$set': {'posted': True}}
            db['comments'].update_one(query, values)
            connection.close()

    mongo.close()
    time.sleep(17 * 60)
