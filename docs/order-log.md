# Order Log

**A working record, meant to be edited.** Fill it in as you place orders and as parts arrive.
Unlike the [BOM](design/bom.md), which is a *specification*, this page is the *history* of
what was actually bought, from whom, for how much, and what was substituted.

Keep it honest even when it is unflattering — a substitution that seemed harmless and later
caused a rebuild is exactly the entry the next person needs.

- **What to buy and why:** [design/bom.md](design/bom.md) — the specification
- **Where to buy it, and what to verify:** [build/01 §1.2.1](build/01-bom-sourcing.md#121-sourcing-in-korea-verified-2026-09-15) — vendors, prices, the date each was read
- **What was approved:** [Purchase Request](purchase-request-2026-fall.md) — **frozen** at 2026-09-28; divergences are in its [Amendments](purchase-request-2026-fall.md#amendments-since-approval) section
- **This page:** what was **actually ordered, paid and received.** The live record — edit it freely

> [!IMPORTANT]
> **Which document changes, and which does not**
>
> The purchase request is evidence of what the university agreed to fund. Editing its tables as
> procurement proceeds would destroy the only record of that, so it is **frozen** and every
> divergence is listed in its Amendments section instead.
>
> **This page is the opposite** — it is meant to be edited, every day if need be, and it is the
> authority for what was actually bought. When the two disagree, this page is what happened and the
> request is what was promised. The gap between them is the reconciliation, and it is the useful
> part.
>
> **Vendor links live here**, not in the request. Several have been corrected since approval — one
> pointed at a receiver rather than a transmitter-and-receiver set — and a frozen document cannot
> carry corrections.

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

Either edit the tables directly, or let the script do it — it writes the same cells and cannot
shift a column:

```bash
# ordered 3 vehicles, charged ₩687,000        (--date defaults to today)
python3 scripts/order_status.py --order 1 --paid 687000

# the boxes arrived
python3 scripts/order_status.py --arrive 1 --date 2026-10-05

# opened them, ran the Verify check, all three are good
python3 scripts/order_status.py --secure 1 --count 3
```

| When | Do this |
|---|---|
| You place an order | `--order <#> --paid <KRW>` |
| The box arrives | `--arrive <#>` |
| You have opened it and **run the check in the Verify column** | `--secure <#> --count <n>` |

It refuses to secure more units than were ordered, rejects a date that is not `YYYY-MM-DD`, and
errors on a line item that does not exist. Partial deliveries are expected — `--secure 1 --count 2`
today and `--count 3` next week is the normal path.

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
| 1 | Vehicle — 12 V single-seat ride-on | 3 | 쿠팡 | 229,000 | 2026-09-29 | 2026-09-30 | 3/3 | 687,000 | Record model + serial per unit. **Stock steering gearmotor present** — see V1 |
| 2 | Teensy 4.1 **[이더넷] DEV-16771** | 3 | 디바이스마트 | 74,250 | 2026-09-29 | 2026-10-08 | 3/3 | 222,750 | ₩67,500 ex-VAT → **₩74,250 incl**. **4.1, not 4.0** — count the pins **Secured 2026-10-08:** confirmed **4.1**, not 4.0. **The `VUSB`–`VIN` pads are still joined from the factory on all three** — cut them before Stage 0, or an externally powered board back-feeds the laptop's USB port. That is a build step, not a receiving one. |
| 3 | **Cytron SmartDriveDuo-30 (MDDS30)** — M1 steering, M2 drive *(replaces Sabertooth 2x32)* | **4** | [디바이스마트 13186549](https://www.devicemart.co.kr/goods/view?no=13186549) 해외구매 | 143,440 | 2026-09-29 | 2026-10-08 | 4/4 | 573,760 | ₩130,400 ex-VAT → **₩143,440 incl**. **4 units — 3 + 1 spare.** **`SW1:SW2=00` RC · `SW3:SW4=11` independent · `SW6=0` timeout ON** — verify SW6 on every board; `SW6=1` disables the stop **Secured 2026-10-08:** genuinely `MDDS30`, not a relabelled 2x25/2x32, and **every switch OFF as shipped** — so `SW1:SW2=00` and `SW6=0` are already right. **`SW3` and `SW4` must be turned ON** before use; that is a build step, not a receiving one. Re-confirm `SW6` board-by-board as each is fitted. |
| 7 | Relay MUX — 4× SPDT 80 A + `IRLZ44N` + passives | 3 | [디바이스마트 14822426](https://www.devicemart.co.kr/goods/view?no=14822426) · 쿠팡 | 57,300 | 2026-10-01 | 2026-10-02 | 0/3 | 171,900 | **12× 5핀 SPDT 80 A @₩12,100** (socket incl.) = 145,200. Bulk, shared across all three: [`IRLZ44N` ×5](https://www.coupang.com/vp/products/9570142606?vendorItemId=95507737241) ₩9,100 · [resistor kit 30 values ×600](https://www.coupang.com/vp/products/9515705626?vendorItemId=95313302183) ₩9,900 · [`1N4007` ×200](https://www.coupang.com/vp/products/8583456225?vendorItemId=91607125807) ₩7,700 = 26,700. **10 kΩ gate pulldown + 100 Ω series** come out of the kit. **Arrived 2026-10-02: the three Coupang bulk items only** — `IRLZ44N`, resistor kit, `1N4007`. The **12 relays + sockets from 디바이스마트 are still outstanding**, which is why this is not secured. *(A 2026-10-08 edit briefly recorded this parcel as lost and the row as nothing-in-hand. It was not lost; the entry was reverted the same day. Nothing was re-ordered and no money moved.)* On arrival check the relay **blade width** against the socket, and that the coil is **12 V, 80 Ω** | **12× 5핀 SPDT 80 A @₩12,100** (socket incl.) = 145,200. Bulk, shared across all three: [`IRLZ44N` ×5](https://www.coupang.com/vp/products/9570142606?vendorItemId=95507737241) ₩9,100 · [resistor kit 30 values ×600](https://www.coupang.com/vp/products/9515705626?vendorItemId=95313302183) ₩9,900 · [`1N4007` ×200](https://www.coupang.com/vp/products/8583456225?vendorItemId=91607125807) ₩7,700 = 26,700. **10 kΩ gate pulldown + 100 Ω series** come out of the kit. **NOTHING FROM #7 IS IN HAND.** *Corrected 2026-10-08.* This row recorded an arrival on 2026-10-02 that did not happen: the Coupang parcel — `IRLZ44N`, resistor kit, `1N4007` — was **marked delivered and never received**, ₩26,700 of it, and is being **re-ordered**. The **12 relays + sockets from 디바이스마트 are still outstanding** on their own account. **The ₩26,700 is still carried as paid once**; if the lost parcel is refunded this stays right, and if it is not, the re-order adds ₩26,700 to the projected total against ₩398,424 of headroom. Record which when it settles. On relay arrival check the **blade width** against the socket, and that the coil is **12 V, 80 Ω** 
| 80 | **#8a** E-stop contactor — 4핀 SPST-NO 40 A | 3 | [디바이스마트 14822420](https://www.devicemart.co.kr/goods/view?no=14822420) | 11,000 | 2026-10-01 | . | 0/3 | 33,000 | Bracket + socket incl. Wired `30→87`, `87a` n/a. **Spec:** [§1.2.4](build/01-bom-sourcing.md#7-8-11-12-14-what-to-actually-buy) |
| 81 | **#8b** E-stop button — 한국미스미 `MRE-RR2R` | 3 | [한국미스미 MRE-RR2R](https://kr.misumi-ec.com/vona2/detail/222005924703/?ProductCode=MRE-RR2R) | 11,924 | 2026-10-01 | . | 0/3 | 35,772 | Ø22, **푸시 록 턴 리셋**, **2a2b**, 적색, IP65, snap-action. The third code character must be **`2`** — `1` is 1a1b and carries only one NC. **Verify on arrival: the two b접점 sit on *different* stacked blocks**, one each |
| 9 | Pololu #2806 RC servo MUX | 3 | 디바이스마트 | 31,680 | 2026-09-29 | 2026-10-08 | 3/3 | 95,040 | ₩28,800 ex-VAT → **₩31,680 incl**. `FAILMODE` jumper present **Secured 2026-10-08:** `FAILMODE` jumper present. |
| 10 | RC TX/RX — FS-i6 transmitter + **FS-iA6B** receiver | 3 | [팰콘샵 100004832](https://www.falconshop.co.kr/shop/goods/goods_view.php?goodsno=100004832) KC인증 | 139,160 | 2026-09-29 | 2026-10-01 | 3/3 | 417,480 | ₩142,000 list, **₩417,480 paid for 3** (≈2% off). **Receiver confirmed iA6B on 2026-10-01** — i-BUS port present on the board, all 3 sets. **Mode 2** — see the note below |
| 110 | **#11a** Logic battery + charger | 3 | [디바이스마트 16071444](https://www.devicemart.co.kr/goods/view?no=16071444) · [16071454](https://www.devicemart.co.kr/goods/view?no=16071454) | 66,000 | 2026-10-02 | 2026-10-07 | 3/3 | 198,000 | SantaLi `SLB1206` 12.8 V 6 Ah LiFePO₄ **₩50,160** + `SLC 1202` 14.6 V 2 A **₩15,840**, both **VAT added — the listing quoted ₩45,600 / ₩14,400 ex-VAT**. 740 g; BMS integral (OCP 60 A, UVD 9.2 V). **Firmware UV threshold 11.5 V.** The maker pairs `1202` with 6–12 Ah, `1204` with 12–18 Ah **Secured 2026-10-08:** pack reads LiFePO₄ **12.8 V 6 Ah**, matching `SLB1206`. Check the charger label reads `SLC 1202` 14.6 V 2 A and say so if it does not — the 4 A `SLC 1204` was deliberately not chosen. |
| 111 | **#11b** UBEC 5 V 3 A ×2/set | 3 | [디바이스마트 1078321](https://www.devicemart.co.kr/goods/view?no=1078321) | 23,518 | 2026-10-02 | 2026-10-08 | 0/3 | 70,554 | **6 units @ ₩10,690 ex-VAT = ₩64,140 → ₩70,554 incl.** Input **7–40 V**, chosen over `ada-1385` (6–16 V), which sits at 91 % of rating while the pack charges at 14.6 V. **Confirm the 5 V output is fixed** — some UBECs carry a 5 V / 6 V jumper **The specified UBEC is what arrived** (7–40 V in, 5 V 3 A continuous, 18 g). **Its PCB is silkscreened `LM2596 DC-DC  HW-411`, and that is the regulator CHIP, not a different module** — this UBEC is built around an LM2596, as most 7–40 V ones are. *A 2026-10-08 entry read that marking as a substitution by a generic LM2596 board and recorded one; it was withdrawn the same day. Nothing was substituted and nothing else is in stock.* **Inventory: 6 UBECs**, 2 per vehicle across three and **zero spares** — the only Batch 1 line carrying none, and the one component a student sets by hand before anything downstream of it survives. Buy two spares. **Not secured until the output is measured:** the board carries a small trimmer, so confirm **5 V** on the pack alone before any Teensy is connected, re-check at 14.6 V with the charger on, lock the trimmer, and record the measured volts per unit here. Wiring: input is **bare red/black leads** needing termination at the pack; output is a **servo plug** — one goes straight into the RC receiver, the other gets adapted to the Teensy's `VIN`/`GND`. The board marks `IN+`, `OUT+`, `OUT-` and an arrow for flow direction. |
| 112 | **#11c** Hold-up + fuse — **closed, absorbed into #12** | 3 | 쿠팡 | 0 | 2026-10-02 | 2026-10-03 | 3/3 | 0 | **₩0 by construction, not by cancellation.** The 1000 µF 25 V capacitors and the 5 A fuses were bought on the #12 Coupang order and are counted there. Splitting the receipt to populate this row would make the log disagree with the invoice. Divider resistors come from the #7 kit **Secured 2026-10-08:** capacitors read **1000 µF 25 V**, which is the part the corrected spec asks for — a 16 V part sits at 91 % while the pack charges at 14.6 V. | **Capacitors arrived 2026-10-03** on the #12 shipment, as designed.
| 900 | **Shipping** — running total, not per set | 1 | — | 11,400 | 2026-10-02 | . | — | 11,400 | Battery ₩3,500 · charger ₩3,500 · UBEC ₩4,400 *(flat, any quantity)*. **#12's ₩3,000 was refunded with a cancelled line**, so that order carries none. Kept off the part rows so `paid = unit × qty` stays a meaningful check — folding carriage in would make it misfire on every shipped row and train the reader to ignore the one thing that has caught two VAT errors. **Closed 2026-10-02: the earlier 디바이스마트 orders show ₩0 carriage**, so nothing is missing from before. UBEC carriage to be re-confirmed from the final charge |
| 12 | Wiring / connectors / fuses | 3 | 쿠팡 | 63,180 | 2026-10-02 | 2026-10-07 | 3/3 | 189,540 | **AWG 14 silicone red+black 10 m each** · AWG 20 UL1007 ×2 (32 m, 4-colour) · AWG 22 UL1015 ×3 · **ATO 대형 10종 50개** · **12 AWG holder ×8 + 12 fuses** · **18 AWG holder ×3** · **1000 µF 25 V ×10** · **XT60 ×10 pairs**. ₩205,820 less a ₩15,800 discount, **less ₩480 for 12× MINI 5 A fuses cancelled 2026-10-02** — ordered in error, they are MINI size and these holders are standard. **The ₩3,000 carriage was refunded with them**, so this order carries none. **Confirm the 10종 set includes 5 A** — with the MINI pack gone there is no fallback **Secured 2026-10-08:** wire lengths and colours all sufficient, and the **ATO 10종 set contains 5 × 5 A** — which closes the open question, because the MINI pack was cancelled and there was no other way to fuse the logic rail. **Three are fitted, so two spares across three vehicles for a whole semester.** Fuses are consumables and a blown one with no replacement stops a lab: top up the 5 A separately. | **Arrived in two parts:** fuse holders, AWG 14, AWG 22, XT60 pairs and the capacitors on **2026-10-03**; AWG 20 and the ATO fuse set on **2026-10-07**. Counts match the order on both.
| 14 | Mounts / 3D-print material | 3 | 로컬 | 41,000 | . | . | 0/3 | | **Spec:** [§1.2.4](build/01-bom-sourcing.md#7-8-11-12-14-what-to-actually-buy) — **PETG, not PLA** — PLA softens at ~60 °C and mast rigidity is a calibration requirement |
| 15 | USB gamepad — Logitech F710 class | 3 | [옥션](https://itempage3.auction.co.kr/DetailView.aspx?ItemNo=E428299758) | 66,680 | 2026-09-29 | . | 0/3 | 200,040 | ₩64,000 est → **₩66,680 actual**. Xbox layout; record the map if not |
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
> **#10 — read the 구성품 table, not the product title**
>
> The transmitter is not the risk; the receiver is, and the difference is one letter.
>
> | | Outputs | Usable here? |
> |---|---|---|
> | **FS-iA6** | PWM only | **No.** No serial stream, so [Layer A](design/safety.md#12-live-override-inside-dbw-mode-two-layers) cannot be built on it |
> | **FS-iA6B** | PWM + PPM + **i-BUS** (+ s.bus per the vendor spec) | Yes |
>
> **팰콘샵 `100004832` is titled "… + iA6 6채널 수신기 포함" and ships the iA6B.** Its own
> specification table reads `Product Model: FS-iA6B`, `Data port: PWM / PPM / i.bus / s.bus`. The
> title is stale; the contents are correct — the same failure as the
> [Sabertooth listing](build/01-bom-sourcing.md#121-sourcing-in-korea-verified-2026-09-15), where a legacy SKU string sat
> above an accurate description.
>
> Two related listings that are *not* the set, and are easy to grab by mistake:
>
> - 팰콘샵 **`100004833`** — the **iA6B receiver alone**, ₩31,000, no transmitter
> - 알씨뱅크 `93882`, FirstBot — genuinely bundle the plain **iA6**
>
> **Verify on arrival regardless of what any listing said.** The iA6B has a physically separate
> **i-BUS port** beside the servo channels; the iA6 does not. Look at the board, not the box.
>
> If a wrong-receiver bundle does arrive it is recoverable — ₩31,000 for a separate iA6B, and the
> iA6 becomes a spare PWM receiver. Money, not a redesign.
>
> **Closed 2026-10-01: all three receivers are iA6B, i-BUS port present on the board.** The
> component table was right and the listing title was wrong, which is why the check was written
> against the board rather than against any listing. [Layer A](design/safety.md#12-live-override-inside-dbw-mode-two-layers)
> is buildable as designed; no contingency spend.

> [!IMPORTANT]
> **#10 — buy **Mode 2**, and drive from the right stick**
>
> Mode 1 and Mode 2 are an *aircraft* convention for which stick holds throttle. This is a car, so
> the question is really: **which stick self-centres?**
>
> | | Left stick | Right stick |
> |---|---|---|
> | **Mode 2** | throttle (V, **ratcheted**) + rudder (H) | elevator (V) + aileron (H) — **both spring-centred** |
> | Mode 1 | elevator (V) + rudder (H) | **throttle (V, ratcheted)** + aileron (H) |
>
> On the FS-i6 the throttle gimbal is **physically ratcheted** — it stays where you leave it, which
> is correct for an aircraft and wrong for this vehicle. Mode 2 puts that ratchet on the **left**
> stick, leaving the entire right stick self-centring.
>
> **So: Mode 2, and map the vehicle to the right stick.**
>
> | Function | Channel | Stick |
> |---|---|---|
> | Steering | CH1 (aileron) | right stick, horizontal |
> | Throttle | **CH2 (elevator)** — *not* CH3 | right stick, vertical |
> | MUX `SEL` | CH5 or CH6 | a two-position switch (SwA–SwD) |
>
> Using CH2 rather than the nominal throttle channel is the whole point: **release the stick and the
> vehicle stops and straightens**, which is what
> [failsafe rows 1–3](design/safety.md#2-failsafe-matrix) already specify. It also makes the right
> stick behave exactly like the gamepad's (#15), so an operator switching between them does not
> have to re-learn anything.
>
> This matters most in **Layer B**, where the MUX routes the receiver *straight to the motor driver*
> with the Teensy out of the loop entirely. There, stick position **is** motor command — nothing is
> going to zero it for you. A ratcheted throttle in that path means letting go leaves the vehicle
> driving.
>
> **Buy Mode 2 units; do not buy Mode 1 and switch it in the menu.** The menu remaps the channels
> but cannot move the ratchet, which leaves a transmitter whose labels and springs disagree. Order
> all three the same.

> [!CAUTION]
> **#6 was one line hiding four parts, and one of them was never funded**
>
> Split into **6a–6d** above and moved to Batch 1G, because three of the four cannot be specified
> until the vehicle is on the bench.
>
> - **6a encoder** — could in principle be bought now, but **quadrature A/B and 3.3 V logic** are
>   hard requirements that the old line never stated. The Teensy 4.1 is **not 5 V tolerant**
> - **6b adapter** — the BOM's `3.15 mm` is *B-MROVER's* motor shaft. [ADR D-R](design/vehicle.md)
>   then changed the vehicle class entirely, so that number has no remaining basis here
> - **6c bracket** — **never in the BOM at all.** [02-mechanical §2.6](build/02-mechanical.md)
>   requires the encoder body bracketed to the motor mount; #13 is the steering coupler and #14 is
>   the sensor mast. Without it the body turns with the shaft and reads zero
> - **6d** — fasteners and cable tie-downs
>
> Full specification, including the decision tree for what the teardown finds:
> **[§1.2.3](build/01-bom-sourcing.md#6-drive-encoder-what-to-actually-buy)**.

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

> [!CAUTION]
> **#3 Sabertooth 2x32 — unavailable as of 2026-09-30. Candidate replacement below**
>
> The order placed 2026-09-29 was cancelled by the vendor: **no stock, no ETA.** The row above is
> cleared; nothing is committed.
>
> **What a replacement must do**, from the design rather than from preference:
>
> | | Requirement | Why it is not negotiable |
> |---|---|---|
> | 1 | **Accepts R/C servo pulses** | The [Pololu #2806 MUX](design/dbw.md#112-hardware-rc-signal-mux-the-d3-condition) multiplexes *servo pulses only*. [ADR §4](design/dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-teensy-as-both-masters) was **reverted** from packetized serial for exactly this reason |
> | 2 | **Stops the motors when the pulses stop** | [Failsafe rows 6 and 8](design/safety.md#2-failsafe-matrix), [FMEA row 9](design/safety.md#7-fmea-lightweight) — severity 5. Traction must die with **no software involved** |
> | 3 | **Two independently controlled channels** | M1 steering, M2 paralleled drive |
> | 4 | 12 V, adequate current, limiting + thermal | The paralleled stall current is still unmeasured |
>
> **Requirement 2 is the one that eliminates most of the market.** Plenty of dual drivers take RC
> pulses; far fewer stop when the pulses stop, and a driver that holds its last command when its
> controller dies is the *stale-setpoint-with-live-actuator* state the design calls more dangerous
> than a stop.
>
> **Leading candidate: Cytron SmartDriveDuo-30 (MDDS30).** Verified against its
> [user manual](https://makermotor.com/content/cytron/pn00218-cyt14/MDDS30_User_Manual.pdf) rev 1.11,
> not from a product blurb:
>
> | | Sabertooth 2x32 | Cytron MDDS30 |
> |---|---|---|
> | Continuous / peak per channel | 32 A / 64 A | **30 A / 80 A** |
> | Voltage | 6–30 V | **7–35 V** |
> | R/C pulse input | yes | **yes** — `SW1:SW2 = 00` |
> | Independent dual control | yes | **yes** — `SW3:SW4 = 11`, "INDEPENDENT BOTH" |
> | **Signal-loss stop** | yes | **yes — 100 ms**, `SW6 = 0` |
> | Current limit + thermal | yes | yes |
> | Price | ₩250,000 | **$76–87** (≈₩104,000–119,000) |
>
> Slightly less continuous current, more peak, wider voltage, and roughly **half the price** — on a
> driver the BOM already calls oversized for this drivetrain.
>
> > [!WARNING]
> > **`SW6 = 1` disables the timeout, and the manual says so plainly**
> >
> > *"The centre point is fixed at 1.5 ms and the timeout feature is disabled. Motor will continue
> > to run…"*
> >
> > That single DIP switch is the difference between satisfying failsafe row 6 and silently
> > violating it. **`SW6` must be OFF**, and it must be *verified on the bench*, not assumed from
> > the factory default. Add it to the Stage 1 checklist.
> >
> > Also operational: *"The RC transmitter must be ON before power up."* That changes the bring-up
> > order and needs re-checking against [safety.md §6](design/safety.md#6-bring-up-protocol-staged-wheels-off-first).
>
> **Still to settle before ordering** — none of these are blockers, all are unverified:
>
> - **Korean stock.** Seeed is out of stock; Makermotor (US) lists it. No Korean distributor found.
>   Lead time is the reason the Sabertooth order was placed domestically in the first place.
> - **NTREX `NT-M-DCDM2430`** — dual 30 A, 7–36 V, RC and joystick input, sold through
>   **디바이스마트**, i.e. domestic and fast. Korean-made. **Its signal-loss behaviour is
>   undocumented in anything found so far** — get the manual and check requirement 2 before
>   considering it, because that is the requirement it is most likely to fail.
> - **Sabertooth 2x25 V2** — same family, same manual, same DIP layout, same $124.99. The
>   lowest-risk swap if it is in stock anywhere, since nothing else in the design changes.

> [!NOTE]
> **One driver actuates the whole vehicle — there is no second motor driver in this BOM**
>
> The Sabertooth is **dual channel**, and both channels are used
> ([dbw.md §11.3](design/dbw.md#112-hardware-rc-signal-mux-the-d3-condition)):
>
> | Input | Output | Drives |
> |---|---|---|
> | S1 | **M1** | steering gearmotor (#4) |
> | S2 | **M2** | the two rear traction motors, **paralleled** |
>
> So #4 needs no driver of its own. Note this project **inverts mrover's assignment** — mrover uses
> M1 = throttle, M2 = steering. If you reuse an mrover harness or printed enclosure, the wiring
> differs; [dbw.md §2.1](design/dbw.md#2-steering-actuation-design) records why.
>
> The rear pair sharing one channel is also why there is no differential and why only one shaft is
> instrumented — see [ADR C](design/dbw.md#8-adr-c-drive-distance-encoding) for what that costs
> odometry.

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
| 4 | Steering gearmotor + encoder — **contingency only** | 3 | TBD | 48,000 | . | . | 0/3 | | **The vehicle has a stock steering gearmotor** (confirmed on the parent remote, 2026-10-01), so [dbw.md §11.5](design/dbw.md#115-3-tap-connector-spec-minimally-invasive) reuses it rather than adding one. **The ≥ 2× torque margin is already demonstrated** by the 25 kg occupant rating against ~6 kg of kit (V1). Kept funded against one residual risk only: the stock motor was never specified for **continuous closed-loop duty**. **Released at [Stage 1](design/safety.md#6-bring-up-protocol-staged-wheels-off-first)** if it holds a sustained position loop without overheating |
| 5 | Absolute angle sensor (AS5600 **or** pot) | 3 | TBD | 27,000 | . | . | 0/3 | | **V2**: lock-to-lock travel — **≤ 340° ⇒ AS5600** |
| 13 | Steering coupler + magnet mount | 3 | TBD | 20,000 | . | . | 0/3 | | **V3**: column / kingpin shaft diameter. **The motor-coupler half is probably not needed** — the stock gearmotor is already coupled to the linkage. The **angle-sensor magnet mount is still required** ([ADR B](design/dbw.md#5-adr-b-steering-angle-encoding) mounts it load-side). Re-scope once M1 settles #4 |
| 60 | **#6a** Sensor — **Hall LATCH ×2 per vehicle, TO-92** | 3 | DigiKey / Mouser | 14,000 | . | . | 0/3 | | **`DRV5013BCQLPGM` or `DRV5013AGQLPGM` (TI, TO-92 `LPG`)** — digital bipolar latch, **2.5–38 V** so it runs straight off the 3.3 V rail, open-drain 30 mA with a **3.3 V pull-up**, `B_OP ±10 %` over temperature. ~$0.50 each, ~6 + spares. **`US1881` (TO-92, marked `U18`/`OH188`) is the fallback** — same latch behaviour, but 3.5 V minimum so it needs a 5 V feed. **A LATCH IS A HARD REQUIREMENT, NOT A PREFERENCE.** A latch's edges come from the field **reversing sign**, which happens at a fixed place on the ring; a switch's edges come from a **threshold on magnitude**, which moves with air gap and temperature — jitter on the counts and, worse, phase error between A and B exactly where direction is decided. **Do not buy `A3144` / `OH3144` / `US5881` (unipolar switches — `US5881` is one digit from `US1881` and is stocked domestically), `49E` (linear), or anything sold as omnipolar.** Take the **less** sensitive variant: a Ø5 × 2 mm disc gives ~75–240 mT across a 1–3 mm gap against a ±12 mT threshold, and the spare margin is better spent on noise immunity beside a PWM'd motor. Spaced **`(n + ½)` pole pitches** — *one electrical cycle spans two magnets, so 90° electrical is half a pole pitch; **6.82 mm** at 18 magnets on the Ø78.2 carrier* — sensing **radially** at the hub from a bracket on the fixed gearbox housing, into the Teensy's hardware quadrature decoder. *(An AS5600 was proposed 2026-10-02 and withdrawn: it needs a free rotating shaft **end**, and this vehicle has none — the same geometry that closed branches A and B.)* ([§1.2.3](build/01-bom-sourcing.md#6-drive-encoder-what-to-actually-buy)) |
| 61 | **#6b** Magnet | 3 | TBD | 4,000 | . | . | 0/3 | | **18 × Ø5 × 2 mm, AXIALLY magnetised (flat faces are the poles — a diametric disc of the same size is useless and is sold beside it), neodymium N35 or better, NiCuNi.** 54 for three vehicles; buy well over that — neodymium chips, a reversed magnet is a destructive removal, and the first one is a fit test. A multipole ring was preferred and does not survive the measured hub: at a **64 mm** bore those are industrial parts. Pole pitch 13.65 mm, 36 counts/rev, **15.8 mm/count** against a 2 %-over-20 m gate. **18 and not 16** because the three grub screws must land exactly half a pitch from their neighbours, so the magnet count has to divide by the screw count. **Acceptance test: magnetic viewing film or a spare magnet walked round the track shows a reversed disc at once; then turn the ring by hand and watch one channel — a reversed magnet shows as one long gap and one short pulse, and you count from the index groove to find it.** A ring fixes spacing, polarity and placement together; loose magnets fix only spacing, and one fitted backwards is a permanent odometry error calibration will partly absorb and therefore hide |
| 62 | **#6c** Printed carrier + sensor bracket | 3 | 로컬 / 3D print | 6,000 | . | . | 0/3 | | The hub is **lobed over its whole exposed surface** (six broad lobes), so this item prints the carrier as well as the bracket. **One piece, not a split clamp** — the sensor rides 1–3 mm off the outer surface, so every feature on the part is a recess; the two-piece revision stood its clamp ears **9 mm proud** and swept Ø91 against a sensor face at Ø78. The wheel comes off, so the ring slides on. **Bore Ø64.2 is clearance, not a fit**: the hub is **63.0 mm** (tape across opposite lobe crests, three positions, 2026-10-08 — a wire reading of 205 mm had put it 2.3 mm high because a wrap measures pi*(D + wire thickness), and a 20 g ring was printed 4 mm oversize before anyone measured across) and FDM holds a Ø64 bore to ±0.3, so **3 × M3 grub screws** take up the slack and drop into lobe gaps — one print fits all three vehicles. Plain **Ø78.2** outside for the magnet pockets. Model at `cad/drive_encoder_carrier.scad`, pitch 13.65 mm, **sensor offset 6.82 mm**, 36 counts/rev. **Do not model the lobe form**: the carrier transmits no torque, and the 8 mm slot captures it axially. **Print `PART = "gauge"` first** — a 12 g fit mule at the real bore, OD and width; fit it, refit the wheel and turn one revolution. That settles the bore, the radial clearance and the axial gap at once, before any magnet is glued. **The bracket clamps the gearbox housing nose**, which is concentric with the axle, so the air gap is a printed dimension rather than an alignment job — and because the bracket does not rotate it may have ears, unlike the carrier. Slot the sensor pad so the gap is adjustable. This replaces bolting to screw bosses, which is the measurement #6c used to be blocked on. **Print both TO-92 sensors into one part** so the **6.82 mm** spacing is fixed by construction, and print the magnet pockets into the carrier for the same reason — uneven spacing aliases into odometry, and a hand-placed pocket is no better than a hand-placed magnet |
| 63 | **#6d** Fasteners, threadlock, tie-downs | 3 | 로컬 | 1,000 | . | . | 0/3 | | Per vehicle: **3 × M3 heat-set insert, 3 × M3 × 10 grub screw** (cup or cone point — a cone point finds a lobe gap on its own), blue threadlocker. The inserts come from [#14](build/01-bom-sourcing.md#7-8-11-12-14-what-to-actually-buy). Route the encoder cable away from the motor leads |
| | **Batch 1G** | | | **120,000** | | | | | **× 3 = 360,000** |

## Measurements that unblock Batch B

Take these on the vehicle you actually bought. Fill in before ordering.

> [!NOTE]
> **`V` for Verification — and why these are not called `M`**
>
> These used to be `M1`/`M2`/`M3`, which collided with two other things in this project: the
> **motor driver's output channels** `M1`/`M2` (printed on the board — `M1` steering, `M2` drive) and the **Learn modules** `M1`–`M8`. All three appeared in bold
> in this one file, forty lines apart, meaning different things. The driver channels cannot be
> renamed and the Learn modules are referenced from seventeen files, so the measurements moved.



### V1 — Steering actuator verification *(torque question closed 2026-10-01)*

> [!NOTE]
> **The ≥ 2× torque margin is already demonstrated. No spring-scale test is required.**
>
> The vehicle is rated for a **25 kg occupant** and steers under the parent remote with that
> load aboard. MRider adds **~6 kg**. The margin is therefore demonstrated at roughly 4× the
> added mass, well past the ≥ 2× gate, without measuring anything.
>
> **And the comparison is conservative**, because of *where* the mass sits. Steering torque
> tracks **front-axle** load, and a seated child sits between the axles with most of their
> weight over the rear. Deck- and mast-mounted kit sits further forward, so 6 kg of kit adds
> less front-axle load than 25 kg of child even before the 4× ratio is counted.
>
> [vehicle.md §4](design/vehicle.md) already runs this argument for **payload** — *"these cars
> are rated for a child (~25–30 kg); ~6 kg of kit is well inside that."* It extends to steering
> torque for the same reason.
>
> The [§2.2 spring-scale procedure](design/dbw.md#22-torque-measurement-procedure-before-sizing-the-gearmotor)
> is retained in the design record — it is how you size a gearmotor you are **buying**, and the
> next cohort may receive a chassis with no stock steering motor at all. It is simply not needed
> on this one.

**What the rated load does *not* settle**, and what therefore still has to be measured:

| Field | Value |
|---|---|
| **Stock steering gearmotor present?** (Y/N) | **Y** — steers under the parent remote, 2026-10-01 |
| **Stock ECU** | **`JR1630RX-12V`** — 2.4 GHz receiver + motor controller, one module. **DC 12 V, load current max 20 A.** Separable, with a connector harness (2026-10-01) |
| **Inline protective device, battery → ECU** | **10 A**, in the main `+` line, **no manual reset** (2026-10-01). See the caution below |
| **Traction pack termination** | **Keyed 2-pin connector, no posts** (2026-10-02). The pack is sealed with a pigtail; the power tap plugs in here rather than bolting to a terminal |
| **Drive-motor termination** | **Keyed 2-pin connector** (2026-10-02, white, red/green pair) — the throttle tap is an unplug too |
| **Rating of both stock connectors** | *(unknown, and they are the current ceiling: everything MRider draws passes through them, against a stock circuit protected at 10 A. Set the drive-channel limit below the smaller. Decided by hand at Stage 4 — a warm connector is the answer)* |
| **Stock motor markings / rating** | *(read the can)* |
| **Steering-motor winding resistance `R` (Ω)** — minimum over several rotor positions, lead resistance subtracted | |
| **Implied stall current `12 / R` (A)** | |
| Date / by | |

**Where to put the probes.** On the **steering motor's own two leads, with the motor unplugged
from the ECU.** Not at the controller end, not on the connector's controller side. Left connected,
you measure the winding in parallel with the output stage — MOSFET body diodes and snubbers — and
get a reading that is wrong and usually low.

1. Identify the steering motor: it is at the **front**, on the steering linkage. Steer with the
   parent remote and watch which motor turns. The two at the rear are the `RS 390-12V` drive
   motors.
2. **Unplug its 2-pin connector** and probe the **motor-side** pins.
3. Multimeter on the lowest Ω range. Take several readings, **rotating the output slightly
   between them** — brush-to-commutator position changes the value. Use the **minimum**, which
   gives the highest current and is therefore the conservative one.
4. **Subtract the lead resistance.** Touch the probes together, note the reading, subtract it. At
   1–3 Ω a 0.3 Ω test lead is a 10–30 % error, which is the whole answer.
5. `I_stall ≈ 12 V / R`.

Measure one vehicle, then spot-check the other two. A large disagreement is itself information.

> [!NOTE]
> **This is five minutes, not a gate. Fitting a fuse and watching it is also a valid answer.**
>
> The number sets the M1-branch fuse and the driver's current limit. Both have defensible
> defaults — a 10 A fuse on the steering branch is consistent with what the stock vehicle already
> runs the whole car behind — and at these power levels the cost of guessing wrong is a blown
> ₩500 fuse, not damage. Measure it if the multimeter is already out; fit a fuse and see if it
> holds if it is not.

> [!CAUTION]
> **The 10 A device is not a fuse, and MRider must not inherit it**
>
> It sits in the battery `+` line to the ECU, is marked **10 A**, and has **no manual reset** —
> so it is almost certainly an **auto-resetting thermal breaker**. Two consequences:
>
> - It trips on **heat**, which is slow. It is not short-circuit protection, and
>   [03-electrical §3.2](build/03-electrical.md) still requires MRider's own fusing, sized to
>   measured stall current.
> - **It re-closes by itself once it cools.** On a toy with a parent watching, that is a feature.
>   On a vehicle that drives itself it means traction can return **unannounced**, minutes after a
>   trip, with no operator action — a state the [failsafe matrix](design/safety.md#2-failsafe-matrix)
>   has no row for, because nothing in MRider's design re-energizes itself.
>
> **Therefore take the power tap at the battery, upstream of this device**, leaving it in the
> stock branch where it belongs. That keeps the stock path factory-protected and reversible, and
> keeps a self-resetting device out of the DBW traction path. *(To tell the two apart: an
> auto-reset breaker restores after a minute or two of cooling; a one-shot thermal fuse never
> does.)*
>
> **And do not reuse this class of part for the E-stop.** Its `10A` is an **AC** rating —
> the label reads `125/250VAC` with `50VDC` listed separately. That is exactly the trap
> [§1.2.2](build/01-bom-sourcing.md) documents: DC has no zero crossing to extinguish the arc.

> [!IMPORTANT]
> **Stall current is a separate question, and a child steering the car does not answer it**
>
> Occasional slow steering is not a locked-rotor condition. This number sets the **M1-branch fuse
> and wire gauge** — still blank in [03-electrical §3.2](build/03-electrical.md) — and the
> **driver current limit** that [FMEA row 6](design/safety.md#7-fmea-lightweight) relies on for a
> severity-4 row. It is recorded nowhere else in this project.

> [!WARNING]
> **The remaining risk is duty cycle, not torque — and Stage 1 is what tests it**
>
> A child steers in occasional slow sweeps. A **position loop** makes small, continuous,
> high-frequency corrections — [ADR B](design/dbw.md#5-adr-b-steering-angle-encoding) describes
> exactly *"the small, high-duty-cycle oscillations a steering servo makes."* The stock motor was
> never specified for that, so the failure mode to watch is **thermal and wear**, not "cannot
> turn the wheel". It will not show up on a spring scale at any load.
>
> [Stage 1](design/safety.md#6-bring-up-protocol-staged-wheels-off-first) already exercises
> exactly this: closed-loop tracking, limit clamping, stall detection, on a current-limited
> supply. **That is the gate on releasing #4**, not a torque measurement. Watch the motor's
> temperature through a sustained hold.

> [!NOTE]
> **If the stock motor is replaced after all**
>
> The documented fallback is a **12 V automotive wiper motor**. Two consequences you must accept
> and re-check against [safety.md](design/safety.md) before the vehicle touches the ground: its
> worm gear is largely **non-back-drivable**, so on power loss the steering **holds** rather than
> freewheels — which invalidates the freewheel analysis — and it rarely has a usable shaft
> encoder. Record the choice here if you take it.

### V2 — Sensor shaft travel → decides #5

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

### V3 — Shaft diameter → sizes #13

| Field | Value |
|---|---|
| Column diameter (mm) | |
| Kingpin / sensed shaft diameter (mm) | |
| **Drive motor (from the can)** | **`DING LI RS 390-12V RPM 18000`** — 2026-09-30 |
| **Drive-motor shaft diameter (mm)** | ~2 mm, carrying a 12-tooth pinion — not accessible |
| **Rear shaft stub present?** (Y/N) | **N** — RS-390 is single-ended |
| **Rear stub diameter (mm) / length protruding** | n/a |
| **Output shaft reachable before the gearbox?** (Y/N) | **N** — pinion meshes directly into a sealed gearbox |
| **Encoder branch chosen** (A / B / C — [§1.2.3](build/01-bom-sourcing.md#6-drive-encoder-what-to-actually-buy)) | **C**, mounted at the **gearbox output hub** (1:1 with the wheel) |
| **Axial clearance, gearbox rotating part → wheel** | **≥ 8 mm** — **the measurement that decided Branch C.** Taken at teardown, recorded 2026-10-03. The bracket arm *and* the sensor package both fit inside it, so specify **surface-mount** Hall parts: a TO-92 pair plus a 3 mm arm leaves ~1 mm |
| **Paralleled drive-motor stall current (A)** — §3.1, locked rotor | *(measure — RS-390 expected well inside the 30 A channel, but a class is not a current)* |
| Coupler type selected | |
| Magnet mount approach (concentricity + air gap) | |
| **Radial room in the 8 mm slice** (≥ 46.1 mm: ring 39.1 + gap 3 + sensor 4) | |
| **Axial length of the lobed boss still exposed with the wheel fitted** (the ring is 6 mm wide) | *Settled by the fit mule* |
| **Gearbox housing nose — diameter and reachable length** (the sensor bracket clamps it) | |
| Date / by | |

---

## Batch 2 — Tier 2 perception, card B

**A different card from Batch 1.** Deliberately last: if the steering loop fails its accuracy gate
at [bench Stage 1](design/safety.md#6-bring-up-protocol-staged-wheels-off-first), this money has not
been spent yet. That sequencing is the entire point of the two-tier split.

| # | Item | Qty | Vendor | Unit ₩ | Ordered | Arrived | Secured | Paid ₩ | Verify on arrival |
|---|------|----:|--------|-------:|:-------:|:-------:|:-------:|-------:|-------------------|
| 16 | 2D LiDAR — RPLIDAR A1M8 | 3 | — **already held** | 0 | — | — | 3/3 | 0 | **In hand before approval.** Confirm 3 units and that each spins up |
| 17 | Front camera — USB 1080p, 120° wide, **고정초점** | 3 | [쿠팡](https://www.coupang.com/vp/products/9574234009?vendorItemId=95522090726) | 24,800 | 2026-09-30 | 2026-09-30 | 3/3 | 74,400 | **Driver: `usb_cam`, `pixel_format: mjpeg2rgb`** — `v4l2_camera` defaults to YUYV, which this camera runs at 10 fps on 720p. MJPG 1280x720 @30 and no focus controls ✅ validated on the first unit; units 2 and 3 are the **same model from the same listing**, so the check is not repeated. ₩35,800 list − ₩11,000 = ₩24,800 VAT incl; ₩74,400 covers all 3. **All 3 in hand 2026-10-01** | grep -i focus`. **`v4l2-ctl --list-formats-ext` must show MJPG 1280x720 @30 fps** |
| 18 | IMU — BNO085 class | 3 | 아이씨뱅큐 | 45,980 | 2026-09-29 | 2026-10-08 | 3/3 | 137,940 | ₩41,800 ex-VAT = **₩45,980 incl**; the approved figure was the ex-VAT one. 9-DoF with **onboard fusion** **Secured 2026-10-08:** genuine BNO085, I²C broken out. |
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
| **3** | Sabertooth 2x32 | **Cytron SmartDriveDuo-30 (MDDS30)** | Sabertooth unavailable — vendor cancelled 2026-09-30, no stock and no ETA. The Cytron meets all four hard requirements and costs ₩106,560 less per unit | **Partly** — see below |
| | | | | |

> [!IMPORTANT]
> **#3 Sabertooth → Cytron MDDS30: what changes, and what deliberately does not**
>
> **Nothing above the driver changes.** The Teensy firmware, the
> [signal MUX wiring](design/dbw.md#112-hardware-rc-signal-mux-the-d3-condition), and the
> `ros2_control` stack are all untouched, because the interface is **servo pulses** either way.
>
> That is not luck. [ADR §4](design/dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-teensy-as-both-masters)
> was reverted from packetized serial to R/C PWM so the hardware MUX could sit in the path — a
> decision that read as a constraint at the time. It is what makes the driver a **swappable box**
> today, under supply pressure, four days before a build. A serial-protocol design would have
> needed firmware work and a re-verified failsafe.
>
> | | Sabertooth 2x32 | Cytron MDDS30 |
> |---|---|---|
> | Continuous / peak per channel | 32 A / 64 A | 30 A / **80 A** |
> | Voltage | 6–30 V | **7–35 V** |
> | Signal-loss stop | yes | **yes, 100 ms** (`SW6=0`) |
> | Unit price | ₩250,000 | **₩143,440** |
>
> **What still needs checking, and must not be assumed:**
>
> 1. **`SW6=0` on every board, verified on the bench.** `SW6=1` disables the timeout entirely —
>    *"motor will continue to run"*. One switch is the difference between honouring
>    [failsafe row 6](design/safety.md#2-failsafe-matrix) and silently violating it. This is the
>    single highest-consequence item in this substitution.
> 2. **"The RC transmitter must be ON before power up."** The MDDS30 manual says so; the Sabertooth
>    has no such requirement. Re-check the
>    [staged bring-up order](design/safety.md#6-bring-up-protocol-staged-wheels-off-first) against it.
> 3. **30 A continuous vs 32 A.** Immaterial on paper — the BOM already calls the 2x32 oversized —
>    but the paralleled drive-motor stall current is *still unmeasured*. Measure it at teardown and
>    record it below. 80 A peak is comfortably above the Sabertooth's 64 A.
> 4. **The design documents still say "Sabertooth 2x32" throughout.** Deliberately not rewritten
>    yet: update them when the boards arrive and Stage 1 passes, not on the strength of an order.
>    A design record that tracks intentions rather than hardware is worse than one that lags.

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
