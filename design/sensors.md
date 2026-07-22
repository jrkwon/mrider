# Sensors & Onboard Compute

> Part of the MRider design set. Siblings: [architecture.md](architecture.md) ·
> [vehicle.md](vehicle.md) · [dbw.md](dbw.md) · [safety.md](safety.md) ·
> [software.md](software.md) · [calibration.md](calibration.md) · [bom.md](bom.md) ·
> [overview.md](overview.md)
>
> Prices are **estimates as of July 2026** and vary by retailer and stock.

This document specifies the MRider perception and localization sensor set and the
onboard computer. Per [overview.md](overview.md), the **minimum sensor package is
one front camera and one 2D LiDAR**; IMU is provided by the Pixhawk 6C; GNSS is
optional with an RTK growth path. Each major choice is an ADR. Frame definitions,
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

**Decision.** **Minimum tier: a color global-shutter USB3 camera** (e.g.,
**Arducam AR0234**, 2.3 MP, global shutter, up to 80 fps, ~$160–180). **Full
tier: Intel RealSense D435i** (~$334–380) when depth + a factory-calibrated IMU
are wanted.

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

**Mounting summary:** forward-facing, on the mast (§4), ~1.0–1.2 m height, slight
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

**Decision:** in v1, **use the Pixhawk 6C's internal IMUs** as the EKF/attitude
source — **no separate standalone IMU.** The Pixhawk 6C carries dual IMUs
(e.g., BMI055 + ICM-class) with temperature compensation and vibration isolation,
already fused by PX4's EKF2, which MRider reuses along with the rest of the mrover
PX4 stack ([software.md](software.md)). Wheel/steering odometry from the
[Nano feedback path](dbw.md) fuses with this IMU in `robot_localization`'s EKF
(mrover `config/ekf.yaml`) to bound the paralleled-motor/single-encoder odometry
error noted in [ADR C](dbw.md).

**Rationale.** Reuse (the mrover EKF + PX4 fusion is validated), fewer parts,
one clock domain to time-sync ([calibration.md](calibration.md)). Adding a
standalone IMU would duplicate what the Pixhawk already provides.

**Consequence / growth path.** The full-tier RealSense D435i contributes a
**second** IMU; treat it as a cross-check for camera-frame motion, **not** the
EKF primary. If a future build drops the Pixhawk (e.g., an Arduino-lite tier),
an IMU becomes a required standalone line item — out of scope for v1.

---

## 4. GNSS (optional) & RTK Growth Path

Per [overview.md](overview.md), **GNSS is optional** and therefore **excluded
from the minimum tier**, included in the **full tier**.

- **Full tier — a Pixhawk-compatible GNSS module** (e.g., Holybro M9N or M10,
  ~$90) on the Pixhawk GPS port. PX4 fuses it into EKF2 for global position and
  heading aid — directly reusing the mrover GNSS wiring.
- **RTK growth path (beyond full tier):** upgrade to an **RTK rover module**
  (e.g., u-blox ZED-F9P-class, ~$220–300) plus an **RTK base/NTRIP correction
  source** for centimeter-level positioning. This is the mrover "(-RTK)" path
  referenced in the plan; PX4 already supports RTK injection over MAVLink, so
  it's a module + corrections swap, not new firmware. Documented here as a future
  option; **not** in either v1 tier total.

**ADR note.** GNSS is a tiering decision rather than a technology contest: the
question is only *present (full) vs absent (min)*, and the RTK path is a labeled
future upgrade. No standalone ADR block is warranted; the LiDAR and camera ADRs
carry the sensor-selection weight.

---

## 5. Mounting / Mast Concept

The sensors share a single **mast** on the deck/bed ([vehicle.md](vehicle.md) C5)
so their extrinsics are fixed once ([calibration.md](calibration.md)).

- **Front camera:** top of mast or a forward boom, **~1.0–1.2 m** height,
  **~10–15° downward pitch**, forward-facing, unobstructed by the mast tube.
  Height/pitch chosen to frame the road 2–8 m ahead for behavior cloning.
- **2D LiDAR:** mounted so its scan plane has a **clear 360°** sightline
  (270° for the Hokuyo) — above the body line and roll bar, below the camera, so
  the vehicle body and mast tube occlude as little as possible. On a UTV bed,
  mount on a short riser above the cargo box lip. Record any permanent occlusion
  sector for Nav2 masking ([software.md](software.md)).
- **Pixhawk 6C:** rigidly on the deck near the vehicle's center, **vibration-
  isolated** (foam/gel mount) and orientation-aligned to `base_link` — its IMU
  is the EKF source (§3), so mounting rigor directly affects state estimation.
- **Vibration:** ride-on drivetrains are buzzy. Use foam/rubber isolation under
  the mast base and the Pixhawk, keep the mast short and stiff (minimize camera
  shake and LiDAR wobble), and torque-check after the first drive. Vibration is
  also why global-shutter imagery (§1) matters.
- **E-stop & control box:** E-stop mushroom head reachable from outside the
  vehicle ([safety.md](safety.md)); control enclosure (Sabertooth/Nano/relays)
  low and central for weight distribution.

A mermaid mount/frame diagram and the full TF tree live in
[architecture.md](architecture.md)/[software.md](software.md);
numeric offsets in [calibration.md](calibration.md).

---

## 6. Onboard Computer (Laptop) Selection Criteria

The laptop is the ROS 2 host, the XRCE-DDS/MAVLink endpoint to the Pixhawk
([dbw.md](dbw.md)), and the behavior-cloning inference/training box. Per the
plan, the **laptop runs on its own internal battery in v1** (no 24 V→19 V
conversion), so runtime and efficiency are real constraints.

| Criterion | Target | Why |
|-----------|--------|-----|
| **GPU (NN inference)** | Discrete NVIDIA GPU (e.g., RTX 3050/4050+), CUDA-capable | Real-time behavior-cloning inference and on-vehicle Keras/TensorRT; CUDA is the path of least resistance for the reused `neural_net/` stack. |
| **USB ports** | ≥ 3× USB-A/USB-C (USB3): camera + LiDAR + Pixhawk/Nano, plus spare | Camera (USB3), LiDAR (USB-serial), Pixhawk XRCE link + Nano USB-serial all connect here ([architecture.md](architecture.md)). A powered USB3 hub is an acceptable fallback but counts against reliability. |
| **Battery runtime** | ≥ ~2 h under sensor + light-inference load | Full data-collection/mapping session without a 24 V tap; drives the [power budget](safety.md) assumption that logic and traction rails are isolated. |
| **RAM / storage** | ≥ 16 GB RAM, ≥ 512 GB NVMe | ROS 2 + rosbag logging of camera/LiDAR is storage-hungry; SLAM and training want RAM. |
| **OS** | Ubuntu 22.04 (ROS 2 Humble) | Matches the mrover/OSCAR reused stack ([software.md](software.md)). |
| **Ruggedness/thermals** | Sustained GPU load without thermal throttle; secure mount | It rides on a vibrating vehicle; sustained inference must not throttle. |

**Recommendation:** a mid-range gaming/mobile-workstation laptop with an RTX-class
GPU, ≥16 GB RAM, ≥3 USB3 ports, and ≥2 h battery. Treated in [bom.md](bom.md) as
**existing/reuse (lab-supplied)** rather than a purchased line item, since the
lab already runs the mrover/OSCAR stack on such a machine.
