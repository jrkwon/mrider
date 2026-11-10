# Light bring-up — firmware changes and the tests that replace the failsafe matrix

Replaces Stages 1 and 2 of the [firmware page](../build/04-firmware.md), Part A of the
[bench test](../build/06-bench-test.md), and the whole of [manual drive](../build/07-manual-drive.md).

*Written 2026-11-10; never built. See [the overview](index.md).*

Every stop that [ADR L](../design/adr-light.md#what-this-waives-stated-plainly) claims is turned
into a test here. **A stop that has not been tested on the vehicle in front of you is a sentence in
a document**, and in this variant there is nothing behind the sentences.

---

## What the firmware does differently

The blocks are [dbw.md §10.2](../design/dbw.md#102-firmware-blocks)'s.

| Block | In Light |
|---|---|
| 1–5 — micro-ROS, sensor read, position loop, motor output, throttle shaping | As specified. Motor output goes to `RC1`/`RC2` directly |
| 6 — RC decode | **Not built.** No i-BUS, no serial port taken for it |
| 7 — safety supervisor | As specified, and the **hardware watchdog is no longer one item in a list** — see below |

**The watchdog.** Arm it at boot, before any output is driven. Feed it from the control loop only,
after an iteration that read the angle sensor and wrote both outputs — never from a timer
interrupt. [safety.md §2](../design/safety.md#2-failsafe-matrix) explains why a hang does not
stop the pulses by itself; in the full design three hardware layers stand behind that, and here
none do. Choose the period and write it down: it is part of the answer to *"how far does the
vehicle travel if the firmware hangs?"*

**Two modes, not three.** `MODE_ESTOP` — neutral on both lines, steering de-energised — and
`MODE_AUTONOMOUS` — following `DbwCommand`. `MODE_MANUAL_RC` stays in the message and is never
entered, so the message is the one on `main`.

**Arming, without a transmitter to arm with.** The full design re-arms from the RC set. Light
needs a rule that cannot start the vehicle by surprise:

> Leave `MODE_ESTOP` only after **500 ms of fresh commands whose speed is zero.** A command stream
> that returns already asking for motion does not arm.

So a laptop that reconnects mid-command, or a node restarted with a goal still active, finds the
vehicle stopped and keeps it stopped until something commands zero first. A sensor fault latches
until reset.

**Manual driving is the gamepad**, through `teleop.launch.py` on the laptop, with the deadman
button it already requires. That path runs through the laptop, the USB link and the firmware — it
is a convenience and a first reflex, **not a stop.** The stops are below.

---

## The tests

| Stage | Where | Power |
|---|---|---|
| **L0** | bench, no motor | USB only |
| **L1** | bench, steering motor | bench supply, **current limit low** |
| **L2** | vehicle on stands, wheels clear | traction pack through the fuse and the switch |
| **L3** | ground, walking pace | as L2 |

**No stage starts until the one before it has passed in full.**

### L0 — the controller alone

[Stage 0 of the firmware page](../build/04-firmware.md#43-stage-0-teensy-alone-no-motor-wired), as
written, on USB power. Add:

| | Test | Pass when |
|---|---|---|
| **T0** | Meter or scope both pulse lines from power-up | Neutral appears on both, and nothing else appears first |
| **T1** | Hang the firmware on purpose — a build that enters `while (true) {}` in the control loop on a serial command | Pulses **stop** on both lines within the watchdog period, then return at neutral after the reboot |

T1 with no motor attached is the cheap version of T4. Do it here first.

### L1 — steering motor on the bench

Wire `RC1` and the steering motor as in [wiring](wiring.md). Tune the loop and apply the
[E4 gate](../build/04-firmware.md#44-stage-1-steering-motor-on-the-bench-current-limited) exactly
as the full design does — that part is not different. **Settle polarity here**, with the current
limit low enough that a loop running the wrong way only buzzes.

Then, with the motor commanded to a steady effort each time:

| | Test | Pass when | What it proves |
|---|---|---|---|
| **T2** | Press the Teensy's reset button | Motor stops; time it | The driver's signal-loss stop — `SW6` is really `0` |
| **T3** | **Pull the USB cable** | Motor stops and **stays** stopped with the cable out | An unpowered Teensy reads as *no pulse* — the open question in [wiring](wiring.md#the-controller-side) |
| **T4** | Hang the firmware on purpose | Motor stops within the watchdog period plus the driver's 100 ms | The watchdog is armed and fed from the loop |
| **T5** | Stop the command stream; leave everything else running | Neutral within 500 ms, mode reads `ESTOP` | Staleness |
| **T6** | Restart the stream **with a non-zero speed in it** | Stays in `ESTOP`. Send zero for 500 ms; only then does it follow | The arming rule |
| **T7** | After T2, T3 and T4 each: command a small effort | Motor responds normally, and neutral is still neutral | The driver did not re-learn its centre from a dead line |

> [!CAUTION]
> **If T3 fails, stop and do not go to L2**
>
> A motor that creeps or twitches with the cable out means the driver is reading noise as a
> command. Then *"pull the USB cable"* is not a stop, and Light has lost one of the three that
> need nothing from the firmware. Fix the input — a stiffer pull-down, a shorter or screened
> lead — and re-run T3 until it passes ten times in ten.

### L2 — on the vehicle, wheels clear of the ground

Both channels, the traction pack, the fuse and the switch. Follow the
[power-on order](wiring.md#power-on-order-which-the-switch-now-enforces) every time — it is a
habit to build now, not at L3.

| | Test | Pass when |
|---|---|---|
| **T8** | Wheels turning under command: **open the switch** | Both motors dead at once. The Teensy stays up and `/mitt/dbw/status` keeps arriving — the controller did not notice |
| **T9** | Repeat T3 with the wheels turning | Both motors stop |
| **T10** | Repeat T4 with the wheels turning | Both motors stop |
| **T11** | Driving from the gamepad: release the deadman | Wheels stop |
| **T12** | Steering held against a lock while the wheels are driven, for a few seconds | The USB session does not drop and the Teensy does not reset. *It cannot brown out — it is not on that rail — so a failure here is noise on the cable, and worth knowing about before the vehicle is on the ground* |

> [!WARNING]
> **Closing the switch again is a power-up for the driver — reset the Teensy first**
>
> The firmware cannot see the switch. After T8 it is still running its loop against motors that
> are no longer there: the steering error does not close, so the steering line can be carrying a
> large effort, and the drive line carries whatever is still being commanded. **Close the switch
> now and the driver takes those two pulses as its new *stop*.** Nothing looks wrong until neutral
> turns out to be a creep.
>
> So after the switch has been opened for any reason: **release the deadman, reset the Teensy,
> wait for neutral, then close the switch** — the power-on order from the top. T8a checks it.

| | Test | Pass when |
|---|---|---|
| **T8a** | After T8: reset the Teensy, close the switch, arm with zero, then command neutral | Both motors still. Then deliberately do it wrong once, wheels clear — close the switch with a steering effort commanded — and see what the vehicle does, so that everyone recognises it |

### L3 — on the ground

**Two people.** One drives from the gamepad. The other walks beside the vehicle with a hand free
for the switch, and does nothing else — no laptop, no phone, no notes. *That second person is the
arm's-reach rule made concrete, and the role does not go away when the driving becomes
autonomous.*

Flat floor, clear of stairs and of anything a coasting vehicle could reach. Walking pace.

| | Test | Pass when |
|---|---|---|
| **T13** | Straight, slow: release the deadman | Stops. Note the distance |
| **T14** | Straight, slow: the walker opens the switch | Coasts to a stop. **Five in five**, and note the longest distance — that distance is the clear space this vehicle needs around it from now on |
| **T15** | Mid-turn: the walker opens the switch | As T14. The steering freewheels with the traction rail, as in the [full design](../design/safety.md#4-steering-motor-power-rail-assignment-and-power-loss-behavior-pinned) |

## Gate to calibration and autonomy

- [ ] T0 to T15 passed, T8a included, on **this** vehicle, and the watchdog period and the T14 distance are
      written down beside the results.
- [ ] Polarity recorded, and where it was fixed.
- [ ] Everyone who will run the vehicle has opened the switch on a moving vehicle at least once.

Then [calibration](../build/06-bench-test.md#part-b-calibration) and
[autonomous bring-up](../build/08-autonomous.md) as written. **The walker stays.**
