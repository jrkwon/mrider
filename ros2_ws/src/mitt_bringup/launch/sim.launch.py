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
Bring up the MITT digital twin: Gazebo + robot + controllers + bridge.

    ros2 launch mitt_bringup sim.launch.py

This is Track A of the semester roadmap (docs/design/software.md 8) - the
software development vehicle. It deliberately cannot test what Track B tests:
backlash, encoder noise, USB latency, motor stall.

The controller stack launched here is the SAME one that will drive the real
vehicle. Only the ros2_control hardware plugin differs (ADR-SW4).
"""

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
    TimerAction,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    desc_pkg = FindPackageShare("mitt_description")
    sim_pkg = FindPackageShare("mitt_sim")

    world = LaunchConfiguration("world")
    x = LaunchConfiguration("x")
    y = LaunchConfiguration("y")
    yaw = LaunchConfiguration("yaw")

    args = [
        DeclareLaunchArgument("world", default_value="depot.sdf"),
        DeclareLaunchArgument(
            "gz_args", default_value="-r",
            description="Extra gz sim args. Add -s for headless.",
        ),
        # Spawn pose. Tune once the depot layout is explored.
        DeclareLaunchArgument("x", default_value="0.0"),
        DeclareLaunchArgument("y", default_value="0.0"),
        DeclareLaunchArgument("yaw", default_value="0.0"),
    ]

    world_path = PathJoinSubstitution([sim_pkg, "worlds", world])

    # -- Robot description ---------------------------------------------------
    robot_description = ParameterValue(
        Command([
            "xacro ",
            PathJoinSubstitution([desc_pkg, "urdf", "mitt.urdf.xacro"]),
            " sim:=true",
        ]),
        value_type=str,
    )

    robot_state_publisher = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description, "use_sim_time": True}],
    )

    # -- Gazebo --------------------------------------------------------------
    gz_sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([
                FindPackageShare("ros_gz_sim"), "launch", "gz_sim.launch.py",
            ])
        ]),
        launch_arguments={
            "gz_args": [LaunchConfiguration("gz_args"), " ", world_path],
        }.items(),
    )

    # -- Spawn the robot from the /robot_description topic -------------------
    spawn = Node(
        package="ros_gz_sim",
        executable="create",
        output="screen",
        arguments=[
            "-topic", "robot_description",
            "-name", "mitt",
            "-x", x, "-y", y, "-z", "0.15", "-Y", yaw,
        ],
    )

    # -- Sensor / clock bridge ----------------------------------------------
    # Sensors and clock only. Actuation goes through gz_ros2_control, not here.
    bridge = Node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        output="screen",
        parameters=[{
            "config_file": PathJoinSubstitution([sim_pkg, "config", "gz_bridge.yaml"]),
            "use_sim_time": True,
        }],
    )

    # -- Controllers ---------------------------------------------------------
    # controller_manager lives inside Gazebo (gz_ros2_control plugin), so these
    # are spawners against it. Chained on spawn completion because the manager
    # does not exist until the model is in the world.
    # --controller-manager-timeout matters here. The manager comes up inside
    # Gazebo, which is still loading a ~100 MB world when the first spawner
    # fires, so its service calls can exceed the 10 s default and the spawner
    # dies with a bare "Failed to activate". That looks like a controller
    # misconfiguration and is not one.
    jsb_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager", "/controller_manager",
            "--controller-manager-timeout", "60",
        ],
        output="screen",
    )

    ackermann_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "ackermann_steering_controller",
            "--controller-manager", "/controller_manager",
            "--controller-manager-timeout", "60",
        ],
        output="screen",
    )

    return LaunchDescription(args + [
        robot_state_publisher,
        gz_sim,
        bridge,
        spawn,
        # The delay is load-bearing, not defensive padding.
        #
        # controller_manager executes a controller switch inside its update
        # loop and gives up after a hard-coded 5 s. While Gazebo is still
        # loading the ~100 MB depot world that loop is not ticking, so an
        # immediate spawn fails with "Switch controller timed out" - which
        # surfaces at the spawner as a bare "Failed to activate" and reads
        # like a controller misconfiguration. It is not one.
        #
        # --controller-manager-timeout does NOT cover this; that flag only
        # governs waiting for the service to appear, and the service appears
        # long before the loop runs. Hence a wall-clock delay.
        #
        # 15 s is sized for software rendering (llvmpipe), which is what you
        # get headless on a machine with no GPU passthrough. With a real GPU
        # the world loads faster and this is simply slack.
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn,
                on_exit=[TimerAction(period=15.0, actions=[jsb_spawner])],
            )
        ),
        RegisterEventHandler(
            OnProcessExit(target_action=jsb_spawner, on_exit=[ackermann_spawner])
        ),
    ])
