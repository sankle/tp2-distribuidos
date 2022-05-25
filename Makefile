
# Generated automatically by generate_services.py

SHELL := /bin/bash
PWD := $(shell pwd)

default: build

services:
	cd $(PWD)/scripts && python3 generate_docker_compose.py && python3 generate_services.py
.PHONY: services

images: services
	docker build -f ./base/images/python-base.dockerfile -t "rabbitmq-python-base:0.0.1" .
	docker build -f ./rabbitmq/Dockerfile -t "rabbitmq:latest" .
	docker build -f .services/ingestor/Dockerfile -t "ingestor:latest" .
	docker build -f .services/filter_posts/Dockerfile -t "filter_posts:latest" .
	docker build -f .services/filter_comments/Dockerfile -t "filter_comments:latest" .
	docker build -f .services/filter_post_max_avg_sentiment/Dockerfile -t "filter_post_max_avg_sentiment:latest" .
	docker build -f .services/filter_student_liked_posts/Dockerfile -t "filter_student_liked_posts:latest" .
	docker build -f .services/calculator_post_avg_score/Dockerfile -t "calculator_post_avg_score:latest" .
	docker build -f .services/calculator_avg_sentiment_by_post/Dockerfile -t "calculator_avg_sentiment_by_post:latest" .
	docker build -f .services/joiner_post_comment_by_id/Dockerfile -t "joiner_post_comment_by_id:latest" .
	
	# docker build -f ./client/Dockerfile -t "client:latest" .
.PHONY: images

up: images
	docker-compose -f docker-compose-dev.yaml up -d --build
.PHONY: up

down:
	docker-compose -f docker-compose-dev.yaml stop -t 1
	docker-compose -f docker-compose-dev.yaml down
.PHONY: down

logs:
	docker-compose -f docker-compose-dev.yaml logs -f
.PHONY: logs

