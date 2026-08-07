# 2. Vehicle Prep & Mechanical

**Goal:** prepare the chassis and mount the steering actuator and encoders mechanically.

Disassemble the necessary trim, identify the steering column and drive-motor shaft,
and fit the steering gearmotor, the absolute steering-angle sensor, and the drive-shaft
encoder. Keep the modifications minimally invasive and reversible.

- **Prerequisites:** Section 1 complete; chassis selected.
- **Specification:** [design/vehicle.md](../design/vehicle.md), [design/dbw.md](../design/dbw.md)
- **Expected outcome:** actuator and sensors mechanically mounted; stock steering still
  reassemblable.

!!! warning "Draft — not yet validated on hardware"

    No MRider vehicle has been disassembled yet. **There are no teardown photos, no bracket
    dimensions, and no torque figures in this page, because none have been measured.** Every
    such value is marked *(measure during bring-up)*. This page gives you the procedure and
    the record sheets; you produce the numbers.

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
| Battery is genuinely 24 V | The whole power tree assumes it | *(measure during bring-up)* |
| Two independent rear drive motors | [Throttle path](../design/dbw.md#7-throttle-path) parallels them onto Sabertooth M2 | *(measure during bring-up)* |
| Steering column is accessible without cutting | Reversibility principle | *(measure during bring-up)* |
| Column has a stock steering motor, or is hand-turned only | Determines whether the steering tap intercepts an existing motor or adds one | *(measure during bring-up)* |
| Paralleled drive-motor **stall current** vs. 32 A/channel | Sabertooth rating limit ([dbw.md §7](../design/dbw.md#7-throttle-path)) | *(measure during bring-up)* |
| Front wheel travel is ≈ ±22.5° | The pinned steering range ([dbw.md §12](../design/dbw.md#12-numeric-interface-contract)) | *(measure during bring-up)* |

!!! danger "Disconnect the battery before disassembly"

    The traction pack is live at the motor terminals even with the vehicle "off" on many
    ride-on models. Pull the pack or the main fuse first.

## 2.2 Teardown

Work in this order and bag-and-tag fasteners by panel.

1. **Remove the seat and body trim** covering the rear motor bay and the steering column.
   Ride-on bodies are typically self-tapping screws into plastic bosses — they strip easily,
   so go slow and do not over-torque on reassembly.
2. **Identify and photograph the stock harness.** You need three interception points, and
   you want to see them before anything is cut or unplugged:
    - the **throttle** leads to the rear motors,
    - the **steering** leads (if a stock steering motor exists),
    - the **24 V pack** output.
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
  [dbw.md §6](../design/dbw.md#6-adr-angle-sensor-technology-potentiometer-vs-as5600-class-magnetic-encoder).

!!! note "The pot's dead-band must sit outside the working range"

    A single-turn pot has a mechanical/electrical dead zone at the ends of its sweep. Mount
    it so that the **±22.5° road-wheel working range lands near the middle** of the pot's
    travel, not near either end. You verify this during zeroing in
    [step 6](06-bench-test.md), but you have to get the mounting clocking approximately right
    now — rotating a bonded coupler later is unpleasant.

## 2.4 Mount the steering gearmotor

The gearmotor drives the column through the existing steering linkage and is driven by
**Sabertooth channel 1 (M1)**. The Nano commands it as a *signed effort* — the output of the
position loop — never as an angle
([dbw.md §2.3](../design/dbw.md#23-why-the-sabertooth-drives-the-steering-motor-as-an-effort-command)).

1. **Decide the coupling point.** Either directly on the column (simplest, needs a coupler
   sized to the column diameter) or on the tie-rod arm (more mechanical advantage, more
   bracket work). Whichever you pick, the sensor and the motor must see a **rigid,
   backlash-free** path to the road wheels or the position loop will hunt.
2. **Fabricate or print the motor bracket.** It must resist the *stall* torque of the motor,
   not its rated torque — a position loop against a limit will apply full effort until the
   Nano's stall detector clamps it. Reuse the mrover 3D-print approach
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
4. **Strain-relieve the wiring.** For a pot, feed it from the Nano's *regulated* rail so the
   reading is ratiometric and supply drift cancels
   ([dbw.md §6 consequences](../design/dbw.md#6-adr-angle-sensor-technology-potentiometer-vs-as5600-class-magnetic-encoder)).

The gearmotor's own incremental encoder, if it has one, mounts with the motor and is
auxiliary — it provides velocity and stall detection only.

## 2.6 Mount the drive-shaft encoder

Follow the mrover shaft-adapter method: a **3.15 mm → 5 mm adapter** onto the drive-motor
shaft, with the encoder body bracketed to the motor mount
([ADR C](../design/dbw.md#8-adr-c-drive-distance-encoding), `vehicle_setup.md:70-72`).

- Confirm the adapter matches **your** measured shaft diameter — the 3.15 mm figure is
  mrover's motor, not necessarily yours.
- Concentricity matters more than it looks: a wobbling encoder disc produces periodic tick
  errors that alias into odometry.
- Route the encoder cable away from the motor leads. Encoder lines next to a PWM'd 24 V
  motor pick up noise that reads as phantom ticks.

!!! note "You are instrumenting one motor of a paralleled pair"

    This is a known, documented limitation, not a mistake. Motor-shaft measurement inherits
    gearbox backlash, wheel slip, and differential wheel speed in turns. The EKF fuses it
    with the IMU to bound drift, and step 6's roll-out calibration bounds the scale error.
    See [ADR C consequences](../design/dbw.md#8-adr-c-drive-distance-encoding) — this is
    worth understanding now, because it is why nobody should expect raw wheel odometry to
    close a loop.

## 2.7 Mount the sensor mast and compute

Camera and LiDAR mounting geometry comes from
[sensors.md §5](../design/sensors.md#5-mounting-mast-concept). Two mechanical constraints
matter at this stage:

- **Rigidity.** Extrinsics calibrated in step 6 are only valid while the mast holds its
  geometry. A mast that flexes under acceleration invalidates the camera↔LiDAR projection.
- **Reachability.** You will re-seat USB connectors more often than you expect during
  bring-up. Do not bury them.

The laptop rides on its own battery and is not wired into the 24 V system in v1
([safety.md §5](../design/safety.md#5-power-rail-isolation-and-brownout-protection)) —
mechanically, it just needs a secure, ventilated place to sit.

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
