# 4. Firmware Bring-up: Teensy DBW Controller

**Goal:** flash and validate the single controller that closes every DBW loop, in stages, with
the motor disconnected until the software is trustworthy.

- **Prerequisites:** Section 3 complete; Sabertooth DIP switches set for packetized serial;
  isolated logic rail built and verified.
- **Specification:** [design/dbw.md](../design/dbw.md) · [design/safety.md](../design/safety.md)
- **Expected outcome:** the Teensy holds a commanded steering angle against a hand
  disturbance, publishes `DbwStatus` at ≥ 50 Hz with zero USB dropouts over 30 minutes, and
  both override layers are demonstrated.

!!! warning "Draft — not yet validated on hardware"

    This procedure is derived from the design documents. No MRider build has been brought up
    yet, so timings, pin assignments, and library behavior are **unconfirmed**. Treat every
    number as a target to verify, not a measurement.

!!! info "Architecture change"

    This step previously covered two controllers — an Arduino Nano smart-servo *and* a Pixhawk
    running PX4. [Decision D3](../design/adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07)
    replaced both with a single Teensy 4.1 running micro-ROS. If you are following an older
    printout, discard it: there is no PX4, no MAVLink, no servo-PWM capture, and no I²C
    register map in this build.

---

## 4.1 The datapath you are building

One command path, one feedback path, one transport, one clock.

```
laptop  /mitt/dbw/command  (DbwCommand: steering_angle rad, speed m/s)
              │
              │  micro-ROS over USB serial  (micro_ros_agent runs on the laptop)
              ▼
      Teensy 4.1  ── position loop >=200 Hz vs. absolute load-side angle sensor
              │  ── throttle ramp / cap / direction interlock
              │  ── SBUS decode, safety supervisor, watchdog
              ▼
      Sabertooth 2x32  ── packetized serial, single master
              ├── M1 → steering gearmotor
              └── M2 → paralleled rear traction motors

      Teensy  ──▶ /mitt/dbw/status  (measured angle, setpoint, speed, ticks, mode, faults)
```

**Why this matters for debugging.** Command and feedback share one link and one clock, so
`ros2 topic echo /mitt/dbw/status` shows both sides of the loop and `ros2 bag` captures a
complete record. The superseded design split them across four boards and two transports,
which is what made latency and dropout faults nearly impossible to localize.

---

## 4.2 Toolchain setup

```bash
# PlatformIO (firmware)
pip install --user platformio
pio --version

# micro-ROS agent — NOT available in the Humble apt repos, build from source
mkdir -p ~/uros_ws/src && cd ~/uros_ws
git clone -b humble https://github.com/micro-ROS/micro_ros_setup.git src/micro_ros_setup
rosdep install --from-paths src --ignore-src -y
colcon build && source install/local_setup.bash
ros2 run micro_ros_setup create_agent_ws.sh
ros2 run micro_ros_setup build_agent.sh && source install/local_setup.bash
```

!!! danger "Verify this before writing any firmware"

    - [ ] A **`micro_ros_arduino` release exists for Humble** with Teensy 4.1 support.
    - [ ] The transport is **USB serial** — the official package does not ship native
          Ethernet. Accept that, or scope a custom transport deliberately.

    **If no Humble release exists**, fall back to a framed **binary** protocol with CRC and
    sequence numbers over the same USB link — never unframed ASCII
    ([dbw.md §9](../design/dbw.md#9-teensy-41-firmware-platform-and-version-pinning)). The
    architecture does not depend on micro-ROS; only the typed-message convenience does.

Record every version you flashed — this is now the platform's reproducibility claim, since
there is no upstream autopilot provenance to lean on
([software.md §6.3](../design/software.md#63-version-pinning)):

```bash
pio pkg list                     # platform + framework versions
# record micro_ros_arduino release tag, Teensyduino version, agent commit
```

---

## 4.3 Stage 0 — Teensy alone, no motor wired

Corresponds to [safety.md Stage 0](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first).
**Nothing is connected to the Sabertooth yet.**

Wire only: absolute angle sensor (I²C), drive encoder, steering encoder, USB to laptop.

### Verify the angle sensor first, in isolation

```bash
# With a simple sketch printing raw counts, rotate the sensed shaft by hand
# through its FULL mechanical travel and watch for a wrap.
```

!!! danger "The wrap check is not optional"

    The AS5600 is **single-turn absolute**. Rotate the sensed shaft lock-to-lock and confirm
    the reading is **monotonic with no discontinuity**. A wrap here is FMEA row 2, severity 5:
    a garbage angle feeding a position loop that drives a motor.

    If it wraps, you mounted it on the wrong shaft. Move it load-side, or switch to the
    potentiometer fallback. Do not proceed.

Also check for magnetic interference: hold the steering motor near the sensor and confirm the
reading does not shift.

### Bring up micro-ROS

```bash
# Terminal 1 — agent
ros2 run micro_ros_agent micro_ros_agent serial --dev /dev/ttyACM0 -b 115200

# Terminal 2 — confirm the vehicle appears
ros2 topic list | grep mitt
ros2 topic echo /mitt/dbw/status --once
ros2 topic hz /mitt/dbw/status          # target: >= 50 Hz
```

### The 30-minute stability run

```bash
ros2 topic hz /mitt/dbw/status > /tmp/dbw_hz.log 2>&1 &
sleep 1800 && kill %1
```

!!! warning "USB dropouts are a blocking defect, not a nuisance"

    Under this architecture the USB link carries the **steering setpoint** as well as
    feedback, so a dropout removes the setpoint and drops the vehicle to `ESTOP`
    ([failsafe row 2](../design/safety.md#2-failsafe-matrix)). That is the safe behavior, but
    a link that drops repeatedly is a vehicle that stops repeatedly.

    **Target: zero dropped sessions over 30 minutes.** If you see any, fix the cable, the
    port, or the transport before wiring a motor.

**Stage 0 gate**

- [ ] Angle sensor monotonic across full travel, no wrap, no motor interference
- [ ] `counts → radians` conversion verified against a digital angle gauge
- [ ] Range/plausibility check rejects an unplugged sensor (fault bit sets, mode → `ESTOP`)
- [ ] `/mitt/dbw/status` ≥ 50 Hz, zero dropouts over 30 min
- [ ] Encoder counts change in the correct sign for forward rotation

---

## 4.4 Stage 1 — steering motor on the bench, current-limited

Corresponds to [safety.md Stage 1](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first).

**Use a bench supply with an adjustable current limit.** This is what turns a runaway position
loop into a harmless buzz. Set it low — just enough to move the motor unloaded.

Wire the Sabertooth: packetized serial from the Teensy, M1 → steering motor.

### Verify the Sabertooth serial timeout

This is a required check, not an assumption. In the previous R/C-PWM design the Sabertooth's
signal-loss timeout came for free; in packetized serial it must be **configured**.

```bash
# With the motor commanded to a steady effort, halt the Teensy (unplug USB / press reset)
# and confirm the motor STOPS rather than latching at its last command.
```

!!! danger "If the timeout cannot be established, stop"

    Revert to independent R/C (PWM) mode and accept the ~50 Hz actuation ceiling
    ([dbw.md §4](../design/dbw.md#4-adr-sabertooth-control-mode-packetized-serial-single-master)).
    [Failsafe row 6](../design/safety.md#2-failsafe-matrix) and FMEA row 9 both depend on this
    behavior — it is one of the layers that makes a single-MCU architecture defensible.

### Tune and measure the position loop

Start with P only, add D, add I last and sparingly. Measure against the
[numeric contract](../design/dbw.md#12-numeric-interface-contract):

| Measurement | Target | How |
|---|---|---|
| Steady-state error | ≤ **1.0°** | Command a series of angles across ±20°, log measured vs. commanded |
| RMS error over sweep | ≤ **1.5°** | Slow triangle sweep, compute RMS |
| Step response (10°) | 90% in ≤ **400 ms**, overshoot ≤ **15%** | Log at ≥ 200 Hz, plot |
| Backlash / hysteresis band | *record the number* | Approach the same angle from both directions |
| Drift over 30 min | ≤ **0.5°** | Hold one angle, log; should be ≈ 0 by construction |
| Disturbance rejection | returns to setpoint | Push the output arm by hand, release |

!!! info "Pre-registered E4 decision point — this is the deadline"

    **If the loop cannot hold ≤ 1° steady-state with no sustained oscillation, adopt the E4
    fallback** — a dedicated closed-loop motion controller (Kangaroo x2 class) — rather than
    continuing to tune
    ([dbw.md §3](../design/dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision)).

    Firmware tuning is unbounded work. This bounds it. Take the decision on the numbers, not
    on how close it feels.

Also verify the interlocks:

- **Mechanical limit clamp** — drive toward a limit, confirm effort clamps *toward center
  only* and the at-limit fault bit sets.
- **Stall detection** — hold the output arm, confirm the stall bit sets and effort backs off.
- **Setpoint staleness** — kill the publisher, confirm `ESTOP` within 500 ms, steering
  centered then de-energized.
- **Freewheel on power cut** — [safety.md §4.4](../design/safety.md#44-test-procedure-freewheel-on-power-loss)
  steps 1–2.

**Stage 1 gate**

- [ ] All six measurements recorded in `docs/build/validation-report.md`
- [ ] Sabertooth serial timeout verified to stop the motor
- [ ] Limit clamp, stall detect, staleness watchdog, freewheel all demonstrated
- [ ] E4 decision taken explicitly — adopted or not needed, recorded either way

---

## 4.5 Stage 2 — both channels and both override layers

Corresponds to [safety.md Stage 2](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first).
Add the drive motor on the bench, wheels off.

### Layer A — SBUS closed-loop override

Bind the RC set, wire SBUS to a Teensy hardware serial port. Verify:

- Moving the mode switch puts the vehicle in `MANUAL_RC` (visible in `DbwStatus.mode`)
- The sticks command an **angle** — the position loop is still closed behind them
- Override engages within **≤ 200 ms** from any state
- RC frame loss → `ESTOP`

### Layer B — hardware RC signal MUX

!!! danger "This is the condition on which the whole architecture was adopted"

    D3 concentrates the steering loop, throttle, override, and arming on one MCU. The
    justification for accepting that is that override is a **wiring property**, not a firmware
    property. **That claim must be demonstrated here, not assumed.**

**Test it with the Teensy deliberately halted.** Hold the Teensy in reset (or unplug it
entirely), then:

- [ ] Flip the MUX channel and confirm the RC transmitter drives the Sabertooth **directly**
- [ ] Confirm steering responds to the sticks with the Teensy dead
- [ ] Confirm the traction channel behaves as designed in this state

Note what changes: through Layer B the override commands raw **effort**, open-loop — not an
angle. Feel the difference on the bench before you need it on the ground. It is acceptable
for an emergency mode, and it is exactly what B-MROVER does in normal operation — but it is a
different control feel and you should not discover that during an incident.

**Stage 2 gate**

- [ ] Both Sabertooth channels driven correctly from the single serial master
- [ ] Layer A: angle-commanding override, ≤ 200 ms, mode visible in `DbwStatus`
- [ ] **Layer B: demonstrated with the Teensy halted**
- [ ] Behavior of Layer B recorded in the validation report, including the effort-vs-angle note

---

## 4.6 Gate to step 5

- [ ] Stage 0, 1, and 2 gates all passed and recorded
- [ ] Toolchain versions pinned and written down (§4.2)
- [ ] Measured steering numbers meet the [numeric contract](../design/dbw.md#12-numeric-interface-contract)
- [ ] No motor has yet been driven with the vehicle on the ground — that is step 7, after the
      relay MUX and E-stop are installed in step 5

---

**Next:** [5. Software & ROS 2 setup](05-software.md)
