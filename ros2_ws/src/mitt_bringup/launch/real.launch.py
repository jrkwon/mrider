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
Bring up a real MITT vehicle: micro-ROS agent + robot + controllers + sensors.

    MITT_VEHICLE=2 source ros2_ws/setup_env.sh
    ros2 launch mitt_bringup real.launch.py vehicle:=2

This is Track B, and it is sim.launch.py with Gazebo taken out. The table is
the whole design (ADR-SW4, docs/design/software.md 7):

    sim.launch.py                        real.launch.py
    -----------------------------------  -----------------------------------
    xacro sim:=true                      xacro sim:=false
    controller_manager inside Gazebo     ros2_control_node + mitt_hardware
    ros_gz_bridge  -> /scan              rplidar_ros      -> /scan
                   -> /camera/image_raw  usb_cam          -> /camera/image_raw
                   -> /imu/data          the Teensy, through the agent
    twist_mux, both spawners             the same, from the same files
    use_sim_time true                    use_sim_time false

Everything above the hardware plugin is the SAME file in both columns:
mitt_controllers.yaml, twist_mux.yaml, the URDF. If a node ever has to be
added to one column only, above that line, that is the divergence the twin
exists to prevent.

WRITTEN 2026-11-16 AND NEVER RUN ON A VEHICLE
---------------------------------------------
On that date mitt_hardware did not exist and neither did the vehicle firmware,
so this file has been parsed and its refusals exercised, and nothing more. It
is here so that the day the plugin loads there is exactly one launch to debug,
and so the build pages stop naming a launch file nobody had written.

IT REFUSES TO START RATHER THAN START HALF A VEHICLE
----------------------------------------------------
Before any node runs it checks, and stops with the reason:

  1. `vehicle:=` is 1, 2 or 3, and ROS_DOMAIN_ID in THIS shell is 10 + vehicle.
     Three vehicles share a room. The firmware of vehicle N asks for domain
     10 + N; a laptop in any other domain sees an empty graph and no error,
     and a laptop in a NEIGHBOUR's domain with localhost-only switched off
     drives the neighbour's car. See docs/design/software.md 3.4.
  2. mitt_hardware is installed. Without it ros2_control_node dies with a
     pluginlib error forty lines up the log.
  3. The device nodes exist. A missing /dev/mitt_dbw otherwise shows up as
     an agent that waits forever in silence.

THERE IS NO IMU DRIVER HERE, BECAUSE THE IMU IS NOT THE LAPTOP'S
---------------------------------------------------------------
The BNO085 is wired to the Teensy's second I2C bus and the firmware publishes
sensor_msgs/Imu on /imu/data in frame imu_link (decided 2026-11-16,
docs/design/sensors.md 3). It arrives through the micro-ROS agent with
/mitt/dbw/status, on the same link and the same clock. So no node below
mentions it - and a silent /imu/data is a firmware or wiring fault, not a
missing launch argument.
"""

import os

from ament_index_python.packages import (
    PackageNotFoundError,
    get_package_prefix,
)
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    LogInfo,
    OpaqueFunction,
    RegisterEventHandler,
    Shutdown,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue
from launch_ros.substitutions import FindPackageShare

# Vehicle N lives in ROS domain DOMAIN_BASE + N. Decided 2026-11-16,
# docs/design/software.md 3.4. The firmware and ros2_ws/setup_env.sh use the
# same rule; check 25 in scripts/check_docs.sh keeps the copies in step.
DOMAIN_BASE = 10
VEHICLES = (1, 2, 3)


def _only_if_it_worked(what, why, then):
    """Chain `then` after a step, but ONLY if that step succeeded.

    Same helper as sim.launch.py, for the same reason: OnProcessExit fires on
    any exit, and a spawner fired at a controller_manager that never came up
    buries the first error under a second one.
    """
    def handler(event, _context):
        rc = event.returncode
        if rc == 0:
            return then
        return [
            LogInfo(msg=f"\n[bringup] {what} FAILED (exit {rc}).\n"
                        f"[bringup] {why}\n"
                        f"[bringup] Not starting what comes next - it would "
                        f"fail for a reason that is not the reason.\n"),
            Shutdown(reason=f"{what} failed with exit code {rc}"),
        ]
    return handler


def _refuse(problems):
    lines = "\n".join(f"[bringup]   - {p}" for p in problems)
    return [
        LogInfo(msg="\n[bringup] NOT STARTING THE VEHICLE.\n" + lines + "\n"),
        Shutdown(reason="real.launch.py preflight failed"),
    ]


def _lidar_executable():
    """rplidar_ros ships its node under two names depending on the release
    (`rplidar_node`, `rplidar_composition`). Ask the install which it has
    rather than pin a name that is right on one laptop and not the next."""
    libdir = os.path.join(get_package_prefix("rplidar_ros"), "lib", "rplidar_ros")
    for name in ("rplidar_node", "rplidar_composition"):
        if os.path.isfile(os.path.join(libdir, name)):
            return name
    return None


def _bringup(context, *_args, **_kwargs):
    def arg(name):
        return LaunchConfiguration(name).perform(context)

    def on(name):
        return arg(name).lower() in ("true", "1", "yes")

    problems = []

    # -- 1. Which vehicle, and is this shell in its domain? -------------------
    vehicle = arg("vehicle")
    if vehicle not in [str(v) for v in VEHICLES]:
        problems.append(
            "vehicle:= must be 1, 2 or 3 - the number on the vehicle you are "
            f"plugged into (got '{vehicle}'). There is no default on purpose.")
    else:
        want = str(DOMAIN_BASE + int(vehicle))
        have = os.environ.get("ROS_DOMAIN_ID", "")
        if have != want:
            problems.append(
                f"vehicle {vehicle} lives in ROS domain {want}, but this shell "
                f"has ROS_DOMAIN_ID='{have or 'unset'}'. In EVERY terminal: "
                f"MITT_VEHICLE={vehicle} source ros2_ws/setup_env.sh")

    # -- 2. Is the software this launch needs actually installed? -------------
    needed = [("mitt_hardware",
               "the ros2_control plugin for the real vehicle. It is Track W's "
               "deliverable (docs/course/teams.md) and did not exist on "
               "2026-11-16")]
    if on("agent"):
        needed.append(("micro_ros_agent",
                       "built from source, docs/build/05-software.md 5.4. Or "
                       "run it yourself and pass agent:=false"))
    if on("lidar"):
        needed.append(("rplidar_ros", "sudo apt install ros-humble-rplidar-ros"))
    if on("camera"):
        needed.append(("usb_cam", "sudo apt install ros-humble-usb-cam"))
    missing = set()
    for pkg, hint in needed:
        try:
            get_package_prefix(pkg)
        except PackageNotFoundError:
            missing.add(pkg)
            problems.append(f"package '{pkg}' is not installed - {hint}")

    lidar_exe = None
    if on("lidar") and "rplidar_ros" not in missing:
        lidar_exe = _lidar_executable()
        if lidar_exe is None:
            problems.append("rplidar_ros is installed but has neither "
                            "rplidar_node nor rplidar_composition")

    # -- 3. Are the devices there? --------------------------------------------
    devices = []
    if on("agent"):
        devices.append((arg("dbw_port"), "the Teensy. udev rule: 05-software 5.6"))
    if on("lidar"):
        devices.append((arg("lidar_port"), "the LiDAR. udev rule: 05-software 5.6"))
    if on("camera"):
        devices.append((arg("camera_device"), "the camera. `v4l2-ctl --list-devices`"))
    for dev, hint in devices:
        if not os.path.exists(dev):
            problems.append(f"{dev} does not exist - {hint}")

    if problems:
        return _refuse(problems)

    # ------------------------------------------------------------------------
    desc_pkg = FindPackageShare("mitt_description")
    ctrl_pkg = FindPackageShare("mitt_control")
    actions = []

    # -- Robot description: the ONE argument that differs from the twin ------
    robot_description = ParameterValue(
        Command([
            "xacro ",
            PathJoinSubstitution([desc_pkg, "urdf", "mitt.urdf.xacro"]),
            " sim:=false",
        ]),
        value_type=str,
    )

    actions.append(Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[{"robot_description": robot_description,
                     "use_sim_time": False}],
    ))

    # -- micro-ROS agent ------------------------------------------------------
    # The Teensy's node joins the graph through this process. It is started
    # here, not in a second terminal, because a vehicle bring-up without it is
    # a controller_manager whose hardware never answers. The DOMAIN is not set
    # here: the firmware names its own.
    if on("agent"):
        actions.append(Node(
            package="micro_ros_agent",
            executable="micro_ros_agent",
            name="micro_ros_agent",
            arguments=["serial", "--dev", arg("dbw_port"), "-b", arg("dbw_baud")],
            output="screen",
        ))

    # -- ros2_control: a controller_manager of our own -----------------------
    # In the twin this lives inside Gazebo. Here it is a process, loading
    # mitt_hardware/MittSystem from the URDF and THE SAME mitt_controllers.yaml.
    actions.append(Node(
        package="controller_manager",
        executable="ros2_control_node",
        parameters=[
            {"robot_description": robot_description, "use_sim_time": False},
            PathJoinSubstitution([ctrl_pkg, "config", "mitt_controllers.yaml"]),
        ],
        output="screen",
    ))

    # -- Command arbitration: same include as the twin, wall clock -----------
    actions.append(IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            PathJoinSubstitution([ctrl_pkg, "launch", "twist_mux.launch.py"])
        ]),
        launch_arguments={"use_sim_time": "false"}.items(),
    ))

    # -- Sensors: what ros_gz_bridge stands in for ---------------------------
    # Topic and frame names are the twin's, not the driver's defaults. A bag
    # recorded on the vehicle and one recorded in the twin must be playable
    # into the same stack.
    if on("lidar"):
        actions.append(Node(
            package="rplidar_ros",
            executable=lidar_exe,
            name="rplidar",
            parameters=[{
                "serial_port": arg("lidar_port"),
                "serial_baudrate": 115200,      # RPLIDAR A1M8
                "frame_id": "laser_link",
                "angle_compensate": True,
            }],
            output="screen",
        ))

    if on("camera"):
        camera_params = {
            "video_device": arg("camera_device"),
            # mjpeg2rgb, not the YUYV default: this camera does 10 fps at
            # 720p in YUYV and 30 in MJPG (docs/order-log.md, line 17).
            "pixel_format": "mjpeg2rgb",
            "image_width": 1280,
            "image_height": 720,
            "framerate": 30.0,
            "camera_name": "camera_front",
            "frame_id": "camera_optical_link",
        }
        # No intrinsics are shipped: each camera is calibrated on its own
        # vehicle (06-bench-test 6.7). Without a file usb_cam publishes an
        # empty camera_info and says so; that is the honest state.
        if arg("camera_info_url"):
            camera_params["camera_info_url"] = arg("camera_info_url")
        actions.append(Node(
            package="usb_cam",
            executable="usb_cam_node_exe",
            name="camera_front",
            parameters=[camera_params],
            remappings=[
                ("image_raw", "/camera/image_raw"),
                ("camera_info", "/camera/camera_info"),
            ],
            output="screen",
        ))

    # -- Controllers ----------------------------------------------------------
    # No wall-clock delay here, unlike the twin: that delay waits for Gazebo
    # to finish loading a world, and there is no world. What the spawner waits
    # for instead is the hardware plugin activating, which needs the Teensy.
    jsb_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "joint_state_broadcaster",
            "--controller-manager", "/controller_manager",
            "--controller-manager-timeout", "30",
        ],
        output="screen",
    )
    ackermann_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=[
            "ackermann_steering_controller",
            "--controller-manager", "/controller_manager",
            "--controller-manager-timeout", "30",
        ],
        output="screen",
    )
    actions += [
        jsb_spawner,
        RegisterEventHandler(
            OnProcessExit(
                target_action=jsb_spawner,
                on_exit=_only_if_it_worked(
                    "spawning joint_state_broadcaster",
                    "controller_manager did not come up. Scroll UP: the first "
                    "error is usually mitt_hardware failing to activate, which "
                    "means no DbwStatus - is the Teensy powered, is the agent "
                    "connected, is the firmware in this vehicle's domain?",
                    [ackermann_spawner],
                ),
            )
        ),
    ]
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument(
            "vehicle", default_value="",
            description="REQUIRED. 1, 2 or 3 - the number on the vehicle. "
                        "Selects ROS domain 10 + vehicle."),
        DeclareLaunchArgument(
            "agent", default_value="true",
            description="Start the micro-ROS agent. false if you run it in "
                        "its own terminal to watch its log."),
        DeclareLaunchArgument("dbw_port", default_value="/dev/mitt_dbw"),
        DeclareLaunchArgument("dbw_baud", default_value="115200"),
        DeclareLaunchArgument("lidar", default_value="true"),
        DeclareLaunchArgument("lidar_port", default_value="/dev/mitt_lidar"),
        DeclareLaunchArgument("camera", default_value="true"),
        DeclareLaunchArgument("camera_device", default_value="/dev/video0"),
        DeclareLaunchArgument(
            "camera_info_url", default_value="",
            description="file:///abs/path/camera_front.yaml from the "
                        "calibration in 06-bench-test 6.7. Empty = "
                        "uncalibrated."),
        OpaqueFunction(function=_bringup),
    ])
