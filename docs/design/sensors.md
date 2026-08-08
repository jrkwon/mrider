# Sensors & Onboard Compute

> Part of the MRider design set. Siblings: [architecture.md](architecture.md) ·
> [vehicle.md](vehicle.md) · [dbw.md](dbw.md) · [safety.md](safety.md) ·
> [software.md](software.md) · [calibration.md](calibration.md) · [bom.md](bom.md) ·
> [overview.md](overview.md)
>
> Prices are **estimates as of July 2026** and vary by retailer and stock.

This document specifies the MRider perception and localization sensor set and the
onboard computer. Per [overview.md](overview.md), the **minimum sensor package is
one front camera and one 2D LiDAR**; the IMU is a standalone BNO085-class module
(§3); GNSS is optional for the indoor target and required for phase-2 outdoor
waypoint following (§4). Each major choice is an ADR. Frame definitions,
intrinsics/extrinsics, and time-sync are handled in [calibration.md](calibration.md);
how these topics flow through ROS 2 is in [software.md](software.md).

Design goals: reuse the mrover/OSCAR sensor lineage where proven, keep the
minimum tier cheap and teachable, and record an honest reason for every upgrade
in the full tier ([bom.md](bom.md)).

---

## 1. Front Camera

The front camera feeds both classical perception and the **end-to-end behavior
cloning** pipeline reused from mrover's `neural_net/` (Keras). Behavior cloning
learns steering from raw forward images, which makes **shutter type** a
first-class concern.

### Rolling shutter vs global shutter — why it matters here

A rolling-shutter sensor exposes the frame row-by-row, so during motion (and
especially vibration on a ride-on chassis) straight edges skew and the image the
network sees is geometrically inconsistent with the steering label. A global
shutter exposes all rows simultaneously, eliminating that skew. For a
behavior-cloning dataset collected while driving and vibrating, global shutter
removes a systematic label-noise source.

### ADR (camera) — Intel RealSense D435i vs global-shutter USB camera

**Status:** Accepted with tiering.

**Context.** We need a forward camera usable for (a) behavior-cloning image
capture and (b) optional depth for obstacle context. The mrover/OSCAR pipeline
trains on RGB frames.

**Decision.** **Semester 1: a $30 rolling-shutter USB camera.** **Phase 2 (behavior cloning):
a color global-shutter USB3 camera** (e.g., **Arducam AR0234**, 2.3 MP, global shutter, up to
80 fps, ~$160–180). RealSense D435i remains the option if depth is wanted later.

!!! info "Re-tiered 2026-08-07 — deferred, not deleted"

    Behavior cloning is **phase 2**
    ([software.md §8](software.md#8-semester-1-scope-and-software-acceptance-gates)), and the
    global-shutter argument below is *entirely* about training-label quality. Semester 1
    delivers teleop and LiDAR SLAM, neither of which cares about rolling-shutter skew, so the
    $150 premium buys nothing this term.

    **The reasoning below still stands and still applies at phase 2.** Do not train a
    behavior-cloning policy on rolling-shutter data and attribute the result to the platform —
    budget the +$150 when the pipeline comes back ([bom.md](bom.md#phase-2-growth-path)).

**Key finding (verified July 2026):** the RealSense D435i uses a **global-shutter
stereo depth pair but a *rolling-shutter* RGB sensor** (1920×1080). So if the
behavior-cloning network trains on the D435i **RGB** stream, it inherits rolling
shutter anyway. To get global-shutter *imagery* for cloning, either (i) train on
a D435i **infrared/depth-aligned** global-shutter stream, or (ii) use a dedicated
global-shutter color USB camera. This is the reason the **minimum tier picks the
dedicated global-shutter color camera** rather than "just the RealSense."

**Alternatives.**
- **Global-shutter color USB3 (Arducam AR0234)** — global-shutter RGB (correct for
  cloning), cheap, plain UVC (works in ROS 2 via `usb_cam`/`v4l2_camera`), no
  depth, no IMU. *Chosen for minimum tier.*
- **RealSense D435i** — adds stereo depth + Bosch BMI055 IMU + global-shutter
  depth; RGB is rolling shutter; heavier USB/CPU load; needs `realsense-ros`.
  *Chosen for full tier* (depth for obstacle context; IMU as a cross-check to the
  Pixhawk).
- **Raspberry-Pi/CSI rolling-shutter webcam** — cheapest, but rolling shutter on
  the cloning stream; rejected as the primary forward camera.

**Rationale.** The cloning label quality depends on global-shutter *imagery*; the
cheapest way to get that is a dedicated global-shutter color camera, which also
keeps the minimum tier simple (UVC, no SDK). Depth is a genuine capability jump,
so it earns its place only in the full tier via the D435i.

**Consequences.** Minimum tier has **no depth** — obstacle sensing is
LiDAR-only (§2), acceptable at ≤ walking speed. Full tier adds a second IMU
(D435i) that [calibration.md](calibration.md)/[software.md](software.md) treat as
a cross-check, with the **Pixhawk IMU remaining the EKF primary** (§3). If a
future build wants both cheap global-shutter RGB *and* depth, run the AR0234 for
cloning alongside the D435i for depth.

**Mounting summary:** forward-facing, on the mast (§4), **~0.55 m** height (see the §5
mast-height note — reduced from 1.0–1.2 m by the vehicle-class reversal), slight
downward pitch (~10–15°) so the road ~2–8 m ahead fills the frame (matches the
OSCAR/behavior-cloning framing). Fix intrinsics/extrinsics in
[calibration.md](calibration.md).

---

## 2. 2D LiDAR

The 2D LiDAR is the primary obstacle sensor and the scan source for
`slam_toolbox` + Nav2 (reused from mrover — see [software.md](software.md)). The
mrover checkout ships a **YDLidar** config (`dev_ws/src/mrover/config/ydlidar_params.yaml`),
with the model commented as **G4** (and an X4 variant), 10 Hz, single-channel
serial at 230400 baud — so YDLidar is the heritage part.

### 2.1 Comparison table

| Spec | **YDLidar G4** (heritage) | **RPLidar S2** | **RPLidar S3** | **Hokuyo UST-10LX** |
|------|---------------------------|----------------|----------------|---------------------|
| Ranging principle | Triangulation | ToF | ToF | ToF |
| Max range | ~16 m (12 m @ low reflect.) | ~30 m | ~40 m (15 m @ 10%) | ~10 m (30 m max) |
| FOV | 360° | 360° | 360° | **270°** |
| Scan rate | 5–12 Hz (cfg 10 Hz) | 10 Hz (up to 20) | 10 Hz (up to 20) | 40 Hz |
| Sample rate | ~9 kHz | 32 kHz | 32 kHz | ~40.5 kHz-equiv |
| Angular res. | ~0.28°–0.5° | 0.12° | 0.1125° | 0.25° |
| Interface | USB-serial (230400) | USB-serial / UART | USB-serial / UART | **Ethernet** |
| Ingress | None rated | IP65 | IP65 | IP65 |
| Eye safety | Class 1 | Class 1 | Class 1 | Class 1 |
| Est. price (Jul 2026) | **~$250–320** | ~$320–370 | ~$450–500 | ~$1,600–1,900 |
| ROS 2 driver | `ydlidar_ros2_driver` (in mrover) | `sllidar_ros2` | `sllidar_ros2` | `urg_node2` |

Notes: ranges/rates are vendor-typical at ~70% reflectance and drop on dark/low-
reflectivity surfaces; treat as estimates. The Hokuyo is 270° (not 360°) but is
the industrial-grade accuracy/rate reference.

### 2.2 ADR (LiDAR) — recommendation for min and full tiers

**Status:** Accepted with tiering.

**Context.** Need a 2D scan for SLAM/Nav2 obstacle avoidance at ≤ walking speed,
outdoors and indoors, on a vibrating ride-on. Reuse of the mrover
`ydlidar_ros2_driver` config is a plus.

**Decision.**
- **Minimum tier — YDLidar G4.** Cheapest, and the **driver + params already
  exist in the mrover checkout** (near-zero integration cost). Its ~16 m
  triangulation range and 10 Hz are adequate for walking-speed navigation.
- **Full tier — RPLidar S3.** ToF (more robust in sunlight and on low-
  reflectivity surfaces than triangulation), ~40 m range, 0.1125° resolution,
  IP65 for outdoor use — a clean accuracy/robustness upgrade at ~$460 without
  the Hokuyo's Ethernet/PoE integration cost and ~$1,700 price.

**Alternatives.**
- **RPLidar S2** — a middle option (ToF, 30 m, IP65, ~$350); pick over G4 if
  triangulation glare outdoors is a problem but S3's range isn't needed.
- **Hokuyo UST-10LX** — best rate (40 Hz) and industrial accuracy, but **~5–7×
  the S3 price**, only 270° FOV, and Ethernet (adds `urg_node2` + a network
  interface). Rejected for both tiers as overkill for an education platform;
  named as the "if budget were no object / research-grade" reference.

**Rationale.** Minimum tier leans entirely on **existing mrover integration**
(G4) to keep cost and setup effort lowest. The full-tier jump buys the two things
triangulation LiDAR is weakest at — **outdoor sunlight robustness and low-
reflectivity range** — via ToF (S3), which matters once MRider drives outdoors
for mapping. The Hokuyo's advantages (rate, accuracy) don't change behavior at
walking speed enough to justify its cost.

**Consequences.** Minimum tier reuses the mrover YDLidar launch/params verbatim.
Full tier swaps to `sllidar_ros2` (S3) — a driver change tracked in
[software.md](software.md), and a frame-id/params change in
[calibration.md](calibration.md). Both mount at the same mast position (§4) so
extrinsics are tier-independent.

---

## 3. IMU

**Decision:** a **standalone BNO085-class 9-DoF IMU** with onboard sensor fusion,
connected directly to the laptop and publishing `sensor_msgs/Imu` on `/imu/data`.

!!! info "Revised 2026-08-07 — this ADR was reversed by D3"

    This previously specified "use the Pixhawk 6C's internal IMUs — no separate standalone
    IMU," on the rationale that PX4's EKF2 was being reused. [D3](adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07)
    removed the Pixhawk, so a standalone IMU is now required.

    **The reuse argument was weaker than it read even before D3.** Finding F11 verified that
    MRider's estimator was always `robot_localization` on the laptop
    ([software.md §4.1](software.md#41-robot_localization-ekf-configekfyaml)), with PX4
    supplying **raw `SensorCombined` only** — EKF2's output was not what the stack consumed.
    So this is a **driver swap, not an estimator change**, and the "PX4 gives you the EKF"
    leg of the original topology argument did not hold.

Wheel/steering odometry from [`DbwStatus`](dbw.md#101-primary-transport-micro-ros-typed-messages)
fuses with this IMU in `robot_localization`'s EKF to bound the paralleled-motor /
single-encoder odometry error noted in [ADR C](dbw.md#8-adr-c-drive-distance-encoding).

**Rationale.** Onboard fusion (BNO085 class) provides a stable quaternion and calibrated
rates without project code, at ~$28. It connects straight to the laptop, so it sits in the
**laptop's clock domain** — which is simpler than the previous arrangement, where PX4 boot-time
microseconds had to be offset-estimated against the laptop clock
([calibration.md §6](calibration.md)).

**Consequence.** Mounting orientation and vibration isolation are now MRider's responsibility
rather than inherited from a flight-controller design — see §5. Calibration moves from
QGroundControl to a documented in-repo procedure ([calibration.md §5](calibration.md)).

---

## 4. GNSS (optional) & RTK Growth Path

Per [overview.md](overview.md), **GNSS is optional** and therefore **excluded
from the minimum tier**, included in the **full tier**.

**Amended:** optional for the semester-1 **indoor** target; **required** for the phase-2
**outdoor waypoint-following** target, where dead reckoning from wheel odometry + IMU alone
drifts out of a lane-width corridor within tens of meters.

- **Phase 2 — a USB/UART GNSS receiver** connected directly to the laptop, feeding
  `navsat_transform` and the global EKF. Without PX4 in the system there is no GPS port to
  use and no MAVLink injection path; the receiver is just another laptop peripheral.
- **RTK (recommended for lane-level accuracy):** a **u-blox ZED-F9P-class rover** (~$220–300)
  plus an **NTRIP correction source** or a local base station. The laptop runs the NTRIP
  client and feeds corrections to the receiver directly — **simpler than the MAVLink RTK
  injection path** the Pixhawk design would have used, since there is no autopilot in the
  middle. Documented as a phase-2 growth item; **not** in the semester-1 totals
  ([bom.md](bom.md#phase-2-growth-path)).

**ADR note.** GNSS is a tiering decision rather than a technology contest: the
question is only *present (full) vs absent (min)*, and the RTK path is a labeled
future upgrade. No standalone ADR block is warranted; the LiDAR and camera ADRs
carry the sensor-selection weight.

---

## 5. Mounting / Mast Concept

!!! danger "Mast height reduced to ~0.65 m — 2026-08-08"

    This section was written for a **24 V two-seater**. [ADR D was reversed](vehicle.md#adr-d-r-reversal-to-the-12-v-single-seater-2026-08-08)
    and MRider now uses a **12 V single-seater**: 98 × 56 × 47 cm, 10 kg.

    **A 1.0–1.2 m mast does not belong on a 47 cm tall, 56 cm wide, 10 kg chassis.** With
    ~6 kg of equipment already riding high on the plate, a mast that tall puts the combined
    centre of mass well above the roofline on a track of only ~46 cm. That is a tip-over
    risk in exactly the manoeuvre the vehicle performs most — a full-lock turn.

    **Mast total height is now ~0.65 m**, giving roughly 0.55 m for the camera and LiDAR
    above the plate. Every height figure below should be read against that.

    **Consequence, stated rather than buried:** the camera sits lower and pitches down ~12°,
    so it frames the floor closer in. That changes the input distribution for phase-2
    behavior cloning — a policy trained on 1.2 m framing would not transfer. Not a problem
    today (behavior cloning is phase 2), but it must not be rediscovered later.

    The [digital twin](software.md#8-semester-1-scope-and-software-acceptance-gates) models
    the equipment plate as a real 6 kg link so this margin is testable in simulation before
    anything is bolted to the real car.


The sensors share a single **mast** on the deck/bed ([vehicle.md](vehicle.md) C5)
so their extrinsics are fixed once ([calibration.md](calibration.md)).

- **Front camera:** top of mast or a forward boom, **~0.55 m** height (see the mast-height
  note below),
  **~10–15° downward pitch**, forward-facing, unobstructed by the mast tube.
  Height/pitch chosen to frame the road 2–8 m ahead for behavior cloning.
- **2D LiDAR:** mounted so its scan plane has a **clear 360°** sightline
  (270° for the Hokuyo) — above the body line and roll bar, below the camera, so
  the vehicle body and mast tube occlude as little as possible. On a UTV bed,
  mount on a short riser above the cargo box lip. Record any permanent occlusion
  sector for Nav2 masking ([software.md](software.md)).
- **IMU:** rigidly on the deck near the vehicle's center, **vibration-isolated**
  (foam/gel mount) and orientation-aligned to `base_link` — it is the EKF
  attitude source (§3), so mounting rigor directly affects state estimation.
  **Record the mounting orientation** and apply it as a static transform; a wrong
  IMU rotation corrupts yaw silently. This responsibility was previously inherited
  from the flight-controller design and is now MRider's own.
- **Vibration:** ride-on drivetrains are buzzy. Use foam/rubber isolation under
  the mast base and the IMU, keep the mast short and stiff (minimize camera shake
  and LiDAR wobble), and torque-check after the first drive. Vibration is also why
  global-shutter imagery (§1) matters for phase-2 behavior cloning.
- **E-stop & control box:** E-stop mushroom head reachable from outside the
  vehicle ([safety.md](safety.md)); control enclosure (Teensy, Sabertooth, relay
  MUX, RC signal MUX, logic battery) low and central for weight distribution.

A mermaid mount/frame diagram and the full TF tree live in
[architecture.md](architecture.md)/[software.md](software.md);
numeric offsets in [calibration.md](calibration.md).

---

## 6. Onboard Computer (Laptop) Selection Criteria

The laptop is the ROS 2 host, runs the **`micro_ros_agent`** that terminates the vehicle link
([dbw.md](dbw.md)), and is the behavior-cloning inference/training box. The **laptop runs on
its own internal battery in v1** (no traction→19 V conversion), so runtime and efficiency are
real constraints.

| Criterion | Target | Why |
|-----------|--------|-----|
| **GPU (NN inference)** | Discrete NVIDIA GPU (e.g., RTX 3050/4050+), CUDA-capable | Real-time behavior-cloning inference and on-vehicle Keras/TensorRT; CUDA is the path of least resistance for the reused `neural_net/` stack. |
| **USB ports** | ≥ 4× USB-A/USB-C (USB3): camera + LiDAR + Teensy + IMU, plus spare | Camera (USB3), LiDAR (USB-serial), **Teensy (micro-ROS — carries command *and* feedback)**, IMU. Give the Teensy a **direct port, not a hub**: this link carries the steering setpoint, and a dropout stops the vehicle ([failsafe row 2](safety.md#2-failsafe-matrix)). |
| **Battery runtime** | ≥ ~2 h under sensor + light-inference load | Full data-collection/mapping session without a 24 V tap; drives the [power budget](safety.md) assumption that logic and traction rails are isolated. |
| **RAM / storage** | ≥ 16 GB RAM, ≥ 512 GB NVMe | ROS 2 + rosbag logging of camera/LiDAR is storage-hungry; SLAM and training want RAM. |
| **OS** | Ubuntu 22.04 (ROS 2 Humble) | Matches the mrover/OSCAR reused stack ([software.md](software.md)). |
| **Ruggedness/thermals** | Sustained GPU load without thermal throttle; secure mount | It rides on a vibrating vehicle; sustained inference must not throttle. |

**Recommendation:** a mid-range gaming/mobile-workstation laptop with an RTX-class
GPU, ≥16 GB RAM, ≥3 USB3 ports, and ≥2 h battery. Treated in [bom.md](bom.md) as
**existing/reuse (lab-supplied)** rather than a purchased line item, since the
lab already runs the mrover/OSCAR stack on such a machine.
