from datetime import datetime

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

from helpers import read_state
from lib_bus import next_buses
from get_weather import get_today_summary

# --- config ---
I2C_ADDRESS = 0x3C        # change to 0x3D if your module shows that in i2cdetect
ROTATION = 0              # 0, 1, 2, 3 if you need to rotate
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"  # good for EN/RU
FONT_SIZE = 15            # 15+1 * 4 = 64px tall

# --- init display ---
# serial = i2c(port=1, address=I2C_ADDRESS)
# device = ssd1306(serial, rotate=ROTATION)  # 128x64

def update_display(lines: list):
    w, h = device.width, device.height
    img = Image.new("1", (w, h), 0)   # 1-bit image
    draw = ImageDraw.Draw(img)

    y = 0
    for i, text in enumerate(lines):
        font_size = 12 if i==0 else FONT_SIZE

        # load font
        font = ImageFont.truetype(FONT_PATH, font_size)
        line_height = font_size + 1

        # truncate so it fits width
        while font.getlength(text) > (w - 2) and len(text) > 0:
            text = text[:-1]
        draw.text((1, y), text, font=font, fill=255)
        y += line_height
        if y >= h:
            break

    device.display(img)

def get_lines():
    weather = get_today_summary()
    now = datetime.now().strftime("%H:%M")
    stop_id = read_state().get('stop_id', '039026550001')
    return [f'{now} {weather}',] + next_buses(stop_id)


if __name__ == '__main__':
    # lines = [
    #     "-= Hello =-",
    #     "Weather & Bus",
    #     "Reading, Lima crt",
    #     "Loading...",
    # ]
    # update_display(lines)

    lines = get_lines()
    print(lines)
    # update_display(lines)

