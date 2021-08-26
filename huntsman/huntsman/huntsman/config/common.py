# -*- coding: utf-8 -*-
from frontera.settings.default_settings import MIDDLEWARES

MAX_NEXT_REQUESTS = 512
SPIDER_FEED_PARTITIONS = 2
SPIDER_LOG_PARTITIONS = 2
#SPIDER_FEED_GROUP= 'nuspider'
DELAY_ON_EMPTY = 5.0

MIDDLEWARES.extend([
    'frontera.contrib.middlewares.domain.DomainMiddleware',
    'frontera.contrib.middlewares.fingerprint.DomainFingerprintMiddleware'
])

LOCAL_MODE = True

#--------------------------------------------------------
# Crawl frontier backend
#--------------------------------------------------------
QUEUE_HOSTNAME_PARTITIONING = True
URL_FINGERPRINT_FUNCTION='frontera.utils.fingerprint.hostname_local_fingerprint'

#MESSAGE_BUS='frontera.contrib.messagebus.kafkabus.MessageBus'
#KAFKA_LOCATION = 'kafka:9092'
#KAFKA_GET_TIMEOUT = 5.0
#SCORING_GROUP = 'scrapy-scoring'
#SCORING_TOPIC = 'frontier-score'

#MESSAGE_BUS_CODEC='frontera.contrib.backends.remote.codecs.json'
#MESSAGE_BUS_CODEC='huntsman.codecs.yaml'

#STRATEGY='frontera.strategy.depth.BreadthFirstCrawlingStrategy'
