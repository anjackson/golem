# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import json
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone

import scrapy
from scrapy import signals
from scrapy import Request
from scrapy.http import Response, TextResponse
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.downloadermiddlewares.robotstxt import IgnoreRequest
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError


class CrawlLogItem(scrapy.Item):
    # The 1st column is a timestamp in ISO8601 format, to millisecond resolution. The time is the instant of logging. 
    ts = scrapy.Field()
    # The 2nd column is the fetch status code. Usually this is the HTTP status code but it can also be a negative number if URL processing was unexpectedly terminated. See Status codes for a listing of possible values.
    sc = scrapy.Field()
    # The 3rd column is the size of the downloaded document in bytes. For HTTP, Size is the size of the content-only. It excludes the size of the HTTP response headers. For DNS, its the total size of the DNS response. 
    size = scrapy.Field()
    # The 4th column is the URI of the document downloaded. 
    url = scrapy.Field()
    # The 5th column holds breadcrumb codes showing the trail of downloads that got us to the current URI. See Discovery path for description of possible code values. 
    hop_path = scrapy.Field()
    # The 6th column holds the URI that immediately referenced this URI ('referrer'). Both of the latter two fields -- the discovery path and the referrer URL -- will be empty for such as the seed URIs.
    # The 7th holds the document mime type, 
    ct = scrapy.Field()
    # the 8th column has the id of the worker thread that downloaded this document, 
    # the 9th column holds a timestamp (in RFC2550/ARC condensed digits-only format) indicating when a network fetch was begun, and if appropriate, the millisecond duration of the fetch, separated from the begin-time by a '+' character.
    # The 10th field is a SHA1 digest of the content only (headers are not digested). 
    # The 11th column is the 'source tag' inherited by this URI, if that feature is enabled. 
    # Finally, the 12th column holds “annotations”, if any have been set. Possible annontations include: the number of times the URI was tried (This field is '-' if the download was never retried); the literal lenTrunc if the download was truncated because it exceeded configured limits; timeTrunc if the download was truncated because the download time exceeded configured limits; or midFetchTrunc if a midfetch filter determined the download should be truncated.

    def to_h3_log(self):
        return f"{self['ts']} {self['sc']} {self['size']} {self['url']} {self['hop_path']} - {self['ct']} - - - - -"

    def to_jsonl(self):
        return json.dumps(dict(self))


def to_item(request: Request, response: Response, datetime=datetime.now(timezone.utc)):
        log = CrawlLogItem()
        log['url'] = response.url
        log['ts'] = datetime.isoformat()
        log['sc'] = response.status
        log['size'] = len(response.body)
        log['ct'] = response.headers.get('content-type', b'-').decode('utf-8')
        log['hop_path'] = request.meta.get('hop_path','')

        return log

def err_to_item(request: Request, exception, datetime=datetime.now(timezone.utc)):
        log = CrawlLogItem()
        log['url'] = request.url
        log['ts'] = datetime.isoformat()
        # https://heritrix.readthedocs.io/en/latest/glossary.html#status-codes
        if isinstance(exception, HttpError):
            log['sc'] = -2
        elif isinstance(exception, DNSLookupError):
            log['sc'] = -1
        elif isinstance(exception, TimeoutError):
            log['sc'] = -4
        elif isinstance(exception, TCPTimedOutError):
            log['sc'] = -4
        elif isinstance(exception, IgnoreRequest):
            log['sc'] = -9998
        else:
            raise Exception("Unknown exception type: " + exception)
        # Other fields:
        log['size'] = '0'
        log['ct'] = '-'
        log['hop_path'] = ''

        return log


class CrawlLogItemSpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        spider.logger.info('process_spider_input: %s' % spider.name)
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        spider.logger.info('process_spider_output: %s' % spider.name)
        yield to_item(response.request, response)
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request, dict
        # or Item objects.
        spider.logger.info('process_spider_exception: %s' % spider.name)
        yield to_item(response.request, exception)
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        spider.logger.info('process_start_requests: %s' % spider.name)
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class CrawlLogDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    crawl_log = logging.getLogger('CrawlLogDownloaderMiddleware')

    fh = TimedRotatingFileHandler('crawl.log', when='midnight', encoding='utf-8', delay=True, utc=True)
    fh.setFormatter(logging.Formatter('%(message)s'))
    fh.setLevel(logging.INFO)
    fh.doRollover()
    crawl_log.propagate = False
    crawl_log.addHandler(fh)

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        spider.logger.info('process_request: %s' % spider.name)
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        spider.logger.info('process_response: %s' % spider)
        self.crawl_log.info(to_item(request,response).to_h3_log())
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        spider.logger.info('process_exception: %s' % spider)
        self.crawl_log.info(err_to_item(request,exception).to_h3_log())
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


