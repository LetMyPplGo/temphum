# Temperature and Humidity reader + weather + next bus prediction


## Tools used
* All setup is for Raspberry Zero 2 W (currently it's a sidecar on RPI 3B with klipper+mainsail)
* DHT22 sensor for temperature and Humidity (read_data.py)
* OLED I2C 128x64 SSD1306 to display text
* Python + RRDTool (time-series DB with auto-rollups) + lighthttpd, etc
* Weather is taken from Open Weather API (get_weather.py)
* Next bus prediction is taken from Reading Open Data API (bus.py)


## Assumptions
* Working dir is /etc/temphum
* RRD DB is in /etc/temphum/dht22.rrd
* Web root is /etc/temphum/www 

## Prepare
1. Run install.sh -> it installs needed libs
2. Copy all *.py files and make_chart.sh into the working dir
3. Copy index.html into the web root

## How it works
Every 10 minutes (cron) read_data.py is executed, it reads temperature and humifity from the DHT22 connected to the GPIO (pins 1,7,9)
The data is saved to RRD database
Every 10 minutes shifted 1 minute the script make_chart.sh is executed - it generates two png files in web root

In similar way, the write_oled.py is (to be) started every minute, it gets fresh data for weather and buses and updates the OLED

### Future work
When Rpi Zero arrives, everything will be rewritten for it
