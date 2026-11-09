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
| `traction-pack-label.jpg` | The traction pack's own label: type, chemistry, capacity, and both charge-voltage rows | #1 | 2026-11-09 *(label first read into the record 2026-11-05)* | [vehicle.md §3.1.1](../../design/vehicle.md#311-the-traction-pack-from-its-own-label) | Pack condition or state of charge |

## Adding one

1. The photograph is the instructor's own, or it does not go in.
2. Name it for what it shows, as the drawings are named — not `IMG_0423.jpg`.
3. JPEG, at the resolution it survives at. These were downscaled before they ever reached a
   file and **cannot be improved**; do not upscale one to make it look better than it is.
4. Add the row above, with the date and the vehicle.
5. Link it from the page whose claim it supports. A photograph nobody links to is a file.
