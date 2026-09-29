# Order Log

**A working record, meant to be edited.** Fill it in as you place orders and as parts arrive.
Unlike the [BOM](design/bom.md), which is a *specification*, this page is the *history* of
what was actually bought, from whom, for how much, and what was substituted.

Keep it honest even when it is unflattering — a substitution that seemed harmless and later
caused a rebuild is exactly the entry the next person needs.

- **What to buy and why:** [design/bom.md](design/bom.md)
- **How to buy it, substitution rules, connector lists:** [build/01](build/01-bom-sourcing.md)
- **This page:** what you actually ordered

> [!NOTE]
> **Currency**
>
> BOM estimates are **USD, August 2026**. Record the **amount you actually paid in the
> currency you paid it in**, and put the USD equivalent in brackets so the totals still
> reconcile — e.g. `₩229,000 ($165)`.

---

## How to use this log

Each line item moves through three states. **Edit the tables below as it happens** — the columns are
the record, and a script reads them.

```bash
python3 scripts/order_status.py
```

| When | Do this |
|---|---|
| You place an order | Put the date in `Ordered` and the amount charged in `Paid ₩` |
| The box arrives | Put the date in `Arrived` |
| You have opened it and **run the check in the Verify column** | Raise the `Secured` count |

`order_status.py` totals what has been paid, projects the rest, compares both against the approved
request, and lists two things you cannot see by eye: what was **ordered and has not arrived**, and
what **arrived but is not yet secured**. Record each unit individually where it matters — three
vehicles arriving on three different days is the normal case, not an exception.

---

## Status at a glance

**Approved 2026-09-28** — see [Purchase Request](purchase-request-2026-fall.md). **3 sets.**
Run `python3 scripts/order_status.py` for the live totals and what is outstanding.

| Batch | Card | What | Per set | × 3 sets |
|---|---|---|---:|---:|
| **1** | **A** | Tier 1, orderable now — 12 items | 973,930 | **2,921,790** |
| **1G** | **A** | Tier 1, gated on vehicle measurements — #4, #5, #13 | 95,000 | **285,000** |
| **2** | **B** | Tier 2 perception — #17, #18 | 82,800 | **248,400** |
| — | — | #16 2D LiDAR — **already in hand, not purchased** | 0 | **0** |
| | | **Total to pay** | **1,151,730** | **₩3,455,190** |

> [!TIP]
> **The LiDAR already being in hand fixes the headroom problem**
>
> The approved request assumed #16 would be bought: 3 × ₩155,430 = **₩466,290**. It is already
> held, so that money is never spent.
>
> Headroom against the ₩4,000,000 ceiling therefore goes from **₩78,520 (2.0%)** to
> **₩544,810 (13.6%)**. The warning attached to the approval — that a 10% overrun on the
> estimated items would breach the ceiling — no longer applies. There is now room for the
> estimated items to land high, for shipping and duties, and for a stripped gear.
>
> **This does not authorise spending it.** It is contingency, and the approved figure is still
> ₩3,921,480.

### The three states, and why "arrived" is not enough

| State | Means | Recorded as |
|---|---|---|
| **Ordered** (주문) | Paid for, vendor has the order | date in `Ordered` |
| **Arrived** (도착) | The box is physically here | date in `Arrived` |
| **Secured** (확보) | Opened, **checked against the Verify column**, and it is the right part in the right quantity | `n/3` |

Arrival is not acquisition. The listing this project's sourcing started from carries a
**2x25 SKU on a 2x32 description** — if the wrong board ships, the box still arrives on time. The
`Secured` count is what separates "a package came" from "I have three working parts", and it is a
**count**, not a tick, because a partial delivery is the normal case.

---

## Batch 1 — Tier 1, card A, order now

Nothing here waits on a measurement. **Order the vehicle first regardless** — Batch 1G cannot be
specified until it arrives, so it is the long pole.

Prices are the verified figures from
[§1.2.1](build/01-bom-sourcing.md#121-sourcing-in-korea-verified-2026-09-15). Record what you
*actually* paid in `Paid ₩` — that is the column the reconciliation uses.

| # | Item | Qty | Vendor | Unit ₩ | Ordered | Arrived | Secured | Paid ₩ | Verify on arrival |
|---|------|----:|--------|-------:|:-------:|:-------:|:-------:|-------:|-------------------|
| 1 | Vehicle — 12 V single-seat ride-on | 3 | 쿠팡 | 229,000 | . | . | 0/3 | | Record model + serial per unit |
| 2 | Teensy 4.1 | 3 | 디바이스마트 | 74,250 | . | . | 0/3 | | **4.1, not 4.0** — count the pins |
| 3 | Sabertooth 2x32 | 3 | 원스톱 | 250,000 | . | . | 0/3 | | **Label must read 32 A / 6–30 V.** A 2x25 is the wrong part |
| 6 | Drive encoder (5 mm bore) | 3 | 디바이스마트 | 25,000 | . | . | 0/3 | | Measure PPR — **do not trust the label** |
| 7 | Relay MUX — 2× DPDT + sockets, diodes, drivers | 3 | 디바이스마트 | 34,000 | . | . | 0/3 | | Contact rating ≥ traction current |
| 8 | E-stop + DC contactor | 3 | 한국미스미 | 35,000 | . | . | 0/3 | | **DC rating, not AC.** Contactor first — it sets the button's rating |
| 9 | Pololu #2806 RC servo MUX | 3 | 디바이스마트 | 31,680 | . | . | 0/3 | | `FAILMODE` jumper present |
| 10 | RC TX/RX — FlySky FS-i6 + **FS-iA6B** | 3 | 팰콘샵 | 75,000 | . | . | 0/3 | | **iA6B, not iA6** — the i-BUS port must be there |
| 11 | Isolated logic rail — SLA + charger + 2× DC-DC | 3 | 11번가 / 디바이스마트 | 60,000 | . | . | 0/3 | | Record capacity + both rail voltages |
| 12 | Wiring / connectors / fuses | 3 | 디바이스마트 | 55,000 | . | . | 0/3 | | Wire gauge sized for stall, not nominal |
| 14 | Mounts / 3D-print material | 3 | 로컬 | 41,000 | . | . | 0/3 | | |
| 15 | USB gamepad — Logitech F710 class | 3 | 컴퓨존 / 11번가 | 64,000 | . | . | 0/3 | | Xbox layout; record the map if not |
| | **Batch 1** | | | **973,930** | | | | | **× 3 = 2,921,790** |

> [!CAUTION]
> **Do not let #9 slip to a later order**
>
> The Pololu RC signal MUX is **₩31,680 and it is the condition the single-Teensy architecture was
> adopted under** ([safety.md §1.2](design/safety.md#12-live-override-inside-dbw-mode-two-layers)).
> Pololu list it as **"Rationed"** at source, so the domestic listing is the whole supply as far as
> this build is concerned. A cheap part on allocation is exactly the one that arrives last.

### Sourcing reference

Verified vendors, prices, links and the date each was read live in
**[Build Guide §1.2.1](build/01-bom-sourcing.md#121-sourcing-in-korea-verified-2026-09-15)**. It is
not repeated here — a second copy of a price table is a second copy to keep current.

### Why some of these parts are not interchangeable

Three notes worth re-reading at the moment of ordering, when a cheaper option is in front of you.

> [!CAUTION]
> **#6 is only half orderable — the shaft adapter is gated, and the BOM hides this**
>
> The encoder itself (**5 mm bore**) can be bought now. The **3.15 → 5 mm adapter cannot**: that
> 3.15 mm is *B-MROVER's* motor shaft, inherited along with the method
> ([dbw.md §8](design/dbw.md#8-adr-c-drive-distance-encoding)), and this vehicle's drive-motor
> shaft has never been measured.
>
> Order the encoder with Batch 1 and treat the adapter as **Batch 1G** — or buy an assortment of
> adapter sleeves, which is a few thousand won and removes the dependency entirely.
>
> Add the motor-shaft diameter to the M3 form when you tear the vehicle down.

> [!WARNING]
> **#15 and #10 are not the same thing, and you need both**
>
> The **gamepad (#15)** is a software input: `joy_node` reads it and its Twist goes through
> `twist_mux`, so a firmware or laptop hang takes it down too.
>
> The **RC transmitter (#10)** is the hardware override, switching servo pulses through the MUX with
> no software in the path at all.
>
> Buying only one leaves either no convenient teleop, or no firmware-independent override.

> [!NOTE]
> **Why the Sabertooth costs what it costs**
>
> The price does not buy amps, it buys three properties, in descending order of how binding they
> are:
>
> 1. **It accepts R/C servo pulses.** The [Pololu #2806 MUX](design/dbw.md#112-hardware-rc-signal-mux-the-d3-condition)
>    multiplexes *servo pulses only*, so any driver downstream of it must take pulses directly.
>    Architecture, not budget.
> 2. **It stops the motors when the pulses stop.** [Failsafe rows 6 and 8](design/safety.md#2-failsafe-matrix)
>    and [FMEA row 9](design/safety.md#7-fmea-lightweight) — D3's principal risk, severity 5 — all
>    lean on this. When the Teensy hangs, traction must die with **no software involved**.
> 3. **It survives and limits stall current**, with thermal protection.
>
> Property 3 is the one still unsettled: the paralleled drive-motor stall current has never been
> measured. Record it in [§Measurements](#measurements-to-record-on-arrival) when you can. If it
> comes in low, that is evidence for the *next* build, not a reason to re-buy this one.
>
> **Do not substitute a bare H-bridge.** It fails on property 1 before current even matters.

---

## Batch 1G — Tier 1, card A, gated on measurement

**Same card as Batch 1, later date.** These three cannot be specified from a catalogue; ordering
them with Batch 1 is the documented way to waste money on this build. Take the measurements below
*first* and put the value that decided each choice in the Verify column.

| # | Item | Qty | Vendor | Unit ₩ | Ordered | Arrived | Secured | Paid ₩ | Verify — measure before ordering |
|---|------|----:|--------|-------:|:-------:|:-------:|:-------:|-------:|----------------------------------|
| 4 | Steering gearmotor + encoder | 3 | TBD | 48,000 | . | . | 0/3 | | **M1**: column torque τ, size at **≥ 2×** rated |
| 5 | Absolute angle sensor (AS5600 **or** pot) | 3 | TBD | 27,000 | . | . | 0/3 | | **M2**: lock-to-lock travel — **≤ 340° ⇒ AS5600** |
| 13 | Steering coupler + magnet mount | 3 | TBD | 20,000 | . | . | 0/3 | | **M3**: column / kingpin shaft diameter |
| | **Batch 1G** | | | **95,000** | | | | | **× 3 = 285,000** |

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

> [!NOTE]
> **If no suitable encoder-gearmotor can be sourced**
>
> The documented fallback is a **12 V automotive wiper motor**. Two consequences you must
> accept and re-check against [safety.md](design/safety.md) before the vehicle touches the
> ground: its worm gear is largely **non-back-drivable**, so on power loss the steering
> **holds** rather than freewheels — which invalidates the freewheel analysis — and it
> rarely has a usable shaft encoder, making the absolute sensor the sole angle source.
> Record the choice here if you take it.

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

## Batch 2 — Tier 2 perception, card B

**A different card from Batch 1.** Deliberately last: if the steering loop fails its accuracy gate
at [bench Stage 1](design/safety.md#6-bring-up-protocol-staged-wheels-off-first), this money has not
been spent yet. That sequencing is the entire point of the two-tier split.

| # | Item | Qty | Vendor | Unit ₩ | Ordered | Arrived | Secured | Paid ₩ | Verify on arrival |
|---|------|----:|--------|-------:|:-------:|:-------:|:-------:|-------:|-------------------|
| 16 | 2D LiDAR — RPLIDAR A1M8 | 3 | — **already held** | 0 | — | — | 3/3 | 0 | **In hand before approval.** Confirm 3 units and that each spins up |
| 17 | Front camera — USB 1080p wide-FOV | 3 | 디바이스마트 | 41,000 | . | . | 0/3 | | Rolling shutter is fine for now — see below |
| 18 | IMU — BNO085 class | 3 | 아이씨뱅큐 | 41,800 | . | . | 0/3 | | 9-DoF with **onboard fusion** |
| | **Batch 2** | | | **82,800** | | | | | **× 3 = 248,400** |

> [!IMPORTANT]
> **#16 is not purchased — verify the three units anyway**
>
> The three LiDARs were already held when the request was approved, which is why this row is
> `3/3` at ₩0 and why ₩466,290 of the approved amount is never spent.
>
> **Secured still means checked.** Confirm there are genuinely three, that each powers up and
> spins, and that `ros-humble-rplidar-ros` sees each one. A unit that has sat in a drawer since
> a previous project is exactly the one that turns out to be dead in week 10, when there is no
> budget cycle left to replace it.

> [!NOTE]
> **The camera is a knowing compromise**
>
> Rolling shutter is fine for SLAM and teleop. **Behaviour cloning (phase 2) needs a global
> shutter** — rolling shutter smears during turns and corrupts the steering labels. Budget
> **+₩200,000 per set** then. Do not train a policy on rolling-shutter data and attribute the
> result to the platform.

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

> [!CAUTION]
> **Every dimension in the twin is currently an estimate**
>
> `mitt_description/config/mitt_dimensions.yaml` is populated with values derived from the
> vendor's 98×56×47 cm listing, each marked `TODO measure`. The URDF has no geometric
> literals, so updating that file updates the model, the controller config, and the body
> mesh scale together.
>
> Two of these propagate further than they look. Wheelbase and steer limit set
> `R_min = wheelbase / tan(steer_limit)` — currently **1.52 m** — which is used in
> `nav2_params.yaml` **twice** (`minimum_turning_radius` on the planner and
> `min_turning_radius` on the controller). Re-derive both when you measure, or Nav2 will be
> planning for a vehicle you do not have.

---

## Substitution log

Record anything bought that differs from the BOM spec, and why. This is what makes the build
reproducible rather than folklore.

| BOM # | Specified | Bought instead | Why | Consequence checked? |
|---|---|---|---|---|
| | | | | |
| | | | | |

> [!WARNING]
> **Substitutions with teeth**
>
> Three where "close enough" is not:
>
> - **#3 Sabertooth → bare H-bridge.** Looks like a $110 saving. The Sabertooth's current
>   limiting, thermal protection and R/C signal-loss timeout are load-bearing in
>   [failsafe row 6](design/safety.md#2-failsafe-matrix). A BTS7960 provides none of them.
> - **#8 E-stop → signal-rated button.** It must switch actual traction current or a
>   contactor coil. A signal-rated mushroom **will weld shut**, which fails exactly when
>   you need it.
> - **#2 Teensy → ESP32/AVR.** The 600 MHz M7's timing determinism and **four hardware
>   quadrature decoders** are why the whole DBW loop fits on one MCU.

---

## Reconciliation

Fill in as each batch closes. **`python3 scripts/order_status.py` computes these from the tables
above** — this section is for the variance narrative, which a script cannot write.

| Batch | Card | Approved | Actual | Δ |
|---|---|---:|---:|---:|
| 1 — Tier 1 now | A | 2,921,790 | | |
| 1G — Tier 1 gated | A | 285,000 | | |
| 2 — Tier 2 perception | B | 248,400 | | |
| #16 LiDAR — already held | — | 0 | 0 | 0 |
| Shipping / duties / tax not in unit prices | | — | | |
| **Total** | | **3,455,190** | | |
| *Approved request* | | *3,921,480* | | |
| *Ceiling* | | *4,000,000* | | |

**Notes on variance** — what came in over or under, and whether it was price drift, shipping, or a
spec change:

> _(write here)_

> [!TIP]
> **Your real numbers are worth more than these estimates**
>
> 43% of the approved figure was still an estimate at approval time, converted from USD at
> 1,362 KRW. Once this table is filled in, fold the actuals back into
> [design/bom.md](design/bom.md) so the next build starts from evidence rather than from a
> retailer survey.
>
> Record **per-card totals** too: two cards were used, and the university will reconcile each
> statement separately.
