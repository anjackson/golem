# Golem<sup>[*](#golem-link)</sup>
Experimental crawler using Scrapy and Playwright.

**NOTE: Highly likely to not work or change unexpectedly!!!**

# Introduction

Inspired by [Brozzler](https://github.com/internetarchive/brozzler), [Memento Tracer](http://tracer.mementoweb.org/) and [WebRecorder Autopilot](https://guide.webrecorder.io/autopilot/), this is an attempt to build a scalable crawler that can be 'trained' by general users in order to interact properly with complex websites.

It's pretty similar to the more mature [Browsertrix Crawler](https://github.com/webrecorder/browsertrix-crawler). The main idea of this project is to see if we can mix browser-based crawling with traditional crawling so we can run at scale, while relying wherever possible on Scrapy rather that writing our own code.

Currently we are only considering Scrapy as an additional crawler for sites that present particular problems to our main Heritrix3 crawler.  That said, it's interesting to consider what it would take to move all crawling to a Scrapy-behind-warcprox model.


## Why Scrapy?

The core crawling functionality of Scrapy is great:

- It’s in Python, so is easier for the in-house team to support.
- it’s better suited to the integration required for behind-paywall access 
- it’s focussed on scraping so would be a good fit for the Document Harvester use case
- it has various modules for browser-based crawling: [Splash](https://github.com/scrapinghub/splash/), [scrapy-headless for Selenium](https://github.com/scrapy-plugins/scrapy-headless), scrapy-playwright.
- Although not official modules, there is a solution for Prometheus integration (https://github.com/sashgorokhov/scrapy_prometheus) and one for Kafka integration [scrapy-kafka-export](https://github.com/TeamHG-Memex/scrapy-kafka-export)
- There is `scrapyd` for managing many crawlers.
- There are also things like [scrapy-cluster](https://github.com/istresearch/scrapy-cluster) and [`Frontera`](https://github.com/scrapinghub/frontera) which support large-scale crawler systems (and which I managed to get [basically working before](https://github.com/anjackson/anjackson.github.io/blob/d2e33c37d81cb10f8a921f6637a5090a2a625348/digipres-lessons-learned/index.md#experimenting-with-frontera)).
- has a large community, lots of online support, [good docs](https://docs.scrapy.org/en/latest/index.html) etc. That community may be interested in the archival tooling too!
- we can get third-party support if we need it (ScrapingHub and others)

But there are some gaps...

# Roadmap

To explore whether this can work, there's a plan to cover a few different use cases via a development roadmap.

## A well-known-URI scanner

As a first case, it would be good to explore a UK domain scanner. Currently, we run this as part of the full domain crawl, but it would be good to have this as a previous step. The goal is:

- Take a list of all known UK domains. For each domain:
    - [ ] Check if it's working/presenting web pages.
    - [ ] Check for all well-known URIs (e.g. `ads.txt` etc.) but do so slowly as quick 404s in succession tend to cause problems. (a DownloaderMiddleware that requests them)
- Expected output:
    - [ ] Capture all requests-responses in WARC.
    - [ ] H3-style crawl log: Log all URL outcomes, e.g. those that get dropped due to e.g. robots.txt exclusion.

This would explore some of the scale issues. For example, if we just use a fairly vanilla Scrapy set up, can we scan 10 million domains quickly? Or do we need to crack out URLFrontier? Or some othe way of scaling up?

## A tricky site

Use scrapy-playwright and custom scripts in a dedicated spider to archive a tricky site and verify we can play it back again. e.g. 206/200 issue.

## A frequent crawl engine

 - [ ] WARC archiving proxy must de-duplicate.
 - [ ] Continuous crawling support, refreshing seeds and sitemaps, but possible to request full re-crawls. 
 - [ ] Consider URLFrontier integration (as per [scrapy-url-frontier](https://github.com/anjackson/scrapy-url-frontier)).
 - [ ] Run seeds through rendering engine. Capture results as per `webrender-puppeteer`
 - [ ] Refresh robots.txt.
 - [ ] Intercept robots.txt to schedule fetch and refresh of site maps.
 - [ ] Implement crawl quotas.
 - [ ] Hop path (`HopPathSpiderMiddleware`)
 - [ ] Scan content for viruses (in the proxy).
 - [ ] Update Kafka crawl log.
 - [ ] Update crawl CDX.
 - [ ] Add link extraction for embeds etc (not just `<a href="...">`)
 - [ ] BEYOND SCOPE? Extend 

## A domain crawl engine

Can we bring this together to run at very large scale? Perhaps integrating with URLFrontier?

## Document harvesting

Work out how to integrate with ideas like [ukwa/glean](https://github.com/ukwa/glean), which is an experiment in harvesting data from the archived web.  Can we meaningfully bring post-crawl patch/extract and crawl-time capture together, or are they better apart? (see 'unified patch crawling' below)

- Document Harvesting with Scrapy (collection side)
    - Custom scraper for www.gov.uk publications.
    - Generic scraper.
    - [Portia](https://github.com/scrapinghub/portia) setup for future scrapers?


## Notes on Scrapy via an archiving proxy:

This works...

```bash
$ docker compose up -d pywb-warcprox
$ https_proxy=http://localhost:8080 https_proxy=http://localhost:8080 scrapy crawl warchiver -a seeds=test-seeds.txt 
```

BUT note that DNS failures don't report as such, just as `400 Client Error: Bad Request for url` from PyWB and `504 Gateway Timeout` from warcprox.



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


----

<a name="golem-link">*</a>: https://en.wikipedia.org/wiki/Golems_(Discworld)
