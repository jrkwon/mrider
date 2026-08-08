# Copyright 2026 Jaerock Kwon
# SPDX-License-Identifier: MIT

"""
Joystick teleop for the MITT twin.

    ros2 launch mitt_control teleop.launch.py

Publishes Twist on cmd_vel_joy, which twist_mux forwards to the
ackermann_steering_controller reference topic.

The deadman button is deliberate and matches the real vehicle's philosophy:
nothing moves unless a human is actively holding it. On hardware the
equivalent guarantee is electrical, not software (docs/design/safety.md 1.2).
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    ctrl_pkg = FindPackageShare("mitt_control")

    return LaunchDescription([
        DeclareLaunchArgument("joy_dev", default_value="0"),

        Node(
            package="joy",
            executable="joy_node",
            name="joy_node",
            parameters=[{
                "device_id": LaunchConfiguration("joy_dev"),
                "deadzone": 0.05,
                "autorepeat_rate": 20.0,
                "use_sim_time": True,
            }],
            output="screen",
        ),

        Node(
            package="teleop_twist_joy",
            executable="teleop_node",
            name="teleop_twist_joy_node",
            parameters=[{
                "use_sim_time": True,
                # Deadman on button 4 (LB on an Xbox-style pad). Nothing moves
                # without it held.
                "require_enable_button": True,
                "enable_button": 4,
                "enable_turbo_button": 5,
                "axis_linear.x": 1,
                "scale_linear.x": 0.5,        # well under the 1.4 m/s cap
                "scale_linear_turbo.x": 1.0,
                "axis_angular.yaw": 3,
                "scale_angular.yaw": 0.8,
            }],
            remappings=[("/cmd_vel", "/cmd_vel_joy")],
            output="screen",
        ),

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
