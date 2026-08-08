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
Command arbitration for the MITT twin.

    ros2 launch mitt_control twist_mux.launch.py

Included by mitt_bringup/sim.launch.py, so it is always running.

WHY IT LIVES HERE AND NOT IN teleop.launch.py. twist_mux is the ONLY path
from any software command source to the ackermann_steering_controller: it
owns the remap onto reference_unstamped. It originally sat inside
teleop.launch.py, which meant an autonomy-only session - sim + slam + nav2,
no joystick - had no mux, and therefore nothing subscribed to Nav2's output
at all. Nav2 accepted goals, planned, and published commands into a topic
with zero subscribers while the vehicle sat still. Nothing errored.

Arbitration remains the same: joystick outranks navigation.
"""

from launch import LaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ctrl_pkg = FindPackageShare("mitt_control")

    return LaunchDescription([
        Node(
            package="twist_mux",
            executable="twist_mux",
            name="twist_mux",
            parameters=[
                PathJoinSubstitution([ctrl_pkg, "config", "twist_mux.yaml"]),
            ],
            remappings=[
                ("/cmd_vel_out",
                 "/ackermann_steering_controller/reference_unstamped"),
            ],
            output="screen",
        ),
    ])
