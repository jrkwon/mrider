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
r"""Grub-screw point types against the seat they actually land on.

    python3 scripts/gen_grub_screw_figure.py  # -> docs/images/grub-screw-points.svg

WHY THIS ONE WAS WORTH GENERATING FIRST
----------------------------------------
The hand-written figure it replaces quoted three numbers and got all three
wrong, and one of them has a physical consequence rather than an embarrassing
one:

    drawn            the model computes
    0.10-0.70 mm     0.05-0.75 mm   stand-off of a seated screw past the OD
    span 7.90 mm     7.25-7.95 mm   what the screw has to cross to a crest

The .scad says of the stand-off: "set the air gap ABOVE this". Believe 0.70,
set a 0.72 mm air gap, and a worst-case screw at 0.75 sweeps the sensor -
which is the exact failure the two-piece carrier was abandoned for, where the
clamp ears stood 9 mm out.

Every number here now comes from carrier_params, which reads the .scad and
holds its arithmetic against OpenSCAD's own echo output.

WHAT IS DRAWN AND WHAT IS ASSERTED
-----------------------------------
The point-type profiles are a drawing of a standard; they are shapes, not
dimensions, and nothing checks them. The NUMBERS are checked, and so is the
one geometric claim the figure makes: that N_SET screws at 360/N_SET degrees
land on lobe crests, which is only true when N_LOBE and N_SET share a phase.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carrier_params  # noqa: E402

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "docs" / "images" / "grub-screw-points.svg"

W, H = 1020, 844
INK = "#0f172a"
MUTED = "#64748b"
RED = "#b91c1c"
DRED = "#7f1d1d"
GREEN = "#15803d"
AMBER = "#b45309"
BLUE = "#1e3a8a"

FITS = []
SCREWS = []     # x of each screw in panel B, checked against the crests


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def txt(x, y, s, size=11, weight="normal", fill=INK, anchor="start", limit=None):
    if limit is not None:
        FITS.append((s, size, x, anchor, limit))
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">'
            f'{esc(s)}</text>')


def rect(x, y, w, h, fill, stroke=None, sw=1.5, rx=0):
    s = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ""
    return (f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" '
            f'rx="{rx}" fill="{fill}"{s}/>')


def point_profile(x, y, kind):
    """A grub screw in profile, 44 wide, tip pointing down."""
    o = [rect(x - 11, y - 44, 22, 36, "#cbd5e1", "#475569", 1.4)]
    for i in range(5):                       # thread hatching
        o.append(f'<line x1="{x - 11}" y1="{y - 40 + i * 7}" x2="{x + 11}" '
                 f'y2="{y - 37 + i * 7}" stroke="#94a3b8" stroke-width="0.9"/>')
    if kind == "flat":
        o.append(rect(x - 11, y - 8, 22, 8, "#cbd5e1", "#475569", 1.4))
    elif kind == "cup":
        o.append(f'<path d="M{x - 11},{y - 8} L{x - 11},{y} L{x - 5},{y - 3} '
                 f'L{x + 5},{y - 3} L{x + 11},{y} L{x + 11},{y - 8} Z" '
                 f'fill="#cbd5e1" stroke="#475569" stroke-width="1.4"/>')
    elif kind == "cone":
        o.append(f'<path d="M{x - 11},{y - 8} L{x},{y + 2} L{x + 11},{y - 8} Z" '
                 f'fill="#cbd5e1" stroke="#475569" stroke-width="1.4"/>')
    else:                                     # dog
        o.append(rect(x - 11, y - 8, 22, 4, "#cbd5e1", "#475569", 1.4))
        o.append(rect(x - 5, y - 4, 10, 10, "#cbd5e1", "#475569", 1.4))
    return "".join(o)


def lobed_hub(x0, y0, w, amp, n):
    """A crest-and-valley profile, drawn flat. Crests are where screws land."""
    pts = []
    for i in range(n * 24 + 1):
        t = i / (n * 24)
        import math
        pts.append((x0 + t * w, y0 - amp * math.cos(2 * math.pi * n * t)))
    d = " ".join(f"{'M' if i == 0 else 'L'}{px:.1f},{py:.1f}"
                 for i, (px, py) in enumerate(pts))
    return (f'<path d="{d}" fill="none" stroke="#94a3b8" stroke-width="2.4"/>',
            pts)


def build(d):
    o = ['<svg xmlns="http://www.w3.org/2000/svg" '
         f'viewBox="0 0 {W} {H}" width="{W}" height="{H}" '
         'font-family="DejaVu Sans, Helvetica, Arial, sans-serif">',
         '<title>Grub-screw point types against the seat they actually land on'
         ' - a convex lobe crest</title>',
         '<desc>Top: the four set-screw point types in profile, flat, cup, cone '
         'and dog, each with the contact it makes on a convex crest and a verdict. '
         'Bottom left: the carrier wall over the lobed hub, with the screws seating '
         'on crests as the length calculation assumes, and the flank, which is the '
         'seat that causes trouble because three screws sharing a lobe phase push '
         'the ring off centre together. Bottom right: the seating check in '
         'millimetres, every figure read from the CAD model, and the witness '
         'mark.</desc>',
         rect(0, 0, W, H, "#ffffff"),
         txt(24, 34, "Grub-screw point types against the seat they actually land on",
             19, "bold", INK),
         txt(24, 56, f"HUB_D is measured across opposite lobe crests, so every span "
                     f"below is a distance to a CREST. All figures read from "
                     f"cad/{carrier_params.SCAD.name}.", 11.5, "normal", MUTED)]

    # ---- A: the four point types -------------------------------------------
    o.append(rect(24, 76, W - 48, 212, "#f8fafc", "#334155", 2, 8))
    o.append(txt(44, 104, "A · Four points, and what each one does on a CONVEX crest",
                 14, "bold", INK))
    kinds = [("flat", "평면 · FLAT", "DIN 913",
              "line contact along the crest", "✓ adequate — and in hand", GREEN),
             ("cup", "컵 · CUP", "DIN 916",
              "rim straddles the ridge", "✓ better — an upgrade", GREEN),
             ("cone", "콘 · CONE", "DIN 914",
              "one point on the apex", "△ wants to slide off", AMBER),
             ("dog", "돌출 · DOG", "DIN 915",
              "needs a matching hole", "✗ wrong anywhere here", RED)]
    for i, (kind, name, din, contact, verdict, col) in enumerate(kinds):
        cx = 150 + i * 232
        o.append(point_profile(cx, 196, kind))
        o.append(f'<path d="M{cx - 40},206 Q{cx},198 {cx + 40},206" fill="none" '
                 f'stroke="#94a3b8" stroke-width="2.2"/>')
        o.append(txt(cx, 132, name, 12.5, "bold", INK, "middle"))
        o.append(txt(cx, 147, din, 10.5, "normal", MUTED, "middle"))
        o.append(txt(cx, 232, contact, 10.5, "normal", MUTED, "middle", limit=cx + 110))
        o.append(txt(cx, 250, verdict, 11, "bold", col, "middle", limit=cx + 110))
    o.append(txt(44, 274, "The seat is CONVEX, which is why a flat face is "
                          "acceptable here and a cone is not.", 11, "normal", MUTED))

    # ---- B: the section ----------------------------------------------------
    o.append(rect(24, 300, 592, 516, "#fffbeb", AMBER, 2, 8))
    o.append(txt(44, 328, "B · The screws land on CRESTS — that is what sets the length",
                 14, "bold", "#78350f"))
    path, pts = lobed_hub(56, 470, 528, 26, d["N_LOBE"])
    o.append(rect(56, 352, 528, 34, "#fde68a", AMBER, 2))
    o.append(txt(578, 374, f"carrier wall {d['WALL']:.0f} mm", 10.5, "normal",
                 "#78350f", "end"))
    o.append(path)
    o.append(txt(60, 508, f"hub — {d['N_LOBE']} lobes: crest · flank · valley · "
                          f"flank · crest …", 10.5, "normal", MUTED))

    # y = y0 - amp*cos(2*pi*n*t) is HIGHEST at t = k/n, so those are the
    # crests. The first version of this script used (k + 0.5), which is the
    # VALLEY - it drew every screw in the one seat panel B exists to warn
    # about. check() now proves the placement against the same formula.
    crests = [56 + k * 528 / d["N_LOBE"] for k in range(d["N_LOBE"] + 1)]
    for i, (kind, label) in enumerate((("flat", "FLAT on a crest"),
                                       ("cup", "CUP on a crest"))):
        sx = crests[i * 2 + 1]
        SCREWS.append(sx)
        o.append(f'<line x1="{sx}" y1="356" x2="{sx}" y2="444" stroke="{DRED}" '
                 f'stroke-width="7" stroke-linecap="butt"/>')
        o.append(txt(sx, 346, label, 10, "bold", DRED, "middle", limit=sx + 72))
    flank = (crests[4] + crests[5]) / 2
    o.append(f'<line x1="{flank}" y1="356" x2="{flank}" y2="470" stroke="{RED}" '
             f'stroke-width="7" stroke-dasharray="6 4"/>')
    o.append(txt(flank, 346, "on a FLANK", 10, "bold", RED, "middle", limit=flank + 72))

    for i, line in enumerate([
            "M3 is tapped STRAIGHT INTO THE PETG — a %.1f mm pilot through the" % d["SET_TAP_D"],
            "whole wall. Heat-set inserts were the plan and would split these faces.",
            "",
            "The FLANK is the seat that bites. A screw part-way down one DOES clamp",
            "— at a smaller radius. And %d lobes at %d° against %d screws at %d° is"
            % (d["N_LOBE"], 360 // d["N_LOBE"], d["N_SET"], 360 // d["N_SET"]),
            "exactly two lobe pitches, so all three share the phase and push the ring",
            "off centre TOGETHER.",
            "",
            "Eccentric ring → varying air gap → the Hall latch drops out over part",
            "of a revolution."]):
        if line:
            o.append(txt(56, 540 + i * 19, line, 11.5, "normal", "#78350f", limit=606))

    o.append(rect(56, 730, 528, 66, "#fef2f2", "#dc2626", 1.6, 6))
    o.append(txt(68, 752, "An M3 × %.0f cannot be asked to reach a VALLEY."
                 % d["SET_SCREW_L"], 11.5, "bold", DRED))
    o.append(txt(68, 770, "The span above is to a CREST. A valley is deeper by the lobe "
                          "depth,", 11, "normal", DRED))
    o.append(txt(68, 786, "which has never been measured. Caliper two opposite valleys "
                          "and record it.", 11, "normal", DRED))

    # ---- C: the numbers ----------------------------------------------------
    o.append(rect(632, 300, W - 656, 516, "#f0fdf4", "#22c55e", 2, 8))
    o.append(txt(652, 328, "C · How you know it seated", 14, "bold", "#14532d"))
    o.append(txt(652, 352, "Every figure below is computed in the .scad:",
                 11, "normal", GREEN))
    rows = [("wall to cross", f"{d['WALL']:.2f} mm"),
            ("+ radial gap, smallest", f"{d['SPAN_MIN']:.2f} mm total"),
            ("+ radial gap, largest", f"{d['SPAN_MAX']:.2f} mm total"),
            ("screw chosen", f"M3 × {d['SET_SCREW_L']:.0f}"),
            ("", ""),
            ("stands PROUD of the OD", f"{d['PROUD_MIN']:.2f} – {d['PROUD_MAX']:.2f} mm")]
    for i, (k, v) in enumerate(rows):
        if not k:
            continue
        y = 378 + i * 22
        bold = "bold" if "PROUD" in k else "normal"
        o.append(txt(652, y, k, 11, bold, "#14532d"))
        o.append(txt(W - 44, y, v, 11, bold, "#14532d", "end"))
    o.append(f'<line x1="652" y1="492" x2="{W - 44}" y2="492" stroke="{GREEN}" '
             f'stroke-width="1"/>')

    o.append(rect(652, 506, W - 696, 86, "#dcfce7", GREEN, 1.6, 6))
    o.append(txt(664, 528, "Set the sensor air gap ABOVE %.2f mm."
                 % d["PROUD_MAX"], 11.5, "bold", "#14532d"))
    o.append(txt(664, 546, "A screw at worst case stands that far out,", 11,
                 "normal", "#14532d"))
    o.append(txt(664, 562, "and anything standing proud sweeps the", 11,
                 "normal", "#14532d"))
    o.append(txt(664, 578, "sensor — the two-piece carrier died of it.", 11,
                 "normal", "#14532d"))

    for i, line in enumerate([
            "Winds in past %.2f mm and still loose?" % d["SPAN_MAX"],
            "It is on a flank or over a valley.",
            "Back it out, rotate the ring, retry.",
            "",
            "Then draw a WITNESS MARK across the",
            "ring-to-hub joint. A slip shows at a",
            "glance afterwards, whatever is fitted."]):
        if line:
            o.append(txt(652, 620 + i * 19, line, 11.5, "normal", "#14532d",
                         limit=W - 40))

    o.append('</svg>')
    return "\n".join(o)


def check(svg, d):
    ys = [float(m) for m in re.findall(r'y="([0-9.]+)"', svg)]
    assert max(ys) <= H - 8, f"content reaches y={max(ys):.0f} on {H}"
    for s_, size, x, anchor, limit in FITS:
        w = len(s_) * size * 0.54
        right = x + w if anchor == "start" else x + w / 2
        assert right <= limit, f"text {s_!r} reaches x={right:.0f}, past {limit}"

    # The one geometric claim this figure makes beyond the numbers: three
    # screws at 120 degrees sit two lobe pitches apart on a six-lobe hub, so
    # they share the phase. If N_LOBE or N_SET ever changes that sentence is
    # wrong, and a figure that argues from it is wrong with it.
    assert (360 / d["N_SET"]) % (360 / d["N_LOBE"]) == 0, (
        f"{d['N_SET']} screws no longer share a phase with "
        f"{d['N_LOBE']} lobes - panel B's argument does not hold")

    # Panel B's screws must sit on CRESTS. Recomputed from the same wave the
    # path is drawn from, not from the list that placed them.
    import math
    for sx in SCREWS:
        t = (sx - 56) / 528
        y = 470 - 26 * math.cos(2 * math.pi * d["N_LOBE"] * t)
        assert abs(y - (470 - 26)) < 0.5, (
            f"a screw at x={sx:.1f} lands at y={y:.1f}; a crest is y=444. "
            f"It is drawn in a flank or a valley")
    assert len(SCREWS) == 2, "expected two seated screws in panel B"

    # And the numbers the old figure got wrong must be the model's.
    for want in (f"{d['PROUD_MIN']:.2f}", f"{d['PROUD_MAX']:.2f}",
                 f"{d['SPAN_MIN']:.2f}", f"{d['SPAN_MAX']:.2f}"):
        assert want in svg, f"{want} is not in the figure"


def main():
    d = carrier_params.load()
    svg = build(d)
    check(svg, d)
    OUT.write_text(svg, encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}  "
          f"span {d['SPAN_MIN']:.2f}-{d['SPAN_MAX']:.2f}  "
          f"proud {d['PROUD_MIN']:.2f}-{d['PROUD_MAX']:.2f}  "
          f"{'cross-checked' if d['_checked'] else 'NOT cross-checked'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
