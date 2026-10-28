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
Generate the two bench-breadboard figures.

    python3 scripts/gen_breadboard_figure.py

  docs/images/breadboard-layout.svg     - the wiring, three boards
  docs/images/breadboard-procedure.svg  - counts, the VUSB rule, bring-up order

They were one figure and it ran to 2190 px tall, which is unreadable on a
screen and unprintable on a page. The split is along a real seam: the first
is what you look at *while* wiring, the second is what you read *before* and
*after*. Neither needs the other open.

WHY A GENERATOR AND NOT HAND-WRITTEN SVG
----------------------------------------
The first two versions of this figure were written by hand and both were
wrong in ways that only a reader noticed:

  1. 33 columns and 8 rows, against the 30 x 10 of the 400-point board that
     was actually ordered. A figure that does not match the part in the box
     teaches the wrong layout.
  2. The upper + rail had no source. A breadboard's rail pairs are separate
     strips, the Teensy's 3V3 pin feeds only the lower one, and the pull-ups
     reached for the upper - so as drawn they did nothing.
  3. Labels drawn dark-on-dark, and text blocks sitting on top of wires.

All three are the kind of mistake that is cheap to make by hand and hard to
see. Here the geometry comes from constants, the grid is generated, and the
drawing is emitted in strict layers - boards, chips, components, wires,
labels - so a label can never hide a wire again.

CHANGING IT
-----------
Edit the geometry block, re-run, and commit both this file and the SVG. Do
not edit the SVG directly; it will be overwritten.
"""
W,H=1180,1470
P=20; C0=180                      # 30 columns, 2.54mm pitch
def col(i): return C0+i*P
BX0,BX1=150,790                   # board rect
RX0,RX1=168,772                   # rail extent
out=[]
def e(s): out.append(s)

def board(y0,y1,rail_t,rail_b,rowsA,rowsF,label,lcol):
    e(f'<rect x="{BX0}" y="{y0}" width="{BX1-BX0}" height="{y1-y0}" rx="6" fill="#f8fafc" stroke="#64748b" stroke-width="2"/>')
    for yy,c in ((rail_t[0],"#dc2626"),(rail_t[1],"#2563eb"),(rail_b[0],"#2563eb"),(rail_b[1],"#dc2626")):
        e(f'<line x1="{RX0}" y1="{yy}" x2="{RX1}" y2="{yy}" stroke="{c}" stroke-width="3"/>')
    e('<g fill="#cbd5e1">')
    for yy in list(rowsA)+list(rowsF):
        for i in range(30): e(f'<circle cx="{col(i)}" cy="{yy}" r="2.4"/>')
    e('</g>')
    # rail holes
    e('<g fill="#e2e8f0">')
    for yy in (rail_t[0],rail_t[1],rail_b[0],rail_b[1]):
        for i in range(25): e(f'<circle cx="{180+i*24}" cy="{yy}" r="2"/>')
    e('</g>')

def gap(x,y,c,w=3,vert=False):
    e(f'<circle cx="{x}" cy="{y}" r="6" fill="#ffffff"/>')
    if vert: e(f'<path d="M{x},{y-6} a6,6 0 0 1 0,12" fill="none" stroke="{c}" stroke-width="{w}"/>')
    else:    e(f'<path d="M{x-6},{y} a6,6 0 0 1 12,0" fill="none" stroke="{c}" stroke-width="{w}"/>')

def zig(x,y0,y1,c="#b45309"):
    d=(y1-y0); s=1 if d>0 else -1; m=y0+d/2
    e(f'<path d="M{x},{y0} L{x},{m-s*18} L{x-7},{m-s*12} L{x+7},{m-s*4} L{x-7},{m+s*4} L{x+7},{m+s*12} L{x},{m+s*18} L{x},{y1}" fill="none" stroke="{c}" stroke-width="2.6"/>')

def cap(x,yh,yr):
    e(f'<path d="M{x},{yh} L{x-9},{yh-6} L{x-9},{yr+26}" fill="none" stroke="#1d4ed8" stroke-width="2.4"/>')
    e(f'<path d="M{x-15},{yr+26} L{x-3},{yr+26} M{x-15},{yr+19} L{x-3},{yr+19} M{x-9},{yr+19} L{x-9},{yr}" fill="none" stroke="#1d4ed8" stroke-width="2.4"/>')

# ---------- geometry ----------
A_t=(182,202); A_b=(476,498); A_A=[236,256,276,296,316]; A_F=[356,376,396,416,436]
B_t=(632,652); B_b=(926,948); B_A=[686,706,726,746,766]; B_F=[806,826,846,866,886]
Cc_t=(1082,1102); Cc_b=(1376,1398); C_A=[1136,1156,1176,1196,1216]; C_F=[1256,1276,1296,1316,1336]

e(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="DejaVu Sans, Helvetica, Arial, sans-serif">')
e('<title>Bench breadboard layout, drawn to a real 400-point half-size board</title>')
e('<desc>Three 400-point half-size breadboards, 30 columns by 10 rows plus four power rails. '
  'Board A carries the Teensy 4.1 straddling the centre channel, with rail-bridge jumpers taking '
  'its 3V3 supply to the upper rails, 10k pull-ups and 1nF on the quadrature columns and 4.7k on '
  'the I2C columns. Board B carries the two Hall latches, board C the AS5600.</desc>')
e(f'<rect width="{W}" height="{H}" fill="#ffffff"/>')

e('<text x="24" y="34" font-size="20" font-weight="bold" fill="#0f172a">Bench layout — drawn to a real 400-point half-size board</text>')
e('<text x="24" y="58" font-size="12.5" fill="#475569">30 columns × 10 rows + four rails = 400 tie points, which is the <tspan font-weight="bold">SZH-BBAD-005</tspan> that was ordered. A <tspan font-weight="bold">pale band</tspan> = one node. A <tspan font-weight="bold">gap</tspan> = passes over, not into.</text>')

# ===== LAYER 1: boards =====
board(150,530,A_t,A_b,A_A,A_F,'A','#14532d')
board(616,996,B_t,B_b,B_A,B_F,'B','#1e3a8a')
board(1050,1430,Cc_t,Cc_b,C_A,C_F,'C','#0f766e')

# node bands
for x in (col(4),col(5)): e(f'<rect x="{x-9}" y="228" width="18" height="56" rx="4" fill="#fde68a" fill-opacity="0.6"/>')
for x in (col(12),col(13)): e(f'<rect x="{x-9}" y="388" width="18" height="56" rx="4" fill="#fde68a" fill-opacity="0.6"/>')
for x in (col(3),col(4),col(5),col(10),col(11),col(12)): e(f'<rect x="{x-9}" y="678" width="18" height="36" rx="4" fill="#fde68a" fill-opacity="0.6"/>')
for x in (col(20),col(22),col(24),col(26)): e(f'<rect x="{x-9}" y="1128" width="18" height="36" rx="4" fill="#fde68a" fill-opacity="0.6"/>')

# ===== LAYER 2: chips =====
e('<rect x="232" y="288" width="476" height="96" rx="5" fill="#1e293b" stroke="#0f172a" stroke-width="2"/>')
e('<rect x="232" y="316" width="28" height="40" rx="3" fill="#94a3b8"/>')
e('<text x="246" y="341" font-size="8.5" fill="#0f172a" text-anchor="middle">USB</text>')
e('<text x="500" y="342" font-size="16" font-weight="bold" fill="#f1f5f9" text-anchor="middle">Teensy 4.1</text>')
for x,t in ((col(3),'GND'),(col(4),'0'),(col(5),'1')):
    e(f'<text x="{x}" y="314" font-size="10.5" font-weight="bold" fill="#fde68a" text-anchor="middle" transform="rotate(-90 {x} 314)">{t}</text>')
for x,t in ((col(3),'VIN'),(col(4),'GND'),(col(5),'3V3'),(col(12),'19'),(col(13),'18')):
    e(f'<text x="{x}" y="358" font-size="10.5" font-weight="bold" fill="#7dd3fc" text-anchor="middle" transform="rotate(-90 {x} 358)">{t}</text>')

for cx,lbl in ((col(4),'Hall A'),(col(11),'Hall B')):
    e(f'<path d="M{cx-21},766 L{cx-21},744 Q{cx},720 {cx+21},744 L{cx+21},766 Z" fill="#1e293b" stroke="#0f172a" stroke-width="1.8"/>')
    e(f'<text x="{cx}" y="756" font-size="9.5" font-weight="bold" fill="#f1f5f9" text-anchor="middle">DRV</text>')
e('<rect x="560" y="1178" width="168" height="38" rx="4" fill="#0f766e" stroke="#115e59" stroke-width="2"/>')
e('<text x="644" y="1203" font-size="13" font-weight="bold" fill="#ecfeff" text-anchor="middle">AS5600</text>')

# ===== LAYER 3: components =====
zig(col(4),236,182); gap(col(4),202,"#b45309",2.6)
zig(col(5),236,182); gap(col(5),202,"#b45309",2.6)
cap(col(4),256,202); cap(col(5),276,202)
zig(col(12),396,498); gap(col(12),476,"#b45309",2.6)
zig(col(13),396,498); gap(col(13),476,"#b45309",2.6)

# ===== LAYER 4: wires =====
e(f'<path d="M{col(3)},236 L{col(3)},202" stroke="#2563eb" stroke-width="3"/>')
e(f'<path d="M{col(5)},396 L{col(5)},498" stroke="#dc2626" stroke-width="3"/>'); gap(col(5),476,"#dc2626",3,True)
e(f'<path d="M{col(4)},396 L{col(4)},476" stroke="#2563eb" stroke-width="3"/>')
e(f'<path d="M{col(3)},436 L{col(3)},458 L104,458" stroke="#dc2626" stroke-width="3" fill="none"/>')
# rail bridges
e(f'<path d="M{RX1},182 L872,182 L872,498 L{RX1},498" fill="none" stroke="#dc2626" stroke-width="3.4"/>')
e(f'<path d="M{RX1},202 L846,202 L846,476 L{RX1},476" fill="none" stroke="#2563eb" stroke-width="3.4"/>')
# rail feeds A->B->C
e(f'<path d="M{RX0},498 L60,498 L60,948 L{RX0},948" fill="none" stroke="#dc2626" stroke-width="3"/>')
e(f'<path d="M{RX0},948 L60,948 L60,1398 L{RX0},1398" fill="none" stroke="#dc2626" stroke-width="3"/>')
e(f'<path d="M{RX0},476 L78,476 L78,926 L{RX0},926" fill="none" stroke="#2563eb" stroke-width="3"/>')
e(f'<path d="M{RX0},926 L78,926 L78,1376 L{RX0},1376" fill="none" stroke="#2563eb" stroke-width="3"/>')
# board B sensor wires
e(f'<path d="M{col(3)},686 L{col(3)},632" stroke="#dc2626" stroke-width="2.6"/>'); gap(col(3),652,"#dc2626",2.6,True)
e(f'<path d="M{col(4)},686 L{col(4)},652" stroke="#2563eb" stroke-width="2.6"/>')
e(f'<path d="M{col(10)},706 L{col(10)},632" stroke="#dc2626" stroke-width="2.6"/>'); gap(col(10),652,"#dc2626",2.6,True)
e(f'<path d="M{col(11)},706 L{col(11)},652" stroke="#2563eb" stroke-width="2.6"/>')
# board C sensor wires
e(f'<path d="M{col(20)},1136 L{col(20)},1082" stroke="#dc2626" stroke-width="2.6"/>'); gap(col(20),1102,"#dc2626",2.6,True)
e(f'<path d="M{col(22)},1136 L{col(22)},1102" stroke="#2563eb" stroke-width="2.6"/>')
# green jumpers
e(f'<path d="M{col(4)},276 L112,276 L112,706 L{col(5)},706" fill="none" stroke="#15803d" stroke-width="3"/>')
e(f'<path d="M{col(5)},256 L90,256 L90,686 L{col(12)},686" fill="none" stroke="#15803d" stroke-width="3"/>')
gap(col(4),256,"#15803d"); gap(col(3),686,"#15803d"); gap(col(4),686,"#15803d")
e(f'<path d="M{col(12)},416 L795,416 L795,1136 L{col(26)},1136" fill="none" stroke="#15803d" stroke-width="3"/>')
e(f'<path d="M{col(13)},436 L818,436 L818,1156 L{col(24)},1156" fill="none" stroke="#15803d" stroke-width="3"/>')
gap(col(13),416,"#15803d")
for x,y in ((col(4),276),(col(5),256),(col(5),706),(col(12),686),(col(12),416),(col(13),436),(col(26),1136),(col(24),1156)):
    e(f'<circle cx="{x}" cy="{y}" r="4.5" fill="#15803d"/>')

# ===== LAYER 5: labels =====
e('<text x="24" y="140" font-size="15" font-weight="bold" fill="#14532d">BOARD A — the Teensy end</text>')
e('<text x="24" y="572" font-size="15" font-weight="bold" fill="#1e3a8a">BOARD B — DRIVE: two Hall latches, BOTH ON THE SAME HUB</text>')
e('<text x="24" y="592" font-size="12" fill="#1d4ed8">Only one rear wheel is instrumented. The pair sits <tspan font-weight="bold">6.80 mm apart on that one carrier</tspan> — a quarter cycle out of step, which is what</text>')
e('<text x="24" y="608" font-size="12" fill="#1d4ed8">gives <tspan font-weight="bold">direction</tspan>. One latch counts; it cannot tell forward from reverse. <tspan font-weight="bold">A and B are two sensors on one wheel, not one sensor on each of two.</tspan></text>')
e('<text x="24" y="1040" font-size="15" font-weight="bold" fill="#0f766e">BOARD C — STEERING: the AS5600</text>')
e('<text x="352" y="196" font-size="11.5" font-weight="bold" fill="#b45309">2 × 10 kΩ → upper + rail</text>')
e('<text x="150" y="238" font-size="11.5" font-weight="bold" fill="#1d4ed8" text-anchor="end">2 × 1 nF</text>')
e('<text x="150" y="253" font-size="11.5" fill="#1d4ed8" text-anchor="end">→ upper − rail</text>')
e('<text x="476" y="470" font-size="11.5" font-weight="bold" fill="#b45309">2 × 4.7 kΩ → lower + rail</text>')
e(f'<text x="{col(16)}" y="322" font-size="10.5" font-weight="bold" fill="#1d4ed8" text-anchor="middle">10 k</text>')
e(f'<text x="{col(16)+13}" y="470" font-size="10.5" font-weight="bold" fill="#1d4ed8">2.7 k</text>')
e(f'<path d="M{col(16)},330 L{col(16)},302 L868,302" fill="none" stroke="#1d4ed8" stroke-width="3"/>')
e('<text x="880" y="298" font-size="11" font-weight="bold" fill="#1d4ed8">E-STOP SENSE</text>')
e('<text x="880" y="313" font-size="10.5" fill="#1d4ed8">to the coil node, through the</text>')
e('<text x="880" y="327" font-size="10.5" fill="#1d4ed8">button\'s NC contact</text>')
e('<text x="880" y="346" font-size="10.5" font-weight="bold" fill="#b91c1c">bench: 12 V through the real</text>')
e('<text x="880" y="360" font-size="10.5" font-weight="bold" fill="#b91c1c">button. METER IT before it</text>')
e('<text x="880" y="374" font-size="10.5" font-weight="bold" fill="#b91c1c">touches pin 14.</text>')
e('<text x="98" y="452" font-size="11.5" font-weight="bold" fill="#b91c1c" text-anchor="end">5 V UBEC</text>')
e('<text x="884" y="300" font-size="12" font-weight="bold" fill="#dc2626">RAIL</text>')
e('<text x="884" y="316" font-size="12" font-weight="bold" fill="#dc2626">BRIDGES</text>')
e('<text x="884" y="334" font-size="11" fill="#7f1d1d">without these the</text>')
e('<text x="884" y="349" font-size="11" fill="#7f1d1d">upper + rail is dead</text>')
e('<text x="884" y="364" font-size="11" fill="#7f1d1d">and the pull-ups</text>')
e('<text x="884" y="379" font-size="11" fill="#7f1d1d">do nothing</text>')
e('<text x="500" y="276" font-size="11" fill="#94a3b8" text-anchor="middle">the pins land UNDER the body — you connect in the rows above and below</text>')
# jumper identity labels
e('<text x="122" y="268" font-size="11" font-weight="bold" fill="#15803d">pin 0 → Hall A OUT</text>')
e('<text x="100" y="248" font-size="11" font-weight="bold" fill="#15803d">pin 1 → Hall B OUT</text>')
e('<text x="806" y="700" font-size="11" font-weight="bold" fill="#15803d">pin 19 → SCL</text>')
e('<text x="828" y="760" font-size="11" font-weight="bold" fill="#15803d">pin 18 → SDA</text>')
e(f'<text x="{col(4)}" y="710" font-size="11.5" font-weight="bold" fill="#1e3a8a" text-anchor="middle">Hall A · OUT → pin 0</text>')
e(f'<text x="{col(11)}" y="710" font-size="11.5" font-weight="bold" fill="#1e3a8a" text-anchor="middle">Hall B · OUT → pin 1</text>')
for base in (3,10):
    for k,(t,u) in enumerate((('1','VCC'),('2','GND'),('3','OUT'))):
        x=col(base+k)
        e(f'<circle cx="{x}" cy="782" r="8.5" fill="#ffffff" stroke="#0f172a" stroke-width="1.4"/>')
        e(f'<text x="{x}" y="786" font-size="10.5" font-weight="bold" fill="#0f172a" text-anchor="middle">{t}</text>')
        e(f'<text x="{x}" y="806" font-size="9.5" font-weight="bold" fill="#334155" text-anchor="middle">{u}</text>')
e('<text x="470" y="770" font-size="10.5" fill="#475569">1 = VCC  2 = GND  3 = OUT —</text>')
e('<text x="470" y="785" font-size="10.5" font-weight="bold" fill="#b91c1c">assumed. Check the datasheet.</text>')
for x,t in ((col(20),'VCC'),(col(22),'GND'),(col(24),'SDA'),(col(26),'SCL')): e(f'<text x="{x}" y="1234" font-size="9.5" fill="#64748b" text-anchor="middle">{t}</text>')
e(f'<text x="{col(24)}" y="1252" font-size="10.5" font-weight="bold" fill="#15803d" text-anchor="middle">→ pin 18</text>')
e(f'<text x="{col(26)}" y="1270" font-size="10.5" font-weight="bold" fill="#15803d" text-anchor="middle">→ pin 19</text>')
e('<text x="180" y="1300" font-size="12" fill="#0f766e">The AS5600 breakout may carry its own pull-ups. If it does, the 4.7 kΩ on board A are in parallel — fine.</text>')
e('<text x="180" y="1320" font-size="12" fill="#0f766e">Rows A–E of every board are left unused here. That is normal; a half-size board has far more holes than this needs.</text>')

e('</svg>')
open(__import__('pathlib').Path(__file__).resolve().parent.parent/'docs'/'images'/'breadboard-layout.svg','w',encoding='utf-8').write('\n'.join(out))
print('written')


# ======================= FIGURE 2 =======================
out=[]
W2,H2=1180,980
e(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W2} {H2}" width="{W2}" height="{H2}" font-family="DejaVu Sans, Helvetica, Arial, sans-serif">')
e('<title>Bench bring-up — what to buy, what the VUSB cut does, and the order to prove things in</title>')
e('<desc>Companion to the breadboard wiring figure. Panels covering the board and sensor counts, '
  'what the VUSB to VIN cut does to USB power, the five-step bring-up order, and the checks to make '
  'before any wire goes in.</desc>')
e(f'<rect width="{W2}" height="{H2}" fill="#ffffff"/>')
e('<text x="24" y="36" font-size="20" font-weight="bold" fill="#0f172a">Bench bring-up — read this before and after, not while wiring</text>')
e('<text x="24" y="60" font-size="12.5" fill="#475569">Companion to <tspan font-style="italic">breadboard-layout</tspan>. That figure is the wiring; this one is the counts, the rules and the order.</text>')

def panel(x,y,w,h,fill,stroke,title,tcol,lines,lcol,ls=19,fs=12):
    e(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
    e(f'<text x="{x+20}" y="{y+28}" font-size="14.5" font-weight="bold" fill="{tcol}">{title}</text>')
    yy=y+54
    for ln in lines:
        ind = 14 if ln.startswith('~') else 0
        e(f'<text x="{x+20+ind}" y="{yy}" font-size="{fs}" fill="{lcol}">{ln.lstrip("~")}</text>')
        yy+=ls

panel(24,96,566,250,'#f0fdf4','#22c55e','Three boards per station — and nothing more to order','#14532d',[
 '<tspan font-weight="bold">9 breadboards</tspan> = 3 stations × 3 boards. Exactly what was ordered.',
 '<tspan font-weight="bold">AS5600 ×5</tspan> covers it, because the bench unit is <tspan font-weight="bold">the one you then fit</tspan>',
 '~to that vehicle — better anyway, since AGC is tuned per part.',
 '<tspan font-weight="bold">The drive board needs no AS5600; the steering board needs no latches.</tspan>',
 'Splitting them costs one breadboard and buys a harness-shaped bench.',
 'Jumper sets ×3 — one per station — is also right.',
 '<tspan font-weight="bold">Nothing on these boards may carry coil current.</tspan> No relay, no MOSFET,',
 '~no 12 V. Signal on breadboard, authority on soldered perfboard.',
],'#166534')

panel(614,96,542,250,'#fffbeb','#f59e0b','After the VUSB–VIN cut: USB is data only','#92400e',[
 '<tspan font-weight="bold">Yes.</tspan> The laptop still programs the board and still carries',
 'micro-ROS. <tspan font-weight="bold">It just cannot power it.</tspan> 5 V comes from a UBEC',
 'into VIN, on the bench and on the vehicle alike.',
 'The cut exists so <tspan font-weight="bold">the laptop\'s 5 V and the UBEC\'s 5 V</tspan>',
 '<tspan font-weight="bold">never meet</tspan> and push current into each other through',
 'the Teensy.',
 '<tspan font-weight="bold">A Teensy that seems dead on USB after the cut is</tspan>',
 '<tspan font-weight="bold">working correctly.</tspan> Tape a note inside the parts box.',
],'#78350f')

panel(24,376,1132,300,'#f8fafc','#94a3b8','Prove it in this order — each step fails for a different reason','#0f172a',[
 '<tspan font-weight="bold">1 · Power only.</tspan> 5 V at VIN. Meter the + rail on <tspan font-weight="bold">board C</tspan>, the far end of the chain: 3.3 V there proves the 3V3 pin, both rail',
 '~bridges and both board-to-board feeds in one reading. Not there → a wire, not a sensor.',
 '<tspan font-weight="bold">2 · Latches, on a meter, before any code.</tspan> Probe each OUT against GND and pass a magnet by. It must snap between <tspan font-weight="bold">0 V</tspan>',
 '~<tspan font-weight="bold">and 3.3 V and stay there</tspan> when the magnet leaves — that is what makes it a <tspan font-style="italic">latch</tspan>. Falls back on its own → it is a switch, and',
 '~the whole quadrature scheme is wrong. <tspan font-weight="bold">Flip the magnet to reset it.</tspan>',
 '<tspan font-weight="bold">3 · I²C scan.</tspan> <tspan font-weight="bold">0x36</tspan> must appear, and nothing else — one device per bus is the design.',
 '<tspan font-weight="bold">4 · AGC.</tspan> Read <tspan font-weight="bold">0x1A</tspan> at the working gap, tune to mid-scale, and <tspan font-weight="bold">write the gap down</tspan> — it is the number the other two',
 '~vehicles are built to.',
 '<tspan font-weight="bold">5 · Counts last.</tspan> Bring up the decoder and move a magnet past both latches in sequence. Up one way and down the other',
 '~is the <tspan font-weight="bold">first proof the (n + ½) spacing is right</tspan> — cheap here, expensive on a wheel.',
 '<tspan font-weight="bold" fill="#15803d">Steps 1–3 need no firmware beyond a scan sketch. If something is wrong, it is wrong before code can be blamed.</tspan>',
],'#334155',ls=22,fs=12.5)

panel(24,706,1132,186,'#fef2f2','#ef4444','Before a single wire goes in','#991b1b',[
 '<tspan font-weight="bold">The TO-92 pin order is not guessable.</tspan> Reversed V<tspan font-size="9">CC</tspan>/GND destroys the part — that is what the fourteen spares are for, and it is',
 '~a far cheaper lesson on a breadboard than on a soldered board. <tspan font-weight="bold">Bend the legs out to 2.54 mm</tspan> before inserting.',
 '<tspan font-weight="bold">Keep them in the labelled bag until each one is fitted.</tspan> TI marks a TO-92 body with an abbreviated code, so loose parts are',
 '~unidentifiable and <tspan font-weight="bold">BC looks exactly like AG</tspan>.',
 '<tspan font-weight="bold">Beep the three boards\' − rails together before powering up.</tspan> A missing ground reads as a dead sensor, and on the vehicle',
 '~this same joint becomes the star ground at the motor driver.',
],'#7f1d1d',ls=22,fs=12.5)



e('</svg>')
open(__import__('pathlib').Path(__file__).resolve().parent.parent/'docs'/'images'/'breadboard-procedure.svg','w',encoding='utf-8').write('\n'.join(out))
print('written 2')
