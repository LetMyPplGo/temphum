sudo apt update
sudo apt install -y python3-pip rrdtool python3-rrdtool python3-libgpiod lighttpd i2c-tools

cd /home/admin/temphum
python3 -m venv --system-site-packages venv1
source ./venv1/bin/activate

pip install adafruit-blinka adafruit-circuitpython-dht pillow smbus2 luma.oled
systemctl enable --now lighttpd

mkdir -p /home/admin/temphum/www
mkdir -p /home/admin/temphum/dht
cd /home/admin/temphum/dht
rrdtool create dht22.rrd --step 600 \
  DS:temp:GAUGE:1200:-40:80 \
  DS:hum:GAUGE:1200:0:100 \
  RRA:AVERAGE:0.5:1:2016 \
  RRA:MIN:0.5:6:1344 \
  RRA:MAX:0.5:6:1344 \
  RRA:AVERAGE:0.5:6:1344

 echo checking the I2C export
 i2cdetect -y 1
 