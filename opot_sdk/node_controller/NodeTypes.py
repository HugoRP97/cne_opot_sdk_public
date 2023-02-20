import time
from random import randrange
from threading import Lock

from opot_sdk.helpers.enums import NodeStatus
from opot_sdk.helpers import socketsSupport
from opot_sdk.helpers.logging.NodeLogging import nodeLogging
from opot_sdk.node_controller.GenericNode import GenericNode
import logging
from socket import error

from opot_sdk.node_controller.SampleGen import SampleGen


class IngressNode(GenericNode):
    """
    This node must be the first node in the path. His mission is to listen for the packets send by the sender_app.py and
    then generate the master_secret and a new_cml value. Once this is done, it will build the first OPoT packet and send
    it to the next node in the path.
    """

    def __init__(self, netconf_packet):
        super().__init__(netconf_packet)
        # self.master_secret = randrange(0, self.lagrange_data["prime"])
        nodeLogging.root_logger.info("IngressNode Created in port {}".format(self.downstream_port))
        # Update the status and send it to the controller
        self.status = NodeStatus.OPERATIVE
        # self.sample_gen = SampleGen(self.node_address,self)

    def get_receiver_message(self):
        """
        The first node will receive the application message encrypted.

        """
        message_encrypted = socketsSupport.extract_raw_data_from_socket(self.socket, protocol=self.protocol)
        return message_encrypted

    def node_functionality(self, data_received):
        logging.info("Packet received from sender")

        # Obtain the timestamp after receiving the packet
        timestamp = int(time.time() * 1e6)

        # The OPoT mechanism starts:{}
        # We create a random integer between 0 and the prime number generated from the OPoT controller.
        # This random number is the independent term for the lagrange polynomial and at the end will be
        # the value that needs to be exactly the same that the CML value.
        master_secret = randrange(0, self.pot_profile_list.prime_number)
        nodeLogging.root_logger.debug(f'Master Secret {master_secret} for packet {self.seq}.')
        # No previous CML calculated for the first node in the OPoT path. The default CML is 0
        new_cml = self.generate_cml_value(previous_cml=0, public_secret=master_secret)
        # Add sequence number
        seq = self.increase_sequence_number()
        # Generate OPoT packet
        opot_packet = self.build_packet(mask=self.upstream_mask,
                                        message_data=data_received,
                                        public_secret=master_secret,
                                        new_cml=new_cml,
                                        seq_number=seq)
        # Get the address of the next node
        # Send the packet
        nodeLogging.root_logger.info("Sending packet to next node.")
        socketsSupport.send_raw_data_to_address(self.socket, opot_packet, self.upstream_address, self.protocol)
        # Send flow status to the controller
        self.send_opot_log(new_cml, seq, timestamp, secret=master_secret)
        # Increase by one the sequence

    def increase_sequence_number(self):
        self.seq = self.seq + 1
        # To avoid the overflow of the sequence field in the packet
        if self.seq > 2 ** (8 * 4) - 1:
            self.seq = 0
        return self.seq

    # def terminate(self):
    #     super(GenericNode, self).terminate()


class MiddleNode(GenericNode):
    """
    This node must be instantiate between two nodes in a OPoT Path. His mission is to decrypt the received OPoT packets
    and generate a new_cml value with the received information. Then it will encrypt those values and send a new OPoT
    packet to the next node in the path.
    """

    def __init__(self, netconf_packet):
        super().__init__(netconf_packet)
        nodeLogging.root_logger.info("MiddleNode Created in port {}".format(self.downstream_port))
        # Update the status and send it to the controller
        self.status = NodeStatus.OPERATIVE
        # self.send_status()

    def node_functionality(self, data_received):
        nodeLogging.root_logger.info("Packet received from the previous node.")
        # The OPoT mechanism continues:
        # We will be waiting to receive the next packet information that will has the CML value calculated in the
        # previous node. It will be an encrypted packet so we need to get the mask shared with our previous partner.
        # IMPORTANT: The mask must be negotiated before socket.recv()

        # Obtain the current timestamp
        timestamp = int(time.time() * 1e6)
        # Decrypt the packet
        public_secret, cml, seq, data = self.decrypt_opot_packet(packet=data_received, mask=self.downstream_mask)
        # Update the sequence from the packet

        # Calculate the new CML
        new_cml = self.generate_cml_value(previous_cml=cml, public_secret=public_secret)
        # We build a new packet updating the CML value and encrypting all the information.
        opot_packet = self.build_packet(mask=self.upstream_mask,
                                        new_cml=new_cml,
                                        public_secret=public_secret,
                                        seq_number=seq,
                                        message_data=data)

        nodeLogging.root_logger.debug("Sending packet to next node.")
        socketsSupport.send_raw_data_to_address(self.socket, opot_packet, self.upstream_address, self.protocol)
        # Set update to the controller
        self.send_opot_log(new_cml, seq, timestamp)


class EgressNode(GenericNode):
    """
    This node must be instantiate as the last node in a OPoT Path. His mission is to decrypt the last OPoT Packet and
    verify that the new_cml mod(p) is equal to the master_secret generated in the first node. If the condition is
    satisfied the data part of the packet will be forwarded to the receiver_app.py
    """

    def __init__(self, netconf_packet):
        super().__init__(netconf_packet)
        # Obtain the information from the previous node
        # Obtain the information of the receiver running the receiver_app.py
        self.receiver_address = self.upstream_address
        nodeLogging.root_logger.info("EgressNode Created in port {}".format(self.downstream_port))
        # Update the status and send it to the controller
        self.status = NodeStatus.OPERATIVE
        # self.send_status()

    def node_functionality(self, data_received):
        nodeLogging.root_logger.info("Packet received from the previous node.")
        # Obtain the current duration
        timestamp = int(time.time() * 1e6)
        # Decrypt the packet
        public_secret, cml, seq, data = self.decrypt_opot_packet(packet=data_received, mask=self.downstream_mask)
        # Calculate the new CML
        new_cml = self.generate_cml_value(previous_cml=cml, public_secret=public_secret)
        # The OPoT mechanism finish:
        # The new_cml mod BigPrimeNumber must be equal to the secret (Polynomial independent term).

        if (new_cml % self.pot_profile_list.prime_number) == public_secret + self.pot_profile_list.validator_key:  # Good case
            nodeLogging.root_logger.info("OPoT Successful")
            # Adding the last timestamp to the nodes_timestamps list
            try:
                socketsSupport.send_raw_data_to_address(self.socket, data, self.receiver_address,
                                                        self.protocol)
                nodeLogging.root_logger.debug("Sending data to the receiver")
            except error as e:
                nodeLogging.error_logger.exception("Error when sending packet {}".format(e))

            # Send update to the controller telling him that the OPoT was successful
            self.send_opot_log(new_cml, seq, timestamp, valid=True)
        # OPoT Unsuccessful
        else:
            nodeLogging.error_logger.error(f'OPoT unsuccessful master secret {public_secret} '
                                           f'vs calculated CML {self.pot_profile_list.prime_number}')
            # Send update to the controller telling him that the OPoT was unsuccessful
            self.send_opot_log(new_cml, seq, timestamp, valid=False)
