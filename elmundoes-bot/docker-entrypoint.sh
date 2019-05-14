#!/usr/bin/env bash

./wait-for-it.sh mongo:27017
./wait-for-it.sh rabbitmq:5672

python -u posts_worker.py &
python -u comments_worker.py &
python -u votes_worker.py &
python -u screening_worker.py &

while true; do sleep 1; done
