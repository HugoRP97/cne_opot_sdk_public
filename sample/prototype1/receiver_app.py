import sys
import os
import time
import json

sys.path.append(os.getcwd() + "/../../")
from opot_sdk.helpers.socketsSupport import prepare_socket_for_connection, extract_raw_data_from_socket

with open('path.json') as f:
    topology = json.load(f)
address = topology['receiver']

APP_PORT = (address['ip'], address['port'])
sock_application = prepare_socket_for_connection(APP_PORT, "OPoT Application", protocol=topology['protocol'])

while True:
    message = extract_raw_data_from_socket(sock_application, protocol=topology['protocol'])
    timestamp = int(time.time() * 1e6)
    message_dec = json.loads(message.decode())
    message_dec['timestamps'].append(timestamp)
    # print("[PACKET RECEIVED: {}]".format(message_dec))
    timestamps = message_dec['timestamps']
    print(f'{((timestamps[len(timestamps) -1] - timestamps[0]) / 1000)} milliseconds have passed since packet '
          f'{message_dec["seq"]} was sent by the sender.')
