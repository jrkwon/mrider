# Bill of Materials (BOM)

> Part of the MRider design set. Siblings: [architecture.md](architecture.md) ·
> [vehicle.md](vehicle.md) · [dbw.md](dbw.md) · [safety.md](safety.md) ·
> [sensors.md](sensors.md) · [software.md](software.md) ·
> [calibration.md](calibration.md) · [overview.md](overview.md)

**All prices are estimates as of August 2026** in USD and vary by retailer, coupon,
and stock. They are for budgeting, not quotes. Verify at purchase.

**Revised 2026-08-07** following [D3](adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07)
(single Teensy replaces Pixhawk + Nano) and a re-scoping of the sensor package to
semester-1 needs. **Estimated total fell from ~$1,570 to ~$1,035** — see §Change record.

The **laptop is not a purchased line item** — it is lab-supplied/reused
([sensors.md §6](sensors.md)), and runs on its own battery in v1.

---

## Purchase tiers

Buy in **two tiers** so the perception spend happens only after the DBW gates pass. If the
steering spike fails at [bring-up Stage 1](safety.md#6-bring-up-protocol-staged-wheels-off-first),
Tier 2 has not been bought yet.

- **Tier 1 — Vehicle + DBW core.** Order in week 1, after the
  [steering-shaft travel measurement](dbw.md#6-adr-angle-sensor-technology-magnetic-encoder-vs-potentiometer).
- **Tier 2 — Perception.** Order by week 10.

---

## Tier 1 — Vehicle + DBW core

| # | Item | Spec / Model | Design ref | Reuse? (mrover) | Est. ($) | Source / note |
|---|------|--------------|-----------|-----------------|---------:|---------------|
| 1 | **Vehicle (chassis)** | **12 V single-seat** ride-on, dual motors, parent remote | [vehicle.md ADR D-R](vehicle.md#adr-d-r-reversal-to-the-12-v-single-seater-2026-08-08) | **No** — class changed | 165 | Land Rover Defender, 98×56×47 cm, 10 kg, ₩229,000. **ADR D was reversed**; see the note below |
| 2 | **Teensy 4.1** | 600 MHz Cortex-M7, 4× hardware QDC, 8× serial | [dbw.md §9](dbw.md#9-teensy-41-firmware-platform-and-version-pinning) | New | 32 | Replaces Pixhawk 6C + PM02 + Nano + USB-TTL |
| 3 | **Sabertooth 2x32** | Dimension Eng. 2×32 A dual motor driver | [dbw.md §4](dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-teensy-as-both-masters) | Yes | 125 | **Do not substitute a bare H-bridge** — see the note below |
| 4 | **Steering gearmotor + encoder** | Geared DC motor w/ encoder (RS-385/390 class) or wiper-motor fallback | [dbw.md §2](dbw.md#2-steering-actuation-design) | Partial | 35 | Sized ≥2× measured column torque ([dbw.md §2.2](dbw.md#22-torque-measurement-procedure-before-sizing-the-gearmotor)) |
| 5 | **Absolute steering angle sensor** | AS5600 breakout + diametric magnet; pot as fallback | [dbw.md §6](dbw.md#6-adr-angle-sensor-technology-magnetic-encoder-vs-potentiometer) | New | 20 | **Budget for either** — technology decided by the bench travel measurement |
| 6 | **Drive encoder + shaft adapter** | Quadrature/Hall encoder + 3.15→5 mm adapter | [dbw.md §8](dbw.md#8-adr-c-drive-distance-encoding) | Yes | 18 | mrover shaft-adapter method. **Verify PPR on the part fitted** (F7) |
| 7 | **Relay MUX hardware** | 2× DPDT automotive relays/contactors + sockets + flyback diodes + drive transistors | [safety.md §1.1](safety.md#11-relay-mux-stock-vs-dbw-selection) | New | 25 | Default de-energized = STOCK |
| 8 | **E-stop switch** | Latching mushroom, traction-rated | [safety.md §3](safety.md#3-e-stop-semantics) | New | 15 | Cuts traction power only |
| 9 | **Hardware RC signal MUX** | **Pololu 4-Channel RC Servo Multiplexer #2806** | [dbw.md §11.2](dbw.md#112-hardware-rc-signal-mux-the-d3-condition) | New | 18 | **Required — the condition of D3's adoption.** $17.95, 4 ch (2 used), `FAILMODE` jumper sets loss-of-select behaviour |
| 10 | **RC transmitter + receiver** | 6-ch 2.4 GHz with **SBUS** out (FlySky FS-i6 + FS-iA6B class) | [safety.md §1.2](safety.md#12-live-override-inside-dbw-mode-two-layers) | New | 55 | Was $120 for a PX4-bindable FrSky set; without PX4 the requirement is just SBUS + a spare channel for the MUX |
| 11 | **Isolated logic rail** | 12 V 7 Ah SLA + charger + 2× DC-DC buck | [safety.md §5](safety.md#5-power-rail-isolation-and-brownout-protection) | New | 45 | Replaces the PM02's isolation role. **Not a retrofit** — the Teensy holds the whole safety supervisor |
| 12 | **Wiring / connectors / fuses** | Silicone wire, spade/XT60, inline fuses, terminals, heatshrink | [safety.md](safety.md) | Partial | 40 | |
| 13 | **Steering shaft coupler / adapter** | Column coupler, set screws, bracket, magnet mount | [dbw.md](dbw.md) · [calibration.md](calibration.md) | New | 15 | Couples gearmotor + angle sensor. Magnet mount needs concentricity — see [dbw.md §6](dbw.md#6-adr-angle-sensor-technology-magnetic-encoder-vs-potentiometer) |
| 14 | **Mounts / 3D prints** | Sensor mast + camera/LiDAR mounts + enclosures | [sensors.md §5](sensors.md) | Partial | 30 | Print filament/hardware; mrover STLs need reworking for the new controller |
| | | | | **Tier 1** | **$773** | |

!!! info "Vehicle class changed — ADR D reversed 2026-08-08"

    This line was a **24 V two-seater at $300**. The project moved to a **12 V single-seater
    at ~$165** ([ADR D-R](vehicle.md#adr-d-r-reversal-to-the-12-v-single-seater-2026-08-08)),
    saving ~$135 and giving a smaller, easier-to-store vehicle.

    What it costs is **not** in this table, which is the point of flagging it here: the mast
    comes down to ~0.65 m, the seat must be replaced with an equipment plate, and finding F1
    (B-MROVER validated on the 24 V two-seater class) no longer transfers.

    The Sabertooth below is now oversized for this drivetrain. **Keep it anyway** — its
    current limiting and R/C signal-loss timeout are load-bearing in the failsafe matrix, and
    headroom is not a defect.

!!! warning "Do not substitute a cheap H-bridge for the Sabertooth"

    A BTS7960-class module is ~$14 and looks like a $110 saving. It is the wrong part here:
    [vehicle.md §3.1](vehicle.md) notes RS-550-class drive motors stall at **30–60 A each**,
    and the two rear motors are paralleled onto one channel. The Sabertooth 2x32 provides
    32 A/channel with current limiting, thermal protection, and a configurable **serial
    timeout** that backs [failsafe row 6](safety.md#2-failsafe-matrix). A bare H-bridge
    provides none of those. Keep it.

## Tier 2 — Perception

| # | Item | Spec / Model | Design ref | Reuse? | Est. ($) | Source / note |
|---|------|--------------|-----------|--------|---------:|---------------|
| 15 | **2D LiDAR** | RPLIDAR A1M8 (360°, 12 m) | [sensors.md §2](sensors.md) | No | 110 | Sufficient for indoor hallway SLAM. `ros-humble-rplidar-ros` is in apt. Upgrade path: RPLidar S3 / YDLidar G4 |
| 16 | **Front camera** | USB 1080p wide-FOV | [sensors.md §1](sensors.md) | No | 30 | **See the behavior-cloning note below** |
| 17 | **IMU** | BNO085-class 9-DoF with onboard fusion | [sensors.md §3](sensors.md) | New | 28 | Replaces the Pixhawk's internal IMU. Estimator is unchanged — it was always `robot_localization` (F11) |
| | | | | **Tier 2** | **$168** | |

!!! note "The global-shutter camera is deferred, not deleted"

    The previous BOM specified an **Arducam AR0234 global-shutter USB3 camera ($180)**,
    chosen deliberately because rolling-shutter distortion during motion degrades
    behavior-cloning training data. Behavior cloning is **phase 2**
    ([software.md §8](software.md#8-semester-1-scope-and-software-acceptance-gates)), so
    semester 1 uses a $30 rolling-shutter camera and the global-shutter part is a **phase-2
    repurchase, budgeted at +$150.** Do not train a behavior-cloning policy on rolling-shutter
    data and attribute the result to the platform.

---

## Totals

| | Sum of line items | Contingency (~10%) | **Estimated total** |
|------|------------------:|-------------------:|--------------------:|
| **Tier 1 + Tier 2** | **$941** | ~$94 | **~$1,035** |
| *Tier 1 alone (weeks 1–9)* | *$773* | *~$77* | *~$850* |

Contingency covers shipping, taxes, connector/fastener miscellany, a blown H-bridge or
stripped steering gear, and the verification-driven risk that the **drive-motor stall
current** ([vehicle.md §3.1](vehicle.md)) forces a current-limit accessory.

---

## Change record — why the total fell from ~$1,570 to ~$1,035

| Change | Δ | Driver |
|---|---:|---|
| Pixhawk 6C + PM02 removed | −$220 | [D3](adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07) |
| Arduino Nano + USB-TTL adapter removed | −$26 | D3 |
| Teensy 4.1 added | +$32 | D3 |
| IMU added (was inside the Pixhawk) | +$28 | D3 |
| **Hardware RC signal MUX added** | +$18 | D3's safety condition — [safety.md §1.2](safety.md#12-live-override-inside-dbw-mode-two-layers) |
| **Isolated logic rail added** (was the PM02's job) | +$45 | D3 — [safety.md §5](safety.md#5-power-rail-isolation-and-brownout-protection) |
| **D3 subtotal** | **−$123** | |
| RC set: PX4-bindable FrSky → SBUS-capable FlySky | −$65 | No PX4 to bind to; requirement is now SBUS + a MUX channel |
| LiDAR: YDLidar G4 → RPLIDAR A1M8 | −$150 | Semester-1 scope is indoor hallway SLAM |
| Camera: AR0234 global shutter → USB 1080p | −$150 | Behavior cloning deferred to phase 2 |
| GNSS excluded | $0 | Already excluded from the minimum tier |
| **Sensor re-scoping subtotal** | **−$365** | |
| **Total** | **−$488** | $1,429 → $941 before contingency |

**Honest attribution:** D3 itself accounts for **−$123**, not the bulk of the saving. Most of
the reduction comes from scoping the sensor package to what semester 1 actually needs. Both
are real, but they are different kinds of decision — one is architectural and permanent, the
other is a deferral with a known phase-2 cost (+$150 camera, +$200–350 GNSS/RTK,
+$150–200 LiDAR upgrade).

**Vehicle voltage was reconsidered and kept at 24 V.** A 12 V single-seater saves ~$100–150,
but [ADR D](vehicle.md#adr-d-24-v-two-seater-vs-12-v-single-seater) rejects it on payload and
torque margin — and it is the chassis class B-MROVER is validated on (finding F1). With D3
removing the validated-autopilot claim, the validated-*chassis* claim carries more weight than
before, not less. Not worth $100.

---

## Levers if the budget must go lower

| Lever | Saving | Cost |
|---|---:|---|
| Buy the vehicle used (marketplace) | −$100 to −$150 | Condition risk; inspect steering column before buying |
| Lab already has an mrover rig — reuse Sabertooth (#3), drive encoder (#6), 3D prints (#14) | −$173 | None, if the parts exist |
| 3D-print couplers and mounts instead of buying | −$30 | Print time |
| Defer Tier 2 entirely to next semester | −$168 | **Loses the SLAM map deliverable** — the semester's visible outcome |
| 12 V single-seater | −$100 to −$150 | Contradicts ADR D; gives up the validated chassis class. **Not recommended** |

**Realistic floor** with a used vehicle, lab-reused Sabertooth and encoder, and printed
mounts: **~$620 all-in.**

---

## Reuse notes (lab already has an mrover build)

Typically already owned and subtractable: **Sabertooth 2x32** (#3), **drive encoder + shaft
adapter** (#6), **3D-printed enclosures** (#14, `config/3D_design/v3/` — though the Pixhawk
and Sabertooth cases need rework for the new controller), and the laptop.

**No longer reusable under D3:** the Pixhawk 6C, PM02, Arduino Nano, and USB-TTL adapter from
an existing mrover rig are not used by MRider. If the lab has them, they remain useful for
other projects — this is a deliberate architectural departure, not a write-off of working
hardware.

**New to MRider** (not in the mrover BOM): the Teensy (#2), absolute angle sensor (#5), relay
MUX (#7), E-stop (#8), **hardware RC signal MUX (#9)**, RC set (#10), isolated logic rail
(#11), and IMU (#17). These implement the [DBW angle servo](dbw.md), the
[layered authority arbitration](safety.md), and the power isolation that distinguish MRider
from the base mrover recipe.

---

## Phase-2 growth path

Not in the totals; documented future upgrades.

| Item | Spec | Est. ($) | Enables |
|------|------|---------:|---------|
| Global-shutter camera | Arducam AR0234 USB3 class | 180 | Behavior cloning without rolling-shutter artifacts |
| RTK GNSS rover | u-blox ZED-F9P class | 220–300 | Outdoor waypoint following |
| RTK corrections | NTRIP subscription or local base | varies | — |
| LiDAR upgrade | RPLidar S3 (ToF, IP65) or YDLidar G4 | 150–200 | Outdoor / longer range |
| 24 V drivetrain tuning, spare gearbox | — | 50 | Bring-up damage margin |

Without PX4, RTK integrates as an F9P + laptop NTRIP client feeding `navsat_transform`
directly — arguably simpler than MAVLink RTK injection.
