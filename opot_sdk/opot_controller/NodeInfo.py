from opot_sdk.helpers.descriptors.NodeDescriptor import NodeDescriptor
from opot_sdk.helpers.enums import NodeStatus


class NodeInfo(NodeDescriptor):
    """
    Helper class that will provide a visualization of the information about a node and will be used to store it
    TODO Maybe we can add an flow_status to this class, if we want to add a method asking for the flow_status of a node.
    """

    __values_to_not_parse__ = ('node_id', 'path_id', 'node_address', 'upstream_address', 'downstream_address',
                               'upstream_id', 'downstream_id', 'status', 'node_type', 'node_position', 'node_mgmt_ip',
                               "node_path_ip", "node_listening_port")

    def __init__(self, **kwargs):
        """

        :param data: The data must contain the following values {"node_id", "node_type", "address", "protocol",
        "lagrange_data", "next_id", "prev_id", "node_mgmt_ip","node_path_ip"}
        """

        # Set the information to identify the node
        super().__init__(**kwargs)
        # Mandatory values
        self.node_mgmt_ip = kwargs.get('node_mgmt_ip')
        # Just to make this a bit clear when asking for some values.
        self.node_path_ip = self.downstream_ip
        self.node_listening_port = self.downstream_port
        self.node_position = kwargs['node_position']

        # Depending on the type of node
        self.node_type = self.get_node_type()
        self.upstream_id = kwargs.get('upstream_id', None)
        self.downstream_id = kwargs.get('downstream_id', None)

        self.status = NodeStatus.PREPARING

    def get_node_info(self):
        """
        Method that creates the necessary dictionary which has all the information of a node.

        :return: dictionary with the information of the node
        """
        data = self.get_info_as_next_prev()
        data['lagrange_data'] = {
            "prime_number": self.pot_profile_list.prime_number,
            "public_pol": self.pot_profile_list.public_polynomial,
            "lpc": self.pot_profile_list.lpc
        }
        data['masks'] = {
            "upstream_mask": self.pot_profile_list.opot_masks.upstream_mask,
            "downstream_mask": self.pot_profile_list.opot_masks.downstream_mask
        }
        return data

    def get_info_as_next_prev(self):
        """
        Method that creates the necessary dictionary which has the main information if we are asking for the information
        as a next or prev node. This is usually done when we are sending the information of this node to another node.

        :return: dictionary with the information of the prev or next node
        """
        data = {'node_id': self.node_id, 'node_type': self.node_type, 'node_address': self.node_address}
        return data

    def set_upstream_node(self, node):
        self.upstream_ip = node.downstream_ip
        self.upstream_port = node.downstream_port

    def set_downstream_node(self,node):
        self.downstream_ip = node.upstream_ip
        self.downstream_port = node.upstream_port


