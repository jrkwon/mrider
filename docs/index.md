---
hide:
  - navigation
---

# MRider — Michigan Rider

<p align="center">
  <img src="images/mrider.png" alt="MRider" height="44">
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="images/mitt.png" alt="MITT" height="44">
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
[B-MROVER](https://github.com/jrkwon/mrover), whose validated ROS 2 + PX4 stack MRider
reuses.

!!! attention "New here? Start with [Getting Started](getting-started.md)."

    It routes you to the right entry point depending on whether you want to **build** a
    vehicle, **teach or take** the course, or **read the design**.

!!! info "Project status — design phase complete"

    The design documents are consensus-reviewed and authoritative. Hardware sourcing and
    the physical build are next. The [Build Guide](build/index.md) and
    [Learn](learn/index.md) sections are written from those designs but have **not yet
    been validated on a physical vehicle** — pages in that state carry a *Draft* banner.

## System at a Glance

| Subsystem | Design |
|---|---|
| Chassis | 24 V two-seater kids ride-on (UTV/Jeep style), parent-remote class, reversible conversion |
| DBW | Pixhawk 6C + PX4 (rover) + Sabertooth 2x32, commanded from ROS 2 via Micro-XRCE-DDS |
| Steering | Arduino-local **"smart-servo"**: absolute column angle sensor, ≥100 Hz position loop on the Nano; datapath `MANUAL_CONTROL.roll` → PX4 servo-PWM → Nano → Sabertooth S1 |
| Odometry | 52 PPR drive-motor shaft encoder + wheel calibration, fused with the Pixhawk IMU (EKF) |
| Sensors | Front camera + 2D LiDAR (minimum); IMU from Pixhawk; GNSS/RTK as a growth path |
| Compute | Onboard laptop (own battery) running ROS 2 Humble — SLAM, Nav2, and an end-to-end NN pipeline |
| Safety | Hardware E-stop, relay-MUX authority arbitration (default = stock), RC-via-PX4 live override, failsafe matrix + FMEA |

Estimated cost: **~$1.4k minimum tier / ~$1.9k full tier** in parts (~$1.6k / ~$2.1k once
~10% contingency is included) — see the [Bill of Materials](design/bom.md).

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
