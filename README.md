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
- Work out how to integrate with ideas like [ukwa/glean](https://github.com/ukwa/glean), which is an experiment in harvesting data from the archived web.  Can we meaningfully bring post-crawl patch/extract and crawl-time capture together, or are they better apart?


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