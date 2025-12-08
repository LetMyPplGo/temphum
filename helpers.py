import json
import os
import socket
import threading

state_file = 'state.json'

def read_state():
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)
        return state
    else:
        return {
            "wifi_ssid": "",
            "wifi_password": "",
            "api_key": "",
            "stop_id": "039026550001",
            "ap_ssid": "busbox",
            "ap_password": "busboxBUSBOX",
            "coordinates": "51.5074,-0.1278",
            "train_from": "RDG",
            "train_to": "PAD",
            "train_coordinates": "51.5074,-0.1278",
        }

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

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip
