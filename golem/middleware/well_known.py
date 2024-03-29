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
    "/.well-known/host-meta",
    "/.well-known/host-meta.json",
    "/.well-known/dat",
    "/.well-known/nodeinfo",
]

class WellKnownURISpiderMiddleware(object):
    """
    Module to attempt to crawl some well-known URIs for any host crawled.

    Based on https://github.com/ukwa/ukwa-heritrix/blob/master/src/main/java/uk/bl/wap/modules/extractor/ExtractorHTTPWellKnownURIs.java
    """

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        return s

    def process_spider_output(self, response, result, spider: scrapy.Spider):
        # If the URL is a home page, generate variations for this home page:
        url = urlparse(response.url,allow_fragments=False)
        if url.path == '/':
            spider.logger.debug(f"Homepage {url} crawled, so enqueueing well-known URIs.")
            for wku in DEFAULT_WELL_KNOWN_URIS:
                # FIXME should this clone-and-replace?
                yield Request(
                    url=urlunparse(url._replace(path=wku)), 
                    meta={
                        'hop': Hop.Inferred.value,
                        })

        # And output the rest of the results from the spider
        for i in result:
            yield i
