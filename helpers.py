import json
import os
import threading

state_file = 'state.json'

def read_state():
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)
        return state
    else:
        return {"wifi_ssid": "", "wifi_password": "", "api_key": "", "stop_id": "039026550001", "ap_ssid": "busbox", "ap_password": "busboxBUSBOX"}

def write_state(state):
    with open(state_file, 'w') as f:
        json.dump(state, f)

class APMode:
    """
    Shared object to pass AP Mode state to the OLED thread
    """
    def __init__(self):
        self.value = False
        self.lock = threading.Lock()

    @property
    def on(self):
        with self.lock:
            v = self.value
        return v

    @on.setter
    def on(self, state: bool):
        with self.lock:
            self.value = state
