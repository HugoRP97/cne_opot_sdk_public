# The following code will be used to take samples of a PoT link.
import socket
import threading
import time

from opot_sdk.helpers import socketsSupport
from opot_sdk.helpers.logging.NodeLogging import nodeLogging


class SampleGen(threading.Thread):

    def __init__(self, to_addr, protocol, interval):
        super().__init__(daemon=True)
        self.to_addr = to_addr
        self.protocol = protocol
        self.interval = interval
        sock = None
        if protocol == "UDP":
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        else:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket = sock
        # Variable to check if the thread need to be closed
        self.close = False

    def run(self):
        nodeLogging.root_logger.info("SampleGen started")
        while not self.close:
            self.send_sample()
            time.sleep(self.interval)
        self.socket.close()

    def terminate(self):
        self.close = True

    def send_sample(self):
        t = str(time.time())
        socketsSupport.send_raw_data_to_address(self.socket, t.encode(), self.to_addr, self.protocol)
