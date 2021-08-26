import logging
from frontera.contrib.backends.sqlalchemy import Distributed

class DistributedPartitionedBackend(Distributed):
    def __init__(self, manager):
        settings = manager.settings

        super(DistributedPartitionedBackend, self).__init__(manager)

        # Set up partition assignment (if defined):
        self.partition_id = int(settings.get('SPIDER_PARTITION_ID'))
        if self.partition_id < 0 or self.partition_id >= settings.get('SPIDER_FEED_PARTITIONS'):
            raise ValueError("Spider partition id cannot be less than 0 or more than SPIDER_FEED_PARTITIONS.")
        self.partitions = [self.partition_id]

        self._logger = logging.getLogger("distributed-partitioned-backend")
        self._logger.info(f"Processing queue partitions {self.partitions}")
        self._logger.info(f"Processing {settings.get('SPIDER_PARTITION_ID')}")
        exit
        
    def get_next_requests(self, max_next_requests, **kwargs):
        batch = []
        for partition_id in self.partitions:
            batch.extend(self.queue.get_next_requests(max_next_requests, partition_id, **kwargs))
        return batch