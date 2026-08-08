# ADR Review — DBW Architecture (2026-08)

> Part of the MRider design set. Siblings: [overview.md](overview.md) ·
> [architecture.md](architecture.md) · [dbw.md](dbw.md) · [safety.md](safety.md) ·
> [software.md](software.md) · [calibration.md](calibration.md) · [vehicle.md](vehicle.md) ·
> [sensors.md](sensors.md) · [bom.md](bom.md)

**Status:** Review — **confirms** the two resolved DBW decisions *on their own terms*, **amends**
two of their stated rationales, **adds** two previously unevaluated alternatives (one as a
pre-registered fallback, one raised as open), and **registers** four factual discrepancies for
verification at bring-up.

**D3 is now CLOSED — ADOPTED.** See [§4.6](#46-decision-adopted-2026-08-07) and
[§7.4](#74-d3-closed-adopted). The single-Teensy topology replaces both the Pixhawk 6C and the
Arduino Nano, conditional on the layered override of [§4.5](#45-the-real-objection-and-the-layered-answer).
**This supersedes D1 and D2 as *implementations*** — their reasoning is preserved below as the
record of why the Pixhawk path was credible, and §2/§3 should now be read as history, not as
the build specification.

**Supersedes:** the Pixhawk-based topology in [dbw.md](dbw.md) and [overview.md](overview.md),
which have been amended to match. Those documents remain the authoritative specification of the
*adopted* design; this document records how it was arrived at.

**Date:** 2026-08-07 (D3 closed 2026-08-07)

---

## 1. Scope and method

Three decisions are in scope — two re-opened, one newly raised:

- **D1 — Topology.** Which controller stack drives the vehicle?
  ([overview.md § Design Decisions (resolved)](overview.md#design-decisions-resolved) pins
  *Pixhawk-based*.)
- **D2 — Steering-loop location.** Where does the steering position loop close?
  ([dbw.md ADR E](dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision) pins
  *the Arduino Nano*.)
- **D3 — Controller hardware.** Raised during this review, from a parallel design discussion:
  **merge the Pixhawk and the Nano into a single Teensy 4.1 running micro-ROS.** Never
  considered in any design document. **Recorded open** — see §4.

**Method.** The existing ADRs were argued largely from the design side, citing B-MROVER as a
validated baseline. This review instead re-read the B-MROVER source at
`/mnt/data/projects/mrover` directly and checked every claim against it. Every citation below
was verified at the stated file and line.

That distinction matters: the review found that **two of the reasons the original ADRs give
are not supported by the code they cite**, even though both conclusions survive.

---

## 2. Decision D1 — Controller topology

### 2.1 Options

| | Option | Description |
|---|---|---|
| **A** | **Pixhawk / PX4-based** ✅ | Laptop → PX4 (rover airframe) → Sabertooth. The B-MROVER recipe. |
| B | Arduino-only | Laptop → Arduino → Sabertooth. No flight controller. ([overview.md](overview.md) "simple but limited".) |
| C | Laptop-direct | Laptop drives the Sabertooth directly over USB/serial. No FC, no MCU in the control path. |

### 2.2 Decision

**Confirmed: Option A, Pixhawk-based.**

### 2.3 Rationale (revised)

[overview.md](overview.md) justifies A as *"complex but powerful/extensible"*. That is true but
it is not the decisive argument, and it undersells the decision. The decisive argument is:

**PX4 supplies four safety-critical subsystems that options B and C would require MRider to
hand-write:**

| Subsystem | What PX4 gives | What B/C would require |
|---|---|---|
| IMU + EKF | Calibrated onboard IMU, EKF2, attitude/heading | A separate IMU plus bespoke fusion |
| **RC override** | Standard RC-override preemption of offboard commands | **Bespoke authority arbitration in new code** |
| RC-loss / offboard-loss failsafe | Configurable timeouts and hold/disarm actions | Bespoke watchdogs |
| Arming / mode logic | A tested state machine | Bespoke |

The second row is the one that decides it. **RC override is authority level 3 in
[safety.md §1.3](safety.md#13-authority-priority-highest-wins)** — the live human override.
Options B and C move that from a tested autopilot into new project code. New code is exactly
what you do not want holding the emergency authority.

There is a second, structural payoff that only option A provides. Because the steering command
flows *through* PX4, **an RC transmitter bound to the Pixhawk overrides steering as well as
throttle, with no separate wiring to the Nano**
([safety.md §1.2](safety.md#12-live-override-inside-dbw-mode-two-layers)). Under B or C,
steering override must be built separately. A topology choice buys a safety property.

**Supporting evidence — the recipe is validated on this exact chassis class.** B-MROVER's own
BOM lists a *POSTACK 24 V 2-Seater Kids Ride-On* (`Note/overview.md`, BOM row 1; Amazon
`B0CJTWDC38`) — the same class [vehicle.md](vehicle.md) selects and the same item cited in
[bom.md](bom.md) line 1. Option A is not "a rover autopilot we hope transfers"; it is a recipe
already run on this vehicle class.

### 2.4 Consequences, stated honestly

- **PX4 version churn is real.** B-MROVER required a forked PX4
  (`jomidokunMain/PX4-Autopilot`, branch `wheelEncoder`) for its custom encoder module.
  *Mitigation:* MRider can drop that fork entirely — see finding F2 and
  [ADR-SW1](software.md#adr-sw1-one-transport-one-clock-typed-messages) — and the version is pinned per
  [dbw.md §9](dbw.md#9-teensy-41-firmware-platform-and-version-pinning).
- **A heavier stack to teach.** Students must meet PX4, MAVLink, and XRCE-DDS before they can
  drive. Accepted: the [Learn curriculum](../learn/index.md) sequences this over M1–M3.

---

## 3. Decision D2 — Steering-loop location

### 3.1 The problem is genuinely new work

**B-MROVER has no steering position control of any kind.** Verified: the joystick maps a stick
axis straight to `MANUAL_CONTROL.roll` (`joystick_control.py:70`, `:75`, `:100-109`), the
bridge forwards it (`mavlink_bridge.py:120-126`), and PX4 emits it as a raw effort. A grep of
the whole repository finds no PID and no position loop. **The human closes the steering loop by
eye.**

That is adequate for teleoperation and inadequate for Nav2, which commands an *angle*. So the
question is not whether to add a position loop but where to put it.

### 3.2 Options re-scored

| | Option | Original verdict | This review |
|---|---|---|---|
| **E1** | **Loop on the Arduino Nano** ✅ | Chosen | **Confirmed** — and for stronger reasons than given |
| E2 | Loop in the laptop `ros2_control` hardware interface | Rejected on latency; credited with "max reuse of mrover's `carlikebot_system.cpp`" | **Rejected — and the reuse credit is withdrawn.** See §3.3 |
| E3 | Loop inside a custom PX4 module | Rejected | Rejected. Unchanged. |
| **E4** | **Dedicated closed-loop motion-controller hardware** | *Never considered* | **Added as a pre-registered fallback.** See §3.5 |

### 3.3 Amendment — E2's reuse advantage does not exist

[ADR E](dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision) describes E2 as
*"close the loop in the laptop `ros2_control` hardware interface (max reuse of mrover's
`carlikebot_system.cpp`)"*.

**That file is the upstream ros2_control demo, unmodified.** Verified in
`dev_ws/src/mrover/hardware/carlikebot_system.cpp`:

- the namespace is `ros2_control_demo_example_11` (`:27`);
- `read()` (`:280`) assigns
  `hw_interfaces_["steering"].state.position = hw_interfaces_["steering"].command.position` —
  it echoes the command back as the state;
- `write()` (`:304`) only calls `RCLCPP_INFO`;
- both are bracketed by the upstream comment *"This part here is for exemplary purposes -
  Please do not copy to your production code"*.

There is **no hardware I/O in it at all**. The `steering_position_controller`
(`mrover_control/config/mrover_controllers.yaml`) is therefore wired to a mock.

**Consequence.** E2's rejection stands, but its cost was understated: E2 would require writing
a real hardware interface from scratch *and* accept the USB round-trip per control cycle. What
[software.md §2](software.md#2-ros-2-stack-reused-adapted-new) marks **REUSE** for this row is
an interface *shape*, not working code — that row should read ADAPT or NEW.

### 3.4 Decision — E1 confirmed, on revised grounds

**Confirmed: close the loop on the Arduino Nano.** Two arguments the original ADR does not
make, both stronger than the ones it does:

1. **The Nano is not optional, so no alternative removes a component.** The Nano reads the
   drive encoder and produces the `/mrider/feedback` frame regardless of where the loop lives
   ([dbw.md §10.1](dbw.md#101-primary-transport-micro-ros-typed-messages)). Every alternative
   therefore only *moves the PID off a board that is already on the vehicle* — and E4 adds a
   part rather than replacing one.
2. **E2 has no reuse advantage** (§3.3), so E1's determinism advantage is uncontested rather
   than a trade against reuse.

The original rationale — a dedicated MCU with direct, deterministic access to the sensor and
the motor driver, off the laptop↔XRCE↔MAVLink chain — remains correct and is unchanged.

The educational argument also survives contact with the evidence. ADR E claims the loop
*"doubles as the honest core of the education tier"*; the [M2 curriculum
module](../learn/m2-dbw-steering.md) is built entirely on it, and finding F2 confirms there is
no prior implementation for students to read instead.

### 3.5 New option E4 — dedicated closed-loop motion controller

**Not evaluated in the original trade study.** A closed-loop motion-controller daughterboard —
the **Dimension Engineering Kangaroo x2** is the canonical example, from the same vendor as the
Sabertooth 2x32 already in [bom.md](bom.md) line 3 — attaches to the Sabertooth, closes a
position loop against a potentiometer or encoder, self-tunes, and accepts an R/C PWM pulse as
the position setpoint.

That is close to a literal description of MRider's smart-servo specification, as an
off-the-shelf part. It preserves the pinned datapath (PX4 servo PWM → controller → Sabertooth),
preserves free RC override, and leaves [ADR B](dbw.md#5-adr-b-steering-angle-encoding)
untouched — the absolute column sensor remains the authority.

**Not adopted as primary**, for two reasons:

- It is **additive, not substitutive** — the Nano stays for encoder aggregation and the
  feedback frame, so E4 adds a part, a tuning procedure, and a failure mode.
- It **deletes the project's best teaching artifact** — a position controller students can read
  — and replaces it with a self-tuning black box, in a platform whose stated purpose is
  research *and education*.

**Adopted as a pre-registered fallback**, in the same style as
[ADR-SW2](software.md#adr-sw2-nav2-local-controller-for-ackermann) pre-registers Regulated Pure
Pursuit:

!!! info "E4 trigger (pre-registered)"

    **If, at the end of [bring-up Stage 1](safety.md#6-bring-up-protocol-staged-wheels-off-first),
    the Nano loop cannot hold ≤ 1° steady-state error with no sustained oscillation, adopt E4
    rather than continuing to tune.** Firmware tuning is unbounded work; this bounds it.

**Verify before adoption** (none of this could be checked from the repository):

- [ ] The part is currently available and priced as expected (~$30 class; BOM prices are
      estimates, verify at purchase).
- [ ] Its position mode accepts the column potentiometer as absolute feedback across the full
      working range, without the single-turn wrap hazard that
      [dbw.md §6](dbw.md#6-adr-angle-sensor-technology-magnetic-encoder-vs-potentiometer)
      rejects the AS5600 for.
- [ ] Its behavior on setpoint-signal loss satisfies
      [failsafe matrix row 6](safety.md#2-failsafe-matrix).
- [ ] Its limit/stall handling can reproduce the "clamp effort toward center only" interlock of
      [failsafe matrix row 7](safety.md#2-failsafe-matrix).

---

## 4. Decision D3 — Controller hardware: Pixhawk + Nano vs. a single Teensy 4.1

**Raised after D1/D2 were drafted**, from a parallel design discussion. It is not the
"Arduino-only" option that [overview.md](overview.md) dismissed, and it must not be filed
against that rejection — the capability gap between an ATmega328P and an i.MX RT1062 is what
the whole proposal turns on.

### 4.1 The proposal

**Merge the Pixhawk 6C *and* the Arduino Nano into one Teensy 4.1 running micro-ROS.** All
actuation and all vehicle sensing terminate on a single MCU that speaks ROS 2 natively.

```
Laptop (ROS 2 Humble) ──USB serial──▶ micro-ROS agent
                                          │
                                  Teensy 4.1 (600 MHz Cortex-M7)
                                    ├─ absolute steering pot        (ADC)
                                    ├─ steering motor encoder       (hardware QDC)
                                    ├─ drive shaft encoder          (hardware QDC)
                                    ├─ IMU (external, e.g. BNO085)
                                    ├─ RC receiver (SBUS)           (hardware serial)
                                    ├─ steering position loop       (≥1 kHz, trivially)
                                    ├─ → Sabertooth S1 (steering effort)
                                    └─ → Sabertooth S2 (throttle)
```

### 4.2 Feasibility — verified against the vendor specification

| MRider needs | Teensy 4.1 provides | Margin |
|---|---|---|
| 2 × quadrature encoders (steering motor, drive shaft) | **4 dedicated hardware quadrature decoder timers** | 2 spare; no ISR contention, unlike the Nano's software decode |
| 1 × absolute pot | 18 analog inputs, 12-bit hardware (≈10 bits usable without averaging) | Better than the Nano's 10-bit |
| SBUS in + GNSS + debug | **8 hardware serial ports** | Ample |
| PWM to Sabertooth, arbitrary frame rate | **35 PWM-capable pins** across several timer modules | Resolves §5 outright |
| Control loop ≥ 100 Hz | 600 MHz Cortex-M7 with FPU, 1024 K RAM | ≥ 1 kHz is not a design constraint |
| ROS 2 transport | `micro_ros_arduino` lists **Teensy 4.1 as officially supported** (Teensyduino 1.58.x) | — |

The peripheral question is settled: **everything fits with spare capacity.**

!!! warning "Transport constraint — verify before committing"

    The official `micro_ros_arduino` package provides **USB serial transports only**; native
    Ethernet is not offered out of the box and would require a custom transport implementation.
    So the laptop↔Teensy link is a USB serial link — the same fragility class as the Nano link
    already covered by [failsafe matrix row 2](safety.md#2-failsafe-matrix), except that under
    D3 **that link now also carries the steering setpoint**, which it does not today. Also
    confirm a `micro_ros_arduino` release exists for **Humble** specifically.

### 4.3 What it deletes

This is the strongest argument for D3, and it is larger than it first appears. Much of
[dbw.md](dbw.md) exists only to manage having PX4 in the middle of a loop PX4 does not own:

| Deleted | Why it existed |
|---|---|
| The pinned `roll → servo-PWM → PWM capture → degrees` round trip ([ADR E](dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision)) | Only because the setpoint had to cross from PX4 to a second MCU. With one MCU the setpoint is a ROS 2 message the loop reads directly. |
| PWM input capture firmware block ([§10.3 item 1](dbw.md#102-firmware-blocks)) | Same reason |
| The `F,...` ASCII serial protocol ([§10.1](dbw.md#101-primary-transport-micro-ros-typed-messages)) | Hand-rolled framing to get data into ROS 2. micro-ROS publishes typed messages. |
| The retained I²C register map ([§10.2](dbw.md#101-primary-transport-micro-ros-typed-messages)) | B-MROVER legacy |
| The feedback-driver node (**NEW** in [software.md §2](software.md#2-ros-2-stack-reused-adapted-new)) | Parses the ASCII frame — nothing left to parse |
| `mavlink_bridge.py` command path, `px4_msgs` dependency | No PX4 |
| PX4 version pinning, QGC parameter archaeology, the custom-PX4-fork decision ([§9](dbw.md#9-teensy-41-firmware-platform-and-version-pinning)) | No PX4 |
| Findings **F5** (XRCE-vs-MAVLink) and **F7** (52 vs 16 PPR) | Transport ambiguity and inherited constants both vanish |

**A rejected option appears to become available again — but does not.** [dbw.md §4](dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-teensy-as-both-masters)
rejected the Sabertooth's packetized serial mode *solely* because two independent masters (Nano
for steering, PX4 for throttle) cannot share one bus. With a single controller there is one
master, so the rejection's premise is gone and packetized serial would give exact, high-rate
actuation on both channels, closing §5 cleanly.

!!! failure "Retracted 2026-08-08 — this claimed benefit does not survive the override design"

    Packetized serial was adopted on this reasoning and then **reverted**. Every available RC
    signal multiplexer — [Pololu 2806](https://www.pololu.com/product/2806), Acroname RxMux,
    ServoCity — switches **servo pulses**, and none can select between a serial packet stream
    and RC PWM. The Sabertooth's input mode is fixed by DIP switches, so it is in one mode or
    the other.

    **Packetized serial and the §4.5 hardware RC MUX are mutually exclusive**, and the MUX is
    the condition on which D3 was adopted. R/C PWM mode stands, and **§5 therefore remains
    open** rather than being closed by D3.

    This is a caution about the review's own method: §4.3 counts what a topology change
    *deletes*, but a deletion is only real once the replacement hardware is specified. Two of
    the eight rows in that table were contingent on parts nobody had chosen yet.

### 4.4 What it costs

| Cost | Severity | Notes |
|---|---|---|
| **RC override, RC-loss failsafe, arming become project code** | **High** | The one serious objection. See §4.5. |
| External IMU required | Low | *But note:* the estimator is already `robot_localization` on the laptop, with PX4 acting only as an IMU driver ([software.md §4.1](software.md#41-robot_localization-ekf-configekfyaml)). A BNO085-class part with onboard fusion covers this. **D1's "PX4 gives you the EKF" argument is weaker than §2.3 states.** |
| GNSS/RTK path changes | Low | PX4 accepts RTK injection over MAVLink; without it, an F9P + laptop NTRIP client feeds `navsat_transform` directly — arguably simpler. |
| Power tree rework | Low | PM02 disappears; the isolated logic rail of [safety.md §5](safety.md#5-power-rail-isolation-and-brownout-protection) must supply the Teensy directly. |
| Calibration procedures change | Medium | [calibration.md §5](calibration.md#5-imu-calibration) is entirely QGroundControl-based and would be rewritten. Conversely **§6 time-sync gets simpler** — micro-ROS provides session time synchronisation, replacing the MAVLink `TIMESYNC` offset estimation. |
| **Lineage / credibility claim** | **Medium–High** | MRider's stated identity is a 4th-generation platform *"whose validated ROS 2 + PX4 stack MRider reuses"*. Replacing a field-tested autopilot with project firmware invites "and did you validate yours?" — a fair question for a platform aimed at external replication. |
| Documentation rewrite | Medium | Bounded and known: [dbw.md](dbw.md) §3/§4/§9/§10/§12, [architecture.md](architecture.md) §2–§6, [safety.md](safety.md) §1.2 and failsafe rows 1/3/5, [software.md](software.md) reuse table, [bom.md](bom.md) lines 2/7/8, [build step 4](../build/04-firmware.md), [Learn M1–M3](../learn/m1-ros2-intro.md). |

**What it does *not* cost.** The reuse that carries MRider's autonomy — `robot_localization`,
slam_toolbox, Nav2, the `ros2_control` interface shape, `data_collection`, and the `neural_net`
behavior-cloning pipeline — sits *above* the vehicle interface and is transport-agnostic.
Finding **F1** (validated on this chassis class) also survives: what was validated on the
POSTACK chassis is the *conversion* — Sabertooth, motors, taps — not the autopilot choice.

Cost delta is roughly **−$160** on a $1,429 BOM: Pixhawk 6C + PM02 ($220) and Nano ($13) out;
Teensy 4.1 (~$32 class) and an IMU (~$25 class) in. It also removes the part
[build step 1](../build/01-bom-sourcing.md) flags as the most supply-constrained.

### 4.5 The real objection, and the layered answer

**Single point of failure.** Under D3 one MCU holds the steering loop, the throttle output, RC
override, and arming. A firmware hang loses all four at once. Under Pixhawk + Nano, a Nano hang
still leaves PX4 able to cut throttle and honour RC.

That is a genuine regression **only if the override lives in software on that same MCU.** The
independence argument is repairable, and arguably ends up stronger:

| Layer | Authority | Independent of the Teensy? |
|---|---|---|
| Hardware E-stop | 1 | **Yes** — already hardwired ([safety.md §3](safety.md#3-e-stop-semantics)) |
| Relay MUX → STOCK | 2 | **Yes** — already de-energize-to-safe |
| **RC override via a hardware servo-signal MUX** | 3 | **Yes, if adopted** — the RC receiver drives a signal MUX selecting Teensy PWM *or* direct RC PWM into the Sabertooth |
| Sabertooth R/C signal-loss timeout | — | **Yes** — motors stop when Teensy PWM stops ([row 6](safety.md#2-failsafe-matrix)) |
| Teensy hardware watchdog | — | Internal; resets to neutral output |

With a **hardware RC MUX**, override stops being firmware and becomes a wiring property —
which is a *stronger* guarantee than PX4's software override, and it fits the relay-MUX
reasoning MRider already uses. A total Teensy failure would then still leave: motors stopped,
authority revertible, traction cuttable, and steering under human control.

**The trade to state plainly:** through PX4 today, RC override commands an *angle* (the loop
stays closed behind it). Through a hardware MUX it commands raw *effort*, open-loop — which is
exactly what B-MROVER does in normal operation (F2), and acceptable for an emergency mode, but
it is a change in override behaviour that must be re-analysed, not assumed.

A layered variant is likely best: SBUS into the Teensy for normal closed-loop override, **plus**
the hardware MUX on the E-stop chain as the independent deeper fallback.

### 4.6 Decision — **ADOPTED** (2026-08-07)

**D3 is adopted.** The single Teensy 4.1 running micro-ROS replaces both the Pixhawk 6C and the
Arduino Nano, **conditional on the layered override of §4.5** — SBUS into the Teensy for normal
closed-loop override, *plus* a hardware RC signal MUX on the E-stop chain as the independent
deeper fallback. The condition is not optional; it is what makes the single-point-of-failure
objection answerable.

Recorded before the hardware order, as §7.4 required. The two factors that could not be settled
from the source tree were put to the lab and answered:

1. **Value of the "we reuse a validated autopilot" claim — judged not decisive.** The claim was
   already thinner than it read. F2 (no steering position control exists), F3 (`carlikebot_system.cpp`
   is an unmodified upstream stub), F5 (the MAVLink hop is laptop-side, not PX4-internal), and
   F11 (the estimator is `robot_localization`, PX4 supplies raw IMU only) each remove a leg. What
   survived was RC override and failsafes — one load-bearing leg — and §4.5 answers it in wiring,
   which is a stronger guarantee than PX4's software override. F1 also survives the change: what
   was validated on the POSTACK chassis is the *conversion*, not the autopilot choice.
2. **Schedule appetite — accepted.** MRider was already committed to substantial new Nano
   firmware (PWM capture, filtering, PID, limits, watchdog, EEPROM, serial protocol), so the
   delta is the override/arming/failsafe layer and an IMU driver, on a far more capable MCU with
   real debugging. Against that, D3 *deletes* the whole of §4.3's table.

**The decisive local factor**, which this review could not have known: the lab's own diagnosis of
why the previous three generations fell short is **sensing/feedback quality and integration
complexity** — not perception or planning. D1's topology is the principal source of the second,
and F4's runtime auto-ranging is a direct instance of the first. The architecture that deletes
both is the one to build.

**Consequences accepted with this decision:**

- The two non-technical costs are real and are not being dismissed — they are being paid. The
  platform's replication claim now rests on **MRider's own measured bring-up numbers**
  (`docs/build/` validation report) rather than on PX4's provenance. That is a heavier
  documentation obligation and it is deliberate: §7 of the design set now gates the platform on
  quantified steering/odometry accuracy rather than on inherited credibility.
- **E4 remains the pre-registered fallback** (§3.5), with its trigger unchanged: if the Teensy
  loop cannot hold ≤ 1° steady-state with no sustained oscillation at bring-up Stage 1, adopt the
  motion-controller daughterboard rather than tuning without bound.

**Still to verify before firmware work** (carried from §4.2's warning):

- [x] **Closed 2026-08-08.** `micro_ros_arduino` **v2.0.8-humble** (published 2025-09-30) is the
      current Humble release, and **Teensy 4.1 is listed as Supported** (min version v1.8.5) in
      the upstream support table. Pin that tag.
- [x] **Closed 2026-08-08.** Upstream README states *"Only USB serial transports are provided"*,
      with Known Issues noting transports still need refactoring for pluggability. An Ethernet
      *example* sketch exists but is not an official transport. **USB serial accepted.** This
      link now carries the steering setpoint, which it did not before — re-analysed at
      [failsafe matrix row 2](safety.md#2-failsafe-matrix) and gated on a measured 30-minute
      stability run at bring-up Stage 0.
- [x] **Closed 2026-08-08.** RC MUX part specified: **Pololu 4-Channel RC Servo Multiplexer
      #2806**, ~$18, 4 channels, `SEL` pulse-width select, `FAILMODE` jumper
      ([dbw.md §11.2](dbw.md#112-hardware-rc-signal-mux-the-d3-condition)).

      **Specifying it forced the reversal of the Sabertooth mode decision** — see the retraction
      in §4.3. The part that satisfies D3's safety condition turned out to constrain a decision
      made above it.
- [ ] `FAILMODE` jumper direction decided and recorded in the as-built record (recommendation
      and rationale in [dbw.md §11.2](dbw.md#112-hardware-rc-signal-mux-the-d3-condition)).

---

## 5. Open question — the loop rate is bounded by the output frame rate

[dbw.md §12](dbw.md#12-numeric-interface-contract) pins the servo loop at **≥ 100 Hz** and the
PX4 setpoint refresh at **≈ 50 Hz**, and [§3](dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision)
correctly explains that those two are decoupled.

**Neither document pins the Nano's *output* frame rate to the Sabertooth.** In independent R/C
(PWM) mode the Sabertooth consumes servo-style pulses. If the Nano emits them with the standard
Arduino `Servo` library, the effort command reaches the motor driver at roughly **50 Hz**,
regardless of a 100 Hz control loop — so the actuation bandwidth, not the loop rate, sets the
closed-loop performance ceiling.

This does not invalidate E1; it means the interface contract is incomplete. **Decide and pin
one of:**

1. emit servo pulses at a higher frame rate that the Sabertooth accepts in R/C mode (verify the
   accepted range on hardware), or
2. drive the Sabertooth channel by analog or serial instead of R/C PWM for the steering channel
   — noting that this reopens the single-master reasoning in
   [dbw.md §4](dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-teensy-as-both-masters),
   or
3. accept ~50 Hz actuation and **restate the ≥100 Hz figure as a sampling/estimation rate
   rather than an actuation rate.**

Whichever is chosen, add the output frame rate to the numeric interface contract, and measure
it at [bring-up Stage 1](safety.md#6-bring-up-protocol-staged-wheels-off-first).

!!! warning "Status 2026-08-08 — still open, and option 2 is now unavailable"

    D3 briefly appeared to close this: single-master packetized serial (option 2) removes the
    R/C frame-rate ceiling outright. That was adopted and then **retracted** (§4.3) — packetized
    serial cannot coexist with the hardware RC signal MUX that D3's adoption is conditional on.

    **Options 1 and 3 remain.** [dbw.md §4](dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-teensy-as-both-masters)
    now carries the decision, and [§12](dbw.md#12-numeric-interface-contract) records the rate as
    *measure and pin at Stage 1* rather than asserting a number — which is the honest state, and
    the one thing this section insisted on from the start.

---

## 6. Findings register

Status key — `confirmed`: design doc is right and the evidence strengthens it ·
`discrepancy`: design doc conflicts with the source it cites · `verify`: must be resolved on
hardware.

| # | Finding | Evidence | Status |
|---|---|---|---|
| F1 | B-MROVER already runs on the same vehicle class (24 V 2-seater ride-on, `B0CJTWDC38`) | `Note/overview.md` BOM row 1 | `confirmed` |
| F2 | B-MROVER has **no** steering position control; steering is open-loop effort | `joystick_control.py:70,75,100-109`; `mavlink_bridge.py:120-126`; no PID in repo | `confirmed` |
| F3 | `carlikebot_system.cpp` is the upstream demo stub — `read()` echoes commands, `write()` only logs | `carlikebot_system.cpp:27,280,304` | `discrepancy` — amends ADR E option E2 and the [software.md §2](software.md#2-ros-2-stack-reused-adapted-new) REUSE row |
| F4 | Steering auto-ranging expands `min`/`max` **at runtime** and rescales all past values; defaults are asymmetric (`-600`, `180`), so boot centre is arbitrary | `mavlink_bridge.py:47-50`, `:243-250` | `confirmed` — strengthens [ADR B](dbw.md#5-adr-b-steering-angle-encoding) beyond what it claims |
| F5 | The command path is **MAVLink emitted by a laptop-side node**, not XRCE-to-PX4: the bridge subscribes `/fmu/in/manual_control_setpoint` and calls `mav.manual_control_send()` | `mavlink_bridge.py:79-82`, `:105-126` | `verify` — see §7.1 |
| F6 | **M1/M2 are inverted relative to B-MROVER.** mrover: M1 = throttle, M2 = steering. MRider: M1 = steering, M2 = throttle | `vehicle_setup.md:51-52` vs [dbw.md §2.1](dbw.md#21-actuator), [§4](dbw.md#4-adr-sabertooth-control-mode-independent-rc-pwm-teensy-as-both-masters), [§11.3](dbw.md#115-3-tap-connector-spec-minimally-invasive) | `verify` — see §7.2 |
| F7 | PPR conflict **inside the source project**: firmware pins 52 PPR, the B-MROVER BOM lists a 16 PPR encoder motor | `code/code.ino:27` vs `Note/overview.md` BOM row 2 | `verify` — see §7.3 |
| F8 | B-MROVER Nano emits human-readable prints, not a protocol; it is a passive reader | `code/code.ino:82-89` | `confirmed` — the `F,...` frame is new work |
| F9 | No closed-loop motion-controller hardware was ever considered | `dbw.md` ADR E lists only E1/E2/E3 | `discrepancy` — resolved by §3.5 |
| F10 | **No MCU-class controller alternative was ever considered.** [overview.md](overview.md) frames the choice as "Pixhawk vs Arduino", which files a 600 MHz Cortex-M7 under the same heading as an ATmega328P and dismisses both together | [overview.md § Plan](overview.md#plan); no mention of Teensy, micro-ROS, STM32 or Cortex anywhere in `docs/design/` | `discrepancy` — **resolved: D3 adopted**, see [§4.6](#46-decision-adopted-2026-08-07) |
| F11 | The estimator is `robot_localization` on the laptop; PX4 supplies raw IMU only, so "PX4 gives you the EKF" overstates D1's case | [software.md §4.1](software.md#41-robot_localization-ekf-configekfyaml) (`imu0: imu/data` ← `/fmu/out/sensor_combined`) | `confirmed` — weakens §2.3 |

---

## 7. Actions arising

### 7.1 Confirm the command transport (F5)

[architecture.md §3](architecture.md#3-command-path-laptop-motors) shows
`agent --XRCE--> PX4 --MAVLink--> mixer`, which places the MAVLink hop *inside* PX4. In
B-MROVER the MAVLink hop happens **on the laptop**: `mavlink_bridge` subscribes to the ROS 2
topic and transmits MAVLink over its own `mavutil` connection.

**Resolve before software bring-up:** confirm on hardware whether `ManualControlSetpoint` is
carried to PX4 over XRCE-DDS directly (i.e. whether `manual_control_setpoint` is in the PX4
`dds_topics.yaml` subscription set for the pinned version). It is plausible that B-MROVER's
MAVLink bridge exists *precisely because* it is not there by default.

- If XRCE carries it → `mavlink_bridge` is **deleted** from the command path, not reused, and
  the architecture simplifies to a single transport.
- If it does not → the bridge is genuinely required, and
  [software.md §2](software.md#2-ros-2-stack-reused-adapted-new)'s REUSE claim is correct but
  the [architecture.md](architecture.md) diagram should move the MAVLink hop onto the laptop.

### 7.2 Decide the M1/M2 assignment deliberately (F6)

MRider is internally consistent (M1 = steering everywhere), so this is a real departure rather
than a typo — but it is undocumented, and it inverts the wiring of the recipe MRider inherits,
including any reused harness or 3D-printed enclosure routing. Either adopt B-MROVER's
assignment or record the swap as an intentional departure in
[dbw.md §11.3](dbw.md#115-3-tap-connector-spec-minimally-invasive).

### 7.3 Mark 52 PPR as unverified (F7)

The conflict is inside the source project, so MRider inherits an unresolved number.
The [roll-out calibration](calibration.md#2-drive-distance-encoder-ticksmeters) is authoritative
and bypasses PPR entirely, so the *result* is safe — but "52 PPR" appears in the
[numeric interface contract](dbw.md#12-numeric-interface-contract) as a pinned fact and should
be annotated *verify on the encoder actually fitted*.

### 7.4 D3 — CLOSED, ADOPTED

Closed 2026-08-07, before any hardware was ordered, as this section required.

| Required to close | Outcome |
|---|---|
| 1. Lab's answer on the two non-technical factors (§4.6) | **Answered.** Validated-autopilot claim judged not decisive (four of its legs are removed by F2/F3/F5/F11); schedule appetite accepted. |
| 2. Verify the transport constraint | **Carried forward as a pre-firmware check**, not a blocker — see the checklist at the end of §4.6. |
| 3. Decide the override design | **Layered form adopted** — SBUS into the Teensy *plus* a hardware RC signal MUX on the E-stop chain. The adoption is conditional on it. |
| 4. Record the outcome with reasons | **This section, plus §4.6.** |

Item 2 is deliberately not a gate on the decision: if no Humble `micro_ros_arduino` release
exists, the fallback is a framed **binary** serial protocol with CRC and sequence numbers on the
same Teensy — which keeps every §4.3 deletion except the typed-message convenience. The topology
decision does not depend on it.

### 7.5 Pin the output frame rate (§5)

Add the Nano → Sabertooth actuation frame rate to the numeric interface contract, and measure
it at bring-up Stage 1.

---

## 8. Summary

| Question | Verdict |
|---|---|
| **Controller hardware (D3)** | **ADOPTED.** Single Teensy 4.1 + micro-ROS replaces *both* the Pixhawk 6C and the Arduino Nano, conditional on the layered override of §4.5. Closed 2026-08-07 before the hardware order. **This is the build specification.** |
| **Topology (D1)** | **Superseded by D3.** Confirmed on its own terms at the time — PX4 supplies RC override and failsafes that options B/C would make into new safety-critical code — but that one surviving leg is answered in wiring under D3 (§4.5), and the topology was the principal source of the integration complexity the lab diagnosed as a root cause. §2 is retained as history. |
| **Steering loop (D2)** | **Superseded by D3.** The reasoning was sound given a Nano on the vehicle — nothing was saved by moving the loop off it. D3 removes the Nano, which removes the premise. The loop now closes on the Teensy, with E2's rejection (F3) still standing for the laptop-side alternative. |
| **New alternatives** | **E4** (closed-loop motion-controller hardware) remains pre-registered as a fallback, trigger unchanged at bring-up Stage 1. |
| **Newly exposed risk** | The ≥100 Hz loop bounded by an unpinned output frame rate (§5) — **still open.** Packetized serial would have closed it, but was retracted (§4.3) because it cannot coexist with the RC signal MUX. Measure and pin the rate at Stage 1. |
| **To verify on hardware** | M1/M2 assignment (F6) still applies. F5 (command transport) and F7 (encoder PPR) are **moot under D3**. New: `micro_ros_arduino` Humble availability and the RC MUX specification (§4.6 checklist). |

Two rationales changed, two alternatives were added, four factual items moved from "assumed" to
"must be checked" — and the decision the review could not make has since been made.

The result worth carrying forward is the one that decided it: **the D1 argument survived, but
thinner than it was written.** Its "PX4 gives you the EKF" leg does not hold (F11), and its
reuse leg was already undercut by F2, F3 and F5. What was left standing was RC override and
failsafes — one leg, load-bearing. D3 asked whether that one leg was worth a flight controller.
The answer, once the override moved from firmware into wiring, was no.
