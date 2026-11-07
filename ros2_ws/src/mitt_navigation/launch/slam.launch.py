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
SLAM (slam_toolbox) for the MITT twin, and the EKF it needs underneath.

    ros2 launch mitt_navigation slam.launch.py
    ros2 launch mitt_navigation slam.launch.py ekf:=false   # EKF already up

TF ownership, which is the thing that goes wrong most often:
    map  -> odom          slam_toolbox            (this file)
    odom -> base_link     robot_localization EKF  (mitt_localization)
    base_link -> *        robot_state_publisher   (sim.launch.py, from the URDF)

WHAT CHANGED ON 2026-11-07, AND WHY IT IS NOT JUST TIDYING
-----------------------------------------------------------
The EKF node used to be declared HERE, which tied odom->base_link to wanting
to build a map. They are unrelated. The EKF fuses wheel odometry and the IMU
and is needed whenever the vehicle moves; running on a saved map, or with no
map at all, meant either re-assembling this launch by hand or starting
slam_toolbox purely to get a transform that has nothing to do with SLAM.

It now lives in mitt_localization/launch/ekf.launch.py and is INCLUDED here,
on by default. Every command already written down still works unchanged. What
is new is that the two can be run apart - see localization.launch.py for the
saved-map case, which is the one this arrangement previously made awkward.

`ekf:=false` exists for the case where something else already started it.
Starting a second ekf_node gives two publishers for odom->base_link, which is
a robot that visibly jitters and is miserable to diagnose - the same failure
`enable_odom_tf: false` on the steering controller is there to prevent.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
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

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),
        DeclareLaunchArgument(
            "ekf", default_value="true",
            description="Start the EKF. Set false only if one is already "
                        "running - two publishers for odom->base_link jitter."),

        ekf,

        Node(
            package="slam_toolbox",
            executable="async_slam_toolbox_node",
            name="slam_toolbox",
            output="screen",
            parameters=[
                PathJoinSubstitution([nav_pkg, "config", "slam_toolbox.yaml"]),
                {"use_sim_time": use_sim_time},
            ],
        ),
    ])
