# MRider Light — a reference variant

**You are on the `light` branch.** It describes MRider with the E-stop circuit, the RC set, the
hardware signal MUX, the relay MUX and the logic battery **removed**, and one manual disconnect
switch added. What is left is the smallest thing that steers to an angle and drives at walking
pace under ROS 2.

> [!WARNING]
> **Read [ADR L](../design/adr-light.md) before building any of this**
>
> Light does **not** meet the condition the single-controller design was adopted under: nobody
> can take this vehicle back with the firmware dead. It can only be **stopped** — by a fuse, a
> switch, or a USB cable — and two of those three need a hand on the vehicle.
>
> **So the operator stays within arm's reach of the vehicle whenever the switch is closed.** That
> one rule is what the rest of this variant rests on. If you cannot keep it, build the
> [full design](../design/safety.md).

**Written 2026-11-10 and never built.** No vehicle has been wired this way. The three pages here
were reasoned from the full design's documents, not from a bench, and the first person to follow
them should expect to correct something — here, on this branch.

**This is not what the Fall 2026 course builds.** Course tracks, gates and rubrics are those on
`main`, and they are unchanged.

---

## What is not fitted

Numbers are the [BOM](../design/bom.md)'s.

| # | Part | In Light |
|---|---|---|
| 7 | Relay MUX — relays, sockets, driver transistors | **not fitted.** Return to stock by hand: unplug the MRider halves and plug the factory pairs back together |
| 8 | E-stop button and contactor | **not fitted.** Replaced by the disconnect switch |
| 9 | Hardware RC signal MUX | **not fitted.** The Teensy's two pulse lines go straight to the driver |
| 10 | RC transmitter and receiver | **not fitted.** Manual driving is the USB gamepad, #15 |
| 11 | Logic battery, charger, two UBECs | **not fitted.** The Teensy is powered from the laptop's USB port |
| — | **Manual disconnect switch** | **added.** Specified in [ADR L](../design/adr-light.md#the-disconnect-switch) |

Everything else in Tier 1 and Tier 2 is fitted exactly as on `main`.

## Which page to follow, step by step

The full build guide is still in this branch, unedited — it arrives from `main` by merge and is
never changed here. **This table is the overlay**: it says which of those pages applies as
written, which applies with changes, and which is replaced.

| Step | On this branch |
|---|---|
| [1. BOM & Sourcing](../build/01-bom-sourcing.md) | As written, minus lines #7–#11, plus the switch. **Each tap needs one mating half, not two** — there is no relay for the second one to run to |
| [2. Mechanical](../build/02-mechanical.md) | **As written.** Sensors, mounts and the teardown are identical |
| [3. Electrical](../build/03-electrical.md) | **Power and authority are replaced by [Light wiring](wiring.md).** The sensor half — [§3.5](../build/03-electrical.md#35-signal-wiring) onward, the bench layout and the signal board — applies as written **except** §3.5.1, the signal MUX, which does not exist here |
| [4. Firmware](../build/04-firmware.md) | Toolchain and Stage 0 as written, **with one reversal: do not cut `VUSB`–`VIN`.** Stages 1 and 2 are replaced by [Light bring-up](bring-up.md) |
| [5. Software](../build/05-software.md) | **As written** |
| [6. Bench test](../build/06-bench-test.md) | Part A, failsafe verification, is replaced by [Light bring-up](bring-up.md). **Part B, calibration, as written** |
| [7. Manual drive](../build/07-manual-drive.md) | Replaced by stage L3 of [Light bring-up](bring-up.md). There is no RC phase and no E-stop phase |
| [8. Autonomous](../build/08-autonomous.md) | **As written** — with the arm's-reach rule still in force throughout |

## What stays identical, and why that matters

`mitt_msgs`, `mitt_description`, the controllers, SLAM and Nav2 are the same packages as on
`main`. `DbwStatus.mode` keeps all three of its values; Light never enters `MODE_MANUAL_RC`.
**Nothing under `ros2_ws/` or `firmware/` differs between the branches**, and
`bash scripts/check_docs.sh` fails here if anything outside `docs/light/`, `mkdocs.yml` and two
banners ever does.

That is deliberate. A Light vehicle that later gains the relay MUX, the RC set and the E-stop
becomes a full one **without changing a line of software above the Teensy** — the layers that were
left out are hardware, plus two firmware blocks.
