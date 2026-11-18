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
Nav2 for the MITT twin, or for one of the three vehicles.

    ros2 launch mitt_navigation nav2.launch.py                 # the estimates
    ros2 launch mitt_navigation nav2.launch.py vehicle:=2      # twin of vehicle 2
    ros2 launch mitt_navigation nav2.launch.py vehicle:=2 use_sim_time:=false

Run AFTER slam.launch.py - Nav2 needs map->odom to exist.

vehicle:= is the same argument sim.launch.py and real.launch.py take, and
means the same thing. Two values in config/nav2_params.yaml are a vehicle's
own: the costmap footprint and the planner's minimum turning radius. With
vehicle:=N they come from mitt_description/config/vehicles/vehicle<N>.yaml -
the footprint from that vehicle's body and wheels, the radius 5% above its measured
turning radius - through a generated copy of the parameter file
(mitt_description/config/vehicle_config.py). A vehicle that has measured
none of those values runs on the committed file, which is the estimates.

On a real vehicle (use_sim_time:=false) this file refuses to start unless
all three hold, for the reason real.launch.py has no default - the estimates
are nobody's vehicle, and a planner radius below the real one plans paths
the car cannot drive:

  1. vehicle:= is 1, 2 or 3;
  2. ROS_DOMAIN_ID in this shell is 10 + vehicle, as real.launch.py requires;
  3. that vehicle's overlay has a measured min_turning_radius
     (docs/design/calibration.md 1.5).

Added 2026-11-18. Checked that day with a test overlay: the generated file
differed from the committed one in the two footprints and the planner radius
and nowhere else, planner_server and both costmaps reported the generated
values, and each of the three refusals above fired. Nav2 has not planned a
path with it, in the twin or on a vehicle.

twist_mux arbitrates Nav2 against joystick input on **/cmd_vel**, with the
joystick winning (mitt_control/config/twist_mux.yaml).

NOT cmd_vel_nav, which this docstring claimed until 2026-11-07. Inside
nav2_bringup, cmd_vel_nav is controller_server's output and the INPUT to
velocity_smoother, whose output is /cmd_vel. Subscribing a stage earlier
would work and would silently discard the acceleration limiting - which
matters more on a steered vehicle than a differential one. The reasoning
lives in twist_mux.yaml, beside the parameter it justifies; this file states
the contract and points there.
"""

import os
import sys

from ament_index_python.packages import get_package_share_directory

# One module for every launch file that needs a vehicle's numbers; it lives
# beside the files it reads (see its docstring).
sys.path.insert(0, os.path.join(
    get_package_share_directory("mitt_description"), "config"))
import vehicle_config  # noqa: E402

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    Shutdown,
)
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def _nav2_for_vehicle(context):
    """Start Nav2 on the parameter file of vehicle:=N, or refuse to start.

    The include is built here, not in generate_launch_description, so that a
    refused vehicle starts no Nav2 node at all.
    """
    vehicle = LaunchConfiguration("vehicle").perform(context)
    sim_time = LaunchConfiguration("use_sim_time").perform(context)
    stock = os.path.join(get_package_share_directory("mitt_navigation"),
                         "config", "nav2_params.yaml")
    real = sim_time.strip().lower() in ("false", "0")
    try:
        number = vehicle_config.parse_vehicle(vehicle)
        if real and number == 0:
            raise ValueError(
                "use_sim_time:=false is a real vehicle, and vehicle:=0 is the "
                "estimates. Add vehicle:=1, 2 or 3 - the number on the vehicle.")
        if real:
            wrong_domain = vehicle_config.domain_problem(
                number, os.environ.get("ROS_DOMAIN_ID", ""))
            if wrong_domain:
                raise ValueError(wrong_domain)
        params = vehicle_config.nav2_for(
            number, get_package_share_directory("mitt_description"), stock,
            real=real)
    except (ValueError, OSError) as e:
        return [LogInfo(msg=f"\nnav2.launch.py will not start: {e}\n"),
                Shutdown(reason="vehicle configuration refused")]

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(
            get_package_share_directory("nav2_bringup"),
            "launch", "navigation_launch.py")),
        launch_arguments={
            "use_sim_time": sim_time,
            "params_file": params,
            "use_composition": "False",
        }.items(),
    )
    return [LogInfo(msg=f"vehicle {number}: Nav2 parameters from {params}"),
            nav2]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument(
            "vehicle", default_value="0",
            description="0 = the estimates. 1|2|3 = that vehicle: its footprint "
                        "and turning radius (mitt_description/config/vehicles/"
                        "vehicle<N>.yaml) in place of the estimates. Required "
                        "with use_sim_time:=false."),
        OpaqueFunction(function=_nav2_for_vehicle),
    ])
