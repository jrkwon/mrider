# MRider Build Guide

A step-by-step guide to converting a kids ride-on electric vehicle ("MITT") into a
drive-by-wire (DBW), self-driving-ready platform. The guide is organized
RoboRacer-style: work through the sections **in order**, from sourcing parts to an
autonomous lap. Each section states its goal, prerequisites, and expected outcome,
and links to the design document that specifies the details.

> Status: **skeleton**. Step-by-step instructions are marked `TODO` and will be filled
> in during the build phase. The design documents linked below are the authoritative
> specification; this guide is the assembly recipe derived from them.

## Prerequisites (whole build)

- All design documents reviewed — start with the [design overview](../../design/overview.md).
- Basic hand tools, a soldering iron, a multimeter, and a bench power supply.
- Comfort with ROS 2 on Ubuntu 22.04 and flashing an Arduino.
- **Safety:** every powered test before "Manual drive" is performed **wheels-off** on a
  stand. Read [safety.md](../../design/safety.md) before applying power to the vehicle.

---

## 1. BOM & sourcing

**Goal:** acquire every part before touching the vehicle, at a known cost.

Order the components for your chosen tier (minimum vs. full) and confirm long-lead
items (flight controller, LiDAR, gearmotor) are in hand. Cross-check quantities and
connectors against the bill of materials.

- **Prerequisites:** budget decided; tier (minimum / full) chosen.
- **Specification:** [design/bom.md](../../design/bom.md)
- **Expected outcome:** all line items received; totals reconciled against the BOM.

`TODO:` per-vendor ordering checklist, substitution notes, connector/crimp list.

## 2. Vehicle prep & mechanical

**Goal:** prepare the chassis and mount the steering actuator and encoders mechanically.

Disassemble the necessary trim, identify the steering column and drive-motor shaft,
and fit the steering gearmotor, the absolute steering-angle sensor, and the drive-shaft
encoder. Keep the modifications minimally invasive and reversible.

- **Prerequisites:** Section 1 complete; chassis selected.
- **Specification:** [design/vehicle.md](../../design/vehicle.md), [design/dbw.md](../../design/dbw.md)
- **Expected outcome:** actuator and sensors mechanically mounted; stock steering still
  reassemblable.

`TODO:` teardown photos, bracket dimensions, shaft-adapter procedure, torque check.

## 3. Electrical & wiring

**Goal:** build the power and signal harness, including the authority MUX and E-stop.

Wire the 24V traction rail, the isolated logic rail, the Sabertooth 2x32, the Pixhawk
power module, the relay-MUX (STOCK vs. DBW), and the hardware E-stop. Verify rail
isolation and default-to-stock behavior before energizing anything downstream.

- **Prerequisites:** Section 2 complete.
- **Specification:** [design/dbw.md](../../design/dbw.md), [design/safety.md](../../design/safety.md)
- **Expected outcome:** harness continuity-checked; relay defaults to STOCK; E-stop cuts
  traction power only.

`TODO:` wiring diagram, per-rail fuse table, relay-MUX bench test procedure.

## 4. Firmware bring-up: Nano smart-servo + PX4

**Goal:** flash and configure the two controllers that close the DBW loops.

Flash the Arduino Nano smart-servo firmware (reads the absolute angle sensor + encoders,
closes the steering position loop, drives Sabertooth S1 from a PX4 servo-PWM setpoint).
Flash and configure PX4 on the Pixhawk 6C (rover setup, RC binding, servo-PWM outputs,
failsafes). Confirm the pinned datapath: `MANUAL_CONTROL.roll` → PX4 servo-PWM → Nano.

- **Prerequisites:** Section 3 complete; Sabertooth in independent R/C (PWM) mode.
- **Specification:** [design/dbw.md](../../design/dbw.md)
- **Expected outcome:** Nano closes a bench steering loop to a commanded angle; PX4 arms
  and emits steering/throttle PWM; RC override verified.

`TODO:` Nano firmware build/flash, PX4 param file + version pin, output-channel map.

## 5. Software install: ROS 2 Humble stack

**Goal:** stand up the on-board ROS 2 Humble stack on the laptop.

Install ROS 2 Humble and the MRider workspace (reusing `jrkwon/mrover` packages),
bring up Micro-XRCE-DDS to the Pixhawk, and confirm the command/feedback topics
(`/mrider/cmd`, `/mrider/feedback`) and the TF tree are alive.

- **Prerequisites:** Section 4 complete; laptop selected.
- **Specification:** [design/software.md](../../design/software.md)
- **Expected outcome:** ROS 2 talks to PX4 over XRCE; feedback streams from the Nano
  over USB serial; TF tree populated.

`TODO:` install script, workspace build, XRCE agent launch, topic verification.

## 6. Bench test (wheels-off) & calibration

**Goal:** validate the full command/feedback chain safely, then calibrate.

With the vehicle on a stand, exercise steering and throttle end-to-end and confirm every
failsafe in the matrix. Then calibrate: steering zero/center and counts→degrees,
encoder ticks→distance, camera intrinsics, and camera/LiDAR→base_link extrinsics.

- **Prerequisites:** Section 5 complete.
- **Specification:** [design/safety.md](../../design/safety.md), [design/calibration.md](../../design/calibration.md)
- **Expected outcome:** all failsafes pass wheels-off; calibration constants recorded.

`TODO:` bench-test checklist, failsafe verification table, calibration record sheet.

## 7. Manual drive (RC + joystick)

**Goal:** drive the vehicle under human control through the DBW path.

First drive with the RC transmitter bound to the Pixhawk (the live override authority),
then via a joystick publishing to `/mrider/cmd`. Confirm authority arbitration and E-stop
behave as specified while the vehicle is moving at walking speed.

- **Prerequisites:** Section 6 complete; open, flat test area.
- **Specification:** [design/safety.md](../../design/safety.md), [design/dbw.md](../../design/dbw.md)
- **Expected outcome:** smooth manual steering/throttle; RC override and E-stop confirmed
  under motion.

`TODO:` first-drive protocol, spotter roles, joystick mapping, abort criteria.

## 8. Autonomous bring-up (SLAM → Nav2 → behavior cloning)

**Goal:** progress from mapping to autonomous driving.

Build a map with slam_toolbox, navigate with Nav2, then collect driving data and run the
end-to-end behavior-cloning pipeline (mrover `neural_net/` lineage) for an autonomous lap.

- **Prerequisites:** Section 7 complete; a mapped test course.
- **Specification:** [design/software.md](../../design/software.md), [design/sensors.md](../../design/sensors.md)
- **Expected outcome:** a saved map, successful Nav2 goals, and an autonomous lap.

`TODO:` SLAM mapping run, Nav2 config, data-collection protocol, training + deploy.

---

## See also

- [Design overview & document index](../../design/overview.md)
- [Learn curriculum](../learn/README.md)
