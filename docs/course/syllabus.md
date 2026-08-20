# Syllabus — 자율주행미들웨어응용

**Autonomous Driving Middleware Applications**
Graduate course · Fall 2026 · Mondays, 3 hours · 24 students

| | |
|---|---|
| **Instructor** | Jaerock Kwon, PhD |
| **Contact** | jrkwon@umich.edu |
| **Meets** | Mondays, one 3-hour block |
| **First class** | **Monday, September 7, 2026** |
| **Last class** | **Monday, December 21, 2026** |
| **Language** | English — lectures, materials, and all submitted work |
| **Platform** | [MRider / MITT](../index.md) — a drive-by-wire research vehicle |
| **Software** | ROS 2 Humble · Ubuntu 22.04 · Gazebo Harmonic |

---

## What this course is

Most robotics courses teach middleware on a simulator or a small differential-drive robot, using
exercises invented for the course. This one does not.

You will learn ROS 2 by **finishing a real vehicle**. MRider is a 12 V ride-on car being converted
into a drive-by-wire autonomous platform. Its digital twin already drives, maps, and navigates. Its
design is fully documented, with every significant decision recorded alongside the alternatives it
was chosen over. And it is **unfinished** in specific, named ways.

By the end of the semester, the four things below will exist because you built them. None of them
exist today:

- the firmware that turns a ROS 2 message into steering-motor motion
- the `ros2_control` hardware interface that lets one launch file drive both the simulation and the
  real car
- the measured geometry that makes the simulation and the vehicle agree
- the test suite and acceptance evidence that make the claim reproducible

The last one is not decoration. In this project, **the write-up is the claim**. A result nobody can
reproduce is not a result.

!!! quote "The standard this course is held to"

    "Honest failure outscores a lucky success." — [M8 capstone rubric](../learn/m8-capstone.md)

    A subsystem that does not work, with a correct and evidenced diagnosis of *why*, earns more than
    one that works for reasons you cannot explain.

---

## Prerequisites

**Required:** Python programming. Comfort with reading other people's code.

**Not required:** Linux, ROS, robotics, control theory, or C++. The course teaches Linux and ROS 2
from the beginning, and reaches C++ only in the second half, where it is optional for most tracks.

!!! danger "One hard prerequisite: a working machine on day one"

    Week 1 opens with a lab. Complete [Environment Setup](environment.md) **before September 7** and
    verify it with `bash scripts/check_env.sh`. Budget 2–4 hours. Students who arrive without a
    working Ubuntu 22.04 install lose Lab 1.

---

## Course calendar

The semester begins Tuesday **September 1** and ends Monday **December 21**. Because the class meets
on Mondays, that is **16 course weeks containing 15 meetings**.

| | |
|---|---|
| First meeting | **Mon 9/7** (9/1 is a Tuesday, so there is no Monday class that week) |
| **No class** | **Mon 10/5** — 개천절 대체공휴일 (10/3 falls on a Saturday) |
| Chuseok | 9/24–26 (Thu–Sat). No substitute holiday, so **Mon 9/28 meets normally** |
| Last meeting | **Mon 12/21** — final presentations |

**Week 5 has no meeting**, but it is not a week off. You receive a self-study packet and Lab 5 on
9/28, both due 10/12. That gives a two-week window — which also serves as catch-up time if your
environment setup went badly.

---

## Structure

```
W1 ─────── W4    Foundations — individual, identical labs for everyone   9/07 – 9/28
     W5    ○      NO MEETING — self-study packet + Lab 5                     10/05
W6 ─────── W10   Subsystem tracks — four teams in parallel              10/12 – 11/09
     W6    ↓      Teams announced; charters written
     W8    ★      MID-SEMESTER PRESENTATION                                  10/26
W11 ────── W13   Merge ladder — subsystems combine, pairwise            11/16 – 11/30
W14 ────── W15   Full integration and validation                        12/07 – 12/14
     W16   ★      FINAL DEMO + PRESENTATIONS                                 12/21
```

**Weeks 1–5 are individual.** Everyone does the same five labs and is graded on their own work. This
is deliberate: in a team project, foundational gaps hide. They will not hide here.

**Weeks 6–16 are team-based.** Four teams of six, each owning a real subsystem, merging into one
working vehicle. See [Teams & Tracks](teams.md).

### A typical 3-hour session

| | |
|---|---|
| 0:00 – 0:50 | Lecture |
| 0:50 – 1:00 | Break |
| 1:00 – 2:30 | Lab (W1–W5) or team work (W6–W16) |
| 2:30 – 3:00 | Standup — each team reports progress, blockers, and what it needs from another team |

The final 30 minutes are not filler. From Week 6 on, that is where cross-team integration actually
gets negotiated, and it is where the participation grade is observed.

---

## Schedule

Reading keys: **B** = *ROS 2: Zero to Robot* · **M** = [MRider learn module](../learn/index.md) ·
**D** = [design document](../design/overview.md)

| W | Date | Lecture | Lab / team block | Due |
|---|---|---|---|---|
| [1](weeks/w01.md) | **9/07** | Course intro. What middleware *is*. Drive-by-wire. The ROS 2 computation graph | [Lab 1](labs/lab1.md) — Environment; run the twin end to end | — |
| [2](weeks/w02.md) | **9/14** | Nodes, topics, messages. Packages, `colcon`, launch files | [Lab 2](labs/lab2.md) — Publisher/subscriber; drive the twin in a square | Lab 1 |
| [3](weeks/w03.md) | **9/21** | Services, actions, parameters. QoS. Command arbitration with `twist_mux` | [Lab 3](labs/lab3.md) — Parameterized speed governor; induce a QoS mismatch | Lab 2 |
| [4](weeks/w04.md) | **9/28** | Description to motion: URDF/Xacro, TF2, RViz, Gazebo, `ros2_control` | [Lab 4](labs/lab4.md) — Add a sensor link; break an extrinsic and diagnose it | Lab 3 |
| [**5**](weeks/w05.md) | **10/05** | ○ **NO MEETING** (개천절 대체공휴일) | **Self-study:** Ackermann kinematics. [Lab 5](labs/lab5.md) — measure turning radius against theory | Track preference form (10/9) |
| [6](weeks/w06.md) | **10/12** | Odometry and sensor fusion. The EKF | **Teams announced.** Kickoff and charter workshop | Lab 5 |
| [7](weeks/w07.md) | **10/19** | Embedded ROS 2: micro-ROS, the Teensy, `hardware_interface` | Track work | Team charters |
| [8](weeks/w08.md) | **10/26** | Safety: authority arbitration, failsafe matrices, FSMs | **★ MID-SEMESTER PRESENTATION** | Mid deliverable · peer eval |
| 9 | **11/02** | Control: PID, pure pursuit, RPP, and the ±22.5° constraint | Track work | — |
| 10 | **11/09** | Perception: camera and 2D LiDAR, intrinsics and extrinsics | Track work | Track milestone |
| 11 | **11/16** | SLAM: `slam_toolbox`, loop closure, and how to read a bad map | **Merge 1 — Electrical + Chassis** | — |
| 12 | **11/23** | Nav2: costmaps, planners, behavior trees, lifecycle nodes | **Merge 2 — Simulation + Software** | — |
| 13 | **11/30** | Simulation to reality: calibration, QoS/DDS, diagnostics, logging | **Merge 3 — (E+C) + Software** | — |
| 14 | **12/07** | System architecture. Docker and CI. Reproducibility | **Merge 4 — full integration** | — |
| 15 | **12/14** | Validation and failure analysis. Behavior cloning, previewed | Measure against the acceptance gates; dress rehearsal | Peer eval 2 |
| 16 | **12/21** | — | **★ FINAL DEMO + PRESENTATIONS** | Final report · demo |

!!! info "Why Week 4 is dense and Week 5 is self-study"

    The 10/5 holiday landed on what would have been the most important foundation week. Rather than
    cut content, the *systems* material — URDF through `ros2_control`, which is what people fail at
    unsupervised — moved into the live Week 4 session. What went to self-study is the *mathematics*:
    the bicycle model and the minimum-turning-radius derivation read perfectly well on paper, and
    Lab 5 measures against an already-working simulator rather than asking you to configure one.

!!! note "A note on the textbook"

    *ROS 2: Zero to Robot* targets ROS 2 **Jazzy**; this course uses **Humble**. Most content
    transfers directly. Where commands differ — `ros_gz` package naming, the `gz_ros2_control` source
    build, and several Nav2 parameter renames — the weekly notes carry a **Humble note** callout.
    Follow the weekly notes, not the book, when they disagree.

---

## Grading

| Component | Weight | What it measures |
|---|---:|---|
| **Individual labs** (Labs 1–5) | **30%** | Your own ROS 2 competence, before teams can hide it |
| **Mid-semester presentation** (W8) | **15%** | Your team's subsystem, demonstrated live |
| **Team deliverable** (W16) | **25%** | The subsystem you shipped, and its evidence |
| **Final demo & presentation** (W16) | **20%** | The integrated vehicle, and how you explain it |
| **Participation & documentation** | **10%** | Standups, git history, and what you wrote down |

Full rubrics are in [Grading & Rubrics](grading.md).

**Participation is not attendance.** It is assessed from standup contributions, commit history, and
documentation written — evidence of work, not presence in a chair.

**Peer evaluation** runs twice, at Week 8 and Week 15. It can adjust an individual's team-component
grade by up to ±15%. A team is not a place to be carried.

### Late work

Labs lose 10% per day, to a floor of 50%, up to one week late. After that, zero. Team deliverables
tied to a merge date cannot be late — a merge that does not happen on its date blocks three other
teams, and that is the real penalty.

If something goes wrong in your life, tell me **before** the deadline rather than after. Extensions
arranged in advance cost nothing.

---

## Academic integrity

**Collaboration is encouraged. Copying is not.** Discuss approaches with anyone. Write your own
submission.

**On AI assistants:** you may use them. Most working engineers do. Two conditions, both firm:

1. **Declare it.** Say what tool you used and for what, in your submission.
2. **Own it.** You are responsible for every line you submit. "The AI wrote it" is not a defence for
   code you cannot explain — and in the demo, I will ask you to explain it.

Using an assistant to write code you understand is engineering. Using one to produce code you cannot
read is how you arrive at Week 14 with a subsystem nobody can debug.

**Citation:** if you use code, a configuration, or an idea from outside the course — Stack Overflow,
a GitHub project, a paper — cite it. This project's own documents cite their sources; yours will too.

---

## What to read

**Primary:** the [MRider design documents](../design/overview.md). These are not textbook chapters.
They are the actual engineering record of this vehicle, including decisions that were made, argued
over, and in two cases **reversed**. Read the reversals — they are the most instructive pages in the
repository.

**Course modules:** the [learn modules M1–M8](../learn/index.md) are assigned as weekly reading.

**Textbook (optional):** [*ROS 2: Zero to Robot*](https://pouya-mansournia.github.io/ros2-zero-to-robot/)
— free online, 20 chapters. Good for a second explanation when the lecture did not land.

**Reference:** [docs.ros.org](https://docs.ros.org/en/humble/) — the official Humble documentation.
Learn to read it. You will need it after this course ends.

---

## See also

- [Environment Setup](environment.md) — **do this before September 7**
- [Teams & Tracks](teams.md) — the four subsystem teams and the merge ladder
- [Grading & Rubrics](grading.md) — how every component is assessed
- [Running the Digital Twin](../run-the-twin.md) — the four-terminal bring-up procedure
