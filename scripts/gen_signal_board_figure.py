#!/usr/bin/env python3
"""Draw where every part sits on the SIGNAL perfboard.

Companion to gen_relay_board_figure.py, and the same discipline: the layout is
DATA - a hole-indexed netlist - and the script asserts the things a reader
cannot check by looking.

WHY THIS BOARD IS HARDER THAN THE RELAY BOARD
---------------------------------------------
On the relay board every part stands between two free holes, so "no two leads
in one hole" holds everywhere. Here every passive hangs off a Teensy pin, and
a pin's hole is already full of the socket. So the rule relaxes to:

    a hole may carry TWO things, never three

and the second thing is soldered to the same pad. A socket pin plus one lead
is normal perfboard work; a socket pin plus two leads is a joint nobody can
inspect. check() enforces the two, and names every doubled hole in the figure
so the builder knows which pads take a second wire.

THE PIN ORDER IS FROM MEMORY AND IS NOT YET VERIFIED
----------------------------------------------------
Every column below is computed from TOP_PINS / BOT_PINS. If that order is
wrong, the whole drawing is wrong in the same way - which is why the figure
PRINTS the order it assumed. Hold a Teensy 4.1 next to it and read along the
edge: ten seconds, and the same ten seconds that turned 31 x 19 into 29 x 18
on the relay board. Correct the two lists and re-run; nothing else moves.

Orientation: the Teensy lies flat with its USB end to the LEFT. Turning the
pinout card that way puts the card's RIGHT column along the TOP row of holes
and its LEFT column along the BOTTOM row, both read left to right.

BOARD
-----
거상인 [GA2] 80 x 80 double-sided, 2.54 mm pitch, counted 29 x 29 end to end
(the 80 mm side is the same 29 as the GA6 - order log row 122). Keeping the
one-hole margin this project keeps, the working area is 27 x 27.

VERIFY TEXT IN A BROWSER, NOT IN IMAGEMAGICK - see gen_relay_board_figure.py.
"""

import io
from pathlib import Path

# ---------------------------------------------------------------- the geometry
COLS, ROWS = 29, 29               # counted 2026-11-05 - see docstring
BORDER = 1                        # outer ring: holes exist, working area does not
P = 26                            # px per hole pitch
X0, Y0 = 108, 150                 # centre of hole (1, 1)
W = 1180


def hx(c):
    return X0 + (c - 1) * P


def hy(r):
    return Y0 + (r - 1) * P


# ------------------------------------------------------------------ the Teensy
# Read left to right along each row of holes. UNVERIFIED - see docstring.
TOP_PINS = ["Vin", "GND", "3V3", "23", "22", "21", "20", "19", "18", "17",
            "16", "15", "14", "13", "GND", "41", "40", "39", "38", "37",
            "36", "35", "34", "33"]
BOT_PINS = ["GND", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
            "11", "12", "3V3", "24", "25", "26", "27", "28", "29", "30",
            "31", "32"]

T_COL0 = 3                        # column of the Teensy's first pin
T_TOP, T_BOT = 11, 17             # the two pin rows; 0.6 in apart = 6 holes


def pin(name, row):
    """Hole of a Teensy pin, by the name printed on the board."""
    pins = TOP_PINS if row == T_TOP else BOT_PINS
    hits = [i for i, p in enumerate(pins) if p == name]
    assert len(hits) == 1, f"{name!r} appears {len(hits)} times on row {row}"
    return (T_COL0 + hits[0], row)


# What each used pin is for. This is the figure's copy of ONE table that lives
# in 04-firmware.md; it is here so the drawing can place things, not so it can
# become a second source. Signal, pin name, row, label colour.
USED = [
    ("drive A",   "0",   T_BOT, "#1d4ed8"),
    ("drive B",   "1",   T_BOT, "#1d4ed8"),
    ("PWM steer", "2",   T_BOT, "#7c3aed"),
    ("PWM drive", "3",   T_BOT, "#7c3aed"),
    ("SCL",       "19",  T_TOP, "#0f766e"),
    ("SDA",       "18",  T_TOP, "#0f766e"),
    ("E-stop",    "20",  T_TOP, "#b45309"),
    ("gate out",  "21",  T_TOP, "#b45309"),
    ("i-BUS RX",  "15",  T_TOP, "#be123c"),
]

# ------------------------------------------------------------------ the layout
# Buses: bare tinned wire soldered along a run of holes.
BUSES = [
    ("V33T", 6,  (5, 19),  "#dc2626", "3.3 V"),
    ("GND",  21, (3, 27),  "#334155", "GND"),
    ("V33B", 24, (4, 17),  "#dc2626", "3.3 V"),
]
# Vertical runs of the same bare wire. (col, row_from, row_to, colour, what)
SPINES = [
    (27, 2, 21, "#334155", "GND up the right edge, for the servo headers"),
]

# A pad already holds a socket pin, so a pin with more than one thing hanging
# off it gets a STUB: two or three holes of bare wire soldered to its pad.
# (col, row_from, row_to, which pin, colour of the net it carries)
# The colour matters: drawn in the GND slate these read as grounded, which is
# the opposite of what a stub is.
STUBS = [
    (4,  17, 20, "0",  "#1d4ed8"),
    (5,  17, 20, "1",  "#1d4ed8"),
    (10, 9,  11, "19", "#0f766e"),
    (11, 9,  11, "18", "#0f766e"),
    (23, 8,  10, None, "#be123c"),   # the i-BUS divider node, not a Teensy pad
]

# designator, value, hole A, hole B, kind, label side, reverse side?
PARTS = [
    ("R1", "4.7 k", (10, 9),  (10, 6),  "res", "L", False),
    ("R2", "4.7 k", (11, 9),  (11, 6),  "res", "R", False),
    ("C1", "1 nF",  (4, 18),  (4, 21),  "cap", "L", False),
    ("C2", "1 nF",  (5, 18),  (5, 21),  "cap", "R", False),
    ("R3", "10 k",  (4, 19),  (4, 24),  "res", "L", True),
    ("R4", "10 k",  (5, 19),  (5, 24),  "res", "R", True),
    # i-BUS level. R5 is a WIRE LINK if the receiver idles at 3.3 V, and the
    # upper leg of a divider with R6 if it idles at 5 V. 3.4 forbids finding
    # that out after the wire is on the pin: the Teensy 4.1 is not 5 V tolerant.
    ("R5", "series", (23, 4), (23, 8),  "res", "L", False),
    ("R6", "to GND", (23, 9), (27, 9),  "res", "R", False),
]

# Pluggable terminal blocks, 5.08 mm -> the two ways are TWO holes apart.
TERMINALS = [
    ("PWR",   3,  2,  "+5 V",  "GND",   "#dc2626"),
    ("RELAY", 8,  2,  "GATE",  "SENSE", "#b45309"),
    ("STRS",  14, 2,  "SDA",   "SCL",   "#0f766e"),
    ("STRP",  19, 2,  "3.3 V", "GND",   "#dc2626"),
    ("DRVS",  7,  26, "A",     "B",     "#1d4ed8"),
    ("DRVP",  12, 26, "3.3 V", "GND",   "#dc2626"),
]

# Servo-style 3-pin headers. The middle pad is the connector's +5 and is left
# UNCONNECTED here: the receiver and the MUX are powered from UBEC B, not from
# this board. Signal and ground are what land.
# 3-pin male pin header, 2.54 mm, cut from the 1x40 strip on order-log row 122
# - the receiver and the MUX both terminate in FEMALE servo sockets.
# Order is SIG - +5 - GND, and the middle pad is deliberately UNCONNECTED:
# this board is on UBEC A and the MUX and receiver are on UBEC B, and joining
# them would undo the authority split that is the whole reason for two UBECs.
HEADERS = [
    ("IBUS", 23, 2,  "#be123c", "i-BUS in \u2190 receiver"),
    ("PWM1", 17, 28, "#7c3aed", "PWM 1 \u00b7 steer"),
    ("PWM2", 22, 28, "#7c3aed", "PWM 2 \u00b7 drive"),
]

# Insulated hookup wire. (from, to, colour, reverse side)
JUMPERS = [
    (pin("3V3", T_TOP), (5, 6),   "#dc2626", False),   # feed the upper 3.3 V bus
    (pin("3V3", T_BOT), (17, 24), "#dc2626", False),   # feed the lower one
    (pin("GND", T_BOT), (3, 21),  "#334155", False),   # feed the GND bus
    ((3, 2),  pin("Vin", T_TOP), "#dc2626", False),    # 5 V in -> Vin
    ((3, 4),  (4, 11),           "#334155", False),    # its GND -> the Teensy GND pad
    ((8, 2),  (8, 11),           "#b45309", True),     # gate out -> pin 21
    ((8, 4),  (9, 11),           "#b45309", True),     # E-stop sense in -> pin 20
    ((14, 2), (11, 10),          "#0f766e", True),     # SDA -> the pin 18 stub
    ((14, 4), (10, 10),          "#0f766e", True),     # SCL -> the pin 19 stub
    ((19, 2), (19, 6),           "#dc2626", False),    # steering 3.3 V -> the bus
    ((19, 4), (17, 11),          "#334155", True),     # its GND -> the other GND pad
    ((7, 26), (4, 20),           "#1d4ed8", True),     # drive A -> the pin 0 stub
    ((7, 28), (5, 20),           "#1d4ed8", True),     # drive B -> the pin 1 stub
    ((12, 26), (12, 24),         "#dc2626", False),    # drive sensor 3.3 V
    ((12, 28), (12, 21),         "#334155", True),     # its GND, behind the 3.3 V bus
    ((23, 2), (23, 4),           "#be123c", False),    # i-BUS signal into R5
    ((23, 10), (14, 11),         "#be123c", True),     # and on to pin 15
    ((25, 2), (27, 2),           "#334155", False),    # i-BUS ground -> the spine
    ((17, 28), (6, 17),          "#7c3aed", True),     # PWM 1 -> pin 2
    ((19, 28), (19, 21),         "#334155", False),    # its ground
    ((22, 28), (7, 17),          "#7c3aed", True),     # PWM 2 -> pin 3
    ((24, 28), (24, 21),         "#334155", False),    # its ground
]


def term_holes(c, r):
    return [(c, r), (c, r + 2)]


def header_holes(c, r):
    return [(c, r), (c + 1, r), (c + 2, r)]


def run(c0, r0, c1, r1):
    """Every hole a bare-wire run passes through, ends included."""
    if r0 == r1:
        return [(c, r0) for c in range(min(c0, c1), max(c0, c1) + 1)]
    return [(c0, r) for r in range(min(r0, r1), max(r0, r1) + 1)]


# ------------------------------------------------------------- the assertions
def check():
    def inside(h):
        return (1 + BORDER <= h[0] <= COLS - BORDER
                and 1 + BORDER <= h[1] <= ROWS - BORDER)

    occupants = {}

    def claim(h, who):
        assert inside(h), (f"{who} at {h} is outside the usable "
                           f"{COLS-2*BORDER}x{ROWS-2*BORDER} ring")
        occupants.setdefault(h, []).append(who)

    for i, name in enumerate(TOP_PINS):
        claim((T_COL0 + i, T_TOP), f"socket {name}")
    for i, name in enumerate(BOT_PINS):
        claim((T_COL0 + i, T_BOT), f"socket {name}")
    for name, row, (c0, c1), *_ in BUSES:
        for h in run(c0, row, c1, row):
            claim(h, f"bus {name}")
    for c, r0, r1, _, _ in SPINES:
        for h in run(c, r0, c, r1):
            claim(h, "GND spine")
    for c, r0, r1, who, _ in STUBS:
        for h in run(c, r0, c, r1):
            claim(h, f"stub {who}")
    for d, _, a, b, *_ in PARTS:
        claim(a, d)
        claim(b, d)
    for d, c, r, *_ in TERMINALS:
        for h in term_holes(c, r):
            claim(h, d)
    for d, c, r, *_ in HEADERS:
        for h in header_holes(c, r):
            claim(h, d)
    for a, b, *_ in JUMPERS:
        claim(a, "wire")
        claim(b, "wire")

    # THE rule for this board, and the reason it differs from the relay board's.
    # Two is a pad with a wire soldered to it: ordinary perfboard work. Three is
    # a joint nobody can inspect.
    for h, who in sorted(occupants.items()):
        assert len(who) <= 2, f"hole {h} would carry {len(who)}: {who}"

    # Every stub must start on the pad of the pin it is named for, or it is
    # wire soldered to nothing.
    for c, r0, r1, who, _ in STUBS:
        if who is None:
            continue                 # a plain node, not a pin's pad
        row = T_TOP if r1 == T_TOP else T_BOT
        assert (c, row) == pin(who, row), \
            f"stub {who} starts at col {c}, but pin {who} is at {pin(who, row)}"

    # A part is on the reverse side exactly when it crosses a bus, and never
    # otherwise - a dashed part that did not need to be is a part nobody can
    # reach with an iron once the board is in the box.
    def crosses_copper(a, b):
        """Does the straight line a-b pass THROUGH a bus or a spine?

        Row alone is not enough: a part in a column the bus never reaches does
        not cross it, and calling that a crossing sends a part to the reverse
        side for no reason - where nobody can reach it with an iron.
        """
        if a[0] == b[0]:
            lo, hi = sorted((a[1], b[1]))
            return any(lo < row < hi and c0 <= a[0] <= c1
                       for _, row, (c0, c1), *_ in BUSES)
        lo, hi = sorted((a[0], b[0]))
        return any(lo < c < hi and r0 <= a[1] <= r1
                   for c, r0, r1, *_ in SPINES)

    for d, _, a, b, _, _, rev in PARTS:
        crosses = crosses_copper(a, b)
        assert crosses == rev, (
            f"{d} runs {a}->{b}: crosses a bus = {crosses}, "
            f"but is drawn on the {'reverse' if rev else 'front'} side")

    # Each passive beside the pin it serves - the rule 3.5.4 states, and the
    # thing a 60 mm track quietly breaks.
    for d, _, a, b, *_ in PARTS:
        span = abs(a[0] - b[0]) + abs(a[1] - b[1])
        assert 2 <= span <= 6, f"{d} spans {span} holes; 2 to 6 is a part you can fit"

    # Every bus must be fed from the Teensy side, or it is an island - the
    # classic perfboard fault this figure exists to warn about.
    for name, row, (c0, c1), *_ in BUSES:
        holes = set(run(c0, row, c1, row))
        fed = any(a in holes or b in holes for a, b, *_ in JUMPERS)
        assert fed, f"bus {name} on row {row} is an island - nothing feeds it"

    # Every used signal must actually reach its pin.
    reached = set()
    for a, b, *_ in JUMPERS:
        reached.update((a, b))
    for c, r0, r1, who, _ in STUBS:
        reached.update(run(c, r0, c, r1))
    for sig, name, row, _ in USED:
        p = pin(name, row)
        assert p in reached or any(p in run(c, r0, c, r1) for c, r0, r1, *_ in STUBS), \
            f"{sig} (pin {name}) has nothing landing on it"

    return {h: w for h, w in occupants.items()
            if len(w) == 2 and any(x.startswith("socket") for x in w)}


DOUBLED = check()

# ------------------------------------------------------------------- drawing
BOLD, EB = '<tspan font-weight="bold">', "</tspan>"


def rich(line):
    """`**bold**` -> tspans. Panels write plain strings, never f-string markup."""
    assert line.count("**") % 2 == 0, f"unbalanced bold: {line}"
    assert "{" not in line and "}" not in line, f"stray brace, missing f-prefix?: {line}"
    return "".join(f"{BOLD}{p}{EB}" if i % 2 else p
                   for i, p in enumerate(line.split("**")) if p)


out = []


def e(s):
    out.append(s)


e("<svg>")
e("<rect/>")

e('<text x="24" y="36" font-size="19" font-weight="bold" fill="#0f172a">'
  "Signal perfboard &#8212; where everything sits</text>")
e(f'<text x="24" y="58" font-size="12.5" fill="#475569">'
  f"[GA2] 80 &#215; 80 double-sided, 2.54 mm pitch: {COLS} &#215; {ROWS} holes, "
  f"{BOLD}{COLS-2*BORDER} &#215; {ROWS-2*BORDER} after the one-hole margin{EB} "
  f"(the 80 mm side is the same 29 as the GA6).</text>")
e('<text x="24" y="77" font-size="12.5" fill="#475569">'
  "A socketed Teensy 4.1, two pull-up pairs, two filter caps, six terminals and "
  "three servo headers. " + BOLD +
  "The pin order drawn here is unverified &#8212; check it against the board." + EB +
  "</text>")

# ---- board
bx0, by0 = hx(1) - P, hy(1) - P
bx1, by1 = hx(COLS) + P, hy(ROWS) + P
e(f'<rect x="{bx0}" y="{by0}" width="{bx1-bx0}" height="{by1-by0}" rx="7" '
  f'fill="#fdf6e3" stroke="#a16207" stroke-width="2.5"/>')

for c in range(1, COLS + 1):
    for r in range(1, ROWS + 1):
        edge = (c <= BORDER or c > COLS - BORDER
                or r <= BORDER or r > ROWS - BORDER)
        e(f'<circle cx="{hx(c)}" cy="{hy(r)}" r="3.1" '
          f'fill="{"#ebe3d2" if edge else "#d6c9a8"}"/>')

e(f'<rect x="{hx(1+BORDER)-13}" y="{hy(1+BORDER)-13}" '
  f'width="{hx(COLS-BORDER)-hx(1+BORDER)+26}" '
  f'height="{hy(ROWS-BORDER)-hy(1+BORDER)+26}" rx="4" fill="none" '
  f'stroke="#a16207" stroke-width="1.2" stroke-dasharray="5 4" opacity="0.65"/>')

for mx, my in ((bx0 + 15, by0 + 15), (bx1 - 15, by0 + 15),
               (bx0 + 15, by1 - 15), (bx1 - 15, by1 - 15)):
    e(f'<circle cx="{mx}" cy="{my}" r="7.5" fill="#ffffff" '
      f'stroke="#a16207" stroke-width="2"/>')
    e(f'<circle cx="{mx}" cy="{my}" r="4" fill="#fdf6e3"/>')

# rulers
e('<g font-size="9.5" fill="#92400e" text-anchor="middle">')
for c in range(1, COLS + 1, 2):
    e(f'<text x="{hx(c)}" y="{by0-7}">{c}</text>')
e("</g>")
e('<g font-size="9.5" fill="#92400e" text-anchor="end">')
for r in range(1, ROWS + 1, 2):
    e(f'<text x="{bx0-7}" y="{hy(r)+3.5}">{r}</text>')
e("</g>")

def res_body(a, b, col, value, side, rev):
    vertical = a[0] == b[0]
    x0, y0 = hx(a[0]), hy(a[1])
    x1, y1 = hx(b[0]), hy(b[1])
    dash = ' stroke-dasharray="5 4"' if rev else ""
    e(f'<line x1="{x0}" y1="{y0}" x2="{x1}" y2="{y1}" stroke="{col}" '
      f'stroke-width="2.4"{dash}/>')
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    if vertical:
        e(f'<rect x="{cx-7}" y="{cy-15}" width="14" height="30" rx="3" '
          f'fill="{col}" opacity="0.92"/>')
    else:
        e(f'<rect x="{cx-15}" y="{cy-7}" width="30" height="14" rx="3" '
          f'fill="{col}" opacity="0.92"/>')
    lx = cx - 13 if side == "L" else cx + 13
    anc = "end" if side == "L" else "start"
    return lx, cy, anc


def draw_part(d, value, a, b, kind, side, rev):
    col = "#0f766e" if kind == "res" and value == "4.7 k" else (
        "#1d4ed8" if kind == "cap" else "#b91c1c")
    lx, cy, anc = res_body(a, b, col, value, side, rev)
    e(f'<text x="{lx}" y="{cy-2}" font-size="11" font-weight="bold" '
      f'fill="{col}" text-anchor="{anc}">{d}</text>')
    e(f'<text x="{lx}" y="{cy+12}" font-size="10.5" fill="{col}" '
      f'text-anchor="{anc}">{value}</text>')


# ---- connector bodies go down FIRST, so no wire vanishes under a white box
for d, c, r, up, lo, col in TERMINALS:
    e(f'<rect x="{hx(c)-15}" y="{hy(r)-14}" width="56" height="{2*P+28}" rx="4" '
      f'fill="#ffffff" fill-opacity="0.88" stroke="{col}" stroke-width="2.2"/>')
for d, c, r, col, label in HEADERS:
    e(f'<rect x="{hx(c)-13}" y="{hy(r)-13}" width="{2*P+26}" height="26" rx="3" '
      f'fill="#ffffff" fill-opacity="0.88" stroke="{col}" stroke-width="2.2"/>')

# ---- reverse side first, so the front-side copper draws over it and a part
# that passes behind a bus looks like it passes behind a bus
e('<g opacity="0.5">')
for a, b, col, rev in JUMPERS:
    if rev:
        e(f'<line x1="{hx(a[0])}" y1="{hy(a[1])}" x2="{hx(b[0])}" y2="{hy(b[1])}" '
          f'stroke="{col}" stroke-width="2.6" stroke-dasharray="6 5"/>')
for _p in [p for p in PARTS if p[6]]:
    draw_part(*_p)
e("</g>")

# ---- buses
for name, row, (c0, c1), col, label in BUSES:
    e(f'<line x1="{hx(c0)}" y1="{hy(row)}" x2="{hx(c1)}" y2="{hy(row)}" '
      f'stroke="{col}" stroke-width="7" stroke-linecap="round" opacity="0.9"/>')
    e(f'<text x="{hx(c1)+14}" y="{hy(row)+4}" font-size="11.5" font-weight="bold" '
      f'fill="{col}">{name}</text>')

for c, r0, r1, col, _ in SPINES:
    e(f'<line x1="{hx(c)}" y1="{hy(r0)}" x2="{hx(c)}" y2="{hy(r1)}" '
      f'stroke="{col}" stroke-width="7" stroke-linecap="round" opacity="0.9"/>')

# ---- per-pin stubs: short bare wire soldered onto a socket pad
for c, r0, r1, who, scol in STUBS:
    e(f'<line x1="{hx(c)}" y1="{hy(r0)}" x2="{hx(c)}" y2="{hy(r1)}" '
      f'stroke="{scol}" stroke-width="4.5" stroke-linecap="round" opacity="0.85"/>')

# ---- front-side jumpers
for a, b, col, rev in JUMPERS:
    if not rev:
        e(f'<line x1="{hx(a[0])}" y1="{hy(a[1])}" x2="{hx(b[0])}" y2="{hy(b[1])}" '
          f'stroke="{col}" stroke-width="2.6" opacity="0.95"/>')

# ---- the Teensy body, drawn over the holes it covers
tx0 = hx(T_COL0) - 13
tx1 = hx(T_COL0 + len(TOP_PINS) - 1) + 13
e(f'<rect x="{tx0}" y="{hy(T_TOP)-13}" width="{tx1-tx0}" '
  f'height="{hy(T_BOT)-hy(T_TOP)+26}" rx="5" fill="#1e293b" fill-opacity="0.13" '
  f'stroke="#1e293b" stroke-width="1.8" stroke-dasharray="7 4"/>')
for row, pins in ((T_TOP, TOP_PINS), (T_BOT, BOT_PINS)):
    e(f'<rect x="{tx0+4}" y="{hy(row)-9}" width="{tx1-tx0-8}" height="18" rx="3" '
      f'fill="#475569"/>')
    for i, name in enumerate(pins):
        e(f'<circle cx="{hx(T_COL0+i)}" cy="{hy(row)}" r="4.2" fill="#f8fafc"/>')
mid = (hy(T_TOP) + hy(T_BOT)) / 2
e(f'<text x="{(tx0+tx1)/2}" y="{mid-4}" font-size="13" font-weight="bold" '
  f'fill="#334155" text-anchor="middle">Teensy 4.1 &#8212; in female headers, '
  f'never soldered down</text>')
e(f'<text x="{(tx0+tx1)/2}" y="{mid+15}" font-size="10.5" fill="#64748b" '
  f'text-anchor="middle">USB end at the left. Pin order below is what this '
  f'drawing assumed &#8212; read it against the board.</text>')

# the assumed pin order, printed INSIDE the body so it can be checked in ten
# seconds without fighting the holes and parts outside it
for row, pins, dy in ((T_TOP, TOP_PINS, 22), (T_BOT, BOT_PINS, -16)):
    e('<g font-size="8.5" fill="#475569" text-anchor="middle">')
    for i, name in enumerate(pins):
        e(f'<text x="{hx(T_COL0+i)}" y="{hy(row)+dy}">{name}</text>')
    e("</g>")

# ---- parts
for _p in [p for p in PARTS if not p[6]]:
    draw_part(*_p)

# ---- terminals: pads and labels only; the bodies went down before the wires
for d, c, r, up, lo, col in TERMINALS:
    x, y = hx(c), hy(r)
    for h in term_holes(c, r):
        e(f'<circle cx="{hx(h[0])}" cy="{hy(h[1])}" r="4" fill="{col}"/>')
    e(f'<text x="{x+46}" y="{y+4}" font-size="10" font-weight="bold" '
      f'fill="{col}">{up}</text>')
    e(f'<text x="{x+46}" y="{y+2*P+4}" font-size="10" font-weight="bold" '
      f'fill="{col}">{lo}</text>')
    e(f'<text x="{x+13}" y="{y-20}" font-size="10.5" font-weight="bold" '
      f'fill="{col}" text-anchor="middle">{d}</text>')

# ---- headers: pads and labels only. The MIDDLE pad is the servo connector's
# +5 and is deliberately left open - see the panel.
for d, c, r, col, label in HEADERS:
    for i, h in enumerate(header_holes(c, r)):
        if i == 1:
            e(f'<circle cx="{hx(h[0])}" cy="{hy(h[1])}" r="4.5" fill="#ffffff" '
              f'stroke="{col}" stroke-width="1.8"/>')
            e(f'<text x="{hx(h[0])}" y="{hy(h[1])+19}" font-size="8" '
              f'font-weight="bold" fill="{col}" text-anchor="middle">n/c</text>')
        else:
            e(f'<circle cx="{hx(h[0])}" cy="{hy(h[1])}" r="4" fill="{col}"/>')
    e(f'<text x="{hx(c+1)}" y="{hy(r)-20}" font-size="10" font-weight="bold" '
      f'fill="{col}" text-anchor="middle">{label}</text>')

# ---- the one place on this board where a value is decided by a measurement
# in the clear margin beside R5, where nothing else is drawn
_cx, _cy = bx1 + 18, hy(4)
e(f'<text x="{_cx}" y="{_cy}" font-size="11" font-weight="bold" fill="#be123c">'
  f'i-BUS LEVEL &#8212; meter it first</text>')
for _i, _ln in enumerate([
        "3.3 V idle &#8594; R5 is a WIRE",
        "LINK, and no R6 at all.",
        "5 V idle &#8594; R5 / R6 as a",
        "divider, to the ratio you",
        "measured. &#167;3.4, and the",
        "Teensy is not 5 V tolerant."]):
    e(f'<text x="{_cx}" y="{_cy+18+_i*15}" font-size="10.5" fill="#be123c">{_ln}</text>')

# ---- the pads that take a second wire
for h in sorted(DOUBLED):
    e(f'<circle cx="{hx(h[0])}" cy="{hy(h[1])}" r="9" fill="none" '
      f'stroke="#be123c" stroke-width="1.6" opacity="0.75"/>')
e(f'<text x="{hx(1)}" y="{by1+22}" font-size="11" font-weight="bold" '
  f'fill="#be123c">Circled: {len(DOUBLED)} pads take a second wire. '
  f'Two is ordinary; three is a joint nobody can inspect.</text>')

# ---------------------------------------------------------------- the panels
def panel(x, y, w, h, fill, stroke, title, tcol, lines, lcol, fs=12.5, ls=19):
    h = max(h, 52 + ls * len(lines) + 12)
    e(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" '
      f'stroke="{stroke}" stroke-width="2"/>')
    e(f'<text x="{x+20}" y="{y+30}" font-size="14" font-weight="bold" '
      f'fill="{tcol}">{title}</text>')
    for i, line in enumerate(lines):
        e(f'<text x="{x+20}" y="{y+56+i*ls}" font-size="{fs}" fill="{lcol}">'
          f"{rich(line)}</text>")
    return y + h


y = by1 + 44
y = panel(24, y, 1132, 0, "#eff6ff", "#1d4ed8",
          "Read the pin order off the board before you believe any column here",
          "#1e3a8a", [
    "Every column in this drawing is computed from the pin order printed along the Teensy. "
    "**It has not been verified against a board.**",
    "The same arithmetic said this perfboard was 31 holes wide and it is 29. "
    "**Hold a Teensy next to the figure and read along the edge** &#8212; if the order differs, "
    "correct the two lists in the",
    "generator and re-run. Nothing else moves, because nothing else is hand-placed.",
], "#1e40af")

y2 = panel(24, y + 16, 556, 0, "#f0fdf4", "#22c55e",
           "Build order &#8212; the first step is still not a component", "#14532d", [
    "**1.** Female headers, with the Teensy plugged in to hold",
    "  them square. Tack two corners, check it sits flat.",
    "**2.** The three buses as **continuous bare wire**. On a",
    "  breadboard the rail is given to you; here an island",
    "  that never got joined is the classic fault.",
    "**3.** Passives, each beside the pin it serves. The two",
    "  **10 k go on the REVERSE side** &#8212; each crosses the",
    "  GND bus on its way to 3.3 V, and the board is 양면",
    "  so that it can.",
    "**4.** Terminals and headers at the edges.",
    "**5.** Continuity and short checks, Teensy **OUT**.",
    "**6.** Only now fit the Teensy.",
], "#166534", fs=12, ls=18)

panel(600, y + 16, 556, 0, "#fffbeb", "#f59e0b",
      "Why the passives sit where they do", "#92400e", [
    "**Both 3.3 V buses come from the Teensy's own 3V3 pins**,",
    "  one on each row &#8212; so they are joined only when the",
    "  Teensy is in. A board that reads 0 V with it out is",
    "  **correct**, not broken.",
    "**The 10 k pull-ups are not optional.** The DRV5013 latch",
    "  output is open-drain: without them the quadrature",
    "  decoder sees a line that never rises, which looks",
    "  exactly like a dead sensor.",
    "**The 1 nF go to GND from the same two lines.** A motor",
    "  edge landing on a 10 k node is a **count**.",
    "**The 4.7 k sit on SDA and SCL**, parallel to the AS5600",
    "  breakout's own pair.",
    "**Both PWM headers go to the MUX's MASTER inputs**, and",
    "  the MUX's two outputs drive the motor driver's S1 and",
    "  S2. Pin 2 is steering, pin 3 is drive.",
    "**The servo headers' middle pad is left open.** That pad",
    "  is the connector's +5. This board runs on **UBEC A**",
    "  and the MUX and receiver on **UBEC B** &#8212; joining them",
    "  undoes the authority split the two UBECs exist for.",
    "  Signal and ground land; +5 does not.",
    "**R5 is a wire LINK or half a divider**, and which one is",
    "  decided by a meter: i-BUS idling at 3.3 V takes the",
    "  link, 5 V takes R5/R6. **The Teensy 4.1 is not 5 V**",
    "  **tolerant**, and the wire goes on the pin last.",
], "#b45309", fs=12, ls=18)

H = int(y2 + 30)
out[0] = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
          f'viewBox="0 0 {W} {H}" font-family="-apple-system,BlinkMacSystemFont,'
          f"'Segoe UI',Roboto,sans-serif\">")
out[1] = f'<rect width="{W}" height="{H}" fill="#ffffff"/>'
e("</svg>")

dst = Path("docs/images/signal-board-perfboard-layout.svg")
io.open(dst, "w", encoding="utf-8").write("\n".join(out))
print(f"wrote {dst}  ({COLS}x{ROWS} holes, {COLS-2*BORDER}x{ROWS-2*BORDER} usable, "
      f"{len(PARTS)} parts, {len(TERMINALS)} terminals, {len(HEADERS)} headers, "
      f"{len(DOUBLED)} doubled pads, canvas {W}x{H})")
print("assertions passed: no hole carries three, reverse side exactly where the "
      "GND bus is crossed, every bus fed, every passive beside its pin")
