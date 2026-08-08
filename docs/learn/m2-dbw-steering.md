# M2 — Drive-by-Wire & the Steering Position Loop

**Learning objectives:**

- Understand closed-loop position control and why the steering loop lives on the MCU.
- Follow the pinned datapath: `DbwCommand` → micro-ROS → Teensy loop → Sabertooth M1.
- Read an absolute angle sensor and convert sensor counts to steering radians.
- Explain why the sensor is mounted **load-side** and what that excludes from the measurement.

**Reference:** [design/dbw.md](../design/dbw.md)

!!! info "Architecture updated 2026-08-07"

    This module previously taught a two-controller datapath (`MANUAL_CONTROL.roll` → PX4
    servo-PWM → Arduino Nano). MRider now uses a **single Teensy 4.1 running micro-ROS**
    ([D3](../design/adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07)). The
    control theory in this module is unchanged — a position loop is a position loop — but the
    PWM-capture step is gone: the setpoint is a typed ROS 2 message the loop reads directly.

    **This is worth teaching as a design lesson in itself.** That PWM round trip existed only
    because the setpoint had to cross from one board to another. Removing a board removed an
    entire class of firmware, and a whole category of debugging.

!!! warning "Draft — lab not yet run on hardware"

    The lecture content is grounded in [dbw.md](../design/dbw.md), which is authoritative. The
    **lab requires a bench steering rig that has not yet been built**, and no step-response
    data from a real MRider exists. Expected values below are marked *(measure)* — the lab
    produces them rather than confirming them.

---

## Lecture

### The one genuinely new control problem

Almost everything in MRider is reused from mrover. Exactly two things are new, and the
steering position loop is the interesting one.

A stock ride-on column has **no servo**. It is turned by hand, or by a dumb DC gearmotor that
the parent remote drives open-loop — press left, the motor runs left, release, it stops.
There is no notion of "go to 12 degrees."

Mapping and navigation need exactly that notion. So MRider must build a servo out of parts:
a gearmotor, an angle sensor, and a controller that closes the gap between them.

### Open loop vs. closed loop, concretely

**Open loop:** apply effort, hope. The stock parent remote works this way. If the tires bind
on carpet, the wheels move less than expected, and nothing notices.

**Closed loop:** measure the actual angle, compute the error, apply effort proportional to
it, repeat fast. Disturbances — tire scrub, a slope, a bump — are rejected automatically,
because they show up as error.

```
setpoint (rad) ──▶( Σ )──▶ [ PID ] ──▶ effort ──▶ [ Sabertooth ] ──▶ [ motor ] ──▶ column
                    ▲ −                                                              │
                    └────────────── measured angle ◀── [ absolute sensor ] ◀─────────┘
```

The Teensy runs this loop at **≥ 200 Hz**. Each iteration: read the most recent setpoint from
the subscription, read the filtered angle, compute error, output a signed effort.

!!! info "The Sabertooth never hears about angles"

    The Teensy commands a **signed effort** — drive left, drive right, stop — which is the
    *output* of the position loop. Angle regulation lives entirely in the Teensy. This keeps
    the Sabertooth a dumb, fast power stage, exactly its role in mrover
    ([dbw.md §2.3](../design/dbw.md#23-why-the-sabertooth-receives-an-effort-command)).

### Why the loop lives on the MCU — ADR E

This is the key decision of the project, and the alternatives were real
([dbw.md §3](../design/dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision)):

| Option | Where the loop runs | Why it was rejected (or chosen) |
|---|---|---|
| **E1 — the MCU** ✅ | Dedicated MCU, direct access to sensor and driver | **Chosen.** Deterministic timing, off a USB link whose latency varies with laptop load |
| E2 — laptop `ros2_control` | In the ROS 2 hardware interface | The servo loop would cross USB every cycle. Latency and jitter scale with laptop load. **Acceptable only if** measured setpoint→actuation latency ≤ **30 ms at p95 over ≥60 s** |
| E3 — inside PX4 | A custom PX4 rover/servo module | Moot now that there is no PX4; kept in the record as rejected |
| E4 — motion-controller board | A Kangaroo-class daughterboard that self-tunes | **Pre-registered fallback**, not primary — it adds a part and replaces the best teaching artifact with a black box |

Notice E2 was not rejected on taste — it was given a **falsifiable acceptance bound**, and E4
has a **pre-registered trigger**: if the loop cannot hold ≤ 1° steady-state at bring-up Stage 1,
adopt E4 rather than tuning without bound. That is what a good ADR looks like. Firmware tuning
is unbounded work, so the decision to stop is made *in advance*, on a number, by someone not yet
frustrated.

!!! warning "One argument for E2 evaporated on inspection"

    Earlier drafts credited E2 with "maximum reuse of mrover's `carlikebot_system.cpp`". Someone
    eventually opened that file. It is the **unmodified upstream demo stub**: `read()` assigns
    `state.position = command.position` — echoing the command back as the measurement — and
    `write()` only logs. Both sit under the upstream comment *"Please do not copy to your
    production code."*

    So mrover's steering controller was wired to a mock, and E2's reuse advantage never existed.
    **Verify the code behind a reuse claim before you weigh it.** A citation is not evidence.

### Setpoint rate is not loop rate

A subtlety students consistently trip over.

- The laptop publishes setpoints at **≥ 50 Hz**.
- The Teensy's loop runs at **≥ 200 Hz**.

These are decoupled. Each loop iteration uses the *most recent* setpoint and the *current*
angle. The loop does not wait for a new setpoint.

!!! danger "But there is a third rate, and forgetting it silently caps everything"

    The loop can only act as fast as its **output** reaches the motor driver. The earlier design
    pinned a ≥ 100 Hz loop but never pinned the output frame rate — and with the standard Arduino
    `Servo` library, effort commands arrived at the driver at ~50 Hz. The loop ran twice as fast
    as anything could act on.

    MRider has *not* fully escaped this — the override hardware forces R/C PWM output, so the
    ceiling is real and the interface contract now says **measure it at Stage 1 and pin it**
    rather than asserting a number. **Ask of any control loop: how fast does the output actually
    leave?**

### Absolute vs. incremental — ADR B

mrover used an **incremental** encoder on the steering, auto-ranging a relative value into
±22.5° at runtime. MRider replaced it with an **absolute, load-side** sensor
([dbw.md §5](../design/dbw.md#5-adr-b-steering-angle-encoding)).

Worse than "it drifts": mrover's mapping was rewritten *retroactively*. Its bridge expands the
observed min/max **at runtime** and rescales past values, so the same raw reading meant
different angles at different times in the same session.

| | Incremental (mrover) | Absolute (MRider) |
|---|---|---|
| Angle at power-on | Unknown — **needs homing every boot** | Known immediately |
| After a linkage slip | Reference lost silently | Still correct |
| After a power glitch | Reference lost | Still correct |
| "Center" | Drifts with the observed min/max range | Fixed, stored in EEPROM |

mrover's runtime auto-ranging (`min_value=-600`, `max_value=180`) is exactly the weakness: the
center depends on what range the system happened to observe. For a research platform used by a
second, less careful driver, that is fragile.

The motor's incremental encoder is *kept* — as an auxiliary source for velocity and stall
detection. It costs nothing (the Teensy has four hardware quadrature decoders) and the fusion
is trivial: **absolute = truth, incremental = rate**.

### Where you mount it decides what you can measure

Before choosing a sensor, choose a **shaft**. ADR B mounts the absolute sensor **load-side** —
downstream of the steering gearbox, on the kingpin or the linkage — not on the motor.

That choice determines what the measurement contains:

| Mounting | What it measures | What it hides |
|---|---|---|
| Motor shaft | What the *motor* did | Gearbox backlash, coupling slip — as **invisible bias** |
| **Load side** ✅ | What the *road wheels* did | Nothing. Backlash shows up as **measured error** |

A sensor exists to catch the errors you cannot predict. Mounting it upstream of the mechanism
most likely to introduce them defeats the purpose. **Put the sensor where the truth is, not
where it is convenient to mount.**

### Which absolute sensor? The mounting point decides

Both candidates are absolute and both cost a few dollars, so the choice turns on a failure
mode ([dbw.md §6](../design/dbw.md#6-adr-angle-sensor-technology-magnetic-encoder-vs-potentiometer)).

An **AS5600-class magnetic encoder** is contactless, 12-bit, I²C, with no wiper to wear — a
real advantage for a steering servo, which spends its life making small, high-duty-cycle
oscillations exactly where a pot wiper would wear a flat spot. But it is **single-turn
(0–360°) absolute**. If its shaft rotates past one turn, it **wraps** and silently reports a
wrong angle — which then feeds a position loop that drives a motor. That is a severity-5
failure, and *silent* is what makes it severe.

A **single-turn potentiometer** maps monotonically across whatever travel its shaft sees,
within one turn. It costs analog filtering, a ratiometric reference, and wiper wear.

!!! success "Notice how the earlier decision resolved itself"

    An earlier draft of this course pinned the **potentiometer**, reasoning that a steering
    *column* is often geared down past one full turn, so the AS5600 would wrap.

    That reasoning was correct — **for a sensor on the column.** Once ADR B moved the sensor
    load-side, where total travel is ±22.5°, wrap became *mechanically impossible*, and the
    objection dissolved. The magnetic encoder became the default; the pot stayed as the
    fallback for chassis where no shaft under 340° is reachable.

    **A component debate that will not resolve is often a mounting debate in disguise.** The
    two options were never really "pot vs. encoder" — they were "which shaft?", and answering
    that answered the other.

!!! note "The general lesson survives, sharpened"

    You still **choose parts by how they fail, not by their spec sheet** — the AS5600 is only
    acceptable because its failure mode was engineered out mechanically, not because its specs
    are better. And because *silent* wrong is worse than *noisy* wrong, the firmware
    range-checks the sensor every loop and refuses to run on an implausible angle.

    Which is why the very first bench step is: rotate the shaft lock-to-lock and confirm the
    reading never jumps.

### Counts → radians

The sensor reports raw counts (I²C for the magnetic encoder, ADC for the pot fallback).
Everything downstream needs radians, with 0 = straight.
Two constants do the whole job
([calibration.md §1](../design/calibration.md#1-steering-zerocenter-and-countsdegrees)):

- **`c0`** — the counts reading when the wheels are physically straight. Found by setting the
  wheels straight by hand with a straightedge, reading counts, and storing it via `C,ZERO`.
  The Teensy persists it in EEPROM, so **center survives reboot** — the whole point of ADR B.
- **`k`** — degrees per count, from a two-point fit at full left and full right lock:
  `k = (θ_L − θ_R) / (c_L − c_R)`.

Then `θ = k · (counts − c0)`. Take 3–5 intermediate points to confirm linearity (residual
< ~0.5°); if the sensor is nonlinear over the working range, store a lookup table instead.

The full chain must then check out: `MANUAL_CONTROL.roll = +1000` → +22.5° commanded → +22.5°
**measured at the road wheels**. Any offset means re-check `c0`.

---

## Lab

**Goal:** command the bench steering rig to a target angle, plot the closed-loop step
response, and measure settling time and steady-state error.

**You need:** the bench steering rig (gearmotor + column + absolute sensor + Teensy +
Sabertooth), a bench supply **with a current limit**, and a laptop running the micro-ROS agent
so you can publish setpoints as `DbwCommand` messages.

!!! danger "Current limit first, always"

    A sign error in the effort output makes the loop drive to the mechanical stop at full
    power. A current-limited supply turns that from a broken linkage into a buzz. Set the
    limit before you set a gain.

### Part 1 — Read the sensor (open loop, motor disconnected)

```bash
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/mitt_dbw -b 115200
ros2 topic echo /mitt/dbw/status
```

1. Turn the column by hand across its **full** travel. Watch the raw counts.
2. **Is it monotonic?** Any reversal or jump is a mounting or wiring problem — fix it now.
   On a magnetic encoder a jump may be a **wrap**, which means the sensor is on a shaft that
   turns more than once. That is not a calibration issue; it is the wrong shaft.
3. **Is it stable at rest?** Record the peak-to-peak jitter over 10 seconds.

| Measurement | Value |
|---|---|
| Counts at full left | *(measure)* |
| Counts at center (by straightedge) — this is `c0` | *(measure)* |
| Counts at full right | *(measure)* |
| Jitter at rest, peak-to-peak | *(measure)* counts |
| **Sensed-shaft travel, lock to lock** | *(measure)* ° — must be ≤ 340° for a single-turn encoder |
| Road-wheel travel, lock to lock | *(measure)* ° |

!!! danger "Do not proceed with a noisy reading"

    Jitter here becomes loop dither later — the motor buzzes at rest and you will misdiagnose
    it as a PID problem for a long time. Fix the filtering, the cable routing, and (on the pot
    fallback) the ratiometric reference first.

    Also run the motor near the sensor while watching the reading. A magnetic encoder sitting
    next to a DC motor can pick up its field, and that failure looks exactly like bad tuning.

### Part 2 — Calibrate counts → radians

1. Set the wheels straight with a straightedge; record `c0`; store it via the zeroing service.
2. Full left → record `(θ_L, c_L)` with a digital angle gauge **on the road wheel**, not the
   column.
3. Full right → record `(θ_R, c_R)`.
4. Compute `k = (θ_L − θ_R) / (c_L − c_R)`.
5. Take three intermediate points; compute the residual against your linear fit.

**Plot** measured angle vs. counts. It should be a straight line through `(c0, 0)`. Report
`k` and the maximum residual.

### Part 3 — Close the loop

Connect the motor. Current limit on. **Verify the effort sign open-loop first**: command a
small fixed positive effort and confirm the column moves in the direction that *reduces* a
positive error. Then enable the loop.

Tune in this order:

1. **P only**, low. Step the setpoint. It should move toward target and stop short.
2. Raise `Kp` until brisk with slight overshoot, then back off.
3. Add `Kd` to damp the overshoot.
4. Add `Ki` **only** if a steady-state offset persists — and clamp it, because integral
   wind-up against a mechanical limit is its own hazard.

**Capture step responses.** Record `/mitt/dbw/status` in a bag and plot `steering_setpoint`
against `steering_angle` for a 0° → 10° step. Both fields are in the same message, on the same
clock — no correlation across logs required.

| Gain set | `Kp` | `Ki` | `Kd` | Settling time (ms) | Overshoot (°) | Steady-state error (°) |
|---|---|---|---|---|---|---|
| P only, low | | | | *(measure)* | *(measure)* | *(measure)* |
| P raised | | | | *(measure)* | *(measure)* | *(measure)* |
| P + D | | | | *(measure)* | *(measure)* | *(measure)* |
| Final | | | | *(measure)* | *(measure)* | *(measure)* |

**Target:** steady-state error ≤ 1°, RMS ≤ 1.5° over a ±20° sweep, 10° step to 90% in ≤ 400 ms,
overshoot ≤ 15%.

!!! info "If you cannot hit it, that is a result — not a failure"

    These numbers are the [pre-registered E4 trigger](../design/dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision).
    If the loop will not hold ≤ 1° with no sustained oscillation, the project's own rule is to
    **stop tuning and adopt the motion-controller fallback**. Record your best gains and the
    numbers they produced, and say so. Deciding in advance when to quit is what stops firmware
    tuning from consuming a semester.

### Part 4 — Verify the loop rate

Do not assume ≥ 200 Hz because the code says so. Toggle a spare pin each iteration and scope
it, or count iterations per second and report it in `DbwStatus`.

Then measure the rate that actually matters: **how often an effort command reaches the
Sabertooth.** Scope the serial line. A fast loop feeding a slow output is a slow system.

| Rate | Target | Measured |
|---|---|---|
| Control loop | ≥ 200 Hz | *(measure)* |
| **Actuation frame to the driver** | *measure, then pin* | *(measure)* |

### Part 5 — Break it on purpose

| Test | Expected behavior | Observed |
|---|---|---|
| Stop the setpoint publisher mid-hold | Staleness > 500 ms → `ESTOP`; steering centered, then de-energized | *(record)* |
| Halt the Teensy mid-hold | Sabertooth **serial timeout** stops the motor | *(record)* |
| Unplug the angle sensor mid-hold | Loop refuses to run on a bad angle; fault bit sets | *(record)* |
| Command past the mechanical stop | Effort clamps **toward center only**; stall bit sets | *(record)* |
| Block the column by hand under effort | Stall detected (encoder velocity ≈ 0 under effort) | *(record)* |
| Cut motor power mid-hold | Column freewheels — turns freely by hand | *(record)* |

The last one is the [safety.md §4.4](../design/safety.md#44-test-procedure-freewheel-on-power-loss)
freewheel test, and M3 explains why that behavior was chosen.

### Expected output

- A counts-vs-angle plot that is linear through `(c0, 0)`, residual < ~0.5°
- At least four step-response plots showing the effect of each gain change
- Loop rate **and actuation frame rate** confirmed by measurement
- Sensed-shaft travel recorded, with no wrap across full travel
- All failure behaviors observed and described

### Check yourself

- [ ] Why can the loop run at 200 Hz when setpoints only arrive at 50 Hz?
- [ ] Your loop runs at 200 Hz but the output frame rate is 50 Hz. What have you actually built?
- [ ] Your `c0` is off by 50 counts. What symptom appears in the M1 command-trace lab?
- [ ] The AS5600 was first rejected, then adopted, with no change to the part. What changed,
      and what does that tell you about how to run a component argument?
- [ ] Why does mounting the sensor load-side change what the *measurement* contains, not just
      where the wire goes?
- [ ] What would fail if the loop ran on the laptop and the laptop hit 100% CPU?
- [ ] The column holds instead of freewheeling on power cut. What does that tell you about
      the motor, and which safety analysis must be redone?

---

## Slide outline

1. **Hook** — a stock column has no servo. Build one from a motor, a sensor, and math.
2. **Open loop vs. closed loop** — one diagram, one disturbance
3. **The loop equation** — error, effort, iterate
4. **ADR E: where does the loop live?** — four options in a table
5. **Falsifiable bounds and pre-registered triggers** — E2's ≤30 ms p95, E4's ≤1° at Stage 1
6. **When a reuse claim does not survive `git show`** — the `carlikebot_system.cpp` stub
7. **Three rates, not two** — setpoint, loop, and the output frame rate that silently caps both
8. **ADR B: absolute vs. incremental** — the homing-every-boot problem, and retroactive rescaling
9. **Mount it load-side** — what the sensor position decides about what you can see
10. **The AS5600 argument, twice** — rejected on the column, adopted on the kingpin, same part
11. **Counts → radians** — `c0`, `k`, and why center lives in EEPROM
12. **Lab brief** — read, calibrate, close, tune, break
13. **Looking ahead** — M3: now that it moves, who is allowed to move it?

---

**Previous:** [M1 — Intro to MRider & ROS 2](m1-ros2-intro.md) · **Next:** [M3 — Manual/teleop control & safety](m3-teleop-safety.md)
