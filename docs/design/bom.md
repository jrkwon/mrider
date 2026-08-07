# Bill of Materials (BOM)

> Part of the MRider design set. Siblings: [architecture.md](architecture.md) ·
> [vehicle.md](vehicle.md) · [dbw.md](dbw.md) · [safety.md](safety.md) ·
> [sensors.md](sensors.md) · [software.md](software.md) ·
> [calibration.md](calibration.md) · [overview.md](overview.md)

**All prices are estimates as of July 2026** in USD and vary by retailer, coupon,
and stock. They are for budgeting, not quotes. Verify at purchase.

This BOM covers **two tiers**:

- **Minimum tier** — no GNSS, budget LiDAR ([YDLidar G4](sensors.md)), budget
  global-shutter camera ([Arducam AR0234](sensors.md)). Smallest cost to a
  working, mappable, behavior-cloning-capable MRider.
- **Full tier** — adds GNSS, upgrades to [RPLidar S3](sensors.md) ToF LiDAR and
  the [RealSense D435i](sensors.md) depth camera.

The **laptop is not a purchased line item** — it is lab-supplied/reused (see
[sensors.md §6](sensors.md)), and runs on its own battery in v1
([safety.md](safety.md) power budget).

Items marked **Reuse?=Yes** already exist in the lab's
[mrover](https://github.com/jrkwon/mrover) build and may not need repurchase for a
lab that is converting an existing rig; they are still listed and priced so a
fresh build has a complete total.

---

## Itemized BOM

| # | Item | Spec / Model | Design ref | Reuse? (mrover) | Min tier ($) | Full tier ($) | Source / note |
|---|------|--------------|-----------|-----------------|-------------:|--------------:|---------------|
| 1 | **Vehicle (chassis)** | 24 V 2-seater ride-on, dual motors, parent remote | [vehicle.md](vehicle.md) | Yes (class) | 300 | 300 | Target A-1002549549 / Amazon B0CJTWDC38 class; ~$260–450 |
| 2 | **Pixhawk 6C + PM02 power module** | Holybro Pixhawk 6C, PM02 V3 | [dbw.md](dbw.md), [architecture.md](architecture.md) | Yes | 220 | 220 | Holybro / Amazon B0BB1VTXGR; mrover BOM ~$220 |
| 3 | **Sabertooth 2x32** | Dimension Eng. 2×32 A dual motor driver | [dbw.md](dbw.md) | Yes | 125 | 125 | makermotor PN00218-DME3; mrover BOM ~$125 |
| 4 | **Steering gearmotor + encoder** | Geared DC motor w/ encoder (RS-385/390 class) or wiper-motor fallback | [dbw.md](dbw.md) steering actuation | Partial | 35 | 35 | Sized ≥2× measured column torque ([dbw.md](dbw.md) procedure) |
| 5 | **Absolute steering angle sensor** | Hollow-shaft / coupled potentiometer (or AS5600-class magnetic) | [dbw.md](dbw.md) ADR B / sensor-tech ADR | New | 20 | 20 | Tech chosen in [dbw.md](dbw.md); single-turn range caveat |
| 6 | **Drive encoder + shaft adapter** | Quadrature/Hall encoder (52 PPR class) + 3.15→5 mm adapter | [dbw.md](dbw.md) ADR C; `code/code.ino:27` | Yes | 18 | 18 | mrover shaft-adapter method |
| 7 | **Arduino Nano V3** | ATmega328P (USB-serial 115200; I2C 0x02 retained) | [dbw.md](dbw.md) firmware; `code/code.ino` | Yes | 13 | 13 | mrover BOM ~$13 |
| 8 | **USB-TTL serial adapter** | 3.3 V FTDI/CP210x cable | [architecture.md](architecture.md) feedback path | Yes | 13 | 13 | Nano→laptop USB; mrover BOM ~$13 |
| 9 | **Relay MUX hardware** | 2× DPDT automotive relays/contactors + sockets + flyback diodes + drive transistors | [safety.md](safety.md) authority arbitration | New | 25 | 25 | Default de-energized = STOCK mode |
| 10 | **E-stop switch** | Latching mushroom, traction-rated (high current / contactor coil) | [safety.md](safety.md) E-stop semantics | New | 15 | 15 | Cuts traction power only |
| 11 | **RC transmitter + receiver** | PX4-bindable (FrSky Taranis-class TX + SBUS/ACCESS RX) | [safety.md](safety.md) RC-via-PX4 override | New | 120 | 120 | Live DBW manual override; TX ~$85 + RX ~$35 |
| 12 | **2D LiDAR** | Min: YDLidar G4 · Full: RPLidar S3 | [sensors.md §2](sensors.md) | G4: Yes | 260 | 460 | mrover ships YDLidar params; S3 ToF/IP65 upgrade |
| 13 | **Front camera** | Min: Arducam AR0234 global-shutter USB3 · Full: RealSense D435i | [sensors.md §1](sensors.md) | No | 180 | 350 | Global-shutter RGB for behavior cloning |
| 14 | **GNSS module** | Full only: Holybro M9N/M10 (RTK-ready growth path) | [sensors.md §4](sensors.md) | Optional | 0 | 90 | Excluded from min tier by design |
| 15 | **Wiring / connectors / fuses** | Silicone wire, spade/XT60 connectors, inline fuses, terminals, heatshrink | [safety.md](safety.md) power budget | Partial | 40 | 45 | Slightly higher for full tier extra runs |
| 16 | **Steering shaft coupler / adapter** | Column coupler, set screws, bracket | [dbw.md](dbw.md); [calibration.md](calibration.md) | New | 15 | 15 | Couples gearmotor + angle sensor to column |
| 17 | **Mounts / 3D prints** | Sensor mast + camera/LiDAR mounts + Pixhawk/Sabertooth enclosures | [sensors.md §5](sensors.md) | Partial | 30 | 35 | Reuse mrover STL cases (`config/3D_design/v3/`); print filament/hardware |
| — | **Laptop (onboard computer)** | RTX-class GPU, ≥16 GB RAM, ≥3× USB3, ≥2 h battery | [sensors.md §6](sensors.md) | Yes | *reuse* | *reuse* | Lab-supplied; own battery (not in totals) |

**17 purchasable line items** (laptop excluded as reuse).

---

## Computed Subtotals

| Tier | Sum of line items | Contingency (~10%) | **Estimated total** |
|------|------------------:|-------------------:|--------------------:|
| **Minimum** (no GNSS, YDLidar G4, Arducam AR0234) | **$1,429** | ~$143 | **~$1,570** |
| **Full** (GNSS, RPLidar S3, RealSense D435i) | **$1,899** | ~$190 | **~$2,090** |

Line-item sums (verify against the table above):

- **Minimum:** 300 + 220 + 125 + 35 + 20 + 18 + 13 + 13 + 25 + 15 + 120 + 260 +
  180 + 0 + 40 + 15 + 30 = **$1,429**.
- **Full:** 300 + 220 + 125 + 35 + 20 + 18 + 13 + 13 + 25 + 15 + 120 + 460 +
  350 + 90 + 45 + 15 + 35 = **$1,899**.

Delta (full − min) = **$470**, entirely in the LiDAR (+$200), camera (+$170),
GNSS (+$90), and minor wiring/mount (+$10) upgrades.

Contingency (~10%) covers shipping, taxes, connector/fastener miscellany, and the
verification-driven risk that the **drive-motor stall current** ([vehicle.md §3.1](vehicle.md)) forces a current-limit accessory or a second motor driver.

---

## Reuse Notes (lab already has an mrover build)

For a lab converting an **existing** mrover rig rather than building fresh, the
following are typically already owned and can be subtracted:

- Pixhawk 6C + PM02 (#2), Sabertooth 2x32 (#3), Arduino Nano (#7), USB-TTL (#8),
  drive encoder + shaft adapter (#6), YDLidar G4 (#12, min tier), 3D-printed
  enclosures (#17, `config/3D_design/v3/`), and the laptop.
- **Reuse-adjusted minimum tier** (buying only the genuinely new/vehicle-specific
  items — vehicle, steering gearmotor, angle sensor, relay MUX, E-stop, RC set,
  camera, couplers, wiring): roughly **$300 + 35 + 20 + 25 + 15 + 120 + 180 + 15
  + 40 + 30 = ~$780** before contingency.

New-to-MRider items (not in the mrover BOM) are the **absolute steering angle
sensor** (#5), **relay MUX** (#9), **E-stop** (#10), **RC TX/RX** (#11), the
**global-shutter camera** (#13), and the **GNSS** (#14, full tier) — these
implement the [DBW angle servo](dbw.md), [safety authority arbitration](safety.md), and the [global-shutter behavior-cloning](sensors.md) decisions that
distinguish MRider from the base mrover recipe.

---

## GNSS RTK Growth Path (beyond full tier)

Not in either total; a documented future upgrade ([sensors.md §4](sensors.md)):

| Item | Spec | Est. ($) |
|------|------|---------:|
| RTK GNSS rover | u-blox ZED-F9P-class module | 220–300 |
| RTK corrections | NTRIP subscription or local base station | varies |

PX4 already accepts RTK injection over MAVLink, so this is a module + corrections
swap, not new firmware.
