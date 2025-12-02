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

    def init_device(self):
        serial = i2c(port=1, address=0x3C)
        self.device = ssd1306(serial, rotate=0)
        self.w, self.h = self.device.width, self.device.height

    def update(self, lines: list):
        if self.lines != lines:
            self.counter = 0
            self.lines = lines

    def scroll_loop(self):
        while True:
            img = Image.new("1", (self.w, self.h), 0)  # 1-bit image
            draw = ImageDraw.Draw(img)

            y = 0
            for i, text in enumerate(self.lines):
                font_size = 12 if i == 0 else FONT_SIZE
                font = ImageFont.truetype(FONT_PATH, font_size)
                line_height = font_size + 1

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

            try:
                self.device.display(img)
            except Exception as err:
                print(f'Failed to display, retrying\n{err}')
                self.init_device()
            self.counter += 1
            sleep(0.5)


if __name__ == '__main__':
    # lines = [
    #     "-= Hello =-",
    #     "Weather & Bus",
    #     "Reading, Lima crt",
    #     "Loading...",
    # ]
    # update_display(lines)
    pass