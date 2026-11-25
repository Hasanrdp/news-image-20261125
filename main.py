#!/usr/bin/env python3
"""TODAY'S WORLD -- a one-page newspaper front page summing up
Wednesday 25 November 2026, drawn entirely in pure-stdlib Python.

The program renders a 1024x1024 front page (masthead, lead story on
China's Shenzhou-24 launch, the Australia-Solomon Islands security
pact, six more stories from around the world and a ticker of the
rest of the day) and writes it to /output/entry.png (or
$MAKEFUN_OUTPUT_DIR/entry.png when set). No network, no image
libraries: a 5x7 bitmap font, vector shapes and a hand-rolled PNG
encoder. The output is fully deterministic: two runs write the
same bytes, and the program verifies the pinned hash and byte
count before it prints its result.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import hashlib
import os
import struct
import sys
import zlib

# Pinned by the author after the first run; the program refuses to
# print a result unless the bytes it just rendered match these.
EXPECTED_SHA256 = "a2bfc07b85ae5c06bbdce431457453bd462a03ecbf1826ca0e56abcb38cb43a9"
EXPECTED_BYTES = 38344

W, H = 1024, 1024

PAPER = (248, 244, 233)
INK = (22, 22, 22)
RED = (166, 25, 25)
BLUE = (30, 78, 121)
GOLD = (200, 155, 60)
SKY = (14, 42, 71)
SKY2 = (24, 68, 104)
SKY3 = (43, 102, 143)
SEA = (52, 120, 158)
EARTH = (46, 111, 173)
GREEN = (74, 124, 64)
GREY = (120, 120, 118)
LIGHTGREY = (214, 210, 198)
WHITE = (255, 255, 255)
ORANGE = (232, 116, 28)
YELLOW = (244, 196, 48)
BROWN = (122, 82, 42)
DARK = (30, 30, 34)

# 5x7 bitmap font. Each glyph is 7 rows of 5 bits, '1' = ink.
FONT = {
    "A": ("01110", "10001", "10001", "11111", "10001", "10001", "10001"),
    "B": ("11110", "10001", "10001", "11110", "10001", "10001", "11110"),
    "C": ("01110", "10001", "10000", "10000", "10000", "10001", "01110"),
    "D": ("11110", "10001", "10001", "10001", "10001", "10001", "11110"),
    "E": ("11111", "10000", "10000", "11110", "10000", "10000", "11111"),
    "F": ("11111", "10000", "10000", "11110", "10000", "10000", "10000"),
    "G": ("01110", "10001", "10000", "10111", "10001", "10001", "01111"),
    "H": ("10001", "10001", "10001", "11111", "10001", "10001", "10001"),
    "I": ("01110", "00100", "00100", "00100", "00100", "00100", "01110"),
    "J": ("00111", "00010", "00010", "00010", "00010", "10010", "01100"),
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
    "W": ("10001", "10001", "10001", "10101", "10101", "11011", "10001"),
    "X": ("10001", "10001", "01010", "00100", "01010", "10001", "10001"),
    "Y": ("10001", "10001", "01010", "00100", "00100", "00100", "00100"),
    "Z": ("11111", "00001", "00010", "00100", "01000", "10000", "11111"),
    "0": ("01110", "10001", "10011", "10101", "11001", "10001", "01110"),
    "1": ("00100", "01100", "00100", "00100", "00100", "00100", "01110"),
    "2": ("01110", "10001", "00001", "00110", "01000", "10000", "11111"),
    "3": ("11111", "00010", "00100", "00010", "00001", "10001", "01110"),
    "4": ("00010", "00110", "01010", "10010", "11111", "00010", "00010"),
    "5": ("11111", "10000", "11110", "00001", "00001", "10001", "01110"),
    "6": ("00110", "01000", "10000", "11110", "10001", "10001", "01110"),
    "7": ("11111", "00001", "00010", "00100", "01000", "01000", "01000"),
    "8": ("01110", "10001", "10001", "01110", "10001", "10001", "01110"),
    "9": ("01110", "10001", "10001", "01111", "00001", "00010", "01100"),
    " ": ("00000", "00000", "00000", "00000", "00000", "00000", "00000"),
    ".": ("00000", "00000", "00000", "00000", "00000", "01100", "01100"),
    ",": ("00000", "00000", "00000", "00000", "01100", "00100", "01000"),
    ":": ("00000", "01100", "01100", "00000", "01100", "01100", "00000"),
    ";": ("00000", "01100", "01100", "00000", "01100", "00100", "01000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "+": ("00000", "00100", "00100", "01110", "00100", "00100", "00000"),
    "=": ("00000", "00000", "01110", "00000", "01110", "00000", "00000"),
    "_": ("00000", "00000", "00000", "00000", "00000", "00000", "11111"),
}


def text_width(s, scale):
    return len(s) * 6 * scale - scale


def wrap_words(text, max_chars):
    """Greedy word wrap; returns a list of lines, each <= max_chars."""
    lines = []
    for raw in text.split("\n"):
        line = ""
        for word in raw.split(" "):
            if not line:
                line = word
            elif len(line) + 1 + len(word) <= max_chars:
                line += " " + word
            else:
                lines.append(line)
                line = word
        if line:
            lines.append(line)
    return lines


class Canvas:
    def __init__(self, w, h, bg):
        self.w, self.h = w, h
        self.px = bytearray(bg * (w * h))
        self.clip = (0, 0, w, h)
        self._clip_stack = []

    def set_clip(self, x, y, w, h):
        self._clip_stack.append(self.clip)
        self.clip = (x, y, w, h)

    def restore_clip(self):
        self.clip = self._clip_stack.pop()

    def set(self, x, y, color):
        cx, cy, cw, ch = self.clip
        if not (cx <= x < cx + cw and cy <= y < cy + ch):
            return
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i:i + 3] = bytes(color)

    def fill_rect(self, x, y, w, h, color):
        cx, cy, cw, ch = self.clip
        x0 = max(0, x, cx)
        y0 = max(0, y, cy)
        x1 = min(self.w, x + w, cx + cw)
        y1 = min(self.h, y + h, cy + ch)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x, y, w, color, thick=1):
        self.fill_rect(x, y, w, thick, color)

    def vline(self, x, y, h, color, thick=1):
        self.fill_rect(x, y, thick, h, color)

    def rect(self, x, y, w, h, color, thick=1):
        self.hline(x, y, w, color, thick)
        self.hline(x, y + h - thick, w, color, thick)
        self.vline(x, y, h, color, thick)
        self.vline(x + w - thick, y, h, color, thick)

    def line(self, x0, y0, x1, y1, color):
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def disc(self, cx, cy, r, color):
        for yy in range(cy - r, cy + r + 1):
            dx = int((r * r - (yy - cy) ** 2) ** 0.5) if abs(yy - cy) <= r else -1
            if dx >= 0:
                self.fill_rect(cx - dx, yy, 2 * dx + 1, 1, color)

    def ellipse(self, cx, cy, rx, ry, color):
        for yy in range(cy - ry, cy + ry + 1):
            t = 1.0 - ((yy - cy) / ry) ** 2
            if t < 0:
                continue
            dx = int(rx * (t ** 0.5))
            self.fill_rect(cx - dx, yy, 2 * dx + 1, 1, color)

    def triangle(self, ax, ay, bx, by, cx, cy, color):
        xs = sorted(((ax, ay), (bx, by), (cx, cy)), key=lambda p: p[1])
        (x0, y0), (x1, y1), (x2, y2) = xs
        if y0 == y2:
            return
        for y in range(y0, y2 + 1):
            if y < y1:
                xa = x0 + (x1 - x0) * (y - y0) / (y1 - y0) if y1 != y0 else x0
            else:
                xa = x1 + (x2 - x1) * (y - y1) / (y2 - y1) if y2 != y1 else x1
            xb = x0 + (x2 - x0) * (y - y0) / (y2 - y0)
            lo, hi = sorted((int(xa), int(xb)))
            self.fill_rect(lo, y, hi - lo + 1, 1, color)

    def char(self, x, y, ch, scale, color):
        glyph = FONT.get(ch, FONT[" "])
        for r, row in enumerate(glyph):
            for c, bit in enumerate(row):
                if bit == "1":
                    self.fill_rect(x + c * scale, y + r * scale, scale, scale, color)

    def text(self, x, y, s, scale, color):
        # The bitmap font holds capitals only; render everything
        # in capitals, as a newspaper front page does.
        cx = x
        for ch in s.upper():
            self.char(cx, y, ch, scale, color)
            cx += 6 * scale
        return cx

    def text_centered(self, cx, y, s, scale, color):
        self.text(cx - text_width(s, scale) // 2, y, s, scale, color)

    def text_right(self, x, y, s, scale, color):
        self.text(x - text_width(s, scale), y, s, scale, color)

# ---------------------------------------------------------------- scenes

def draw_rocket_panel(c, x, y, w, h):
    """Night sky, Earth arc below, a rocket climbing with flame."""
    c.set_clip(x, y, w, h)
    c.fill_rect(x, y, w, h, SKY)
    c.fill_rect(x, y + h // 3, w, h // 3, SKY2)
    c.fill_rect(x, y + 2 * h // 3, w, h // 3, SKY3)
    # Fixed-seed stars: a tiny LCG, same stars on every run.
    seed = 20261125
    for _ in range(46):
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        sx = x + 6 + seed % (w - 12)
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        sy = y + 4 + seed % (h // 2)
        c.set(sx, sy, WHITE)
        if seed % 5 == 0:
            c.set(sx + 1, sy, WHITE)
    # Moon.
    c.disc(x + w - 66, y + 34, 16, LIGHTGREY)
    c.disc(x + w - 72, y + 30, 4, GREY)
    c.disc(x + w - 58, y + 40, 3, GREY)
    # Earth arc rising from the bottom of the panel.
    c.ellipse(x + w // 2, y + h + 150, 320, 190, EARTH)
    c.ellipse(x + w // 2 - 130, y + h + 96, 90, 26, GREEN)
    c.ellipse(x + w // 2 + 150, y + h + 110, 70, 20, GREEN)
    c.fill_rect(x, y + h - 6, w, 6, BLUE)
    # Rocket, nose up, centre-left of the panel.
    rx, ry = x + w // 2 - 90, y + 42
    c.fill_rect(rx, ry + 26, 34, 96, WHITE)               # body
    c.triangle(rx, ry + 26, rx + 34, ry + 26, rx + 17, ry, RED)  # nose
    c.fill_rect(rx, ry + 58, 34, 8, RED)                  # band
    c.disc(rx + 17, ry + 84, 7, SKY)                      # window
    c.disc(rx + 17, ry + 84, 4, WHITE)
    c.triangle(rx, ry + 96, rx - 16, ry + 130, rx, ry + 122, RED)   # fin L
    c.triangle(rx + 34, ry + 96, rx + 50, ry + 130, rx + 34, ry + 122, RED)  # fin R
    # Flame and smoke.
    c.triangle(rx + 4, ry + 122, rx + 30, ry + 122, rx + 17, ry + 168, ORANGE)
    c.triangle(rx + 10, ry + 122, rx + 24, ry + 122, rx + 17, ry + 150, YELLOW)
    c.disc(rx - 8, ry + 178, 16, LIGHTGREY)
    c.disc(rx + 42, ry + 182, 18, LIGHTGREY)
    c.disc(rx + 17, ry + 192, 20, GREY)
    # A small satellite drifting top-right.
    sx, sy = x + w - 150, y + 96
    c.fill_rect(sx, sy, 26, 10, GOLD)
    c.fill_rect(sx - 18, sy + 2, 16, 6, BLUE)
    c.fill_rect(sx + 28, sy + 2, 16, 6, BLUE)
    c.restore_clip()


def draw_islands(c, x, y, w, h):
    """Two Pacific islands, sea, sun and flags."""
    c.fill_rect(x, y, w, h, (198, 226, 232))
    c.disc(x + w - 40, y + 22, 14, YELLOW)
    c.ellipse(x + 90, y + h - 18, 120, 34, GREEN)
    c.ellipse(x + w - 90, y + h - 10, 90, 26, GREEN)
    c.fill_rect(x, y + h - 26, w, 4, SEA)
    c.fill_rect(x + 30, y + h - 44, w - 60, 3, SEA)
    # Flagpoles with small flags on each island.
    for fx, fy, col in ((x + 70, y + h - 52, RED), (x + w - 100, y + h - 40, BLUE)):
        c.vline(fx, fy, 34, INK, 2)
        c.fill_rect(fx + 2, fy, 20, 12, col)
        c.fill_rect(fx + 2, fy + 4, 20, 4, WHITE)
    # A small boat between them.
    bx, by = x + w // 2 - 10, y + h - 34
    c.triangle(bx, by, bx + 34, by, bx + 17, by + 10, BROWN)
    c.vline(bx + 17, by - 16, 16, INK, 2)
    c.triangle(bx + 19, by - 16, bx + 19, by - 2, bx + 32, by - 2, WHITE)


def draw_ship(c, x, y, w, h):
    c.fill_rect(x, y, w, h, (214, 232, 238))
    c.fill_rect(x, y + h - 22, w, 6, SEA)
    c.fill_rect(x + 16, y + h - 34, w - 32, 3, SEA)
    hx, hy = x + w // 2 - 52, y + h - 52
    c.fill_rect(hx, hy + 22, 96, 18, INK)                            # hull
    c.triangle(hx + 96, hy + 22, hx + 96, hy + 40, hx + 114, hy + 22, INK)  # bow
    c.fill_rect(hx + 26, hy, 52, 22, WHITE)                            # deck
    c.fill_rect(hx + 34, hy - 14, 20, 14, RED)                         # bridge
    c.vline(hx + 62, hy - 12, 12, INK, 3)                             # mast
    c.fill_rect(hx + 65, hy - 12, 18, 10, RED)                        # flag
    c.disc(x + 34, y + 18, 5, WHITE)
    c.disc(x + 52, y + 12, 4, WHITE)


def draw_tower(c, x, y, w, h):
    c.fill_rect(x, y, w, h, (232, 220, 196))
    tx = x + w // 2 - 14
    c.fill_rect(tx, y + 26, 28, h - 26, INK)                          # tower
    c.vline(tx + 13, y + 8, 18, INK, 3)                               # antenna
    for wy in range(y + 34, y + h - 8, 12):
        c.fill_rect(tx + 4, wy, 6, 6, YELLOW)
        c.fill_rect(tx + 18, wy, 6, 6, YELLOW)
    c.disc(x + 44, y + 20, 9, GREY)                                   # smoke
    c.disc(x + 58, y + 14, 7, LIGHTGREY)
    c.disc(x + 30, y + 28, 6, LIGHTGREY)
    c.disc(x + w - 46, y + 46, 6, GREY)


def draw_gavel(c, x, y, w, h):
    c.fill_rect(x, y, w, h, (226, 214, 186))
    gx, gy = x + w // 2 - 40, y + 18
    c.line(gx, gy + 26, gx + 80, gy + 2, BROWN)                       # handle
    c.line(gx, gy + 30, gx + 80, gy + 6, BROWN)
    c.fill_rect(gx + 8, gy, 34, 18, BROWN)                            # head
    c.fill_rect(gx + 8, gy + 2, 34, 4, GOLD)
    c.ellipse(x + w // 2, y + h - 16, 46, 10, DARK)                   # block
    c.ellipse(x + w // 2, y + h - 20, 46, 8, BROWN)


def draw_medal(c, x, y, w, h):
    c.fill_rect(x, y, w, h, (238, 230, 208))
    mx, my = x + w // 2, y + h // 2 + 6
    c.triangle(mx - 22, y + 4, mx - 4, y + 4, mx - 8, my - 16, RED)    # ribbon L
    c.triangle(mx + 22, y + 4, mx + 4, y + 4, mx + 8, my - 16, BLUE)   # ribbon R
    c.disc(mx, my, 24, GOLD)
    c.disc(mx, my, 19, YELLOW)
    # Star.
    c.triangle(mx, my - 13, mx - 4, my - 2, mx + 4, my - 2, RED)
    c.triangle(mx, my + 11, mx - 4, my + 1, mx + 4, my + 1, RED)
    c.triangle(mx - 12, my, mx - 2, my - 4, mx - 2, my + 4, RED)
    c.triangle(mx + 12, my, mx + 2, my - 4, mx + 2, my + 4, RED)


def draw_chip(c, x, y, w, h):
    c.fill_rect(x, y, w, h, (210, 220, 226))
    cx, cy = x + w // 2, y + h // 2
    for i in range(-2, 3):
        c.fill_rect(cx + i * 14 - 2, cy - 26, 4, 8, INK)
        c.fill_rect(cx + i * 14 - 2, cy + 18, 4, 8, INK)
        c.fill_rect(cx - 26, cy + i * 14 - 2, 8, 4, INK)
        c.fill_rect(cx + 18, cy + i * 14 - 2, 8, 4, INK)
    c.fill_rect(cx - 22, cy - 22, 44, 44, DARK)
    c.fill_rect(cx - 12, cy - 12, 24, 24, GOLD)
    c.fill_rect(cx - 5, cy - 5, 10, 10, DARK)


def draw_chart(c, x, y, w, h):
    c.fill_rect(x, y, w, h, (236, 228, 216))
    ox, oy = x + 24, y + h - 20
    c.hline(ox, oy, w - 44, INK, 2)
    c.vline(ox, y + 12, h - 32, INK, 2)
    pts = [(ox + 6, y + 22), (ox + 34, y + 30), (ox + 62, y + 26),
           (ox + 90, y + 40), (ox + 118, y + 38), (ox + 146, y + 54),
           (ox + 174, y + 50), (ox + 202, y + 66)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        c.line(ax, ay, bx, by, RED)
        c.line(ax, ay + 1, bx, by + 1, RED)
    for px, py in pts:
        c.disc(px, py, 3, RED)
    ex, ey = pts[-1]
    c.triangle(ex, ey, ex + 16, ey - 2, ex + 4, ey + 12, RED)


# ---------------------------------------------------------------- page

CARDS = [
    ("UKRAINE", draw_ship,
     "KYIV CONFIRMS SHIP STRIKE",
     "Zelenskiy says Ukraine hit a Russian cargo ship in the Gulf of Finland."),
    ("SAUDI ARABIA", draw_tower,
     "HOUTHI DRONE HITS RIYADH TOWER",
     "Eleven wounded in a strike on the capital's tallest tower, officials say."),
    ("FRANCE", draw_gavel,
     "SARKOZY ORDERED TO TRIAL",
     "The former president and his wife Carla Bruni face a corruption trial."),
    ("UNITED STATES", draw_medal,
     "GIULIANI WINS MEDAL OF FREEDOM",
     "Trump awards his former lawyer the Presidential Medal of Freedom."),
    ("TECHNOLOGY", draw_chip,
     "HUAWEI GUILTY IN US SECRETS TRIAL",
     "A US jury convicts the firm of stealing trade secrets."),
    ("MARKETS", draw_chart,
     "ASIAN TECH SHARES SLIDE",
     "AI-linked stocks fall after a Wall Street retreat rattles investors."),
]


def draw_card(c, x, y, w, kicker, scene, headline, body):
    scene(c, x, y, w, 64)
    c.text(x, y + 74, kicker, 2, RED)
    hl = wrap_words(headline, 26)
    by = y + 96
    for line in hl[:2]:
        c.text(x, by, line, 2, INK)
        by += 15
    bl = wrap_words(body, 26)
    by += 4
    for line in bl[:3]:
        c.text(x, by, line, 2, INK)
        by += 15


def render_page():
    c = Canvas(W, H, PAPER)
    c.rect(12, 12, W - 24, H - 24, INK, 3)
    # Masthead.
    c.text_centered(W // 2, 30, "TODAY'S WORLD", 9, INK)
    c.hline(24, 102, W - 48, INK, 2)
    c.text_centered(W // 2, 110, "WEDNESDAY, 25 NOVEMBER 2026", 3, RED)
    c.text_centered(W // 2, 138, "ONE DAY - ONE WORLD - ONE PAGE", 2, INK)
    c.hline(24, 160, W - 48, INK, 3)
    c.hline(24, 166, W - 48, INK, 1)
    # Lead story: Shenzhou-24.
    draw_rocket_panel(c, 24, 180, 596, 216)
    c.text(24, 408, "CHINA LOFTS SHENZHOU-24", 4, INK)
    c.text(24, 444, "A crew including Pakistan's first", 2, INK)
    c.text(24, 462, "astronaut heads for the Tiangong station.", 2, INK)
    # Right column: the Pacific pact.
    c.text(644, 180, "THE PACIFIC", 2, RED)
    c.text(644, 204, "SOLOMON ISLANDS", 3, INK)
    c.text(644, 228, "NAMES AUSTRALIA", 3, INK)
    c.text(644, 252, "TOP SECURITY", 3, INK)
    c.text(644, 276, "PARTNER", 3, INK)
    c.text(644, 308, "The two nations sign a pact", 2, INK)
    c.text(644, 326, "naming Australia the islands'", 2, INK)
    c.text(644, 344, "top security partner and", 2, INK)
    c.text(644, 362, "ruling out foreign bases.", 2, INK)
    draw_islands(c, 644, 388, 356, 92)
    # Section divider and grid.
    c.hline(24, 500, W - 48, INK, 2)
    c.text(24, 512, "THE DAY IN BRIEF", 3, INK)
    c.text_right(1000, 514, "SIX STORIES FROM AROUND THE WORLD", 2, RED)
    c.hline(24, 538, W - 48, INK, 1)
    col_x = (24, 356, 688)
    row_y = (550, 748)
    for i, (kicker, scene, headline, body) in enumerate(CARDS):
        draw_card(c, col_x[i % 3], row_y[i // 3], 312, kicker, scene, headline, body)
    # Ticker footer.
    c.hline(24, 946, W - 48, INK, 2)
    c.text(24, 958, "ALSO TODAY: SEOUL MINISTER QUITS - DHAKA WORKERS WIN 36% PAY RISE", 2, INK)
    c.text(24, 978, "NATO VOWS SPACE DEFENCE - UN COURT CONDEMNS MYANMAR - SIX MISSING IN PLANE CRASH", 2, INK)
    return c

# ---------------------------------------------------------------- PNG

def png_chunk(kind, data):
    out = struct.pack(">I", len(data)) + kind + data
    out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    return out


def encode_png(canvas):
    ihdr = struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0)
    raw = bytearray()
    for y in range(canvas.h):
        raw.append(0)
        raw += canvas.px[y * canvas.w * 3:(y + 1) * canvas.w * 3]
    idat = zlib.compress(bytes(raw), 6)
    return (b"\x89PNG\r\n\x1a\n" + png_chunk(b"IHDR", ihdr)
            + png_chunk(b"IDAT", idat) + png_chunk(b"IEND", b""))


def verify(data):
    """Read-back gate: the rendered bytes must match the pinned
    hash and byte count exactly. A mismatch fails loudly instead
    of writing a changed image."""
    digest = hashlib.sha256(data).hexdigest()
    if EXPECTED_SHA256 and digest != EXPECTED_SHA256:
        raise SystemExit("MISMATCH sha256 %s != pinned %s" % (digest, EXPECTED_SHA256))
    if EXPECTED_BYTES and len(data) != EXPECTED_BYTES:
        raise SystemExit("MISMATCH bytes %d != pinned %d" % (len(data), EXPECTED_BYTES))
    return digest


def main():
    canvas = render_page()
    data = encode_png(canvas)
    digest = verify(data)
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    os.makedirs(outdir, exist_ok=True)
    path = os.path.join(outdir, "entry.png")
    with open(path, "wb") as f:
        f.write(data)
    print("wrote %s (%d bytes, sha256 %s)" % (path, len(data), digest))


if __name__ == "__main__":
    main()
