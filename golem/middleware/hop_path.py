# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import logging
import re

import scrapy
from scrapy import signals
from scrapy import Request

from enum import Enum

# Hops that can make up a discovery path (or hop_path)
# https://heritrix.readthedocs.io/en/latest/glossary.html
class Hop(Enum):
    # Link (normal navigation links like <a href=...>)
    Link = 'L'
    # Redirect
    Redirect = 'R'
    # Embedded links necessary to render the page (such as <img src=...>)
    Embed = 'E'
    # Speculative embed (aggressive JavaScript link extraction)
    Speculative = 'X'
    # Prerequisite (such as DNS lookup or robots.txt)
    Prerequisite = 'P'
    #  Inferred/implied links. Not necessarily in the source material, but deduced by convention (such as /favicon.ico)
    Inferred = 'I'
    # Manifest (such as links discovered from a sitemap file)
    Manifest = 'M'
    # Synthesized form-submit
    Synthesized = 'S'


class HopPathSpiderMiddleware(object):
    """
    Each URI has a discovery path. The path contains one character for each link or embed followed
    from the seed, for example “LLLE” might be an image on a page that’s 3 links away from a seed.
    
    The discovery path of a seed is an empty string.

    See <https://heritrix.readthedocs.io/en/latest/glossary.html>
    """

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        # FIXME Drop requests if hop path over configurable limit.
        # FIXME Warn that redirects won't be logged if REDIRECT_ENABLED=True
        return s

    # Copy the hop_path into the results so it can get updated later:
    def process_spider_output(self, response, result, spider: scrapy.Spider):
        # Follow redirects:
        if 'location_ORF' in response.headers:
            yield self._update_hop_path(
                Request(
                url=response.headers['Location'].decode('utf-8'),
                meta={'hop': Hop.Redirect.value}
                )
            )
        # And update hops for output from spider:
        for i in result:
            #if i.meta.get('redirect_times', 0) > 0:
            #    i.meta['hop'] = Hop.Redirect.value
            #yield self._update_hop_path(i)
            # Copy hop path so downloader can update it:
            i.meta['hop_path'] = response.meta.get('hop_path', '')
            i.meta['hop'] = i.meta.get('hop', Hop.Link.value)
            yield i

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


class HopPathDownloaderMiddleware(object):
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
        # Update the hop_path based on the 'hop', defaulting to 'L'
        if 'hop_path' not in request.meta:
            request.meta['hop_path'] = ''
        else:
            hop = request.meta.get('hop', Hop.Link.value)
            if 'redirect_urls' in request.meta:
                hop = Hop.Redirect.value
            request.meta['hop_path'] = request.meta['hop_path'] + hop

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


