#!/usr/bin/env python3
import json

# the-reddit-irl-dataset-comments.csv / sample_comments.csv
COMMENTS_FILE = "the-reddit-irl-dataset-comments.csv"
# the-reddit-irl-dataset-posts.csv / sample_posts.csv
POSTS_FILE = "the-reddit-irl-dataset-posts.csv"

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

  <INGESTOR>

  <POST_FILTERS>

  <COMMENT_FILTERS>

  <CALCULATOR_POST_AVG_SCORE>

  <JOINERS>

  <CALCULATORS_AVG_SENTIMENT_BY_POST>

  <POST_MAX_AVG_SENTIMENT_FILTER>

  <STUDENT_LIKED_POSTS_FILTER>

networks:
  tp2-distribuidos-net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""

INGESTOR = """

  ingestor:
    container_name: ingestor
    image: ingestor:latest
    entrypoint: python3 /main.py
    environment:
      - PYTHONUNBUFFERED=1
      - ENTITY_NAME=ingestor
      - N_END_MESSAGES_EXPECTED=%d
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

"""

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

STUDENT_LIKED_POSTS_FILTER = """

  filter_student_liked_posts_%d:
    container_name: filter_student_liked_posts_%d
    image: filter_student_liked_posts:latest
    entrypoint: python3 /main.py
    environment:
      - ENTITY_NAME=filter_student_liked_posts
      - ENTITY_SUB_ID=%d
      - N_END_MESSAGES_EXPECTED_FROM_POST_AVG_SCORE_CALCULATOR=%d
      - N_END_MESSAGES_EXPECTED_FROM_JOINER=%d
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

    n_filters_student_liked_posts = pipeline_config["filter_student_liked_posts"]["scale"]

    filters_student_liked_posts = ''
    for i in range(n_filters_student_liked_posts):
        filters_student_liked_posts += STUDENT_LIKED_POSTS_FILTER % (
            i, i, i, 1, n_joiners, PYTHONHASHSEED)

    ingestor = INGESTOR % (
        n_filters_student_liked_posts + 1 + 1, PYTHONHASHSEED, COMMENTS_FILE, POSTS_FILE)

    docker_compose = DOCKER_COMPOSE_BASE \
        .replace("<INGESTOR>", ingestor) \
        .replace("<POST_FILTERS>", post_filters) \
        .replace("<COMMENT_FILTERS>", comment_filters) \
        .replace("<CALCULATOR_POST_AVG_SCORE>", calculator_post_avg_score) \
        .replace("<JOINERS>", joiners) \
        .replace("<CALCULATORS_AVG_SENTIMENT_BY_POST>", calculators_avg_sentiment_by_post) \
        .replace("<POST_MAX_AVG_SENTIMENT_FILTER>", filter_post_max_avg_sentiment) \
        .replace("<STUDENT_LIKED_POSTS_FILTER>", filters_student_liked_posts)

    with open(DOCKER_COMPOSE_PATH, "w") as file:
        file.write(docker_compose)


def main():
    print("Generating docker-compose-dev.yaml...")
    generate_compose()
    print("Docker compose generated successfully!")


if __name__ == "__main__":
    main()
