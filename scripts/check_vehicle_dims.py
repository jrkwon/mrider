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
2. VALUES that are DERIVED: Nav2's turning radii are not copies of anything,
   they are >= wheelbase / tan(steer_limit) with margin. Checking them as
   copies would be wrong; checking the inequality is the real contract, and
   it is the one that breaks silently when somebody finally measures the
   wheelbase and updates only the file they were looking at.
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

# Nav2's radii are a FLOOR with margin, not a copy.
DERIVED_RADII = [("min_turning_radius", NAV), ("minimum_turning_radius", NAV)]


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

    # R_min = wheelbase / tan(steer_limit). Nav2 must sit at or above it.
    r_min = d["wheelbase"] / math.tan(math.radians(d["steer_limit_deg"]))
    nav = scalars(NAV)
    for key, path in DERIVED_RADII:
        if key not in nav:
            bad.append(f"{path.name} has no {key}")
            continue
        if nav[key] < r_min - 1e-9:
            bad.append(f"{path.name}:{key} = {nav[key]} is BELOW the physical "
                       f"{r_min:.2f} m (wheelbase {d['wheelbase']} / "
                       f"tan {d['steer_limit_deg']}deg) - Nav2 would plan paths "
                       f"the vehicle cannot drive")

    if len(set(nav.get(k, object()) for k, _ in DERIVED_RADII)) != 1:
        bad.append("the two Nav2 turning radii disagree with each other; "
                   "the planner and the controller must share one floor")

    if bad:
        print("vehicle geometry disagrees across packages:", file=sys.stderr)
        for b in bad:
            print("   " + b, file=sys.stderr)
        return 1

    print(f"   ok  (wheelbase {d['wheelbase']} m, steer {d['steer_limit_deg']}deg "
          f"-> R_min {r_min:.2f} m; Nav2 at "
          f"{nav['min_turning_radius']} m)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
