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
"""Two wiring claims that are each made in two places, compared.

Both stood wrong until 2026-11-10 and both were found by an outside review rather
than by anything in this repository.

A. SERIES PARTS IN A HARNESS
   harness/traction-supply.yml ran a red/black PAIR through the fuse and the
   contactor: pack + on `in`, pack - on `out`. Built as drawn, that is the pack
   shorted through its own fuse. WireViz was content, because to WireViz a
   2-pin part is a 2-pin part.

   A 2-pin part labelled [in, out], or typed as a fuse, contactor or switch,
   is a series part: two ends of ONE conductor. So across every connection set
   the wires on its two terminals must be the same colour, and must not be two
   cores of one cable.

B. THE TEENSY PIN ASSIGNMENT
   docs/build/04-firmware.md holds the pin table and says it is the only one.
   scripts/gen_signal_board_figure.py keeps a copy "so the drawing can place
   things". The table read "not assigned" for four signals the figure had
   already put on pins 2, 3, 15 and 21, so the page that says "freeze this
   before an iron is hot" was the one page that could not be soldered from.

   The two must name the same pins for the same signals, in both directions,
   and the table may not say "not assigned".
"""
import ast
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
problems = []

# ---------------------------------------------------------------- A
SERIES_TYPE = re.compile(r"fuse|contactor|switch|breaker|isolator", re.I)


def pin_list(pins):
    """WireViz accepts [1, 2] and ['1-2']; flatten both."""
    out = []
    for p in pins if isinstance(pins, list) else [pins]:
        m = re.fullmatch(r"(\d+)-(\d+)", str(p))
        out.extend(range(int(m.group(1)), int(m.group(2)) + 1) if m else [p])
    return out


for yml in sorted((ROOT / "harness").glob("*.yml")):
    data = yaml.safe_load(yml.read_text())
    cables = data.get("cables") or {}
    series = {
        name for name, c in (data.get("connectors") or {}).items()
        if c.get("pincount") == 2 and (
            [str(p).lower() for p in c.get("pinlabels", [])] == ["in", "out"]
            or SERIES_TYPE.search(str(c.get("type", ""))))
    }
    # Every conductor that touches each pin of a series part, across ALL
    # connection sets - the same short split over two sets is still a short.
    touch = {name: {} for name in series}
    for conn in data.get("connections") or []:
        hops = [(n, pin_list(p)) for h in conn if isinstance(h, dict) for n, p in h.items()]
        for i, (name, pins) in enumerate(hops):
            if name not in series:
                continue
            for j in (i - 1, i + 1):
                if 0 <= j < len(hops) and hops[j][0] in cables:
                    cab, wires = hops[j]
                    colors = cables[cab].get("colors", [])
                    for pin, w in zip(pins, wires):
                        col = colors[int(w) - 1] if str(w).isdigit() and int(w) <= len(colors) else "?"
                        touch[name].setdefault(pin, set()).add((cab, w, col))
    for name, by_pin in touch.items():
        cols = {pin: {c for _, _, c in ws} for pin, ws in by_pin.items()}
        cabs = {pin: {(cab) for cab, _, _ in ws} for pin, ws in by_pin.items()}
        pins = sorted(by_pin, key=str)
        if len(pins) == 2:
            if cols[pins[0]] != cols[pins[1]]:
                problems.append(
                    f"{yml.relative_to(ROOT)}: {name} is a series part, but its two "
                    f"terminals carry different conductors ({sorted(cols[pins[0]])} "
                    f"and {sorted(cols[pins[1]])}). They are two ends of ONE.")
            elif cabs[pins[0]] & cabs[pins[1]]:
                problems.append(
                    f"{yml.relative_to(ROOT)}: one cable lands on both terminals of "
                    f"{name}, a series part.")

# ---------------------------------------------------------------- B
gen = (ROOT / "scripts" / "gen_signal_board_figure.py").read_text()
m = re.search(r"^USED = (\[.*?^\])", gen, re.S | re.M)
if not m:
    problems.append("gen_signal_board_figure.py: no USED list found")
    used = []
else:
    used = [(sig, pin) for sig, pin, *_ in ast.literal_eval(
        m.group(1).replace("T_BOT", "0").replace("T_TOP", "0"))]

# What the table's row must say for the figure's short name to be the same signal.
SAME = {
    "drive A": r"encoder \*\*A\*\*", "drive B": r"encoder \*\*B\*\*",
    "PWM steer": r"PWM.*steering", "PWM drive": r"PWM.*drive",
    "SCL": r"SCL", "SDA": r"SDA", "E-stop": r"E-stop sense",
    "gate out": r"Relay gate", "i-BUS RX": r"i-BUS",
}

fw = (ROOT / "docs" / "build" / "04-firmware.md").read_text()
m = re.search(r"\| Signal \| Pin \|.*?\n((?:\|.*\n)+)", fw)
rows = m.group(1).splitlines()[1:] if m else []
if not rows:
    problems.append("04-firmware.md: pin table not found")
table = {}
for row in rows:
    cells = [c.strip() for c in row.strip("|").split("|")]
    if len(cells) < 2:
        problems.append(f"04-firmware.md: malformed pin-table row: {row[:60]}")
        continue
    if "not assigned" in cells[1]:
        problems.append(f"04-firmware.md: pin table still says 'not assigned' for {cells[0]}")
    for pin in re.findall(r"\*\*(\d+)\*\*", cells[1]):
        table[pin] = cells[0]
for sig, pin in used if rows else []:
    if pin not in table:
        problems.append(f"signal-board figure puts '{sig}' on pin {pin}; "
                        f"the pin table in 04-firmware.md has no such pin")
    elif sig not in SAME:
        problems.append(f"signal-board figure has a signal '{sig}' this check cannot name; add it to SAME")
    elif not re.search(SAME[sig], table[pin]):
        problems.append(f"pin {pin}: the figure calls it '{sig}', the pin table '{table[pin]}'")
for pin in sorted(set(table) - {p for _, p in used}, key=int):
    problems.append(f"pin table assigns pin {pin} ({table[pin]}); the signal-board figure does not use it")

if problems:
    for p in problems:
        print("   " + p, file=sys.stderr)
    sys.exit(1)
print(f"   {len(used)} figure pins agree with the pin table; no series part is fed a pair")
