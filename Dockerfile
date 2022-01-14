# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /webapp

COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y gcc nginx python-dev default-libmysqlclient-dev libssl-dev

RUN pip3 install -r requirements.txt

ENV FLASK_APP=App.py

COPY . .

COPY nginx.conf /etc/nginx

RUN chmod +x ./start.sh

CMD ["./start.sh"]
