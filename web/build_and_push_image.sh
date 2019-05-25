#!/usr/bin/env bash

docker build . -t chincheta/mejorvalorados_web:latest
docker push chincheta/mejorvalorados_web:latest