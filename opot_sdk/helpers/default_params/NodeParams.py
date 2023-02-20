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
        # Define the controller Port.
        self.grpc_port = int(node.get('GRPC_CONTROLLER_PORT', 9111))
        # Setup the address of the controller.
        self.grpc_ip = self.controller_ip
        # Logs path
        self.logs_path = node.get("LOGS_PATH", "/var/log/opot/")
        self.nsh_port = node.get("NSH_PORT",6633)

        # Interfaces to listen
        interfaces = node.get("INTERFACES_TO_LISTEN",None)
        parsed_interfaces = interfaces
        if interfaces is not None:
            if type(interfaces) is str:
                parsed_interfaces = interfaces.split(",")
        self.interfaces_to_listen = parsed_interfaces



node_params = NodeParams()
