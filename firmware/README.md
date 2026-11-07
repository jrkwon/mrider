# Firmware

## What is here, and what is not

**Three bench sketches.** They cover steps 3, 4 and 5 of the five-step bench order in
[`03-electrical.md §3.5.3`](../docs/build/03-electrical.md#353-build-the-circuit-twice-and-not-for-the-reason-it-sounds-like),
and nothing beyond it.

| Step | Environment | Proves |
|---|---|---|
| 1 | *(no code)* | 3.3 V on the rail. A meter, so a jumper fault cannot be blamed on software |
| 2 | *(no code)* | each Hall latch snaps 0 ↔ 3.3 V and **stays**. A meter and a magnet |
| 3 | `i2c_scan` | `0x36` answers, **and nothing else does** — the design is one device per bus |
| 4 | `as5600_check` | air gap set by AGC, and **no wrap** over the full mechanical travel |
| 5 | `quad_count` | counts rise one way and fall the other — the first proof of the half-pitch offset |

> [!IMPORTANT]
> **The vehicle firmware does not exist yet.** Nothing here closes a loop, drives a motor,
> speaks micro-ROS, reads i-BUS or implements the safety state machine. Those are Stages 0–2
> in [`04-firmware.md`](../docs/build/04-firmware.md), and that page describes what they must
> do rather than shipping something that does it.
>
> *This README exists because the build pages referred to "a scan sketch" and "the decoder" as
> though they were on the shelf, and until 2026-11-07 there was no `firmware/` directory at
> all. A procedure that names a tool nobody has written is a procedure nobody can follow.*

## Running one

[PlatformIO](https://platformio.org/), as [`04-firmware.md §4.2`](../docs/build/04-firmware.md#42-toolchain-setup)
specifies:

```bash
pip install --user platformio
cd firmware/bench
pio run -e i2c_scan     -t upload -t monitor      # step 3
pio run -e as5600_check -t upload -t monitor      # step 4
pio run -e quad_count   -t upload -t monitor      # step 5
```

Each environment builds **exactly one** source file. There is no shared state between them, so
no sketch can mask another's fault — which is the same reason the five steps are separate steps.

## Pins come from one table and are not repeated here

[`04-firmware.md` § the pin assignment](../docs/build/04-firmware.md#the-pin-assignment-the-one-table-that-must-be-frozen-before-an-iron-is-hot)
is the only place pin numbers are decided. The sketches use `18/19` for I²C because the Teensy
4.1's `Wire` fixes them, and `0/1` for the encoder because that table chose them. **If you change
a pin, change it there first** — the bench layout and the soldered signal board both read from
that table, and if any of the three disagreed the bench would prove nothing about the board.

## Two numbers in this code that came from somewhere

Both are the kind that are easy to type wrong and impossible to notice:

- **AGC mid-scale is ≈ 64, not 128.** The AS5600's AGC spans `0–255` at 5 V but `0–128` at
  3.3 V, and the Teensy 4.1 is a 3.3 V part. Aiming at 128 on this board means closing the air
  gap until the magnet nearly touches and the sensor still reports *too weak*.
- **36 counts per revolution.** 18 alternating magnets are **9 electrical cycles**, and the
  Teensy's hardware decoder counts all four edges, so `9 × 4 = 36`. That is the figure the
  sizing table in [`01-bom-sourcing.md`](../docs/build/01-bom-sourcing.md) settled on when it
  chose 18 magnets over 12 or 24.

## Status

Written 2026-11-07. **Built in CI against the pinned `teensy@6.0.0` platform; never run on
hardware.** The first person to flash them should expect to fix something, and should fix it here
rather than in a copy.

*Until 2026-11-07 this said "syntax-checked against stub headers; never compiled" — and nothing
in CI touched `firmware/` at all, so the statement was true and stayed true. A page that tells
thirteen students to flash something should know the something builds; the
[`firmware` job](https://github.com/jrkwon/mrider/blob/main/.github/workflows/workspace.yml) now
does, in minutes and with no hardware.*
