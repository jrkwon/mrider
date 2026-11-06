# 3. Electrical & Wiring

**Goal:** build the power and signal harness, including the authority MUX and E-stop.

Wire the traction rail, the isolated logic rail, the motor driver, the Teensy,
the relay-MUX (STOCK vs. DBW), the hardware RC signal MUX, and the hardware E-stop. Verify
rail isolation and default-to-stock behavior before energizing anything downstream.

- **Prerequisites:** Section 2 complete.
- **Specification:** [design/dbw.md](../design/dbw.md), [design/safety.md](../design/safety.md)
- **Expected outcome:** harness continuity-checked; relay defaults to STOCK; E-stop cuts
  traction power only.

> [!WARNING]
> **Draft — not yet validated on hardware**
>
> This wiring plan is derived from the
> [architecture.md power tree](../design/architecture.md#5-power-tree-and-safetyauthority-chain)
> and [safety.md](../design/safety.md). It has **not** been built. Fuse values, wire gauges,
> and relay contact ratings depend on the stall currents you measured in step 2 and are
> marked *(measure during bring-up)*.

> [!CAUTION]
> **This is the step where mistakes become dangerous**
>
> Everything before this was mechanical. From here the vehicle can move under power. Wire
> the E-stop and the MUX **first**, verify default-to-STOCK **before** energizing the
> motor driver, and keep the vehicle wheels-off until step 7.

---

## 3.1 The two rails

MRider has exactly two power rails, and the split is safety-critical.

```
Chassis traction pack
  │
  └──▶ 25 A fuse ──▶ E-stop contactor ──┬──▶ stock ECU  (through its own factory protector)
       (cuts TRACTION only)             └──▶ Motor driver B+

  The Relay MUX then switches the MOTOR LEADS — not either controller's supply:

  stock ECU motor outputs ──▶ 87a (NC, default) ─┐
                                                 ├─▶ 30 (COM) ─┬─▶ steering gearmotor
  driver M1 / M2 outputs  ──▶ 87  (NO, DBW)     ─┘             └─▶ paralleled drive motors

12 V logic battery ─┬─▶ UBEC A ─▶ 5 V ─▶ Teensy 4.1 VIN   (and nothing else)
                    │                         └─▶ Teensy 3.3 V pin ─┬─▶ AS5600 (I²C)
                    │                                               └─▶ 2 × Hall latch + pull-ups
                    ├─▶ UBEC B ─▶ 5 V ─┬─▶ RC receiver
                    │                  ├─▶ hardware RC signal MUX
                    │                  └─▶ motor driver signal logic
                    └─▶ 12 V direct ───┬─▶ relay MUX coils
                                       └─▶ E-stop contactor coil

Laptop ──▶ its own internal battery (NOT wired to traction in v1)
```


> [!IMPORTANT]
> **Three things that diagram fixes, all of which this page used to get wrong**
>
> ![The logic side of MRider: the logic battery feeding two UBECs and a direct 12 V tap, the Teensy's own 3.3 V pin feeding the AS5600 and the Hall latches, the Teensy and receiver both feeding the Pololu signal MUX into the motor driver, and the E-stop's two NC contacts breaking the contactor coil and the relay MUX coil separately](../images/logic-signal-wiring.svg)
>
> **1. There is no 3.3 V rail.** This page used to say the angle sensor takes *"3.3 V from the logic
> rail"* — but **the logic rail is 5 V.** The 3.3 V comes from the **Teensy's own regulator**, which
> is correct and also a budget: everything on it shares the Teensy's 3.3 V pin, so the AS5600, both
> Hall latches and their pull-ups all draw from one source. None of them is hungry, but it has to be
> counted rather than assumed.
>
> **2. The two UBECs are split by AUTHORITY LAYER, not by current.** **UBEC A carries the Teensy
> alone. UBEC B carries the receiver, the signal MUX and the driver's signal logic.** The reason is
> the whole justification for [D3](../design/dbw.md#112-hardware-rc-signal-mux-the-d3-condition):
> the hardware override exists to survive the Teensy. **Put both on one regulator and a single UBEC
> failure takes out the override and the thing it overrides at the same time.** Split this way, a
> UBEC A failure leaves the receiver, the MUX and the driver alive — flip `SEL` to slave and drive
> it off the field by hand.
>
> **3. The relay MUX is in the MOTOR LEADS, not in the driver's `B+`.** *Corrected 2026-10-28.*
> This diagram, the §3.2 gauge table and the §3.2 branch sketch all used to read
> `… ▶ E-stop contactor ▶ relay MUX ▶ driver B+`, which is **a different circuit from the one the
> rest of the build describes** — and [power-wiring.svg](../images/power-wiring.svg) drew it that
> way while carrying a box of its own saying *"the MUX breaks **both** motor conductors, which is
> why four poles and not two."* **The figure contradicted itself.**
>
> The number of poles settles it. **Switching a supply needs one pole; switching two motor circuits
> at both ends needs four**, which is what [#7](../order-log.md) bought and what
> [dbw.md §11.5](../design/dbw.md#115-3-tap-connector-spec-minimally-invasive) specifies — the
> throttle and steering taps intercept *motor leads*, and the **power tap separately feeds `B+`**.
>
> **And the wrong version is not merely untidy, it is unsafe.** With the MUX in `B+`, the motor
> leads are never broken, so **the stock ECU's output stage and the driver's output stage stay
> connected to the same motor permanently.** Whichever is powered wins, and the unpowered one is a
> back-feed path through its own H-bridge body diodes. *Breaking both conductors is the thing that
> stops those two sources from ever meeting, and it is what the four poles are for.*

| Rail | Feeds | Dies when |
|---|---|---|
| **Traction / motor** | Driver B+, M1 (steering gearmotor), M2 (drive motors) | E-stop pressed, MUX drops, pack disconnected |
| **Isolated logic** | Teensy, angle sensor, RC receiver, signal MUX, motor driver signal logic, MUX coil driver | Logic battery disconnected only |

> [!CAUTION]
> **The logic rail is now a separate battery, not a tap off the pack**
>
> The superseded design got logic isolation from the Pixhawk's PM02 power module. **That
> part is deleted**, so the isolation must be built explicitly — a dedicated 12 V battery and
> DC-DC, from day one, not as a retrofit
> ([safety.md §5](../design/safety.md#5-power-rail-isolation-and-brownout-protection)).
>
> This matters more than it did before. The Teensy holds the **entire** safety supervisor —
> the position loop, throttle shaping, the staleness watchdog, RC serial decode, arming. A reset
> mid-drive loses every firmware-layer protection at once (FMEA row 4, severity 5). There is
> no second controller to survive it.

> [!NOTE]
> **The steering gearmotor is on the traction rail — deliberately**
>
> [safety.md §4.1](../design/safety.md#4-steering-motor-power-rail-assignment-and-power-loss-behavior-pinned)
> pins this. The consequence is that **E-stop de-energizes the steering motor and the
> column freewheels**. That is the intended, analyzed behavior — acceptable at ≤ walking
> speed with an operator alongside. Putting the steering motor on the logic rail would risk
> browning out the Teensy on a steering stall, and would leave a live actuator after an
> emergency stop. Do not "improve" this.

**Brownout isolation is the point of the split.** Motor stalls sag the traction rail. The
logic rail must not follow. Use adequate hold-up capacitance and put the undervoltage monitor
on the **logic** rail.

![Power wiring in detail, in two rows: the supply row runs the traction pack through a 25 A fuse and the E-stop contactor, then forks to the stock ECU and to the motor driver's B+ with the relay MUX in neither fork; the authority row puts the four-pole relay MUX in the motor leads, stock ECU outputs on 87a and driver M1/M2 on 87, COM out to the steering gearmotor and the paralleled drive motors; and separately the LiFePO4 logic pack through a 5 A fuse to two UBECs and a direct coil tap feeding every relay coil, with the E-stop button's two NC contacts sitting in those two coil feeds and nowhere else, and the single star ground where the two rails meet](../images/power-wiring.svg)

## 3.2 Per-rail fuse and gauge table

Fuse for the **stall** current, not the nominal draw, and size wire for the fuse.

> [!IMPORTANT]
> **Put each fuse at its battery, not at its load — and pick the holder style from that**
>
> A fuse protects everything **downstream** of it, and nothing upstream. Keep that unprotected stub
> as short as the hardware allows: **at the traction pack** for the 25 A, **at the logic pack** for
> the 5 A. On this vehicle the stub is a few centimetres of insulated lead between the stock
> connector and the fuse, which is what the rule is asking for.
>
> That placement decides the holder style, which is otherwise a coin toss:
>
> | | best where | why |
> |---|---|---|
> | **Panel/spade holder** | screwed to a plate or enclosure wall at the battery | **Fixed, findable, labelable.** You choose the wire gauge and crimp your own spades, and you can unplug without cutting |
> | **Inline pigtail** | a run with nothing to mount to, or an exposed location | Waterproof cap, no mounting. But it dangles in the harness, and its wire gauge is whatever the vendor used |
>
> **Prefer the panel type.** Thirteen students will debug three vehicles, and **a fuse nobody can
> find is a fuse nobody checks** — a blown one then reads as a dead controller. Use the inline type
> only where there is genuinely nothing to screw a holder to, or where the spot is exposed to
> weather.
>
> **If the panel type is short of stock, take inline for all three rather than mixing.** Three
> vehicles that differ from each other cost more than the style does: a lab instruction that is
> true of one vehicle and false of another is worse than either style. And the thing the panel
> mount was really buying — *findability* — is better bought directly: **label the holder, and
> record its location** on the per-vehicle calibration sheet.

| Rail / branch | What protects it | Wire | Fuse? |
|---|---|---|:---:|
| **Traction pack → 25 A fuse → E-stop contactor → *everything*** | **25 A blade fuse, at the pack** | AWG 14 | **yes — 1** |
| Driver M2 → **MUX** → paralleled drive motors | the driver's current limit, set to **20 A** | AWG 14 | no |
| Driver M1 → **MUX** → steering gearmotor | same current limit | AWG 14 | no |
| **Logic pack → UBEC inputs + MUX coils** | **5 A blade fuse, at the pack** | AWG 18 | **yes — 1** |
| UBEC → Teensy, sensor, RC RX, signal MUX | the UBEC's own 3 A limit | AWG 20 | no |

**Two fuses per vehicle, one at each battery.** Not one per row.

> [!WARNING]
> **"The driver's current limit, set to 20 A" is a Sabertooth setting, and the board bought does
> not appear to have it — OPEN**
>
> Two rows above justify **no fuse on the motor branches** on a *"current limit, set to 20 A"*.
> **The `MDDS30` manual documents no user-settable limit.** It lists *"current limit protection"*
> as a feature with no number, and the only current figures it gives are **30 A continuous and
> 80 A peak per channel**, derated by temperature (80 A below 50 °C, 50 A to 70 °C, 40 A to
> 100 °C, 30 A above).
>
> **That matters because the branches are AWG 14**, which is not a 30 A conductor in a loom. *The
> no-fuse argument may still be right — a fuse that blows and stays blown mid-lab is a real cost —
> but it is currently resting on a number from a board that was never fitted.*
>
> **Two things close it:** find the limit in the board's own configuration if it has one, and
> **measure the drive-motor stall current** (`I1`, still outstanding). *The traction pack is a
> 4.5 Ah SLA; at 20 A that is a 4.4 C discharge, so the pack's own internal resistance may be the
> real limiter — which is a measurement, not an assumption.*

> [!NOTE]
> **Why the branches are not individually fused**
>
> An earlier revision of this table asked for a fuse on every row and sized none of them, because
> nothing had been measured yet. With the gauges settled, most of those rows do not want one.
>
> **A branch needs its own fuse only when its wire is thinner than what the upstream fuse
> protects.** The traction side is 2.5 mm² end to end, so the 25 A fuse at the pack protects all of
> it; a second fuse downstream would guard nothing the first does not.
>
> **And on the motor branches a fuse would be actively worse.** The driver's current limit is
> already the mitigation [FMEA row 6](../design/safety.md#7-fmea-lightweight) relies on, and it
> **clamps and recovers**. A fuse in the same place **blows and stays blown** — a steering stall
> during a lab would end with dead steering and a field repair, where the current limit ends with
> the motor sitting there warm.
>
> Fuses earn their place at the **batteries**, against the fault a current limit cannot see: a short
> anywhere in the harness **MRider adds**.
>
> That is the realistic scenario, and it is duller than it sounds. The vehicle's own terminals are
> insulated and connectorised, so there is nothing to drop a spanner across. What there *is*, is
> several metres of new wiring routed by **thirteen students** through a chassis they are drilling,
> bolting and re-opening across a semester — pinched under a panel, chafed on a bracket edge, or
> landed on the wrong terminal. A pack of this chemistry will push hundreds of amps into any of
> those, and the driver's current limit sits downstream and never sees it.

> [!CAUTION]
> **Verify paralleled drive-motor stall current against 32 A/channel**
>
> This is [FMEA row 7](../design/safety.md#7-fmea-lightweight) and an explicit cross-check
> in [dbw.md §13](../design/dbw.md#13-cross-checks-and-open-follow-ups). If the two
> paralleled rear motors can exceed 32 A stalled, you must either current-limit in the
> driver's configuration or select lower-draw motors. Measure it — a locked-rotor test
> with a clamp meter and a current-limited supply — do not assume.

## 3.3 The three taps

Reversibility comes from three keyed inline connectors that intercept the stock harness
without cutting it ([dbw.md §11.5](../design/dbw.md#115-3-tap-connector-spec-minimally-invasive)).

| Tap | Intercepts | MUX side | Notes |
|---|---|---|---|
| **Throttle tap** | stock throttle motor leads | NC → stock ECU, NO → driver M2 | paralleled rear motors — and they are paralleled **inside the stock ECU-end housing**, so this tap intercepts **four conductors carrying two nets**. **Read the pairing off the housing** (two wires to a contact); do not infer it from colour, because the two motors are mirror-mounted and the stock harness may cross them. Traced on vehicle #1 2026-11-06 — [02-mechanical §2.2](02-mechanical.md#22-teardown) step 2 |
| **Steering tap** | stock steering motor leads | NC → stock ECU, NO → driver M1 | **The stock steering motor exists and is connectorised at the ECU end** (`M2M3`, its own 2-pin socket) — confirmed 2026-11-06, so the tap **reuses the stock motor** rather than adding one. *That does not release BOM #4*, which stays funded until the duty-cycle test ([dbw.md §2.1](../design/dbw.md#21-actuator)). **Note the M1/M2 assignment is inverted vs. mrover** — intentional, see [dbw.md §2.1](../design/dbw.md#21-actuator) (finding F6) |
| **Power tap** | chassis traction pack, **in the trunk** | feeds the driver's B+ **and the stock ECU, through the contactor** | fused. The logic rail is a **separate battery** (§3.1), not tapped from here. **Tap at the battery, upstream of the stock inline protector** — see the caution below, and the one after it |

> [!CAUTION]
> **The contactor goes in the TRUNK, so it cuts the stock ECU too — corrected 2026-11-05**
>
> Two tables on this page used to read *"traction pack → E-stop contactor → driver B+"* and
> *"feeds the motor driver's B+ only"*, which puts the contactor in the **DBW branch alone**.
> **That leaves the stock ECU live after an E-stop** — and the same button drops the relay MUX to
> `87a`, which connects the motors to that live ECU. **Press the E-stop, press the pedal, and the
> vehicle drives.**
>
> **The contactor is in the battery's positive lead, upstream of the fork**, so one press removes
> power from the stock ECU and the driver together. *Three things on this page already said so and
> only the tables did not:* [the power figure](../images/power-wiring.svg) tees after the
> contactor, §3.4 says the E-stop *"cuts traction power"* rather than cuts the driver, and the
> figure's own reversibility line — **"returning it to stock means unbolting the contactor"** —
> only makes sense if the contactor is in the stock path.
>
> **What this means at the vehicle:** *the only stock conductor interrupted is the pack's `+`.*
> The `−` is never switched; it runs to the star ground. If the pack's `+` ends in a connector,
> **the contactor and fuse go in on an adapter lead and nothing is cut at all** — which is the
> §2.8 reversibility requirement met by construction rather than by promise.

> [!CAUTION]
> **Take the power tap upstream of the stock inline device, not downstream**
>
> The 2026 vehicle carries a **10 A** protector in the battery `+` line to the stock ECU, with
> **no manual reset** — an auto-resetting thermal breaker. Tapping downstream of it would put a
> device that **re-closes by itself** inside the DBW traction path: traction could return
> unannounced, minutes after a thermal trip, with no operator action. Nothing else in this design
> re-energizes itself, and the [failsafe matrix](../design/safety.md#2-failsafe-matrix) has no row
> for it.
>
> Tapping at the battery leaves that device in the **stock** branch, where it is the factory
> protection and where a parent is watching. MRider's own fusing (§3.2) then protects the DBW
> branch, sized to measured stall current — which is what that table is for.

### Wire gauge — match the stock harness for the taps, size the new runs yourself

The throttle and steering taps carry **the stock currents through the stock motors**. The loads do
not change, so **matching the conductor area of the stock harness is correct by construction** —
the manufacturer sized it for these motors, this pack, and this duty, and had it certified.

> [!NOTE]
> **Do not measure the stock harness. Use 1.5 mm² and move on.**
>
> An earlier revision of this page had you strip the insulation, count strands, measure strand
> diameter, and compute the area — because the 2026 harness marking
> (`ZR-RVV-300/300V-XF3061-2007`) gives type and voltage class but **no cross-section**.
>
> That procedure was disproportionate to the currents involved. The stock ECU is rated **20 A
> max** and sits behind a **10 A** device, and the motor driver's channel limit is **30 A**. At
> those currents over the ~1 m runs on this vehicle:
>
> | Conductor | drop at 10 A | drop at 30 A |
> |---|---:|---:|
> | 1.0 mm² | 0.35 V (2.9 %) | 1.05 V (8.8 %) |
> | **1.5 mm²** | **0.23 V (1.9 %)** | **0.70 V (5.8 %)** |
>
> **Use AWG 14 (≈2.1 mm²) silicone on the traction side** and **AWG 18–20 (≈0.5–0.8 mm²)** for
> logic and signal. Two numbers, no measurement. Both units are given because the design records
> mm² and Korean listings sell by AWG — and **AWG counts down as the wire gets thicker**.
>
> *Corrected 2026-10-02.* This box previously said 1.5 mm², which the table above justifies on
> **voltage drop** — and drop was never the binding constraint. **Ampacity is:** 1.5 mm² is ≈16 AWG,
> good for 18–22 A in chassis wiring, and it sits behind a **25 A** fuse. The wire would overheat
> before the fuse acted, which inverts the thing a fuse is for. 2.5 mm² (≈14 AWG, 25–32 A) puts the
> fuse back below the wire.
>
> Silicone rather than PVC for the reason the BOM already gives ([§1.5](01-bom-sourcing.md)):
> finer strands where the harness moves, and 180–200 °C against PVC's 70 °C.

**One place does differ from stock**, and it is worth a sentence rather than a procedure:

```
pack ──▶ power tap ──▶ 25 A fuse ──▶ E-stop contactor ──▶ driver B+
```

The stock ECU is capped at 20 A and sits behind a 10 A device; the motor driver will deliver **30 A
continuous** into a stalled pair if you let it. So this branch can carry more than the stock harness
ever did — which is an argument for setting the **driver's current limit** deliberately and fusing
this branch, not for a thicker wire than 1.5 mm².

Use **keyed** connectors — not generic bullets. During bring-up you will unplug and re-plug
these many times, and a reversed steering tap means the position loop runs away from its
setpoint instead of toward it.

## 3.4 Wire the E-stop and MUX first

Build the authority chain before anything can be commanded.

**E-stop.** Hardwired in the **traction** power path — not a software command. It must work when
the laptop and the Teensy have both hung. It does two things at once:

1. cuts traction power, and
2. drops the MUX coil, reverting authority to STOCK.

> [!IMPORTANT]
> **It is TWO parts, and which one carries the traction current is the whole point**
>
> | | Part | Carries |
> |---|---|---|
> | **the button** | [`#8b`](../order-log.md#L81) — 한국미스미 `MRE-RR2R`, Ø22 latching mushroom, **푸시 록 · 턴 리셋**, `2a2b`, IP65 | **coil current only** |
> | **the contactor** | [`#8a`](../order-log.md#L80) — `KKA-B4` 방수 릴레이 40 A 4-pin, wired `30→87` | **the traction current** |
>
> *This page used to call it "a latching mushroom-head contactor", one object, in the traction
> power path — which puts the button where the contactor goes. Corrected 2026-11-05.*
>
> **Nothing but coil current ever passes through the button.** Its two NC contacts break the
> contactor coil and the relay MUX coils; the contactor's contact is what interrupts the pack.
> *A signal-rated mushroom asked to switch traction **will weld shut**, and it fails in exactly
> the moment it exists for.* **`2a2b` is why the button can do both jobs** — two independent NC
> contacts, one per coil, which the caution below requires to be on **different contact blocks**.
>
> *"Contactor" here is a role, not a product category: the part is an automotive relay. It is
> called that because it is the thing that makes and breaks the traction contact.*

> [!NOTE]
> **The contactor appears TWICE in the power figure, and it is one relay drawn by its two halves**
>
> The traction row shows its **contact** (`30 → 87`); the logic section shows its **coil**
> (`85 · 86`). *Same part, two sections — because its contact lives on one rail and its coil on
> the other, which is the entire point of the design.*
>
> **Wire it like this. Six connections, and only one stock conductor is interrupted:**
>
> ```
> CONTACT HALF  — traction rail, AWG 14
>   pack +  ──▶ 25 A blade fuse ──▶ 30
>   87      ──▶ tee ──▶ stock ECU +   and   motor driver B+
>   pack −  ──────────────────────▶ star ground        (never switched)
>
> COIL HALF     — logic rail, AWG 18-20
>   12 V DIRECT ──▶ button #8b NC ① ──▶ 85
>   86          ──────────────────────▶ logic GND (the same star)
> ```
>
> **The button's second NC contact (`NC ②`) does the same job for the four relay MUX coils**, on a
> *different contact block* — see the caution below.
>
> **How to actually make the tee.** It is the joint that carries the whole 25 A, so it has to be
> one you can *look at* later.
>
> | | | |
> |---|---|---|
> | **Recommended** | a small **brass bus bar / power distribution block** — one stud in from `87`, two studs out | inspectable, re-openable, and the B+ branch unbolts to return the vehicle to stock |
> | Acceptable | **one uninsulated butt barrel, three wires** — the `87` lead in, two AWG 14 out — ratchet-crimped and sealed with the 3:1 heatshrink already bought | it works, and **it can never be inspected again** |
> | Avoid | **piggyback spades** stacked on the socket's `87` | the stack is the weak point, and it is carrying everything |
>
> **Build it at the PACK end, in the adapter lead, on the bench.** *Fuse, contactor and tee then
> form one removable assembly:* the stock side keeps its connector, the new side is one branch to
> `B+`, and the whole intervention comes out as a unit. **The tee must sit downstream of both the
> fuse and the contact** — upstream of either and one branch is unprotected or uncut, which is the
> defect [§3.3](#33-the-three-taps) corrected on the contactor's own placement.
>
> **No line in the [Order Log](../order-log.md) buys one.** *Same shape as the terminal blocks and
> the bypass caps: a part specified by the wiring and procured by nothing.* **Check the lab drawer
> first** — the part costs about ₩2,200 and a delivery costs more than the part.
>
> **What to look for, if it has to be bought:** a **fixed barrier terminal block, 30 A, M4**, which
> takes an AWG 14 ring terminal and clears the 25 A fuse with 20 % to spare. *Two ways to make the
> tee in one: land the input ring on one side of a pole and **two output rings on the opposite
> screw**, or bridge two poles with a shorting bar.* **Do not buy a 접지 부스바** — a grounding
> busbar tidies earth wires and is not a 1-in-2-out power joint.
>
> **It is a panel part, not an automotive one.** Screw terminals on a vehicle need the screws
> locked — threadlocker or star washers — and the cable strain-relieved to a bracket, *which this
> page already requires of every terminal and which is what kills hand-built boards.*
>
> **Check `85 · 86` on the body before assuming they are interchangeable.** A bare coil is not
> polarised and either way round works; **a relay with an internal flyback diode is**, and the
> markings say which. *Nothing drives this coil but a mechanical contact, so it needs no diode of
> its own — unlike the four MUX coils, which are switched by a MOSFET and each carry a `1N4007`.*

> [!IMPORTANT]
> **The contactor coil runs off the LOGIC battery, not the traction pack**
>
> The obvious choice is the traction pack — the thing the contactor is cutting. **It is the wrong
> one, and the reason is brownout.** Under a stall the pack sags; if the coil hangs off it, the sag
> drops the contactor, which cuts traction, which **removes the load and restores the voltage**,
> which re-closes it. **That is a chatter loop, and it is worst exactly when the vehicle is in
> trouble** — which is also when [§5 brownout](../design/safety.md#5-power-rail-isolation-and-brownout-protection)
> is already watching.
>
> The logic battery does not sag with motor load, so the contactor holds or drops cleanly.
>
> **State the cost rather than hide it: with no logic battery the vehicle is dead, not a stock
> toy.** The contactor is upstream of the relay MUX, so an unpowered coil means no traction at all
> even though the MUX has correctly fallen back to STOCK. For a vehicle thirteen students handle
> that reads as a feature — **it cannot be driven with the DBW system unpowered.** Returning it to
> factory condition means unbolting the contactor, which is one connector and is already what
> [§2.8](02-mechanical.md#28-confirm-reversibility) describes.

> [!WARNING]
> **Put the button's two NC contacts on DIFFERENT contact blocks — one each**
>
> The `MRE-RR2R` ships as a head plus **loose stacked contact blocks**, so which contact sits on
> which block is **your assembly decision, not the vendor's.** Confirmed on arrival 2026-10-20.
>
> The two tasks above are carried by the two NC contacts. **Put both on the same block and a single
> loose terminal screw, or one cracked block, takes out both at once** — a common-cause failure in
> the one device whose whole job is not to have one. Split across blocks, a block failure still
> leaves one function intact.
>
> Label each block's terminals on the body in permanent marker as you assemble. You will be wiring
> this weeks later, and a guess here is not a guess you find out about on the bench.

**Relay MUX — four 5-pin SPDT relays per vehicle, not two DPDT.** Two poles per motor circuit × two motor circuits. *(The design was written as "two DPDT"; [#7](../order-log.md) bought twelve 5-pin SPDT for three vehicles, which is the same function in the parts that are actually on the shelf. The count is what somebody wires, so the count is what this page states.)*

- **NC (normally closed) contacts** → stock controller drives the motors. This is the state
  when the coil is de-energized, which is the **default**.
- **NO (normally open) contacts** → the motor driver drives the motors. Coil energized = DBW mode.
- **Flyback diode across every coil**, oriented correctly. A relay coil without a flyback
  diode will eventually kill the transistor driving it, and that failure can leave the MUX
  in an indeterminate state.
- Drive the coils from the **logic** rail through a logic-level MOSFET/transistor, so any
  logic-rail collapse drops the coil.

> [!NOTE]
> **Default de-energized = STOCK is the whole safety story**
>
> Every failure direction leads back to the factory-controlled vehicle: E-stop, logic
> brownout, a pulled connector, a dead Teensy. If you wire the relays inverted — energize for
> STOCK — you invert the entire failsafe analysis in
> [safety.md](../design/safety.md). Check this twice.

### Which relay is which — and wire by the numbers moulded on the body

`K1`–`K4` are this page's designators and they appear nowhere on the hardware.
**Write them on the sockets in permanent marker as you assemble**, the same rule as the E-stop
contact blocks above, and for the same reason: twelve identical relays across three vehicles, and
the person wiring them is not the person who read this table.

| Relay | Carries | `30` COM | `87a` NC → STOCK | `87` NO → DBW |
|---|---|---|---|---|
| **K1** | steering tap, lead **A** | steering motor A | stock ECU steering A | driver `M1`, terminal A |
| **K2** | steering tap, lead **B** | steering motor B | stock ECU steering B | driver `M1`, terminal B |
| **K3** | throttle tap, lead **A** | drive motors A, paralleled | stock ECU throttle A | driver `M2`, terminal A |
| **K4** | throttle tap, lead **B** | drive motors B, paralleled | stock ECU throttle B | driver `M2`, terminal B |

All four coils sit on **one bus** — see the
[relay-driver board](../images/relay-driver-board.svg) for the driver side: the four coils in
parallel across the E-stop-fed logic feed and a single `IRLZ44N` pulling all four low sides. The
coil is the same circuit on every relay; **only the contacts differ, and that is what this table
is for.**

**The numbers are DIN automotive relay terminals, not a part number:** `30` is the common input,
`87` the **normally-open** output, `87a` the normally-closed one, and `85 · 86` the coil. *So the
contactor's "`30→87`" means the traction current enters at `30` and leaves at `87` — a contact
that is closed ONLY while the coil is energised, which is de-energise-to-safe stated in terminal
numbers.* The contactor is a **4-pin** relay and has no `87a`; the four MUX relays are **5-pin**
and use both. `#8a` and `#8b` are this repo's part codes, not markings on the part.

`30 · 87 · 87a · 85 · 86` are **moulded into the relay body**, confirmed on arrival
([#7](../order-log.md)). Wire to those numbers, not to pigtail colour: #7's `RV-90` sockets put
visibly heavier wire on the contacts than on the coil pair, which is the right arrangement, but
**which colour lands on which contact is the socket maker's choice and has to be rung out** with a
meter rather than assumed. Terminal `A`/`B` on the driver is likewise whatever its silkscreen
says — the pairing is what matters, not the letter.

> [!WARNING]
> **Do not cross a pair — and this is the fault that STOCK mode cannot show you**
>
> Both poles of a pair must keep the same motor lead on the same side. If `K1` carries lead A but
> `K2` has its `87a` and `87` swapped, then **STOCK drives the motor one way and DBW drives it the
> other.** Because the NC side is still wired straight through, **the parent remote keeps working
> perfectly** — so every check that happens before the first DBW command passes.
>
> It surfaces as steering that runs *away* from the correction instead of toward it, on the first
> closed loop, which is the worst possible moment to find a wiring error.
>
> It is recoverable by flipping a sign in firmware. **Do not.** The AS5600 sign convention, the
> odometry sign and [§3.7](#37-relay-mux-bench-test-procedure)'s bench test all assume the two
> modes agree about which way is forward. Fix the wire.

**Coil polarity — pick one convention and hold it across all twelve.** Take **`86` to the
E-stop-fed feed** and **`85` to the MOSFET drain**. A plain relay coil is not polarised, so either
way energises it — **the `1N4007` across it is**, and a convention that drifts from relay to relay
is exactly how one diode ends up reversed, which is a short across the logic battery.
*Check the body for a diode symbol first: if the relay has an internal one, `85`/`86` are already
fixed and the convention has to match the part.*

## 3.5 Signal wiring

The motor driver runs in **independent R/C (PWM) mode**. Both signal lines come from the Teensy,
and **both pass through the hardware RC signal MUX** on the way
([dbw.md §4](../design/dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-teensy-as-both-masters)).
Set the DIP switches for R/C mode before wiring. **The switch map differs between boards** —
the configuration for the board actually purchased is recorded with it in the
[Order Log](../order-log.md), including which switch enables the signal-loss stop. Set it from
there and from the board's own manual, not from another board's table.

| Driver input | Normal source | Override source | Motor output |
|---|---|---|---|
| `RC1` | Teensy PWM (via MUX) | RC receiver (via MUX) | motor **Left** — steering gearmotor |
| `RC2` | Teensy PWM (via MUX) | RC receiver (via MUX) | motor **Right** — drive motors, paralleled |

> [!IMPORTANT]
> **R/C mode needs ONE wire per channel. PWM mode needs two, and that is a different mode**
>
> *This comes up from the vendor's Arduino tutorial, which is written for PWM mode and shows
> extra direction GPIOs.* It is correct — **for that mode**, which is not the one this build uses.
>
> | `SW1:SW2` | Mode | Per channel |
> |---|---|---|
> | `00` | **R/C — what this build uses** | **one servo pulse on `RC1` / `RC2`.** 1.5 ms is stop, shorter is one way, longer is the other. **Direction and magnitude are both in the pulse width** |
> | `10` | PWM | **two pins:** `AN1`/`AN2` carry the PWM magnitude and `IN1`/`IN2` carry a **digital direction** — four pins for two channels |
> | `01` | Analog | `AN1`/`AN2`, a voltage |
> | `11` | Serial | `IN1` |
>
> **`SW3:SW4 = 11` (independent both) is the manual's own recommendation for microcontroller
> control**, and it is what the [Order Log](../order-log.md#L122) records. *Terminals are labelled
> `RC1`/`RC2` on the board — `S1`/`S2` is Sabertooth naming and this page used it until
> 2026-11-05.*
>
> **The MUX is why R/C mode is not a convenience.** A hardware signal multiplexer switches *servo
> pulses*; it cannot select between a direction GPIO and a receiver. **PWM mode would cost the
> override path**, which is the thing D3 was adopted on.

> [!CAUTION]
> **"All eight switches off" is wrong in two places, and one of them mixes the motors together**
>
> | Switch | Set | Why |
> |---|---|---|
> | `SW1` `SW2` | **`0` `0`** | R/C input mode |
> | `SW3` `SW4` | **`1` `1` — ON** | **independent both.** The manual's own words: *"Recommended this mode if controlled using Microcontroller"* |
> | `SW5` | **`0`** | exponential OFF — response linear in the pulse width |
> | `SW6` | **`0`** | centre calibrated at power-up; **100 ms signal-loss stop** |
> | `SW7` `SW8` | **`1` `0` — SLA** | battery monitor. The pack is an **`Aroma 6-FM-4.5`, 4.5 Ah sealed lead-acid** — `NON-SPILLABLE`, `Pb`, label read 2026-11-05 |
>
> **`SW3:SW4 = 00` is MIXED, and on this vehicle that is not a degraded mode, it is a wrong one.**
> The manual: *"the motor speed is controlled by channel `RC1` and direction is controlled by
> channel `RC2`"* — tank mixing, for a transmitter's two sticks. **Here motor Left is the steering
> gearmotor and motor Right is the traction pair**, so a throttle command would drive the steering
> motor and a steering command would drive the wheels. *It is the one setting that silently
> redefines what both outputs mean.*
>
> **`SW7:SW8 = 00` selects LiPo**, which nothing on this vehicle is — the logic pack is LiFePO₄ and
> the traction pack is the chassis's own. **No document records the traction pack's chemistry**,
> so this is a label to read before the switches are set: `10` if it is the usual sealed lead-acid,
> `11` to turn the monitor off and leave low-voltage protection to the pack.
>
> *Five off, three on. Not eight off.*
>
> **The monitor warns and does not cut.** The manual is explicit: on under-voltage the error LED
> blinks three times but *"the power to the motor will be maintained and will not be cut out."*
> **So nothing on this vehicle protects the traction pack from being flattened** — that is a
> person's job, and deep discharge is what kills a lead-acid pack. *Setting it to `10` costs
> nothing and makes the warning mean something; setting it to `00` would have it warn at LiPo
> thresholds on a pack that is not LiPo.*

> [!NOTE]
> **"Servo pulse" is the signal format, not the motor — the motors are brushed DC throughout**
>
> A **servo pulse** is the RC convention: a pulse repeated about every 20 ms whose **HIGH time**
> carries the value — **1.0 ms one way, 1.5 ms stop, 2.0 ms the other way.** It is named after
> hobby servos because they use it, but RC speed controllers and this driver read the same format.
> **Nothing in this vehicle is a servo.**
>
> **It is not the same thing as PWM speed control**, and the difference is which part of the
> waveform means something: *a servo pulse carries its value in the **width** of one pulse, and the
> duty ratio is incidental; PWM carries its value in the **duty ratio**.* That is exactly why one
> wire can mean "full reverse" — **a value below centre is not a smaller duty, it is a shorter
> pulse** — and why PWM mode needs a second pin to say which way.

> [!NOTE]
> **Why not packetized serial?**
>
> Single-master packetized serial was briefly adopted — it gives exact, high-rate commands
> and would close the actuation-rate question outright. It was **reverted** because every
> available RC signal multiplexer switches *servo pulses*, and none can select between a
> serial stream and RC PWM. Packetized serial and the RC signal MUX are mutually exclusive,
> and the MUX is the condition D3 was adopted on. See
> [dbw.md §4](../design/dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-teensy-as-both-masters).
>
> The consolation: in R/C mode the driver has a signal-loss timeout. **It is not inherent and it
> is not free — `SW6` turns it off**, which is why the [Order Log](../order-log.md#L122) calls that
> switch the highest-consequence item in the whole substitution.
>
> | `SW6` | Behaviour, from the board's manual |
> |---|---|
> | **`0` — set it here** | centre point calibrated at power-up; **loss of signal for 100 ms stops the motor** |
> | `1` | centre fixed at 1.5 ms, **timeout DISABLED — the motor keeps running at its last speed** |

> [!CAUTION]
> **`SW6 = 0` calibrates the centre at power-up, so what is on `RC1`/`RC2` at that moment becomes
> "stop"**
>
> The board's manual says it twice over: *the RC transmitter must be ON before the driver is
> powered up*, and with `SW6 = 0` *the centre point is calibrated upon power up.* **Whatever pulse
> is present then is what the driver will afterwards believe means zero.**
>
> **So the power-up order is part of the design, not a habit:** receiver on, **Teensy already
> emitting 1.5 ms on both lines**, MUX settled — *then* the driver. Power the driver first and a
> neutral command can come out as a creep, or a real command as neutral, and **neither announces
> itself until the wheels are on the ground.**
>
> **The board also refuses to start without a valid stop**, which is the other half of this: the
> manual's first safety feature is *"every time SmartDriveDuo-30 is powered up, the input data
> must be 'stop'"*, and otherwise the **error LED blinks twice**. *So the two failure shapes are
> different and both worth knowing: **no signal at power-up → it will not run, error LED 2 blinks**;
> a steady but wrong pulse at power-up → `SW6 = 0` adopts it as the centre and **every later
> command is offset by that error**.*
>
> *Write the order into the bring-up checklist before the first powered test, and give the Teensy
> firmware a startup state that emits neutral before anything else
> ([§4](04-firmware.md#the-pin-assignment-the-one-table-that-must-be-frozen-before-an-iron-is-hot)).*

**Signal connections to make:**

| From | To | Notes |
|---|---|---|
| Teensy PWM out ×2 | RC signal MUX **master** inputs | Servo-style pulses — steering and throttle |
| Absolute angle sensor — **AS5600** | Teensy **I²C** (SDA/SCL) | **3.3 V from the Teensy's own pin, not from the logic rail** — the logic rail is 5 V and the AS5600 is a 3.3 V part. Address is fixed at `0x36`, which is fine because the drive side went to Hall latches, leaving one per bus |
| Drive encoder A/B — **2 × DRV5013 Hall latch** | Teensy **hardware quadrature decoder** pins | Not software interrupts — the Teensy has 4 dedicated QDC channels. **The latches are OPEN-DRAIN: each output needs a pull-up to 3.3 V.** Without them the decoder sees a line that never rises, which looks exactly like a dead sensor |
| ~~Steering motor encoder A/B~~ | — | **There is none.** The stock steering gearmotor has no shaft encoder ([dbw.md §2.1](../design/dbw.md#21-actuator)), so the auxiliary incremental channel ADR B specifies does not exist on this vehicle and stall detection moves to the absolute sensor |
| RC receiver **RC serial (i-BUS)** | Teensy hardware serial RX | Layer A override (closed-loop). **The Teensy 4.1 is NOT 5 V tolerant — meter the i-BUS idle level before it touches a serial pin.** The receiver runs on 5 V; if its signal swings to 5 V it needs a divider or a level shifter. One wire, one meter, one minute, and the alternative is a dead pin on a board that is soldered in |
| RC receiver **MUX channel** | Hardware RC signal MUX select | Layer B override — see below |
| RC receiver PWM out ×2 | RC signal MUX **slave** inputs | Emergency path |
| Signal MUX outputs ×2 | Motor driver **S1** and **S2** | Whichever source the MUX selects |
| **E-stop sense** — divider off the coil supply | Teensy digital input | **Not a safety function; it is what makes the *resume* deliberate.** High = authority chain energised. Tap the node the button's NC contacts feed, through a divider to ≈2.3–3.0 V. See the caution below |
| Teensy **USB** | Laptop | micro-ROS — carries **command *and* feedback** |

> [!CAUTION]
> **Give the Teensy USB a direct laptop port, not a hub**
>
> This single link carries the steering setpoint as well as the feedback. A dropout removes
> the setpoint and drops the vehicle to `ESTOP`
> ([failsafe row 2](../design/safety.md#2-failsafe-matrix)). That is the safe behavior, but a
> flaky cable or a marginal hub becomes a vehicle that stops repeatedly. Use a good cable and
> a direct port, and log 30 minutes of session stability at
> [bring-up Stage 0](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first).

### 3.5.2 Sensor runs — both are long, both pass a motor, neither is 5 V

![Two sensor runs to the Teensy: two Hall latches on the drive hub with 10 k pull-ups and 1 nF at the Teensy end, and the AS5600 on I2C at the kingpin with twisted pairs and 4.7 k pull-ups; below, the two-stage build of breadboard on the bench and soldered perfboard on the vehicle](../images/sensor-wiring-and-build.svg)

**Four conductors each, and the sensors take their 3.3 V from the Teensy's own pin.**

| | Drive | Steering |
|---|---|---|
| Part | 2 × `DRV5013` Hall latch | `AS5600` |
| Mount | printed bracket clamping the **gearbox housing nose**, sensing radially | chassis bracket facing the **magnet cap on the kingpin bolt** |
| Conductors | **3.3 V · GND · A · B** | **3.3 V · GND · SDA · SCL** |
| At the Teensy | two pins of **one hardware QDC** | I²C, address fixed `0x36`, **one device on the bus** |
| Must add | **10 kΩ pull-up on A and on B** | **4.7 kΩ pull-ups**, parallel to the breakout's own |

> [!WARNING]
> **The latch output is open-drain. Without a pull-up the line never rises — and that does not look
> like a missing resistor, it looks like a dead sensor.**
>
> Put both pull-ups **at the Teensy**, not at the sensor. Add **1 nF from each output to ground**
> there as well — **not 100 nF**: with 10 kΩ that is a 1 ms corner, and a count at walking pace is
> only about 11 ms, so it would round the edges the quadrature decoder depends on. **1 nF gives
> 10 µs** — enough to kill PWM pickup, fast enough to keep the edge square.
>
> **What the 1 nF is actually for.** A 10 kΩ pull-up on an open-drain output is a **high-impedance
> node**, and this one runs a metre alongside leads carrying PWM'd motor current. Capacitive
> coupling puts spikes on it, and **the quadrature decoder cannot tell a spike from an edge** — it
> counts it. The counts then drift in a way that looks like wheel slip or a mechanical fault, which
> is the expensive way to find a missing ₩4 capacitor. **Any 0.5–1.5 nF part does the job**, so
> tolerance and voltage rating are irrelevant; fit them from the start rather than waiting to see.

**Cable treatment, and all three are free.** **Twist each signal with a ground return** — A with
GND, B with GND, SDA with GND, SCL with GND — because the return path is what makes a long logic
run quiet, and a loose bundle beside a motor lead is an antenna. **Route away from the motor leads**
and cross at 90° where they must meet. **Ground at the star point only**: the sensor grounds go back
to the driver's star, not to a convenient chassis screw.

> [!TIP]
> **I²C is the link that will misbehave first — and the escape hatch is inside the chip**
>
> I²C was designed as a *board-level* bus. This run is about a metre, from a front kingpin to a box
> in the bay, past a motor. **Run it at 100 kHz, not 400.**
>
> If it proves flaky, the AS5600's **`OUT` pin can be configured as a PWM output** instead of
> analog: one wire, timing-based, and far more robust over a metre of cable — **a corrupted bit
> becomes a slightly wrong angle rather than a hung bus.**
>
> **Bench it on I²C and keep PWM in reserve.** Switching it over is an I²C register write, so the
> bus has to work on the desk first. You need it exactly once — to turn itself off.

#### Terminal-block and breadboard count — worked out rather than estimated

**Terminal blocks, per vehicle. Count WAYS, not blocks.**

| Board | Connection | Ways |
|---|---|---:|
| Signal | Drive sensor — 3.3 V · GND · A · B | 2 × 2-pin |
| Signal | Steering sensor — 3.3 V · GND · SDA · SCL | 2 × 2-pin |
| Signal | 5 V power in | 1 × 2-pin |
| Signal | **Gate out + E-stop sense in** | **1 × 2-pin** |
| Relay | **Gate in + E-stop sense out** | 1 × 2-pin |
| Relay | 12 V + GND in | 1 × 2-pin |
| Relay | Four relay coils, a pair each | 4 × 2-pin |
| | **Per vehicle** | **12 × 2-pin** |
| | **Fleet** | **36 × 2-pin** |

> **Those two rows said "Gate + GND" until 2026-11-05, and that was wrong in both directions.**
>
> **No GND belongs on that block.** The relay board's ground already returns to the star on its
> 12 V terminal, carrying the whole 600 mA of coil current; a second ground conductor up to the
> Teensy would be a parallel path — a loop, which is the thing
> [§3.5.3](#353-build-the-circuit-twice-and-not-for-the-reason-it-sounds-like) forbids one page
> earlier. *What you accept instead is the IR drop in that single wire: 600 mA × ~0.011 Ω
> (1.5 mm² over a metre) ≈ **7 mV**, against a worst-case `Vgs(th)` of 1.0 V. Under a percent.*
>
> **And the way it took was needed by something else.** The **E-stop sense divider sits on the
> relay board** — it is tapped off the coil feed ([§3.4](#34-wire-the-e-stop-and-mux-first)) — and
> its output has to reach a Teensy input, **but no terminal in this count carried it.** *The same
> omission as the gate-out way found the day before, one board over: a signal that crosses between
> the two boxes, counted at neither end or at only one.*
>
> **Swapping `GND` for `SENSE` closes both and leaves the count alone**, because the ground was
> never supposed to be there and the sense line always was.

> **This table said 11 and 33 until 2026-11-05, and the figure below it said 12 and 36.**
> The missing way is the **gate leaving the signal board.** The gate line crosses from the logic
> box to the power box, so it needs a terminal at **both** ends — the old count had it arriving at
> the relay board and never departing. *The recount was done when the perfboard transfer was worked
> out, and it reached the figure and the Order Log and not the table beside them.*

> **What is actually in the drawer: thirty 2-pin and ten 3-pin — pieces, not packs** (counted
> 2026-11-05, closing a question open since the quote, because the listing sells 10개 단위).
>
> **36 ways needed, and only 30 of them can be 2-pin.** The last six take a 3-pin with one way
> left unused. So the margin is four blocks — **and all four are 3-pin. There is no spare 2-pin at
> all.**
>
> **That matters at layout, not at reorder.** Replacing a cracked 2-pin with a 3-pin costs
> **5.08 mm of extra board width** in a footprint drawn for a 2-pin, and the relay board is a
> 50 × 80 carrying six of them. Leave the terminals a lobe of slack on that edge. *A 2-pin is
> ₩600 and will never justify a carriage of its own; the fix is the layout.*

> **The 3-pin is the less useful part, which is the opposite of what the first estimate assumed.**
> Both sensor cables carry **four** conductors, and four does not fit a 3-way — so they take two
> 2-pin blocks each. **3-pin only earns its place where three wires genuinely travel together**,
> and on this build that is the servo-style runs to the signal MUX, which use pin headers instead.
>
> **The PWM outputs and the i-BUS line do not get terminal blocks at all** — they are servo
> connectors and belong on 3-pin headers, which is what the receiver and the Pololu MUX already
> expect.

**Breadboards: two half-size per bench station, and none ever goes on a vehicle.**

| Where | What sits on it |
|---|---|
| **Teensy end** | The Teensy, the two 10 kΩ pull-ups, the two 1 nF, the 4.7 kΩ I²C pair |
| **Sensor end** | Both TO-92 Hall latches and the AS5600 breakout, so magnets can be waved and rotated **away from the Teensy** |

> **One board is enough at the Teensy end.** A half-size board is 30 columns and a Teensy 4.1
> occupies 24 — but **each pin column still has four free holes**, which is where the pull-ups,
> capacitors and jumpers go. *An earlier note here said to clip two together; that was
> over-cautious and the second board is better spent at the sensor end.*
>
> **A third board per station is worth it if drive and steering are to be bench-tested in
> parallel** rather than one after the other. With thirteen students on three stations, that is
> usually what happens.

### 3.5.3 Build the circuit twice, and not for the reason it sounds like

**Yes, use a solderless breadboard — on the bench.** This page warned against breadboard *on the
vehicle* and said nothing about the bench, which are different claims and only one of them is true.

**On the bench it earns its place:** prove the pull-ups and the QDC counts before anything is
soldered, find the AS5600 on the bus and tune its AGC with the magnet in a vice, and **try pin
assignments freely** — they are not fixed yet, and changing a soldered board costs an evening where
changing a breadboard costs nothing.

**What it must never carry, even on the bench: relay coil current and the MOSFET gate pulldown.**
600 mA through spring clips is at their limit, and an intermittent contact on that pulldown floats
the gate — which chatters the relays between STOCK and DBW. **So bench the *signal* side on a
breadboard and the *authority* side on the perfboard you will actually fit.** Build that one first.

#### The bench layout, hole by hole

![Three 400-point half-size breadboards drawn at 30 columns by 10 rows: board A with the Teensy straddling the centre channel, its USB end at the left so the Vin/GND/3V3 edge is the upper row and the pin 0 edge the lower, rail-bridge jumpers carrying its 3V3 supply down to the lower rails, 10k pull-ups and 1nF on the quadrature columns below and 4.7k on the I2C columns above; board B with both Hall latches; board C with the AS5600](../images/breadboard-layout.svg)

*Drawn to the board actually ordered — `SZH-BBAD-005`, **30 columns × 10 rows + four rails = 400
tie points**. Rows A–E go unused; a half-size board has far more holes than this needs.*

> [!WARNING]
> **The Teensy in this figure was mirrored until 2026-11-05 — a bottom view drawn as a top view**
>
> It had `GND · 0 · 1` on the **upper** row and `VIN · GND · 3V3 · 20 · 19 · 18` on the lower, with
> the USB end at the left. **That combination cannot happen.** With USB to the left the pinout card
> rotates counter-clockwise, which puts the `Vin · GND · 3V3 · 23 · 22 · 21 · 20 · 19 · 18` edge on
> **top** and the `GND · 0 · 1 · 2 …` edge below — which is what
> [the signal board figure](#where-it-all-sits-on-the-signal-board) shows and what the board in
> hand does.
>
> **Anyone wiring board A from the old figure would have put every component on the wrong side of
> the Teensy**, and the first symptom would have been two dead quadrature channels — which reads
> exactly like a dead sensor, the failure this section already warns about twice.
>
> *The figure was internally consistent, which is why it survived: every component agreed with
> every other component, and all of them agreed with a mirror. It took holding a Teensy next to a
> second, independently drawn figure to see it. **That is the argument for drawing the same thing
> twice** — not redundancy, but a second chance to disagree.*

> [!NOTE]
> **Both Hall latches are on the SAME hub — one wheel is instrumented, not two**
>
> The pair sits **6.80 mm apart on one carrier**, a quarter cycle out of step. **That is what gives
> direction.** A single latch counts edges but cannot tell forward from reverse, and a vehicle that
> cannot tell those apart has no odometry worth having.
>
> **`A` and `B` are two sensors on one wheel, not one sensor on each of two.**

**Board A holds three component pairs and nothing else:** `2 × 10 kΩ` from the pin-0 and pin-1
columns up to the `+` rail, `2 × 1 nF` from the same columns down to `−`, and `2 × 4.7 kΩ` from the
pin-18 and pin-19 columns to `+`. **The 3.3 V comes from the Teensy's own 3V3 pin** — there is no
other 3.3 V source in this build, and everything on it shares that one pin's budget.

> [!CAUTION]
> **Fit the two rail bridges, or the pull-ups do nothing**
>
> A breadboard's **upper and lower rail pairs are separate strips.** The Teensy's `3V3` and `GND`
> pins are on its **upper** edge and therefore feed only the upper rails — but the 10 kΩ pull-ups
> hang off pins 0 and 1 in the **lower** half and reach for the **lower** `+` rail, which has no
> source at all.
>
> **Two jumpers fix it:** upper `+` to lower `+`, upper `−` to lower `−`. Without them the latch
> outputs float, and **a floating open-drain output reads exactly like a dead sensor** — the same
> failure the pull-ups exist to prevent.
>
> *Caught in review on 2026-10-27; the first version of this figure had the bridges missing.*
>
> *Which edge is which was corrected on 2026-11-05 — see below. The jumpers were always right;
> the reason given for them was upside down.*

**Three boards, not two — drive and steering get their own.** They become **two harnesses at two
ends of the vehicle**, a rear hub and a front kingpin, so splitting them on the bench means each
board transfers to its own section of perfboard. It also lets two people work in parallel, one
waving a magnet past the latches and one rotating one in front of the AS5600.

**Nothing extra had to be bought for it:** **nine breadboards is three stations × three boards**,
which is what the order carries, and **five AS5600s covers it because the bench unit is the one you
then fit to that vehicle** — which is better practice anyway, since AGC is tuned per part.

> [!CAUTION]
> **The TO-92 pin order is not guessable, and reversed `V`<tspan></tspan>`CC`/`GND` destroys the part**
>
> The figure draws legs 1-2-3 as **VCC · GND · OUT**, which is the common arrangement — **read the
> `DRV5013` datasheet and confirm it before inserting anything.** That is what the fourteen spares
> are for, and it is a cheaper lesson here than on a soldered board.
>
> **Keep them in their labelled bag until each one is fitted.** TI marks a TO-92 body with an
> abbreviated code, so loose parts are unidentifiable and `BC` looks exactly like `AG`. And **bend
> the legs out to 2.54 mm** — they leave the package closer together than a breadboard pitch.

![Companion panel figure: board and AS5600 counts, what the VUSB to VIN cut does to USB power, the five-step bring-up order, and the checks to make before any wire goes in](../images/breadboard-procedure.svg)

**Prove it in this order, because each step fails for a different reason.**

1. **Power only.** 5 V at `VIN`, then meter the `+` rail **on board B**: 3.3 V. Not there → the
   fault is a jumper, not a sensor.
2. **Latches, with a meter, before any code.** Probe each `OUT` against GND and pass a magnet by.
   It must snap between **0 V and 3.3 V and stay there** when the magnet leaves — *that is what
   makes it a latch*. If it falls back on its own you have a switch, and the whole quadrature
   scheme is wrong. **Flip the magnet to reset it.**
3. **I²C scan.** `0x36` must appear, and nothing else — one device per bus is the design.
4. **AGC.** Read `0x1A` at the working gap, tune to mid-scale, and **write the gap down**: it is
   the number the other two vehicles are built to.
5. **Counts last.** Only now bring up the decoder and move a magnet past both latches in sequence.
   Counting up one way and down the other is the **first proof the `(n + ½)` spacing is right**,
   and it is cheap here and expensive on a wheel.

**Steps 1–3 need no firmware beyond a scan sketch.** If something is wrong, it is wrong before any
code can be blamed for it.

> [!IMPORTANT]
> **Cut `VUSB`–`VIN` before the first bench session that involves a UBEC**
>
> After the cut the laptop **still programs the board and still carries micro-ROS — it just cannot
> power it.** 5 V comes from a UBEC into `VIN`, on the bench and on the vehicle alike, which is the
> point: the cut exists so the laptop's 5 V and the UBEC's 5 V never meet and push current into each
> other through the Teensy. *"We'll do it later"* is how they meet.
>
> **A Teensy that seems dead on USB after the cut is working correctly.** Tape a note inside the
> parts box — somebody will meet this at eleven at night.
>
> **Beep the two boards' `−` rails together before powering up.** A missing ground reads as a dead
> sensor, and on the vehicle this same joint becomes the star at the motor driver.

#### 3.5.4 Transferring to perfboard — three boards become one

![Mapping from the three bench breadboards to what is actually built: only the Teensy board becomes a perfboard, the two sensor boards disappear because the sensors live on the ends of cables, and a relay-driver board that was never breadboarded appears; plus the signal perfboard layout with each passive labelled by the signal it serves — 10 k and 1 nF on drive A and B, 4.7 k on SDA and SCL — the build order, and the cautions](../images/perfboard-transfer.svg)

> [!IMPORTANT]
> **The three bench boards do not become three perfboards. Two of them disappear.**
>
> The bench had three boards for one reason — **you have to be able to wave a magnet at a sensor.**
> The vehicle has no such need: the latches sit on a printed bracket at the hub and the AS5600 on a
> chassis bracket at the kingpin, each on the end of a **1 m cable whose four wires land on a
> terminal of the signal board.** There is nothing to put on a board at either end.
>
> | Bench | Vehicle |
> |---|---|
> | Board A — Teensy | **Signal perfboard**, `GA2 80 × 80`, in the logic box |
> | Board B — Hall latches | *no board* — a bracket at the hub, on a cable |
> | Board C — AS5600 | *no board* — a bracket at the kingpin, on a cable |
> | *(never breadboarded)* | **Relay-driver perfboard**, `GA6 50 × 80`, in the power box |

**Build order, and the first step is not a component.**

1. **Female headers first**, with the Teensy plugged into them to hold them square. Tack two
   corners, check it sits flat, then do the rest.
2. **Run the 3.3 V and GND buses as continuous bare wire.** A breadboard gives you the rail; on
   perfboard **an island that never got joined is the classic fault** — and it is the same mistake
   the missing rail bridges were.
3. **Passives, each beside the pin it serves.** A 1 nF at the far end of a 60 mm track is doing
   much less than one at the pin.
4. **Terminals at the edges**, oriented so each cable leaves towards where it is going.
5. **Continuity and short checks.** 6. **Only now fit the Teensy.**

**Point-to-point with insulated wire, soldered both ends.** Long solder-bridge runs between
adjacent pads crack on a vehicle that vibrates.

> [!NOTE]
> **Six passives, and the figure names the SIGNAL rather than the pin**
>
> | | | |
> |---|---|---|
> | **2 × 10 kΩ** | pull-up to 3.3 V on **drive A and B** | the `DRV5013` output is open-drain; without them the quadrature decoder sees a line that never rises |
> | **2 × 1 nF** | **those same two lines**, down to GND | a motor-edge spike on a 10 kΩ node is a count |
> | **2 × 4.7 kΩ** | pull-up to 3.3 V on **SDA and SCL** | parallel to the AS5600 breakout's own |
>
> **The pin numbers are not here because they are somewhere else** —
> [one table in `04-firmware.md`](04-firmware.md#the-pin-assignment-the-one-table-that-must-be-frozen-before-an-iron-is-hot),
> which the bench layout and this board **both** use. *If the two differed, the bench would prove
> nothing about the board.* **On a breadboard you move a wire; on perfboard you desolder**, so the
> table is settled and frozen before anything is soldered.
>
> *Corrected 2026-11-05: this page previously said the numbers "do not exist yet". They did — a
> provisional set had been in `breadboard-layout.svg` since it was drawn, and no document carried
> them. That is the defect, not the silence: a number that lives in exactly one figure is a number
> nobody can check.*

#### Where it all sits on the signal board

The figure above says what this board *is*. **It does not tell you where to put anything** — the
Teensy is a dashed box and the passives are squiggles at no particular hole. This one does, on the
same 29 × 29 grid the GA2 actually has.

![Signal perfboard placement on a 29 by 29 hole grid with four plated corner mounting holes and a
one-hole margin: a socketed Teensy 4.1 lying across the middle with its USB end to the left and its
assumed pin order printed along both rows; a 3.3 V bus above it fed from one 3V3 pin and a second
3.3 V bus below fed from the other, a GND bus below that and a GND spine up the right edge; short
bare-wire stubs soldered to the pads of pins 0, 1, 18 and 19 so each can carry more than one
connection; two 4.7 k pull-ups up to the upper 3.3 V bus from the I2C stubs; two 1 nF down to GND
and two 10 k up to the lower 3.3 V bus from the drive stubs, the 10 k on the reverse side because
each crosses the GND bus; a level-shift position R5 and R6 in the i-BUS line; six screw terminals
along the top and bottom edges and three servo headers whose middle +5 pad is drawn hollow and
marked n/c; and panels on the pin order, the build order and why each passive sits where it
does](../images/signal-board-perfboard-layout.svg)

**Generated** — [`scripts/gen_signal_board_figure.py`](https://github.com/jrkwon/mrider/blob/main/scripts/gen_signal_board_figure.py).
*Edit the script and re-run it; do not edit the SVG.*

> [!IMPORTANT]
> **A socket pad already has something in it, which is why this board has stubs**
>
> On the relay board every part stands between two free holes, so *no two leads in one hole* holds
> everywhere. **Here every passive hangs off a Teensy pin, and that hole is full of the socket.**
> So the rule relaxes to **two things in a hole, never three** — a pad with one wire soldered to it
> is ordinary work; a pad with two is a joint nobody can inspect.
>
> **Pins 0, 1, 18 and 19 each need more than one thing**, so each gets a **stub**: two or three
> holes of bare wire soldered to its pad, giving the pull-up, the cap and the sensor wire a hole
> each. *The generator asserts the two-per-hole rule and circles every doubled pad in the drawing,
> so the builder knows which pads take a second wire before the iron is hot.*
>
> **The two 10 kΩ go on the reverse side.** Each crosses the GND bus on its way to 3.3 V, and the
> board is 양면 so that it can. *The script asserts a part is on the reverse side **exactly** when
> it crosses a bus — a dashed part that did not need to be is a part nobody can reach with an iron
> once the board is in the box.*

> [!NOTE]
> **What the three servo headers are, and why their middle pad is empty**
>
> Each is a **3-pin male pin header, 2.54 mm**, cut from the `1×40` strip on
> [row 122](../order-log.md#L122). *Male, because the receiver and the MUX both terminate in
> female servo sockets.* The order along a servo connector is **signal · +5 · ground**.
>
> **The middle pad is deliberately unconnected, and the reason is the whole point of having two
> UBECs.** This board runs on **UBEC A**; the receiver, the MUX and the driver's signal logic run
> on **UBEC B**. *Tying the header's +5 to this board would join the two rails and undo the
> authority split* — the one that lets a UBEC A failure leave the receiver, the MUX and the driver
> alive. **Signal and ground land here; +5 does not.**
>
> **The two PWM headers go to the MUX's MASTER inputs** — pin 2 steering, pin 3 drive — and the
> **MUX's** two outputs drive the motor driver's `RC1` and `RC2`. *The Teensy never reaches the
> driver directly; that is what makes the RC override a hardware path.*

> [!CAUTION]
> **R5 and R6 are an i-BUS level-shift position, and which one you fit is a measurement**
>
> **The i-BUS signal comes from a receiver on 5 V, and the Teensy 4.1 is not 5 V tolerant.**
> [§3.4](#34-wire-the-e-stop-and-mux-first) already says to meter the idle level before it touches
> a serial pin — but no figure had anywhere to *put* the answer, so the wire went straight to
> pin 15.
>
> | Metered idle | Fit |
> |---|---|
> | **3.3 V** | **R5 is a wire link**, R6 omitted |
> | **5 V** | **R5 / R6 as a divider** to the measured ratio |
>
> *Two holes reserved now cost nothing. Finding out after the header is soldered and the wire is
> on the pin costs a Teensy — ₩74,250, and the board is in the box.*

> [!NOTE]
> **Three of those connectors are on the board and not on the bench, and that is on purpose**
>
> **The i-BUS header and the two PWM headers appear nowhere in the breadboard layout.** The bench
> rig exists to prove the *sensors* — pull-ups, quadrature counts, the I²C read — with a magnet in
> your hand. **The RC path is not a bench exercise**: it needs a bound receiver, the hardware MUX
> and the motor driver, and it is wired and proved on the vehicle in
> [§3.5.1](#351-hardware-rc-signal-mux-wire-this-it-is-not-optional) and
> [§3.4](#34-wire-the-e-stop-and-mux-first).
>
> **Say it out loud because the omission is invisible:** three connectors on this board are
> soldered without ever having been rehearsed, and **the first time a PWM header is exercised, the
> vehicle can move.** *Drive the gate and the PWM outputs from a bench 3.3 V and a servo tester
> before the driver's `RC1`/`RC2` are plugged in, the same way the relay board's coils are listened
> to before anything is bolted in.*

> [!WARNING]
> **The pin order in that drawing has not been checked against a board**
>
> Every column is computed from the pin order printed along the Teensy. **If that order is wrong,
> the whole drawing is wrong the same way.** *The same arithmetic said this perfboard was 31 holes
> wide and it is 29.* **Hold a Teensy 4.1 next to the figure and read along the edge** — ten
> seconds. If it differs, correct the two lists in the generator and re-run; nothing else moves,
> because nothing else is hand-placed.


> [!CAUTION]
> **The 3.3 V bus is dead until the Teensy is plugged in — and you should still test the board
> without it**
>
> The bus is fed by the **Teensy's own 3V3 pin through the socket**, so a board powered up with the
> Teensy out reads 0 V and **looks broken**. *Same shape as the `VUSB` cut: a correct board that
> looks dead. Both belong on the note taped inside the parts box.*
>
> **Test it with the Teensy out anyway, for shorts.** Meter 3.3 V bus ↔ GND and 5 V ↔ GND. A solder
> bridge found then costs nothing; found later it is being driven by the Teensy's own regulator.

> [!NOTE]
> **Add a 100 nF across each Hall latch's own `VCC` and `GND`, at the bracket**
>
> TI's `DRV5013` datasheet asks for a bypass capacitor close to the device, and **a sensor on the
> end of a metre of cable beside a PWM'd motor is exactly the case it exists for.** Six are needed,
> two per vehicle.
>
> **Soldered at the bracket, not at the board end** — a capacitor at the far end of the cable does
> nothing for the sensor's own supply.
>
> **The 1 nF already bought is not a substitute.** 1 nF across the *signal* line filters pickup;
> 100 nF across the *supply* is a local reservoir. Different jobs, both wanted.

#### Why these capacitors, and why they sit where they sit

![Three capacitors compared: 1000 microfarad across the whole logic rail, 100 nanofarad across one sensor's own supply at the bracket, and 1 nanofarad across one signal line at the Teensy — with what each is across, where it must sit, and what fails without it](../images/capacitor-roles.svg)

**A capacitor is always the same thing — a low-impedance path for fast changes.** What it *does* is
decided entirely by **what you put it across**, and this build uses three.

| | Across | Must sit | Without it |
|---|---|---|---|
| **1000 µF** | the whole logic rail | anywhere on the rail | a current step sags the rail and the Teensy resets |
| **100 nF** | **one sensor's own supply** | **at the bracket** | the latch's supply dips as it switches — a metre of wire cannot deliver fast |
| **1 nF** | **one signal line** | **at the Teensy** | a motor-edge spike lands on a 10 kΩ node and the decoder **counts it** |

**Only the 1 nF is about the signal.** The 100 nF is about the *supply*, and improves the signal
only indirectly — by keeping the part that generates it properly fed. **That distinction is not
academic: it is what decides which end of the cable each one is soldered to.**

> [!NOTE]
> **The circuit works without either of the small two — they are insurance, not function**
>
> What they buy is that the failure they prevent is **one of the hardest to diagnose on this
> vehicle**: a count that is slightly wrong, only while the motor is running, and that looks exactly
> like tyre slip.
>
> **Fit them from the start. Do not wait to see whether they are needed** — by then you are
> debugging a vehicle instead of a bench.
>
> **Specify `0.1 µF / 50 V / 104` and nothing further** — tolerance, dielectric and brand are all
> irrelevant here. The one thing that matters is that it is a **ceramic**: a 마일러 (polyester film)
> part turns up in the same search at a similar price and is the wrong family.

**Four things the breadboard could not teach.** **Pin assignment freezes here** — on a breadboard
you move a wire, on perfboard you desolder, so **finalise the pins at the bench and write them into
[04-firmware](04-firmware.md) before soldering anything.** **Strain relief:** cable movement must
pull on a tie or a bracket, never on a terminal — *this is what kills hand-built boards, not the
soldering but the five hundred tugs a loom gets.* **One ground wire off this board**, to the star
at the motor driver; a second path is a loop and a loop is
[FMEA row 5](../design/safety.md#7-fmea-lightweight). And **standoffs, not loose** — perfboard
flexes, and a flexing board works a socketed Teensy loose.

![Relay-driver board schematic: 12 V through the E-stop NC contact to four relay coils in parallel, each with a 1N4007; the low sides joined to an IRLZ44N drain; gate driven from a Teensy pin through 100 ohms, with the 10 kilohm pulldown tapped on the MOSFET side of that resistor; and the sense divider tapped off the coil feed. Coils are labelled K1-K4 with the motor lead each one's contacts carry, and 85/86 marked; the contacts themselves are not on this board](../images/relay-driver-board.svg)

> [!WARNING]
> **The relay-driver board has no bench version, and that was deliberate**
>
> It carries 600 mA of coil current and the MOSFET gate pulldown, and **neither may ever sit in a
> spring clip.** So it goes from schematic straight onto perfboard — **solder the 10 kΩ gate
> pulldown first, before the MOSFET**, because a floating gate chatters the relays between STOCK
> and DBW. **Then meter gate-to-GND for 10 kΩ before a single coil is connected.**
>
> *De-energise-to-safe is a property of that one resistor, so it is tested on its own.* **The
> reading is of the two joints and the two holes, not of the resistor** — a meter can check a
> loose 10 kΩ before it goes anywhere near the board, and cannot check a cold joint or a ground
> lead one pad short of the bus until it is in. **With nothing else fitted, a wrong number has
> exactly one suspect.**
>
> **Corrected 2026-11-05 — which SIDE of the 100 Ω the pulldown taps.** The schematic above drew
> it on the **Teensy side**, where the placement figure below has always had it on the **MOSFET
> side.** The schematic was wrong, and *it contradicted its own build order* — step 1 says
> "pulldown, **gate** to GND, first, alone" and step 2 meters gate-to-GND **before the 100 Ω is
> fitted at all**, neither of which describes a resistor hanging off the terminal. Schematic
> moved to match.
>
> **It is not a cosmetic difference.** On the Teensy side the pulldown stops holding the gate the
> moment anything **between it and the gate** opens — a cracked 100 Ω joint, a lifted pad — and it
> does so *silently*, because the resistor is still fitted and still meters 10 kΩ. On the MOSFET
> side nothing upstream can float the gate. *The cost is 1 % of gate drive to the R2/R1 divider:
> 3.3 V × 10 k / 10.1 k = 3.27 V, against a worst-case `Vgs(th)` of 2.0 V.*
>
> **The generator now asserts the node rather than the neighbourhood.** The old check only asked
> whether the pulldown was *near* the gate, and the wrong version would have passed it.

#### Where it all sits on the board

Because there is no bench version, **the first physical build of this board is also the final
one** — so the placement is worth settling before the iron is hot rather than during.

![Relay-driver perfboard placement on a 29 by 18 hole grid with four plated corner mounting holes, a one-hole margin kept all round leaving 27 by 16: a +12 V bus along row 2, a DRAIN bus
along row 8 joining the four coil low sides, and a GND bus along row 17; four pluggable coil
terminals K1 to K4 between the two upper buses with a 1N4007 beside each, band to +12 V; the
IRLZ44N standing upright with gate, drain and source marked; the 10 k pulldown dropping from the
gate node to the GND bus one hole from the source's own landing; the 100 ohm in series from the
Teensy terminal; and the 10 k / 2.7 k E-stop sense divider on the left, with panels explaining the
single star ground, why the pulldown lives beside the MOSFET, and the build
order](../images/relay-board-perfboard-layout.svg)

**The drawing is generated** — [`scripts/gen_relay_board_figure.py`](https://github.com/jrkwon/mrider/blob/main/scripts/gen_relay_board_figure.py)
holds the layout as a hole-indexed netlist and asserts what a reader cannot check by looking:
**no two leads share a hole**, **every lead is inside the usable ring** rather than merely on
the board, the gate node stays under four holes long, and **the pulldown grounds within one hole
of the MOSFET source.** *Edit the script and re-run it; do not edit the SVG.*

> [!IMPORTANT]
> **The pulldown goes on THIS board, beside the MOSFET — never at the Teensy end**
>
> The gate line crosses from the logic box to the power box. **With the pulldown at the Teensy
> end, cutting or unplugging that wire would leave the gate floating at the MOSFET** — partial
> enhancement, relays chattering between STOCK and DBW, which is the exact failure the resistor
> exists to prevent.
>
> **With it here, a broken gate wire still leaves 10 kΩ tied across gate and source.** Gate low,
> coils dropped, STOCK. *The pulldown is only a failsafe if it is on the far side of every
> connector it is protecting against.*
>
> **Its ground lands one hole from the source's**, so no coil current flows in the copper between
> them. Across a soldered bus that drop is microvolts — this is cheap insurance rather than a live
> hazard — but it is the habit that stays correct the day someone rebuilds the same circuit with
> wire instead of a bus.

**The grid is counted, and divide-by-pitch was over on both sides.** 80 / 2.54 = 31.5 and
50 / 2.54 = 19.7 would give 31 × 19. **Counted end to end 2026-11-05**
([row 122](../order-log.md#L122)): **29 × 18.** The figure draws that, and asserts every lead
into **27 × 16** — a one-hole margin this layout keeps on purpose, so a bus never ends on the
outermost pad.

> [!WARNING]
> **The board is exactly spent, both ways.** The layout runs **rows 2–17 and columns 2–28** —
> sixteen into sixteen, twenty-seven into twenty-seven. **The GND bus sits on the last row of the
> margin and the three buses end on its last column.** Nothing goes beyond, and any later edit
> that wants a row or a column has to take one back from the spacing it already has.
>
> **This is also why a 3-pin terminal cannot stand in for a coil 2-pin here.** At 5.08 mm it spans
> four holes instead of two, so a coil block at row 4 would reach **row 8 — the DRAIN bus**, into
> the very hole that coil's own `85` jumper already occupies. *The spare blocks being all 3-pin is
> a layout fact, and this is its shape on this board.*

> [!NOTE]
> **Dividing by the pitch assumes the pads run to the board edge. They do not.** The array sits
> inside a blank margin, and that margin is the thing the arithmetic had no way to know —
> **4.4 mm** across the width (80 − 28 × 2.54, halved) and **3.4 mm** across the height
> (50 − 17 × 2.54, halved). *Two different margins, neither of them derivable from the other.*
>
> **Those margins are also why the corner holes fit where they do.** A 3.2 mm hole needs about
> that much blank FR-4 — **a board whose pads really did reach to within 1.9 mm of the edge could
> not have carried one.** The photograph and the hole count agree, which is exactly the check the
> derived figure failed.
>
> **Mounting needs no decision at all** — *and an earlier revision of this page got that wrong.*
> **The board ships with four plated corner holes**, in the blank margin outside the pad array
> (photographed 2026-11-05). Nothing is drilled and no pad is spent. *The superseded note reasoned
> from the margin that a corner M3 could not fit; it was deriving the geometry of a part that was
> already on the bench, using the same arithmetic the row count had just caught out.*

**Three rules for the board that goes in.**

1. **The Teensy sits in female headers, not soldered down.** Thirteen students, one bricked
   bootloader, ₩74,250 a board.
2. **Every off-board wire lands on a screw terminal.** A sensor then swaps without a soldering iron,
   and cable movement pulls on a terminal instead of on a solder joint — which is how joints crack.
3. **Pull-ups and the 1 nF live on the board beside the Teensy** — not at the sensor end, not
   spliced into the middle of a loom.

**Two boards, not one:** the signal board in the logic box and the relay-driver board in the power
box, which is the same split as the enclosures and for the same reason.

> [!CAUTION]
> **The assembly consumables were specified in one document and bought in neither**
>
> [§1.2.4](01-bom-sourcing.md#7-8-11-12-14-what-to-actually-buy) calls for perfboard, screw
> terminals and an enclosure for the relay-driver board. **[#7](../order-log.md) bought relays,
> MOSFETs, resistors and diodes and stopped there.** Nothing here is expensive and all of it stops
> work on the day it is missed:
>
> **One 디바이스마트 order covers all of it**, which matters more than any single part number: six
> Coupang sellers would be six carriages on ₩50,000 of goods, and [#6a](../order-log.md) already
> proved this route at ₩2,700 with no fees.
>
> | | |
> |---|---|
> | **만능기판** | 거상인 **`[GA2] 80 × 80 양면` ₩4,300** (signal board — a Teensy 4.1 is 61 mm long, so 50 × 80 is tight once terminals are on) and **`[GA6] 50 × 80 양면` ₩3,500** (relay driver). **Four of each** — a perfboard is the part a student ruins |
> | **Terminal blocks** | EM Tech **`2EDGK+2EDGRC-5.08`**, 2-pin ₩600 / 3-pin ₩900. **Pluggable, not plain screw** — the harness unplugs whole, so a sensor or a box comes out without a screwdriver inside the bay. **Count below: 12 × 2-pin per vehicle, 36 for the fleet — and 3-pin is the *less* useful of the two.** Thirty 2-pin and ten 3-pin arrived; the four spare blocks are all 3-pin |
> | **Headers** | CONNFLY **`핀헤더소켓 Single 1x40 Straight (2.54mm)` ₩530**. A Teensy 4.1 is **24 pins a side**, so one strip cuts a row with 16 to spare — **two per Teensy**. *Not the `적층형` at ₩1,000: its 9.1 mm legs are for stacking shields and only raise the board in the box* |
> | **Bench** | `브레드보드` + `점퍼케이블 세트`. **Two half-size boards per bench station** — one at the Teensy, one at the sensor end. See the count below |
> | **Splicing** | **`NT-DIY 열수축튜브 328세트` ₩3,900.** The [#8a](../order-log.md) splice joins **0.75 mm² (OD ~2.5 mm) to AWG 14 silicone (OD ~4 mm)**, so the tube must shrink from **≥ 6 mm to under 2.5 mm**; 8 sizes bracket that |
> | **Passives** | **`DONGIL HV(E) Ceramic 1000pF` ₩40 / 10** — 1000 pF *is* 1 nF, and it is **through-hole**. The chip parts a search returns are SMD and unusable on perfboard. **4.7 kΩ is already in the 30-value kit** |

### 3.5.1 Hardware RC signal MUX — wire this, it is not optional

![FlySky FS-iA6B feeding the Teensy over i-BUS, the Pololu 2806 signal MUX slave inputs and its select channel; the Teensy feeding the master inputs; the MUX outputs driving RC1 and RC2; and below, the E-stop's two NC contacts breaking the contactor and relay MUX coils while not touching the signal MUX at all](../images/rc-mux-estop.svg)

**The receiver does three separate jobs at once**, which is the thing most people miss:

| From the FS-iA6B | To | Why |
|---|---|---|
| **i-BUS pad** | Teensy serial RX | Layer 1 — closed-loop RC override, commands an *angle* |
| **CH1 · CH2** servo out | signal MUX **SLAVE** | Layer 2 — the raw-effort emergency path |
| **CH5** servo out | signal MUX **SEL** | chooses between them, in hardware |

The **Teensy's two PWM outputs go to the MASTER inputs**, and the **MUX's two outputs go to the
driver's `RC1` and `RC2`**. The MUX and the receiver both sit on **UBEC B**, and **all three grounds —
receiver, MUX, driver — reference the same star**: a servo pulse is a voltage *against ground*, and
two grounds means the driver reads a different number than the one that was sent.

> [!CAUTION]
> **The E-stop does not connect to the signal MUX, and that is deliberate**
>
> There are **two muxes** in this vehicle and conversation calls both of them "the MUX":
>
> | | what it switches | E-stop |
> |---|---|---|
> | **Relay MUX** | motor **power**, **80 A** contacts (70 A was the spec; 80 A arrived), 12 V coils | **drops it** |
> | **Signal MUX** (Pololu) | **servo pulses**, logic rail, selected by an RC channel | **does not touch it** |
>
> The E-stop's two NC contacts break the **contactor coil** (traction power cut) and the **relay MUX
> coils** (authority back to STOCK). The signal MUX stays powered and keeps whatever state it was
> in — **which is correct, because with traction cut and the relay MUX dropped it is driving
> nothing.** Say which mux you mean, every time.
>
> **De-energise-to-safe falls out of this for free.** Both coils are fed through NC contacts from
> the logic battery, so **pressing the button, a dead logic battery, and a broken wire all do the
> same thing.** There is no state in which something must *work* for the E-stop to work — which is
> why the button is wired to coils rather than to anything clever.

> [!IMPORTANT]
> **ADOPTED 2026-10-28 — the E-stop sense wire, because the state machine already required it**
>
> [dbw.md §10.3](../design/dbw.md#103-safety-state-machine) has `E-stop` as a transition **into**
> `ESTOP` and `E-stop released + RC arm` as the only way **out**. Both need the firmware to know,
> and **no wire was ever specified.** Two arcs of a published state machine were unimplementable.
>
> **The practical consequence is concrete.** Both coils are fed through the button's NC contacts, so
> **turning the button to reset re-energises both at once.** The Teensy never noticed anything — it
> has been closing a loop against a sensor that was not moving, **winding up its integrator** — so
> the vehicle **resumes under whatever command was last in flight.**
>
> **Hardware owns stopping; firmware owns not restarting by accident.**
>
> **Wire it as a tap on the COIL SUPPLY, not on a spare contact.** A divider on the node the NC
> contacts feed, into a plain digital input:
>
> ```
> E-stop NC ──┬──▶ contactor coil + relay MUX coils
>             │
>             └──[ 10 kΩ ]──┬──▶ Teensy digital in
>                           │
>                        [ 2.7 kΩ ]
>                           │
>                          GND  (the star)
> ```
>
> | | sense reads |
> |---|---|
> | released, coils live | **high** |
> | pressed | low |
> | **broken wire · pulled connector · blown coil fuse · dead logic pack** | **low** |
>
> **Every failure reads "stopped", which is the conservative direction** — and it senses *whether
> the authority chain is energised*, not merely whether a finger is on the button. **A spare `NO`
> contact would be simpler and worse:** an open circuit would read *"not pressed"*, silently
> restoring the instant-resume behaviour this exists to prevent. The `NO` pair stays spare.
>
> **Pick the divider so the output lands between 2.2 V and 3.1 V** across the pack's whole range —
> **12.0 V flat to 14.6 V on charge.** `10 k / 2.7 k` gives 2.56 V and 3.11 V. **Then meter it
> before the wire goes anywhere near the pin**, which makes the arithmetic moot: the Teensy 4.1 is
> **not 5 V tolerant** and this node starts at pack voltage.
>
> **It must never become a safety function.** The safety is the NC contacts and the coils, which
> work with the Teensy dead.

> [!CAUTION]
> **This is the condition on which the architecture was adopted**
>
> D3 concentrates the steering loop, throttle, override, and arming on one MCU. The
> justification for accepting that is that override is a **wiring property**, not a firmware
> property ([safety.md §1.2](../design/safety.md#12-live-override-inside-dbw-mode-two-layers)).
> A build without this MUX has no independent override and does not match the safety analysis
> the design was approved against.

The MUX sits **between the Teensy and the motor driver**, selecting which source reaches the
motor driver:

```
Teensy output ──▶ MUX input A ─┐
                               ├──▶ MUX output ──▶ Motor driver
RC receiver   ──▶ MUX input B ─┘
                     ▲
RC channel ──────────┘  (select: A = normal, B = emergency)
```

- Power the MUX from the **logic rail**, so it survives an E-stop and a traction brownout.
- Choose the **failsafe direction deliberately**: on RC signal loss the MUX should fall back to
  a defined state, and you must know which. Set the receiver's failsafe values before wiring.
- Verify at [Stage 2](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first) **with
  the Teensy deliberately halted** — held in reset or unplugged. A safety claim you have not
  tested with the component dead is not a safety claim.

> [!CAUTION]
> **Star-ground at the motor driver**
>
> Tie the signal grounds of the Teensy, the RC receiver, the signal MUX, and the motor driver
> to a **single** point at the motor driver. This is
> [FMEA row 5](../design/safety.md#7-fmea-lightweight) — a ground loop between logic and a
> motor power stage produces erratic motor commands that are extremely hard to diagnose later,
> because they look like a firmware bug.

## 3.6 Continuity and isolation checks — before any power

Battery **disconnected**, multimeter in continuity mode.

- [ ] No continuity between traction rail and logic rail anywhere except the intended DC-DC input
- [ ] No continuity between driver M1 and M2 outputs
- [ ] MUX NC contacts connect stock ECU → motors with the coil de-energized
- [ ] MUX NO contacts connect the motor driver → motors only with the coil energized
- [ ] E-stop, when latched in, opens the traction path **and** the coil circuit
- [ ] Every flyback diode is present and correctly oriented (diode-test across each coil)
- [ ] Signal grounds meet at exactly one point
- [ ] All three taps are keyed and cannot be plugged in reversed
- [ ] Every fuse holder is populated with the value from §3.2

## 3.7 Relay-MUX bench test procedure

Perform this on a **bench supply with a current limit**, with the motor outputs connected to
either nothing or a dummy load — **not** to the vehicle's motors, and with the vehicle
wheels off the ground regardless.

1. **Cold state.** Apply logic power only. Confirm with a meter that the MUX contacts are in
   the **STOCK** position. Nothing energized the coil, so nothing should have moved.
2. **Deliberate mode switch.** Energize the coil. Confirm contacts transfer to the DBW
   position, and that they transfer back when de-energized.
3. **Logic-loss revert.** With the coil energized, cut the logic rail. Confirm the coil drops
   and the contacts return to STOCK. This is [failsafe matrix row 4](../design/safety.md#2-failsafe-matrix).
4. **E-stop revert.** With the coil energized, press the E-stop. Confirm both traction power
   is cut **and** the coil drops to STOCK. This is
   [failsafe matrix row 5](../design/safety.md#2-failsafe-matrix).
5. **Latch behavior.** Confirm the E-stop stays latched — nothing re-energizes until it is
   manually reset.
6. **Repeat 10×.** Relay contacts that work once are not the same as relay contacts that work
   reliably. Watch for chatter or slow transfer.

**Record sheet — MUX bench test**

| Test | Expected | Observed | Pass |
|---|---|---|---|
| Power-up default state | STOCK | *(record)* | ☐ |
| Coil energize → DBW | contacts transfer | *(record)* | ☐ |
| Coil de-energize → STOCK | contacts return | *(record)* | ☐ |
| Logic-rail loss with coil energized | reverts to STOCK | *(record)* | ☐ |
| E-stop with coil energized | traction cut **and** STOCK | *(record)* | ☐ |
| E-stop latches until manual reset | latched | *(record)* | ☐ |
| 10× repeat, no chatter | consistent | *(record)* | ☐ |

> [!NOTE]
> **Relay welding is the one failure the MUX cannot self-protect against**
>
> [FMEA row 8](../design/safety.md#7-fmea-lightweight) rates a welded-closed MUX relay as
> severity 5 — you cannot revert to STOCK, and DBW is stuck live. The mitigation is that
> the **E-stop cuts traction power independently of the MUX**, so it remains authoritative
> even then. This is why the E-stop must be in the power path and not merely commanding the
> coil. Use an adequately rated contactor and check the contacts during every bring-up.

## 3.8 First power-on of the traction rail

Only after §3.6 and §3.7 pass.

1. Wheels off the ground, vehicle on stands.
2. Connect the pack. Do **not** energize the MUX coil — the vehicle should be in STOCK mode.
3. Confirm the stock parent remote still drives the vehicle normally. If it does not, your
   taps are wrong, and you have learned that before involving the motor driver.
4. Confirm the logic rail is up and stable, and that the Teensy powers on and enumerates over USB.
5. Measure the logic rail while someone forces a stock steering stall. **The logic rail must
   not sag.** If it does, your isolation is inadequate — add hold-up capacitance before
   continuing.

**Record sheet — rail measurements**

| Measurement | Value |
|---|---|
| Traction rail, at rest | *(measure during bring-up)* V |
| Traction rail, under drive-motor stall | *(measure during bring-up)* V |
| Logic rail, at rest | *(measure during bring-up)* V |
| Logic rail, during traction stall | *(measure during bring-up)* V |
| Logic-rail sag under stall | *(measure during bring-up)* V — target: negligible |
| Undervoltage monitor trip point | *(record setting)* V |

## 3.9 Gate to step 4

- [ ] Two-rail split built; steering gearmotor confirmed on the **traction** rail
- [ ] Fuse table complete with measured values; every holder populated
- [ ] Paralleled drive-motor stall current measured and confirmed < 32 A/channel
- [ ] Three keyed taps installed; no stock wire cut
- [ ] E-stop hardwired in the traction path, latching, drops the MUX coil
- [ ] MUX defaults to STOCK de-energized; verified 10× without chatter
- [ ] All flyback diodes present and correctly oriented
- [ ] Signal grounds star-tied at the motor driver
- [ ] Continuity/isolation checklist (§3.6) passes
- [ ] Stock parent remote still drives the vehicle through the taps
- [ ] Logic rail does not sag under traction stall
- [ ] **Logic rail is its own battery**, not tapped from the traction pack (§3.1)
- [ ] Motor driver DIP switches set for **independent R/C (PWM) mode**, per the
      [Order Log](../order-log.md) entry for the board fitted
- [ ] **Hardware RC signal MUX installed and powered from the logic rail** (§3.5.1) — its
      Stage 2 test with the Teensy halted is the condition D3 was adopted on
- [ ] RC receiver failsafe values set, and the MUX's failsafe direction known and written down
- [ ] Teensy USB on a **direct laptop port**, not a hub

---

**Previous:** [2. Vehicle prep & mechanical](02-mechanical.md) · **Next:** [4. Firmware bring-up](04-firmware.md)
