# -*- coding: utf-8 -*-
import csv
import scrapy
from scrapy import Request


class EthosSpider(scrapy.Spider):
    name = 'ethos'

    def start_requests(self):
        reader = csv.reader(open('ethos-urls.csv'),delimiter='\t')
        for row in reader:
            url = row[1]
            yield Request(url=url)

    def parse(self, response):
        print(response)
        pass
