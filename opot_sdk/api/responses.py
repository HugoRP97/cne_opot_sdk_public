from opot_sdk.opot_controller.OPoTPath import OPoTPath


def create_default_response(message: str):
    return {
        "msg": message,
        "status": 200
    }


def create_path_response(path: OPoTPath):
    status = path.status
    nodes = []
    # TODO Maybe is better if we add something like __dict__ method instead in the classes instead of doing this here.
    for node_id, node in path.nodes.items():
        nodes.append(
            {'status': node.status,
             'address': {'mgmt_ip': node.node_mgmt_ip, 'path_ip': node.node_path_ip, 'port': node.node_listening_port},
             'node_id': node.node_id,
             'node_type': node.node_type,
             'node_position': node.node_position})
    masks = path.masks

    return {'pot_id': path.path_id, status: 200, 'path_status': status, 'nodes': nodes, 'masks': masks,
            'protocol': path.protocol,
            'creation_time': path.creation_time}
