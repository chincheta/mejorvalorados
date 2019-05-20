import logging
import os
import time
from datetime import datetime

import pika
from pymongo import MongoClient

import common
from secrets import get_secret


def get_tally(urls):
    tally = []
    for url in urls:
        disqus_comments = common.fetch_okdiariocom_comments(url, disqus_key)
        for disqus_comment in disqus_comments:
            heat = common.heat(
                disqus_comment['likes'],
                disqus_comment['dislikes'],
                common.dt2ts(datetime.fromisoformat(disqus_comment['createdAt'])))
            votes = {
                'comment_id': disqus_comment['id'],
                'post_id': disqus_comment['thread'],
                'ups': disqus_comment['likes'],
                'downs': disqus_comment['dislikes'],
                'heat': heat}
            tally.append(votes)
    return tally


mongo_host = os.getenv('MONGO_HOST') or 'localhost'
rabbitmq_host = os.getenv('RABBITMQ_HOST') or 'localhost'
disqus_key = get_secret('DISQUS_API_KEY')

logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO
)

while True:
    mongo = MongoClient(mongo_host)
    db = mongo['okdiariocom-bot']
    comment_count = 0
    urls = []
    for comment in db['comments'].find():
        if comment['url'] not in urls:
            urls.append(comment['url'])
    tally = get_tally(urls)

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
