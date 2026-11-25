#!/usr/bin/env python3
"""Draw Wednesday 25 November 2026 as one deterministic news page.

Python 3.13, standard library only. Writes entry.png under
$MAKEFUN_OUTPUT_DIR or /output. Same bytes on every run.
"""

import os
import struct
import zlib

W = 1024
H = 1024

NAVY = (14, 32, 64)
NAVY_DEEP = (10, 22, 46)
RED = (168, 36, 44)
RED_DEEP = (122, 24, 32)
CREAM = (244, 238, 226)
PAPER = (255, 252, 246)
INK = (24, 28, 36)
MUTED = (86, 78, 68)
GOLD = (196, 148, 58)
WHITE = (255, 252, 246)
TEAL = (14, 110, 114)
GREEN = (26, 102, 68)
AMBER = (154, 92, 28)
PURPLE = (92, 48, 120)
BLUE = (28, 72, 140)

# 5x7 glyphs, top row first, leftmost bit is column 0. Width is 5.
_RAW = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01111", "10000", "10000", "10000", "10000", "10000", "01111"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01111", "10000", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("11111", "00100", "00100", "00100", "00100", "00100", "11111"),
    "J": ("00111", "00010", "00010", "00010", "10010", "10010", "01100"),
    "K": ("10001", "10010", "10100", "11000", "10100", "10010", "10001"),
    "L": ("10000", "10000", "10000", "10000", "10000", "10000", "11111"),
    "M": ("10001", "11011", "10101", "10101", "10001", "10001", "10001"),
    "N": ("10001", "11001", "10101", "10011", "10001", "10001", "10001"),
    "O": ("01110", "10001", "10001", "10001", "10001", "10001", "01110"),
    "P": ("11110", "10001", "10001", "11110", "10000", "10000", "10000"),
    "Q": ("01110", "10001", "10001", "10001", "10101", "10010", "01101"),
    "R": ("11110", "10001", "10001", "11110", "10100", "10010", "10001"),
    "S": ("01111", "10000", "10000", "01110", "00001", "00001", "11110"),
    "T": ("11111", "00100", "00100", "00100", "00100", "00100", "00100"),
    "U": ("10001", "10001", "10001", "10001", "10001", "10001", "01110"),
    "V": ("10001", "10001", "10001", "10001", "10001", "01010", "00100"),
    "W": ("10001", "10001", "10001", "10101", "10101", "10101", "01010"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00010", "00100", "01000", "11111"),
    "3": ("11110", "00001", "00001", "01110", "00001", "00001", "11110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "10000", "11110", "00001", "10001", "01110"),
    "6": ("01110", "10000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00001", "01110"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "00110", "00110", "00100"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    "-": ("00000", "00000", "00000", "11111", "00000", "00000", "00000"),
    "/": ("00001", "00001", "00010", "00100", "01000", "10000", "10000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "&": ("01100", "10010", "10100", "01000", "10100", "10010", "01101"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
}

FONT = {ch: tuple(int(row, 2) for row in rows) for ch, rows in _RAW.items()}
GLYPH_W = 5
GLYPH_H = 7


class Canvas:
    def __init__(self, w, h, color):
        self.w = w
        self.h = h
        self.buf = bytearray(color * (w * h))

    def put(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.buf[i] = color[0]
            self.buf[i + 1] = color[1]
            self.buf[i + 2] = color[2]

    def rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x0 >= x1 or y0 >= y1:
            return
        row = bytes(color) * (x1 - x0)
        stride = self.w * 3
        for yy in range(y0, y1):
            start = yy * stride + x0 * 3
            self.buf[start : start + (x1 - x0) * 3] = row

    def circle(self, cx, cy, r, color):
        r2 = r * r
        for y in range(cy - r, cy + r + 1):
            for x in range(cx - r, cx + r + 1):
                if (x - cx) * (x - cx) + (y - cy) * (y - cy) <= r2:
                    self.put(x, y, color)

    def ring(self, cx, cy, r, thickness, color):
        outer = r * r
        inner = (r - thickness) * (r - thickness)
        for y in range(cy - r, cy + r + 1):
            dy = (y - cy) * (y - cy)
            for x in range(cx - r, cx + r + 1):
                d = (x - cx) * (x - cx) + dy
                if inner <= d <= outer:
                    self.put(x, y, color)

    def line(self, x0, y0, x1, y1, color, thick=1):
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        rad = max(0, thick // 2)
        while True:
            if rad == 0:
                self.put(x0, y0, color)
            else:
                self.circle(x0, y0, rad, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def text(self, s, x, y, scale, color):
        s = s.upper()
        cursor = x
        gap = scale
        for ch in s:
            glyph = FONT.get(ch, FONT[" "])
            for row in range(GLYPH_H):
                bits = glyph[row]
                for col in range(GLYPH_W):
                    if bits & (1 << (GLYPH_W - 1 - col)):
                        self.rect(
                            cursor + col * scale,
                            y + row * scale,
                            scale,
                            scale,
                            color,
                        )
            cursor += GLYPH_W * scale + gap
        return cursor

    def text_width(self, s, scale):
        s = s.upper()
        if not s:
            return 0
        gap = scale
        return len(s) * (GLYPH_W * scale + gap) - gap

    def center_text(self, s, cx, y, scale, color):
        tw = self.text_width(s, scale)
        self.text(s, cx - tw // 2, y, scale, color)


def png_bytes(canvas):
    raw = bytearray()
    stride = canvas.w * 3
    buf = canvas.buf
    for y in range(canvas.h):
        raw.append(0)
        start = y * stride
        raw.extend(buf[start : start + stride])
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)

    def chunk(tag, data):
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
        + chunk(b"IEND", b"")
    )


def icon_station(c, x, y, color):
    # Tiangong ring plus the Long March that carried Shenzhou-24.
    c.ring(x + 14, y + 24, 12, 3, color)
    c.rect(x + 11, y + 8, 6, 8, color)
    c.rect(x + 2, y + 22, 24, 4, color)
    c.rect(x + 36, y + 16, 8, 26, color)
    c.line(x + 34, y + 16, x + 40, y + 4, color, 3)
    c.line(x + 46, y + 16, x + 40, y + 4, color, 3)
    c.rect(x + 32, y + 38, 5, 8, color)
    c.rect(x + 43, y + 38, 5, 8, color)


def icon_chart(c, x, y, color):
    c.rect(x + 4, y + 6, 12, 44, color)
    c.rect(x + 22, y + 20, 12, 30, color)
    c.rect(x + 40, y + 34, 12, 16, color)


def icon_bolt(c, x, y, color):
    c.line(x + 32, y + 4, x + 14, y + 28, color, 4)
    c.line(x + 14, y + 28, x + 28, y + 28, color, 4)
    c.line(x + 28, y + 28, x + 16, y + 54, color, 4)
    c.line(x + 16, y + 54, x + 40, y + 24, color, 4)
    c.line(x + 40, y + 24, x + 26, y + 24, color, 4)
    c.line(x + 26, y + 24, x + 32, y + 4, color, 4)


def icon_drone(c, x, y, color):
    c.rect(x + 22, y + 24, 14, 8, color)
    arms = ((8, 8), (48, 8), (8, 46), (48, 46))
    for ax, ay in arms:
        c.line(x + 28, y + 28, x + ax, y + ay, color, 2)
        c.ring(x + ax, y + ay, 6, 2, color)


def icon_city(c, x, y, color):
    c.rect(x + 4, y + 28, 14, 24, color)
    c.rect(x + 20, y + 10, 16, 42, color)
    c.rect(x + 38, y + 22, 14, 30, color)
    c.rect(x + 24, y + 18, 8, 6, PAPER)
    c.rect(x + 24, y + 30, 8, 6, PAPER)


def icon_ship(c, x, y, color):
    c.rect(x + 4, y + 26, 48, 10, color)
    c.line(x + 8, y + 36, x + 48, y + 46, color, 4)
    c.line(x + 48, y + 46, x + 52, y + 26, color, 3)
    c.rect(x + 30, y + 12, 12, 14, color)
    c.rect(x + 40, y + 6, 4, 8, color)


def icon_bat(c, x, y, color):
    c.rect(x + 16, y + 6, 12, 30, color)
    c.rect(x + 18, y + 36, 8, 16, color)
    c.circle(x + 42, y + 16, 6, color)


def icon_sun(c, x, y, color):
    c.circle(x + 28, y + 28, 10, color)
    for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1)):
        c.line(x + 28 + dx * 16, y + 28 + dy * 16, x + 28 + dx * 24, y + 28 + dy * 24, color, 3)


def card(c, x, y, w, h, bar, title, lines, subs, icon):
    c.rect(x, y, w, h, PAPER)
    c.rect(x, y, 8, h, bar)
    icon(c, x + w - 64, y + 8, bar)
    c.text(title, x + 18, y + 8, 3, bar)
    yy = y + 34
    for line in lines:
        c.text(line, x + 18, yy, 4, INK)
        yy += 4 * GLYPH_H + 4
    yy += 4
    for line in subs:
        c.text(line, x + 18, yy, 3, MUTED)
        yy += 3 * GLYPH_H + 3


def draw():
    c = Canvas(W, H, CREAM)
    c.rect(0, 0, W, 176, NAVY)
    c.rect(0, 176, W, 10, RED)

    c.text("25", 36, 28, 16, WHITE)
    c.text("WEDNESDAY", 250, 36, 4, GOLD)
    c.text("NOVEMBER 2026", 250, 78, 5, WHITE)
    c.text("ONE DAY OF WORLD NEWS", 250, 128, 3, GOLD)

    # Lead: China's station, first foreign crew member.
    c.rect(20, 202, 488, 252, NAVY_DEEP)
    c.rect(20, 202, 8, 252, TEAL)
    c.text("ASIA  /  SCIENCE", 40, 214, 2, GOLD)
    c.text("ALI REACHES", 40, 244, 5, WHITE)
    c.text("TIANGONG", 40, 290, 6, WHITE)
    c.text("FIRST FOREIGN ASTRONAUT", 40, 346, 3, GOLD)
    c.text("ALI, 40, DOCKED 06:35 GMT", 40, 376, 3, WHITE)
    c.text("TANG HONGBO AND WU YI", 40, 400, 3, WHITE)
    c.text("LAUNCHED FROM JIUQUAN", 40, 424, 3, WHITE)
    icon_station(c, 400, 214, GOLD)

    # Lead: tariffs proposed Wednesday, and the morning selloff.
    c.rect(516, 202, 488, 252, RED_DEEP)
    c.rect(516, 202, 8, 252, GOLD)
    c.text("AMERICAS  /  ECONOMY", 536, 214, 2, GOLD)
    c.text("NEW TARIFFS", 536, 244, 5, WHITE)
    c.text("S&P OFF 2.7%", 536, 292, 5, WHITE)
    c.text("14 PARTNERS AT 20-40%", 536, 342, 3, GOLD)
    c.text("CAPPED BY TRADE DEALS", 536, 366, 3, WHITE)
    c.text("NASDAQ -4.1%  DOW -2%", 536, 394, 3, WHITE)
    c.text("LATE MORNING PCE 3.3%", 536, 418, 3, WHITE)
    icon_chart(c, 920, 214, GOLD)

    stories = (
        (
            20,
            468,
            TEAL,
            "EUROPE  /  WAR",
            ("RUSSIA CUTS", "UKRAINE POWER"),
            ("FIVE REGIONS IN THE DARK.", "TWO KILLED IN ODESA."),
            icon_bolt,
        ),
        (
            516,
            468,
            GREEN,
            "AFRICA  /  WAR",
            ("DRONES KILL 19", "IN BLUE NILE"),
            ("EMERGENCY LAWYERS SAID.", "RSF DRONES KILLED THEM."),
            icon_drone,
        ),
        (
            20,
            640,
            AMBER,
            "MIDEAST  /  WAR",
            ("ABUELOUF KILLED", "WITH HIS FAMILY"),
            ("WIFE AND TWO CHILDREN.", "IDF: MILITARY OPERATIVES."),
            icon_city,
        ),
        (
            516,
            640,
            BLUE,
            "MIDEAST  /  ENERGY",
            ("TWO TANKERS BURN", "HORMUZ STRAIT"),
            ("IRGC: MINES SET FIRES.", "HOUTHIS CLAIM RAS TANURA."),
            icon_ship,
        ),
        (
            20,
            812,
            PURPLE,
            "ASIA  /  SPORT",
            ("52-BALL LIST A", "DOUBLE CENTURY"),
            ("SOORYAVANSHI, AGE 15.", "28 SIXES, UAE BEATEN."),
            icon_bat,
        ),
        (
            516,
            812,
            RED,
            "WORLD  /  CLIMATE",
            ("POPE LEO XIV", "FAULTS COP31"),
            ("NO CLEAR COMMITMENTS.", "HE CALLS IT TROUBLING."),
            icon_sun,
        ),
    )
    for x, y, bar, title, lines, subs, icon in stories:
        card(c, x, y, 488, 160, bar, title, lines, subs, icon)

    c.rect(0, 984, W, 40, NAVY)
    c.center_text("WEDNESDAY  25  NOVEMBER  2026", W // 2, 996, 3, WHITE)
    return c


def main():
    canvas = draw()
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.png")
    data = png_bytes(canvas)
    with open(path, "wb") as fh:
        fh.write(data)


if __name__ == "__main__":
    main()
