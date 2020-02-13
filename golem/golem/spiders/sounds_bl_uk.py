# -*- coding: utf-8 -*-
import scrapy
from scrapy_headless import HeadlessRequest

class SoundsBlUkSpider(scrapy.Spider):
    name = 'sounds.bl.uk'
    
    # Include domain sounds files get served from:
    allowed_domains = ['sounds.bl.uk', '194.66.233.31']
    # Just use the hopepage as a seed:
    start_urls = ['http://sounds.bl.uk/']

    def start_requests(self):
        for url in self.start_urls:
            yield HeadlessRequest(url=url, 
                callback=self.parse,
                driver_callback=self.run_macros)

    def parse(self, response):
        print("RESPONSE")
        print(response)
        print(response.request)
        pass

    def run_macros(self,driver):
        print("MACROS")
        print(driver)