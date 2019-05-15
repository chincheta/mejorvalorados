FROM python:3.7

ADD . /app
WORKDIR /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt

ENV MONGO_HOST mongo
ENV POSTS_POLLING_PERIOD 900

CMD "./docker-entrypoint.sh"
