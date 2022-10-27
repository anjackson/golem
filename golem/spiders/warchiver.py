import csv
from datetime import datetime, timezone
import scrapy
from scrapy import Request
from scrapy.http import Response, TextResponse
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.downloadermiddlewares.robotstxt import IgnoreRequest
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

from golem.middleware.hop_path import Hop

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
        "DOWNLOAD_DELAY": 2.0,
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        "REDIRECT_ENABLED": True, # Let the Scrapy downloader middleware handle redirects
        "HTTPERROR_ALLOW_ALL": False, # Make this spider process all outcomes (404s etc.).
        "FEEDS": {
            "items.jsonl":{
                "format": "jsonl"
            }
        },
        "SPIDER_MIDDLEWARES": {
            # Install this so that the hop path from the seed can be tracked, including via middleware:
            'golem.middleware.hop_path.HopPathSpiderMiddleware': 1,
            # If a homepage gets crawled, crawl well-known URIs for that host:
            'golem.middleware.well_known.WellKnownURISpiderMiddleware': 5,
            # Emit Crawl Log Items for each result:
            'golem.middleware.crawl_log.CrawlLogItemSpiderMiddleware': 10,
        },
        "DOWNLOADER_MIDDLEWARES": {
            # Install at the end so all robots.txt/3xx/4xx/5xx can be observed:
            'golem.middleware.crawl_log.CrawlLogDownloaderMiddleware': 999998,
            # Put hop path middleware at the end so that gets updated first on response, before logging:
            'golem.middleware.hop_path.HopPathDownloaderMiddleware':   999999
        },
        #"LOG_LEVEL": "INFO",
    }