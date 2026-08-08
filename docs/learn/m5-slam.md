# M5 — Localization & SLAM

**Learning objectives:**

- Explain odometry from wheel encoders and its fusion with IMU (EKF).
- Understand simultaneous localization and mapping with slam_toolbox.
- Diagnose drift and evaluate map quality.

**Reference:** [design/calibration.md](../design/calibration.md)

---

## Lecture

### Odometry: counting your way to a position

The drive encoder reports **52 pulses per revolution** of the motor shaft. Combined with the
steering angle from M2's absolute sensor, a bicycle model integrates a trajectory: how far
forward, at what heading rate, therefore where.

The conversion needs one constant, `meters_per_tick`, and MRider's calibration deliberately
avoids deriving it from gear ratios
([calibration.md §2.1](../design/calibration.md#21-effective-distance-per-tick)):

> Drive or push the vehicle a **measured straight distance** `L`, record the tick delta
> `Δticks`, then `meters_per_tick = L / Δticks`. Repeat 3× and average.

This **roll-out calibration is authoritative because it bypasses guessing**. You do not need
to know the gear ratio, the quadrature decode factor, or the exact tire diameter under load —
all of those are folded into one empirically measured number.

!!! danger "The classic bug: assuming a 4× quadrature factor"

    Use the effective counts the **firmware actually reports**. mrover's firmware divides the
    count by PPR before reporting. Assume the wrong decode factor and your odometry is off by
    an integer multiple — a scale error so large it looks like a mechanical fault.

### Odometry is wrong, and MRider is honest about why

Three error sources are structural, not fixable by calibration
([ADR C consequences](../design/dbw.md#8-adr-c-drive-distance-encoding)):

1. **Gearbox backlash** between the encoder and the wheel.
2. **Wheel slip** and tire deformation.
3. **Differential wheel speed in turns** — the two rear motors are paralleled onto one
   channel, and **only one shaft is instrumented**. In a turn, the measured wheel is going a
   different speed than the vehicle center.

The design accepted this deliberately. The alternative — a magnetic ring on the wheel hub,
giving true wheel odometry — was rejected as the default because it is a more invasive,
per-vehicle mechanical mount, against the "minimally invasive" principle. It is kept as the
documented upgrade path if odometry proves inadequate.

!!! info "Calibration bounds the scale error. The EKF bounds the drift."

    This is the sentence to remember. `meters_per_tick` fixes how far a tick *means*; nothing
    in calibration can fix the fact that the instrumented wheel is not the vehicle. That is
    the EKF's job.

### Sensor fusion, and why an EKF

The wheel encoder and the IMU are wrong in **complementary** ways:

| | Wheel odometry | IMU |
|---|---|---|
| Short-term | Good — direct distance measurement | Good — high-rate angular rate |
| Long-term | Drifts with slip and backlash | Drifts badly (gyro bias integrates) |
| Fails when | Wheels slip, turning | Vehicle is genuinely still (bias hard to see) |
| Rate | ≥ 20 Hz | ≥ 100 Hz |

An **Extended Kalman Filter** maintains a state estimate plus an uncertainty, predicts forward
using the motion model, and corrects when a measurement arrives — weighting each source by how
much it is trusted. Where the two disagree, the more certain one wins, continuously.

MRider reuses B-MROVER's **dual-EKF** structure
([software.md §4.1](../design/software.md#41-robot_localization-ekf-configekfyaml)):

- **Local EKF** — `world_frame: odom`, fuses wheel odometry (vx, vy, vyaw) and IMU (yaw,
  vyaw, ax). Publishes `odom → base_link`. **Smooth and continuous**, drifts slowly.
- **Global EKF** — `world_frame: map`, adds GNSS when present. Publishes `map → odom`.
  **Accurate**, allowed to jump.

Both run with `two_d_mode: true` — MRider is a planar ride-on, so estimating z, roll, and
pitch would just add noise.

### SLAM: mapping and localizing at once

The chicken-and-egg problem: to build a map you need to know where you are; to know where you
are you need a map. SLAM solves both jointly — it accumulates scans, matches each new scan
against the map so far, and adjusts both the pose estimate and the map to stay consistent.

**Loop closure** is the powerful part. When you return to a place you have been, the system
recognizes it and corrects all accumulated drift back along the path. This is why "drive a
loop and come back the way you came" is not just a convenience — it is what makes the map
metrically correct.

MRider reuses slam_toolbox essentially as-is: `solver_plugin: CeresSolver`, `mode: mapping`,
`scan_topic: /scan`, `resolution: 0.05`, `max_laser_range: 10.0`
([software.md §4.2](../design/software.md#42-slam_toolbox-configslammapper_params_online_asyncyaml)).
For repeat runs, switch `mode` to `localization` with a saved map.

!!! danger "The frame-mismatch bug you will hit"

    B-MROVER's slam config uses `base_frame: base_footprint` while the EKF uses `base_link`.
    Design verification caught this and MRider must reconcile it — recommend `base_link`
    throughout, or add a static transform. **Nothing crashes** if you skip it. The map just
    comes out subtly wrong, and you spend a day blaming the LiDAR.

### Reading a bad map

Map defects are diagnostic — each shape of failure points at a different subsystem.

| Symptom | Likely cause | Where to look |
|---|---|---|
| **Doubled walls** — the same wall appears twice, offset | Drift not corrected; loop never closed, or odometry badly scaled | Odometry calibration; drive a closing loop |
| **Smeared / thick walls** | Extrinsic yaw error, or scan matching struggling with fast rotation | M4 extrinsics; drive slower |
| **Map rotates relative to reality** | IMU board rotation (`SENS_BOARD_ROT`) wrong | [calibration.md §5](../design/calibration.md#5-imu-calibration) |
| **Pose jumps in open areas** | Featureless stretch — nothing for scan matching to lock onto | Add features; check `max_laser_range` |
| **`map → odom` grows without bound** | Systematic odometry bias | Re-run roll-out calibration |

That last one is worth internalizing: a **monotonically growing** `map → odom` correction is
not normal drift, it is a *bias*. Random drift wanders; bias marches.

---

## Lab

**Goal:** drive a loop and build a map with slam_toolbox; compare odometry-only vs. EKF-fused
trajectories.

### Part 1 — Calibrate odometry

Do this first. Every later result depends on it.

1. Measure the **loaded** rolling circumference: mark the tire, roll exactly one revolution on
   the floor, measure the distance. (More accurate than `πD` because of tire squish.)
2. Tape out a straight `L` = 10.0 m.
3. Drive or push it, recording `drive_ticks` at both ends.
4. Repeat 3×.

| Run | `L` (m) | `Δticks` | `meters_per_tick` |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| **Mean** | | | |

**Verify** on a *fresh* 20 m line: integrated odometry must match within **~2%**.

### Part 2 — Odometry-only vs. fused

Record both trajectory sources while driving a closed loop that returns to a marked start
point.

```bash
ros2 bag record -o m5_loop \
  /mitt/dbw/status /wheel/odometry /odometry/filtered \
  /fmu/out/sensor_combined /scan /tf /tf_static
```

Plot both `wheel/odometry` and `odometry/filtered` in the xy-plane.

| Metric | Odometry only | EKF fused |
|---|---|---|
| Loop closure error (start → end distance) | *(measure)* m | *(measure)* m |
| Final heading error | *(measure)* ° | *(measure)* ° |
| Path length reported | *(measure)* m | *(measure)* m |

**Then do it again with more turns.** The gap between the two should widen — turning is
exactly where the single-instrumented-wheel limitation bites.

### Part 3 — Build a map

```bash
ros2 launch slam_toolbox online_async_launch.py \
  params_file:=<mrover>/config/slam/mapper_params_online_async.yaml
rviz2   # Map, LaserScan, TF displays
```

Drive the course. Technique matters:

- **Slowly and smoothly** — scan matching degrades with fast rotation, and ±22.5° of steering
  already makes your turns wide.
- **Close loops deliberately** — return along a path you have driven.
- **Watch `odom → base_link`** while you drive, not just the map.

```bash
ros2 run nav2_map_server map_saver_cli -f config/maps/m5_course
```

### Part 4 — Evaluate the map

| Check | Result |
|---|---|
| Do the walls appear once, single-thickness? | |
| Does the start point return to itself? Error = | *(measure)* m |
| Are right angles in the room right angles in the map? | |
| Does the map scale match a tape measure across a known span? | *(measure)* % error |

### Part 5 — Break it on purpose

Run at least two of these and record the map defect each produces:

1. **Wrong `meters_per_tick`** — halve it. What happens to the map?
2. **5° LiDAR yaw error** (from M4). What do the walls look like?
3. **No loop closure** — drive out and back a different way, never revisiting. Where does the
   drift show?
4. **Fast rotation** — spin as quickly as the steering allows through a corner.

Match each defect to a row of the diagnostic table above. **This is the actual skill**: given
a broken map, name the subsystem.

### Expected output

- `meters_per_tick` measured 3× and verified within ~2% on a fresh line
- A trajectory plot showing odometry-only vs. EKF-fused, with the fused one closing better
- A saved map with single-thickness walls
- At least two deliberately broken maps, each matched to its cause

### Check yourself

- [ ] Why is roll-out calibration better than computing distance-per-tick from the gear ratio?
- [ ] Only one of two paralleled motors is instrumented. When is that worst, and why?
- [ ] Give one thing calibration can fix and one thing only the EKF can bound.
- [ ] What does a *monotonically growing* `map → odom` correction tell you that a wandering
      one does not?
- [ ] Your map has doubled walls. Name three candidate causes and one experiment that
      distinguishes them.

---

## Slide outline

1. **Hook** — show a good map and a doubled-wall map. Same room, same vehicle.
2. **Odometry from 52 PPR** — ticks to meters
3. **Roll-out calibration** — measure the thing you want, not its ingredients
4. **Three structural error sources** — backlash, slip, and the paralleled-motor problem
5. **"Calibration bounds scale, the EKF bounds drift"**
6. **Complementary sensors** — wheel vs. IMU failure modes side by side
7. **What an EKF does** — predict, correct, weight by uncertainty
8. **Dual-EKF** — smooth-but-drifting `odom` vs. accurate-but-jumpy `map`
9. **SLAM and the chicken-and-egg problem**
10. **Loop closure** — the drift eraser
11. **The `base_footprint` / `base_link` trap** — a bug that never crashes
12. **Reading a bad map** — the diagnostic table
13. **Lab brief** — calibrate, compare, map, break
14. **Looking ahead** — M6: we know where we are; now go somewhere

---

**Previous:** [M4 — Perception](m4-perception.md) · **Next:** [M6 — Navigation (Nav2)](m6-nav2.md)
