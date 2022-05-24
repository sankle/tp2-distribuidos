import json
import logging
import pika
import time

from operator import itemgetter
from common.middleware.protocol import BrokerProtocol
from common.middleware.send_strategies import StrategyBuilder


class Middleware:
    def __init__(self, broker_config, pipeline_config):
        # Reduce pika info logging noise
        logging.getLogger("pika").setLevel(logging.WARNING)

        n_connect_attempt = 0
        connected = False

        # give some time for broker to initialize
        time.sleep(broker_config["freq_retry_connect"])

        while not connected:
            try:
                self._connection = pika.BlockingConnection(
                    pika.ConnectionParameters(host=broker_config["host"]))
                self._channel = self._connection.channel()

                connected = True
                logging.info("Successfully connected to broker.")
            except:
                if n_connect_attempt >= broker_config["n_connect_attempts"]:
                    raise

                logging.warn("Broker not ready. Retrying connection in %d secs. [%d/%d]" % (
                    broker_config["freq_retry_connect"], n_connect_attempt, broker_config["n_connect_attempts"]))

                n_connect_attempt += 1
                time.sleep(broker_config["freq_retry_connect"])
                continue

        self._pipeline_config = pipeline_config
        self.__initialize_pipeline()
        self._send_strategies = {}

    def __initialize_pipeline(self):
        """
        Pipeline idempotent initialization for all entities.
        Creates exchanges and queues and their bindings, as specified in pipeline_config
        """
        logging.info("Initializing pipeline")

        for exchange_config in self._pipeline_config["exchanges"].values():
            self.__declare_exchange(exchange_config)

        for queue_config in self._pipeline_config["queues"].values():
            queue_base_name = queue_config["name"]
            scale_entity = queue_config.get("scale_based_on_entity")

            if not scale_entity:
                self.__declare_and_bind_queue(queue_base_name, queue_config)
                continue

            n_queues = self._pipeline_config[scale_entity]["scale"]

            for i in range(n_queues):
                queue_name = "{}_{}".format(queue_base_name, i)
                routing_key = str(i)
                self.__declare_and_bind_queue(
                    queue_name, queue_config, routing_key)

        logging.info("Pipeline initialized successfully")

    def __declare_exchange(self, exchange_config):
        name, exchange_type, durable, auto_delete = itemgetter(
            'name', 'type', 'durable', 'auto_delete')(exchange_config)

        self._channel.exchange_declare(exchange=name, exchange_type=exchange_type,
                                       durable=durable, auto_delete=auto_delete)

    def __declare_and_bind_queue(self, queue_name, queue_config, routing_key=''):
        durable, exclusive, auto_delete, bind_to_exchange = itemgetter(
            'durable', 'exclusive', 'auto_delete', 'bind_to_exchange')(queue_config)

        self._channel.queue_declare(queue=queue_name, durable=durable,
                                    exclusive=exclusive, auto_delete=auto_delete)

        self._channel.queue_bind(
            exchange=bind_to_exchange, queue=queue_name, routing_key=routing_key)

    def __consume_from_queue(self, queue_name, queue_config, cb):
        auto_ack, exclusive = itemgetter(
            'auto_ack', 'exclusive')(queue_config)

        self._channel.basic_consume(
            queue=queue_name, on_message_callback=lambda ch, method, properties, body: cb(ch, method, properties, BrokerProtocol.deserialize(body)), auto_ack=auto_ack, exclusive=exclusive)

        self._channel.start_consuming()

    def __get_next_routing_key(self, exchange_name, payload):
        if not exchange_name in self._send_strategies:
            strategy = self._pipeline_config["exchanges"][exchange_name].get("strategy", {
                                                                             "name": "default"})
            n_routing_keys = self._pipeline_config["exchanges"][exchange_name].get(
                "n_routing_keys", 1)
            logging.debug("[Middleware] Creating strategy {} for exchange {}".format(
                strategy, exchange_name))
            self._send_strategies[exchange_name] = StrategyBuilder.build(
                strategy, n_routing_keys)

        strategy = self._send_strategies[exchange_name]
        return strategy.get_routing_key(payload)

    def __get_all_routing_keys(self, exchange_name):
        n_routing_keys = self._pipeline_config["exchanges"][exchange_name].get(
            "n_routing_keys", 1)
        return range(n_routing_keys)

    def __send(self, exchange_name, routing_key, payload):
        self._channel.basic_publish(
            exchange=exchange_name, routing_key=routing_key, body=BrokerProtocol.serialize(payload))

    def send(self, exchange_name, payload):
        routing_key = self.__get_next_routing_key(exchange_name, payload)

        logging.debug("[Middleware] sending to exchange: {} routing_key: {} batch: {}".format(
            exchange_name, routing_key, payload))

        self.__send(exchange_name, routing_key, payload)

    def send_termination(self, exchange_name, payload):
        for routing_key in self.__get_all_routing_keys(exchange_name):
            self.__send(exchange_name, str(routing_key), payload)

    def create_filter(self, recv_queue_config, callback_user_method, entity_sub_id=None):
        queue_name = recv_queue_config["name"]
        if entity_sub_id:
            queue_name += "_{}".format(entity_sub_id)

        self.__consume_from_queue(
            queue_name, recv_queue_config, callback_user_method)
