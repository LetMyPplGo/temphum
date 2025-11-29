import os

import requests
from datetime import datetime, timezone
from dotenv import load_dotenv
import xmltodict

from typing import List, Dict, Any, Optional
from datetime import datetime
from zoneinfo import ZoneInfo

load_dotenv()

LONDON = ZoneInfo("Europe/London")

def _parse_iso(iso_ts: Optional[str]) -> Optional[datetime]:
    if not iso_ts:
        return None
    try:
        # handle both "+00:00" and "Z"
        if iso_ts.endswith("Z"):
            iso_ts = iso_ts[:-1] + "+00:00"
        return datetime.fromisoformat(iso_ts).astimezone(LONDON)
    except Exception:
        return None

def _to_hhmm(dt: Optional[datetime]) -> str:
    return dt.strftime("%H:%M") if dt else ""

def extract_bus_times_one_time(siri: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    Return rows with: line, destination, time (hh:mm).
    Time is chosen by 'monitored': expected if monitored, else aimed.
    """
    try:
        delivery = siri["Siri"]["ServiceDelivery"]["StopMonitoringDelivery"]
    except (KeyError, TypeError):
        return []

    visits = delivery.get("MonitoredStopVisit", [])
    if isinstance(visits, dict):
        visits = [visits]

    now = datetime.now(tz=LONDON)
    rows: List[Dict[str, str]] = []
    for v in visits:
        vj = (v or {}).get("MonitoredVehicleJourney", {}) or {}
        call = vj.get("MonitoredCall", {}) or {}

        line = vj.get("PublishedLineName") or vj.get("LineRef") or ""
        destination = vj.get("DestinationName") or vj.get("DestinationRef") or ""
        monitored = str(vj.get("Monitored", "")).lower() == "true"

        aimed_dt = _parse_iso(call.get("AimedArrivalTime"))
        expected_dt = _parse_iso(call.get("ExpectedArrivalTime"))
        chosen_dt = expected_dt if (monitored and expected_dt) else aimed_dt

        hhmm = _to_hhmm(chosen_dt)
        diff_min = round((chosen_dt - now).total_seconds() / 60) if chosen_dt else None

        rows.append({
            "line": line,
            "destination": destination,
            "time": hhmm,
            'due_at': diff_min,
        })

    return rows[:3]

def get_bus_stops():
    return [
        {'id': '1234567', 'name': 'Station'},
        {'id': '1234567', 'name': 'Station'},
        {'id': '1234567', 'name': 'Station'},
        {'id': '1234567', 'name': 'Station'},
        {'id': '1234567', 'name': 'Station'},
        {'id': '1234567', 'name': 'Station'},
        {'id': '1234567', 'name': 'Station'},
        {'id': '1234567', 'name': 'Station'},
    ]

def next_buses(stop_code: str, as_dict: bool = False):
    """
    Return the next 3 predicted departures for a Reading Buses stop (by Acto-code).
    Requires an API key from reading-opendata.r2p.com.
    """
    api_key = os.environ.get('ROD_API_KEY')
    base_url = "https://reading-opendata.r2p.com"
    url = f"{base_url}/api/v1/siri-sm"
    params = {"api_token": api_key, "location": stop_code}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
    except Exception as err:
        print(f'Failed to get bus info\n{err}')
        records = [{}]
    else:
        records = extract_bus_times_one_time(xmltodict.parse(r.text))

    if as_dict:
        return records
    else:
        # return [f"{item.get('time', '??:??')} {item.get('line', '??')} {item.get('destination', '?')}" for item in records]
        return [f"{item.get('due_at', '??')}m {item.get('line', '??')} {item.get('destination', '?')}" for item in records]



if __name__ == '__main__':
    # 039027180001 - Russel street bus stop code according to ChatGPT
    # 039026550001 - Lima Court bus stop
    # print(next_three_reading_buses('039027180001'))
    print(next_buses('039026550001'))


