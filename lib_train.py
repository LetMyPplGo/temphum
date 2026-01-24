from zeep import Client, Settings, xsd
from zeep.plugins import HistoryPlugin
import json
from pathlib import Path
import pandas as pd
from pyproj import Transformer
from datetime import datetime, timedelta

from helpers import read_state, get_active_tab

LDB_TOKEN = read_state().get('train_token')
WSDL = 'http://lite.realtime.nationalrail.co.uk/OpenLDBWS/wsdl.aspx?ver=2021-11-01'


def convert_stations(xlsx_path: str | Path, out_path: str | Path) -> list[dict]:
    """
    Converts table-6329 from this page: https://dataportal.orr.gov.uk/statistics/infrastructure-and-environment/rail-infrastructure-and-assets/table-6329-station-attributes-for-all-mainline-stations/
    Result is list of dicts like:
        [
          {
            "name": "Abbey Wood",
            "crs": "ABW",
            "latitude": 51.491060102553256,
            "longitude": 0.11993907723072637
          }, ...
        ]
    """
    xlsx_path = Path(xlsx_path)
    out_path = Path(out_path)

    # Read the sheet, skipping first 3 rows (metadata)
    df = pd.read_excel(
        xlsx_path,
        sheet_name="6329_station_attributes",
        skiprows=3,   # headers are on row 4 (1-based)
    )

    # Drop completely empty rows
    df = df.dropna(how="all")

    # Detect column names (in case line breaks or minor changes)
    def find_col(substr: str) -> str:
        for col in df.columns:
            if substr.lower() in str(col).lower():
                return col
        raise KeyError(f"Column containing '{substr}' not found in sheet")

    col_name = find_col("Station name")
    col_crs = find_col("Three Letter Code")
    col_east = find_col("Easting")
    col_north = find_col("Northing")

    # Transformer from OSGB36 / British National Grid (EPSG:27700) to WGS84 (EPSG:4326)
    transformer = Transformer.from_crs(
        "EPSG:27700",  # OSGB36 / British National Grid
        "EPSG:4326",   # WGS84 (lon/lat)
        always_xy=True
    )

    stations: list[dict] = []

    for _, row in df.iterrows():
        name = row.get(col_name)
        crs = row.get(col_crs)
        easting = row.get(col_east)
        northing = row.get(col_north)

        # Skip rows without essential data
        if pd.isna(name) or pd.isna(crs) or pd.isna(easting) or pd.isna(northing):
            continue

        try:
            # transformer returns (lon, lat)
            lon, lat = transformer.transform(float(easting), float(northing))
        except Exception:
            print(f'Skipping {name} as coordinates convertion failed')
            continue

        stations.append(
            {
                "name": str(name),
                "crs": str(crs),
                "latitude": lat,
                "longitude": lon,
            }
        )

    # Save list of dicts as JSON
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(stations, f, ensure_ascii=False, indent=2)

    return stations


def get_train_stops():
    file_name = 'train_stations.json'
    with open(file_name, 'r') as f:
        return json.load(f)

def get_train_coordinates(crs):
    stops = get_train_stops()
    for stop in stops:
        if stop.get('crs') == crs:
            return f'{stop.get("latitude")},{stop.get("longitude")}'

def _get_trains(station_from: str, station_to: str):
    settings = Settings(strict=False)
    history = HistoryPlugin()
    client = Client(wsdl=WSDL, settings=settings, plugins=[history])
    header = xsd.Element(
        '{http://thalesgroup.com/RTTI/2013-11-28/Token/types}AccessToken',
        xsd.ComplexType([
            xsd.Element(
                '{http://thalesgroup.com/RTTI/2013-11-28/Token/types}TokenValue',
                xsd.String()),
        ])
    )
    header_value = header(TokenValue=LDB_TOKEN)

    ret = client.service.GetDepBoardWithDetails(
        numRows=50,
        crs=station_from,
        _soapheaders=[header_value],
        timeOffset=0,
        timeWindow=240,
    )

    filtered_services = [
        svc for svc in ret.trainServices.service
        if getattr(svc, "subsequentCallingPoints", None)
           and svc.subsequentCallingPoints.callingPointList
           and any(
            cp.crs == station_to
            for cpl in svc.subsequentCallingPoints.callingPointList
            for cp in cpl.callingPoint
        )
    ]
    return filtered_services


def _parse_time_hhmm(value: str):
    fmt = "%H:%M"
    if not value or value.lower() in ("cancelled", "canceled", "delayed", "on time"):
        return None
    try:
        return datetime.strptime(value, fmt)
    except ValueError:
        return None

def minutes_between(start_st: str, end_st: str) -> int | None:
    fmt = "%H:%M"
    start = _parse_time_hhmm(start_st)
    end = _parse_time_hhmm(end_st)
    if start is None or end is None:
        return None
    diff = (end - start).total_seconds() / 60
    # If end is before start, add 24 hours worth of minutes, if it's more than 12h forward, treat as backward
    if diff < 0:
        diff += 1440  # 24 * 60
    if diff > 720:
        diff -= 1440

    return int(diff)

def get_trains():
    state = read_state()
    tab = get_active_tab(state)
    station_from = tab.get('train_from', 'RDG')
    station_to = tab.get('train_to', 'PAD')
    services = _get_trains(station_from, station_to)
    lines = []
    for t in services:
        my_stop_time = next(
            cp.st
            for cpl in t.subsequentCallingPoints.callingPointList
            for cp in cpl.callingPoint
            if cp.crs == station_to
        )
        duration = minutes_between(t.std, t.subsequentCallingPoints.callingPointList[0].callingPoint[-1].st)
        if duration is None:
            duration = 0
        platform = f'p{t.platform}' if t.platform is not None else ''
        est = t.etd if t.etd != 'On time' else t.std
        time_to_train = minutes_between(datetime.now().strftime("%H:%M"), est)
        if time_to_train is None:
            time_to_train = ""
        # Long format
        # stops = len(t.subsequentCallingPoints.callingPointList[0].callingPoint)
        # lines.append(f'{est} {platform} {t.operatorCode} to {t.destination.location[0].locationName}, {duration}m, {stops} stop{"s" if stops > 1 else ""} ')
        # Short format
        # lines.append(f'{est} {platform} {t.operatorCode} to {t.destination.location[0].locationName}, {duration}m')
        # Tiny format
        # lines.append(f'{est}->{my_stop_time} {platform} {duration}m')
        # lines.append(f'{est} {time_to_train}m {platform} {duration}m')
        lines.append(f'{est} {platform} {duration}m')
    # return '\n'.join(lines)
    return sorted(lines)


if __name__ == '__main__':
    # convert_stations('table-6329-station-attributes-for-all-mainline-stations.ods', 'train_stations.json')
    print('\n'.join(get_trains()))
