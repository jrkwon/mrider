# ADR L — the Light variant

**Status:** accepted **2026-11-10** as a **reference variant**. It is not what the Fall 2026 course
builds: the course's tracks, gates and rubrics are unchanged, and the vehicles the teams hold are
being built to the full design. It lives on the **`light`** branch of this repository.

**Written 2026-11-10 and never built.** No vehicle has been wired this way. Everything below is a
design argument; the bring-up page on the branch is where it becomes a test.

---

## Context

The full design puts four authority layers between a command and a motor, three of them
independent of firmware ([safety.md §1.3](safety.md#13-authority-priority-highest-wins)). That
layering is the condition under which a single controller was adopted
([D3](adr-dbw-architecture-review.md#46-decision-adopted-2026-08-07)), and it stands.

It also has a price, and the price is paid before the vehicle moves under ROS 2 at all:

| What the layers cost | |
|---|---|
| Parts | 5 of the 15 Tier 1 lines in the [BOM](bom.md) — #7 to #11 |
| Batteries | a third one, with its charger, for the logic rail |
| Bring-up | half of Stage 2 and all of Stage 3 in [safety.md §6](safety.md#6-bring-up-protocol-staged-wheels-off-first) verify the layers, not the vehicle |
| Firmware | i-BUS decode, a `MANUAL_RC` mode, arming by transmitter |
| Assembly hazards | the one hidden severity-5 row in the [FMEA](safety.md#7-fmea-lightweight) — row 12 — exists because of the relay MUX |

A reader who wants the smallest thing that steers to an angle and drives at walking pace under
`ros2_control` has to build all of that first. Light is that smallest thing, written down
separately so that nobody arrives at it by quietly skipping steps of the full build.

## Decision

| | | Why |
|---|---|---|
| **Removed** | E-stop circuit — button #8b, contactor #8a, both coil feeds | Replaced by a manual switch, below |
| **Removed** | RC transmitter and receiver #10, hardware RC signal MUX #9, i-BUS decode, `MANUAL_RC` | Manual driving is the USB gamepad #15 with its deadman button, which the full design already has |
| **Removed** | Relay MUX #7 | All three taps are unplugs ([01-bom-sourcing](../build/01-bom-sourcing.md)), so returning to stock is done by hand: unplug the MRider halves, plug the factory pairs back together |
| **Removed** | Logic battery, charger and both UBECs #11 | [safety.md §5](safety.md#5-power-rail-isolation-and-brownout-protection) gives two reasons the laptop cannot be the logic supply — 7.2 W of relay coils, and the independence of the hardware override. Light has neither. **The Teensy is powered from the laptop's USB port**, which is already a source the traction rail cannot sag |
| **Kept** | 25 A fuse · driver signal-loss timeout (`SW6 = 0`, 100 ms) · command staleness → neutral · wheels-off first · operator alongside at walking pace | |
| **Added** | **One manual disconnect switch** in the traction `+` lead | The only stop that works when the firmware is alive and wrong |
| **Required, not optional** | **Hardware watchdog**, fed from the control loop | The only automatic recovery from a hang ([safety.md §2](safety.md#2-failsafe-matrix)) — in Light there is no hardware layer behind it |

### The disconnect switch

**DC-rated for at least the fuse's current at pack voltage, in the `+` lead downstream of the fuse,
operable from outside the body without reaching past a wheel, and with no coil.**

**A 22 mm mushroom button is not this part.** Its contacts carry an AC rating that says nothing
about breaking a DC motor current — [01-bom-sourcing](../build/01-bom-sourcing.md) sets that out,
and it is why the full design switches a contactor's coil instead of the traction lead. A rotary
battery isolator is the ordinary part for the job.

*Not purchased: as of 2026-11-10 the [order log](../order-log.md) has no line for it.* If none is
to hand, the parts the full design already bought make a coil version with no logic battery —
contactor #8a in the `+` lead, its coil fed from the traction pack through button #8b. That is an
E-stop again in everything but name, which is fine; it is just more than this variant asks for.

## What this waives, stated plainly

**D3 was adopted on the condition that a human can take the vehicle back with the firmware dead**
([dbw.md §11.2](dbw.md#112-hardware-rc-signal-mux-the-d3-condition)). **Light does not meet that
condition.** It is a different risk posture, not a cheaper way of meeting the same one.

What stops the vehicle, failure by failure:

| Failure | What stops it | Needs the firmware to be… |
|---|---|---|
| Laptop stops commanding | staleness > 500 ms → neutral | alive and correct |
| USB cable out, laptop dead | Teensy loses power → pulses stop → driver timeout, 100 ms | **nothing** |
| Firmware hang | watchdog reset → pulses stop → driver timeout | armed once, at boot |
| **Firmware alive and wrong** — a sign error, a stuck setpoint | **the operator:** release the deadman, pull the USB cable, open the switch | **nothing** — but it needs the operator |
| Angle sensor fault | plausibility check → neutral, de-energise | alive and correct |
| Short or sustained overcurrent | 25 A fuse | nothing |
| Pack sags under the driver's floor | driver drops out; the Teensy, on USB, does not | nothing |

**The fourth row is the whole difference.** Neither design stops a wrong-but-alive firmware
automatically — an E-stop is pressed by a person too. What the full design gives that person is a
**stop from a distance** (a transmitter) and a **palm-strikeable one** (a mushroom). Light gives
them a switch and a cable on the vehicle itself. **So in Light the operator must be within arm's
reach of the vehicle for as long as the switch is closed.** That is the rule everything else here
depends on, and it is a rule about a person, which is the weakest kind.

Also given up: steering under human control during a fault (Layer B gave it back; Light can only
stop), and a live return to the parent remote.

### What the argument rests on

- **Speed cannot exceed the toy's.** Same motors, same pack, and a driver cannot deliver more than
  pack voltage — so the top speed is whatever the vehicle did as shipped, carrying about 10 kg.
  *This is a bound relative to stock, not a number: no top speed is recorded in this repository
  as of 2026-11-10.*
- **Current can exceed the toy's, and this is where "no worse than stock" stops being true.** The
  stock supply sits behind a 10 A device; Light's fuse is 25 A, and the MDDS30 has no settable
  limit ([dbw.md §4.1](dbw.md#41-part-substitution-cytron-mdds30-replaces-the-sabertooth-2x32-2026-09-29)).
  The open stall-current question in [vehicle.md §3.1](vehicle.md#31-drive-motor-stall-current-vs-the-drivers-rating-critical)
  is open here too.
- **Three stops need nothing from the firmware:** the fuse, the switch, the USB cable.

### Three hazards the simplification creates or keeps

Found while writing the branch's pages, and recorded here because this is where the risk is
argued. The procedures are on the branch.

- **A mis-plug survives the removal of the relay MUX.** The power and drive taps are the same
  blade family ([FMEA row 12](safety.md#7-fmea-lightweight)). With no relay the pack can no longer
  land on the stock ECU — but the drive-tap half still fits the pack, and then the driver powers
  up through its own output stage's body diodes, **upstream of the fuse and the switch.** Same
  mitigation: pigtails cut too short to reach the wrong connector.
- **Re-closing the switch is a power-up for the driver**, which takes whatever pulse it sees as
  *stop*. The firmware cannot see the switch — Light has no sense line — so it may be mid-effort
  when that happens. **Reset the Teensy before closing the switch again.** The full design does
  not have this problem in this form: its E-stop is sensed. *It had it in another: until
  2026-11-10 its firmware kept the steering loop's proportional term alive while the E-stop was
  down. Writing this bullet did not prompt a check of `main`; an outside review did.*
- **With no transmitter there is nothing to arm with**, so the firmware leaves `ESTOP` only after
  500 ms of fresh commands at zero speed. Without that rule a laptop reconnecting mid-command
  starts the vehicle.

### What it is not for

Anything heavier or faster than this chassis. Any run with the operator out of reach. Slopes,
stairwells, or anywhere a coasting 10 kg vehicle is itself the hazard. Any demonstration to people
who have not been told where the switch is. **For those, build the full design** — that is what
it is for.

## Open, as of 2026-11-10

- **What the MDDS30 reads on an undriven `RC1`/`RC2`.** With the Teensy unpowered its outputs
  float. The branch specifies a pull-down on each line and a test that pulls the USB cable with a
  motor commanded; until that test is run, "USB out stops the vehicle" is an expectation.
- ~~**Whether the driver's signal header needs an external 5 V.**~~ **Answered the same day, by inference: it
  does not, and should not be given one.** The manual's own RC drawing powers a receiver from
  that header with nothing but the pack attached, so the centre pin is the board's supply coming out
  ([03-electrical §3.5.1](../build/03-electrical.md#351-hardware-rc-signal-mux-wire-this-it-is-not-optional)).
  Light connects signal and ground to that header and nothing else. The full design's "motor
  driver signal logic on UBEC B" was an error, corrected with this.
- **A Teensy whose `VUSB`–`VIN` pads were already cut** for the full build cannot be USB-powered
  until they are bridged again. Feeding `VIN` from a regulator on the traction pack instead is
  **not** an acceptable shortcut — it couples the controller to traction sag, which is the fault
  the logic rail was built to prevent.

## How the branch is kept

A variant kept as a second copy of the documents rots: the E-stop alone is mentioned in 56 files.
So `light` is **`main` plus a thin overlay**, and the rule is checkable.

1. **`light` differs from `main` only in:** `docs/light/**`, the navigation in `mkdocs.yml`, and
   one banner each in `README.md` and `docs/index.md`. Nothing else. Check 23 in
   `scripts/check_docs.sh` enforces it on that branch.
2. **Full-design pages are never edited on `light`.** The overlay says, step by step, which page
   applies as written, which applies with changes, and which is replaced.
3. **Sync runs one way.** `main` is merged into `light`; `light` is never merged into `main`. A
   fix that is true of both designs is made on `main` and arrives by merge.
4. **Code has one source, on `main`.** `mitt_msgs` is identical in both — `MODE_MANUAL_RC` simply
   is never entered — and when vehicle firmware exists, the variant is a build environment, not a
   fork of the source.
5. **It is not deployed.** The published site is `main`. The docs workflow builds `light` to prove
   it builds, and publishes nothing from it.
6. **Review after 2026-12-21.** If Light turns out to be the build people actually reach for, the
   honest move is to make it the default build on `main` and present the layers as the upgrade —
   not to keep a branch that has quietly become the real project.
