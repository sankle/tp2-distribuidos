import logging
import os
import pika
import time

from operator import itemgetter
from common.constants import FINISH_PROCESSING_TYPE
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

        self._batch_size = broker_config["batch_size"]
        self._batches = {}
        self._pipeline_config = pipeline_config
        self.__initialize_pipeline()
        self._send_strategies = {}
        self._n_pending_end_messages = {}
        self._consuming = False

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
                self.__declare_and_bind_queue(
                    queue_base_name, queue_config)
                continue

            n_queues = self._pipeline_config[scale_entity]["scale"]

            for routing_key in range(n_queues):
                queue_name = "{}_{}".format(queue_base_name, routing_key)
                self.__declare_and_bind_queue(
                    queue_name, queue_config, str(routing_key))

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

    def __consume_from_queue(self, queue_name, queue_config, consume_cb, stop_cb):
        self._n_pending_end_messages[queue_name] = int(queue_config.get(
            "n_end_messages", "1"))

        def cb_wrapper(ch, method, properties, body):
            deserialized_body = BrokerProtocol.deserialize(body)
            # logging.debug(
            #     "cb_wrapper: deserialized_body: {}".format(deserialized_body))

            if deserialized_body.get("type") == FINISH_PROCESSING_TYPE:
                self._n_pending_end_messages[queue_name] -= 1

                if not self._n_pending_end_messages[queue_name]:
                    logging.info("Terminating...")
                    return stop_cb()

                logging.debug("Received termination. Pending terminations: {}".format(
                    self._n_pending_end_messages[queue_name]))
                return

            for payload in deserialized_body["batch"]:
                consume_cb(payload)

        auto_ack, exclusive = itemgetter(
            'auto_ack', 'exclusive')(queue_config)

        self._channel.basic_consume(
            queue=queue_name, on_message_callback=cb_wrapper, auto_ack=auto_ack, exclusive=exclusive)

        if not self._consuming:
            self._consuming = True
            self._channel.start_consuming()

    def __get_next_routing_key(self, exchange_name, payload):
        if not exchange_name in self._send_strategies:
            strategy = self._pipeline_config["exchanges"][exchange_name].get("strategy", {
                "name": "default"})
            n_routing_keys = self._pipeline_config["exchanges"][exchange_name].get(
                "n_routing_keys", 1)
            # logging.debug("[Middleware] Creating strategy {} for exchange {}".format(
            #     strategy, exchange_name))
            self._send_strategies[exchange_name] = StrategyBuilder.build(
                strategy, n_routing_keys)

        strategy = self._send_strategies[exchange_name]
        return strategy.get_routing_key(payload)

    def __get_all_routing_keys(self, exchange_name):
        n_routing_keys = self._pipeline_config["exchanges"][exchange_name].get(
            "n_routing_keys")
        if not n_routing_keys:
            return [""]
        return [str(routing_key) for routing_key in range(n_routing_keys)]

    def __send_batch(self, exchange_name, batch, routing_key):
        payload = {"batch": batch}
        # logging.debug("sending payload: {} to routing_key: {}".format(
        #     payload, routing_key))
        raw_payload = BrokerProtocol.serialize(payload)
        self._channel.basic_publish(
            exchange=exchange_name, routing_key=routing_key, body=raw_payload)

    def __send(self, exchange_name, routing_key, payload, wrap_in_batch=True):
        if not wrap_in_batch:
            raw_payload = BrokerProtocol.serialize(payload)
            self._channel.basic_publish(
                exchange=exchange_name, routing_key=routing_key, body=raw_payload)
            return

        batch = self._batches.get((exchange_name, routing_key), [])
        batch.append(payload)

        if len(batch) >= self._batch_size:
            self.__send_batch(exchange_name, batch, routing_key)
            self._batches[(exchange_name, routing_key)] = []
        else:
            self._batches[(exchange_name, routing_key)] = batch
            # print("batch not sent.. self._batches: {} ".format(self._batches))

    def send(self, exchanges, payload):
        for exchange_name in exchanges.keys():
            routing_key = self.__get_next_routing_key(exchange_name, payload)

            # logging.debug("[Middleware] sending to exchange: {} routing_key: {} batch: {}".format(
            #     exchange_name, routing_key, payload))

            self.__send(exchange_name, routing_key, payload, True)

    def send_termination(self, exchanges, payload):
        # Check if there is a pending batch. If so, send it
        for exchange_name in exchanges.keys():
            for routing_key in self.__get_all_routing_keys(exchange_name):
                pending_batch = self._batches.get(
                    (exchange_name, routing_key), [])
                if len(pending_batch):
                    self.__send_batch(
                        exchange_name, pending_batch, routing_key)
                    self._batches[(exchange_name, routing_key)] = []
                self.__send(exchange_name, routing_key,
                            payload, False)

    def start_consuming(self, recv_queue_config, consume_cb, stop_cb, entity_sub_id=None):
        queue_name = recv_queue_config["name"]
        if entity_sub_id:
            queue_name += "_{}".format(entity_sub_id)

        self.__consume_from_queue(
            queue_name, recv_queue_config, consume_cb, stop_cb)

    def stop_consuming(self):
        if self._consuming:
            self._channel.stop_consuming()
            self._consuming = False
        self._channel.close()
