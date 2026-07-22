# MRider Safety Design

This is a **standalone** safety document for MRider. It defines the failsafe matrix, authority arbitration, power-rail assignments that determine behavior on power loss, an FMEA, and a staged bring-up protocol. It is written so a reader can evaluate MRider's safety story without reading the other docs first — but it cross-links [dbw.md](dbw.md) (datapath, relay MUX, Sabertooth mode), [architecture.md](architecture.md) (power tree, timing contract), [calibration.md](calibration.md), and [software.md](software.md) where detail lives.

Design principle (from the plan): **safety first** — hardware E-stop, RC override with explicit electrical authority, PX4 failsafes, and a failsafe matrix designed in from day one. The vehicle operates at **≤ walking speed** with a person alongside during all early phases, which is what makes several of the mitigations below acceptable.

---

## 1. Authority arbitration — who is allowed to drive the motors

Three possible controllers exist; **at most one may reach the motors at any instant**:

1. **Stock parent-remote / factory ECU** — the vehicle as shipped.
2. **DBW autonomy** — laptop → PX4 → Sabertooth (throttle) and → Nano → Sabertooth (steering).
3. **RC transmitter bound to the Pixhawk** — the *live* manual override while in DBW mode.

### 1.1 Relay-MUX: STOCK vs. DBW selection

A **DPDT relay/contactor MUX** selects STOCK vs. DBW per motor circuit. **Default (coil de-energized) = STOCK.** Energizing the coil switches the motor circuits from the factory controller (NC contacts) to the Sabertooth (NO contacts). See the MUX diagram and 3-tap connector spec in [dbw.md §11](dbw.md).

Key property: **any loss of logic power, any E-stop, or any deliberate abort drops the coil and reverts to STOCK.** The failure direction is always toward the factory-safe vehicle. "Parent-remote fallback" is thus **reversibility** (drop to stock), not live dual authority — the parent remote and Sabertooth are never simultaneously wired to the motors.

### 1.2 Live override inside DBW mode — RC via PX4

Within DBW mode, the live human override is an **RC transmitter bound to the Pixhawk**, using PX4's standard RC-override and RC-loss failsafe. Because MRider's steering command flows *through* PX4 (`MANUAL_CONTROL.roll` → PX4 servo PWM → Nano, [dbw.md ADR E](dbw.md)), **RC override covers steering as well as throttle** — the operator taking the sticks overrides the laptop on both axes without any separate wiring to the Nano. This is a direct benefit of pinning the single datapath through PX4.

### 1.3 Authority priority (highest wins)

| Priority | Authority | Mechanism |
|---|---|---|
| 1 (highest) | **Hardware E-stop** | cuts traction power + drops MUX coil (see §3) |
| 2 | **Relay MUX position** | de-energized = STOCK; overrides DBW entirely |
| 3 | **RC transmitter (via PX4)** | PX4 RC override preempts offboard/laptop |
| 4 (lowest) | **Laptop autonomy** | only drives when 1–3 all permit |

---

## 2. Failsafe matrix

Behavior on each loss scenario. "Traction" = drive motors; "steering" = the Nano-driven steering gearmotor. Rates referenced are the timing contract in [dbw.md §12](dbw.md) / [architecture.md](architecture.md).

| # | Loss scenario | Detection | Immediate behavior | Steering behavior | Recovery |
|---|---|---|---|---|---|
| 1 | **Command/heartbeat loss** (laptop stops sending `MANUAL_CONTROL`/offboard setpoint, stream < 10 Hz) | PX4 offboard-loss timeout | PX4 rover failsafe: **throttle → 0**, enter hold | PX4 stops emitting servo setpoint → Nano PWM-valid bit clears → **steering holds last commanded angle** (motor de-energizes, see §4) | resume when stream returns ≥10 Hz; operator re-arms |
| 2 | **USB loss** (Nano↔laptop serial drops) | laptop node: no `F,...` frame for T_timeout (e.g. 250 ms); Nano: no diagnostic traffic | Feedback lost → laptop autonomy **degrades to safe-stop** (commands throttle 0 via PX4). **Steering setpoint is unaffected** (it comes via PX4 servo PWM, not USB — [dbw.md ADR E](dbw.md)), so steering still tracks PX4 | steering continues to track PX4 setpoint; odometry stale → localization flags degraded | reconnect USB; node resubscribes |
| 3 | **RC loss** (Pixhawk-bound TX lost) | PX4 `COM_RC_LOSS_T` timeout | PX4 RC-loss failsafe (configured **Hold/Disarm**): **throttle → 0** | steering setpoint from PX4 goes to hold/center per PX4 config → Nano holds | TX re-links; per PX4 RC-recovery policy |
| 4 | **Battery sag / brownout** (24 V pack droops under stall) | logic-rail undervoltage monitor; PX4 power-module voltage | if logic rail dips below threshold → **MUX coil drops → revert to STOCK**; Sabertooth low-voltage cutoff also stops motors | steering motor de-energizes with the coil → **freewheel** (§4) | recharge/settle; brownout isolation (§5) should prevent logic-rail dip in the first place |
| 5 | **E-stop pressed** (operator or bump) | hardwired contactor | **traction power cut**; MUX coil dropped → STOCK; Sabertooth unpowered on motor rail | steering motor loses power → **freewheel** (non-self-centering column); acceptable at ≤ walking speed (§4) | manual reset of E-stop latch; re-arm sequence |
| 6 | **Sabertooth signal loss** (PWM on S1 or S2 disappears) | Sabertooth R/C-mode signal timeout | affected channel **stops its motor** (built-in R/C failsafe, [dbw.md §4](dbw.md)) | if S1 lost, steering motor stops (holds via friction / freewheels per §4) | signal returns → motor re-enabled |
| 7 | **Steering at mechanical limit / linkage jam** | Nano: stall-detected bit (motor encoder velocity ≈ 0 under effort) | Nano **clamps effort toward center only**, flags stall in `status` | holds at limit, no further drive into the stop | operator/autonomy commands away from limit |

This matrix covers **≥ 5** independent loss scenarios (rows 1–5 are the required set; 6–7 are additional). Every row is testable on the bench (§6).

---

## 3. E-stop semantics

**E-stop cuts traction power only, and drops the MUX coil.** It is a hardwired, latching mushroom-head contactor in the traction power path (not a software command), so it works even if the laptop, Nano, or PX4 has hung.

Consequences of the traction-only design:
- Drive motors lose power immediately → vehicle coasts to a stop (no regenerative braking assumed; ≤ walking speed makes coast-down distance small).
- Dropping the MUX coil simultaneously reverts motor authority to STOCK, so nothing can re-drive the motors until E-stop is reset.
- The **steering column is non-self-centering** (no spring return on these ride-on columns), so steering behavior on E-stop is governed by the steering motor's power rail — pinned in §4.

---

## 4. Steering-motor power-rail assignment and power-loss behavior (pinned)

This section makes the explicit rail assignment the plan requires, because **which rail the steering motor sits on determines whether it freewheels or holds when that rail dies.**

### 4.1 Rail assignment (pinned)

**The steering gearmotor is powered from the Sabertooth motor rail (24 V traction rail via the MUX), NOT the isolated logic rail.** Its drive current flows through Sabertooth M1, which is fed from the traction battery through the power tap and MUX ([dbw.md §11.3](dbw.md)). The Nano, absolute sensor, and Sabertooth *logic* are on the **isolated logic rail** (§5).

Rationale: the steering motor is a power actuator drawing amps; it belongs on the motor rail with its power stage (the Sabertooth), and it must lose power together with traction on E-stop so the MUX can cleanly hand authority back to STOCK. Putting the steering motor on the logic rail would (a) risk brownout of the Nano/PX4 when the steering motor stalls, and (b) leave steering live after an E-stop cut traction — an inconsistent, more dangerous state.

### 4.2 Behavior on power loss / E-stop (consequence of 4.1)

Because the steering motor is on the traction/motor rail, **cutting that rail (E-stop, brownout, MUX drop) de-energizes the steering motor → the column freewheels** (the chosen DC gearmotor is back-drivable; contrast the wiper-motor fallback in [dbw.md §2.4](dbw.md), whose worm gear would hold instead).

### 4.3 Why traction-cut + freewheel steering is acceptable

- **Speed bound:** MRider operates at **≤ walking speed** with an operator alongside in all early phases. Coast-down distance after traction cut is short (< a couple of meters).
- **Freewheel ≠ uncontrolled:** with traction already cut, a freewheeling front axle simply tracks straight or is trivially hand-corrected by the walking operator; there is no power to steer the car into anything.
- **Fail-consistent:** freewheel-on-E-stop matches the STOCK-revert direction (the factory vehicle also has no autonomous steering when off), so the failure state is simple and predictable.
- The alternative (hold-last-angle through E-stop) would require keeping the steering motor powered after an E-stop — contradicting "E-stop cuts power" and adding a live actuator during an emergency. Rejected.

### 4.4 Test procedure (freewheel-on-power-loss)

1. Wheels **off the ground**, vehicle on stands. Command a mid-range steering angle, confirm the Nano holds it.
2. Press E-stop. Confirm: (a) traction dead, (b) MUX shows STOCK, (c) steering motor de-energized, (d) column **turns freely by hand** with light force (spring-scale check < a few N at the rim).
3. Repeat on the ground at walking pace: driver walks alongside, hits E-stop mid-turn, confirms the car coasts straight/steerable-by-hand and stops within the expected distance.
4. Log coast-down distance and hand-steer force in [calibration.md](calibration.md) bring-up records.

---

## 5. Power-rail isolation and brownout protection

- **Two rails:** (1) **traction/motor rail** — 24 V pack → power tap → Sabertooth B+ and M1/M2 (drive + steering motors); (2) **isolated logic rail** — a separate DC-DC (or independent supply) feeding the Nano, absolute sensor, Sabertooth signal logic, MUX coil driver, and the Pixhawk power module.
- **The laptop runs on its own internal battery** (no 24 V→19 V conversion in v1) — stated explicitly so laptop compute is immune to traction sag.
- **Brownout isolation:** motor stalls (steering into a limit, drive on an incline) sag the traction rail; the logic rail must not follow, or the Nano/PX4 could reset mid-drive. Achieve with a dedicated logic DC-DC with adequate hold-up capacitance, and place the undervoltage monitor (failsafe row 4) on the logic rail.
- The per-rail current table and hold-up sizing live in [architecture.md](architecture.md) power tree; this doc pins only the *safety-relevant* assignment (steering motor on the traction rail, §4) and the isolation requirement.

---

## 6. Bring-up protocol (staged, wheels-off first)

No stage begins until the previous stage passes. **Bench before vehicle; wheels-off before wheels-on; walking pace before anything faster.**

**Stage 0 — bench, no motors.** Nano firmware alone: verify absolute-sensor read, counts→degrees, PWM-input capture of a bench servo tester, USB feedback frames at ≥20 Hz. No motor wired.

**Stage 1 — bench, steering motor only, wheels off the vehicle.** Wire Sabertooth S1←Nano, M1→steering motor on a bench supply with current limit. Verify: closed-loop position tracking ≥100 Hz, no runaway, limit-clamp behavior, stall detection, freewheel on power cut (§4.4 step 1–2).

**Stage 2 — bench, Sabertooth R/C mode + PX4.** Add PX4 with the rover airframe; confirm `MANUAL_CONTROL.roll` → servo PWM → Nano → steering, and `.throttle` → S2 (drive motor on the bench, wheels off). Verify independent-master operation with no bus conflict ([dbw.md §4](dbw.md)), and RC-override preemption of the laptop.

**Stage 3 — relay MUX + E-stop, still wheels off.** Install the DPDT MUX and E-stop. Test every failsafe-matrix row (§2) and the E-stop/freewheel test (§4.4 steps 1–2). Confirm default = STOCK on every power-up and every fault.

**Stage 4 — vehicle, wheels on stands.** Full integration on the actual chassis, wheels off the ground. Repeat failsafe matrix. Measure steering torque/limits, drive-encoder ticks, verify no logic-rail brownout under steering stall.

**Stage 5 — ground, walking pace, operator alongside.** First on-ground manual DBW driving at ≤ walking speed. E-stop-on-the-move test (§4.4 step 3). Only after this passes does autonomy (SLAM/Nav2) engage — see [software.md](software.md).

---

## 7. FMEA (lightweight)

Severity S: 1 = negligible, 5 = hazardous. Detection D: 1 = obvious/monitored, 5 = hidden.

| # | Failure mode | Effect | S | Mitigation | Detection (D) |
|---|---|---|---|---|---|
| 1 | Absolute steering sensor fails/open (pot wiper lifts) | steering angle reads garbage; loop could drive to a limit | 4 | range-check reading each loop; out-of-range → hold + flag stall bit; clamp effort; motor incremental encoder cross-check | in-range/plausibility monitor (2) |
| 2 | PX4 servo-PWM setpoint lost | steering has no target | 3 | Nano PWM-valid bit clears → hold last safe / center; PX4 offboard-loss failsafe stops traction | PWM presence monitor (1) |
| 3 | USB (Nano→laptop) disconnect | odometry/telemetry lost; autonomy blind | 3 | laptop safe-stop on frame timeout; steering unaffected (PX4 path) | frame-timeout watchdog (1) |
| 4 | Traction battery sag under stall | logic reset / brownout mid-drive | 4 | isolated logic rail + hold-up cap; undervoltage monitor → MUX drop to STOCK | logic-rail UV monitor (2) |
| 5 | Sabertooth signal-wire ground loop / noise | erratic motor command | 3 | common-ground star at Sabertooth; R/C-mode signal-loss timeout stops motor | Sabertooth signal timeout (2) |
| 6 | Steering gearmotor stall (jam/limit) | overcurrent, heat, drivetrain stress | 4 | Sabertooth current limit; Nano stall detect (encoder velocity ≈ 0 under effort) → effort clamp toward center | stall bit + current limit (2) |
| 7 | Drive motors overcurrent (incline/obstacle) exceeds 32 A/ch | Sabertooth thermal/limit trip; loss of drive | 3 | verify paralleled stall current vs. 32 A ([vehicle.md](vehicle.md)); Sabertooth current limiting | Sabertooth thermal/overcurrent (2) |
| 8 | MUX relay welds closed in DBW mode | cannot revert to STOCK; DBW stuck live | 5 | E-stop still cuts *traction power* independently of the MUX; periodic contact check in bring-up; use adequately rated contactor | E-stop remains authoritative (3) |
| 9 | Nano firmware hang | steering loop frozen | 4 | hardware watchdog on Nano → outputs neutral (1500 µs) on reset; PX4 servo-loss + E-stop as outer layers | watchdog reset (2) |
| 10 | Laptop autonomy commands unsafe steer/throttle | vehicle drives wrong | 4 | RC-via-PX4 live override (§1.2); ≤ walking speed; operator alongside; E-stop | operator observation (2) |

FMEA has **10 rows** (≥ 8 required). Rows 8 and 9 are the "silent" high-severity items whose mitigation relies on the E-stop and watchdog being *independent* of the failing component.

---

## 8. Summary of pinned safety decisions

- Default authority = **STOCK** (relay de-energized); DBW is opt-in and fails back to STOCK.
- Live override in DBW = **RC via PX4**, covering both steering and throttle thanks to the single PX4 datapath.
- E-stop **cuts traction power + drops MUX coil**; it is hardwired and independent of laptop/Nano/PX4.
- **Steering motor is on the traction/motor rail** → freewheels on power loss; acceptable at ≤ walking speed with an operator alongside (§4.3), verified by the §4.4 test.
- **Logic rail is isolated** from traction sag; **laptop on internal battery**.
- Bring-up is **staged, wheels-off first**; autonomy only after Stage 5.
