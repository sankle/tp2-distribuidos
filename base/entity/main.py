#!/usr/bin/env python3

import json
import logging
import os

from common.entity import Entity

BASE_CONFIG_FILE = "config.json"
PIPELINE_CONFIG_FILE = "pipeline.json"


def parse_base_config():
    base_config = {}

    with open(BASE_CONFIG_FILE, 'r') as base_config_file:
        base_config = json.load(base_config_file)

    base_config["entity_name"] = os.environ["ENTITY_NAME"]
    return base_config


def parse_pipeline_config(entity_name):
    with open(PIPELINE_CONFIG_FILE, 'r') as pipeline_config_file:
        full_pipeline_config = json.load(pipeline_config_file)

    logging.info("full_pipeline_config: {}".format(full_pipeline_config))

    parsed_pipeline_config = {}

    parsed_pipeline_config[entity_name] = full_pipeline_config[entity_name]

    common_components = ["exchanges", "queues"]
    for c in common_components:
        parsed_pipeline_config[c] = full_pipeline_config[c]

    logging.info("parsed_pipeline_config: {}".format(parsed_pipeline_config))

    return parsed_pipeline_config


def main():
    base_config = parse_base_config()
    initialize_log(base_config["logging_level"])

    pipeline_config = parse_pipeline_config(base_config["entity_name"])

    logging.debug("[{}] Base configuration: {}".format(
        base_config["entity_name"], base_config))

    # Initialize server and start server loop
    entity = Entity(base_config, pipeline_config)
    entity.run()


def initialize_log(logging_level):
    """
    Python custom logging initialization

    Current timestamp is added to be able to identify in docker
    compose logs the date when the log has arrived
    """
    logging.basicConfig(
        format='%(asctime)s %(levelname)-8s %(message)s',
        level=logging_level,
        datefmt='%Y-%m-%d %H:%M:%S',
    )


if __name__ == "__main__":
    main()
