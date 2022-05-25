import logging
import os
import re

from common.middleware.middleware import Middleware
from common.constants import FINISH_PROCESSING_TYPE, STUDENT_LIKED_POST_WITH_SCORE_AVG_HIGHER_THAN_MEAN_TYPE


class Entity:
    def __init__(self, base_config, pipeline_config):
        broker_config = base_config["broker_config"]
        entity_name = base_config["entity_name"]
        entity_config = pipeline_config[entity_name]
        self.entity_name = entity_name

        self._recv_post_avg_score_queue_config = pipeline_config[
            "queues"][entity_config["recv_post_avg_score_queue"]]
        self._recv_joined_post_comments_queue_config = pipeline_config[
            "queues"][entity_config["recv_joined_post_comments_queue"]]

        self._send_exchanges = entity_config["send_exchanges"]

        self.entity_sub_id = os.environ["ENTITY_SUB_ID"]

        os.environ["N_END_MESSAGES_EXPECTED"] = os.environ["N_END_MESSAGES_EXPECTED_FROM_POST_AVG_SCORE_CALCULATOR"]

        self._middleware = Middleware(broker_config, pipeline_config)

        self._student_regexp = re.compile(
            "(?:university|college|student|teacher|professor)", flags=re.IGNORECASE)

        self._post_avg_score = None

    def start_consuming_post_comments(self):
        logging.info("Finished consuming post_avg_score: {}".format(
            self._post_avg_score))
        if self._post_avg_score == None:
            self.stop()

        os.environ["N_END_MESSAGES_EXPECTED"] = os.environ["N_END_MESSAGES_EXPECTED_FROM_JOINER"]
        self._middleware.start_consuming(
            self._recv_joined_post_comments_queue_config, self.process_post_comments, self.stop, self.entity_sub_id)

    def run(self):
        self._middleware.start_consuming(
            self._recv_post_avg_score_queue_config, self.process_post_avg_score, self.start_consuming_post_comments, self.entity_sub_id)

    def stop(self):
        self._middleware.send_termination(self._send_exchanges, {
                                          "type": FINISH_PROCESSING_TYPE})

        self._middleware.stop_consuming()

    def process_post_avg_score(self, payload):
        self._post_avg_score = float(payload["post_avg_score"])

    def process_post_comments(self, post_comment):
        if float(post_comment["score"]) <= self._post_avg_score:
            # logging.debug("discarding post_comment {} with score {} < post_avg_score {}".format(
            # post_comment, post_comment["score"], self._post_avg_score))
            return

        result = {
            "type": STUDENT_LIKED_POST_WITH_SCORE_AVG_HIGHER_THAN_MEAN_TYPE, "post_id": post_comment["post_id"], "url": post_comment["url"], "score": post_comment["score"]}

        # logging.debug("Result: {}".format(result))

        self._middleware.send(self._send_exchanges, result)

    def stop(self):
        self._middleware.send_termination(self._send_exchanges, {
                                          "type": FINISH_PROCESSING_TYPE})

        self._middleware.stop_consuming()
