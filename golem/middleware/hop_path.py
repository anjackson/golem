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

    This part is needed to copy the current hop path from the response to the spider outputs.

    Also records the 'via' and 'source' so we can track how we got to this URL

    See <https://heritrix.readthedocs.io/en/latest/glossary.html>
    """

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        # FIXME Drop requests if hop path over configurable limit.
        # FIXME Warn that redirects won't be logged if REDIRECT_ENABLED=True
        return s

    # Copy the hop_path into the results so it can get updated later:
    def process_spider_output(self, response, result, spider: scrapy.Spider):
        # And update hops for output from spider:
        for i in result:
            if isinstance(i, scrapy.Request):
                # Copy hop path so downloader can update it:
                i.meta['hop_path'] = response.meta.get('hop_path', '')
                i.meta['hop'] = i.meta.get('hop', Hop.Link.value)
                # Add the via:
                i.meta['via'] = response.url
                # Copy source so downloader can update it:
                if 'source' in response.meta:
                    i.meta['source'] = response.meta['source']
                
            yield i

    def process_start_requests(self, start_requests, spider):
        # Set source == Seed URL if not otherwise set:
        # (only works for start_requests defined in spiders)
        for r in start_requests:
            if not 'source' in r.meta:
                r.meta['source'] = r.url

            yield r


class HopPathDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        return s

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest

        # Update the hop_path based on the 'hop', defaulting to 'L'
        if 'hop_path' not in request.meta:
            request.meta['hop_path'] = ''
        else:
            hop = request.meta.get('hop', Hop.Link.value)
            if 'redirect_urls' in request.meta:
                hop = Hop.Redirect.value
                request.meta['via'] = request.meta['redirect_urls'][0]
            request.meta['hop_path'] = request.meta['hop_path'] + hop

        return response


