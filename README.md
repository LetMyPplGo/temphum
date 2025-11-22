# Temperature and Humidity reader

Based on RPI + DHT22 sensor

Python (read sensor) + RRDTool (time-series DB with auto-rollups) + a static PNG chart served by any tiny web server.

Assuming that the working dir is /home/admin/temphum (if not - change in all scripts)
RRD DB is in folder /home/admin/temphum/dht
Web root is /home/admin/temphum/www 

## Prepare
1. run install.sh
2. copy read_data.py and make_chart.sh into the working dir
3. copy index.html into the web root
4. setup cron as shown in cron.tab
5. If your nginx is serving from some special place, create a symlink
`sudo ln -s /home/admin/temphum/www /home/admin/mainsail/env`
Now you just need to serve index.html from the web root. As temporary solution use:
`cd /home/admin/temphum/www && python3 -m http.server 8088`
But better use lighthppd or nginx (I use RPI that serves as klipper+mainsail for 3D printer, so I reuse mainsail nginx for that, see step 5 above)

## How it works
Every 10 minutes (cron) read_data.py is executed, it reads temperature and humifity from the DHT22 connected to the GPIO (pins 1,7,9)
The data is saved to RRD database
Every 10 minutes shifted 1 minute the script make_chart.sh is executed - it generates two png files in web root

### Future work
When Rpi Zero arrives, everything will be rewritten for it
