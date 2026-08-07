# M4 — Perception (Camera + 2D LiDAR)

**Learning objectives:**

- Understand camera and 2D LiDAR sensing: fields of view, rates, and coordinate frames.
- Bring up the sensor drivers in ROS 2 and inspect the data in RViz.
- Relate raw sensor data to the vehicle base frame via extrinsics.

**Reference:** [design/sensors.md](../design/sensors.md)

---

## Lecture

### Two sensors that fail in opposite ways

MRider's minimum sensor package is one front camera and one 2D LiDAR. That pairing is not
arbitrary — each covers the other's blind spot.

| | Camera | 2D LiDAR |
|---|---|---|
| Measures | Colour and texture, projected | Range, directly |
| Depth | Not directly (mono) | Metric, per beam |
| Field of view | Narrow-ish, forward | Typically 360° |
| Sees in the dark | No | Yes |
| Sees glass, black surfaces | Yes | Poorly or not at all |
| Sees lane markings, signs, colour | Yes | No |
| Data rate | High (megapixels × fps) | Low (a few hundred ranges × scan rate) |
| Good for | Behavior cloning, classification | Mapping, obstacle avoidance, localization |

The 2D LiDAR sees a **single horizontal plane**. An obstacle below or above that plane —
a curb, a low bar, a table edge — is invisible to it. Students find this out by driving into
something the map said was not there.

### Why a global shutter matters more than resolution

The camera is specified as **global shutter**
([sensors.md §1](../design/sensors.md#1-front-camera)), and that constraint is stronger than
it sounds.

A **rolling shutter** exposes the image row by row. While the rows are being read, the vehicle
is turning, so different rows correspond to different vehicle poses. The resulting image is
skewed — and crucially, the *amount* of skew depends on the turn rate.

For behavior cloning (M7), each image is paired with a steering label. With a rolling shutter,
the image is smeared by an amount **correlated with the very quantity you are trying to
predict**. The network can learn to read the smear instead of the road. That is a subtle,
hard-to-debug form of label leakage, and it is why the BOM refuses a cheap webcam.

!!! note "Choosing a sensor by what it does to your labels"

    Resolution and frame rate are the specs people compare. The property that actually decided
    this component was how its artifact interacts with the downstream learning task. Keep
    that habit.

### Rates, and what depends on them

| Stream | Typical rate | Consumer |
|---|---|---|
| `/scan` (LiDAR) | scan rate, ~10 Hz class | slam_toolbox, Nav2 costmaps |
| `/camera/color/image_raw` | camera fps | Data recorder, learned policy |
| `/fmu/out/sensor_combined` (IMU) | ≥ 100 Hz | EKF |
| `/mrider/feedback` (encoders) | ≥ 20 Hz | Odometry → EKF |

The IMU is **internal to the Pixhawk 6C** — it is not a separate purchase, and its
calibration happens through QGroundControl
([sensors.md §3](../design/sensors.md#3-imu)). GNSS is optional and excluded from the minimum
tier by design; the map-EKF runs GNSS-free until a receiver is added
([sensors.md §4](../design/sensors.md#4-gnss-optional-rtk-growth-path)).

### Frames: the part everyone gets wrong

A sensor reading is meaningless without knowing **where the sensor was** when it was taken.
That is what the TF tree provides, and MRider follows REP-105:

```
map → odom → base_link → { camera_link, laser/lidar_link, imu_link, gnss_link }
```

- `map → odom` — published by SLAM / the global EKF. Jumps when SLAM corrects.
- `odom → base_link` — published by the local EKF. Smooth and continuous, but drifts.
- `base_link → sensors` — **static**, from the URDF. These are the *extrinsics*.

**`base_link` is pinned** at the center of the rear axle, on the ground plane, X forward, Z
up, Y left ([calibration.md §4.1](../design/calibration.md#41-base_link-definition)).

!!! info "Why `odom` exists at all"

    A common question: if SLAM knows where we are, why keep a drifting `odom` frame? Because
    `odom → base_link` is **continuous** — it never jumps — which is what a local controller
    needs to avoid commanding a step change. `map → odom` absorbs the discontinuities when
    SLAM corrects. The two-level structure separates "smooth but drifting" from "accurate but
    jumpy."

### Extrinsics — two kinds of wrong

Extrinsics are the static transforms from `base_link` to each sensor: three translations and
three rotations.

**Getting the translation wrong** by a few centimeters shifts your map slightly. Annoying.

**Getting the rotation wrong** — especially yaw — is much worse. A LiDAR mounted 5° off in yaw
produces a scan that rotates relative to the vehicle as it turns. SLAM interprets this as
inconsistent observations and produces a map with doubled or smeared walls. Students almost
always blame SLAM.

The refinement procedure is deliberately physical
([calibration.md §4.3](../design/calibration.md#43-lidarbase_link-refinement)): park a known
distance from a flat wall, perpendicular. The scan of the wall should be a straight line at
the measured range, centered. Adjust yaw/x/y until it matches ground truth. Then confirm the
scan's zero-heading points **forward (+X)** and that left/right are not mirrored.

For camera↔LiDAR, place a target visible to both and verify that a LiDAR return of the target
projects onto the correct camera pixel, chaining intrinsics and both extrinsics through
`base_link`.

### Intrinsics, briefly

Camera intrinsics — `fx, fy, cx, cy` plus distortion — describe how the lens maps 3D
directions onto pixels. Without them, you cannot project a LiDAR point into the image at all.

They are measured with a checkerboard of known geometry, moved across the full field of view
and depth range until the calibrator's coverage bars fill
([calibration.md §3](../design/calibration.md#3-camera-intrinsics)). Verification is visual
and satisfying: rectify an image of the checkerboard, and straight board edges must appear
straight. Target reprojection error < ~0.3 px.

---

## Lab

**Goal:** record a rosbag while driving manually; replay it and overlay the LiDAR scan and
camera image; identify obstacles.

**You need:** a vehicle with sensors mounted (or an instructor-provided bag), ROS 2 Humble,
RViz.

### Part 1 — Bring up the sensors and look at them

```bash
ros2 launch mrider bringup.launch.py

ros2 topic hz /scan
ros2 topic hz /camera/color/image_raw
ros2 topic echo /scan --once | head -40    # note angle_min, angle_max, range_max
```

In RViz, add **LaserScan** (`/scan`), **Image** (`/camera/color/image_raw`), and **TF**. Set
the fixed frame to `base_link`.

**Answer these from the data, not the datasheet:**

| Question | Value |
|---|---|
| LiDAR angular range | *(read from `/scan`)* |
| LiDAR angular resolution | *(compute)* |
| LiDAR max usable range in this room | *(observe)* |
| Camera resolution and fps | *(read)* |
| Camera horizontal FOV, estimated | *(estimate from a known object)* |

### Part 2 — Find the blind spots

1. Place a **low obstacle** (a book on the floor) in front of the vehicle. Does it appear in
   `/scan`? In the image?
2. Place a **tall thin obstacle** (a chair leg) at increasing distance. At what range does it
   stop being reliably detected?
3. Try a **dark, matte** surface and a **glass or polished** surface. Compare LiDAR returns.
4. Turn the room lights off. Which sensor still works?

Record what each sensor missed. This table is the most useful thing you will produce today:

| Obstacle | Seen by LiDAR? | Seen by camera? | Why |
|---|---|---|---|
| Book on floor | | | |
| Chair leg at 1 m / 3 m / 6 m | | | |
| Dark matte surface | | | |
| Glass / polished surface | | | |
| Everything, lights off | | | |

### Part 3 — Record a bag

```bash
ros2 bag record -o m4_run \
  /scan /camera/color/image_raw /mrider/feedback /tf /tf_static \
  /fmu/out/sensor_combined
```

Drive the course manually (M3 rules: wheels-on only under the M3 protocol, operator alongside,
walking pace). Include at least one pass by each obstacle from Part 2.

```bash
ros2 bag play m4_run --loop
ros2 bag info m4_run
```

!!! tip "Always record `/tf` and `/tf_static`"

    A bag without transforms is nearly useless — you have sensor data with no way to relate it
    to the vehicle. This is the most common rosbag mistake, and you only discover it after the
    vehicle has been put away.

### Part 4 — Overlay LiDAR on the camera image

Write a node that subscribes to `/scan` and the image, transforms each LiDAR point into the
camera frame using TF, projects it with the camera intrinsics, and draws it on the image.

```python
# Sketch -- the pieces you need:
#   tf_buffer.lookup_transform('camera_link', scan.header.frame_id, scan.header.stamp)
#   convert each (range, angle) to a 3D point in the laser frame
#   transform into camera frame, then project with fx, fy, cx, cy from CameraInfo
#   skip points with z <= 0 (behind the camera) and points outside the image
```

**Verification:** points must land on the corresponding structure. If they are consistently
offset, your extrinsics are wrong — go fix them rather than adding a fudge factor.

### Part 5 — Break the extrinsics on purpose

Deliberately add **5° of yaw error** to the LiDAR extrinsic and re-run the overlay.

- How obvious is the error when the vehicle is stationary?
- How obvious when it turns?
- Predict what this would do to a SLAM map. (M5 will let you check.)

### Expected output

- The FOV/rate table filled from measurements
- The blind-spot table, with at least one surprise
- A rosbag containing `/tf` and `/tf_static`
- An overlay image where LiDAR points land on real structure
- A second overlay showing the effect of 5° of yaw error

### Check yourself

- [ ] Why does the BOM insist on a global shutter, in terms of M7's training labels?
- [ ] Name an obstacle class that a 2D LiDAR structurally cannot see, and say why.
- [ ] Why keep a drifting `odom` frame when SLAM knows better?
- [ ] Which is worse, 3 cm of translation error or 3° of yaw error? Justify it.
- [ ] Your overlay is offset by a constant amount in x. Extrinsics or intrinsics? How do you tell?

---

## Slide outline

1. **Hook** — two sensors, two blind spots. Show a photo where each one fails.
2. **Camera vs. LiDAR** — the comparison table
3. **The 2D plane problem** — one horizontal slice, and what falls outside it
4. **Global vs. rolling shutter** — skew correlated with turn rate
5. **Label leakage** — choosing a sensor by what it does to your training data
6. **Rates table** — and who consumes each stream
7. **REP-105 frames** — `map` → `odom` → `base_link` → sensors
8. **Why `odom` exists** — continuous vs. accurate
9. **Extrinsics** — translation error vs. rotation error, and why yaw is worst
10. **Wall-calibration procedure** — physical ground truth beats a tape measure
11. **Intrinsics in one slide** — checkerboard, coverage bars, rectification check
12. **Lab brief** — measure, find blind spots, record, overlay, break it
13. **Looking ahead** — M5: the vehicle sees; now let it know where it is

---

**Previous:** [M3 — Manual/teleop control & safety](m3-teleop-safety.md) · **Next:** [M5 — Localization & SLAM](m5-slam.md)
