import json
import os

state_file = 'state.json'

def read_state():
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)
        return state
    else:
        return {"wifi_ssid": "", "wifi_password": "", "api_key": "", "selected_stop_id": "039026550001"}

def write_state(state):
    with open(state_file, 'w') as f:
        json.dump(state, f)