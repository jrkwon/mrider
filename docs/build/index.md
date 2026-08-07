# MRider Build Guide

A step-by-step guide to converting a kids ride-on electric vehicle ("MITT") into a
drive-by-wire (DBW), self-driving-ready platform. The guide is organized
RoboRacer-style: work through the sections **in order**, from sourcing parts to an
autonomous lap. Each section states its goal, prerequisites, and expected outcome,
and links to the design document that specifies the details.

!!! warning "Draft — not yet validated on hardware"

    These procedures are derived from the design documents. They have **not** been performed
    on a physical vehicle. Values marked *(measure during bring-up)* must be recorded and
    these pages updated before they are used for teaching or external replication. The
    design documents remain the authoritative specification; where a build step and a design
    document disagree, the design document is correct.

## The eight steps

| # | Step | Gate you must pass to continue |
|---|---|---|
| 1 | [BOM & sourcing](01-bom-sourcing.md) | Every line item received and reconciled |
| 2 | [Vehicle prep & mechanical](02-mechanical.md) | Actuator and sensors mounted; stock steering still reassemblable |
| 3 | [Electrical & wiring](03-electrical.md) | Harness continuity-checked; relay defaults to STOCK; E-stop cuts traction only |
| 4 | [Firmware bring-up](04-firmware.md) | Nano closes a bench steering loop; PX4 emits servo PWM; RC override verified |
| 5 | [Software install](05-software.md) | ROS 2 ↔ PX4 over XRCE; feedback frames streaming; TF tree populated |
| 6 | [Bench test & calibration](06-bench-test.md) | All failsafes pass wheels-off; calibration constants recorded |
| 7 | [Manual drive](07-manual-drive.md) | Smooth manual control; RC override and E-stop confirmed under motion |
| 8 | [Autonomous bring-up](08-autonomous.md) | A saved map, successful Nav2 goals, and an autonomous lap |

These steps map onto the staged bring-up protocol in
[safety.md §6](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first). Steps 4–6
are Stages 0–4 of that protocol; step 7 is Stage 5. **No stage begins until the previous
stage passes.**

## Prerequisites (whole build)

- All design documents reviewed — start with the [design overview](../design/overview.md).
- Basic hand tools, a soldering iron, a multimeter, and a bench power supply.
- Comfort with ROS 2 on Ubuntu 22.04 and flashing an Arduino.
- **Safety:** every powered test before "Manual drive" is performed **wheels-off** on a
  stand. Read [safety.md](../design/safety.md) before applying power to the vehicle.

!!! danger "Bench before vehicle; wheels-off before wheels-on; walking pace before anything faster."

    This is a 24 V two-seater with enough torque to injure someone. The staged protocol is
    not a suggestion — each stage exists because it catches a class of fault that is
    dangerous to discover at the next stage.

## What you are actually building

Three things happen to a stock ride-on vehicle:

1. **A steering servo appears where there was none.** The stock column is turned by hand or
   by a parent-remote gearmotor. MRider adds a gearmotor plus an *absolute* column angle
   sensor, and the Arduino Nano closes a position loop against it at ≥100 Hz — the
   "smart-servo" of [dbw.md ADR E](../design/dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision).
2. **Authority becomes explicit.** A DPDT relay MUX selects STOCK or DBW per motor circuit,
   defaulting (de-energized) to STOCK, and a hardwired E-stop cuts traction power. Nothing
   can drive the motors unless every layer permits it
   ([safety.md §1](../design/safety.md#1-authority-arbitration-who-is-allowed-to-drive-the-motors)).
3. **The vehicle becomes reversible.** Three inline connector taps — throttle, steering,
   power — intercept the stock harness without cutting it
   ([dbw.md §11.3](../design/dbw.md#113-3-tap-connector-spec-minimally-invasive)). Unplug
   the three taps and the vehicle is factory-stock again.

## Recording your build

Several steps produce values that are specific to *your* vehicle and must be written down:
column torque, wheel rollout, steering counts-per-degree, stall currents. Create
`config/calibration/` in your working copy and store one file per subsystem, each stamped
with date, operator, vehicle serial, and the git commit of the firmware in use — the index
is in [calibration.md §7](../design/calibration.md#7-calibration-artifact-index).

If you complete a step and the procedure here was wrong or incomplete, the edit link at the
top of the page goes straight to the source file. Corrections from real builds are the
single most valuable contribution to this guide.

---

## See also

- [Design overview & document index](../design/overview.md)
- [Learn curriculum](../learn/index.md)
