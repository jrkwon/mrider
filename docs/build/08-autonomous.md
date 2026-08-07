# 8. Autonomous Bring-up (SLAM → Nav2 → Behavior Cloning)

**Goal:** progress from mapping to autonomous driving.

Build a map with slam_toolbox, navigate with Nav2, then collect driving data and run the
end-to-end behavior-cloning pipeline (mrover `neural_net/` lineage) for an autonomous lap.

- **Prerequisites:** Section 7 complete; a mapped test course.
- **Specification:** [design/software.md](../design/software.md), [design/sensors.md](../design/sensors.md)
- **Expected outcome:** a saved map, successful Nav2 goals, and an autonomous lap.

!!! warning "Draft — not yet validated on hardware"

    Derived from [software.md §4–§5](../design/software.md#4-slam-nav2-ekf-configuration-plan).
    No map has been built, no Nav2 goal executed, and no policy trained on MRider. Nav2
    parameter values, dataset sizes, and training hyperparameters are marked
    *(measure during bring-up)* or *(record)*.

!!! danger "Autonomy does not remove the operator"

    Every rule from [step 7](07-manual-drive.md) still applies: operator on the RC
    transmitter, spotter on the E-stop, ≤ walking speed, clear area sized by the measured
    coast-down distance. The RC transmitter preempts autonomy through PX4 — that is the
    entire reason the datapath was pinned through PX4 in the first place. **Autonomy is the
    lowest authority in the stack** ([safety.md §1.3](../design/safety.md#13-authority-priority-highest-wins)).

---

## 8.1 Order of operations

Each phase gates the next, and each is separately abortable:

| Phase | You get | Gate |
|---|---|---|
| A — [Mapping](#82-phase-a-slam-mapping) | A saved map of the test course | Map closes; no drift artifacts |
| B — [Localization](#83-phase-b-localization-on-the-saved-map) | Repeatable pose on the saved map | Pose stable, no jumps |
| C — [Nav2](#84-phase-c-nav2-goals) | Autonomous point-to-point goals | Goals reached without recovery spam |
| D — [Data collection](#85-phase-d-data-collection) | A behavior-cloning dataset | Balanced, correctly labeled |
| E — [Train & deploy](#86-phase-e-train-and-deploy-the-policy) | An autonomous lap | Lap completed under supervision |

## 8.2 Phase A — SLAM mapping

slam_toolbox is reused essentially as-is: `solver_plugin: CeresSolver`, `mode: mapping`,
`odom_frame: odom`, `map_frame: map`, `scan_topic: /scan`, `resolution: 0.05`,
`max_laser_range: 10.0`, `transform_publish_period: 0.02`
([software.md §4.2](../design/software.md#42-slam_toolbox-configslammapper_params_online_asyncyaml)).

!!! danger "Fix the frame mismatch before your first map"

    B-MROVER's slam config uses `base_frame: base_footprint` while the EKF uses `base_link`.
    If you skipped this correction in [step 5](05-software.md#58-re-parameterize-for-the-real-chassis),
    TF will be inconsistent and your map will be subtly, confusingly wrong. Reconcile to one
    convention — `base_link` throughout is recommended.

**Drive the map manually.** Use joystick teleop from step 7 — you are not navigating yet.

```bash
ros2 launch mrider bringup.launch.py
ros2 launch slam_toolbox online_async_launch.py \
  params_file:=$(ros2 pkg prefix mrover)/share/mrover/config/slam/mapper_params_online_async.yaml

rviz2   # add Map, LaserScan, TF displays
```

Mapping technique that matters on this vehicle:

- **Drive slowly and smoothly.** Scan matching degrades with fast rotation, and ±22.5° of
  steering means your turns are already wide.
- **Close loops deliberately.** Return to the start along a path you have already driven —
  loop closure is what corrects accumulated drift.
- **Watch the EKF, not just the map.** If `odom` → `base_link` is drifting badly, your
  odometry calibration or IMU alignment is wrong; fix that before blaming SLAM.

```bash
ros2 run nav2_map_server map_saver_cli -f config/maps/test_course
```

**Record sheet — mapping**

| Item | Value |
|---|---|
| Course dimensions | *(measure)* m × *(measure)* m |
| Map resolution | 0.05 m/cell |
| `max_laser_range` used | *(record)* m |
| Loop-closure error at start point | *(measure)* m |
| Mapping run duration | *(record)* |
| Artifact | `config/maps/test_course.{pgm,yaml}` |

**Gate:** the map closes, walls are single-thickness (not doubled — doubling means drift or
bad extrinsics), and the start point returns to itself.

## 8.3 Phase B — Localization on the saved map

Switch slam_toolbox `mode: localization` with the saved map for repeat runs. Drive the course
manually again and confirm the pose stays locked.

- [ ] Pose does not jump when the vehicle passes featureless stretches
- [ ] Pose recovers correctly after a deliberate re-start from a known point
- [ ] `map` → `odom` correction stays small and does not grow monotonically

A monotonically growing correction means odometry is biased — go back to
[odometry calibration](06-bench-test.md#66-drive-distance-ticksmeters).

## 8.4 Phase C — Nav2 goals

Nav2 is reused with the NavFn planner and B-MROVER's costmap layers, re-parameterized for the
real chassis ([software.md §4.3](../design/software.md#43-nav2-configslamnav2_paramsyaml)).

**Re-parameterize before the first goal:**

| Parameter | B-MROVER value | Your value | Why |
|---|---|---|---|
| `robot_radius` | 0.1397 | *(from step 2 dimensions)* | The real chassis is much larger |
| `max_vel_x` | 0.26 | *(cap at walking speed)* | Safety case is only valid ≤ walking speed |
| `max_vel_theta` | 1.0 | *(derive from ±22.5° limit)* | You cannot rotate faster than the steering allows |
| `max_vel_y` | 0.0 | 0.0 | Non-holonomic — keep at zero |

```bash
ros2 launch nav2_bringup navigation_launch.py \
  params_file:=config/slam/nav2_params.yaml map:=config/maps/test_course.yaml
```

Send a goal from RViz's **2D Goal Pose**, starting with a short straight-line goal and only
then progressing to goals requiring turns.

!!! note "Expect DWB to struggle, and know what to do about it"

    DWB is a diff-drive/omni-oriented local planner. On a true Ackermann vehicle with a
    ±22.5° steering limit, it can plan paths the vehicle physically cannot follow.
    [ADR-SW2](../design/software.md#adr-sw2-nav2-local-controller-for-ackermann) keeps DWB as
    the reused default for bring-up and **pre-registers Regulated Pure Pursuit as the swap**,
    with a concrete trigger: persistent path-tracking error or infeasible commands during
    turning tests. If you hit that trigger, swapping to RPP is the planned action, not a
    workaround.

**Record sheet — Nav2**

| Test | Result |
|---|---|
| Straight-line goal, 5 m | *(record)* |
| Goal requiring a single turn | *(record)* |
| Goal requiring reversing/recovery | *(record)* |
| Path-tracking error, worst case | *(measure)* m |
| Recovery behaviors triggered | *(count)* |
| Controller retained | DWB / swapped to RPP — *(record + why)* |

**Gate:** goals are reached without repeated recovery behaviors, and the vehicle never
commands a steering angle it cannot achieve.

## 8.5 Phase D — Data collection

The recorder is reused from B-MROVER with one retarget
([software.md §5.1](../design/software.md#51-data-collection)). It subscribes to a control
topic (the steering/throttle **label**), an odometry topic, and the camera image, and records
synchronized samples to `e2e_data`.

**The one required change:** `vehicle_control_topic` moves from `/rover` to
**`/mrider/feedback`** — the new steering-angle-labeled source — and `base_pose_topic` points
at the EKF odometry output.

```yaml title="config/data_collection/mrider.yaml"
vehicle_control_topic: /mrider/feedback      # was /rover
base_pose_topic:       /odometry/filtered
camera_image_topic:    /camera/color/image_raw
steering_angle_max:    22.5
```

```bash
ros2 launch mrider bringup.launch.py
ros2 run data_collection data_collection_main --ros-args --params-file config/data_collection/mrider.yaml
# then drive the course manually, well, repeatedly
```

!!! danger "You are recording your own driving as ground truth"

    Behavior cloning learns what you demonstrate, including your mistakes. Drive the racing
    line you actually want the policy to take. Sloppy demonstrations produce a sloppy policy,
    and no amount of training fixes a badly labeled dataset.

Collection guidance:

- **Both directions.** Drive the course clockwise and counter-clockwise, or the policy learns
  a steering bias.
- **Balance the label distribution.** A course that is mostly straight produces a dataset that
  is mostly zero-steering, and the policy will learn to drive straight through corners.
  Record extra cornering laps, or rebalance at training time.
- **Include recoveries.** Approach from slightly off-line and steer back. A policy trained
  only on perfect laps has never seen the state it will inevitably enter.
- **Fixed conditions.** Same lighting, same course layout. The global-shutter camera was
  specified precisely so turns do not smear the image relative to the steering label
  ([sensors.md §1](../design/sensors.md#1-front-camera)) — do not undermine it with a
  variable exposure that motion-blurs instead.

**Record sheet — dataset**

| Item | Value |
|---|---|
| Laps recorded (CW / CCW) | *(record)* / *(record)* |
| Total samples | *(record)* |
| Steering label distribution (straight / left / right) | *(record)* |
| Recovery samples included | *(record)* |
| Image resolution recorded | *(record)* |
| Lighting conditions | *(record)* |
| Dataset path | `e2e_data/<date>_<course>` |

## 8.6 Phase E — Train and deploy the policy

The Keras pipeline is reused verbatim
([software.md §5.2](../design/software.md#52-end-to-end-model)). `neural_net/net_model.py`
provides `model_ce491` — the classic PilotNet architecture (Conv 24→36→48→64→64 with a
normalization `Lambda x/127.5−1.0`, then Dense 100→50→10→`num_outputs`) — plus
`model_agribot` and `model_jaerock` variants and a ResNet inference path.

Default config: `num_outputs: 1` (steering; optionally throttle), input image 160×160×3,
selectable `network_type`.

```bash
python neural_net/train.py --data e2e_data/<date>_<course> \
  --config config/neural_net/mrider.yaml
```

**Record sheet — training**

| Item | Value |
|---|---|
| `network_type` | *(record)* |
| `num_outputs` | 1 (steering) / 2 (+ throttle) — *(record)* |
| Input image size | 160×160×3 |
| Train/validation split | *(record)* |
| Epochs | *(record)* |
| Final validation loss | *(record)* |
| Weights artifact | *(record path)* |

**Deploy for inference.** The policy publishes to `/mrider/cmd` → command shim →
`ManualControlSetpoint` — **the exact same datapath as Nav2 and teleop**. The learned policy
gets no special privileges and no shortcut to the motors.

```bash
ros2 run run_neural run_neural --ros-args -p weights:=<path>
```

!!! danger "First autonomous lap protocol"

    Treat it exactly like the first manual drive:

    1. Operator on the RC transmitter, **thumb on the sticks**, not in a pocket
    2. Spotter's hand on the E-stop
    3. Clear area sized by the coast-down distance measured in [step 7](07-manual-drive.md#75-phase-2-e-stop-under-motion)
    4. Software speed cap still at walking pace
    5. **Abort on the first surprise.** A policy that mis-steers once will mis-steer again,
       and the second time it will be faster.

Progress in this order: **straight segment → single corner → half lap → full lap.** Do not
jump to a full lap because the straight worked.

**Record sheet — autonomous lap**

| Attempt | Segment | Interventions | Outcome |
|---|---|---|---|
| 1 | straight | *(count)* | *(record)* |
| 2 | single corner | *(count)* | *(record)* |
| 3 | half lap | *(count)* | *(record)* |
| 4 | full lap | *(count)* | *(record)* |

**Success criterion:** one full lap, zero interventions, repeatable across at least three
consecutive attempts. One lucky lap is not a working policy.

## 8.7 If it does not work

| Symptom | Likely cause | Where to look |
|---|---|---|
| Policy drives straight through corners | Label distribution dominated by straights | [Phase D](#85-phase-d-data-collection) balance |
| Policy oscillates left/right on straights | Overfit, or noisy steering labels | Check `steer_deg` noise from [step 6](06-bench-test.md); more data |
| Policy works one direction only | Trained on one course direction | Record the other direction |
| Nav2 paths the vehicle cannot follow | DWB vs. Ackermann | Swap to RPP — [ADR-SW2](../design/software.md#adr-sw2-nav2-local-controller-for-ackermann) |
| Map doubles walls | Odometry drift or bad extrinsics | [Odometry](06-bench-test.md#66-drive-distance-ticksmeters) and [extrinsics](06-bench-test.md#68-extrinsics-sensors-base_link) |
| Pose jumps during localization | Featureless stretches, or LiDAR range too short | `max_laser_range`; add features to the course |
| Steering label does not match image | Time-sync error | [calibration.md §6](../design/calibration.md#6-laptoppixhawk-time-synchronization) |

## 8.8 You are done — now write it down

The build is complete. The most valuable remaining artifact is the record of what actually
happened, because every *(measure during bring-up)* placeholder in this guide is a question
that only your build can answer.

- [ ] All calibration artifacts committed under `config/calibration/` with full stamps
- [ ] Map and Nav2 parameters committed
- [ ] Dataset and trained weights archived with their config
- [ ] **This guide updated** — replace the placeholders with your measured values, remove the
      Draft banners from pages you have now validated, and correct anything that was wrong
- [ ] Open a pull request. The edit link at the top of every page goes straight to the source.

A build guide written from designs is a hypothesis. Yours is the first evidence.

---

**Previous:** [7. Manual drive](07-manual-drive.md) · **Back to:** [Build guide overview](index.md) · **See also:** [Learn curriculum](../learn/index.md)
