# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
import json
import logging
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime, timezone

from scrapy import signals
from scrapy import Request
from scrapy.http import Response, TextResponse
from scrapy.spidermiddlewares.httperror import HttpError
from scrapy.downloadermiddlewares.robotstxt import IgnoreRequest
from twisted.internet.error import DNSLookupError
from twisted.internet.error import TimeoutError, TCPTimedOutError

from golem.items import CrawlLogItem

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
        elif isinstance(exception, TimeoutError):#, TCPTimedOutError):
            log['sc'] = -4
        elif isinstance(exception, IgnoreRequest):
            log['sc'] = -9998
        else:
            raise Exception("Unknown exception type: " + exception)
        # Other fields:
        log['size'] = '-'
        log['ct'] = '-'
        log['hop_path'] = ''

        return log

class GolemSpiderMiddleware(object):
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
            # Update the hop_path based on the 'hop', defaulting to 'L'
            if 'hop_path' not in i.meta:
                i.meta['hop_path'] = ''
            hop = i.meta.get('hop', 'L')
            i.meta['hop_path'] += hop
            # And return:
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


class GolemDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

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
        spider.logger.info('process_request: %s' % request.url)
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        spider.logger.info('process_response: %s' % spider.name)
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        spider.logger.info('process_exception: %s' % spider.name)
        spider.logger.info('process_exception: %s' % request.url)
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------

# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------


from enum import Enum

class Hop(Enum):
    Link = 'L'
    Redirect = 'R'
    Embed = 'E'
    Speculative = 'X'
    Prerequisite = 'P'


class HopPathSpiderMiddleware(object):

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        # FIXME Drop requests if hop path over configurable limit.
        # FIXME Warn that redirects won't be logged if REDIRECT_ENABLED=True
        return s

    def process_spider_output(self, response, result, spider):
        # Follow redirects:
        if 'location' in response.headers:
            yield self._update_hop_path(
                Request(
                url=response.headers['Location'].decode('utf-8'),
                meta={'hop': Hop.Redirect.value}
                )
            )
        # And update hops for output from spider:
        for i in result:
            yield self._update_hop_path(i)

    def _update_hop_path(self, r):
        # Update the hop_path based on the 'hop', defaulting to 'L'
        if 'hop_path' not in r.meta:
            r.meta['hop_path'] = ''
        hop = r.meta.get('hop', Hop.Link.value)
        r.meta['hop_path'] += hop
        # And return:
        return r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------
# ------------------------------------------------------------------------------------

class CrawlLogDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    crawl_log = logging.getLogger('CrawlLogDownloaderMiddleware')

    fh = TimedRotatingFileHandler('crawl.jsonl', when='midnight', encoding='utf-8', delay=True, utc=True)
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
        self.crawl_log.info(json.dumps(dict(to_item(request,response))))
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        spider.logger.info('process_exception: %s' % spider)
        self.crawl_log.info(json.dumps(dict(err_to_item(request,exception))))
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


