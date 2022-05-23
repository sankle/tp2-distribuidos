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
      - ./config/config.json:/config.json
      - ./config/pipeline.json:/pipeline.json
    depends_on:
      - rabbitmq
    networks:
      - tp2-distribuidos-net

  filter_post_select_cols_and_drop_invalid:
    container_name: filter_post_select_cols_and_drop_invalid
    image: filter_post_select_cols_and_drop_invalid:latest
    entrypoint: python3 /main.py
    environment:
      - ENTITY_NAME=filter_post_select_cols_and_drop_invalid
    volumes:
      - ./config/config.json:/config.json
      - ./config/pipeline.json:/pipeline.json
    depends_on:
      - rabbitmq
    networks:
      - tp2-distribuidos-net


networks:
  tp2-distribuidos-net:
    ipam:
      driver: default
      config:
        - subnet: 172.25.125.0/24
"""
