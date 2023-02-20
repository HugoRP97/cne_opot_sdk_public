import os

from opot_sdk.helpers.Singleton import Singleton
import configparser

from opot_sdk.helpers.default_params import EnvInterpolation


class NodeParams(metaclass=Singleton):
    def __init__(self):
        """
        :raises KeyError: If the Environment variable does not exists it will rise this exception
        """

        parser = configparser.ConfigParser(os.environ, interpolation=EnvInterpolation())
        parser.read("/etc/default/node_config.ini")

        node = parser['NODE']
        # Define the controller IP.
        self.controller_ip = node['OPOT_CONTROLLER_IP']
        r_error = node.get('CHANCE_RANDOM_ERROR', '0')
        if r_error is None or len(r_error) == 0:
            r_error = 0.0
        self.chance_random_error = float(r_error)
        s_gen_time = node.get('GEN_TIME', '1')
        if s_gen_time is None or len(s_gen_time) == 0:
            s_gen_time = 1
        self.sample_gen_time = float(1)
        # Define the controller Port.
        port = node.get('GRPC_CONTROLLER_PORT', '9111')
        if port is None or len(port) ==0:
            port = 9111
        self.grpc_port = int(port)
        # Setup the address of the controller.
        self.grpc_ip = self.controller_ip
        # Logs path
        self.logs_path = node.get("LOGS_PATH", "/var/log/opot/")


node_params = NodeParams()
