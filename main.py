#!/usr/bin/env python3
"""The Monday Ledger -- sum up 23 November 2026 world news in one image.

A 1024x1024 newspaper front page drawn with the Python standard library
only. No network, no timestamps, no randomness: two runs produce
byte-identical PNG files. The font below is a 5x7 bitmap font designed
for this entry, the canvas and PNG encoder are written from scratch.

Run:  mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""
import os
import struct
import zlib
from pathlib import Path

W = H = 1024

PAPER = (247, 243, 234)
INK = (20, 20, 20)
RED = (163, 22, 33)
BLUE = (29, 78, 137)
GREY = (110, 108, 100)
LIGHT = (232, 227, 214)
SEA = (178, 205, 224)
LAND = (222, 205, 165)

# ---------------------------------------------------------------- font ----
# A 5x7 bitmap font, designed glyph by glyph for this entry. Each glyph is
# a tuple of 7 rows; "#" is ink, " " is blank. Narrow glyphs (I, l, 1, i,
# punctuation, space) are 3 columns wide so lines of small text fit the
# column; all other glyphs are 5 columns wide. Rows are 0-based from the
# top; lowercase letters sit on the baseline (row 6), ascenders reach row 0.
GLYPHS = {
    "A": (" ### ", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "B": ("#### ", "#   #", "#   #", "#### ", "#   #", "#   #", "#### "),
    "C": (" ####", "#    ", "#    ", "#    ", "#    ", "#    ", " ####"),
    "D": ("#### ", "#   #", "#   #", "#   #", "#   #", "#   #", "#### "),
    "E": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#####"),
    "F": ("#####", "#    ", "#    ", "#### ", "#    ", "#    ", "#    "),
    "G": (" ####", "#    ", "#    ", "#  ##", "#   #", "#   #", " ### "),
    "H": ("#   #", "#   #", "#   #", "#####", "#   #", "#   #", "#   #"),
    "I": ("###", " # ", " # ", " # ", " # ", " # ", "###"),
    "J": ("  ###", "   # ", "   # ", "   # ", "   # ", "#  # ", " ##  "),
    "K": ("#   #", "#  # ", "# #  ", "##   ", "# #  ", "#  # ", "#   #"),
    "L": ("#  ", "#  ", "#  ", "#  ", "#  ", "#  ", "###"),
    "M": ("#   #", "## ##", "# # #", "# # #", "#   #", "#   #", "#   #"),
    "N": ("#   #", "##  #", "# # #", "#  ##", "#   #", "#   #", "#   #"),
    "O": (" ### ", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "P": ("#### ", "#   #", "#   #", "#### ", "#    ", "#    ", "#    "),
    "Q": (" ### ", "#   #", "#   #", "#   #", "# # #", "#  # ", " ## #"),
    "R": ("#### ", "#   #", "#   #", "#### ", "# #  ", "#  # ", "#   #"),
    "S": (" ####", "#    ", "#    ", " ### ", "    #", "    #", "#### "),
    "T": ("#####", "  #  ", "  #  ", "  #  ", "  #  ", "  #  ", "  #  "),
    "U": ("#   #", "#   #", "#   #", "#   #", "#   #", "#   #", " ### "),
    "V": ("#   #", "#   #", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "W": ("#   #", "#   #", "#   #", "# # #", "# # #", "## ##", "#   #"),
    "X": ("#   #", "#   #", " # # ", "  #  ", " # # ", "#   #", "#   #"),
    "Y": ("#   #", "#   #", " # # ", "  #  ", "  #  ", "  #  ", "  #  "),
    "Z": ("#####", "    #", "   # ", "  #  ", " #   ", "#    ", "#####"),
    "a": ("     ", "     ", " ### ", "    #", " ####", "#   #", " ####"),
    "b": ("#    ", "#    ", "#### ", "#   #", "#   #", "#   #", "#### "),
    "c": ("     ", "     ", " ####", "#    ", "#    ", "#    ", " ####"),
    "d": ("    #", "    #", " ####", "#   #", "#   #", "#   #", " ####"),
    "e": ("     ", "     ", " ### ", "#   #", "#####", "#    ", " ### "),
    "f": ("  ## ", " #   ", " #   ", "#### ", " #   ", " #   ", " #   "),
    "g": ("     ", " ####", "#   #", "#   #", " ####", "    #", " ### "),
    "h": ("#    ", "#    ", "#### ", "#   #", "#   #", "#   #", "#   #"),
    "i": ("   ", " # ", "   ", "## ", " # ", " # ", "###"),
    "j": ("   ", "  #", "   ", "  #", "  #", "# #", " # "),
    "k": ("#    ", "#    ", "#  # ", "# #  ", "##   ", "# #  ", "#  # "),
    "l": (" # ", " # ", " # ", " # ", " # ", " # ", " # "),
    "m": ("     ", "     ", "## ##", "# # #", "# # #", "# # #", "# # #"),
    "n": ("     ", "     ", "#### ", "#   #", "#   #", "#   #", "#   #"),
    "o": ("     ", "     ", " ### ", "#   #", "#   #", "#   #", " ### "),
    "p": ("     ", "     ", "#### ", "#   #", "#   #", "#### ", "#    "),
    "q": ("     ", "     ", " ####", "#   #", "#   #", " ####", "    #"),
    "r": ("     ", "     ", "# ## ", "##  #", "#    ", "#    ", "#    "),
    "s": ("     ", "     ", " ####", "#    ", " ### ", "    #", "#### "),
    "t": (" #   ", " #   ", "#### ", " #   ", " #   ", " #   ", "  #  "),
    "u": ("     ", "     ", "#   #", "#   #", "#   #", "#   #", " ####"),
    "v": ("     ", "     ", "#   #", "#   #", "#   #", " # # ", "  #  "),
    "w": ("     ", "     ", "#   #", "#   #", "# # #", "# # #", " # # "),
    "x": ("     ", "     ", "#   #", " # # ", "  #  ", " # # ", "#   #"),
    "y": ("     ", "     ", "#   #", "#   #", "#   #", " ####", "    #"),
    "z": ("     ", "     ", "#####", "   # ", "  #  ", " #   ", "#####"),
    "0": (" ### ", "#   #", "#  ##", "# # #", "##  #", "#   #", " ### "),
    "1": (" # ", "## ", " # ", " # ", " # ", " # ", "###"),
    "2": (" ### ", "#   #", "    #", "   # ", "  #  ", " #   ", "#####"),
    "3": ("#### ", "    #", "    #", " ### ", "    #", "    #", "#### "),
    "4": ("   # ", "  ## ", " # # ", "#  # ", "#####", "   # ", "   # "),
    "5": ("#####", "#    ", "#### ", "    #", "    #", "#   #", " ### "),
    "6": (" ### ", "#    ", "#    ", "#### ", "#   #", "#   #", " ### "),
    "7": ("#####", "    #", "   # ", "   # ", "  #  ", "  #  ", "  #  "),
    "8": (" ### ", "#   #", "#   #", " ### ", "#   #", "#   #", " ### "),
    "9": (" ### ", "#   #", "#   #", " ####", "    #", "    #", " ### "),
    " ": ("   ", "   ", "   ", "   ", "   ", "   ", "   "),
    ".": ("   ", "   ", "   ", "   ", "   ", "   ", " # "),
    ",": ("   ", "   ", "   ", "   ", "   ", " # ", "#  "),
    "-": ("   ", "   ", "   ", "###", "   ", "   ", "   "),
    "/": ("   #", "   #", "  # ", "  # ", " #  ", " #  ", "#   "),
    "|": (" # ", " # ", " # ", " # ", " # ", " # ", " # "),
    ":": ("   ", " # ", "   ", "   ", "   ", " # ", "   "),
    ";": ("   ", " # ", "   ", "   ", "   ", " # ", "#  "),
    "!": (" # ", " # ", " # ", " # ", " # ", "   ", " # "),
    "'": (" # ", " # ", "   ", "   ", "   ", "   ", "   "),
    "(": ("  #", " # ", " # ", " # ", " # ", " # ", "  #"),
    ")": ("#  ", " # ", " # ", " # ", " # ", " # ", "#  "),
    "%": ("##  #", "## # ", "   # ", "  #  ", " #   ", "# ## ", "#  ##"),
    "?": (" ### ", "#   #", "    #", "   # ", "  #  ", "     ", "  #  "),
    "&": (" ### ", "#   #", "# #  ", " #   ", "# # #", "#  # ", " ## #"),
}


def glyph_width(ch):
    return len(GLYPHS[ch][0])


def text_width(text, scale, tracking):
    """Width in pixels of text rendered at scale with tracking px between glyphs."""
    if not text:
        return 0
    total = 0
    for ch in text:
        if ch not in GLYPHS:
            raise ValueError("no glyph for %r" % ch)
        total += glyph_width(ch) * scale + tracking
    return total - tracking


def wrap_text(text, scale, tracking, max_w):
    """Greedy word wrap using the font's own metrics; returns a list of lines."""
    lines = []
    cur = ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if text_width(trial, scale, tracking) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


# -------------------------------------------------------------- canvas ----
class Canvas:
    def __init__(self, w, h, bg):
        self.w = w
        self.h = h
        self.px = bytearray(bytes(bg) * (w * h))

    def set_pixel(self, x, y, color):
        if 0 <= x < self.w and 0 <= y < self.h:
            i = (y * self.w + x) * 3
            self.px[i] = color[0]
            self.px[i + 1] = color[1]
            self.px[i + 2] = color[2]

    def fill_rect(self, x, y, w, h, color):
        x0 = max(0, x)
        y0 = max(0, y)
        x1 = min(self.w, x + w)
        y1 = min(self.h, y + h)
        if x1 <= x0 or y1 <= y0:
            return
        row = bytes(color) * (x1 - x0)
        for yy in range(y0, y1):
            i = (yy * self.w + x0) * 3
            self.px[i:i + len(row)] = row

    def hline(self, x0, x1, y, color, thick=1):
        for t in range(thick):
            self.fill_rect(x0, y + t, x1 - x0, 1, color)

    def vline(self, x, y0, y1, color, thick=1):
        for t in range(thick):
            self.fill_rect(x + t, y0, 1, y1 - y0, color)

    def rect(self, x, y, w, h, color, thick=1):
        self.hline(x, x + w, y, color, thick)
        self.hline(x, x + w, y + h - thick, color, thick)
        self.vline(x, y, y + h, color, thick)
        self.vline(x + w - thick, y, y + h, color, thick)

    def line(self, x0, y0, x1, y1, color):
        # Bresenham line, for polygon edges.
        dx = abs(x1 - x0)
        dy = -abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            self.set_pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def fill_polygon(self, points, color):
        # Even-odd scanline fill.
        ys = [p[1] for p in points]
        for y in range(min(ys), max(ys) + 1):
            xs = []
            n = len(points)
            for i in range(n):
                x0, y0 = points[i]
                x1, y1 = points[(i + 1) % n]
                if (y0 <= y < y1) or (y1 <= y < y0):
                    x = x0 + (y - y0) * (x1 - x0) / (y1 - y0)
                    xs.append(x)
            xs.sort()
            for j in range(0, len(xs) - 1, 2):
                self.fill_rect(int(round(xs[j])), y,
                               int(round(xs[j + 1])) - int(round(xs[j])), 1, color)

    def polygon(self, points, fill, outline):
        self.fill_polygon(points, fill)
        n = len(points)
        for i in range(n):
            x0, y0 = points[i]
            x1, y1 = points[(i + 1) % n]
            self.line(x0, y0, x1, y1, outline)

    def fill_circle(self, cx, cy, r, color):
        for dy in range(-r, r + 1):
            dx = int((r * r - dy * dy) ** 0.5)
            self.fill_rect(cx - dx, cy + dy, 2 * dx + 1, 1, color)

    def circle(self, cx, cy, r, fill, outline):
        self.fill_circle(cx, cy, r, fill)
        # Ring outline: draw pixels at radius r.
        steps = 8 * r
        for s in range(steps):
            import math
            a = 2 * math.pi * s / steps
            self.set_pixel(cx + int(round(r * math.cos(a))),
                           cy + int(round(r * math.sin(a))), outline)

    # -- text ------------------------------------------------------
    def draw_text(self, x, y, text, scale, color, tracking=None):
        if tracking is None:
            tracking = scale
        cx = x
        for ch in text:
            glyph = GLYPHS[ch]
            gw = len(glyph[0])
            for r, row in enumerate(glyph):
                for c, p in enumerate(row):
                    if p == "#":
                        self.fill_rect(cx + c * scale, y + r * scale,
                                       scale, scale, color)
            cx += gw * scale + tracking
        return cx - tracking

    def draw_text_right(self, x_right, y, text, scale, color, tracking=None):
        if tracking is None:
            tracking = scale
        w = text_width(text, scale, tracking)
        return self.draw_text(x_right - w, y, text, scale, color, tracking)

    def draw_text_centred(self, cx, y, text, scale, color, tracking=None):
        if tracking is None:
            tracking = scale
        w = text_width(text, scale, tracking)
        return self.draw_text(cx - w // 2, y, text, scale, color, tracking)


# ---------------------------------------------------------------- png ------
def write_png(canvas, path):
    raw = bytearray()
    stride = canvas.w * 3
    for y in range(canvas.h):
        raw.append(0)  # filter: None
        raw += canvas.px[y * stride:(y + 1) * stride]
    compressed = zlib.compress(bytes(raw), 9)

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        out += struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
        return out

    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", canvas.w, canvas.h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", compressed)
    png += chunk(b"IEND", b"")
    Path(path).write_bytes(png)
    return len(png)


# -------------------------------------------------------------- layout ----
M = 30            # margin
X0, X1 = M, W - M


def build():
    cv = Canvas(W, H, PAPER)

    # ---- masthead ----
    mast = "THE MONDAY LEDGER"
    cv.draw_text_centred(W // 2, 30, mast, 9, INK)
    cv.hline(X0, X1, 108, INK, 3)
    cv.hline(X0, X1, 114, INK, 1)

    # ---- dateline bar ----
    cv.draw_text(X0, 122, "MONDAY 23 NOVEMBER 2026", 3, RED)
    cv.draw_text_right(X1, 122, "WORLD NEWS IN ONE PAGE", 3, INK)
    cv.hline(X0, X1, 156, INK, 2)

    # ---- LEAD: Gulf war reaches U.S. bases in Bahrain ----
    cv.draw_text(X0, 170, "GULF WAR REACHES", 5, INK)
    cv.draw_text(X0, 212, "U.S. BASES IN BAHRAIN", 5, INK)
    sub = wrap_text("Iran claims missile and drone strikes destroyed "
                    "two Patriot radars", 3, 3, 600)
    y = 254
    for ln in sub:
        cv.draw_text(X0, y, ln, 3, INK)
        y += 25
    body = wrap_text("Tehran says its Revolutionary Guard hit U.S. radars "
                     "at Al-Riffa and Awali air bases on Saturday night. "
                     "Bahrain says the attacks were intercepted; a fire "
                     "burned at an industrial site on Sitra and two people "
                     "were hurt.", 2, 1, 600)
    y += 12
    for ln in body:
        cv.draw_text(X0, y, ln, 2, INK, 1)
        y += 20
    y += 8
    cv.draw_text(X0, y, "SAT 21 NOV - REPORTED SUN 22 NOV", 2, GREY, 1)

    # ---- LEAD map: schematic Gulf ----
    gx, gy, gw, gh = 640, 170, 354, 250
    cv.fill_rect(gx, gy, gw, gh, SEA)
    cv.rect(gx, gy, gw, gh, INK, 2)
    cv.polygon([(660, 190), (790, 190), (775, 270), (700, 290), (655, 245)],
               LAND, INK)
    cv.polygon([(845, 325), (990, 325), (990, 405), (845, 405)], LAND, INK)
    cv.draw_text(668, 200, "IRAN", 2, INK)
    cv.draw_text(670, 300, "GULF", 2, BLUE)
    cv.draw_text(880, 305, "BAHRAIN", 2, INK)
    cv.draw_text(650, 345, "STRAIT OF HORMUZ", 2, BLUE)
    cv.circle(880, 355, 6, RED, INK)
    cv.circle(915, 370, 6, RED, INK)
    cv.draw_text(848, 385, "2 RADARS HIT", 2, RED)
    cv.draw_text(650, 402, "AL-RIFFA - AWALI", 2, INK)

    cv.hline(X0, X1, 480, INK, 2)

    # ---- HORMUZ band ----
    cv.draw_text(X0, 492, "HORMUZ UNDER FIRE", 4, INK)
    hbody = wrap_text("Attacks on shipping in and around the Strait of "
                      "Hormuz are at their highest level since the war "
                      "began: at least 22 reported in November.", 2, 1, 670)
    y = 530
    for ln in hbody:
        cv.draw_text(X0, y, ln, 2, INK, 1)
        y += 20
    y += 8
    cv.draw_text(X0, y, "SUN 22 NOV - CNN / UKMTO - THREE TANKERS HIT FRI-SAT",
                 2, GREY, 1)

    # mini bar chart: reported attacks + traffic
    cx, cy = 720, 498
    cv.fill_rect(cx, cy, 274, 118, LIGHT)
    cv.rect(cx, cy, 274, 118, INK, 1)
    cv.draw_text(cx + 10, cy + 8, "REPORTED ATTACKS", 2, INK)
    cv.fill_rect(cx + 20, cy + 62, 55, 20, BLUE)    # Oct: short bar
    cv.fill_rect(cx + 95, cy + 32, 55, 50, RED)     # Nov: tall bar
    cv.draw_text(cx + 16, cy + 88, "OCT 31", 2, INK)
    cv.draw_text(cx + 91, cy + 88, "NOV 22", 2, INK)
    cv.draw_text(cx + 170, cy + 37, "TRAFFIC", 2, INK)
    cv.draw_text(cx + 170, cy + 62, "-65%", 3, RED)

    cv.hline(X0, X1, 622, INK, 1)

    # ---- 2x2 grid ----
    gy0 = 634
    cw, ch = 470, 142
    stories = [
        ("GENEVA TALKS ON UKRAINE PEACE PLAN",
         "U.S., Ukrainian and European officials meet over Trump's "
         "28-point plan. Rubio calls the talks the most productive yet; "
         "the draft is cut to 19 points. Trump says it is not his final "
         "offer.",
         "MON 23 NOV"),
        ("COP31 COLLAPSES IN TURKEY",
         "The U.N. climate summit ends with no deal after the EU and "
         "Britain reject a pact that never mentions fossil fuels. The "
         "longest COP ever; the first failure since Copenhagen in 2009.",
         "SUN 22 NOV"),
        ("ISRAEL KILLS HEZBOLLAH CHIEF IN BEIRUT",
         "An Israeli airstrike in Beirut's Dahiyeh kills Hezbollah chief "
         "of staff Haytham Ali Tabatabai - the first strike on the "
         "capital in five months. Fears of a wider regional escalation "
         "grow.",
         "MON 23 NOV"),
        ("DOZENS MISSING AFTER FACTORY FIRE",
         "A fire at a factory in Indonesia leaves dozens of workers "
         "unaccounted for as rescue teams search the wreckage. The toll "
         "is still being counted.",
         "MON 23 NOV"),
    ]
    for i, (head, text, when) in enumerate(stories):
        gx = X0 + (i % 2) * (cw + 24)
        gy = gy0 + (i // 2) * (ch + 12)
        cv.rect(gx, gy, cw, ch, INK, 1)
        cv.fill_rect(gx, gy, cw, 30, INK)
        cv.draw_text(gx + 10, gy + 8, head, 2, PAPER)
        blines = wrap_text(text, 2, 1, cw - 20)
        by = gy + 38
        for ln in blines:
            cv.draw_text(gx + 10, by, ln, 2, INK, 1)
            by += 17
        cv.draw_text(gx + 10, gy + ch - 18, when, 2, GREY, 1)

    # ---- bottom strip: the day in numbers ----
    cv.fill_rect(X0, 940, X1 - X0, 56, INK)
    cv.draw_text(X0 + 12, 948, "THE DAY IN NUMBERS", 2, PAPER)
    cv.draw_text(X0, 970,
                 "22 attacks on shipping in November | 65% Hormuz traffic "
                 "lost | 19 points left in the Ukraine draft",
                 2, PAPER, 1)

    # ---- footer ----
    cv.draw_text_centred(W // 2, 1004,
                         "Sources: Reuters - CNN - Al Jazeera - AP - UKMTO "
                         "- Le Monde - The Monday Ledger, 23 November 2026",
                         1, GREY, 1)
    return cv


def main():
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    out_dir.mkdir(parents=True, exist_ok=True)
    cv = build()
    path = out_dir / "entry.png"
    size = write_png(cv, path)
    print("wrote %s (%d bytes)" % (path, size))
    print("masthead width: %d" % text_width("THE MONDAY LEDGER", 9, 9))
    print("numbers width: %d" % text_width(
        "22 attacks on shipping in November | 65% Hormuz traffic lost | "
        "19 points left in the Ukraine draft", 2, 1))
    for head, _, _ in [
            ("GENEVA TALKS ON UKRAINE PEACE PLAN", None, None),
            ("COP31 COLLAPSES IN TURKEY", None, None),
            ("ISRAEL KILLS HEZBOLLAH CHIEF IN BEIRUT", None, None),
            ("DOZENS MISSING AFTER FACTORY FIRE", None, None)]:
        print("header %r width: %d" % (head, text_width(head, 2, 2)))


if __name__ == "__main__":
    main()
