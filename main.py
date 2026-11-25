#!/usr/bin/env python3
"""Draw a 1024x1024 newspaper front page summing up the world news of
Wednesday 25 November 2026.

Pure Python standard library, no network, no fonts on disk: text is drawn
with a small 5x7 bitmap font defined below, scaled up. The output is fully
deterministic: running the program twice writes identical bytes.

Writes entry.png to $MAKEFUN_OUTPUT_DIR (default /output).
"""

import os
import struct
import zlib

W, H = 1024, 1024

PAPER = (248, 243, 230)
CARD = (255, 253, 246)
INK = (20, 20, 20)
GREY = (96, 92, 82)
RED = (166, 25, 46)
NAVY = (22, 53, 95)
TEAL = (14, 107, 107)
GOLD = (176, 124, 16)
WHITE = (255, 255, 255)

# 5x7 bitmap font. Each glyph is 7 rows of 5 characters ('#' = ink).
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
    "-": ("00000", "00000", "00000", "01110", "00000", "00000", "00000"),
    "'": ("00100", "00100", "01000", "00000", "00000", "00000", "00000"),
    "!": ("00100", "00100", "00100", "00100", "00100", "00000", "00100"),
    "?": ("01110", "10001", "00001", "00110", "00100", "00000", "00100"),
    ":": ("00000", "01100", "00000", "00000", "00000", "01100", "00000"),
    ";": ("00000", "01100", "00000", "00000", "01100", "00100", "01000"),
    "%": ("11001", "11010", "00010", "00100", "01000", "01011", "10011"),
    "/": ("00001", "00010", "00010", "00100", "01000", "01000", "10000"),
    "(": ("00010", "00100", "01000", "01000", "01000", "00100", "00010"),
    ")": ("01000", "00100", "00010", "00010", "00010", "00100", "01000"),
    "+": ("00000", "00100", "00100", "11111", "00100", "00100", "00000"),
    "&": ("01100", "10010", "10100", "01000", "10101", "10010", "01101"),
    "$": ("00100", "01111", "10100", "01110", "00101", "11110", "00100"),
    "#": ("01010", "01010", "11111", "01010", "11111", "01010", "01010"),
    "=": ("00000", "00000", "11111", "00000", "11111", "00000", "00000"),
    '"': ("01010", "01010", "00000", "00000", "00000", "00000", "00000"),
    "*": ("00000", "10101", "01110", "10101", "00000", "00000", "00000"),
    "•": ("00000", "00100", "01110", "01110", "01110", "00100", "00000"),
}

# --- image buffer -----------------------------------------------------------

row = bytes(PAPER) * W
buf = bytearray(row * H)


def fill_rect(x, y, w, h, color):
    """Fill an axis-aligned rectangle (clipped to the canvas)."""
    x0 = max(0, x)
    y0 = max(0, y)
    x1 = min(W, x + w)
    y1 = min(H, y + h)
    if x1 <= x0 or y1 <= y0:
        return
    px = bytes(color)
    line = px * (x1 - x0)
    for yy in range(y0, y1):
        base = (yy * W + x0) * 3
        buf[base:base + len(line)] = line


def normalise(text):
    return (
        text.upper()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("—", "-")
        .replace("–", "-")
    )


def text_width(text, scale):
    return len(normalise(text)) * 6 * scale


def draw_text(x, y, text, scale, color, align="left"):
    """Draw one line of text. align: left | center | right (x = anchor)."""
    s = normalise(text)
    if align == "center":
        x -= text_width(s, scale) // 2
    elif align == "right":
        x -= text_width(s, scale)
    for ci, ch in enumerate(s):
        glyph = FONT.get(ch, FONT[" "])
        cx = x + ci * 6 * scale
        for r in range(7):
            bits = glyph[r]
            for c in range(5):
                if bits[c] == "1":
                    fill_rect(cx + c * scale, y + r * scale, scale, scale, color)


def wrap(text, max_px, scale):
    """Greedy word wrap; returns a list of lines fitting max_px."""
    max_chars = max(1, max_px // (6 * scale))
    lines = []
    for paragraph in normalise(text).split("\n"):
        words = paragraph.split(" ")
        cur = ""
        for word in words:
            trial = word if not cur else cur + " " + word
            if len(trial) <= max_chars:
                cur = trial
            else:
                if cur:
                    lines.append(cur)
                # long word: hard-split it
                while len(word) > max_chars:
                    lines.append(word[:max_chars])
                    word = word[max_chars:]
                cur = word
        if cur:
            lines.append(cur)
    return lines


def draw_block(x, y, text, max_px, scale, color, line_h):
    """Draw wrapped text; returns the y just below the last line."""
    for i, line in enumerate(wrap(text, max_px, scale)):
        draw_text(x, y + i * line_h, line, scale, color)
    return y + len(wrap(text, max_px, scale)) * line_h


# --- page -------------------------------------------------------------------

M = 28                      # outer margin
CW = W - 2 * M              # content width: 968


def draw_page():
    # Masthead
    draw_text(W // 2, 30, "THE WORLD TODAY", 8, INK, align="center")
    fill_rect(M, 96, CW, 2, INK)
    draw_text(W // 2, 108, "WEDNESDAY, 25 NOVEMBER 2026", 3, INK, align="center")
    fill_rect(M, 134, CW, 6, RED)

    # Lead story: ICJ genocide verdict
    draw_text(M, 152, "LEAD  •  THE HAGUE  •  WORLD COURT", 2, RED)
    draw_block(M, 176, "ICJ: MYANMAR GUILTY OF GENOCIDE AGAINST ROHINGYA",
               CW, 5, INK, 36)
    draw_block(M, 256,
               "The World Court rules 9-6 - the first verdict ever finding a "
               "state guilty of genocide. A landmark judgment for the "
               "Rohingya people.",
               CW, 3, GREY, 22)
    fill_rect(M, 322, CW, 2, INK)

    # Six news panels, 2 columns x 3 rows
    panels = [
        ("UKRAINE WAR", RED,
         "KYIV HITS RUSSIAN SHIP IN GULF OF FINLAND",
         "Zelenskiy confirms drone strike on a cargo ship. Sea drones sink "
         "the corvette Merkury off Benghazi, Libya."),
        ("CLIMATE", TEAL,
         "COP31 IN ANTALYA COLLAPSES",
         "No fossil-fuel deal as 90+ nations reject the draft text. Talks "
         "end with no agreement."),
        ("SPACE", NAVY,
         "NATO VOWS TO DEFEND SPACE",
         "Allies pledge protection as reports say Russia may launch a "
         "nuclear-armed satellite within 60 days."),
        ("MIDDLE EAST", RED,
         "HOUTHIS HIT RIYADH'S TALLEST TOWER",
         "Missile strike wounds 11 in the Saudi capital. Israel airstrike "
         "kills a Hamas official in Gaza."),
        ("TECH", NAVY,
         "MICROSOFT DECLARES CODE RED",
         "Historic global outage hits services worldwide. Huawei found "
         "guilty of trade-secret theft."),
        ("ASIA", TEAL,
         "CHINA LAUNCHES SHENZHOU-24",
         "Crew heads to Tiangong with the first Pakistani astronaut. "
         "S. Korea minister quits over exam fraud."),
    ]
    pw, ph, gap = 477, 168, 14
    y0 = 338
    for i, (tag, color, head, body) in enumerate(panels):
        px = M + (i % 2) * (pw + gap)
        py = y0 + (i // 2) * (ph + gap)
        fill_rect(px, py, pw, ph, CARD)
        fill_rect(px, py, pw, 10, color)
        # border
        fill_rect(px, py, pw, 2, INK)
        fill_rect(px, py + ph - 2, pw, 2, INK)
        fill_rect(px, py, 2, ph, INK)
        fill_rect(px + pw - 2, py, 2, ph, INK)
        draw_text(px + 16, py + 22, tag, 2, color)
        draw_block(px + 16, py + 48, head, pw - 32, 3, INK, 24)
        draw_block(px + 16, py + 104, body, pw - 32, 2, GREY, 16)

    # Bottom strip: also today
    sy = 884
    fill_rect(M, sy, CW, 112, NAVY)
    draw_text(M + 16, sy + 12, "ALSO TODAY", 2, GOLD)
    draw_block(M + 16, sy + 38,
               "GTA 6 draws 39M PS5 players in 4 days  •  Nepal quake 5.6  •  "
               "Israel airstrike kills Hamas official in Gaza  •  Huawei "
               "guilty of trade-secret theft  •  S. Korea education minister "
               "resigns over exam cheating",
               CW - 32, 2, WHITE, 17)


def write_png(path):
    raw = b"".join(
        b"\x00" + bytes(buf[y * W * 3:(y + 1) * W * 3]) for y in range(H)
    )

    def chunk(kind, data):
        out = struct.pack(">I", len(data)) + kind + data
        return out + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "wb") as f:
        f.write(png)


def main():
    draw_page()
    outdir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    write_png(os.path.join(outdir, "entry.png"))


if __name__ == "__main__":
    main()
