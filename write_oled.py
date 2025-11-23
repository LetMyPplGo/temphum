from luma.core.interface.serial import i2c
from luma.oled.device import ssd1306
from PIL import Image, ImageDraw, ImageFont

# --- config ---
I2C_ADDRESS = 0x3C        # change to 0x3D if your module shows that in i2cdetect
ROTATION = 0              # 0, 1, 2, 3 if you need to rotate
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"  # good for EN/RU
FONT_SIZE = 12            # 12 * 5 = 60px tall -> fits into 64px with margins
LINES = [
    "Line 1: Hello",
    "Line 2: RPi Zero 2",
    "Line 3: SSD1306",
    "Line 4: I2C",
    "Line 5: ✔ Ready"
]

# --- init display ---
serial = i2c(port=1, address=I2C_ADDRESS)
device = ssd1306(serial, rotate=ROTATION)  # 128x64

# --- render ---
W, H = device.width, device.height
img = Image.new("1", (W, H), 0)   # 1-bit image
draw = ImageDraw.Draw(img)

# load font
font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

# draw lines (auto-truncate to display width)
line_height = FONT_SIZE + 1
y = 0
for text in LINES[:5]:
    # truncate so it fits width
    t = text
    while font.getlength(t) > (W - 2) and len(t) > 0:
        t = t[:-1]
    draw.text((1, y), t, font=font, fill=255)
    y += line_height
    if y >= H:
        break

device.display(img)
