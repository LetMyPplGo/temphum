import json
import os
import socket
import threading

state_file = 'state.json'

_DEFAULT_COORDS = "51.5074,-0.1278"
_DEFAULT_STOP_ID = "039026550001"
_DEFAULT_TRAIN_FROM = "RDG"
_DEFAULT_TRAIN_TO = "PAD"

def _settings_tab() -> dict:
    return {
        "id": "settings",
        "name": "Settings",
    }

def _default_tab(tab_id: str = "tab-1", name: str = "Tab 1") -> dict:
    return {
        "id": tab_id,
        "name": name,
        "stop_id": _DEFAULT_STOP_ID,
        "coordinates": _DEFAULT_COORDS,
        "train_from": _DEFAULT_TRAIN_FROM,
        "train_to": _DEFAULT_TRAIN_TO,
        "coordinates_from": _DEFAULT_COORDS,
        "coordinates_to": _DEFAULT_COORDS,
    }

def _normalize_tabs(state: dict) -> dict:
    changed = False
    if "tabs" not in state or not isinstance(state.get("tabs"), list):
        tab = _default_tab()
        tab["stop_id"] = state.get("stop_id", tab["stop_id"])
        tab["coordinates"] = state.get("coordinates", tab["coordinates"])
        tab["train_from"] = state.get("train_from", tab["train_from"])
        tab["train_to"] = state.get("train_to", tab["train_to"])
        tab["coordinates_from"] = state.get("coordinates_from", tab["coordinates_from"])
        tab["coordinates_to"] = state.get("coordinates_to", tab["coordinates_to"])
        state["tabs"] = [_settings_tab(), tab]
        state["active_tab_id"] = tab["id"]
        changed = True

    if not state["tabs"]:
        state["tabs"] = [_settings_tab(), _default_tab()]
        state["active_tab_id"] = state["tabs"][1]["id"]
        changed = True

    seen_ids = set()
    for i, tab in enumerate(state["tabs"]):
        if not isinstance(tab, dict):
            state["tabs"][i] = _default_tab(tab_id=f"tab-{i+1}")
            tab = state["tabs"][i]
            changed = True
        if not tab.get("id") or tab["id"] in seen_ids:
            tab["id"] = f"tab-{i+1}"
            changed = True
        seen_ids.add(tab["id"])
        if not tab.get("name"):
            tab["name"] = f"Tab {i+1}"
            changed = True
        if tab.get("id") == "settings":
            if tab.get("name") != "Settings":
                tab["name"] = "Settings"
                changed = True
        if tab.get("id") != "settings" and "stop_id" not in tab:
            tab["stop_id"] = _DEFAULT_STOP_ID
            changed = True
        if tab.get("id") != "settings" and "coordinates" not in tab:
            tab["coordinates"] = _DEFAULT_COORDS
            changed = True
        if tab.get("id") != "settings" and "train_from" not in tab:
            tab["train_from"] = _DEFAULT_TRAIN_FROM
            changed = True
        if tab.get("id") != "settings" and "train_to" not in tab:
            tab["train_to"] = _DEFAULT_TRAIN_TO
            changed = True
        if tab.get("id") != "settings" and "coordinates_from" not in tab:
            tab["coordinates_from"] = _DEFAULT_COORDS
            changed = True
        if tab.get("id") != "settings" and "coordinates_to" not in tab:
            tab["coordinates_to"] = _DEFAULT_COORDS
            changed = True

    if "settings" not in seen_ids:
        state["tabs"].insert(0, _settings_tab())
        seen_ids.add("settings")
        changed = True
    else:
        for i, tab in enumerate(state["tabs"]):
            if tab.get("id") == "settings" and i != 0:
                state["tabs"].insert(0, state["tabs"].pop(i))
                changed = True
                break

    if len(state["tabs"]) == 1 and state["tabs"][0].get("id") == "settings":
        state["tabs"].append(_default_tab())
        changed = True

    active_id = state.get("active_tab_id")
    if active_id not in seen_ids:
        state["active_tab_id"] = state["tabs"][1]["id"] if len(state["tabs"]) > 1 else state["tabs"][0]["id"]
        changed = True

    # Remove legacy per-tab keys from the root after migration
    for legacy_key in ("stop_id", "coordinates", "train_from", "train_to", "coordinates_from", "coordinates_to", "tab_name"):
        if legacy_key in state:
            state.pop(legacy_key, None)
            changed = True

    return state

def get_active_tab(state: dict) -> dict:
    tab_id = state.get("active_tab_id")
    for tab in state.get("tabs", []):
        if tab.get("id") == tab_id:
            return tab
    return state.get("tabs", [_settings_tab()])[0]

def read_state():
    if os.path.exists(state_file):
        with open(state_file, 'r') as f:
            state = json.load(f)
        return _normalize_tabs(state)
    else:
        return _normalize_tabs({
            "wifi_ssid": "",
            "wifi_password": "",
            "api_key": "",
            "ap_ssid": "busbox",
            "ap_password": "busboxBUSBOX",
        })

def write_state(state):
    with open(state_file, 'w') as f:
        state = _normalize_tabs(state)
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
