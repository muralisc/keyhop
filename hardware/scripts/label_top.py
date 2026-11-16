"""Add callout labels to renders/keyhop-top.png -> renders/keyhop-top-labelled.png.

Needs Pillow. Board placement (mm) comes from build_pcb.py's PLACE table;
the render maps board x 100..160 mm, y 100..135 mm onto pixels detected
from the image. High-contrast black/white only (no colour coding).

usage: python label_top.py <keyhop-top.png> <out.png>
"""
import sys

from PIL import Image, ImageDraw, ImageFont

SRC, OUT = sys.argv[1], sys.argv[2]
BOARD_MM = (100.0, 100.0, 160.0, 135.0)

LEFT = [  # (designators, description, target mm)
    ("Q1/Q2, R3/R4", "auto-reset: flash without buttons", (112.0, 108.6)),
    ("R1/R2", "USB-C resistors: ask for 5 V", (103.5, 112.0)),
    ("U3", "ESD protection, USB-C data", (112.0, 113.0)),
    ("C9", "CH340C decoupling capacitor", (112.0, 117.2)),
    ("J1", "USB-C: power in + flashing/logs", (102.0, 120.0)),
    ("U2", "CH340C USB-to-serial chip", (116.4, 123.0)),
    ("U5", "5 V to 3.3 V regulator", (104.0, 132.0)),
    ("C1-C5", "power supply capacitors", (110.3, 131.8)),
]
RIGHT = [
    ("F1", "500 mA fuse for keyboard power", (142.6, 108.6)),
    ("C7/C8", "keyboard 5 V capacitors", (149.2, 108.6)),
    ("U4", "ESD protection, keyboard data", (142.4, 120.0)),
    ("J2", "USB-A: plug the keyboard in here", (156.0, 120.0)),
    ("R7 + D1", "green status LED", (142.0, 132.3)),
    ("J3", "UART header (not fitted)", (151.8, 132.6)),
]
TOP = [
    ("Antenna", "keep metal and copper away", (122.0, 103.0), 0.12),
    ("U1", "ESP32-S3 module: Bluetooth LE + USB host", (134.0, 112.0), 0.80),
]
BOTTOM = [
    ("SW1", "RESET button", (124.6, 131.4), 0.36),
    ("R5/C6/R6", "EN/BOOT pull-ups", (130.0, 130.4), 0.52),
    ("SW2", "BOOT button", (135.4, 131.4), 0.68),
]

FONT = "/System/Library/Fonts/Supplemental/Arial.ttf"
BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
f_reg = ImageFont.truetype(FONT, 24)
f_bold = ImageFont.truetype(BOLD, 24)
f_title = ImageFont.truetype(BOLD, 34)
f_small = ImageFont.truetype(FONT, 20)


def board_bbox(im):
    px = im.load()
    w, h = im.size
    xs, ys = [], []
    for y in range(0, h, 2):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if (r + g + b) / 3 < 120 and g >= b - 5:
                xs.append(x)
                ys.append(y)
    return min(xs), min(ys), max(xs), max(ys)


src = Image.open(SRC).convert("RGB")
bx0, by0, bx1, by1 = board_bbox(src)
# crop the render's wide background to a band around the board
PAD_X, PAD_Y = 60, 140
src = src.crop((bx0 - PAD_X, by0 - PAD_Y, bx1 + PAD_X, by1 + PAD_Y))
bx0, by0, bx1, by1 = PAD_X, PAD_Y, PAD_X + (bx1 - bx0), PAD_Y + (by1 - by0)
ML, MR, MT, MB = 580, 560, 90, 110
canvas = Image.new("RGB", (src.width + ML + MR, src.height + MT + MB), "white")
canvas.paste(src, (ML, MT))
d = ImageDraw.Draw(canvas)
sx = (bx1 - bx0) / (BOARD_MM[2] - BOARD_MM[0])
sy = (by1 - by0) / (BOARD_MM[3] - BOARD_MM[1])


def to_px(mm):
    return (ML + bx0 + (mm[0] - BOARD_MM[0]) * sx, MT + by0 + (mm[1] - BOARD_MM[1]) * sy)


def label_size(des, desc):
    a = d.textlength(des + "  ", font=f_bold)
    b = d.textlength(desc, font=f_reg)
    return a + b


def draw_label(x, y, des, desc, align):
    w = label_size(des, desc)
    left = x - w if align == "right" else (x - w / 2 if align == "center" else x)
    d.text((left, y), des + "  ", font=f_bold, fill="black", anchor="lm")
    d.text((left + d.textlength(des + "  ", font=f_bold), y), desc, font=f_reg, fill="black", anchor="lm")
    return left, left + w


def leader(p0, p1):
    d.line([p0, p1], fill="white", width=6)
    d.line([p0, p1], fill="black", width=2)
    x, y = p1
    d.ellipse([x - 8, y - 8, x + 8, y + 8], fill="white")
    d.ellipse([x - 5, y - 5, x + 5, y + 5], fill="black")


board_top, board_bot = MT + by0, MT + by1
board_left, board_right = ML + bx0, ML + bx1


def column(items, side):
    items = sorted(items, key=lambda it: it[2][1])
    n = len(items)
    span_top, span_bot = board_top + 20, board_bot - 20
    for i, (des, desc, mm) in enumerate(items):
        y = span_top + (span_bot - span_top) * (i / (n - 1) if n > 1 else 0.5)
        if side == "left":
            tx = board_left - 70
            draw_label(tx, y, des, desc, "right")
            leader((tx + 12, y), to_px(mm))
        else:
            tx = board_right + 70
            draw_label(tx, y, des, desc, "left")
            leader((tx - 12, y), to_px(mm))


column(LEFT, "left")
column(RIGHT, "right")

for des, desc, mm, frac in TOP:
    x = board_left + (board_right - board_left) * frac
    y = board_top - 70
    draw_label(x, y, des, desc, "center")
    leader((x, y + 18), to_px(mm))

for des, desc, mm, frac in BOTTOM:
    x = board_left + (board_right - board_left) * frac
    y = board_bot + 70 + (40 if des == "R5/C6/R6" else 0)
    draw_label(x, y, des, desc, "center")
    leader((x, y - 18), to_px(mm))

d.text((40, 45), "keyhop v0.1: top view (60 x 35 mm, 2-layer)", font=f_title, fill="black", anchor="lm")
d.text((40, canvas.height - 45),
       "USB socket 3D models are close stand-ins; buttons shown as outlines. "
       "Labels: designator (bold) + what it does.",
       font=f_small, fill="black", anchor="lm")
canvas.save(OUT)
print("saved", OUT, canvas.size)
