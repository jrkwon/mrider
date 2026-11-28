# Copyright 2026 MRider team 3
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
Functional tests: what the twin and Nav2 load is what was measured.

Not a linter. Each test produces the file a launch file hands to ROS for
vehicle N - the URDF from `xacro vehicle:=N`, the controller parameters and
the Nav2 parameters from config/vehicle_config.py - and checks the numbers in
it against config/mitt_dimensions.yaml with vehicles/vehicle<N>.yaml laid
over it. No simulator is started.

Run with `colcon test --packages-select mitt_description --ctest-args -R
'^functional_'` (CMakeLists.txt registers it as functional_vehicle_geometry).
"""

import importlib.util
import math
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

import pytest
import yaml

PKG = Path(__file__).resolve().parents[1]          # mitt_description (source)
SRC = PKG.parent                                   # ros2_ws/src
CTRL_YAML = SRC / 'mitt_control' / 'config' / 'mitt_controllers.yaml'
NAV_YAML = SRC / 'mitt_navigation' / 'config' / 'nav2_params.yaml'
VEHICLES = (0, 1, 2, 3)

# Team 3's vehicle, and the values Merge 2 says the twin must carry measured
# (docs/course/weeks/w11.md "The number Chassis owes everyone", w12.md Merge 2).
TEAM_VEHICLE = 3
MERGE2_KEYS = ('wheelbase', 'track_width', 'wheel_radius', 'min_turning_radius')

TOL = 1e-9


def _vehicle_config():
    spec = importlib.util.spec_from_file_location(
        'vehicle_config', PKG / 'config' / 'vehicle_config.py')
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


VC = _vehicle_config()


def dims(vehicle):
    """Return the estimates with vehicle N's measured values laid over them."""
    with open(PKG / 'config' / 'mitt_dimensions.yaml') as fh:
        base = yaml.safe_load(fh)
    return {**base, **VC.load_overlay(str(PKG), vehicle)}


def urdf(vehicle):
    """Expand the URDF exactly as sim.launch.py does, and parse it."""
    out = subprocess.run(
        ['xacro', str(PKG / 'urdf' / 'mitt.urdf.xacro'), 'sim:=true',
         f'vehicle:={vehicle}', 'controllers:=/dev/null'],
        check=True, capture_output=True, text=True).stdout
    return ET.fromstring(out)


def _origin(root, joint):
    j = root.find(f"joint[@name='{joint}']")
    return [float(v) for v in j.find('origin').get('xyz').split()]


def _cylinder(root, link):
    c = root.find(f"link[@name='{link}']/collision/geometry/cylinder")
    return float(c.get('radius')), float(c.get('length'))


@pytest.mark.parametrize('vehicle', VEHICLES)
def test_urdf_carries_the_vehicle_geometry(vehicle):
    """The twin's wheels, steering limits and body are vehicle N's numbers."""
    d, root = dims(vehicle), urdf(vehicle)
    fl = _origin(root, 'front_left_steer_joint')
    fr = _origin(root, 'front_right_steer_joint')
    rl = _origin(root, 'rear_left_wheel_joint')
    rr = _origin(root, 'rear_right_wheel_joint')
    assert fl[0] - rl[0] == pytest.approx(d['wheelbase'], abs=TOL)
    assert fl[1] - fr[1] == pytest.approx(d['track_width'], abs=TOL)
    assert rl[1] - rr[1] == pytest.approx(d['track_width'], abs=TOL)
    for link in ('rear_left_wheel_link', 'front_right_wheel_link'):
        radius, width = _cylinder(root, link)
        assert radius == pytest.approx(d['wheel_radius'], abs=TOL)
        assert width == pytest.approx(d['wheel_width'], abs=TOL)
    for joint in ('front_left_steer_joint', 'front_right_steer_joint'):
        lim = root.find(f"joint[@name='{joint}']/limit")
        assert float(lim.get('upper')) == pytest.approx(
            math.radians(d['steer_limit_deg']), abs=TOL)
        assert float(lim.get('lower')) == pytest.approx(
            -math.radians(d['steer_limit_deg']), abs=TOL)
        assert float(lim.get('velocity')) == pytest.approx(d['max_steer_rate'], abs=TOL)
    box = root.find("link[@name='chassis_link']/collision/geometry/box")
    size = [float(v) for v in box.get('size').split()]
    assert size == pytest.approx(
        [d['chassis_length'], d['chassis_width'], d['chassis_height']], abs=TOL)


@pytest.mark.parametrize('vehicle', VEHICLES)
def test_controller_gets_the_vehicle_geometry(vehicle):
    """ackermann_steering_controller is given vehicle N's wheelbase, track, radius."""
    d = dims(vehicle)
    with open(VC.controllers_for(vehicle, str(PKG), str(CTRL_YAML))) as fh:
        p = yaml.safe_load(fh)['ackermann_steering_controller']['ros__parameters']
    for src, dst in VC.GEOMETRY:
        assert p[dst] == pytest.approx(d[src], abs=TOL), dst


@pytest.mark.parametrize('vehicle', (1, 2, 3))
def test_nav2_plans_above_the_measured_radius(vehicle):
    """Nav2's planner radius is 5% above the measured one, never below it."""
    d = dims(vehicle)
    if 'min_turning_radius' not in VC.load_overlay(str(PKG), vehicle):
        pytest.skip(f'vehicle {vehicle} has no measured min_turning_radius')
    with open(VC.nav2_for(vehicle, str(PKG), str(NAV_YAML), real=True)) as fh:
        text = fh.read()
    planner = yaml.safe_load(text)['planner_server']['ros__parameters']['GridBased']
    radius = planner['minimum_turning_radius']
    assert radius >= d['min_turning_radius']
    assert radius == pytest.approx(VC.planner_radius(d['min_turning_radius']), abs=TOL)


@pytest.mark.parametrize('vehicle', VEHICLES)
def test_nav2_footprint_holds_the_body_and_inflation_reaches_its_corner(vehicle):
    """Both costmaps get vehicle N's outline; inflation reaches its farthest corner."""
    d = dims(vehicle)
    with open(VC.nav2_for(vehicle, str(PKG), str(NAV_YAML))) as fh:
        p = yaml.safe_load(fh)
    front, rear, half = VC._outline(d)
    corner = math.hypot(max(front, -rear), half)
    for cm in ('local_costmap', 'global_costmap'):
        params = p[cm][cm]['ros__parameters']
        pts = yaml.safe_load(params['footprint'])
        xs, ys = [q[0] for q in pts], [q[1] for q in pts]
        # holds the body box (centred between the axles) and all four wheels
        assert max(xs) >= max(d['wheelbase'] / 2 + d['chassis_length'] / 2,
                              d['wheelbase'] + d['wheel_radius']) - TOL
        assert min(xs) <= -max(d['chassis_length'] / 2 - d['wheelbase'] / 2,
                               d['wheel_radius']) + TOL
        assert max(ys) >= max(d['chassis_width'] / 2,
                              d['track_width'] / 2 + d['wheel_width'] / 2) - TOL
        assert params['inflation_layer']['inflation_radius'] >= corner - TOL


def test_team_vehicle_has_what_merge2_needs_measured():
    """vehicle3.yaml carries every value Merge 2 says must be measured."""
    over = VC.load_overlay(str(PKG), TEAM_VEHICLE)
    missing = [k for k in MERGE2_KEYS if k not in over]
    assert not missing, f'vehicle{TEAM_VEHICLE}.yaml lacks measured {missing}'
