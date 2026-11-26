# Teams & Tracks

From Week 6, the class splits into **three teams, and each team builds its own vehicle**: team *N*
builds vehicle *N*. A vehicle is four subsystems, called **tracks** here, and every team carries all
four. Over Weeks 11–14 a team's four tracks merge, one pair at a time, into its working vehicle.

Thirteen students in three teams is four or five to a team, so **a track inside a team is one or two
people**, not a group.

> [!TIP]
> **Every track's deliverable is something that does not exist yet**
>
> These are not exercises. Each track owns a genuine hole in the repository — named in the design
> documents, blocking a named acceptance gate. When the semester ends, MRider is further along
> because of what you built, and the git history says who built it.

---

## How teams are assigned

| | |
|---|---|
| **10/05 (W4)** | Preference form handed out |
| **10/16 (Fri)** | Preference form due |
| **10/19 (W6)** | Teams announced; charter workshop in class |
| **10/26 (W7)** | Team charters due |

Assignment — your team, and your track inside it — is **by the instructor**, from your ranked
preferences plus observed Lab 1–4 work. You will usually get your first or second choice of track.

It is not self-selection, and the reason is worth stating plainly: left to themselves, the strongest
programmers concentrate on the Software track and the Chassis track ends up under-resourced, and the
same happens between teams. Chassis owns the measurements that **every other track is blocked on**.
That cannot go to whoever was left over, and no team can be the one without it.

### Preference form

Submit by **Friday 10/16**:

1. **Rank all four tracks**, 1 (most wanted) to 4.
2. **What relevant experience do you have?** Soldering, machining, CAD, embedded C/C++, Python,
   Linux, testing, CI, ML — anything. Being a complete beginner in every one is a perfectly
   acceptable answer and does not disadvantage you.
3. **What do you most want to be able to do by December?** One or two sentences.
4. **Anyone you would work well with?** Optional, not guaranteed, but considered.

---

## The four tracks

Every team has all four. The tables below say what each track owns **on your team's vehicle**; the
person or pair holding a track answers for it to the rest of the team.

### E — Electrical & Firmware

**Owns:** the Teensy 4.1, micro-ROS, the MDDS30 motor driver, the relay MUX, the RC signal MUX,
and the emergency stop.

You write the code that turns a ROS 2 message into motion, and — more importantly — the code that
guarantees a human can always take the vehicle back.

| Deliverable | Today |
|---|---|
| `firmware/` — the Teensy DBW controller | **Does not exist.** No firmware in this repository at all |
| `DbwCommand` / `DbwStatus` actually flowing over micro-ROS | The message types are defined and built, but **nothing publishes or subscribes to them** |
| The failsafe matrix, demonstrated wheels-off | Specified in [safety.md](../design/safety.md), never executed |
| The IMU published from the Teensy — `/imu/data`, ≥ 100 Hz | **Does not exist.** Added 2026-11-16, when the IMU moved onto the Teensy's second I²C bus ([sensors.md §3](../design/sensors.md#3-imu)) |
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
| A **measured** `config/vehicles/vehicle<n>.yaml` — your vehicle's numbers, laid over the estimates | **Empty.** Every value the stack runs on is still an estimate from `mitt_dimensions.yaml`, whose own header says: *"NOTHING IN THIS FILE HAS BEEN MEASURED"* |
| Verification gates V1, V2, V3 | Steering-motor stall current, sensor shaft travel, shaft diameter — all blocking. *(V1's torque question closed 2026-10-01: the vehicle's rated 25 kg occupant load already demonstrates the margin.)* |
| [Build step 2](../build/02-mechanical.md) validated | Draft, never run |
| Calibration constants recorded | [calibration.md](../design/calibration.md) specifies the procedure |

> [!WARNING]
> **This track's output is everyone else's input**
>
> The simulator currently runs on estimates derived from a vendor's marketing dimensions. Until
> Chassis measures the real car, **the twin is fiction that happens to be plausible.** Software
> cannot tune Nav2 for real geometry and Simulation cannot claim sim-to-real agreement until these
> numbers land.

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

> **The gap this track exists to close**
>
> `mitt_controllers.yaml` carries the comment *"mitt_bringup checks the two agree at launch."*
> **No such check exists.** Finding and closing gaps like that one is this track's actual job.

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

> [!NOTE]
> **Why `mitt_hardware` is the keystone**
>
> [ADR-SW4](../design/software.md) commits to one property: *the identical control stack runs in
> simulation and on hardware, differing only in one plugin.* That plugin is `mitt_hardware`.
> Without it, the twin is a demo. With it, the twin is a test rig. Merge 3 exists to prove it.

**Good fit if** you want the deepest ROS 2 work. Most code, most C++, and the track most dependent on
the other tracks delivering on time.

**Read first:** [software.md §2–4](../design/software.md) ·
[architecture.md](../design/architecture.md) · [M4](../learn/m4-perception.md) ·
[M5](../learn/m5-slam.md)

---

## The merge ladder

Subsystems do not merge all at once at the end. Inside each team they merge in pairs, and **each
merge is a live demonstration of a specific claim** on that team's vehicle — not a meeting, not a
status update. All three teams merge on the same dates.

| Week | Date | Merge | The claim it proves |
|---|---|---|---|
| **11** | 11/23 | **E + C** | The vehicle steers to a commanded angle under firmware control, wheels off the ground. Closes bring-up Stage 1: ≤ 1° steady-state error, no sustained oscillation |
| **12** | 11/30 | **S + W** | The twin runs *measured* geometry and the functional test suite is green in CI. Shown inside the [mid-semester presentation](grading.md#mid-semester-presentation-15) |
| **13** | 12/07 | **(E+C) + W** | `mitt_hardware` talks to the real Teensy. **The ADR-SW4 gate:** the identical teleop launch runs in sim and on hardware, differing only in the plugin |
| **14** | 12/14 | **all four** | Full stack on the vehicle — teleop, then a hallway map, then a Nav2 goal. Then measured against the acceptance gates in [software.md §8](../design/software.md) |
| **15** | 12/21 | — | **★ Final demo and presentations** |

> [!CAUTION]
> **A merge date cannot slip**
>
> A merge that does not happen on its date blocks the other three tracks of your own team. Merge 1 is in Week 11 and full
> integration is Week 14, which leaves exactly **one week** before the demo — and Week 14 is already
> carrying validation against the acceptance gates.
>
> Be clear-eyed about that: this schedule has no dedicated buffer week. Adding the Week 0 on-ramp
> cost it. So a merge that slips does not eat slack, it eats demo preparation.
>
> If your track is going to miss a merge, say so **at the Week 10 standup**, not on the day.
> Announcing a slip early is professional. Discovering it at the merge is not.

---

## Where your work lives

Three teams write the same deliverables. `firmware/` is one path, `mitt_hardware` is one package,
and three teams cannot each fill it on the same `main`. So the repository is split along the line
that is actually there: **numbers that differ per vehicle** go to `main` now, and **code** stays in
your team's fork until the semester ends.

*Decided 2026-11-17.*

### 1. One fork per team — all your code goes there

Your team works in **one fork** of [`jrkwon/mrider`](https://github.com/jrkwon/mrider), at the same
paths this repository uses: `firmware/`, `ros2_ws/src/mitt_hardware/`, `ros2_ws/src/mitt_bench/`,
your final report. Every member commits there, under their own name. **Your fork's history is what is
graded** — both the deliverables and the individual commit record.

How to set it up:

- **One member creates the fork**, normally the team lead, and invites every other member as a
  collaborator with **Write** access (*Settings → Collaborators*). Send me the fork's URL.
- **Nobody makes a second fork.** Members clone the team fork and push branches to it. A personal
  fork of the team fork scatters the history that is graded.
- **Do not squash-merge.** A squashed pull request records whoever pressed the button as the
  author, and the commits of the person who did the work are gone. Use a merge commit or a rebase.
- **Commit as yourself.** Check `git config user.name` and `git config user.email` on every machine
  you commit from, and that the email is one your GitHub account knows. On a shared laptop, set
  them per clone or pass `--author`, or one person ends up with everyone's work.
- **Fork, do not copy.** Use GitHub's *Fork* button, so the repository stays public and
  `git merge upstream/main` keeps working. A new repository with the files copied in has neither.

Keep the fork current. `main` keeps moving, and a fork that falls behind stops building against the
interfaces below:

```bash
git remote add upstream https://github.com/jrkwon/mrider.git   # once
git fetch upstream
git merge upstream/main                                        # every week, and before every merge demo
```

### 2. Interfaces change on `main`, never in a fork

Three implementations stay interchangeable only while they agree on what crosses between them. These
are **frozen in your fork**:

| Interface | Where it is defined |
|---|---|
| Message types — `mitt_msgs` | `ros2_ws/src/mitt_msgs/` |
| Topic names, rates, frames | [software.md §3.1](../design/software.md#31-topic-interface-contract), [§3.3](../design/software.md#33-tf-tree) |
| Teensy pin assignments | [build step 4](../build/04-firmware.md) |
| ROS domain, vehicle *N* → 10 + *N* | [software.md §3.4](../design/software.md#34-ros-domain-one-per-vehicle) |
| Key names in `mitt_dimensions.yaml` | `ros2_ws/src/mitt_description/config/` |
| Arguments of `sim.launch.py`, `real.launch.py` and `nav2.launch.py` | `ros2_ws/src/mitt_bringup/launch/`, `ros2_ws/src/mitt_navigation/launch/` |

If one of them is wrong or missing something — and some will be; none of this has met hardware —
**open a pull request against `main`** that changes the interface and says why. When it is merged,
all three teams pull it. Changing it only in your fork means your vehicle works and nobody else's
code runs on it.

### 3. Your vehicle's numbers go to `main` as you measure them

`mitt_dimensions.yaml` stays what it is: the estimates every vehicle starts from. What your team
has **measured** goes in an overlay,

```
ros2_ws/src/mitt_description/config/vehicles/vehicle<n>.yaml
```

where a key replaces the estimate for your vehicle only, and a key you have not written is still an
estimate. Measured values only — no `TODO` lives in that file.

This is the **one file of yours that lands on `main` during the semester.** Open a pull request
from your fork that touches that file and nothing else, with how each value was measured in a
comment beside it. `python3 scripts/check_vehicle_dims.py` must pass.

It is used by naming the vehicle:

```bash
ros2 launch mitt_bringup sim.launch.py vehicle:=<n>     # the twin of YOUR vehicle
ros2 launch mitt_bringup real.launch.py vehicle:=<n>    # the vehicle itself
```

Both hand the URDF and the controller your measured geometry — checked in the twin on 2026-11-17;
`real.launch.py` cannot run until `mitt_hardware` exists. `vehicle:=0`, the twin's default, is
the estimates.

### 4. After the final demo, one implementation of each deliverable is merged

`main` ends the semester with one `firmware/`, one `mitt_hardware`, one `mitt_bench`. For each
deliverable the implementation with the strongest acceptance-gate evidence is merged from its
team's fork, **with its commit history**, so the record of who built it stays.

Which one is merged is not a grade. Your grade comes from your own fork and your own vehicle.

> [!NOTE]
> **Why the interfaces are worth the trouble**
>
> If all three teams hold the same pin table, the same messages and the same domain rule, then one
> team's firmware runs on another team's vehicle. That is the strongest reproducibility test this
> course has — *could another team rebuild this from what you wrote down* — and it only exists
> because nobody changed an interface privately.

---

## Team charters

> [!NOTE]
> **The charter is not collected and not graded** *(decided 2026-11-26)*
>
> The vehicles arrived late and the weeks since have gone to integration. A charter written now
> would describe decisions already made. What it was for is covered elsewhere: **Functionality** in
> the [Team deliverable](grading.md#team-deliverable-25) is read against the
> [track tables](#the-four-tracks) above, and section 1 of the [final report](final-report.md) is
> where your team says what it set out to build and what it gave up.
>
> The four points below are still the right questions to have answered inside your team.

Planned for **Week 7 (10/26)**: one page per team at `docs/course/charters/vehicle<n>.md`,
containing:

1. **Who owns what.** Every deliverable in all four track tables, with a name against it. Not "the
   team will" — a person.
2. **Your definition of done.** For each deliverable, the observable evidence that it works. "The
   encoder is mounted" is not evidence. "The encoder reports monotonic counts through a full
   steering sweep, logged, plotted, committed" is.
3. **What each track needs from the others, and by when.** This is the dependency contract, and it
   is inside your own team. Software needs measured geometry from Chassis; put a date on it.
4. **Your risks.** Two or three things that could stop you, and what you would do instead.

A team that wrote one can keep it in its fork and cite it in the final report.

---

## Peer evaluation

Runs twice: **Week 12** and **Week 14**. *(The first was planned for Week 8 and moved with the
mid-semester presentation, 2026-11-20.)* Confidential; only I see individual responses.

For each teammate including yourself, on a 1–5 scale:

1. **Contribution** — did they deliver what they owned?
2. **Reliability** — could the team depend on their commitments?
3. **Collaboration** — did they make the team work better?

Plus, in free text: *what did this person do that the git history would not show me?* Documentation,
debugging someone else's problem, and asking the question that saved a week are all real work that
leaves no commit.

### Effect on grade

*Decided 2026-11-20.*

- **Only the Team deliverable (25%) is adjusted**, by up to **±15%** of your share of it. The
  mid-semester presentation and the final demo are graded per team and stay as they are.
- **Only the Week 14 evaluation adjusts a grade.** The Week 12 one is a check: it tells me, and
  through me your team, where something is going wrong while there are weeks left to fix it.
- **How the number is computed.** Your score is the mean of what your teammates gave you; your own
  rating of yourself is not in it. That score divided by your team's mean is your ratio. A ratio
  between **0.90 and 1.10 changes nothing**, because four or five people cannot measure a
  difference that small. Outside that band the ratio is your multiplier, limited to 0.85–1.15.
- **No multiplier is applied on numbers alone.** I read it against the free text, your fork's
  commit history and the standups before using it.

Consistent, evidenced under-contribution can reduce it further.

> [!NOTE]
> **If your team has a problem**
>
> Tell me now, not at Week 15. While there are weeks left it is fixable. At Week
> 15 there is nothing I can do but adjust grades, which helps nobody build anything.

---

## See also

- [Syllabus](syllabus.md) — the full 16-week schedule
- [Grading & Rubrics](grading.md) — how team deliverables are assessed
- [Design overview](../design/overview.md) — the document index every track reads from
- [Build guide](../build/index.md) — the lab-infrastructure manual for the hardware tracks
