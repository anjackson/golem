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
        if self.seeds is None:
            return
        # Otherwise, process the seeds...
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
            print(f"Number of links found: {len(links)}")
            for href in links:
                print(response.urljoin(href.extract()))
                #yield response.follow(href, self.parse)

    custom_settings = {
        #"SCHEDULER": 'urlfrontier.scheduler.URLFrontierScheduler',
        "SCHEDULER_URLFRONTIER_ENDPOINT": '127.0.0.1:7071',
        "DOWNLOAD_DELAY": 5.0,
        "REQUEST_FINGERPRINTER_IMPLEMENTATION": "2.7",
        # Switch off 'Accept-Encoding: gzip' compression support:
        'COMPRESSION_ENABLED': False,
        "REFERER_ENABLED": True, # So the log can log the referring URLs
        # Switching this off will stop the hop path tracking working.
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
            # Emit Crawl Log Items for each result (also track source references):
            'golem.middleware.crawl_log.CrawlLogItemSpiderMiddleware': 10,
        },
        "DOWNLOADER_MIDDLEWARES": {
            # Record the response digest and length:
            'golem.middleware.crawl_log.ResponseDigestDownloaderMiddleware': 999997,
            # Install at the end so all robots.txt/3xx/4xx/5xx can be observed:
            'golem.middleware.crawl_log.CrawlLogDownloaderMiddleware': 999998,
            # Put hop path middleware at the end so that gets updated first on response, before logging:
            'golem.middleware.hop_path.HopPathDownloaderMiddleware':   999999
        },
        # Broad Crawl settings (general)
        # https://docs.scrapy.org/en/latest/topics/broad-crawls.html
        'CONCURRENT_REQUESTS': 100,
        'REACTOR_THREADPOOL_MAXSIZE': 20,
        'LOG_LEVEL': 'INFO',
        'COOKIES_ENABLED': False,
        # Broad Crawl settings (default scheduler only)
        'SCHEDULER_PRIORITY_QUEUE': 'scrapy.pqueues.DownloaderAwarePriorityQueue',
        # Breadth-first order (default scheduler only):
        # https://docs.scrapy.org/en/latest/faq.html#faq-bfo-dfo
        'DEPTH_PRIORITY': 1,
        'SCHEDULER_DISK_QUEUE': 'scrapy.squeues.PickleFifoDiskQueue',
        'SCHEDULER_MEMORY_QUEUE': 'scrapy.squeues.FifoMemoryQueue',
        # Alternative Twisted Reactor (?)
        #'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
    }