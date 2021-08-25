# -*- coding: utf-8 -*-
import scrapy
from scrapy.http import Request
from scrapy.http.response.html import HtmlResponse
from scrapy.linkextractors import LinkExtractor
from scrapy import signals
from scrapy.exceptions import DontCloseSpider


class CrawlTestSiteSpider(scrapy.Spider):
    name = 'crawl-test-site'
#    allowed_domains = ['crawl-test-site.webarchive.org.uk']
#    start_urls = ['http://crawl-test-site.webarchive.org.uk/']
    allowed_domains = ['data.webarchive.org.uk']

    def __init__(self, *args, **kwargs):
        super(CrawlTestSiteSpider, self).__init__(*args, **kwargs)
        self.le = LinkExtractor()

    def parse(self, response):
        if not isinstance(response, HtmlResponse):
            return

        for link in self.le.extract_links(response):
            r = Request(url=link.url)
            r.meta.update(link_text=link.text)
            self.log("GOT %s to yield..." % r)
            yield r

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = cls(*args, **kwargs)
        spider._set_crawler(crawler)
        spider.crawler.signals.connect(spider.spider_idle, signal=signals.spider_idle)
        return spider

    def spider_idle(self):
        self.log("Spider idle signal caught.")
        raise DontCloseSpider