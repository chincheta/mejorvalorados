from flask import Flask, render_template
from pymongo import MongoClient
import os

app = Flask(__name__)
mongo_host = os.getenv('MONGO_HOST') or 'localhost'


@app.route('/')
def index():
    mongo = MongoClient(mongo_host)
    db = mongo['elmundoes-bot']

    comments = db['comments'].find().sort('heat', -1)
    mongo.close()
    return render_template("comments.html", comments=comments)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')