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
r"""Prose and figures must quote the carrier the way the model computes it.

    python3 scripts/check_carrier_numbers.py

WHY THIS EXISTS
---------------
On 2026-11-07 three figures were migrated onto cad/drive_encoder_carrier.scad
and every one of them turned out to be quoting a number the model does not
produce. Then the PROSE turned out to carry the same three errors, because the
figures and the pages had been copying each other rather than the part:

    SPAN_MAX   said 7.90        model 7.95
    proud      said 0.10-0.70   model 0.05-0.75
    screw past said 3 mm        model 1.00 mm   (a fossil of the rejected M3x10)

Generating the figures fixes the figures. It does nothing for a sentence, and
a sentence is what a builder reads at eleven at night.

TWO RULES, AND THEY PULL IN OPPOSITE DIRECTIONS
------------------------------------------------
1. SUPERSEDED values must not reappear anywhere. These are not typos, they are
   old answers, and an old answer reads exactly like a current one.

2. Values someone BUILDS TO are deliberately rounded. 01-bom-sourcing.md:
   "Build to the round figures - pitch 13.60, offset 6.80 ... carrying the
   extra digit into a drawing would be false precision." So a drawing quoting
   13.62 or 6.81 is ALSO wrong - in the other direction. A margin someone
   CHECKS keeps its digits, which is why 0.05 is not rounded to 0.1.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import carrier_params  # noqa: E402

REPO = Path(__file__).resolve().parent.parent

# Only files that actually discuss the carrier. A blanket scan for "7.90"
# across the repo would hit prices, and a check that cries wolf gets muted.
SCOPE_HINTS = ("drive_encoder_carrier", "grub screw", "magnet pitch", "HUB_D",
               "lobe crest", "SPAN_MAX", "magnet track", "Hall latch")

SUPERSEDED = [
    (r"SPAN_MAX\s*=?\s*7\.90", "SPAN_MAX is 7.95; 7.90 is a superseded value"),
    (r"0\.10\s*[-–]\s*0\.70", "the screw stands 0.05-0.75 proud, not 0.10-0.70"),
    (r"reach(?:es)? 3 mm past", "an M3x8 reaches 1.00 mm past the bore; 3 mm was the "
                                "rejected M3x10"),
    (r"five times what they must close", "it is 1.05x, not five times"),
]


# The air-gap floor is NOT a round number: a grub screw seated on a crest can
# stand PROUD_MAX above the OD, so the sensor must stay clear of it. These three
# say so, and if PROUD_MAX ever moves they have to move with it. Naming the
# files keeps the rule narrow - a check that cries wolf gets muted.
MUST_QUOTE_PROUD = (
    "docs/build/01-bom-sourcing.md",
    "docs/images/grub-screw-points.svg",
    "docs/images/hall-sensor-mounting.svg",
)


def in_scope(text):
    return any(h in text for h in SCOPE_HINTS)


def main():
    d = carrier_params.load()
    bad = []

    files = sorted(list((REPO / "docs").rglob("*.md")) +
                   list((REPO / "docs" / "images").glob("*.svg")))
    scanned = 0
    for f in files:
        if "archive" in f.parts:
            continue
        text = f.read_text(encoding="utf-8", errors="replace")
        if not in_scope(text):
            continue
        scanned += 1
        rel = f.relative_to(REPO)
        for pat, why in SUPERSEDED:
            for m in re.finditer(pat, text):
                line = text[:m.start()].count("\n") + 1
                bad.append(f"{rel}:{line}  {m.group(0)!r} - {why}")

        # Rule 2 applies to DRAWINGS: they carry build figures, not computed ones.
        if f.suffix == ".svg":
            for val, name in ((f"{d['PITCH']:.2f}", "pitch"),
                              (f"{d['OFFSET']:.2f}", "offset")):
                for m in re.finditer(re.escape(val) + r"\s*mm", text):
                    line = text[:m.start()].count("\n") + 1
                    bad.append(
                        f"{rel}:{line}  {val} mm - a drawing builds to the ROUND "
                        f"figure ({d[name.upper() + '_BUILD']:.2f}); see "
                        f"01-bom-sourcing.md on false precision")

    for rel in MUST_QUOTE_PROUD:
        f = REPO / rel
        assert f.exists(), f"{rel} is in MUST_QUOTE_PROUD but does not exist"
        if f"{d['PROUD_MAX']:.2f}" not in f.read_text(encoding="utf-8",
                                                      errors="replace"):
            bad.append(f"{rel}  does not state the {d['PROUD_MAX']:.2f} mm "
                       f"stand-off that sets the sensor air-gap floor")

    if bad:
        print("carrier numbers that do not match the model:", file=sys.stderr)
        for b in bad:
            print("   " + b, file=sys.stderr)
        return 1
    print(f"   ok  ({scanned} pages and figures scanned against "
          f"cad/{carrier_params.SCAD.name})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
