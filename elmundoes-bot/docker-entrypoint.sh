#!/usr/bin/env bash

python posts_worker.py &
python comments_worker.py &
python votes_worker.py &
python screening_worker.py &

while sleep 60; do
    echo "sleeping..."
done
