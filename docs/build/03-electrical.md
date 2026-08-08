# 3. Electrical & Wiring

**Goal:** build the power and signal harness, including the authority MUX and E-stop.

Wire the 24V traction rail, the isolated logic rail, the Sabertooth 2x32, the Teensy,
the relay-MUX (STOCK vs. DBW), the hardware RC signal MUX, and the hardware E-stop. Verify
rail isolation and default-to-stock behavior before energizing anything downstream.

- **Prerequisites:** Section 2 complete.
- **Specification:** [design/dbw.md](../design/dbw.md), [design/safety.md](../design/safety.md)
- **Expected outcome:** harness continuity-checked; relay defaults to STOCK; E-stop cuts
  traction power only.

!!! warning "Draft — not yet validated on hardware"

    This wiring plan is derived from the
    [architecture.md power tree](../design/architecture.md#5-power-tree-and-safetyauthority-chain)
    and [safety.md](../design/safety.md). It has **not** been built. Fuse values, wire gauges,
    and relay contact ratings depend on the stall currents you measured in step 2 and are
    marked *(measure during bring-up)*.

!!! danger "This is the step where mistakes become dangerous"

    Everything before this was mechanical. From here the vehicle can move under power. Wire
    the E-stop and the MUX **first**, verify default-to-STOCK **before** energizing the
    Sabertooth, and keep the vehicle wheels-off until step 7.

---

## 3.1 The two rails

MRider has exactly two power rails, and the split is safety-critical.

```
24 V traction pack
  │
  └──▶ E-stop contactor (cuts TRACTION only) ──▶ Relay MUX ──┬──▶ STOCK: parent-remote receiver + ESC
                                                             └──▶ DBW:   Sabertooth 2x32 B+
                                                                          ├─ M1 → steering gearmotor
                                                                          └─ M2 → paralleled drive motors

12 V logic battery ──▶ DC-DC ──▶ ISOLATED LOGIC RAIL
                                   ├─ Teensy 4.1 (5 V in, 3.3 V logic)
                                   ├─ absolute angle sensor (3.3 V, I²C)
                                   ├─ RC receiver
                                   ├─ hardware RC signal MUX
                                   ├─ Sabertooth signal logic
                                   └─ MUX coil driver

Laptop ──▶ its own internal battery (NOT wired to traction in v1)
```

| Rail | Feeds | Dies when |
|---|---|---|
| **Traction / motor** | Sabertooth B+, M1 (steering gearmotor), M2 (drive motors) | E-stop pressed, MUX drops, pack disconnected |
| **Isolated logic** | Teensy, angle sensor, RC receiver, signal MUX, Sabertooth signal logic, MUX coil driver | Logic battery disconnected only |

!!! danger "The logic rail is now a separate battery, not a tap off the pack"

    The superseded design got logic isolation from the Pixhawk's PM02 power module. **That
    part is deleted**, so the isolation must be built explicitly — a dedicated 12 V battery and
    DC-DC, from day one, not as a retrofit
    ([safety.md §5](../design/safety.md#5-power-rail-isolation-and-brownout-protection)).

    This matters more than it did before. The Teensy holds the **entire** safety supervisor —
    the position loop, throttle shaping, the staleness watchdog, SBUS decode, arming. A reset
    mid-drive loses every firmware-layer protection at once (FMEA row 4, severity 5). There is
    no second controller to survive it.

!!! info "The steering gearmotor is on the traction rail — deliberately"

    [safety.md §4.1](../design/safety.md#4-steering-motor-power-rail-assignment-and-power-loss-behavior-pinned)
    pins this. The consequence is that **E-stop de-energizes the steering motor and the
    column freewheels**. That is the intended, analyzed behavior — acceptable at ≤ walking
    speed with an operator alongside. Putting the steering motor on the logic rail would risk
    browning out the Teensy on a steering stall, and would leave a live actuator after an
    emergency stop. Do not "improve" this.

**Brownout isolation is the point of the split.** Motor stalls sag the traction rail. The
logic rail must not follow. Use adequate hold-up capacitance and put the undervoltage monitor
on the **logic** rail.

## 3.2 Per-rail fuse and gauge table

Fuse for the **stall** current, not the nominal draw, and size wire for the fuse.

| Rail / branch | Nominal | Stall / peak | Fuse | Wire gauge |
|---|---|---|---|---|
| Pack → E-stop contactor → MUX | *(measure during bring-up)* | *(measure during bring-up)* | *(size to measured)* | *(size to fuse)* |
| MUX → Sabertooth B+ | *(measure during bring-up)* | *(measure during bring-up)* | *(size to measured)* | *(size to fuse)* |
| Sabertooth M2 → paralleled drive motors | *(measure during bring-up)* | **must be < 32 A** ([dbw.md §7](../design/dbw.md#7-throttle-path)) | *(size to measured)* | *(size to fuse)* |
| Sabertooth M1 → steering gearmotor | *(measure during bring-up)* | *(measure during bring-up)* | *(size to measured)* | *(size to fuse)* |
| Logic battery → DC-DC input | < 2 A typical | — | 3–5 A | 18–20 AWG |
| Logic rail → Teensy / sensor / RC RX / signal MUX | < 1 A typical | — | 1–2 A | 22–24 AWG |
| MUX coil circuit | per relay coil spec | — | *(size to coil)* | 22 AWG |

!!! danger "Verify paralleled drive-motor stall current against 32 A/channel"

    This is [FMEA row 7](../design/safety.md#7-fmea-lightweight) and an explicit cross-check
    in [dbw.md §13](../design/dbw.md#13-cross-checks-and-open-follow-ups). If the two
    paralleled rear motors can exceed 32 A stalled, you must either current-limit in the
    Sabertooth configuration or select lower-draw motors. Measure it — a locked-rotor test
    with a clamp meter and a current-limited supply — do not assume.

## 3.3 The three taps

Reversibility comes from three keyed inline connectors that intercept the stock harness
without cutting it ([dbw.md §11.5](../design/dbw.md#115-3-tap-connector-spec-minimally-invasive)).

| Tap | Intercepts | MUX side | Notes |
|---|---|---|---|
| **Throttle tap** | stock throttle motor leads | NC → stock ECU, NO → Sabertooth M2 | paralleled rear motors |
| **Steering tap** | stock steering motor leads | NC → stock ECU, NO → Sabertooth M1 | MRider adds the gearmotor if the column had none. **Note the M1/M2 assignment is inverted vs. mrover** — intentional, see [dbw.md §2.1](../design/dbw.md#21-actuator) (finding F6) |
| **Power tap** | 24 V battery pack | feeds Sabertooth B+ only | fused. The logic rail is a **separate battery** (§3.1), not tapped from here |

Use **keyed** connectors — not generic bullets. During bring-up you will unplug and re-plug
these many times, and a reversed steering tap means the position loop runs away from its
setpoint instead of toward it.

## 3.4 Wire the E-stop and MUX first

Build the authority chain before anything can be commanded.

**E-stop.** A latching mushroom-head contactor, hardwired in the **traction** power path —
not a software command. It must work when the laptop and the Teensy have both hung. It does
two things at once:

1. cuts traction power, and
2. drops the MUX coil, reverting authority to STOCK.

**Relay MUX.** Two DPDT relays/contactors, one per motor circuit:

- **NC (normally closed) contacts** → stock controller drives the motors. This is the state
  when the coil is de-energized, which is the **default**.
- **NO (normally open) contacts** → Sabertooth drives the motors. Coil energized = DBW mode.
- **Flyback diode across every coil**, oriented correctly. A relay coil without a flyback
  diode will eventually kill the transistor driving it, and that failure can leave the MUX
  in an indeterminate state.
- Drive the coils from the **logic** rail through a logic-level MOSFET/transistor, so any
  logic-rail collapse drops the coil.

!!! note "Default de-energized = STOCK is the whole safety story"

    Every failure direction leads back to the factory-controlled vehicle: E-stop, logic
    brownout, a pulled connector, a dead Teensy. If you wire the relays inverted — energize for
    STOCK — you invert the entire failsafe analysis in
    [safety.md](../design/safety.md). Check this twice.

## 3.5 Signal wiring

The Sabertooth runs in **independent R/C (PWM) mode**. Both signal lines come from the Teensy,
and **both pass through the hardware RC signal MUX** on the way
([dbw.md §4](../design/dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-teensy-as-both-masters)).
Set the DIP switches for R/C mode before wiring — consult the Sabertooth manual for the table.

| Sabertooth input | Normal source | Override source | Motor output |
|---|---|---|---|
| S1 | Teensy PWM (via MUX) | RC receiver (via MUX) | M1 — steering gearmotor |
| S2 | Teensy PWM (via MUX) | RC receiver (via MUX) | M2 — drive motors, paralleled |

!!! info "Why not packetized serial?"

    Single-master packetized serial was briefly adopted — it gives exact, high-rate commands
    and would close the actuation-rate question outright. It was **reverted** because every
    available RC signal multiplexer switches *servo pulses*, and none can select between a
    serial stream and RC PWM. Packetized serial and the RC signal MUX are mutually exclusive,
    and the MUX is the condition D3 was adopted on. See
    [dbw.md §4](../design/dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-teensy-as-both-masters).

    The consolation: in R/C mode the Sabertooth's **signal-loss timeout is inherent** — motors
    stop when pulses stop, with nothing to configure.

**Signal connections to make:**

| From | To | Notes |
|---|---|---|
| Teensy PWM out ×2 | RC signal MUX **master** inputs | Servo-style pulses — steering and throttle |
| Absolute angle sensor | Teensy **I²C** (SDA/SCL) | 3.3 V from the logic rail. Pot fallback → an analog input instead |
| Drive encoder A/B | Teensy **hardware quadrature decoder** pins | Not software interrupts — the Teensy has 4 dedicated QDC channels |
| Steering motor encoder A/B | Teensy hardware quadrature decoder pins | Second QDC channel |
| RC receiver **SBUS** | Teensy hardware serial RX | Layer A override (closed-loop) |
| RC receiver **MUX channel** | Hardware RC signal MUX select | Layer B override — see below |
| RC receiver PWM out ×2 | RC signal MUX **slave** inputs | Emergency path |
| Signal MUX outputs ×2 | Sabertooth **S1** and **S2** | Whichever source the MUX selects |
| Teensy **USB** | Laptop | micro-ROS — carries **command *and* feedback** |

!!! danger "Give the Teensy USB a direct laptop port, not a hub"

    This single link carries the steering setpoint as well as the feedback. A dropout removes
    the setpoint and drops the vehicle to `ESTOP`
    ([failsafe row 2](../design/safety.md#2-failsafe-matrix)). That is the safe behavior, but a
    flaky cable or a marginal hub becomes a vehicle that stops repeatedly. Use a good cable and
    a direct port, and log 30 minutes of session stability at
    [bring-up Stage 0](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first).

### 3.5.1 Hardware RC signal MUX — wire this, it is not optional

!!! danger "This is the condition on which the architecture was adopted"

    D3 concentrates the steering loop, throttle, override, and arming on one MCU. The
    justification for accepting that is that override is a **wiring property**, not a firmware
    property ([safety.md §1.2](../design/safety.md#12-live-override-inside-dbw-mode-two-layers)).
    A build without this MUX has no independent override and does not match the safety analysis
    the design was approved against.

The MUX sits **between the Teensy and the Sabertooth**, selecting which source reaches the
motor driver:

```
Teensy output ──▶ MUX input A ─┐
                               ├──▶ MUX output ──▶ Sabertooth
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

!!! danger "Star-ground at the Sabertooth"

    Tie the signal grounds of the Teensy, the RC receiver, the signal MUX, and the Sabertooth to
    a **single** point at the Sabertooth. This is
    [FMEA row 5](../design/safety.md#7-fmea-lightweight) — a ground loop between logic and a
    24 V power stage produces erratic motor commands that are extremely hard to diagnose later,
    because they look like a firmware bug.

## 3.6 Continuity and isolation checks — before any power

Battery **disconnected**, multimeter in continuity mode.

- [ ] No continuity between traction rail and logic rail anywhere except the intended DC-DC input
- [ ] No continuity between Sabertooth M1 and M2 outputs
- [ ] MUX NC contacts connect stock ECU → motors with the coil de-energized
- [ ] MUX NO contacts connect Sabertooth → motors only with the coil energized
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

!!! note "Relay welding is the one failure the MUX cannot self-protect against"

    [FMEA row 8](../design/safety.md#7-fmea-lightweight) rates a welded-closed MUX relay as
    severity 5 — you cannot revert to STOCK, and DBW is stuck live. The mitigation is that
    the **E-stop cuts traction power independently of the MUX**, so it remains authoritative
    even then. This is why the E-stop must be in the power path and not merely commanding the
    coil. Use an adequately rated contactor and check the contacts during every bring-up.

## 3.8 First power-on of the traction rail

Only after §3.6 and §3.7 pass.

1. Wheels off the ground, vehicle on stands.
2. Connect the pack. Do **not** energize the MUX coil — the vehicle should be in STOCK mode.
3. Confirm the stock parent remote still drives the vehicle normally. If it does not, your
   taps are wrong, and you have learned that before involving the Sabertooth.
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
- [ ] Signal grounds star-tied at the Sabertooth
- [ ] Continuity/isolation checklist (§3.6) passes
- [ ] Stock parent remote still drives the vehicle through the taps
- [ ] Logic rail does not sag under traction stall
- [ ] **Logic rail is its own battery**, not tapped from the traction pack (§3.1)
- [ ] Sabertooth DIP switches set for **independent R/C (PWM) mode**
- [ ] **Hardware RC signal MUX installed and powered from the logic rail** (§3.5.1) — its
      Stage 2 test with the Teensy halted is the condition D3 was adopted on
- [ ] RC receiver failsafe values set, and the MUX's failsafe direction known and written down
- [ ] Teensy USB on a **direct laptop port**, not a hub

---

**Previous:** [2. Vehicle prep & mechanical](02-mechanical.md) · **Next:** [4. Firmware bring-up](04-firmware.md)
