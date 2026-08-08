# 5. Software Install: ROS 2 Humble Stack

**Goal:** stand up the ROS 2 stack on the laptop, connect it to the Teensy over micro-ROS, and
confirm the vehicle interface end to end.

Install ROS 2 Humble and the packages the design set names, settle the Gazebo pairing, build
the micro-ROS agent from source, and verify `DbwCommand`/`DbwStatus` round-trip at rate.

- **Prerequisites:** Section 4 complete (Teensy passes Stage 0–2 gates).
- **Specification:** [design/software.md](../design/software.md)
- **Expected outcome:** `/mitt/dbw/status` at ≥ 50 Hz, `ros2_control` loaded, TF tree complete,
  and the identical launch working in simulation.

!!! warning "Draft — not yet validated on hardware"

    Commands are derived from [software.md](../design/software.md). No MRider has been brought
    up, so package versions and device paths are **unconfirmed**. Record what you actually
    install — under this architecture, your pinned versions *are* the reproducibility claim
    ([software.md §6.3](../design/software.md#63-version-pinning)).

---

## 5.1 What is reused and what is new

The controller change does **not** touch the autonomy stack. Everything that carries MRider's
navigation sits *above* the vehicle interface and is transport-agnostic.

| Reused from B-MROVER | Status |
|---|---|
| `robot_localization` EKF configs, `slam_toolbox`, Nav2 params | ADAPT — re-parameterize for the real chassis (§5.8) |
| URDF/xacro Ackermann structure, Gazebo worlds | ADAPT — same distro, minimal change |
| `data_collection`, `neural_net/` behavior cloning | REUSE — phase 2 |

| New in MRider | Why |
|---|---|
| **`mitt_hardware`** | A real `ros2_control` `hardware_interface` bridging to the micro-ROS topics. B-MROVER's `carlikebot_system.cpp` is an **unmodified upstream demo stub** — `read()` echoes the command back as state, `write()` only logs (finding F3). There was never working code here to reuse. |
| **`mitt_msgs`** | `DbwCommand` / `DbwStatus`, replacing `px4_msgs` |
| **Odometry node** | Bicycle model from `DbwStatus` → `wheel/odometry` |
| **`mitt_bench`** | Produces the quantified acceptance numbers |

**Retired:** `mavlink_bridge.py`, `px4_msgs`, the Micro-XRCE-DDS agent, the ASCII feedback
driver, and the command shim. The vehicle interface is two typed topics on one transport
([ADR-SW1](../design/software.md#adr-sw1-one-transport-one-clock-typed-messages)).

## 5.2 Install ROS 2 Humble and packages

```bash
source /opt/ros/humble/setup.bash

sudo apt install -y \
  ros-humble-ackermann-steering-controller \
  ros-humble-joint-state-broadcaster \
  ros-humble-robot-localization \
  ros-humble-slam-toolbox \
  ros-humble-nav2-bringup \
  ros-humble-rplidar-ros \
  ros-humble-gz-ros2-control \
  ros-humble-ros-gz-sim

# Record exactly what you got — this is the reproducibility claim
apt list --installed 2>/dev/null | grep -E "ros-humble-(ackermann|gz-ros2|ros-gz|robot-local|slam|nav2|rplidar)" \
  | tee ~/mrider_pinned_versions.txt
```

## 5.3 Settle the Gazebo pairing — do this in week 1, not week 12

!!! danger "Humble's paired Gazebo is Fortress; this lab machine has Harmonic"

    `gz sim 8.14.0` (Harmonic) is installed, but Humble's apt `ros_gz` (0.244.x) and
    `gz_ros2_control` (0.7.x) are built against **Fortress**. This is a known mismatch, and
    resolving it is a **week-1 gate with a one-day cap**
    ([software.md §6.2](../design/software.md#62-gazebo-pairing-week-1-gate)).

```bash
gz sim --version                       # what is actually installed
ros2 pkg prefix ros_gz_sim             # what ROS thinks it has
ros2 launch ros_gz_sim gz_sim.launch.py gz_args:="-r empty.sdf"
```

**Decision rule — do not spend more than one day here:**

1. It works against Harmonic → keep it, pin the versions, record them in `docs/build/`.
2. It does not → **install Gazebo Fortress and use the apt binaries.** Fortress is the
   supported Humble pairing and is entirely adequate for a 14-week indoor-navigation project.

**Do not** attempt a source build of `ros_gz` + `gz_ros2_control` against Harmonic on a
semester timeline. The twin is a means, not the deliverable.

## 5.4 Build the micro-ROS agent from source

`micro_ros_agent` is **not in the Humble apt repositories.** Build it now, during Track A —
not in week 5 when it blocks the vehicle.

```bash
mkdir -p ~/uros_ws/src && cd ~/uros_ws
git clone -b humble https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup
rosdep install --from-paths src --ignore-src -y
colcon build && source install/local_setup.bash

ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh && source install/local_setup.bash

ros2 pkg prefix micro_ros_agent        # confirm it exists
```

Record the commit you built.

## 5.5 Build the workspace

```bash
cd ~/mrider/ros2_ws
rosdep install --from-paths src --ignore-src -y
colcon build --symlink-install
source install/setup.bash
```

## 5.6 Stable device names

Under this architecture there is **one** MCU, so the old two-way `/dev/ttyUSB*` ambiguity is
gone — but the LiDAR is also a USB serial device, so pin both.

```bash
udevadm info -a -n /dev/ttyACM0 | grep -E "idVendor|idProduct|serial" | head
```

`/etc/udev/rules.d/99-mrider.rules`:

```
# Teensy 4.1 (VID 16c0) — fill in the serial from the command above
SUBSYSTEM=="tty", ATTRS{idVendor}=="16c0", ATTRS{serial}=="XXXXXXXX", SYMLINK+="mitt_dbw"
# LiDAR — fill in from udevadm
SUBSYSTEM=="tty", ATTRS{idVendor}=="XXXX", ATTRS{idProduct}=="XXXX", SYMLINK+="mitt_lidar"
```

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
ls -l /dev/mitt_dbw /dev/mitt_lidar
```

!!! danger "Give `/dev/mitt_dbw` a direct laptop port, not a hub"

    This link carries the steering **setpoint** as well as feedback. A dropout removes the
    setpoint and drops the vehicle to `ESTOP`
    ([failsafe row 2](../design/safety.md#2-failsafe-matrix)) — safe, but a flaky link is a
    vehicle that stops repeatedly.

## 5.7 `mitt_hardware` — the `ros2_control` interface

The plugin implements `read()` by taking the latest `DbwStatus` and `write()` by publishing a
`DbwCommand`. The controller stack above it is upstream
`ackermann_steering_controller`: front steer = **position**, rear drive = **velocity**.

**The point of this design** is that the *same* controller stack and the *same* Nav2/SLAM
configs run in simulation and on the vehicle. Only the plugin differs:

| Context | `hardware_interface` plugin |
|---|---|
| Simulation | `gz_ros2_control` |
| Vehicle | `mitt_hardware` |

That is [ADR-SW4](../design/software.md#7-software-adr-summary), and it is what makes the twin
a development vehicle rather than a demonstration. If you find yourself adding a
sim-only or vehicle-only node above this line, stop — you are re-introducing the divergence
the design exists to prevent.

## 5.8 Re-parameterize for the real chassis

!!! danger "Treat every B-MROVER dimension as a placeholder"

    B-MROVER's URDF mixes a simulation chassis (`chassis_length=1.3`) with a controller
    `wheelbase=0.325` — these are simulation artifacts, not measurements
    ([software.md §3.2](../design/software.md#32-ackermann-kinematic-parameters)). Measure
    everything on your vehicle. The one value consistent across three independent files is the
    **±22.5° steering range**, adopted as the design target and still to be re-verified against
    the real mechanical lock.

| Parameter | Source | Action |
|---|---|---|
| `wheelbase`, track, `wheel_radius` | Measured in step 2 | Set in URDF + controller config |
| Steering range | Measured mechanical lock | Verify against ±22.5° |
| Drive encoder PPR | **Measured on the part fitted** | Do **not** inherit 52 — the source project conflicts with itself (F7) |
| `robot_radius`, velocity limits | Real chassis | Nav2 params |

## 5.9 EKF and TF

Three corrections carried over from the design verification
([software.md §7](../design/software.md#7-software-adr-summary)):

1. SLAM `base_frame: base_footprint` vs EKF `base_link` — reconcile to one convention.
2. `navsat_transform` magnetic declination is set for **Lisbon** in B-MROVER — set the local
   value.
3. Nav2's DWB controller is diff-drive-oriented; RPP is pre-registered as the Ackermann swap.

EKF inputs: `odom0: wheel/odometry` from the new odometry node, `imu0: /imu/data` from the
**BNO085-class IMU driver** — a driver swap only, since the estimator was always
`robot_localization` (finding F11).

## 5.10 Bring-up smoke test

```bash
# Terminal 1 — micro-ROS agent
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/mitt_dbw -b 115200

# Terminal 2 — vehicle bring-up
ros2 launch mitt_bringup real.launch.py

# Terminal 3 — verify
ros2 topic hz /mitt/dbw/status          # target >= 50 Hz
ros2 topic echo /mitt/dbw/status --once # mode, faults, measured angle
ros2 control list_controllers           # ackermann + joint_state_broadcaster: active
ros2 run tf2_tools view_frames          # map -> odom -> base_link -> sensors
```

Then run the **identical** stack in simulation and confirm only the plugin differs:

```bash
ros2 launch mitt_bringup sim.launch.py
```

| Link | Target | Measured | ☐ |
|---|---|---|---|
| Command stream (laptop → Teensy) | ≥ 50 Hz | *(record)* | ☐ |
| Steering position loop (Teensy) | ≥ 200 Hz | *(from step 4)* | ☐ |
| Actuation frame (Teensy → MUX → Sabertooth) | **measure & pin** | *(from step 4)* | ☐ |
| Status feedback (Teensy → laptop) | ≥ 50 Hz | *(record)* | ☐ |
| IMU | ≥ 100 Hz | *(record)* | ☐ |
| RC override (SBUS) | ~50 Hz | *(record)* | ☐ |

## 5.11 Gate to step 6

- [ ] All apt packages installed and versions recorded
- [ ] **Gazebo pairing settled** (§5.3) and the choice written down
- [ ] `micro_ros_agent` built from source; commit recorded
- [ ] Workspace builds clean; `colcon test` passes
- [ ] udev gives stable `/dev/mitt_dbw` and `/dev/mitt_lidar`; Teensy on a direct port
- [ ] `/mitt/dbw/status` ≥ 50 Hz with **zero session dropouts over 30 min**
- [ ] `ros2_control` controllers active; TF tree complete with no warnings
- [ ] **The same launch runs in sim and on hardware, differing only in the plugin**
- [ ] Chassis dimensions and encoder PPR are *measured* values, not inherited ones
- [ ] Full toolchain pinned in `docs/build/`

---

**Previous:** [4. Firmware bring-up](04-firmware.md) · **Next:** [6. Bench test](06-bench-test.md)
