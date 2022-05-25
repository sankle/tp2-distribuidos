import logging
import os

from common.basic_filter import BasicFilter
from common.constants import FINISH_PROCESSING_TYPE


class Entity(BasicFilter):
    def __init__(self, base_config, pipeline_config):
        BasicFilter.__init__(self, base_config, pipeline_config,
                             self.callback, self.stop, os.environ["ENTITY_SUB_ID"])

    def stop(self):
        self._middleware.send_termination(self._send_exchanges, {
                                          "type": FINISH_PROCESSING_TYPE})

    def callback(self, input):
        logging.info("Received post: {}".format(input))

        parsed_post = {"type": "post"}
        keys_to_extract = ['id', 'url', 'score']

        for k in keys_to_extract:
            # TODO: verify filter invalid criteria
            v = input.get(k)
            if not v:
                logging.info(
                    "Dropping invalid post: missing or invalid {}: {}".format(k, v))
                return
            parsed_post[k] = v

        if not parsed_post['score'].isnumeric():
            logging.info(
                "Dropping invalid post: score is not numeric: {}".format(parsed_post['score']))
            return

        logging.info("Sending parsed post: {}".format(parsed_post))

        self._middleware.send(self._send_exchanges, parsed_post)
