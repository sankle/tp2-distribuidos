import logging

from common.basic_filter import BasicFilter
from common.constants import FINISH_PROCESSING_TYPE, POST_WITH_MAX_AVG_SENTIMENT_TYPE


class Entity(BasicFilter):
    def __init__(self, base_config, pipeline_config):
        BasicFilter.__init__(
            self, base_config, pipeline_config, self.callback, self.stop)

        self._max_avg_sentiment_post = (None, None, None)

    def stop(self):
        result = {
            "type": POST_WITH_MAX_AVG_SENTIMENT_TYPE, "post_id": self._max_avg_sentiment_post[0], "url": self._max_avg_sentiment_post[1], "post_avg_sentiment": self._max_avg_sentiment_post[2]}

        logging.info("Result: post_with_max_avg_sentiment: {}".format(
            self._max_avg_sentiment_post))

        self._middleware.send(self._send_exchanges, result)

        self._middleware.send_termination(self._send_exchanges, {
                                          "type": FINISH_PROCESSING_TYPE})

        self._middleware.stop_consuming()

    def callback(self, input):
        # logging.info("input: {}, _max_avg_sentiment_post: {}, value: {}".format(
        # input, self._max_avg_sentiment_post, self._max_avg_sentiment_post[2]))

        # filter posts without url
        if not input["url"]:
            return

        input_max_avg_sentiment = float(input["avg_sentiment"])
        if self._max_avg_sentiment_post[2] == None or self._max_avg_sentiment_post[2] < input_max_avg_sentiment:
            self._max_avg_sentiment_post = (
                input["post_id"], input["url"], input_max_avg_sentiment)
