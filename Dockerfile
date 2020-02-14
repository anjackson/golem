FROM python:3.7-slim

COPY . /golem

WORKDIR /golem

RUN \
  pip install -r requirements.txt

#EXPOSE 8010

CMD scrapy
