import os
import threading

from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv
from waitress import serve

from lib_bus import get_bus_stops
from helpers import read_state, write_state
from lib_wifi import wait_for_internet, start_ap_mode, connect_with_fallback
from write_oled import get_lines
load_dotenv()
app = Flask(__name__)
app.secret_key = "LdiAPFZomOk5qD1rOBQdM4sich2nTIzjheeiXhEod8wQsMjiwJlyfJ7aULtI"

# TODO: switch other scripts to use state.json
# TODO: create proper chart from temphum data and show it on the page
# TODO: attach the screen
# TODO: implement function to show text on the screen and use it when connected to AP (service mode)
# TODO: design the bus box for 3d printing

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

    flash("Wi-Fi настройки сохранены. Подключаемся к WiFi")
    threading.Thread(target=connect_with_fallback, args=(ssid, pwd), daemon=True).start()
    return redirect(url_for("index"))

@app.route("/save_stop", methods=["POST"])
def save_stop():
    stop_id = request.form.get("stop_id", "").strip()

    state = read_state()
    state["stop_id"] = stop_id
    write_state(state)

    flash(f"Остановка сохранена: {stop_id or '—'}")
    return redirect(url_for("index"))

@app.route("/save_api_key", methods=["POST"])
def save_api_key():
    api_key = request.form.get("api_key", "").strip()

    state = read_state()
    state["api_key"] = api_key
    write_state(state)

    flash("API Key сохранён.")
    return redirect(url_for("index"))


if __name__ == "__main__":
    if not wait_for_internet():
        start_ap_mode()

    AT_DEBUG = bool(os.getenv('AT_DEBUG', 0))
    if AT_DEBUG:
        print('Running in DEBUG mode')
        app.run(debug=True, host="0.0.0.0")
    else:
        print('Running in prod mode')
        serve(app, host="0.0.0.0", port=8000)
