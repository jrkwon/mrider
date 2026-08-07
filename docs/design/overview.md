# MRider (Michgian Rider) Project

The MRider project is to convert a kids-ride-on remote-controllable electric vehicle to a self-driving ready car with a Drive-By-Wire (DBW) system. The vehicle's nick name is MITT (Michigan Intelligent Transportation Tech) inspired by KITT from Knight Rider.

## Plan

### Two design choices for DBW

1. Pixhawk-based: complex but powerful/extensible.
2. Arduino-based: simple but limited.

### Vehicle choices for Chassis

- 12V or 24V  kids electic vehicle ride on car with parent remote control.
- These vehicles do not have servo motors for steering.

## Requirements

- Needs to know and control the steering angle and driving distance for mapping and navigation. 
  - Find a way to add sensors to measure the angle and distance with a minimally invasive way.
- A laptop will be an on-board computer to which most sensors are connected.
- IMU for pose estimation if necessary.
- Minimum sensor packages: one front camera and one LiDAR.
- GNSS is an optional.

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

- **DBW architecture — Pixhawk-based.** Pixhawk 6C + PX4 (rover) + Sabertooth 2x32,
  ROS 2 via Micro-XRCE-DDS. Reuses the validated `jrkwon/mrover` transport, EKF/IMU,
  RC-failsafe, and GNSS path nearly verbatim. → [dbw.md](dbw.md), [architecture.md](architecture.md)
- **Steering — Arduino-local "smart-servo".** An absolute steering-column angle sensor is
  read by the Arduino Nano, which closes the position loop locally (≥100 Hz). Pinned
  datapath: `MANUAL_CONTROL.roll` → PX4 servo-PWM → Nano → Sabertooth S1. Sabertooth runs
  in independent R/C (PWM) mode (S1 ← Nano, S2 ← PX4). → [dbw.md](dbw.md)
- **Drive odometry — drive-motor shaft encoder** (52 PPR) with wheel-diameter calibration,
  fused with IMU via EKF to bound gearbox/slip error. → [dbw.md](dbw.md), [calibration.md](calibration.md)
- **Chassis — 24V two-seater ride-on** (UTV/Jeep style) for payload and voltage headroom.
  → [vehicle.md](vehicle.md)
- **Sensors — camera + 2D LiDAR minimum**, IMU from the Pixhawk, GNSS(+RTK) optional as a
  growth path. → [sensors.md](sensors.md)
- **Software — ROS 2 Humble**, reusing `jrkwon/mrover` packages (SLAM, Nav2, EKF, and the
  end-to-end `neural_net/` pipeline). → [software.md](software.md)
- **Safety — hardware E-stop + relay-MUX authority arbitration** with RC-via-PX4 as the live
  override; default-to-stock, reversible. → [safety.md](safety.md)

## Documents

### Design

- [architecture.md](architecture.md) — system architecture, command/feedback flow, power tree, timing/heartbeat contract.
- [vehicle.md](vehicle.md) — chassis selection criteria and the 24V two-seater decision.
- [dbw.md](dbw.md) — the core drive-by-wire design: steering smart-servo, throttle, encoding, interface contract.
- [safety.md](safety.md) — failsafe matrix, authority arbitration, E-stop semantics, FMEA, bring-up protocol.
- [sensors.md](sensors.md) — camera, 2D LiDAR, IMU, optional GNSS/RTK, mounting and laptop criteria.
- [calibration.md](calibration.md) — steering, odometry, camera/LiDAR, IMU, and time-sync calibration.
- [software.md](software.md) — ROS 2 Humble stack, mrover reuse map, topic/TF contract, SLAM/Nav2/NN plan.
- [bom.md](bom.md) — itemized bill of materials with minimum- and full-tier totals.

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
