#!/usr/bin/env bash

docker build . -t chincheta/mejorvalorados_okdiariocom-bot:latest
docker push chincheta/mejorvalorados_okdiariocom-bot:latest