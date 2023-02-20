import hashlib
import re
import xml.etree.ElementTree as ET

# TODO implement this with a method
from opot_sdk.helpers.descriptors.PotProfileListDescriptor import PotProfileListDescriptor
from opot_sdk.helpers.enums import NodeType


class NodeDescriptor:
    __values_to_not_parse__ = ('node_id', 'path_id', 'node_address', 'upstream_address', 'downstream_address')

    def __init__(self, **kwargs):
        """
        :param kwargs:
        """
        # Mandatory values that must be passed
        # Identifier of the path
        self.pot_profile_name = kwargs['pot_profile_name']
        # Path identifier, it is equal to pot_profile_name
        self.path_id = self.pot_profile_name
        # Protocol used (TCP or UDP)
        self.protocol = kwargs['protocol']
        # Information containing the data of the SSS values and the OPoT masks
        self.pot_profile_list = PotProfileListDescriptor(**kwargs['pot_profile_list'][0])
        # Optional values, that may be setup later.
        # IP and Port of the next node or the receiver
        self.upstream_ip = kwargs.get('upstream_ip', None)
        self.upstream_port = kwargs.get('upstream_port', None)
        self.upstream_address = (self.upstream_ip, self.upstream_port)

        # IP and Port of
        self.downstream_ip = kwargs.get('downstream_ip', None)
        self.downstream_port = kwargs.get('downstream_port', None)
        self.downstream_address = (self.downstream_ip, self.downstream_port)

        # Identifier of the node which is md5(node_ip,node_port)
        self.node_id = NodeDescriptor.generate_id(self.downstream_ip, self.downstream_port)

        # Tuple containing the node address
        self.node_address = (self.downstream_ip, self.downstream_port)

    def create_node_config(self):
        """
        Function that parser the values of the Node to a RPC format which will be sent
        through the ncclient.
        :return:
        """
        config = ET.Element('config')
        config.set('xmlns', 'urn:ietf:params:xml:ns:netconf:base:1.0')
        pot_profiles = ET.SubElement(config, 'pot-profiles')
        pot_profiles.set('xmlns', 'urn:ietf:params:xml:ns:yang:ietf-pot-profile')
        pot_profile_set = ET.SubElement(pot_profiles, 'pot-profile-set')
        for k, v in vars(self).items():
            # This values are not in the model
            if k in self.__values_to_not_parse__: continue

            if k == "pot_profile_list":
                _add_to_parent(pot_profile_set, k, vars(self.pot_profile_list))
            else:
                _add_to_parent(pot_profile_set, k, v)
        xml_string = ET.tostring(config, encoding='utf8', method='xml').decode()
        return re.sub(r'<\?xml.*?\?>', '', xml_string).strip().encode()

    def get_node_type(self):
        """
        Function which returns the type of node of the class

        :return: It can return NodeType.INGRESS, NodeType.MIDDLE, NodeType.EGRESS
        """
        if self.pot_profile_list.status:
            return NodeType.INGRESS
        elif self.pot_profile_list.validator:
            return NodeType.EGRESS
        else:
            return NodeType.MIDDLE

    def remove_node_config(self):
        config = ET.Element('config')
        config.set('xmlns', 'urn:ietf:params:xml:ns:netconf:base:1.0')
        config.set('xmlns:nc', 'urn:ietf:params:xml:ns:netconf:base:1.0')
        pot_profiles = ET.SubElement(config, 'pot-profiles')
        pot_profiles.set('xmlns', 'urn:ietf:params:xml:ns:yang:ietf-pot-profile')
        pot_profile_set = ET.SubElement(pot_profiles, 'pot-profile-set')
        pot_profile_set.set('nc:operation', 'delete')
        ET.SubElement(pot_profile_set, 'pot-profile-name').text = self.pot_profile_name
        xml_string = ET.tostring(config, encoding='utf8', method='xml').decode()
        return re.sub(r'<\?xml.*?\?>', '', xml_string).strip().encode()

    @staticmethod
    def generate_id(ip, port):
        """
        Function that crea

        :param ip: Ip assigned to the node
        :param port: Port where the node is listening for incoming packets
        :return: MD5 String of (ip + port)
        """
        return hashlib.md5((ip + str(port)).encode()).hexdigest()


def _add_to_parent(parent, key, value):
    """
    This method is only used inside this python script for the moment. Used to parse the XML Elements of the class NodeDescriptor
    :param parent:
    :param key:
    :param value:
    :return:
    """
    if value is not None:

        if type(value) is dict:
            element = ET.SubElement(parent, key.replace('_', '-'))
            for k, v in value.items():
                _add_to_parent(element, k, v)
        elif type(value) is list:
            for i in value:
                element = ET.SubElement(parent, key.replace('_', '-'))
                element.text = str(i)
        else:
            element = ET.SubElement(parent, key.replace('_', '-'))
            if type(value) is bool:
                element.text = str(value).lower()
            else:
                element.text = str(value)
