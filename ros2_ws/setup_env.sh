# MITT workspace environment. Source this in EVERY terminal used for the twin:
#
#     source ros2_ws/setup_env.sh
#
# and in every terminal used for a REAL vehicle, with its number (section 5):
#
#     MITT_VEHICLE=2 source ros2_ws/setup_env.sh
#
# It exists because several things in this environment need overriding, and each
# fails in a way that looks like a project bug rather than an environment
# problem.

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

# ---------------------------------------------------------------------------
# 4. NETWORK ISOLATION - and it takes TWO variables, not one.
#
# 13 students run this simulator on one classroom network. Each machine must be
# an island: your robot must not receive someone else's commands, and your
# Gazebo must not discover theirs.
#
# 4a. ROS 2 / DDS.
#
# Measured on this machine, same node, only this variable changed:
#
#     ROS_LOCALHOST_ONLY=0 -> binds 0.0.0.0:7400 AND 192.168.0.146:52573
#                                              AND 172.16.77.105:36989
#     ROS_LOCALHOST_ONLY=1 -> binds 127.0.0.1 only
#
# So without it, traffic really does leave the machine. A unique
# ROS_DOMAIN_ID per student would only PARTITION that traffic; this stops it
# being sent. It is also the stronger guarantee operationally, since it cannot
# be defeated by two people picking the same number.
export ROS_LOCALHOST_ONLY=1

# 4b. Gazebo, which does NOT honour the variable above.
#
# gz-transport is a separate stack from DDS with its own discovery, and it
# ignores ROS_LOCALHOST_ONLY completely. Measured with ROS_LOCALHOST_ONLY=1
# already exported, gz-sim still joined its discovery multicast group
# 239.255.0.7 on enx3c18a0b7d966 AND wlo1 - the wired and wireless interfaces.
#
# That matters more than it sounds. Two gz instances that find each other
# interleave /clock and /scan, and the symptom reads as a physics bug, not a
# networking one. On one machine that is already documented as confusing; with
# the second simulator on someone else's desk it would be close to
# undiagnosable.
#
# GZ_IP moves the group to lo alone. Verified: the sim still comes up and
# /clock, /stats and /gazebo/resource_paths remain discoverable locally.
export GZ_IP=127.0.0.1

# NOTE on the loopback interface, because it looks like it should break this.
# `ip link show lo` reports <LOOPBACK,UP,LOWER_UP> - no MULTICAST flag - and
# section 1 above names that as the suspected cause of the CycloneDDS failure.
# It does NOT break localhost-only discovery: Fast DDS falls back to shared
# memory and localhost unicast. Tested talker/listener and the full twin.
# Recorded so the next person does not re-derive it.

# ---------------------------------------------------------------------------
# 5. REAL VEHICLES: one ROS domain per vehicle. Vehicle N -> domain 10 + N.
#
#     MITT_VEHICLE=1  ->  ROS_DOMAIN_ID=11
#     MITT_VEHICLE=2  ->  ROS_DOMAIN_ID=12
#     MITT_VEHICLE=3  ->  ROS_DOMAIN_ID=13
#     (unset)         ->  ROS_DOMAIN_ID left alone: the twin, domain 0
#
# Decided 2026-11-16, docs/design/software.md 3.4. The twin does not need this
# - section 4 already makes each machine an island. A vehicle is different in
# one way that matters: sooner or later somebody switches ROS_LOCALHOST_ONLY
# off to watch RViz from a second laptop, and three vehicles are in the room.
# On one shared domain that is team A's joystick steering team B's car. A
# domain per vehicle means the isolation does not depend on nobody ever
# touching section 4.
#
# The number is not chosen here alone. The Teensy firmware of vehicle N asks
# for the same domain (a micro-ROS client names its own; the agent's shell
# does not set it), and real.launch.py refuses to start in any other. All
# three follow the one rule, 10 + N.
#
# ROS_LOCALHOST_ONLY stays 1 on the vehicle too. Everything that drives the
# car runs on its own laptop, and the Teensy arrives over USB serial.
case "${MITT_VEHICLE:-}" in
  "")    ;;
  1|2|3) export ROS_DOMAIN_ID=$((10 + MITT_VEHICLE)) ;;
  *)     echo "MITT env: MITT_VEHICLE must be 1, 2 or 3 (got '${MITT_VEHICLE}') - ROS_DOMAIN_ID NOT set" >&2 ;;
esac

_here="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
[ -f /opt/ros/humble/setup.bash ] && source /opt/ros/humble/setup.bash
[ -f "${_here}/install/setup.bash" ] && source "${_here}/install/setup.bash"
unset _here

echo "MITT env: RMW=${RMW_IMPLEMENTATION}, GZ_VERSION=${GZ_VERSION}, user-site disabled"
echo "          isolated to loopback (ROS_LOCALHOST_ONLY=${ROS_LOCALHOST_ONLY}, GZ_IP=${GZ_IP})"
# Say what the shell IS, not what was asked for: a domain left over from an
# earlier `MITT_VEHICLE=N source` in this same shell is still in force.
case "${MITT_VEHICLE:-}:${ROS_DOMAIN_ID:-}" in
  1:11|2:12|3:13) echo "          REAL VEHICLE ${MITT_VEHICLE}: ROS_DOMAIN_ID=${ROS_DOMAIN_ID}" ;;
  :)              echo "          twin: ROS_DOMAIN_ID unset (domain 0)" ;;
  :11|:12|:13)    echo "          WARNING: no MITT_VEHICLE, but ROS_DOMAIN_ID=${ROS_DOMAIN_ID} is a VEHICLE's domain," >&2
                  echo "                   left over in this shell. For the twin: unset ROS_DOMAIN_ID" >&2 ;;
  :*)             echo "          twin: ROS_DOMAIN_ID=${ROS_DOMAIN_ID} (set outside this script)" ;;
  *)              echo "          WARNING: MITT_VEHICLE='${MITT_VEHICLE}' and ROS_DOMAIN_ID='${ROS_DOMAIN_ID:-unset}' do not go together" >&2 ;;
esac
