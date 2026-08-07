# 3. Electrical & Wiring

**Goal:** build the power and signal harness, including the authority MUX and E-stop.

Wire the 24V traction rail, the isolated logic rail, the Sabertooth 2x32, the Pixhawk
power module, the relay-MUX (STOCK vs. DBW), and the hardware E-stop. Verify rail
isolation and default-to-stock behavior before energizing anything downstream.

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
24 V battery pack
  │
  ├──▶ E-stop contactor (cuts TRACTION only) ──▶ Relay MUX ──┬──▶ STOCK: parent-remote receiver + ESC
  │                                                          └──▶ DBW:   Sabertooth 2x32 B+
  │                                                                       ├─ M1 → steering gearmotor
  │                                                                       └─ M2 → paralleled drive motors
  │
  └──▶ Pixhawk power module (PM02) ──▶ ISOLATED LOGIC RAIL
                                        ├─ Pixhawk 6C
                                        ├─ Arduino Nano
                                        ├─ absolute angle sensor (regulated, ratiometric)
                                        ├─ Sabertooth signal logic
                                        └─ MUX coil driver

Laptop ──▶ its own internal battery (NOT wired to 24 V in v1)
```

| Rail | Feeds | Dies when |
|---|---|---|
| **Traction / motor** | Sabertooth B+, M1 (steering gearmotor), M2 (drive motors) | E-stop pressed, MUX drops, pack disconnected |
| **Isolated logic** | Pixhawk, Nano, angle sensor, Sabertooth signal logic, MUX coil driver | Pack disconnected only |

!!! info "The steering gearmotor is on the traction rail — deliberately"

    [safety.md §4.1](../design/safety.md#4-steering-motor-power-rail-assignment-and-power-loss-behavior-pinned)
    pins this. The consequence is that **E-stop de-energizes the steering motor and the
    column freewheels**. That is the intended, analyzed behavior — acceptable at ≤ walking
    speed with an operator alongside. Putting the steering motor on the logic rail would risk
    browning out the Nano and PX4 on a steering stall, and would leave a live actuator after
    an emergency stop. Do not "improve" this.

**Brownout isolation is the point of the split.** Motor stalls sag the traction rail. The
logic rail must not follow, or the Nano/PX4 reset mid-drive. Use a dedicated logic DC-DC with
adequate hold-up capacitance and put the undervoltage monitor on the **logic** rail
([safety.md §5](../design/safety.md#5-power-rail-isolation-and-brownout-protection)).

## 3.2 Per-rail fuse and gauge table

Fuse for the **stall** current, not the nominal draw, and size wire for the fuse.

| Rail / branch | Nominal | Stall / peak | Fuse | Wire gauge |
|---|---|---|---|---|
| Pack → E-stop contactor → MUX | *(measure during bring-up)* | *(measure during bring-up)* | *(size to measured)* | *(size to fuse)* |
| MUX → Sabertooth B+ | *(measure during bring-up)* | *(measure during bring-up)* | *(size to measured)* | *(size to fuse)* |
| Sabertooth M2 → paralleled drive motors | *(measure during bring-up)* | **must be < 32 A** ([dbw.md §7](../design/dbw.md#7-throttle-path)) | *(size to measured)* | *(size to fuse)* |
| Sabertooth M1 → steering gearmotor | *(measure during bring-up)* | *(measure during bring-up)* | *(size to measured)* | *(size to fuse)* |
| Pack → Pixhawk power module (PM02) | per PM02 spec | — | *(size to measured)* | per PM02 harness |
| Logic rail → Nano / sensor / signal logic | < 1 A typical | — | 1–2 A | 22–24 AWG |
| MUX coil circuit | per relay coil spec | — | *(size to coil)* | 22 AWG |

!!! danger "Verify paralleled drive-motor stall current against 32 A/channel"

    This is [FMEA row 7](../design/safety.md#7-fmea-lightweight) and an explicit cross-check
    in [dbw.md §13](../design/dbw.md#13-cross-checks-and-open-follow-ups). If the two
    paralleled rear motors can exceed 32 A stalled, you must either current-limit in the
    Sabertooth configuration or select lower-draw motors. Measure it — a locked-rotor test
    with a clamp meter and a current-limited supply — do not assume.

## 3.3 The three taps

Reversibility comes from three keyed inline connectors that intercept the stock harness
without cutting it ([dbw.md §11.3](../design/dbw.md#113-3-tap-connector-spec-minimally-invasive)).

| Tap | Intercepts | MUX side | Notes |
|---|---|---|---|
| **Throttle tap** | stock throttle motor leads | NC → stock ECU, NO → Sabertooth M2 | paralleled rear motors |
| **Steering tap** | stock steering motor leads | NC → stock ECU, NO → Sabertooth M1 | MRider adds the gearmotor if the column had none |
| **Power tap** | 24 V battery pack | feeds Sabertooth B+ and the isolated logic rail | fused; brownout isolation per §3.1 |

Use **keyed** connectors — not generic bullets. During bring-up you will unplug and re-plug
these many times, and a reversed steering tap means the position loop runs away from its
setpoint instead of toward it.

## 3.4 Wire the E-stop and MUX first

Build the authority chain before anything can be commanded.

**E-stop.** A latching mushroom-head contactor, hardwired in the **traction** power path —
not a software command. It must work when the laptop, Nano, and PX4 have all hung. It does
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
    brownout, a pulled connector, a dead Nano. If you wire the relays inverted — energize for
    STOCK — you invert the entire failsafe analysis in
    [safety.md](../design/safety.md). Check this twice.

## 3.5 Signal wiring

The Sabertooth runs in **independent R/C (PWM) mode** with two separate masters
([dbw.md §4](../design/dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-mode-per-channel-masters)).

| Sabertooth input | Driven by | Motor output | Function |
|---|---|---|---|
| **S1** | Arduino Nano PWM (steering effort) | M1 | steering gearmotor |
| **S2** | PX4 PWM (throttle) | M2 | drive motors, paralleled |

This is the one place MRider departs from mrover, which fed **both** S1 and S2 from the PX4
PWM board. There is no bus conflict because in R/C mode S1 and S2 are electrically separate
one-way PWM lines with a common ground — not a shared addressed bus.

**Signal connections to make:**

- PX4 servo output → Sabertooth **S2** (3-wire servo lead)
- Nano PWM output pin → Sabertooth **S1**
- Absolute angle sensor → Nano ADC input (fed from the Nano's regulated rail)
- Drive encoder → Nano interrupt pins
- Steering gearmotor encoder (if fitted) → Nano interrupt pins
- Nano USB → laptop (this is the feedback transport, 115200 baud)

!!! danger "Star-ground at the Sabertooth"

    Tie the signal grounds of the Nano, the PX4, and the Sabertooth to a **single** point at
    the Sabertooth. This is [FMEA row 5](../design/safety.md#7-fmea-lightweight) — a ground
    loop between two independent PWM masters and a 24 V power stage produces erratic motor
    commands that are extremely hard to diagnose later, because they look like a firmware
    bug.

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
4. Confirm the logic rail is up and stable, and that the Pixhawk and Nano power on.
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

---

**Previous:** [2. Vehicle prep & mechanical](02-mechanical.md) · **Next:** [4. Firmware bring-up](04-firmware.md)
