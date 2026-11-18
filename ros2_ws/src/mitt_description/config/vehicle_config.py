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

"""
One vehicle's numbers, for the launch files that need them.

NOT a parameter file - it is a Python module that sits in config/ because that
directory is installed, and because the files it reads are its neighbours.
sim.launch.py and real.launch.py (mitt_bringup) and nav2.launch.py
(mitt_navigation) import it from this package's share directory; it lives
here, not in mitt_bringup, because mitt_bringup depends on mitt_navigation
and the import cannot run the other way.

Three teams build three vehicles, and no two measure the same wheelbase. The
estimates every vehicle starts from are config/mitt_dimensions.yaml; what
team N has measured is config/vehicles/vehicle<N>.yaml, laid over it. The
URDF takes the merged values through `xacro vehicle:=N`. This module covers
the two consumers that cannot read that file.

1. mitt_controllers.yaml carries its own copy of the geometry (the Ackermann
   controller needs wheelbase, track and wheel radius, and reads no other
   file). For a vehicle whose measured values differ, controllers_for()
   writes a copy of the controller file with those five numbers replaced.

2. nav2_params.yaml carries the costmap footprint (twice) and the planner's
   minimum turning radius. nav2_for() writes a copy with the outline of that
   vehicle's body and wheels, and a planner radius above its measured one.

Both return the path of the copy; the committed file is never edited. With
vehicle 0, or an overlay that touches none of the values a file depends on,
they return the committed file itself. scripts/check_vehicle_dims.py keeps
the committed copies equal to the estimates, using the rules written here.

Controllers: written 2026-11-17, exercised in the twin with a test overlay.
Nav2: written 2026-11-18. No vehicle has measured values yet, so no real
overlay has been through either.
"""

import getpass
import math
import os
import tempfile

VEHICLES = (1, 2, 3)

# (key in mitt_dimensions.yaml, key in mitt_controllers.yaml).
# scripts/check_vehicle_dims.py reads these rules rather than keeping its own.
GEOMETRY = (
    ('wheelbase', 'wheelbase'),
    ('track_width', 'front_wheel_track'),
    ('track_width', 'rear_wheel_track'),
    ('wheel_radius', 'front_wheels_radius'),
    ('wheel_radius', 'rear_wheels_radius'),
)


# Vehicle N lives in ROS domain DOMAIN_BASE + N (docs/design/software.md 3.4).
# scripts/check_docs.sh reads the next line and compares it with setup_env.sh
# and the design page; real.launch.py and nav2.launch.py take it from here.
DOMAIN_BASE = 10

# Nav2. The footprint is the outline of the URDF (mitt_base.xacro): the body
# box, centred between the axles, and the four wheels. These keys place it.
FOOTPRINT_KEYS = ('wheelbase', 'chassis_length', 'chassis_width',
                  'track_width', 'wheel_radius', 'wheel_width')
TURNING_RADIUS = 'min_turning_radius'       # mitt_dimensions.yaml, measured
PLANNER_RADIUS = 'minimum_turning_radius'   # nav2_params.yaml, SmacPlannerHybrid
# The planner plans this much wider than the vehicle turns. 5% is the margin
# the committed file already keeps over the estimate (1.52 m -> 1.6 m).
PLANNER_MARGIN = 1.05


def parse_vehicle(vehicle):
    """The vehicle number as an int: 0, or one of VEHICLES. Else ValueError.

    Every launch file compares the NUMBER, never the text of its argument:
    `vehicle:=00` is vehicle 0 and must be treated as vehicle 0 everywhere.
    """
    try:
        n = int(str(vehicle).strip())
    except (TypeError, ValueError):
        raise ValueError(f'vehicle must be a number, got {vehicle!r}') from None
    if n != 0 and n not in VEHICLES:
        raise ValueError(f'vehicle must be 0 or one of {VEHICLES}, got {n}')
    return n


def domain_problem(vehicle, ros_domain_id):
    """Why this shell must not drive vehicle N, or None if it may.

    ros_domain_id is the shell's ROS_DOMAIN_ID as text ('' when unset). Three
    vehicles share a room; the numbers of vehicle 2 in the domain of vehicle 1
    is a wrong footprint on a moving car, with no error anywhere.
    """
    want = str(DOMAIN_BASE + parse_vehicle(vehicle))
    if (ros_domain_id or '') == want:
        return None
    return (f'vehicle {parse_vehicle(vehicle)} lives in ROS domain {want}, but '
            f"this shell has ROS_DOMAIN_ID='{ros_domain_id or 'unset'}'. In "
            f'EVERY terminal: MITT_VEHICLE={parse_vehicle(vehicle)} '
            f'source ros2_ws/setup_env.sh')


def _cm_up(x):
    """x rounded up to a whole centimetre."""
    return math.ceil(round(x * 100.0, 6)) / 100.0


def footprint(dims):
    """The vehicle's outline as Nav2's footprint string, corners in base_link.

    The smallest rectangle that holds the body box AND the four wheels, as
    the URDF places them: base_link is the rear-axle centre, the box is
    centred half a wheelbase ahead of it, the rear wheels are at x = 0 and
    the front wheels at x = wheelbase, each track/2 out. With the estimates
    the box holds the wheels; a measured body shorter or narrower than the
    wheels would otherwise leave them outside. Every edge is rounded OUTWARD
    to a centimetre. A bumper or a mast that overhangs is not in the
    dimensions file, and so not in here.
    """
    for k in FOOTPRINT_KEYS:
        if not (math.isfinite(dims[k]) and dims[k] > 0):
            raise ValueError(f'{k} must be a positive number, got {dims[k]}')
    wb, length, r = dims['wheelbase'], dims['chassis_length'], dims['wheel_radius']
    front = _cm_up(max(wb / 2.0 + length / 2.0, wb + r))
    rear = -_cm_up(max(length / 2.0 - wb / 2.0, r))
    half = _cm_up(max(dims['chassis_width'] / 2.0,
                      dims['track_width'] / 2.0 + dims['wheel_width'] / 2.0))
    return (f'[[{front:.2f}, {half:.2f}], [{front:.2f}, {-half:.2f}], '
            f'[{rear:.2f}, {-half:.2f}], [{rear:.2f}, {half:.2f}]]')


def planner_radius(turning_radius):
    """The radius Nav2 plans at for a vehicle that turns at turning_radius."""
    if not (math.isfinite(turning_radius) and turning_radius > 0):
        raise ValueError(
            f'{TURNING_RADIUS} must be a positive number, got {turning_radius}')
    return _cm_up(turning_radius * PLANNER_MARGIN)


def overlay_path(desc_share, vehicle):
    return os.path.join(desc_share, 'config', 'vehicles', f'vehicle{vehicle}.yaml')


def _estimates(desc_share):
    import yaml

    with open(os.path.join(desc_share, 'config', 'mitt_dimensions.yaml')) as fh:
        return yaml.safe_load(fh)


def load_overlay(desc_share, vehicle):
    """Return what vehicle N has measured, as a dict. {} for vehicle 0.

    Raises ValueError - and nothing else - for a vehicle number that does not
    exist, a missing or malformed file, a value that is not a number, or a
    key that mitt_dimensions.yaml does not have: a misspelt key would
    otherwise be ignored and the estimate used in silence.
    """
    import yaml

    vehicle = parse_vehicle(vehicle)
    if vehicle == 0:
        return {}
    path = overlay_path(desc_share, vehicle)
    if not os.path.exists(path):
        raise ValueError(f'{path} does not exist')
    base = _estimates(desc_share)
    try:
        with open(path) as fh:
            over = yaml.safe_load(fh) or {}
    except yaml.YAMLError as e:
        raise ValueError(f'{path} is not valid YAML: {e}') from None
    if not isinstance(over, dict):
        raise ValueError(f'{path} must be `key: value` lines, nothing else')
    unknown = sorted(k for k in over if k not in base)
    if unknown:
        raise ValueError(
            f'{path} has key(s) mitt_dimensions.yaml does not: '
            f'{", ".join(unknown)}')
    notnum = sorted(k for k, v in over.items()
                    if isinstance(v, bool) or not isinstance(v, (int, float))
                    or not math.isfinite(v))
    if notnum:
        raise ValueError(f'{path}: not a number: {", ".join(notnum)}')
    return over


def _replace(node, key, value):
    """Set every `key` found anywhere under node. Return how many were set."""
    n = 0
    if isinstance(node, dict):
        for k in node:
            if k == key:
                node[k] = value
                n += 1
            else:
                n += _replace(node[k], key, value)
    return n


def _generated(vehicle, stock, values, what):
    """Write a copy of `stock` with `values` set, and return its path.

    values is {key: (value, how many times the key must be found)}. A key
    found any other number of times means the committed file has changed
    shape, and a copy that silently missed one would be worse than none.
    """
    import yaml

    with open(stock) as fh:
        params = yaml.safe_load(fh)
    for key, (value, times) in values.items():
        found = _replace(params, key, value)
        if found != times:
            raise ValueError(
                f'{stock}: expected `{key}` {times} time(s), found {found}')
    # One fixed name per vehicle and user: a launch replaces the file of the
    # launch before it, so nothing piles up in the temp directory.
    out = os.path.join(
        tempfile.gettempdir(),
        f'mitt_vehicle{parse_vehicle(vehicle)}_{what}_{getpass.getuser()}.yaml')
    with open(out, 'w') as fh:
        fh.write(f'# GENERATED by mitt_description/config/vehicle_config.py from\n'
                 f'# {stock}\n'
                 f'# with the geometry of vehicle {parse_vehicle(vehicle)}. '
                 f'Do not edit.\n')
        yaml.safe_dump(params, fh, default_flow_style=None, sort_keys=False)
    return out


def controllers_for(vehicle, desc_share, ctrl_yaml):
    """Return the controller parameter file to use for this vehicle."""
    over = load_overlay(desc_share, vehicle)
    values = {dst: (float(over[src]), 1) for src, dst in GEOMETRY if src in over}
    if not values:
        return ctrl_yaml
    return _generated(vehicle, ctrl_yaml, values, 'controllers')


def nav2_values(base, over):
    """What vehicle N's overlay changes in nav2_params.yaml: {key: value}.

    Empty when the overlay touches nothing Nav2 depends on. The planner
    radius follows the MEASURED turning radius only - a measured wheelbase
    without it leaves the committed radius alone, because that radius is not
    derived from the wheelbase (mitt_dimensions.yaml says why).
    """
    values = {}
    if any(k in over for k in FOOTPRINT_KEYS):
        values['footprint'] = footprint({**base, **over})
    if TURNING_RADIUS in over:
        values[PLANNER_RADIUS] = planner_radius(float(over[TURNING_RADIUS]))
    return values


def nav2_for(vehicle, desc_share, nav_yaml, real=False):
    """Return the Nav2 parameter file to use for this vehicle.

    real=True is a vehicle on the floor, not its twin. It is refused until
    that vehicle's turning radius has been measured: the committed radius is
    5% above an ESTIMATE, and a planner radius below the real one plans paths
    the car cannot drive.
    """
    over = load_overlay(desc_share, vehicle)
    if real and TURNING_RADIUS not in over:
        raise ValueError(
            f'vehicle {parse_vehicle(vehicle)} has no measured {TURNING_RADIUS} '
            f'in {overlay_path(desc_share, parse_vehicle(vehicle))}. Measure it '
            f'first (docs/design/calibration.md 1.5): Nav2 would otherwise plan '
            f'at a radius derived from an estimate.')
    values = nav2_values(_estimates(desc_share), over)
    if not values:
        return nav_yaml
    # The footprint is stated once per costmap: local and global.
    times = {'footprint': 2, PLANNER_RADIUS: 1}
    return _generated(
        vehicle, nav_yaml, {k: (v, times[k]) for k, v in values.items()}, 'nav2')
