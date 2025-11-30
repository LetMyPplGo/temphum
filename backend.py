import os
import threading
from datetime import datetime
from time import sleep

from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from waitress import serve

from get_weather import get_today_summary
from lib_bus import get_bus_stops, next_buses
from helpers import read_state, write_state, APMode
from lib_oled import update_display
from lib_wifi import wait_for_internet, start_ap_mode, connect_with_fallback
load_dotenv()
app = Flask(__name__)
app.secret_key = "LdiAPFZomOk5qD1rOBQdM4sich2nTIzjheeiXhEod8wQsMjiwJlyfJ7aULtI"
is_ap_mode = APMode()


# TODO: attach the screen
# TODO: design the bus box for 3d printing
# TODO: create proper chart from temphum data and show it on the page

@app.route("/", methods=["GET"])
def index():
    state = read_state()
    return render_template(
        "dashboard.html",
        wifi_ssid=state["wifi_ssid"],
        wifi_password=state["wifi_password"],
        api_key=f'**********************************{state["api_key"][-3:]}',
        bus_stops=get_bus_stops(),
        stop_id=state["stop_id"],
        pixel_lines=get_lines(),
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

    state = read_state()
    state["stop_id"] = stop_id
    write_state(state)

    flash(f"Bus stop is saved: {stop_id or '—'}")
    return redirect(url_for("index"))

@app.route("/save_api_key", methods=["POST"])
def save_api_key():
    api_key = request.form.get("api_key", "").strip()

    state = read_state()
    state["api_key"] = api_key
    write_state(state)

    flash("API Key is saved.")
    return redirect(url_for("index"))

# ======================================== Helpers

def get_lines():
    weather = get_today_summary()
    now = datetime.now().strftime("%H:%M")
    stop_id = read_state().get('stop_id', '039026550001')
    buses = next_buses(stop_id)
    if None in [weather, buses]:
        return None
    else:
        return [f'{now} {weather}',] + buses


def oled_loop(state: APMode):
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
            update_display(ap_lines)
        else:
            lines = get_lines()
            if lines is not None:
                update_display(lines)
        sleep(10)


if __name__ == "__main__":
    if not wait_for_internet():
        start_ap_mode()
        is_ap_mode.on = True

    oled_thread = threading.Thread(target=oled_loop, args=(is_ap_mode,), daemon=True)
    oled_thread.start()

    AT_DEBUG = bool(int(os.getenv('AT_DEBUG', 0)))
    if AT_DEBUG:
        print('Running in DEBUG mode')
        app.run(debug=True, host="0.0.0.0", port=8000)
    else:
        print('Running in prod mode')
        serve(app, host="0.0.0.0", port=8000)
