# Trabajo Práctico II - Sistemas Distribuidos - FIUBA

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

## Puntos de mejora

- El `ingestor` efectúa un trabajo secuencial, procesando primero todos los posts, luego todos los comments y por último los resultados. Debido a esto, los resultados se encolan en el MOM y permanecen allí en tanto y en cuanto el `ingestor` no termine de procesar los posts y comments. Se podría utilizar otro hilo del `ingestor` (u otra entidad) para ir consumiendo y enviando los resultados a medida que se generan.
- Así como se implementó el `BasicFilter` para encapsular el comportamiento de la mayoría de los filtros que consumen de una cola, realizan un procesamiento a través de la callback y envían el resultado a un exchange, se podría haber desarrollado otro filtro genérico que consuma primero de una cola, obtenga un resultado, y luego consuma de otra cola, para finalmente enviar los resultados a un exchange (para los casos de `filter_student_liked_posts` y `joiner`, que dependen de dos colas).
- Tanto el protocolo de comunicación entre `cliente` y `servidor`, y el protocolo de los mensajes del broker son subóptimos, dado que se utiliza `json` como formato. Esto podría optimizarse, reduciendo la cantidad de información en tránsito y aumentando la performance. Considerando que el `client` y el `ingestor` son el cuello de botella de funcionamiento del sistema (con un CPU rondando el 100%), este es un factor importante de mejora.
- El archivo de configuración del pipeline (`pipeline.json`) puede ser optimizado en un formato que contenga menos información redundante. Además, los atributos de cada exchange no se están utilizando (fueron agregados para una optimización que no se alcanzó a ejecutar), y podrían utilizarse para enviar a cada exchange solamente la información que necesita, reduciendo el tráfico de información innecesaria.
- Actualmente, cada entidad del pipeline conoce la configuración del mismo, y lo primero que realiza es configurar **todas** las colas y los exchanges, y hacer los binds correspondientes. Esto se puede realizar de manera segura porque son operaciones idempotentes, mas una optimización posible es crear un script o servicio que se encargue de la configuración del pipeline en el comienzo de la ejecución, o bien que cada servicio configure solamente lo que va a usar, pero se optó por el enfoque actual para simplificar y evitar problemas.
