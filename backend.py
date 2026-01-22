import os
import threading
from datetime import datetime
from time import time as now_ts
from time import sleep

from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from dotenv import load_dotenv
from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from waitress import serve

from get_weather import get_today_summary
from lib_bus import get_bus_stops, next_buses, get_bus_coordinates
from helpers import read_state, write_state, APMode, get_active_tab
from lib_oled import get_display
from lib_train import get_trains, get_train_stops, get_train_coordinates
from lib_voice import Voice
from lib_wifi import wait_for_internet, start_ap_mode, connect_with_fallback
load_dotenv(override=True)
app = Flask(__name__)
app.secret_key = "LdiAPFZomOk5qD1rOBQdM4sich2nTIzjheeiXhEod8wQsMjiwJlyfJ7aULtI"
is_ap_mode = APMode()
AT_DEBUG = bool(int(os.getenv('AT_DEBUG', 0)))
voice = None
STOPS = None

# TODO:
#  Drop bus stations into file and load from there instead of waiting for API on every boot
#  Add station_from and station_to into web ui
#  Fit train info to the display. Now it breaks on "p"
#  Write details the Loading process to display
#  Complete the voice output
#   Think what should be the trigger (trigger from the google speaker? Add Smart Home?)
#   Add selection of casting devices to the web page
#   Add selecting Bluetooth devices as well as chromecast
#  Reorganize the screen
#    Top line: time and bus stop
#    Three lines of text (123m 26a) - some space is left to the right
#    In the right space that's left put the weather info with borders
# TODO: create proper chart from temphum data and show it on the page

@app.route("/", methods=["GET"])
def index():
    state = read_state()
    active_tab = get_active_tab(state)
    return render_template(
        "dashboard.html",
        wifi_ssid=state["wifi_ssid"],
        wifi_password=state["wifi_password"],
        api_key=f'**********************************{state["api_key"][-3:]}',
        bus_stops=STOPS,
        tabs=state.get("tabs", []),
        active_tab_id=state.get("active_tab_id"),
        tab=active_tab,
        stop_id=active_tab.get("stop_id"),
        pixel_lines=get_lines(),
        coordinates=active_tab.get('coordinates', '1,1'),
        train_from=active_tab.get('train_from', '1,1'),
        train_to=active_tab.get('train_to', '1,1'),
        coordinates_from=active_tab.get('coordinates_from', '1,1'),
        coordinates_to=active_tab.get('coordinates_to', '1,1'),
        google_api_key=state.get('google_api_key', ''),
        train_stops=get_train_stops()
    )

@app.route("/save_wifi", methods=["POST"])
def save_wifi():
    ssid = request.form.get("ssid", "").strip()
    pwd  = request.form.get("password", "").strip()

    state = read_state()
    state["wifi_ssid"] = ssid
    state["wifi_password"] = pwd
    write_state(state)

    flash("Wi-Fi settings are saved. Connecting to WiFi...")
    threading.Thread(target=connect_with_fallback, args=(ssid, pwd, is_ap_mode), daemon=True).start()
    return redirect(url_for("index"))

@app.route("/save_stop", methods=["POST"])
def save_stop():
    stop_id = request.form.get("stop_id", "").strip()
    tab_id = request.form.get("tab_id", "").strip()

    state = read_state()
    for tab in state.get("tabs", []):
        if tab.get("id") == tab_id:
            tab["stop_id"] = stop_id
            tab["coordinates"] = get_bus_coordinates(stop_id)
            break
    write_state(state)

    flash(f"Bus stop is saved: {stop_id or '—'}")
    return redirect(url_for("index"))

@app.route("/save_train_stop", methods=["POST"])
def save_train_stop():
    train_from = request.form.get("train_from", "").strip()
    train_to = request.form.get("train_to", "").strip()
    tab_id = request.form.get("tab_id", "").strip()

    state = read_state()
    for tab in state.get("tabs", []):
        if tab.get("id") == tab_id:
            tab["train_from"] = train_from
            tab["train_to"] = train_to
            tab["coordinates_from"] = get_train_coordinates(train_from)
            tab["coordinates_to"] = get_train_coordinates(train_to)
            break
    write_state(state)

    flash(f"Train stops are saved: {train_from} - {train_to}")
    return redirect(url_for("index"))

@app.route("/save_api_key", methods=["POST"])
def save_api_key():
    api_key = request.form.get("api_key", "").strip()

    state = read_state()
    state["api_key"] = api_key
    write_state(state)

    flash("API Key is saved.")
    return redirect(url_for("index"))

@app.route("/save_tab_name", methods=["POST"])
def save_tab_name():
    tab_name = request.form.get("tab_name", "").strip()
    tab_id = request.form.get("tab_id", "").strip()

    state = read_state()
    for tab in state.get("tabs", []):
        if tab.get("id") == tab_id:
            tab["name"] = tab_name or tab.get("name", "Tab")
            break
    write_state(state)
    flash("Tab name is saved.")
    return redirect(url_for("index"))

@app.route("/select_tab", methods=["POST"])
def select_tab():
    tab_id = request.form.get("tab_id", "").strip()
    state = read_state()
    if any(t.get("id") == tab_id for t in state.get("tabs", [])):
        state["active_tab_id"] = tab_id
        write_state(state)
    return redirect(url_for("index"))

@app.route("/add_tab", methods=["POST"])
def add_tab():
    tab_name = request.form.get("tab_name", "").strip() or "New tab"
    state = read_state()
    active = get_active_tab(state)
    if active.get("id") == "settings":
        active = {
            "stop_id": "039026550001",
            "coordinates": "51.5074,-0.1278",
            "train_from": "RDG",
            "train_to": "PAD",
            "coordinates_from": "51.5074,-0.1278",
            "coordinates_to": "51.5074,-0.1278",
        }
    new_tab = {
        "id": f"tab-{int(now_ts() * 1000)}",
        "name": tab_name,
        "stop_id": active.get("stop_id"),
        "coordinates": active.get("coordinates"),
        "train_from": active.get("train_from"),
        "train_to": active.get("train_to"),
        "coordinates_from": active.get("coordinates_from"),
        "coordinates_to": active.get("coordinates_to"),
    }
    state.setdefault("tabs", []).append(new_tab)
    state["active_tab_id"] = new_tab["id"]
    write_state(state)
    flash("Tab is added.")
    return redirect(url_for("index"))

@app.route("/remove_tab", methods=["POST"])
def remove_tab():
    tab_id = request.form.get("tab_id", "").strip()
    state = read_state()
    tabs = state.get("tabs", [])
    if tab_id == "settings":
        flash("Settings tab cannot be removed.")
        return redirect(url_for("index"))
    if len(tabs) <= 2:
        flash("At least two tabs must remain.")
        return redirect(url_for("index"))
    state["tabs"] = [t for t in tabs if t.get("id") != tab_id]
    if state.get("active_tab_id") == tab_id and state["tabs"]:
        state["active_tab_id"] = state["tabs"][0]["id"]
    write_state(state)
    flash("Tab is removed.")
    return redirect(url_for("index"))

@app.route("/tts.mp3")
def serve_tts():
    return send_file('tts.mp3', mimetype="audio/mpeg")

@app.route("/say")
def say():
    state = read_state()
    active_tab = get_active_tab(state)
    stop_id = active_tab.get('stop_id', '039026550001')
    buses = next_buses(stop_id)
    if len(buses) > 0:
        bus = buses[0].split(' ', maxsplit=2)
        voice.say(f'Следующий автобус через {bus[0][:-1]} минут. Это автобус номер {bus[1]} до {bus[2]}')
    else:
        voice.say('Автобусов нет, иди пешком')
    return redirect(url_for("index"))


# ======================================== Helpers

def get_lines():
    weather = get_today_summary()
    now = datetime.now().strftime("%H:%M")
    state = read_state()
    active_tab = get_active_tab(state)
    stop_id = active_tab.get('stop_id', '039026550001')
    buses = next_buses(stop_id)
    # buses = get_trains()
    if None in [weather, buses]:
        return None
    else:
        tab_name = active_tab.get("name", "Tab")
        header = f'{now} {tab_name} {weather}'
        return [header] + buses


def oled_loop(state: APMode, display):
    """
    The function in a loop updates the OLED
    If AP mode - show AP details (ssid/password/hostname)
    If in WiFi mode - show weather and bus details
    """
    settings = read_state()
    ssid = settings.get('ap_ssid', 'busbox')
    password = settings.get('ap_password', 'busboxBUSBOX')

    ap_lines = [
        '-= Service mode =-',
        f'ssid: {ssid}',
        f'pwd: {password}'
        'http://pi2w:8000'
    ]
    while True:
        if state.on:
            display.update(ap_lines)
        else:
            lines = get_lines()
            if lines is not None:
                display.update(lines)
        sleep(10)


if __name__ == "__main__":
    # print("Starting service instance, PID =", os.getpid(), flush=True)
    # display = get_display("IIC")
    # display.log('Loading...')
    #
    # display.log('...voice skip')
    # # voice = Voice()
    #
    # display.log('...network')
    # if not wait_for_internet():
    #     start_ap_mode()
    #     is_ap_mode.on = True
    #
    # display.log('...bus stops')
    STOPS = get_bus_stops()
    #
    # display.log('...screen')
    # oled_thread = threading.Thread(target=oled_loop, args=(is_ap_mode, display), daemon=True)
    # oled_thread.start()

    if AT_DEBUG:
        print('Running in DEBUG mode')
        app.run(debug=True, host="0.0.0.0", port=8000)
    else:
        print('Running in prod mode')
        serve(app, host="0.0.0.0", port=8000)
