# Vehicle (Chassis) Selection

> Part of the MRider design set. Siblings: [architecture.md](architecture.md) ·
> [dbw.md](dbw.md) · [safety.md](safety.md) · [sensors.md](sensors.md) ·
> [software.md](software.md) · [calibration.md](calibration.md) · [bom.md](bom.md) ·
> [overview.md](overview.md)
>
> Prices are **estimates as of July 2026** and vary by retailer, coupon, and stock.

This document selects the base ride-on vehicle ("MITT") that MRider converts to
drive-by-wire. It states the **selection criteria first**, then evaluates real,
currently-purchasable candidate models against them, lists the physical
verification that must be done on the unit actually purchased, and records the
chassis decision as [ADR D](#adr-d-24-v-two-seater-vs-12-v-single-seater).

The choice is driven by the project's decision drivers: payload
for an onboard laptop plus sensors, an accessible steering column for the
[DBW](dbw.md) angle actuator and absolute sensor, 24 V electrical headroom, and
reuse of the [mrover](https://github.com/jrkwon/mrover) Sabertooth + Pixhawk
recipe.

---

## 1. Selection Criteria

These are ordered by how hard they are to fix after purchase. A vehicle that
fails a "must" criterion is rejected regardless of price.

| # | Criterion | Target | Why (which subsystem needs it) |
|---|-----------|--------|--------------------------------|
| C1 | **Payload margin** | ≥ ~6 kg usable deck load (laptop ~2 kg + LiDAR/camera/mast + Pixhawk/Sabertooth/Nano/relays + wiring ~3–4 kg), on top of the rated child weight the vehicle already carries | Onboard compute ([sensors.md](sensors.md)) and the DBW control box ride on the deck. A two-seater rated for ~60 kg of kids trivially carries the ~6 kg kit. |
| C2 | **24 V electrical system** | 24 V battery pack, dual drive motors | Voltage headroom for the [Sabertooth 2x32](dbw.md) throttle channel; matches the mrover recipe; more torque margin on grass/ramps than 12 V. |
| C3 | **Dual rear drive motors** | 2 rear motors (4WD acceptable) | The two rear motors parallel onto one Sabertooth channel ([ADR C](dbw.md), throttle path). Confirms a real H-bridge-drivable DC traction path, not a sealed ESC. |
| C4 | **Accessible steering column** | Exposed vertical steering shaft between wheel and linkage, with ~30–50 mm of clear shaft | The [steering angle gearmotor](dbw.md) couples to the column, and the **absolute angle sensor** ([ADR B, sensor-tech ADR](dbw.md)) mounts on the shaft. A sealed/rack-hidden column blocks both. |
| C5 | **Deck / cargo space** | Flat area ≥ ~30 × 30 cm, or a rear bed (UTV/truck style) | Mounting the control enclosure, mast base ([sensors.md](sensors.md)), and E-stop. UTV beds are ideal. |
| C6 | **Metal gearbox (preferred)** | Steel/metal reduction gears on drive motors | Plastic gearboxes strip under the extra mass + autonomous duty cycle. Not a hard reject, but a strong preference and a stated risk if unmet. |
| C7 | **Parent 2.4 GHz remote (present)** | OEM parent remote included | Confirms the OEM already has a remote-drive electrical path we can tap; its receiver becomes the de-energized STOCK side of the [relay MUX](safety.md). Note: the OEM remote is **not** the live DBW override — that is the [RC-via-Pixhawk](safety.md) path. |
| C8 | **Stock geometry & serviceability** | Bolt-on seat/body panels, standard fasteners | Minimally-invasive, reversible modification (plan principle 2). |

Non-criteria (explicitly do not care): Bluetooth/MP3, LED lights, leather seats,
"spring suspension" marketing — these do not affect the conversion and are
ignored in scoring.

---

## 2. Candidate Models (July 2026)

All three are 24 V two-seaters with parent remote and dual/quad motors, in the
$250–450 street-price band, and are the vehicle class the
[mrover build](https://github.com/jrkwon/mrover) already used (its BOM lists a
"POSTACK 24V 2-Seater" at ~$260 and an "ELEMARA 2-Seater" at ~$369). The point
of listing three is availability resilience (per the plan risk "vehicle model
availability varies"), not that these exact SKUs must be bought — **buy any unit
that passes Section 1 and Section 3.**

| | **Cand. 1 — 24V 2-Seat Jeep (Target/Amazon class)** | **Cand. 2 — GARVEE / Siavonce 24V 2-Seat UTV** | **Cand. 3 — POSTACK / ELEMARA 24V 2-Seat** |
|---|---|---|---|
| Body style | Jeep/SUV, 2 seats | **UTV / side-by-side (rear bed)** | Truck / tractor-style, 2 seats |
| Est. price (Jul 2026) | ~$280–320 | ~$350–450 | ~$260–370 |
| Voltage / motors | 24 V, "2×200 W" (4× on some 4WD) | 24 V, 4WD (4 motors) | 24 V, 2–4 motors |
| Remote | 2.4 GHz parent remote | 2.4 GHz parent remote | 2.4 GHz parent remote |
| Deck / bed (C5) | Flat seat backs; moderate | **Best — open cargo bed** | Good; flat rear |
| Steering column (C4) | Vertical shaft under dash — verify access | Vertical shaft — verify access | Vertical shaft — verify access |
| Metal gearbox (C6) | Model-dependent — **verify** | Model-dependent — **verify** | Model-dependent — **verify** |
| Sources | Target 1002549549; Amazon B0DNWRKKZY / B0DHVS12XF | garvee.com UTV listings; Home Depot XMJ-P184803 | mrover BOM (`Note/overview.md`); Amazon B0CJTWDC38 / B0DHCVHCJY |

**Recommendation:** prefer **Candidate 2 (24 V two-seat UTV with a rear bed)**
when available — the open bed (C5) makes the compute/control-box and mast
mounting the cleanest and most reversible, and 4WD UTVs in this class ship with
the sturdiest steel drivetrains. Candidate 3 is the proven fallback (mrover
heritage, lowest cost). Candidate 1 is the widest-available fallback. Final pick
is whichever in-stock unit passes Section 3 on the bench.

Links (representative, July 2026):
- Target 2-Seater 24 V Jeep, 2×200 W: <https://www.target.com/p/-/A-1002549549>
- GARVEE 24 V 2-Seater UTV: <https://www.garvee.com/>
- Siavonce 24 V 2-Seater UTV (Home Depot): <https://www.homedepot.com/p/333378612>
- Amazon 24 V 2-Seater (mrover-class): <https://www.amazon.com/dp/B0CJTWDC38>

---

## 3. Required Verification Checklist (on the purchased unit)

These measurements gate the [DBW](dbw.md) and [safety](safety.md) design. Do
them **before** cutting into wiring; several determine whether the stock motors
can be driven by the Sabertooth at all.

### 3.1 Drive-motor stall current vs Sabertooth rating (critical)

The two rear motors are wired **in parallel onto one Sabertooth 2x32 channel**
([ADR C](dbw.md), throttle path). The Sabertooth 2x32 is rated **32 A continuous
per channel (~64 A peak per channel for a few seconds)**. The paralleled pair
must stay within that.

- **Procedure:** with wheels off the ground, measure per-motor no-load current
  (clamp meter on one motor lead) at each OEM speed. Then measure locked-rotor
  (stall) current by briefly (<1 s) holding a wheel and reading peak, one motor
  at a time. Stall for RS-550-class 12 V motors is typically **30–60 A each**.
- **Acceptance:** paralleled continuous draw under load ≤ 32 A; transient/stall
  of the pair should not sit above ~64 A. If the pair can stall near/over 64 A,
  mitigations (per-motor current limit in Sabertooth config, gentler PX4
  accel/torque limits, or driving **one** motor per Sabertooth channel and
  sacrificing the steering channel split) must be chosen **before** wiring — see
  [dbw.md](dbw.md) throttle path and [safety.md](safety.md) power budget.
- **Consequence if it fails:** a 24 V two-seater whose paralleled stall exceeds
  the Sabertooth ceiling forces either current-limited (weaker) traction or a
  second motor driver — flag to [bom.md](bom.md).

### 3.2 OEM motor voltage configuration (critical)

"24 V" ride-ons are built two ways, and it changes how the Sabertooth B+ and
motor leads are tapped:

- **(a) Native 24 V motors** — each motor sees the full 24 V pack. Sabertooth
  M-outputs drive them directly at 24 V.
- **(b) 12 V motors in series/paired across a 24 V pack** — common on
  "2×12 V" builds. Here a single motor must **not** see 24 V.
- **Procedure:** read the motor can label (e.g., `RS-550 12V` vs `24V`); with a
  meter, measure the voltage across one motor's terminals at full throttle in
  OEM mode. **Acceptance:** confirm whether each drive motor terminal sees 12 V
  or 24 V, and wire the Sabertooth output to match (never apply 24 V across a
  12 V motor). This determines the [power budget](safety.md) rail assignment.

### 3.3 Steering column geometry

- **Procedure:** remove the dash/kick panel; confirm a **vertical steering shaft**
  is exposed between the wheel hub and the tie-rod/pitman linkage, with clear
  radial space for (a) a gear/pulley or direct coupler to the
  [steering gearmotor](dbw.md) and (b) a hollow-shaft or coupled **absolute
  angle sensor**. Measure shaft diameter, exposed length, and mechanical
  steering range (lock-to-lock) in degrees.
- **Acceptance:** ≥ ~30 mm clear shaft, measurable and repeatable mechanical
  stops, total column travel that a **single-turn** sensor can span (if it
  exceeds ~ one turn, that forces the pot-vs-magnetic
  [angle-sensor ADR in dbw.md](dbw.md) toward a multi-turn pot or a geared-down
  magnetic sensor). Record lock-to-lock for the
  [calibration](calibration.md) counts→degrees map.

### 3.4 Secondary checks

- Gearbox material (C6): open one drive gearbox — steel vs nylon gears.
- Pack: confirm 24 V (nominal) battery, connector type, and charger.
- Confirm the parent remote's receiver board is a **separable module** whose
  motor-drive lines can be routed through the [relay MUX](safety.md).

---

## ADR D — 24 V two-seater vs 12 V single-seater

**Status:** Accepted (chassis class). Instance SKU chosen at purchase per §2/§3.

**Context.** MRider must carry an onboard laptop plus a camera, 2D LiDAR, mast,
Pixhawk, Sabertooth, Nano, and relay MUX, and drive that mass at walking speed
for a full data-collection/mapping session while the [DBW](dbw.md) closes a
steering position loop. The mrover/OSCAR lineage and prior Ridon work used this
same ride-on class.

**Decision.** Use a **24 V two-seater ride-on (UTV/Jeep/truck style) with dual
rear motors and a parent remote**, of the class mrover already validated. Select
the specific unit by the Section 1 criteria and Section 3 bench verification.

**Alternatives considered.**
- **D1 (chosen) — 24 V two-seater.** Payload headroom (C1), 24 V torque/voltage
  margin (C2), wide flat deck or UTV bed (C5), dual motors (C3). Cost ~$260–450.
- **D2 — 12 V single-seater.** Cheapest (~$150–250), matches the older Ridon
  precedent, smallest footprint. Rejected as the baseline: marginal payload once
  a laptop + sensors + control box are added, less torque margin on inclines/
  grass, and a tighter deck for mounting. Kept as a possible "lite tier" appendix
  only.
- **Off-class — mobility scooter / larger EV.** Rejected: heavier, faster than
  the ≤ walking-speed [safety](safety.md) envelope, and higher-stakes failure
  modes for an education platform.

**Rationale.** The 24 V two-seater is the smallest, cheapest platform that
comfortably meets payload and torque margin while preserving the exact
Sabertooth-2x32 + Pixhawk electrical recipe MRider reuses. The extra ~$100–200
over a 12 V single-seater buys margin on every axis that is expensive to add
later (payload, torque, deck area) and costs nothing MRider needs.

**Consequences.**
- Paralleled dual-motor draw must be verified against the 32 A/channel Sabertooth
  ceiling (§3.1) — the one place the bigger vehicle can bite back.
- Motor voltage configuration (§3.2) must be confirmed before wiring.
- Higher base cost flows into the [BOM](bom.md) (both tiers use this line item).
- The wide deck / UTV bed simplifies the [sensor mast](sensors.md) and control-box
  mounting versus a 12 V single-seater.
- Non-self-centering steering column (typical of this class) drives the
  [E-stop steering-on-power-loss semantics](safety.md).

**Follow-ups.** Purchase a unit passing §1; run §3 bench checks and feed results
into [dbw.md](dbw.md) (torque/stall sizing), [safety.md](safety.md) (power rails),
and [calibration.md](calibration.md) (lock-to-lock range).
