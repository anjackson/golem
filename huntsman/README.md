Huntsman
========

Experimenting with Frontera

The processes starts when we load seeds in using the Strategy Worker:

    python -m frontera.worker.strategy  --config huntsman.config.sw --add-seeds --seeds-url file:///Users/andy/absolute-path/seeds.txt

This scores the seed URLs and places them on the `frontier-score` queue. A DB worker processes these incoming, scored URLs:

    python -m frontera.worker.db  --config huntsman.config.dbw --partitions 0 1 --no-batches

This reads the `frontier-score` queue and pushes the content into the `queue` table of the database. A separate DB worker:

    python -m frontera.worker.db  --config huntsman.config.dbw --partitions 0 1 --no-incoming

...reads the `queue` table and breaks the prioritised queue down into batches to be sent to the crawlers, posting them onto the `frontier-todo` queue. For each partition we have a crawler instance:

     scrapy crawl crawl-test-site -L INFO -s SPIDER_PARTITION_ID=0

The spiders download the URLs and extract the links. The results are posted onto the `frontier-done` queue, as a stream of different events. There are `page-crawled` events, `links-extracted` events (where one message lists all the URLs from one response), and `offset` events that indicate where the spiders have got to in the queue partition they are processing.

(AFIACT) the DB workers and the Strategy Worker:

    python -m frontera.worker.strategy  --config huntsman.config.sw --partitions 0 1

...all read the `frontier-done` queue, and update the state they are responsible for accordingly. Tasks that get done are:

- The crawled items update(?) the `metadata` table to refect that they've been downloads. (Incoming DB worker?)
- The `offset` events are used to keep track of where the spiders have got to (Batching DB worker)
- The extracted links are scored and enqueued in the `frontier-score` queue, and the cycle continues.

Overall, Frontera has lots of good ideas to learn from, but is also somewhat confusing and the documentation appears to be out of date (probably just by one release).  Using different message types in a single single stream is rather clumsy -- Kafka's design (e.g keys and compaction) and my preference leans towards having separate queues for different message types.

