# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import json
import scrapy

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
        return f"{self['ts']} {self['sc']} {self['url']} {self['hop_path']} - {self['ct']} - - - - -"

    def to_jsonl(self):
        return json.dumps(dict(self))


