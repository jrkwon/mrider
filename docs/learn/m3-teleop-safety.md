# M3 — Manual/Teleop Control & Safety

**Learning objectives:**

- Reason about control authority, RC override, and the relay-MUX arbitration.
- Interpret a failsafe matrix and E-stop semantics.
- Run a safe wheels-off bring-up before any powered driving.

**Reference:** [design/safety.md](../design/safety.md)

!!! warning "Draft — lab not yet run on hardware"

    The lecture is grounded in [safety.md](../design/safety.md), which is authoritative and
    complete. The **lab requires a vehicle with the relay MUX and E-stop installed**, which has
    not been built. No failsafe has been physically exercised on an MRider.

---

## Lecture

### The question this module answers

Three different controllers can drive MRider's motors, and **at most one may reach them at
any instant**:

1. The **stock parent-remote** / factory ECU — the vehicle as shipped
2. **DBW autonomy** — laptop → PX4 → Sabertooth
3. An **RC transmitter** bound to the Pixhawk — the live human override inside DBW mode

If two of them can command the motors simultaneously, you do not have a vehicle, you have a
race condition with wheels. So the design must answer: *who wins, and what happens when a
link dies?*

### Authority is enforced electrically, not in software

The core mechanism is a **DPDT relay MUX**: two relays, one per motor circuit, selecting
STOCK or DBW.

- **Coil de-energized → STOCK** (normally-closed contacts route the factory controller)
- **Coil energized → DBW** (normally-open contacts route the Sabertooth)

**Default is de-energized.** Therefore *any* loss of logic power, *any* E-stop, and *any*
deliberate abort drops the coil and reverts to the factory-safe vehicle.

!!! info "The failure direction is always toward stock"

    This is the single most important property in the whole safety design. Not "the software
    detects a fault and switches to a safe mode" — software that must run correctly in order
    to fail safely is not a safety mechanism. **Physics does it:** no current in the coil, no
    DBW.

    Note the precise meaning of "parent-remote fallback": it is **reversibility**, not live
    dual authority. The parent remote and the Sabertooth are never simultaneously wired to the
    motors.

### The priority ladder

| Priority | Authority | Mechanism |
|---|---|---|
| 1 (highest) | **Hardware E-stop** | Cuts traction power + drops the MUX coil |
| 2 | **Relay MUX position** | De-energized = STOCK; overrides DBW entirely |
| 3 | **RC transmitter (via PX4)** | PX4 RC override preempts offboard/laptop |
| 4 (lowest) | **Laptop autonomy** | Only drives when 1–3 all permit |

Autonomy is at the **bottom**. The most sophisticated component in the system has the least
authority — because it is the component most likely to be wrong in a novel way.

**RC override covers steering for free.** Because MRider's steering command flows *through*
PX4 ([ADR E](../design/dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision)),
an operator grabbing the sticks overrides the laptop on **both** axes with no separate wiring
to the Nano. This is the safety payoff of pinning a single datapath — an architectural choice
in M2 turned into a safety property in M3.

### Reading a failsafe matrix

A [failsafe matrix](../design/safety.md#2-failsafe-matrix) enumerates every way a link can
die and states the defined behavior. MRider's has seven rows. Three worth studying:

**Row 1 — command/heartbeat loss.** The laptop stops streaming (< 10 Hz). PX4's offboard-loss
timeout fires: throttle → 0, enter hold. PX4 stops emitting the servo setpoint, so the Nano's
PWM-valid bit clears and **steering holds its last angle** as the motor de-energizes.

**Row 2 — USB loss.** The Nano↔laptop serial drops. Feedback is lost, so autonomy degrades to
a safe stop. But **steering is unaffected** — the setpoint arrives via PX4 servo PWM, not
USB, so the column keeps tracking while the laptop goes blind on odometry.

!!! danger "Row 2 is the counter-intuitive one"

    Unplugging the Nano's USB cable does **not** stop the steering. Every operator's intuition
    says it should. That intuition, held during an actual incident, produces exactly the wrong
    response. This is why you exercise the matrix on a bench rather than reading it.

**Row 5 — E-stop.** Traction power cut, MUX coil dropped, Sabertooth unpowered on the motor
rail. The steering motor loses power and the **column freewheels**.

### Why freewheel is the right answer

The steering column on these vehicles is **non-self-centering** — no spring return. So which
rail the steering motor sits on determines its behavior on power loss, and the design pins it
explicitly ([safety.md §4](../design/safety.md#4-steering-motor-power-rail-assignment-and-power-loss-behavior-pinned)):

**The steering gearmotor is on the traction rail**, not the logic rail. Consequences:

- E-stop cuts traction → steering de-energizes → column freewheels.
- A steering stall cannot brown out the Nano and PX4, because they are on the other rail.
- Steering cannot remain live after an E-stop cut traction — which would be an inconsistent,
  more dangerous state.

Why freewheeling is acceptable, in the design's own terms:

- **Speed bound.** MRider operates at ≤ walking speed with an operator alongside during all
  early phases. Coast-down is under a couple of meters.
- **Freewheel ≠ uncontrolled.** With traction already cut, a freewheeling front axle tracks
  straight or is trivially hand-corrected. There is no power to steer the car into anything.
- **Fail-consistent.** It matches the STOCK-revert direction — the factory vehicle also has no
  autonomous steering when off.

The alternative, hold-last-angle through an E-stop, would require keeping the steering motor
powered *after* an emergency stop. Rejected.

!!! note "Notice the shape of that argument"

    "Freewheel is safe" is not a universal claim. It is safe **given** ≤ walking speed, an
    operator alongside, and a short coast-down. Change the speed cap and the argument no
    longer holds. Safety claims are conditional, and a good safety document states the
    conditions. This is why the software speed cap in the build guide is not a tuning
    parameter.

### FMEA — the failures nobody watches

A failsafe matrix covers *link losses*. An [FMEA](../design/safety.md#7-fmea-lightweight)
covers *component failures*, rated by severity (S) and detectability (D). MRider's has ten
rows; the two that matter most are the ones rated hardest to see:

**Row 8 — MUX relay welds closed in DBW mode.** Severity 5. You cannot revert to STOCK; DBW is
stuck live. Mitigation: **the E-stop cuts traction power independently of the MUX**, so it
remains authoritative even then. This is precisely why the E-stop is in the power path and
not merely commanding the coil.

**Row 9 — Nano firmware hang.** Severity 4. The steering loop freezes. Mitigation: a hardware
watchdog resets the Nano to neutral output (1500 µs), with PX4 servo-loss and the E-stop as
outer layers.

The pattern: **each mitigation is independent of the component that failed.** A watchdog
implemented inside the hung firmware is not a mitigation.

### Staged bring-up

The protocol exists so nobody has to be brave
([safety.md §6](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first)). **Bench
before vehicle; wheels-off before wheels-on; walking pace before anything faster.**

| Stage | What is connected | What you prove |
|---|---|---|
| 0 | Nano alone, **no motor** | Sensor reads, PWM capture, feedback frames |
| 1 | + steering motor, bench supply | Closed-loop tracking, limits, stall, freewheel |
| 2 | + PX4, Sabertooth R/C mode | Full datapath, independent masters, RC override |
| 3 | + relay MUX and E-stop | Every failsafe row; default = STOCK on every fault |
| 4 | Full vehicle, wheels on stands | Repeat matrix; no brownout under steering stall |
| 5 | Ground, walking pace, operator alongside | E-stop under motion |

No stage begins until the previous one passes. Autonomy engages only after Stage 5.

---

## Lab

**Goal:** drive by joystick and RC, then deliberately trigger heartbeat-loss and RC-loss
failsafes on the bench and confirm each specified behavior.

!!! danger "Wheels off the ground for this entire lab"

    Every test here is a Stage 3 test. The vehicle stays on stands. One student keeps a hand
    on the E-stop for the whole session and does nothing else.

### Part 1 — Predict before you test

**Do this before touching anything.** For each row, write down what you think will happen.
Then test. The gap between prediction and observation is the actual learning.

| # | Scenario | Your prediction | Observed | Match? |
|---|---|---|---|---|
| 1 | Command/heartbeat loss (< 10 Hz) | | | |
| 2 | USB unplugged (Nano ↔ laptop) | | | |
| 3 | RC transmitter powered off | | | |
| 4 | Logic-rail brownout | | | |
| 5 | E-stop pressed | | | |
| 6 | Sabertooth S1 signal unplugged | | | |
| 7 | Steering commanded past its limit | | | |

### Part 2 — Manual control

1. **Confirm STOCK first.** With the MUX de-energized, the parent remote must drive the
   vehicle normally. This proves the taps and the authority chain before DBW is involved.
2. **Energize the MUX** to enter DBW. Confirm on telemetry.
3. **RC steering sweep**, no throttle. Watch `steer_deg` track `setpoint_deg`.
4. **Joystick teleop** publishing to `/mrider/cmd`. Note that it must have a **dead-man gate**
   and a **software speed cap** — and note *why* the cap exists (the freewheel argument above
   only holds at walking speed).

### Part 3 — Exercise the failsafe matrix

Work the seven rows. Suggested inductions:

```bash
# Row 1 — kill the heartbeat
#   stop the command shim; watch PX4 failsafe and the Nano's bit0

# Row 2 — USB loss
#   unplug /dev/mrider_nano. Does steering stop? (Predict first!)

# Row 3 — RC loss
#   power off the transmitter; observe PX4 COM_RC_LOSS_T behavior

# Row 6 — Sabertooth signal loss
#   unplug S1, then S2; each channel should stop its own motor
```

For rows 4 and 5, use the bench supply and the E-stop respectively.

### Part 4 — The freewheel test

[safety.md §4.4](../design/safety.md#44-test-procedure-freewheel-on-power-loss), steps 1–2:

1. Command a mid-range steering angle; confirm the Nano holds it.
2. Press the E-stop. Confirm all four:
   traction dead · MUX shows STOCK · steering motor de-energized · **column turns freely by
   hand** with light force.
3. Measure the hand-steer force at the rim with a spring scale: *(measure)* N.

### Part 5 — Authority ladder

Verify the priority order holds, from the bottom up:

| Test | Expected | Observed |
|---|---|---|
| Joystick commands, then take the RC sticks | RC wins, **both axes**, < 1 s | *(record)* |
| RC commands, then de-energize the MUX | Reverts to STOCK mid-command | *(record)* |
| Anything commands, then E-stop | Traction cut + STOCK | *(record)* |

### Expected output

- A completed prediction-vs-observation table for all seven rows
- At least two predictions that were **wrong** — if all seven matched, you were probably
  reading the matrix while predicting
- Freewheel test passed with the hand-steer force recorded
- Authority ladder verified in order

### Check yourself

- [ ] Why is "default de-energized = STOCK" stronger than a software-detected safe mode?
- [ ] The steering motor is on the traction rail. Name two things that would go wrong if it
      were on the logic rail instead.
- [ ] A MUX relay welds closed. What still protects you, and why is it independent?
- [ ] Under what conditions does the "freewheel is acceptable" argument stop holding?
- [ ] Autonomy is the lowest authority in the ladder. Argue for that, then against it.

---

## Slide outline

1. **Hook** — three controllers, one set of motors. Who wins?
2. **The relay MUX** — NC/NO contacts, default de-energized
3. **Failure direction** — why physics beats software for failing safe
4. **The priority ladder** — and why autonomy sits at the bottom
5. **RC override covers steering for free** — the M2 datapath decision paying off
6. **Reading a failsafe matrix** — rows 1, 2, 5 in detail
7. **Row 2 is counter-intuitive** — USB loss does not stop the steering
8. **Rail assignment decides freewheel vs. hold** — and the conditions that make freewheel OK
9. **Safety claims are conditional** — change the speed cap, break the argument
10. **FMEA** — rows 8 and 9, and independence of mitigations
11. **Staged bring-up** — six stages, no skipping
12. **Lab brief** — predict, then break it on purpose
13. **Looking ahead** — M4: the vehicle is safe to drive; now let it see

---

**Previous:** [M2 — Drive-by-wire & the smart-servo steering loop](m2-dbw-steering.md) · **Next:** [M4 — Perception](m4-perception.md)
