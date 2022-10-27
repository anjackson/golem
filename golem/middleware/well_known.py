# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import logging
from urllib import request
from urllib.parse import urlparse, urlunparse

import scrapy
from scrapy import signals
from scrapy import Request
from scrapy.http import Response

from golem.middleware.hop_path import Hop

DEFAULT_WELL_KNOWN_URIS = [
    "/humans.txt", 
    "/ads.txt", 
    "/sellers.json",
    "/.well-known/security.txt",
    "/.well-known/host-meta.json",
    "/.well-known/dat",
]

class WellKnownURISpiderMiddleware(object):
    """
    Module to attempt to crawl some well-known URIs for any host crawled.

    Based on https://github.com/ukwa/ukwa-heritrix/blob/master/src/main/java/uk/bl/wap/modules/extractor/ExtractorHTTPWellKnownURIs.java
    """

    #Hop.Inferred

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response: Response, spider):
        # If the URL is a home page, generate variations for this home page:
        url = urlparse(response.url,allow_fragments=False)
        if url.path == '/':
            spider.logger.debug(f"Homepage {url} crawled, so enqueing well-known URIs.")
            for wku in DEFAULT_WELL_KNOWN_URIS:
                # FIXME should this clone-and-replace?
                req = Request(
                    url=urlunparse(url._replace(path=wku)), 
                    meta={
                        'hop': Hop.Inferred.value,
                        #'hop_path': response.meta.get('hop_path', ''),
                        })
                spider.crawler.engine.crawl(req)

        return None

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
