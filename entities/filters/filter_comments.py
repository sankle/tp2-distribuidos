import logging
import os
import re
import time

from common.basic_filter import BasicFilter
from common.constants import FINISH_PROCESSING_TYPE, COMMENT_TYPE


class Entity(BasicFilter):
    def __init__(self, base_config, pipeline_config):
        BasicFilter.__init__(self, base_config, pipeline_config,
                             self.callback, self.stop, os.environ["ENTITY_SUB_ID"])
        self._n_dropped_comments = 0
        self._n_processed_comments = 0

    def stop(self):
        logging.info("Finished: n_processed_comments: {} n_dropped_comments: {} time_elapsed: {} mins".format(
            self._n_processed_comments, self._n_dropped_comments, (time.time() - self._start_time) / 60))

        self._middleware.send_termination(self._send_exchanges, {
                                          "type": FINISH_PROCESSING_TYPE})

        self._middleware.stop_consuming()

    def callback(self, input):
        # logging.debug("Received comment: {}".format(input))
        self._n_processed_comments += 1
        parsed_comment = {"type": COMMENT_TYPE}
        keys_to_extract = ["body", "sentiment"]

        for k in keys_to_extract:
            # TODO: verify filter invalid criteria
            v = input.get(k)
            if not v:
                # logging.info(
                #     "Dropping invalid comment: missing or invalid {}: {}".format(input, k, v))
                self._n_dropped_comments += 1
                return
            parsed_comment[k] = v

        try:
            float(parsed_comment["sentiment"])
        except ValueError:
            # logging.info(
            #     "Dropping invalid comment: sentiment is not numeric: {}".format(parsed_comment['sentiment']))
            self._n_dropped_comments += 1
            return

        # Extract post_id from url
        try:
            post_id = re.search(
                'comments/([^/]+)/', input["permalink"]).group(1)
        except AttributeError:
            # post_id could not be extracted
            self._n_dropped_comments += 1
            return

        parsed_comment["post_id"] = post_id

        # logging.debug("Sending parsed comment: {}".format(parsed_comment))
        self._middleware.send(self._send_exchanges, parsed_comment)
