import csv
from datetime import datetime, timezone
import scrapy
from scrapy import Request
from scrapy.http import Response, TextResponse
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.downloadermiddlewares.robotstxt import IgnoreRequest
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

from golem.items import CrawlLogItem


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
                    yield Request(url=url, errback=self.errback_httpbin)
        else:
            with open(self.seeds) as file:
                for line in file:
                    if line:
                        yield Request(url=line.rstrip(), errback=self.errback_httpbin)

    def parse(self, response: Response):
        yield self.to_item(response)
        # Follow redirects (FIXME needs depth limit!)
        if 'location' in response.headers:
            yield Request(url=response.headers['Location'].decode('utf-8'), errback=self.errback_httpbin)
        
        if isinstance(response, TextResponse):
            links = response.css('a::attr(href)')
            print(len(links))
            for href in links:
                print(response.urljoin(href.extract()))
                #yield response.follow(href, self.parse)

    def errback_httpbin(self, failure):
        # log all failures
        self.logger.error(repr(failure))
        yield self.to_item(failure)

    def to_item(self, response: Response, datetime=datetime.now(timezone.utc)):
            log = CrawlLogItem()
            log['url'] = response.request.url
            log['ts'] = datetime.isoformat()
            # Check status to see if this was a valid response:
            if hasattr(response, 'status'):
                log['sc'] = response.status
                log['size'] = len(response.body)
                log['ct'] = response.headers.get('content-type', b'-').decode('utf-8')
            else:
                # https://heritrix.readthedocs.io/en/latest/glossary.html#status-codes
                if response.check(HttpError):
                    log['sc'] = -2
                elif response.check(DNSLookupError):
                    log['sc'] = -1
                elif response.check(TimeoutError, TCPTimedOutError):
                    log['sc'] = -4
                elif response.check(IgnoreRequest):
                    log['sc'] = -9998
                else:
                    raise Exception("Unknown response type: " + response)
                # Other fields:
                log['size'] = '-'
                log['ct'] = '-'

            return log

    custom_settings = {
        "REDIRECT_ENABLED": False,
        "HTTPERROR_ALLOW_ALL": True, # Make this crawler process of all outcomes.
        "FEEDS": {
            "items.jsonl":{
                "format": "jsonl"
            }
        },
        #"LOG_LEVEL": "INFO",
    }