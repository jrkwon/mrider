# 자율주행미들웨어응용 — Autonomous Driving Middleware Applications

Graduate course · Fall 2026 · University of Michigan-Dearborn, BIMI Lab
Mondays, 3 hours · 24 students · taught in English

---

## Start here

<div class="grid cards" markdown>

-   :material-download: **[Environment Setup](environment.md)**

    ---

    **Do this before September 7.** Ubuntu 22.04, ROS 2 Humble, Gazebo Harmonic, and a verification
    script that tells you exactly what is missing. Budget 2–4 hours.

-   :material-calendar: **[Syllabus](syllabus.md)**

    ---

    The 16-week schedule, grading weights, policies, and reading. Start here to see where the course
    is going.

-   :material-account-group: **[Teams & Tracks](teams.md)**

    ---

    The four subsystem teams — Electrical, Chassis, Simulation, Software — what each owns, and how
    they merge into one vehicle.

-   :material-check-decagram: **[Grading & Rubrics](grading.md)**

    ---

    Every rubric, in full. Read the standard the course is graded against before you write anything.

</div>

---

## What you will build

This course teaches ROS 2 by **finishing a real vehicle**.

[MRider](../index.md) is a 12 V ride-on car being converted into a drive-by-wire autonomous research
platform. Its digital twin already drives, maps a warehouse, and navigates to goals. Its design is
documented down to the decisions that were argued over and, twice, reversed.

And it is unfinished in specific, named ways. By December, these will exist because you built them:

| | |
|---|---|
| **`firmware/`** | The Teensy controller that turns a ROS 2 message into steering motion. No firmware exists in this repository today |
| **`mitt_hardware`** | The `ros2_control` plugin that makes one launch file drive both the simulator and the real car |
| **Measured geometry** | Every dimension the simulator uses is currently an estimate. The file says so itself: *"NOTHING IN THIS FILE HAS BEEN MEASURED"* |
| **A real test suite** | The repository has 29 tests. All 29 are linters |

!!! quote "The standard"

    "Honest failure outscores a lucky success."

    A subsystem that does not work, with a correct and evidenced diagnosis of why, scores above one
    that works for reasons you cannot explain. See [Grading](grading.md).

---

## Weekly material

Individual labs run Weeks 1–5; team tracks run Weeks 6–16.

| W | Date | Topic | Lab |
|---|---|---|---|
| [1](weeks/w01.md) | 9/07 | Middleware, drive-by-wire, and the ROS 2 graph | [Lab 1](labs/lab1.md) |
| [2](weeks/w02.md) | 9/14 | Nodes, topics, packages, launch | [Lab 2](labs/lab2.md) |
| [3](weeks/w03.md) | 9/21 | Services, actions, parameters, QoS | [Lab 3](labs/lab3.md) |
| [4](weeks/w04.md) | 9/28 | Description to motion: URDF, TF2, Gazebo, `ros2_control` | [Lab 4](labs/lab4.md) |
| [5](weeks/w05.md) | 10/05 | ○ No meeting — Ackermann kinematics, self-study | [Lab 5](labs/lab5.md) |
| [6](weeks/w06.md) | 10/12 | Odometry, sensor fusion, and **teams announced** | — |
| [7](weeks/w07.md) | 10/19 | Embedded ROS 2: micro-ROS, Teensy, `hardware_interface` | — |
| [8](weeks/w08.md) | 10/26 | Safety, authority, failsafe — **★ mid-semester presentation** | — |
| [9](weeks/w09.md) | 11/02 | Control: PID, pure pursuit, RPP | — |
| [10](weeks/w10.md) | 11/09 | Perception: camera, LiDAR, calibration | — |
| [11](weeks/w11.md) | 11/16 | SLAM — **★ Merge 1: Electrical + Chassis** | — |
| [12](weeks/w12.md) | 11/23 | Nav2 — **★ Merge 2: Simulation + Software** | — |
| 13–16 | 11/30 – 12/21 | Sim-to-real, integration, validation, final demo | see [Teams](teams.md) |

Weekly notes for W13 onward are published once the hardware exists — they depend on
measured geometry and on which bench kit actually works.

---

## How this fits the rest of the documentation

This site is the engineering record of a real project, and the course sits inside it rather than
beside it. That is deliberate — you learn from the actual decisions, not a simplified retelling.

| | |
|---|---|
| **[Design docs](../design/overview.md)** | The specification. Authoritative. Includes the reversals — the most instructive pages here |
| **[Build guide](../build/index.md)** | The lab-infrastructure manual: eight gated steps from parts to autonomy |
| **[Learn modules M1–M8](../learn/index.md)** | Self-contained topic modules, assigned as weekly reading |
| **[Running the Digital Twin](../run-the-twin.md)** | The four-terminal bring-up procedure. Verified working |
| **Course** *(you are here)* | Schedule, labs, teams, and assessment for Fall 2026 |

---

## Contact

**Jaerock Kwon, PhD** — jrkwon@umich.edu
Associate Professor, Electrical and Computer Engineering

If you are stuck on setup for more than 30 minutes, stop and ask. There is a lot of real work waiting
and none of it is installing drivers.
