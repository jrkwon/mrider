# 6. Bench Test (Wheels-Off) & Calibration

**Goal:** validate the full command/feedback chain safely, then calibrate.

With the vehicle on a stand, exercise steering and throttle end-to-end and confirm every
failsafe in the matrix. Then calibrate: steering zero/center and counts→degrees,
encoder ticks→distance, camera intrinsics, and camera/LiDAR→base_link extrinsics.

- **Prerequisites:** Section 5 complete.
- **Specification:** [design/safety.md](../design/safety.md), [design/calibration.md](../design/calibration.md)
- **Expected outcome:** all failsafes pass wheels-off; calibration constants recorded.

!!! warning "Draft — not yet validated on hardware"

    The procedures below come from
    [safety.md §6](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first) and
    [calibration.md](../design/calibration.md). **Every result cell is empty because no
    vehicle has been tested.** The record sheets are the deliverable of this step — fill them
    in and commit them.

!!! danger "This is the last step before the vehicle touches the ground"

    Everything the vehicle will do wrong at walking speed in step 7, it will do wrong here
    first — on a stand, where it is harmless. Do not shorten this step. **Failsafes first,
    calibration second**: there is no point calibrating a vehicle that cannot be stopped.

This step covers **Stages 3–4** of the bring-up protocol.

---

## Part A — Failsafe verification

## 6.1 Setup

- Vehicle on stands, **wheels off the ground**, verified by lifting each corner.
- Traction pack connected, E-stop within arm's reach of the operator.
- A second person present whose only job is the E-stop.
- Bench supply current limits still in place if you can keep them.

## 6.2 Failsafe matrix verification

Test **every row** of [safety.md §2](../design/safety.md#2-failsafe-matrix). Each row is a
specific way this vehicle can fail; each has a defined behavior; each is testable here.

| # | Loss scenario | How to induce | Expected immediate behavior | Expected steering behavior | Observed | Pass |
|---|---|---|---|---|---|---|
| 1 | **Command/heartbeat loss** | Kill the command shim (stream < 10 Hz) | PX4 offboard-loss failsafe: throttle → 0, enter hold | PX4 stops emitting servo setpoint → Nano bit0 clears → steering **holds last angle**, motor de-energizes | | ☐ |
| 2 | **USB loss** (Nano ↔ laptop) | Unplug `/dev/mrider_nano` | Feedback lost → autonomy degrades to safe-stop (throttle 0 via PX4) | **Steering unaffected** — setpoint comes via PX4 servo PWM, not USB | | ☐ |
| 3 | **RC loss** | Power off the transmitter | PX4 `COM_RC_LOSS_T` → configured Hold/Disarm: throttle → 0 | setpoint goes to hold/center per PX4 config → Nano holds | | ☐ |
| 4 | **Battery sag / brownout** | Force a stall while watching the logic rail; or bench-drop the logic rail | Logic rail below threshold → MUX coil drops → **revert to STOCK**; Sabertooth LVC also stops motors | steering motor de-energizes with the coil → **freewheel** | | ☐ |
| 5 | **E-stop pressed** | Press it | Traction power cut; MUX coil dropped → STOCK; Sabertooth unpowered on motor rail | steering motor loses power → **freewheel** | | ☐ |
| 6 | **Sabertooth signal loss** | Unplug S1, then S2 | Affected channel stops its motor (built-in R/C timeout) | S1 lost → steering motor stops | | ☐ |
| 7 | **Steering at limit / jam** | Command beyond the mechanical stop | Nano clamps effort **toward center only**, sets stall bit | holds at limit, no further drive into the stop | | ☐ |

!!! danger "Row 2 is the counter-intuitive one — verify it deliberately"

    Unplugging the Nano's USB cable does **not** stop the steering. The setpoint arrives via
    PX4 servo PWM, so the column keeps tracking while the laptop goes blind on odometry. This
    is by design — and it is exactly the behavior an operator will misread in an emergency if
    they have not seen it on the bench.

## 6.3 Freewheel-on-power-loss test

The pinned test from [safety.md §4.4](../design/safety.md#44-test-procedure-freewheel-on-power-loss),
steps 1–2 (step 3 happens in [step 7](07-manual-drive.md) on the ground):

1. Wheels off the ground. Command a mid-range steering angle; confirm the Nano holds it.
2. Press E-stop. Confirm all four:
    - [ ] traction dead
    - [ ] MUX shows STOCK
    - [ ] steering motor de-energized
    - [ ] column **turns freely by hand** with light force

**Record:** hand-steer force at the rim after E-stop = *(measure during bring-up)* N
(spring-scale check; expect a few N).

!!! note "Wiper-motor builds behave differently — and that is a re-analysis, not a variation"

    If you took the [wiper-motor fallback](../design/dbw.md#24-wiper-motor-fallback), the
    worm gear is largely non-back-drivable and the column will **hold** rather than freewheel.
    That invalidates the analysis in
    [safety.md §4.3](../design/safety.md#43-why-traction-cut-freewheel-steering-is-acceptable).
    Write down the actual behavior and re-derive whether it is acceptable **before** step 7.

## 6.4 Stage 3 and 4 checks

**Stage 3 — MUX + E-stop, wheels off:**

- [ ] Every failsafe-matrix row (§6.2) passes
- [ ] Freewheel test (§6.3) passes
- [ ] Default = STOCK confirmed on **every** power-up and **every** fault

**Stage 4 — full integration on the chassis, wheels on stands:**

- [ ] Failsafe matrix repeated on the fully assembled vehicle
- [ ] Steering mechanical limits measured — actual travel vs. the ±22.5° design target
- [ ] Drive-encoder ticks increment correctly under powered rotation
- [ ] **No logic-rail brownout under steering stall** — measure it, do not assume

**Record sheet — Stage 4**

| Measurement | Value |
|---|---|
| Measured full-left road-wheel angle | *(measure during bring-up)* ° |
| Measured full-right road-wheel angle | *(measure during bring-up)* ° |
| Logic rail during steering stall | *(measure during bring-up)* V |
| Logic rail sag vs. rest | *(measure during bring-up)* V |
| Steering stall current | *(measure during bring-up)* A |
| Drive stall current (paralleled) | *(measure during bring-up)* A — must be < 32 A |

---

## Part B — Calibration

Only begin once every failsafe passes. Each calibration produces a **stored artifact** the
runtime loads, plus a **verification step**. Store everything under `config/calibration/`,
stamped with date, operator, vehicle serial, and the firmware/software git commit
([calibration.md §7](../design/calibration.md#7-calibration-artifact-index)).

## 6.5 Steering: zero and counts→degrees

**Find mechanical center** ([calibration.md §1.1](../design/calibration.md#11-find-mechanical-center-zero)):

1. Wheels off the ground, steering motor **unpowered** (freewheel).
2. By hand, set the front wheels physically straight — use a straightedge across both front
   tires.
3. Read the absolute-sensor raw counts. Record as `c0`.
4. Store it via the Nano config command `C,ZERO`. The Nano persists `c0` in EEPROM, so center
   survives reboot — this boot-stable center is exactly what
   [ADR B](../design/dbw.md#5-adr-b-steering-angle-encoding) bought.

**Counts→degrees scale** ([calibration.md §1.2](../design/calibration.md#12-countsdegrees-scale-two-point-multi-point)):

1. Full **left** lock — measure the actual road-wheel angle with a digital angle gauge →
   record `(θ_L, c_L)`.
2. Full **right** lock → record `(θ_R, c_R)`.
3. Take 3–5 intermediate points to check linearity (residual < ~0.5°).
4. Fit `θ(counts) = k · (counts − c0)` where `k = (θ_L − θ_R) / (c_L − c_R)`.
5. Store `c0` and `k` in `config/calibration/steering.yaml`.

**Record sheet — steering calibration**

| Point | Road-wheel angle θ (°) | Raw counts | Residual (°) |
|---|---|---|---|
| Full left | *(measure)* | *(measure)* | — |
| Intermediate 1 | *(measure)* | *(measure)* | *(compute)* |
| Center | 0 | `c0` = *(measure)* | — |
| Intermediate 2 | *(measure)* | *(measure)* | *(compute)* |
| Full right | *(measure)* | *(measure)* | — |

`k` = *(compute)* °/count · linearity residual max = *(compute)* ° · artifact:
`config/calibration/steering.yaml`

**Setpoint normalization check** ([calibration.md §1.3](../design/calibration.md#13-setpoint-normalization-check)):
`MANUAL_CONTROL.roll = +1000` must produce a **measured** +22.5° at the wheels; `−1000` →
−22.5°; `0` → 0° (1500 µs servo pulse). Log the commanded-vs-measured curve — it should be
linear through the origin. **Any offset means re-check `c0`.**

**Verification:** command a sweep 0 → +22.5 → −22.5 → 0. Measured road-wheel angle must match
within **±1°** and return to 0° at center. Store the sweep log.

## 6.6 Drive distance: ticks→meters

The roll-out calibration is authoritative because it **bypasses guessing the gear ratio**
([calibration.md §2.1](../design/calibration.md#21-effective-distance-per-tick)):

1. Measure the **loaded** rolling circumference directly — mark the tire, roll one full
   revolution on the floor, measure. More accurate than `πD` because of tire squish.
2. Drive or push the vehicle a **measured straight distance** `L` (e.g. 10.0 m by tape),
   recording the tick delta `Δticks` from the feedback frame.
3. `meters_per_tick = L / Δticks`. **Repeat 3× and average.**
4. Store in `config/calibration/odom.yaml`.

!!! note "Do not assume a 4× quadrature factor"

    Use the effective counts the **firmware actually reports**. The mrover firmware divides
    count by PPR before reporting (`code.ino:83,141`), so an assumed decode factor will put
    your odometry off by an integer multiple — a scale error large enough to look like a
    mechanical problem.

**Record sheet — odometry calibration**

| Run | Measured distance `L` (m) | `Δticks` | `meters_per_tick` |
|---|---|---|---|
| 1 | *(measure)* | *(measure)* | *(compute)* |
| 2 | *(measure)* | *(measure)* | *(compute)* |
| 3 | *(measure)* | *(measure)* | *(compute)* |
| **Mean** | | | *(compute)* |

Loaded rolling circumference = *(measure)* m · artifact: `config/calibration/odom.yaml`

**Verification:** drive a fresh measured 20 m straight line; integrated odometry must match
within **~2%**. Then drive a known square loop — the closure error is the *fused* odometry
check (EKF), not a calibration check.

!!! info "What calibration can and cannot fix"

    `meters_per_tick` captures straight-line **scale**. It cannot capture per-turn
    differential slip or gearbox backlash, because only one motor shaft of a paralleled pair
    is instrumented ([ADR C](../design/dbw.md#8-adr-c-drive-distance-encoding)). That is why
    odometry is fused with the IMU in the EKF: **calibration bounds the scale error, the EKF
    bounds the drift.** Nobody should expect raw wheel odometry to close a loop.

## 6.7 Camera intrinsics

Use ROS 2 `camera_calibration` with a printed checkerboard of known square size (e.g. 8×6
inner corners, 25 mm squares) mounted rigidly flat
([calibration.md §3](../design/calibration.md#3-camera-intrinsics)).

```bash
ros2 run camera_calibration cameracalibrator \
  --size 8x6 --square 0.025 \
  --ros-args -r image:=/camera/color/image_raw -r camera:=/camera
```

Move the board across the **full** field of view and depth range — near/far, all corners,
tilts — until the X/Y/size/skew bars are full. Commit, then save as
`config/calibration/camera_front.yaml` in ROS `CameraInfo` format.

**Verification:** rectify a checkerboard image; straight board edges must appear straight.
Reprojection error < ~0.3 px as reported by the tool.

Record: reprojection error = *(measure)* px · squares = *(record)* · resolution = *(record)*

!!! tip "RealSense users: re-verify anyway"

    Factory intrinsics are available from the driver, but re-run the checkerboard for the
    exact lens and resolution you will actually stream.

## 6.8 Extrinsics: sensors → `base_link`

**Define `base_link` first** ([calibration.md §4.1](../design/calibration.md#41-base_link-definition)):
center of the **rear axle, on the ground plane, X forward, Z up, Y left** (REP-103/105). The
Ackermann parameters from step 2 are measured from this origin.

**Coarse, by measurement:** for each sensor, tape-and-level the translation (x, y, z) and
orientation (roll, pitch, yaw) from `base_link` to the sensor frame. This gets you to a few
cm and a few degrees.

**LiDAR refinement** ([calibration.md §4.3](../design/calibration.md#43-lidarbase_link-refinement)):

1. Park a known distance from a flat wall, perpendicular. The scan of the wall should be a
   straight line at the measured range, centered. Adjust yaw/x/y until it matches.
2. Confirm zero-heading points **forward (+X)** and that left/right are not mirrored.

**Camera↔LiDAR refinement** ([calibration.md §4.4](../design/calibration.md#44-cameralidar-cross-sensor-refinement)):
place a target visible to both at several known positions; verify a LiDAR return projects
onto the correct camera pixel through the intrinsics and both extrinsics chained via
`base_link`. Adjust until projection error is a few pixels / few cm.

**Record sheet — extrinsics** (artifact: `config/calibration/extrinsics.yaml` or URDF joints)

| Sensor | x (m) | y (m) | z (m) | roll (°) | pitch (°) | yaw (°) |
|---|---|---|---|---|---|---|
| `camera_link` | *(measure)* | *(measure)* | *(measure)* | *(measure)* | *(measure)* | *(measure)* |
| `laser`/`lidar_link` | *(measure)* | *(measure)* | *(measure)* | *(measure)* | *(measure)* | *(measure)* |
| `imu_link` | *(measure)* | *(measure)* | *(measure)* | *(measure)* | *(measure)* | *(measure)* |
| `gnss_link` (optional) | *(measure)* | *(measure)* | *(measure)* | *(measure)* | *(measure)* | *(measure)* |

**Verification:** overlay projected LiDAR points on a camera image of a known scene; points
must land on the corresponding structure.

!!! danger "Extrinsics are only valid while the mast holds its geometry"

    Re-run this section after **any** mechanical change — a re-mounted sensor, a bumped mast,
    new tires (which change `base_link` height). A silently invalidated extrinsic looks like a
    SLAM problem in step 8.

## 6.9 IMU and time sync

**IMU** — done in [step 4](04-firmware.md) via QGroundControl. Confirm here that it survived:
with the vehicle stationary and level, `VehicleAttitude` roll/pitch ≈ 0 and stable; rotate
the vehicle a known 90° and confirm yaw changes ~90° **in the correct sign**. Export the
parameter file to `config/calibration/px4_params_<version>.params`.

**Time sync** ([calibration.md §6](../design/calibration.md#6-laptoppixhawk-time-synchronization)):

- Single authoritative clock = **the laptop**. Sensors physically connected to it are already
  laptop-referenced.
- PX4 → laptop offset estimated via MAVLink `TIMESYNC`/`SYSTEM_TIME` round-trip and applied
  in the bridge, so PX4-originated messages carry laptop-referenced stamps.
- Nano frames are stamped **on receipt**. Record the mean USB latency once via a loopback
  test and subtract it as a fixed offset if needed.
- `use_sim_time=false`. Always.

**Verification:** wiggle a feature seen by both LiDAR and camera while driving; the events
should align within one sensor period. Confirm the EKF is not rejecting measurements as
out-of-sequence (no PX4 EKF timestamp warnings).

Record: mean Nano USB latency = *(measure)* ms · PX4↔laptop offset method = *(record)*

## 6.10 Calibration artifact index

| Subsystem | Procedure | Artifact | Done |
|---|---|---|---|
| Steering zero + scale | §6.5 | `config/calibration/steering.yaml` (`c0`, `k`) | ☐ |
| Drive odometry | §6.6 | `config/calibration/odom.yaml` (`meters_per_tick`) | ☐ |
| Camera intrinsics | §6.7 | `config/calibration/camera_front.yaml` | ☐ |
| Extrinsics | §6.8 | `config/calibration/extrinsics.yaml` or URDF joints | ☐ |
| IMU / PX4 | §6.9 | `config/calibration/px4_params_<ver>.params` | ☐ |
| Time sync | §6.9 | offset in bridge config; loopback-latency note | ☐ |
| As-built BOM | [step 1](01-bom-sourcing.md) | `config/calibration/bom_asbuilt.md` | ☐ |

Every artifact carries date, operator, vehicle serial, and firmware/software git commit.
**Re-run the relevant section after any mechanical change** — new tires, re-mounted sensor,
re-flashed firmware.

## 6.11 Gate to step 7

- [ ] All seven failsafe-matrix rows verified wheels-off
- [ ] Freewheel-on-E-stop confirmed (or hold-behavior re-analyzed for a wiper-motor build)
- [ ] Default = STOCK on every power-up and every fault
- [ ] Steering mechanical limits measured against the ±22.5° target
- [ ] No logic-rail brownout under steering stall
- [ ] Drive stall current confirmed < 32 A/channel
- [ ] Steering sweep verifies within ±1° and returns to 0° at center
- [ ] Odometry verifies within ~2% over a fresh 20 m straight line
- [ ] Camera reprojection error < ~0.3 px
- [ ] LiDAR points project onto the correct camera structure
- [ ] IMU verified; yaw changes correctly through a known 90°
- [ ] All seven calibration artifacts committed with full stamps

---

**Previous:** [5. Software install](05-software.md) · **Next:** [7. Manual drive](07-manual-drive.md)
