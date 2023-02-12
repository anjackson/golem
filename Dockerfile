FROM python:3.11

COPY . /golem

WORKDIR /golem

RUN \
  pip install -r requirements.txt

#EXPOSE 8010

CMD scrapy
