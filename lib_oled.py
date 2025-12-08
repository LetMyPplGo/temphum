import threading
from time import sleep

from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

# --- config ---
I2C_ADDRESS = 0x3C  # change to 0x3D if your module shows that in i2cdetect
ROTATION = 0  # 0, 1, 2, 3 if you need to rotate
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"  # good for EN/RU
FONT_SIZE = 15  # 15+1 * 4 = 64px tall

# --- init display ---
# serial = i2c(port=1, address=I2C_ADDRESS)
# device = ssd1306(serial, rotate=ROTATION)  # 128x64


def update_display_dbg(lines: list):
    with open('oled_emu.txt', 'w') as f:
        f.write('\n'.join(lines))


class Display:
    def __init__(self):
        self.w = self.h = self.device = None
        self.init_device()
        self.lines = []
        self.counter = 0
        self.scroll_thread = threading.Thread(target=self.scroll_loop, daemon=True)
        self.scroll_thread.start()

        self.small_font = ImageFont.truetype(FONT_PATH, 12)
        self.big_font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
        longest_text = '888m 88a'
        bbox = self.big_font.getbbox(longest_text)
        text_width = bbox[2] - bbox[0]
        self.weather_start = text_width + 4
        self.rectangle = (text_width + 1, 14, self.w, self.h)


    def init_device(self):
        serial = i2c(port=1, address=0x3C)
        self.device = ssd1306(serial, rotate=0)
        self.w, self.h = self.device.width, self.device.height

    def update(self, lines: list):
        if self.lines != lines:
            self.counter = 0
            self.lines = lines

    def display(self, img):
        try:
            self.device.display(img)
        except Exception as err:
            print(f'Failed to display, retrying\n{err}')
            self.init_device()
            try:
                self.device.display(img)
            except Exception as err:
                print(f'Still failing\n{err}')


    def scroll_loop(self):
        while True:
            img = Image.new("1", (self.w, self.h), 0)  # 1-bit image
            draw = ImageDraw.Draw(img)

            y = 0
            for i, text in enumerate(self.lines):
                font_size = 12 if i == 0 else FONT_SIZE
                font = ImageFont.truetype(FONT_PATH, font_size)
                line_height = font_size + 2

                bbox = font.getbbox(text)
                text_width = bbox[2] - bbox[0]
                if text_width > (self.w - 2):
                    parts = text.split(' ', maxsplit=2)
                    fixed = parts[0] + ' ' + parts[1] + ' '
                    scrolled = parts[2] + '. '
                    scrolled = scrolled[self.counter % len(scrolled):]
                    text = fixed + scrolled
                    bbox = font.getbbox(text)
                    text_width = bbox[2] - bbox[0]
                    if text_width <= (self.w - 2):
                        text += parts[2]

                draw.text((1, y), text, font=font, fill=255)
                y += line_height
                if y >= self.h:
                    break

            self.display(img)
            self.counter += 1
            sleep(0.5)

    def update_new(self, data: dict):
        """
        data dict contains:
            time: str = '
            stop: str
            times: list(3)
            weather: list(3)
        {
            'time': '12:12'
        }
        draw a rectangle for weather taking max length of times
        21:35 Reading Station
        12m 26 | 11/-2C
        23m 2a | 82%
        24m 26 | 23>34
        """
        # TODO: complete this and use instead of the old one
        img = Image.new("1", (self.w, self.h), 0)
        draw = ImageDraw.Draw(img)
        draw.rectangle(self.rectangle, outline=1, fill=0)

        # line 1
        draw.text((1, 0), data['time'] + ' ' + data['stop'], font=self.small_font, fill=255)

        # bus lines
        for i, value in enumerate(data['times']):
            draw.text((1, 14 + i * FONT_SIZE), value, font=self.big_font, fill=255)

        # weather lines
        for i, value in enumerate(data['weather']):
            draw.text((self.weather_start, 14 + i * FONT_SIZE), value, font=self.small_font, fill=255)

        print('showing now')
        self.display(img)


if __name__ == '__main__':
    # lines = [
    #     "-= Hello =-",
    #     "Weather & Bus",
    #     "Reading, Lima crt",
    #     "Loading...",
    # ]
    # update_display(lines)
    data = {
        'time': '12:12',
        'stop': 'Lima crt.',
        'times': [
            '12m 26',
            '23m 2a',
            '888m 33b'
        ],
        'weather': [
            '11/-11C',
            '82%',
            'W23>24m/s'
        ],
    }
    display = Display()
    while True:
        display.update_new(data)
        sleep(0.5)
