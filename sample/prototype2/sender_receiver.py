import sys
import os
import time
import json
import requests
import signal
import threading
import argparse
from opot_sdk.helpers.socketsSupport import prepare_socket_for_connection, extract_raw_data_from_socket, \
    send_raw_data_to_address

OPOT_CONTROLLER_IP = os.environ['OPOT_CONTROLLER_IP']
NETWORK_IP = os.environ['NETWORK_IP']
endpoint = f'http://{OPOT_CONTROLLER_IP}:8080/api/v2/'
PATH_CREATE = 'pot/controller/path'
PATH_DESTROY = 'pot/controller/path/{uuid}'

parser = argparse.ArgumentParser(description='opot_sdk')
parser.add_argument('path', metavar='path', help="File with the path in json format")
t = parser.parse_args()


def listen_for_packet(socket, protocol):
    message = extract_raw_data_from_socket(socket, protocol)
    timestamp = int(time.time() * 1e6)
    message_dec = json.loads(message.decode())
    message_dec['timestamps'].append(timestamp)
    # print("[PACKET RECEIVED: {}]".format(message_dec))
    timestamps = message_dec['timestamps']
    print('[+] Packet received')
    print(f'[+] {((timestamps[len(timestamps) - 1] - timestamps[0]) / 1000)} milliseconds have passed since packet '
          f'{message_dec["seq"]} was sent by the sender.')


def send_packet(ip, port, protocol):
    timestamp = int(time.time() * 1e6)
    message_to_encrypt = {"timestamps": [timestamp]}
    send_raw_data_to_address(json.dumps(message_to_encrypt).encode(), (ip, port), protocol=protocol)

def destroy_path(uuid):
    r = requests.delete(endpoint + PATH_DESTROY.format(uuid=uuid))
    if r.status_code == 200:
        print('[+] The path has been removed')
    else:
        json_r = r.json()
        print(json_r['detail'])


print(f'[+] Parsing the path1.json{t.path}')
with open(t.path) as f:
    path = json.load(f)
protocol = path['protocol']
receiver = path['receiver']
sender = path['sender']
# Define our IP
sender['ip'] = NETWORK_IP
receiver['ip'] = NETWORK_IP
nodes = path['nodes']
ingress_node = nodes[0]
egress_node = nodes[len(nodes) - 1]
print("[+] Ask the controller to crate a OPoT path")
r = requests.post(endpoint + PATH_CREATE, json=path)
json_r = r.json()


# If we press ctrl + c
def signal_handler(sig, frame):
    print('[+] Exiting')
    destroy_path(opot_id)
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
if r.status_code == 200:
    print("[+] Path Correctly deployed")
    opot_id = json_r['opot_id']
    print(f'[+] ID of the path {opot_id}')
    try:
        c = ""
        listener_socket = prepare_socket_for_connection((receiver['ip'], receiver['port']), protocol=protocol)
        print("[+] Press ctrl+c if you want to stop sending messages.")
        while True:
            print("[+] Sending packet")
            # First we run the socket listener in another thread.
            t = threading.Thread(target=listen_for_packet, args=(listener_socket, protocol), daemon=True)
            t.start()
            # Send packet
            send_packet(ingress_node['ip'], sender['port'], protocol=protocol)
            print("[+] Waiting for incoming")
            time.sleep(0.1)

    except Exception as e:
        print(e)
        pass
    print('[+] Deleting path')
    destroy_path(opot_id)

else:
    print("[-] An error has been produced when asking the controller to create a OPoT path")
    print(f'[-] Status Code: {r.status_code}')
    print(f'[-] Message: \n {json_r["detail"]}')
