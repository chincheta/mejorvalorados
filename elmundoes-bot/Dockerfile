FROM python:3.7

ADD . /app
WORKDIR /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt

CMD "./docker-entrypoint.sh"
