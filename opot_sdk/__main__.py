import argparse
import json
import sys
import os

sys.path.append(os.getcwd() + "/../")

def launch_opot_controller(topology = None):
    print("Launching the OPoT Controller")
    from opot_sdk.opot_controller.OPoTController import OPoTController
    opot_controller = OPoTController()
    if topology is not None:
        with open(topology) as f:
            opot_controller.create_path(json.load(f))


def launch_node_controller():
    print("Launching the OPoT Node")
    if os.environ.get("INSTALL_YANG", None) is not None:
        os.system("bash /config/entrypoint.sh")
    from opot_sdk.node_controller.NodeController import NodeController

    NodeController()

def launch_api():
    print("Launching the OPoT API")
    from opot_sdk.api.app import instantiate_api
    instantiate_api()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='opot_sdk')
    option_group = parser.add_mutually_exclusive_group()
    option_group.add_argument("-n", "--node", help="Launch the NodeController", action="store_true")
    option_group.add_argument("-c", "--controller", help="Launch the OPoTController", action="store_true")
    option_group.add_argument("-a", "--api", help="Launch the API", action="store_true")
    parser.add_argument("-t", "--topology", help="Pass a topology to the Controller", default="None")
    t = parser.parse_args()
    if t.node:
        launch_node_controller()
    elif t.controller:
        launch_opot_controller(t.topology)
    elif t.api:
        launch_api()

