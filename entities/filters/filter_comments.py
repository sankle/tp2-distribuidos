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
        self._middleware.send_termination(self._send_exchanges, {
                                          "type": FINISH_PROCESSING_TYPE})
        # TODO: finalize execution

    def callback(self, input):
        logging.info("Received comment: {}".format(input))

        parsed_comment = {"type": "comment"}
        keys_to_extract = ['body', 'sentiment']

        for k in keys_to_extract:
            # TODO: verify filter invalid criteria
            v = input.get(k)
            if not v:
                logging.info(
                    "Dropping invalid comment: missing or invalid {}: {}".format(input, k, v))
                return
            parsed_comment[k] = v

        try:
            float(parsed_comment["sentiment"])
        except ValueError:
            logging.info(
                "Dropping invalid comment: sentiment is not numeric: {}".format(parsed_comment['sentiment']))
            return

        # Extract post_id from url
        try:
            post_id = re.search(
                'https://old.reddit.com/r/meirl/comments/([^/]+)/meirl/.*', input["permalink"]).group(1)
        except AttributeError:
            # post_id not found
            return

        parsed_comment["post_id"] = post_id

        logging.info("Sending parsed comment: {}".format(parsed_comment))
        self._middleware.send(self._send_exchanges, parsed_comment)
