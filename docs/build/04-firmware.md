# 4. Firmware Bring-up: Nano Smart-Servo + PX4

**Goal:** flash and configure the two controllers that close the DBW loops.

Flash the Arduino Nano smart-servo firmware (reads the absolute angle sensor + encoders,
closes the steering position loop, drives Sabertooth S1 from a PX4 servo-PWM setpoint).
Flash and configure PX4 on the Pixhawk 6C (rover setup, RC binding, servo-PWM outputs,
failsafes). Confirm the pinned datapath: `MANUAL_CONTROL.roll` → PX4 servo-PWM → Nano.

- **Prerequisites:** Section 3 complete; Sabertooth in independent R/C (PWM) mode.
- **Specification:** [design/dbw.md](../design/dbw.md)
- **Expected outcome:** Nano closes a bench steering loop to a commanded angle; PX4 arms
  and emits steering/throttle PWM; RC override verified.

!!! warning "Draft — not yet validated on hardware"

    The firmware described here has not been written or flashed. PID gains, the exact PX4
    parameter set, and the output-channel map are marked *(measure during bring-up)* or
    *(record)*. The interface contract it must satisfy — rates, ranges, serial framing — **is**
    pinned in [dbw.md §12](../design/dbw.md#12-numeric-interface-contract) and is not a draft.

This step covers **Stages 0–2** of the
[bring-up protocol](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first).

---

## 4.1 The datapath you are building

Exactly one steering path exists. There is no alternate, and no direct laptop→Nano steering
link ([ADR E](../design/dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision)):

```
laptop /mrider/cmd  ──XRCE-DDS──▶  PX4 (ManualControlSetpoint.roll, [-1000,+1000])
                                          │
                                PX4 rover: roll → servo output
                                          │  servo PWM 1000–2000 µs (1500 µs = 0°)
                                          ▼
                              Arduino Nano  ── reads PWM like a hobby servo
                                          │  ── closes position loop ≥100 Hz vs. absolute column sensor
                                          │  ── outputs signed effort as PWM
                                          ▼
                              Sabertooth 2x32  S1 → M1 → steering gearmotor
```

!!! info "Why this matters for safety, not just architecture"

    Because steering flows *through* PX4, an RC transmitter bound to the Pixhawk overrides
    **both** steering and throttle using PX4's standard RC override — with no separate wiring
    to the Nano. That is a direct payoff of pinning a single datapath
    ([safety.md §1.2](../design/safety.md#12-live-override-inside-dbw-mode-rc-via-px4)).

**Setpoint rate ≠ loop rate.** PX4 emits the servo frame at ≈50 Hz. The Nano's control loop
runs at ≥100 Hz, using the *most recent* captured pulse and the *current* angle each
iteration. The two are decoupled — that is what "reads it exactly as a hobby servo would"
means.

## 4.2 Stage 0 — Nano firmware alone, no motor wired

**Nothing is connected to Sabertooth S1 yet.** This stage proves the sensing and framing
before any actuator can respond to a bug.

The Nano firmware grows from the mrover encoder reader (`code/code.ino`) by adding five
blocks ([dbw.md §10.3](../design/dbw.md#103-new-firmware-blocks-added-for-adr-e)):

1. **PWM input capture** on an interrupt pin — measure the servo pulse width (1000–2000 µs),
   map to setpoint degrees.
2. **Absolute-sensor read** — ADC read of the column pot, median + low-pass filter,
   counts→degrees.
3. **Position PID** at ≥100 Hz — error = setpoint − measured, output = signed effort.
4. **Motor output** — effort → PWM on the S1 line (1500 µs = stop, ± toward each lock).
5. **Safety interlocks** — PWM setpoint absent → hold last safe/center; at mechanical limit →
   clamp effort toward center only.

**Build and flash:**

```bash
# Nano V3 = ATmega328P, "Old Bootloader" on many clones
arduino-cli compile --fqbn arduino:avr:nano:cpu=atmega328old firmware/mrider_nano
arduino-cli upload  --fqbn arduino:avr:nano:cpu=atmega328old -p /dev/ttyUSB0 firmware/mrider_nano
```

**Verify the feedback frame.** The Nano emits one line per `\n` at **≥20 Hz**, 115200 baud
([dbw.md §10.1](../design/dbw.md#101-primary-transport-usb-serial-115200-baud)):

```
F,<steer_deg>,<steer_counts>,<drive_ticks>,<drive_rpm>,<setpoint_deg>,<status>\n
```

| Field | Meaning |
|---|---|
| `steer_deg` | absolute column angle, degrees (float, +left/−right per calibration) |
| `steer_counts` | raw absolute-sensor counts (calibration/debug) |
| `drive_ticks` | cumulative drive-encoder ticks (int32, 52 PPR) |
| `drive_rpm` | drive motor RPM |
| `setpoint_deg` | the setpoint the Nano is tracking, decoded from PX4 servo PWM |
| `status` | bitfield: bit0 setpoint-valid (PWM present), bit1 at-limit, bit2 stall-detected |

```bash
# Watch raw frames
python3 -m serial.tools.miniterm /dev/ttyUSB0 115200

# Confirm the rate is >= 20 Hz
timeout 10 cat /dev/ttyUSB0 | grep -c '^F,'   # expect >= 200
```

**Stage 0 checks:**

- [ ] Frames arrive at ≥20 Hz, well-formed, one per line
- [ ] `steer_counts` changes smoothly and monotonically as the column is turned by hand
- [ ] `steer_counts` is **stable** when the column is still — jitter here becomes loop dither
- [ ] Feeding a bench servo tester into the PWM input pin moves `setpoint_deg` across its range
- [ ] With the servo tester unplugged, `status` bit0 clears
- [ ] Turning the drive wheel by hand increments `drive_ticks`

!!! danger "Do not proceed with a noisy angle reading"

    The absolute sensor is the authority for the entire system. If `steer_counts` jitters at
    rest, fix it now — check the ratiometric reference, the filtering, and the cable routing.
    A noisy sensor feeding a position loop produces a motor that hunts, and you will
    misdiagnose it as a PID tuning problem for a long time.

## 4.3 Stage 1 — steering motor on the bench, current-limited

Wire Sabertooth S1 ← Nano and M1 → steering gearmotor, on a **bench supply with the current
limit turned down**. The current limit is what turns a sign error into a buzz instead of a
broken linkage.

!!! danger "Check the effort sign before closing the loop"

    With the loop **disabled**, command a small fixed positive effort and confirm the column
    moves in the direction that *reduces* a positive error. If the sign is inverted, the
    position loop will drive to the mechanical stop at full effort the instant you enable it.
    Verify this open-loop, at low current limit, every time you re-wire.

**Tune the position loop:**

1. Start with P only, low gain. Command a small step. The column should move toward the
   setpoint and stop short.
2. Raise P until the response is brisk with slight overshoot, then back off.
3. Add D to damp the overshoot. Add I only if a steady-state offset persists — integral wind-up
   against a mechanical limit is its own hazard, so clamp it.
4. Confirm the loop actually runs at ≥100 Hz. Instrument it: toggle a spare pin each iteration
   and scope it, or count iterations per second and report it in a diagnostic frame.

**Record sheet — steering loop**

| Parameter | Value |
|---|---|
| `Kp` | *(measure during bring-up)* |
| `Ki` | *(measure during bring-up)* |
| `Kd` | *(measure during bring-up)* |
| Measured loop rate | *(measure during bring-up)* Hz — target ≥100 |
| Step response settling time | *(measure during bring-up)* ms |
| Steady-state error | *(measure during bring-up)* ° — target ≤ 1° |
| Overshoot | *(measure during bring-up)* ° |
| Bench supply current limit used | *(record)* A |

**Stage 1 checks** ([safety.md Stage 1](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first)):

- [ ] Closed-loop position tracking at ≥100 Hz, no runaway
- [ ] Limit-clamp works — at a mechanical stop, effort is clamped **toward center only**
- [ ] Stall detection sets `status` bit2 (encoder velocity ≈ 0 under applied effort)
- [ ] Setpoint-loss interlock: unplug the PWM input mid-hold → bit0 clears, motor de-energizes
- [ ] Freewheel on power cut: kill motor power, confirm the column turns freely by hand
      ([safety.md §4.4](../design/safety.md#44-test-procedure-freewheel-on-power-loss) steps 1–2)
- [ ] Hardware watchdog: force a firmware hang, confirm the Nano resets and outputs neutral
      (1500 µs) — [FMEA row 9](../design/safety.md#7-fmea-lightweight)

## 4.4 Stage 2 — PX4 on the Pixhawk 6C

**Airframe.** Select the PX4 **Rover** (Ackermann) frame, so `MANUAL_CONTROL.roll` → steering
servo and `.throttle` → drive mapping holds as the bridge expects
(`mavlink_bridge.py:122-124`).

**Version pinning is mandatory, not optional.** Record the exact PX4 version tag and export
the full parameter set. Do **not** float on `main` — the `roll`→servo-PWM behavior is exactly
the kind of thing that drifts upstream
([dbw.md §9](../design/dbw.md#9-pixhawk-6c-px4-rover-configuration-and-version-pinning)).

```bash
# Record what you actually flashed
#   QGroundControl → Vehicle Setup → Summary → Firmware Version
#   QGroundControl → Parameters → Tools → Save to file
cp px4_params.params config/calibration/px4_params_<version>.params
```

**Record sheet — PX4 configuration**

| Item | Value |
|---|---|
| PX4 version tag | *(record — pin this)* |
| Airframe | Rover (Ackermann) |
| Parameter file | `config/calibration/px4_params_<version>.params` |
| Steering servo output channel | *(record)* |
| Throttle output channel → Sabertooth S2 | *(record)* |
| Servo PWM range | 1000–2000 µs, 1500 µs = 0° |
| Servo output rate | *(record)* Hz — ≈50 nominal |
| RC protocol | *(record: SBUS / ACCESS / CRSF)* |
| `COM_RC_LOSS_T` | *(record)* s |
| RC-loss failsafe action | Hold / Disarm — *(record)* |
| Offboard-loss failsafe action | *(record)* |
| Board rotation (`SENS_BOARD_ROT`) | *(record — wrong value corrupts yaw)* |

!!! note "The custom wheel-encoder PX4 fork is probably unnecessary now"

    mrover used a forked PX4 (`jomidokunMain/PX4-Autopilot`, branch `wheelEncoder`) to carry
    encoder data up through `WHEEL_DISTANCE`. MRider reroutes feedback to Nano→USB
    ([ADR-SW1](../design/software.md#adr-sw1-reroute-feedback-off-mavlink)), so that module
    is **no longer required for steering feedback**. Prefer a **stock PX4 rover build** —
    simpler to maintain and to teach. Record which you chose and why.

**Bind and configure RC.** This is your live override authority. Bind the receiver, verify
every channel maps correctly, and confirm the RC-loss failsafe action.

**Calibrate the IMU now**, while the vehicle is accessible: accel/gyro/mag calibration in
QGroundControl, level horizon, and — critically — set `SENS_BOARD_ROT` to match how the
Pixhawk is physically mounted. Wrong board rotation corrupts yaw, and you will chase it
through SLAM in step 8 instead of finding it here
([calibration.md §5](../design/calibration.md#5-imu-calibration)). Photograph the mounting
orientation alongside the parameter value.

## 4.5 Stage 2 integration — the full pinned datapath

Drive motor connected to the bench (wheels off), Sabertooth in independent R/C (PWM) mode.

1. **Steering end-to-end.** Send `MANUAL_CONTROL.roll` and confirm the chain: roll →
   PX4 servo PWM → Nano `setpoint_deg` → column moves → `steer_deg` converges.
2. **Normalization spot-check.** `roll = +1000` → `+22.5°`; `roll = −1000` → `−22.5°`;
   `roll = 0` → `0°` (1500 µs). Full calibration happens in
   [step 6](06-bench-test.md), but a gross error should be caught now.
3. **Throttle end-to-end.** `.throttle` → PX4 PWM → Sabertooth S2 → drive motor spins.
4. **Independent masters, no bus conflict.** Command steering and throttle simultaneously and
   confirm neither disturbs the other — the proof of
   [the R/C-mode ADR](../design/dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-mode-per-channel-masters).
5. **RC override preemption.** With the laptop commanding, take the RC sticks. The transmitter
   must win on **both** axes immediately.
6. **Sabertooth signal-loss failsafe.** Unplug S1, then S2. Each channel must stop its own
   motor on the Sabertooth's built-in R/C timeout — a free layer of the failsafe stack
   ([failsafe matrix row 6](../design/safety.md#2-failsafe-matrix)).

**Record sheet — datapath verification**

| Test | Expected | Observed | Pass |
|---|---|---|---|
| `roll=+1000` → steering | ≈ +22.5° | *(record)* | ☐ |
| `roll=−1000` → steering | ≈ −22.5° | *(record)* | ☐ |
| `roll=0` → steering | 0° (1500 µs) | *(record)* | ☐ |
| `.throttle` → drive motor | spins proportionally | *(record)* | ☐ |
| Simultaneous steer + throttle | no interaction | *(record)* | ☐ |
| RC override, both axes | TX preempts laptop | *(record)* | ☐ |
| S1 unplugged | steering motor stops | *(record)* | ☐ |
| S2 unplugged | drive motor stops | *(record)* | ☐ |
| Setpoint stream stopped (<10 Hz) | PX4 failsafe, throttle → 0 | *(record)* | ☐ |

!!! note "If PX4 servo-PWM emission blocks you"

    A documented contingency exists: drive the Nano steering setpoint **directly** from the
    laptop (Arduino-direct), keeping PX4 for IMU/EKF/RC
    ([software.md §6](../design/software.md#6-px4-firmware-pinning-and-fallback)). This
    trades away the single-pinned-path property — and with it, free RC override on steering —
    so it is a schedule-risk contingency, not a preference. If you take it, you must
    re-analyze [safety.md §1.2](../design/safety.md#12-live-override-inside-dbw-mode-rc-via-px4)
    and provide steering override another way.

## 4.6 Gate to step 5

- [ ] Nano feedback frames well-formed at ≥20 Hz; angle reading stable at rest
- [ ] Position loop closes at ≥100 Hz; gains recorded; settling and steady-state error logged
- [ ] Effort sign verified open-loop; limit-clamp and stall detect working
- [ ] Setpoint-loss and watchdog interlocks verified
- [ ] Freewheel-on-power-cut confirmed (or, for a wiper-motor build, hold-on-power-cut
      **re-analyzed** against [safety.md §4](../design/safety.md#4-steering-motor-power-rail-assignment-and-power-loss-behavior-pinned))
- [ ] PX4 version tag pinned; parameter file exported to `config/calibration/`
- [ ] `SENS_BOARD_ROT` set and mounting photographed
- [ ] RC bound; override preempts the laptop on both axes
- [ ] Full pinned datapath verified end-to-end; independent-master operation confirmed
- [ ] Sabertooth signal-loss failsafe confirmed on both channels

---

**Previous:** [3. Electrical & wiring](03-electrical.md) · **Next:** [5. Software install](05-software.md)
