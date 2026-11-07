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
r"""One source for every number the drive-encoder figures quote.

    python3 scripts/carrier_params.py       # print them, and cross-check

WHY THIS IS A MODULE AND NOT A CONSTANT BLOCK IN EACH FIGURE
-------------------------------------------------------------
Five figures describe the same printed part. Before this existed they each
typed their own copy of its dimensions, and two of them were wrong:

  drive-encoder-carrier.svg  drew the sensors a FULL pitch apart under a label
                             that said HALF
  grub-screw-points.svg      said a seated screw stands "0.10-0.70 mm proud"
                             where the model computes 0.05-0.75

The second one has a physical consequence rather than just an embarrassing
one. The .scad says of that figure "set the air gap ABOVE this"; believing
0.70 and setting a 0.72 mm gap lets a worst-case screw sweep the sensor, which
is the exact failure the two-piece carrier was abandoned for.

WHAT IT DOES
------------
Reads the INPUT parameters out of cad/drive_encoder_carrier.scad, recomputes
the derived ones here, and then checks that arithmetic against OpenSCAD's own
echo output. The model is the authority - it is the thing that was printed and
fitted - so if Python and OpenSCAD ever disagree, nothing is drawn.
"""
import math
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCAD = REPO / "cad" / "drive_encoder_carrier.scad"

# Six lobes are a feature of the HUB. The carrier's bore is plain and round, so
# this is an observation of the vehicle, not a model parameter, and it is kept
# here rather than dressed up as one.
N_LOBE = 6

_INPUTS = ("HUB_D", "HUB_TOL", "WALL", "WIDTH", "BORE_CLEAR", "N_MAG", "MAG_D",
           "MAG_T", "N_SET", "SET_TAP_D", "SET_SCREW_L", "MARK_W", "MARK_DEPTH",
           "AXIAL_GAP", "SENSOR_GAP", "SENSOR_T")


def read():
    src = SCAD.read_text(encoding="utf-8")
    p = {}
    for name in _INPUTS:
        m = re.search(r"^%s\s*=\s*([-0-9.]+)\s*;" % name, src, re.M)
        assert m, f"{name} not found in {SCAD.name}"
        p[name] = float(m.group(1))
    p["N_MAG"] = int(p["N_MAG"])
    p["N_SET"] = int(p["N_SET"])

    d = dict(p)
    d["N_LOBE"] = N_LOBE
    d["BORE_D"] = p["HUB_D"] + p["BORE_CLEAR"]
    d["OD"] = d["BORE_D"] + 2 * p["WALL"]
    d["CIRC"] = math.pi * d["OD"]
    d["PITCH"] = d["CIRC"] / p["N_MAG"]
    d["OFFSET"] = d["PITCH"] / 2
    d["COUNTS"] = 2 * p["N_MAG"]
    d["SET_A0"] = 180.0 / p["N_MAG"]

    # What a grub screw has to cross to touch the hub, and what is left over.
    # SPAN is a distance to a CREST, because HUB_D is measured across opposite
    # crests. A valley sits deeper by the lobe depth, which nobody has measured.
    d["SPAN_MIN"] = p["WALL"] + (p["BORE_CLEAR"] - p["HUB_TOL"]) / 2
    d["SPAN_MAX"] = p["WALL"] + (p["BORE_CLEAR"] + p["HUB_TOL"]) / 2
    d["PROUD_MIN"] = p["SET_SCREW_L"] - d["SPAN_MAX"]
    d["PROUD_MAX"] = p["SET_SCREW_L"] - d["SPAN_MIN"]

    # The sensors. A sits on the MAGNET nearest the top of a drawing and B is A
    # plus the quadrature offset as an angle, which is half a pitch - so B
    # necessarily lands on a BOUNDARY. Deriving them is the point: putting A at
    # a round 270 degrees looks right and is wrong whenever 270 is not a
    # multiple of 360/N_MAG, and then the caption is exactly reversed.
    step = 360.0 / p["N_MAG"]
    d["STEP"] = step
    d["A_DEG"] = round(270.0 / step) * step
    d["B_DEG"] = d["A_DEG"] + d["OFFSET"] / d["CIRC"] * 360.0
    return d


def cross_check(d, quiet=True):
    """Hold this module's arithmetic against the model's own echo output."""
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
             ("SWEPT Ø", d["OD"]),
             ("WORST-CASE SCREW STAND-OFF", d["PROUD_MAX"])]
    for key, ours in pairs:
        m = re.search(re.escape(key) + r"\s*([0-9.]+)", echo)
        assert m, f"openscad did not echo {key!r}; the model changed"
        theirs = float(m.group(1))
        assert abs(theirs - ours) < 0.01, \
            f"{key}: this module says {ours:.4f}, the .scad says {theirs:.4f}"
    # the span pair is echoed as one line
    m = re.search(r"screw span needed\s*([0-9.]+)\s*to\s*([0-9.]+)", echo)
    assert m, "openscad did not echo the screw span"
    assert abs(float(m.group(1)) - d["SPAN_MIN"]) < 0.01
    assert abs(float(m.group(2)) - d["SPAN_MAX"]) < 0.01
    if not quiet:
        print("  cross-checked against openscad")
    return True


def load():
    d = read()
    d["_checked"] = cross_check(d)
    return d


if __name__ == "__main__":
    d = load()
    for k in sorted(k for k in d if not k.startswith("_")):
        v = d[k]
        print(f"  {k:<12} {v:.4f}" if isinstance(v, float) else f"  {k:<12} {v}")
    print(f"\n  cross-checked: {d['_checked']}")
