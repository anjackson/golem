# golem
Experimental crawler using Scrapy and Selenium

**NOTE: Highly likely to not work or change unexpectedly!!!**

# Introduction

Inspired by [Brozzler](https://github.com/internetarchive/brozzler), [Memento Tracer](http://tracer.mementoweb.org/) and [WebRecorder Autopilot](https://guide.webrecorder.io/autopilot/), this is an attempt to build a scalable crawler that can be 'trained' by general users in order to interact properly with complex websites.

This prototype is built on [Selenium](https://selenium.dev/), [Scrapy](https://scrapy.org/) and [warcprox](https://github.com/internetarchive/warcprox).

# Current Workflow

Users can install the [Selenium IDE](https://selenium.dev/selenium-ide/) browser plugin to create and test macros that interact with 'difficult' pages.  The goal here is to ensure all necessary dynamic dependencies within one page are revealed, rather than attempting to crawl the site.

These macros can be saved and maintained as [SIDE](https://selenium.dev/selenium-ide/docs/en/introduction/getting-started#save-your-work) files, and [exported as Python `pytest` code](https://selenium.dev/selenium-ide/docs/en/introduction/code-export#python-pytest).

The Python code is then used to create suitable code to run in a Scrapy crawler (by hand, but see [below](#future-plans)). This spider talks to [Selenium Grid](https://selenium.dev/documentation/en/grid/) via the [scrapy-headless](https://github.com/scrapy-plugins/scrapy-headless) model.  The web browsers that serve the Selenium Grid are configured to use warcprox as a web proxy, and therefore every request and response the browsers make will be captured in a WARC file.

The rest of the crawler workflow (enqueuing and de-duping URLs, scope, robots.txt etc.) is all just the standard Scrapy stuff.

# Running the crawler.

You need a suitable Selenium Grid instance, e.g. for development:

    cd golem
    docker-compose up -d

Then you can run the crawler:

    cd golem
    export SELENIUM_GRID_URL="http://localhost:4444/wd/hub"
    scrapy crawl sounds.bl.uk


# Future Plans

## Automated Workflow Execution

The recent work on Selenium IDE offers a couple of way things could be made easier in the future.

Firstly, the new SIDE file format is a fairly simple scripting language, quite similar to that proposed by the Memento Tracer project.  There is already a [standalone command-line runner](https://www.seleniumhq.org/selenium-ide/docs/en/introduction/command-line-runner/) for these files, and others have already made [some progress](https://github.com/side-runner-py/side-runner-py/issues/49) on a [Python implementation](https://github.com/side-runner-py/side-runner-py).

Therefore, in the future we many be able to use SIDE executor from within a larger crawler rather than manually porting the code.  Some conventions would have to be established around the format so the same macro could be run on different pages and integrate with the main crawl engine, but this should be workable.  However, the [SIDE language](https://selenium.dev/selenium-ide/docs/en/api/commands) is quite complex and [still growing](https://github.com/SeleniumHQ/selenium-ide/issues/182) so it's not clear how much work this will entail.

The second option comes from the fact that the Selenium IDE already support exporting tests as Python code.  The [code for the Python `pytest` exporter](https://github.com/SeleniumHQ/selenium-ide/tree/v3/packages/code-export-python-pytest/src) could be extended or adapted to emit Python code that the Scrapy crawler could invoke directly rather than being manually translated.  As with the previous option, some additional conventions would be required to store the SIDE files and associate them with the sites they can be used on, but with that in place, a standard build process (similar to [this](https://gist.github.com/varunnayak26/708f5d7e2c5c4b8db61a7a5a4a2a760f)) could create the python modules we need.

As the `pytest` export already exists, this second option is probably the most likely to work in the near term. It's also the easiest in terms of permitting co-existence between manually-created and SIDE-derived crawler modules within one codebase.  The main risk is that some small gaps in behaviour between implementation means it does't work as well as expected (e.g. when porting some code manually, it became clear the Scrapy version was going to fast and re-clicking elements as they changed state, leading to crashes).  Doing things like noting exceptions and capturing screenshots will help debug these problems.

## Other ideas

- Generic crawler that dynamically decides whether to use plain `ScrapyRequest` requests, or `HeadlessRequest`, or SIDE macros.
- Add intelligence to attempt to download transclusions when not using Selenium.
- Integrate with Crawl Index for recrawls, deduplication.
- Full gap evaluation against H3. e.g. can we live without the `hopPath`, etc. See internal ticket covering gaps.
- Scale tests, e.g. can we run our frequent crawl stream through this?
- Use `driver.save_screenshot` etc. and POST to `warcprox` like `webrender-puppeteer` does.
- Work out how to integrate with ideas like [ukwa/glean](https://github.com/ukwa/glean), which is an experiment in harvesting data from the archived web.  Can we meaningfully bring post-crawl patch/extract and crawl-time capture together, or are they better apart? (see 'unified patch crawling' below)
- Document Harvesting with Scrapy (collection side)
    - Custom scraper for www.gov.uk publications.
    - Generic scraper.
    - [Portia](https://github.com/scrapinghub/portia) setup for future scrapers?
- Automated QA and pre/post crawl render services 
    - Integrate with Memento Tracer?
    - Against pywb in patch mode? To integrate the crawling activity?

## Unified Patch Crawling

One idea would be to extend `warcprox` or `pywb` to support a time-aware patch mode. The crawlers could be adapted to send an `Accept-Datetime` header, which the proxy would then look-up in the OutbackCDX. If we already have copy of that URL on or after the requested date, the proxy returns that. Otherwise, the proxy reaches out to the live web and downloads from there, storing the result in a WARC and posting the outcome to OutbackCDX.

By having a target timestamp for a crawl of a given resource, we can more easily run multiple crawlers together. Each could run, and each would add requests for URLs the others missed, but re-use the resources that had already been successfully downloaded rather than always hitting the remote site.

Like the `launchTimestamp` in our current continuous crawler, we would have to extend the crawler(s) to include and propagate this timestamp as necessary.

If warcprox or pywb cannot be easily modified to work this way, adding a custom `mitmproxy` app to the chain [like this one](https://github.com/mitmproxy/mitmproxy/blob/master/examples/complex/change_upstream_proxy.py) would allow us to query the CDX and then decide which upstream proxy to use.

### Scrapy-only Unified Patch Crawling

Within Scrapy, we could mostly implement this by adding the 'accept-timestamp' as a `meta` field, and writing a suitable middleware module that checks if at item is already downloaded and returns that instead of using the normal downloader.  This would allow us to explore the issues without having to build/extend the existing tools.


### Limitations

The main problem is that we can't reliably add a header from Selenium crawlers (or even Puppeteer when it comes to Service Workers). If that remains the case, it's not clear what the semantics of 'no Accept-Datetime header' should be: capture or playback?

Perhaps multiple proxies could be used, one defaults to playback, the other to capture? i.e. when we're running crawl renderers it goes through the 'capture-by-default' proxy, but remaining requests go through a 'playback-by-default' service? 

Or maybe `capture-by-default` is fine because for all normal crawlers we can always add the `Accept-Datetime` header?

One possibility is that we could add an intermediary proxy that did some clever stuff with virtual hosts. e.g. if the proxy is set to e.g.:

    proxy-npld-20200101120000.api.wa.bl.uk # Mark as NPLD, set Accept-Datetime: ~2020-01-01T12:00:00.000Z
    proxy-npcl-record.api.wa.bl.uk         # Mark as NPLD, force all activity to be recorded.
    proxy-replay.api.wa.bl.uk              # Force only-replay (no recording).

This could be turned into a call to an upstream instance of `warcprox`/`pywb` with the appropriate NPLD and `Accept-Datetime` headers set. As indicated above, this could likely be implemented as a `mitmproxy` app, or if the upstream can handle the CDX-lookup part, perhaps just using NGINX.


## Heritrix Alternative?

Currently we are only considering Scrapy as an additional crawler for sites that present particular problems to our main Heritrix3 crawler.  That said, it's interesting to consider what it would take to move all crawling to a Scrapy-behind-warcprox model.

The core crawling functionality of Scrapy is great:

- It’s in Python, so is easier for the in-house team to support.
- it’s better suited to the integration required for behind-paywall access 
- it’s focussed on scraping so would be a good fit for the Document Harvester use case
- it has support for a fairly scalable QT-based renderer: https://github.com/scrapinghub/splash/
- it has support for less-scalable but still handy Selenium-based rendering.
- Although not an official module, there is a solution for Prometheus integration (https://github.com/sashgorokhov/scrapy_prometheus)
- There is `scrapyd` for managing many crawlers.
- has a large community, lots of online support etc. That community may be interested in the archival tooling too!
- we can get third-party support if we need it (ScrapingHub and others)

But there are some known gaps:

- virus scanning will need to become a post-processing task in warcprox (via it's plugins).
- may be difficult to implement scoping precisely as Heritrix3 does it.
    - e.g. no hop-path concept - that would have to be added if needed.
    - Not clear how to do quotas.
- may be difficult to implement extraction like H3 does it:
    - Scrapy crawlers are often written in quite a specific way per host, e.g. SitemapCrawler. We would want a more dynamically mouldable ('clay') crawler that is content-type aware and parameterised from outside for each crawl target.
    - We also need it to extract ALL links, rather than the current focus on e.g. `a href`.
    - Sitemap extraction would need to intercept robots.txt downloads.
    - The caching would need to be understood, e.g. robots.txt refreshed every 24 hrs?
- would need to set up crawl-log entries as scraped Items and keep the log
- we’ll be alone among our web-archiving peers as AFAIK everyone else uses Heritrix3 or Brozzler.


## Example of SIDE output

This is an example of the `pytest` code the current SIDE exporter produces:

```python
# Generated by Selenium IDE
import pytest
import time
import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities

class TestDefaultSuite():
  def setup_method(self, method):
    self.driver = webdriver.Remote(command_executor='http://localhost:4444/wd/hub', desired_capabilities=DesiredCapabilities.CHROME)
    self.vars = {}
  
  def teardown_method(self, method):
    self.driver.quit()
  
  def test_soundsRecordingHistoryEquipment(self):
    self.driver.get("https://sounds.bl.uk/")
    self.driver.set_window_size(1312, 989)
    self.driver.find_element(By.CSS_SELECTOR, "#ui-id-3 > span").click()
    self.driver.find_element(By.CSS_SELECTOR, "#ui-id-2 > span").click()
    self.driver.find_element(By.LINK_TEXT, "Radio & sound recording history").click()
    element = self.driver.find_element(By.LINK_TEXT, "Radio & sound recording history")
    actions = ActionChains(self.driver)
    actions.move_to_element(element).perform()
    element = self.driver.find_element(By.CSS_SELECTOR, "#equipmentLink img")
    actions = ActionChains(self.driver)
    actions.move_to_element(element).perform()
    self.driver.find_element(By.CSS_SELECTOR, "#equipmentLink img").click()
    WebDriverWait(self.driver, 30000).until(expected_conditions.presence_of_element_located((By.CSS_SELECTOR, ".viewByCollectionNavTree")))
    condition = True
    while condition:
      self.driver.find_element(By.CSS_SELECTOR, "li.closed a").click()
      self.vars["toclose"] = len(self.driver.find_elements(By.XPATH, "//div[@aria-hidden=\'false\']/nav/ul/li[@class=\'closed\']/a"))
      print(str("toclose = self.vars["toclose"]"))
      condition = self.driver.execute_script("return (arguments[0] > 0)", self.vars["toclose"])
  
```