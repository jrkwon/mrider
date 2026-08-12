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
| 3 | Sabertooth 2x32 | 125 | | | | | *see stall-current note below* |
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

### Sourcing — Korea (checked 2026-08-12)

Prices at Korean distributors are quoted **부가세 별도 (ex-VAT)** — add 10%. Lead times are the
vendor's own estimate, not a promise.

| # | Item | Source | Price seen | Verified? |
|---|------|--------|-----------|-----------|
| 1 | Vehicle | daehotoys | ₩229,000 | you found it |
| 2 | Teensy 4.1 | **Eleparts** — SparkFun `20359` "TEENSY 4.1 WITHOUT ETHERNET" | ₩52,182 ex-VAT (~₩57,400) | ✅ listed, ~6 d |
| 3 | Sabertooth 2x32 | **Import** — [Dimension Engineering](https://www.dimensionengineering.com/products/sabertooth2x32) direct | $124.99 | ✅ no Korean source; see table below |
| 6 | Drive encoder (5 mm bore) | Devicemart / Eleparts / AliExpress | ~₩20–40k | ⚠️ adapter is gated — see below |
| 7 | Relay MUX (DPDT + sockets + diodes + drivers) | Devicemart / Eleparts (Omron, Autonics) | commodity | category only |
| 8 | E-stop, traction-rated | **Autonics** (Korean maker) via Devicemart or an industrial supplier | commodity | category only |
| 9 | Pololu #2806 RC servo MUX | **Devicemart [1179242](https://www.devicemart.co.kr/goods/view?no=1179242)** — titled *"Pololu 4-Channel RC Servo Multiplexer (Assembled) #2806"*, the correct part. Also Eleparts (해외구매, ~6.5 d), or [Pololu](https://www.pololu.com/product/2806) direct $17.95 | Eleparts ₩38,545 ex-VAT | ✅ #2806 confirmed |
| 10 | RC TX/RX with SBUS | Coupang / RC hobby shops (FlySky FS-i6 + FS-iA6B class) | commodity | category only |
| 11 | 12 V 7 Ah SLA + charger + 2× DC-DC | Coupang (battery/charger) + Devicemart (DC-DC) | commodity | category only |
| 12 | Wiring / connectors / fuses | Devicemart / Coupang | commodity | category only |
| 14 | Mounts / 3D prints | lab printer, or a local print service | — | — |
| 15 | USB gamepad | Coupang (Logitech F710 class) | commodity | category only |

**"Category only" means I did not verify a specific SKU or price.** Those items are genuine
commodities in Korea and specifying a part number here would be inventing precision. Search
the named vendor and record what you actually buy.

!!! info "#3 Sabertooth — Korean options priced 2026-08-12, and why the 2x12 is not the saving it looks like"

    | Option | Cont / peak per channel | Price seen | Source |
    |---|---|---|---|
    | **2x12** (DFRobot `DRI0003`) | 12 A / 25 A | **₩154,900 ex-VAT → ₩170,390 inc-VAT** | Devicemart [1065967](https://www.devicemart.co.kr/goods/view?no=1065967), own stock |
    | 2x5 (`DRI0012`) | 5 A / 10 A | ₩114,370 | Devicemart via Digi-Key — **품절** |
    | 2x12 (`DRI0003`) | 12 A / 25 A | ₩181,550 | Devicemart via Digi-Key — **품절** |
    | 2x25 (`DRI0004`) | 25 A / 50 A | ₩284,520 | Devicemart via Digi-Key — **품절** |
    | **2x32** | 32 A / 64 A | **$124.99** + intl shipping | [Dimension Engineering](https://www.dimensionengineering.com/products/sabertooth2x32) — **no Korean source found** |

    **There is no 2x32 in the Korean channel.** Devicemart lists 2x5 / 2x12 / 2x25 through the
    Digi-Key feed and all three read 품절; only its own 2x12 is stocked.

    **The 2x12 is roughly the same money as importing a 2x32.** ₩170,390 is about $120 at
    ₩1,400/USD; the 2x32 lands near $150–165 with international shipping. Paying ~$30–45 more
    buys **2.7× the continuous rating** — on the one parameter this project has explicitly
    failed to measure. The 2x25 via Digi-Key is out of stock *and* ₩284,520 (~$205), i.e. more
    than the bigger part.

    Check the **de minimis** before assuming customs cost: Korea clears US-origin goods under
    목록통관 at a higher threshold than general imports, and Dimension Engineering ships from
    Ohio, so a single $125 board plausibly arrives with no duty or import VAT. Verify current
    thresholds at order time and record what you actually paid.

    All Sabertooth variants support **R/C input** — the 2x12 is not disqualified on
    architecture, only on headroom.

!!! warning "#3 Sabertooth is the only true import, and it is worth checking the local markup"

    Not stocked at Eleparts. Dimension Engineering sells direct at **$124.99** and ships
    internationally. Before importing, note what the Pololu MUX shows: Eleparts lists it at
    ~₩42,400 inc-VAT against **$17.95** direct — roughly a 70% markup, which is still often
    worth paying to avoid customs handling on a small order.

    For the Sabertooth, check RobotShop / Generation Robots / DFRobot as alternates, and
    compare landed cost including **customs and 부가세 on import** before assuming direct is
    cheaper.

!!! danger "#6 is only half orderable — the shaft adapter is gated, and the BOM hides this"

    The encoder itself (**5 mm bore**) can be bought now. The **3.15 → 5 mm adapter cannot**:
    that 3.15 mm is *B-MROVER's* motor shaft, inherited along with the method
    ([dbw.md §8](design/dbw.md#8-adr-c-drive-distance-encoding)), and the Defender's drive-motor
    shaft has never been measured.

    Order the encoder with Batch A, and treat the adapter as a **Batch B** item alongside the
    other measure-first parts — or buy an assortment of adapter sleeves, which is a few
    thousand won and removes the dependency entirely.

    Add the motor-shaft diameter to the M3 measurement form when you tear the vehicle down.

!!! question "Why the Sabertooth costs $125, and why it is still bought before measuring"

    The price does not buy amps, it buys three properties, in descending order of how binding
    they are:

    1. **It accepts R/C servo pulses.** The [Pololu #2806 MUX](design/dbw.md#112-hardware-rc-signal-mux-the-d3-condition)
       multiplexes *servo pulses only* — which is why
       [ADR §4](design/dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-teensy-as-both-masters)
       was reverted from packetized serial to R/C PWM. Any driver sitting downstream of that
       MUX must take pulses directly. This is architecture, not budget.
    2. **It stops the motors when the pulses stop.** [Failsafe rows 6 and 8](design/safety.md#2-failsafe-matrix)
       and [FMEA row 9](design/safety.md#7-fmea-lightweight) — D3's principal risk, severity 5 —
       all lean on this. When the Teensy hangs, traction must die with **no software
       involved**. That is a property of the driver.
    3. **It survives and limits stall current**, with thermal protection.

    **Property 3 is the one that is genuinely unsettled**, and the honest position is that
    nobody knows yet: `vehicle.md` asserts the motor class twice, differently
    ([see the warning there](design/vehicle.md#adr-d-r-reversal-to-the-12-v-single-seater-2026-08-08)),
    and it has never been measured.

    Buy it anyway, now, for a scheduling reason rather than an electrical one: the sizing
    question concerns **M2 (drive)**, which cannot be measured until the vehicle is in hand,
    while [bench Stage 1](design/safety.md#6-bring-up-protocol-staged-wheels-off-first) needs
    **M1 (steering)** working before that. You need *a* driver to make progress either way, and
    a second order cycle costs more than the part.

    **Correction, 2026-08-12.** An earlier version of this note said ~$30 could be saved by
    dropping to a 2x25. That is wrong: Dimension Engineering prices the **2x25 V2 and the 2x32
    identically at $124.99**. There is no cheaper mid-range Sabertooth. The only real
    step down is the 2x12 at $79.99 — see the sourcing comparison below.

    Record the measured paralleled stall current in §Measurements. If it comes in low, that is
    evidence for the *next* build, not a reason to re-buy this one.

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
| **Drive-motor shaft diameter (mm)** | | 
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
