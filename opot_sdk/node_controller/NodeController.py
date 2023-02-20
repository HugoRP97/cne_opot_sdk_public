import signal
import threading
import re

from sysrepo import ChangeCreated, ChangeDeleted
from opot_sdk.node_controller.NodeTypes import *
from opot_sdk.helpers.default_params.NodeParams import node_params
import sysrepo


class NodeController(threading.Thread):
    """
    Class that will manage all the incoming commands from the OPoTController and instantiate the different nodes. It is
    also capable of removing and updating the masks of the running nodes.
    TODO: In update and remove operations verify that the node already exists.
    """

    def __init__(self):
        # This field will store all the actives nodes in the controller by their OPoT identifier
        super().__init__()
        # Assign name to the thread
        self.name = "NodeController"
        self.nodes = {}
        self.sample_generators = {}
        self.lock = threading.Lock()
        # For logging purposes, we setup the necessary loggers used by this controller
        # Get the default parameters
        try:
            node_params
        except KeyError as e:
            logging.getLogger().exception(f'Environment variable {e.args[0]} has not been defined.')
            exit(-1)
        except Exception as e:
            logging.getLogger().exception('An exception occurred when getting the default parameters')
            exit(-1)

        self._running = True
        self.start()

    def run(self):
        nodeLogging.root_logger.info("NodeController started")
        nodeLogging.root_logger.info(f'Random change to calculate wrong cml {node_params.chance_random_error}')
        nodeLogging.root_logger.info(f'Packets every {node_params.sample_gen_time}s')

        # Wait for the incoming connections of
        with sysrepo.SysrepoConnection() as conn:
            with conn.start_session() as sess:
                nodeLogging.root_logger.info("Session with sysrepo created")
                nodeLogging.root_logger.info("Verify saved session on sysrepo.")
                try:
                    out = sess.get_data("/ietf-pot-profile:pot-profiles")
                    pot_profiles = out["pot-profiles"]["pot-profile-set"]
                    nodeLogging.root_logger.info("There are previous PoT paths stored.")
                    for p in pot_profiles:
                        pass
                        # self.create_node(p)
                except KeyError as e:
                    nodeLogging.root_logger.info("There are no previous PoT paths stored in Sysrepo")
                except Exception as e:
                    nodeLogging.error_logger.error(e)

                # Subscribe to the sysrepo session
                sess.subscribe_module_change("ietf-pot-profile", "/ietf-pot-profile:pot-profiles", self.handle_packet)
                signal.sigwait({signal.SIGINT, signal.SIGTERM})

    def terminate(self):
        """
        Method that will close the OPoTController and the deployed paths

        :return:
        """
        # TODO try to close all the currently working paths (with a timer of time X)
        # Setup the running variable to False
        self._running = False

    def handle_packet(self, event, req_id, changes, private_data):
        """
        Method that will manage all the incoming commands from the OPoTController in order to instantiate,
        update or remove the nodes of a paths.

        :arg event: Type of event that we are going to handle. For the moment we only handle "change"
        :arg changes: List of changes that are parsed from the rpc message received. For the moment we are only interested
        in the first argument, which contains the dict with all the information
        """
        # For the moment we only handle two types of events, ChangeCreated and ChangeDeleted
        try:
            if event == "change":
                nodeLogging.root_logger.info("Request Received")
                data = changes[0]
                # If it is requested to create a node
                if type(data) is ChangeCreated:
                    nodeLogging.root_logger.info('Creation of node has been requested')
                    self.create_node(data.value)
                elif type(data) is ChangeDeleted:
                    r = r'\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b'
                    path_id = re.search(r, data.xpath).group(0)
                    self.destroy_node(path_id)
                nodeLogging.root_logger.info("Request Handled")
        except Exception as e:
            nodeLogging.root_logger.exception('An error has occurred')
            raise e

    def create_node(self, netconf_packet):
        """
        Method that will instantiate the respective node when a create command has been received

        :param info: The packet wit the information of the node that is going to be created
        :return:
        """

        try:
            node = None
            netconf_packet = parse_netconf_data(netconf_packet)
            # Check the type of node
            info = netconf_packet['pot_profile_list'][0]

            nodeLogging.root_logger.info(info)
            # This means that it is a ingress node
            if info.get('status', False):
                node = IngressNode(netconf_packet)
                sample_gen = SampleGen(node.node_address, node.protocol, node_params.sample_gen_time)
                self.sample_generators[node.path_id] = sample_gen
                sample_gen.start()

            # If the node is a validator it means it is a egress node
            elif info.get('validator', False):
                node = EgressNode(netconf_packet)
            #  If not condition is satisfied it means it is a middle node
            else:
                node = MiddleNode(netconf_packet)
            self.lock.acquire()
            self.nodes[node.path_id] = node
            self.lock.release()
            # Start the node
            node.start()
        except Exception as e:  # If there is an error while creating the node, we must remove it from the dict
            if node is not None:
                node.terminate()
            try:
                path_id = node.path_id
                sample_gen = self.sample_generators.get(path_id, None)
                if sample_gen is not None:
                    sample_gen.terminate()
                    self.sample_generators.pop(path_id)
            except:
                pass

            nodeLogging.root_logger.exception("Impossible to create this node")
            raise Exception(f'An error has occurred when deploying the node {e}')

    def destroy_node(self, path_id):
        """
        Method that is going to be called when a delete command is received from the opot_controller

        :param path_id: The information about the node that is going to be removed
        :return
        """
        sample_gen = self.sample_generators.get(path_id, None)
        if sample_gen is not None:
            sample_gen.terminate()
            self.sample_generators.pop(path_id)
        self.nodes[path_id].terminate()
        self.nodes.pop(path_id)
        nodeLogging.root_logger.info(f'Node from {path_id} has been removed')

    def update_masks(self, info):
        """
        Method that will update the masks used by the node

        :param info: The information received in the request which must contain the keys
        :return:
        """
        node = self.nodes[info['opot_id']][info['node_id']]
        nodeLogging.root_logger.info(f'Update {info["masks"].keys()} masks from node {node.path_id}:{node.node_id}')
        node.update_masks(info['masks'])


def parse_netconf_data(d):
    new_d = d
    if (type(d) is dict):
        new_d = {}
        for k, v in d.items():
            new_d[k.replace('-', '_')] = parse_netconf_data(v)
    elif (type(d) is list):
        new_d = [parse_netconf_data(v) for v in d]
    return new_d
