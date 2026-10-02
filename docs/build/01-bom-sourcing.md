# 1. BOM & Sourcing

**Goal:** acquire every part before touching the vehicle, at a known cost.

Order the components for Tier 1 and confirm long-lead items (vehicle, LiDAR, gearmotor) are
in hand. Cross-check quantities and connectors against the bill of materials.

- **Prerequisites:** budget decided; Tier 1 vs. Tier 2 timing understood.
- **Specification:** [design/bom.md](../design/bom.md)
- **Expected outcome:** all line items received; totals reconciled against the BOM.

> [!WARNING]
> **Draft — not yet validated on hardware**
>
> This checklist is derived from [bom.md](../design/bom.md). No MRider build has been
> sourced yet, so vendor availability, current prices, and connector compatibility are
> **unconfirmed**. Prices in the BOM are estimates as of July 2026 and vary by retailer,
> coupon, and stock — verify at purchase.

---

## 1.1 Two purchase tiers, bought at different times

The BOM is split so the **perception spend follows the DBW gates**. If the steering loop fails
its accuracy gate at [bring-up Stage 1](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first),
you have not yet bought Tier 2.

| Tier             | What it covers               | When to order |     Line items | With ~10% contingency |
| ---------------- | ---------------------------- | ------------- | -------------: | --------------------: |
| **Tier 1** | Vehicle + DBW core + gamepad | Week 1        |           $678 |                 ~$745 |
| **Tier 2** | LiDAR, camera, IMU           | By week 10    |           $168 |                 ~$185 |
| **Both**   |                              |               | **$846** |       **~$930** |

This is down from ~$1,570 in the previous revision. The Tier 1 figure was also **corrected on 2026-08-10** — it had been published as $773 while its line items summed to $638, the vehicle price drop never having been re-added. See
[bom.md § Change record](../design/bom.md#change-record-why-the-total-fell-from-1570-to-1035)
for where the money went and what was deferred rather than deleted.

> [!TIP]
> **Already have an mrover rig?**
>
> Reusable: **Sabertooth 2x32**, drive encoder + shaft adapter, 3D-printed enclosures
> (though the controller cases need rework), and the laptop — roughly **−$173**.
>
> **Not reusable:** the Pixhawk 6C, PM02, Arduino Nano, and USB-TTL adapter. MRider's
> controller is a single Teensy 4.1
> ([D3](../design/adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07)). Those
> parts remain useful for other projects; this is a deliberate architectural departure, not
> a write-off.
>
> With a used vehicle, lab-reused Sabertooth and encoder, and printed mounts, the realistic
> floor is **~$620 all-in**.

## 1.2 Order long-lead items first

Order in this sequence. The first group gates everything else; the last group can be bought
at the hardware store the week you need it. **Vendors and prices are in
[§1.2.1](#121-sourcing-in-korea-verified-2026-09-15)**, not here — one place, so they cannot drift.

=== "Week 0 — order immediately"

| Item | BOM # | Why it gates the build |
|------|-------|------------------------|
| Vehicle (12 V single-seat ride-on) | 1 | Nothing can be measured until it arrives; seasonal stock |
| Teensy 4.1 | 2 | Needed from step 4; cheap enough to buy a spare |
| RC transmitter + receiver (i-BUS) | 10 | Needed for step 4 override verification |
| Hardware RC signal MUX | 9 | Safety-critical and easy to forget — see the warning below |

=== "Week 1 — after the vehicle arrives"

| Item | BOM # | Why it waits |
|------|-------|--------------|
| Steering gearmotor + encoder | 4 | **Sized from a measurement you cannot take yet** — see §1.3 |
| Absolute steering angle sensor | 5 | Technology depends on measured shaft travel (§1.3) |
| Steering shaft coupler / adapter | 13 | Depends on the actual column diameter |

=== "Anytime (Tier 1)"

| Item | BOM # |
|------|-------|
| Sabertooth 2x32 | 3 |
| Drive encoder + 3.15→5 mm shaft adapter | 6 |
| Relay MUX hardware (2× DPDT + sockets + flyback diodes + drive transistors) | 7 |
| E-stop switch (latching mushroom, traction-rated) | 8 |
| Isolated logic rail (12 V SLA + charger + 2× DC-DC) | 11 |
| Wiring / connectors / fuses | 12 |
| Mounts / 3D prints | 14 |
| USB gamepad (Xbox-layout, teleop) | 15 |

=== "By week 10 (Tier 2)"

| Item | BOM # |
|------|-------|
| 2D LiDAR (RPLIDAR A1M8) | 16 |
| Front camera (USB 1080p) | 17 |
| IMU (BNO085 class) | 18 |

> [!CAUTION]
> **The hardware RC signal MUX is not optional**
>
> Item #9 is the **condition on which the single-Teensy architecture was adopted**
> ([safety.md §1.2](../design/safety.md#12-live-override-inside-dbw-mode-two-layers)). With
> one MCU holding the steering loop, throttle, override, and arming, a firmware hang loses
> all four — unless override is a *wiring* property. Order it with the RC set, not later.
> It is $18 and it is the difference between a defensible safety story and a fragile one.

## 1.2.1 Sourcing in Korea — verified 2026-09-15

Prices below were read off the vendor page on **2026-09-15** at **1 USD = 1,362 KRW**. Anything
marked *unverified* came from a search result, not from the vendor's own page — treat it as a lead,
not a quote.

| # | Item | Where | Price | Status |
|---|------|-------|------:|--------|
| 1 | Vehicle | [Coupang](https://www.coupang.com/vp/products/9597329401?itemId=28670205397&vendorItemId=95592760206) | ₩229,000 | recorded earlier |
| 3 | **Sabertooth 2x32** | [Coupang](https://www.coupang.com/vp/products/8926855294?itemId=26092961552&vendorItemId=93333777957) | **₩215,300** | verified — est. arrival **10/8** |
| 3 | ↳ alternative | [one-stop.co.kr](https://one-stop.co.kr/goods/view?no=11156) | ₩250,000 VAT incl. | verified — ships soon |
| 3 | ↳ alternative | [Dimension Engineering](https://www.dimensionengineering.com/products/sabertooth2x32) | $124.99 ≈ ₩185,000 landed | verified — ~2 weeks, USPS |
| 9 | Pololu RC servo MUX #2806 | [DeviceMart 1179242](https://www.devicemart.co.kr/goods/view?no=1179242) | **₩31,680** VAT incl. | verified — ships ~1 week |
| 2 | Teensy 4.1 | [DeviceMart 14276922](https://www.devicemart.co.kr/goods/view?no=14276922) | **₩74,250** VAT incl. | verified |
| 16 | RPLIDAR A1M8-R6 (DFR0315) | [ICBanQ](https://www.icbanq.com/P013130745) | ₩141,300 + VAT = **₩155,430** | verified, ships ≤1 week |
| 10 | FlySky FS-i6 + FS-iA6B | [팰콘샵 100004832](https://www.falconshop.co.kr/shop/goods/goods_view.php?goodsno=100004832) | ₩139,160 VAT incl. | **verified in hand 2026-10-01** — iA6B with i-BUS port, ×3. Read the receiver warning below before buying elsewhere: the title said iA6 |

**Everything in Tier 1 that was thought to need importing is available domestically.** The
Sabertooth is on Coupang and at one-stop; the Pololu MUX is at DeviceMart. The "no Korean source"
reading in the first pass of this section was wrong, and came from searching badly — DeviceMart and
Eleparts render prices in JavaScript and return nothing to an automated search, which is a limit of
the search, not a fact about the market.

> [!NOTE]
> **Two prices came in well over the BOM estimate**
>
> | | BOM est. | actual | over by |
> |---|---:|---:|---:|
> | Teensy 4.1 | $32 ≈ ₩43,600 | ₩74,250 | **+70%** |
> | Pololu MUX #2806 | $18 ≈ ₩24,500 | ₩31,680 | +29% |
>
> Both are the domestic premium on a US part, and both are worth paying here: the Pololu is
> [listed "Rationed"](https://www.pololu.com/product/2806) at source, and it is the part
> [§1.2](#12-order-long-lead-items-first) says not to be waiting on. Together they add about
> ₩38,000 to Tier 1 — record the actuals in the [Order Log](../order-log.md) rather than the
> estimates.

### Leads still to confirm

Everything here came from a search result rather than the vendor's own page — DeviceMart and
Eleparts render prices in JavaScript, so they cannot be read automatically. **Confirm before
ordering.**

| # | Item | Lead | Indicative | BOM est. |
|---|------|------|-----------:|---------:|
| 10 | FlySky FS-i6 + **FS-iA6B** | 알씨뱅크, 팰콘샵, 다나와 | — | $55 ≈ ₩74,900 |
| 15 | Logitech F710 gamepad | 다나와, 컴퓨존, 11번가 | ₩58,000–69,900 | $40 ≈ ₩54,500 |
| 18 | BNO085 (Adafruit breakout) | ICBanQ · [DeviceMart 12507416](https://www.devicemart.co.kr/goods/view?no=12507416) · VCTec | ~₩41,800 | $28 ≈ ₩38,100 |
| 11 | ~~12 V 7 Ah SLA (로케트 ES7-12)~~ → **2–3 Ah, 9.5–14 V, LiFePO₄ preferred** | 11번가, 쿠팡, 알리 | — | **Re-specified 2026-10-01** — the 7 Ah SLA is 3× oversized and 2.5 kg. See §1.2.4 |
| 11 | **Charger matched to the pack chemistry** | same vendors as the pack | — | Buy it *with* the pack, not separately — a mismatched charger is a fire |
| 11 | **DC-DC buck 12→5 V, ≥ 2 A, ×2** | DeviceMart 전원/파워 → DC-DC 컨버터 | — | Non-isolated is fine (§1.2.4). One for Teensy + sensors, one for RC + signal MUX |
| 11 | Electrolytic 1000 µF 16 V ×2, divider resistors, 5 A blade fuse + holder | DeviceMart, 엘레파츠 | — | Hold-up and the undervoltage monitor — passive parts, no module needed |
| 8 | 22 mm mushroom E-stop | 한국미스미, 레고전자부품, 다아라몰 (IDEC) | — | $15 — **but read the warning** |

> [!IMPORTANT]
> **Buy the FS-iA6B, not the FS-iA6**
>
> Korean RC shops list the FS-i6 bundled with either. The plain **FS-iA6 is PWM only** — no serial
> stream, so [Layer A](../design/safety.md#12-live-override-inside-dbw-mode-two-layers) cannot be
> built on it. Only the **FS-iA6B** carries the i-BUS port. One letter, and it is the difference
> between having a closed-loop override and not.

> [!CAUTION]
> **A 22 mm mushroom button will not switch this traction circuit — and its rating will not say so**
>
> [§1.4](#14-substitution-notes) already requires the E-stop to be traction-rated. What the Korean
> listings make easy to miss is that their ratings are **AC** ratings: a switch sold as "10 A 250 V"
> may be rated for a small fraction of that at **12 V DC**, because DC has no zero crossing to
> extinguish the arc. Drive stall current here is
> [unmeasured](../design/vehicle.md#31-drive-motor-stall-current-vs-sabertooth-rating-critical) and
> both rear motors share one channel.
>
> Use the pattern the BOM already permits: the **mushroom button switches a contactor coil**, and a
> **DC-rated contactor** (12 V coil, **50–60 A continuous**, sold as a battery isolator)
> carries the traction current. **DC-rated is the part that matters, not the amp figure** — an
> AC-rated switch breaking DC can weld its contacts closed, and that failure is silent until the
> moment you press the button.
>
> *Sized down from "100 A+" on 2026-10-01.* The stock ECU is rated 20 A and the motor driver
> limits at 30 A, so 50–60 A is already ~2× margin. Over-sizing cascades: a bigger contactor draws
> more coil current, and coil current is what sets the button's rating (below). The button then only ever sees coil current, which is what a 22 mm
> switch is actually good for.
>
> Do not buy the button until the contactor is chosen — its coil current sets the button's rating.

### Still unsourced

No usable Korean lead found yet for: **#6** drive encoder + 3.15→5 mm shaft adapter, **#7** relay
MUX hardware (2× DPDT + sockets + flyback diodes + drive transistors), **#12** wiring / connectors /
fuses, **#14** 3D-print filament and hardware, **#17** USB 1080p camera.

Most are commodity and will come from DeviceMart, Eleparts or Coupang; they are listed here so the
gap is visible rather than assumed closed. **#4, #5 and #13 are deliberately absent** — they are the
[measure-first parts](#13-two-parts-you-must-not-order-blind).

> [!NOTE]
> **The one-stop.co.kr listing: the title is stale, the product is a 2x32**
>
> [one-stop.co.kr #11156](https://one-stop.co.kr/goods/view?no=11156) is titled **"DRI0004
> Sabertooth Dual 25A"**, which reads like a mislabelled 2x25. It is not. The page body is
> unambiguous:
>
> - every datasheet link points at **`Sabertooth2x32.pdf`**, `Sabertooth2x32.doc`, and
>   `Sabertooth2x32QuickStart.pdf` on dimensionengineering.com
> - it states **6–30 V nominal, 33.6 V absolute max** — the 2x32's range. The 2x25 is 6–24 V
>   nominal, 30 V max
> - it states **32 A continuous / 64 A peak**, and names the **v1.1** revision
>
> `DRI0004` is DFRobot's legacy SKU string for this line, and DFRobot themselves have not kept it
> straight: their own wiki page for DRI0004 is titled *Sabertooth Dual 32A* while its specification
> table says 25 A / 6–24 V. The Korean reseller inherited the title and replaced the body.
>
> **The only residual risk is procurement, not specification.** If the vendor picks stock by SKU
> rather than by the page you read, a 2x25 could arrive. One email before paying settles it — ask
> them to confirm 32 A/64 A and the 6–30 V range on the unit they will actually ship.

> [!TIP]
> **Domestic at ₩250,000 versus importing at ~₩185,000 — both are defensible**
>
> Dimension Engineering list the 2x32 at **$124.99** and ship worldwide at a flat rate ("our
> shipping prices are the same whether you live in the USA or overseas"), by USPS air mail, ~10
> business days.
>
> That routing matters for tax. Korea's **$200** de-minimis under KORUS applies only to **courier**
> shipments (DHL/FedEx/UPS); goods arriving by **international post** fall under the **$150**
> threshold. At $124.99 the Sabertooth is below either, so it should clear free of duty and VAT —
> but the margin is thin enough that adding a second item to the same order could push the parcel
> over and tax the whole thing, not just the excess.
>
> | | landed | arrives | if it fails |
> |---|---|---|---|
> | **Coupang** | **₩215,300** | est. **10/8** | domestic |
> | one-stop.co.kr | ₩250,000 | ships soon | domestic A/S |
> | Dimension Engineering | ~$135 ≈ ₩185,000 | ~2 weeks | return shipping to the USA |
>
> The spread is about **₩65,000** end to end, which is small against what it buys: a local return
> path on the most expensive board in the build.
>
> **Time is the real variable, not price.** Coupang's estimated 10/8 is roughly three weeks out —
> slower than importing — so if the bench schedule needs the Sabertooth before then, one-stop
> shipping now is worth its ₩35,000 premium over Coupang. Check the Coupang listing's seller and
> dispatch estimate before committing; a long estimate there usually means it ships from overseas
> anyway, in which case the domestic advantage is only the return path.

> [!WARNING]
> **Order the Pololu MUX first, not last**
>
> Pololu lists #2806 as **"Rationed"**. It is $17.95, it ships from the US, and
> [§1.2](#12-order-long-lead-items-first) makes it the condition the single-Teensy architecture was
> adopted under. A cheap part on allocation is exactly the one that arrives last. Order it in the
> same batch as the RC set.

### #6 drive encoder — what to actually buy

`드라이브 엔코더 + 샤프트 어댑터` names **four** parts, funds three of them, and omits the electrical
limits that decide which encoder is even safe to connect. This section is the buyable version.

**Quantity: one per vehicle — three in total, not six.** Only one motor of the paralleled rear pair
is instrumented ([ADR C](../design/dbw.md#8-adr-c-drive-distance-encoding)). That is deliberate, and
the reason it is stated here is so nobody "corrects" it to two per vehicle.

#### The four parts

| | Part | Gated on a measurement? |
|---|---|---|
| **6a** | Quadrature encoder | No — specify now |
| **6b** | Shaft adapter / coupling | **Yes** — the shaft diameter is unknown |
| **6c** | **Encoder mounting bracket** | **Yes** — depends on the motor's mounting face |
| **6d** | Fasteners, threadlock, cable tie-downs | No |

**6c has never been in the BOM.** [02-mechanical.md §2.6](02-mechanical.md) requires *"the encoder
body bracketed to the motor mount"*, and #13 is the steering coupler while #14 is the sensor mast.
Nothing funded the part that holds the encoder still. **Without it the body simply rotates with the
shaft and reads zero** — a failure that looks like a dead sensor.

#### Hard electrical requirements

> [!CAUTION]
> **3.3 V logic. The Teensy 4.1 is not 5 V tolerant.**
>
> Its GPIO is 3.3 V, and a 5 V push-pull encoder output **will damage the pin it is wired to**. This
> limit appears nowhere else in the design record, which is why it is stated here as a hard filter.
>
> Most hobby encoder modules are sold as "3.3 V–5 V" and are fine. If a part outputs 5 V only, it
> needs a level shifter — budget one, and record the substitution.

**Quadrature A/B is required. A single-channel speed sensor is not sufficient**, and this is the
easiest mistake to make because those sensors are cheaper and far more common. A single channel
gives pulse *rate* with no direction, so it cannot distinguish forward from reverse.

That matters concretely here:

- Nav2 plans with **Reeds-Shepp** paths and `allow_reversing: true` — this vehicle reverses as a
  matter of course, not as an exception
- The vehicle can roll backwards on a slope, or be pushed, with no command to infer sign from

Inferring direction from the *commanded* throttle instead would be wrong in exactly the cases where
odometry matters most. `03-electrical.md` wires this to a **Teensy hardware quadrature decoder**, so
A/B is what the design already assumes.

| Requirement | Value |
|---|---|
| Output | **Quadrature A/B**, two channels. Index/Z not needed |
| Logic level | **3.3 V** (or 3.3–5 V compatible) |
| Supply | From the logic rail — state the voltage at purchase |
| Output type | Open-collector or push-pull, **stated**. Open-collector needs pull-ups |
| Resolution | **Any** — see below |

#### PPR is deliberately unconstrained

The [roll-out calibration](../design/calibration.md#2-drive-distance-encoder-ticksmeters) derives
`meters_per_tick` from a measured distance and bypasses PPR entirely, so the *result* is correct
whatever the part turns out to be. **Do not pay for resolution.** Do not inherit a number either —
see finding **F7**.

The geometry sets a floor rather than a target. The wheel is 0.09 m radius — **0.566 m per
revolution** — and turns about **2.5 rev/s** at walking pace.

**As built** (magnets on the gearbox output hub, 1:1 with the wheel, quadrature decode):

| Magnet pairs | Counts / wheel rev | Distance per count | Counts over a 20 m run |
|---:|---:|---:|---:|
| 8 | 32 | 17.7 mm | 1,132 |
| 12 | 48 | 11.8 mm | 1,698 |
| 16 | 64 | 8.8 mm | 2,264 |

Even the coarsest of these clears the **≤ 2 % drift over 20 m** gate
([dbw.md §12](../design/dbw.md#8-adr-c-drive-distance-encoding)) with enormous margin — a ±1 count
error on the 8-magnet ring is **0.09 %**. Resolution is not the binding constraint; it never was.
Pick the count that fits the hub comfortably rather than the highest that fits at all, because even
magnet spacing matters more than magnet count.

> [!NOTE]
> **The motor-shaft figures this table used to carry were wrong twice over**
>
> It compared against *"motor shaft, behind ~20:1 gearing"*. The delivered motor is an **RS-390 at
> 18000 RPM**, which against ~149 wheel RPM at walking pace implies roughly **120:1** — six times
> the assumed ratio, so the quoted resolution was off by that factor.
>
> It is moot regardless: there is no accessible motor shaft on this vehicle, so that row describes
> a mount that cannot be built. Kept only as the reason the comparison is no longer made.

#### Which one to buy depends on what the vehicle turns out to be

![Three ways to instrument the drive, keyed on what the teardown finds: a rear shaft stub, an accessible output shaft, or neither](../images/drive-encoder-options.svg)

**Measure first** — the fields are in [V3](../order-log.md#v3-shaft-diameter-sizes-13).

> [!IMPORTANT]
> **Resolved for the 2026 vehicle: Branch C, mounted at the gearbox output hub.**
>
> Teardown found a **`DING LI RS 390-12V RPM 18000`** with a ~2 mm shaft carrying a 12-tooth pinion
> straight into a sealed gearbox — **no rear stub, no bare output shaft**, which is how the family
> is built rather than how this one is packaged. Branches A and B are both unavailable.
>
> The gearbox drives a **splined plastic hub** that the wheel slides onto, with clearance at the hub
> once the wheel is fitted. That is the mount: magnets on the hub, sensor bracketed to the gearbox
> housing. See [ADR C's recorded outcome](../design/dbw.md#8-adr-c-drive-distance-encoding) for why
> this is better than the original plan rather than a compromise.
>
> The `3.15 mm` the BOM inherited from B-MROVER is now doubly dead: it was orphaned when
> [ADR D-R](../design/vehicle.md) changed the vehicle class, and an earlier revision of this section
> guessed it was *"probably 3.175 mm, the RS-550 family standard"* — **the wrong family**, and moot
> now that no shaft is involved at all.
>
> **Branches A and B stay documented below.** The next cohort may receive a different chassis, and
> a tree whose branches have been pruned to the one that happened is no longer a tree.

| | What the teardown finds | What to buy |
|---|---|---|
| **A** | A **rear shaft stub** on the motor | Magnetic ring + dual-Hall board clamped to the stub, or a bore-matched incremental encoder. Bracket to the motor's rear face |
| **B** | No rear stub, but the **output shaft is reachable** before the gearbox | Ring magnet on the output shaft + Hall board on a bracket. Same electrical spec, different mount |
| **C** | Neither is accessible | **Wheel or axle side.** This is **[ADR C2](../design/dbw.md#8-adr-c-drive-distance-encoding)**, already recorded as the pre-registered upgrade path — taking it is a documented choice, not an improvisation |

> [!TIP]
> **The magnetic ring + Hall board serves all three branches**
>
> It needs no shaft *end* — only a cylindrical surface to grip and somewhere to bolt the sensor. That
> makes it the one part worth buying before the teardown decides anything, and it is why the tree
> does not fork into three incompatible shopping lists.
>
> Search **디바이스마트 → 센서 → 마그네틱/홀/리드/엔코더**
> ([category 000400040012](https://www.devicemart.co.kr/goods/catalog?code=000400040012)) and filter
> on the electrical requirements above.

> [!WARNING]
> **The cheap optical sensors are single-channel — check before buying**
>
> **HC-020K** (~₩8,800) and the LM393 slot-type speed modules are the obvious hits when searching for
> a motor encoder, and they are **one channel**. They measure speed, not direction.
>
> They are usable only in pairs, mounted with a quarter-slot offset to synthesise A/B — which is
> fiddly to align and easy to get wrong. If the budget allows, a purpose-built quadrature part is
> the better buy at this scale. ₩25,000 per vehicle covers it.

---

### #17 USB camera — what "1080p wide-FOV" actually has to mean

The BOM line said *"USB 1080p wide-FOV"*, which is not a specification — it is the marketing copy on
every camera in the category. What semester 1 actually needs:

| Requirement | Why it matters |
|---|---|
| **UVC class, no driver** | It must enumerate as `/dev/video*` and work with `v4l2_camera` or `usb_cam`. A camera needing a vendor SDK or a Windows-only driver is a dead end on Ubuntu 22.04 — [sensors.md](../design/sensors.md) makes plain UVC a requirement, not a preference |
| **MJPEG at the resolution you will use** | **The trap in this category.** USB 2.0 cannot carry 1080p raw at 30 fps. Many cameras advertise "1080p 30fps" and deliver it *only* in MJPEG; in raw YUYV the same camera drops to **5 fps**. A student sees 5 fps and concludes ROS is broken |
| **≥ 30 fps at 1280×720** | Teleop needs frame *rate*, not pixels. 720p30 is better to drive from than 1080p5, and this vehicle is driven at walking pace by someone watching the feed |
| **Focus that can be locked** | Autofocus hunts continuously on a moving vehicle and every hunt is a blurred frame. Fixed focus avoids this by construction; an autofocus camera is fine **if** it exposes the UVC focus control, because then you turn AF off once and forget it. If it does not, you cannot |
| **70–120° horizontal FOV** | Wide enough for situational awareness. Past ~120° the fisheye distortion is severe enough to complicate calibration for no teleop benefit |
| USB 2.0 | Sufficient at 720p30 MJPEG. USB 3.0 buys nothing here |

**Resolution is the least important item on this list.** 1080p is already more than teleop needs; the
things that decide whether the camera is usable are the format and the frame rate.

> [!TIP]
> **The acceptance test is two commands, and it settles every question above**
>
> ```bash
> sudo apt install v4l-utils
> v4l2-ctl --list-devices
> v4l2-ctl -d /dev/video0 --list-formats-ext
> ```
>
> The second prints **every format, resolution and frame rate the camera actually supports** — not
> what the box claims. Look for a line like `MJPG … 1280x720 … 30.000 fps`. If 30 fps appears only
> under `MJPG` and not `YUYV`, that is normal and fine; it just means the ROS node must request
> MJPEG.
>
> **If the camera is autofocus**, add a third command — this is what decides whether AF is a
> non-issue or a permanent defect:
>
> ```bash
> v4l2-ctl -d /dev/video0 --list-ctrls | grep -i focus
> ```
>
> You want to see `focus_automatic_continuous` (or `focus_auto` on older kernels). If it is there,
> AF is fully solved:
>
> ```bash
> v4l2-ctl -d /dev/video0 -c focus_automatic_continuous=0
> v4l2-ctl -d /dev/video0 -c focus_absolute=<value>      # tune once, outdoors, at driving distance
> ```
>
> **An empty result has two readings, and they are opposites.** Either the camera has no focus
> mechanism at all — fixed focus, nothing to control, which is the *good* outcome — or it has
> autofocus the driver does not expose, which cannot be fixed in software.
>
> Distinguish them from the rest of the same output, not by guessing:
>
> ```
> white_balance_temperature ... flags=inactive
> exposure_time_absolute    ... flags=inactive
> ```
>
> **If controls appear marked `inactive`, the driver is listing hardware that exists but is
> currently overridden by an auto mode.** A driver that surfaces inactive controls is not hiding
> anything — so the absence of *any* focus entry means there is no focus unit to expose. That is a
> fixed-focus camera.
>
> Confirm optically, because it takes ten seconds: point the camera at detailed text at **20 cm**,
> then at something **2–3 m** away, and watch the stream. A fixed-focus lens simply goes soft up
> close and stays that way. An autofocus lens visibly hunts — the image pulses out of focus and
> back — within a second or two of the scene changing.

> [!WARNING]
> **What autofocus actually breaks — it is narrower than "blurry pictures", and worse**
>
> The damage is not blur. It is that **autofocus changes the focal length**, and
> [calibration.md §3](../design/calibration.md#3-camera-intrinsics) produces a `camera_matrix`
> (`fx`, `fy`, `cx`, `cy`) that is only valid for **one fixed focus position**. A camera that
> refocuses has different intrinsics from moment to moment, so the stored
> `config/calibration/camera_front.yaml` is describing a lens the camera no longer has.
>
> [§4](../design/calibration.md#4-extrinsics-camera-lidar-base_link) then chains through those intrinsics —
> it verifies that a LiDAR return projects onto the correct camera pixel — so it inherits the error.
>
> | Use | Affected by uncontrollable AF? |
> |---|---|
> | **Navigation, SLAM, obstacle avoidance** | **No.** The camera is not in that pipeline at all — it is LiDAR ([software.md](../design/software.md)) |
> | Teleoperation | No. Occasional hunting is a nuisance, nothing more |
> | CNN object recognition | Largely no. Networks tolerate moderate blur; hunting is intermittent |
> | **Camera intrinsics (§3)** | **Yes — this is the one that breaks** |
> | **Camera↔LiDAR extrinsics (§4)** | **Yes**, because it is computed through §3 |
> | Projecting detections into 3D, camera/LiDAR fusion | **Yes**, same reason |
>
> These land in **weeks 12–14**, during merge. So an AF camera whose focus cannot be locked is
> usable for two thirds of the semester and then fails exactly when the tracks integrate.
>
> **Not a reason to avoid autofocus cameras** — nearly all UVC webcams expose the control, and one
> command settles it. It is a reason to run that command **on arrival in week 10**, not in week 12.
>
> **Outcome for the 2026 cohort's camera:** fixed focus, confirmed 2026-09-30. `--list-ctrls`
> exposes no focus unit at all while listing other controls as `inactive`, so nothing is being
> hidden. The intrinsics are stable and §3/§4 are unaffected — this risk did not materialise.
>
> Run all of this on **one unit before buying three**. It is also the natural `Secured` check for
> this row.

> [!CAUTION]
> **The camera meeting the spec is not enough — the ROS driver has to ask for MJPEG**
>
> Validated on the 2026 test unit, which is exactly the shape the warning above predicts:
>
> | | 1920×1080 | 1280×720 | 640×480 |
> |---|---|---|---|
> | **MJPG** | 30 fps | **30 fps** | 30 fps |
> | **YUYV** | **5 fps** | **10 fps** | 30 fps |
>
> Now the part that bites. In Humble:
>
> | Driver | MJPEG? | Default `pixel_format` |
> |---|---|---|
> | **`v4l2_camera`** | **No** — YUYV / UYVY / GREY only | **`YUYV`** |
> | **`usb_cam`** | **Yes** — `mjpeg2rgb`, `raw_mjpeg` | — |
>
> So `ros2 run v4l2_camera v4l2_camera_node` at its defaults asks this camera for **YUYV at 10 fps**
> on 720p. Nothing errors. The image is live, correct, and a third the rate it should be.
>
> **Use `usb_cam` with `pixel_format: mjpeg2rgb`.** [sensors.md](../design/sensors.md) names
> "`usb_cam`/`v4l2_camera`" as if interchangeable; for a camera whose 30 fps lives only in MJPEG,
> they are not.
>
> The diagnostic signature is worth knowing, because it looks like a hardware problem: **640×480
> runs at 30 fps while 720p runs at 10.** That is not a slow camera or a slow laptop — it is YUYV
> hitting the USB 2.0 bandwidth ceiling, and the ceiling moves with resolution.

> [!NOTE]
> **Phase 2 will need a different camera, and that is already decided**
>
> Behaviour cloning needs a **global shutter** — rolling shutter smears during turns and corrupts
> the steering labels. [sensors.md](../design/sensors.md) pre-registers an **Arducam AR0234** class
> part (~$160–180) for that phase.
>
> So do not over-buy now. Semester 1 delivers teleop and LiDAR SLAM, neither of which cares about
> rolling-shutter skew. A cheap compliant camera is the correct choice, and the money is better
> kept for the global-shutter part later.

---

### #7, #8, #11, #12, #14 — what to actually buy

The five remaining Batch 1 items, specified to the level a vendor can fill. Sized against the
vehicle actually delivered: **stock ECU rated 20 A, a 10 A device in its supply, motor driver
limiting at 30 A.** Prices are rough Korean street estimates (**basis E**) — the budget is
₩225,000/set against these five, and the list below comes to roughly ₩200,000.

#### #7 — Relay MUX (~₩34,000)

Switches both motor circuits between the stock ECU and the motor driver. **De-energized = STOCK**
([safety.md §1](../design/safety.md#1-authority-arbitration-who-is-allowed-to-drive-the-motors)).

**Both conductors of each motor circuit must break.** Switching only the positive side leaves the
stock ECU's output tied to the driver's output through the motor winding. That is four poles:
two for throttle, two for steering.

| Qty | Part | Note |
|---:|---|---|
| 4 | **Automotive power relay, SPDT (1C), 12 V coil, 80 A, 5-pin** + matching socket | **One part for all four poles.** Sold as relay-plus-socket sets, often waterproof |

The design says "2× DPDT". **Use 4× SPDT instead** — a 30 A DPDT is hard to source in Korea, while
automotive SPDT relays with sockets are commodity parts. Four poles either way, and each is
separately replaceable.

> [!TIP]
> **Use the same 80 A relay for all four poles — and for the [#8](#7-8-11-12-14-what-to-actually-buy) E-stop as well**
>
> An earlier revision split this: 80 A for the throttle poles, 40 A for the steering poles, and a
> separate SPST-NO part for the E-stop. **Three part numbers, three sockets, three spares.**
>
> The steering poles only need a few amps, so 80 A there is over-specified — but a 5-pin SPDT
> wired `30→87` behaves exactly as SPST-NO, so **one part covers all five positions in the
> build**: four MUX poles plus the E-stop contactor. One socket type, one spare, one bracket
> footprint, one thing for a student to identify. In a three-vehicle build that is worth more than
> the few thousand won saved by under-specifying two of the poles.
>
> Leave `87a` unconnected on the E-stop relay.

> [!WARNING]
> **Relay current ratings are for RESISTIVE loads. Motors are inductive.**
>
> Datasheets in this class state e.g. *"Rated Load (Resistive Load): 13.5 VDC 80 A."* A DC motor
> is inductive and sustains the arc on break, so the usable figure is roughly **50–60 % of the
> resistive rating**:
>
> | Relay | resistive | usable, inductive | vs the 30 A drive branch |
> |---|---:|---:|---|
> | 40 A | 40 A | **20–24 A** | **insufficient** |
> | 80 A | 80 A | 40–48 A | 1.3–1.6× — adequate |
>
> This matters because the MUX does **not** only switch a parked vehicle. A brownout or an E-stop
> drops the coils **while the motors are running**, so these contacts break motor current under
> load by design ([failsafe rows 4 and 5](../design/safety.md#2-failsafe-matrix)).
>
> *Corrected 2026-10-01: this table previously specified 40 A for all four poles.*
| 1 | **`IRLZ44NPBF`** (Infineon, TO-220AB) — logic-level N-MOSFET | **Verified 2026-10-01.** Vgs(th) 1.0–2.0 V, Vds 55 V, Id 47 A. Four coils ≈ 600 mA total, so it dissipates under 0.1 W and needs no heatsink. **The TO-220 tab is the DRAIN** — do not bolt it to a grounded plate without an insulator. Buy spares; they cost little and are static-sensitive |
| 1 | 10 kΩ resistor, ¼ W — **gate to GND** | The pulldown |
| 1 | 100 Ω resistor, ¼ W — **Teensy pin to gate, in series** | Limits the current into the gate capacitance on each switching edge, protecting the Teensy pin |
| 4 | **1N4007** flyback diode, one across each coil | **Required even on coils that already carry a parallel resistor** — see below |
| 1 | **Perfboard (만능기판), soldered** | **Not a solderless breadboard** — see the warning below |
| — | **Hookup wire, 22–24 AWG**, two or three colours | Board-level wiring. The 1.5 mm² silicone of [#12](#7-8-11-12-14-what-to-actually-buy) is power cable and will not route on a board |
| 2–3 | **Screw terminal block, 2–3 way, 5 mm pitch** | Where the off-board wires land: Teensy gate line, 12 V, GND, four coil pairs. Lets a harness be unplugged without desoldering, and takes wire movement off the solder joints |
| 1 | Small enclosure | Can be printed off [#14](#7-8-11-12-14-what-to-actually-buy) |

> [!WARNING]
> **Build this on soldered perfboard. A solderless breadboard is not a prototyping shortcut here — it is a failure mode.**
>
> Breadboard contacts are spring clips. **This board goes on a vehicle that vibrates**, and the
> circuit it carries is part of the authority chain:
>
> - **The 10 kΩ pulldown is what makes de-energize-to-safe work.** An intermittent contact on that
>   leg leaves the MOSFET gate floating, and a floating gate can partially enhance — relays
>   chattering between STOCK and DBW while the vehicle is moving.
> - **600 mA through breadboard rails** is at the limit of what those clips are good for, and their
>   contact resistance is both high and unpredictable.
>
> A breadboard is genuinely useful at **[Stage 0](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first)**, on the bench, to prove the driver switches from a
> 3.3 V pin before anything is soldered. It does not then go on the vehicle.

**Feed the coils from the logic rail**, so a logic brownout drops them to STOCK (failsafe row 4).
The **10 kΩ pulldown is safety-critical**: it holds the gate low — relays de-energized, STOCK —
whenever the Teensy is unpowered, in reset, or has not yet configured the pin as an output. A
floating gate can partially enhance.

> [!WARNING]
> **`IRF520` is not `IRL520`, and the Teensy drives at 3.3 V**
>
> The common Arduino "MOSFET module" is built around an **`IRF520`**, whose Vgs(th) is **2.0–4.0 V**
> and whose on-resistance is specified at **Vgs = 10 V**. At 3.3 V a high-threshold sample may not
> turn on **at all**, and a low-threshold one sits in the linear region making heat instead of
> switching.
>
> The logic-level part is **`IRL520`** — one letter — or **`IRLZ44N`**, Vgs(th) 1.0–2.0 V. A
> pre-built module is fine *provided* it states **logic-level** or **3.3 V compatible**; most do
> not, because they were designed for 5 V Arduinos where an IRF part is merely marginal rather
> than dead.

> [!WARNING]
> **A parallel resistor across the coil is not a flyback diode. Fit the 1N4007 anyway.**
>
> Relays in this family ship with a **680 Ω resistor** across the coil, and it is tempting to read
> that as the clamp already being there. It is not. When the MOSFET turns off, the coil's 150 mA
> has to keep flowing, and the resistor is the only path:
>
> | clamp | voltage the MOSFET sees |
> |---|---:|
> | 680 Ω resistor alone | **0.150 A × 680 Ω = 102 V** |
> | 1N4007 flyback | 12 + 0.7 ≈ **12.7 V** |
>
> A logic-level MOSFET in this class is rated **55 V** drain-source. 102 V is **nearly twice
> that.** The resistor damps ringing; it does not clamp. **One ₩100 diode per coil.**
>
> *(If a variant ships with a built-in **diode** rather than a resistor, then the clamp is real —
> but coil polarity on 85/86 becomes mandatory, and reversing it shorts the drive.)*

> [!CAUTION]
> **A 40 A socket may not fit an 80 A relay**
>
> Relays at 80 A commonly use **wider power blades** on 30/87 — 9.5 mm against the standard
> 6.3 mm — because 80 A through a quarter-inch blade is a lot. The coil terminals stay 6.3 mm, so
> a 40 A pigtail socket will take the coil pins and **not** the power pins.
>
> **Buy the socket that matches each relay**, not one socket type for all four poles. Check the
> blade width on the 80 A part before ordering its socket.

#### #8 — E-stop + contactor (~₩40,000)

| Qty | Part | Note |
|---:|---|---|
| 1 | **22 mm latching mushroom with 2a2b contacts** — 한국미스미 **`MRE-RR2R`** | **Verified 2026-10-01.** Decodes as `R` protruding Ø22 / `R` push-lock turn-reset / **`2` = 2a2b** / `R` red. The two **b접점 (NC)** are the ones that matter; the two a접점 go unused. Snap-action, IP65, screw terminals.

> `2a2b` arrives as **two stacked `1a1b` blocks**, not one block with four contacts — so the two NC you need sit on **different blocks**, one each. Identify them by the terminal marking before wiring; taking both circuits off one block gets you one NC and one NO, and the NO half of the E-stop would then do nothing until pressed and nothing at all if its wiring failed. |
| 1 | **The same 80 A SPDT relay as [#7](#7-8-11-12-14-what-to-actually-buy)**, wired `30→87`, `87a` unused | A dedicated SPST-NO part (e.g. Foocle `FLS820-012-1A`) also works, but standardising on one relay across the build is worth more than the saving |
| 1 | **1N4007 across the contactor coil** | Arc suppression, so the E-stop contact is not eroded by breaking an inductive DC load. It delays drop-out by tens of ms, which is centimetres at walking pace |

> [!IMPORTANT]
> **Three things decide this part, and the amp figure is the least of them**
>
> **1 — "연속정격 / continuous duty", not "단속정격 / intermittent".** A starter solenoid looks
> identical, costs half, and is rated for *seconds* of conduction. MRider energizes this coil for
> the whole session. An intermittent part will cook. This single keyword matters more than the
> current rating.
>
> **2 — DC-rated.** An AC-rated switch breaking DC can weld its contacts closed, and the failure
> is **silent until the button is pressed.** Continuous-duty automotive solenoids are inherently
> DC parts, which is why this class is the right one.
>
> **3 — coil current, because it cascades.** Reference parts (White-Rodgers, Trombetta class) draw
> **~500 mA** at 12 V. That is the figure the E-stop's NC block has to break — **check the block's
> DC rating, not its AC rating**, which is the same trap one level down.
>
> **A power relay beats the solenoid class here, on the one spec that cascades.** `FLS820-012-1A`
> (80 A, 12 V) has an **80 Ω coil → 150 mA at 1.8 W**, against roughly **500 mA** for a
> continuous-duty solenoid of the same contact rating. That is the figure the E-stop's NC block
> has to break and the figure the logic battery carries, so a third of it is a real win. Release
> time **≤ 5 ms**, and **AgSnO₂In** contacts, which is the material used precisely because it
> resists DC arc welding.
>
> **1.8 W is also what settles the duty question.** Starter solenoids are intermittent-rated
> because their pull-in coils dissipate tens of watts. A 1.8 W coil can hold indefinitely, which
> is what MRider asks of it.
>
> **Check three things on any listing in this class:**
>
> - **That the coil is 12 V.** This family ships 12 V and 24 V in the same shell, and the Korean
>   titles carry the voltage — `KKA-B4 릴레이 **24V** 40A 4핀`. The 24 V coil is **320 Ω with a
>   16 V pick-up**, so on this vehicle's rail it simply will not pull in. The 12 V coil is 80 Ω,
>   pick-up ≤ 8 V.
> - **That you are ordering the 12 V / 80 A variant.** These listings routinely carry several in
>   one title — *"24V 100A 12V … SPDT 80A"* — and the title is not the order. This project has
>   already been bitten twice by trusting a listing title over its specification table: the
>   Sabertooth 2x25/2x32 SKU and the FS-iA6/iA6B bundle. **Read the option you select, not the
>   headline.**
> - **Do not expect the listing to tell you the contact rating.** See the box below: on the part
>   actually evaluated, neither the title nor the description was trustworthy. Design so it does
>   not matter.
> - **Coil current.** Four coils run off one MOSFET and off the logic battery. 150 mA each is
>   600 mA; 250 mA each is 1 A, which starts to matter on a 7 Ah rail that must outlast a session.
>
> **Also check:**
>
> - **Contact form.** `-1A` is SPST-NO — correct for the E-stop, where de-energized must mean
>   open. `-1C` is SPDT, which is what [#7](#7-8-11-12-14-what-to-actually-buy) wants instead.
> - **Whether the coil has a built-in diode or resistor across it.** Some variants in this family
>   ship with a 680 Ω parallel resistor; if yours has a **diode**, coil polarity on pins 85/86
>   matters and reversing it shorts the drive. A built-in diode also means the separate 1N4007
>   is redundant.
>
> [!CAUTION]
> **On the parts evaluated here, the contact rating could not be established from the listing — so stop needing it**
>
> `KKA-B4 / TYE-RL082` (디바이스마트, ₩12,100 incl. socket) is **titled 80 A** and **described as
> "NO : 40A 14V / NC : 30A 14V / 1a1b1c"**. Those disagree, and the description is not
> per-variant — the **4-pin** listing in the same family carries that line **verbatim**, including
> an NC rating and a `1c` form on a part that physically has **no NC contact**.
>
> Comparing three listings in the family says where it came from:
>
> | listing | title | shared description | agree? |
> |---|---|---|---|
> | 80 A, 5-pin | 80 A | NO 40 / NC 30 | no |
> | 80 A, 4-pin | 80 A | NO 40 / NC 30 | no |
> | **40 A, 4-pin** | **40 A** | NO 40 / NC 30 | **yes** |
>
> The boilerplate matches the **40 A** sibling exactly, so the likeliest reading is that it was
> written for that part and copied onto the 80 A listings — making the 80 A titles probably
> correct. The `FLS820` datasheet for the same form factor, from another brand, independently
> states `MAX Operating Current 80A` and `Rated Load 13.5VDC 80A`.
>
> **It still cannot be confirmed per-variant from any listing**, which is the point: design so it
> does not have to be.
>
> Chasing it is the wrong move. **Constrain the system instead**, so any rating in this class is
> sufficient:
>
> | | |
> |---|---|
> | **Drive-channel current limit** | **20 A** |
> | Main traction fuse | **25 A** |
> | Worst case the contacts break | even the pessimistic 40 A NO reading gives 20–24 A inductive |
>
> **20 A is already twice what the whole stock vehicle runs on** — its own inline device is 10 A,
> for the same motors doing the same job. And the current these contacts actually break in service
> is the **driving** current, 5–15 A at walking pace: a failsafe revert happens while moving, not
> while stalled.
>
> Where the limit is set depends on what the board exposes — a driver-side setting if it has one,
> otherwise firmware throttle shaping plus the fuse. **Check this when the boards arrive**; it is
> not yet known whether the selected driver offers an adjustable limit.
>
> With that in place the 80 A question never has to be answered.
>
> **Buy two part numbers, not one, and let the roles be physically distinct:**
>
> | position | part | why |
> |---|---|---|
> | 4× MUX poles | **5-pin SPDT** | The MUX needs a changeover: NC → stock ECU, NO → driver. A 4-pin SPST cannot make the NC path |
> | 1× E-stop contactor | **4-pin SPST-NO, 40 A** — `TYE-RL076` (12 V 40 A 4핀) | Only ever uses `30→87`, and **the inductive derate does not apply here** — see below |
>
> This reverses an earlier preference for a single part number, and there are two reasons, both
> better than price.
>
> **A 4-pin relay physically will not seat in a 5-pin MUX position**, so the one relay with a
> different job cannot be swapped into the wrong place by a student rebuilding a harness.
>
> **And the two positions break different kinds of current.** The MUX poles sit **in series with
> the motor leads**, so they break an inductive load and take the 50–60 % derate — which is why
> they need the 80 A part. The E-stop contactor sits in the **B+ supply to the driver**, upstream
> of the H-bridge: the motor's stored magnetic energy is on the *other* side of the bridge and
> never reaches this contact, while the driver's input capacitance works against the arc rather
> than feeding it. That break is essentially resistive, so a **40 A contact against a 20 A limit
> is a straight 2×**, not a marginal one.

> **If the seller ships "one of two models at random"** — which this listing does, at 26×26×38 or
> 28×28×42 mm — **mount to the socket, not to the relay body.** The pin pattern is the ISO
> automotive standard and is common to both; only the shell differs. Buying the matching socket
> makes the random dimension irrelevant, which matters when three vehicles must end up alike.
>
> **Feed the contactor coil from the traction pack, not the logic rail.** The designed safe state
> on a logic brownout is *the factory-controlled vehicle*, not a dead one
> ([failsafe row 4](../design/safety.md#2-failsafe-matrix) reverts to STOCK, with traction still
> available to the stock ECU). Coil from the pack gives exactly that, and keeps 500 mA off a 7 Ah
> logic battery that is already carrying four relay coils.

> [!IMPORTANT]
> **NC, never NO — and two of them**
>
> **Do not order the `1` contact option** (`1a1b`) — it carries only **one** NC, and this design
> needs two independent ones. In the `MRE` series that is the third character: `MRE-RR**2**R`.
>
> **And `MRF` is not `MRE`.** Same manufacturer, adjacent catalogue pages, one letter apart:
>
> | | series | latching option |
> |---|---|---|
> | **`MRE`** | **비상정지 스위치** — mushroom | **`R` 푸시 록 턴 리셋** |
> | `MRF` | 푸시버튼 스위치 — flush/extended cap | `A` 유지동작 (Alternate) |
>
> An `MRF` part can be ordered with the right `2a2b` contacts and still be unusable here, because
> the other two attributes are both safety-relevant:
>
> - **The actuator is not a mushroom.** An E-stop must be strikeable with a palm, without aiming,
>   by someone who is not looking at it. A flush cap needs a fingertip placed on it.
> - **`Alternate` is not `push-lock turn-reset`.** Alternate releases on a *second press* — the
>   same careless motion that triggered it. The contactor coil runs straight through this contact,
>   so a second bump **re-energizes traction with no deliberate act**. That is the same hazard
>   class as the vehicle's auto-resetting thermal breaker, which this design already refuses to
>   inherit. Turn-reset requires a different motion on purpose.
>
> [!CAUTION]
> **The actuator must be RED, on a YELLOW background. This is not cosmetic.**
>
> `ISO 13850` requires the emergency-stop actuator to be **red**, with the surface immediately
> around it **yellow**. Catalogue codes carry the colour as a trailing letter and the correct type
> is available in the wrong colour — e.g. `KGE-H4R2**G**` is a conforming Ø22 push-lock turn-reset
> with 2a2b contacts, and **green**.
>
> **Green means start.** Thirteen students will operate three vehicles, and under stress a person
> reaches for the colour, not the shape. A green mushroom is the one control that could be pressed
> *expecting* motion. Order the `…R` variant.
>
> The yellow half costs nothing here: **print the E-stop's mounting plate in yellow PETG** off
> [#14](#7-8-11-12-14-what-to-actually-buy), which is already in the BOM for the enclosures.

> **Do not trade this part's correctness for lead time.** The E-stop is not needed until
> [Stage 3](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first), which is two stages
> after anything is first powered — so a two-week ship date costs nothing here.
>
> **Decided 2026-10-01 — `MRE-RR2R`, 한국미스미.** Three candidates were evaluated and the two
> faster ones each failed on a different attribute, which is why all three are recorded:
>
> | part | ships | verdict |
> |---|---|---|
> | **`MRE-RR2R`** 한영넉스 | 10/16 | **chosen** — Ø22, push-lock turn-reset, 2a2b, red, IP65, snap-action |
> | `MRF-AA2R` 한영넉스 | next day | rejected — **pushbutton, not E-stop**: flush Ø30 cap, and `Alternate` releases on a second press |
> | `KGE-H4R2G` KGE Auto | next day | rejected — correct device, **green**. Its red variant ships 10/23, later than the choice |
>
> The fastest option was wrong, and the correct-but-green option's red variant was slower than
> simply ordering the right part first.
>
> **Why NC (b접점).** An emergency stop must **open** a circuit that is closed in normal operation,
> so that a cut wire, a loose terminal, or a corroded contact **stops the vehicle** rather than
> silently disabling the stop. Wired through an **NO** contact, the E-stop does nothing at all
> until pressed — and nothing when its wiring fails, with no indication. This is why every
> industrial E-stop uses NC contacts, and it rules out the hobby "mushroom switch" parts sold with
> a single NO contact for signalling a microcontroller input.
>
> **An AC-only contact rating is acceptable on this button — and the reason is not "the current is
> small".** Blocks in this class are rated e.g. *6 A 250 V a.c.* with no DC figure at all, which
> elsewhere in this document is a red flag. Here it is not, for two specific reasons:
>
> - **A sustained DC arc needs roughly 12–14 V across silver contacts.** The AC/DC derating that
>   wrecks switches is driven by *voltage*, not current — it is why a 250 V AC block collapses to
>   a fraction of an amp at 30 V DC and to almost nothing at 110 V DC. At **12 V** the supply is
>   at or below the threshold that keeps an arc alive, so the arc self-extinguishes.
> - **Both loads are diode-clamped.** The contactor coil carries its own 1N4007 and each MUX relay
>   coil carries one, so neither circuit can push the contact voltage above the rail during break.
>
> Combined with ~150 mA and ~600 mA, this is a benign duty. **The derating that governs the
> contactor does not reach the button, because the button was kept out of the traction path** —
> which is the entire reason for the contactor pattern.
>
> **Why two.** The button has to do **two things**, and they sit on **two different power rails**,
> so no single contact can reach both.
>
> ```
>  traction pack ──[ NC #1 ]── contactor coil ───▶  traction power cut
>  logic rail ────[ NC #2 ]── MOSFET ── 4× MUX coil ──▶  authority reverts to STOCK
> ```
>
> **The first reason is that the E-stop does not cut the logic rail — deliberately.**
> [safety.md §4](../design/safety.md) pins it: *"E-stop cuts traction power **only**."* The Teensy
> stays alive so it keeps reporting state and the operator can still see what the vehicle thinks.
> But the MUX coils are fed from that same surviving rail, so **they stay energized through an
> E-stop** unless something breaks them separately. Cutting traction alone would stop the vehicle
> and leave it latched in DBW — and on reset it would come back in DBW rather than STOCK.
>
> **The second reason is a failure the first does not cover.** The coil driver's credible failure
> is a **MOSFET shorted on**: relays stuck energized, stuck in DBW. No firmware can fix that,
> because firmware is upstream of the short. Breaking the **coil supply** with its own contact
> overrides it in hardware.
>
> A `2a2b` block set gives the two **b접점** this needs; the two **a접점** are spare. One optional
> use for them: feed an E-stop-pressed signal to a Teensy input, so `DbwStatus` can report the
> button's state rather than the operator inferring it. That is a convenience, not a safety layer —
> the safety is entirely in the two NC contacts.
>
> Buy the button only after the contactor: the contactor's coil current sets the block rating.

#### #11 — Isolated logic rail (~₩47,000)

| Qty | Part | Note |
|---:|---|---|
| 1 | **SantaLi `SLB1206`, 12.8 V 6 Ah LiFePO₄** ([디바이스마트 16071444](https://www.devicemart.co.kr/goods/view?no=16071444)) | **Verified 2026-10-02.** 10.0–14.6 V range, **740 g** against the SLA's 2 500 g, IP54, F2 spades *and* a 5.5-2.1 barrel jack. BMS integral: **OCP 60 A, UVD 9.2 V, charge cut-off 15.0 V** |
| 1 | **SantaLi `SLC 1202`**, 14.6 V 2 A ([디바이스마트 16071454](https://www.devicemart.co.kr/goods/view?no=16071454)) | **Sold separately. Chosen 2026-10-02 over the 4 A `SLC 1204`** — the manufacturer's own matrix pairs `1202` with **SLB 12 V 6–12 Ah** and `1204` with **12–18 Ah**, so the 6 Ah pack sits below the `1204`'s range. Φ5.5-2.1 plugs straight into the pack's jack |
| 2 | **DC-DC buck, 12 V → 5 V, fixed output, 1–2 A** | One for Teensy + sensors, one for RC receiver + signal MUX. Separating them keeps servo-side transients off the rail holding the safety supervisor. **Fixed, not adjustable** — see below |
| 2 | **1000 µF electrolytic, 25 V**, 105 °C | Hold-up, per [safety.md §5](../design/safety.md#5-power-rail-isolation-and-brownout-protection). **25 V, not 16 V** — see below |
| 2 | Resistors for a divider into a Teensy analog pin | The logic-rail **undervoltage monitor** of failsafe row 4. **Required** — "two resistors, not a module" means skip the *module*, not the monitor |
| 1 | Blade fuse holder + **5 A** fuse | |

**A non-isolated buck is adequate.** The isolation that matters — traction from logic — is provided
by the separate battery. Galvanic isolation downstream of it buys nothing here.

**Current capability is not the spec to shop on.** Each 5 V rail carries roughly **120 mA**, so a
1 A module is already eight times the load. Two other properties matter far more.

> [!WARNING]
> **Buy a *buck*, fixed at 5 V. Not a buck-boost, and not adjustable.**
>
> Korean listings for these modules are usually **`승압/강하 … 가변`** — boost *and* buck, trimmer
> adjustable. A common example pairs an `LM2577` boost with an `LM2596` buck. **That is the wrong
> part twice over.**
>
> **Fixed, not adjustable (가변).** A trimmer can be knocked in a harness, drift, or be set wrong
> once. This rail feeds the Teensy's **3.6–5.5 V** input and the board holding the entire safety
> supervisor.
>
> **Buck only (강압), not buck-boost (승압/강하).** A buck's output is `Vin × duty`, so it is
> **physically incapable of exceeding its input** — a failed buck tops out at the rail, 12.8–14.6 V.
> A boost stage has no such bound and can produce 30 V+. Both figures kill a Teensy, but one is
> bounded by the battery and the other is not, and the bound is free.
>
> **A 5 V RC UBEC is the easiest part that satisfies both.** It is a fixed-output buck built to run
> receivers off a battery pack — which is literally one of the two loads here — 5 V out, 3 A. If it
> carries a 5 V / 6 V jumper, confirm it is on **5 V**: a jumper is far harder to disturb than a
> trimmer, but it is still a setting.
>
> **Check its INPUT rating against the charging voltage, not against the nominal 12.8 V.** This is
> the one place the LiFePO₄ pack bites: the rail sits at 12.8 V in use but reaches **14.6 V while
> charging**, and the BMS does not cut until **15.0 V**.
>
> | | input | % of a 16 V part | headroom |
> |---|---:|---:|---:|
> | pack nominal | 12.8 V | 80 % | 3.2 V |
> | **charging** | **14.6 V** | **91 %** | 1.4 V |
> | BMS cut-off | 15.0 V | 94 % | 1.0 V |
>
> **Chosen 2026-10-02: the 7–40 V UBEC** ([디바이스마트 1078321](https://www.devicemart.co.kr/goods/view?no=1078321), 5 V 3 A continuous), over
> Adafruit's `ada-1385`. Both are correct-topology fixed 5 V 3 A buck UBECs; they differ only in
> input rating, and that is where the pack bites:
>
> | | `ada-1385` (6–16 V) | 1078321 (7–40 V) |
> |---|---:|---:|
> | pack nominal 12.8 V | 80 % of rating | 32 % |
> | **charging 14.6 V** | **91 %** | 37 % |
> | BMS cut-off 15.0 V | 94 % | 38 % |
>
> The `ada-1385` is inside spec at every point and would work. The 7–40 V part simply deletes the
> question, costs no more, and needs no "disconnect while charging" caveat. Its 7 V lower bound is
> never approached either — the BMS cuts at 9.2 V and the firmware reverts at 11.5 V.
>
> It also survives a change of chassis class without being re-selected, which is the same reason
> [§1.2.4 keeps voltages out of the build pages](#7-8-11-12-14-what-to-actually-buy).
>
> **Confirm its 5 V output is fixed** — some UBECs carry a 5 V / 6 V jumper.
>
> **The same input-rating question applies to the hold-up capacitors, and this page got it wrong
> once.** It originally said *"1000 µF 16 V"*, which is the identical **91 % at 14.6 V** figure that
> disqualified the `ada-1385`.
>
> | | 16 V part | 25 V part |
> |---|---:|---:|
> | pack nominal 12.8 V | 80 % | 51 % |
> | charging 14.6 V | **91 %** | 58 % |
>
> **Put the hold-up on the 12 V rail, at the UBEC inputs, and use 25 V parts.** The 12 V side is
> where the capacitance does more: 1000 µF from 12.8 V down to the UBEC's 7 V floor is about
> **95 ms** of ride-through for the logic load, against roughly 3 ms if the same part sits on the
> 5 V output.
>
> A 16 V part is not *wrong* — at 105 °C rated and room-temperature ambient its life is long, and
> 14.6 V only appears while charging. But 25 V costs the same, and **16 V would be usable only on
> the 5 V side**, where it buys far less hold-up.
>
> If only an adjustable buck is available, set it, **seal the trimmer**, and record the measured
> voltage.

> [!CAUTION]
> **Cut the Teensy's `VUSB`–`VIN` pads before powering it from this rail**
>
> On a Teensy 4.1, `VUSB` and `VIN` are **joined by default**, so external power on `VIN` with a
> USB cable attached shorts two supplies together and **back-feeds the laptop's USB port**. PJRC
> provides a pair of pads on the underside to be cut apart for exactly this case.
>
> This is not optional on MRider: the Teensy sits on the logic rail *and* keeps a permanent USB
> link to the laptop, because that link carries both command and feedback
> ([failsafe row 2](../design/safety.md#2-failsafe-matrix)). **Every one of the three boards needs
> the cut**, and it has to happen before the first time external power and USB are present
> together — which is [Stage 0](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first).
>
> The damage lands on a **student's own laptop**, which is the kind of mistake this project cannot
> make thirteen times.

> [!WARNING]
> **The 12 V 7 Ah SLA is the wrong part — oversized by 3× and heavy enough to matter**
>
> Measured against the actual load rather than a guess:
>
> | | |
> |---|---:|
> | 4× MUX relay coils (150 mA each) | **600 mA** |
> | Teensy, angle sensor, RC receiver, signal MUX, driver logic — 240 mA at 5 V through an 85 % buck | 118 mA |
> | **Total at 12 V** | **≈ 720 mA, 8.6 W** |
>
> The relay coils are **84 %** of it, and they are irreducible: a latching relay would cut the
> draw and is forbidden here, because de-energize-to-safe requires a relay that drops out when
> its coil loses power.
>
> | Pack | usable | runtime | mass |
> |---|---:|---:|---:|
> | 12 V 7 Ah SLA (50 % DoD) | 3.5 Ah | 4.9 h | **2500 g** |
> | 4S LiFePO₄ 2.5 Ah (80 %) | 2.0 Ah | 2.8 h | 300 g |
> | 3S Li-ion 2.6 Ah (80 %) | 2.1 Ah | 2.9 h | 180 g |
>
> **2–3 Ah covers a session.** The SLA buys runtime nobody needs and spends **2.5 kg** doing it —
> against a [C1 kit budget](../design/vehicle.md) of ~6 kg total, of which the control box,
> battery and wiring share 3–4 kg. The logic battery alone would take most of that bucket, and
> `vehicle.md` names **centre of mass** rather than mass as the real tip-over risk: a 2.5 kg brick
> on the deck is the worst single item to place.
>
> **The rail tolerates a wide window**, so chemistry is a free choice: the bucks accept a range and
> the relays pick up at **≤ 8 V**. Anything delivering roughly **9.5–14 V** works.
>
> **Prefer LiFePO₄ over LiPo, and the reason is the course, not the physics.** A 4S LiFePO₄ pack
> is **12.8 V nominal** — a near-exact 12 V replacement with a flat discharge curve, which is what
> you want under a rail feeding the safety supervisor — and its chemistry does not enter thermal
> runaway the way LiPo does. Thirteen students will charge, store, knock and eventually puncture
> these over a semester. A 3S Li-ion pack **with an integrated BMS** is the acceptable second
> choice. **Bare LiPo is not**, whatever the drone hobby does with it.
>
> **Changing chemistry moves one firmware constant**: the logic-rail undervoltage threshold of
> [failsafe row 4](../design/safety.md#2-failsafe-matrix).
>
> **Set it to 11.5 V for the `SLB1206`.** The reasoning, so it can be re-derived for another pack:
> a 4S LiFePO₄ sits flat near 13.0 V for most of its discharge and then falls quickly, and this
> pack's **BMS cuts at 9.2 V**. The firmware threshold has to sit *above* the BMS cut-off, so the
> Teensy sees the rail failing and reverts to STOCK **deliberately**, rather than having the BMS
> remove power from the safety supervisor without warning. 11.5 V is below the flat region — no
> false trips — and leaves enough energy above 9.2 V to execute the revert.
>
> **The protections are then ordered correctly**: the 5 A fuse blows first, the firmware monitor
> trips next, and the BMS's 60 A OCP / 9.2 V UVD is the last resort that should never be reached.
>
> **Why the 2 A charger and not the 4 A.** Both are inside the pack's recommended 2–4 A, so the
> decision is not about whether 4 A would work. The manufacturer assigns `1202` to this pack size
> and `1204` to the next one up, and deviating from a vendor's own pairing needs a reason better
> than *faster*. There isn't one here: **3 hours against 1.5 is invisible** when the packs charge
> between weekly sessions and run 6.7 hours on a charge. And **0.33 C is gentler than 0.67 C** on
> cells that three cohorts will share.
>
> **Do not operate the vehicle while charging.** At 14.6 V the rail is inside the relay coils'
> rating at room temperature (20.2 V) but close to their **15.7 V limit at 85 °C**.

#### #12 — Wiring, connectors, fuses (~₩55,000)

| Item | Spec |
|---|---|
| **Traction wire** | **AWG 14** (≈2.1 mm²) silicone, **red + black**. AWG 12 for margin. *Corrected 2026-10-02 — see below; 1.5 mm² was sized on voltage drop alone* |
| **Logic wire** | **AWG 18–20** (≈0.5–0.8 mm²) silicone, **red + black** |
| **Signal / board wire** | **AWG 22–24**, two or three colours — **anything but red or black** |

> [!NOTE]
> **Red and black on both power rails — and what they do *not* mean on a motor lead**
>
> Both packs get **red = +, black = −**. Keeping one polarity convention everywhere matters more
> than distinguishing the two rails by colour, because **reversed polarity kills a board while a
> crossed rail merely loses isolation** — and the two rails are already told apart by gauge, AWG 14
> against AWG 18–20.
>
> **Motor leads are the exception, and the steering one bites.** A driver output is a bidirectional
> H-bridge: its two conductors are not `+` and `−`, they are **A and B**, and swapping them
> **reverses the motor**. Red/black is fine as an A/B label, but it carries no polarity meaning
> there, and [§3.3](03-electrical.md) already warns that *"a reversed steering tap means the
> position loop runs away from its setpoint instead of toward it."*
>
> **Record which conductor went where, per vehicle.** Three cars wired from the same spool can
> still end up with two turning left and one turning right.
>
> Keep red and black off the signal wiring entirely, so nothing that carries 12 V is ever confused
> with something that carries 3.3 V.
| **Fuses** | **25 A ×1 and 5 A ×1 per vehicle** — blade (ATC/ATO). Six fitted across the three vehicles. Two per vehicle, one at each battery; the branches are not separately fused ([§3.2](03-electrical.md)). Buy an **assorted ATC kit** for spares — fuses are consumables and a blown one with no replacement stops a lab |
| **Fuse holders** | **2 per vehicle** — *one* 12–14 AWG for the 25 A, *one* 18–20 AWG for the 5 A. **Six for the three vehicles: 3 + 3.** Gauge no thinner than the wire it splices into |

> [!WARNING]
> **A fuse protects the wire, so the fuse must be smaller than the wire — and 1.5 mm² failed that**
>
> This page sized the traction wire on **voltage drop** and never checked it against the fuse. Drop
> was fine; ampacity is not:
>
> Korean listings sell silicone wire by **AWG**, so both units are given here. **AWG counts down as
> the wire gets thicker.**
>
> | AWG | mm² | chassis ampacity | used for |
> |---:|---:|---:|---|
> | 12 | 3.31 | 35–41 A | traction, if you want margin |
> | **14** | **2.08** | **25–32 A** | **traction — behind the 25 A fuse** |
> | 16 | 1.31 | 18–22 A | *(what this page wrongly specified)* |
> | **18** | **0.82** | **10–16 A** | **logic — behind the 5 A fuse** |
> | **20** | **0.52** | **5–8 A** | logic, lighter runs |
> | 22–24 | 0.33–0.20 | 2–5 A | board wiring only |
>
> A **25 A** fuse on **1.5 mm²** (≈16 AWG, ~20 A) is backwards: the wire overheats before the fuse
> acts, which is the one thing a fuse exists to prevent. **2.5 mm² on the traction side** fixes it
> and keeps the 20 A driver limit and the 25 A fuse as decided. The logic side was already correct
> — 5 A against 0.5–0.75 mm².
>
> **The same rule picks the fuse holder's pigtail gauge.** A `12 AWG ATC/ATO` holder **will** take a
> 5 A fuse — the blade socket is identical for every ATC fuse, and the gauge limits the *holder*,
> not which fuse fits. It is simply over-specified there, and the problem is mechanical rather than
> electrical: **a butt splice sized for 12 AWG will not grip 0.75 mm² logic wire.** Match roughly —
> **18–20 AWG** for the 5 A holder, **12–14 AWG** for the 25 A.
>
> [!CAUTION]
> **Check that the silicone wire is copper, not CCA**
>
> Cheap silicone wire is often **copper-clad aluminium**, sold at the same AWG number. CCA carries
> roughly **61 %** of copper's conductivity, so AWG 14 CCA behaves about like AWG 16 copper — which
> is exactly the gauge this page just rejected for sitting under a 25 A fuse. Listings say
> **순동 / 무산소동 / OFC** when it is real copper, and often say nothing at all when it is not.
>
> **Avoid holders that do not state a gauge**, especially at high ratings. Cheap ones are built with
> thin wire regardless of the fuse they are sold alongside, and then the holder, not the fuse, is
> what the circuit is really limited by.
| **Battery tap** | XT60 |
| **Three taps** | Keyed inline connectors — **and deliberately three *different* connector families**, so throttle, steering, and power physically cannot be cross-plugged. A reversed steering tap makes the position loop run away from its setpoint instead of toward it |
| Terminals | Ring/spade for the driver's screw terminals |
| Signal | Dupont / JST-XH pigtails; 6× servo-style 3-wire leads; one good USB A–micro/C cable |
| Heatshrink | At least two sizes |

#### #14 — Mounts and print material (~₩38,000)

| Item | Spec |
|---|---|
| **Filament** | **PETG, 1 kg. Not PLA.** PLA softens around 60 °C — reached in a parked car or direct sun — and [sensors.md](../design/sensors.md) makes mast rigidity a calibration requirement: a mast that moves invalidates the camera↔LiDAR extrinsics |
| Inserts | M3 heat-set threaded inserts for the enclosures |
| Fasteners | M3/M4 bolts, nylon standoffs |

> [!NOTE]
> **Consider aluminium profile for the mast itself**
>
> Printed brackets are right for the LiDAR and camera mounts. The **mast** carries them at height
> and is the part whose flex shows up directly in the extrinsics. A short length of 2020 extrusion
> is stiffer than any print of the same mass, and it is cheap.

---

## 1.3 Two parts you must not order blind

Two line items depend on measurements taken on the vehicle you actually bought. Ordering
them in week 0 is the most common way to waste money on this build.

**Steering gearmotor (#4)** — sized from the *measured* column torque, with a **≥2× margin**
at rated (not stall) torque. The measurement procedure is
[dbw.md §2.2](../design/dbw.md#22-torque-measurement-procedure-before-sizing-the-gearmotor):
vehicle at full load, on the target surface, spring scale on the rim, record peak force `F`
to turn lock-to-lock while stationary, then `τ_column = F × r`.

> [!NOTE]
> **Fallback if you cannot source a suitable encoder-gearmotor**
>
> A **12 V automotive wiper motor** is the documented fallback — high stall torque
> (typically 10–30 N·m), built-in worm gearing. Two consequences you must accept and
> re-check against [safety.md](../design/safety.md):
>
> 1. The worm gear is largely **non-back-drivable**, so on power loss the steering
>    **holds** rather than freewheels. This invalidates the freewheel analysis in
>    [safety.md §4](../design/safety.md#4-steering-motor-power-rail-assignment-and-power-loss-behavior-pinned)
>    and must be re-evaluated before the vehicle touches the ground.
> 2. Wiper motors rarely have a usable shaft encoder, so the absolute column sensor
>    becomes the **sole** angle source. Acceptable — [ADR B](../design/dbw.md#5-adr-b-steering-angle-encoding)
>    already makes it authoritative.

**Absolute steering angle sensor (#5)** — the default is an **AS5600-class magnetic encoder**
mounted **load-side**: downstream of the steering gearbox, on the kingpin/road-wheel axis or
the linkage, where total travel is only ±22.5°. Load-side mounting is the point —
it measures what the road wheels actually do, so gearbox backlash appears as *measured error*
rather than invisible bias
([ADR B](../design/dbw.md#5-adr-b-steering-angle-encoding)).

> [!CAUTION]
> **Measure shaft travel before ordering — this is a hard gate**
>
> The AS5600 is **single-turn absolute (0–360°)**. If the shaft it is mounted on rotates
> more than one turn lock-to-lock, it wraps and **silently** loses absolute meaning — a
> garbage angle feeding a position loop that drives a motor. This is FMEA row 2, severity 5.
>
> **Measure every candidate mounting shaft on the vehicle you actually bought.**
>
> - Shaft travel ≤ 340° → **AS5600**. Contactless, 12-bit, no wiper wear at the small
>   high-duty-cycle oscillations a steering servo makes, no ADC noise, no ratiometric
>   reference.
> - No accessible shaft under 340° → **single-turn conductive-plastic potentiometer**, the
>   pre-registered fallback. Costs analog filtering and wiper wear, but maps monotonically
>   across whatever travel its shaft sees.
>
> Budget for either — they are within a few dollars. Record the measurement in
> [calibration.md](../design/calibration.md).
>
> The AS5600 also needs a **diametrically magnetized magnet mounted concentric** to the
> sensed shaft, with the air gap inside spec. That mechanical precision is the main reason
> the pot fallback is retained. Check for magnetic interference from the steering motor
> during bench validation.

## 1.4 Substitution notes

| Item                   | Safe to substitute? | Constraint                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                         |
| ---------------------- | ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Vehicle                | Yes, within class   | Must be **12 V, single-seat, dual rear motors, parent-remote class** ([ADR D-R](../design/vehicle.md#adr-d-r-reversal-to-the-12-v-single-seater-2026-08-08) reversed the original 24 V two-seater call), with an accessible steering column. Run the [vehicle.md §3 verification checklist](../design/vehicle.md) on whatever you buy.                                                                                                                                                                                                                                                                                         |
| Teensy 4.1             | Not recommended     | A Teensy 4.0 fits the peripheral budget, but 4.1 is $8 more for headroom.**Do not drop to an ESG32/AVR-class part** — the 600 MHz Cortex-M7's timing determinism and 4 hardware quadrature decoders are load-bearing ([dbw.md §9](../design/dbw.md#9-teensy-41-firmware-platform-and-version-pinning)).                                                                                                                                                                                                                                                                                                                     |
| Sabertooth 2x32        | Only within class   | **Do not substitute a bare H-bridge.** It is disqualified on inputs before current even matters: a BTS7960 takes PWM + DIR, so it cannot sit downstream of the [servo-pulse RC MUX](../design/dbw.md#112-hardware-rc-signal-mux-the-d3-condition), and it has no signal-loss timeout to back [failsafe rows 6 and 8](../design/safety.md#2-failsafe-matrix). A smaller *Sabertooth* is a defensible saving; a bare bridge is not. Drive-motor stall current is **unmeasured** — [measure it](../design/vehicle.md#31-drive-motor-stall-current-vs-sabertooth-rating-critical) against 32 A/channel and log the result. |
| Drive encoder          | Yes                 | Any quadrature/Hall encoder.**Record the actual PPR — do not assume 52.** The source project conflicts with itself (52 PPR in `code.ino:27` vs 16 PPR in its own BOM, finding F7). The roll-out calibration in step 6 bypasses PPR anyway.                                                                                                                                                                                                                                                                                                                                                                                |
| Camera                 | Yes for semester 1  | A $30 rolling-shutter USB camera is fine for SLAM and teleop.**Behavior cloning (phase 2) needs a global shutter** — rolling shutter smears during turns and corrupts steering labels. Budget +$150 then; do not train on rolling-shutter data and attribute the result to the platform.                                                                                                                                                                                                                                                                                                                                    |
| LiDAR                  | Yes                 | `rplidar_ros` is in apt for Humble. Swapping to YDLidar or another vendor means swapping the ROS 2 driver ([software.md §2](../design/software.md#2-ros-2-stack-reused-adapted-new)).                                                                                                                                                                                                                                                                                                                                                                                                                                            |
| RC TX/RX               | Yes                 | Must have a **serial channel stream — i-BUS or SBUS — plus a spare channel** to drive the hardware signal MUX. The FlySky FS-iA6B speaks **i-BUS, not SBUS**; either satisfies the design. No longer needs to be PX4-bindable. This is your live override authority — do not economize here.                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| Hardware RC signal MUX | Within class        | Any servo-signal multiplexer that selects between two PWM sources on an RC channel.**Do not omit** — see §1.2.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| IMU                    | Yes                 | Any 9-DoF publishing`sensor_msgs/Imu`. Onboard fusion (BNO085 class) saves work; the estimator is `robot_localization` either way.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                             |
| E-stop                 | No                  | Must be**traction-rated** (switching the actual motor current, or a contactor coil). A signal-rated mushroom button will weld.                                                                                                                                                                                                                                                                                                                                                                                                                                                                                               |

## 1.5 Connector and consumable list

Not individually itemized in the BOM (they fall under line 12, wiring/connectors/fuses), but
you need all of them before step 3:

**Traction side (12 V, high current)**

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

**Moved.** The fill-in record now lives in one place — **[Order Log](../order-log.md)** — so
there is a single source of truth for what was actually bought.

It carries the per-batch order tables, the measurement fields that gate the three
measure-first parts (#4 gearmotor, #5 angle sensor, #13 coupler), a substitution log, and the
final reconciliation. A second copy of the same table here would only drift out of step with
it.

Record actuals as parts arrive: your totals will not match the estimates, and the next person
to build one needs your real numbers, not these.

When ordering is complete, store the filled log as `config/calibration/bom_asbuilt.md`,
stamped with date and operator per
[calibration.md §7](../design/calibration.md#7-calibration-artifact-index).

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

**Next:** [2. Vehicle prep &amp; mechanical](02-mechanical.md)
