import os
import socket
import threading
import time
from random import randrange

import scapy.all as scapy
from scapy.contrib.nsh import NSH
from scapy.layers.inet import UDP, IP, TCP, fragment
from scapy.layers.l2 import Ether
from scapy.packet import Packet

from opot_sdk.helpers.default_params.NodeParams import node_params
from opot_sdk.helpers.enums import NodeStatus
from opot_sdk.helpers import socketsSupport
from opot_sdk.helpers.logging.NodeLogging import nodeLogging
from opot_sdk.node_controller.GenericNode import GenericNode


class IngressNode(GenericNode):
    """
    This node must be the first node in the path. His mission is to listen for the packets send by the sender_app.py and
    then generate the master_secret and a new_cml value. Once this is done, it will build the first OPoT packet and send
    it to the next node in the path.
    """

    def __init__(self, netconf_packet):
        super().__init__(netconf_packet)
        # self.master_secret = randrange(0, self.lagrange_data["prime"])
        nodeLogging.root_logger.info("IngressNode Created")
        # Update the status and send it to the controller
        self.status = NodeStatus.OPERATIVE
        # Socket to send udp packets
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.seq = 0

    #  TODO for the moment we are using UDP to encapsulate the NSH header so fragmentation by the IP protocol
    def pot_packet_handler(self, p: Packet):
        # Obtain the timestamp after receiving the packet
        timestamp = int(time.time() * 1e6)
        # We create a random integer between 0 and the prime number generated from the OPoT controller.
        # This random number is the independent term for the lagrange polynomial and at the end will be
        # the value that needs to be exactly the same that the CML value.
        public_secret = randrange(0, self.pot_profile_list.prime_number)
        new_cml = self.generate_cml_value(previous_cml=0, public_secret=public_secret)
        # Add sequence number
        seq = self.increase_sequence_number()
        # Calculate first the pot information, which will be stored in the 16bytes context header of the NSH header
        context_header = self.crypt_pot_values(public_secret, new_cml, self.seq, self.upstream_mask)
        # Create the NSH header with the information needed.
        ip_packet = p[IP]
        nsh_header = self.generate_nsh(context_header, ip_packet)
        # Send the encapsulated packet to the next hop IP / UDP / NSH
        self.socket.sendto(bytes(nsh_header), (self.upstream_ip, node_params.nsh_port))
        # scapy.send(IP(dst=self.upstream_ip) / udp_header, verbose=False)
        # Send logs to controller
        nodeLogging.root_logger.debug(f'Master Secret {public_secret} for packet {self.seq}.')
        nodeLogging.root_logger.debug("Sending packet to next node.")
        self.send_pot_log(new_cml, timestamp, seq, secret=public_secret)

    def generate_nsh(self, context_header, ip_packet):
        return NSH(
            ttl=self.pot_path_length + 1,
            mdtype=1,
            # IP
            nextproto=1,
            # SFC path information
            spi=self.service_path_identifier,
            si=self.pot_path_length - 1,
            # PoT data
            context_header=context_header
        ) / ip_packet

    def increase_sequence_number(self):
        self.seq = self.seq + 1
        # To avoid the overflow of the sequence field in the packet
        if self.seq > 2 ** (8 * 4) - 1:
            self.seq = 0
        return self.seq


class MiddleNode(GenericNode):
    """
    This node must be instantiate between two nodes in a OPoT Path. His mission is to decrypt the received OPoT packets
    and generate a new_cml value with the received information. Then it will encrypt those values and send a new OPoT
    packet to the next node in the path.
    """

    def __init__(self, netconf_packet):
        super().__init__(netconf_packet)
        nodeLogging.root_logger.info("MiddleNode Created")
        # Update the status and send it to the controller
        self.status = NodeStatus.OPERATIVE
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def pot_packet_handler(self, nsh_header: NSH):
        timestamp = int(time.time() * 1e6)
        # First get the NSH packet
        if not self.verify_nsh_packet(nsh_header):
            return
        # If the verification of the packet is correct, get the context header
        enc_pot_data = nsh_header.context_header
        # Decode pot data
        public_secret, cml, seq = self.decrypt_pot_values(packet=enc_pot_data, mask=self.downstream_mask)
        # Calculate new_cml
        new_cml = self.generate_cml_value(previous_cml=cml, public_secret=public_secret)
        # Encrypt pot values
        new_enc_pot_data = self.crypt_pot_values(public_secret, new_cml, seq, self.upstream_mask)
        # Modify nsh_header
        nsh_header.ttl = nsh_header.ttl - 1
        nsh_header.si = nsh_header.si - 1
        nsh_header.context_header = new_enc_pot_data
        # Send the new packet
        self.socket.sendto(bytes(nsh_header), (self.upstream_ip, node_params.nsh_port))
        # Send logs
        self.send_pot_log(new_cml, timestamp, seq)


class EgressNode(GenericNode):
    """
    This node must be instantiate as the last node in a OPoT Path. His mission is to decrypt the last OPoT Packet and
    verify that the new_cml mod(p) is equal to the master_secret generated in the first node. If the condition is
    satisfied the data part of the packet will be forwarded to the receiver_app.py
    """

    def __init__(self, netconf_packet):
        super().__init__(netconf_packet)
        # Obtain the information from the previous node
        nodeLogging.root_logger.info("EgressNode Created in port.")
        # Update the status and send it to the controller
        self.status = NodeStatus.OPERATIVE
        if os.environ.get("FORCE_ERROR", None) is not None:
            self.pot_profile_list.lpc = self.pot_profile_list.lpc + 1

    def pot_packet_handler(self, nsh_header: NSH):
        timestamp = int(time.time() * 1e6)
        # First get the NSH packet
        if not self.verify_nsh_packet(nsh_header):
            return
        # If the verification of the packet is correct, get the context header
        enc_pot_data = nsh_header.context_header
        # Decode pot data
        public_secret, cml, seq = self.decrypt_pot_values(packet=enc_pot_data, mask=self.downstream_mask)
        # Calculate the new CML
        new_cml = self.generate_cml_value(previous_cml=cml, public_secret=public_secret)
        if (
                new_cml % self.pot_profile_list.prime_number) == public_secret + self.pot_profile_list.validator_key:  # Good case
            ip_packet = nsh_header[IP]
            scapy.send(ip_packet, verbose=False)
            self.send_pot_log(new_cml, timestamp, seq, valid=True)
        else:
            nodeLogging.error_logger.error(f'OPoT unsuccessful master secret {public_secret} '
                                           f'vs calculated CML {self.pot_profile_list.prime_number}')
            # Send update to the controller telling him that the OPoT was unsuccessful
            self.send_pot_log(new_cml, timestamp, seq, valid=False)
