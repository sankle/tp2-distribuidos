#!/usr/bin/env python3
import os
import shutil

SERVICES_DIRECTORY = "../.services"
BASE_ENTITY_STRUCTURE_PATH = "../base/entity"
ENTITIES_BASE_PATH = "../entities"
ENTITY_IMPL_FILENAME = "entity.py"
ENTITY_FILE_CONTAINER_DIR = "common/"

# Relative from docker-compose-dev.yaml
MIDDLEWARE_BASE_PATH_FROM_COMPOSE = "./entities/middleware"
ENTITIES_BASE_PATH_FROM_COMPOSE = "entities"
SERVICES_BASE_PATH_FROM_COMPOSE = ".services"

MAKEFILE_PATH = "../Makefile"

ENTITY_RELATIVE_PATHS = [
    # (relative_path, entity_name)
    ("", "ingestor"),
    ("filters", "filter_post_select_cols_and_drop_invalid")
]

ENTITY_BASE_DOCKERFILE = """
# Generated automaticaly by generate_services.py

FROM rabbitmq-python-base:0.0.1
COPY <ENTITY_PATH_FROM_COMPOSE> /
COPY <MIDDLEWARE_FROM_PATH> /middleware
CMD /main.py
"""

MAKEFILE_BASE = """
# Generated automatically by generate_services.py

SHELL := /bin/bash
PWD := $(shell pwd)

default: build

services:
	cd $(PWD)/scripts && python3 generate_services.py
.PHONY: services

images: services
	docker build -f ./base/images/python-base.dockerfile -t "rabbitmq-python-base:0.0.1" .
	docker build -f ./rabbitmq/Dockerfile -t "rabbitmq:latest" .
	<SERVICE_BUILD_COMMANDS>
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

"""


class EntityParser:
    def __init__(self):
        self._build_commands = []

    def create_file(self, path, content):
        with open(path, "w") as file:
            file.write(content)

    def build_entities(self):
        self.remove_service_directory_if_exists()
        print("Building services into directory {}".format(SERVICES_DIRECTORY))

        for (relative_path, entity_name) in ENTITY_RELATIVE_PATHS:
            self.build_service(relative_path, entity_name)

    def build_makefile(self):
        # build_commands_str = "/n/t".join(self._build_commands)
        build_commands_str = ""
        for build_command in self._build_commands:
            build_commands_str += build_command
        makefile = MAKEFILE_BASE.replace(
            "<SERVICE_BUILD_COMMANDS>", build_commands_str)
        self.create_file(MAKEFILE_PATH, makefile)

    def remove_service_directory_if_exists(self):
        print("Deleting old {} directory if existent".format(SERVICES_DIRECTORY))

        try:
            shutil.rmtree(SERVICES_DIRECTORY,
                          ignore_errors=False, onerror=None)
        except:
            # directory did not exist
            pass

    def build_service(self, relative_path, entity_name):
        print("Creating entity {}...".format(entity_name))

        entity_path = "{}/{}".format(SERVICES_DIRECTORY, entity_name)

        # Copiar base entity structure
        shutil.copytree(BASE_ENTITY_STRUCTURE_PATH, entity_path)

        # Copy entity implementation
        src_path = ""
        src_path_from_compose = "{}/{}".format(SERVICES_BASE_PATH_FROM_COMPOSE,
                                               entity_name)
        if relative_path != "":
            src_path = "{}/{}/{}/{}".format(ENTITIES_BASE_PATH,
                                            relative_path, entity_name, ENTITY_IMPL_FILENAME)
        else:
            src_path = "{}/{}/{}".format(ENTITIES_BASE_PATH,
                                         entity_name, ENTITY_IMPL_FILENAME)

        dst_path = "{}/{}".format(entity_path, ENTITY_FILE_CONTAINER_DIR)

        shutil.copy2(src_path, dst_path)

        # Create entity Dockerfile
        entity_dockerfile = ENTITY_BASE_DOCKERFILE.replace("<MIDDLEWARE_FROM_PATH>", MIDDLEWARE_BASE_PATH_FROM_COMPOSE) \
            .replace("<ENTITY_PATH_FROM_COMPOSE>", src_path_from_compose)

        entity_dockerfile_filename = "{}/Dockerfile".format(entity_path)
        self.create_file(entity_dockerfile_filename, entity_dockerfile)

        self._build_commands.append(
            "docker build -f {}/Dockerfile -t \"{}:latest\" .\n	".format(src_path_from_compose, entity_name))

        print("Entity {} created successfully!".format(entity_name))


def main():
    entity_parser = EntityParser()
    entity_parser.build_entities()
    entity_parser.build_makefile()


if __name__ == "__main__":
    main()
