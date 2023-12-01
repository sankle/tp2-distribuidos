# Reddit Analyzer

Assignment II - Distributed Systems - Faculty of Engineering, University of Buenos Aires
Developed by Santiago Klein

## Runbook

1) Download `the-reddit-irl-dataset-comments.csv` and `the-reddit-irl-dataset-posts.csv` from [kaggle](https://www.kaggle.com/datasets/pavellexyr/the-reddit-irl-data) and move them to a the directory `data` in the root folder of repository.

2) Modify the `config/scale.json` file with the desired number of each component that can be scaled.

3) Move to `scripts` directory, and run:

- `./scale_pipeline.py` to generate the scaled `pipeline.json` file
- `./generate_services.py` to generate the `Makefile` and each `service` in a `.services` directory
- `./generate_docker_compose.py` to generate the `docker-compose-dev.yaml`

4) Run the service using `make up && make logs` and see the outputs

5) Once processing is finished, results will be stored in the `results` directory.

6) Run `make down` to stop and destroy all containers

## Scale the services

1) Modify the `config/scale.json` file with the desired number of each component that can be scaled.
2) Move to `scripts` directory, and 
- run `./scale_pipeline.py` to generate the scaled `pipeline.json` file
- run `./generate_docker_compose.py` to generate the `docker-compose-dev.yaml` with the scaled services

