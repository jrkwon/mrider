# MITT workspace environment. Source this in EVERY terminal used for the twin:
#
#     source ros2_ws/setup_env.sh
#
# It exists because two things in this environment need overriding, and both
# fail in ways that look like project bugs rather than environment problems.

# ---------------------------------------------------------------------------
# 1. RMW: FastRTPS, not CycloneDDS.
#
# ~/.bashrc sets RMW_IMPLEMENTATION=rmw_cyclonedds_cpp. CycloneDDS is
# installed and working for ordinary topics and services, but the twin does
# not come up under it: the controller_manager lives inside the Gazebo
# process (gz_ros2_control plugin), and the spawner's calls to
# /controller_manager/list_controllers never receive a RESPONSE -
#
#     Failed getting a result from calling /controller_manager/list_controllers
#     in 10.0. (Attempt 1 of 3.)
#
# The service is discovered; the reply does not arrive. The model spawns and
# the sensor bridge runs fine, so this is narrowly a service-response problem,
# not general discovery failure.
#
# Suspected contributing factor, NOT yet confirmed: the loopback interface
# reports LOOPBACK but not MULTICAST (`ip link show lo`), and CycloneDDS
# discovers via multicast by default. A unicast/loopback CYCLONEDDS_URI
# config was drafted but not conclusively tested - see the open item in
# docs/design/software.md.
#
# Everything is verified working under FastRTPS: both controllers activate,
# odometry runs at ~100 Hz, and slam_toolbox maps the depot world.
#
# NOTE this must be consistent across ALL terminals in a session. Setting it
# only for the launch would leave your `ros2 topic list` on CycloneDDS,
# unable to see any of the sim's topics - a worse failure, because it looks
# like the sim is dead when it is running fine.
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

# ---------------------------------------------------------------------------
# 2. Ignore ~/.local site-packages during builds.
#
# ~/.local has setuptools 82.0.1, which expects packaging >= 22, but only the
# system packaging 21.3 is installed. rosidl's Python egg step then dies with:
#
#     TypeError: canonicalize_version() got an unexpected keyword argument
#     'strip_trailing_zero'
#
# Deliberately NOT fixed with `pip install --user -U packaging`: that would
# shadow the system packaging for all Python run by this user, including ROS
# tooling that expects 21.3. Scoping the build away from ~/.local is the
# smaller blast radius.
export PYTHONNOUSERSITE=1

# ---------------------------------------------------------------------------
# 3. Gazebo Harmonic, for building gz_ros2_control from source.
#
# No Harmonic build of gz_ros2_control exists in apt for Humble; only 0.7.20,
# which targets Fortress. ros_gz itself is fine - the machine has
# ros-humble-ros-gzharmonic. See docs/design/software.md 6.2.
export GZ_VERSION=harmonic

_here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
[ -f /opt/ros/humble/setup.bash ] && source /opt/ros/humble/setup.bash
[ -f "${_here}/install/setup.bash" ] && source "${_here}/install/setup.bash"
unset _here

echo "MITT env: RMW=${RMW_IMPLEMENTATION}, GZ_VERSION=${GZ_VERSION}, user-site disabled"
