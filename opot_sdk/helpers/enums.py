from enum import IntEnum, Enum


class PathStatus(str, Enum):
    """
    Status of the path
    """
    PREPARING = 'Preparing'
    """When the path is still in the deployment process"""
    OPERATIVE = 'Operative'
    """The OPoT path is operative and packets can be forwarded"""
    FINISHED = 'Finished'
    """The OPoT path has been removed or stopped"""
    ERROR = 'Error'
    """There was an error while deploying,finishing or running the OPoT Path"""


class FlowStatus(str, Enum):
    """
    Status of a flow
    """
    ERROR = 'Error'
    """If there has been an error with the packet."""
    FAIL = 'Fail'
    """OPoT has not been successful. There was an error between the nodes and the verification of the master_secret
    has failed."""
    NOT_FINISHED = 'Not Finished'
    """OPoT has not finished. This means that the packet has not arrived to the last node."""
    SUCCESSFUL = 'Successful'
    """OPoT has been successful. The packet has arrived to the EgressNode and the verification of the master_secret 
    has been successful."""


class Command(str, Enum):
    """
    Possible commands that can be sent to the nodes or to the opot_controller
    """
    UPDATE_FLOW_STATUS = "update_flow_status"
    """When a node send a OPoT packet, it send an update with the CML value and a timestamp. In the case of the last
    node it send the status of the verification and with the first node it also sends the value of the master_secret."""
    UPDATE_NODE_STATUS = "update_node_status"
    """When a node send the information about their status to the controller."""
    CREATE_PATH = "create_path"
    """Command to request the controller to create a OPoT path"""
    DESTROY_PATH = "destroy_path"
    """Command to request the controller to delete a OPoT path"""
    UPDATE_MASKS = "update_masks"
    """When the controller send new masks to the controller"""
    CREATE_NODE = "create_node"
    """Command send to the NodeController to deploy a new Node"""
    DESTROY_NODE = "destroy_node"
    """Command send to the NodeController to remove a running Node"""
    ERROR_NODE = "error_node"
    """Command send to the OPotController when an error has occurred in the Node"""


class NodeStatus(str, Enum):
    """
    Status of a node
    """
    PREPARING = 'Preparing'
    """The node is been created"""
    OPERATIVE = 'Operative'
    """The node is running"""
    FINISHED = 'Finished'
    """The node has finished running"""
    ERROR = 'Error'
    """There was an error in the node"""


class NodeType(str, Enum):
    """
    Possible types of nodes
    """
    INGRESS = "Ingress"
    """First node in the path"""
    MIDDLE = "Middle"
    """Nodes that must exist between two nodes"""
    EGRESS = "Egress"
    """Last node in the path"""


class NodeLoggingLevels(IntEnum):
    """
    Logging levels that may be produced in the Node
    """
    FLOW_INFO = 10
    """When logging information about a OPoT Packet and we want to save it in a file (same as logging.DEBUG)"""
    FLOW_INFO_CONTROLLER = 12
    """When logging information about a OPoT Packet that must be sent to the controller"""
    NODE_STATUS = 21
    """When logging the status of a Node"""
    ERROR_NODE = 41
    """When logging the error of node"""
