# -*- coding: utf-8 -*-
import time
import scrapy
#from scrapy_headless import HeadlessRequest
#from selenium.webdriver.common.by import By
#from selenium.webdriver.support.ui import WebDriverWait
#from selenium.webdriver.support import expected_conditions as EC

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
        pass
        #for url in self.start_urls:
        #    yield HeadlessRequest(url=url, 
        #        callback=self.parse,
        #        driver_callback=self.run_macros)

    def parse(self, response):
        print("RESPONSE")
        print(len(response.css('a::attr(href)')))
        for href in response.css('a::attr(href)'):
            print(response.urljoin(href.extract()))
            #yield response.follow(href, self.parse)

    closed_list_css ='div[aria-hidden="false"] li[class="closed"] a'

    def get_closed_count(self, driver):
        return len(driver.find_elements(By.CSS_SELECTOR, self.closed_list_css))
    
    def open_all_visible_lists(self, driver):
        print("LISTS")
        to_open = self.get_closed_count(driver)
        while to_open > 0:
            # Click on a closed list item:
            list_el = driver.find_element(By.CSS_SELECTOR, self.closed_list_css)
            list_el.click()
            # Wait for the click to be implemented:
            time.sleep(0.5)
            # Re-count items waiting to be opened:
            to_open = self.get_closed_count(driver)
            print("There are %i closed list items to open." % to_open)

    def run_macros(self, driver):
        print("MACROS")
        # Make any players play:
        #
        # Unfortunately, this site uses Flash players via JavaScript via SWFObject
        # view-source:https://sounds.bl.uk/scripts/main.js
        # This makes 206 partial requests, and so warcprox doens't get the whole file.
        # It may be possible to interfere via a stacked mitmproxy that turns to 206 into a 200?
        # OR just grab all the URLs and download them separately.
        # A double-crawl like that would be clumsy but would work.
        # OR the WARCs could be post-processed, stripping out the 206s and
        # recording all URLs that had 206's and just getting those separately.
        for playable in driver.find_elements(By.CSS_SELECTOR, ".playable"):
            print("PLAY %s" % playable)
            playable.click()
            # Give it some time to get going...
            time.sleep(2)
        # Attempt to flip through all tabs:
        tab_num = 1
        while tab_num < 7:
            tab_selector = "a#ui-id-%i" % tab_num
            print("TAB %s" % tab_selector)
            # Check it exists:
            if driver.find_elements(By.CSS_SELECTOR, tab_selector):
                driver.find_element(By.CSS_SELECTOR, tab_selector).click();
                # Give it time to flip:
                time.sleep(2)
                # Now open any lists this revealed:
                self.open_all_visible_lists(driver)
            tab_num += 1
        print("DONE MACROS")
