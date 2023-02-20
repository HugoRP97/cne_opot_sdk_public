import requests
import os
import sys
import socket
import argparse
import time
import json
from opot_sdk.helpers.socketsSupport import prepare_socket_for_connection, extract_raw_data_from_socket, \
    send_raw_data_to_address

api_address = "http://192.168.0.100:8080/api/v2/"


def send_packet(address, protocol):
    """
    Send message to the IngressNode
    """
    timestamp = int(time.time() * 1e6)
    message_to_encrypt = {"timestamps": [timestamp]}
    send_raw_data_to_address(json.dumps(message_to_encrypt).encode(), address, protocol=protocol)


def request_opot_information(opot_id):
    """
    Request the controller for the information of the deployed path.
    """
    r = requests.get(api_address + f'pot/controller/path/{opot_id}')
    if r.status_code == 200:
        print("[+] The path is already deployed.")
        return r.json()
    else:
        exit(r.json())

def remove_pad(opot_id):
    """
    Removes the path.
    """
    r = requests.get(api_address + f'pot/controller/path/{opot_id}')
    if r.status_code == 200:
        print("[+] The path has been destroyed.")
        return r.json()
    else:
        exit(r.json())
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='opot_sdk')
    parser.add_argument('opot_id', metavar='opot_id', help="Identificator of the path that is going to be deployed")
    t = parser.parse_args()
    # Request for the information
    opot_info = request_opot_information(t.opot_id)

    ingress_address = (opot_info['nodes'][0]['address']['ip'], opot_info['nodes'][0]['address']['port'])
    protocol = opot_info['protocol']

    while True:
        r_i = input("[?] Do you want to send a packet? [y/N] \n").strip().lower()
        # Exist the loop in this case
        if r_i == "n": break
        send_packet(address=ingress_address,protocol=protocol)
        print("[+] Packet sent")

    r_i = input("[?] Do you want to remove the path? [y/N] \n").strip().lower()

    if r_i == "y":
        remove_pad(t.opot_id)





