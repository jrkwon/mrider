#!/usr/bin/env python3
r"""
Generate docs/images/nose-diameter-decides.svg

The companion figure to drive-encoder-bracket-mount.svg. That one answers
"what do I measure and where is it"; this one answers "what does the number
decide, and why can nothing be drawn without it".

Why this is generated and not hand-written
------------------------------------------
Every radius in it comes out of cad/drive_encoder_carrier.scad, and they have
to agree with each other:

    HUB_D 62.7  ->  BORE 63.9  ->  OD 77.9  ->  +gap  ->  +sensor
      R 31.35       R 31.95       R 38.95     R 41.95   R 45.95

A hand-drawn version of this is a drawing of numbers that are nearly right,
and the last two figures this project drew by hand were both wrong in ways
only a reader caught - a breadboard with the wrong hole count, and a power
diagram that contradicted its own caption. The circles here are drawn FROM
the radii at a fixed scale, so the picture cannot disagree with the model.

The two candidate nose diameters are the real open question: two photographs
read Ø85-90 end-on and Ø72-75 from the side, and those land on OPPOSITE SIDES
of the Ø77.9 magnet track. That is the whole point of the figure, so both are
drawn to scale rather than described.

Layers are emitted in order - plates, rings, arms, dimensions, labels - so a
label can never end up under a circle.
"""

import pathlib

# ---- from cad/drive_encoder_carrier.scad ---------------------------------
HUB_D = 62.7            # measured across opposite lobe crests, 2026-10-15
BORE_D = 63.9           # HUB_D + BORE_CLEAR 1.2
OD = 77.9               # BORE_D + 2 * WALL 7.0 -- the magnet track
SENSOR_GAP = 3.0        # largest air gap the bracket will be set to
SENSOR_T = 4.0          # sensor + PCB radial thickness
AXIAL_GAP = 8.0         # the slice the carrier lives in
CARRIER_W = 6.0         # WIDTH

R_HUB = HUB_D / 2
R_BORE = BORE_D / 2
R_TRACK = OD / 2
R_FACE = R_TRACK + SENSOR_GAP
R_OUT = R_FACE + SENSOR_T

# the two readings that disagree
NOSE_SMALL = (72.0, 75.0)
NOSE_LARGE = (85.0, 90.0)

CLAMP_MIN = 6.0         # a clamp needs this much bare cylinder
CLAMP_MAX = 10.0

W, H = 1240, 1240
S = 2.45                # px per mm in the end views

out = []
e = out.append


def esc(t):
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# =========================================================================
e(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}"')
e('     font-family="DejaVu Sans, Helvetica, Arial, sans-serif">')
e('  <title>What the nose diameter decides — a clamp has no drawing without its own diameter</title>')
e('  <desc>Three panels. The first is a radial budget from the axle outward, marking the hub at '
  'radius 31.35 mm, the carrier bore at 31.95, the magnet track at 38.95, the sensor face at up to '
  '41.95 and the sensor back at 45.95, with the two disagreeing nose readings shaded across it: '
  'diameter 72 to 75 falls inside the magnet track, diameter 85 to 90 falls outside it. The second '
  'panel draws both cases to scale as end views, showing that the bracket arm reaches outward in '
  'one case and inward in the other. The third panel shows the axial question: the bare length of '
  'the nose decides whether a clamp fits at all, and if it does not, the fallbacks are not '
  'concentric with the axle.</desc>')
e('  <defs>')
e('    <marker id="ar" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">'
  '<path d="M0,0 L0,6 L8,3 z" fill="#0f172a"/></marker>')
e('    <marker id="arb" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">'
  '<path d="M0,0 L0,6 L8,3 z" fill="#1d4ed8"/></marker>')
e('    <marker id="arr" markerWidth="9" markerHeight="9" refX="8" refY="3" orient="auto">'
  '<path d="M0,0 L0,6 L8,3 z" fill="#b91c1c"/></marker>')
e('    <pattern id="fixed" width="7" height="7" patternUnits="userSpaceOnUse" '
  'patternTransform="rotate(45)">')
e('      <rect width="7" height="7" fill="#e2e8f0"/>')
e('      <line x1="0" y1="0" x2="0" y2="7" stroke="#94a3b8" stroke-width="1.4"/>')
e('    </pattern>')
e('  </defs>')
e(f'  <rect width="{W}" height="{H}" fill="#ffffff"/>')

e('  <text x="24" y="38" font-size="21" font-weight="bold" fill="#0f172a">'
  'What the nose diameter decides — and why the bracket cannot be drawn without it</text>')
e('  <text x="24" y="62" font-size="12.5" fill="#475569">'
  'The clamp band <tspan font-weight="bold">is</tspan> a circle at this diameter. Everything else on the '
  'bracket hangs off where that circle sits relative to the magnet track.</text>')

# =========================================================================
# PANEL 1 — the radial budget
# =========================================================================
P1Y = 86
e(f'  <rect x="24" y="{P1Y}" width="1192" height="300" rx="8" fill="#f8fafc" '
  'stroke="#94a3b8" stroke-width="2"/>')
e(f'  <text x="44" y="{P1Y+28}" font-size="15" font-weight="bold" fill="#0f172a">'
  '1 · The radial budget, measured from the axle. Every number here comes out of the carrier model.</text>')

AX_X0, AX_X1 = 120, 1120          # r = 0 .. 50 mm
AX_Y = P1Y + 150
RS = (AX_X1 - AX_X0) / 50.0


def rx(r):
    return AX_X0 + r * RS


# the two nose bands, drawn behind the axis
for (lo, hi), col, fill in ((NOSE_SMALL, "#15803d", "#bbf7d0"),
                            (NOSE_LARGE, "#b91c1c", "#fecaca")):
    x0, x1 = rx(lo / 2), rx(hi / 2)
    e(f'  <rect x="{x0:.1f}" y="{AX_Y-46}" width="{x1-x0:.1f}" height="92" '
      f'fill="{fill}" opacity="0.75"/>')

# the track line, so the bands are visibly on either side of it
e(f'  <line x1="{rx(R_TRACK):.1f}" y1="{AX_Y-62}" x2="{rx(R_TRACK):.1f}" y2="{AX_Y+62}" '
  'stroke="#7e22ce" stroke-width="3"/>')

# axis
e(f'  <line x1="{AX_X0}" y1="{AX_Y}" x2="{AX_X1+20}" y2="{AX_Y}" stroke="#0f172a" '
  'stroke-width="2.4" marker-end="url(#ar)"/>')
e(f'  <line x1="{AX_X0}" y1="{AX_Y-56}" x2="{AX_X0}" y2="{AX_Y+56}" stroke="#0f172a" '
  'stroke-width="3"/>')
e(f'  <text x="{AX_X0}" y="{AX_Y+76}" font-size="11.5" font-weight="bold" fill="#0f172a" '
  'text-anchor="middle">axle</text>')
e(f'  <text x="{AX_X0}" y="{AX_Y+91}" font-size="11.5" font-weight="bold" fill="#0f172a" '
  'text-anchor="middle">centre</text>')
e(f'  <text x="{AX_X1+26}" y="{AX_Y+5}" font-size="11.5" fill="#475569">radius, mm</text>')

# ticks that matter, alternating above/below so labels never collide
TICKS = [
    # keep the sub-labels SHORT: the two on each side sit at the same height,
    # and 38.95 vs 45.95 is only 140 px apart on this axis.
    (R_HUB,   "hub Ø62.7",          "#b45309", -1, "lobe crests"),
    (R_TRACK, "magnet track Ø77.9", "#7e22ce", +1, "carrier outside"),
    (R_FACE,  "sensor face",        "#1d4ed8", -1, "+ up to 3 mm gap"),
    (R_OUT,   "sensor back",        "#1d4ed8", +1, "+ sensor + PCB"),
]
for r, lab, col, side, sub in TICKS:
    x = rx(r)
    y0 = AX_Y - 8 if side < 0 else AX_Y + 8
    y1 = AX_Y - 66 if side < 0 else AX_Y + 66
    e(f'  <line x1="{x:.1f}" y1="{y0}" x2="{x:.1f}" y2="{y1}" stroke="{col}" '
      'stroke-width="1.8" stroke-dasharray="4 3"/>')
    e(f'  <circle cx="{x:.1f}" cy="{AX_Y}" r="4.5" fill="{col}"/>')
    ty = y1 - 20 if side < 0 else y1 + 16
    e(f'  <text x="{x:.1f}" y="{ty}" font-size="12" font-weight="bold" fill="{col}" '
      f'text-anchor="middle">{esc(lab)}</text>')
    e(f'  <text x="{x:.1f}" y="{ty+15}" font-size="10.5" fill="{col}" '
      f'text-anchor="middle">R {r:.2f} · {esc(sub)}</text>')

# band labels
e(f'  <text x="{rx(sum(NOSE_SMALL)/4):.1f}" y="{AX_Y-54}" font-size="12" font-weight="bold" '
  f'fill="#14532d" text-anchor="middle">side view read Ø{NOSE_SMALL[0]:.0f}–{NOSE_SMALL[1]:.0f}</text>')
e(f'  <text x="{rx(sum(NOSE_LARGE)/4):.1f}" y="{AX_Y+62}" font-size="12" font-weight="bold" '
  f'fill="#991b1b" text-anchor="middle">end-on read Ø{NOSE_LARGE[0]:.0f}–{NOSE_LARGE[1]:.0f}</text>')

e(f'  <text x="44" y="{P1Y+276}" font-size="13" font-weight="bold" fill="#0f172a">'
  'The two photographs do not merely disagree by 15 mm — they land on '
  '<tspan fill="#7e22ce">OPPOSITE SIDES of the magnet track</tspan>. That is a different bracket, '
  'not a different number.</text>')

# =========================================================================
# PANEL 2 — the two cases, to scale
# =========================================================================
P2Y = 400
e(f'  <rect x="24" y="{P2Y}" width="1192" height="500" rx="8" fill="#ffffff" '
  'stroke="#94a3b8" stroke-width="2"/>')
e(f'  <text x="44" y="{P2Y+28}" font-size="15" font-weight="bold" fill="#0f172a">'
  '2 · Both readings are buildable. Neither can be drawn until you know which one it is. '
  '<tspan font-size="12" font-weight="normal" fill="#475569">End view, wheel off, drawn to scale.</tspan></text>')

CY = P2Y + 268
CASES = [
    (330, NOSE_SMALL, "#15803d", "#bbf7d0", "A", "nose INSIDE the track",
     "the arm reaches OUTWARD", +1),
    (900, NOSE_LARGE, "#b91c1c", "#fecaca", "B", "nose OUTSIDE the track",
     "the arm reaches INWARD", -1),
]

for cx, (nlo, nhi), col, fill, tag, head, arm, direction in CASES:
    rn = (nlo + nhi) / 4.0            # mid radius of the band

    # --- rings, largest first -------------------------------------------
    e(f'  <circle cx="{cx}" cy="{CY}" r="{R_OUT*S:.1f}" fill="none" stroke="#cbd5e1" '
      'stroke-width="1.4" stroke-dasharray="3 4"/>')
    # the fixed nose, hatched
    e(f'  <circle cx="{cx}" cy="{CY}" r="{nhi/2*S:.1f}" fill="url(#fixed)" '
      f'stroke="{col}" stroke-width="2.6"/>')
    e(f'  <circle cx="{cx}" cy="{CY}" r="{nlo/2*S:.1f}" fill="none" '
      f'stroke="{col}" stroke-width="1.6" stroke-dasharray="5 4"/>')
    # the carrier, rotating
    e(f'  <circle cx="{cx}" cy="{CY}" r="{R_TRACK*S:.1f}" fill="#f3e8ff" opacity="0.88" '
      'stroke="#7e22ce" stroke-width="2.6"/>')
    e(f'  <circle cx="{cx}" cy="{CY}" r="{R_BORE*S:.1f}" fill="#ffffff" '
      'stroke="#7e22ce" stroke-width="1.6"/>')
    # the hub
    e(f'  <circle cx="{cx}" cy="{CY}" r="{R_HUB*S:.1f}" fill="#fef3c7" '
      'stroke="#b45309" stroke-width="2"/>')
    e(f'  <circle cx="{cx}" cy="{CY}" r="3.5" fill="#0f172a"/>')

    # --- the clamp band and the arm, at 8 o'clock ------------------------
    # clamp: a thick arc on the nose
    import math
    a0, a1 = math.radians(196), math.radians(254)
    rb = nhi / 2 * S + 4
    x0, y0 = cx + rb * math.cos(a0), CY + rb * math.sin(a0)
    x1, y1 = cx + rb * math.cos(a1), CY + rb * math.sin(a1)
    e(f'  <path d="M{x0:.1f},{y0:.1f} A{rb:.1f},{rb:.1f} 0 0 1 {x1:.1f},{y1:.1f}" '
      f'fill="none" stroke="#0f172a" stroke-width="7" stroke-linecap="round"/>')

    # arm: radial, from the clamp to the sensor face, at 225 deg
    aa = math.radians(225)
    r_from = nhi / 2 * S + 4
    r_to = R_FACE * S
    ax0, ay0 = cx + r_from * math.cos(aa), CY + r_from * math.sin(aa)
    ax1, ay1 = cx + r_to * math.cos(aa), CY + r_to * math.sin(aa)
    e(f'  <line x1="{ax0:.1f}" y1="{ay0:.1f}" x2="{ax1:.1f}" y2="{ay1:.1f}" '
      'stroke="#0f172a" stroke-width="6" stroke-linecap="round"/>')
    # the sensor pad sits on the face, tangentially
    px, py = cx + (R_FACE * S) * math.cos(aa), CY + (R_FACE * S) * math.sin(aa)
    e(f'  <rect x="{px-13:.1f}" y="{py-7:.1f}" width="26" height="14" rx="2.5" '
      'fill="#1d4ed8" stroke="#1e3a8a" stroke-width="1.6" '
      f'transform="rotate(-45 {px:.1f} {py:.1f})"/>')

    # --- labels ----------------------------------------------------------
    e(f'  <text x="{cx}" y="{P2Y+60}" font-size="16" font-weight="bold" fill="{col}" '
      f'text-anchor="middle">CASE {tag} — Ø{nlo:.0f}–{nhi:.0f}</text>')
    e(f'  <text x="{cx}" y="{P2Y+80}" font-size="12.5" font-weight="bold" fill="{col}" '
      f'text-anchor="middle">{esc(head)}</text>')

    e(f'  <text x="{cx}" y="{CY + R_OUT*S + 34:.0f}" font-size="13" font-weight="bold" '
      f'fill="#0f172a" text-anchor="middle">{esc(arm)}</text>')

    # radial callout to the right, outside every circle
    lx = cx + R_OUT * S + 18
    e(f'  <line x1="{cx}" y1="{CY}" x2="{lx+6:.1f}" y2="{CY}" stroke="#64748b" '
      'stroke-width="1.2" stroke-dasharray="3 3"/>')

# shared key, between and below the two views
KY = P2Y + 108
e(f'  <rect x="{600-62}" y="{KY}" width="124" height="118" rx="5" fill="#f8fafc" '
  'stroke="#cbd5e1" stroke-width="1.6"/>')
keys = [("url(#fixed)", "#94a3b8", "nose · FIXED"),
        ("#f3e8ff", "#7e22ce", "carrier · ROTATES"),
        ("#fef3c7", "#b45309", "lobed hub"),
        ("#1d4ed8", "#1e3a8a", "sensor pad")]
for i, (f, st, lab) in enumerate(keys):
    y = KY + 18 + i * 26
    e(f'  <rect x="{600-50}" y="{y-9}" width="16" height="14" rx="2" fill="{f}" '
      f'stroke="{st}" stroke-width="1.4"/>')
    e(f'  <text x="{600-28}" y="{y+2}" font-size="10.5" fill="#334155">{esc(lab)}</text>')

e(f'  <text x="44" y="{P2Y+466}" font-size="13" fill="#0f172a">'
  '<tspan font-weight="bold">Read the two drawings as one question:</tspan> the clamp is black, and in '
  'A it sits under the carrier while in B it sits outside it. '
  '<tspan font-weight="bold">Same sensor position, mirrored bracket.</tspan></text>')
e(f'  <text x="44" y="{P2Y+486}" font-size="12.5" fill="#475569">'
  'There is no shape that is right for both, and no average of the two that is right for either — '
  'which is why this is a measurement and not an assumption.</text>')

# =========================================================================
# PANEL 3 — the axial question, and what it decides
# =========================================================================
P3Y = 914
e(f'  <rect x="24" y="{P3Y}" width="584" height="300" rx="8" fill="#fffbeb" '
  'stroke="#f59e0b" stroke-width="2"/>')
e(f'  <text x="44" y="{P3Y+28}" font-size="15" font-weight="bold" fill="#92400e">'
  '3 · N2 is a different kind of question: go or no-go</text>')

# a simple axial strip
SX, SY = 60, P3Y + 70
e(f'  <rect x="{SX}" y="{SY}" width="150" height="54" fill="url(#fixed)" stroke="#94a3b8" '
  'stroke-width="2"/>')
e(f'  <text x="{SX+75}" y="{SY+32}" font-size="11.5" font-weight="bold" fill="#475569" '
  'text-anchor="middle">gearbox body</text>')
e(f'  <rect x="{SX+150}" y="{SY+10}" width="118" height="34" fill="url(#fixed)" '
  'stroke="#b45309" stroke-width="2.4"/>')
e(f'  <text x="{SX+209}" y="{SY-6}" font-size="11.5" font-weight="bold" fill="#92400e" '
  'text-anchor="middle">bare NOSE</text>')
e(f'  <line x1="{SX+150}" y1="{SY+56}" x2="{SX+268}" y2="{SY+56}" stroke="#b45309" '
  'stroke-width="2" marker-end="url(#ar)"/>')
e(f'  <text x="{SX+209}" y="{SY+72}" font-size="11.5" font-weight="bold" fill="#92400e" '
  'text-anchor="middle">N2 = ? mm</text>')
e(f'  <rect x="{SX+280}" y="{SY+4}" width="46" height="46" fill="#f3e8ff" stroke="#7e22ce" '
  'stroke-width="2.2"/>')
e(f'  <text x="{SX+303}" y="{SY-6}" font-size="11" font-weight="bold" fill="#581c87" '
  'text-anchor="middle">carrier</text>')
e(f'  <text x="{SX+303}" y="{SY+70}" font-size="10.5" fill="#6b21a8" '
  f'text-anchor="middle">{AXIAL_GAP:.0f} mm slice</text>')

rows = [
    ("#15803d", f"N2 ≥ {CLAMP_MIN:.0f} mm, bare",
     "Clamp the nose. Concentric with the axle, so the air gap is a printed dimension."),
    ("#b91c1c", f"N2 < {CLAMP_MIN:.0f} mm, or something sits on it",
     "Fallbacks: the housing's own assembly screws, or the chassis pocket. "),
]
yy = P3Y + 164
for col, head, body in rows:
    e(f'  <circle cx="{SX+4}" cy="{yy-4}" r="5" fill="{col}"/>')
    e(f'  <text x="{SX+20}" y="{yy}" font-size="12.5" font-weight="bold" fill="{col}">'
      f'{esc(head)}</text>')
    e(f'  <text x="{SX+20}" y="{yy+18}" font-size="11.5" fill="#334155">{esc(body)}</text>')
    yy += 48
e(f'  <text x="{SX+20}" y="{P3Y+258}" font-size="11.5" font-weight="bold" fill="#991b1b">'
  'Neither fallback is concentric, so both hand the air gap back to the builder’s eye.</text>')
e(f'  <text x="{SX+20}" y="{P3Y+276}" font-size="11.5" fill="#7f1d1d">'
  'That is what N2 is really asking: whether this design stands at all.</text>')

# ---- what exists today --------------------------------------------------
e(f'  <rect x="632" y="{P3Y}" width="584" height="300" rx="8" fill="#fef2f2" '
  'stroke="#ef4444" stroke-width="2"/>')
e(f'  <text x="652" y="{P3Y+28}" font-size="15" font-weight="bold" fill="#991b1b">'
  'And this is not a blank parameter. The file does not exist.</text>')

files = [
    ("#15803d", "cad/drive_encoder_carrier.scad",
     "the rotating ring. Finished — bore, track, pockets, grub screws."),
    ("#15803d", "cad/steering_magnet_cap.scad",
     "the kingpin cap. Finished except STACK_H."),
    ("#b91c1c", "cad/drive_encoder_bracket.scad",
     "DOES NOT EXIST. Nothing in cad/ contains a nose dimension."),
]
yy = P3Y + 62
for col, name, body in files:
    e(f'  <text x="652" y="{yy}" font-size="12.5" font-family="DejaVu Sans Mono, monospace" '
      f'font-weight="bold" fill="{col}">{esc(name)}</text>')
    e(f'  <text x="652" y="{yy+18}" font-size="11.5" fill="#334155">{esc(body)}</text>')
    yy += 48

e(f'  <text x="652" y="{P3Y+218}" font-size="12.5" font-weight="bold" fill="#991b1b">'
  'The carrier could be modelled because the hub was measured first.</text>')
e(f'  <text x="652" y="{P3Y+238}" font-size="11.5" fill="#7f1d1d">'
  'It still cost four wasted prints, because the first hub figure came off a wire</text>')
e(f'  <text x="652" y="{P3Y+256}" font-size="11.5" fill="#7f1d1d">'
  'wrap and was 2.3 mm high. N1 off a photograph would be the same mistake.</text>')

e('</svg>')

p = pathlib.Path(__file__).resolve().parent.parent / "docs/images/nose-diameter-decides.svg"
p.write_text("\n".join(out) + "\n")
print(f"wrote {p}")
print(f"  R hub {R_HUB:.2f} · bore {R_BORE:.2f} · track {R_TRACK:.2f} "
      f"· face {R_FACE:.2f} · out {R_OUT:.2f}")
print(f"  nose candidates: R {NOSE_SMALL[0]/2:.1f}-{NOSE_SMALL[1]/2:.1f} "
      f"and R {NOSE_LARGE[0]/2:.1f}-{NOSE_LARGE[1]/2:.1f}")
assert NOSE_SMALL[1] / 2 < R_TRACK < NOSE_LARGE[0] / 2, \
    "the figure's whole argument is that the two readings straddle the track"
