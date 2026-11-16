# M3 — Manual/Teleop Control & Safety

**Learning objectives:**

- Reason about control authority, RC override, and the relay-MUX arbitration.
- Interpret a failsafe matrix and E-stop semantics.
- Run a safe wheels-off bring-up before any powered driving.

**Reference:** [design/safety.md](../design/safety.md)

> [!TIP]
> **What makes this module different from a checklist**
>
> MRider concentrates the steering loop, throttle, override, and arming on a **single MCU**.
> That is only defensible because three of the four authority layers are *independent of that
> MCU's firmware* — and one of them exists purely to make it so.
>
> The lab therefore does something unusual: it asks you to **kill the controller on purpose**
> and confirm you can still steer. A safety claim you have not tested with the component dead
> is not a safety claim.

> [!WARNING]
> **Draft — lab not yet run on hardware**
>
> The lecture is grounded in [safety.md](../design/safety.md), which is authoritative and
> complete. The **lab requires a vehicle with the relay MUX and E-stop installed**, which has
> not been built. No failsafe has been physically exercised on an MRider.

---

## Lecture

### The question this module answers

Three different controllers can drive MRider's motors, and **at most one may reach them at
any instant**:

1. The **stock parent-remote** / factory ECU — the vehicle as shipped
2. **DBW autonomy** — laptop → Teensy → MDDS30
3. An **RC transmitter** — the live human override inside DBW mode, in **two layers**

If two of them can command the motors simultaneously, you do not have a vehicle, you have a
race condition with wheels. So the design must answer: *who wins, and what happens when a
link dies?*

### Authority is enforced electrically, not in software

The core mechanism is a **DPDT relay MUX**: two relays, one per motor circuit, selecting
STOCK or DBW.

- **Coil de-energized → STOCK** (normally-closed contacts route the factory controller)
- **Coil energized → DBW** (normally-open contacts route the MDDS30)

**Default is de-energized.** Therefore *any* loss of logic power, *any* E-stop, and *any*
deliberate abort drops the coil and reverts to the factory-safe vehicle.

> [!NOTE]
> **The failure direction is always toward stock**
>
> This is the single most important property in the whole safety design. Not "the software
> detects a fault and switches to a safe mode" — software that must run correctly in order
> to fail safely is not a safety mechanism. **Physics does it:** no current in the coil, no
> DBW.
>
> Note the precise meaning of "parent-remote fallback": it is **reversibility**, not live
> dual authority. The parent remote and the MDDS30 are never simultaneously wired to the
> motors.

### The priority ladder

| Priority | Authority | Mechanism | Independent of Teensy firmware? |
|---|---|---|---|
| 1 (highest) | **Hardware E-stop** | Cuts traction power + drops the MUX coil | **Yes** |
| 2 | **Relay MUX position** | De-energized = STOCK; overrides DBW entirely | **Yes** |
| 3 | **Hardware RC signal MUX** | Selects RC effort directly into the MDDS30 | **Yes** |
| 4 | **RC via serial** | Teensy switches to `MANUAL_RC`, loop still closed | No |
| 5 (lowest) | **Laptop autonomy** | Only drives when 1–4 all permit | No |

Autonomy is at the **bottom**. The most sophisticated component in the system has the least
authority — because it is the component most likely to be wrong in a novel way.

### Why the override has two layers

This is the most important thing in the module, and it comes from a real argument.

MRider puts the steering loop, the throttle output, RC override, and arming **all on one
MCU**. The obvious objection: a firmware hang loses all four at once. Under the earlier
Pixhawk design, a hung Arduino still left PX4 able to cut throttle and honour RC.

That objection is **only fatal if the override lives in software on that same MCU.** So it
does not:

- **Layer A — RC serial into the Teensy.** Normal manual mode. The sticks command an *angle*, with
  the position loop still closed behind them. Better than raw effort — when it works.
- **Layer B — a hardware RC signal MUX.** A dedicated RC channel drives a multiplexer that
  selects Teensy output *or* the receiver's output into the MDDS30. This is **wiring**. It
  works with the firmware hung, crashed, or never flashed.

> [!TIP]
> **The general move: convert a software guarantee into a physical one**
>
> PX4's RC override was *software* — good software, but software. Layer B is a signal path.
> Ask of any safety claim: **what has to be executing correctly for this to work?** If the
> answer includes the thing that might fail, it is not a mitigation.

> [!CAUTION]
> **And state the cost honestly**
>
> Through Layer B the override commands raw **effort**, open-loop — not an angle. It feels
> different, and an operator meeting that difference for the first time during an emergency
> is a hazard you created. That is why the lab makes you feel it on the bench, deliberately,
> with the Teensy halted.

### Reading a failsafe matrix

A [failsafe matrix](../design/safety.md#2-failsafe-matrix) enumerates every way a link can
die and states the defined behavior. MRider's has nine rows. Three worth studying:

**Row 1 — command loss.** The laptop stops publishing, or drops below rate. The Teensy's
staleness watchdog fires at **500 ms**: mode → `ESTOP`, throttle → 0, **steering centered**,
then the motor de-energizes.

**Row 2 — USB loss.** The link carries *both* the command and the feedback, so losing it
removes the setpoint. The Teensy detects the dead session and enters `ESTOP` on its own; the
laptop separately sees stale status and halts Nav2.

> [!CAUTION]
> **Row 2 reversed direction, and that is worth dwelling on**
>
> Under the earlier design, unplugging USB left **steering still tracking**, because the
> setpoint arrived on a separate wire from PX4. Now it stops the vehicle.
>
> Which is safer? The design argues the new behaviour is: a stale setpoint driving a live
> actuator is worse than a stop, and now there is **one link with one timeout** instead of a
> fault that manifests differently depending on which of two paths died.
>
> But notice the real lesson: **the same physical action — pulling a cable — produced
> opposite behaviours under two reasonable designs.** An operator who learned one and is
> working with the other will do the wrong thing. This is why you exercise the matrix on a
> bench rather than reading it, and why changing a failsafe means retraining the humans.

**Row 5 — E-stop.** Traction power cut, MUX coil dropped, MDDS30 unpowered on the motor
rail. The steering motor loses power and the **column freewheels**.

> [!WARNING]
> **Releasing the E-stop is not the reverse of pressing it**
>
> The MDDS30's own logic runs from the traction supply, downstream of the contactor. So when
> the latch is released the driver does not resume — it **boots**, and it takes whatever pulse
> it sees at that moment as *stop*. A pulse that is off-centre then becomes an offset on every
> later command.
>
> Two things must therefore be true before release: the firmware is holding both lines at
> exactly neutral, and the **transmitter sticks are centred, hands off** — with the signal MUX
> on the receiver, the sticks *are* the pulse
> ([safety.md §2](../design/safety.md#2-failsafe-matrix)). Recovery from a stop is part of the
> stop's design, and it is the part people rehearse least.

### Why freewheel is the right answer

The steering column on these vehicles is **non-self-centering** — no spring return. So which
rail the steering motor sits on determines its behavior on power loss, and the design pins it
explicitly ([safety.md §4](../design/safety.md#4-steering-motor-power-rail-assignment-and-power-loss-behavior-pinned)):

**The steering gearmotor is on the traction rail**, not the logic rail. Consequences:

- E-stop cuts traction → steering de-energizes → column freewheels.
- A steering stall cannot brown out the Teensy, because it is on the other rail. This matters
  *more* than it did with two controllers: the Teensy holds the entire safety supervisor, and
  there is no second board to survive its reset.
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

> [!NOTE]
> **Notice the shape of that argument**
>
> "Freewheel is safe" is not a universal claim. It is safe **given** ≤ walking speed, an
> operator alongside, and a short coast-down. Change the speed cap and the argument no
> longer holds. Safety claims are conditional, and a good safety document states the
> conditions. This is why the software speed cap in the build guide is not a tuning
> parameter.

### FMEA — the failures nobody watches

A failsafe matrix covers *link losses*. An [FMEA](../design/safety.md#7-fmea-lightweight)
covers *component failures*, rated by severity (S) and detectability (D). MRider's has thirteen
rows; two of the severity-5 ones are worth reading closely:

**Row 8 — MUX relay welds closed in DBW mode.** Severity 5. You cannot revert to STOCK; DBW is
stuck live. Mitigation: **the E-stop cuts traction power independently of the MUX**, so it
remains authoritative even then. This is precisely why the E-stop is in the power path and
not merely commanding the coil.

**Row 9 — Teensy firmware hang.** Severity **5**, and the single most important row in the
document, because one MCU now holds the loop, throttle, override, and arming. Three layers
need no firmware at all: the hardware RC signal MUX hands steering back, the relay MUX reverts
to STOCK, and the E-stop cuts traction. All three need a **person** to act.

The only *automatic* recovery is a **hardware watchdog**, and the reason is worth knowing.

> [!WARNING]
> **A hung firmware does not stop sending pulses**
>
> It is natural to expect the driver's signal-loss timeout to catch a hang. It does not. The
> servo pulse train is produced by a hardware timer, not by the main loop — so when the loop
> stops, the timer carries on, and the driver keeps receiving the **last commanded width**: a
> perfectly valid signal, at whatever effort was last asked for.
>
> The timeout fires only when pulses actually stop — a reset, a power loss, a pulled lead. What
> turns a hang into one of those is the watchdog, which resets the Teensy; *then* the pulses
> stop and the timeout stops the motors. So the watchdog must be armed at boot and fed **only
> from a completed control-loop iteration** — a watchdog fed from a timer interrupt survives
> exactly the hang it exists for.
>
> This design's own safety document had this wrong until 2026-11-10, and the bench test
> induced a "hang" by holding the reset button — which stops the pulses and so tests a
> different row. **Holding reset is not a hang.**

The pattern: **each of the three hardware layers is independent of the component that
failed.** The watchdog is not quite in that class, and the design says so: it is independent
of the main *loop*, not of the *firmware*. It survives a hang; it does not survive a firmware
that never armed it.

### Staged bring-up

The protocol exists so nobody has to be brave
([safety.md §6](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first)). **Bench
before vehicle; wheels-off before wheels-on; walking pace before anything faster.**

| Stage | What is connected | What you prove |
|---|---|---|
| 0 | Teensy alone, **no motor** | Sensor reads, **no wrap across full travel**, 30 min of USB stability |
| 1 | + steering motor, bench supply | Closed-loop tracking, limits, stall, freewheel, **driver R/C signal-loss timeout**, and the **watchdog under a deliberate hang** |
| 2 | + drive motor, RC bound | Both channels from one master; **both override layers, Layer B with the Teensy halted** |
| 3 | + relay MUX and E-stop | Every failsafe row; default = STOCK on every fault |
| 4 | Full vehicle, wheels on stands | Repeat matrix; no brownout under steering stall |
| 5 | Ground, walking pace, operator alongside | E-stop under motion |

No stage begins until the previous one passes. Autonomy engages only after Stage 5.

---

## Lab

**Goal:** drive by joystick and RC, then deliberately trigger heartbeat-loss and RC-loss
failsafes on the bench and confirm each specified behavior.

> [!CAUTION]
> **Wheels off the ground for this entire lab**
>
> Every test here is a Stage 3 test, except row 8, which repeats Stage 1's deliberate-hang
> test on the assembled vehicle. The vehicle stays on stands. One student keeps a hand
> on the E-stop for the whole session and does nothing else.

### Part 1 — Predict before you test

**Do this before touching anything.** For each row, write down what you think will happen.
Then test. The gap between prediction and observation is the actual learning.

| # | Scenario | Your prediction | Observed | Match? |
|---|---|---|---|---|
| 1 | Command stream stopped (> 500 ms) | | | |
| 2 | USB unplugged (Teensy ↔ laptop) | | | |
| 3 | RC transmitter powered off | | | |
| 4 | Logic-rail brownout | | | |
| 5 | E-stop pressed — **also with the laptop off** | | | |
| 6 | Teensy **held in reset** while a motor is commanded (pulses stop) | | | |
| 7 | Steering commanded past its limit | | | |
| 8 | Firmware **hang** with a motor commanded — the deliberate-hang build, not the reset button | | | |
| 9 | Angle sensor unplugged | | | |

### Part 2 — Manual control

1. **Confirm STOCK first.** With the MUX de-energized, the parent remote must drive the
   vehicle normally. This proves the taps and the authority chain before DBW is involved.
2. **Energize the MUX** to enter DBW. Confirm on telemetry.
3. **RC steering sweep**, no throttle. Watch `steering_angle` track `steering_setpoint` in
   `DbwStatus`.
4. **Joystick teleop** through `ros2_control`. Note that it must have a **dead-man gate** and a
   **software speed cap** — and note *why* the cap exists (the freewheel argument above only
   holds at walking speed).

### Part 3 — Exercise the failsafe matrix

Work all nine rows. Suggested inductions:

```bash
# Row 1 — command staleness
#   stop the publisher; watch DbwStatus.mode go to ESTOP within 500 ms

# Row 2 — USB loss
#   unplug /dev/mitt_dbw. Does steering stop? (Predict first!)

# Row 3 — RC loss
#   power off the transmitter; watch mode and faults

# Row 6 — pulses stop
#   hold the reset button while a motor is commanded.
#   The driver's R/C signal-loss timeout should stop it -- holding reset
#   stops the pulse train, which is exactly what that timeout watches for.
#   If the motor LATCHES
#   at its last command instead, stop the lab and report it -- that is a
#   failed precondition of the architecture, not a tuning issue.

# Row 8 — firmware hang. NOT the reset button: that was row 6.
#   flash the build with the deliberate-hang command (build step 4, section 4.4),
#   command a motor, trigger the hang. Predict first: does the motor stop at once?
#   It should KEEP RUNNING until the hardware watchdog resets the Teensy,
#   and only then stop. Time that gap. If it never stops, the watchdog is
#   not armed or is being fed from the wrong place -- press the E-stop.

# Row 9 — sensor fault
#   unplug the angle sensor; the loop must refuse to run on a bad angle
```

For rows 4, 5 and 7, use the bench supply, the E-stop, and a commanded over-travel.

### Part 4 — The freewheel test

[safety.md §4.4](../design/safety.md#44-test-procedure-freewheel-on-power-loss), steps 1–2:

1. Command a mid-range steering angle; confirm the Teensy holds it.
2. Press the E-stop. Confirm all four:
   traction dead · MUX shows STOCK · steering motor de-energized · **column turns freely by
   hand** with light force.
3. Measure the hand-steer force at the rim with a spring scale: *(measure)* N.
4. **Before releasing the E-stop: transmitter sticks centred, hands off.** Releasing it boots
   the motor driver, which reads the pulse present at that instant as *stop* (see the lecture).

### Part 5 — Authority ladder

Verify the priority order holds, from the bottom up:

| Test | Expected | Observed |
|---|---|---|
| Joystick commands, then take the RC sticks (Layer A) | RC wins, **both axes**, ≤ 200 ms; sticks command an *angle* | *(record)* |
| **Hold the Teensy in reset, then flip the MUX channel (Layer B)** | Transmitter drives the MDDS30 directly, with the controller dead | *(record)* |
| Compare the feel of Layer A vs Layer B | B is raw **effort**, open-loop — noticeably different | *(record)* |
| RC commands, then de-energize the MUX | Reverts to STOCK mid-command | *(record)* |
| Anything commands, then E-stop | Traction cut + STOCK, **works with the laptop off** | *(record)* |

> [!CAUTION]
> **Layer B is the row that matters**
>
> Every other line in this table tests something that also existed under the previous
> architecture. **Layer B is the one that makes a single-MCU design defensible at all**, and
> it is the only one that must be tested with the controller deliberately dead. If you skip
> one test in this module, do not let it be this one.

### Expected output

- A completed prediction-vs-observation table for all nine rows
- At least two predictions that were **wrong** — if all nine matched, you were probably
  reading the matrix while predicting
- Freewheel test passed with the hand-steer force recorded
- Authority ladder verified in order
- **Layer B demonstrated with the Teensy halted**, and the effort-vs-angle difference described
  in your own words

### Check yourself

- [ ] Why is "default de-energized = STOCK" stronger than a software-detected safe mode?
- [ ] The steering motor is on the traction rail. Name two things that would go wrong if it
      were on the logic rail instead.
- [ ] A MUX relay welds closed. What still protects you, and why is it independent?
- [ ] Under what conditions does the "freewheel is acceptable" argument stop holding?
- [ ] Autonomy is the lowest authority in the ladder. Argue for that, then against it.
- [ ] One MCU holds the loop, throttle, override, and arming. List every mitigation that still
      works when its firmware hangs — then say which one you actually tested.
- [ ] Holding the reset button and hanging the firmware both "kill the controller". Why does
      the driver's signal-loss timeout catch one and not the other?
- [ ] The E-stop was pressed mid-turn. What must be true before it is released, and what goes
      wrong if it is not?
- [ ] Pulling the USB cable used to leave steering tracking; now it stops the vehicle. Argue
      which is safer, then say what you would do about operators trained on the other one.
- [ ] Layer B override commands effort, not angle. Name a situation where that difference
      matters, and one where it does not.

---

## Slide outline

1. **Hook** — three controllers, one set of motors. Who wins?
2. **The relay MUX** — NC/NO contacts, default de-energized
3. **Failure direction** — why physics beats software for failing safe
4. **The priority ladder** — and why autonomy sits at the bottom
5. **Two override layers** — RC serial for control, hardware MUX for survival
6. **Converting a software guarantee into a physical one** — what must be executing for this to work?
7. **Reading a failsafe matrix** — rows 1, 2, 5 in detail; why releasing the E-stop is a power-up
8. **Row 2 reversed** — the same cable pull, opposite behaviour, under two reasonable designs
9. **Rail assignment decides freewheel vs. hold** — and the conditions that make freewheel OK
10. **Safety claims are conditional** — change the speed cap, break the argument
11. **FMEA** — rows 8, 9 and 10; a hang is not a reset; independence of mitigations
12. **Staged bring-up** — six stages, no skipping
13. **Lab brief** — predict, then break it on purpose. Kill the controller deliberately.
14. **Looking ahead** — M4: the vehicle is safe to drive; now let it see

---

**Previous:** [M2 — Drive-by-wire & the smart-servo steering loop](m2-dbw-steering.md) · **Next:** [M4 — Perception](m4-perception.md)
