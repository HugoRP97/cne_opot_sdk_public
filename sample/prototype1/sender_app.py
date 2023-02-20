import sys
import os
import time
import json
sys.path.append(os.getcwd() + "/../")
from opot_sdk.helpers.socketsSupport import send_raw_data_to_address

with open('path.json') as f:
    path = json.load(f)
address = path['nodes'][0]
protocol = path['protocol']
timestamp = int(time.time() * 1e6)
message_to_encrypt = {"timestamps": [timestamp]}
NODE_ADDRESS_CONNECTED_TO_THIS_APP = (address['ip'], path['sender']['port'])

send_raw_data_to_address(json.dumps(message_to_encrypt).encode(), NODE_ADDRESS_CONNECTED_TO_THIS_APP, protocol=protocol)
