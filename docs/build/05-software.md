# 5. Software Install: ROS 2 Humble Stack

!!! danger "Superseded — pending rewrite (2026-08-07)"

    This page still describes the **Pixhawk 6C + PX4 + Arduino Nano** topology. That was
    replaced by a **single Teensy 4.1 running micro-ROS**
    ([decision D3](../design/adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07)).

    **Do not follow the steps below as written.** Specifically, these no longer exist: PX4,
    QGroundControl, MAVLink, the Micro-XRCE-DDS agent, `px4_msgs`, the Arduino Nano, the
    USB-TTL adapter, the servo-PWM steering setpoint, and the ASCII/I2C feedback protocols.
    New in their place: micro-ROS over USB, `DbwCommand`/`DbwStatus`, Sabertooth **packetized
    serial**, an isolated logic rail, and a **hardware RC signal MUX**.

    The [design set](../design/overview.md) is authoritative and current —
    [dbw.md](../design/dbw.md), [architecture.md](../design/architecture.md),
    [safety.md](../design/safety.md), [software.md](../design/software.md) — as are
    [step 1](01-bom-sourcing.md) and [step 4](04-firmware.md).


**Goal:** stand up the on-board ROS 2 Humble stack on the laptop.

Install ROS 2 Humble and the MRider workspace (reusing `jrkwon/mrover` packages),
bring up Micro-XRCE-DDS to the Pixhawk, and confirm the command/feedback topics
(`/mrider/cmd`, `/mrider/feedback`) and the TF tree are alive.

- **Prerequisites:** Section 4 complete; laptop selected.
- **Specification:** [design/software.md](../design/software.md)
- **Expected outcome:** ROS 2 talks to PX4 over XRCE; feedback streams from the Nano
  over USB serial; TF tree populated.

!!! warning "Draft — not yet validated on hardware"

    The MRider workspace does not exist yet. Package names, launch files, and the two NEW
    nodes (the Nano feedback driver and the command shim) are specified in
    [software.md](../design/software.md) but **not written**. Commands below show the intended
    shape; adjust to the workspace as it actually lands.

---

## 5.1 What is reused and what is new

The guiding rule is **reuse before invent**. B-MROVER already provides the MAVLink bridge,
the EKF, slam_toolbox, Nav2, the ros2_control CarlikeBot interface, the data recorder, and
the Keras end-to-end pipeline. MRider changes exactly two things
([software.md §1](../design/software.md#1-reuse-posture)):

1. **The feedback datapath** moves off MAVLink `WHEEL_DISTANCE` onto Nano → USB →
   `/mrider/feedback` ([ADR-SW1](../design/software.md#adr-sw1-one-transport-one-clock-typed-messages)).
2. **Kinematic and frame parameters** are re-measured for the real chassis, and two B-MROVER
   config artifacts are corrected.

That means exactly **two new nodes**:

| New node | Job |
|---|---|
| **Feedback driver** | Parse Nano USB serial `F,...` frames → publish `/mrider/feedback` |
| **Command shim** (thin) | Map `/mrider/cmd` → `ManualControlSetpoint` (roll/throttle) |

Everything else is reused or reconfigured. If you find yourself writing a third node, check
[the reuse table](../design/software.md#2-ros-2-stack-reused-adapted-new) first — it is
probably already there.

## 5.2 Install ROS 2 Humble

Target is **Ubuntu 22.04 + ROS 2 Humble** — B-MROVER's validated distro. Do not substitute a
newer distro to be helpful; the reuse claims are verified against Humble.

```bash
sudo apt install -y software-properties-common curl
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

sudo apt update
sudo apt install -y ros-humble-desktop ros-dev-tools
sudo apt install -y ros-humble-slam-toolbox ros-humble-navigation2 ros-humble-nav2-bringup \
                    ros-humble-robot-localization ros-humble-ros2-control \
                    ros-humble-ros2-controllers python3-colcon-common-extensions

echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
```

## 5.3 Build the workspace

```bash
mkdir -p ~/mrider_ws/src && cd ~/mrider_ws/src

# B-MROVER packages: bridge, px4_msgs, description, configs, data_collection, run_neural
git clone https://github.com/jrkwon/mrover.git

cd ~/mrider_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

!!! tip "Use `--symlink-install`"

    You will edit YAML configs constantly during steps 6–8. Symlink installs mean a config
    change does not require a rebuild.

## 5.4 Micro-XRCE-DDS agent

The transport between the laptop and PX4. B-MROVER pins **Agent v2.4.2**, TELEM2 =
`/dev/ttyS2`, `SER_TEL2_BAUD` typically **2000000**, with client auto-start via SD
`etc/extras.txt` ([dbw.md §9](../design/dbw.md#9-teensy-41-firmware-platform-and-version-pinning)).

```bash
git clone -b v2.4.2 https://github.com/eProsima/Micro-XRCE-DDS-Agent.git
cd Micro-XRCE-DDS-Agent && mkdir build && cd build
cmake .. && make && sudo make install && sudo ldconfig /usr/local/lib/

# Run against the Pixhawk TELEM2 link
MicroXRCEAgent serial --dev /dev/ttyUSB0 -b 2000000
```

Domain ID comes from `agent_config.xml` (default **10**). Set `ROS_DOMAIN_ID` to match, or
nothing will appear in `ros2 topic list` and you will assume the link is dead:

```bash
export ROS_DOMAIN_ID=10
```

**Verify the link:**

```bash
ros2 topic list | grep /fmu
# expect /fmu/in/manual_control_setpoint, /fmu/out/sensor_combined, ...

ros2 topic hz /fmu/out/sensor_combined     # expect >= 100 Hz (EKF input)
```

## 5.5 Stable device names for the two USB links

You have two USB serial devices — the Nano and the Pixhawk — and `/dev/ttyUSB0` will swap
between them across reboots. Fix this now rather than after it silently sends steering
commands to the wrong device.

```bash
# Find the stable identifiers
ls -l /dev/serial/by-id/
udevadm info -a -n /dev/ttyUSB0 | grep -E 'idVendor|idProduct|serial' | head
```

```title="/etc/udev/rules.d/99-mrider.rules"
SUBSYSTEM=="tty", ATTRS{idVendor}=="1a86", ATTRS{idProduct}=="7523", SYMLINK+="mrider_nano"
SUBSYSTEM=="tty", ATTRS{idVendor}=="XXXX", ATTRS{idProduct}=="XXXX", SYMLINK+="mrider_px4"
```

*(Vendor/product IDs above are placeholders — read yours from `udevadm` and record them.)*

```bash
sudo udevadm control --reload-rules && sudo udevadm trigger
sudo usermod -aG dialout $USER     # log out and back in
ls -l /dev/mrider_nano /dev/mrider_px4
```

## 5.6 The feedback driver

The one genuinely new node. It opens the Nano serial link at **115200**, parses

```
F,<steer_deg>,<steer_counts>,<drive_ticks>,<drive_rpm>,<setpoint_deg>,<status>\n
```

and publishes `/mrider/feedback`. The message descends from B-MROVER's
`mrover_control/msg/Control.msg` — retaining `timestamp` and `steer_angle` (degrees, the
absolute-sensor reading) and adding a drive-distance/velocity field derived from the drive
encoder ([software.md §3.1](../design/software.md#31-topic-interface-contract)).

Three behaviors the driver must implement, because downstream safety depends on them:

1. **Stamp on receipt with the laptop clock.** The Nano has no real-time clock. The laptop is
   the single authoritative clock ([calibration.md §6](../design/calibration.md#6-time-synchronization)).
2. **Flag staleness.** No frame for `T_timeout` (e.g. 250 ms) → mark `/mrider/feedback` stale
   so the EKF coasts on IMU and Nav2 halts
   ([failsafe matrix row 2](../design/safety.md#2-failsafe-matrix)).
3. **Surface the `status` bitfield** — setpoint-valid, at-limit, stall-detected — rather than
   swallowing it. Step 6's failsafe tests read these.

```bash
ros2 run mrider feedback_driver --ros-args -p port:=/dev/mrider_nano -p baud:=115200

ros2 topic hz   /mrider/feedback      # expect >= 20 Hz
ros2 topic echo /mrider/feedback --once
```

!!! note "Steering does not travel this link"

    The USB link carries feedback up and only non-time-critical config down (`C,PID,...`,
    `C,ZERO`). The steering **setpoint** arrives via PX4 servo PWM
    ([ADR E](../design/dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision)).
    This is why USB loss degrades odometry but leaves steering tracking — row 2 of the
    failsafe matrix.

## 5.7 The command shim

Thin by design: maps `/mrider/cmd` (normalized steer + throttle from Nav2, teleop, or the
learned policy) onto `ManualControlSetpoint` with `roll` = STEER and `throttle` = THROTTLE,
published to `/fmu/in/manual_control_setpoint`.

Keeping this shim thin is what makes Nav2, teleop, and behavior cloning share one datapath —
they all publish `/mrider/cmd` and nothing else knows the difference.

```bash
ros2 run mrider command_shim
ros2 topic hz /fmu/in/manual_control_setpoint    # expect >= 10 Hz (heartbeat contract)
```

!!! danger "The ≥10 Hz stream is a heartbeat, not a suggestion"

    PX4's offboard-loss failsafe fires when the stream drops below 10 Hz: throttle → 0, enter
    hold ([failsafe matrix row 1](../design/safety.md#2-failsafe-matrix)). If your shim
    publishes only on change, the vehicle will failsafe every time the command is steady.

## 5.8 Re-parameterize for the real chassis

Fill in the measurements from [step 2](02-mechanical.md). B-MROVER's URDF mixes a simulation
chassis (`chassis_length=1.3`) with a much smaller controller `wheelbase=0.325` — these are
simulation artifacts, **not** measurements. Treat every dimension as a placeholder
([software.md §3.2](../design/software.md#32-ackermann-kinematic-parameters)).

| Parameter | B-MROVER reference | Your value | File |
|---|---|---|---|
| Steering range | ±22.5° | keep as design target; re-verify mechanically | `robot_core2_urdf.xacro:26` |
| Wheelbase | 0.325 m (controller) / 1.3 m (URDF placeholder) | *(from step 2)* | `carlike_controllers.yaml:13` |
| Track | 0.4 m (sim placeholder) | *(from step 2)* | `robot_core2_urdf.xacro:9-10` |
| Wheel radius | 0.1397 m | *(from step 2)* | `robot_core2_urdf.xacro:19` |
| `robot_radius` (Nav2) | 0.1397 | *(derive from real chassis)* | `nav2_params.yaml` |

**Three corrections found during design verification** — make all three now
([software.md §7](../design/software.md#7-software-adr-summary)):

1. **Frame mismatch.** slam_toolbox uses `base_frame: base_footprint`; the EKF uses
   `base_link`. Reconcile to one convention — recommend `base_link` throughout, or add a
   static `base_link` → `base_footprint` transform.
2. **Magnetic declination.** `navsat_transform.magnetic_declination_radians` is set for
   **Lisbon** in B-MROVER. Set your local value. (GNSS is optional; the map-EKF runs
   GNSS-free until a receiver is added.)
3. **Nav2 local controller.** DWB is diff-drive/omni-oriented. Keep it for first bring-up as
   the reused default, but pre-register Regulated Pure Pursuit as the swap
   ([ADR-SW2](../design/software.md#adr-sw2-nav2-local-controller-for-ackermann)) — the
   ±22.5° minimum-turn-radius constraint may make DWB paths infeasible.

## 5.9 EKF and TF

Keep B-MROVER's **dual-EKF** structure — local (`world_frame: odom`) and global
(`world_frame: map`, GNSS) — with `two_d_mode: true` for a planar ride-on
([software.md §4.1](../design/software.md#41-robot_localization-ekf-configekfyaml)).

Retarget `odom0` from `wheel/odometry` to odometry derived from `/mrider/feedback`: an
odometry node applies the bicycle model to steer angle + drive distance. Keep `imu0` sourced
from the Pixhawk (`/fmu/out/sensor_combined` → `imu/data`).

**Verify the TF tree** — `map` → `odom` → `base_link` → sensor frames (REP-105):

```bash
ros2 run tf2_tools view_frames        # writes frames.pdf
ros2 run tf2_ros tf2_echo odom base_link
```

Sensor frames are static from the URDF; their **values** are only meaningful after the
extrinsics calibration in [step 6](06-bench-test.md). At this stage you are confirming the
tree is *connected*, not that it is *accurate*.

!!! danger "Never enable simulated time on the real vehicle"

    Keep `use_sim_time=false`. Everything stamps against the laptop wall clock
    ([calibration.md §6](../design/calibration.md#6-time-synchronization)).

## 5.10 Bring-up smoke test

```bash
# Terminal 1 — XRCE agent
MicroXRCEAgent serial --dev /dev/mrider_px4 -b 2000000

# Terminal 2 — vehicle bring-up (bridge + feedback driver + shim + EKF + description)
ros2 launch mrider bringup.launch.py

# Terminal 3 — verify
ros2 topic hz /fmu/out/sensor_combined          # >= 100 Hz
ros2 topic hz /mrider/feedback                  # >= 20 Hz
ros2 topic hz /fmu/in/manual_control_setpoint   # >= 10 Hz
ros2 topic echo /mrider/feedback --once
ros2 run tf2_tools view_frames
```

**Record sheet — rates observed**

| Link | Contract | Observed | Pass |
|---|---|---|---|
| Setpoint stream (laptop → PX4) | ≥ 10 Hz | *(record)* | ☐ |
| Steering servo loop (Nano-local) | ≥ 100 Hz | *(from step 4)* | ☐ |
| Feedback (Nano → laptop) | ≥ 20 Hz | *(record)* | ☐ |
| PX4 IMU (`sensor_combined`) | ≥ 100 Hz | *(record)* | ☐ |
| RC override (RX → PX4) | ~50 Hz | *(record)* | ☐ |

These are the [architecture.md timing contract](../design/architecture.md#6-timing-heartbeat-contract)
rates. A link that misses its rate does not fail loudly — it degrades, and the failure
surfaces later as bad odometry or spurious failsafes.

## 5.11 Gate to step 6

- [ ] ROS 2 Humble installed; workspace builds clean
- [ ] XRCE agent connected; `/fmu/*` topics present at the right `ROS_DOMAIN_ID`
- [ ] udev rules give stable `/dev/mrider_nano` and `/dev/mrider_px4`
- [ ] Feedback driver publishes `/mrider/feedback` at ≥20 Hz with laptop-clock stamps
- [ ] Staleness flagging and `status` bitfield pass-through implemented
- [ ] Command shim publishes `ManualControlSetpoint` at ≥10 Hz continuously
- [ ] Real chassis dimensions substituted for all B-MROVER placeholders
- [ ] All three config corrections applied (frame, declination, controller decision)
- [ ] Dual-EKF running; `odom0` retargeted to feedback-derived odometry
- [ ] TF tree connected `map` → `odom` → `base_link` → sensors
- [ ] `use_sim_time=false`
- [ ] All five timing-contract rates observed and recorded

---

**Previous:** [4. Firmware bring-up](04-firmware.md) · **Next:** [6. Bench test & calibration](06-bench-test.md)
