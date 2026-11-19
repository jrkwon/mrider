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

   The floor is `min_turning_radius` - a value each team MEASURES
   (docs/design/calibration.md 1.5) and records in its vehicle's overlay
   (item 3); mitt_dimensions.yaml keeps the derived figure. Until 2026-11-16 the floor
   was computed here as wheelbase / tan(steer_limit) and compared against two
   Nav2 keys. One of the two, `min_turning_radius` on the RPP controller, is
   not a parameter Nav2 1.1.20 declares; it was ignored at runtime while this
   script kept it carefully in step with the planner's. It is gone from
   nav2_params.yaml, and this script now fails if it comes back.
3. EACH VEHICLE'S OVERLAY (since 2026-11-17). Three teams build three
   vehicles. mitt_dimensions.yaml stays the estimates; what team N measured
   is config/vehicles/vehicle<N>.yaml, laid over it by `xacro vehicle:=N` and
   by mitt_description/config/vehicle_config.py. Checked here: every key is
   one the base file has (a misspelt key would be ignored and the estimate
   used in silence) and no line still says TODO (an overlay holds measured
   values only). The copies in mitt_controllers.yaml and nav2_params.yaml are
   compared against the ESTIMATES only; for a vehicle they are generated at
   launch, not committed.
4. NAV2'S OWN COPIES (since 2026-11-18). The costmap footprint is the outline
   of the body and wheels in mitt_dimensions.yaml, stated once per costmap,
   and had been typed by hand twice. Both lines must equal what
   vehicle_config.footprint() makes of the estimates, and the planner radius
   must equal vehicle_config.planner_radius() of the estimate - the rules
   `nav2.launch.py vehicle:=N` applies to a vehicle's measured values. Until
   that date the planner radius in the one committed file had to clear all
   three vehicles; now each vehicle gets its own, so that check is gone and
   this script prints what each would run on.

5. THE INFLATION RADIUS (since 2026-11-19). Both costmaps' inflation_radius
   must equal vehicle_config.inflation_radius() of the estimates: the
   distance from base_link to the footprint's farthest corner, rounded up to
   5 cm. It was 0.55 m under a footprint that reaches 0.857 m, and
   SmacPlannerHybrid does not collision-check a corner that inflation does
   not reach (docs/design/software.md 4.7).
"""
import importlib.util
import math
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DIMS = REPO / "ros2_ws/src/mitt_description/config/mitt_dimensions.yaml"
CTRL = REPO / "ros2_ws/src/mitt_control/config/mitt_controllers.yaml"
NAV = REPO / "ros2_ws/src/mitt_navigation/config/nav2_params.yaml"
VEHICLE_DIR = DIMS.parent / "vehicles"
VEHICLE_CONFIG = DIMS.parent / "vehicle_config.py"


def _vehicle_config():
    """The launch-time module, loaded by path: its list of which dimension
    feeds which controller key is the one this script uses too."""
    spec = importlib.util.spec_from_file_location("vehicle_config", VEHICLE_CONFIG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def overlay(path, base):
    """One vehicle's measured values, and what is wrong with the file."""
    bad = []
    seen = set()
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        body = line.split("#", 1)[0].strip()
        if not body:
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*)\s*:\s*(-?\d+(?:\.\d+)?)$", body)
        if not m:
            bad.append(f"{path.name}:{n} is not `key: number` - {body!r}")
        elif m.group(1) not in base:
            bad.append(f"{path.name}:{n} `{m.group(1)}` is not a key of {DIMS.name}")
        elif m.group(1) in seen:
            # This script reads the first copy and yaml reads the last.
            bad.append(f"{path.name}:{n} `{m.group(1)}` is written twice")
        elif "TODO" in line:
            bad.append(f"{path.name}:{n} `{m.group(1)}` still says TODO - an "
                       f"overlay holds measured values only; delete the line "
                       f"until it is measured")
        if m:
            seen.add(m.group(1))
    return ({} if bad else scalars(path)), bad

# Nav2's planner radius sits on a FLOOR with margin; it is not a copy.
PLANNER_RADIUS = "minimum_turning_radius"   # SmacPlannerHybrid
FLOOR = "min_turning_radius"                # mitt_dimensions.yaml, measured
# How far the measured radius may sit from wheelbase / tan(steer_limit) before
# it is worth a line of output. Not an error: the measurement is the truth.
SURPRISE = 0.15


def main():
    for f in (DIMS, CTRL, NAV, VEHICLE_CONFIG):
        if not f.exists():
            print(f"   missing: {f.relative_to(REPO)}", file=sys.stderr)
            return 1

    d = scalars(DIMS)
    bad = []
    vc = _vehicle_config()

    for src, dst in vc.GEOMETRY:
        path = CTRL
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
    elif floor is not None and abs(nav[PLANNER_RADIUS] - vc.planner_radius(floor)) > 1e-9:
        bad.append(f"{NAV.name}:{PLANNER_RADIUS} = {nav[PLANNER_RADIUS]} but "
                   f"the rule gives {vc.planner_radius(floor)} for the "
                   f"estimate {floor} m ({DIMS.name}:{FLOOR}). That file is "
                   f"the estimates; a vehicle's value is generated at launch")
    if FLOOR in nav:
        bad.append(f"{NAV.name} has a `{FLOOR}` key again. Nav2's RPP declares "
                   f"no such parameter; it is ignored at runtime and reads as "
                   f"though it constrains something")

    # The footprint is a copy of the body box, stated once per costmap.
    want = vc.footprint(d) if all(k in d for k in vc.FOOTPRINT_KEYS) else None
    stated = re.findall(r'^\s*footprint\s*:\s*"([^"]*)"\s*(?:#.*)?$',
                        NAV.read_text(encoding="utf-8"), re.M)
    if want is None:
        bad.append(f"{DIMS.name} lacks one of: {', '.join(vc.FOOTPRINT_KEYS)}")
    elif len(stated) != 2:
        bad.append(f"{NAV.name} states `footprint` {len(stated)} time(s); the "
                   f"local and the global costmap each need it")
    else:
        for got in stated:
            if got != want:
                bad.append(f"{NAV.name}:footprint = {got} but the body and "
                           f"wheels of {DIMS.name} give {want}")

    # Inflation must reach the footprint's farthest corner, in both costmaps.
    inflation = re.findall(r'^\s*inflation_radius\s*:\s*([0-9.]+)\s*(?:#.*)?$',
                           NAV.read_text(encoding="utf-8"), re.M)
    if want is not None:
        need = vc.inflation_radius(d)
        if len(inflation) != 2:
            bad.append(f"{NAV.name} states `inflation_radius` {len(inflation)} "
                       f"time(s); the local and the global costmap each need it")
        for got in inflation:
            if abs(float(got) - need) > 1e-9:
                bad.append(f"{NAV.name}:inflation_radius = {got} but the "
                           f"footprint of {DIMS.name} needs {need}: the "
                           f"planner does not check a corner that inflation "
                           f"does not reach")

    # Each vehicle: its overlay is well formed, and what Nav2 would run on.
    measured = {}
    nav_for = {}
    for v in vc.VEHICLES:
        path = VEHICLE_DIR / f"vehicle{v}.yaml"
        if not path.exists():
            bad.append(f"{path.relative_to(REPO)} is missing")
            continue
        over, problems = overlay(path, d)
        bad += problems
        measured[v] = sorted(over)
        if not problems and want is not None:
            try:
                nav_for[v] = vc.nav2_values(d, over)
            except ValueError as e:
                bad.append(f"{path.name}: {e}")

    if bad:
        print("vehicle geometry disagrees across packages:", file=sys.stderr)
        for b in bad:
            print("   " + b, file=sys.stderr)
        return 1

    print(f"   ok  (turning radius {floor} m in {DIMS.name}; Nav2 plans at "
          f"{nav[PLANNER_RADIUS]} m)")
    for v, keys in measured.items():
        print(f"       vehicle {v}: " + (f"{len(keys)} measured - {', '.join(keys)}"
                                         if keys else "nothing measured yet"))
        own = nav_for.get(v, {})
        radius = own.get(PLANNER_RADIUS)
        print("                  Nav2 plans at "
              + (f"{radius} m, 5% above its measured radius" if radius is not None
                 else f"{nav[PLANNER_RADIUS]} m, the estimate - and refuses to "
                      f"start on the real vehicle until {FLOOR} is measured"))
        print("                  Nav2 footprint "
              + (own["footprint"] if "footprint" in own
                 else f"{want}, the estimate"))
    if abs(floor - derived) > SURPRISE * derived:
        print(f"   note: that is {abs(floor - derived) / derived:.0%} away from "
              f"wheelbase / tan(steer limit) = {derived:.2f} m. If all three "
              f"were measured, the steering does not reach its nominal lock.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
