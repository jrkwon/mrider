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
Generate the authority-tap wiring figure - where the connectors go.

    python3 scripts/gen_authority_tap_figure.py
    -> docs/images/authority-tap-wiring.svg

WHY THIS FIGURE EXISTS
----------------------
`power-wiring.svg` draws the AUTHORITY row as four relays in the motor leads
and stops there. It never draws a connector, so it cannot answer the question
a builder actually has in front of the vehicle: *which half do I buy, and
which end does it go on.*

The answer is counter-intuitive enough to need a picture: MRider's harness
carries a FEMALE receptacle at the end that faces the stock module - because
the module presents male tabs - and a MALE tab at the end that faces the
vehicle, because the vehicle's own plug is female. Both halves of every tap
are therefore the opposite gender from the thing they are named after, and
counting them off a sentence is how a builder orders twelve wrong parts.

NOTHING IS CUT
--------------
Both authority taps land on connectors the vehicle already has, so the whole
intervention is an unplug. That is the figure's second job: to make the
restore path visible as two plugs, not as a splice to undo.

WHY A GENERATOR AND NOT HAND-WRITTEN SVG
----------------------------------------
Four rows with identical structure, and the facts that must hold are facts a
reader cannot check by looking:

  * the de-energised path is 87a, on EVERY row - invert one and the whole
    failsafe analysis in safety.md inverts with it
  * the stock side of every row is female, the vehicle side male - the
    gender error this figure exists to prevent
  * the driver feeds 87 and only 87
  * no two text runs overlap

VERIFY IT IN A BROWSER, NOT IN IMAGEMAGICK
------------------------------------------
`convert` resets x on a <tspan>, so bold runs pile onto the start of their
line and real overlaps hide. Use headless Chrome:

    google-chrome --headless --screenshot=out.png \
        --window-size=1300,980 file://$PWD/docs/images/authority-tap-wiring.svg

WHAT THE DRIVE ROWS USED TO ASK FOR, AND WHY THEY STOPPED
---------------------------------------------------------
They printed "RECORD colours", which treated the colour pairing at M1 as an
open question. It is not one, and it never was.

The pairing lives in the VEHICLE's plug, and this tap reuses that plug intact:
the relay's 30 leaves on a male tab and enters it on the way to the motors.
Nothing is unterminated, so the two wires that shared a receptacle still share
it afterwards. The pairing is preserved by construction and cannot be built
wrong. Recording the colours would be a per-vehicle cross-check of a thing the
build cannot get wrong, and the three vehicles need not agree.

What CAN be built wrong is which net the driver's positive output feeds, and no
colour answers that - a plug shows pairing, never polarity. So the rows name
the property that holds, and the check for the one that does not is
07-manual-drive.md 7.4 step 4.
"""

import pathlib
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from svg_common import esc  # noqa: E402

OUT = pathlib.Path("docs/images/authority-tap-wiring.svg")

W, H = 1300, 880

# ---- geometry -------------------------------------------------------------
X_ECU, W_ECU = 48, 176
X_FEM, W_FEM = 252, 104
X_REL, W_REL = 392, 236
X_MAL, W_MAL = 664, 104
X_VEH, W_VEH = 800, 176
X_MOT, W_MOT = 1012, 240

STOCK = "#64748b"      # the vehicle's own parts
NEW = "#047857"        # what MRider buys - the point of the figure
DRIVER = "#7e22ce"

# ---- data -----------------------------------------------------------------
# (relay, ecu_pad, ecu_note, colour, wire_label, vehicle_wires)
TAPS = [
    dict(
        title="STEERING TAP",
        socket="M2M3  socket",
        driver="driver M1",
        ab=["A", "B"],
        motor="steering gearmotor",
        tint="#f0f9ff", edge="#0369a1", ink="#0c4a6e",
        key="No key seen on this plug \u2014 MARK the polarity before you unplug it.",
        fem=("FEMALE", "43645 + 43030"),
        mal=("MALE", "43640 + 43031"),
        rows=[
            ("K1", "M3\u2212", "#92400e", "brown", "brown \u2014 1 wire"),
            ("K2", "M3+", "#1d4ed8", "blue", "blue \u2014 1 wire"),
        ],
    ),
    dict(
        title="DRIVE TAP",
        socket="M1  socket",
        driver="driver M2",
        ab=["A", "B"],
        motor="both rear motors",
        tint="#fffbeb", edge="#b45309", ink="#78350f",
        key="Tabs keyed 90\u00b0 apart \u2014 this plug cannot go in REVERSED. It CAN be "
            "swapped with the power tap: same .250, same key. See FMEA row 12.",
        fem=("FEMALE", ".250 receptacle"),
        mal=("MALE", ".250 male tab"),
        rows=[
            ("K3", "horizontal tab", "#334155", "net A", "2 wires \u2014 pair preserved"),
            ("K4", "vertical tab", "#334155", "net B", "2 wires \u2014 pair preserved"),
        ],
    ),
]

ROW_H = 104
HEAD_H = 76
FOOT_H = 52


FITS = []          # (text, size, available width) - checked after the build


def box(x, y, w, h, fill, stroke, sw=2.2, rx=5):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')


def txt(x, y, s, size=12, weight="normal", fill="#0f172a", anchor="start"):
    return (f'<text x="{x}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{esc(s)}</text>')


def txt_in(bx, bw, y, s, size=12, weight="normal", fill="#0f172a"):
    """Centred inside a box, and REGISTERED so check() can prove it fits.

    The first draft put the wire colour on the arrows between the boxes, in
    gaps 36 px wide, and every one of those labels landed on top of its
    neighbour. check() passed anyway, because it only looked at rectangles.
    Text that belongs to a box now goes INSIDE the box and is measured."""
    FITS.append((s, size, bw - 10))
    return txt(bx + bw / 2, y, s, size, weight, fill, "middle")


def arrow(x1, y, x2, colour):
    return (f'<line x1="{x1}" y1="{y}" x2="{x2 - 9}" y2="{y}" stroke="{colour}" '
            f'stroke-width="3" marker-end="url(#a{colour[1:]})"/>')


def build():
    FITS.clear()
    out = []
    markers = {STOCK, NEW, DRIVER, "#92400e", "#1d4ed8", "#334155"}
    defs = "".join(
        f'<marker id="a{c[1:]}" markerWidth="10" markerHeight="10" refX="9" '
        f'refY="3.2" orient="auto"><path d="M0,0 L0,6.4 L9,3.2 z" fill="{c}"/></marker>'
        for c in sorted(markers))

    out.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" '
        f'width="{W}" height="{H}" '
        f'font-family="DejaVu Sans, Helvetica, Arial, sans-serif">')
    out.append("<title>Authority tap wiring - which connector half goes on which end</title>")
    out.append(
        "<desc>Each motor conductor runs from a tab on the stock module, through a "
        "receptacle MRider supplies, into a relay on 87a; the relay's 30 leaves on a tab "
        "MRider supplies and enters the vehicle's own plug on its way to the motor. The "
        "motor driver feeds 87. Nothing is cut: both taps are connectors the vehicle "
        "already has.</desc>")
    out.append(f"<defs>{defs}</defs>")
    out.append(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

    out.append(txt(24, 34, "Authority tap wiring \u2014 nothing is cut, and each half is the "
                           "gender opposite to the thing it mates", 18, "bold"))
    out.append(
        f'<text x="24" y="58" font-size="12.5" fill="#475569">'
        f'<tspan font-weight="bold" fill="{STOCK}">Grey = the vehicle\u2019s own parts.</tspan>'
        f'<tspan font-weight="bold" fill="{NEW}">  Green = what MRider buys.</tspan>'
        f'<tspan font-weight="bold" fill="{DRIVER}">  Purple = the motor driver.</tspan>'
        f'  Coil off \u2192 30 sits on 87a \u2192 the vehicle is factory stock.</text>')

    y = 78
    for tap in TAPS:
        h = HEAD_H + ROW_H * len(tap["rows"]) + FOOT_H
        out.append(box(24, y, W - 48, h, tap["tint"], tap["edge"], 2.4, 8))
        out.append(txt(44, y + 30, tap["title"], 15, "bold", tap["ink"]))
        out.append(txt(44, y + 52,
                       f"{tap['socket']} on the stock module  \u2192  {tap['motor']}",
                       12, "normal", tap["ink"]))

        cy = y + 70
        for cx, cw, cap in ((X_ECU, W_ECU, "STOCK MODULE"),
                            (X_FEM, W_FEM, "MRider buys"),
                            (X_REL, W_REL, "RELAY MUX"),
                            (X_MAL, W_MAL, "MRider buys"),
                            (X_VEH, W_VEH, "VEHICLE\u2019S OWN PLUG"),
                            (X_MOT, W_MOT, "MOTOR")):
            out.append(txt_in(cx, cw, cy, cap, 9.5, "bold", "#94a3b8"))

        for i, (relay, pad, col, wlabel, veh) in enumerate(tap["rows"]):
            ry = y + HEAD_H + ROW_H * i + ROW_H / 2

            out.append(box(X_ECU, ry - 26, W_ECU, 52, "#ffffff", STOCK))
            out.append(txt_in(X_ECU, W_ECU, ry - 5, pad, 13, "bold", "#334155"))
            out.append(txt_in(X_ECU, W_ECU, ry + 14, f"male tab \u00b7 {wlabel}", 10.5, "normal", col))

            out.append(arrow(X_ECU + W_ECU, ry, X_FEM, col))

            out.append(box(X_FEM, ry - 26, W_FEM, 52, "#ecfdf5", NEW, 2.6))
            out.append(txt_in(X_FEM, W_FEM, ry - 5, tap["fem"][0], 12.5, "bold", NEW))
            out.append(txt_in(X_FEM, W_FEM, ry + 14, tap["fem"][1], 9.5, "normal", NEW))

            out.append(arrow(X_FEM + W_FEM, ry, X_REL, col))

            out.append(box(X_REL, ry - 34, W_REL, 68, "#ffffff", "#334155", 2.6))
            out.append(txt(X_REL + 12, ry - 13, relay, 14, "bold", "#0f172a"))
            out.append(txt(X_REL + W_REL - 12, ry - 13, "30 \u2192", 13, "bold", "#0f172a", "end"))
            out.append(txt(X_REL + 12, ry + 7, "87a", 11.5, "bold", "#334155"))
            out.append(txt(X_REL + 44, ry + 7, "STOCK \u2014 coil off", 10.5, "normal", "#64748b"))
            out.append(txt(X_REL + 12, ry + 25, "87", 11.5, "bold", DRIVER))
            out.append(txt(X_REL + 44, ry + 25, f"{tap['driver']}{tap['ab'][i]} \u2014 coil on",
                           10.5, "normal", DRIVER))
            FITS.append((f"87a STOCK \u2014 coil off", 11.5, W_REL - 24))
            FITS.append((f"87 {tap['driver']}{tap['ab'][i]} \u2014 coil on", 11.5, W_REL - 24))

            out.append(arrow(X_REL + W_REL, ry, X_MAL, col))

            out.append(box(X_MAL, ry - 26, W_MAL, 52, "#ecfdf5", NEW, 2.6))
            out.append(txt_in(X_MAL, W_MAL, ry - 5, tap["mal"][0], 12.5, "bold", NEW))
            out.append(txt_in(X_MAL, W_MAL, ry + 14, tap["mal"][1], 9.5, "normal", NEW))

            out.append(arrow(X_MAL + W_MAL, ry, X_VEH, col))

            out.append(box(X_VEH, ry - 26, W_VEH, 52, "#ffffff", STOCK))
            out.append(txt_in(X_VEH, W_VEH, ry - 5, "female receptacle", 11.5, "bold", "#334155"))
            out.append(txt_in(X_VEH, W_VEH, ry + 14, veh, 10.5, "normal", col))

            out.append(arrow(X_VEH + W_VEH, ry, X_MOT, col))

            out.append(box(X_MOT, ry - 26, W_MOT, 52, "#f8fafc", STOCK))
            out.append(txt_in(X_MOT, W_MOT, ry + 3, tap["motor"], 11.5, "bold", "#334155"))

        fy = y + HEAD_H + ROW_H * len(tap["rows"]) + 26
        out.append(txt(44, fy, tap["key"], 11.5, "bold", tap["ink"]))

        y += h + 18

    out.append(txt(24, y + 20,
                   "Restoring the vehicle: unplug MRider\u2019s two assemblies and put the "
                   "vehicle\u2019s own plugs back on the module. No conductor was cut.",
                   12.5, "bold", "#334155"))
    out.append(txt(24, y + 42,
                   "Per vehicle: 2 taps \u00d7 (2 female + 2 male) = 4 female + 4 male. "
                   "Three vehicles: 12 female, 12 male, plus spares. The POWER tap is "
                   "a third .250 pair, drawn in traction-supply.svg.",
                   12.5, "normal", "#475569"))
    out.append(txt(24, y + 62,
                   "Steering, full numbers: 43645-0200 housing + 43030-0001 terminals "
                   "towards the module; 43640-0200 + 43031-0001 towards the plug. "
                   "Drive and power: .250 uninsulated, 16\u201314 AWG.",
                   12, "normal", "#475569"))
    out.append("</svg>")
    return "\n".join(out)


def check(svg):
    assert svg.count("STOCK \u2014 coil off") == 4, "the de-energised path must reach STOCK on every row"
    assert svg.count("coil on") == 4
    assert "STOCK \u2014 coil on" not in svg and "DBW" not in svg.replace("coil on", ""), (
        "de-energise-to-safe inverted - safety.md's failsafe matrix inverts with it")

    relays = [r for tap in TAPS for r, *_ in tap["rows"]]
    assert svg.count(">FEMALE<") == len(relays) and svg.count(">MALE<") == len(relays)
    toks = [m.group(1) for m in
            re.finditer(r">(FEMALE|MALE|" + "|".join(relays) + r")<", svg)]
    expected = [x for r in relays for x in ("FEMALE", r, "MALE")]
    assert toks == expected, f"row order is {toks}, expected {expected}"

    for tap in TAPS:
        for ab in tap["ab"]:
            assert f"{tap['driver']}{ab}" in svg
    assert "87a" in svg and svg.count("30 \u2192") == 4

    # text must fit the box it was drawn in - the check the first draft lacked
    # The canvas is a fixed H. check() has always measured text WIDTH against
    # its box and never measured whether the drawing still fits the page: on
    # 2026-11-07 a second footer line landed at y=848 of 850 and nothing would
    # have said so at 851. An SVG does not complain, it crops.
    ys = [float(m) for m in re.findall(r'y="([0-9.]+)"', svg)]
    assert ys, "no y coordinates - the figure is empty"
    assert max(ys) <= H - 8, (
        f"content reaches y={max(ys):.0f} on a {H} px canvas. Raise H.")

    for s, size, avail in FITS:
        w = len(s) * size * 0.60
        assert w <= avail, f"text {s!r} is ~{w:.0f} px in a {avail:.0f} px box"

    for m in re.finditer(r'<rect x="([\d.]+)" y="([\d.]+)" width="([\d.]+)" height="([\d.]+)"', svg):
        x, yy, w, h = map(float, m.groups())
        assert x >= 0 and yy >= 0 and x + w <= W and yy + h <= H, f"box {m.groups()} off canvas"

    cols = [(X_ECU, W_ECU), (X_FEM, W_FEM), (X_REL, W_REL),
            (X_MAL, W_MAL), (X_VEH, W_VEH), (X_MOT, W_MOT)]
    for (a, aw), (b, _) in zip(cols, cols[1:]):
        assert a + aw < b, f"column at {a} overlaps the next at {b}"
    assert X_MOT + W_MOT <= W - 24


if __name__ == "__main__":
    svg = build()
    check(svg)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT}  ({len(svg)} bytes)")
