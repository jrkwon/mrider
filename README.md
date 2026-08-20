# MRider — Michigan Rider

<p align="center">
  <img src="docs/images/mrider-small.png" alt="MRider">
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="docs/images/mitt-small.png" alt="MITT">
</p>

<p align="center">
  📖 <strong>Documentation site: <a href="https://jrkwon.github.io/mrider/">jrkwon.github.io/mrider</a></strong>
</p>

**MRider** converts a kids ride-on, remote-controllable electric vehicle into a self-driving-ready car with a full **Drive-By-Wire (DBW)** system. The vehicle's nickname is **MITT** (Michigan Intelligent Transportation Tech), inspired by KITT from *Knight Rider*.

MRider is a **research and education platform**: rigorous enough for autonomous-driving research (mapping, navigation, end-to-end learning), documented well enough — [RoboRacer](https://roboracer.ai/)-style — for courses and external replication. It is the fourth generation of a platform line: [AVCS Kit](https://ieeexplore.ieee.org/document/8095696) (2017) → [Ridon Vehicle](https://www.mdpi.com/1996-1073/14/23/8039) (2021) → [OSCAR](https://github.com/bimilab/project-oscar/tree/devel_mrover) (2022) → [B-MROVER](https://github.com/jrkwon/mrover), whose validated ROS 2 stack MRider reuses.

> **Status:** design complete and consensus-reviewed. The **digital twin runs end to end** —
> Gazebo Harmonic, `slam_toolbox` mapping, Nav2 reaching goals ([run the twin](docs/run-the-twin.md)).
> Hardware sourcing is underway ([order log](docs/order-log.md)). Taught as
> [자율주행미들웨어응용](docs/course/syllabus.md), Fall 2026.

## System at a Glance

| Subsystem | Design |
|---|---|
| Chassis | **12 V single-seater** ride-on (Land Rover Defender class, 98 × 56 × 47 cm, ~10 kg), parent-remote, reversible conversion — [ADR D-R](docs/design/vehicle.md) |
| DBW | **Single Teensy 4.1 running micro-ROS** + Sabertooth 2x32 in independent R/C PWM mode — [ADR D3](docs/design/adr-dbw-architecture-review.md) |
| Steering | **Load-side absolute angle sensor** on the kingpin axis, ≥200 Hz position loop **on the Teensy**; ±22.5° travel, R_min 1.52 m — [ADR B / ADR E](docs/design/dbw.md) |
| Odometry | One quadrature encoder on one drive-motor shaft — **PPR must be measured, never inherited** (finding F7) — roll-out calibrated, fused with the IMU in an EKF — [ADR C](docs/design/dbw.md) |
| Sensors | Front camera + 2D LiDAR (minimum); BNO085-class IMU; GNSS/RTK as a growth path. **No rear sensing** — see the reverse constraint in [software.md §4.5](docs/design/software.md) |
| Compute | Onboard laptop (own battery) running ROS 2 Humble — SLAM, Nav2, and an end-to-end NN pipeline |
| Safety | Hardware E-stop, relay MUX (default = stock), hardware RC signal MUX, SBUS override — **three of the four work with the firmware dead** — plus failsafe matrix + FMEA |

Estimated cost: **~$745 Tier 1 / ~$930 both tiers**, contingency included (see [BOM](docs/design/bom.md); line items sum to $678 / $846).

## Documentation

### Design

| Document | Contents |
|---|---|
| [docs/design/overview.md](docs/design/overview.md) | Project goals, requirements, and resolved design decisions |
| [docs/design/architecture.md](docs/design/architecture.md) | System architecture, command/feedback flows, power tree, timing contract |
| [docs/design/vehicle.md](docs/design/vehicle.md) | Chassis selection criteria, candidate models, ADR D and its reversal to the 12 V single-seater |
| [docs/design/dbw.md](docs/design/dbw.md) | The core DBW design: steering smart-servo, throttle, encoders, interface contract |
| [docs/design/safety.md](docs/design/safety.md) | Failsafe matrix, authority arbitration, E-stop semantics, FMEA, bring-up protocol |
| [docs/design/sensors.md](docs/design/sensors.md) | Camera and LiDAR ADRs, IMU, GNSS/RTK path, mounting, laptop criteria |
| [docs/design/calibration.md](docs/design/calibration.md) | Steering, odometry, camera/LiDAR extrinsics, IMU, time-sync procedures |
| [docs/design/software.md](docs/design/software.md) | ROS 2 Humble stack, mrover reuse map, topic/TF contract, SLAM/Nav2/NN plan |
| [docs/design/bom.md](docs/design/bom.md) | Itemized bill of materials with minimum- and full-tier totals |

### Build & Learn (RoboRacer-style)

- **[Build guide](docs/build/index.md)** — BOM → mechanical → electrical → firmware → software → bench test → manual drive → autonomous.
- **[Learn curriculum](docs/learn/index.md)** — ROS 2 intro → DBW → safety → perception → SLAM → Nav2 → behavior cloning → capstone.

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
