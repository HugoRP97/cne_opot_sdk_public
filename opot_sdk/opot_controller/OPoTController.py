import threading
import grpc
from concurrent import futures

import time
from prometheus_client import start_http_server
from ncclient import manager
from opot_sdk.helpers.logging.ControllerLogging import controller_logging
from opot_sdk.helpers.logging import log_pb2_grpc
from opot_sdk.opot_controller.LogListener import LogListener
from opot_sdk.opot_controller.OPoTPath import OPoTPath
from opot_sdk.helpers.enums import Command, NodeStatus, PathStatus
from opot_sdk.helpers.Singleton import Singleton
from opot_sdk.helpers.default_params.ControllerParams import controller_params


class OPoTController(threading.Thread, metaclass=Singleton):
    """
    Class that will handle all the classes. Since we only want an instance of the class it is a singleton. It will
    run as a thread waiting for the incoming packets like requests or responses from the nodes.
    """

    def __init__(self):
        super().__init__()
        self.log_server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.paths = {}
        # Get the environment variables, where it is defined from which port the controller must be listening to
        # incoming packets. Also, we must define the IP of the OPoT Controller and the port where the nodes are
        # listening the controller packets

        # First lets configure the static parameters like the working port, ip address, etc...
        try:
            controller_params
        except KeyError as e:
            controller_logging.error_logger.exception(f'Environment variable {e.args[0]} has not been defined.')
            exit(-1)
        except Exception as e:
            controller_logging.error_logger.exception('An exception occurred when getting the default parameters')
            exit(-1)
        # self.node_controller_port = params.node_controller_port

        self._running = True
        self.daemon = True
        self.start()

    def run(self):
        # First we check if the thread was stopped, so we can instantiate another socket
        start_http_server(controller_params.prometheus_port, addr=controller_params.prometheus_ip)
        # Start logging server
        self.serve_log_server()
        controller_logging.root_logger.info("Starting OPoTController")

    def terminate(self):
        """
        Method that will close the OPoTController and the deployed paths

        :return:
        """
        # TODO try to close all the currently working paths (with a timer of time X)
        # Setup the running variable to False
        self._running = False
        # Remove the existing paths
        for path in self.paths:
            self.destroy_path(path.path_id)
        # Close the grpc server
        self.log_server.stop(0)

    def handle_packet(self, packet):
        """
        Method that handles the incoming packets to the OPoTController.

        :param packet: Packet with the command and the information that will be managed by the method
        :return:
        """
        # If we receive an update from the opot_nodes
        try:
            if packet['command'] == Command.UPDATE_FLOW_STATUS:
                controller_logging.root_logger.debug(
                    "Information about a flow update has been received from node {}".format(packet['info']['node_id']))
                self.paths[packet['info']['opot_id']].update_flow_status(packet['info'])
                self.paths[packet['info']['opot_id']].update_node_status(packet['info'])
            if packet['command'] == Command.UPDATE_NODE_STATUS:
                controller_logging.root_logger.debug(
                    f'Information about a node update has been received from {packet["info"]["node_id"]}')
                self.paths[packet['info']['opot_id']].update_node_status(packet['info'])
        except Exception:
            controller_logging.root_logger.exception("An error has occurred")

    def create_path(self, data):
        """
        This method will deploy the paths passed for the moment via a file.
        :param data The information that needs the OPoTPath in order to create the necessary values.
        :return
        """
        controller_logging.root_logger.info("Path creation has been requested")
        # Save the paths information as a field
        path = OPoTPath(data)
        test = data.get('prometheus', False)
        self.paths[path.path_id] = path
        try:
            for node_id, node in path.nodes.items():

                # Create the connexion to the ncclient
                with manager.connect(host=node.node_mgmt_ip,
                                     port=controller_params.netconf_ssh_port,
                                     username=controller_params.netconf_user,
                                     password=controller_params.netconf_password,
                                     timeout=90,
                                     hostkey_verify=False) as m:
                    config = node.create_node_config().decode('utf8')
                    response = m.edit_config(config=config, target='running')
                    node.status = NodeStatus.OPERATIVE
        except Exception as e:
            controller_logging.root_logger.exception(f'Error occurred when instantiating the node {node_id}')
            try:
                self.destroy_path(path.path_id)
            except:
                pass
            raise e
        path.status = PathStatus.OPERATIVE
        if test:
            duration = int(time.time() * 1e6) - path.creation_time
            controller_params.create_time_metric.set(duration)
        controller_logging.root_logger.info(f'Path {path.path_id} has been created')
        return path.path_id

    def destroy_path(self, path_id):
        """
        Method that removes a paths based in their id.

        :param path_id: Path that we are going to remove
        :return:
        """
        controller_logging.root_logger.debug(f'Path {path_id} is going to be removed')
        for node_id, node in self.paths[path_id].nodes.items():
            # If the node is in state
            if node.status != NodeStatus.PREPARING:
                try:
                    with manager.connect(host=node.node_mgmt_ip,
                                         port=controller_params.netconf_ssh_port,
                                         username=controller_params.netconf_user,
                                         password=controller_params.netconf_password,
                                         timeout=90,
                                         hostkey_verify=False) as m:
                        config = node.remove_node_config().decode('utf8')
                        response = m.edit_config(config=config, target='running')
                except Exception as e:
                    # TODO ADD any kind of validation to check if the node is still working
                    controller_logging.root_logger.exception(f'Error occurred when removing the node {node_id}')
                    raise e
        self.paths.pop(path_id)
        controller_logging.root_logger.info(f'Path {path_id} has been removed.')
        return True

    def serve_log_server(self):
        """
        This method instantiate a gRPC server that will be listening for the incoming OPoT logs from the nodes.

        :return:
        """

        log_pb2_grpc.add_LogReportServicer_to_server(LogListener(self.paths), self.log_server)
        # TODO add listener address
        listen_addr = f'{controller_params.controller_ip}:{controller_params.grpc_port}'
        self.log_server.add_insecure_port(listen_addr)
        controller_logging.root_logger.info(f'Starting server on {listen_addr}')
        self.log_server.start()
