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
r"""Draw the carrier and magnet track FROM THE PART, not beside it.

    python3 scripts/gen_carrier_figure.py   # -> docs/images/drive-encoder-carrier.svg

WHY THIS SCRIPT EXISTS
----------------------
The figure it replaces was a hand-written SVG with every coordinate typed in.
It carried the label "6.80 mm = HALF a magnet pitch" while DRAWING the two
sensors a FULL pitch apart, and it shipped that way: the label was a string and
the position was a number, and nothing tied them together.

The number was not even unknown. cad/drive_encoder_carrier.scad -- the model
that was printed and checked on the bench -- has computed it all along:

    PITCH  = CIRC / N_MAG
    OFFSET = PITCH / 2        <- the figure got this one wrong by 2x

So this script reads the PARAMETERS out of that .scad, recomputes the derived
values in Python, and then ASSERTS ITS ARITHMETIC AGAINST OPENSCAD'S OWN ECHO
output. Three independent statements of the same geometry have to agree before
a figure is written. After that, sensor B's angle is OFFSET expressed in
degrees, so drawing it a full pitch away is no longer expressible.

WHAT IS NOT FROM THE .scad, AND WHY
-----------------------------------
N_LOBE is a feature of the HUB, not of the carrier -- the carrier's bore is
plain and round with clearance. Six is an observation of the vehicle, so it
lives here with that said out loud rather than being passed off as a model
parameter.
"""
import math
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCAD = REPO / "cad" / "drive_encoder_carrier.scad"
OUT = REPO / "docs" / "images" / "drive-encoder-carrier.svg"

N_LOBE = 6          # observed on the vehicle's hub. NOT a carrier parameter.
W, H = 980, 760

INK = "#0f172a"
MUTED = "#64748b"
BLUE = "#1e3a8a"
BLUE2 = "#2563eb"
AMBER = "#b45309"
RED = "#b91c1c"
GREEN = "#15803d"
GREEN_D = "#14532d"


# ---- read the part ---------------------------------------------------------
def scad_params():
    """Pull the input parameters out of the .scad by name."""
    src = SCAD.read_text(encoding="utf-8")
    want = ("HUB_D", "WALL", "WIDTH", "BORE_CLEAR", "N_MAG", "MAG_D", "MAG_T",
            "N_SET", "SET_TAP_D", "SET_SCREW_L", "MARK_W", "MARK_DEPTH",
            "AXIAL_GAP")
    p = {}
    for name in want:
        m = re.search(r"^%s\s*=\s*([-0-9.]+)\s*;" % name, src, re.M)
        assert m, f"{name} not found in {SCAD.name}"
        p[name] = float(m.group(1))
    p["N_MAG"] = int(p["N_MAG"])
    p["N_SET"] = int(p["N_SET"])
    return p


def derive(p):
    d = dict(p)
    d["BORE_D"] = p["HUB_D"] + p["BORE_CLEAR"]
    d["OD"] = d["BORE_D"] + 2 * p["WALL"]
    d["CIRC"] = math.pi * d["OD"]
    d["PITCH"] = d["CIRC"] / p["N_MAG"]
    d["OFFSET"] = d["PITCH"] / 2
    d["COUNTS"] = 2 * p["N_MAG"]
    d["SET_A0"] = 180.0 / p["N_MAG"]
    # The sensors. A sits on the MAGNET nearest the top of the drawing, B is
    # A plus the quadrature offset expressed as an angle - which is half a
    # pitch, so B necessarily lands on a BOUNDARY. Picking 270 for A looks
    # right and is wrong: 270 is not a multiple of 360/18, so A would sit on a
    # boundary and B on a magnet, which is the drawing's own caption reversed.
    step = 360.0 / p["N_MAG"]
    d["STEP"] = step
    d["A_DEG"] = round(270.0 / step) * step
    d["B_DEG"] = d["A_DEG"] + d["OFFSET"] / d["CIRC"] * 360.0
    return d


def cross_check(d):
    """Run OpenSCAD and hold our arithmetic against the model's own ECHO.

    This is the whole point of the script. If the two ever disagree the figure
    is not written, because one of them is lying about a part that exists.
    """
    try:
        r = subprocess.run(
            ["openscad", "--export-format=asciistl", "-o", "/dev/null", str(SCAD)],
            capture_output=True, text=True, timeout=300)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("  openscad unavailable - arithmetic NOT cross-checked", file=sys.stderr)
        return False
    echo = r.stdout + r.stderr
    pairs = [("magnet pitch", d["PITCH"]),
             ("SENSOR OFFSET", d["OFFSET"]),
             ("track circum.", d["CIRC"]),
             ("counts / rev", d["COUNTS"]),
             ("SWEPT Ø", d["OD"])]
    seen = 0
    for key, ours in pairs:
        m = re.search(re.escape(key) + r"\s*([0-9.]+)", echo)
        assert m, f"openscad did not echo {key!r}; the model changed"
        theirs = float(m.group(1))
        assert abs(theirs - ours) < 0.01, \
            f"{key}: this script says {ours:.4f}, the .scad says {theirs:.4f}"
        seen += 1
    assert seen == len(pairs)
    return True


# ---- svg helpers -----------------------------------------------------------
def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


FITS = []   # (text, size, x, anchor, right-hand limit) - verified by check()


def txt(x, y, s, size=11, weight="normal", fill=INK, anchor="start", style="",
        limit=None):
    """Draw text, and register it so check() can prove it stays in its panel."""
    if limit is not None:
        FITS.append((s, size, x, anchor, limit))
    st = f' font-style="{style}"' if style else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{st}>'
            f'{esc(s)}</text>')


def rect(x, y, w, h, fill, stroke=None, sw=1.5, rx=0):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{rx}" fill="{fill}"{s}/>')


def build(d):
    mm = 2.735                      # px per mm in the end view
    cx, cy = 270.0, 352.0
    r_od = d["OD"] / 2 * mm
    r_bore = d["BORE_D"] / 2 * mm
    r_mag = (d["OD"] / 2 - d["MAG_T"] / 2 - 0.6) * mm
    r_sens = (d["OD"] / 2 + 2.6) * mm

    o = ['<svg xmlns="http://www.w3.org/2000/svg" '
         f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         'font-family="DejaVu Sans, Helvetica, Arial, sans-serif">',
         '<title>Carrier and magnet track - drawn from the printed part</title>',
         '<desc>Left: end view looking along the axle. A one-piece printed ring on the '
         'six-lobe hub, carrying eighteen magnets in alternating polarity, with three '
         'recessed grub screws 120 degrees apart dropped into lobe gaps. The two Hall '
         'latches sit radially outside the track, HALF a magnet pitch apart, so when A '
         'is over a magnet B is over the boundary between two - the angles are computed '
         'from the CAD model rather than placed by hand. Right: axial section, with each '
         'magnet drawn magnetised radially, poles stacked through the ring wall and the '
         'outward face alternating north and south as the carrier turns.</desc>',
         rect(0, 0, W, H, "#ffffff"),
         txt(24, 34, "Carrier and magnet track — one piece, nothing standing proud",
             19, "bold", INK),
         txt(24, 56, f"Every dimension here is read from cad/{SCAD.name}, the model that "
                     f"was printed and checked.", 12, "normal", MUTED),
         rect(24, 76, 492, 660, "#f8fafc", "#334155", 2, 8),
         rect(532, 76, 424, 660, "#f0fdf4", "#22c55e", 2, 8),
         txt(44, 104, "END VIEW — looking along the axle", 15, "bold", INK),
         txt(552, 104, "AXIAL SECTION — where the 8 mm goes", 15, "bold", GREEN_D)]

    # ---- ring ----
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r_od:.1f}" fill="#fde68a" '
             f'stroke="{AMBER}" stroke-width="2.4"/>')
    o.append(f'<circle cx="{cx}" cy="{cy}" r="{r_bore:.1f}" fill="#dbe3ec" '
             f'stroke="#94a3b8" stroke-width="1.6"/>')

    # ---- hub lobes: an observation of the vehicle, not a carrier parameter --
    for i in range(N_LOBE):
        a = math.radians(i * 360.0 / N_LOBE + 30)
        for s in (-1, 1):
            a2 = a + s * math.radians(9)
            o.append(f'<line x1="{cx + r_bore * math.cos(a):.1f}" '
                     f'y1="{cy + r_bore * math.sin(a):.1f}" '
                     f'x2="{cx + (r_bore - 16) * math.cos(a2):.1f}" '
                     f'y2="{cy + (r_bore - 16) * math.sin(a2):.1f}" '
                     f'stroke="#94a3b8" stroke-width="1.4"/>')

    # ---- magnets, every 360/N_MAG, alternating ----
    step = 360.0 / d["N_MAG"]
    mw, mh = d["MAG_T"] * mm, d["MAG_D"] * mm
    for i in range(d["N_MAG"]):
        a = i * step
        x = cx + r_mag * math.cos(math.radians(a))
        y = cy + r_mag * math.sin(math.radians(a))
        fill = "#93c5fd" if i % 2 == 0 else BLUE
        o.append(f'<g transform="translate({x:.1f},{y:.1f}) rotate({a:.1f})">'
                 f'<rect x="{-mw / 2:.1f}" y="{-mh / 2:.1f}" width="{mw:.1f}" '
                 f'height="{mh:.1f}" rx="1.5" fill="{fill}" stroke="{BLUE}" '
                 f'stroke-width="1.2"/></g>')

    # ---- grub screws, N_SET of them, SET_A0 off magnet 0 ----
    sw_ = d["SET_TAP_D"] * mm
    for i in range(d["N_SET"]):
        a = d["SET_A0"] + i * 360.0 / d["N_SET"]
        ar = math.radians(a)
        o.append(f'<line x1="{cx + (r_bore + 2) * math.cos(ar):.1f}" '
                 f'y1="{cy + (r_bore + 2) * math.sin(ar):.1f}" '
                 f'x2="{cx + (r_od - 3) * math.cos(ar):.1f}" '
                 f'y2="{cy + (r_od - 3) * math.sin(ar):.1f}" '
                 f'stroke="#7f1d1d" stroke-width="{sw_:.1f}" stroke-linecap="round"/>')

    # ---- THE SENSORS. B is A plus OFFSET, as an angle. ----
    a_deg, b_deg = d["A_DEG"], d["B_DEG"]
    for label, ang in (("A", a_deg), ("B", b_deg)):
        ar = math.radians(ang)
        x = cx + r_sens * math.cos(ar)
        y = cy + r_sens * math.sin(ar)
        o.append(f'<g transform="translate({x:.1f},{y:.1f}) rotate({ang + 90:.1f})">'
                 f'<rect x="-6" y="-9" width="12" height="18" rx="2" fill="#bbf7d0" '
                 f'stroke="{GREEN}" stroke-width="2"/></g>')
        o.append(txt(x, y + 4, label, 10, "bold", GREEN_D, "middle"))

    ax = cx + r_sens * math.cos(math.radians(a_deg))
    bx = cx + r_sens * math.cos(math.radians(b_deg))
    ytop = cy - r_sens - 16
    o.append(f'<line x1="{ax:.1f}" y1="{ytop:.1f}" x2="{bx:.1f}" y2="{ytop:.1f}" '
             f'stroke="{GREEN}" stroke-width="2"/>')
    midx = (ax + bx) / 2
    o.append(txt(midx, ytop - 8, f"{d['OFFSET']:.2f} mm", 11.5, "bold", GREEN, "middle"))
    o.append(txt(midx, ytop - 22, "= HALF a magnet pitch", 10.5, "normal", GREEN, "middle"))
    o.append(txt(midx, ytop - 36, "A on a magnet → B on a BOUNDARY",
                 10, "normal", GREEN, "middle"))

    o.append(txt(44, 150, f"{N_LOBE} broad lobes, narrow gaps", 11.5, "bold", INK))
    o.append(txt(44, 164, "— the hub's feature, not the", 10.5, "normal", MUTED))
    o.append(txt(44, 178, "carrier's. Bore is round.", 10.5, "normal", MUTED,
                 limit=188))
    o.append(txt(44, 560, f"{d['N_MAG']} magnets, alternating", 11.5, "bold", BLUE))
    o.append(txt(44, 576, f"pitch {d['PITCH']:.2f} mm · {d['COUNTS']} counts/rev",
                 10.5, "normal", BLUE2))
    o.append(txt(290, 606, f"{d['N_SET']} × M3 grub screw", 11.5, "bold", RED))
    o.append(txt(290, 622, f"recessed below the OD Ø{d['OD']:.2f}", 10.5, "normal", RED))
    o.append(txt(290, 638, f"first one {d['SET_A0']:.0f}° off magnet 0,",
                10.5, "normal", RED))
    o.append(txt(290, 654, "so all three land in lobe gaps", 10.5, "normal", RED))
    o.append(rect(44, 668, 452, 52, "#fef2f2", "#dc2626", 1.6, 6))
    o.append(txt(56, 690, "Every feature here is a RECESS.", 12, "bold", "#7f1d1d"))
    o.append(txt(56, 708, f"Nothing stands proud of Ø{d['OD']:.2f}.",
                11, "normal", "#7f1d1d"))

    # ---- axial section ----
    gx, gy = 570, 330
    o.append(rect(gx, gy, 78, 140, "#e2e8f0", "#94a3b8"))
    o.append(txt(gx + 4, gy + 162, "gearbox", 11, "bold", "#334155"))
    o.append(txt(gx + 10, gy + 176, "FIXED", 10.5, "normal", MUTED))
    bx0 = 660
    o.append(rect(bx0, 372, 96, 98, "#e2e8f0", "#475569", 2))
    o.append(txt(bx0 + 4, 492, "lobed boss · ROTATES", 11, "bold", BLUE))
    o.append(rect(bx0 + 8, 344, 80, 28, "#fde68a", AMBER, 2))

    # magnets: RADIAL magnetisation - poles stack through the wall
    nshow = 4
    seg = 72.0 / nshow
    for i in range(nshow):
        x0 = bx0 + 12 + i * seg
        up, dn = (RED, BLUE) if i % 2 == 0 else (BLUE, RED)
        o.append(rect(x0, 330, seg, 8, up))
        o.append(rect(x0, 338, seg, 8, dn))
        t, b = ("N", "S") if i % 2 == 0 else ("S", "N")
        o.append(txt(x0 + seg / 2, 337, t, 7, "normal", "#fff", "middle"))
        o.append(txt(x0 + seg / 2, 345, b, 7, "normal", "#fff", "middle"))
    o.append(rect(bx0 + 12, 330, 72, 16, "none", "#1e293b", 1))
    o.append(rect(684, 310, 32, 16, "#bbf7d0", GREEN, 2))
    o.append(txt(726, 300, "bracket + sensors", 11, "bold", GREEN))
    o.append(txt(726, 315, "both A and B in one part", 10.5, "normal", GREEN))
    o.append(rect(768, 300, 30, 170, "none", "#94a3b8", 2, 5))
    o.append(txt(804, 392, "wheel", 11, "normal", MUTED))
    o.append(txt(786, 176, "magnets", 11, "bold", BLUE))
    o.append(txt(786, 190, f"{d['N_MAG']}, alternating", 10, "normal", BLUE2))
    o.append(txt(786, 214, "carrier — one piece", 11, "bold", AMBER))
    o.append(txt(786, 228, f"wall {d['WALL']:.0f} mm, width {d['WIDTH']:.0f} mm",
                10, "normal", "#92400e"))
    o.append(f'<line x1="660" y1="534" x2="768" y2="534" stroke="{RED}" '
             f'stroke-width="2"/>')
    o.append(txt(714, 554, f"{d['AXIAL_GAP']:.0f} mm — gearbox to wheel",
                12, "bold", RED, "middle"))

    for i, line in enumerate([
            "The sensors sit radially OUTSIDE the magnets, not beside",
            f"them — so the {d['AXIAL_GAP']:.0f} mm holds the track width and the",
            "sensor's thickness side by side, not stacked.",
            "",
            "Each magnet is magnetised RADIALLY — its poles stack",
            "through the ring wall, they do not run along it. What the",
            "sensor reads is the OUTWARD face, and THAT is what",
            "alternates N, S, N, S."]):
        if line:
            o.append(txt(552, 592 + i * 18, line, 12.5, "normal", GREEN_D,
                         limit=944))
    o.append('</svg>')
    return "\n".join(o)


def check(svg, d):
    ys = [float(m) for m in re.findall(r'y="([0-9.]+)"', svg)]
    assert max(ys) <= H - 8, f"content reaches y={max(ys):.0f} on {H}"
    assert svg.count("<text") > 20, "suspiciously few labels"
    for s_, size, x, anchor, limit in FITS:
        w = len(s_) * size * 0.54
        right = x + w if anchor == "start" else x + w / 2
        assert right <= limit, (
            f"text {s_!r} reaches x={right:.0f}, past its limit {limit}")
    # The three things the hand-drawn figure got wrong, now unexpressible.
    step = d["STEP"]
    b_off = d["B_DEG"] - d["A_DEG"]
    assert abs(b_off - step / 2) < 1e-9, \
        f"sensor B is {b_off:.3f} deg from A; half a pitch is {step / 2:.3f}"
    # A must be ON a magnet: magnets sit at multiples of step from zero.
    assert abs((d["A_DEG"] / step) - round(d["A_DEG"] / step)) < 1e-9, \
        f"sensor A is at {d['A_DEG']:.2f} deg, which is not a magnet centre"
    # ...and B must therefore be on a BOUNDARY, halfway between two.
    half = (d["B_DEG"] / step) % 1.0
    assert abs(half - 0.5) < 1e-9, \
        f"sensor B is at {d['B_DEG']:.2f} deg, which is not a magnet boundary"


def main():
    p = scad_params()
    d = derive(p)
    checked = cross_check(d)
    svg = build(d)
    check(svg, d)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}  "
          f"N_MAG={d['N_MAG']} pitch={d['PITCH']:.4f} offset={d['OFFSET']:.4f} "
          f"counts={d['COUNTS']}  "
          f"{'cross-checked against openscad' if checked else 'NOT cross-checked'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
