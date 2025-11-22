#!/usr/bin/env python3
import time
import subprocess
import sys

import board
import adafruit_dht
import rrdtool

GPIO_PIN = board.D4   # BCM4 / Pin 7 on the header
RRD = "/home/admin/temphum/dht/dht22.rrd"

# Initialise sensor
dht = adafruit_dht.DHT22(GPIO_PIN)

try:
    temperature = dht.temperature      # °C
    humidity = dht.humidity            # %
except RuntimeError:
    # DHTs are a bit noisy; a failed read is normal — just skip this cycle
    sys.exit(0)
except Exception:
    dht.exit()
    raise
finally:
    dht.exit()


if humidity is None or temperature is None:
    sys.exit(0)

t = round(float(temperature), 2)
h = round(float(humidity), 2)

print(f'{t=}, {h=}')
try:
    print('Saving data to RRD')
    rrdtool.update(RRD, f"N:{t}:{h}")
    print('Done')
except rrdtool.OperationalError as e:
    # Optional: log error instead of crashing
    print(f"RRD update failed: {e}", file=sys.stderr)
    sys.exit(1)
except Exception as e:
    print(f'Error: {e}')

