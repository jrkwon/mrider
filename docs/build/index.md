# MRider Build Guide

A step-by-step guide to converting a kids ride-on electric vehicle ("MITT") into a
drive-by-wire (DBW), self-driving-ready platform. The guide is organized
RoboRacer-style: work through the sections **in order**, from sourcing parts to an
autonomous lap. Each section states its goal, prerequisites, and expected outcome,
and links to the design document that specifies the details.

> [!WARNING]
> **Draft — not yet validated on hardware**
>
> These procedures are derived from the design documents. Except for the vehicle #1 teardown
> on 2026-11-06, they have **not** been performed on a physical vehicle. Every blank in a
> record sheet's **Yours** column must be filled and these pages updated before they are used
> for teaching or external replication — see [Reference and Yours](#reference-and-yours). The
> design documents remain the authoritative specification; where a build step and a design
> document disagree, the design document is correct.

## The eight steps

| # | Step | Gate you must pass to continue |
|---|---|---|
| 1 | [BOM & sourcing](01-bom-sourcing.md) | Every line item received and reconciled |
| 2 | [Vehicle prep & mechanical](02-mechanical.md) | Actuator and sensors mounted; stock steering still reassemblable |
| 3 | [Electrical & wiring](03-electrical.md) | Harness continuity-checked; relay defaults to STOCK; E-stop cuts traction only |
| 4 | [Firmware bring-up](04-firmware.md) | Teensy closes a bench steering loop and emits servo PWM through the signal MUX; RC override verified |
| 5 | [Software install](05-software.md) | ROS 2 ↔ Teensy over micro-ROS; feedback frames streaming; TF tree populated |
| 6 | [Bench test & calibration](06-bench-test.md) | All failsafes pass wheels-off; calibration constants recorded |
| 7 | [Manual drive](07-manual-drive.md) | Smooth manual control; RC override and E-stop confirmed under motion |
| 8 | [Autonomous bring-up](08-autonomous.md) | A saved map, successful Nav2 goals, and an autonomous lap |

These steps map onto the staged bring-up protocol in
[safety.md §6](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first). Steps 4–6
are Stages 0–4 of that protocol; step 7 is Stage 5. **No stage begins until the previous
stage passes.**

## The whole vehicle on one page

Every other figure in this guide is a close-up. This one is the map they are close-ups **of** —
every box, what joins it to what, and which of them the vehicle already came with.

[![MRider system overview: five groups. The vehicle as delivered holds the traction pack, the
stock inline protector, the stock ECU with its four sockets, the steering gearmotor and the
paralleled rear motors. The power box holds the 25 A fuse, XT60, E-stop contactor and button,
the barrier block, the four-pole relay MUX and the motor driver. The logic box holds the
isolated LiFePO4 pack, two UBECs, the Teensy on its signal perfboard, the RC servo MUX and the
RC receiver. Sensors and the autonomy laptop hang off those. Edges are coloured by what the
wire carries: traction, authority through the MUX, logic rail, signal and
USB](../images/system-overview.svg)](../images/system-overview.svg)

**Generated** — [`scripts/gen_system_figure.py`](https://github.com/jrkwon/mrider/blob/main/scripts/gen_system_figure.py).
*Edit the script and re-run it; do not edit the SVG.*

> [!NOTE]
> **It names parts on purpose, and [architecture.md](../design/architecture.md) does not**
>
> The design-side block diagram says *"traction battery pack"* and *"motor driver"* so that it
> does not go stale when a part changes — and it did not, when the Sabertooth was cancelled.
> This figure is the opposite document: it names the actual part, the actual pin and the actual
> tap, so a builder can trace one wire end to end without opening six pages.
>
> **The two are allowed to look different. They are not allowed to disagree about what connects
> to what.** The generator asserts that every `#n` it prints is a real line in the
> [Order Log](../order-log.md), so a figure that cites procurement cannot quietly drift from it.

## One sheet to carry with you

The record sheets are spread across eight pages, and a blank nobody is standing in front of is
a blank nobody fills. So the measurements that block **a cut, a print or a solder joint** — not
every row, just those — are collected on **one printable page**, grouped by where the
measurement is taken rather than by which step needs it, because you take them with a caliper
in your hand and not with a document open.

[![MRider measurement sheet: a single printable page listing every outstanding measurement on
the build, grouped by where it is taken — deck and lid, drive encoder, steering, sensors,
electronics and electrical checks — each row giving the quantity, a blank to write in, and one
line on what it unblocks](../images/measurement-sheet.svg)](../images/measurement-sheet.svg)

*This sheet was edited three times and linked from nowhere until 2026-11-07, which is why
[`check_docs.sh`](https://github.com/jrkwon/mrider/blob/main/scripts/check_docs.sh) now fails
on a figure no page references.*

## Prerequisites (whole build)

- All design documents reviewed — start with the [design overview](../design/overview.md).
- Basic hand tools, a soldering iron, a multimeter, and a bench power supply.
- Comfort with ROS 2 on Ubuntu 22.04 and flashing an Arduino.
- **Safety:** every powered test before "Manual drive" is performed **wheels-off** on a
  stand. Read [safety.md](../design/safety.md) before applying power to the vehicle.

> [!CAUTION]
> **Bench before vehicle; wheels-off before wheels-on; walking pace before anything faster.**
>
> This vehicle is geared roughly 120:1 at the wheel and has enough torque to injure someone —
> the pack voltage is not what makes it dangerous. The staged protocol is
> not a suggestion — each stage exists because it catches a class of fault that is
> dangerous to discover at the next stage.

## What you are actually building

Three things happen to a stock ride-on vehicle:

1. **A steering servo appears where there was none.** The stock column is turned by hand or
   by a parent-remote gearmotor. MRider adds a gearmotor plus an *absolute* column angle
   sensor, and the Teensy closes a position loop against it at ≥ 200 Hz — the
   "smart-servo" of [dbw.md ADR E](../design/dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision).
2. **Authority becomes explicit.** A DPDT relay MUX selects STOCK or DBW per motor circuit,
   defaulting (de-energized) to STOCK, and a hardwired E-stop cuts traction power. Nothing
   can drive the motors unless every layer permits it
   ([safety.md §1](../design/safety.md#1-authority-arbitration-who-is-allowed-to-drive-the-motors)).
3. **The vehicle becomes reversible.** Three inline connector taps — throttle, steering,
   power — intercept the stock harness without cutting it
   ([dbw.md §11.3](../design/dbw.md#115-3-tap-connector-spec-minimally-invasive)). Unplug
   the three taps and the vehicle is factory-stock again.

## Recording your build

### Reference and Yours

Every record sheet in these pages has the same two columns, and they mean different things.

| Column | What goes in it |
|---|---|
| **Reference** | What vehicle #1 measured, or the spec or limit the value must satisfy. **Filled in already** — never by you. A dash with a parenthetical says *why* there is no reference, which is information, not an omission. |
| **Yours** | Blank. Your vehicle's measurement. |

**A reference is not an expected answer.** Where it is a vehicle #1 measurement it is one
sample, and your vehicle may legitimately differ — the three were not built to a tolerance.
Where it is a **limit** (`< 30 A`, `≤ 340°`) a disagreement is a fault; where it is a
*(nominal)* or *(target)* a disagreement is a question. The *why that reference* column says
which, so you never have to guess whether a mismatch matters.

**Reference columns are sometimes named after their source** rather than "Reference" —
[the Nav2 table](08-autonomous.md#84-phase-c-nav2-goals) uses
*B-MROVER value*, because knowing the number came from the small rover is the whole reason
not to copy it.

**Some sheets have no Reference column, and say so.** Those are **worksheets**: their rows are
samples rather than quantities — five steering calibration points, three odometry runs, four
lap attempts, one pose per sensor. A per-row reference would be a category error there, so the
acceptance criterion sits above the table instead, where the blanks are.

Vehicle #1's references are sparse, and the honest reason is in the dashes: the three vehicles
went to the teams in the week of **2026-11-02**, so what was never measured before then cannot
be measured now. Filling a *Yours* column is therefore not homework duplicating a known answer.
For most rows it is the first time anyone has measured the thing at all.

### Where the files go

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
