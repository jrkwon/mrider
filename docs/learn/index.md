# MRider Learn Curriculum

A RoboRacer-style coursekit that teaches autonomous-vehicle fundamentals on the MRider
platform. The modules run **in order**: each builds on the previous one, from a first ROS 2
node to an autonomous lap. Every module lists its learning objectives, a hands-on lab, and
the design document that grounds the theory in the real vehicle.

**Audience:** upper-year undergraduates and early graduate students, or self-learners with
some Python. **Format:** short lecture + guided lab per module. **Prerequisites for the
course:** basic Python and Linux; no robotics background assumed.

!!! info "What state this curriculum is in"

    Lecture notes, labs, and slide outlines are written. Modules **M1** and **M4–M8** are
    hardware-independent enough to teach or self-study now — several can be run against
    recorded data or simulation. **M2** and **M3** include bench-rig labs that have not yet
    been run on a physical MRider; those pages carry a Draft banner.

    Slides are provided as **outlines**, not as binary decks — an instructor builds the deck
    from the outline in whatever tool their institution uses.

## The eight modules

| # | Module | You learn | Design reference |
|---|---|---|---|
| M1 | [Intro to MRider & ROS 2](m1-ros2-intro.md) | What drive-by-wire is; ROS 2 nodes, topics, TF | [architecture.md](../design/architecture.md) |
| M2 | [Drive-by-wire & the smart-servo loop](m2-dbw-steering.md) | Closed-loop position control on a real actuator | [dbw.md](../design/dbw.md) |
| M3 | [Manual/teleop control & safety](m3-teleop-safety.md) | Control authority, failsafes, E-stop semantics | [safety.md](../design/safety.md) |
| M4 | [Perception](m4-perception.md) | Camera and 2D LiDAR sensing, frames, extrinsics | [sensors.md](../design/sensors.md) |
| M5 | [Localization & SLAM](m5-slam.md) | Odometry, EKF fusion, mapping, drift diagnosis | [calibration.md](../design/calibration.md) |
| M6 | [Navigation (Nav2)](m6-nav2.md) | Costmaps, planners, controllers for a car-like robot | [software.md](../design/software.md) |
| M7 | [Behavior cloning](m7-behavior-cloning.md) | Imitation learning end-to-end; modular vs. learned | [software.md](../design/software.md) |
| M8 | [Capstone: autonomous lap](m8-capstone.md) | Integration, debugging, and presenting results | [architecture.md](../design/architecture.md) |

## How the course is structured

Each module follows the same shape, so students and instructors always know where they are:

- **Learning objectives** — what you should be able to *do* afterwards, not just recognize.
- **Lecture** — the concepts, grounded in MRider's actual design decisions rather than
  generic robotics theory.
- **Lab** — a hands-on exercise with setup, steps, expected output, and a check-yourself list.
- **Slide outline** — a deck skeleton for the instructor.
- **Reference** — the design document that specifies what the module teaches.

## Why teach on this vehicle

Most robotics courses teach on a simulator or a small differential-drive robot. MRider is a
**car** — non-holonomic, Ackermann-steered, limited to ±22.5° at the road wheels — which
makes several things concrete that are otherwise abstract:

- **A steering angle is a real thing you must measure.** M2's absolute sensor and position
  loop exist because [ADR B](../design/dbw.md#5-adr-b-steering-angle-encoding) rejected the
  simpler incremental approach for a documented, arguable reason. Students read the argument.
- **Safety is designed, not assumed.** M3 works through a real failsafe matrix and FMEA for a
  vehicle that can hurt someone — not a thought experiment.
- **Odometry is wrong, and you learn why.** M5 confronts the fact that only one motor shaft of
  a paralleled pair is instrumented
  ([ADR C](../design/dbw.md#8-adr-c-drive-distance-encoding)), so the EKF is a necessity
  rather than a formality.
- **Planners can demand impossible things.** M6 meets the ±22.5° turn constraint that makes
  a diff-drive-oriented local planner produce infeasible paths
  ([ADR-SW2](../design/software.md#adr-sw2-nav2-local-controller-for-ackermann)).

Every module points at a design document containing a real decision with alternatives and
consequences. That is the pedagogical asset: students are not told *what* the system does,
they are shown *why it was chosen over the alternative*.

## For instructors

- **Modules are ~1 lecture + ~1 lab each**, so the set fits a quarter or a half-semester with
  room for the capstone.
- **M1, M4, M5, M6, M7 can run without a completed vehicle** using recorded rosbags,
  simulation, or a shared demo rig. **M2 and M3 want the bench rig**; M8 wants a vehicle.
- **The [build guide](../build/index.md) is the lab-infrastructure manual.** If your students
  are building the vehicle as part of the course, build steps 1–8 interleave naturally with
  modules M1–M8.
- **Safety is not optional in M3 and beyond.** The bring-up protocol
  ([safety.md §6](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first)) is staged
  specifically so a class can proceed without an instructor supervising every action
  individually.

---

## See also

- [Design overview & document index](../design/overview.md)
- [Build guide](../build/index.md)
