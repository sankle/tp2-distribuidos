import logging
import os

from common.basic_filter import BasicFilter
from common.constants import FINISH_PROCESSING_TYPE


class Entity(BasicFilter):
    def __init__(self, base_config, pipeline_config):
        BasicFilter.__init__(self, base_config, pipeline_config,
                             self.callback, self.stop, os.environ["ENTITY_SUB_ID"])
        self._post_sum_count = {}  # {post_id: (count, sum)}

    def __send_results(self):
        logging.info("Finished processing: n_posts_processed: {}".format(
            len(self._post_sum_count)))
        for (post_id, data) in self._post_sum_count.items():
            avg_sentiment = data[1] / data[0]
            payload = {"type": "post_avg_sentiment", "post_id": post_id,
                       "avg_sentiment": avg_sentiment, "url": data[2]}
            self._middleware.send(self._send_exchanges, payload)

    def stop(self):
        self.__send_results()
        self._middleware.send_termination(self._send_exchanges, {
                                          "type": FINISH_PROCESSING_TYPE})

    def callback(self, input):
        post_id = input["post_id"]
        (partial_count, partial_sum, url) = self._post_sum_count.get(
            post_id, (0, 0, ''))
        partial_count += 1
        partial_sum += float(input["sentiment"])
        self._post_sum_count[post_id] = (
            partial_count, partial_sum, input["url"])
