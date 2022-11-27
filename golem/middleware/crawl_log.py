# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import json
import logging
from hashlib import sha1
from base64 import b32encode
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


# Crawl log information, as per
# https://github.com/internetarchive/heritrix3/blob/37ce8d694590b0cf8cbe0a38a58c5f8ee719c4f0/engine/src/main/java/org/archive/crawler/io/UriProcessingFormatter.java#L73
# but key names aiming to be consistent with:
# https://github.com/internetarchive/heritrix3/blob/37ce8d694590b0cf8cbe0a38a58c5f8ee719c4f0/contrib/src/main/java/org/archive/modules/postprocessor/CrawlLogJsonBuilder.java#L21
class CrawlLogItem(scrapy.Item):
    # The 1st column is a timestamp in ISO8601 format, to millisecond resolution. The time is the instant of logging. 
    timestamp = scrapy.Field()
    # The 2nd column is the fetch status code. Usually this is the HTTP status code but it can also be a negative number if URL processing was unexpectedly terminated. See Status codes for a listing of possible values.
    status_code = scrapy.Field()
    # The 3rd column is the size of the downloaded document in bytes. For HTTP, Size is the size of the content-only. It excludes the size of the HTTP response headers. For DNS, its the total size of the DNS response. 
    content_length = scrapy.Field()
    # The 4th column is the URI of the document downloaded. 
    url = scrapy.Field()
    # The 5th column holds breadcrumb codes showing the trail of downloads that got us to the current URI. See Discovery path for description of possible code values. 
    hop_path = scrapy.Field()
    # The 6th column holds the URI that immediately referenced this URI ('referrer'). Both of the latter two fields -- the discovery path and the referrer URL -- will be empty for such as the seed URIs.
    via = scrapy.Field()
    # The 7th holds the document mime type, 
    mimetype = scrapy.Field()
    # TODO??? the 8th column has the id of the worker thread that downloaded this document, 
    thread = scrapy.Field()
    # TODO??? the 9th column holds a timestamp (in RFC2550/ARC condensed digits-only format) indicating when a network fetch was begun, and if appropriate, the millisecond duration of the fetch, separated from the begin-time by a '+' character.
    start_time_plus_duration = scrapy.Field()
    # TODO The 10th field is a SHA1 digest of the content only (headers are not digested). 
    content_digest = scrapy.Field()
    # The 11th column is the 'source tag' inherited by this URI, if that feature is enabled. 
    seed = scrapy.Field()
    # TODO Finally, the 12th column holds “annotations”, if any have been set. Possible annontations include: the number of times the URI was tried (This field is '-' if the download was never retried); the literal lenTrunc if the download was truncated because it exceeded configured limits; timeTrunc if the download was truncated because the download time exceeded configured limits; or midFetchTrunc if a midfetch filter determined the download should be truncated.
    annotations = scrapy.Field()

    # ----------------------------------
    # Additional fields not in crawl.log
    # ----------------------------------

    # The size of the response, including headers.
    size = scrapy.Field()
    # The host part of the URL:
    host = scrapy.Field()
    # A name to identify the crawl:
    crawl_name = scrapy.Field()
    # A dict for extra info, e.g. scopeDecision:
    extra_info = scrapy.Field()

    # WARC-related fields, but we're not writing the WARCs.
    #warc_filename = scrapy.Field()
    #warc_offset = scrapy.Field()
    #warc_length = scrapy.Field()
    #warc_content_type = scrapy.Field()
    #warc_type = scrapy.Field()
    #warc_id = scrapy.Field()

    def to_h3_log(self):
        return f"{self['timestamp']} {self['status_code']} {self['content_length']} \
{self['url']} {self['hop_path']} {self['via']} {self['mimetype'].split(';')[0]} \
{self['thread']} {self['start_time_plus_duration']} {self['content_digest']} \
{self['seed']} {self['annotations']}"

    def to_jsonl(self):
        return json.dumps(dict(self))

def to_item(request: Request, response: Response, datetime=datetime.now(timezone.utc)):
        log = CrawlLogItem()
        log['url'] = response.url
        log['timestamp'] = datetime.now().isoformat()
        log['status_code'] = response.status
        log['content_length'] = len(response.body)
        log['mimetype'] = response.headers.get('content-type', b'-').decode('utf-8')
        log['hop_path'] = request.meta.get('hop_path','')
        log['seed'] = request.meta.get('source','-')
        log['via'] = request.meta.get('via','-')
        log['thread'] = request.meta.get('thread','-')
        log['start_time_plus_duration'] = request.meta.get('start_time_plus_duration','-')
        log['content_digest'] = b32encode( sha1(response.body).digest() ).decode('utf-8')
        log['annotations'] = request.meta.get('annotations','-')

        return log

def err_to_item(request: Request, exception, datetime=datetime.now(timezone.utc)):
        log = CrawlLogItem()
        log['url'] = request.url
        log['timestamp'] = datetime.now().isoformat()
        # https://heritrix.readthedocs.io/en/latest/glossary.html#status-codes
        if isinstance(exception, HttpError):
            log['status_code'] = -2
        elif isinstance(exception, DNSLookupError):
            log['status_code'] = -1
        elif isinstance(exception, TimeoutError):
            log['status_code'] = -4
        elif isinstance(exception, TCPTimedOutError):
            log['status_code'] = -4
        elif isinstance(exception, IgnoreRequest):
            log['status_code'] = -9998
        else:
            raise Exception("Unknown exception type: " + exception)
        # Other fields:
        log['content_length'] = '0'
        log['mimetype'] = '-'
        log['hop_path'] = request.meta.get('hop_path','')
        log['seed'] = request.meta.get('source','-')
        log['via'] = request.meta.get('via','-')
        log['thread'] = request.meta.get('thread','-')
        log['start_time_plus_duration'] = request.meta.get('start_time_plus_duration','-')
        log['content_digest'] = request.meta.get('content_digest','-')
        log['annotations'] = request.meta.get('annotations','-')

        return log


class CrawlLogItemSpiderMiddleware(object):
    """
    Emits a Crawl Log Item for every response.
    """

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        return s

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        yield to_item(response.request, response)
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request, dict
        # or Item objects.
        yield to_item(response.request, exception)


class ResponseDigestDownloaderMiddleware(object):
    """
    Calculates the length and digest of the HTTP response.
    Connects to download signals so hashes the 'raw' (transfer/content encoded) response.
    """
    
    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.request_reached_downloader, signal=signals.request_reached_downloader)
        crawler.signals.connect(s.bytes_received, signal=signals.bytes_received)
        crawler.signals.connect(s.response_downloaded, signal=signals.response_downloaded)
        return s

    def request_reached_downloader(self, request, spider):
        request.meta['response_bytes'] = 0
        request.meta['__download_hasher'] = sha1()

    def bytes_received(self, data, request, spider):
        request.meta['response_bytes'] += len(data)
        request.meta['__download_hasher'].update(data)
    
    def response_downloaded(self, request, spider):
        sha1_sum = request.meta.pop('__download_hasher')
        request.meta['response_digest'] = b32encode(sha1_sum.digest()).decode('utf-8')
    

class CrawlLogDownloaderMiddleware(object):
    """
    """

    start_time_format = "%Y%m%d%H%M%S%f"

    crawl_log = logging.getLogger('CrawlLogDownloaderMiddleware')
    fh = TimedRotatingFileHandler('crawl.log', when='midnight', encoding='utf-8', delay=True, utc=True)
    fh.setFormatter(logging.Formatter('%(message)s'))
    fh.setLevel(logging.INFO)
    crawl_log.propagate = False # Only log locally, not to 
    crawl_log.addHandler(fh)

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.request_reached_downloader, signal=signals.request_reached_downloader)
        crawler.signals.connect(s.response_downloaded, signal=signals.response_downloaded)
        return s

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        self.crawl_log.info(to_item(request,response).to_h3_log())
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        self.crawl_log.info(err_to_item(request,exception).to_h3_log())

    def request_reached_downloader(self, request, spider):
        request.meta['start_time_plus_duration'] = datetime.utcnow().strftime(self.start_time_format)
    
    def response_downloaded(self, request, spider):
        finish_time = datetime.utcnow()
        start_time = datetime.strptime(request.meta['start_time_plus_duration'], self.start_time_format)
        request.meta['start_time_plus_duration'] += "+" + str((finish_time-start_time).microseconds / 1000)


