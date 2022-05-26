#!/usr/bin/env python3
import csv
import json
import logging
import os
import socket
import time

import common.cs_protocol
from common.constants import FINISH_PROCESSING_TYPE, STUDENT_LIKED_POST_WITH_SCORE_AVG_HIGHER_THAN_MEAN_TYPE, POST_WITH_MAX_AVG_SENTIMENT_TYPE,  POST_AVG_SCORE_TYPE

BASE_CONFIG_FILE = "config.json"
POSTS_FILE = '/posts.csv'
COMMENTS_FILE = '/comments.csv'

RESULTS_FILE_PATH = '/results/results.txt'
IMG_FILE_PATH = '/results/meme_with_highest_avg_sentiment'

RETRY_SERVER_CONNECT_CADENCY = 5


class Client:
    def __init__(self, host, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        logging.info(f"Connecting to server {host}:{port}")

        connected = False
        while not connected:
            try:
                self.s.connect((host, port))
                connected = True
            except:
                logging.warn(
                    f"Could not connect to server: server not ready. Retryin in {RETRY_SERVER_CONNECT_CADENCY} secs")
                time.sleep(RETRY_SERVER_CONNECT_CADENCY)
                continue

        logging.info("Connected successfully to server")

    def __ingest_file(self, filename):
        with open(filename, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                common.cs_protocol.send(self.s, row)
        common.cs_protocol.send(self.s, {"type": FINISH_PROCESSING_TYPE})

    def __recv_results(self):
        with open(RESULTS_FILE_PATH, "w") as results_file:
            while True:
                result = common.cs_protocol.recv(self.s)
                if result["type"] == STUDENT_LIKED_POST_WITH_SCORE_AVG_HIGHER_THAN_MEAN_TYPE or result["type"] == POST_AVG_SCORE_TYPE:
                    results_file.write(json.dumps(result))
                    results_file.write("\n")
                    continue

                if result["type"] == POST_WITH_MAX_AVG_SENTIMENT_TYPE:
                    if not result.get("file_length"):
                        logging.error(
                            "Server could not download post with max avg sentiment image")
                    else:
                        img_bytes = common.cs_protocol.recv_img(self.s)
                        with open("{}{}".format(IMG_FILE_PATH, result["ext"]), "wb") as img_file:
                            img_file.write(img_bytes)

                    results_file.write(json.dumps(result))
                    results_file.write("\n")
                    continue

                if result["type"] == FINISH_PROCESSING_TYPE:
                    break

                logging.error("Unknown result type recved: {}", result)

    def run(self):
        self.__ingest_file(POSTS_FILE)
        self.__ingest_file(COMMENTS_FILE)
        self.__recv_results()

    def stop(self):
        self.s.close()


def parse_base_config():
    base_config = {}

    with open(BASE_CONFIG_FILE, 'r') as base_config_file:
        base_config = json.load(base_config_file)

    base_config["entity_name"] = os.environ["ENTITY_NAME"]
    return base_config


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


def main():
    base_config = parse_base_config()
    initialize_log(base_config["logging_level"])

    client = Client(base_config["server_config"]["host"], int(
        base_config["server_config"]["port"]))

    client.run()
    client.stop()


if __name__ == "__main__":
    main()
