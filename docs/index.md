---
hide:
  - navigation
---

# MRider — Michigan Rider

!!! warning "Architecture updated 2026-08-07"

    MRider's DBW controller is a **single Teensy 4.1 running micro-ROS**, replacing the
    Pixhawk 6C + Arduino Nano topology described in earlier drafts. See
    [decision D3](design/adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07).

    Two further changes landed after it: the chassis reversed to a **12 V single-seater**
    ([ADR D-R](design/vehicle.md)), and the Nav2 planner became **SmacPlannerHybrid with
    reversing enabled** ([ADR-SW2, closed](design/software.md#45-planner-swap-to-smacplannerhybrid-resolved-2026-08-09)).
    The `design/`, `learn/`, and `course/` documents are current; some `build/` pages are
    still being updated and carry their own notices.


<p align="center">
  <img src="images/mrider-small.png" alt="MRider">
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="images/mitt-small.png" alt="MITT">
</p>

**MRider** converts a kids ride-on, remote-controllable electric vehicle into a
self-driving-ready car with a full **Drive-By-Wire (DBW)** system. The vehicle's nickname
is **MITT** (Michigan Intelligent Transportation Tech), inspired by KITT from
*Knight Rider*.

MRider is a **research and education platform**: rigorous enough for autonomous-driving
research (mapping, navigation, end-to-end learning), documented well enough —
[RoboRacer](https://roboracer.ai/)-style — for courses and external replication. It is the
fourth generation of a platform line:
[AVCS Kit](https://ieeexplore.ieee.org/document/8095696) (2017) →
[Ridon Vehicle](https://www.mdpi.com/1996-1073/14/23/8039) (2021) →
[OSCAR](https://github.com/bimilab/project-oscar/tree/devel_mrover) (2022) →
[B-MROVER](https://github.com/jrkwon/mrover), whose validated ROS 2 stack MRider
reuses.

!!! attention "New here? Start with [Getting Started](getting-started.md)."

    It routes you to the right entry point depending on whether you want to **build** a
    vehicle, **teach or take** the course, or **read the design**.

!!! info "Project status"

    The design documents are consensus-reviewed and authoritative. The **digital twin runs
    end to end** — Gazebo Harmonic, `slam_toolbox` mapping, and Nav2 reaching goals
    ([run it yourself](run-the-twin.md)). Hardware sourcing is underway
    ([order log](order-log.md)); nothing has been built yet.

    The [Build Guide](build/index.md) is written from the designs but has **not been
    validated on a physical vehicle** — those pages carry a *Draft* banner.

    MRider is taught as **[자율주행미들웨어응용](course/syllabus.md)** in Fall 2026, where four
    student tracks build the subsystems that are still missing.

## System at a Glance

| Subsystem | Design |
|---|---|
| Chassis | **12 V single-seater** ride-on (Land Rover Defender class, 98 × 56 × 47 cm, ~10 kg), parent-remote, reversible conversion — [ADR D-R](design/vehicle.md) |
| DBW | **Single Teensy 4.1 running micro-ROS** + Sabertooth 2x32 in independent R/C PWM mode — [ADR D3](design/adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07) |
| Steering | **Load-side absolute angle sensor** on the kingpin axis, ≥200 Hz position loop **on the Teensy**; ±22.5° travel, R_min 1.52 m — [ADR B / ADR E](design/dbw.md) |
| Odometry | One quadrature encoder on one drive-motor shaft — **PPR must be measured, never inherited** (finding F7) — roll-out calibrated, fused with the IMU in an EKF — [ADR C](design/dbw.md) |
| Sensors | Front camera + 2D LiDAR (minimum); BNO085-class IMU; GNSS/RTK as a growth path. **No rear sensing** — see the reverse constraint in [software.md §4.5](design/software.md#45-planner-swap-to-smacplannerhybrid-resolved-2026-08-09) |
| Compute | Onboard laptop (own battery) running ROS 2 Humble — SLAM, Nav2, and an end-to-end NN pipeline |
| Safety | Hardware E-stop, relay MUX (default = stock), hardware RC signal MUX, SBUS override — **three of the four work with the firmware dead** — plus failsafe matrix + FMEA |

Estimated cost: **~$745 Tier 1 / ~$930 both tiers** once ~10% contingency is included
(line items sum to $678 / $846) — see the [Bill of Materials](design/bom.md).

## Where to go

<div class="grid cards" markdown>

-   :material-file-document-multiple: **[Design](design/overview.md)**

    The authoritative specification — nine documents covering architecture, the DBW
    design, safety, sensors, calibration, software, and cost.

-   :material-wrench: **[Build Guide](build/index.md)**

    Eight ordered steps from sourcing parts to an autonomous lap. Each step names its
    goal, prerequisites, specification, and expected outcome.

-   :material-school: **[Learn](learn/index.md)**

    A RoboRacer-style coursekit: eight modules from a first ROS 2 node to a capstone
    autonomous lap, each with a lecture, a lab, and a slide outline.

-   :material-github: **[Source](https://github.com/jrkwon/mrider)**

    Everything on this site lives in the `jrkwon/mrider` repository. Corrections are
    welcome — every page has an edit link.

</div>

## Lineage & Related Work

**Previous work (documents):**
[Scaled-vehicle platform thesis (UM Deep Blue)](https://deepblue.lib.umich.edu/bitstreams/30717b2a-7c57-4604-95d6-ea3918857a89/download) ·
[Ridon Vehicle, *Energies* 2021](https://www.mdpi.com/1996-1073/14/23/8039) ·
[AVCS Kit, IEEE AFRICON 2017](https://ieeexplore.ieee.org/document/8095696)

**Previous work (code):**
[jrkwon/mrover](https://github.com/jrkwon/mrover) ·
[bimilab/project-oscar (devel_mrover)](https://github.com/bimilab/project-oscar/tree/devel_mrover)

**Similar work:**
[SKKUAutoLab/autolab_kingocar](https://github.com/SKKUAutoLab/autolab_kingocar) ·
[SKKUAutoLab/H-Mobility-Autonomous-Advanced-Course](https://github.com/SKKUAutoLab/H-Mobility-Autonomous-Advanced-Course) ·
[RoboRacer (F1TENTH)](https://roboracer.ai/)
