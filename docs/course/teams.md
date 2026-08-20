# Teams & Tracks

From Week 6, the class splits into **four teams of six**, each owning one subsystem of MRider. Over
Weeks 11–14 those subsystems merge, one pair at a time, into a working vehicle.

!!! success "Every track's deliverable is something that does not exist yet"

    These are not exercises. Each track owns a genuine hole in the repository — named in the design
    documents, blocking a named acceptance gate. When the semester ends, MRider is further along
    because of what you built, and the git history says who built it.

---

## How teams are assigned

| | |
|---|---|
| **9/28 (W4)** | Preference form handed out |
| **10/9 (Fri)** | Preference form due |
| **10/12 (W6)** | Teams announced; charter workshop in class |
| **10/19 (W7)** | Team charters due |

Assignment is **by the instructor**, from your ranked preferences plus observed Lab 1–4 work. You
will usually get your first or second choice.

It is not self-selection, and the reason is worth stating plainly: left to themselves, the strongest
programmers concentrate on the Software track and the Chassis track ends up under-resourced. Chassis
owns the measurements that **every other track is blocked on**. That cannot be the team that got
whoever was left over.

### Preference form

Submit by **Friday 10/9**:

1. **Rank all four tracks**, 1 (most wanted) to 4.
2. **What relevant experience do you have?** Soldering, machining, CAD, embedded C/C++, Python,
   Linux, testing, CI, ML — anything. Being a complete beginner in every one is a perfectly
   acceptable answer and does not disadvantage you.
3. **What do you most want to be able to do by December?** One or two sentences.
4. **Anyone you would work well with?** Optional, not guaranteed, but considered.

---

## The four tracks

### E — Electrical & Firmware

**Owns:** the Teensy 4.1, micro-ROS, the Sabertooth motor driver, the relay MUX, the RC signal MUX,
and the emergency stop.

You write the code that turns a ROS 2 message into motion, and — more importantly — the code that
guarantees a human can always take the vehicle back.

| Deliverable | Today |
|---|---|
| `firmware/` — the Teensy DBW controller | **Does not exist.** No firmware in this repository at all |
| `DbwCommand` / `DbwStatus` actually flowing over micro-ROS | The message types are defined and built, but **nothing publishes or subscribes to them** |
| The failsafe matrix, demonstrated wheels-off | Specified in [safety.md](../design/safety.md), never executed |
| [Build step 4](../build/04-firmware.md) validated | Draft, never run on hardware |

**Acceptance gates you close:** `/mitt/dbw/status` sustains ≥ 50 Hz · zero USB dropouts over 30
minutes · both override layers demonstrated.

**Good fit if** you like embedded work, or want to. C++ on a microcontroller; no prior experience
assumed, but the track has the steepest early ramp.

**Read first:** [dbw.md §10–12](../design/dbw.md) · [safety.md](../design/safety.md) ·
[M2](../learn/m2-dbw-steering.md) · [M3](../learn/m3-teleop-safety.md)

---

### C — Chassis & Measurement

**Owns:** the physical vehicle. Teardown, the steering gearmotor mount, the load-side angle sensor,
the drive encoder, the equipment plate, and the sensor mast.

And — this is the part that matters most — **the numbers.**

| Deliverable | Today |
|---|---|
| A **measured** `mitt_dimensions.yaml` | Every value in it is `TODO measure`. The file's own header says: *"NOTHING IN THIS FILE HAS BEEN MEASURED"* |
| Measurement gates M1, M2, M3 | Steering torque, sensor shaft travel, shaft diameter — all blocking |
| [Build step 2](../build/02-mechanical.md) validated | Draft, never run |
| Calibration constants recorded | [calibration.md](../design/calibration.md) specifies the procedure |

!!! warning "This track's output is everyone else's input"

    The simulator currently runs on estimates derived from a vendor's marketing dimensions. Until
    Chassis measures the real car, **the twin is fiction that happens to be plausible.** Software
    cannot tune Nav2 for real geometry and Simulation cannot claim sim-to-real agreement until these
    numbers land.

**Good fit if** you like working with your hands, or want a track where careful, honest measurement —
not code volume — is the skill being graded.

**Read first:** [vehicle.md §3](../design/vehicle.md) · [calibration.md](../design/calibration.md) ·
[build step 2](../build/02-mechanical.md)

---

### S — Simulation & Validation

**Owns:** the simulated world, simulation fidelity, the test infrastructure, and CI.

You are the track that decides whether anyone else's claim is true.

| Deliverable | Today |
|---|---|
| A parametric world matching the **real** test hallway | Only the stock warehouse world exists |
| `mitt_bench` — the acceptance measurement scripts | **Does not exist.** Referenced by three documents |
| Functional and launch tests | The repository has **29 tests and all 29 are linters.** Nothing tests that the URDF loads or that any launch file comes up |
| ROS build and test in CI | CI currently builds **documentation only** |
| Sim/real agreement within 10% | An acceptance gate with no measurement behind it yet |

!!! quote "The gap this track exists to close"

    `mitt_controllers.yaml` carries the comment *"mitt_bringup checks the two agree at launch."*
    **No such check exists.** Finding and closing gaps like that one is this track's actual job.

**Good fit if** you like testing, tooling, automation, or being the person who finds the thing
everyone else assumed was fine. Highest leverage track in the course, and the least glamorous.

**Read first:** [software.md §8](../design/software.md) · [run-the-twin.md](../run-the-twin.md) ·
[M6](../learn/m6-nav2.md)

---

### W — Software & Autonomy

**Owns:** the ROS 2 stack that runs on the real vehicle.

| Deliverable | Today |
|---|---|
| `mitt_hardware` — the real `ros2_control` plugin | **Does not exist.** This is the single most important missing piece: it is what makes one launch file drive both sim and hardware |
| The odometry node (bicycle model from `DbwStatus`) | **Does not exist** |
| A perception package | The camera is bridged into ROS and **nothing consumes it** |
| An RViz configuration | None ships; the runbook borrows Nav2's |
| Nav2 retuned for measured geometry | Currently tuned for estimated geometry |

!!! info "Why `mitt_hardware` is the keystone"

    [ADR-SW4](../design/software.md) commits to one property: *the identical control stack runs in
    simulation and on hardware, differing only in one plugin.* That plugin is `mitt_hardware`.
    Without it, the twin is a demo. With it, the twin is a test rig. Merge 3 exists to prove it.

**Good fit if** you want the deepest ROS 2 work. Most code, most C++, and the track most dependent on
other teams delivering on time.

**Read first:** [software.md §2–4](../design/software.md) ·
[architecture.md](../design/architecture.md) · [M4](../learn/m4-perception.md) ·
[M5](../learn/m5-slam.md)

---

## The merge ladder

Subsystems do not merge all at once at the end. They merge in pairs, and **each merge is a live
demonstration of a specific claim** — not a meeting, not a status update.

| Week | Date | Merge | The claim it proves |
|---|---|---|---|
| **11** | 11/16 | **E + C** | The vehicle steers to a commanded angle under firmware control, wheels off the ground. Closes bring-up Stage 1: ≤ 1° steady-state error, no sustained oscillation |
| **12** | 11/23 | **S + W** | The twin runs *measured* geometry and the functional test suite is green in CI |
| **13** | 11/30 | **(E+C) + W** | `mitt_hardware` talks to the real Teensy. **The ADR-SW4 gate:** the identical teleop launch runs in sim and on hardware, differing only in the plugin |
| **14** | 12/07 | **all four** | Full stack on the vehicle — teleop, then a hallway map, then a Nav2 goal |
| **15** | 12/14 | — | Measured against the acceptance gates in [software.md §8](../design/software.md) |

!!! danger "A merge date cannot slip"

    A merge that does not happen on its date blocks three other teams. This is why the schedule
    front-loads: Merge 1 is in Week 11 and full integration is Week 14, leaving Week 15 entirely for
    the things that go wrong. They will.

    If your track is going to miss a merge, say so **at the Week 10 standup**, not on the day.
    Announcing a slip early is professional. Discovering it at the merge is not.

---

## Team charters

Due **Week 7 (10/19)**. One page, committed to the repository at
`docs/course/charters/<track>.md`. It contains:

1. **Who owns what.** Every deliverable in your track table, with a name against it. Not "the team
   will" — a person.
2. **Your definition of done.** For each deliverable, the observable evidence that it works. "The
   encoder is mounted" is not evidence. "The encoder reports monotonic counts through a full
   steering sweep, logged, plotted, committed" is.
3. **What you need from other tracks, and by when.** This is the dependency contract. Software needs
   measured geometry from Chassis; put a date on it.
4. **Your risks.** Two or three things that could stop you, and what you would do instead.

The charter is a working document. Update it when reality changes — that is not failure, it is the
point. An unchanged charter in Week 14 means nobody was reading it.

---

## Peer evaluation

Runs twice: **Week 8** and **Week 15**. Confidential; only I see individual responses.

For each teammate including yourself, on a 1–5 scale:

1. **Contribution** — did they deliver what they owned?
2. **Reliability** — could the team depend on their commitments?
3. **Collaboration** — did they make the team work better?

Plus, in free text: *what did this person do that the git history would not show me?* Documentation,
debugging someone else's problem, and asking the question that saved a week are all real work that
leaves no commit.

**Effect on grade:** peer evaluation can adjust your personal team-component grade by up to **±15%**.
Consistent, evidenced under-contribution can reduce it further.

!!! note "If your team has a problem"

    Tell me at Week 8, not Week 15. At Week 8 there are seven weeks left and it is fixable. At Week
    15 there is nothing I can do but adjust grades, which helps nobody build anything.

---

## See also

- [Syllabus](syllabus.md) — the full 16-week schedule
- [Grading & Rubrics](grading.md) — how team deliverables are assessed
- [Design overview](../design/overview.md) — the document index every track reads from
- [Build guide](../build/index.md) — the lab-infrastructure manual for the hardware tracks
