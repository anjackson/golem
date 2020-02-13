# -*- coding: utf-8 -*-
import scrapy


class SoundsBlUkSpider(scrapy.Spider):
    name = 'sounds.bl.uk'
    allowed_domains = ['sounds.bl.uk']
    start_urls = ['http://sounds.bl.uk/']

    def parse(self, response):
        pass
