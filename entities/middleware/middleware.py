import json
import logging
import pika
import time

from operator import itemgetter


class Middleware:
    def __init__(self, broker_config, middleware_user):
        logging.getLogger("pika").setLevel(logging.WARNING)
        self._middleware_user = middleware_user

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

    def __declare_exchange(self, exchange_config):
        print("exchange_config: ", exchange_config)  # TODO
        name, exchange_type, durable, auto_delete = itemgetter(
            'name', 'type', 'durable', 'auto_delete')(exchange_config)

        self._channel.exchange_declare(exchange=name, exchange_type=exchange_type,
                                       durable=durable, auto_delete=auto_delete)

    def __declare_queue(self, queue_config):
        name, durable, exclusive, auto_delete = itemgetter(
            'name', 'durable', 'exclusive', 'auto_delete')(queue_config)

        self._channel.queue_declare(queue=name, durable=durable,
                                    exclusive=exclusive, auto_delete=auto_delete)

    def __consume_from_queue(self, queue_config, cb):
        name, auto_ack, exclusive = itemgetter(
            'name', 'auto_ack', 'exclusive')(queue_config)

        print("cb: ", cb)

        self._channel.basic_consume(
            queue=name, on_message_callback=lambda ch, method, properties, body: cb(ch, method, properties, body), auto_ack=auto_ack, exclusive=exclusive)

        self._channel.start_consuming()

    def send(self, exchange_name, payload, routing_key=''):
        logging.debug("[Middleware] sending to exchange: {} routing_key: {} batch: {}".format(
            exchange_name, routing_key, payload))

        self._channel.basic_publish(
            exchange=exchange_name, routing_key=routing_key, body=json.dumps(payload))

    def create_ingestor(self, send_exchange_config, send_queue_config):
        self.__declare_exchange(send_exchange_config)
        self.__declare_queue(send_queue_config)

        self._channel.queue_bind(
            exchange=send_exchange_config["name"], queue=send_queue_config["name"], routing_key=None)

    def create_filter(self, recv_exchange_config, recv_queue_config, callback_user_method):
        self.__declare_exchange(recv_exchange_config)
        self.__declare_queue(recv_queue_config)

        self._channel.queue_bind(
            exchange=recv_exchange_config["name"], queue=recv_queue_config["name"], routing_key=None)

        # self.__declare_exchange(filter_config["send_exchange"])
        # # es necesario? TODO: revisar odenes de declaración de las cosas..
        # self.__declare_queue(filter_config["send_queue"])

        self.__consume_from_queue(recv_queue_config, callback_user_method)
