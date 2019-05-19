#!/usr/bin/env bash

export RABBITMQ_HOST=${RABBITMQ_HOST:-localhost}

./wait-for-it.sh ${RABBITMQ_HOST}:5672

python -u publisher_worker.py