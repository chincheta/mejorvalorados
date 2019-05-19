FROM python:3.7

ADD . /app
WORKDIR /app

RUN pip install --trusted-host pypi.python.org -r requirements.txt

ENV MONGO_HOST mongo

EXPOSE 5000

ENTRYPOINT [ "python" ]

CMD [ "app.py" ]