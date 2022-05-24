import logging
import os

from common.basic_filter import BasicFilter
from common.constants import FINISH_PROCESSING_TYPE


class Entity(BasicFilter):
    def __init__(self, base_config, pipeline_config):
        BasicFilter.__init__(self, base_config, pipeline_config,
                             self.callback, self.stop, os.environ["ENTITY_SUB_ID"])

    def stop(self):
        self._middleware.send_termination(self._send_exchange_name, {
                                          "type": FINISH_PROCESSING_TYPE})

    def callback(self, _ch, _method, _properties, input):
        logging.info("Received post: {}".format(input))

        parsed_post = {"type": "post"}
        keys_to_extract = ['id', 'url', 'score']

        for k in keys_to_extract:
            # TODO: verify filter invalid criteria
            if not input[k]:
                return
            parsed_post[k] = input[k]

        logging.info("Sending parsed post: {}".format(parsed_post))

        self._middleware.send(self._send_exchange_name, parsed_post)
