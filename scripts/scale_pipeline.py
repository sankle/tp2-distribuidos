#!/usr/bin/env python3
import json

##################################################################
#                                                                #
# This script automatically generates the pipeline.json, setting #
# the right values to safely scale the pipes & filters           #
#                                                                #
##################################################################

PIPELINE_CONFIG_PATH = "../config/pipeline.json"
ENTITIES_SCALE_CONFIG_PATH = "../config/scale.json"

# This can be deduced from the pipeline itself, but due to time limit
# we choose to hardcode it for simplicity
TO_MODIFY = {
    "filter_posts": {
        "queues": [
            "posts_total_avg_calculator_queue",
            "posts_joiner_queue"
        ],
        "exchanges": [
            "posts_boundary_exchange"
        ]
    },
    "filter_comments": {
        "queues": [
            "comments_joiner_queue"
        ],
        "exchanges": [
            "comments_boundary_exchange"
        ]
    },
    "joiner": {
        "queues": [
            "post_avg_sentiment_calculator_queue",
            "filter_student_liked_posts_queue"
        ],
        "exchanges": [
            "posts_filtered_for_joiner_exchange",
            "comments_filtered_exchange"
        ]
    },
    "calculator_avg_sentiment_by_post": {
        "queues": [
            "filter_post_max_avg_sentiment_queue"
        ],
        "exchanges": [
            "post_comments_joined_for_calculator_exchange"
        ]
    },
    "filter_student_liked_posts": {
        "queues": [],
        "exchanges": [
            "post_comments_joined_for_filter_exchange"
        ]
    }
}


def scale_pipeline():
    pipeline_config = {}
    scale_config = {}

    with open(PIPELINE_CONFIG_PATH, "r") as pipeline_config_file:
        pipeline_config = json.load(pipeline_config_file)

    with open(ENTITIES_SCALE_CONFIG_PATH, "r") as scale_config_file:
        scale_config = json.load(scale_config_file)

    for (entity_name, scale) in scale_config.items():
        assert scale >= 1
        pipeline_config[entity_name]["scale"] = scale

        # poner en la queue el n_ack, para eso hay que ver dependencias...
        # poner en los exchanges del que reciben sus colas el n_routing_keys

        exchanges_to_modify = TO_MODIFY[entity_name]["exchanges"]
        for exchange_name in exchanges_to_modify:
            pipeline_config["exchanges"][exchange_name]["n_routing_keys"] = scale

        queues_to_modify = TO_MODIFY[entity_name]["queues"]
        for queue_name in queues_to_modify:
            pipeline_config["queues"][queue_name]["n_end_messages"] = scale

    pipeline_config["queues"]["results_queue"]["n_end_messages"] = 2 + \
        scale_config["filter_student_liked_posts"]

    with open(PIPELINE_CONFIG_PATH, "w") as new_pipeline_config_file:
        json.dump(pipeline_config,
                  new_pipeline_config_file, ensure_ascii=False, indent=4)


def main():
    print("Scaling pipeline according to scale.json")
    scale_pipeline()
    print("Pipeline scaled successfully!")


if __name__ == "__main__":
    main()
