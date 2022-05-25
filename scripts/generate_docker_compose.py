#!/usr/bin/env python3
import json

COMMENTS_FILE = "sample_comments.csv"
POSTS_FILE = "sample_posts.csv"

PYTHONHASHSEED = 1

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
      - PYTHONHASHSEED=%d
    volumes:
      - ./data/%s:/comments.csv
      - ./data/%s:/posts.csv
      - ./config/config.json:/config.json
      - ./config/pipeline.json:/pipeline.json
    depends_on:
      - rabbitmq
    networks:
      - tp2-distribuidos-net

  <POST_FILTERS>

  <COMMENT_FILTERS>

  <CALCULATOR_POST_AVG_SCORE>

  <JOINERS>

  <CALCULATORS_AVG_SENTIMENT_BY_POST>

  <POST_MAX_AVG_SENTIMENT_FILTER>

networks:
  tp2-distribuidos-net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
""" % (PYTHONHASHSEED, COMMENTS_FILE, POSTS_FILE)

POST_FILTER = """

  filter_posts_%d:
    container_name: filter_posts_%d
    image: filter_posts:latest
    entrypoint: python3 /main.py
    environment:
      - ENTITY_NAME=filter_posts
      - ENTITY_SUB_ID=%d
      - PYTHONHASHSEED=%d
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
      - PYTHONHASHSEED=%d
    volumes:
      - ./config/config.json:/config.json
      - ./config/pipeline.json:/pipeline.json
    depends_on:
      - rabbitmq
    networks:
      - tp2-distribuidos-net

"""

CALCULATOR_POST_AVG_SCORE = """

  calculator_post_avg_score:
    container_name: calculator_post_avg_score
    image: calculator_post_avg_score:latest
    entrypoint: python3 /main.py
    environment:
      - ENTITY_NAME=calculator_post_avg_score
      - N_END_MESSAGES_EXPECTED=%d
      - PYTHONHASHSEED=%d
    volumes:
      - ./config/config.json:/config.json
      - ./config/pipeline.json:/pipeline.json
    depends_on:
      - rabbitmq
    networks:
      - tp2-distribuidos-net

"""

JOINER = """

  joiner_%d:
    container_name: joiner_%d
    image: joiner_post_comment_by_id:latest
    entrypoint: python3 /main.py
    environment:
      - ENTITY_NAME=joiner
      - ENTITY_SUB_ID=%d
      - N_END_MESSAGES_EXPECTED_FROM_POSTS=%d
      - N_END_MESSAGES_EXPECTED_FROM_COMMENTS=%d
      - PYTHONHASHSEED=%d
    volumes:
      - ./config/config.json:/config.json
      - ./config/pipeline.json:/pipeline.json
    depends_on:
      - rabbitmq
    networks:
      - tp2-distribuidos-net

"""

CALCULATOR_AVG_SENTIMENT_BY_POST = """

  calculator_avg_sentiment_by_post_%d:
    container_name: calculator_avg_sentiment_by_post_%d
    image: calculator_avg_sentiment_by_post:latest
    entrypoint: python3 /main.py
    environment:
      - ENTITY_NAME=calculator_avg_sentiment_by_post
      - ENTITY_SUB_ID=%d
      - N_END_MESSAGES_EXPECTED=%d
      - PYTHONHASHSEED=%d
    volumes:
      - ./config/config.json:/config.json
      - ./config/pipeline.json:/pipeline.json
    depends_on:
      - rabbitmq
    networks:
      - tp2-distribuidos-net

"""

POST_MAX_AVG_SENTIMENT_FILTER = """

  filter_post_max_avg_sentiment:
    container_name: filter_post_max_avg_sentiment
    image: filter_post_max_avg_sentiment:latest
    entrypoint: python3 /main.py
    environment:
      - ENTITY_NAME=filter_post_max_avg_sentiment
      - N_END_MESSAGES_EXPECTED=%d
      - PYTHONHASHSEED=%d
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
            i, i, i, PYTHONHASHSEED)

    n_comment_filters = pipeline_config["filter_comments"]["scale"]

    comment_filters = ""
    for i in range(n_comment_filters):
        post_filters += COMMENT_FILTER % (
            i, i, i, PYTHONHASHSEED)

    calculator_post_avg_score = CALCULATOR_POST_AVG_SCORE % (
        n_post_filters, PYTHONHASHSEED)

    n_joiners = pipeline_config["joiner"]["scale"]

    joiners = ""
    for i in range(n_joiners):
        joiners += JOINER % (i, i, i, n_post_filters,
                             n_comment_filters, PYTHONHASHSEED)

    n_calculators_avg_sentiment_by_post = pipeline_config[
        "calculator_avg_sentiment_by_post"]["scale"]

    calculators_avg_sentiment_by_post = ""
    for i in range(n_calculators_avg_sentiment_by_post):
        calculator_post_avg_score += CALCULATOR_AVG_SENTIMENT_BY_POST % (
            i, i, i, n_joiners, PYTHONHASHSEED)

    filter_post_max_avg_sentiment = POST_MAX_AVG_SENTIMENT_FILTER % (
        n_calculators_avg_sentiment_by_post, PYTHONHASHSEED)

    docker_compose = DOCKER_COMPOSE_BASE \
        .replace("<POST_FILTERS>", post_filters) \
        .replace("<COMMENT_FILTERS>", comment_filters) \
        .replace("<CALCULATOR_POST_AVG_SCORE>", calculator_post_avg_score) \
        .replace("<JOINERS>", joiners) \
        .replace("<CALCULATORS_AVG_SENTIMENT_BY_POST>", calculators_avg_sentiment_by_post) \
        .replace("<POST_MAX_AVG_SENTIMENT_FILTER>", filter_post_max_avg_sentiment)

    with open(DOCKER_COMPOSE_PATH, "w") as file:
        file.write(docker_compose)


def main():
    print("Generating docker-compose-dev.yaml...")
    generate_compose()
    print("Docker compose generated successfully!")


if __name__ == "__main__":
    main()
