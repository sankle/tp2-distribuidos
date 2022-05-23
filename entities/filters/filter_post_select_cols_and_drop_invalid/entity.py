import logging

from middleware.middleware import Middleware


class Entity:
    def __init__(self, base_config, pipeline_config):
        self.entity_name = base_config["entity_name"]
        self._pipeline_config = pipeline_config

        self._middleware = Middleware(base_config["broker_config"], self)

    def callback(self, ch, method, properties, body):
        logging.info("[{}] Received body: {}".format(
            self.entity_name, body))

    def run(self):
        recv_exchange_config = self._pipeline_config["exchanges"][
            self._pipeline_config[self.entity_name]["recv_exchange"]]
        recv_queue_config = self._pipeline_config["queues"][
            self._pipeline_config[self.entity_name]["recv_queue"]]

        self._middleware.create_filter(
            recv_exchange_config, recv_queue_config, self.callback)
