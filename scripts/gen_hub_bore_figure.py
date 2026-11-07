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
r"""Hub and bore: which diameter is which, and how little margin the screw has.

    python3 scripts/gen_hub_bore_figure.py  # -> docs/images/hub-and-bore.svg

THE NUMBER THE HAND-DRAWN VERSION GOT WRONG, AND WHICH WAY
-----------------------------------------------------------
It said the grub screws "reach 3 mm past [the bore], five times what they must
close". Both halves are wrong, and they are wrong in the REASSURING direction,
which is the dangerous one:

    reach past the bore   SET_SCREW_L - WALL        = 1.00 mm, not 3
    must close, worst     (BORE_CLEAR + HUB_TOL)/2  = 0.95 mm
    margin                SET_SCREW_L - SPAN_MAX    = 0.05 mm

So it is 1.05x, not 5x. The 3 mm is a fossil of the M3 x 10 that #6d rejected
for standing 1.9-2.7 mm proud of the sensing surface: 10 - 7 = 3. The figure
told a builder there was loads of headroom where the .scad asserts there is
five hundredths of a millimetre.

LAYOUT IS FLOWED, NOT PLACED
----------------------------
Every panel keeps a y cursor and each block advances it. The grub-screw figure
grew a prose block by two lines and slid it under a callout, because the
callout's y was a constant. Here that is unexpressible: there are no constant
y values below a panel's heading.
"""
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carrier_params  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "images" / "hub-and-bore.svg"

W = 980
INK = "#0f172a"
MUTED = "#64748b"
BLUE = "#1e3a8a"
BLUE2 = "#2563eb"
AMBER = "#b45309"
RED = "#b91c1c"
DRED = "#7f1d1d"

FITS = []


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class Flow:
    """A column that remembers where it got to. Nothing below a heading has a
    constant y, so growing a block cannot push another block under a box."""

    def __init__(self, x, y, width):
        self.x, self.y, self.width = x, y, width
        self.out = []

    def text(self, s, size=11.5, weight="normal", fill=INK, gap=17, dx=0):
        self.y += gap
        FITS.append((s, size, self.x + dx, self.width - dx))
        self.out.append(
            f'<text x="{self.x + dx:.1f}" y="{self.y:.1f}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}">{esc(s)}</text>')
        return self

    def bullet(self, lead, rest, fill=DRED):
        self.y += 20
        self.out.append(
            f'<text x="{self.x:.1f}" y="{self.y:.1f}" font-size="11" fill="{fill}">'
            f'<tspan font-weight="bold">• {esc(lead)}</tspan> {esc(rest)}</text>')
        FITS.append((f"• {lead} {rest}", 11, self.x, self.width))
        return self

    def space(self, n=10):
        self.y += n
        return self

    def box(self, h, fill, stroke, sw=1.6, pad=0):
        self.y += 10
        self.out.append(
            f'<rect x="{self.x - pad:.1f}" y="{self.y:.1f}" '
            f'width="{self.width + 2 * pad:.1f}" height="{h:.1f}" rx="6" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
        top = self.y
        self.y += h
        return top

    def raw(self, s):
        self.out.append(s)
        return self


def lobed_ring(cx, cy, r, n, amp, fill, stroke, sw=2.0):
    pts = []
    for i in range(n * 36 + 1):
        a = 2 * math.pi * i / (n * 36)
        rr = r - amp * (1 - math.cos(n * a)) / 2
        pts.append(f"{cx + rr * math.cos(a):.1f},{cy + rr * math.sin(a):.1f}")
    return (f'<polygon points="{" ".join(pts)}" fill="{fill}" stroke="{stroke}" '
            f'stroke-width="{sw}"/>')


def dim(x1, y, x2, label, col=BLUE):
    return (f'<line x1="{x1:.1f}" y1="{y:.1f}" x2="{x2:.1f}" y2="{y:.1f}" '
            f'stroke="{col}" stroke-width="1.6"/>'
            f'<text x="{(x1 + x2) / 2:.1f}" y="{y - 6:.1f}" font-size="12" '
            f'font-weight="bold" fill="{col}" text-anchor="middle">{esc(label)}</text>')


def build(d):
    reach = d["SET_SCREW_L"] - d["WALL"]            # past the bore, into the gap
    close_nom = d["BORE_CLEAR"] / 2                  # nominal, per side
    close_max = (d["BORE_CLEAR"] + d["HUB_TOL"]) / 2  # worst case, per side
    margin = d["SET_SCREW_L"] - d["SPAN_MAX"]
    ratio = reach / close_max

    o = []
    # ---- two top panels ---------------------------------------------------
    # PH used to be a constant 300 while the captions below each circle were
    # placed at cy + 164 and cy + 180, so they fell OUTSIDE the panel. That is
    # the same defect the flowed bottom panel exists to prevent; it simply
    # survived in the half still placed by hand. The panel now measures its
    # own contents.
    CY = 262
    CAP1, CAP2 = CY + 164, CY + 180
    PH = CAP2 + 22 - 100
    for i, (px, title, sub) in enumerate((
            (24, "HUB — on the vehicle. It ROTATES.",
             "An OUTSIDE diameter. Nothing is printed here; you measure it."),
            (504, "BORE — in the printed carrier. It is a HOLE.",
             "An INSIDE diameter. Nothing is measured here; you print it."))):
        o.append(f'<rect x="{px}" y="100" width="452" height="{PH}" rx="8" '
                 f'fill="#f8fafc" stroke="#334155" stroke-width="2"/>')
        f = Flow(px + 20, 100, 412)
        f.text(title, 13.5, "bold", INK, gap=28)
        f.text(sub, 11, "normal", MUTED, gap=18)
        o += f.out

        cx, cy = px + 226, CY
        if i == 0:
            o.append(lobed_ring(cx, cy, 86, d["N_LOBE"], 16, "#dbe3ec", "#64748b"))
            o.append(f'<circle cx="{cx}" cy="{cy}" r="12" fill="#fff" '
                     f'stroke="#475569" stroke-width="2"/>')
            o.append(f'<text x="{cx}" y="{cy + 4}" font-size="10" fill="{MUTED}" '
                     f'text-anchor="middle">axle</text>')
            o.append(dim(cx - 86, cy + 118, cx + 86,
                         f"Ø{d['HUB_D']:.2f}  crest to crest"))
            o.append(f'<text x="{cx}" y="{cy + 134}" font-size="10.5" fill="{RED}" '
                     f'text-anchor="middle">root Ø is NOT this one</text>')
            o.append(f'<text x="{px + 20}" y="{CAP1}" font-size="10.5" '
                     f'fill="{MUTED}">{d["N_LOBE"]} lobes is an EVEN count, so opposite '
                     f'crests face each other</text>')
            o.append(f'<text x="{px + 20}" y="{CAP2}" font-size="10.5" '
                     f'fill="{MUTED}">and a caliper reads the crest circle straight off. '
                     f'Three positions.</text>')
        else:
            o.append(f'<circle cx="{cx}" cy="{cy}" r="100" fill="#fde68a" '
                     f'stroke="{AMBER}" stroke-width="2.4"/>')
            o.append(f'<circle cx="{cx}" cy="{cy}" r="82" fill="#ffffff" '
                     f'stroke="#94a3b8" stroke-width="1.8"/>')
            o.append(dim(cx - 82, cy + 128, cx + 82,
                         f"Ø{d['BORE_D']:.2f}  the bore"))
            o.append(f'<text x="{cx}" y="{cy + 148}" font-size="11.5" '
                     f'font-weight="bold" fill="{AMBER}" text-anchor="middle">'
                     f'Ø{d["OD"]:.2f} — the carrier’s OUTSIDE Ø, '
                     f'the magnet track</text>')
            o.append(f'<text x="{px + 20}" y="{CAP1}" font-size="10.5" '
                     f'fill="{MUTED}">Two diameters on one part. The bore faces the HUB,'
                     f'</text>')
            o.append(f'<text x="{px + 20}" y="{CAP2}" font-size="10.5" '
                     f'fill="{MUTED}">the OD faces the SENSOR.</text>')

    # ---- bottom panel, flowed ----
    top = 100 + PH + 20
    f = Flow(44, top, 892)
    f.text("TOGETHER — the bore is bigger than the hub, ON PURPOSE",
           13.5, "bold", AMBER, gap=30)
    f.text(f"Ø{d['BORE_D']:.2f} bore − Ø{d['HUB_D']:.2f} hub = "
           f"{d['BORE_CLEAR']:.2f} mm on diameter, {close_nom:.2f} mm per side. "
           f"It is SUPPOSED to rattle.", 12, "normal", "#78350f", gap=24)
    f.text("The three grub screws remove the rattle. The bore never does.",
           12, "normal", "#78350f", gap=18)

    bt = f.box(118, "#fef2f2", "#dc2626", 1.8, pad=8)
    g = Flow(60, bt, 860)
    g.text("And they do it with 0.05 mm to spare, not with room to burn.",
           12.5, "bold", DRED, gap=24)
    rows = [("a screw reaches past the bore",
             f"SET_SCREW_L {d['SET_SCREW_L']:.1f} − WALL {d['WALL']:.1f}",
             f"{reach:.2f} mm"),
            ("worst case it must close, per side",
             f"(BORE_CLEAR {d['BORE_CLEAR']:.1f} + HUB_TOL {d['HUB_TOL']:.1f}) / 2",
             f"{close_max:.2f} mm"),
            ("so the margin is",
             f"SET_SCREW_L − SPAN_MAX {d['SPAN_MAX']:.2f}",
             f"{margin:.2f} mm  ({ratio:.2f}×)")]
    for k, how, v in rows:
        g.y += 20
        g.out.append(f'<text x="60" y="{g.y:.1f}" font-size="11" fill="{DRED}">'
                     f'{esc(k)}</text>')
        g.out.append(f'<text x="430" y="{g.y:.1f}" font-size="10.5" fill="#b45309">'
                     f'{esc(how)}</text>')
        g.out.append(f'<text x="912" y="{g.y:.1f}" font-size="11.5" '
                     f'font-weight="bold" fill="{DRED}" text-anchor="end">'
                     f'{esc(v)}</text>')
    f.out += g.out
    f.y = max(f.y, g.y + 14)

    f.text("Three ways this has already gone wrong", 12.5, "bold", INK, gap=30)
    f.bullet("The fixed grey collar around the hub is not the hub.",
             "It does not rotate — that one takes the sensor bracket.")
    f.bullet("Root Ø is not crest Ø.",
             "The bore has to clear the CRESTS, which is the larger of the two.")
    f.bullet("A wrap measures π(D + its own thickness).",
             "A 2 mm wire read 205 mm, put the hub 2.3 mm high, and a ring "
             "was printed 4 mm oversize.")
    f.space(14)

    H = int(f.y + 24)
    head = ['<svg xmlns="http://www.w3.org/2000/svg" '
            f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
            'font-family="DejaVu Sans, Helvetica, Arial, sans-serif">',
            '<title>Hub and bore - which diameter is which</title>',
            '<desc>Three panels. Left: the hub, the lobed rotating boss on the '
            'vehicle, an outside diameter measured across two opposite crests. '
            'Right: the bore, the hole through the printed carrier, and the '
            'carrier’s own larger outside diameter which carries the magnets. '
            'Bottom: the two together, the deliberate clearance between them, and '
            'the arithmetic showing a grub screw clears the worst-case gap by five '
            'hundredths of a millimetre - not by the wide margin an earlier version '
            'of this figure claimed.</desc>',
            f'<rect width="{W}" height="{H}" fill="#ffffff"/>',
            f'<text x="24" y="36" font-size="19" font-weight="bold" fill="{INK}">'
            'Hub and bore — one is on the vehicle, the other is a hole in the '
            'print</text>',
            f'<text x="24" y="58" font-size="12" fill="{MUTED}">Both are diameters '
            'near 63 mm, which is why they keep getting swapped. Neither is a '
            'fit.</text>',
            f'<text x="24" y="76" font-size="11" fill="{MUTED}">Every figure here is '
            f'read from cad/{carrier_params.SCAD.name}.</text>',
            f'<rect x="24" y="{top}" width="{W - 48}" height="{H - top - 16}" rx="8" '
            f'fill="#fffbeb" stroke="{AMBER}" stroke-width="2"/>']
    return "\n".join(head + o + f.out + ['</svg>']), H, dict(
        reach=reach, close_max=close_max, margin=margin, ratio=ratio)


def check(svg, H, d, v):
    ys = [float(m) for m in re.findall(r'y="([0-9.]+)"', svg)]
    assert max(ys) <= H - 8, f"content reaches y={max(ys):.0f} on {H}"
    # FITS carries the AVAILABLE WIDTH from x, not an absolute limit.
    for s_, size, _x, avail in FITS:
        w = len(s_) * size * 0.54
        assert w <= avail, f"text {s_!r} is ~{w:.0f} px in a {avail:.0f} px column"
    # the arithmetic the old figure stated backwards
    assert abs(v["reach"] - 1.00) < 1e-9, v["reach"]
    assert v["ratio"] < 1.2, (
        f"the screw clears the worst-case gap by {v['ratio']:.2f}x; if this ever "
        f"rises the panel's whole point has changed and the text must too")
    assert abs(v["margin"] - (d["SET_SCREW_L"] - d["SPAN_MAX"])) < 1e-9
    for want in (f"{d['HUB_D']:.2f}", f"{d['BORE_D']:.2f}", f"{d['OD']:.2f}",
                 f"{v['margin']:.2f}"):
        assert want in svg, f"{want} missing from the figure"


def main():
    d = carrier_params.load()
    svg, H, v = build(d)
    check(svg, H, d, v)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}  H={H}  reach={v['reach']:.2f} "
          f"close={v['close_max']:.2f} margin={v['margin']:.2f} "
          f"({v['ratio']:.2f}x)  "
          f"{'cross-checked' if d['_checked'] else 'NOT cross-checked'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
