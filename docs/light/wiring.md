# Light wiring — power and authority

Replaces [§3.1 to §3.4](../build/03-electrical.md#31-the-two-rails) and
[§3.5.1](../build/03-electrical.md#351-hardware-rc-signal-mux-wire-this-it-is-not-optional) of the
full electrical page. **The sensor wiring is not on this page because it does not change** — the
AS5600, the two Hall latches, the bench layout and the signal board are
[§3.5](../build/03-electrical.md#35-signal-wiring) as written.

*Written 2026-11-10; never built. See [the overview](index.md).*

---

## The whole circuit

```
Traction pack
  │
  └─[factory connector]─[MRider power-tap half]─▶ 25 A fuse ─▶ DISCONNECT SWITCH ─▶ driver B+
                                                                  pack − ──────────▶ driver B−

  driver Left  ─▶ [MRider steering-tap half] ─▶ the vehicle's own steering plug ─▶ steering gearmotor
  driver Right ─▶ [MRider drive-tap half]    ─▶ the vehicle's own drive plug    ─▶ both rear motors

  The stock ECU drives nothing: both of its motor plugs are out, and they stay out.

Laptop (on its own battery)
  │
  └─ USB ─▶ Teensy 4.1   power AND data, one cable
              ├─ 3.3 V pin ─▶ AS5600, two Hall latches + pull-ups      (unchanged)
              ├─ PWM out ──┬─▶ driver RC1   steering
              │            └─ 10 kΩ to GND
              ├─ PWM out ──┬─▶ driver RC2   drive
              │            └─ 10 kΩ to GND
              └─ GND ───────▶ driver signal GND
```

There is **one** rail with motors on it and **one** source for the controller, and they meet only
at the signal ground. Compare [the full design's two rails](../build/03-electrical.md#31-the-two-rails):
the third battery, both regulators, every relay coil and the contactor are gone.

## The traction side

**Fuse first, then the switch, then the driver.** The fuse sits as close to the pack as the
harness allows, so that a fault anywhere downstream of it — including in the switch — is fused.
Fuse value, wire gauge and the reasoning behind both are
[§3.2](../build/03-electrical.md#32-per-rail-fuse-and-gauge-table) and are unchanged. **So is its
warning about the steering branch:** the steering tap is AWG 20 behind this 25 A fuse, and wants
an inline fuse of its own. With no relay in Light, that fuse goes in the lead from the driver's
Left output to the steering-tap half.

**The switch** is specified in [ADR L](../design/adr-light.md#the-disconnect-switch): DC-rated for
at least the fuse's current, no coil, and mounted where a hand reaches it from outside the body
without passing a wheel. **Mount it before anything else on this page** — it is the first thing
you will want and the last thing people fit.

**The stock ECU's supply.** The full design's power tap is a pass-through, because the stock ECU
has to stay powered for STOCK mode. Light needs only the first half. A pass-through harness built
for the full design works unchanged — the ECU powers up and drives nothing — and a new one can
simply end at the fuse.

## The motor leads — one mating half per tap

In the full design each tap is cut into by a relay, so each needs both halves of its connector.
**Here the vehicle's own plug goes straight to the driver, so each tap needs only the half that
mates with the vehicle's plug.** Which connector that is, for each tap, is
[02-mechanical §2.2](../build/02-mechanical.md#22-teardown) and
[the part-number table](../build/03-electrical.md#the-same-two-taps-part-number-by-part-number).
The two are different families and cannot be swapped with each other.

> [!CAUTION]
> **One mis-plug survives the simplification, and it bypasses both the fuse and the switch**
>
> The power tap and the drive tap are the **same** flat-blade family in the same keyed housing
> ([FMEA row 12](../design/safety.md#7-fmea-lightweight), confirmed 2026-11-07). In the full
> design that mistake puts the pack on the stock ECU's outputs. There is no relay here, so that
> exact fault is gone — **but plug the drive-tap half onto the pack's connector and the pack is on
> the driver's motor terminals.** An H-bridge's body diodes conduct from its outputs to its supply,
> so the driver powers up **through its own output stage, upstream of the fuse and of the switch.**
>
> The mitigation is the full design's, and it is geometry rather than labelling: **cut the
> drive-tap pigtail too short to reach the pack, and the power-tap pigtail too short to reach the
> ECU bay.** Then fit and verify the power tap before the drive tap is opened at all.

**Polarity is found, not assumed.** Which way each motor turns for a positive command is settled
at stage L1 of [bring-up](bring-up.md), on a current-limited supply. Record which way it was
fixed — leads swapped at the driver, or a sign in firmware — because the next person will
otherwise fix it a second time, in the other place.

## The controller side

**The Teensy runs from the laptop's USB port, so do not cut `VUSB`–`VIN`.** This reverses the
[first instruction of the firmware page](../build/04-firmware.md), which exists because the full
design feeds `VIN` from a regulator. A board whose pads were already cut must have them bridged
again before it will power up here.

*Do not feed `VIN` from a regulator on the traction pack instead.* It looks equivalent and is the
one thing the logic battery was bought to prevent: a stalled motor sags the pack, and the
controller resets at the moment it is needed.

**Run on the laptop's battery whenever the switch is closed.** That is what makes "the traction
rail cannot reach the controller" true without qualification, and a driving vehicle cannot trail
a charger anyway.

**The two pulse lines go straight to `RC1` and `RC2`**, with a 10 kΩ resistor from each to signal
ground at the driver. When the Teensy is unpowered its pins float, and the driver should see *no
pulse* rather than whatever the lead picks up beside a motor. **Whether that is enough is an open
question, not a fact** — what the MDDS30 reads on an undriven input is not recorded in this
repository as of 2026-11-10 — and test T3 in [bring-up](bring-up.md) is what settles it.

**Signal and ground only. Nothing goes to the centre pin of the driver's RC header.** That pin is
the driver's own 5 V coming out
([§3.5.1](../build/03-electrical.md#351-hardware-rc-signal-mux-wire-this-it-is-not-optional));
tying it to the Teensy's 5 V would join the laptop's USB supply to a regulator on the traction
pack.

**Pins.** The [pin table](../build/04-firmware.md#the-pin-assignment-the-one-table-that-must-be-frozen-before-an-iron-is-hot)
is still the only place a pin number is decided. Three of its rows have nothing to connect to in
Light: *E-stop sense*, *Relay gate* and *i-BUS RX*. Leave those pins unconnected rather than reusing
them, so a board built for Light can still become a full one.

**DIP switches** are the driver's and do not change with the variant:
[§3.5](../build/03-electrical.md#35-signal-wiring) has the table. `SW6 = 0` matters more here than
anywhere — the 100 ms signal-loss stop is the last link in two of Light's stops, and `SW6 = 1`
turns it off.

## Power-on order, which the switch now enforces

The driver takes whatever pulse it sees at power-up as *stop*
([dbw.md §4.1](../design/dbw.md#41-part-substitution-cytron-mdds30-replaces-the-sabertooth-2x32-2026-09-29)).

| | |
|---|---|
| **On** | USB in → wait for the Teensy to be emitting neutral on both lines → **then** close the switch |
| **Off** | Open the switch → then USB out |
| **Again, after the switch was opened** | Release the deadman → **reset the Teensy** → wait for neutral → close the switch |

**Never close the switch with the Teensy unpowered.** The driver would calibrate its centre on a
line carrying nothing.

**And never close it on a Teensy that is mid-command.** The firmware has no way to know the switch
was opened — Light has no sense line for it — so it goes on emitting whatever its loop asks for,
and the driver would take *that* as stop. Resetting the Teensy is what guarantees neutral.
[Bring-up](bring-up.md) test T8a exists for this.

## Before any power

[§3.6](../build/03-electrical.md#36-continuity-and-isolation-checks-before-any-power) applies, less
every line about a relay, a coil or the logic rail. Add three:

- [ ] Switch open: **no continuity** from the pack `+` connector to driver `B+`.
- [ ] Switch closed, fuse out: still none. *The fuse and the switch are each able to open the
      circuit alone.*
- [ ] Drive-tap pigtail offered up to the pack connector: **it does not reach.**
