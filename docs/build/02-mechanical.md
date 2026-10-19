# 2. Vehicle Prep & Mechanical

**Goal:** prepare the chassis and mount the steering actuator and encoders mechanically.

Disassemble the necessary trim, identify the steering column and drive-motor shaft,
and fit the steering gearmotor, the absolute steering-angle sensor, and the drive-shaft
encoder. Keep the modifications minimally invasive and reversible.

- **Prerequisites:** Section 1 complete; chassis selected.
- **Specification:** [design/vehicle.md](../design/vehicle.md), [design/dbw.md](../design/dbw.md)
- **Expected outcome:** actuator and sensors mechanically mounted; stock steering still
  reassemblable.

> [!WARNING]
> **Draft — not yet validated on hardware**
>
> No MRider vehicle has been disassembled yet. **There are no teardown photos, no bracket
> dimensions, and no torque figures in this page, because none have been measured.** Every
> such value is marked *(measure during bring-up)*. This page gives you the procedure and
> the record sheets; you produce the numbers.

---

## 2.1 Before you take anything apart

**Photograph everything.** Every trim panel, every connector, every cable route, before it
moves. The reversibility requirement means you must be able to put this vehicle back to
factory-stock, and the parent-remote harness routing is not documented by the manufacturer.

Run the [vehicle.md §3 verification checklist](../design/vehicle.md) on the unit you
actually bought — the candidate models in the design doc were evaluated from listings, not
in person. Specifically confirm:

| Check | Why it matters | Result |
|---|---|---|
| Battery is genuinely 12 V | The whole power tree assumes it, and [ADR D-R](../design/vehicle.md#adr-d-r-reversal-to-the-12-v-single-seater-2026-08-08) pinned the class | *(measure during bring-up)* |
| Two independent rear drive motors | [Throttle path](../design/dbw.md#7-throttle-path) parallels them onto Sabertooth M2 | *(measure during bring-up)* |
| Steering column is accessible without cutting | Reversibility principle | *(measure during bring-up)* |
| Column has a stock steering motor, or is hand-turned only | Determines whether the steering tap intercepts an existing motor or adds one | *(measure during bring-up)* |
| Paralleled drive-motor **stall current** vs. 32 A/channel | Sabertooth rating limit ([dbw.md §7](../design/dbw.md#7-throttle-path)) | *(measure during bring-up)* |
| Front wheel travel is ≈ ±22.5° | The pinned steering range ([dbw.md §12](../design/dbw.md#12-numeric-interface-contract)) | *(measure during bring-up)* |

> [!CAUTION]
> **Disconnect the battery before disassembly**
>
> The traction pack is live at the motor terminals even with the vehicle "off" on many
> ride-on models. Pull the pack or the main fuse first.

## 2.2 Teardown

Work in this order and bag-and-tag fasteners by panel.

1. **Remove the seat and body trim** covering the rear motor bay and the steering column.
   Ride-on bodies are typically self-tapping screws into plastic bosses — they strip easily,
   so go slow and do not over-torque on reassembly.
2. **Identify and photograph the stock harness.** You need three interception points, and
   you want to see them before anything is cut or unplugged:
    - the **throttle** leads to the rear motors,
    - the **steering** leads (if a stock steering motor exists),
    - the **12 V pack** output.
3. **Expose the steering column** from the wheel down to the linkage. Note the column
   diameter, its total lock-to-lock rotation, and whether there is a usable flat or
   D-profile for a coupler set screw.
4. **Expose one rear drive-motor shaft.** Only one shaft is instrumented — see
   [ADR C](../design/dbw.md#8-adr-c-drive-distance-encoding) — so pick the more accessible
   one and note which side, because your odometry inherits that side's behavior in turns.

**Record sheet — teardown measurements**

| Measurement | Units | Value | Method |
|---|---|---|---|
| Column diameter | mm | *(measure during bring-up)* | Calipers |
| Column lock-to-lock rotation | ° | *(measure during bring-up)* | Angle gauge on the wheel |
| Road-wheel travel, center → full lock, left | ° | *(measure during bring-up)* | Angle gauge on the tire |
| Road-wheel travel, center → full lock, right | ° | *(measure during bring-up)* | Angle gauge on the tire |
| Column-to-road-wheel ratio | — | *(measure during bring-up)* | Derived from the two rows above |
| Drive-motor shaft diameter | mm | *(measure during bring-up)* | Calipers |
| Instrumented side | L / R | *(measure during bring-up)* | — |
| Wheelbase (rear axle → front axle) | m | *(measure during bring-up)* | Tape |
| Track (wheel separation) | m | *(measure during bring-up)* | Tape |
| Loaded wheel rolling circumference | m | *(measure during bring-up)* | Mark tire, roll one revolution |

The last three rows feed the Ackermann parameters in
[software.md §3.2](../design/software.md#32-ackermann-kinematic-parameters), which are
currently B-MROVER placeholders — treat **every** dimension there as a placeholder until you
have filled this table.

## 2.3 Column travel decides your angle sensor

You ordered a sensor in step 1 based on an estimate. Confirm it now, before mounting.

- **Column lock-to-lock ≤ ~300°** → the single-turn potentiometer is correct. Coupled 1:1 to
  the column, its absolute range maps monotonically across the whole travel with margin.
- **Column lock-to-lock > ~330°** → you are inside the pot's end-stop/dead-band risk, or past
  one turn entirely. Either take the sensor off a reduced take-off shaft, or switch to the
  multi-turn magnetic option — the escape hatch in
  [dbw.md §6](../design/dbw.md#6-adr-angle-sensor-technology-magnetic-encoder-vs-potentiometer).

> [!NOTE]
> **The pot's dead-band must sit outside the working range**
>
> A single-turn pot has a mechanical/electrical dead zone at the ends of its sweep. Mount
> it so that the **±22.5° road-wheel working range lands near the middle** of the pot's
> travel, not near either end. You verify this during zeroing in
> [step 6](06-bench-test.md), but you have to get the mounting clocking approximately right
> now — rotating a bonded coupler later is unpleasant.

## 2.4 Mount the steering gearmotor

The gearmotor drives the column through the existing steering linkage and is driven by
**Sabertooth channel 1 (M1)**. The Teensy commands it as a *signed effort* — the output of the
position loop — never as an angle
([dbw.md §2.3](../design/dbw.md#23-why-the-sabertooth-receives-an-effort-command)).

1. **Decide the coupling point.** Either directly on the column (simplest, needs a coupler
   sized to the column diameter) or on the tie-rod arm (more mechanical advantage, more
   bracket work). Whichever you pick, the sensor and the motor must see a **rigid,
   backlash-free** path to the road wheels or the position loop will hunt.
2. **Fabricate or print the motor bracket.** It must resist the *stall* torque of the motor,
   not its rated torque — a position loop against a limit will apply full effort until the
   Teensy's stall detector clamps it. Reuse the mrover 3D-print approach
   (`config/3D_design/v3/`) as a starting point for enclosures.
3. **Fit the coupler** with set screws onto a flat or D-profile if one exists. If the column
   is perfectly round, use a clamping-style coupler — set screws on a round shaft will slip,
   and a slipped steering coupler means your absolute reference silently walks away from
   center.
4. **Check for interference through full travel** — turn lock to lock by hand and confirm
   nothing fouls the body, the linkage, or the wiring.

**Record sheet — steering actuator**

| Item | Value |
|---|---|
| Measured peak force `F` at rim, center → lock, stationary, full load | *(measure during bring-up)* N |
| Lever radius `r` | *(measure during bring-up)* m |
| Computed `τ_column = F × r` | *(measure during bring-up)* N·m |
| Motor rated torque (through coupling ratio) | *(measure during bring-up)* N·m |
| Margin achieved (target ≥ 2×) | *(measure during bring-up)* |
| Coupling point | column / tie-rod arm |
| Motor model + gear ratio | *(record)* |
| Bracket source | printed / fabricated — *(record STL or drawing)* |

If you have not yet done the torque measurement, the procedure is
[dbw.md §2.2](../design/dbw.md#22-torque-measurement-procedure-before-sizing-the-gearmotor) —
do it **at full load on the target operating surface**, because tire scrub on carpet and on
asphalt differ enough to change the motor choice.

## 2.5 Mount the absolute angle sensor

This sensor is the authoritative angle source for the entire system
([ADR B](../design/dbw.md#5-adr-b-steering-angle-encoding)). Everything downstream —
the position loop, odometry, the behavior-cloning steering labels — inherits its mounting
quality.

1. **Couple it 1:1 to the column** (or to a take-off that sees ≤ one turn).
2. **Clock it so the working range is centered** in the sensor's sweep (§2.3).
3. **Mount the body rigidly.** A sensor body that can rotate under vibration produces a slow,
   invisible calibration drift — the exact failure mode the absolute sensor was chosen to
   avoid.
4. **Strain-relieve the wiring.** For the pot fallback, feed it from the Teensy's *regulated* rail so the
   reading is ratiometric and supply drift cancels
   ([dbw.md §6 consequences](../design/dbw.md#6-adr-angle-sensor-technology-magnetic-encoder-vs-potentiometer)).

The gearmotor's own incremental encoder, if it has one, mounts with the motor and is
auxiliary — it provides velocity and stall detection only.

## 2.6 Mount the drive-shaft encoder

> [!WARNING]
> **This section used to describe the mrover shaft-adapter method. You cannot do it on this
> vehicle, and following it will waste a teardown.** It called for a 3.15 mm → 5 mm adapter onto
> the drive-motor shaft with the encoder bracketed to the motor mount. This vehicle's motor has a
> **2 mm shaft carrying a pinion straight into a sealed gearbox** — there is no shaft to couple to
> and no face to bracket against. That is exactly why
> [§1.2.3 branches A and B](01-bom-sourcing.md#6-drive-encoder-what-to-actually-buy) were closed and
> **Branch C** taken. *Corrected 2026-10-06.*

Measure at the **gearbox output hub** instead — 1:1 with the wheel, which is better than the motor
shaft was going to be. The buildable form is specified in full at
[§1.2.3](01-bom-sourcing.md#6-drive-encoder-what-to-actually-buy); the mechanical work here is:

1. **Pull the wheel.** The carrier is a one-piece ring and goes on over the hub.
2. **Print the fit mule first** (`PART = "gauge"` in `cad/drive_encoder_carrier.scad`), fit it,
   refit the wheel and **turn one revolution**. Nothing may touch. Do not populate a carrier with
   magnets until a mule has passed on that vehicle.
3. **Fit the carrier**, rotating it one lobe so the three grub screws drop into lobe gaps rather
   than onto crests, and tighten them in rotation so the ring centres itself.
4. **Bracket the two Hall latches to something that does not turn**, with both sensors in one
   printed part so their **6.80 mm** spacing is fixed by construction rather than by assembly.
5. **Route the encoder cable away from the motor leads.** Encoder lines next to a PWM'd motor pick
   up noise that reads as phantom ticks.

**Concentricity still matters, and the mount now supplies it** rather than asking the builder for
it: the carrier is centred by three screws on a round hub, and the bracket clamps the gearbox
housing nose, which is concentric with the axle. A carrier that runs out produces periodic tick
errors that alias into odometry — the same failure the old shaft-adapter note warned about, from a
different cause.

**Direction comes from quadrature, so the two sensors are not optional** and neither is the
**latch** type — [§1.2.3](01-bom-sourcing.md#6-drive-encoder-what-to-actually-buy) explains why a
Hall *switch* cannot do this job.

> [!NOTE]
> **You are instrumenting one motor of a paralleled pair**
>
> This is a known, documented limitation, not a mistake. Motor-shaft measurement inherits
> gearbox backlash, wheel slip, and differential wheel speed in turns. The EKF fuses it
> with the IMU to bound drift, and step 6's roll-out calibration bounds the scale error.
> See [ADR C consequences](../design/dbw.md#8-adr-c-drive-distance-encoding) — this is
> worth understanding now, because it is why nobody should expect raw wheel odometry to
> close a loop.

## 2.7 Mount the sensor mast and compute

Camera and LiDAR mounting geometry comes from
[sensors.md §5](../design/sensors.md#5-mounting-mast-concept). Two mechanical constraints
matter at this stage:

- **Rigidity.** Extrinsics calibrated in step 6 are only valid while the mast holds its
  geometry. A mast that flexes under acceleration invalidates the camera↔LiDAR projection.
- **Reachability.** You will re-seat USB connectors more often than you expect during
  bring-up. Do not bury them.

The laptop rides on its own battery and is not wired into the 12 V system in v1
([safety.md §5](../design/safety.md#5-power-rail-isolation-and-brownout-protection)) —
mechanically, it just needs a secure, ventilated place to sit.

### 2.7.1 What this stage actually builds

> [!IMPORTANT]
> **Build the plates first — and there are two of them, at two heights.**
>
> ![Cockpit plan view: a raised, moulded seat plinth at the rear carrying only the mast on four printed standoffs, and a flat low footwell at the front carrying the motor driver, battery and both enclosures](../images/cockpit-zones.svg)
>
> The cockpit photographs taken 2026-10-19 corrected an assumption this section started with — that
> removing the seat leaves *one* flat area. It does not.
>
> | Zone | What it is | What goes on it |
> |---|---|---|
> | **A — seat plinth**, rear | raised and **moulded**, not a flat pad | **the mast, and nothing else** |
> | **B — footwell**, front | flat, low, under the rubber mat | motor driver, battery, **both enclosures** |
>
> **The split is not tidiness, it is centre of gravity.** Zone B is the lowest already-flat surface
> in the vehicle and it is load-bearing by design — a child stands on it. Every gram put there is a
> gram not raising the centre of mass that the mast is already working against, and it is carried on
> a floor rather than on four moulded bosses.
>
> **Zone A's plate sits on four printed PETG standoffs, each cut to its own height** (D1), so it
> finishes level in spite of the contour. A plate that rocks under a 500 mm mast is a plate that
> works loose.
>

> [vehicle.md §3](../design/vehicle.md) records that this chassis has **no flat deck** — the seat is
> the only flat area, it comes out, and an **equipment plate** takes its place. The mast, both
> enclosures, the IMU and the motor driver all land on that plate, so it is not an accessory to this
> stage; it is the stage's first part.

Five parts, in this order. **Nothing is cut or printed before
[V4](../order-log.md) is filled in** — the drive encoder cost four wasted
prints and 20 g of filament by designing to a hub diameter nobody had measured across.

| Order | Part | Made from | Gated on |
|---:|---|---|---|
| 1 | **Plate A** (mast) + four standoffs | 12 mm plywood on printed PETG standoffs, on the seat plinth | V4 **D1–D3** |
| 1 | **Plate B** (electronics) | 12 mm plywood, cut to the footwell floor | V4 **D4**, **D7** |
| 2 | **Mast + base rail** | 2020 aluminium extrusion, on Plate A | V4 **D1–D3** |
| 3 | **LiDAR mount** | printed PETG, clamps to the 2020 T-slot | V4 **S** |
| 4 | **Camera mount** | printed PETG, clamps to the 2020 T-slot, ~10–15° down | V4 **S** |
| 5 | **Two enclosures** | printed PETG, heat-set M3 inserts from [#14](../order-log.md) | V4 **E**, plus #7 and #8 in hand |

**The mast is extrusion, not a print.** A 0.65 m printed tube delaminates along its layer lines
under exactly the bending load a mast sees, and that flex lands straight in the camera↔LiDAR
extrinsics the bullet above calls load-bearing. The T-slot earns its place twice over: sensor height
becomes adjustable **without reprinting a bracket**, which matters over sixteen weeks.

**The plate is plywood, not aluminium or print.** A 30–40 cm span is past most printer beds, and a
split plate puts a glue joint directly under the mast base. Plywood is re-drillable on the bench
with a cordless drill, which is what a cohort of thirteen moving the layout actually needs, and it
damps better than aluminium — relevant because vibration is an IMU and camera problem here, not a
comfort one.

**Two enclosures, not one** — power (contactor, relay MUX, fuses, XT60, logic battery, UBECs) and
logic (Teensy, RC signal MUX, receiver). The rail isolation in
[safety.md §5](../design/safety.md#5-power-rail-isolation-and-brownout-protection) is currently a
claim in a document; two boxes make it something you can see without a meter, and they keep a 30 A
PWM harness out of the box students open every week.

> [!WARNING]
> **The motor driver goes in neither box.**
>
> The MDDS30 dissipates into a heatsink. Enclose it and the heatsink does nothing. It mounts in
> **open air on the plate**, under a vented guard that stops a dropped spanner reaching the
> terminals — a guard, not a case.

### 2.7.2 The layout and the cut plan

![Sensor mast layout: a 500 mm 2020 post on a 250 mm fore-aft base rail bolted through the plywood plate, the LiDAR on a printed cap at the top of the post so the scan plane is clear of the mast, and the camera on a 150 mm forward boom pitched 12 degrees down; alongside, how one 900 mm length is cut into post, rail and boom, and why a post beside the LiDAR leaves a permanent blind sector](../images/sensor-mast-layout.svg)

**One 900 mm length of 2020 per vehicle, cut into three. Two cuts, no offcut.**

| Piece | Length | Job |
|---|---:|---|
| **Post** | 500 mm | vertical; carries everything |
| **Base rail** | 250 mm | flat on the plate, fore-aft, **T-slot facing up** |
| **Camera boom** | 150 mm | horizontal, forward, at ~380 mm |

Aluminium 2020 cuts with a hacksaw and a mitre box in about two minutes. **File the cut square** —
a post that meets the rail out of square puts the whole mast out of plumb, and the camera pitch is
then wrong by whatever the error is.

**The four corner brackets each have a job.** Two at the post foot, **front and rear**, because
braking and kerb strikes load the mast fore-and-aft and that is the plane that needs the triangle.
Two at the boom joint, above and below, which is what stops the camera drooping and twisting. The
base rail needs none — it bolts **down through the plywood into T-nuts** in its upward slot, which
is both stronger and easier to move later. The LiDAR needs none either: a printed cap slides onto
the post's top end and carries its bolt pattern.

> [!IMPORTANT]
> **The LiDAR goes on TOP of the post, and the camera below it on the boom — the reverse of
> [sensors.md §5](../design/sensors.md#5-mounting-mast-concept)'s ordering**
>
> That section puts the camera at the top and the LiDAR below it. **It also gives the reason — the
> body and mast tube should "occlude as little as possible" — and the reason beats the ordering.**
>
> A post running past the side of a LiDAR subtends a **permanent blind sector of roughly 20°**: a
> 20 mm post at ~55 mm from the scan centre. It is in every scan, every map and every costmap, and
> it points backwards, which is where you most want to see while reversing. Put the post **under**
> the scan plane instead and the occlusion is **zero** — the mast simply ends below the sensor.
>
> The price is camera height: **~390 mm instead of ~550 mm.** That is acceptable because the
> camera's height only has to be **fixed and recorded**, not maximised — §5's own warning is that a
> policy trained at one height does not transfer, which is an argument for writing the number down,
> not for making it large. At 390 mm and 12° down the optical axis meets the ground at ~1.8 m, so
> the 2–8 m band §5 asks for is still well inside the frame.
>
> **Record the final heights in [calibration.md](../design/calibration.md)** before the first
> behavior-cloning dataset is captured.

> [!WARNING]
> **The seat bolts thread into body plastic — confirmed 2026-10-19. Label the mast NOT A HANDLE.**
>
> Run the numbers rather than guessing. 0.5 kg of sensors at 0.555 m hitting a kerb at 1 g is
> **2.7 N·m**; across the 250 mm base rail that is **±11 N, about 1 kgf per end** — a moulded boss
> shrugs it off. One adult leaning **10 kgf** on the mast top is **54 N·m**, which is **±216 N or
> 22 kgf of pull-out per end**, and that is what tears a boss out of a moulding.
>
> **Driving is not the hazard. Handling is.** So the response is three cheap changes rather than a
> heavier mast — the **250 mm base rail** (a couple, not a point load), a **plate that extends past
> the seat bolt pattern** so it bears on the tub shell in compression, and **large backing washers**
> under the plastic. Then the rule that follows from the second number: never lift, push, drag or
> park the vehicle by the mast, and put a label on it saying so where a student will read it.

### 2.7.3 Before the first cut

- [ ] [V4 **D**](../order-log.md) — deck geometry, **and whether the seat bolts thread into metal or plastic**
- [ ] [V4 **S**](../order-log.md) — LiDAR and camera bodies; both parts are already in hand
- [ ] [V4 **E**](../order-log.md) — every item destined for the two boxes, measured **and weighed**
- [ ] Build **vehicle 1 only**, fit it, drive it, then repeat for 2 and 3

## 2.8 Confirm reversibility

Before moving to electrical, satisfy yourself that this is still a stock vehicle underneath:

- [ ] No stock harness wire has been **cut** — all interception is at inline connectors
- [ ] All removed trim and fasteners are bagged, tagged, and photographed
- [ ] The stock steering path still functions mechanically if the gearmotor is unbolted
- [ ] You can describe, out loud, how to return this vehicle to factory condition

## 2.9 Gate to step 3

- [ ] Teardown record sheet complete — all *(measure during bring-up)* rows filled
- [ ] Column travel measured; angle-sensor technology confirmed against it
- [ ] Steering gearmotor mounted; ≥2× torque margin confirmed against measured `τ_column`
- [ ] Absolute angle sensor coupled, clocked centered, rigidly mounted, strain-relieved
- [ ] Drive-shaft encoder mounted concentric, cable routed away from motor leads
- [ ] Full steering travel checked for interference, lock to lock
- [ ] Wheelbase, track, and loaded rolling circumference recorded for
      [software.md §3.2](../design/software.md#32-ackermann-kinematic-parameters)
- [ ] Reversibility checklist (§2.8) passes

---

**Previous:** [1. BOM & sourcing](01-bom-sourcing.md) · **Next:** [3. Electrical & wiring](03-electrical.md)
