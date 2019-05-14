#!/usr/bin/env bash

python -u posts_worker.py &
python -u comments_worker.py &
python -u votes_worker.py &
python -u screening_worker.py &

while true; do sleep 1; done
