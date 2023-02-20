import os
import requests
import shelve
import threading
import time
from abc import abstractmethod
from opot_sdk.helpers.Singleton import Singleton
from opot_sdk.helpers.default_params.ControllerParams import controller_params


class MaskManager(threading.Thread, metaclass=Singleton):
    """
    This class will process all the requests asked by the controller, in order to generate the necessary masks
    """

    MASK_SIZE = 16
    """It must be a divisor of 1024"""

    def __init__(self, time_timer=20):
        """

        :param time_timer: Time in seconds that must pass to reload the stored keys.
        """
        super().__init__()
        self.keys = shelve.open("/tmp/keys")
        # In order to make the operations thread safe we need to lock the thread when modifying the last_update and
        # the keys
        self.lock = threading.Lock()
        # Time that must pass be
        self.timer_time = time_timer
        # Last timestamp where the masks were updated
        self.last_update = None
        # Before running the masks we generate the first set of masks
        self.generate_masks()
        self._running = True
        self.start()

    def run(self):
        while self._running:
            time.sleep(self.timer_time)
            # Make sure that the variable is not being used by another thread.
            self.generate_masks()
            self.last_update = time.time()
        self.keys.close()

    def terminate(self):
        self._running = False

    @abstractmethod
    def generate_masks(self):
        """
        This method will generate the keys which will be stored locally.

        :return:
        """
        pass

    def extract_opot_masks(self, number_of_nodes):
        masks = []
        keys = self.keys['keys']
        for n in range(number_of_nodes - 1):
            # Check that the last has a length higher than MASK_SIZE
            n_keys = len(keys)
            if len(keys[n_keys - 1]) < MaskManager.MASK_SIZE:
                keys.pop()
                # Update the value of n_keys
                n_keys = n_keys - 1
            if n_keys == 0:
                self.generate_masks()
                keys = self.keys['keys']
            # Create the mask
            mask = keys[n_keys - 1][0:MaskManager.MASK_SIZE]
            part1 = int.from_bytes(mask[0:int(MaskManager.MASK_SIZE/2)],byteorder='big')
            part2 = int.from_bytes(mask[int(MaskManager.MASK_SIZE/2):MaskManager.MASK_SIZE],byteorder='big')
            masks.append([part1,part2])
            keys[n_keys - 1] = keys[n_keys - 1][MaskManager.MASK_SIZE::]
        self._update_masks(keys)
        return masks

    def _update_masks(self, new_keys, reason=False):
        """
        This method is used to manage the writing into the shelve to avoid multithreading issues

        :param reason: Reason why the keys are being updated. True means that the keys are
        being updated because the timer has been exceeded or because the length of the mask
        is not long enough. False (Default value), will only look at the timer to check if
        it needs to change the masks or not.
        """
        self.lock.acquire()
        if reason:
            self.last_update = time.time()
            self.keys['keys'] = new_keys
        else:
            # Verify that the current time - last_updated  time is still under timer_time
            if time.time() - self.last_update <= self.timer_time:
                self.keys['keys'] = new_keys
        self.lock.release()


class LocalMaskManager(MaskManager):

    def generate_masks(self):
        # The value 30 is just for testing purposes. From the API we will request 1024 bytes. 32 * 32 = 1024
        keys = [os.urandom(MaskManager.MASK_SIZE * 32)]
        self._update_masks(keys, reason=True)


class ApiMaskManager(MaskManager):

    def __init__(self, api_address, timer_time=20):
        """

        :param api_address: The API address where the qcryptrandom generator is located
        :param timer_time:
        """
        self.keys_endpoint = api_address + "/qryptrandom/stream?keysize=" + str(MaskManager.MASK_SIZE)
        super().__init__(timer_time)

    def generate_masks(self):
        r = requests.get(self.keys_endpoint).json()
        random_keys = r['random']
        precision = r['precision']
        key_format = r['format']
        # Parse the keys
        keys = []
        for key_list in random_keys:
            parsed_key = bytearray()
            for i in key_list:
                # Transform from str to hex
                if key_format == "hexadecimal":
                    parsed_key.extend(bytes().fromhex(i[2::]))
                # Transform from decimal to hex
                if key_format == "decimal":
                    parsed_key.extend(int(i).to_bytes(precision / 8, 'big'))
            keys.append(parsed_key)
        # We need to lock the thread, in order to avoid any kind of multithreading related issues.
        self._update_masks(keys, reason=True)


def get_mask_manager():
    if controller_params.key_generator_api is not None:
        api_link = os.environ['KEY_GENERATOR_API']
        return ApiMaskManager(api_link)
    else:
        return LocalMaskManager()
