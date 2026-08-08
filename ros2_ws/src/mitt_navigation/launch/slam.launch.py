# Copyright 2026 Jaerock Kwon
# SPDX-License-Identifier: MIT

"""
SLAM (slam_toolbox) + EKF for the MITT twin.

    ros2 launch mitt_navigation slam.launch.py

TF ownership, which is the thing that goes wrong most often:
    map  -> odom        slam_toolbox   (this file)
    odom -> base_link   robot_localization EKF (this file)
    base_link -> *      robot_state_publisher (sim.launch.py, from the URDF)

The ackermann_steering_controller has enable_odom_tf: false precisely so it
does NOT also publish odom->base_link. Two publishers for one transform gives
a robot that visibly jitters and is miserable to diagnose.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    nav_pkg = FindPackageShare("mitt_navigation")
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
