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
One vehicle's numbers, for the two launch files that need them.

NOT a launch file - it has no generate_launch_description. It sits in launch/
because sim.launch.py and real.launch.py both import it and that directory is
the one they are installed into together.

Three teams build three vehicles, and no two measure the same wheelbase. The
estimates every vehicle starts from are mitt_description/config/
mitt_dimensions.yaml; what team N has measured is config/vehicles/
vehicle<N>.yaml, laid over it. The URDF takes the merged values through
`xacro vehicle:=N`. This module covers the other consumer.

mitt_controllers.yaml carries its own copy of the geometry (the Ackermann
controller needs wheelbase, track and wheel radius, and reads no other file).
scripts/check_vehicle_dims.py keeps that copy equal to the estimates. For a
vehicle whose measured values differ, controllers_for() writes a copy of the
controller file with those five numbers replaced and returns its path; the
committed file is never edited. With vehicle 0, or an overlay that touches
none of the five, it returns the committed file itself.

Written 2026-11-17. Exercised in the twin with a test overlay; no vehicle has
measured values yet, so no real overlay has been through it.
"""

import getpass
import os
import tempfile

VEHICLES = (1, 2, 3)

# (key in mitt_dimensions.yaml, key in mitt_controllers.yaml).
# scripts/check_vehicle_dims.py reads this list rather than keeping its own.
GEOMETRY = (
    ('wheelbase', 'wheelbase'),
    ('track_width', 'front_wheel_track'),
    ('track_width', 'rear_wheel_track'),
    ('wheel_radius', 'front_wheels_radius'),
    ('wheel_radius', 'rear_wheels_radius'),
)


def overlay_path(desc_share, vehicle):
    return os.path.join(desc_share, 'config', 'vehicles', f'vehicle{vehicle}.yaml')


def load_overlay(desc_share, vehicle):
    """Return what vehicle N has measured, as a dict. {} for vehicle 0.

    Raises ValueError - and nothing else - for a vehicle number that does not
    exist, a missing or malformed file, a value that is not a number, or a
    key that mitt_dimensions.yaml does not have: a misspelt key would
    otherwise be ignored and the estimate used in silence.
    """
    import yaml

    try:
        vehicle = int(vehicle)
    except (TypeError, ValueError):
        raise ValueError(f'vehicle must be a number, got {vehicle!r}') from None
    if vehicle == 0:
        return {}
    if vehicle not in VEHICLES:
        raise ValueError(f'vehicle must be 0 or one of {VEHICLES}, got {vehicle}')
    path = overlay_path(desc_share, vehicle)
    if not os.path.exists(path):
        raise ValueError(f'{path} does not exist')
    with open(os.path.join(desc_share, 'config', 'mitt_dimensions.yaml')) as fh:
        base = yaml.safe_load(fh)
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
                    if isinstance(v, bool) or not isinstance(v, (int, float)))
    if notnum:
        raise ValueError(f'{path}: not a number: {", ".join(notnum)}')
    return over


def _replace(node, values):
    """Set every `key` found anywhere under node. Return how many were set."""
    n = 0
    if isinstance(node, dict):
        for k in node:
            if k in values:
                node[k] = values[k]
                n += 1
            else:
                n += _replace(node[k], values)
    return n


def controllers_for(vehicle, desc_share, ctrl_yaml):
    """Return the controller parameter file to use for this vehicle."""
    import yaml

    over = load_overlay(desc_share, vehicle)
    values = {dst: float(over[src]) for src, dst in GEOMETRY if src in over}
    if not values:
        return ctrl_yaml
    with open(ctrl_yaml) as fh:
        params = yaml.safe_load(fh)
    if _replace(params, values) != len(values):
        raise ValueError(
            f'{ctrl_yaml} is missing one of: {", ".join(sorted(values))}')
    # One fixed name per vehicle and user: a launch replaces the file of the
    # launch before it, so nothing piles up in the temp directory.
    out = os.path.join(
        tempfile.gettempdir(),
        f'mitt_vehicle{int(vehicle)}_controllers_{getpass.getuser()}.yaml')
    with open(out, 'w') as fh:
        fh.write(f'# GENERATED by mitt_bringup/launch/vehicle_config.py from\n'
                 f'# {ctrl_yaml}\n'
                 f'# with the geometry of vehicle {int(vehicle)}. Do not edit.\n')
        yaml.safe_dump(params, fh, default_flow_style=None, sort_keys=False)
    return out
