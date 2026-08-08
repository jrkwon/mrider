# M7 — Behavior Cloning / End-to-End Driving

!!! warning "Partially superseded (2026-08-07)"

    Some references on this page still assume the **Pixhawk + Arduino Nano** topology, replaced
    by a **single Teensy 4.1 running micro-ROS**
    ([decision D3](../design/adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07)).
    The substance of this page is unaffected; treat the [design set](../design/overview.md) as
    authoritative where they disagree.


**Learning objectives:**

- Understand imitation learning and end-to-end driving (mrover `neural_net/` lineage).
- Collect and curate a driving dataset; train and evaluate a model.
- Compare modular (Nav2) vs. learned (end-to-end) control.

**Reference:** [design/software.md](../design/software.md)

---

## Lecture

### Two philosophies of driving

M6 built a **modular** pipeline: perceive → localize → map → plan → control. Each stage has a
defined interface, each is separately testable, each failure is separately diagnosable.

**End-to-end** replaces the whole chain with one function:

```
camera image  ──▶  [ neural network ]  ──▶  steering angle
```

No map. No planner. No costmap. The network learns the mapping directly from examples of a
human driving.

| | Modular (Nav2) | End-to-end |
|---|---|---|
| Needs a map | Yes | No |
| Goes to an arbitrary goal | Yes | No — it drives *the road it learned* |
| Debuggable | Per stage | Barely — one opaque function |
| Handles novel situations | Via explicit planning | Only if similar examples were seen |
| Engineering effort | High: many configs | Low: collect, train, deploy |
| Data required | None | A lot, and it must be good |

Neither is "better." They fail differently, and M8 lets students choose.

### Imitation learning, and its central weakness

**Behavior cloning** is supervised learning where the input is a sensor observation and the
label is what the human did. Collect (image, steering) pairs, fit a network, deploy.

The weakness follows directly from the setup: the network only ever saw states a *good* driver
visits. The moment it drifts slightly off-line — as it will, since it is imperfect — it is in
a state that never appeared in training. Its output there is unconstrained, which pushes it
further off-line, which is even further out of distribution.

This compounding is the classic failure of naive behavior cloning, and the practical mitigation
is in the data: **deliberately record recoveries.** Approach the line from slightly off and
steer back. A policy that has only seen perfect laps has never seen the state it will
inevitably enter.

### The pipeline MRider reuses

Nearly verbatim from B-MROVER
([software.md §5](../design/software.md#5-data-collection-end-to-end-nn-pipeline)):

```
/camera/color/image_raw  ─┐
/mrider/feedback (label) ─┼─▶ data_collection_main.py ─▶ e2e_data
EKF odometry             ─┘                                 │
                                                            ▼
                                          neural_net/train.py (PilotNet)
                                                            │
                                                            ▼
                                                  trained weights
                                                            │
                                                            ▼
                                     run_neural.py ─▶ /mrider/cmd ─▶ command shim
```

**The one MRider change:** the recorder's `vehicle_control_topic` moves from `/rover` to
**`/mrider/feedback`** — the new steering-angle-labeled source from
[ADR-SW1](../design/software.md#adr-sw1-one-transport-one-clock-typed-messages) — and `base_pose_topic`
points at the EKF odometry output.

!!! info "The learned policy gets no special privileges"

    Inference output goes to `/mrider/cmd` → command shim → `ManualControlSetpoint` — **the
    exact same datapath as Nav2 and as your joystick**. The network cannot reach the motors
    any more directly than a human can, and the RC transmitter still preempts it through PX4.
    Single pinned datapath, again paying off.

### The model

`neural_net/net_model.py` provides `model_ce491`, the classic **PilotNet** architecture:

```
Lambda(x / 127.5 − 1.0)          # normalization
Conv 24 → 36 → 48 → 64 → 64
Dense 100 → 50 → 10 → num_outputs
```

Input is 160×160×3; `num_outputs: 1` predicts steering (optionally 2, adding throttle).
Variants `model_agribot` and `model_jaerock` exist, plus a ResNet inference path.

It is a small network by modern standards, and that is appropriate — the task is narrow, the
dataset is small, and it must run in real time on the onboard laptop.

### Your label is the absolute steering angle

The steering label comes from `steer_deg` in the Nano's feedback frame — the **absolute column
sensor** reading from M2, not the commanded value.

That distinction matters. The label is what the wheels **actually did**, including the position
loop's tracking error and any mechanical lag. Training on the *command* would teach the network
to reproduce commands that the vehicle does not actually follow.

!!! danger "Time sync is a silent killer here"

    If images and steering labels are misaligned in time, you are training the network to
    predict what the driver did **half a second ago**. It will still converge — the loss goes
    down, the plots look fine — and the resulting policy will consistently turn late.

    MRider's answer: the **laptop is the single authoritative clock**; Nano frames are stamped
    on receipt; PX4 timestamps are offset-corrected in the bridge; `use_sim_time=false`
    ([calibration.md §6](../design/calibration.md#6-time-synchronization)).

### Dataset problems, in order of how often they bite

1. **Label imbalance.** A course that is mostly straight yields a dataset that is mostly
   zero-steering. Minimizing average error then means predicting ≈0 everywhere — a policy that
   drives straight through corners *and has low training loss*.
2. **Directional bias.** Drive the course one way only and the network learns that turns go
   left. Record both directions.
3. **No recoveries.** Covered above.
4. **Inconsistent conditions.** Different lighting between sessions teaches the network to key
   on brightness rather than road geometry.
5. **Sloppy demonstrations.** The policy learns exactly what you demonstrated, including your
   mistakes. There is no training trick that fixes badly labeled data.

---

## Lab

**Goal:** collect data on a course, train a behavior-cloning model, and deploy it for
inference; measure lap completion.

**Prerequisites:** M3 safety protocol, an M5 course, and a working manual drive.

### Part 1 — Collect

```yaml title="config/data_collection/mrider.yaml"
vehicle_control_topic: /mrider/feedback      # NOT /rover
base_pose_topic:       /odometry/filtered
camera_image_topic:    /camera/color/image_raw
steering_angle_max:    22.5
```

```bash
ros2 launch mrider bringup.launch.py
ros2 run data_collection data_collection_main \
  --ros-args --params-file config/data_collection/mrider.yaml
```

Then drive — **well**, and a lot.

- Both directions, roughly equal lap counts
- Extra cornering laps to fight label imbalance
- Deliberate recovery runs: start off-line, steer back
- Consistent lighting

| Item | Value |
|---|---|
| Laps clockwise / counter-clockwise | *(record)* / *(record)* |
| Total samples | *(record)* |
| Recovery runs included | *(record)* |
| Lighting conditions | *(record)* |

### Part 2 — Look at your data before you train

**Plot the steering-label histogram.** Do this before any training. It is the single most
informative five minutes in this lab.

```python
# Sketch:
#   load the steering labels from e2e_data
#   plt.hist(labels, bins=41)
#   report: fraction within +/-2 deg of zero, and left/right balance
```

| Metric | Value | Concern if… |
|---|---|---|
| Fraction of samples within ±2° of zero | *(measure)* % | > ~70% — heavily straight-biased |
| Left/right balance | *(measure)* | Far from 1:1 — directional bias |
| Samples in the outer third of the range | *(measure)* % | Very low — sharp turns underrepresented |

Also **spot-check alignment**: pick ten random samples, look at the image, and predict the
label yourself. If your guess and the stored label disagree systematically, you have a
time-sync problem — go back to M5/M6 before burning GPU time.

### Part 3 — Train

```bash
python neural_net/train.py --data e2e_data/<date>_<course> \
  --config config/neural_net/mrider.yaml
```

| Item | Value |
|---|---|
| `network_type` | *(record)* |
| `num_outputs` | 1 (steering) / 2 (+ throttle) |
| Train/validation split | *(record)* |
| Epochs | *(record)* |
| Final training loss | *(record)* |
| Final validation loss | *(record)* |

!!! note "Low loss is not a working policy"

    A network that always outputs 0° scores well on a straight-heavy dataset. **Always check
    predictions against a held-out set that includes corners**, not just the aggregate loss.
    Plot predicted vs. actual steering across the validation set; the interesting region is the
    tails, not the middle.

### Part 4 — Deploy

```bash
ros2 run run_neural run_neural --ros-args -p weights:=<path>
```

!!! danger "First autonomous run: same protocol as the first manual drive"

    Operator with **thumbs on the RC sticks**, spotter's hand on the E-stop, clear area sized
    by the coast-down distance measured in M3, software speed cap at walking pace. **Abort on
    the first surprise** — a policy that mis-steers once will mis-steer again, faster.

Progress: **straight segment → single corner → half lap → full lap.** Do not jump to a full
lap because the straight worked.

| Attempt | Segment | Interventions | Outcome |
|---|---|---|---|
| 1 | straight | | |
| 2 | single corner | | |
| 3 | half lap | | |
| 4 | full lap | | |

### Part 5 — Compare against Nav2

Run the **same course** under M6's Nav2 stack and under your policy.

| Metric | Nav2 | Learned policy |
|---|---|---|
| Lap completed | | |
| Lap time | | |
| Interventions | | |
| Worst deviation from the intended line | | |
| Setup effort (be honest) | | |
| What it does in a situation it has not seen | | |

The last row is the interesting one, and it is worth engineering a test for: move a cone onto
the course. Nav2 replans around it. The policy has never seen it.

### Expected output

- A label histogram, with imbalance identified before training
- Training and validation loss, plus a predicted-vs-actual plot on held-out corners
- A deployment log with the four progressive attempts
- A filled comparison table with a written paragraph on when you would choose each approach

### Check yourself

- [ ] Why does the label come from the absolute sensor rather than the commanded angle?
- [ ] Your dataset is 80% near-zero steering. Predict the trained policy's behavior at corners.
- [ ] What does a 200 ms image/label misalignment do, and why won't the loss curve reveal it?
- [ ] Why must the policy publish to `/mrider/cmd` rather than driving the Nano directly?
- [ ] Name one situation where end-to-end clearly beats Nav2, and one where it clearly loses.

---

## Slide outline

1. **Hook** — same course, two philosophies. Show the block diagrams side by side.
2. **Modular vs. end-to-end** — the comparison table
3. **Behavior cloning in one slide** — (observation, action) pairs, supervised learning
4. **The compounding-error problem** — drift off-line → out of distribution → drift more
5. **Recovery data as the mitigation**
6. **The MRider pipeline** — collect, train, infer, and the one retargeted topic
7. **No special privileges** — the policy uses the same datapath as your joystick
8. **PilotNet** — the architecture in five lines
9. **The label is what the wheels did** — not what was asked
10. **Time sync, the silent killer** — loss goes down, policy turns late
11. **Five dataset problems**, ordered by frequency
12. **Low loss ≠ working policy** — the always-predict-zero trap
13. **Lab brief** — collect, inspect, train, deploy, compare
14. **Looking ahead** — M8: pick a stack and prove a lap

---

**Previous:** [M6 — Navigation (Nav2)](m6-nav2.md) · **Next:** [M8 — Capstone: autonomous lap](m8-capstone.md)
