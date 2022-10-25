import csv
from datetime import datetime, timezone
import scrapy
from scrapy import Request
from scrapy.http import Response, TextResponse
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.downloadermiddlewares.robotstxt import IgnoreRequest
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

from golem.middlewares import Hop

class WarchiverSpider(scrapy.Spider):
    name = 'warchiver'

    def __init__(self, seeds=None, *args, **kwargs):
        super(WarchiverSpider,self).__init__(*args, **kwargs)
        self.seeds = seeds

    def start_requests(self):
        if self.seeds.endswith('.csv'):
            reader = csv.reader(open(self.seeds),delimiter='\t')
            for row in reader:
                url = row[1]
                if url:
                    yield Request(url=url)
        else:
            with open(self.seeds) as file:
                for line in file:
                    if line:
                        yield Request(url=line.rstrip())

    def parse(self, response: Response):        
        if isinstance(response, TextResponse):
            links = response.css('a::attr(href)')
            print(len(links))
            for href in links:
                print(response.urljoin(href.extract()))
                #yield response.follow(href, self.parse)

    custom_settings = {
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "REDIRECT_ENABLED": False,
        "HTTPERROR_ALLOW_ALL": True, # Make this crawler process of all outcomes.
        "FEEDS": {
            "items.jsonl":{
                "format": "jsonl"
            }
        },
        "SPIDER_MIDDLEWARES": {
            'golem.middlewares.HopPathSpiderMiddleware': 5,
        },
        "DOWNLOADER_MIDDLEWARES": {
            # Install just after the robots.txt handler so downloads of robots.txt can be observed.
            'golem.middlewares.CrawlLogDownloaderMiddleware': 150,
        },
        #"LOG_LEVEL": "INFO",
    }