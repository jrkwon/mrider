#!/usr/bin/env bash
#
# check_env.sh - verify a student machine is ready for 자율주행미들웨어응용.
#
# Run this BEFORE the first class. If every line says OK you are ready for Lab 1.
# If something says FAIL, the line tells you exactly what to run to fix it.
#
#     bash scripts/check_env.sh
#
# Exit status is 0 only when there are no failures, so you can paste the tail of
# the output into your Lab 1 submission as evidence.

# NOTE: deliberately no `pipefail`. This script uses `... | grep -q` throughout;
# grep -q exits on the first match, the producer takes SIGPIPE, and under
# pipefail the whole pipeline would report failure on a successful match.
set -u

PASS=0
WARN=0
FAIL=0

# Colour, but only when writing to a terminal - otherwise the log you paste into
# your submission is full of escape codes.
if [ -t 1 ]; then
    G=$'\033[32m'; Y=$'\033[33m'; R=$'\033[31m'; B=$'\033[1m'; N=$'\033[0m'
else
    G=""; Y=""; R=""; B=""; N=""
fi

ok()   { printf "  %sOK  %s %s\n" "$G" "$N" "$1"; PASS=$((PASS+1)); }
warn() { printf "  %sWARN%s %s\n" "$Y" "$N" "$1"; [ $# -gt 1 ] && printf "       %s\n" "$2"; WARN=$((WARN+1)); }
bad()  { printf "  %sFAIL%s %s\n" "$R" "$N" "$1"; [ $# -gt 1 ] && printf "       fix: %s\n" "$2"; FAIL=$((FAIL+1)); }
section() { printf "\n%s%s%s\n" "$B" "$1" "$N"; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

printf "%s\n" "================================================================"
printf "%s\n" " MRider course environment check"
printf "%s\n" " host: $(hostname)   date: $(date -Iseconds)"
printf "%s\n" " repo: ${REPO_ROOT}"
printf "%s\n" "================================================================"

# ---------------------------------------------------------------------------
section "1. Operating system"

if [ -r /etc/os-release ]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    case "${VERSION_ID:-}" in
        22.04) ok "Ubuntu 22.04 (${PRETTY_NAME})" ;;
        24.04) bad "Ubuntu 24.04 - this course uses 22.04" \
                   "24.04 ships ROS 2 Jazzy. The MRider stack is Humble. Install Ubuntu 22.04 LTS." ;;
        *)     bad "Unsupported OS: ${PRETTY_NAME:-unknown}" \
                   "Install Ubuntu 22.04 LTS (Jammy Jellyfish), natively - not WSL, not a VM." ;;
    esac
else
    bad "Cannot read /etc/os-release" "Are you on Linux? This course requires native Ubuntu 22.04."
fi

# WSL and VMs both fail on GPU-accelerated Gazebo in ways that are painful to
# debug mid-lab, so name them explicitly rather than letting the GPU check
# report a confusing symptom later.
if grep -qi microsoft /proc/version 2>/dev/null; then
    bad "Running under WSL" "Gazebo needs a real GPU. Install Ubuntu 22.04 natively (dual-boot is fine)."
fi
if command -v systemd-detect-virt >/dev/null 2>&1; then
    VIRT="$(systemd-detect-virt 2>/dev/null | head -1)"
    VIRT="${VIRT:-none}"
    [ "$VIRT" != "none" ] && warn "Running inside a VM (${VIRT})" \
        "Gazebo may be unusably slow. Native install strongly recommended."
fi

# ---------------------------------------------------------------------------
section "2. Hardware"

CORES="$(nproc 2>/dev/null || echo 0)"
if   [ "$CORES" -ge 8 ]; then ok "CPU cores: ${CORES}"
elif [ "$CORES" -ge 4 ]; then warn "CPU cores: ${CORES} (4-7)" "colcon build will be slow. Use: colcon build --parallel-workers 2"
else                          bad "CPU cores: ${CORES}" "Need at least 4 cores. Talk to the instructor about lab machine access."
fi

MEM_GB="$(awk '/MemTotal/ {printf "%.0f", $2/1024/1024}' /proc/meminfo 2>/dev/null || echo 0)"
if   [ "$MEM_GB" -ge 16 ]; then ok "RAM: ${MEM_GB} GB"
elif [ "$MEM_GB" -ge 8 ];  then warn "RAM: ${MEM_GB} GB (8-15)" "Gazebo + Nav2 + RViz together will be tight. Close your browser during labs."
else                            bad "RAM: ${MEM_GB} GB" "Need 8 GB minimum, 16 GB recommended."
fi

DISK_GB="$(df -BG --output=avail "$HOME" 2>/dev/null | tail -1 | tr -dc '0-9' || echo 0)"
if   [ "${DISK_GB:-0}" -ge 50 ]; then ok "Free disk: ${DISK_GB} GB"
elif [ "${DISK_GB:-0}" -ge 25 ]; then warn "Free disk: ${DISK_GB} GB" "ROS + Gazebo + build artifacts want ~40 GB. Free some space."
else                                  bad "Free disk: ${DISK_GB:-?} GB" "Need at least 25 GB free in ${HOME}."
fi

# ---------------------------------------------------------------------------
section "3. Graphics (Gazebo needs this)"

if command -v glxinfo >/dev/null 2>&1; then
    RENDERER="$(glxinfo -B 2>/dev/null | grep -i 'OpenGL renderer' | cut -d: -f2- | sed 's/^ *//')"
    if [ -z "$RENDERER" ]; then
        bad "No OpenGL renderer reported" "Graphics drivers are not working. Check Software & Updates > Additional Drivers."
    elif echo "$RENDERER" | grep -qiE 'llvmpipe|softpipe|swrast'; then
        bad "Software rendering: ${RENDERER}" \
            "Gazebo will run at ~1 fps. Install a GPU driver: Software & Updates > Additional Drivers."
    else
        ok "OpenGL renderer: ${RENDERER}"
    fi
else
    warn "glxinfo not installed - cannot check the GPU" "sudo apt install -y mesa-utils, then re-run this script"
fi

# ---------------------------------------------------------------------------
section "4. ROS 2 Humble"

if [ -f /opt/ros/humble/setup.bash ]; then
    ok "ROS 2 Humble present at /opt/ros/humble"
    # shellcheck disable=SC1091
    set +u; . /opt/ros/humble/setup.bash; set -u
else
    bad "ROS 2 Humble not found at /opt/ros/humble" \
        "Follow docs/course/environment.md section 3. Do NOT install Jazzy or Iron."
fi

for tool in ros2 colcon rosdep python3 git; do
    if command -v "$tool" >/dev/null 2>&1; then
        ok "$tool found ($(command -v "$tool"))"
    else
        case "$tool" in
            colcon) bad "colcon not found" "sudo apt install -y python3-colcon-common-extensions" ;;
            rosdep) bad "rosdep not found" "sudo apt install -y python3-rosdep && sudo rosdep init && rosdep update" ;;
            ros2)   bad "ros2 not found"   "source /opt/ros/humble/setup.bash (add it to ~/.bashrc)" ;;
            *)      bad "$tool not found"  "sudo apt install -y $tool" ;;
        esac
    fi
done

# ---------------------------------------------------------------------------
section "5. Required ROS packages"

REQUIRED_PKGS=(
    ackermann_steering_controller
    joint_state_broadcaster
    controller_manager
    robot_localization
    slam_toolbox
    nav2_bringup
    nav2_smac_planner
    twist_mux
    teleop_twist_joy
    joy
    ros_gz_sim
    ros_gz_bridge
    xacro
    robot_state_publisher
    rviz2
)
if command -v ros2 >/dev/null 2>&1; then
    # One `ros2 pkg list` call, not one per package - the per-call startup cost
    # dominates and makes this section take ~30 s instead of ~2 s.
    INSTALLED="$(ros2 pkg list 2>/dev/null)"
    MISSING=()
    for p in "${REQUIRED_PKGS[@]}"; do
        if printf '%s\n' "$INSTALLED" | grep -qx "$p"; then
            ok "$p"
        else
            MISSING+=("$p")
            bad "$p missing" "see the apt line in docs/course/environment.md section 4"
        fi
    done
    if [ ${#MISSING[@]} -gt 0 ]; then
        printf "\n  Install all missing packages at once:\n    sudo apt install -y"
        for p in "${MISSING[@]}"; do printf " ros-humble-%s" "${p//_/-}"; done
        printf "\n"
    fi
else
    bad "Skipping package check - ros2 is not on PATH"
fi

# The `ros2 control` verb comes from ros2controlcli, which is NOT a dependency
# of ros-humble-desktop or ros-humble-controller-manager. Easy to miss, and the
# failure ("invalid choice: 'control'") does not name the missing package.
if command -v ros2 >/dev/null 2>&1; then
    if ros2 --help 2>/dev/null | grep -qw control; then
        ok "ros2 control verb available (ros2controlcli)"
    else
        bad "ros2 control verb missing" "sudo apt install -y ros-humble-ros2controlcli"
    fi
fi

# ---------------------------------------------------------------------------
section "6. Gazebo Harmonic"

if command -v gz >/dev/null 2>&1; then
    GZ_VER="$(gz sim --version 2>/dev/null | head -1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)"
    GZ_MAJOR="${GZ_VER%%.*}"
    if [ "${GZ_MAJOR:-0}" = "8" ]; then
        ok "Gazebo Harmonic (gz-sim ${GZ_VER})"
    elif [ -n "${GZ_VER:-}" ]; then
        bad "Gazebo ${GZ_VER} is not Harmonic" \
            "This course needs gz-sim 8.x (Harmonic). See environment.md section 5."
    else
        bad "gz found but version unreadable" "Try: gz sim --version"
    fi
else
    bad "Gazebo not installed" "See docs/course/environment.md section 5."
fi

# The single most common wrong turn: apt offers ros-humble-ros-gz-* built
# against Fortress. Humble + Harmonic needs the ros-gzharmonic variant.
DPKG_PKGS="$(dpkg-query -W -f='${Package}\n' 2>/dev/null)"
if printf '%s' "$DPKG_PKGS" | grep -qx 'ros-humble-ros-gzharmonic'; then
    ok "ros-humble-ros-gzharmonic installed (the Harmonic-paired variant)"
elif printf '%s' "$DPKG_PKGS" | grep -qx 'ros-humble-ros-gz-sim'; then
    bad "ros-humble-ros-gz-sim is the FORTRESS variant" \
        "sudo apt install -y ros-humble-ros-gzharmonic  (see environment.md section 5)"
else
    warn "Could not confirm which ros_gz variant is installed" \
         "dpkg-query -W -f='\${Package}\\n' | grep ros-gz"
fi

# ---------------------------------------------------------------------------
section "7. Workspace"

if [ -d "${REPO_ROOT}/ros2_ws/src" ]; then
    ok "ros2_ws/src present"
else
    bad "ros2_ws/src not found under ${REPO_ROOT}" "git clone the course repository, then run this script from inside it"
fi

if [ -f "${REPO_ROOT}/ros2_ws/setup_env.sh" ]; then
    ok "ros2_ws/setup_env.sh present"
else
    bad "ros2_ws/setup_env.sh missing" "Your clone is incomplete. git pull."
fi

if [ -d "${REPO_ROOT}/ros2_ws/src/gz_ros2_control" ]; then
    ok "gz_ros2_control source present"
else
    bad "gz_ros2_control not cloned" \
        "cd ${REPO_ROOT}/ros2_ws/src && git clone -b humble https://github.com/ros-controls/gz_ros2_control.git"
fi

if [ -f "${REPO_ROOT}/ros2_ws/install/setup.bash" ]; then
    ok "Workspace has been built"
else
    warn "Workspace not built yet" \
        "cd ${REPO_ROOT}/ros2_ws && source setup_env.sh && colcon build --symlink-install"
fi

# ---------------------------------------------------------------------------
section "8. Environment variables"

# These two are set by setup_env.sh and both cause failures that look like
# project bugs rather than environment problems. Report what the shell has
# *now*, before sourcing, because that is what bites students.
case "${RMW_IMPLEMENTATION:-unset}" in
    rmw_fastrtps_cpp)  ok "RMW_IMPLEMENTATION=rmw_fastrtps_cpp" ;;
    rmw_cyclonedds_cpp) warn "RMW_IMPLEMENTATION=rmw_cyclonedds_cpp in this shell" \
        "The twin does not come up under CycloneDDS. setup_env.sh overrides it - always source it." ;;
    unset) ok "RMW_IMPLEMENTATION not set (setup_env.sh will set FastRTPS)" ;;
    *)     warn "RMW_IMPLEMENTATION=${RMW_IMPLEMENTATION}" "Expected rmw_fastrtps_cpp. setup_env.sh will override." ;;
esac

if [ -n "${ROS_DOMAIN_ID:-}" ]; then
    ok "ROS_DOMAIN_ID=${ROS_DOMAIN_ID}"
else
    warn "ROS_DOMAIN_ID not set" \
        "In a shared classroom your nodes will see everyone else's. Set a unique value in ~/.bashrc: export ROS_DOMAIN_ID=<your number>"
fi

# ---------------------------------------------------------------------------
printf "\n%s\n" "================================================================"
printf " %sOK: %d%s   %sWARN: %d%s   %sFAIL: %d%s\n" "$G" "$PASS" "$N" "$Y" "$WARN" "$N" "$R" "$FAIL" "$N"
printf "%s\n" "================================================================"

if [ "$FAIL" -gt 0 ]; then
    printf "\n%sNot ready.%s Fix the FAIL lines above and run this again.\n" "$R" "$N"
    printf "Full instructions: docs/course/environment.md\n"
    printf "Still stuck after 30 minutes? Bring this output to the setup clinic - do not lose a whole evening to it.\n\n"
    exit 1
fi

if [ "$WARN" -gt 0 ]; then
    printf "\n%sReady, with warnings.%s You can start Lab 1. Read the WARN lines - they predict\n" "$Y" "$N"
    printf "what will be slow or surprising later.\n\n"
else
    printf "\n%sReady.%s Paste this output into your Lab 1 submission.\n\n" "$G" "$N"
fi
exit 0
