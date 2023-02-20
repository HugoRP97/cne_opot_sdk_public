import logging
import os
from configparser import ConfigParser

from prometheus_client import Gauge, Counter
from kafka import KafkaProducer
from opot_sdk.helpers.Singleton import Singleton
from opot_sdk.helpers.default_params import EnvInterpolation


class ControllerParams(metaclass=Singleton):
    def __init__(self):
        """

        :raises KeyError: If the Environment variable does not exists it will rise this exception
        """

        parser = ConfigParser(os.environ, interpolation=EnvInterpolation())
        parser.read("/etc/default/controller_config.ini")

        controller = parser['CONTROLLER']

        # Range of ports that can be used by the nodes when no port has been chosen
        self.min_node_port = controller.get('MIN_PORT', 30000)
        self.max_node_port = controller.get('MAX_PORT', 40000)

        # IP of the controller inside the management plane
        self.controller_ip = controller['OPOT_CONTROLLER_IP']
        # Port of the controller inside the management plane
        self.grpc_port = int(controller.get('GRPC_CONTROLLER_PORT', 9111))
        # Control Plane address, the port is the grpc Port
        self.controller_address = (self.controller_ip, self.grpc_port)
        # Netconf port, to connect to the node. Default: 830
        self.netconf_ssh_port = int(controller.get('NETCONF_SSH_PORT', 830))
        # Netconf user
        self.netconf_user = controller.get("NETCONF_USER", "netconf")
        # Netconf password
        self.netconf_password = controller.get("NETCONF_PASSWORD", "netconf")
        # If there is not KEY_GENERATOR_VALUE then just dont use it
        self.key_generator_api = controller.get('KEY_GENERATOR_API', None)
        # For prometheus configuration
        self.prometheus_port = int(controller.get("PROMETHEUS_PORT", 9091))
        self.prometheus_ip = controller.get("PROMETHEUS_IP", self.controller_ip)
        self.prometheus_address = (self.prometheus_ip, self.prometheus_port)

        # Logs path
        self.logs_path = controller.get("LOGS_PATH", "/tmp/")

        # Metrics for prometheus
        self.valid_time_metric = Gauge("valid_verification_time", "Time spent to verify that the OPoT validation has "
                                                                  "been successful")
        self.invalid_time_metric = Gauge("invalid_verification_time",
                                         "Time spent to verify that the OPoT validation has "
                                         "been unsuccessful")
        self.create_time_metric = Gauge("create_time", "Time spent by the controller and the nodes to instantiate an "
                                                       "OPoT Path")
        self.valid_validations_metric = Counter("valid_verifications", "Number of times where a valid verification of "
                                                                     "the PoT has occurred.")
        self.invalid_validations_metric = Counter("invalid_verifications",
                                                  "Number of times where an invalid verification of "
                                                  "the PoT has occurred.")
        self.kafka_enable = False

        try:
            kafka_params = parser['KAFKA']
            self.kafka_enable = True
        except:
            logging.getLogger('root_logger').warn("No KAFKA configuration has been found.")

        if self.kafka_enable:
            try:
                # Kafka producer:
                self.kafka_servers = kafka_params['KAFKA_SERVERS']
                # Producer used by OPoTPath to send the JSON messages.
                self.kafka_producer = KafkaProducer(bootstrap_servers=self.kafka_servers, linger_ms=5e3)
                # Topic where the producer is going to be sending the messages.
                self.kafka_topic = kafka_params['KAFKA_TOPIC']
                # If we are testing and we dont need kafka enabled.
                self.kafka_enable = True
            except Exception as e:
                logging.getLogger('error_logger').exception(e)
                logging.getLogger('root_logger').warn("Kafka has been disable")

                self.kafka_servers = os.environ.get('KAFKA_SERVERS', None)
                self.kafka_topic = os.environ.get('KAFKA_TOPIC', None)

                if self.kafka_servers is not None and self.kafka_topic is not None:
                    try:
                        self.kafka_producer = KafkaProducer(bootstrap_servers=self.kafka_servers, linger_ms=5e3)
                    except Exception as e:
                        self.kafka_enable = False
                        logging.getLogger('error_logger').exception(e)
                        logging.getLogger('root_logger').warn("Kafka has been disable")
                else:
                    self.kafka_enable = False
                    logging.getLogger('error_logger').exception(e)
                    logging.getLogger('root_logger').warn("Kafka has been disable")


controller_params = ControllerParams()
