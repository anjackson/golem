# -*- coding: utf-8 -*-
from __future__ import absolute_import
from .common import *
from time import time


#BACKEND = 'frontera.contrib.backends.remote.messagebus.MessageBusBackend'

BACKEND = 'huntsman.backends.partitioned.DistributedPartitionedBackend'
SQLALCHEMYBACKEND_ENGINE = 'cockroachdb://root@localhost:26257/huntsman?sslmode=disable'
SQLALCHEMYBACKEND_ENGINE_ECHO = False
SQLALCHEMYBACKEND_DROP_ALL_TABLES = False
SQLALCHEMYBACKEND_CLEAR_CONTENT = False
from datetime import timedelta
SQLALCHEMYBACKEND_REVISIT_INTERVAL = timedelta(days=3)

SQLALCHEMYBACKEND_MODELS = {
    'MetadataModel': 'huntsman.crdb.models.MetadataModel',
    'QueueModel': 'huntsman.crdb.models.QueueModel',
    'StateModel': 'huntsman.crdb.models.StateModel',
    'DomainMetadataModel': 'huntsman.crdb.models.DomainMetadataModel'
}

MAX_NEXT_REQUESTS = 2048
NEW_BATCH_DELAY = 3.0

