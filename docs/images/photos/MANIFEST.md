# Photographs — what each one is, and what it is evidence for

Every photograph published under `docs/images/photos/` has a row here. A drawing in
`docs/images/` is generated: it carries its own date implicitly, because re-running its
generator reproduces it. **A photograph cannot do that.** It shows one vehicle, on one day,
in one state, and nothing about the file says which — so a photograph of a superseded part
reads exactly like a photograph of the current one.

That is the same failure the dated-absence-claim rule exists for, and the checks already in
`scripts/check_docs.sh` cannot see it: check 12 (traction voltage), check 20 (motor driver)
and check 21 (absence claims) all read **text**. None of them look at an image.

So the rule is: **a photograph is published only with a row here**, and the row carries the
date, the vehicle, and — where it matters — what the photograph is *not* evidence for.

## Why these exist at all

The three vehicles and every part went to the student teams in the week of **2026-11-02**, so
nothing here can be re-shot. These were recovered on **2026-11-09** from the build log of the
conversation in which the decisions were made. The build guide cites photographs as evidence
in sixteen places; until now a reader could see none of them.

## Provenance

All photographs are the instructor's own, taken during this project's teardown and build.
They are published under the repository's Apache-2.0 licence along with everything else.

**No vendor or manufacturer images are published here.** Component listing photographs belong
to the seller or the maker; the BOM and the order log link to those listings instead, which is
a reference rather than a copy. The same applies to scans of third-party manuals.

## The photographs

| File | Shows | Vehicle | Dated | Used on | Not evidence for |
|---|---|---|---|---|---|
| `drive-gearbox-hub-and-nose.jpg` | The drive gearbox off the vehicle: the white six-lobe hub at the output end, and the short collar of grey housing it emerges from | #1 | 2026-11-04 | [01-bom-sourcing](../../build/01-bom-sourcing.md#the-bracket-clamp-the-gearbox-housing-nose-do-not-hunt-for-screw-bosses) | **Any dimension.** The nose diameter is still unmeasured, and that page says in as many words that reading one off a photograph is the mistake that cost four prints |
| `battery-bay-under-seat.jpg` | Seat removed: the traction battery and the stock controller in an open bay whose walls finish in a continuous flat rim | #1 | 2026-10-19 | [02-mechanical §2.7.1](../../build/02-mechanical.md#271-what-this-stage-actually-builds) | Bay dimensions — those were measured separately and are in that page's record sheet |
| `battery-bay-measured.jpg` | The same bay from above with the measurements drawn on at the time: 37 × 21 cm, seat screws 300 apart, spare holes 100 apart, 13 cm bay depth and 13 cm rim height | #1 | 2026-10-20 | [02-mechanical §2.7.1](../../build/02-mechanical.md#271-what-this-stage-actually-builds) | **Your bay.** Three vehicles; the figures are a reference to check against, not to assume |
| `traction-pack-label.jpg` | The traction pack's own label: type, chemistry, capacity, and both charge-voltage rows | #1 | 2026-11-09 *(label first read into the record 2026-11-05)* | [vehicle.md §3.1.1](../../design/vehicle.md#311-the-traction-pack-from-its-own-label) | Pack condition or state of charge |
| `stock-ecu-pcb-silkscreen.jpg` | The stock ECU's bare board: the `M3±`/`M2±`, `M1` and `P1` silkscreen, and `JR1630RX 20201216` | #1 | 2026-11-06 | [02-mechanical §2.2](../../build/02-mechanical.md#22-teardown) | Which conductor is which **on your vehicle** — the silkscreen names sockets, not colours |
| `stock-ecu-wire-colours.jpg` | The same module installed, with its wire bundle: red/green, blue/yellow, brown, white | #1 | 2026-11-06 | [02-mechanical §2.2](../../build/02-mechanical.md#22-teardown) | **Any wiring decision.** Colour is the weakest evidence on this vehicle; trace, do not match |
| `relay-5-pin-body.jpg` | The 5-pin relay moulding: `KKA B8`, `COIL:12VDC`, `70A/14VDC`, `40A/28VDC`, and a schematic with `87a` | #1's part | 2026-10-26 | [01-bom-sourcing §1.3](../../build/01-bom-sourcing.md#7-8-11-12-14-what-to-actually-buy) | A different batch. Relay markings vary by shipment — this is why the page says read the part |
| `relay-4-pin-body.jpg` | The 4-pin relay moulding: `KKA V4`, `012-1H-12`, `NO 40A 14VDC`, four terminals and no `87a` | #1's part | 2026-10-26 | [01-bom-sourcing §1.3](../../build/01-bom-sourcing.md#7-8-11-12-14-what-to-actually-buy) | As above |
| `drive-hub-caliper.jpg` | A caliper across two opposite lobe crests of the drive hub, reading 62.82 mm | #1 | 2026-11-04 | [01-bom-sourcing §1.3](../../build/01-bom-sourcing.md#7-8-11-12-14-what-to-actually-buy) | **Your hub.** Three vehicles, and the same hub read 62.23, 62.70 and 62.82 across three sessions |
| `traction-pack-connector.jpg` | The pack's pigtail ending in a red keyed 2-pin housing, with the stock inline protector downstream — and no posts anywhere | #1 | 2026-10-02 | [01-bom-sourcing §1.5](../../build/01-bom-sourcing.md#15-connector-and-consumable-list) | The protector's rating, which is not legible here |
| `perfboards-as-delivered.jpg` | The two perfboards as bought: the pad array, the blank margin, and a plated hole at each corner | #1's parts | 2026-11-05 *(the page's own date; this one arrived between two messages and carries no timestamp of its own)* | [03-electrical §5](../../build/03-electrical.md#354-transferring-to-perfboard-three-boards-become-one) | Hole **count** — count yours. The point of the photograph is that the corner holes exist |
| `drive-hub-lobes-end-on.jpg` | The gearbox output end-on, in the hand: six broad lobes, six narrow gaps, a bearing and an empty bore, with the red circumference wire still lying in the gaps | #1 | 2026-10-06 | [01-bom-sourcing](../../build/01-bom-sourcing.md#measurements-this-needs) | **Any diameter.** The red wire in this frame is the wrap measurement that page then discarded |
| `drive-gearbox-nose-side-view.jpg` | The same gearbox from the side with a tape along it: the white hub leaves the grey housing as a step standing clear of it | #1 | 2026-10-08 | [01-bom-sourcing](../../build/01-bom-sourcing.md#measurements-this-needs) | **The 10 mm.** It is a tape read against a curved grey step; the photograph shows only that the boss is not sunk |
| `steering-tap-caliper.jpg` | A caliper across the steering tap's white 2-position housing, reading 8.35 mm | #1 | 2026-11-06 | [02-mechanical §2.2](../../build/02-mechanical.md#22-teardown) | The **pitch**, which is what identifies this connector. Housing width does not — a 2-way housing is about the same at three different pitches |
| `drive-tap-caliper.jpg` | A caliper across the drive tap's white 2-position flat-blade housing, reading 16.19 mm | #1 | 2026-11-06 | [02-mechanical §2.2](../../build/02-mechanical.md#22-teardown) | The **tab cross-section**, which is what identifies this connector. Nothing in frame shows the 6.3 × 0.8 |

## Adding one

1. The photograph is the instructor's own, or it does not go in.
2. Name it for what it shows, as the drawings are named — not `IMG_0423.jpg`.
3. JPEG, at the resolution it survives at. These were downscaled before they ever reached a
   file and **cannot be improved**; do not upscale one to make it look better than it is.
4. Add the row above, with the date and the vehicle.
5. Link it from the page whose claim it supports. A photograph nobody links to is a file.
