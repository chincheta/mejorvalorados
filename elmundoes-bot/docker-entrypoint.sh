#!/usr/bin/env bash

./wait-for-it.sh mongo:27017
./wait-for-it.sh rabbitmq:5672

python -u posts_worker.py &
python -u comments_worker.py &
python -u votes_worker.py &

while sleep 10; do
    ps aux |grep posts_worker |grep -q -v grep
    POSTS_WORKER_STATUS=$?
    ps aux |grep comments_worker |grep -q -v grep
    COMMENTS_WORKER_STATUS=$?
    ps aux |grep votes_worker |grep -q -v grep
    VOTES_WORKER_STATUS=$?

  if [[ ${POSTS_WORKER_STATUS} -ne 0 || ${COMMENTS_WORKER_STATUS} -ne 0  || ${VOTES_WORKER_STATUS} -ne 0  ]]; then
    echo "One of the processes crashed. Exiting to force a restart..."
    exit 1
  fi
done
