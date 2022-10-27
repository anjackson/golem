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
        "REDIRECT_ENABLED": True,
        "HTTPERROR_ALLOW_ALL": True, # Make this spider process all outcomes.
        "FEEDS": {
            "items.jsonl":{
                "format": "jsonl"
            }
        },
        "SPIDER_MIDDLEWARES": {
            # Install this so that the hop path from the seed is tracked:
            'golem.middleware.hop_path.HopPathSpiderMiddleware': 1,
            'golem.middleware.well_known.WellKnownURISpiderMiddleware': 5,
        },
        "DOWNLOADER_MIDDLEWARES": {
            # Install at the end so all downloads e.g. redirects, or robots.txt can be observed.
            'golem.middleware.crawl_log.CrawlLogDownloaderMiddleware': 999998,
            # But the hop path middleware needs to be right at the end to fix that up:
            'golem.middleware.hop_path.HopPathDownloaderMiddleware':   999999
        },
        #"LOG_LEVEL": "INFO",
    }