# M2 — Drive-by-Wire & the Smart-Servo Steering Loop

**Learning objectives:**

- Understand closed-loop position control and why the steering loop lives on the Nano.
- Follow the pinned datapath: `MANUAL_CONTROL.roll` → PX4 servo-PWM → Nano → Sabertooth S1.
- Read an absolute angle sensor and convert sensor counts to steering degrees.

**Reference:** [design/dbw.md](../design/dbw.md)

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
setpoint (deg) ──▶( Σ )──▶ [ PID ] ──▶ effort ──▶ [ Sabertooth ] ──▶ [ motor ] ──▶ column
                    ▲ −                                                              │
                    └────────────── measured angle ◀── [ absolute sensor ] ◀─────────┘
```

The Nano runs this loop at **≥100 Hz**. Each iteration: read the most recent setpoint pulse,
read the filtered angle, compute error, output a signed effort.

!!! info "The Sabertooth never hears about angles"

    The Nano commands a **signed effort** — drive left, drive right, stop — which is the
    *output* of the position loop. Angle regulation lives entirely in the Nano. This keeps
    the Sabertooth a dumb, fast power stage, exactly its role in mrover
    ([dbw.md §2.3](../design/dbw.md#23-why-the-sabertooth-drives-the-steering-motor-as-an-effort-command)).

### Why the loop lives on the Nano — ADR E

This is the key decision of the project, and the alternatives were real
([dbw.md §3](../design/dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision)):

| Option | Where the loop runs | Why it was rejected (or chosen) |
|---|---|---|
| **E1 — Nano** ✅ | Dedicated MCU, direct access to sensor and driver | **Chosen.** Deterministic timing, off the laptop↔XRCE↔MAVLink chain |
| E2 — laptop `ros2_control` | In the ROS 2 hardware interface | The servo loop would cross USB every cycle. Latency and jitter scale with laptop load. **Acceptable only if** measured setpoint→actuation latency ≤ **30 ms at p95 over ≥60 s** |
| E3 — inside PX4 | A custom PX4 rover/servo module | Requires PX4 C++ module work, hardest to teach, couples the controller to PX4 release churn |

Notice E2 was not rejected on taste — it was given a **falsifiable acceptance bound**. That
is what a good ADR looks like: the fallback is pre-registered with a number, so if E1 ever
proves impossible at build time, nobody has to re-argue the decision from scratch.

**The consequence is honest and stated:** the Nano's role grows from mrover's *passive sensor
reader* to an *active servo controller*. Firmware complexity rises. The upstream ROS 2 / PX4
interface is unchanged, so nothing else in the stack cares.

### Setpoint rate is not loop rate

A subtlety students consistently trip over.

- PX4 emits the servo frame at **≈50 Hz** (standard servo PWM, configurable higher).
- The Nano's loop runs at **≥100 Hz**.

These are decoupled. Each loop iteration uses the *most recently captured* pulse and the
*current* angle. The loop does not wait for a new setpoint — that is precisely what "reads it
exactly as a hobby servo would" means. A hobby servo does not run at its input frame rate
either.

### Absolute vs. incremental — ADR B

mrover used an **incremental** encoder on the steering, auto-ranging a relative value into
±22.5° at runtime. MRider replaced it with an **absolute** column sensor
([dbw.md §5](../design/dbw.md#5-adr-b-steering-angle-encoding)).

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
detection. It costs nothing (the Nano already has the interrupt pins) and the fusion is
trivial: **absolute = truth, incremental = rate**.

### Which absolute sensor? A pot beats a fancier chip

The obvious modern choice is an AS5600-class magnetic encoder: contactless, 12-bit, I²C, no
wear. It was rejected as the default
([dbw.md §6](../design/dbw.md#6-adr-angle-sensor-technology-potentiometer-vs-as5600-class-magnetic-encoder)).

**Because it is single-turn (0–360°) absolute.** If the *column* — not the road wheel —
rotates more than 360° across lock-to-lock travel, which is common when steering is geared
down, the AS5600 **wraps** and silently loses absolute meaning. You would then need to mount
it on a shaft that sees ≤360°, or add a reduction: more mechanism, to solve a problem the
cheap part does not have.

A single-turn potentiometer maps monotonically across *whatever* travel its shaft sees, as
long as it stays inside one turn. For a ±22.5°-road-wheel column, that is comfortable. It
costs a few dollars, and "voltage is proportional to angle" is trivially teachable.

Its drawbacks are real and managed: wiper wear (acceptable at these duty cycles), and analog
noise (median + low-pass filter in firmware, plus a **ratiometric** reference — feed the pot
from the Nano's own regulated rail so supply drift cancels).

!!! note "The general lesson"

    The more sophisticated component was rejected because its failure mode — silent wraparound
    — was worse than the simpler component's failure mode — gradual wear. **Choose parts by
    how they fail, not by their spec sheet.**

### Counts → degrees

The sensor reports raw ADC counts. Everything downstream needs degrees, with 0° = straight.
Two constants do the whole job
([calibration.md §1](../design/calibration.md#1-steering-zerocenter-and-countsdegrees)):

- **`c0`** — the counts reading when the wheels are physically straight. Found by setting the
  wheels straight by hand with a straightedge, reading counts, and storing it via `C,ZERO`.
  The Nano persists it in EEPROM, so **center survives reboot** — the whole point of ADR B.
- **`k`** — degrees per count, from a two-point fit at full left and full right lock:
  `k = (θ_L − θ_R) / (c_L − c_R)`.

Then `θ = k · (counts − c0)`. Take 3–5 intermediate points to confirm linearity (residual
< ~0.5°); if the pot is nonlinear, store a lookup table instead.

The full chain must then check out: `MANUAL_CONTROL.roll = +1000` → +22.5° commanded → +22.5°
**measured at the road wheels**. Any offset means re-check `c0`.

---

## Lab

**Goal:** command the bench steering rig to a target angle, plot the closed-loop step
response, and measure settling time and steady-state error.

**You need:** the bench steering rig (gearmotor + column + absolute sensor + Nano +
Sabertooth), a bench supply **with a current limit**, and a servo tester or a PX4 emitting
servo PWM.

!!! danger "Current limit first, always"

    A sign error in the effort output makes the loop drive to the mechanical stop at full
    power. A current-limited supply turns that from a broken linkage into a buzz. Set the
    limit before you set a gain.

### Part 1 — Read the sensor (open loop, motor disconnected)

```bash
python3 -m serial.tools.miniterm /dev/mrider_nano 115200
```

1. Turn the column by hand across its full travel. Watch `steer_counts`.
2. **Is it monotonic?** Any reversal or jump means a mounting or wiring problem — fix it now.
3. **Is it stable at rest?** Record the peak-to-peak jitter over 10 seconds.

| Measurement | Value |
|---|---|
| Counts at full left | *(measure)* |
| Counts at center (by straightedge) — this is `c0` | *(measure)* |
| Counts at full right | *(measure)* |
| Jitter at rest, peak-to-peak | *(measure)* counts |
| Column travel, lock to lock | *(measure)* ° |

!!! danger "Do not proceed with a noisy reading"

    Jitter here becomes loop dither later — the motor buzzes at rest and you will misdiagnose
    it as a PID problem for a long time. Fix the filtering, the ratiometric reference, and the
    cable routing first.

### Part 2 — Calibrate counts → degrees

1. Set the wheels straight with a straightedge; record `c0`; store it with `C,ZERO`.
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

**Capture step responses.** Log `setpoint_deg` and `steer_deg` at ≥50 Hz for a 0° → 10° step.

| Gain set | `Kp` | `Ki` | `Kd` | Settling time (ms) | Overshoot (°) | Steady-state error (°) |
|---|---|---|---|---|---|---|
| P only, low | | | | *(measure)* | *(measure)* | *(measure)* |
| P raised | | | | *(measure)* | *(measure)* | *(measure)* |
| P + D | | | | *(measure)* | *(measure)* | *(measure)* |
| Final | | | | *(measure)* | *(measure)* | *(measure)* |

**Target:** steady-state error ≤ 1°, no sustained oscillation.

### Part 4 — Verify the loop rate

Do not assume ≥100 Hz because the code says so. Toggle a spare pin each iteration and scope
it, or count iterations per second and report it in a diagnostic frame.

Measured loop rate = *(measure)* Hz.

### Part 5 — Break it on purpose

| Test | Expected behavior | Observed |
|---|---|---|
| Unplug the PWM setpoint mid-hold | `status` bit0 clears; motor de-energizes; column holds by friction | *(record)* |
| Command past the mechanical stop | Effort clamps **toward center only**; stall bit sets | *(record)* |
| Block the column by hand under effort | Stall detected (encoder velocity ≈ 0 under effort) | *(record)* |
| Cut motor power mid-hold | Column freewheels — turns freely by hand | *(record)* |

The last one is the [safety.md §4.4](../design/safety.md#44-test-procedure-freewheel-on-power-loss)
freewheel test, and M3 explains why that behavior was chosen.

### Expected output

- A counts-vs-angle plot that is linear through `(c0, 0)`, residual < ~0.5°
- At least four step-response plots showing the effect of each gain change
- Loop rate confirmed ≥ 100 Hz **by measurement**
- All four failure behaviors observed and described

### Check yourself

- [ ] Why can the loop run at 100 Hz when setpoints only arrive at 50 Hz?
- [ ] Your `c0` is off by 50 counts. What symptom appears in the M1 command-trace lab?
- [ ] Why was the AS5600 rejected, and under what condition would it be the right choice?
- [ ] What would fail if the loop ran on the laptop and the laptop hit 100% CPU?
- [ ] The column holds instead of freewheeling on power cut. What does that tell you about
      the motor, and which safety analysis must be redone?

---

## Slide outline

1. **Hook** — a stock column has no servo. Build one from a motor, a sensor, and math.
2. **Open loop vs. closed loop** — one diagram, one disturbance
3. **The loop equation** — error, effort, iterate
4. **ADR E: where does the loop live?** — three options in a table
5. **E2's falsifiable bound** — ≤30 ms p95: what a good rejected alternative looks like
6. **Setpoint rate ≠ loop rate** — 50 Hz in, 100 Hz around
7. **ADR B: absolute vs. incremental** — the homing-every-boot problem
8. **The AS5600 trap** — single-turn wraparound, and choosing parts by failure mode
9. **Counts → degrees** — `c0`, `k`, and why center lives in EEPROM
10. **Lab brief** — read, calibrate, close, tune, break
11. **Looking ahead** — M3: now that it moves, who is allowed to move it?

---

**Previous:** [M1 — Intro to MRider & ROS 2](m1-ros2-intro.md) · **Next:** [M3 — Manual/teleop control & safety](m3-teleop-safety.md)
