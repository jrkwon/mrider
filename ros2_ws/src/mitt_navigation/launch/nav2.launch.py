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
Nav2 for the MITT twin.

    ros2 launch mitt_navigation nav2.launch.py

Run AFTER slam.launch.py - Nav2 needs map->odom to exist.

Nav2's output is remapped to cmd_vel_nav so twist_mux arbitrates it against
joystick input, with the joystick winning (mitt_control/config/twist_mux.yaml).
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    nav_pkg = FindPackageShare("mitt_navigation")
    use_sim_time = LaunchConfiguration("use_sim_time")

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("nav2_bringup"),
                "launch", "navigation_launch.py",
            ])
        ]),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "params_file": PathJoinSubstitution([
                nav_pkg, "config", "nav2_params.yaml",
            ]),
            "use_composition": "False",
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        nav2,
    ])
