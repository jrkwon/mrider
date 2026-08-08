# MRider Calibration Design

Concrete calibration procedures for MRider — steering zero/center and counts→degrees, drive-encoder ticks→distance, camera intrinsics, camera/LiDAR→`base_link` extrinsics, IMU calibration, and time synchronization. Each section is a procedure a student or researcher can execute and log, not a hand-wave. Every calibration produces a **stored artifact** (a YAML/param file or a recorded constant) that the runtime loads, plus a **verification step**.

Cross-links: [dbw.md](dbw.md) (angle range, encoder PPR, serial contract), [sensors.md](sensors.md) (camera/LiDAR models), [software.md](software.md) (TF tree, EKF), [safety.md](safety.md) (bring-up staging), [architecture.md](architecture.md).

Store all calibration artifacts under `config/calibration/` in the repo, one file per subsystem, each stamped with date, operator, vehicle serial, and the git commit of the firmware/software used.

---

## 1. Steering: zero/center and counts→degrees

The absolute angle sensor (AS5600-class magnetic, mounted **load-side**; potentiometer as the fallback — [dbw.md §6](dbw.md#6-adr-angle-sensor-technology-magnetic-encoder-vs-potentiometer)) reports raw counts; the Teensy and ROS 2 need **radians**, with `0` = wheels straight. Working range is **±22.5°** (±0.3927 rad) at the road wheels ([dbw.md §12](dbw.md#12-numeric-interface-contract)).

!!! danger "Do this before anything else: the wrap check"

    Rotate the sensed shaft through its **full mechanical travel** and confirm the raw reading
    is **monotonic with no discontinuity**. The AS5600 is single-turn absolute — a wrap means
    a garbage angle feeding a position loop that drives a motor (FMEA row 2, severity 5). If
    it wraps, the sensor is on the wrong shaft: move it load-side or switch to the pot
    fallback. **Record the measured travel here.**

### 1.1 Find mechanical center (zero)

1. Vehicle wheels **off the ground** (bench stands), steering motor **unpowered** (freewheel).
2. By hand, set the front wheels physically straight — use a straightedge across both front tires, or drive a short straight line first and mark the neutral.
3. With the wheels straight, read the absolute-sensor raw counts. Record as `c0` (zero-offset counts).
4. Store `c0` via the Teensy's ROS 2 zeroing service ([dbw.md §10.1](dbw.md#101-primary-transport-micro-ros-typed-messages)); the Teensy persists it (EEPROM) so center survives reboot — this is the boot-stable center that ADR B buys us, and the direct fix for B-MROVER's arbitrary boot centre (finding F4).

### 1.2 Counts→degrees scale (two-point / multi-point)

The pot is near-linear over the small ±22.5° span, so a two-point fit is adequate; take extra points to confirm linearity.

1. Turn wheels to **full left lock**, measure the actual road-wheel angle with a digital angle gauge (protractor/inclinometer on the wheel) → record `(θ_L, c_L)`; ideally `θ_L ≈ +22.5°`.
2. Turn to **full right lock** → record `(θ_R, c_R)`; ideally `θ_R ≈ −22.5°`.
3. Optionally record 3–5 intermediate points to check linearity (residual < ~0.5°).
4. Fit `θ(counts) = k · (counts − c0)`, where `k = (θ_L − θ_R)/(c_L − c_R)` (degrees per count). If nonlinearity matters, store a small lookup/polynomial instead.
5. Store `c0`, `k` (or the LUT) in `config/calibration/steering.yaml`. The Teensy applies `θ = k·(raw − c0)` before publishing `steering_angle` (radians) in `DbwStatus`.

### 1.3 Setpoint normalization check

Confirm the full command chain: `MANUAL_CONTROL.roll = +1000` should command `+22.5°` and produce a measured `+22.5°` at the wheels; `−1000 → −22.5°`; `0 → 0°` (1500 µs servo pulse). Log the commanded-vs-measured curve; it should be linear through the origin. Any offset means re-check `c0`.

### 1.4 Verification

Command a sweep (0 → +22.5 → −22.5 → 0) and confirm the measured road-wheel angle matches within **±1°** and returns to `0°` at center. Store the sweep log.

---

## 2. Drive distance: encoder ticks→meters

The drive encoder is **52 PPR** on the motor shaft (`code.ino:27`, verified). Distance needs the wheel-diameter and the gear/coupling ratio between the instrumented motor shaft and the wheel.

### 2.1 Effective distance-per-tick

1. Measure the **loaded** wheel diameter `D` (person/payload aboard, correct tire pressure) — measure rolling circumference directly by marking the tire and rolling one full revolution on the floor; `C_wheel = ` measured rollout (more accurate than `πD` because of tire squish).
2. Determine ticks-per-wheel-revolution `N_wheel`. If the encoder is on the motor shaft through gear ratio `G` (motor:wheel), then `N_wheel = 52 × G × (quadrature factor)`. If the firmware counts one edge (as `code.ino` divides count by PPR for the throttle wheel, `code.ino:83,141`), use the effective counts the firmware actually reports — do **not** assume 4× unless the firmware decodes all quadrature edges.
3. **Roll-out calibration (authoritative, bypasses guessing G):** drive/push the vehicle a **measured straight distance** `L` (e.g. 10.0 m marked with a tape), record the tick delta `Δticks` from the feedback frame. Then `meters_per_tick = L / Δticks`. Repeat 3× and average.
4. Store `meters_per_tick` in `config/calibration/odom.yaml`.

### 2.2 Consequence to document (not a defect to calibrate away)

Only one motor shaft is instrumented and the two rear motors are paralleled ([dbw.md ADR C](dbw.md)). `meters_per_tick` captures straight-line scale but **cannot** capture per-turn differential slip or backlash. This is why odometry is **fused with the IMU in the EKF** ([software.md](software.md)); calibration bounds the *scale* error, the EKF bounds the *drift*. State this in the student notes so no one expects raw wheel odometry to be exact.

### 2.3 Verification

Drive a fresh measured 20 m straight line; integrated odometry distance should match within **~2%**. Drive a known square loop; the closure error is the fused-odometry check (EKF, not calibration alone).

---

## 3. Camera intrinsics

For the front camera ([sensors.md](sensors.md)).

1. Use the ROS 2 `camera_calibration` (`cameracalibrator`) tool with a printed **checkerboard** of known square size (e.g. 8×6 inner corners, 25 mm squares) mounted rigidly flat.
2. Stream the camera, move the board across the full field of view and depth range (near/far, all corners, tilts) until the tool's X/Y/size/skew bars are full.
3. Commit → produces `camera_matrix` (fx, fy, cx, cy), `distortion_coefficients`, `rectification`, `projection`. Save as `config/calibration/camera_front.yaml` (ROS `CameraInfo` format).
4. If using a RealSense D435i, the factory intrinsics are available from the driver, but re-verify with the checkerboard for the exact lens/resolution used.

**Verification:** rectify a checkerboard image; straight board edges must appear straight (reprojection error < ~0.3 px reported by the tool).

---

## 4. Extrinsics: camera / LiDAR → `base_link`

Every sensor frame must be located relative to `base_link` for the TF tree ([software.md](software.md): `map → odom → base_link → sensor frames`). Define `base_link` first, then each sensor's static transform.

### 4.1 base_link definition

Pin `base_link` at the **center of the rear axle, on the ground plane, X forward, Z up, Y left** (REP-103 / REP-105). The Ackermann kinematics (wheelbase, track) in [software.md](software.md) are measured from this origin.

### 4.2 Coarse extrinsics by measurement

For each sensor, measure the translation (x, y, z in meters) and orientation (roll, pitch, yaw) from `base_link` to the sensor's optical/scan frame with a tape and level. Publish as `static_transform_publisher` entries (or a URDF joint). This gets you to a few cm / few degrees.

### 4.3 LiDAR→base_link refinement

1. Place the vehicle a **known distance** from a flat wall, perpendicular. The 2D LiDAR scan of the wall should be a straight line at the measured range and centered — adjust yaw/x/y until the scan matches ground truth.
2. Confirm the scan's zero-heading points **forward** (+X) and that left/right are not mirrored.

### 4.4 Camera→LiDAR (cross-sensor) refinement

1. Place a target visible to both (e.g. a board/pole) at several known positions.
2. Verify a LiDAR return of the target projects onto the correct camera pixel using the intrinsics (§3) and the two extrinsics chained through `base_link`.
3. Adjust the camera extrinsic until projection error is within a few pixels / few cm. Store `config/calibration/extrinsics.yaml` (or the URDF `<joint>` origins).

**Verification:** overlay projected LiDAR points on the camera image of a known scene; points land on the corresponding structure.

---

## 5. IMU calibration

The IMU is a **standalone BNO085-class module connected directly to the laptop**
([sensors.md §3](sensors.md#3-imu)), publishing `sensor_msgs/Imu` on `/imu/data` into
`robot_localization`.

!!! info "Revised 2026-08-07"

    This procedure was previously QGroundControl-based, because the IMU lived inside the
    Pixhawk. [D3](adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07) removed the
    Pixhawk, so calibration is now an in-repo procedure with no external ground-station tool.
    The **estimator is unchanged** — it was always `robot_localization`, with PX4 supplying
    raw IMU only (finding F11).

1. **Onboard fusion calibration:** a BNO085-class part self-calibrates its accel/gyro/mag in
   the background and reports a **calibration-status byte per sensor**. Drive the sequence the
   vendor specifies (slow figure-8 for the magnetometer, brief rest for the gyro, a few static
   orientations for the accel) until status reads fully calibrated. **Log the status byte** —
   a partially-calibrated IMU is a silent yaw-drift source.
2. **Level horizon:** set the vehicle on a known-level surface and record the residual
   roll/pitch as a static offset so `0` matches the physical vehicle.
3. **Gyro bias:** let the IMU sit still for ~10 s after power-up before driving. Confirm the
   reported yaw rate settles to ≈ 0.
4. **Mounting orientation:** publish the IMU→`base_link` rotation as a **static transform in
   the URDF**, not as a driver parameter, so it lives with the rest of the frame tree. A wrong
   rotation corrupts yaw silently — this is the highest-risk step here. Record a photo of the
   physical mounting alongside the transform values.
5. Store the calibration offsets and the mounting transform in
   `config/calibration/imu.yaml`, stamped with date, operator, and the IMU part number.

**Verification:** with the vehicle stationary and level, roll/pitch ≈ 0 and stable over 60 s;
rotate the vehicle a known 90° and confirm yaw changes ~90° **in the correct sign**; drive a
closed 20 m figure-8 and confirm heading error ≤ 5° (this is also an
[acceptance gate](software.md#8-semester-1-scope-and-software-acceptance-gates)).

---

## 6. Time synchronization

Odometry, LiDAR, camera, and IMU must share a common time base or the EKF/SLAM fuses stale
data.

!!! success "This got simpler under D3"

    The superseded design had **two clocks** — the laptop and PX4 boot-time microseconds — and
    required estimating a constant offset plus drift between them via MAVLink
    `TIMESYNC`/`SYSTEM_TIME` round-trips. That machinery is gone. **micro-ROS provides session
    time synchronisation**, so the Teensy stamps in a clock already related to the laptop's,
    and every other sensor is physically connected to the laptop. One clock domain, no offset
    estimation.

**Approach (pinned):**

1. **Single authoritative clock = the laptop.** All ROS 2 sensor drivers (camera, LiDAR, IMU)
   stamp with the laptop clock on arrival. Since every sensor is connected to the laptop
   ([overview.md](overview.md): "a laptop will be an on-board computer to which most sensors
   are connected"), their timestamps are already laptop-referenced.
2. **Teensy:** use **micro-ROS session time sync** so `DbwStatus.stamp` is laptop-referenced.
   Verify the sync is actually established at startup rather than assuming it — log the
   reported offset once per session.
3. **Residual link latency:** measure the USB round-trip once with a loopback test and record
   the mean. If it is significant relative to a control period, subtract it as a fixed offset
   and document the value. This is also the
   [joystick→wheel-motion latency gate](software.md#8-semester-1-scope-and-software-acceptance-gates)
   (≤ 100 ms at p95).
4. Keep everything on one machine's wall clock; do **not** enable ROS 2 simulated time
   (`use_sim_time=false`) on the real vehicle — **but do enable it in simulation**, which is
   the one place the twin and the vehicle legitimately differ.

**Verification:** wiggle a feature seen by both LiDAR and camera while driving; the events
should align within one sensor period. Confirm `robot_localization` does not reject
measurements as out-of-sequence.

---

## 7. Calibration artifact index

| Subsystem | Procedure | Stored artifact |
|---|---|---|
| Steering zero + scale | §1 | `config/calibration/steering.yaml` (`c0`, `k`/LUT) |
| Drive odometry | §2 | `config/calibration/odom.yaml` (`meters_per_tick`) |
| Camera intrinsics | §3 | `config/calibration/camera_front.yaml` |
| Extrinsics (cam/LiDAR→base_link) | §4 | `config/calibration/extrinsics.yaml` or URDF joints |
| IMU | §5 | `config/calibration/imu.yaml` (offsets + mounting transform + part number) |
| Time sync | §6 | offset recorded in bridge config; loopback-latency note |

Each artifact is stamped with date, operator, vehicle serial, and the firmware/software git commit so a calibration can be reproduced or invalidated when hardware changes. Re-run the relevant section after any mechanical change (new tires, re-mounted sensor, re-flashed firmware).
