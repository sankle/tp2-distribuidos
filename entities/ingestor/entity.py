import csv
import json
import logging
import socket

from middleware.middleware import Middleware


POSTS_FILE = '/posts.csv'
COMMENTS_FILE = '/comments.csv'


class Entity:
    def __init__(self, base_config, pipeline_config):
        server_config = base_config["server_config"]
        broker_config = base_config["broker_config"]

        self._entity_name = base_config["entity_name"]
        self._pipeline_config = pipeline_config

        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', server_config["port"]))
        self._server_socket.listen(server_config["listen_backlog"])

        self._middleware = Middleware(broker_config, self)

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

        post_send_exchange_name = self._pipeline_config[self._entity_name]["post_send_exchange"]
        comment_send_exchange_name = self._pipeline_config[self._entity_name]["comment_send_exchange"]

        post_send_exchange_config = self._pipeline_config["exchanges"][post_send_exchange_name]
        comment_send_exchange_config = self._pipeline_config["exchanges"][comment_send_exchange_name]

        post_send_queue_name = self._pipeline_config[self._entity_name]["post_send_queue"]
        comment_send_queue_name = self._pipeline_config[self._entity_name]["comment_send_queue"]

        post_send_queue_config = self._pipeline_config["queues"][post_send_queue_name]
        comment_send_queue_config = self._pipeline_config["queues"][comment_send_queue_name]

        print("post_send_exchange_config: ", post_send_exchange_config)

        self._middleware.create_ingestor(
            post_send_exchange_config, post_send_queue_config)

        self._middleware.create_ingestor(
            comment_send_exchange_config, comment_send_queue_config)

        with open(POSTS_FILE, "r") as posts_file:
            reader = csv.DictReader(posts_file)
            for post in reader:
                self._middleware.send(post_send_exchange_name, post)

        # Send comments

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
