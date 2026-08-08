# MRider Safety Design

This is a **standalone** safety document for MRider. It defines the failsafe matrix, authority arbitration, power-rail assignments that determine behavior on power loss, an FMEA, and a staged bring-up protocol. It is written so a reader can evaluate MRider's safety story without reading the other docs first — but it cross-links [dbw.md](dbw.md) (datapath, MUXes, Sabertooth mode), [architecture.md](architecture.md) (power tree, timing contract), [calibration.md](calibration.md), and [software.md](software.md) where detail lives.

Design principle: **safety first** — hardware E-stop, override with explicit *electrical* authority, and a failsafe matrix designed in from day one. The vehicle operates at **≤ walking speed** with a person alongside during all early phases, which is what makes several of the mitigations below acceptable.

!!! warning "Architecture change — read this first"

    Under the superseded Pixhawk design, override, arming, and failsafes were delegated to PX4, a field-tested autopilot. Under the adopted single-Teensy design ([D3](adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07)) **they are project responsibility.** That is the principal safety cost of D3 and it is paid, not waved away, by the layered design in §1: three of the four authority layers are **independent of Teensy firmware**, and the top three are pure hardware. The adoption of D3 was made *conditional* on this layering.

---

## 1. Authority arbitration — who is allowed to drive the motors

Three possible controllers exist; **at most one may reach the motors at any instant**:

1. **Stock parent-remote / factory ECU** — the vehicle as shipped.
2. **DBW autonomy** — laptop → Teensy → Sabertooth (both channels).
3. **RC transmitter** — the *live* manual override while in DBW mode, in two layers (§1.2).

### 1.1 Relay-MUX: STOCK vs. DBW selection

A **DPDT relay/contactor MUX** selects STOCK vs. DBW per motor circuit. **Default (coil de-energized) = STOCK.** Energizing the coil switches the motor circuits from the factory controller (NC contacts) to the Sabertooth (NO contacts). See the MUX diagram and 3-tap connector spec in [dbw.md §11](dbw.md#11-authority-arbitration-relay-mux-and-hardware-rc-signal-mux).

Key property: **any loss of logic power, any E-stop, or any deliberate abort drops the coil and reverts to STOCK.** The failure direction is always toward the factory-safe vehicle. "Parent-remote fallback" is thus **reversibility** (drop to stock), not live dual authority — the parent remote and Sabertooth are never simultaneously wired to the motors.

### 1.2 Live override inside DBW mode — two layers

Because a single MCU now holds the steering loop, the throttle output, override, and arming, a firmware hang would lose all four at once if override lived only in firmware. It does not.

**Layer A — SBUS into the Teensy (normal manual mode).** The RC receiver's SBUS stream is decoded by the Teensy. Taking the sticks switches the vehicle to `MANUAL_RC` and the operator commands a **steering angle**, with the position loop still closed behind it. This is the everyday manual mode and is *better* than raw effort.

**Layer B — hardware RC signal MUX (independent fallback).** A dedicated RC channel drives a **signal multiplexer** that selects either Teensy output *or* direct RC input into the Sabertooth. This is a wiring property: it works with the Teensy hung, crashed, or unprogrammed. **This is a stronger guarantee than the software RC override the superseded PX4 design relied on.**

!!! danger "The trade, stated plainly"

    Through Layer B the override commands raw **effort**, open-loop — not an angle. That is a behavioral change from Layer A and from the superseded design, and it must be **re-analysed at bring-up, not assumed**. It is nonetheless exactly what B-MROVER does in *normal* operation (finding F2: `joystick_control.py:70,75,100-109` map the stick straight to effort with no position loop anywhere in the repository), and it is acceptable for an emergency mode where the goal is to get the vehicle away from a hazard, not to track a trajectory.

### 1.3 Authority priority (highest wins)

| Priority | Authority | Mechanism | Independent of Teensy firmware? |
|---|---|---|---|
| 1 (highest) | **Hardware E-stop** | cuts traction power + drops MUX coil (§3) | **Yes** |
| 2 | **Relay MUX position** | de-energized = STOCK; overrides DBW entirely | **Yes** |
| 3 | **Hardware RC signal MUX** | selects RC effort directly into the Sabertooth | **Yes** |
| 4 | **RC via SBUS** | Teensy switches to `MANUAL_RC`, closed-loop | No |
| 5 (lowest) | **Laptop autonomy** | only drives when 1–4 all permit | No |
| — | *Sabertooth serial timeout* | motors stop when the Teensy stops transmitting | **Yes** (verify, §2 row 6) |

---

## 2. Failsafe matrix

Behavior on each loss scenario. "Traction" = drive motors; "steering" = the Teensy-driven steering gearmotor. Rates referenced are the timing contract in [dbw.md §12](dbw.md#12-numeric-interface-contract) / [architecture.md §6](architecture.md#6-timing-heartbeat-contract).

| # | Loss scenario | Detection | Immediate behavior | Steering behavior | Recovery |
|---|---|---|---|---|---|
| 1 | **Command loss** (laptop stops publishing `DbwCommand`, or rate < 50 Hz) | Teensy supervisor: setpoint staleness **> 500 ms** | Enter `ESTOP`: **throttle → 0** | **Steering centered**, then motor de-energized | resume when stream returns; operator re-arms via RC |
| 2 | **USB link loss** (micro-ROS session drops) | Teensy: no session / no setpoint. Laptop: `/mitt/dbw/status` stale > 250 ms | Teensy enters `ESTOP` autonomously; laptop halts Nav2 | **Centered, then de-energized** | reconnect; agent re-establishes session |
| 3 | **RC loss** (TX off or out of range) | Teensy: SBUS frame timeout; MUX channel goes to failsafe value | Enter `ESTOP`: **throttle → 0** | Centered, then de-energized | TX re-links; explicit re-arm |
| 4 | **Battery sag / brownout** (pack droops under stall) | logic-rail undervoltage monitor | logic rail dips below threshold → **MUX coil drops → revert to STOCK**; Sabertooth low-voltage cutoff also stops motors | steering motor de-energizes with the coil → **freewheel** (§4) | recharge/settle; isolation (§5) should prevent the dip |
| 5 | **E-stop pressed** (operator or bump) | hardwired contactor | **traction power cut**; MUX coil dropped → STOCK | steering motor loses power → **freewheel** (non-self-centering column); acceptable at ≤ walking speed (§4) | manual reset of latch; re-arm sequence |
| 6 | **Sabertooth command loss** (Teensy stops transmitting) | **Sabertooth serial timeout** | affected channels **stop their motors** | steering motor stops | transmission resumes → motors re-enabled |
| 7 | **Steering at mechanical limit / linkage jam** | Teensy: stall detected (encoder velocity ≈ 0 under effort) | **clamps effort toward center only**, sets stall bit in `DbwStatus.faults` | holds at limit, no further drive into the stop | command away from limit |
| 8 | **Teensy firmware hang** | Sabertooth serial timeout (row 6); operator observation | **Motors stop** (row 6). Hardware watchdog resets the Teensy to neutral outputs | freewheel or held per §4 | watchdog reset; if repeated, abort session |
| 9 | **Absolute angle sensor fault** (I²C NAK, out-of-range, magnet lost) | Teensy: plausibility + range check each loop | Enter `ESTOP`; set encoder-fault bit. **Never run the loop on a bad angle** | de-energized (do not drive to a garbage target) | diagnose sensor; re-zero per [calibration.md](calibration.md) |

Rows 1–5 are the required set; 6–9 are additional. Every row is testable on the bench (§6).

!!! warning "Row 2 is a genuine regression from the superseded design — accept it knowingly"

    Under the Pixhawk design, the USB link carried **feedback only**; the steering setpoint arrived separately as PX4 servo-PWM, so a USB dropout left steering still tracking. **Under D3 the same link carries the setpoint**, so a USB dropout removes it.

    This was flagged in [adr §4.2](adr-dbw-architecture-review.md#42-feasibility-verified-against-the-vendor-specification) and is accepted on these grounds: the failure is now **detected in one place with one timeout** and resolves to a defined safe state (center + de-energize) rather than to "keep tracking a setpoint whose author is gone". A stale-setpoint-with-live-actuator state is more dangerous than a stop. **Measure USB session stability at Stage 1 and log dropouts across a ≥ 30 min run** — if dropouts occur at all, treat it as a blocking defect, not a nuisance.

---

## 3. E-stop semantics

**E-stop cuts traction power only, and drops the MUX coil.** It is a hardwired, latching mushroom-head contactor in the traction power path (not a software command), so it works even if the laptop or the Teensy has hung — and with the laptop entirely powered off.

Consequences of the traction-only design:

- Drive motors lose power immediately → vehicle coasts to a stop (no regenerative braking assumed; ≤ walking speed makes coast-down distance small).
- Dropping the MUX coil simultaneously reverts motor authority to STOCK, so nothing can re-drive the motors until E-stop is reset.
- The **steering column is non-self-centering** (no spring return on these ride-on columns), so steering behavior on E-stop is governed by the steering motor's power rail — pinned in §4.

---

## 4. Steering-motor power-rail assignment and power-loss behavior (pinned)

**Which rail the steering motor sits on determines whether it freewheels or holds when that rail dies.**

### 4.1 Rail assignment (pinned)

**The steering gearmotor is powered from the Sabertooth motor rail (traction rail via the MUX), NOT the isolated logic rail.** Its drive current flows through Sabertooth M1, fed from the traction battery through the power tap and MUX ([dbw.md §11.5](dbw.md#115-3-tap-connector-spec-minimally-invasive)). The Teensy, absolute sensor, RC receiver, signal MUX, and Sabertooth *logic* are on the **isolated logic rail** (§5).

Rationale: the steering motor is a power actuator drawing amps; it belongs on the motor rail with its power stage, and it must lose power together with traction on E-stop so the MUX can cleanly hand authority back to STOCK. Putting the steering motor on the logic rail would (a) risk browning out the Teensy — which now holds the *entire* safety supervisor — when the steering motor stalls, and (b) leave steering live after an E-stop cut traction, an inconsistent and more dangerous state. **Under D3 point (a) is more important than it was**, because there is no second controller to survive the brownout.

### 4.2 Behavior on power loss / E-stop (consequence of 4.1)

Because the steering motor is on the traction/motor rail, **cutting that rail (E-stop, brownout, MUX drop) de-energizes the steering motor → the column freewheels** (the chosen DC gearmotor is back-drivable; contrast the wiper-motor fallback in [dbw.md §2.4](dbw.md#24-wiper-motor-fallback), whose worm gear would hold instead).

### 4.3 Why traction-cut + freewheel steering is acceptable

- **Speed bound:** MRider operates at **≤ walking speed** with an operator alongside in all early phases. Coast-down distance after traction cut is short (< a couple of meters).
- **Freewheel ≠ uncontrolled:** with traction already cut, a freewheeling front axle tracks straight or is trivially hand-corrected by the walking operator; there is no power to steer the car into anything.
- **Fail-consistent:** freewheel-on-E-stop matches the STOCK-revert direction, so the failure state is simple and predictable.
- The alternative (hold-last-angle through E-stop) would require keeping the steering motor powered after an E-stop — contradicting "E-stop cuts power" and adding a live actuator during an emergency. Rejected.

### 4.4 Test procedure (freewheel-on-power-loss)

1. Wheels **off the ground**, vehicle on stands. Command a mid-range steering angle, confirm the Teensy holds it.
2. Press E-stop. Confirm: (a) traction dead, (b) MUX shows STOCK, (c) steering motor de-energized, (d) column **turns freely by hand** with light force (spring-scale check < a few N at the rim).
3. **Repeat with the laptop powered off entirely** — the E-stop must not depend on any software being alive.
4. Repeat on the ground at walking pace: driver walks alongside, hits E-stop mid-turn, confirms the car coasts straight/steerable-by-hand and stops within the expected distance.
5. Log coast-down distance and hand-steer force in [calibration.md](calibration.md) bring-up records. **Target: 10/10 successful trials, cut within ≤ 200 ms.**

---

## 5. Power-rail isolation and brownout protection

- **Two rails:** (1) **traction/motor rail** — pack → power tap → Sabertooth B+ and M1/M2 (drive + steering motors); (2) **isolated logic rail** — a separate battery and DC-DC feeding the Teensy, absolute sensor, RC receiver, hardware signal MUX, Sabertooth signal logic, and the MUX coil driver.
- **The isolated logic rail is not optional and not a retrofit.** The superseded design got logic isolation from the Pixhawk power module; that part is deleted, so the rail must be built explicitly. The Teensy holds the whole safety supervisor — a reset mid-drive is a loss of every firmware-layer protection at once.
- **The laptop runs on its own internal battery** (no traction→19 V conversion in v1), so laptop compute is immune to traction sag.
- **Brownout isolation:** motor stalls (steering into a limit, drive on an incline) sag the traction rail; the logic rail must not follow. Achieve with a dedicated logic supply with adequate hold-up capacitance, and place the undervoltage monitor (failsafe row 4) on the logic rail.
- The per-rail current table and hold-up sizing live in the [architecture.md power tree](architecture.md#5-power-tree-and-safetyauthority-chain); this doc pins only the *safety-relevant* assignment (§4) and the isolation requirement.

---

## 6. Bring-up protocol (staged, wheels-off first)

No stage begins until the previous stage passes. **Bench before vehicle; wheels-off before wheels-on; walking pace before anything faster.**

**Stage 0 — bench, no motors.** Teensy firmware alone: verify absolute-sensor read, counts→degrees, plausibility/range checking, and micro-ROS session establishment. Confirm `/mitt/dbw/status` at ≥ 50 Hz with `ros2 topic hz`. **Log USB session stability over ≥ 30 min** (failsafe row 2). No motor wired.

**Stage 1 — bench, steering motor only, off the vehicle.** Wire the Sabertooth (packetized serial) and M1 → steering motor on a current-limited bench supply. Verify: closed-loop position tracking at ≥ 200 Hz, no runaway, limit-clamp behavior, stall detection, and freewheel on power cut (§4.4 steps 1–2). **Verify the Sabertooth serial timeout stops the motor when the Teensy stops transmitting** (failsafe row 6) — if this cannot be established, revert [dbw.md §4](dbw.md#4-adr-sabertooth-control-mode-packetized-serial-single-master) to independent R/C mode.

!!! info "E4 decision point"

    Stage 1 is the [pre-registered E4 trigger](dbw.md#3-adr-e-steering-control-loop-location-the-key-dbw-decision). **If the loop cannot hold ≤ 1° steady-state error with no sustained oscillation, adopt the dedicated motion-controller fallback rather than continuing to tune.**

**Stage 2 — bench, both channels + RC.** Add the drive motor on the bench (wheels off). Verify both Sabertooth channels from the single serial master. Bind the RC set and verify **both** override layers: SBUS closed-loop override (Layer A) and the **hardware signal MUX with the Teensy deliberately halted** (Layer B) — the latter is the D3 condition and must be demonstrated, not assumed.

**Stage 3 — relay MUX + E-stop, still wheels off.** Install the DPDT MUX and E-stop. Test every failsafe-matrix row (§2), including the §4.4 E-stop test **with the laptop powered off**. Confirm default = STOCK on every power-up and every fault.

**Stage 4 — vehicle, wheels on stands.** Full integration on the actual chassis, wheels off the ground. Repeat the failsafe matrix. Measure steering torque/limits, drive-encoder ticks, and verify **no logic-rail brownout under steering stall** (§5).

**Stage 5 — ground, walking pace, operator alongside.** First on-ground manual DBW driving at ≤ walking speed. E-stop-on-the-move test (§4.4 step 4). Only after this passes does autonomy (SLAM/Nav2) engage — see [software.md](software.md).

---

## 7. FMEA (lightweight)

Severity S: 1 = negligible, 5 = hazardous. Detection D: 1 = obvious/monitored, 5 = hidden.

| # | Failure mode | Effect | S | Mitigation | Detection (D) |
|---|---|---|---|---|---|
| 1 | Absolute steering sensor fails (I²C NAK, magnet lost, out of range) | steering angle reads garbage; loop could drive to a limit | 4 | range/plausibility check each loop → `ESTOP`, de-energize, flag fault; motor incremental encoder cross-check | in-range monitor (2) |
| 2 | **Magnet wrap** — sensed shaft rotates past one turn | angle folds back; loop drives the wrong way, *silently* | **5** | **load-side mounting (±22.5°) makes wrap mechanically impossible**; travel measured at the §6 bench gate before ordering; pot fallback if no ≤340° shaft exists | continuity check at calibration (3) |
| 3 | Command setpoint stale (laptop hang, USB drop) | steering has no valid target | 3 | staleness > 500 ms → `ESTOP`, center, de-energize (row 1/2) | staleness watchdog (1) |
| 4 | Traction battery sag under stall | **logic reset → loss of the entire safety supervisor** | **5** | isolated logic rail + hold-up cap (§5); undervoltage monitor → MUX drop to STOCK; E-stop and RC MUX remain independent | logic-rail UV monitor (2) |
| 5 | Sabertooth signal ground loop / serial noise | erratic or corrupted motor command | 3 | common-ground star at the Sabertooth; packetized serial is checksummed; serial timeout stops motors | checksum + timeout (2) |
| 6 | Steering gearmotor stall (jam/limit) | overcurrent, heat, drivetrain stress | 4 | Sabertooth current limit; stall detect (encoder velocity ≈ 0 under effort) → clamp effort toward center | stall bit + current limit (2) |
| 7 | Drive motors overcurrent exceeds 32 A/ch | Sabertooth thermal/limit trip; loss of drive | 3 | verify paralleled stall current vs. 32 A ([vehicle.md](vehicle.md)); Sabertooth current limiting | thermal/overcurrent (2) |
| 8 | MUX relay welds closed in DBW mode | cannot revert to STOCK; DBW stuck live | 5 | E-stop still cuts *traction power* independently of the MUX; contact check each bring-up; adequately rated contactor | E-stop remains authoritative (3) |
| 9 | **Teensy firmware hang** — loses loop, throttle, arming, SBUS override at once | vehicle unresponsive to software | **5** | **This is D3's principal risk.** Four independent layers: Sabertooth serial timeout stops motors; hardware RC signal MUX gives steering back; relay MUX reverts to STOCK; E-stop cuts traction. Hardware watchdog resets to neutral | serial timeout + operator (2) |
| 10 | Hardware RC signal MUX fails or is mis-wired | Layer B override unavailable — D3's condition unmet | **5** | **Demonstrated at Stage 2 with the Teensy deliberately halted**, not assumed; E-stop and relay MUX remain as layers 1–2 | Stage 2 test (2) |
| 11 | Laptop autonomy commands unsafe steer/throttle | vehicle drives wrong | 4 | SBUS override (Layer A); RC MUX (Layer B); ≤ walking speed; operator alongside; E-stop | operator observation (2) |

FMEA has **11 rows** (≥ 8 required). Rows 2, 4, 9, and 10 are the severity-5 items introduced or sharpened by D3; each is mitigated by something *independent* of the failing component, and rows 9 and 10 are the ones the bring-up protocol tests explicitly rather than reasoning about.

---

## 8. Summary of pinned safety decisions

- Default authority = **STOCK** (relay de-energized); DBW is opt-in and fails back to STOCK.
- Live override in DBW is **two-layered**: SBUS closed-loop (Layer A) and a **hardware RC signal MUX** (Layer B) that works with the Teensy dead. Layer B is the **condition of D3's adoption** and must be demonstrated at Stage 2.
- E-stop **cuts traction power + drops MUX coil**; hardwired, independent of laptop and Teensy, verified with the laptop powered off, ≤ 200 ms, 10/10 trials.
- **Steering motor is on the traction/motor rail** → freewheels on power loss; acceptable at ≤ walking speed with an operator alongside (§4.3), verified by the §4.4 test.
- **Logic rail is isolated** from traction sag, built from day one — the Teensy holds the whole supervisor. **Laptop on internal battery.**
- Command staleness > 500 ms → `ESTOP`. A stale setpoint with a live actuator is never an accepted state.
- **The angle sensor is never trusted blindly**: range/plausibility checked every loop, and mounted where wrap is mechanically impossible.
- Bring-up is **staged, wheels-off first**; autonomy only after Stage 5.
