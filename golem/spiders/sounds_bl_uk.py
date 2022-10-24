# -*- coding: utf-8 -*-
import time
import scrapy
from pathlib import Path
from scrapy_playwright.page import PageMethod

class SoundsBlUkSpider(scrapy.Spider):
    name = 'sounds.bl.uk'

    # Include domain sounds files get served from:
    allowed_domains = ['sounds.bl.uk', '194.66.233.31']
    # Just use the hopepage as a seed:
    start_urls = [
#        'http://sounds.bl.uk/',
        # This page has two highlight players and two tree tabs:
        'https://sounds.bl.uk/Arts-literature-and-performance/Theatre-Archive-Project'
        #'http://sounds.bl.uk/Sound-recording-history/Equipment'
    ]

    

    def start_requests(self):
        # Load userscript
        path = Path(__file__).parent / "..//userscripts/sounds-bl.uk.user.js"
        with path.open() as f:
            userscript = f.read()
        # Launch
        for url in self.start_urls:
            yield scrapy.Request(
                url=url,
                meta=dict(
                    playwright=True,
                    playwright_context=1,
                    playwright_page_methods=[
                        PageMethod("evaluate", userscript),
                    ],
                )
            )

    async def parse(self, response):
        self.logger.info(f"RESPONSE has {len(response.css('a::attr(href)'))} links.")
        for href in response.css('a::attr(href)'):
            self.logger.info(f"LINK: {response.urljoin(href.extract())}")
            #yield response.follow(href, self.parse)

    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_CONTEXTS": {
            1: {
                "ignore_https_errors": True,
                "proxy": {
                    "server": "http://localhost:8080",
                },
            },
        }
    }
