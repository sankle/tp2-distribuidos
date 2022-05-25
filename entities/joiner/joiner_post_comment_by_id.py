import logging
import os

from common.middleware.middleware import Middleware
from common.constants import FINISH_PROCESSING_TYPE


class Entity:
    def __init__(self, base_config, pipeline_config):
        broker_config = base_config["broker_config"]
        entity_name = base_config["entity_name"]
        entity_config = pipeline_config[entity_name]
        self.entity_name = entity_name

        recv_posts_queue_config = pipeline_config["queues"][entity_config["recv_posts_queue"]]
        self._recv_comments_queue_config = pipeline_config[
            "queues"][entity_config["recv_comments_queue"]]

        self._send_exchanges = entity_config["send_exchanges"]

        self.entity_sub_id = os.environ["ENTITY_SUB_ID"]

        os.environ["N_END_MESSAGES_EXPECTED"] = os.environ["N_END_MESSAGES_EXPECTED_FROM_POSTS"]

        self._middleware = Middleware(broker_config, pipeline_config)

        # Initialize post consuming
        self._post_map = {}
        self._middleware.start_consuming(
            recv_posts_queue_config, self.process_post, self.__start_consuming_comments, self.entity_sub_id)

    def __start_consuming_comments(self):
        logging.info("Finished consuming posts: total_posts: {}".format(
            len(self._post_map)))
        os.environ["N_END_MESSAGES_EXPECTED"] = os.environ["N_END_MESSAGES_EXPECTED_FROM_COMMENTS"]
        self._middleware.start_consuming(
            self._recv_comments_queue_config, self.join_comment_with_post, self.stop, self.entity_sub_id)

    def stop(self):
        self._middleware.send_termination(self._send_exchanges, {
                                          "type": FINISH_PROCESSING_TYPE})
        # TODO: finalize execution

    def process_post(self, post):
        post_id = post["id"]
        del post["id"]
        del post["type"]
        self._post_map[post_id] = post

    def join_comment_with_post(self, comment):
        del comment["type"]

        post_data = self._post_map.get(comment["post_id"], None)
        if not post_data:
            # logging.info("dropping comment with post_id: {} because it does not have post data associated (it was filtered if existent)".format(
            #     comment["post_id"]))
            return

        join_result = {**comment, **post_data}
        join_result["type"] = "comment_with_post_info"

        # logging.debug("Sending joined post/comment: {}".format(join_result))

        self._middleware.send(self._send_exchanges, join_result)
