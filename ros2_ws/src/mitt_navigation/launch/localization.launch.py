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
Drive a map you already have: AMCL instead of SLAM, plus the same EKF.

    ros2 launch mitt_navigation localization.launch.py map:=/abs/path/to/map.yaml

Then nav2.launch.py, exactly as after slam.launch.py.

    map  -> odom          AMCL                    (this file)
    odom -> base_link     robot_localization EKF  (mitt_localization)
    base_link -> *        robot_state_publisher   (sim.launch.py, from the URDF)

WHY THIS FILE DID NOT EXIST BEFORE
----------------------------------
Because it could not be written cleanly. The EKF was declared inside
slam.launch.py, so the only way to get odom->base_link was to start
slam_toolbox - and running SLAM while also running AMCL gives TWO publishers
for map->odom, which is the jitter failure one level up. Splitting the EKF out
on 2026-11-07 is what made this a six-line include instead of a copied node.

That is the test of whether a refactor was worth doing: something that was
awkward becomes ordinary.

WHAT YOU STILL HAVE TO DO BY HAND
---------------------------------
`set_initial_pose: false` in nav2_params.yaml, so AMCL does not assume where
the vehicle is. Give it a 2D Pose Estimate in RViz before asking Nav2 for a
goal. A particle cloud that never converges is almost always this.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    nav_pkg = FindPackageShare("mitt_navigation")
    use_sim_time = LaunchConfiguration("use_sim_time")

    ekf = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("mitt_localization"),
                "launch", "ekf.launch.py",
            ])
        ]),
        launch_arguments={"use_sim_time": use_sim_time}.items(),
        condition=IfCondition(LaunchConfiguration("ekf")),
    )

    amcl = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("nav2_bringup"),
                "launch", "localization_launch.py",
            ])
        ]),
        launch_arguments={
            "use_sim_time": use_sim_time,
            "map": LaunchConfiguration("map"),
            "params_file": PathJoinSubstitution([
                nav_pkg, "config", "nav2_params.yaml",
            ]),
            "use_composition": "False",
        }.items(),
    )

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument(
            "map",
            description="Absolute path to the map .yaml saved by "
                        "`ros2 run nav2_map_server map_saver_cli -f <name>`."),
        DeclareLaunchArgument(
            "ekf", default_value="true",
            description="Start the EKF. Set false only if one is already "
                        "running - two publishers for odom->base_link jitter."),
        ekf,
        amcl,
    ])
