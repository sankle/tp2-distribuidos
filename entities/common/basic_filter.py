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
        self._send_exchange_name = entity_config["send_exchange"]
        self.entity_sub_id = entity_sub_id
        self.callback = callback
        self.stop_callback = stop_callback
        self.n_pending_end_msgs = int(
            os.environ.get("N_END_MESSAGES_EXPECTED", "1"))
        self._middleware = Middleware(broker_config, pipeline_config)

    def callback_wrapper(self, ch, method, properties, input):
        if input["type"] == FINISH_PROCESSING_TYPE:
            self.n_pending_end_msgs -= 1
            if not self.n_pending_end_msgs:
                logging.info("Terminating...")
                return self.stop_callback()
            logging.info("Received termination. Pending terminations: {}".format(
                self.n_pending_end_msgs))
            return
        return self.callback(ch, method, properties, input)

    def run(self):
        self._middleware.create_filter(
            self._recv_queue_config, self.callback_wrapper, self.entity_sub_id)
