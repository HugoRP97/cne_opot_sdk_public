import json
import os
import uuid
from collections import OrderedDict
import time
import random
from opot_sdk.helpers.default_params.ControllerParams import controller_params
from opot_sdk.helpers.descriptors.PotProfileListDescriptor import PotProfileListDescriptor
from opot_sdk.helpers.descriptors.OPotLogDescriptor import OPoTLog
from opot_sdk.helpers.lagrange import generate_lagrange_parameters, calculate_new_cml
from opot_sdk.helpers.enums import Command, NodeStatus, NodeType, PathStatus, FlowStatus
from opot_sdk.helpers.logging.ControllerLogging import controller_logging
from opot_sdk.opot_controller import MaskManager
from opot_sdk.opot_controller.NodeInfo import NodeInfo


class OPoTPath:
    """
    Class that will be used to store all the information about the deployed OPoT Scenario
    in order to be able of tracking the information sent by the nodes
    """

    def __init__(self, data):
        """
        This will instantiate all the necessary parameters to deploy the scenario.

        :param data:
        """
        # For logging module
        self.creation_time = int(time.time() * 1e6)
        self.path_id = str(uuid.uuid1())
        self.service_path_identifier = random.randint(1, 16777216)
        self.number_of_nodes = len(data['nodes'])
        self.protocol = data['protocol']
        self.prime = None  # To remove the warning from intellij
        # Set the receiver address
        self.receiver_ip = data['receiver']['ip']
        # Set the sender (it can be useful for next prototypes) address
        self.sender_ip = data['sender']['ip']
        # Add the instance of the mask_manager and extract the masks
        self.mask_manager = MaskManager.get_mask_manager()
        self.masks = self.mask_manager.extract_opot_masks(self.number_of_nodes)
        self.nodes = self.generate_node_descriptors(data['nodes'])

        # self.mask_manager = MaskManager(self)
        # We should consider the possibility where we are sending more than one packet, so there is a sequence number
        # were we want to identify each packet sent by the sender_app.py. That is the reason why we put the
        # flow_status as a dictionary, to store the status of each of the packets sent by the send_app.py
        self.flow_status = {}
        self.status = PathStatus.PREPARING
        self.prometheus = data.get('prometheus', None)

    def generate_node_descriptors(self, data_nodes):
        """
        This method is used to obtain all the node information from the paths that we are deploying.

        :param data_nodes: Path that we want to create
        :return: It will return an array with the information of each of the nodes. The indexes of this array will be the
        ids of each of the nodes.
        """
        # Dict that will help to store the information of each of the nodes. Notice that each node has a node_id
        # value, which will be the position of the node in the OPoT path and in the list

        nodes = []
        lagrange_parameters = generate_lagrange_parameters(self.number_of_nodes)
        self.prime = lagrange_parameters['prime_number']
        for i in range(self.number_of_nodes):
            address = data_nodes[i]
            pot_profile_list = {
                "bitmask": 64,
                "secret_share": int(lagrange_parameters["y_points"][i]),
                "lpc": lagrange_parameters["LPCs"][i],
                "prime_number": self.prime,
            }
            # IngressNode configuration
            if i == 0:
                pot_profile_list["opot_masks"] = {"upstream_mask": self.masks[i]}
                pot_profile_list["status"] = True
                nodes.append(NodeInfo(
                    node_mgmt_ip=address['mgmt_ip'],
                    downstream_ip=address['path_ip'],
                    pot_profile_name=self.path_id,
                    pot_profile_list=[pot_profile_list],
                    service_path_identifier=self.service_path_identifier,
                    protocol=self.protocol,
                    pot_path_length=self.number_of_nodes,
                    node_position=i + 1
                ))
            # EgressNode
            elif i == (self.number_of_nodes - 1):
                if os.environ.get("FORCE_ERROR",None) is not None:
                    pot_profile_list['lpc'] = pot_profile_list['lpc'] + 1
                pot_profile_list["validator_key"] = lagrange_parameters['polynomial'][-1]
                pot_profile_list["validator"] = True
                pot_profile_list["opot_masks"] = {"downstream_mask": self.masks[i - 1]}

                nodes.append(NodeInfo(
                    node_mgmt_ip=address['mgmt_ip'],
                    downstream_ip=address['path_ip'],
                    upstream_ip=self.receiver_ip,
                    pot_profile_name=self.path_id,
                    service_path_identifier=self.service_path_identifier,
                    pot_path_length=self.number_of_nodes,
                    pot_profile_list=[pot_profile_list],
                    protocol=self.protocol,
                    node_position= i + 1
                ))
            # Middle Node
            else:
                pot_profile_list["opot_masks"] = {"upstream_mask": self.masks[i], "downstream_mask": self.masks[i - 1]}
                nodes.append(NodeInfo(
                    node_mgmt_ip=address['mgmt_ip'],
                    downstream_ip=address['path_ip'],
                    service_path_identifier=self.service_path_identifier,
                    pot_path_length=self.number_of_nodes,
                    pot_profile_name=self.path_id,
                    pot_profile_list=[pot_profile_list],
                    protocol=self.protocol,
                    node_position= i + 1
                ))

        nodes_descriptors = OrderedDict()
        # Adding the final information
        for i, node in enumerate(nodes):
            if i == 0 or i != (self.number_of_nodes - 1):
                node.set_upstream_node(nodes[i + 1])
            if i == (self.number_of_nodes - 1) or i != 0:
                node.set_downstream_node(nodes[i - 1])
            nodes_descriptors[node.node_id] = node
        return nodes_descriptors

    def create_node_command(self, node_id):
        """
        This method builds the crate_command data for the specific node. It will return the data that will be sent to
        the specific node controller.

        :return: data that will be sent to the node
        """
        info = {"path_id": self.path_id, "protocol": self.protocol}
        data = {"command": Command.CREATE_NODE.value, "info": info}
        # Get the specific node information (prev | next)
        node_info = self.nodes[node_id]
        info['node_info'] = node_info.get_node_info()
        # Add masks

        # Add the information of the previous or next node if needed
        # If prev node
        masks = {}
        if node_info.downstream_id is not None:
            info['prev_info'] = self.nodes[node_info.downstream_id].get_info_as_next_prev()
        # If next node
        if node_info.upstream_id is not None:
            info['next_info'] = self.nodes[node_info.upstream_id].get_info_as_next_prev()
        # Add the information of the receiver or the receiver if needed
        # If first node
        if node_info.node_type == NodeType.INGRESS:
            info['sender_info'] = self.sender_address
        # If last node
        if node_info.node_type == NodeType.EGRESS:
            info['receiver_info'] = self.receiver_address
        return data

    def update_flow_status(self, log: OPoTLog):
        """
        Method that will update the information about a flow. The data will contain the information about a packet
        that has crossed one of the nodes of the path. It may contain the master_secret or if the opot was
        successful or not.

        :param log: The information that must contain the sequence number and the calculated CML by the node. Then
        it can include the final state of the OPoT or the master_secret.
        :return:
        """
        seq_number = log.sequence_number
        # Update Node_status
        # First we check that a FlowInfo already exists with the respective sequence number. If not we create it
        if seq_number not in self.flow_status:
            self.flow_status[seq_number] = FlowInfo(self.number_of_nodes)
        flow_status = self.flow_status[seq_number]
        flow_status.update_status(log)
        # Check the current state of the flow if there is an error run in other threat the calculation to prevent
        #  blocking the main thread
        if flow_status.status == FlowStatus.SUCCESSFUL:
            if self.prometheus:
                controller_params.valid_time_metric.set(flow_status.duration)
                controller_params.valid_validations_metric.inc(1)
            controller_logging.valid_logger.debug(f'{time.time()},{seq_number},{True},{flow_status.duration}')
            controller_logging.root_logger.debug(
                f'OPoT was successful in path "{self.path_id}" for the packet {seq_number}'
                f' with a duration of {flow_status.duration} microseconds.')
            self.send_to_kafka(flow_status, seq_number)

            # controllerLogging.flow_logger.debug(f'{self.path_id},{seq_number},{flow_status.duration}')
        elif flow_status.status == FlowStatus.FAIL:
            if self.prometheus:
                controller_params.invalid_time_metric.set(flow_status.duration)
                controller_params.invalid_validations_metric.inc(1)
            error_position = flow_status.locate_error(self.nodes)
            controller_logging.valid_logger.debug(f'{time.time()},{seq_number},{False},{flow_status.duration}')
            # controller_logging.root_logger.error(
            #     f'OPoT was unsuccessful in path "{self.path_id}" for the packet {seq_number}'
            #     f' between the nodes {error_position - 1} and {error_position}.')
            self.send_to_kafka(flow_status, seq_number)
        controller_logging.flow_logger.debug(log)

    def send_to_kafka(self, flow_status, packet_number):
        """
        Method that produces the kafka information and is sent to the kafka producers.

        :param flow_status:
        :param packet_number:
        :return:
        """
        if controller_params.kafka_enable:
            node_list = list(self.nodes.keys())
            flow_status.timestamps.sort()
            timestamps = flow_status.timestamps
            data = {"pot_id": self.path_id, "packet_number": packet_number, "nodes": node_list,
                    "timestamps": timestamps, "valid": flow_status.status == FlowStatus.SUCCESSFUL}
            message = json.dumps(data).encode('utf-8')
            controller_params.kafka_producer.send(controller_params.kafka_topic, message)

    def update_node_status(self, data):
        """
        Method to update the status of the path. This will also update the status of the path.

        :param data: It must contain the status information about an existing node.
        :return:
        """
        node_info = self.nodes[data['node_id']]
        node_info.status = data['node_status']
        self.update_status()

    def update_status(self):
        """
        Method that returns and update the status of the path. It will consider the status of all the nodes to
        update the status.

        :return: It will return the status of the path.
        """
        status = PathStatus.PREPARING
        # To get an operative status every node must be OPERATIVE status
        n_preparing = 0
        n_finished = 0
        n_operative = 0
        n_error = 0
        for node_id, node in self.nodes.items():
            if node.status == NodeStatus.ERROR:
                n_error = n_error + 1
            if node.status == NodeStatus.FINISHED:
                n_finished = n_finished + 1
            if node.status == NodeStatus.PREPARING:
                n_preparing = n_preparing + 1
            if node.status == NodeStatus.OPERATIVE:
                n_operative = n_operative + 1
        # If error
        if n_error > 0:
            self.status = PathStatus.ERROR
        elif n_preparing > 0:
            self.status = PathStatus.PREPARING
        elif n_operative == self.number_of_nodes:
            self.status = PathStatus.OPERATIVE
        elif n_finished == self.number_of_nodes:
            self.status = PathStatus.FINISHED
        return self.status


class FlowInfo:
    """
    Class that will represent the status and information of a packet that goes from the ingress node to the egress
    node and verify where did the the error happened (if the verification in the egress node is wrong). Maybe it is
    not necessary to implement this with the sequence number.
    """

    def __init__(self, number_of_nodes):
        """

        :param number_of_nodes: Number of node in the path
        """
        self.status = FlowStatus.NOT_FINISHED
        self.secret = None
        self.valid = None
        self.number_of_nodes = number_of_nodes
        self.timestamps = []
        self.status_information = {}  # We need a dictionary instead a list, because the packets can arrived unordered
        # Time that has passed from the packet received in the IngressNode until the packet that has been received in
        # the EgressNode
        self.duration = None

    def update_status(self, log: OPoTLog):
        """
        Function that will calculate the state of the OPoT for an specific sequence number.

        :param log: The information that must contain the sequence number and the calculated CML by the node. Then
        it can include the final state of the OPoT or the master_secret.
        :return:
        """
        # First we need to know if all the packets from the node have arrived, in the case where the number of nodes
        # is not equal that means that there are some packets that need to arrive
        if self.number_of_nodes != len(self.status_information):
            node_id = log.node_id
            # Then we check that the information has not been already stored.
            if node_id not in self.status_information:
                self.status_information[node_id] = log
                if self.secret is None:
                    self.secret = log.secret
                if self.valid is None:
                    self.valid = log.valid
                self.timestamps.append(log.timestamp)
        if self.number_of_nodes == len(self.status_information):
            self.status = FlowStatus.SUCCESSFUL if self.valid else FlowStatus.FAIL
            self.duration = self.calculate_timestamp()

    def calculate_timestamp(self):
        """
        Method that returns the time that has passed since the IngressNode has received the first packet from the
        receiver until the Egress node has receiver the OPoT packet.

        :return
        :param log: The information that must contain the sequence number and the calculated CML by the node. Then
:
        """
        first_node_timestamp = self.first_timestamp()
        last_node_timestamp = self.last_timestamp()
        return last_node_timestamp - first_node_timestamp

    def first_timestamp(self):
        """
        It returns the newest timestamp from the list (it should be the timestamp sent by the IngressNode)

        :return:
        """
        return min(self.timestamps)

    def last_timestamp(self):
        """
        It returns the newest timestamp from the list (it should be the timestamp sent by the EgressNode)

        :return:
        """
        return max(self.timestamps)

    def locate_error(self, nodes):
        prev_cml = 0
        for node_id, node in nodes.items():
            new_cml = calculate_new_cml(prev_cml, public_secret=self.secret,
                                        prime_number=node.pot_profile_list.prime_number,
                                        public_pol=node.pot_profile_list.public_polynomial,
                                        secret_share=node.pot_profile_list.secret_share,
                                        lpc=node.pot_profile_list.lpc)

            if new_cml != self.status_information[str(node_id)].cml:
                # This will indicate in which node we have found the error. This means that the connection between
                # the node i and the the previous node (i-1) has been compromised
                return node.node_id
            else:
                prev_cml = new_cml
