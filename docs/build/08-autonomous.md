# 8. Autonomous Bring-up (SLAM → Nav2 → Behavior Cloning)

**Goal:** progress from mapping to autonomous driving.

Build a map with slam_toolbox, navigate with Nav2, then collect driving data and run the
end-to-end behavior-cloning pipeline (mrover `neural_net/` lineage) for an autonomous lap.

- **Prerequisites:** Section 7 complete; a mapped test course.
- **Specification:** [design/software.md](../design/software.md), [design/sensors.md](../design/sensors.md)
- **Expected outcome:** a saved map, successful Nav2 goals, and an autonomous lap.

> [!WARNING]
> **Draft — not yet validated on hardware**
>
> Derived from [software.md §4–§5](../design/software.md#4-slam-nav2-ekf-configuration-plan).
> No map has been built, no Nav2 goal executed, and no policy trained on MRider. Every
> reference in this page is therefore a **fixed value, a target, or the B-MROVER number you
> are being told not to copy** — never a measurement from this vehicle. [Reference and Yours](index.md#reference-and-yours).

> [!CAUTION]
> **Autonomy does not remove the operator**
>
> Every rule from [step 7](07-manual-drive.md) still applies: operator on the RC
> transmitter, spotter on the E-stop, ≤ walking speed, clear area sized by the measured
> coast-down distance. The RC transmitter preempts autonomy through both override layers —
> including the hardware signal MUX, which works even if the controller is hung. **Autonomy is the
> lowest authority in the stack** ([safety.md §1.3](../design/safety.md#13-authority-priority-highest-wins)).

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

> [!NOTE]
> **One base frame, already**
>
> B-MROVER's slam config used `base_frame: base_footprint` while its EKF used `base_link`.
> `mitt_navigation/config/slam_toolbox.yaml` says `base_link`, as the EKF does, so there is
> nothing to reconcile here. If a map comes out subtly wrong, check that nobody has put
> `base_footprint` back.

**Drive the map manually.** Use joystick teleop from step 7 — you are not navigating yet.

```bash
MITT_VEHICLE=<n> source ros2_ws/setup_env.sh            # every terminal
ros2 launch mitt_bringup real.launch.py vehicle:=<n>
ros2 launch mitt_navigation slam.launch.py use_sim_time:=false

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

**Record sheet — mapping** · [how to read the Reference column](index.md#reference-and-yours)

| Item | Reference | Yours | Why that reference |
|---|---|---|---|
| Course dimensions | — *(your course)* | m × m | Decides which goals are reachable: a turn needs more than twice the turning radius of clear floor |
| Map resolution | **0.05 m/cell** *(fixed)* | | Changing it invalidates the costmap tuning that follows |
| `max_laser_range` used | — *(your LiDAR)* | m | Record it: a map made at a different range will not localize the same |
| Loop-closure error at start point | — *(gate: the map closes)* | m | Doubled walls mean drift or bad extrinsics, not a tuning problem |
| Mapping run duration | — *(your run)* | | |
| Artifact | `config/maps/test_course.{pgm,yaml}` | | |

**Gate:** the map closes, walls are single-thickness (not doubled — doubling means drift or
bad extrinsics), and the start point returns to itself.

## 8.3 Phase B — Localization on the saved map

For repeat runs, stop `slam.launch.py` and localize on the saved map with AMCL. Both publish
`map` → `odom`, so never run the two together.

```bash
ros2 launch mitt_navigation localization.launch.py use_sim_time:=false \
  map:=/absolute/path/to/test_course.yaml
```

`map:=` must be an absolute path. AMCL does not assume where the vehicle is: give it a
**2D Pose Estimate** in RViz first, and **before you start Nav2**. Until AMCL has a pose there is no
`map` frame, and Nav2's bring-up waits for it without reporting an error
([software.md §4.8](../design/software.md#48-nav2-does-not-come-up-until-amcl-has-a-pose-result-2026-11-20)). Then drive the course manually again and confirm the pose
stays locked.

- [ ] Pose does not jump when the vehicle passes featureless stretches
- [ ] Pose recovers correctly after a deliberate re-start from a known point
- [ ] `map` → `odom` correction stays small and does not grow monotonically

A monotonically growing correction means odometry is biased — go back to
[odometry calibration](06-bench-test.md#66-drive-distance-ticksmeters).

## 8.4 Phase C — Nav2 goals

Nav2 runs from this repo's own launch file and parameter file, not B-MROVER's. The planner is
`SmacPlannerHybrid`, which plans inside the turning circle, and the controller is Regulated
Pure Pursuit. DWB and NavFn were dropped in the twin before any vehicle existed
([software.md §4.4–§4.5](../design/software.md#44-nav2-bring-up-in-the-twin-result-2026-08-08)).

**Three values are your vehicle's own, and you do not type any of them into Nav2.** They come from
your overlay, `mitt_description/config/vehicles/vehicle<n>.yaml`:

| Nav2 parameter | Comes from | Rule |
|---|---|---|
| `footprint` (local and global costmap) | wheelbase, track, wheel and chassis sizes | Outline of body and wheels, each edge rounded outward to 1 cm |
| `inflation_radius` (local and global costmap) | the footprint above | `base_link` to its farthest corner, rounded up to 5 cm — the planner does not check a corner that inflation does not reach |
| `minimum_turning_radius` (planner) | `min_turning_radius` | 5% above the measured radius, rounded up to 1 cm |

`nav2.launch.py vehicle:=<n>` writes a copy of `nav2_params.yaml` with those values and runs
Nav2 on the copy. **Do not edit `nav2_params.yaml` for your vehicle**: it holds the estimates,
and a check keeps it that way. Change the overlay and open a pull request with that one file
([teams.md](../course/teams.md)).

```bash
MITT_VEHICLE=<n> source ros2_ws/setup_env.sh            # every terminal
ros2 launch mitt_navigation nav2.launch.py vehicle:=<n> use_sim_time:=false
```

Start it after `real.launch.py` and after SLAM or localization, because Nav2 needs
`map` → `odom` to exist. On a real vehicle it refuses to start, with exit status 1 and one
line saying why, unless all three hold:

- [ ] `vehicle:=` is 1, 2 or 3
- [ ] `ROS_DOMAIN_ID` in this shell is 10 + `<n>`
- [ ] `vehicle<n>.yaml` has a **measured** `min_turning_radius`
      ([calibration.md §1.5](../design/calibration.md#15-minimum-turning-radius-measured-not-derived))

It also compares the body of the running robot with `vehicle:=<n>` and prints a block headed
`WRONG VEHICLE` if they differ. That is a warning, not a stop: read the first screen of output.

> [!CAUTION]
> **Autonomous reverse is unproven on a real vehicle**
>
> The committed parameters let the planner reverse (`motion_model_for_search: REEDS_SHEPP`,
> `allow_reversing: true`), and `nav2.launch.py` runs them on a real vehicle unchanged. The
> LiDAR scans 360° from the top of the mast, so a reverse segment is driven against a live
> costmap, but it has been driven **in the twin only**
> ([software.md §4.5](../design/software.md#45-planner-swap-to-smacplannerhybrid-resolved-2026-08-09)).
> Before the first reverse goal, check in RViz that `/scan` has returns **behind** the vehicle
> as built: a cable or a post beside the LiDAR leaves a sector with none. Then treat it as a
> first run: clear area behind, walking speed, operator's thumbs on the sticks. Nothing on the
> vehicle sees an obstacle lower than the scan plane, ahead or behind.

Send a goal from RViz's **2D Goal Pose**, starting with a short straight-line goal and only
then progressing to goals requiring turns. Pick goals with at least 1 m of clearance: the
footprint reaches about 0.8 m ahead of `base_link`.

> [!NOTE]
> **What recovery there is**
>
> The only recovery behavior is `wait`. `Spin` is absent because the vehicle cannot rotate in
> place, and `BackUp` because the trees were tested without it. A vehicle that noses into an obstacle is
> finished until the operator takes the RC sticks
> ([safety.md §1.2](../design/safety.md)). The goal tolerance is 0.6 m and 0.6 rad, so "reached"
> means within that, not on the point.

**Record sheet — Nav2**

| Test | Expected | Yours | Why that expectation |
|---|---|---|---|
| `minimum_turning_radius` Nav2 reports | **1.05 × your measured radius**, rounded up to 1 cm | m | `ros2 param get /planner_server GridBased.minimum_turning_radius`; anything else means the overlay was not used |
| Straight-line goal, 5 m | reaches it | | The simplest goal there is; a failure here is localization, not planning |
| Goal requiring a single turn | reaches it | | First goal the turning radius constrains; an undrivable path means the measured radius is too small |
| `/scan` returns behind the vehicle | **present over the whole rear half** | | An empty sector is an occlusion: the costmap there is never updated — see the caution above |
| First reverse segment | driven, operator on the sticks | m | Reverse has been driven in the twin only; yours is the first evidence |
| Path-tracking error, worst case | — *(your course)* | m | No reference: compare against your own earlier runs |
| Recoveries (`wait`) triggered | **as few as possible** | | Frequent recoveries mean the costmap or the footprint is wrong, not that Nav2 is working |

**Gate:** goals are reached without repeated recoveries, and the vehicle never
commands a steering angle it cannot achieve.

## 8.5 Phase D — Data collection

The recorder is reused from B-MROVER with one retarget
([software.md §5.1](../design/software.md#51-data-collection)). It subscribes to a control
topic (the steering/throttle **label**), an odometry topic, and the camera image, and records
synchronized samples to `e2e_data`.

**The one required change:** `vehicle_control_topic` moves from `/rover` to
**`/mitt/dbw/status`** — the absolute steering-angle-labeled source — and `base_pose_topic` points
at the EKF odometry output.

```yaml title="config/data_collection/mrider.yaml"
vehicle_control_topic: /mitt/dbw/status      # was /rover
base_pose_topic:       /odometry/filtered
camera_image_topic:    /camera/image_raw
steering_angle_max:    22.5
```

```bash
ros2 launch mitt_bringup real.launch.py vehicle:=<n>
ros2 run data_collection data_collection_main --ros-args --params-file config/data_collection/mrider.yaml
# then drive the course manually, well, repeatedly
```

> [!CAUTION]
> **You are recording your own driving as ground truth**
>
> Behavior cloning learns what you demonstrate, including your mistakes. Drive the racing
> line you actually want the policy to take. Sloppy demonstrations produce a sloppy policy,
> and no amount of training fixes a badly labeled dataset.

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

**Record sheet — dataset** · [how to read the Reference column](index.md#reference-and-yours)

| Item | Reference | Yours | Why that reference |
|---|---|---|---|
| Laps recorded (CW / CCW) | **balanced both ways** *(target)* | / | One direction only teaches the policy to turn one way — see §8.7 |
| Total samples | — *(your run)* | | |
| Steering label distribution (straight / left / right) | **not straight-dominated** *(target)* | | A straight-dominated set is the first symptom row in §8.7 |
| Recovery samples included | **yes** *(target)* | | Without them the policy cannot return from an error it has never seen |
| Image resolution recorded | **160×160×3** *(fixed)* | | What `model_ce491` expects; a mismatch fails at inference, not at training |
| Lighting conditions | — *(your run)* | | Record it: a policy trained at one lighting does not transfer silently |
| Dataset path | `e2e_data/<date>_<course>` | | |

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

**Record sheet — training** · [how to read the Reference column](index.md#reference-and-yours)

| Item | Reference | Yours | Why that reference |
|---|---|---|---|
| `network_type` | **`model_ce491`** *(reused verbatim)* | | PilotNet, from software.md §5.2 — substituting one is a deliberate choice to record |
| `num_outputs` | 1 (steering) | | 2 adds throttle; say which, because the deploy node has to agree |
| Input image size | **160×160×3** *(fixed)* | | Must equal the dataset row above |
| Train/validation split | — *(your run)* | | |
| Epochs | — *(your run)* | | |
| Final validation loss | — *(your run)* | | Compare against your own earlier runs; there is no cross-course reference |
| Weights artifact | — *(your path)* | | |

**Deploy for inference.** The policy drives `ros2_control` — **the exact same datapath as Nav2
and teleop**. The learned policy gets no special privileges and no shortcut to the motors.

```bash
ros2 run run_neural run_neural --ros-args -p weights:=<path>
```

> [!CAUTION]
> **First autonomous lap protocol**
>
> Treat it exactly like the first manual drive:
>
> 1. Operator on the RC transmitter, **thumb on the sticks**, not in a pocket
> 2. Spotter's hand on the E-stop
> 3. Clear area sized by the coast-down distance measured in [step 7](07-manual-drive.md#75-phase-2-e-stop-under-motion)
> 4. Software speed cap still at walking pace
> 5. **Abort on the first surprise.** A policy that mis-steers once will mis-steer again,
>    and the second time it will be faster.

Progress in this order: **straight segment → single corner → half lap → full lap.** Do not
jump to a full lap because the straight worked.

**Record sheet — autonomous lap** — *a worksheet: four attempts of increasing scope. The
success criterion below governs the set, not any single attempt.*

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
| Policy oscillates left/right on straights | Overfit, or noisy steering labels | Check `steering_angle` noise from [step 6](06-bench-test.md); more data |
| Policy works one direction only | Trained on one course direction | Record the other direction |
| Nav2 paths the vehicle cannot follow | Planner radius below the real turning radius | Re-measure both locks — [calibration.md §1.5](../design/calibration.md#15-minimum-turning-radius-measured-not-derived); record the larger in `vehicle<n>.yaml` |
| `nav2.launch.py will not start: …` | Vehicle number, ROS domain, or an unmeasured turning radius | The line names which — [Phase C](#84-phase-c-nav2-goals) |
| Nav2 never prints `Managed nodes are active`; `Timed out waiting for transform from base_link to map` repeats | AMCL has no initial pose, so there is no `map` frame. Or `ekf_node` has died: look for `process has died` in the localization terminal | Set the **2D Pose Estimate**; Nav2 finishes by itself in about 10 s. If the EKF died, relaunch localization — [software.md §4.8](../design/software.md#48-nav2-does-not-come-up-until-amcl-has-a-pose-result-2026-11-20) |
| `WRONG VEHICLE` in the Nav2 terminal | Nav2 and the robot were started with different `vehicle:=` | Stop Nav2; start it with the robot's number |
| Map doubles walls | Odometry drift or bad extrinsics | [Odometry](06-bench-test.md#66-drive-distance-ticksmeters) and [extrinsics](06-bench-test.md#68-extrinsics-sensors-base_link) |
| Pose jumps during localization | Featureless stretches, or LiDAR range too short | `max_laser_range`; add features to the course |
| Steering label does not match image | Time-sync error | [calibration.md §6](../design/calibration.md#6-time-synchronization) |

## 8.8 You are done — now write it down

The build is complete. The most valuable remaining artifact is the record of what actually
happened, because every blank **Yours** cell in this guide is a question that only your build
can answer — and for most of them, nobody has answered it yet at all.

- [ ] All calibration artifacts committed under `config/calibration/` with full stamps
- [ ] Map committed, and your measured values in `vehicle<n>.yaml` (Nav2 takes its numbers from there)
- [ ] Dataset and trained weights archived with their config
- [ ] **This guide updated** — replace the placeholders with your measured values, remove the
      Draft banners from pages you have now validated, and correct anything that was wrong
- [ ] Open a pull request. The edit link at the top of every page goes straight to the source.

A build guide written from designs is a hypothesis. Yours is the first evidence.

---

**Previous:** [7. Manual drive](07-manual-drive.md) · **Back to:** [Build guide overview](index.md) · **See also:** [Learn curriculum](../learn/index.md)
