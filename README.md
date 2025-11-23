# Temperature and Humidity reader + weather + next bus prediction


## Tools used
* All setup is for Raspberry Zero 2 W
* DHT22 sensor for temperature and Humidity (read_data.py)
* OLED I2C 128x64 SSD1306 to display text
* Python + RRDTool (time-series DB with auto-rollups) + lighthttpd, etc
* Weather is taken from Open Weather API (get_weather.py)
* Next bus prediction is taken from Reading Open Data API (bus.py)


## Assumptions
* Working dir is /home/admin/temphum (if not - change in all scripts)
* RRD DB is in folder /home/admin/temphum/dht
* Web root is /home/admin/temphum/www 

## Prepare
1. Run install.sh -> it installs needed libs
2. Copy read_data.py and make_chart.sh into the working dir
3. Copy index.html into the web root
4. Setup cron as shown in cron.tab
5. If your nginx/lighthttpd is serving from some special place, create a symlink
`sudo ln -s /home/admin/temphum/www /home/admin/mainsail/env`
As temporary solution you can use python http server:
`cd /home/admin/temphum/www && python3 -m http.server 8088`
But better use lighthppd or nginx (I use RPI that serves as klipper+mainsail for 3D printer, so I reuse mainsail nginx for that, see step 5 above)

## How it works
Every 10 minutes (cron) read_data.py is executed, it reads temperature and humifity from the DHT22 connected to the GPIO (pins 1,7,9)
The data is saved to RRD database
Every 10 minutes shifted 1 minute the script make_chart.sh is executed - it generates two png files in web root

In similar way, the write_oled.py is (to be) started every minute, it gets fresh data for weather and buses and updates the OLED

### Future work
When Rpi Zero arrives, everything will be rewritten for it
