# Purchase Request — MRider Platform, Fall 2026

**Requested by:** Jaerock Kwon, BIMI Lab · **Course:** 자율주행미들웨어응용 (Autonomous Driving
Middleware Applications) · **Prepared:** 2026-09-21 · **Budget ceiling:** ₩4,000,000

> 한국어본: [구매 요청서 (Korean)](purchase-request-2026-fall-ko.md)

---

## Summary

| | |
|---|---|
| **Requested** | **3 complete vehicle sets** |
| **Total** | **₩3,921,480** |
| **Against ceiling** | 98.0% — **₩78,520 remaining** |
| **4 sets** | **₩5,228,640 — exceeds the ceiling by ₩1,228,640. Not requested.** |

Each set is one drive-by-wire research vehicle: a 12 V ride-on chassis converted to computer
control, with the sensing needed for autonomous navigation. Students work in four subsystem teams
and merge onto the vehicles late in the semester.

> [!IMPORTANT]
> **Why three and not four**
>
> Four sets do not fit, and not narrowly. Even **stripped of every perception component** — no
> LiDAR, no camera, no IMU — four sets come to **₩4,275,720**, still ₩275,720 over the ceiling.
>
> A fourth set cannot be reached by reducing scope; it needs roughly ₩1.3 M more. Three complete
> sets fit with ₩78,520 in hand.

---

## Per-set bill of materials

Prices are **KRW, VAT included**, as listed by the vendor on **2026-09-21**. The **Basis** column
states how each price is known.

| | |
|---|---|
| **V** | Verified — read from the vendor's own product page |
| **L** | Lead — vendor identified, price from an aggregator, not yet confirmed |
| **E** | Estimated — converted from the design BOM at 1 USD = 1,362 KRW |

### Tier 1 — vehicle and drive-by-wire core

| # | Item | Purpose | Vendor / URL | Unit (₩) | Basis |
|---|------|---------|--------------|---------:|:-----:|
| 1 | Vehicle, 12 V single-seat ride-on | The platform itself, converted from a remote-control toy into a computer-controlled research vehicle | 쿠팡<br>`https://www.coupang.com/vp/products/9597329401` | 229,000 | V |
| 2 | Teensy 4.1 microcontroller | Real-time controller: closes the steering position loop at ≥200 Hz, shapes throttle, reads encoders, runs the safety supervisor | 디바이스마트<br>`https://www.devicemart.co.kr/goods/view?no=14276922` | 74,250 | V |
| 3 | Sabertooth 2x32 motor driver | Drives both rear traction motors. Chosen for its signal-loss timeout and current limiting, which are required safety behaviours | 원스톱<br>`https://one-stop.co.kr/goods/view?no=11156` | 250,000 | V |
| 4 | Steering gearmotor + encoder | Actuates the steering column. Sized from a torque measurement taken on the delivered vehicle — second batch | 디바이스마트 (2차 발주)<br>`https://www.devicemart.co.kr` | 48,000 | E |
| 5 | Absolute steering angle sensor | Measures true road-wheel angle, so gearbox backlash appears as measured error rather than hidden bias | 디바이스마트 (2차 발주)<br>`https://www.devicemart.co.kr` | 27,000 | E |
| 6 | Drive encoder + shaft adapter | Measures distance travelled at the rear axle; the input to odometry | 디바이스마트<br>`https://www.devicemart.co.kr` | 25,000 | E |
| 7 | Relay MUX hardware (2× DPDT + sockets, diodes, transistors) | Hardware selection between factory remote control and computer control. Defaults to factory control when unpowered | 디바이스마트<br>`https://www.devicemart.co.kr` | 34,000 | E |
| 8 | E-stop switch + DC contactor | Emergency traction cut-off. The contactor carries motor current; the mushroom button only switches its coil | 한국미스미<br>`https://kr.misumi-ec.com` | 35,000 | E |
| 9 | Pololu 4-channel RC servo multiplexer #2806 | Hardware override that works with the controller software completely dead. Required by the architecture review | 디바이스마트<br>`https://www.devicemart.co.kr/goods/view?no=1179242` | 31,680 | V |
| 10 | RC transmitter + receiver (FlySky FS-i6 + FS-iA6B) | Live manual override for the safety operator during all testing | 팰콘샵<br>`https://www.falconshop.co.kr/shop/goods/goods_view.php?goodsno=100004833` | 75,000 | E |
| 11 | Isolated logic rail (12 V 7 Ah battery + charger + 2× DC-DC) | Separates controller power from motor power, so motor current surges cannot reset the safety controller | 11번가 / 디바이스마트<br>`https://www.11st.co.kr/products/1334182072` | 60,000 | E |
| 12 | Wiring, connectors, fuses | Silicone wire, XT60/spade terminals, inline fuses, heatshrink | 디바이스마트<br>`https://www.devicemart.co.kr` | 55,000 | E |
| 13 | Steering shaft coupler / adapter | Couples gearmotor and angle sensor to the column. Depends on the measured column diameter — second batch | 로컬 가공 (2차 발주) | 20,000 | E |
| 14 | Mounts / 3D-print material | Sensor mast, LiDAR and camera mounts, controller enclosures | 로컬 | 41,000 | E |
| 15 | USB gamepad (Logitech F710 class) | Student teleoperation from the laptop — distinct from item 10, which is the safety override | 다나와 / 컴퓨존<br>`https://prod.danawa.com/info/?pcode=1880276` | 64,000 | L |
| | | | **Tier 1 subtotal** | **1,068,930** | |

### Tier 2 — perception

| # | Item | Purpose | Vendor / URL | Unit (₩) | Basis |
|---|------|---------|--------------|---------:|:-----:|
| 16 | 2D LiDAR, RPLIDAR A1M8-R6 | 360° range sensing for mapping and obstacle avoidance. The primary navigation sensor | 아이씨뱅큐<br>`https://www.icbanq.com/P013130745` | 155,430 | V |
| 17 | USB camera, 1080p wide-FOV | Forward vision for teleoperation and, later, learning-based control | 디바이스마트<br>`https://www.devicemart.co.kr` | 41,000 | E |
| 18 | IMU, BNO085 9-DoF | Orientation sensing, fused with wheel odometry to correct drift | 아이씨뱅큐<br>`https://www.icbanq.com/P013465652` | 41,800 | L |
| | | | **Tier 2 subtotal** | **238,230** | |

### Totals

| | Per set | × 3 sets |
|---|--------:|---------:|
| Tier 1 — vehicle and drive-by-wire | 1,068,930 | 3,206,790 |
| Tier 2 — perception | 238,230 | 714,690 |
| **Total** | **1,307,160** | **₩3,921,480** |
| | | *remaining: ₩78,520* |

---

## Notes for the approving office

### Two purchases, not one

Three items — **#4 steering gearmotor, #5 angle sensor, #13 shaft coupler** — **cannot be specified
until the vehicle is in hand.** The gearmotor is sized against steering torque measured on the
delivered chassis; the sensor and coupler depend on measured shaft travel and column diameter.

They are budgeted here at **₩95,000 per set (₩285,000 total)** so the approved amount covers them,
but they will be ordered in a **second batch** about two weeks after the vehicles arrive. Ordering
them now is the most common way to waste money on this build.

### Price confidence

| Basis | Share of each set |
|---|---:|
| **V** — verified on the vendor page | ₩740,360 (57%) |
| **L** + **E** — lead or estimated | ₩566,800 (43%) |

> [!WARNING]
> **The headroom is thin — please review this with the approval**
>
> ₩78,520 is **2.0%** of the request, while **43% of the cost is still estimated**. If
> the estimated items land 10% above expectation, the total reaches **₩4,091,520** and exceeds the
> ceiling.
>
> One response is already decided: **defer Tier 2 on a single set — ₩238,230.** Perception is not
> needed until week 10, and the course is deliberately structured so that perception spend follows
> the drive-by-wire milestones. The adjustment therefore costs no schedule.

### Sabertooth motor driver — selected on lead time, not price

Item #3 is available from Coupang at ₩215,300, but with an **estimated arrival of 8 October** —
about three weeks. This request uses **one-stop at ₩250,000, which ships immediately**. That is
₩104,100 more across three sets, in exchange for holding the bench-test schedule.

### Items not in this request

**Tools and consumables** are shared across all sets and are not per-set costs: ratcheting crimper,
multimeter with a 20 A range, **bench power supply with adjustable current limit**, digital angle
gauge, spring scale (0–20 kg). If the lab does not already hold these they should be requested
separately. The bench supply in particular is a safety item — it is what turns a runaway steering
loop into a harmless buzz at first power-on.

**Laptops** are not included; students use their own.

---

## Sources

Vendor links, the date each price was read, and the exchange rate used are recorded in
[Build Guide §1.2.1 — Sourcing in Korea](build/01-bom-sourcing.md#121-sourcing-in-korea-verified-2026-09-15).
Design justification for every line item is in [bom.md](design/bom.md), which links each part to the
document that requires it.

Actual prices paid go in the [Order Log](order-log.md) as parts arrive — the estimates above will
not match, and the next cohort needs the real numbers.
