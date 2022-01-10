# syntax=docker/dockerfile:1

FROM python:3.8-slim-buster

WORKDIR /webapp

COPY requirements.txt requirements.txt
RUN apt-get update && apt-get install -y python-dev default-libmysqlclient-dev libssl-dev
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
