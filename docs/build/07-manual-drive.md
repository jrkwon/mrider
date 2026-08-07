# 7. Manual Drive (RC + Joystick)

**Goal:** drive the vehicle under human control through the DBW path.

First drive with the RC transmitter bound to the Pixhawk (the live override authority),
then via a joystick publishing to `/mrider/cmd`. Confirm authority arbitration and E-stop
behave as specified while the vehicle is moving at walking speed.

- **Prerequisites:** Section 6 complete; open, flat test area.
- **Specification:** [design/safety.md](../design/safety.md), [design/dbw.md](../design/dbw.md)
- **Expected outcome:** smooth manual steering/throttle; RC override and E-stop confirmed
  under motion.

!!! warning "Draft — not yet validated on hardware"

    This is the first-drive protocol derived from
    [safety.md §6 Stage 5](../design/safety.md#6-bring-up-protocol-staged-wheels-off-first).
    **No MRider has been driven.** Coast-down distances, joystick scaling, and the abort
    criteria thresholds are marked *(measure during bring-up)*.

!!! danger "The vehicle is on the ground and moving from this point"

    Everything the bench could tell you, it already told you. What remains is what only the
    ground can teach — and it teaches at 24 V with real momentum. **≤ walking speed, operator
    alongside, spotter on the E-stop, every time.**

This step is **Stage 5** of the bring-up protocol. Autonomy (step 8) does not begin until it
passes.

---

## 7.1 Do not start until all of these are true

- [ ] Every failsafe-matrix row passed wheels-off in [step 6](06-bench-test.md)
- [ ] Steering sweep verified within ±1°, returning to 0° at center
- [ ] Odometry verified within ~2% on a straight line
- [ ] E-stop verified: traction cut + MUX reverts to STOCK + steering freewheels
- [ ] Logic rail confirmed not to sag under steering stall
- [ ] RC override verified to preempt the laptop on **both** axes
- [ ] Test area: open, flat, no downhill run-out, nothing fragile within the coast-down
      distance, no bystanders

If any box is unchecked, go back. There is no version of this step that is safe on a vehicle
that failed a bench test.

## 7.2 Roles

Three roles. On a first drive, three **people** — do not combine them.

| Role | Responsibility | Position |
|---|---|---|
| **Operator** | Holds the RC transmitter. The authority of last resort in DBW mode. Never looks at a laptop screen. | Walking alongside, always within RC range and line of sight |
| **Spotter** | One job: the E-stop. Announces "STOPPING" and presses it. Does not narrate, does not debug. | Walking alongside, hand on or beside the E-stop |
| **Engineer** | Runs the laptop, watches telemetry, calls out what is being commanded before it happens. | Stationary or walking behind |

**Call-and-response before every powered movement:**

```
Engineer: "Commanding forward, 20 percent, three seconds."
Operator: "Ready."
Spotter:  "Clear."
Engineer: "Go."
```

Nobody commands anything without all three responses. This feels excessive for thirty
seconds and then saves a vehicle.

## 7.3 Abort criteria

**Press E-stop immediately, without discussion, on any of these:**

- Steering moves in a direction not commanded, or oscillates/hunts
- Vehicle accelerates without a throttle command, or does not decelerate when throttle returns to zero
- RC override does not take effect within one second of touching the sticks
- Any smell of hot insulation, any smoke, any unusual noise from the steering linkage
- The vehicle deviates from the intended path by more than half a vehicle width
- Anyone shouts "stop" — anyone, for any reason, including a bystander
- Telemetry shows the stall bit set while the vehicle is moving
- Anyone loses line of sight to the vehicle

**Stop and re-bench (do not just retry) after any abort.** An abort means a bench test
missed something. Find out which one before the vehicle moves again.

## 7.4 Phase 1 — RC only, no laptop autonomy

Start with the simplest authority chain: transmitter → PX4 → vehicle. The laptop is not
commanding anything yet.

1. Vehicle on the ground, MUX in **STOCK**. Confirm the parent remote still drives it
   normally. This proves the taps and the mechanical build survived assembly.
2. Energize the MUX coil to enter **DBW**. Confirm on telemetry.
3. **Stationary steering.** With no throttle, sweep the RC steering stick lock to lock. Watch
   `steer_deg` track `setpoint_deg`. Look for hunting, dead-band, or asymmetry between left
   and right.
4. **Creep forward.** Smallest throttle that produces motion. Walk alongside. Stop with
   throttle only.
5. **Creep and steer.** Gentle S-curves at walking pace. Confirm the vehicle goes where it is
   pointed and that steering effort under load does not sag the logic rail.
6. **Straight-line odometry check under motion.** Drive a measured distance and compare
   integrated odometry — this is the first check with real tire slip involved.

**Record sheet — Phase 1**

| Observation | Value |
|---|---|
| Steering hunting at rest | *(record: none / amplitude)* |
| Left/right travel symmetry | *(measure)* ° difference |
| Steering dead-band around center | *(measure)* ° |
| Minimum throttle that produces motion | *(measure)* % |
| Logic rail minimum under steer-and-drive load | *(measure)* V |
| Odometry error over measured distance | *(measure)* % |

## 7.5 Phase 2 — E-stop under motion

The test that could not be done on a stand:
[safety.md §4.4](../design/safety.md#44-test-procedure-freewheel-on-power-loss) step 3.

1. Driver walks alongside; vehicle moving at walking pace.
2. **Mid-turn**, the spotter presses the E-stop.
3. Confirm: traction dies, the car **coasts straight or is trivially hand-corrected**, MUX
   reverts to STOCK, and the column is freely hand-steerable.
4. **Measure and record the coast-down distance.**
5. Repeat at least three times — straight, mid-left-turn, mid-right-turn.

**Record sheet — E-stop under motion**

| Trial | Condition | Speed (m/s) | Coast-down distance (m) | Hand-steer force at rim (N) | Behavior |
|---|---|---|---|---|---|
| 1 | straight | *(measure)* | *(measure)* | *(measure)* | *(record)* |
| 2 | mid-left-turn | *(measure)* | *(measure)* | *(measure)* | *(record)* |
| 3 | mid-right-turn | *(measure)* | *(measure)* | *(measure)* | *(record)* |

Log these in the bring-up records per
[safety.md §4.4](../design/safety.md#44-test-procedure-freewheel-on-power-loss) step 4. The
coast-down distance is a **safety parameter for every later test** — it defines how much
clear space step 8 needs.

!!! note "Expected: freewheel, and that is fine"

    With traction already cut, a freewheeling front axle tracks straight or is trivially
    hand-corrected by the walking operator. There is no power to steer the car into anything,
    and the failure state matches the STOCK-revert direction. If instead your column **holds**
    (wiper-motor build), record that and confirm the held angle is not a turn that would carry
    the coasting vehicle somewhere unintended.

## 7.6 Phase 3 — joystick via `/mrider/cmd`

Now the laptop commands, and the RC transmitter becomes the override rather than the primary.

```bash
ros2 run joy joy_node
ros2 run mrider teleop_joy    # publishes /mrider/cmd -> command shim -> ManualControlSetpoint
```

**Joystick mapping** — record what you actually bind:

| Control | Axis / button | Maps to | Range |
|---|---|---|---|
| Steering | *(record)* | `roll` → ±22.5° | −1.0 … +1.0 |
| Throttle | *(record)* | `throttle` | −1.0 … +1.0 |
| **Dead-man** | *(record — required)* | gate: no output unless held | — |
| Speed scale | *(record)* | caps output to walking speed | *(record)* |

!!! danger "Require a dead-man control, and cap the speed in software"

    A joystick that commands motion when nobody is holding it is a runaway waiting for a
    dropped controller. Gate all output behind a held button. Separately, scale the maximum
    throttle in software to walking speed — the [safety.md](../design/safety.md) analysis
    (coast-down distance, freewheel acceptability, operator alongside) is **only valid at
    ≤ walking speed**. Raising this cap invalidates the safety case.

Repeat §7.4's sequence under joystick control: stationary sweep, creep, S-curves.

## 7.7 Phase 4 — authority arbitration under motion

The point of this whole architecture, verified with the vehicle moving. Priority order, from
[safety.md §1.3](../design/safety.md#13-authority-priority-highest-wins):

| Priority | Authority | Test | Observed | Pass |
|---|---|---|---|---|
| 1 (highest) | **Hardware E-stop** | Press while under joystick command | traction cut + STOCK | ☐ |
| 2 | **Relay MUX** | De-energize the coil while driving | reverts to STOCK mid-motion | ☐ |
| 3 | **RC transmitter** | Take the sticks while the joystick commands | TX wins, **both** axes, < 1 s | ☐ |
| 4 (lowest) | **Laptop autonomy** | — | only drives when 1–3 permit | ☐ |

Also verify under motion:

- [ ] **Command loss:** kill the shim while moving → throttle → 0, steering holds
- [ ] **RC loss:** power off the transmitter while moving → PX4 RC-loss failsafe fires
- [ ] **USB loss:** unplug the Nano while moving → odometry goes stale, **steering keeps
      tracking**, autonomy safe-stops

!!! danger "Verify RC-loss deliberately, with space"

    Turning off the transmitter on a moving vehicle is exactly the scenario the failsafe
    exists for, and exactly the moment you find out it was configured wrong. Do it in the
    largest clear space you have, with the spotter's hand on the E-stop, at the lowest speed
    that maintains motion.

## 7.8 Tuning notes

With real road load, the bench PID gains from [step 4](04-firmware.md) will probably need
adjustment. Tire scrub under vehicle weight is a much larger disturbance than the bench saw.

| Symptom | Likely cause | Fix |
|---|---|---|
| Steering hunts/oscillates around setpoint | `Kp` too high, or sensor noise | Lower `Kp`, add `Kd`, re-check filtering |
| Slow to reach commanded angle under load | `Kp` too low, or motor undersized | Raise `Kp`; if effort saturates, the ≥2× torque margin was not met |
| Steady-state offset that does not close | Friction dead-band | Small clamped `Ki` — clamp it, or it winds up against limits |
| Asymmetric left vs. right response | Mechanical binding, or `c0` off-center | Re-check linkage; re-run [zeroing](06-bench-test.md#65-steering-zero-and-countsdegrees) |
| Angle drifts over a session | Coupler slipping | **Stop.** Re-seat the coupler — a slipping absolute reference defeats the whole design |

**Record final gains:** `Kp` = *(measure)* · `Ki` = *(measure)* · `Kd` = *(measure)*
— and re-run the [steering sweep verification](06-bench-test.md#65-steering-zero-and-countsdegrees)
wheels-off after any gain change.

## 7.9 Gate to step 8

- [ ] Stock parent remote verified working on the ground before DBW engaged
- [ ] Smooth RC steering and throttle at walking pace, no hunting under load
- [ ] E-stop-under-motion tested ≥3× (straight, both turn directions); coast-down recorded
- [ ] Coast-down distance logged in bring-up records and used to size the step-8 test area
- [ ] Joystick teleop working with a dead-man gate and a software speed cap
- [ ] All four authority levels verified under motion, in priority order
- [ ] Command loss, RC loss, and USB loss each verified while moving
- [ ] Final PID gains recorded; steering sweep re-verified after tuning
- [ ] Odometry error under real motion recorded

---

**Previous:** [6. Bench test & calibration](06-bench-test.md) · **Next:** [8. Autonomous bring-up](08-autonomous.md)
