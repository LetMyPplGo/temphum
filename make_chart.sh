#!/bin/bash
set -e

RRD="/home/admin/temphum/dht/dht22.rrd"
OUT_DIR="/home/admin/temphum/www"

mkdir -p "$OUT_DIR"

# 1) Last 24 hours, 10-min resolution
rrdtool graph "${OUT_DIR}/dht22_24h.png" \
  --width 900 --height 260 \
  --start end-24h --end now \
  --title "Temperature & Humidity – last 24 hours (10 min step)" \
  --vertical-label "Temp °C / Humidity %" \
  --x-grid MINUTE:10:HOUR:1:HOUR:2:0:%H:%M \
  DEF:t="$RRD":temp:AVERAGE \
  DEF:h="$RRD":hum:AVERAGE \
  CDEF:h_scaled=h,0.5,* \
  LINE2:t#ff7f0e:"Temp (°C)" \
  LINE1:h_scaled#1f77b4:"Humidity (% ×0.5)" \
  GPRINT:t:LAST:"Last Temp\: %2.1lf°C  " \
  GPRINT:h:LAST:"Last Humidity\: %2.0lf%%\n" \
  GPRINT:t:MIN:"Min Temp\: %2.1lf°C  " \
  GPRINT:t:MAX:"Max Temp\: %2.1lf°C  " \
  GPRINT:t:AVERAGE:"Avg Temp\: %2.1lf°C\n" \
  GPRINT:h:MIN:"Min Humid\: %2.0lf%%  " \
  GPRINT:h:MAX:"Max Humid\: %2.0lf%%  " \
  GPRINT:h:AVERAGE:"Avg Humid\: %2.0lf%%\n"

# 2) Last 7 days overview (optional, keeps older chart)
rrdtool graph "${OUT_DIR}/dht22_7d.png" \
  --width 900 --height 260 \
  --start end-7d --end now \
  --title "Temperature & Humidity – last 7 days" \
  --vertical-label "Temp °C / Humidity %" \
  DEF:t="$RRD":temp:AVERAGE \
  DEF:h="$RRD":hum:AVERAGE \
  CDEF:h_scaled=h,0.5,* \
  LINE2:t#ff7f0e:"Temp (°C)" \
  LINE1:h_scaled#1f77b4:"Humidity (% ×0.5)" \
  GPRINT:t:LAST:"Last Temp\: %2.1lf°C  " \
  GPRINT:h:LAST:"Last Humidity\: %2.0lf%%\n" \
  GPRINT:t:MIN:"Min Temp\: %2.1lf°C  " \
  GPRINT:t:MAX:"Max Temp\: %2.1lf°C  " \
  GPRINT:t:AVERAGE:"Avg Temp\: %2.1lf°C\n" \
  GPRINT:h:MIN:"Min Humid\: %2.0lf%%  " \
  GPRINT:h:MAX:"Max Humid\: %2.0lf%%  " \
  GPRINT:h:AVERAGE:"Avg Humid\: %2.0lf%%\n"