# 1. BOM & Sourcing

**Goal:** acquire every part before touching the vehicle, at a known cost.

Order the components for your chosen tier (minimum vs. full) and confirm long-lead
items (flight controller, LiDAR, gearmotor) are in hand. Cross-check quantities and
connectors against the bill of materials.

- **Prerequisites:** budget decided; tier (minimum / full) chosen.
- **Specification:** [design/bom.md](../design/bom.md)
- **Expected outcome:** all line items received; totals reconciled against the BOM.

!!! warning "Draft — not yet validated on hardware"

    This checklist is derived from [bom.md](../design/bom.md). No MRider build has been
    sourced yet, so vendor availability, current prices, and connector compatibility are
    **unconfirmed**. Prices in the BOM are estimates as of July 2026 and vary by retailer,
    coupon, and stock — verify at purchase.

---

## 1.1 Choose your tier first

Two tiers are specified. The delta is **$470**, entirely in LiDAR (+$200), camera (+$170),
GNSS (+$90), and minor wiring/mounts (+$10).

| Tier | What you get | Line items | With ~10% contingency |
|---|---|---:|---:|
| **Minimum** | YDLidar G4, Arducam AR0234 global-shutter, no GNSS | $1,429 | ~$1,570 |
| **Full** | RPLidar S3 (ToF/IP65), RealSense D435i, GNSS | $1,899 | ~$2,090 |

**Pick minimum unless you have a specific reason not to.** The minimum tier is fully capable
of mapping, navigation, and behavior cloning. The full tier buys outdoor robustness (IP65
LiDAR), depth sensing, and the RTK growth path — none of which the core curriculum requires.

!!! tip "Already have an mrover rig?"

    If your lab is converting an existing [mrover](https://github.com/jrkwon/mrover) build,
    the Pixhawk, Sabertooth, Nano, USB-TTL, drive encoder, YDLidar G4, 3D-printed enclosures,
    and laptop are typically already owned. The genuinely new purchase list — vehicle,
    steering gearmotor, angle sensor, relay MUX, E-stop, RC set, camera, couplers, wiring,
    mounts — comes to roughly **$780** before contingency. See
    [bom.md § Reuse Notes](../design/bom.md#reuse-notes-lab-already-has-an-mrover-build).

## 1.2 Order long-lead items first

Order in this sequence. The first group gates everything else; the last group can be bought
at the hardware store the week you need it.

=== "Week 0 — order immediately"

    | Item | BOM # | Why it gates the build |
    |---|---|---|
    | Vehicle (24 V 2-seater ride-on) | 1 | Nothing can be measured until it arrives; seasonal stock |
    | Pixhawk 6C + PM02 power module | 2 | Flight-controller stock is erratic; needed from step 4 |
    | 2D LiDAR | 12 | Long lead; needed from step 8 but too risky to defer |
    | RC transmitter + receiver | 11 | Needed for step 4 RC-override verification |

=== "Week 1 — after the vehicle arrives"

    | Item | BOM # | Why it waits |
    |---|---|---|
    | Steering gearmotor + encoder | 4 | **Sized from a measurement you cannot take yet** — see §1.3 |
    | Absolute steering angle sensor | 5 | Choice depends on measured column travel (§1.3) |
    | Steering shaft coupler / adapter | 16 | Depends on the actual column diameter |

=== "Anytime"

    | Item | BOM # |
    |---|---|
    | Sabertooth 2x32 | 3 |
    | Drive encoder + 3.15→5 mm shaft adapter | 6 |
    | Arduino Nano V3 | 7 |
    | USB-TTL serial adapter (3.3 V) | 8 |
    | Relay MUX hardware (2× DPDT + sockets + flyback diodes + drive transistors) | 9 |
    | E-stop switch (latching mushroom, traction-rated) | 10 |
    | Front camera | 13 |
    | GNSS module (full tier only) | 14 |
    | Wiring / connectors / fuses | 15 |
    | Mounts / 3D prints | 17 |

## 1.3 Two parts you must not order blind

Two line items depend on measurements taken on the vehicle you actually bought. Ordering
them in week 0 is the most common way to waste money on this build.

**Steering gearmotor (#4)** — sized from the *measured* column torque, with a **≥2× margin**
at rated (not stall) torque. The measurement procedure is
[dbw.md §2.2](../design/dbw.md#22-torque-measurement-procedure-before-sizing-the-gearmotor):
vehicle at full load, on the target surface, spring scale on the rim, record peak force `F`
to turn lock-to-lock while stationary, then `τ_column = F × r`.

!!! note "Fallback if you cannot source a suitable encoder-gearmotor"

    A **12 V automotive wiper motor** is the documented fallback — high stall torque
    (typically 10–30 N·m), built-in worm gearing. Two consequences you must accept and
    re-check against [safety.md](../design/safety.md):

    1. The worm gear is largely **non-back-drivable**, so on power loss the steering
       **holds** rather than freewheels. This invalidates the freewheel analysis in
       [safety.md §4](../design/safety.md#4-steering-motor-power-rail-assignment-and-power-loss-behavior-pinned)
       and must be re-evaluated before the vehicle touches the ground.
    2. Wiper motors rarely have a usable shaft encoder, so the absolute column sensor
       becomes the **sole** angle source. Acceptable — [ADR B](../design/dbw.md#5-adr-b-steering-angle-encoding)
       already makes it authoritative.

**Absolute steering angle sensor (#5)** — the default is a **single-turn conductive-plastic
potentiometer** coupled 1:1 to the column. Before ordering, measure the column's total
lock-to-lock rotation. If it stays comfortably inside one turn (expected, since road-wheel
travel is only ±22.5°), the pot is correct. If the column is geared such that it exceeds one
turn, you need the multi-turn magnetic fallback — the escape hatch in
[dbw.md §6](../design/dbw.md#6-adr-angle-sensor-technology-potentiometer-vs-as5600-class-magnetic-encoder).

!!! danger "Do not substitute an AS5600 without checking column travel"

    The AS5600 is attractive — contactless, 12-bit, I²C, no wear — but it is **single-turn
    absolute (0–360°)**. If the column rotates more than 360° lock-to-lock, it wraps and
    silently loses absolute meaning. That failure is a garbage angle reading feeding a
    position loop that drives a motor.

## 1.4 Substitution notes

| Item | Safe to substitute? | Constraint |
|---|---|---|
| Vehicle | Yes, within class | Must be **24 V, two-seater, dual rear motors, parent-remote class**, with an accessible steering column. Run the [vehicle.md §3 verification checklist](../design/vehicle.md) on whatever you buy. |
| Pixhawk 6C | Not recommended | The PX4 rover airframe behavior and `MANUAL_CONTROL.roll` → servo-PWM mapping are validated on 6C. Another FC means re-validating [dbw.md §9](../design/dbw.md#9-pixhawk-6c-px4-rover-configuration-and-version-pinning). |
| Sabertooth 2x32 | Only for higher current | **Verify paralleled drive-motor stall current against the 32 A/channel rating.** If the pair can exceed 32 A stalled, current-limit in the Sabertooth config or pick lower-draw motors ([dbw.md §7](../design/dbw.md#7-throttle-path)). |
| Drive encoder | Yes | Any quadrature/Hall encoder. **Record the actual PPR** — the firmware default is 52 PPR (`code.ino:27`) and the roll-out calibration in step 6 bypasses gear-ratio guessing anyway. |
| Camera | Yes, if global-shutter | Behavior cloning needs a **global shutter**; a rolling-shutter webcam will smear during turns and corrupt the steering labels. |
| LiDAR | Yes | Swapping away from YDLidar means swapping the ROS 2 driver ([software.md §2](../design/software.md#2-ros-2-stack-reused-adapted-new)). |
| RC TX/RX | Yes | Must be **PX4-bindable** (SBUS/ACCESS/CRSF class). This is your live override authority — do not economize here. |
| E-stop | No | Must be **traction-rated** (switching the actual motor current, or a contactor coil). A signal-rated mushroom button will weld. |

## 1.5 Connector and consumable list

Not individually itemized in the BOM (they fall under line 15, wiring/connectors/fuses), but
you need all of them before step 3:

**Traction side (24 V, high current)**

- XT60 or equivalent for the battery power tap — sized for peak drive current
- Ring/spade terminals for Sabertooth B+/B− and M1/M2 terminals
- Inline blade-fuse holders, one per rail (values from the
  [architecture.md power tree](../design/architecture.md#5-power-tree-and-safetyauthority-chain))
- Silicone-insulated stranded wire, gauge sized for stall current, not nominal
- Heatshrink in at least two sizes

**Signal side (logic level)**

- Keyed inline connectors ×3 for the throttle, steering, and power taps — the reversibility
  requirement of [dbw.md §11.3](../design/dbw.md#113-3-tap-connector-spec-minimally-invasive)
- Dupont / JST-XH pigtails for Nano ↔ Sabertooth S1, Nano ↔ pot, Nano ↔ drive encoder
- Servo-style 3-wire leads for PX4 → Sabertooth S2
- Flyback diodes (1N4007 class) across each relay coil
- Logic-level MOSFETs or transistors + base resistors for the MUX coil drivers

**Tools and consumables**

- Ratcheting crimper matched to your terminal type — hand-squeezed crimps fail under vibration
- Multimeter with continuity beep and a 20 A current range
- Bench power supply with adjustable **current limit** (essential for step 4 —
  it is what turns a runaway position loop into a harmless buzz)
- Digital angle gauge / inclinometer (step 6 steering calibration)
- Spring scale, 0–20 kg (column torque measurement, §1.3)
- Tape measure and a straightedge long enough to span both front tires

## 1.6 Receiving checklist

As parts arrive, reconcile against the BOM. Record actuals — your totals will not match the
estimates, and the next person to build one needs your real numbers.

| # | Item | Ordered | Received | Actual $ | Notes / substitution |
|---|---|---|---|---|---|
| 1 | Vehicle (24 V 2-seater) | ☐ | ☐ | | *(record model + serial)* |
| 2 | Pixhawk 6C + PM02 | ☐ | ☐ | | |
| 3 | Sabertooth 2x32 | ☐ | ☐ | | |
| 4 | Steering gearmotor + encoder | ☐ | ☐ | | *(record rated torque + gear ratio)* |
| 5 | Absolute angle sensor | ☐ | ☐ | | *(pot or magnetic — record which and why)* |
| 6 | Drive encoder + shaft adapter | ☐ | ☐ | | *(record PPR)* |
| 7 | Arduino Nano V3 | ☐ | ☐ | | |
| 8 | USB-TTL serial adapter | ☐ | ☐ | | |
| 9 | Relay MUX hardware | ☐ | ☐ | | *(record relay contact rating)* |
| 10 | E-stop switch | ☐ | ☐ | | *(record current rating)* |
| 11 | RC transmitter + receiver | ☐ | ☐ | | *(record protocol: SBUS / ACCESS / CRSF)* |
| 12 | 2D LiDAR | ☐ | ☐ | | |
| 13 | Front camera | ☐ | ☐ | | *(confirm global shutter)* |
| 14 | GNSS module (full tier) | ☐ | ☐ | | |
| 15 | Wiring / connectors / fuses | ☐ | ☐ | | |
| 16 | Steering coupler / adapter | ☐ | ☐ | | *(record column diameter)* |
| 17 | Mounts / 3D prints | ☐ | ☐ | | |
| — | Laptop | reuse | ☐ | — | *(record GPU, RAM, USB3 ports, battery hours)* |

**Totals:** estimated $ ______ · actual $ ______ · delta ______

Store the completed table as `config/calibration/bom_asbuilt.md`, stamped with date and
operator per [calibration.md §7](../design/calibration.md#7-calibration-artifact-index).

## 1.7 Gate to step 2

- [ ] Tier chosen and budget approved
- [ ] All week-0 long-lead items received
- [ ] Vehicle received and its model/serial recorded
- [ ] Column torque measured, gearmotor ordered against it with ≥2× margin
- [ ] Column lock-to-lock travel measured, angle sensor technology confirmed
- [ ] Paralleled drive-motor stall current checked against the Sabertooth 32 A/channel rating
- [ ] Receiving table complete; totals reconciled

---

**Next:** [2. Vehicle prep & mechanical](02-mechanical.md)
