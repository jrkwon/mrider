# Order Log

**A working record, meant to be edited.** Fill it in as you place orders and as parts arrive.
Unlike the [BOM](design/bom.md), which is a *specification*, this page is the *history* of
what was actually bought, from whom, for how much, and what was substituted.

Keep it honest even when it is unflattering — a substitution that seemed harmless and later
caused a rebuild is exactly the entry the next person needs.

- **What to buy and why:** [design/bom.md](design/bom.md)
- **How to buy it, substitution rules, connector lists:** [build/01](build/01-bom-sourcing.md)
- **This page:** what you actually ordered

!!! note "Currency"

    BOM estimates are **USD, August 2026**. Record the **amount you actually paid in the
    currency you paid it in**, and put the USD equivalent in brackets so the totals still
    reconcile — e.g. `₩229,000 ($165)`.

---

## Status at a glance

Update as you go.

| Batch | What | Est. $ | Actual $ | Ordered | Received |
|---|---|---:|---:|:---:|:---:|
| **A** | Order now — nothing gates these | 608 | | ☐ | ☐ |
| **B** | After the vehicle arrives and is measured | 70 | | ☐ | ☐ |
| **C** | Perception — by week 10 | 168 | | ☐ | ☐ |
| | **Line items** | **846** | | | |
| | *With ~10% contingency* | *~931* | | | |

Contingency covers shipping, tax, fasteners, and the odd stripped gear. It is not a line item;
it is the number to have approved.

---

## Batch A — order now

Nothing in this batch depends on a measurement. **Order the vehicle first regardless** —
Batch B cannot be specified until it arrives, so it is the long pole.

| # | Item | Est $ | Vendor | Ordered | Actual | Received | Notes |
|---|------|------:|--------|---------|-------:|----------|-------|
| 1 | Vehicle — 12 V single-seat ride-on | 165 | | | | | *record model + serial* |
| 2 | Teensy 4.1 | 32 | | | | | *buy a spare* |
| 3 | Sabertooth 2x32 | 125 | | | | | |
| 6 | Drive encoder + 3.15→5 mm adapter | 18 | | | | | *record measured PPR* |
| 7 | Relay MUX hardware | 25 | | | | | *record contact rating* |
| 8 | E-stop, latching mushroom | 15 | | | | | *record current rating* |
| 9 | Pololu #2806 RC servo MUX | 18 | | | | | *safety-critical* |
| 10 | RC transmitter + receiver (SBUS) | 55 | | | | | *confirm SBUS + spare channel* |
| 11 | Isolated logic rail — SLA + charger + 2× DC-DC | 45 | | | | | *record capacity + rail V* |
| 12 | Wiring / connectors / fuses | 40 | | | | | |
| 14 | Mounts / 3D prints | 30 | | | | | |
| 15 | USB gamepad, Xbox layout | 40 | | | | | *record button/axis map if not Xbox* |
| | **Batch A** | **608** | | | | | |

!!! danger "Do not let #9 slip to a later order"

    The Pololu RC signal MUX is **$18 and it is the condition the single-Teensy architecture
    was adopted under** ([safety.md §1.2](design/safety.md#12-live-override-inside-dbw-mode-two-layers)).
    With one MCU holding steering, throttle, override and arming, a firmware hang loses all
    four — unless override is a *wiring* property. Order it with the RC set, in this batch.

!!! warning "#15 and #10 are not the same thing"

    The **gamepad (#15)** is a software input: `joy_node` reads it and its Twist goes through
    `twist_mux`, so a firmware or laptop hang takes it down too.

    The **RC transmitter (#10)** is the hardware override, switching servo pulses through the
    MUX with no software in the path at all.

    Both are needed. Buying only one leaves either no convenient teleop, or no
    firmware-independent override.

---

## Batch B — only after the vehicle is measured

**These three cannot be specified from a catalogue.** Ordering them with Batch A is the
documented way to waste money on this build. Record the measurements in §Measurements below
*before* ordering, and put the value that decided each choice in the Notes column.

| # | Item | Est $ | Gate — measure this first | Vendor | Ordered | Actual | Received |
|---|------|------:|---------------------------|--------|---------|-------:|----------|
| 4 | Steering gearmotor + encoder | 35 | Column torque **τ**, size at **≥2×** | | | | |
| 5 | Absolute angle sensor (AS5600 **or** pot) | 20 | Lock-to-lock travel — **≤340° ⇒ AS5600** | | | | |
| 13 | Steering coupler + magnet mount | 15 | Column / kingpin shaft **diameter** | | | | |
| | **Batch B** | **70** | | | | | |

---

## Measurements that unblock Batch B

Take these on the vehicle you actually bought. Fill in before ordering.

### M1 — Steering column torque → sizes #4

Procedure: [dbw.md §2.2](design/dbw.md#22-torque-measurement-procedure-before-sizing-the-gearmotor).
Vehicle at **full load** (laptop + LiDAR + payload), on the **target surface**, spring scale on
the rim, peak force turning lock-to-lock **while stationary** — that is the worst case.

| Field | Value |
|---|---|
| Surface tested | |
| Lever radius `r` (m) | |
| Peak force `F` (N) | |
| **τ_column = F × r** (N·m) | |
| **Required rated torque (≥ 2 × τ)** | |
| Motor selected (model, rated torque, ratio) | |
| Date / by | |

!!! note "If no suitable encoder-gearmotor can be sourced"

    The documented fallback is a **12 V automotive wiper motor**. Two consequences you must
    accept and re-check against [safety.md](design/safety.md) before the vehicle touches the
    ground: its worm gear is largely **non-back-drivable**, so on power loss the steering
    **holds** rather than freewheels — which invalidates the freewheel analysis — and it
    rarely has a usable shaft encoder, making the absolute sensor the sole angle source.
    Record the choice here if you take it.

### M2 — Sensor shaft travel → decides #5

**This is a hard gate, not a preference.** The AS5600 is single-turn absolute (0–360°). If the
shaft it sits on rotates past one turn, it **wraps and silently loses absolute meaning** — a
garbage angle feeding a position loop that drives a motor. That is FMEA row 2, severity 5.

Measure **every** candidate mounting shaft, not just the intended one.

| Candidate shaft | Lock-to-lock travel (°) | ≤340°? | Chosen? |
|---|---|:---:|:---:|
| Kingpin / road-wheel axis (the ADR B default) | | ☐ | ☐ |
| Steering linkage / tie-rod arm | | ☐ | ☐ |
| Steering column | | ☐ | ☐ |

| Field | Value |
|---|---|
| **Technology chosen** (AS5600 / potentiometer) | |
| **Because** (the number that decided it) | |
| Date / by | |

### M3 — Shaft diameter → sizes #13

| Field | Value |
|---|---|
| Column diameter (mm) | |
| Kingpin / sensed shaft diameter (mm) | |
| Coupler type selected | |
| Magnet mount approach (concentricity + air gap) | |
| Date / by | |

---

## Batch C — perception, by week 10

Deliberately last. If the steering loop fails its accuracy gate at
[bench Stage 1](design/safety.md#6-bring-up-protocol-staged-wheels-off-first), this money has
not been spent yet — that sequencing is the entire point of the two-tier split.

| # | Item | Est $ | Vendor | Ordered | Actual | Received | Notes |
|---|------|------:|--------|---------|-------:|----------|-------|
| 16 | 2D LiDAR — RPLIDAR A1M8 | 110 | | | | | |
| 17 | Front camera — USB 1080p wide-FOV | 30 | | | | | *rolling shutter is fine for now* |
| 18 | IMU — BNO085 class | 28 | | | | | |
| | **Batch C** | **168** | | | | | |

!!! note "The camera is a knowing compromise"

    Rolling shutter is fine for SLAM and teleop. **Behavior cloning (phase 2) needs a global
    shutter** — rolling shutter smears during turns and corrupts the steering labels. Budget
    **+$150** then. Do not train a policy on rolling-shutter data and attribute the result to
    the platform.

---

## Measurements to record on arrival

Values that must come from the part in your hand, not the datasheet or the source project.

| Measurement | Value | Why it matters |
|---|---|---|
| **Drive encoder PPR** (measured) | | The source project contradicts itself — 52 PPR in firmware vs 16 PPR in its own BOM (finding F7). **Do not inherit either.** The [roll-out calibration](design/calibration.md#2-drive-distance-encoder-ticksmeters) is authoritative and bypasses PPR entirely |
| Wheel diameter, loaded (m) | | Ticks→metres |
| Wheelbase (m) | | Replaces the **estimated** 0.63 in `mitt_dimensions.yaml` |
| Track width (m) | | Replaces the estimated 0.46 |
| Vehicle mass, bare (kg) | | Replaces the estimated 8.0 |
| Steering limit, mechanical (°) | | Replaces the assumed ±22.5 — **and changes the Nav2 turning radius** |

!!! danger "Every dimension in the twin is currently an estimate"

    `mitt_description/config/mitt_dimensions.yaml` is populated with values derived from the
    vendor's 98×56×47 cm listing, each marked `TODO measure`. The URDF has no geometric
    literals, so updating that file updates the model, the controller config, and the body
    mesh scale together.

    Two of these propagate further than they look. Wheelbase and steer limit set
    `R_min = wheelbase / tan(steer_limit)` — currently **1.52 m** — which is used in
    `nav2_params.yaml` **twice** (`minimum_turning_radius` on the planner and
    `min_turning_radius` on the controller). Re-derive both when you measure, or Nav2 will be
    planning for a vehicle you do not have.

---

## Substitution log

Record anything bought that differs from the BOM spec, and why. This is what makes the build
reproducible rather than folklore.

| BOM # | Specified | Bought instead | Why | Consequence checked? |
|---|---|---|---|---|
| | | | | |
| | | | | |

!!! warning "Substitutions with teeth"

    Three where "close enough" is not:

    - **#3 Sabertooth → bare H-bridge.** Looks like a $110 saving. The Sabertooth's current
      limiting, thermal protection and R/C signal-loss timeout are load-bearing in
      [failsafe row 6](design/safety.md#2-failsafe-matrix). A BTS7960 provides none of them.
    - **#8 E-stop → signal-rated button.** It must switch actual traction current or a
      contactor coil. A signal-rated mushroom **will weld shut**, which fails exactly when
      you need it.
    - **#2 Teensy → ESP32/AVR.** The 600 MHz M7's timing determinism and **four hardware
      quadrature decoders** are why the whole DBW loop fits on one MCU.

---

## Reconciliation

Fill in when ordering is complete.

| | Estimated | Actual | Δ |
|---|---:|---:|---:|
| Batch A | 608 | | |
| Batch B | 70 | | |
| Batch C | 168 | | |
| Shipping / tax / duties | — | | |
| **Total** | **846** | | |

**Notes on variance** — what came in over or under, and whether it was price drift, shipping,
or a spec change:

> _(write here)_

!!! tip "Your real numbers are more useful than these estimates"

    The BOM figures are budgeting estimates from a single retailer survey. Once this table is
    filled in, the actuals are worth folding back into
    [design/bom.md](design/bom.md) so the next build starts from evidence.
