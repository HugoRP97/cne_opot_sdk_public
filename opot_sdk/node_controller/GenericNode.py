import json
from abc import ABC, abstractmethod
import socket
from queue import Queue

import grpc
from scapy.contrib.nsh import NSH
from scapy.packet import Packet

from opot_sdk.helpers.descriptors.NodeDescriptor import NodeDescriptor
from opot_sdk.helpers import socketsSupport
from opot_sdk.helpers.lagrange import calculate_new_cml
from opot_sdk.helpers.logging.NodeLogging import nodeLogging
from opot_sdk.helpers.enums import Command, NodeStatus, NodeLoggingLevels
from opot_sdk.helpers.default_params.NodeParams import node_params
# Size of the OPoT info exchanged between the OPoT Packets
from opot_sdk.helpers.logging import log_pb2_grpc
from opot_sdk.helpers.logging.log_pb2 import IngressLog, EgressLog, MiddleLog

CML_SIZE = 8
PUBLIC_SECRET_SIZE = 4
SIZE_OF_CML_AND_SECRET = CML_SIZE + PUBLIC_SECRET_SIZE
SEQUENCE_SIZE = 4
SIZE_OF_POT_INFO = SIZE_OF_CML_AND_SECRET + SEQUENCE_SIZE


class GenericNode(ABC, NodeDescriptor):
    """
    Abstract class used to describe the main attributes and functions of the Nodes defined in NodeTypes.py
    """

    def __init__(self, netconf_packet):
        """

        :param netconf_packet: Will be the packet that the OPoT controller send to this node.
                                  It will contain information needed to calculate all the Lagrange Polynomial.
        """
        NodeDescriptor.__init__(self, **netconf_packet)
        # Define the first status
        self.status = NodeStatus.PREPARING
        # Field to save the error if something has occurred during the execution
        self.error = None
        # Adding the masks for the symmetric encryption, so we need to parse them
        self.upstream_mask = self.parse_mask(self.pot_profile_list.opot_masks['upstream_mask'])
        self.downstream_mask = self.parse_mask(self.pot_profile_list.opot_masks['downstream_mask'])

        # How many nodes including the current one are left in the path.
        self.service_index = self.pot_path_length + 1 - self.node_position



        # Define the name of the thread
        self.name = f'{self.path_id}'

        # Maybe we could find another way to use the same connexion across different nodes in the same machine
        self.log_channel = grpc.insecure_channel(f'{node_params.grpc_ip}:{node_params.grpc_port}')
        self.log_stub = log_pb2_grpc.LogReportStub(self.log_channel)
        # Queue that will be use to pass the packets to the thread
        self.queue = Queue()

        # Set flow logging level, that will be used to send the information about the packets to the controller
        # TODO add this option to the netconf configuration
        # self.monitor = node_info.get('monitor', False)
        self.flow_debug_level = NodeLoggingLevels.FLOW_INFO_CONTROLLER
        self.monitor = True
        self._running = True

    def parse_mask(self, mask):
        if mask is None: return None
        mask = [m for m in mask]
        return bytearray(mask[0].to_bytes(8, 'big') + mask[1].to_bytes(8, 'big'))

    def terminate(self):
        """
        Method to close the thread. It is important to close the socket that is listening for incoming packet from the
        nodes or the sender_app.py in the run method.

        :return:
        """
        self._running = False
        self.queue.empty()

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
        :param public_secret:      Secret obtained from the previous packet.
        :return:            It will return the CML calculated for this node.
        """
        #
        return calculate_new_cml(previous_cml, public_secret, prime_number=self.pot_profile_list.prime_number,
                                 public_pol=self.pot_profile_list.secret_share, lpc=self.pot_profile_list.lpc,
                                 secret_share=self.pot_profile_list.secret_share)

    # TODO do this in another way
    @staticmethod
    def generate_opot_message(cml, secret, lagrange, state):
        # cml:secret:y_point:lpc:prime
        return f'{cml}:{secret}:{lagrange["y_point"]}:{lagrange["LPC"]}:{lagrange["prime"]}:{state}'

    @staticmethod
    def crypt_pot_values(secret, cml, seq_number, mask):
        """
        Method that will crypt the new OPoT values using the mask.

        :param seq_number:
        :param secret: secret obtained from the previous packet
        :type secret: int
        :param cml: CML calculated with the received packet
        :type cml: int
        :param mask: next_mask to encrypt the opot information
        :type mask: bytearray
        :return: return the encrypted values of secret and cml
        """
        # Transform to bytes the secret and the cml
        secret_b = int(secret).to_bytes(PUBLIC_SECRET_SIZE, "big")
        cml_b = int(cml).to_bytes(CML_SIZE, "big")
        seq_number_b = int(seq_number).to_bytes(SEQUENCE_SIZE, "big")

        # Then we add the secret and cml values to the packet
        pot_values = bytearray(secret_b)
        pot_values.extend(cml_b)
        pot_values.extend(seq_number_b)

        # We encrypt the data received. The packet_encrypted is composed by the Secret followed by the CML
        # in Big Endian.
        enc_pot_values = bytearray()
        for i in range(len(pot_values)):
            enc_pot_values.append(pot_values[i] ^ mask[i])
        return enc_pot_values

    @staticmethod
    def decrypt_pot_values(packet, mask):
        """
        Method to decrypt and separated the values obtained with the received OPoT packet.

        :param packet: packet received from the previous node
        :type packet: bytearray
        :param mask: prev_key to decrypt the opot information
        :type mask: bytearray
        :return: secret,
        """
        # We decrypt the data received.
        decrypted_pot_values = bytearray()
        # We decrypt until the cml + secret size of the packet. The other part of the packet is the
        # client application message which we will not be able to decrypt.
        for i in range(SIZE_OF_POT_INFO):
            decrypted_pot_values.append(packet[i] ^ mask[i])

        secret = int.from_bytes(decrypted_pot_values[:PUBLIC_SECRET_SIZE], "big")
        cml = int.from_bytes(decrypted_pot_values[PUBLIC_SECRET_SIZE:SIZE_OF_CML_AND_SECRET], "big")
        # We could also encrypt the sequence
        seq = int.from_bytes(decrypted_pot_values[SIZE_OF_CML_AND_SECRET:SIZE_OF_POT_INFO], "big")
        # Obtain data from the raw packet
        return secret, cml, seq

    @abstractmethod
    def pot_packet_handler(self, p: Packet):
        """
        Method that will handle the incoming packets from scapy (PoT packets or Client packets)

        :param p: Packet that the function must handle.
        :return:
        """
        pass

    def send_pot_log(self, cml, timestamp, seq, secret=None, valid=None):
        """
        This method is used to send the information about the OPoT to the.

        :param cml: The calculated CML in the Node
        :param timestamp: The timestamp added to the opot_packet
        :param secret: In the first node we should send the secret
        :param valid: The last node must tell if the controller if the OPoT was successful or not
        :return:
        """
        data = {"path_id": self.path_id, "node_id": str(self.node_id), "sequence_number": seq, "cml": cml,
                "timestamp": timestamp}
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
        nodeLogging.root_logger.debug("Sending flow information to controller")

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

    @staticmethod
    def verify_nsh_packet(nsh_header: NSH):
        return nsh_header.ttl > 0
