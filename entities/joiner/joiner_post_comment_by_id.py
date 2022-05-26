import logging
import os
import time

from common.middleware.middleware import Middleware
from common.constants import FINISH_PROCESSING_TYPE, COMMENT_WITH_POST_INFO_TYPE


class Entity:
    def __init__(self, base_config, pipeline_config):
        broker_config = base_config["broker_config"]
        entity_name = base_config["entity_name"]
        entity_config = pipeline_config[entity_name]
        self.entity_name = entity_name

        self._recv_posts_queue_config = pipeline_config["queues"][entity_config["recv_posts_queue"]]
        self._recv_comments_queue_config = pipeline_config[
            "queues"][entity_config["recv_comments_queue"]]

        self._send_exchanges = entity_config["send_exchanges"]

        self.entity_sub_id = os.environ["ENTITY_SUB_ID"]

        self._middleware = Middleware(broker_config, pipeline_config)

        # Initialize post consuming
        self._post_map = {}
        self._start_time = time.time()
        self._n_joins = 0

    def start_consuming_comments(self):
        self._start_consuming_comments_time = time.time()

        logging.info("Finished consuming posts: total_posts: {} time_elapsed: {} mins".format(
            len(self._post_map), (self._start_consuming_comments_time - self._start_time) / 60))

        self._middleware.start_consuming(
            self._recv_comments_queue_config, self.join_comment_with_post, self.stop, self.entity_sub_id)

    def run(self):
        self._middleware.start_consuming(
            self._recv_posts_queue_config, self.process_post, self.start_consuming_comments, self.entity_sub_id)

    def stop(self):
        logging.info("Finished joining comments with posts: total_joins: {} time_elapsed: {} mins".format(
            self._n_joins, (time.time() - self._start_consuming_comments_time) / 60))

        self._middleware.send_termination(self._send_exchanges, {
                                          "type": FINISH_PROCESSING_TYPE})

        self._middleware.stop_consuming()

    def process_post(self, post):
        post_id = post["id"]
        del post["id"]
        del post["type"]
        self._post_map[post_id] = post

    def join_comment_with_post(self, comment):
        self._n_joins += 1
        del comment["type"]

        post_data = self._post_map.get(comment["post_id"], None)
        if not post_data:
            # logging.info("dropping comment with post_id: {} because it does not have post data associated (it was filtered if existent)".format(
            #     comment["post_id"]))
            return

        join_result = {**comment, **post_data}
        join_result["type"] = COMMENT_WITH_POST_INFO_TYPE

        # logging.debug("Sending joined post/comment: {}".format(join_result))

        self._middleware.send(self._send_exchanges, join_result)
