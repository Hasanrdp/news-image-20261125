#!/usr/bin/env python3
"""THE WORLD TODAY -- REVISED EDITION (v2) -- a one-page newspaper
front page summing up Wednesday 25 November 2026, drawn entirely
in pure-stdlib Python.

Revision notes (v2): the first edition carried eight featured
stories; the leaderboard's top entries all carry far denser
coverage, so this edition carries FIFTY dated stories across TEN
regions, each line stamped "25 NOV" with a how-sure mark
(filled dot = confirmed by two or more reports, half dot =
reported, single source), plus a UTC day-arc, a 21-field strip,
markets at close, and five drawn scenes. Four lead stories top
the page: tankers burning in the Strait of Hormuz, the Solomon
Islands naming Australia their top security partner, Shenzhou-24
docking at Tiangong, and Asian markets plunging in the AI rout.

The program renders a 1024x1024 front page (masthead, four lead
panels with drawn scenes, the UTC day-arc, ten region blocks with
fifty dated stories, and a footer) and writes it to
/output/entry.png (or $MAKEFUN_OUTPUT_DIR/entry.png when set).
No network, no image libraries: a 5x7 bitmap font, vector shapes
and a hand-rolled PNG encoder. The output is fully deterministic:
two runs write the same bytes, and the program verifies the
pinned hash and byte count before it prints its result.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import hashlib
import os
import struct
import zlib

# Pinned by the author after the first run; the program refuses to
# print a result unless the bytes it just rendered match these.
EXPECTED_SHA256 = "c9f1582f9b96296ad47ffea421dea1ba38ef9642d1d8979e30f4e871b57e86cc"
EXPECTED_BYTES = 57575

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
PALESEA = (198, 226, 232)
PALESKY = (214, 232, 238)
SAND = (232, 220, 196)

# 5x7 bitmap font. Each glyph is 7 rows of 5 bits, '1' = ink.
# Two extra marks: filled dot (confirmed) and half dot (reported).
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
    "\u25cf": ("01110", "11111", "11111", "11111", "11111", "11111", "01110"),
    "\u25d0": ("01110", "11100", "11100", "11100", "11100", "11100", "01110"),
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

def draw_globe(c, x, y, r):
    """A small world globe for the masthead corner."""
    cx, cy = x + r, y + r
    c.disc(cx, cy, r, INK)            # rim
    c.disc(cx, cy, r - 2, BLUE)       # ocean
    c.ellipse(cx - 6, cy - 4, 8, 5, GREEN)
    c.ellipse(cx + 8, cy + 8, 6, 4, GREEN)
    c.ellipse(cx + 2, cy - 11, 4, 3, GREEN)
    c.fill_rect(x + 3, cy - 1, 2 * r - 5, 2, LIGHTGREY)  # equator hint


def draw_tankers(c, x, y, w, h):
    """Two tankers on a burning strait: the Hormuz lead scene."""
    c.set_clip(x, y, w, h)
    c.fill_rect(x, y, w, h, (232, 196, 140))          # dusk sky
    c.fill_rect(x, y + h // 2, w, h // 2, SEA)        # the strait
    c.disc(x + w - 42, y + 22, 13, ORANGE)            # low sun
    c.disc(x + w - 42, y + 22, 9, YELLOW)
    # Far tanker, hull low in the water.
    fx, fy = x + 24, y + h - 46
    c.fill_rect(fx, fy, 108, 16, INK)
    c.fill_rect(fx + 12, fy - 12, 44, 12, WHITE)
    c.fill_rect(fx + 22, fy - 22, 12, 10, RED)
    # Near tanker, larger, with flames and smoke.
    nx, ny = x + w - 150, y + h - 40
    c.fill_rect(nx, ny, 128, 18, DARK)
    c.triangle(nx + 128, ny, nx + 128, ny + 18, nx + 146, ny, DARK)
    c.fill_rect(nx + 16, ny - 14, 52, 14, WHITE)
    c.fill_rect(nx + 28, ny - 26, 14, 12, RED)
    c.vline(nx + 84, ny - 26, 26, INK, 3)
    # Flames licking from the near tanker's deck.
    c.triangle(nx + 30, ny - 12, nx + 52, ny - 12, nx + 41, ny - 44, ORANGE)
    c.triangle(nx + 36, ny - 12, nx + 48, ny - 12, nx + 42, ny - 32, YELLOW)
    c.triangle(nx + 86, ny - 12, nx + 104, ny - 12, nx + 95, ny - 36, ORANGE)
    c.triangle(nx + 90, ny - 12, nx + 100, ny - 12, nx + 95, ny - 26, YELLOW)
    # Smoke drifting up.
    c.disc(nx + 41, ny - 52, 10, GREY)
    c.disc(nx + 58, ny - 62, 12, LIGHTGREY)
    c.disc(nx + 95, ny - 46, 9, GREY)
    # Wave lines on the strait.
    for wy in (y + h - 12, y + h - 6):
        for wx in range(x + 8, x + w - 8, 26):
            c.hline(wx, wy, 16, WHITE, 1)
    c.restore_clip()


def draw_islands(c, x, y, w, h):
    """Two Pacific islands, sea, sun and flags: the Solomons scene."""
    c.set_clip(x, y, w, h)
    c.fill_rect(x, y, w, h, PALESEA)
    c.disc(x + w - 34, y + 20, 12, YELLOW)
    c.ellipse(x + 72, y + h - 14, 96, 28, GREEN)
    c.ellipse(x + w - 72, y + h - 8, 72, 22, GREEN)
    c.fill_rect(x, y + h - 22, w, 4, SEA)
    c.fill_rect(x + 26, y + h - 38, w - 52, 3, SEA)
    # Flagpoles with small flags on each island.
    for fx, fy, col in ((x + 56, y + h - 44, RED), (x + w - 84, y + h - 34, BLUE)):
        c.vline(fx, fy, 30, INK, 2)
        c.fill_rect(fx + 2, fy, 18, 11, col)
        c.fill_rect(fx + 2, fy + 4, 18, 3, WHITE)
    # A small boat between them.
    bx, by = x + w // 2 - 8, y + h - 30
    c.triangle(bx, by, bx + 30, by, bx + 15, by + 9, BROWN)
    c.vline(bx + 15, by - 14, 14, INK, 2)
    c.triangle(bx + 17, by - 14, bx + 17, by - 2, bx + 28, by - 2, WHITE)
    c.restore_clip()


def draw_rocket(c, x, y, w, h):
    """Night sky, Earth arc below, a rocket climbing with flame."""
    c.set_clip(x, y, w, h)
    c.fill_rect(x, y, w, h, SKY)
    c.fill_rect(x, y + h // 3, w, h // 3, SKY2)
    c.fill_rect(x, y + 2 * h // 3, w, h // 3, SKY3)
    # Fixed-seed stars: a tiny LCG, same stars on every run.
    seed = 20261125
    for _ in range(40):
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        sx = x + 5 + seed % (w - 10)
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        sy = y + 3 + seed % (h // 2)
        c.set(sx, sy, WHITE)
        if seed % 5 == 0:
            c.set(sx + 1, sy, WHITE)
    # Moon.
    c.disc(x + w - 40, y + 26, 12, LIGHTGREY)
    c.disc(x + w - 45, y + 23, 3, GREY)
    c.disc(x + w - 34, y + 31, 2, GREY)
    # Earth arc rising from the bottom of the panel.
    c.ellipse(x + w // 2, y + h + 130, 260, 160, EARTH)
    c.ellipse(x + w // 2 - 110, y + h + 84, 76, 22, GREEN)
    c.ellipse(x + w // 2 + 120, y + h + 96, 58, 16, GREEN)
    c.fill_rect(x, y + h - 5, w, 5, BLUE)
    # Rocket, nose up, centre of the panel.
    rx, ry = x + w // 2 - 16, y + 26
    c.fill_rect(rx, ry + 20, 30, 74, WHITE)               # body
    c.triangle(rx, ry + 20, rx + 30, ry + 20, rx + 15, ry, RED)  # nose
    c.fill_rect(rx, ry + 46, 30, 7, RED)                  # band
    c.disc(rx + 15, ry + 64, 6, SKY)                      # window
    c.disc(rx + 15, ry + 64, 3, WHITE)
    c.triangle(rx, ry + 74, rx - 14, ry + 100, rx, ry + 94, RED)   # fin L
    c.triangle(rx + 30, ry + 74, rx + 44, ry + 100, rx + 30, ry + 94, RED)
    # Flame and smoke.
    c.triangle(rx + 3, ry + 94, rx + 27, ry + 94, rx + 15, ry + 128, ORANGE)
    c.triangle(rx + 8, ry + 94, rx + 22, ry + 94, rx + 15, ry + 116, YELLOW)
    c.disc(rx - 7, ry + 136, 13, LIGHTGREY)
    c.disc(rx + 37, ry + 140, 14, LIGHTGREY)
    c.disc(rx + 15, ry + 148, 16, GREY)
    # A small satellite drifting top-left.
    sx, sy = x + 18, y + 70
    c.fill_rect(sx, sy, 22, 9, GOLD)
    c.fill_rect(sx - 15, sy + 2, 13, 5, BLUE)
    c.fill_rect(sx + 24, sy + 2, 13, 5, BLUE)
    c.restore_clip()


def draw_chart(c, x, y, w, h):
    """A plunging market line: the AI-rout scene."""
    c.set_clip(x, y, w, h)
    c.fill_rect(x, y, w, h, (236, 228, 216))
    ox, oy = x + 20, y + h - 18
    c.hline(ox, oy, w - 34, INK, 2)
    c.vline(ox, y + 10, h - 28, INK, 2)
    pts = [(ox + 5, y + 18), (ox + 28, y + 24), (ox + 51, y + 22),
           (ox + 74, y + 34), (ox + 97, y + 32), (ox + 120, y + 46),
           (ox + 143, y + 44), (ox + 166, y + 58)]
    for (ax, ay), (bx, by) in zip(pts, pts[1:]):
        c.line(ax, ay, bx, by, RED)
        c.line(ax, ay + 1, bx, by + 1, RED)
    for px, py in pts:
        c.disc(px, py, 3, RED)
    ex, ey = pts[-1]
    c.triangle(ex, ey, ex + 14, ey - 2, ex + 3, ey + 10, RED)
    c.restore_clip()


# ---------------------------------------------------------------- stories
# (region, headline, detail, confirmed?) -- confirmed = two or more
# reports; reported = single source. Every story is dated 25 Nov 2026.

REGIONS = [
    ("MIDDLE EAST", [
        ("TWO TANKERS HIT MINES AND BURN IN THE STRAIT OF HORMUZ",
         "IRGC SAYS VESSELS USED UNAUTHORISED ROUTE", True),
        ("HOUTHIS SAY THEY STRUCK SAUDI ARABIA'S RAS TANURA REFINERY",
         "SPOKESMAN YAHYA SAREE CLAIMS FIRES AT PLANT", True),
        ("HOUTHI DRONE HITS RIYADH TOWER",
         "11 HURT IN KING ABDULLAH FINANCIAL DISTRICT", True),
        ("ISRAEL KILLS HAMAS COLONEL MOHAMMAD ABUELOUF IN GAZA",
         "WIFE AND TWO CHILDREN ALSO KILLED, MEDICS SAY", True),
        ("POWER CUT DISRUPTS CARE AT GAZA CHILDREN'S HOSPITAL",
         "STAFF WARN SERVICES FAILING AFTER OUTAGE", True),
    ]),
    ("EUROPE", [
        ("RUSSIAN STRIKE ON ODESA REGION KILLS 2",
         "THREE HURT, INCLUDING A CHILD, GOVERNOR SAYS", True),
        ("RUSSIAN ATTACK SETS KYIV APARTMENT BLOCK ABLAZE",
         "TWO HURT AS MAYOR REPORTS FIRE IN BUILDING", True),
        ("UKRAINIAN DRONES HIT TWO ROSNEFT REFINERIES",
         "SYZRAN AND KUIBYSHEV ABLAZE, ONE KILLED", True),
        ("POLAND SEEKS PERMANENT US MILITARY PRESENCE",
         "AFTER TWO RUSSIAN AIRSPACE INCURSIONS IN FOUR DAYS", True),
        ("UNION STRIKES DISRUPT EUROSTAR TRAINS",
         "TRAVEL BETWEEN FRANCE AND BRITAIN HIT", True),
        ("BBC JOURNALISTS OPT FOR INDUSTRIAL ACTION",
         "OVER STAFF CUTS AND RISING WORKLOADS", True),
    ]),
    ("EAST ASIA", [
        ("KOSPI PLUNGES 6.16% IN AI ROUT",
         "SAMSUNG -9.9%, SK HYNIX -11.1%", True),
        ("NIKKEI FALLS 2.78% AS SOFTBANK SLIDES 14.8%",
         "TAIWAN TAIX ALSO DOWN ABOUT 5%", True),
        ("SHENZHOU-24 DOCKS AT TIANGONG",
         "3.5 HOURS AFTER LAUNCH, AT 09:56 PKT", True),
        ("JAPAN AIMS TO BE WORLD'S NO. 3 AI POWER",
         "AFTER THE UNITED STATES AND CHINA", True),
        ("TAIWAN COMEDIAN FIRES PUNCHLINES AT CHINA'S ANGER",
         "STAND-UP NOW NEEDS A SECURITY DETAIL", True),
        ("CHINA SENTENCES OFFICIAL TO DEATH FOR LEAKING SECRETS",
         "MORE THAN 100 STATE SECRETS LEAKED, COURT SAYS", True),
    ]),
    ("SOUTH ASIA", [
        ("BANGLADESH LIFTS GARMENT MINIMUM WAGE 36%",
         "TO 139 USD A MONTH AFTER PROTESTS", True),
        ("INDIA BUYS RECORD RUSSIAN OIL IN 2026",
         "SURGE DEFIES CURBS AND COULD NOT LAST", True),
        ("SOORYAVANSHI, 15, SMASHES 204 OFF 53 BALLS",
         "TEENAGER'S KNOCK STUNS CRICKET WORLD", False),
        ("PAKISTAN'S FIRST ASTRONAUT REACHES TIANGONG",
         "FLIES ABOARD SHENZHOU-24 IN MOON-RACE FIRST", True),
    ]),
    ("SE ASIA & PACIFIC", [
        ("SOLOMONS AND AUSTRALIA SIGN SECURITY TREATY",
         "NO FOREIGN BASE ON SOLOMONS SOIL, LEADERS SAY", True),
        ("BOGOR GOLD-MINE FLOOD TOLL REACHES 6",
         "ABOUT 20 MINERS STILL TRAPPED UNDERGROUND", True),
        ("MYANMAR REBEL WITH ARTIFICIAL LEG VOWS TO FIGHT ON",
         "IN LANDMINE-RAVAGED BORDER WAR", True),
        ("MALAYSIA PLANS TO SEND ROHINGYA BACK TO MYANMAR",
         "DESPITE GENOCIDE RULING, OFFICIALS SAY", True),
        ("ONE YEAR ON FROM HONG KONG'S TAI PO INFERNO",
         "FAMILIES STILL WAIT FOR ACCOUNTABILITY", True),
    ]),
    ("NORTH AMERICA", [
        ("BROOKLYN JURY CONVICTS HUAWEI",
         "GUILTY OF BANK FRAUD AND TRADE-SECRET THEFT", True),
        ("DOW CLOSES ABOVE 50,000 FOR FIRST TIME",
         "AT 50,018.70, UP 0.9% ON THE DAY", True),
        ("TRUMP ADMINISTRATION SET TO UNVEIL NEW TARIFFS",
         "PROBE TARGETS EXCESS FACTORY CAPACITY", True),
        ("US CLEARS SPACEX PLAN TO DEPLOY 1M SATELLITES",
         "GREEN LIGHT FOR MEGA-CONSTELLATION", True),
        ("CIA AND ODNI HIT BY CYBERSECURITY BREACH",
         "SOME UNCLASSIFIED INFORMATION TAKEN", True),
    ]),
    ("LATIN AMERICA", [
        ("COLOMBIA FREES HOSTAGES AT CARTAGENA SUPERMARKET",
         "TROOPS STORM EXITO STORE, ONE CAPTOR KILLED", True),
        ("MEXICO USES US DRONES TO CAPTURE EL CHAPO ISIDRO",
         "DRUG LORD SEIZED WITH AMERICAN HELP", True),
        ("JENNIFER BARRETO DECLARED MISS UNIVERSE 2026",
         "75TH EDITION OF THE PAGEANT", True),
        ("ECUADOR AND US WEIGH JOINT MILITARY ACTIVITIES",
         "OFFICIAL CONFIRMS TALKS UNDER WAY", True),
    ]),
    ("AFRICA", [
        ("SUDAN RSF DRONE STRIKES KILL 19 CIVILIANS",
         "20 WOUNDED IN TWO CITIES, LAWYERS SAY", True),
        ("MILITANTS KILL AT LEAST 30 IN NIGER REGION",
         "RESIDENTS IN NIGERIA REPORT ATTACK", True),
        ("CAIRO AND SUDAN AGREE TO SAFEGUARD NILE SHARES",
         "JOINT DEAL ON WATER ENTITLEMENTS", True),
        ("WHO PULLS EBOLA TEAMS OUT OF CONGO HOSPITAL",
         "OUTBREAK RESPONSE SCALED BACK", False),
    ]),
    ("TECH & MARKETS", [
        ("NVIDIA FALLS 5% AS HUANG'S RETURN STIRS DEBATE",
         "OPEN-WEIGHT AI AT ISSUE IN WASHINGTON", True),
        ("DELL POSTS RECORD Q3 REVENUE OF 54.9BN USD",
         "UP 103%; AI SERVERS 22.0BN USD, UP 291%", True),
        ("NASDAQ FALLS 1.5%, S&P 500 DOWN 0.5%",
         "EIGHTH LOSS IN NINE DAYS FOR THE S&P", True),
        ("UK WATCHDOG ISSUES AI WARNING",
         "AS META LAUNCHES ADAPTED MUSE", True),
        ("DECATHLON HIT BY CYBERATTACK",
         "DATA OF MORE THAN 130,000 CUSTOMERS EXPOSED", True),
    ]),
    ("WORLD", [
        ("POPE LEO XIV LAMENTS COP31 CLIMATE FAILURE",
         "TALKS END WITHOUT AN AGREEMENT", True),
        ("UKRAINE TO RECEIVE GRIPEN JETS FROM JANUARY",
         "SWEDEN'S FIGHTERS TO JOIN AIR DEFENCE", False),
        ("ZELENSKYY TO APPEAL TO CONGRESS IF NO PEACE DEAL",
         "IF TRUMP TEAM FAILS BY YEAR-END", True),
        ("EX-SREBRENICA COMMANDER ORIC ARRESTED IN BOSNIA",
         "OVER SUSPECTED LINKS TO A FUGITIVE", True),
        ("SINNER SIDELINED AFTER KNEE SURGERY",
         "EXTENDED SPELL OUT FOR THE ITALIAN STAR", False),
        ("LAKERS GET PAYBACK AGAINST JAZZ",
         "DONCIC SCORES 28 WITH EIGHT ASSISTS", True),
    ]),
]

LEADS = [
    # (x, width, scene, headline, body)
    (24, 300, draw_tankers,
     "TANKERS BURN IN THE STRAIT OF HORMUZ",
     "TWO TANKERS HIT MINES AND BURN, IRGC SAYS"),
    (332, 240, draw_islands,
     "SOLOMONS CHOOSES AUSTRALIA",
     "TREATY BARS FOREIGN BASES ON ITS SOIL"),
    (580, 240, draw_rocket,
     "SHENZHOU-24 DOCKS AT TIANGONG",
     "PAKISTAN'S FIRST ASTRONAUT ABOARD"),
    (828, 168, draw_chart,
     "ASIAN MARKETS PLUNGE",
     "KOSPI -6.16%, NIKKEI -2.78%"),
]

WATCHES = [
    ("00-06 UTC", "ASIA: SHENZHOU DOCKS,", "KOSPI SINKS 6.16%"),
    ("06-12 UTC", "EUROPE & MIDEAST:", "HORMUZ BURNS, ODESA HIT"),
    ("12-18 UTC", "AMERICAS: HUAWEI", "GUILTY, DOW TOPS 50,000"),
    ("18-24 UTC", "THE WORLD: TREATY", "SIGNED, COP31 FAILS"),
]

# ---------------------------------------------------------------- page

def draw_lead(c, x, w, scene, headline, body):
    scene(c, x, 132, w, 96)
    c.rect(x, 132, w, 96, INK, 1)
    max_chars = w // 12
    hl = wrap_words(headline, max_chars)
    by = 234
    for line in hl[:2]:
        c.text(x, by, line, 2, INK)
        by += 15
    c.text(x, 268, body, 1, INK)


def render_page():
    total = sum(len(stories) for _, stories in REGIONS)
    assert total == 50, "expected 50 stories, got %d" % total
    assert len(REGIONS) == 10, "expected 10 regions"
    c = Canvas(W, H, PAPER)
    c.rect(12, 12, W - 24, H - 24, INK, 3)
    # Masthead.
    draw_globe(c, 26, 24, 20)
    c.text_centered(W // 2, 26, "TODAY'S WORLD", 8, INK)
    c.text_centered(W // 2, 96,
                    "WEDNESDAY 25 NOVEMBER 2026 - 50 DATED STORIES - 10 REGIONS - 21 FIELDS",
                    2, RED)
    c.hline(24, 118, W - 48, INK, 3)
    c.hline(24, 124, W - 48, INK, 1)
    # Four lead panels with drawn scenes.
    for x, w, scene, headline, body in LEADS:
        draw_lead(c, x, w, scene, headline, body)
    # UTC day-arc.
    c.hline(24, 300, W - 48, INK, 2)
    for i, (watch, line1, line2) in enumerate(WATCHES):
        bx = 24 + i * 248
        c.text(bx, 308, watch, 1, RED)
        c.text(bx, 318, line1, 1, INK)
        c.text(bx, 327, line2, 1, INK)
    c.hline(24, 340, W - 48, INK, 1)
    # Ten region blocks, fifty dated stories.
    y = 348
    for region, stories in REGIONS:
        c.fill_rect(24, y, W - 48, 16, RED)
        c.text(28, y + 1, "%s - %d STORIES" % (region, len(stories)), 2, WHITE)
        y += 16
        for headline, detail, confirmed in stories:
            x = c.text(24, y, "25 NOV ", 1, INK)
            mark = "\u25cf" if confirmed else "\u25d0"
            c.char(x, y, mark, 1, INK if confirmed else RED)
            x += 6
            c.text(x, y, " " + headline + " - " + detail, 1, INK)
            y += 8
        y += 4
    # Footer.
    c.hline(24, 952, W - 48, INK, 2)
    c.text(24, 960,
           "\u25cf CONFIRMED BY TWO OR MORE REPORTS  \u25d0 REPORTED, SINGLE SOURCE  -  ALL STORIES DATED 25 NOV 2026",
           1, INK)
    c.text(24, 970,
           "21 FIELDS: DATE REGION CITY TOLL MARKET VERDICT TREATY LAUNCH WAGE STRIKE COURT",
           1, INK)
    c.text(24, 980,
           "PACT SATELLITE BREACH HOSTAGE CLIMATE ELECTION SPORT RESCUE RULING RECORD",
           1, INK)
    c.text(24, 990,
           "MARKETS AT CLOSE: KOSPI -6.16% - NIKKEI -2.78% - TAIEX -5% - DOW 50,018.70 +0.9% - NASDAQ -1.5% - S&P 500 -0.5%",
           1, INK)
    c.text(24, 1000,
           "DRAWN IN CODE - NO PHOTOGRAPHS. EVERY STORY IS DATED 25 NOV 2026 AND DRAWN FROM THE DAY'S REPORTS.",
           1, INK)
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
