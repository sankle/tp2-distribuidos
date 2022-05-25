import csv
import logging
import os
import socket

from common.middleware.middleware import Middleware
from common.constants import FINISH_PROCESSING_TYPE


POSTS_FILE = '/posts.csv'
COMMENTS_FILE = '/comments.csv'


class Entity:
    def __init__(self, base_config, pipeline_config):
        server_config = base_config["server_config"]
        broker_config = base_config["broker_config"]
        entity_name = base_config["entity_name"]
        entity_config = pipeline_config[entity_name]

        self.entity_name = entity_name

        self._send_posts_exchanges = pipeline_config[self.entity_name]["send_posts_exchanges"]
        self._send_comments_exchanges = pipeline_config[self.entity_name]["send_comments_exchanges"]

        self._recv_queue_config = pipeline_config["queues"][entity_config["recv_queue"]]

        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', server_config["port"]))
        self._server_socket.listen(server_config["listen_backlog"])

        self._middleware = Middleware(broker_config, pipeline_config)

    def consume_callback(self, input):
        logging.info("[{}] Received result: {}".format(
            self.entity_name, input))

    def stop_callback(self):
        pass

    def ingest_file(self, filename, exchanges):
        with open(filename, "r") as file:
            reader = csv.DictReader(file)
            for row in reader:
                self._middleware.send(exchanges, row)

            self._middleware.send_termination(exchanges, {
                "type": FINISH_PROCESSING_TYPE})

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        # while True:
        #     client_sock = self.__accept_new_connection()
        #     self.__handle_client_connection(client_sock)

        self.ingest_file(POSTS_FILE, self._send_posts_exchanges)
        self.ingest_file(COMMENTS_FILE, self._send_comments_exchanges)

        # TODO: fix to consume 3 results instead of only one...
        self._middleware.start_consuming(
            self._recv_queue_config, self.consume_callback, self.stop_callback)

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg = client_sock.recv(1024).rstrip().decode('utf-8')
            logging.info(
                'Message received from connection {}. Msg: {}'
                .format(client_sock.getpeername(), msg))
            client_sock.send(
                "Your Message has been received: {}\n".format(msg).encode('utf-8'))
        except OSError:
            logging.info("Error while reading socket {}".format(client_sock))
        finally:
            client_sock.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
        logging.info("Proceed to accept new connections")
        c, addr = self._server_socket.accept()
        logging.info('Got connection from {}'.format(addr))
        return c
