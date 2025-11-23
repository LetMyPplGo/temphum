import os

import requests
from datetime import datetime, timezone
from dotenv import load_dotenv

load_dotenv()

def next_three_reading_buses(stop_code: str):
    """
    Return the next 3 predicted departures for a Reading Buses stop (by Acto-code).
    Requires an API key from reading-opendata.r2p.com.
    """
    # NOTE: The exact path/param names are shown in the portal after login.
    # Commonly it's the "Stop Predictions" API; adjust `url` and `params` if your portal shows different names.
    api_key = os.environ.get('ROD_API_KEY')
    base_url = "https://reading-opendata.r2p.com"
    url = f"{base_url}/api/StopPredictions"          # sometimes shown as /api/stop-predictions
    params = {"ActoCode": stop_code, "format": "json"}
    headers = {"Accept": "application/json", "X-Api-Key": api_key}

    r = requests.get(url, params=params, headers=headers, timeout=10)
    r.raise_for_status()
    records = r.json()  # array of records

    def parse_iso(dt_str):
        if not dt_str:
            return None
        # Accept both 'Z' and '+00:00' endings
        if dt_str.endswith("Z"):
            dt_str = dt_str.replace("Z", "+00:00")
        return datetime.fromisoformat(dt_str)

    # Choose the first available time (ExpectedDeparture, then ScheduledDeparture)
    for rec in records:
        rec["_when"] = parse_iso(rec.get("ExpectedDeparture")) or parse_iso(rec.get("ScheduledDeparture"))

    upcoming = sorted((r for r in records if r.get("_when")), key=lambda r: r["_when"])[:3]

    now = datetime.now(timezone.utc)
    result = []
    for rec in upcoming:
        minutes = int((rec["_when"] - now).total_seconds() // 60)
        due_in = f"{minutes} min" if minutes >= 0 else "due",
        result.append(f'{due_in} {rec.get("ServiceNumber")} to {rec.get("DestinationName")}')
        # result.append({
        #     "service": rec.get("ServiceNumber"),
        #     "destination": rec.get("DestinationName"),
        #     "due_in": f"{mins} min" if mins >= 0 else "due",
        #     "expected_time_utc": rec.get("ExpectedDeparture"),
        #     "scheduled_time_utc": rec.get("ScheduledDeparture"),
        #     "vehicle": rec.get("VehicleRef"),
        # })
    return result

if __name__ == '__main__':
    # 039027180001 - Russel street bus stop code according to ChatGPT
    # 039026550001 - Lima Court bus stop
    # print(next_three_reading_buses('039027180001'))
    print(next_three_reading_buses('039026550001'))


