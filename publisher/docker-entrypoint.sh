#!/usr/bin/env bash

./wait-for-it.sh rabbitmq:5672

python -u publisher_worker.py