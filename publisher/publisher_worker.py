import logging
import os

import pika
import tweepy

from secrets import get_secret

twitter_consumer_key = get_secret('TWITTER_CONSUMER_KEY')
twitter_secret = get_secret('TWITTER_SECRET') or ''
twitter_access_token = get_secret('TWITTER_ACCESS_TOKEN') or ''
twitter_access_token_secret = get_secret('TWITTER_ACCESS_TOKEN_SECRET') or ''

rabbitmq_host = os.getenv('RABBITMQ_HOST') or 'localhost'

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
channel = connection.channel()

channel.queue_declare(queue='post.event.screening_passed')


def callback(ch, method, properties, body):
    auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_secret)
    auth.set_access_token(twitter_access_token, twitter_access_token_secret)
    twitter = tweepy.API(auth)
    twitter.update_status(status=body)
    logging.info('New tweet posted.')


logging.basicConfig(
    format='%(asctime)s - %(message)s',
    level=logging.INFO
)

channel.basic_consume(queue='post.event.screening_passed', on_message_callback=callback, auto_ack=True)

channel.start_consuming()
