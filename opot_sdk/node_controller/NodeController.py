import signal
import threading
import re
import socket

import scapy.all as scapy
import sysrepo
from scapy.contrib.nsh import NSH
from scapy.layers.inet import IP, UDP
from scapy.layers.vxlan import VXLAN
from scapy.packet import Packet
from sysrepo import ChangeCreated, ChangeDeleted
from queue import Queue
from opot_sdk.node_controller.NodeTypes import *
from opot_sdk.helpers.default_params.NodeParams import node_params

scapy.split_layers(UDP, VXLAN, dport=6633)
scapy.bind_layers(UDP, NSH, dport=6633)


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
        # Client table will store all those nodes that are ingress nodes. They key identifier will be the downstream_ip.
        #  However, this could be changed depending on what we need.
        self.client_table = {}
        # Forward table, will be used to determine which node should handle the NSH packets and determine the next hop.
        # The keys will be as following:
        # {
        #   SPI : {
        #       SI: "node",
        #   }
        # }
        self.forward_table = {}
        # Dictionary to keep track of the nodes.
        self.nodes = {}

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

        self.pot_queue = Queue()
        self.sniff_queue = Queue()
        self.workers = []

        self._running = True
        self.start()

    def run(self):
        nodeLogging.root_logger.info("NodeController started")
        # Start threads
        self.setup_workers(5)
        threading.Thread(target=self.scapy_listen).start()
        threading.Thread(target=self.udp_listen).start()

        # Wait for the incoming connections of
        with sysrepo.SysrepoConnection() as conn:
            with conn.start_session() as sess:
                nodeLogging.root_logger.info("Session with sysrepo created.")
                # Load the previous stored pot paths
                nodeLogging.root_logger.info("Verify saved session on sysrepo.")
                try:
                    out = sess.get_data("/ietf-pot-profile:pot-profiles")
                    pot_profiles = out["pot-profiles"]["pot-profile-set"]
                    nodeLogging.root_logger.info("There are previous PoT paths stored.")
                    for p in pot_profiles:
                        self.create_node(p)
                except KeyError as e:
                    nodeLogging.root_logger.info("There is no previous PoT paths stored in Sysrepo")
                except Exception as e:
                    nodeLogging.error_logger.error(e)

                sess.subscribe_module_change("ietf-pot-profile", "/ietf-pot-profile:pot-profiles",
                                             self.handle_netconf_message)
                signal.sigwait({signal.SIGINT, signal.SIGTERM})

    def udp_listen(self):
        # Create a UDP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Bind the socket to the port
        server_address = ("0.0.0.0", node_params.nsh_port)
        s.bind(server_address)
        while self._running:
            b, address = s.recvfrom(4096)
            self.pot_queue.put(b)

    def setup_workers(self, workers):
        for i in range(workers):
            self.workers.append(threading.Thread(target=self.nsh_packet_worker))
            self.workers.append(threading.Thread(target=self.scapy_packet_worker))
        for w in self.workers:
            w.start()

    def nsh_packet_worker(self):
        while self._running:
            b = self.pot_queue.get()
            try:
                nsh_header = NSH(b)
                # TODO Maybe if the node does not belong to the path, we only need to forward the packet?
                # Values that will determine what to do if those values exist in the forwarding table
                spi = nsh_header.spi
                si = nsh_header.si
                try:
                    self.forward_table[spi][si].pot_packet_handler(nsh_header)
                except KeyError as e:
                    nodeLogging.root_logger.debug("This node does not belong to the pot path for this packet")
            except Exception as e:
                nodeLogging.error_logger.exception(e)

    def scapy_listen(self):
        """
        Set the sniffer for scapy
        :return:
        """
        if node_params.interfaces_to_listen is None:
            while self._running:
                scapy.sniff(prn=self.add_scapy_packet)
        else:
            interfaces = node_params.interfaces_to_listen
            while self._running:
                scapy.sniff(prn=self.add_scapy_packet, iface=interfaces)

    def add_scapy_packet(self, p: Packet):
        self.sniff_queue.put(p)

    def scapy_packet_worker(self):
        """
        Logic to determine to which node of the machine should the packet be forwarded to. This could be changed depending
        on the protocol used to forward the OPoT Packets.

        :return:
        """
        while self._running:
            p = self.sniff_queue.get()
            # First check if there is an IP header we can understand.
            if IP in p:
                ip_packet = p['IP']
                if ip_packet.src in self.client_table:
                    # self.client_table[ip_packet.src].queue.put(ip_packet)
                    self.client_table[ip_packet.src].pot_packet_handler(ip_packet)

    def terminate(self):
        """
        Method that will close the OPoTController and the deployed paths

        :return:
        """
        # Setup the running variable to False
        self._running = False

    def handle_netconf_message(self, event, req_id, changes, private_data):
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
                data = changes[0]
                # If it is requested to create a node
                if type(data) is ChangeCreated:
                    nodeLogging.root_logger.info('Creation of node has been requested')
                    self.create_node(data.value)
                elif type(data) is ChangeDeleted:
                    r = r'\b[0-9a-f]{8}\b-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-\b[0-9a-f]{12}\b'
                    path_id = re.search(r, data.xpath).group(0)
                    self.destroy_node(path_id)
        except Exception as e:
            nodeLogging.root_logger.exception('An error has occurred')
            raise e

    def create_node(self, netconf_packet):
        """
        Method that will instantiate the respective node when a create command has been received

        :param netconf_packet: The packet wit the information of the node that is going to be created
        :return:
        """

        try:
            node = None
            netconf_packet = parse_netconf_data(netconf_packet)
            # Check the type of node
            info = netconf_packet['pot_profile_list'][0]
            # This means that it is a ingress node
            if info.get('status', False):
                node = IngressNode(netconf_packet)
                self.client_table[node.downstream_ip] = node
            # If the node is a validator it means it is a egress node
            elif info.get('validator', False):
                node = EgressNode(netconf_packet)
                f = self.forward_table.get(node.service_path_identifier, {})
                f[node.service_index] = node
                self.forward_table[node.service_path_identifier] = f
            #  If not condition is satisfied it means it is a middle node
            else:
                node = MiddleNode(netconf_packet)
                f = self.forward_table.get(node.service_path_identifier, {})
                f[node.service_index] = node
                self.forward_table[node.service_path_identifier] = f
            self.nodes[node.path_id] = node
        except Exception as e:  # If there is an error while creating the node, we must remove it from the dict
            nodeLogging.root_logger.exception("Impossible to create this node")
            raise Exception(f'An error has occurred when deploying the node {e}')

    def destroy_node(self, path_id):
        """
        Method that is going to be called when a delete command is received from the opot_controller

        :param path_id: The information about the node that is going to be removed
        :return
        """
        n = self.nodes[path_id]
        if type(n) is IngressNode:
            self.client_table.pop(n.downstream_ip)
        else:
            self.forward_table.pop(n.service_path_identifier)
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
