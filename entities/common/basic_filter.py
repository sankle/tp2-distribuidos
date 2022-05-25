import logging
import os

from common.constants import FINISH_PROCESSING_TYPE
from common.middleware.middleware import Middleware


class BasicFilter:
    def __init__(self, base_config, pipeline_config, callback, stop_callback, entity_sub_id=None):
        broker_config = base_config["broker_config"]
        entity_name = base_config["entity_name"]
        entity_config = pipeline_config[entity_name]
        self.entity_name = entity_name
        self._recv_queue_config = pipeline_config["queues"][entity_config["recv_queue"]]
        self._send_exchanges = entity_config["send_exchanges"]
        self.entity_sub_id = entity_sub_id
        self.callback = callback
        self.stop_callback = stop_callback
        self._middleware = Middleware(broker_config, pipeline_config)

    def run(self):
        self._middleware.start_consuming(
            self._recv_queue_config, self.callback, self.stop_callback, self.entity_sub_id)
