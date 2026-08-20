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
| **Local controller** | Follow that route, avoiding what appears in real time | `RegulatedPurePursuitController`, `allow_reversing: true` |
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

### ADR-SW2 — CLOSED 2026-08-09: RPP + SmacPlannerHybrid

!!! success "This decision is settled. Here is how it was reached."

    ADR-SW2 originally read *"DWB now, RPP pre-registered with a trigger."* It closed on
    **2026-08-09**, and the outcome is more interesting than the original plan:
    **DWB and NavFn were both dropped without a trial run**, rejected on geometry rather than
    on measurement.

**The reasoning.** DWB (Dynamic Window Approach) is a diff-drive/omni-oriented local planner. It
samples a velocity space that, at R_min = 1.52 m, is *mostly unreachable* for this vehicle — most
of what it evaluates, the car cannot execute. NavFn is worse in a subtler way: it plans **as though
the robot were a free-turning point**, so it routinely returns paths that are undrivable by
construction. In testing, the controller rejected them mid-follow with `detected collision ahead!`
on geometry that was never feasible in the first place.

No amount of controller tuning fixes a path the vehicle cannot drive.

**What runs now:**

| Role | Plugin | Key parameter |
|---|---|---|
| Global planner | `nav2_smac_planner/SmacPlannerHybrid` | `motion_model_for_search: REEDS_SHEPP`, `minimum_turning_radius: 1.6` |
| Local controller | `RegulatedPurePursuitController` | `min_turning_radius: 1.6`, `allow_reversing: true` |

SmacPlannerHybrid searches in **(x, y, heading)** rather than (x, y), with Reeds-Shepp curves
bounded by the turning radius. It cannot produce a path the car cannot drive, because
undrivable paths are not in its search space.

!!! info "The two changes only work together"

    `allow_reversing: true` was **inert** before the planner swap. RPP only reverses where the
    *path* reverses, and NavFn never produced such a path. Enabling reversing on the controller
    while keeping a planner that cannot express a reversing manoeuvre changes nothing at all.

    This is worth internalising: a parameter that is switched on but has no effect looks exactly
    like a parameter that is working.

**Verified.** An 8.98 m traverse succeeded, stopping 0.44 m from the goal. Then the decisive test:
a goal **2.5 m directly behind** the vehicle — geometrically impossible forward-only at a 1.6 m
turning radius. The vehicle reversed 2.1 m in a straight line, heading unchanged at ~3°, and
arrived 0.40 m from the goal. **Before the swap, that manoeuvre had no solution at all.**

### Reverse is expensive, not free

`reverse_penalty: 2.5` makes reversing a last resort rather than a normal option. There is a
hardware reason, and it is the best example in this course of the simulator earning its keep:

!!! danger "The vehicle has no rear sensing"

    The LiDAR faces forward. There is no rear camera and no rear bumper. Autonomous reverse is
    therefore **blind**, relying entirely on costmap memory of what was seen while driving in.

    In simulation that is free. On the real vehicle it is not.

    **The twin surfaced a hardware requirement before the vehicle existed.** Track B must choose
    one of: add rear sensing, hard-cap reverse distance and speed in firmware, or forbid
    autonomous reverse on hardware. Until that is decided, autonomous reverse on the real car is
    **unproven and must not be enabled by inheriting this configuration unchanged.**

!!! warning "Both radius parameters are derived from unmeasured numbers"

    `minimum_turning_radius` (planner) and `min_turning_radius` (controller) both come from
    `0.63 / tan(22.5°) = 1.52 m`. **Neither the wheelbase nor the steering limit has been
    measured.** When they are, both parameters must be re-derived together.

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

    Nav2 driving does not change the M3 rules. The RC transmitter preempts it through both
    override layers — including the hardware MUX, which does not depend on firmware.
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

### Part 4 — Measure what the closed decision bought

```bash
ros2 topic echo /local_plan
ros2 topic echo /mitt/dbw/command          # what is actually being commanded?
ros2 topic echo /mitt/dbw/status     # what is actually being achieved?
```

| Metric | Value |
|---|---|
| Worst-case cross-track error | *(measure)* m |
| Number of times a steering angle beyond ±22.5° was commanded | *(count)* |
| Recovery behaviors triggered | *(count)* |
| `spin` recoveries that accomplished nothing | *(count)* |

**ADR-SW2 is closed, so this is verification rather than a decision.** If cross-track error is persistent or infeasible commands appear
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
- [ ] Why were DWB and NavFn rejected on geometry rather than after a trial run?
- [ ] Why was `allow_reversing: true` inert until the planner was swapped?
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
8. **ADR-SW2 (closed)** — RPP + SmacPlannerHybrid; why DWB and NavFn were rejected on geometry
9. **What a good decision looks like** — naming the evidence that would change your mind
10. **Regulated Pure Pursuit** — lookahead, curvature, speed regulation
11. **Lab brief** — compute constraints first, then five goals
12. **Looking ahead** — M7: instead of planning, just imitate a driver

---

**Previous:** [M5 — Localization & SLAM](m5-slam.md) · **Next:** [M7 — Behavior cloning](m7-behavior-cloning.md)
