#!/usr/bin/env python3
"""
Ultra-short weather summary for today (Reading, UK by default) using Open-Meteo.

Usage:
    from reading_weather import get_today_summary

    print(get_today_summary())                      # default: Reading, GB
    print(get_today_summary("London", "GB"))        # other place
"""

import requests
from datetime import date
from typing import Dict, List, Optional


# ---------- Public API ----------

def get_today_summary(place: str = "Reading", country_code: str = "GB") -> str:
    """
    Returns a single compact string with emojis instead of words like 'wind', 'rain', etc.
    Example:
        "🌦️ Reading 4–9°C 💨6↗11m/s 🌧️2.3mm ☔78%"
    """
    loc = _geocode(place, country_code)

    base_vars = [
        "weathercode",
        "temperature_2m",
        "wind_speed_10m",
        "wind_gusts_10m",
        "precipitation",   # total mm
        "rain",            # rain-only, if available
        "snowfall",        # cm
        "cloudcover",      # %
    ]
    optional_vars = [
        "precipitation_probability",
    ]

    hourly = _fetch_today_hourly_with_fallback(
        lat=loc["lat"],
        lon=loc["lon"],
        primary_vars=base_vars,
        optional_vars=optional_vars,
    )

    return _build_compact_line(place=loc["name"], hourly=hourly)


# ---------- Fetch helpers ----------

def _geocode(place: str, country_code: str = "GB"):
    r = requests.get(
        "https://geocoding-api.open-meteo.com/v1/search",
        params={
            "name": place,
            "count": 1,
            "language": "en",
            "format": "json",
            "country": country_code,
        },
        timeout=15,
    )
    r.raise_for_status()
    results = r.json().get("results") or []
    if not results:
        raise RuntimeError(f"Place not found: {place} ({country_code})")
    hit = results[0]
    return {"lat": hit["latitude"], "lon": hit["longitude"], "name": hit["name"]}


def _fetch_today_hourly_with_fallback(
    lat: float,
    lon: float,
    primary_vars: List[str],
    optional_vars: List[str],
) -> Dict[str, List[Optional[float]]]:
    """
    Try requesting primary+optional vars; on 400, retry without optionals; if still 400, trim to a minimal core.
    """
    today = date.today().isoformat()

    def request(vars_list: List[str]) -> Dict[str, List[Optional[float]]]:
        params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": "UTC",
            "start_date": today,
            "end_date": today,
            "hourly": ",".join(vars_list),
        }
        r = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=20)
        r.raise_for_status()
        return r.json().get("hourly", {}) or {}

    # Attempt 1: primary + optional
    try:
        return request(primary_vars + optional_vars)
    except requests.HTTPError as e:
        if e.response is None or e.response.status_code != 400:
            raise

    # Attempt 2: primary only
    try:
        return request(primary_vars)
    except requests.HTTPError as e:
        if e.response is None or e.response.status_code != 400:
            raise

    # Attempt 3: minimal core
    minimal = ["weathercode", "temperature_2m", "wind_speed_10m", "wind_gusts_10m", "precipitation", "cloudcover"]
    return request(minimal)


# ---------- Compact line builder ----------

def _build_compact_line(place: str, hourly: Dict[str, List[Optional[float]]]) -> str:
    """
    Build shortest possible human-readable line using emojis instead of words:
    - condition icon
    - place name
    - temperature range
    - wind + gusts
    - rain / snow
    - precip probability
    """
    temps = hourly.get("temperature_2m") or []
    t_min = _min_nan(temps)
    t_max = _max_nan(temps)

    winds = hourly.get("wind_speed_10m") or []
    gusts = hourly.get("wind_gusts_10m") or []
    w_max = _max_nan(winds)
    g_max = _max_nan(gusts)

    rain_mm  = hourly.get("rain") or []
    precip   = hourly.get("precipitation") or []
    rains = rain_mm if any(v not in (None, 0) for v in rain_mm) else precip
    r_total = round(sum(x or 0 for x in rains), 1) if rains else 0.0

    snow = hourly.get("snowfall") or []
    s_total = round(sum(x or 0 for x in snow), 1) if snow else 0.0

    probs = hourly.get("precipitation_probability") or []
    p_max = _max_nan(probs)

    parts = []

    # Main condition + place
    # cond_icon = _condition_icon(hourly)
    # if cond_icon:
    #     parts.append(cond_icon)
    # parts.append(place)

    # Temperature range
    if t_min is not None and t_max is not None:
        parts.append(f"{t_min:.0f}/{t_max:.0f}°C")
    elif t_max is not None:
        parts.append(f"↗{t_max:.0f}°C")

    # # Snow
    # if s_total > 0:
    #     parts.append(f"S{s_total:.1f}cm")
    #
    # # Rain
    # if r_total > 0:
    #     parts.append(f"R{r_total:.1f}mm")

    # Precip probability
    if p_max is not None and p_max > 0:
        parts.append(f"{p_max:.0f}%")

    # Wind + gusts
    if w_max is not None and w_max > 0:
        if g_max is not None and g_max > w_max:
            parts.append(f"W{w_max:.0f}↗{g_max:.0f}m/s")
        else:
            parts.append(f"W{w_max:.0f}m/s")

    return " ".join(parts)


# ---------- Condition icon from WMO ----------

def _condition_icon(hourly: Dict[str, List[Optional[float]]]) -> str:
    wmo_list = hourly.get("weathercode") or []
    clouds = hourly.get("cloudcover") or []

    if not wmo_list:
        # fallback: derive from clouds and precip
        rain_mm  = hourly.get("rain") or []
        precip   = hourly.get("precipitation") or []
        rains = rain_mm if any(v not in (None, 0) for v in rain_mm) else precip
        total_rain = sum(x or 0 for x in rains) if rains else 0.0
        mean_clouds = _mean([c for c in clouds if c is not None])

        if total_rain > 0:
            return "🌧️"
        if mean_clouds is None or mean_clouds < 25:
            return "☀️"
        if mean_clouds < 60:
            return "⛅"
        return "☁️"

    def sev(code):
        if code is None: return -1
        if code in (95, 96, 99): return 6
        if code in (71, 72, 73, 75, 77, 85, 86): return 5
        if code in (61, 63, 65, 80, 81, 82, 66, 67, 56, 57, 51, 53, 55): return 4
        if code in (45, 48): return 3
        if code in (3,): return 2
        if code in (2,): return 1
        if code in (1, 0): return 0
        return 0

    code = max(wmo_list, key=sev)

    if code in (95, 96, 99): return "⛈️"
    if code in (71, 72, 73, 75, 77, 85, 86): return "🌨️"
    if code in (66, 67): return "🧊"
    if code in (61, 63, 65, 80, 81, 82, 56, 57, 51, 53, 55): return "🌧️"
    if code in (45, 48): return "🌫️"
    if code in (3,): return "☁️"
    if code in (2,): return "⛅"
    if code in (1, 0): return "☀️"
    return "❓"


# ---------- Utilities ----------

def _min_nan(seq):
    vals = [x for x in seq if x is not None]
    return min(vals) if vals else None

def _max_nan(seq):
    vals = [x for x in seq if x is not None]
    return max(vals) if vals else None

def _mean(seq):
    return (sum(seq) / len(seq)) if seq else None


# ---------- CLI demo ----------

if __name__ == "__main__":
    print(get_today_summary())
