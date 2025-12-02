sudo apt update
sudo apt install -y python3-pip rrdtool python3-rrdtool python3-libgpiod i2c-tools

mkdir -p /etc/temphum
mkdir -p /etc/temphum/www

cd /etc/temphum
python3 -m venv --system-site-packages venv
source /etc/temphum/venv/bin/activate

pip install -r requirements.txt

rrdtool create dht22.rrd --step 600 \
  DS:temp:GAUGE:1200:-40:80 \
  DS:hum:GAUGE:1200:0:100 \
  RRA:AVERAGE:0.5:1:2016 \
  RRA:MIN:0.5:6:1344 \
  RRA:MAX:0.5:6:1344 \
  RRA:AVERAGE:0.5:6:1344

#echo checking the I2C export
i2cdetect -y 1
 