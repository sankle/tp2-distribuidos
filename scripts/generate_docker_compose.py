#!/usr/bin/env python3
import json

COMMENTS_FILE = "sample_comments.csv"
POSTS_FILE = "sample_posts.csv"

PIPELINE_CONFIG_PATH = "../config/pipeline.json"
DOCKER_COMPOSE_PATH = "../docker-compose-dev.yaml"

DOCKER_COMPOSE_BASE = """
# Generated automatically by generate_docker_compose.py

version: '3'
services:
  rabbitmq:
    container_name: rabbitmq
    image: rabbitmq:latest
    ports:
      - 15672:15672
    networks:
      - tp2-distribuidos-net

  ingestor:
    container_name: ingestor
    image: ingestor:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - ENTITY_NAME=ingestor
    volumes:
      - ./data/{}:/comments.csv
      - ./data/{}:/posts.csv
      - ./config/config.json:/config.json
      - ./config/pipeline.json:/pipeline.json
    depends_on:
      - rabbitmq
    networks:
      - tp2-distribuidos-net

  <POST_FILTERS>

  <COMMENT_FILTERS>

  <CALCULATOR_POST_AVG_SCORE>

networks:
  tp2-distribuidos-net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
""".format(COMMENTS_FILE, POSTS_FILE)

CALCULATOR_POST_AVG_SCORE = """

  calculator_post_avg_score:
    container_name: calculator_post_avg_score
    image: calculator_post_avg_score:latest
    entrypoint: python3 /main.py
    environment:
      - ENTITY_NAME=calculator_post_avg_score
      - N_END_MESSAGES_EXPECTED=%d
    volumes:
      - ./config/config.json:/config.json
      - ./config/pipeline.json:/pipeline.json
    depends_on:
      - rabbitmq
    networks:
      - tp2-distribuidos-net

"""

POST_FILTER = """

  filter_posts_%d:
    container_name: filter_posts_%d
    image: filter_posts:latest
    entrypoint: python3 /main.py
    environment:
      - ENTITY_NAME=filter_posts
      - ENTITY_SUB_ID=%d
    volumes:
      - ./config/config.json:/config.json
      - ./config/pipeline.json:/pipeline.json
    depends_on:
      - rabbitmq
    networks:
      - tp2-distribuidos-net

"""

COMMENT_FILTER = """

  filter_comments_%d:
    container_name: filter_comments_%d
    image: filter_comments:latest
    entrypoint: python3 /main.py
    environment:
      - ENTITY_NAME=filter_comments
      - ENTITY_SUB_ID=%d
    volumes:
      - ./config/config.json:/config.json
      - ./config/pipeline.json:/pipeline.json
    depends_on:
      - rabbitmq
    networks:
      - tp2-distribuidos-net

"""


def generate_compose():
    with open(PIPELINE_CONFIG_PATH, 'r') as pipeline_config_file:
        pipeline_config = json.load(pipeline_config_file)

    n_post_filters = pipeline_config["filter_posts"]["scale"]

    post_filters = ""
    for i in range(n_post_filters):
        post_filters += POST_FILTER % (
            i, i, i)

    n_comment_filters = pipeline_config["filter_comments"]["scale"]

    comment_filters = ""
    for i in range(n_comment_filters):
        post_filters += COMMENT_FILTER % (
            i, i, i)

    calculator_post_avg_score = CALCULATOR_POST_AVG_SCORE % (
        n_post_filters)

    docker_compose = DOCKER_COMPOSE_BASE \
        .replace("<CALCULATOR_POST_AVG_SCORE>", calculator_post_avg_score) \
        .replace("<POST_FILTERS>", post_filters) \
        .replace("<COMMENT_FILTERS>", comment_filters)

    with open(DOCKER_COMPOSE_PATH, "w") as file:
        file.write(docker_compose)


def main():
    print("Generating docker-compose-dev.yaml...")
    generate_compose()
    print("Docker compose generated successfully!")


if __name__ == "__main__":
    main()
