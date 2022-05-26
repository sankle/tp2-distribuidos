import json
import logging

ENCODING = 'utf-8'
N_LEN_BYTES = 4
ENDIANNESS = 'big'


def send(s, row):
    # logging.info("cs_protocol sending row: {}".format(row))
    json_str = json.dumps(row)
    encoded_row = json_str.encode(ENCODING)
    try:
        s.sendall(len(encoded_row).to_bytes(N_LEN_BYTES, ENDIANNESS))
        s.sendall(encoded_row)
    except Exception as e:
        logging.error("ERROR: {}".format(e))
        raise e


def recv(s):
    be_len = recv_all(s, N_LEN_BYTES)
    row_len = int.from_bytes(be_len, ENDIANNESS)
    bytes_recved = recv_all(s, row_len)
    bytes_recved_decoded = bytes_recved.decode(ENCODING)
    # logging.info("cs_protocol recved row: {}".format(row))
    try:
        row = json.loads(bytes_recved_decoded)
    except Exception as e:
        logging.error("ERROR: {} bytes_recved_decoded: {}".format(
            e, bytes_recved_decoded))
        raise e
    return row


def send_img(s, img_bytes):
    s.sendall(len(img_bytes).to_bytes(N_LEN_BYTES, ENDIANNESS))
    s.sendall(img_bytes)


def recv_img(s):
    be_len = recv_all(s, N_LEN_BYTES)
    img_len = int.from_bytes(be_len, ENDIANNESS)
    return recv_all(s, img_len)


def recv_all(s, expected_bytes):
    bytes = s.recv(expected_bytes)
    while len(bytes) < expected_bytes:
        bytes += s.recv(expected_bytes - len(bytes))
    return bytes
