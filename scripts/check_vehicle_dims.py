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
r"""The vehicle's geometry is stated in three files. Make them agree.

    python3 scripts/check_vehicle_dims.py

WHY THIS EXISTS
---------------
mitt_controllers.yaml carried this comment:

    "It is duplicated here because ros2_control params cannot read that yaml
     directly; mitt_bringup checks the two agree at launch."

No such check existed. mitt_bringup contains one file, sim.launch.py, and it
never opens mitt_dimensions.yaml. The claim had been in the repository long
enough to be believed, which is worse than no claim at all: a reader who sees
"this is checked" stops checking.

The first half of the comment is true and is the reason this is a script
rather than a shared parameter - ros2_control reads its own YAML and cannot
dereference another package's. So the duplication stays and the agreement gets
enforced from outside, which also means it runs in CI without a ROS install.

WHAT IT CHECKS
--------------
1. VALUES that are copies: a copy that drifts is the whole hazard.
2. A FLOOR: Nav2's planner radius is not a copy of anything, it must be >=
   the vehicle's turning radius with margin. Checking it as a copy would be
   wrong; checking the inequality is the real contract, and it is the one
   that breaks silently when somebody finally measures the vehicle and
   updates only the file they were looking at.

   The floor is `min_turning_radius` in mitt_dimensions.yaml - a value each
   team MEASURES (docs/design/calibration.md 1.5). Until 2026-11-16 the floor
   was computed here as wheelbase / tan(steer_limit) and compared against two
   Nav2 keys. One of the two, `min_turning_radius` on the RPP controller, is
   not a parameter Nav2 1.1.20 declares; it was ignored at runtime while this
   script kept it carefully in step with the planner's. It is gone from
   nav2_params.yaml, and this script now fails if it comes back.
"""
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DIMS = REPO / "ros2_ws/src/mitt_description/config/mitt_dimensions.yaml"
CTRL = REPO / "ros2_ws/src/mitt_control/config/mitt_controllers.yaml"
NAV = REPO / "ros2_ws/src/mitt_navigation/config/nav2_params.yaml"


def scalars(path):
    """Flat `key: number` pairs. Enough for these files and no yaml dependency,
    which is the point - this has to run before anything is built."""
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^\s*([a-z_][a-z0-9_]*)\s*:\s*(-?\d+(?:\.\d+)?)\s*(?:#.*)?$",
                     line, re.I)
        if m:
            out.setdefault(m.group(1), float(m.group(2)))
    return out


# (name in mitt_dimensions, name in the other file, which file)
COPIES = [
    ("wheelbase", "wheelbase", CTRL),
    ("track_width", "front_wheel_track", CTRL),
    ("track_width", "rear_wheel_track", CTRL),
    ("wheel_radius", "front_wheels_radius", CTRL),
    ("wheel_radius", "rear_wheels_radius", CTRL),
]

# Nav2's planner radius sits on a FLOOR with margin; it is not a copy.
PLANNER_RADIUS = "minimum_turning_radius"   # SmacPlannerHybrid
FLOOR = "min_turning_radius"                # mitt_dimensions.yaml, measured
# How far the measured radius may sit from wheelbase / tan(steer_limit) before
# it is worth a line of output. Not an error: the measurement is the truth.
SURPRISE = 0.15


def main():
    for f in (DIMS, CTRL, NAV):
        if not f.exists():
            print(f"   missing: {f.relative_to(REPO)}", file=sys.stderr)
            return 1

    d = scalars(DIMS)
    bad = []

    for src, dst, path in COPIES:
        other = scalars(path)
        if src not in d:
            bad.append(f"{DIMS.name} has no {src}")
            continue
        if dst not in other:
            bad.append(f"{path.name} has no {dst}")
            continue
        if abs(d[src] - other[dst]) > 1e-9:
            bad.append(f"{path.name}:{dst} = {other[dst]} but "
                       f"{DIMS.name}:{src} = {d[src]}")

    # The planner must sit at or above the vehicle's turning radius.
    derived = d["wheelbase"] / math.tan(math.radians(d["steer_limit_deg"]))
    nav = scalars(NAV)
    floor = d.get(FLOOR)
    if floor is None:
        bad.append(f"{DIMS.name} has no {FLOOR}")
    if PLANNER_RADIUS not in nav:
        bad.append(f"{NAV.name} has no {PLANNER_RADIUS}")
    elif floor is not None and nav[PLANNER_RADIUS] < floor - 1e-9:
        bad.append(f"{NAV.name}:{PLANNER_RADIUS} = {nav[PLANNER_RADIUS]} is "
                   f"BELOW the vehicle's {floor} m ({DIMS.name}:{FLOOR}) - "
                   f"Nav2 would plan paths the vehicle cannot drive")
    if FLOOR in nav:
        bad.append(f"{NAV.name} has a `{FLOOR}` key again. Nav2's RPP declares "
                   f"no such parameter; it is ignored at runtime and reads as "
                   f"though it constrains something")

    if bad:
        print("vehicle geometry disagrees across packages:", file=sys.stderr)
        for b in bad:
            print("   " + b, file=sys.stderr)
        return 1

    print(f"   ok  (turning radius {floor} m in {DIMS.name}; Nav2 plans at "
          f"{nav[PLANNER_RADIUS]} m)")
    if abs(floor - derived) > SURPRISE * derived:
        print(f"   note: that is {abs(floor - derived) / derived:.0%} away from "
              f"wheelbase / tan(steer limit) = {derived:.2f} m. If all three "
              f"were measured, the steering does not reach its nominal lock.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
