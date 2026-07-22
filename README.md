# MRider — Michigan Rider

<p align="center">
  <img src="images/mrider.png" alt="MRider" height="180">
  <img src="images/mitt.png" alt="MITT" height="180">
</p>

**MRider** converts a kids ride-on, remote-controllable electric vehicle into a self-driving-ready car with a full **Drive-By-Wire (DBW)** system. The vehicle's nickname is **MITT** (Michigan Intelligent Transportation Tech), inspired by KITT from *Knight Rider*.

MRider is a **research and education platform**: rigorous enough for autonomous-driving research (mapping, navigation, end-to-end learning), documented well enough — [RoboRacer](https://roboracer.ai/)-style — for courses and external replication. It is the fourth generation of a platform line: [AVCS Kit](https://ieeexplore.ieee.org/document/8095696) (2017) → [Ridon Vehicle](https://www.mdpi.com/1996-1073/14/23/8039) (2021) → [OSCAR](https://github.com/bimilab/project-oscar/tree/devel_mrover) (2022) → [B-MROVER](https://github.com/jrkwon/mrover), whose validated ROS 2 + PX4 stack MRider reuses.

> **Status:** design phase complete (consensus-reviewed). Hardware sourcing and build are next.

## System at a Glance

| Subsystem | Design |
|---|---|
| Chassis | 24V two-seater kids ride-on (UTV/Jeep style), parent-remote class, reversible conversion |
| DBW | Pixhawk 6C + PX4 (rover) + Sabertooth 2x32, commanded from ROS 2 via Micro-XRCE-DDS |
| Steering | Arduino-local **"smart-servo"**: absolute column angle sensor, ≥100 Hz position loop on the Nano; datapath `MANUAL_CONTROL.roll` → PX4 servo-PWM → Nano → Sabertooth S1 |
| Odometry | 52 PPR drive-motor shaft encoder + wheel calibration, fused with the Pixhawk IMU (EKF) |
| Sensors | Front camera + 2D LiDAR (minimum); IMU from Pixhawk; GNSS/RTK as a growth path |
| Compute | Onboard laptop (own battery) running ROS 2 Humble — SLAM, Nav2, and an end-to-end NN pipeline |
| Safety | Hardware E-stop, relay-MUX authority arbitration (default = stock), RC-via-PX4 live override, failsafe matrix + FMEA |

Estimated cost: **~$1.4k minimum tier / ~$1.9k full tier** (see [BOM](design/bom.md)).

## Documentation

### Design

| Document | Contents |
|---|---|
| [design/overview.md](design/overview.md) | Project goals, requirements, and resolved design decisions |
| [design/architecture.md](design/architecture.md) | System architecture, command/feedback flows, power tree, timing contract |
| [design/vehicle.md](design/vehicle.md) | Chassis selection criteria, candidate models, 24V two-seater ADR |
| [design/dbw.md](design/dbw.md) | The core DBW design: steering smart-servo, throttle, encoders, interface contract |
| [design/safety.md](design/safety.md) | Failsafe matrix, authority arbitration, E-stop semantics, FMEA, bring-up protocol |
| [design/sensors.md](design/sensors.md) | Camera and LiDAR ADRs, IMU, GNSS/RTK path, mounting, laptop criteria |
| [design/calibration.md](design/calibration.md) | Steering, odometry, camera/LiDAR extrinsics, IMU, time-sync procedures |
| [design/software.md](design/software.md) | ROS 2 Humble stack, mrover reuse map, topic/TF contract, SLAM/Nav2/NN plan |
| [design/bom.md](design/bom.md) | Itemized bill of materials with minimum- and full-tier totals |

### Build & Learn (RoboRacer-style)

- **[Build guide](docs/build/README.md)** — BOM → mechanical → electrical → firmware → software → bench test → manual drive → autonomous.
- **[Learn curriculum](docs/learn/README.md)** — ROS 2 intro → DBW → safety → perception → SLAM → Nav2 → behavior cloning → capstone.

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

---

Bio-Inspired Machine Intelligence Lab (BIMI), University of Michigan-Dearborn
