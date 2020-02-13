# -*- coding: utf-8 -*-
import time
import scrapy
from scrapy_headless import HeadlessRequest
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class SoundsBlUkSpider(scrapy.Spider):
    name = 'sounds.bl.uk'

    # Include domain sounds files get served from:
    allowed_domains = ['sounds.bl.uk', '194.66.233.31']
    # Just use the hopepage as a seed:
    start_urls = [
#        'http://sounds.bl.uk/',
        'http://sounds.bl.uk/Sound-recording-history/Equipment'
    ]

    def start_requests(self):
        for url in self.start_urls:
            yield HeadlessRequest(url=url, 
                callback=self.parse,
                driver_callback=self.run_macros)

    def parse(self, response):
        print("RESPONSE")
        print(len(response.css('a::attr(href)')))
        for href in response.css('a::attr(href)'):
            print(response.urljoin(href.extract()))
            #yield response.follow(href, self.parse)

    closed_list_css ='div[aria-hidden="false"] li[class="closed"] a'

    def get_closed_count(self, driver):
        return len(driver.find_elements(By.CSS_SELECTOR, self.closed_list_css))

    def run_macros(self, driver):
        print("MACROS")
        to_open = self.get_closed_count(driver)
        while to_open > 0:
            # Click on a closed list item:
            list_el = driver.find_element(By.CSS_SELECTOR, self.closed_list_css)
            list_el.click()
            # Wait for the click to be implemented:
            time.sleep(1)
            # Re-count items waiting to be opened:
            to_open = self.get_closed_count(driver)
            print("There are %i closed list items to open." % to_open)
        print("DONE MACROS %i" % to_open)
