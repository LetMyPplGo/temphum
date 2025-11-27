from flask import Flask, render_template, request, redirect, url_for, flash
from dotenv import load_dotenv

from helpers import read_state, write_state
from write_oled import get_lines
load_dotenv()
app = Flask(__name__)
app.secret_key = "LdiAPFZomOk5qD1rOBQdM4sich2nTIzjheeiXhEod8wQsMjiwJlyfJ7aULtI"

# TODO: implement get_bus_stops()
# TODO: implement switching between wifi hotsopt and wifi client
# TODO: implement automatic detection of wifi connection and fallback to hotspot showing text on the OLED
# TODO: switch other scripts to use state.json

@app.route("/", methods=["GET"])
def index():
    state = read_state()
    return render_template(
        "dashboard.html",
        wifi_ssid=state["wifi_ssid"],
        wifi_password=state["wifi_password"],
        api_key=f'**********************************{state["api_key"][-3:]}',
        bus_stops='',#get_bus_stops(),
        selected_stop_id=state["selected_stop_id"],
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

    flash("Wi-Fi настройки сохранены.")
    return redirect(url_for("index"))

@app.route("/save_stop", methods=["POST"])
def save_stop():
    stop_id = request.form.get("stop_id", "").strip()

    state = read_state()
    state["selected_stop_id"] = stop_id
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
    app.run(debug=True, host="0.0.0.0")
