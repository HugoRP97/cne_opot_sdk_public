import argparse
import json
import logging
import sys
import os
import threading

sys.path.append(os.getcwd() + "/../")


def launch_opot_controller(path):
    print("You have selected the OPoTController.")
    with open(path, "r") as json_file:
        data = json.load(json_file)
        from opot_sdk.opot_controller.OPoTController import OPoTController
        opot = OPoTController()
        threading.Thread(target=opot.create_path, args=(data,)).start()


def launch_node_controller():
    print("You have selected the NodeController.")
    from opot_sdk.node_controller.NodeController import NodeController
    NodeController()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='opot_sdk')
    option_group = parser.add_mutually_exclusive_group()
    option_group.add_argument("-n", "--node", help="Launch the NodeController", action="store_true")
    opot_option = option_group.add_argument_group()
    opot_option.add_argument("-o", "--opot_controller", help="Launch the OPoTController", action="store_true")
    t = parser.parse_args()
    if t.node:
        launch_node_controller()
    elif t.opot_controller:
        launch_opot_controller('path.json')
