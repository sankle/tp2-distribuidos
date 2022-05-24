import os
import logging

from common.basic_filter import BasicFilter
from common.constants import FINISH_PROCESSING_TYPE


class Entity(BasicFilter):
    def __init__(self, base_config, pipeline_config):
        BasicFilter.__init__(
            self, base_config, pipeline_config, self.callback, self.stop)

        self.score_count = 0
        self.score_sum = 0

    def stop(self):
        post_avg_score = 0

        if self.score_count:
            post_avg_score = self.score_sum // self.score_count

        self._middleware.send(self._send_exchange_name, {
            "post_avg_score": post_avg_score})

        self._middleware.send_termination(self._send_exchange_name, {
                                          "type": FINISH_PROCESSING_TYPE})

        # TODO: finalize execution

    def callback(self, _ch, _method, _properties, input):
        logging.info("[{}] Received post: {}".format(
            self.entity_name, input))

        self.score_count += 1
        self.score_sum += int(input["score"])

        logging.info("[{}] Partial results - count: {} sum: {}".format(
            self.entity_name, self.score_count, self.score_sum))
