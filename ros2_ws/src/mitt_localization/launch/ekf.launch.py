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
The EKF, and nothing else. It owns exactly one transform.

    ros2 launch mitt_localization ekf.launch.py

    odom -> base_link    robot_localization EKF   (this file)

WHY THIS IS ITS OWN FILE
------------------------
It used to start inside mitt_navigation/launch/slam.launch.py, which made
odom->base_link conditional on wanting to BUILD A MAP. Those are unrelated:
the EKF fuses wheel odometry and the IMU and is needed whenever the vehicle
moves, mapping or not. Driving a saved map, or driving with no map at all,
meant either re-assembling the launch by hand or starting slam_toolbox for a
transform that has nothing to do with SLAM.

Split on 2026-11-07. slam.launch.py still starts it by default, so every
command already written down keeps working; what changed is that it can now
be started WITHOUT slam_toolbox, and slam_toolbox without it.

THE RULE THIS FILE EXISTS TO PROTECT
------------------------------------
One publisher per transform. ackermann_steering_controller has
`enable_odom_tf: false` precisely so it does not also publish odom->base_link.
Two publishers for one transform is a robot that visibly jitters and is
miserable to diagnose, and the second publisher is usually something somebody
started "just to see".
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    loc_pkg = FindPackageShare("mitt_localization")
    use_sim_time = LaunchConfiguration("use_sim_time")

    return LaunchDescription([
        DeclareLaunchArgument("use_sim_time", default_value="true"),

        Node(
            package="robot_localization",
            executable="ekf_node",
            name="ekf_filter_node",
            output="screen",
            parameters=[
                PathJoinSubstitution([loc_pkg, "config", "ekf_indoor.yaml"]),
                {"use_sim_time": use_sim_time},
            ],
        ),
    ])
