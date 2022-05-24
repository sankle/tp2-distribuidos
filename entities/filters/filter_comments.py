import logging
import os
import re

from common.basic_filter import BasicFilter
from common.constants import FINISH_PROCESSING_TYPE


class Entity(BasicFilter):
    def __init__(self, base_config, pipeline_config):
        BasicFilter.__init__(self, base_config, pipeline_config,
                             self.callback, self.stop, os.environ["ENTITY_SUB_ID"])

    def stop(self):
        self._middleware.send_termination(self._send_exchange_name, {
                                          "type": FINISH_PROCESSING_TYPE})
        # TODO: finalize execution

    def callback(self, _ch, _method, _properties, input):
        logging.info("Received comment: {}".format(input))

        parsed_comment = {"type": "comment"}
        keys_to_extract = ['body', 'sentiment']

        for k in keys_to_extract:
            # TODO: verify criteria
            if not input[k]:
                return
            parsed_comment[k] = input[k]

        # Extract post_id from url
        try:
            post_id = re.search(
                'https://old.reddit.com/r/meirl/comments/([^/]+)/meirl/.*', input["permalink"]).group(1)
        except AttributeError:
            # post_id not found
            return

        parsed_comment["post_id"] = post_id

        logging.info("Sending parsed comment: {}".format(parsed_comment))
        self._middleware.send(self._send_exchange_name, parsed_comment)
