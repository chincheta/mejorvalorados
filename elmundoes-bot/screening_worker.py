import os
import time

import pika
import common
from pymongo import MongoClient

rabbitmq_host = os.getenv('RABBITMQ_HOST') or 'localhost'
mongo_host = os.getenv('MONGO_HOST') or 'localhost'

while True:
    mongo = MongoClient(mongo_host)
    db = mongo['elmundoes-bot']
    for comment in db['comments'].find():
        query = {'comment_id': comment['comment_id'], 'post_id': comment['post_id']}
        values = {'$set': {'heat': common.heat(comment['ups'], comment['downs'], comment['posted_at'])}}
        db['comments'].update_one(query, values)

    for comment in db['comments'].find().sort('heat', -1).limit(1):
        if 'posted' not in comment:
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
    time.sleep(60)
