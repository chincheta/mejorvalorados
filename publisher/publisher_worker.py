import os

import pika
import tweepy

twitter_consumer_key = os.getenv('TWITTER_CONSUMER_KEY') or ''
twitter_secret = os.getenv('TWITTER_SECRET') or ''
twitter_access_token = os.getenv('TWITTER_ACCESS_TOKEN') or ''
twitter_access_token_secret = os.getenv('TWITTER_ACCESS_TOKEN_SECRET') or ''

rabbitmq_host = os.getenv('RABBITMQ_HOST') or 'localhost'

connection = pika.BlockingConnection(pika.ConnectionParameters(host=rabbitmq_host))
channel = connection.channel()

channel.queue_declare(queue='post.event.screening_passed')


def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    auth = tweepy.OAuthHandler(twitter_consumer_key, twitter_secret)
    auth.set_access_token(twitter_access_token, twitter_access_token_secret)
    twitter = tweepy.API(auth)
    twitter.update_status(status=body)


channel.basic_consume(queue='post.event.screening_passed', on_message_callback=callback, auto_ack=True)

print(' [*] Waiting for messages. To exit press CTRL+C')
channel.start_consuming()
