import ipaddress
import threading
from abc import ABC, abstractmethod
import socket
import random

import grpc
from opot_sdk.helpers.descriptors.NodeDescriptor import NodeDescriptor
from opot_sdk.helpers import socketsSupport
from opot_sdk.helpers.lagrange import calculate_new_cml
from opot_sdk.helpers.logging.NodeLogging import nodeLogging
from opot_sdk.helpers.enums import Command, NodeStatus, NodeLoggingLevels
from opot_sdk.helpers.default_params.NodeParams import node_params
# Size of the OPoT info exchanged between the OPoT Packets
from opot_sdk.helpers.logging import log_pb2_grpc
from opot_sdk.helpers.logging.log_pb2 import IngressLog, EgressLog, MiddleLog
import netifaces

CML_SIZE = 8
PUBLIC_SECRET_SIZE = 4
SIZE_OF_CML_AND_SECRET = CML_SIZE + PUBLIC_SECRET_SIZE
SEQUENCE_SIZE = 4
SIZE_OF_OPOT_INFO = SIZE_OF_CML_AND_SECRET + SEQUENCE_SIZE


class GenericNode(ABC, NodeDescriptor, threading.Thread):
    """
    Abstract class used to describe the main attributes and functions of the Nodes defined in NodeTypes.py
    """

    def __init__(self, netconf_packet):
        """

        :param netconf_packet: Will be the packet that the OPoT controller send to this node.
                                  It will contain information needed to calculate all the Lagrange Polynomial.
        """
        threading.Thread.__init__(self, daemon=True)
        NodeDescriptor.__init__(self, **netconf_packet)
        # Define the first status
        self.status = NodeStatus.PREPARING
        # Field to save the error if something has occurred during the execution
        self.error = None
        # Adding the masks for the symmetric encryption, so we need to parse them
        self.upstream_mask = self.parse_mask(self.pot_profile_list.opot_masks['upstream_mask'])
        self.downstream_mask = self.parse_mask(self.pot_profile_list.opot_masks['downstream_mask'])

        # Sequence number of the last packet that have been forwarded.
        self.seq = 0

        # Define the name of the thread
        self.name = f'{self.path_id}'

        # Check which should be the listening address
        self.node_address = (get_nic_ip(self.downstream_ip), self.downstream_port)

        # Socket listener it created for receiving the OPoTPackets or the packets from the sender_app.py
        self.socket = socketsSupport.prepare_socket_for_connection(self.node_address, "Node",
                                                                   protocol=self.protocol)


        # Maybe we could find another way to use the same connexion across different nodes in the same machine
        self.log_channel = grpc.insecure_channel(f'{node_params.grpc_ip}:{node_params.grpc_port}')
        self.log_stub = log_pb2_grpc.LogReportStub(self.log_channel)

        # Set flow logging level, that will be used to send the information about the packets to the controller
        # TODO add this option to the netconf configuration
        # self.monitor = node_info.get('monitor', False)
        # self.flow_debug_level = NodeLoggingLevels.FLOW_INFO if self.monitor else NodeLoggingLevels.FLOW_INFO_CONTROLLER
        self.flow_debug_level = NodeLoggingLevels.FLOW_INFO_CONTROLLER
        self.monitor = True
        self._running = True


    def parse_mask(self, mask):
        if mask is None: return None
        mask = [m for m in mask]
        return bytearray(mask[0].to_bytes(8, 'big') + mask[1].to_bytes(8, 'big'))

    def run(self):
        """
        This is the thread method that will be used for listening incoming packets.

        :return:
        """
        self.status = NodeStatus.OPERATIVE
        # If an error has been encountered, we should continue?
        while self._running:
            try:
                data_received = socketsSupport.extract_raw_data_from_socket(self.socket, self.protocol)
                # If nothing
                if len(data_received) != 0:
                    threading.Thread(target=self.node_functionality, args=(data_received,)).start()
            except Exception as e:
                # If there is an error change the status to error.
                # TODO maybe we should remove the node and from the controller
                self.status = NodeStatus.ERROR
                self.error = e
                self.logging.error_logger.exception(f'An error has been produced in node {self.path_id}:{self.node_id}')
        self.status = NodeStatus.FINISHED
        # Tell the controller that the node has finished and is going to be destroyed

    def terminate(self):
        """
        Method to close the thread. It is important to close the socket that is listening for incoming packet from the
        nodes or the sender_app.py in the run method.

        :return:
        """
        self._running = False
        socketsSupport.send_raw_data_to_address(self.socket,bytearray(), self.node_address, self.protocol)
        if self.protocol == 'TCP':
            self.socket.shutdown(socket.SHUT_WR)
        self.socket.close()

    def get_mask(self, mask_type):
        """
        This method must return the prev-next mask that will depend on the node we are working with.

        :param mask_type: It should be "prev" or "next"
        :return:
        """
        return self.pot_profile_list.opot_masks['upstream_mask'] if mask_type == "next" \
            else self.pot_profile_list.opot_masks['downstream_mask']

    def generate_cml_value(self, previous_cml, public_secret):
        """

        :param previous_cml: All previous information calculated.
        :param public_secret: Secret obtained from the previous packet.
        :return: It will return the CML calculated for this node.
        """
        #
        if random.random() < node_params.chance_random_error:
            return calculate_new_cml(previous_cml + 1, public_secret + 1, prime_number=self.pot_profile_list.prime_number,
                                 secret_share=self.pot_profile_list.public_polynomial, lpc=self.pot_profile_list.lpc)
        else:
            return calculate_new_cml(previous_cml, public_secret, prime_number=self.pot_profile_list.prime_number,
                                     secret_share=self.pot_profile_list.public_polynomial, lpc=self.pot_profile_list.lpc)



    # TODO do this in another way
    @staticmethod
    def generate_opot_message(cml, secret, lagrange, state):
        # cml:secret:y_point:lpc:prime
        return f'{cml}:{secret}:{lagrange["y_point"]}:{lagrange["LPC"]}:{lagrange["prime"]}:{state}'

    def build_packet(self, mask, public_secret, new_cml, seq_number, message_data):
        """
        This function will return a packet with the structure needed for the OPoT protocol.

        :param mask: Mask used for encrypting the message_data
        :param message_data:
        :param public_secret: Information needed to build the packet. In this case it will be the secret
                      (Independent term of the polynomial).
        :param new_cml: It will be the accumulative values previously calculated in the nodes.
                             In the first node it will be 0.
        :param seq_number: Sequence number of the packet.
        :return:     It will construct a packet for sending to the next node with the data param received.
        """
        # We extract a mask for encrypt the data.
        encryption_key = self.get_mask("next")
        # We encrypt the OPoT content of the message with the received mask.
        packet_encrypted = self.crypt_opot_values(public_secret, new_cml, mask, seq_number)
        packet_encrypted.extend(message_data)
        return packet_encrypted

    @staticmethod
    def crypt_opot_values(secret, cml, key, seq_number):
        """
        Method that will crypt the new OPoT values using the mask.

        :param seq_number: sequence number of the packet
        :param secret: secret obtained from the previous packet
        :type secret: int
        :param cml: CML calculated with the received packet
        :type cml: int
        :param key: next_mask to encrypt the opot information
        :type key: bytearray
        :return: return the encrypted values of secret and cml
        """
        # Transform to bytes the secret and the cml
        secret_b = int(secret).to_bytes(PUBLIC_SECRET_SIZE, "big")
        cml_b = int(cml).to_bytes(CML_SIZE, "big")
        seq_number_b = int(seq_number).to_bytes(SEQUENCE_SIZE, "big")

        # Then we add the secret and cml values to the packet 
        packet_decrypted = bytearray(secret_b)
        packet_decrypted.extend(cml_b)
        packet_decrypted.extend(seq_number_b)

        # We encrypt the data received. The packet_encrypted is composed by the Secret followed by the CML
        # in Big Endian.
        packet_encrypted = bytearray()
        for i in range(len(packet_decrypted)):
            packet_encrypted.append(packet_decrypted[i] ^ key[i])
        return packet_encrypted

    @staticmethod
    def decrypt_opot_packet(packet, mask):
        """
        Method to decrypt and separated the values obtained with the received OPoT packet.

        :param packet: packet received from the previous node
        :type packet: bytearray
        :param mask: prev_key to decrypt the opot information
        :type mask: bytearray
        :return: dictionary with the masks "message_data", "secret", "seq", "data"
        """
        # We decrypt the data received.
        packet_decrypted = bytearray()
        # We decrypt until the cml + secret size of the packet. The other part of the packet is the
        # client application message which we will not be able to decrypt.
        for i in range(SIZE_OF_OPOT_INFO):
            packet_decrypted.append(packet[i] ^ mask[i])

        secret_decrypted = int.from_bytes(packet_decrypted[:PUBLIC_SECRET_SIZE], "big")
        cml_decrypted = int.from_bytes(packet_decrypted[PUBLIC_SECRET_SIZE:SIZE_OF_CML_AND_SECRET], "big")
        # We could also encrypt the sequence
        seq = int.from_bytes(packet_decrypted[SIZE_OF_CML_AND_SECRET:SIZE_OF_OPOT_INFO], "big")
        # Obtain data from the raw packet
        data = bytes(packet[SIZE_OF_OPOT_INFO:])
        return secret_decrypted, cml_decrypted, seq, data

    @abstractmethod
    def node_functionality(self, data_received):
        """
        Depending on what kind of node (first, middle, last) is, the functionality will be different in the OPoT paradigm.

        :param data_received: Will be the packet received from the other nodes or from the receiver.
        :return:
        """
        pass

    def send_opot_log(self, cml, seq, timestamp, secret=None, valid=None):
        """
        This method is used to send the information about the OPoT to the.

        :param cml: The calculated CML in the Node
        :param timestamp: The timestamp added to the opot_packet
        :param secret: In the first node we should send the secret
        :param valid: The last node must tell if the controller if the OPoT was successful or not
        :return:
        """
        data = {"path_id": self.path_id, "node_id": self.node_id, "sequence_number": seq, "cml": cml,
                "timestamp": timestamp}
        # print(data)
        if secret is not None:
            data['secret'] = secret
            log = IngressLog(**data)
            self.log_stub.ingressToController(log)
        elif valid is not None:
            data['valid'] = valid
            log = EgressLog(**data)
            self.log_stub.egressToController(log)
        else:
            log = MiddleLog(**data)
            self.log_stub.middleToController(log)

        # self.logging.flow_logger.log(self.flow_debug_level, data)
        # self.send_data_to_controller(data, self.flow_debug_level)
        # nodeLogging.root_logger.debug("Sending flow information to controller")

    # TODO change the logic of the following methods to handle possible errors or status changes.
    def send_error(self, message):
        pass
        # self.send_data_to_controller(message, NodeLoggingLevels.ERROR_NODE)
        # nodeLogging.root_logger.error("Sending error to controller")

    def send_status(self):
        pass
        """
        Method that will send the status of the node to the OPoTController.
        :return:
        """
        # data = {"opot_id": self.path_id, "node_id": self.node_id, 'node_status': self.status.value}
        # self.logging.flow_logger.log(NodeLoggingLevels.NODE_STATUS, data)
        # self.send_data_to_controller(data, NodeLoggingLevels.NODE_STATUS)
        # nodeLogging.root_logger.debug("Sending node status to controller")

    def send_data_to_controller(self, data, level):
        pass


def get_nic_ip(ip_to_check):
    ifaces = netifaces.interfaces()
    for i in ifaces:
        iface = netifaces.ifaddresses(i).get(netifaces.AF_INET, None)
        print(iface)
        if iface is not None:
            for info in iface:
                ip = info["addr"]
                mask = info["netmask"]
                if ipaddress.ip_address(ip_to_check) in ipaddress.ip_network(f'{ip}/{mask}', strict=False):
                    return ip
    raise Exception(f'Error, none of the NICs addresses are suitable for {ip_to_check}')
