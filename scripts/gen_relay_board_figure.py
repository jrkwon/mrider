#!/usr/bin/env python3
# Copyright 2026 Jaerock Kwon
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

r"""
Generate the relay-driver perfboard placement figure.

    python3 scripts/gen_relay_board_figure.py
    -> docs/images/relay-board-perfboard-layout.svg

WHY THIS FIGURE EXISTS
----------------------
`relay-driver-board.svg` is the SCHEMATIC - what connects to what. It does not
say where anything sits, and this board is the one the project forbids
breadboarding, so the first physical build is also the final one. There was no
placement drawing: `perfboard-transfer.svg` draws the *signal* perfboard and
stops.

WHY A GENERATOR AND NOT HAND-WRITTEN SVG
----------------------------------------
Precedent: `gen_breadboard_figure.py`, whose docstring records three faults a
hand-drawn figure shipped - a grid that did not match the board in the box, a
rail with no source, and labels over wires. A placement drawing adds a fourth
way to be wrong that a human cannot see by reading: two leads in one hole.

So the layout here is DATA - a hole-indexed netlist - and the script asserts
what a reader cannot check:

  * no two component leads share a hole
  * every lead and every bus end is inside the grid
  * the pulldown's ground lands within one hole of the MOSFET source's,
    which is the whole point of the drawing
  * no panel text overlaps another panel

THE GRID IS COUNTED, AND DIVIDE-BY-PITCH WAS OVER ON BOTH SIDES
---------------------------------------------------------------
The board is 거상인 `[GA6] 50 x 80` double-sided, 2.54 mm pitch. The arithmetic
said:

    80 / 2.54 = 31.5  ->  31 columns      WRONG, over by two
    50 / 2.54 = 19.7  ->  19 rows         WRONG, over by one

COUNTED 2026-11-05, end to end including the edge holes:

    holes   29 x 18
    usable  27 x 16      columns 2..28, rows 2..17

Dividing by the pitch assumes the pads run to the board edge. They do not -
the array sits inside a blank margin, and that margin is what the arithmetic
had no way to know:

    width   (80 - 28 x 2.54) / 2 = 4.4 mm
    height  (50 - 17 x 2.54) / 2 = 3.4 mm

Those margins are also why the four plated corner holes fit where they do: a
3.2 mm hole needs about that much blank FR-4, and a board whose pads really did
run to within 1.9 mm of the edge could not have carried one. The photograph and
the hole count agree, which is the check that the earlier guess failed.

The BORDER below is one hole on each edge. That ring is not a measured property
of the board - it is margin this layout keeps on purpose, so that a bus never
ends on the outermost pad with nothing beyond it to take a strain or a stray
strand. check() enforces it rather than leaving it to the eye of the next
editor.

THE ROW BUDGET IS EXACTLY SPENT. The layout runs rows 2..17 - sixteen rows into
sixteen - so the GND bus sits on the LAST usable row. Nothing may be added
below it, and any future edit that needs a row has to take one back from the
bus spacing above. Columns are no longer loose either: 27 of 27.

MOUNTING: the board ships with four plated corner holes, in the blank margin
outside the pad array (photographed 2026-11-05). Nothing is drilled and no pad
is spent. An earlier revision of this file reasoned from the margin that a
corner M3 could not fit - it was answering a question the manufacturer had
already answered, and the arithmetic it used is the same one the row count
caught out. Look at the part before deriving its geometry.

VERIFY IT IN A BROWSER, NOT IN IMAGEMAGICK
------------------------------------------
`convert` renders a <text> containing <tspan> by resetting x, so bold runs
pile up on the start of their line and the whole block looks like mush. That
hides real overlaps underneath it - a four-pixel collision between two panel
entries survived three rounds of "I rendered it and looked" because the mush
was the same either way. Use:

    google-chrome --headless --screenshot=out.png \
        --window-size=1180,1519 file://$PWD/docs/images/<figure>.svg

ImageMagick is still fine for geometry - buses, holes, part bodies - and it is
what caught the paint-order halo that erased the TO-220's G/D/S letters.
"""

import io
import sys
from pathlib import Path

# ---------------------------------------------------------------- the geometry
COLS, ROWS = 29, 18               # counted end to end 2026-11-05 - see docstring
BORDER = 1                        # outer ring: holes exist, working area does not
P = 26                            # px per hole pitch
X0, Y0 = 100, 130                 # centre of hole (1, 1)

W = 1180                          # H is computed from the last panel


def hx(c):
    return X0 + (c - 1) * P


def hy(r):
    return Y0 + (r - 1) * P


# ------------------------------------------------------------------ the layout
# Buses: bare tinned wire soldered along a whole run of holes.
BUSES = [
    ("V12", 2, (2, 28), "#dc2626", "+12 V  (E-stop NC feed)"),
    ("DRN", 8, (7, 28), "#b45309", "DRAIN  (all four coil low sides)"),
    ("GND", 17, (2, 28), "#334155", "GND  (star return)"),
]
# One vertical run, because the power terminal's ground has to reach row 17.
GND_SPINE = (4, 6, 17)            # col, row_from, row_to

# Pluggable terminal blocks, 5.08 mm pitch -> the two pins are TWO holes apart.
TERMINALS = [
    ("PWR",    2, 4,  "+12 V",  "GND",    "#dc2626"),
    ("TEENSY", 2, 12, "GATE",   "SENSE",  "#2563eb"),  # NOT gate+GND - see the panel
    ("K1",     7, 4,  "86",     "85",     "#15803d"),
    ("K2",    12, 4,  "86",     "85",     "#15803d"),
    ("K3",    17, 4,  "86",     "85",     "#15803d"),
    ("K4",    22, 4,  "86",     "85",     "#15803d"),
]

# Two-lead parts: designator, value, hole A, hole B, kind
# designator, value, hole A, hole B, kind, label side for vertical parts
PARTS = [
    ("R1", "10 k",  (15, 14), (15, 17), "res-pd", "L"),
    ("R2", "100",   (7, 12),  (12, 12), "res",    "R"),
    ("R3", "10 k",  (5, 2),   (5, 8),   "res",    "L"),
    ("R4", "2.7 k", (5, 10),  (5, 17),  "res",    "R"),
    ("D1", "1N4007", (10, 2), (10, 8),  "diode",  "L"),
    ("D2", "1N4007", (15, 2), (15, 8),  "diode",  "L"),
    ("D3", "1N4007", (20, 2), (20, 8),  "diode",  "L"),
    ("D4", "1N4007", (25, 2), (25, 8),  "diode",  "L"),
]

# IRLZ44N, TO-220, standing upright. Pin 1 = Gate, 2 = Drain, 3 = Source.
Q1 = {"row": 12, "g": 14, "d": 15, "s": 16}

# Jumpers: insulated hookup wire. `under` means route on the reverse side,
# because it passes beneath the TO-220 package.
JUMPERS = [
    ((2, 4),   (2, 2),   "#dc2626", False),   # PWR +12 V up to the V12 bus
    ((2, 6),   (4, 6),   "#334155", False),   # PWR GND across to the spine
    ((2, 12),  (7, 12),  "#2563eb", False),   # GATE in
    ((12, 12), (14, 12), "#2563eb", False),   # through the 100 ohm to the gate
    ((14, 12), (15, 14), "#2563eb", False),   # gate node down to the pulldown
    ((15, 12), (15, 8),  "#b45309", True),    # DRAIN up to the drain bus
    ((16, 12), (16, 17), "#334155", True),    # SOURCE down to the GND bus
    ((5, 8),   (5, 10),  "#7c3aed", False),   # sense node bridge
    ((5, 10),  (2, 14),  "#7c3aed", False),   # sense out to the Teensy
]
for c in (7, 12, 17, 22):
    JUMPERS.append(((c, 4), (c, 2), "#dc2626", False))   # 86 up to +12 V
    JUMPERS.append(((c, 6), (c, 8), "#b45309", False))   # 85 down to DRAIN


# ------------------------------------------------------------- the assertions
def check():
    def inside(h):
        """Inside the USABLE ring, not merely on the board.

        The border ring has holes and no room: the bus or jumper that has to
        reach a lead there runs off the edge. Counted, not assumed - docstring.
        """
        return (1 + BORDER <= h[0] <= COLS - BORDER
                and 1 + BORDER <= h[1] <= ROWS - BORDER)

    leads = []
    for d, _, a, b, _, _ in PARTS:
        leads += [(a, d), (b, d)]
    for d, c, r, *_ in TERMINALS:
        leads += [((c, r), d), ((c, r + 2), d)]
    for pin in "gds":
        leads.append(((Q1[pin], Q1["row"]), "Q1"))

    seen = {}
    for h, owner in leads:
        assert inside(h), (f"{owner} lead at {h} is outside the usable "
                           f"{COLS-2*BORDER}x{ROWS-2*BORDER} ring")
        assert h not in seen, f"two leads in hole {h}: {seen[h]} and {owner}"
        seen[h] = owner

    for name, row, (c0, c1), *_ in BUSES:
        assert inside((c0, row)) and inside((c1, row)), f"bus {name} off grid"
    assert inside((GND_SPINE[0], GND_SPINE[1])) and inside((GND_SPINE[0], GND_SPINE[2]))

    for a, b, *_ in JUMPERS:
        assert inside(a) and inside(b), f"jumper {a}->{b} off grid"

    # The one rule this whole drawing exists to carry.
    src = (Q1["s"], 17)
    pd_gnd = next(b for d, _, a, b, _, _ in PARTS if d == "R1")
    assert pd_gnd[1] == src[1] == 17, "pulldown ground and source must both land on the GND bus"
    assert abs(pd_gnd[0] - src[0]) <= 1, (
        f"the 10k pulldown grounds at {pd_gnd} but the MOSFET source grounds at {src} - "
        "no coil current may flow in the copper between them")

    # The gate network must be compact: the pulldown is the ONLY thing that
    # holds the gate low, so a long gate node is a long antenna.
    gate = (Q1["g"], Q1["row"])
    r1_gate = next(a for d, _, a, b, _, _ in PARTS if d == "R1")
    span = abs(r1_gate[0] - gate[0]) + abs(r1_gate[1] - gate[1])
    assert span <= 3, f"gate node spans {span} holes to reach the pulldown; keep it under 4"

    # ...and it must be the GATE node, not the Teensy side of R2. Proximity is
    # not connection: the schematic had the pulldown tapped before the 100 ohm
    # for weeks and every "is it near the gate" check would have passed it.
    # On that side a cracked R2 joint floats the gate with the pulldown still
    # fitted and still reading 10k on a meter.
    assert any({a, b} == {gate, r1_gate} for a, b, *_ in JUMPERS), (
        f"the pulldown's gate lead at {r1_gate} must connect straight to the "
        f"gate hole {gate} - on the Teensy side of R2 it protects the wrong node")


check()

# ------------------------------------------------------------------ the drawing
out = []
sys.path.insert(0, str(Path(__file__).resolve().parent))
from svg_common import BOLD, EB, esc, rich  # noqa: E402,F401


def e(s):
    out.append(s)




# out[0] and out[1] are rewritten at the end, once H is known from the panels.
e('<svg>')
e('<rect/>')

e(f'<text x="24" y="36" font-size="19" font-weight="bold" fill="#0f172a">'
  f'Relay-driver board on perfboard &#8212; where everything sits</text>')
e(f'<text x="24" y="58" font-size="12.5" fill="#475569">'
  f'[GA6] 50 &#215; 80 double-sided, 2.54 mm pitch: {COLS} &#215; {ROWS} holes counted end to end, '
  f'{BOLD}{COLS-2*BORDER} &#215; {ROWS-2*BORDER} after the one-hole margin this layout keeps{EB} '
  f'(both sides counted 2026-11-05).</text>')
e(f'<text x="24" y="77" font-size="12.5" fill="#475569">'
  f'One MOSFET, four coils, four flyback diodes, the gate pulldown, and the E-stop sense divider. '
  f'The schematic is a separate figure; this one is only about placement.</text>')

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

# the usable ring, drawn because a builder counting in from the edge is
# exactly the person who puts a lead in the border by one hole
e(f'<rect x="{hx(1+BORDER)-13}" y="{hy(1+BORDER)-13}" '
  f'width="{hx(COLS-BORDER)-hx(1+BORDER)+26}" '
  f'height="{hy(ROWS-BORDER)-hy(1+BORDER)+26}" rx="4" fill="none" '
  f'stroke="#a16207" stroke-width="1.2" stroke-dasharray="5 4" opacity="0.65"/>')

# the four plated corner mounting holes, in the blank margin outside the pads
for mx, my in ((bx0 + 15, by0 + 15), (bx1 - 15, by0 + 15),
               (bx0 + 15, by1 - 15), (bx1 - 15, by1 - 15)):
    e(f'<circle cx="{mx}" cy="{my}" r="7.5" fill="#ffffff" '
      f'stroke="#a16207" stroke-width="2"/>')
    e(f'<circle cx="{mx}" cy="{my}" r="4" fill="#fdf6e3"/>')

# column / row rulers
e('<g font-size="9.5" fill="#92400e" text-anchor="middle">')
for c in range(1, COLS + 1, 2):
    e(f'<text x="{hx(c)}" y="{by0-7}">{c}</text>')
e('</g>')
e('<g font-size="9.5" fill="#92400e" text-anchor="end">')
for r in range(1, ROWS + 1, 2):
    e(f'<text x="{bx0-7}" y="{hy(r)+3.5}">{r}</text>')
e('</g>')

# ---- buses
for name, row, (c0, c1), col, label in BUSES:
    e(f'<line x1="{hx(c0)}" y1="{hy(row)}" x2="{hx(c1)}" y2="{hy(row)}" '
      f'stroke="{col}" stroke-width="7" stroke-linecap="round" opacity="0.9"/>')
    e(f'<text x="{hx(c1)+14}" y="{hy(row)+4}" font-size="11.5" font-weight="bold" '
      f'fill="{col}">{name}</text>')
sc, sr0, sr1 = GND_SPINE
e(f'<line x1="{hx(sc)}" y1="{hy(sr0)}" x2="{hx(sc)}" y2="{hy(sr1)}" '
  f'stroke="#334155" stroke-width="7" stroke-linecap="round" opacity="0.9"/>')

# ---- jumpers, under the parts
e('<g stroke-linecap="round">')
for a, b, col, under in JUMPERS:
    dash = ' stroke-dasharray="5 4"' if under else ''
    e(f'<line x1="{hx(a[0])}" y1="{hy(a[1])}" x2="{hx(b[0])}" y2="{hy(b[1])}" '
      f'stroke="{col}" stroke-width="3.2"{dash}/>')
e('</g>')

# ---- terminal blocks.  Edge blocks label OUTWARD, into the margin, because
#      "+12 V" and "SENSE" are wider than the block and collided with the
#      sense divider in the first draft.
for d, c, r, pa, pb, col in TERMINALS:
    x, y = hx(c), hy(r)
    edge = c <= 3
    e(f'<rect x="{x-P*1.1}" y="{y-P*0.85}" width="{P*2.2}" height="{P*2.7}" rx="4" '
      f'fill="#ffffff" stroke="{col}" stroke-width="2.4"/>')
    for yy, lbl in ((y, pa), (hy(r + 2), pb)):
        e(f'<circle cx="{x}" cy="{yy}" r="4.6" fill="{col}"/>')
        lx = x - P * 1.1 - 7 if edge else x + 9
        e(f'<text x="{lx}" y="{yy+4}" font-size="10.5" font-weight="bold" fill="{col}" '
          f'text-anchor="{"end" if edge else "start"}">{lbl}</text>')
    e(f'<text x="{x}" y="{y-P*0.85-7}" font-size="11.5" font-weight="bold" '
      f'fill="{col}" text-anchor="middle">{d}</text>')

# ---- two-lead parts
for d, val, a, b, kind, side in PARTS:
    x1, y1, x2, y2 = hx(a[0]), hy(a[1]), hx(b[0]), hy(b[1])
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    body = "#be123d" if kind == "res-pd" else ("#0f766e" if kind.startswith("res") else "#1e3a8a")
    e(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{body}" stroke-width="2.4"/>')
    vert = abs(y2 - y1) >= abs(x2 - x1)
    bw, bh = (13, 34) if vert else (34, 13)
    e(f'<rect x="{mx-bw/2}" y="{my-bh/2}" width="{bw}" height="{bh}" rx="3" '
      f'fill="{body}" stroke="#ffffff" stroke-width="1.6"/>')
    if kind == "diode":          # cathode band at hole A, which is the +12 V bus
        e(f'<rect x="{mx-6.5}" y="{my-bh/2+3}" width="13" height="5" fill="#e2e8f0"/>')
    for xx, yy in ((x1, y1), (x2, y2)):
        e(f'<circle cx="{xx}" cy="{yy}" r="4.2" fill="{body}"/>')
    if vert:
        lx = mx - 11 if side == "L" else mx + 11
        anc = "end" if side == "L" else "start"
        e(f'<text x="{lx}" y="{my-1}" font-size="11" font-weight="bold" fill="{body}" '
          f'text-anchor="{anc}">{d}</text>')
        e(f'<text x="{lx}" y="{my+13}" font-size="10" fill="{body}" '
          f'text-anchor="{anc}">{val}</text>')
    else:
        e(f'<text x="{mx}" y="{my-13}" font-size="11" font-weight="bold" fill="{body}" '
          f'text-anchor="middle">{d}</text>')
        e(f'<text x="{mx}" y="{my+22}" font-size="10" fill="{body}" '
          f'text-anchor="middle">{val}</text>')

# ---- the MOSFET, standing upright
qr = Q1["row"]
qx0, qx1 = hx(Q1["g"]) - P * 0.8, hx(Q1["s"]) + P * 0.8
e(f'<rect x="{qx0}" y="{hy(qr)-P*1.6}" width="{qx1-qx0}" height="{P*1.6}" rx="3" '
  f'fill="#1f2937" stroke="#0f172a" stroke-width="2"/>')
e(f'<rect x="{qx0+4}" y="{hy(qr)-P*1.6+4}" width="{qx1-qx0-8}" height="{P*0.42}" '
  f'rx="2" fill="#94a3b8"/>')
e(f'<text x="{(qx0+qx1)/2}" y="{hy(qr)-P*0.55}" font-size="10.5" font-weight="bold" '
  f'fill="#ffffff" text-anchor="middle">IRLZ44N</text>')
e(f'<text x="{(qx0+qx1)/2}" y="{hy(qr)-P*1.6-8}" font-size="11" font-weight="bold" '
  f'fill="#0f172a" text-anchor="middle">Q1 &#8212; the TAB is the DRAIN</text>')
for pin, lbl in (("g", "G"), ("d", "D"), ("s", "S")):
    e(f'<circle cx="{hx(Q1[pin])}" cy="{hy(qr)}" r="5" fill="#0f172a"/>')
    # A backing chip, not a text stroke: `paint-order` is not universal, and a
    # renderer that ignores it strokes OVER the glyph and erases the letter.
    e(f'<rect x="{hx(Q1[pin])-7}" y="{hy(qr)+P*0.78-11}" width="14" height="14" rx="3" '
      f'fill="#fdf6e3" opacity="0.95"/>')
    e(f'<text x="{hx(Q1[pin])}" y="{hy(qr)+P*0.78}" font-size="10.5" font-weight="bold" '
      f'fill="#0f172a" text-anchor="middle">{lbl}</text>')

# ---- the one callout that belongs on the board itself, drawn BELOW the GND bus
sx, sy = hx(Q1["s"]), hy(17)
px = hx(15)
for cx in (sx, px):
    e(f'<circle cx="{cx}" cy="{sy}" r="11" fill="none" stroke="#be123d" stroke-width="2.6"/>')
e(f'<text x="{px+20}" y="{sy+P+4}" font-size="12" font-weight="bold" fill="#be123d">'
  f'PULLDOWN and SOURCE ground ONE HOLE APART</text>')
e(f'<path d="M {px+14} {sy+6} L {px+22} {sy+P-9}" stroke="#be123d" stroke-width="2" fill="none"/>')

# ---- panels
PANELS = []


def panel(x, y, w, h, fill, stroke, title, tcol, lines, lcol, fs=12.5, ls=19):
    # `h` is a FLOOR, not the height: a panel grows to fit its own text rather
    # than clipping it. Hand-tuned heights are how a figure ships a cropped
    # last line that nobody notices until a student is reading it at a bench.
    h = max(h, 52 + ls * len(lines) + 12)
    for px0, py0, px1, py1 in PANELS:
        assert x >= px1 or x + w <= px0 or y >= py1 or y + h <= py0, \
            f"panel {title[:28]!r} overlaps one already placed"
    PANELS.append((x, y, x + w, y + h))
    e(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" '
      f'stroke="{stroke}" stroke-width="2"/>')
    e(f'<text x="{x+20}" y="{y+27}" font-size="14" font-weight="bold" fill="{tcol}">{title}</text>')
    yy = y + 52
    for ln in lines:
        ind = 14 if ln.startswith("  ") else 0
        e(f'<text x="{x+20+ind}" y="{yy}" font-size="{fs}" fill="{lcol}">{rich(ln.strip())}</text>')
        yy += ls
    return y + h


PY0 = by1 + 30

y = panel(24, PY0, 1132, 180, "#fef2f2", "#be123d",
          "Your question: yes &#8212; but the Teensy&#8217;s ground reaches it through the STAR, not through a second wire",
          "#991b1b", [
    "**The MOSFET is a low-side switch, so its SOURCE is the board ground.** The pulldown holds the gate low "
    "against that source, so",
    "  &#8220;3.3 V on the gate&#8221; and &#8220;0 V on the gate&#8221; only mean anything if the Teensy shares "
    "that same node. That part of your reading is exactly right.",
    "**What it must not be is a second ground WIRE.** This board&#8217;s ground already returns to the star on the "
    "PWR terminal, carrying the",
    "  whole 600 mA of coil current. A second ground conductor up to the Teensy is a parallel path &#8212; a loop, "
    "which is what &#167;3.5.3 forbids.",
    "**What you accept instead is the IR drop in that one wire:** 600 mA &#215; ~0.011 &#937; "
    "(1.5 mm&#178; over 1 m) &#8776; **7 mV**, against a worst-case",
    "  V&#7504;&#8347;(th) of 1.0 V. **0.7 %.** A single star ground is not a compromise here &#8212; it is simply "
    "right, and it is one wire fewer.",
], "#7f1d1d")

y = panel(24, y + 16, 1132, 142, "#fff7ed", "#c2410c",
          "Why the pulldown lives HERE, beside the MOSFET, and not at the Teensy end",
          "#9a3412", [
    "**Because then a cut gate wire is still safe.** That wire runs from the logic box to the power box. With the "
    "pulldown at the Teensy end,",
    "  unplugging it would leave the gate floating **at the MOSFET** &#8212; partial enhancement, relays chattering "
    "between STOCK and DBW.",
    "**With it on this board, a broken gate wire still leaves 10 k&#937; tied across gate and source.** Gate low. "
    "Coils dropped. STOCK.",
    "**And its ground lands one hole from the source&#8217;s.** Across a soldered bus that drop is microvolts, so "
    "this is cheap insurance rather than a",
    "  live hazard &#8212; but it is the habit that stays correct the day someone rebuilds the same circuit with "
    "wire instead of a bus.",
], "#7c2d12")

y = panel(24, y + 16, 1132, 123, "#f0fdf4", "#15803d",
          "One thing this drawing changed: the Teensy terminal carries GATE + SENSE, not GATE + GND",
          "#166534", [
    "**The E-stop sense divider is on this board** (R3/R4, tapped off the coil feed), and its output has to get back "
    "to a Teensy input &#8212; but",
    "  **no terminal in the &#167;3.5.4 count carried it.** The same omission as the gate-out way found on "
    "2026-11-05, one board over.",
    "**Swapping GND for SENSE on that block fixes both at once** and leaves the count untouched at 12 per vehicle, "
    "36 for the fleet: the",
    "  ground was never supposed to be there, and the sense line always was.",
], "#14532d")

SIDE_H = 52 + 18 * 15 + 12
y2 = panel(24, y + 16, 556, SIDE_H, "#eff6ff", "#1d4ed8",
           "Build order &#8212; unchanged; the layout follows it",
           "#1e3a8a", [
    "**1.** GND bus, GND spine, R1. Nothing else.",
    "**2.** Meter **10 k&#937;** from R1&#8217;s upper pad to the GND",
    "  bus. The reading is of **the two joints and the two**",
    "  **holes**, not of the resistor &#8212; a meter could check",
    "  the part in your hand. Nothing else is fitted, so a",
    "  wrong number has exactly one suspect.",
    "**3.** Q1, then R2, then the four diodes.",
    "  **Every band at the +12 V bus** &#8212; one reversed",
    "  diode is a short across the logic pack.",
    "**4.** Terminals, then coils last. Drive the gate from",
    "  a bench 3.3 V and **listen for four clicks**.",
    "**5.** R3/R4 last, and **meter the sense node before**",
    "  **the wire goes near a pin** &#8212; it starts at pack",
    "  volts and the Teensy 4.1 is not 5 V tolerant.",
], "#1e40af", fs=12, ls=18)

panel(600, y + 16, 556, SIDE_H, "#f5f3ff", "#7c3aed",
      "Reading the drawing",
      "#5b21b6", [
    "**Thick coloured runs** are bare tinned wire soldered",
    "  along the holes: three buses and the GND spine.",
    "**Thin runs** are insulated hookup wire, 22&#8211;24 AWG.",
    "**Dashed** means route it on the reverse side &#8212; it",
    "  passes under the TO-220 and you cannot solder it",
    "  afterwards.",
    "**Crossings are fine.** The board is &#50577;&#47732; and the wire",
    "  is insulated. What is never fine is two leads in one",
    "  hole, which this script asserts rather than trusting",
    "  the eye.",
    "**No row to spare.** Rows 2&#8211;17 are the whole usable",
    "  height: the GND bus is on the LAST usable row.",
    "**Mounting:** four **plated corner holes** come with the",
    "  board, in the margin outside the pads. Nothing to",
    "  drill and no pad spent &#8212; shown at the corners here.",
], "#6d28d9", fs=12, ls=18)

H = int(y2 + 30)
out[0] = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
          f'viewBox="0 0 {W} {H}" font-family="-apple-system,BlinkMacSystemFont,'
          f'\'Segoe UI\',Roboto,sans-serif">')
out[1] = f'<rect width="{W}" height="{H}" fill="#ffffff"/>'
e('</svg>')

# Script-relative, not CWD-relative: this is run from CI and from a
# regeneration check, and neither should have to cd first.
dst = Path(__file__).resolve().parent.parent / "docs/images/relay-board-perfboard-layout.svg"
# Importing this module must not rewrite the documentation. Only the file
# writes move under the guard; the drawing above still runs on import, which
# is what lets another script or a test reuse it without a side effect.
if __name__ == "__main__":
    io.open(dst, "w", encoding="utf-8").write("\n".join(out))
    print(f"wrote {dst}  ({COLS}x{ROWS} holes, {COLS-2*BORDER}x{ROWS-2*BORDER} usable, {len(PARTS)} parts, "
          f"{len(TERMINALS)} terminals, {len(JUMPERS)} jumpers, canvas {W}x{H})")
    print("assertions passed: every lead inside the usable ring, no shared holes, "
          "pulldown ground within one hole of the source, no panel overlaps")
