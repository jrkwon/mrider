# MRider (Michgian Rider) Project

The MRider project is to convert a kids-ride-on remote-controllable electric vehicle to a self-driving ready car with a Drive-By-Wire (DBW) system. The vehicle's nick name is MITT (Michigan Intelligent Transportation Tech) inspired by KITT from Knight Rider.

## Plan

### Two design choices for DBW

1. Pixhawk-based: complex but powerful/extensible.
2. Arduino-based: simple but limited.

> **Resolved: neither — a third option.** This framing filed a 600 MHz Cortex-M7 under the
> same heading as an ATmega328P and dismissed both together (finding F10). A **single Teensy
> 4.1 running micro-ROS** keeps the Arduino option's simplicity — one board, one link — while
> adding the timing determinism and typed messaging a plain Arduino lacks, and drops PX4 from
> the control path. See [Design Decisions](#design-decisions-resolved) below.

### Vehicle choices for Chassis

- 12V or 24V  kids electic vehicle ride on car with parent remote control.
- These vehicles do not have servo motors for steering.

> **Resolved: 24 V two-seater.** Payload and torque margin, and it is the chassis class
> B-MROVER is validated on. Steering is motorized with a DC gearmotor on the column, with an
> absolute angle sensor mounted **load-side** so gearbox backlash appears as measured error
> rather than invisible bias. → [vehicle.md](vehicle.md), [dbw.md](dbw.md)

## Requirements

- Needs to know and control the steering angle and driving distance for mapping and navigation. 
  - Find a way to add sensors to measure the angle and distance with a minimally invasive way.
- A laptop will be an on-board computer to which most sensors are connected.
- IMU for pose estimation if necessary.
- Minimum sensor packages: one front camera and one LiDAR.
- GNSS is an optional.
  - **Amended:** optional for the semester-1 indoor target; **required** for the phase-2
    outdoor waypoint-following target, where dead reckoning from wheel odometry + IMU alone
    drifts out of a lane-width corridor within tens of meters. RTK-class if lane-level
    accuracy is wanted. → [sensors.md](sensors.md), [bom.md](bom.md) phase-2 growth path

## Expected Results

### Design choices

- Vehicle
- DBW
  - Steering and driving encoding method
- Sensors: camera, LiDAR, IMU, etc.
  
### Design documents

- Something similar to [RoboRacer](https://roboracer.ai/).
  - For now, [Build](https://roboracer.ai/build) and [Learn](https://roboracer.ai/learn).

## Design Decisions (resolved)

The following choices are decided and drive all design documents. Each is recorded as an
ADR in the linked document below.

- **DBW architecture — single Teensy 4.1 + micro-ROS.** One MCU owns all actuation and
  low-level sensing, speaking native ROS 2 over USB to the laptop, commanding a Sabertooth
  2x32 in independent R/C (PWM) mode through a hardware RC signal MUX. Replaces the Pixhawk 6C
  + Arduino Nano pair.
  → [dbw.md](dbw.md), [architecture.md](architecture.md),
  [the decision record](adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07)
- **Steering — Teensy-local position loop at ≥ 200 Hz**, against an **absolute magnetic angle
  sensor mounted load-side** (downstream of the steering gearbox, ±22.5°) so backlash shows up
  as measured error. Setpoint arrives as a typed `DbwCommand` message — no PWM round trip.
  Potentiometer is the pre-registered fallback if no shaft with ≤ 340° travel is accessible.
  → [dbw.md](dbw.md)
- **Drive odometry — drive-motor shaft encoder** with wheel-diameter calibration, fused with
  IMU via EKF to bound gearbox/slip error. **PPR is verified on the part fitted, not
  inherited** — the source project conflicts with itself. → [dbw.md](dbw.md), [calibration.md](calibration.md)
- **Chassis — 24V two-seater ride-on** (UTV/Jeep style) for payload and voltage headroom.
  Reconsidered against a cheaper 12 V single-seater and kept. → [vehicle.md](vehicle.md)
- **Sensors — camera + 2D LiDAR minimum**, discrete BNO085-class IMU, GNSS(+RTK) as the
  phase-2 outdoor path. → [sensors.md](sensors.md)
- **Software — ROS 2 Humble on Ubuntu 22.04**, reusing `jrkwon/mrover` autonomy packages
  (SLAM, Nav2, EKF, `neural_net/`) — all of which sit above the vehicle interface and are
  unaffected by the controller change. The same `ros2_control` stack runs in simulation and on
  hardware; only the `hardware_interface` plugin swaps. → [software.md](software.md)
- **Safety — layered authority.** Hardware E-stop → relay MUX to STOCK → **hardware RC signal
  MUX** → SBUS closed-loop override. The first three are independent of Teensy firmware. The
  RC signal MUX is the **condition** on which the single-MCU architecture was adopted.
  → [safety.md](safety.md)
- **Scope — semester 1 delivers a trustworthy DBW, a working twin, and an indoor SLAM map**,
  evidenced by quantified accuracy numbers. Outdoor GNSS waypoints and behavior cloning are
  phase 2. **The Learn course kit is no longer deferred** — it is the reading spine of
  [자율주행미들웨어응용](../course/index.md), taught Fall 2026, whose four student tracks build
  the subsystems this scope leaves open.
  → [software.md §8](software.md#8-semester-1-scope-and-software-acceptance-gates)

## Documents

### Design

- [architecture.md](architecture.md) — system architecture, command/feedback flow, power tree, timing/heartbeat contract.
- [vehicle.md](vehicle.md) — chassis selection criteria and the 24V two-seater decision.
- [dbw.md](dbw.md) — the core drive-by-wire design: steering smart-servo, throttle, encoding, interface contract.
- [safety.md](safety.md) — failsafe matrix, authority arbitration, E-stop semantics, FMEA, bring-up protocol.
- [sensors.md](sensors.md) — camera, 2D LiDAR, IMU, optional GNSS/RTK, mounting and laptop criteria.
- [calibration.md](calibration.md) — steering, odometry, camera/LiDAR, IMU, and time-sync calibration.
- [software.md](software.md) — ROS 2 Humble stack, mrover reuse map, topic/TF contract, SLAM/Nav2/NN plan.
- [bom.md](bom.md) — itemized bill of materials, split into Tier 1 (vehicle + DBW core) and Tier 2 (perception) so the sensor spend follows the DBW gates. ~$1,035 estimated total; ~$620 floor.

### Reviews

- [adr-dbw-architecture-review.md](adr-dbw-architecture-review.md) — 2026-08 re-review of the DBW decisions against the B-MROVER source, re-reading the code rather than arguing from the design side. It found that two stated rationales were not supported by the code they cited, added two alternatives, and raised the single-MCU controller question. **Decision D3 was closed as ADOPTED on 2026-08-07**, before any hardware was ordered; the Pixhawk topology it supersedes is retained there as the record of how the decision was reached. Also the source of findings F1–F11, several of which remain open for verification at bring-up.

### Build & Learn (RoboRacer-style)

- [Build guide](../build/index.md) — step-by-step Build guide (BOM → mechanical → electrical → firmware → software → bench test → manual drive → autonomous).
- [Learn curriculum](../learn/index.md) — Learn curriculum (ROS 2 intro → DBW → safety → perception → SLAM → Nav2 → behavior cloning → capstone).

## My Previous Work (Documents)

- <https://deepblue.lib.umich.edu/bitstreams/30717b2a-7c57-4604-95d6-ea3918857a89/download>
- <https://www.mdpi.com/1996-1073/14/23/8039>
- <https://ieeexplore.ieee.org/document/8095696>

## My Previous Work (Code)

- <https://github.com/jrkwon/mrover>
- <https://github.com/bimilab/project-oscar/tree/devel_mrover>

## Similar Work

- <https://github.com/SKKUAutoLab/autolab_kingocar>
- <https://github.com/SKKUAutoLab/H-Mobility-Autonomous-Advanced-Course>
