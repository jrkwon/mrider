# 1. BOM & Sourcing

**Goal:** acquire every part before touching the vehicle, at a known cost.

Order the components for Tier 1 and confirm long-lead items (vehicle, LiDAR, gearmotor) are
in hand. Cross-check quantities and connectors against the bill of materials.

- **Prerequisites:** budget decided; Tier 1 vs. Tier 2 timing understood.
- **Specification:** [design/bom.md](../design/bom.md)
- **Expected outcome:** all line items received; totals reconciled against the BOM.

!!! warning "Draft — not yet validated on hardware"

    This checklist is derived from [bom.md](../design/bom.md). No MRider build has been
    sourced yet, so vendor availability, current prices, and connector compatibility are
    **unconfirmed**. Prices in the BOM are estimates as of July 2026 and vary by retailer,
    coupon, and stock — verify at purchase.

---

## 1.1 Two purchase tiers, bought at different times

The BOM is split so the **perception spend follows the DBW gates**. If the steering loop fails
its accuracy gate at [bring-up Stage 1](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first),
you have not yet bought Tier 2.

| Tier | What it covers | When to order | Line items | With ~10% contingency |
|---|---|---|---:|---:|
| **Tier 1** | Vehicle + DBW core | Week 1 | $773 | ~$850 |
| **Tier 2** | LiDAR, camera, IMU | By week 10 | $168 | ~$185 |
| **Both** | | | **$941** | **~$1,035** |

This is down from ~$1,570 in the previous revision. See
[bom.md § Change record](../design/bom.md#change-record-why-the-total-fell-from-1570-to-1035)
for where the money went and what was deferred rather than deleted.

!!! tip "Already have an mrover rig?"

    Reusable: **Sabertooth 2x32**, drive encoder + shaft adapter, 3D-printed enclosures
    (though the controller cases need rework), and the laptop — roughly **−$173**.

    **Not reusable:** the Pixhawk 6C, PM02, Arduino Nano, and USB-TTL adapter. MRider's
    controller is a single Teensy 4.1
    ([D3](../design/adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07)). Those
    parts remain useful for other projects; this is a deliberate architectural departure, not
    a write-off.

    With a used vehicle, lab-reused Sabertooth and encoder, and printed mounts, the realistic
    floor is **~$620 all-in**.

## 1.2 Order long-lead items first

Order in this sequence. The first group gates everything else; the last group can be bought
at the hardware store the week you need it.

=== "Week 0 — order immediately"

    | Item | BOM # | Why it gates the build |
    |---|---|---|
    | Vehicle (24 V 2-seater ride-on) | 1 | Nothing can be measured until it arrives; seasonal stock |
    | Teensy 4.1 | 2 | Needed from step 4; cheap enough to buy a spare |
    | RC transmitter + receiver (SBUS) | 10 | Needed for step 4 override verification |
    | Hardware RC signal MUX | 9 | Safety-critical and easy to forget — see the warning below |

=== "Week 1 — after the vehicle arrives"

    | Item | BOM # | Why it waits |
    |---|---|---|
    | Steering gearmotor + encoder | 4 | **Sized from a measurement you cannot take yet** — see §1.3 |
    | Absolute steering angle sensor | 5 | Technology depends on measured shaft travel (§1.3) |
    | Steering shaft coupler / adapter | 13 | Depends on the actual column diameter |

=== "Anytime (Tier 1)"

    | Item | BOM # |
    |---|---|
    | Sabertooth 2x32 | 3 |
    | Drive encoder + 3.15→5 mm shaft adapter | 6 |
    | Relay MUX hardware (2× DPDT + sockets + flyback diodes + drive transistors) | 7 |
    | E-stop switch (latching mushroom, traction-rated) | 8 |
    | Isolated logic rail (12 V SLA + charger + 2× DC-DC) | 11 |
    | Wiring / connectors / fuses | 12 |
    | Mounts / 3D prints | 14 |

=== "By week 10 (Tier 2)"

    | Item | BOM # |
    |---|---|
    | 2D LiDAR (RPLIDAR A1M8) | 15 |
    | Front camera (USB 1080p) | 16 |
    | IMU (BNO085 class) | 17 |

!!! danger "The hardware RC signal MUX is not optional"

    Item #9 is the **condition on which the single-Teensy architecture was adopted**
    ([safety.md §1.2](../design/safety.md#12-live-override-inside-dbw-mode-two-layers)). With
    one MCU holding the steering loop, throttle, override, and arming, a firmware hang loses
    all four — unless override is a *wiring* property. Order it with the RC set, not later.
    It is $18 and it is the difference between a defensible safety story and a fragile one.

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

**Absolute steering angle sensor (#5)** — the default is an **AS5600-class magnetic encoder**
mounted **load-side**: downstream of the steering gearbox, on the kingpin/road-wheel axis or
the linkage, where total travel is only ±22.5°. Load-side mounting is the point —
it measures what the road wheels actually do, so gearbox backlash appears as *measured error*
rather than invisible bias
([ADR B](../design/dbw.md#5-adr-b-steering-angle-encoding)).

!!! danger "Measure shaft travel before ordering — this is a hard gate"

    The AS5600 is **single-turn absolute (0–360°)**. If the shaft it is mounted on rotates
    more than one turn lock-to-lock, it wraps and **silently** loses absolute meaning — a
    garbage angle feeding a position loop that drives a motor. This is FMEA row 2, severity 5.

    **Measure every candidate mounting shaft on the vehicle you actually bought.**

    - Shaft travel ≤ 340° → **AS5600**. Contactless, 12-bit, no wiper wear at the small
      high-duty-cycle oscillations a steering servo makes, no ADC noise, no ratiometric
      reference.
    - No accessible shaft under 340° → **single-turn conductive-plastic potentiometer**, the
      pre-registered fallback. Costs analog filtering and wiper wear, but maps monotonically
      across whatever travel its shaft sees.

    Budget for either — they are within a few dollars. Record the measurement in
    [calibration.md](../design/calibration.md).

    The AS5600 also needs a **diametrically magnetized magnet mounted concentric** to the
    sensed shaft, with the air gap inside spec. That mechanical precision is the main reason
    the pot fallback is retained. Check for magnetic interference from the steering motor
    during bench validation.

## 1.4 Substitution notes

| Item | Safe to substitute? | Constraint |
|---|---|---|
| Vehicle | Yes, within class | Must be **24 V, two-seater, dual rear motors, parent-remote class**, with an accessible steering column. Run the [vehicle.md §3 verification checklist](../design/vehicle.md) on whatever you buy. |
| Teensy 4.1 | Not recommended | A Teensy 4.0 fits the peripheral budget, but 4.1 is $8 more for headroom. **Do not drop to an ESG32/AVR-class part** — the 600 MHz Cortex-M7's timing determinism and 4 hardware quadrature decoders are load-bearing ([dbw.md §9](../design/dbw.md#9-teensy-41-firmware-platform-and-version-pinning)). |
| Sabertooth 2x32 | Only for higher current | **Do not substitute a bare H-bridge to save money.** RS-550-class drive motors stall at 30–60 A each and the pair is paralleled onto one channel; the Sabertooth provides current limiting, thermal protection, and the **serial timeout** backing [failsafe row 6](../design/safety.md#2-failsafe-matrix). Verify paralleled stall current against 32 A/channel ([dbw.md §7](../design/dbw.md#7-throttle-path)). |
| Drive encoder | Yes | Any quadrature/Hall encoder. **Record the actual PPR — do not assume 52.** The source project conflicts with itself (52 PPR in `code.ino:27` vs 16 PPR in its own BOM, finding F7). The roll-out calibration in step 6 bypasses PPR anyway. |
| Camera | Yes for semester 1 | A $30 rolling-shutter USB camera is fine for SLAM and teleop. **Behavior cloning (phase 2) needs a global shutter** — rolling shutter smears during turns and corrupts steering labels. Budget +$150 then; do not train on rolling-shutter data and attribute the result to the platform. |
| LiDAR | Yes | `rplidar_ros` is in apt for Humble. Swapping to YDLidar or another vendor means swapping the ROS 2 driver ([software.md §2](../design/software.md#2-ros-2-stack-reused-adapted-new)). |
| RC TX/RX | Yes | Must have **SBUS output plus a spare channel** to drive the hardware signal MUX. No longer needs to be PX4-bindable. This is your live override authority — do not economize here. |
| Hardware RC signal MUX | Within class | Any servo-signal multiplexer that selects between two PWM sources on an RC channel. **Do not omit** — see §1.2. |
| IMU | Yes | Any 9-DoF publishing `sensor_msgs/Imu`. Onboard fusion (BNO085 class) saves work; the estimator is `robot_localization` either way. |
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
  requirement of [dbw.md §11.5](../design/dbw.md#115-3-tap-connector-spec-minimally-invasive)
- Dupont / JST-XH pigtails for Teensy ↔ angle sensor (I²C: SDA/SCL/3V3/GND), Teensy ↔ steering
  encoder, Teensy ↔ drive encoder
- Servo-style 3-wire leads: Teensy → signal MUX master inputs (×2), RC receiver → MUX slave
  inputs (×2), MUX outputs → Sabertooth S1/S2 (×2)
- Servo-style 3-wire leads for the RC receiver → signal MUX → Sabertooth
- USB cable, Teensy → laptop (this carries **both** command and feedback — use a good one; a
  marginal cable is now a vehicle-safety issue, see
  [failsafe row 2](../design/safety.md#2-failsafe-matrix))
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
| 2 | Teensy 4.1 | ☐ | ☐ | | *(buy a spare — it is $32)* |
| 3 | Sabertooth 2x32 | ☐ | ☐ | | |
| 4 | Steering gearmotor + encoder | ☐ | ☐ | | *(record rated torque + gear ratio)* |
| 5 | Absolute angle sensor | ☐ | ☐ | | *(**record measured shaft travel** + which tech and why)* |
| 6 | Drive encoder + shaft adapter | ☐ | ☐ | | *(record **measured** PPR — do not assume 52)* |
| 7 | Relay MUX hardware | ☐ | ☐ | | *(record relay contact rating)* |
| 8 | E-stop switch | ☐ | ☐ | | *(record current rating)* |
| 9 | Hardware RC signal MUX | ☐ | ☐ | | *(**safety-critical** — record part + channel count)* |
| 10 | RC transmitter + receiver | ☐ | ☐ | | *(confirm SBUS out + a spare channel for the MUX)* |
| 11 | Isolated logic rail (SLA + charger + DC-DC) | ☐ | ☐ | | *(record capacity + rail voltages)* |
| 12 | Wiring / connectors / fuses | ☐ | ☐ | | |
| 13 | Steering coupler / adapter + magnet mount | ☐ | ☐ | | *(record column diameter)* |
| 14 | Mounts / 3D prints | ☐ | ☐ | | |
| 15 | 2D LiDAR *(Tier 2)* | ☐ | ☐ | | |
| 16 | Front camera *(Tier 2)* | ☐ | ☐ | | *(rolling shutter OK for semester 1)* |
| 17 | IMU *(Tier 2)* | ☐ | ☐ | | |
| — | Laptop | reuse | ☐ | — | *(record GPU, RAM, USB3 ports, battery hours)* |

**Totals:** estimated $ ______ · actual $ ______ · delta ______

Store the completed table as `config/calibration/bom_asbuilt.md`, stamped with date and
operator per [calibration.md §7](../design/calibration.md#7-calibration-artifact-index).

## 1.7 Gate to step 2

- [ ] Budget approved; Tier 2 timing understood (order by week 10)
- [ ] All week-0 long-lead items received
- [ ] Vehicle received and its model/serial recorded
- [ ] Column torque measured, gearmotor ordered against it with ≥2× margin
- [ ] **Candidate sensor-shaft travel measured; angle-sensor technology confirmed against the ≤ 340° rule**
- [ ] **Hardware RC signal MUX in hand** — the safety chain cannot be built without it
- [ ] Paralleled drive-motor stall current checked against the Sabertooth 32 A/channel rating
- [ ] Drive-encoder PPR measured on the part actually fitted (not assumed)
- [ ] Receiving table complete; totals reconciled

---

**Next:** [2. Vehicle prep & mechanical](02-mechanical.md)
