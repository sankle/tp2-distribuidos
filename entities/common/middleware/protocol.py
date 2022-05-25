import json


class BrokerProtocol:
    def serialize(body, attributes):
        # TODO: implement batches & attributes
        return json.dumps(body)

    def deserialize(raw_body):
        return json.loads(raw_body.decode("utf-8"))
