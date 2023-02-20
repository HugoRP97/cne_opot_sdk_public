import argparse

from opot_sdk.helpers.socketsSupport import prepare_socket_for_connection, extract_raw_data_from_socket, \
    send_raw_data_to_address
import time
import json


def listen_for_packet(socket, protocol):
    message = extract_raw_data_from_socket(socket, protocol)
    timestamp = int(time.time() * 1e6)
    message_dec = json.loads(message.decode())
    message_dec['timestamps'].append(timestamp)
    # print("[PACKET RECEIVED: {}]".format(message_dec))
    timestamps = message_dec['timestamps']
    print('[+] Packet received')
    print(f'[+] {((timestamps[len(timestamps) - 1] - timestamps[0]) / 1000)} milliseconds have passed since packet '
          f' was sent by the sender.')


parser = argparse.ArgumentParser(description='opot_sdk')
parser.add_argument('path', metavar='path', help="File with the path in json format")
t = parser.parse_args()
with open(t.path) as f:
    path = json.load(f)
protocol = path['protocol']
receiver = path['receiver']
listener_socket = prepare_socket_for_connection((receiver['ip'], receiver['port']), protocol=protocol)
while True:
    listen_for_packet(listener_socket, protocol)
