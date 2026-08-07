# M6 — Navigation (Nav2)

**Learning objectives:**

- Understand the Nav2 stack: costmaps, planners, and controllers.
- Configure Ackermann-appropriate parameters (wheelbase, track, steer range).
- Send navigation goals and tune for a car-like platform.

**Reference:** [design/software.md](../design/software.md)

---

## Lecture

### The stack, top to bottom

Nav2 turns "go to that pose" into a stream of velocity commands. Four pieces:

| Piece | Job | MRider's choice |
|---|---|---|
| **Costmaps** | Represent where it is safe to be — static map, live obstacles, inflation | Reused from B-MROVER, `robot_radius` re-parameterized |
| **Global planner** | Find a route from here to the goal across the whole map | `NavfnPlanner` — reused |
| **Local controller** | Follow that route, avoiding what appears in real time | `DWBLocalPlanner` — reused for bring-up, **flagged for replacement** |
| **Recoveries** | What to do when stuck | `spin` / `back_up` / `wait` — reused, and problematic here |

The **inflation layer** is worth dwelling on: obstacles are grown by roughly the robot radius
so the planner can treat the robot as a point. Set `robot_radius` too small and you plan paths
that clip walls; too large and you cannot fit through a doorway you physically fit through.

B-MROVER's value is `0.1397` — which is a *simulation* placeholder, not MRider's chassis
([software.md §4.3](../design/software.md#43-nav2-configslamnav2_paramsyaml)). MRider is a
two-seater ride-on. Using the inherited value would let the planner drive you into a wall with
complete confidence.

### The parameters you must change before the first goal

| Parameter | B-MROVER value | What MRider needs | Why |
|---|---|---|---|
| `robot_radius` | 0.1397 | Measured from the real chassis | It is a much bigger vehicle |
| `max_vel_x` | 0.26 | Capped at walking speed | The [safety case](../design/safety.md#43-why-traction-cut-freewheel-steering-is-acceptable) only holds at walking speed |
| `max_vel_theta` | 1.0 | Derived from the ±22.5° steer limit and wheelbase | You cannot rotate faster than the steering permits |
| `max_vel_y` | 0.0 | 0.0 — keep it | Non-holonomic; sideways motion is impossible |

Also required from M5's measurements: `wheelbase`, track, and wheel radius, which set the
bicycle-steering controller
([software.md §3.2](../design/software.md#32-ackermann-kinematic-parameters)).

!!! danger "Every dimension you inherited is a placeholder"

    B-MROVER's URDF mixes a simulation chassis (`chassis_length = 1.3 m`) with a controller
    `wheelbase = 0.325 m`. Those are simulation artifacts, not measurements of anything. The
    design doc says it plainly: treat **all** dimensions as placeholders until measured. The
    one value consistent across three independent files — the **±22.5° steering range** — is
    the only inherited number adopted as a design target.

### Non-holonomic is the whole lesson

A differential-drive robot can spin in place and translate in any direction it is facing. Most
Nav2 tutorials assume one. **MRider cannot do either.**

It is **non-holonomic**: it can only move along its heading, and it can only change heading by
moving. And its steering is limited to **±22.5°** at the road wheels, which sets a **minimum
turning radius**:

```
R_min ≈ wheelbase / tan(22.5°) ≈ wheelbase / 0.414 ≈ 2.4 × wheelbase
```

So a vehicle with a 0.8 m wheelbase needs roughly a 2 m radius to turn — a 4 m diameter circle.
That is a large fraction of a classroom.

Three consequences students meet immediately:

1. **A plan the vehicle cannot follow.** A path with a tighter curve than `R_min` is
   geometrically infeasible, no matter how good the controller is.
2. **In-place rotation is impossible.** The `spin` recovery behavior — Nav2's standard answer
   to being stuck — cannot execute. It will be commanded, and nothing will happen.
3. **Reversing matters.** Multi-point turns are how a car gets out of tight spots. A planner
   that never reverses will declare failure where a human driver would simply back up.

### ADR-SW2 — DWB now, RPP pre-registered

DWB (Dynamic Window Approach) is a diff-drive/omni-oriented local planner. It samples velocity
commands including ones MRider structurally cannot execute.

MRider keeps it anyway for first bring-up — and this is a deliberate, documented decision
([ADR-SW2](../design/software.md#adr-sw2-nav2-local-controller-for-ackermann)):

- **Decision.** Start with B-MROVER's DWB (maximum reuse), evaluate **Regulated Pure Pursuit**
  as a swap once basic navigation works.
- **Rationale.** Reuse-first for bring-up velocity. But the ±22.5° constraint is real and may
  make DWB paths infeasible — so RPP is pre-registered as the fallback **with a concrete
  trigger**: path-tracking error or infeasible commands during turning tests.

!!! info "This is what a good engineering decision looks like"

    Not "use the right tool" and not "use what we have," but: *use what we have, having already
    decided what evidence would change our minds, and having named the replacement.* When you
    hit the trigger in the lab, swapping to RPP is the **planned action**, not a workaround or
    an admission of failure.

Regulated Pure Pursuit is curvature-aware: it picks a lookahead point on the path and computes
the steering that arcs toward it, regulating speed by curvature. That maps naturally onto a
car.

---

## Lab

**Goal:** set navigation goals on a saved map and have MRider drive to them; tune the
controller to reduce overshoot on turns.

**Prerequisites:** a saved map from M5, and the M3 safety protocol in force — operator on the
RC transmitter, spotter on the E-stop, walking pace, clear area.

!!! danger "Autonomy is the lowest authority in the ladder"

    Nav2 driving does not change the M3 rules. The RC transmitter preempts it through PX4.
    Nobody stands in the planned path to "see what it does."

### Part 1 — Compute your constraints before you configure

Do the arithmetic first; it tells you what is even possible in your test space.

| Quantity | Value |
|---|---|
| Wheelbase (from M5 / build step 2) | *(measure)* m |
| Steering limit | ±22.5° |
| **Minimum turning radius** `R_min = wheelbase / tan(22.5°)` | *(compute)* m |
| Minimum turning **diameter** | *(compute)* m |
| Your test area's smallest dimension | *(measure)* m |
| Can the vehicle turn around in it? | *(answer honestly)* |

**If the answer is no**, that is not a lab failure — it is the most important result of the
day, and it constrains every goal you set.

### Part 2 — Parameterize honestly

Edit `nav2_params.yaml`:

```yaml
robot_radius: <measured, not 0.1397>
max_vel_x: <walking speed cap>
max_vel_theta: <derived from R_min and max_vel_x>
max_vel_y: 0.0
```

Record what you set and why. `max_vel_theta` in particular should be **derived**, not guessed:
at speed `v` on a circle of radius `R_min`, the yaw rate is `v / R_min`.

### Part 3 — Progressive goals

Send goals from RViz's **2D Goal Pose**, in this order. Do not skip ahead.

| # | Goal | What it tests | Result |
|---|---|---|---|
| 1 | Straight ahead, 5 m | Basic tracking, speed limits | |
| 2 | 5 m ahead, rotated 45° in place | Whether the controller demands the impossible | |
| 3 | Around one corner | Curvature feasibility | |
| 4 | Somewhere requiring a turn tighter than `R_min` | The failure mode you predicted in Part 1 | |
| 5 | A goal behind the vehicle | Reversing / multi-point turn behavior | |

Goal 2 is the instructive one. A diff-drive robot spins in place and is done. Watch what
MRider is *commanded* to do versus what it *can* do.

### Part 4 — Measure, then decide about RPP

```bash
ros2 topic echo /local_plan
ros2 topic echo /mrider/cmd          # what is actually being commanded?
ros2 topic echo /mrider/feedback     # what is actually being achieved?
```

| Metric | Value |
|---|---|
| Worst-case cross-track error | *(measure)* m |
| Number of times a steering angle beyond ±22.5° was commanded | *(count)* |
| Recovery behaviors triggered | *(count)* |
| `spin` recoveries that accomplished nothing | *(count)* |

**Apply ADR-SW2's trigger.** If cross-track error is persistent or infeasible commands appear
during turning tests, swap the controller to Regulated Pure Pursuit and re-run goals 1–5.

| Metric | DWB | RPP |
|---|---|---|
| Goals reached (of 5) | | |
| Worst cross-track error | | |
| Infeasible commands | | |
| Recoveries triggered | | |

Record which controller you retained **and why** — that decision, with evidence, is the
deliverable.

### Part 5 — Tune overshoot on turns

Overshoot on a car-like vehicle usually is not a gain problem. Work through these in order:

1. Is the commanded curvature within `R_min`? If not, no tuning fixes it.
2. Is `max_vel_x` too high for the turn radius? Slow down and re-run.
3. Is the lookahead distance (RPP) too long? Long lookahead cuts corners; short lookahead
   oscillates.
4. Only now, adjust controller gains.

### Expected output

- `R_min` computed and compared against your test area
- All five goals attempted with outcomes recorded
- A quantitative DWB-vs-RPP comparison, if the trigger fired
- A stated, evidenced controller decision
- Turn overshoot reduced, with the cause identified rather than tuned around

### Check yourself

- [ ] Compute `R_min` for a 1.0 m wheelbase at ±22.5°. Does it fit in your lab?
- [ ] Why can Nav2's `spin` recovery never work on MRider?
- [ ] Why was DWB kept for bring-up despite being a poor kinematic fit?
- [ ] What specific evidence triggers the swap to RPP? Did you see it?
- [ ] `robot_radius` is left at 0.1397 on a two-seater ride-on. Describe the first crash.

---

## Slide outline

1. **Hook** — a Nav2 tutorial robot spins in place. Ours cannot. Everything follows from that.
2. **The four pieces** — costmap, global planner, local controller, recoveries
3. **Inflation and `robot_radius`** — too small vs. too big
4. **The inherited-placeholder trap** — 0.1397 on a two-seater
5. **Non-holonomic** — move along heading, turn only while moving
6. **`R_min = wheelbase / tan(22.5°)`** — do the arithmetic on screen
7. **Three consequences** — infeasible paths, no in-place spin, reversing matters
8. **ADR-SW2** — DWB now, RPP pre-registered with a trigger
9. **What a good decision looks like** — naming the evidence that would change your mind
10. **Regulated Pure Pursuit** — lookahead, curvature, speed regulation
11. **Lab brief** — compute constraints first, then five goals
12. **Looking ahead** — M7: instead of planning, just imitate a driver

---

**Previous:** [M5 — Localization & SLAM](m5-slam.md) · **Next:** [M7 — Behavior cloning](m7-behavior-cloning.md)
