class DefaultStrategy:
    def __init__(self, _n_routing_keys, based_on_attribute=None):
        pass

    def get_routing_key(self, _payload):
        return ""


class RoundRobinStrategy:
    def __init__(self, n_routing_keys, based_on_attribute=None):
        self.n_routing_keys = n_routing_keys
        self.last_routing_key = 0

    def get_routing_key(self, _payload):
        self.last_routing_key = (
            self.last_routing_key + 1) % self.n_routing_keys

        return str(self.last_routing_key)


class AffinityStrategy:
    def __init__(self, n_routing_keys, based_on_attribute):
        self.n_routing_keys = n_routing_keys
        self.attribute = based_on_attribute

    def get_routing_key(self, payload):
        return str(hash(payload[self.attribute]) % self.n_routing_keys)


class StrategyBuilder:
    def build(strategy_spec, n_routing_keys, based_on_attribute=None):
        strategy_name = strategy_spec["name"]
        if strategy_name == "default":
            return DefaultStrategy(n_routing_keys)
        if strategy_name == "round_robin":
            return RoundRobinStrategy(n_routing_keys)
        if strategy_name == "affinity":
            based_on_attribute = strategy_spec["based_on_attribute"]
            return AffinityStrategy(n_routing_keys, based_on_attribute)
        raise Exception(
            "[StrategyBuilder] Unknown strategy: {}".format(strategy_name))
