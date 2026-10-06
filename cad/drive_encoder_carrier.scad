// MRider — drive encoder magnet carrier
// =====================================
// A one-piece ring that slides onto the gearbox output hub and presents a plain
// cylinder carrying the encoder magnets. Three recessed grub screws hold it.
//
// THE RULE THIS FILE EXISTS TO OBEY
//   The Hall sensors ride 1-3 mm off the ring's outer surface, so every feature
//   below is a SUBTRACTION from that cylinder. Anything ADDED outside it is
//   swept through the sensor and its bracket once per revolution. An earlier
//   two-piece revision put the clamp screws in ears standing 9 mm proud of the
//   track: they swept Ø91 against a sensor face at Ø78, and would have taken the
//   sensor off on the first turn of the wheel.
//
// WHY ONE PIECE
//   The wheel comes off, so the ring can simply be slid on. A split ring has to
//   put its fastener somewhere, and on a wall this thin there is nowhere that is
//   both reachable by a hex key and inside the sensing cylinder.
//
// WHY THE BORE IS CLEAR AND NOT A PRESS FIT
//   The hub measures 63-64 mm and FDM holds a Ø65 bore to perhaps +-0.3 mm. A
//   press fit needs both numbers to +-0.1, so it is two significant figures out
//   of reach — and there are three hubs, not one. The bore is therefore
//   deliberately LOOSE and carries no load. The three grub screws take up
//   whatever slack exists and their points settle into spline valleys, which is
//   a form lock rather than friction. A hub 0.5 mm off nominal changes nothing
//   except how far the screws go in, so one print fits all three vehicles.
//
//   Nothing here needs a hard grip: the carrier transmits no torque, and the
//   8 mm slot between the gearbox face and the wheel captures it axially.
//
//   Build:       openscad -o carrier.stl drive_encoder_carrier.scad
//   Bore check:  set PART = "gauge"  — print this FIRST, see FITTING below
//
// Spec: docs/build/01-bom-sourcing.md  §1.2.3
// Figure: docs/images/drive-encoder-carrier.svg

/* [What to build] */
// "ring" = the carrier, ready to slice · "gauge" = thin bore-check ring
PART = "ring";              // [ring, gauge]
// Bore adjustment for the gauge ring only, mm. Print at -0.4, 0 and +0.4.
GAUGE_DELTA  = 0.0;

/* [Measured on the vehicle] */
// Spline crest diameter of the gearbox output hub, mm.
//
// Measured 2026-10-06 by paper strip: circumference 205 mm -> 205/pi = 65.25.
// That is a FLOOR, not the answer. The strip rides the crests and chords the
// valleys, so it measures an inscribed polygon, P = N*D*sin(pi/N), which is
// always short of pi*D. Recovering D needs the spline count N:
//
//     N      12      16      20      24      30
//     D    66.00   65.67   65.52   65.44   65.37
//
// N is not counted yet, so this takes the top of that band. Erring HIGH is the
// benign direction — a bore too large only means the screws go in further, a
// bore too small means the ring does not go on at all. Count the splines and
// this tightens to +-0.1.
HUB_D        = 66.0;
// How uncertain that measurement is, mm. The grub screws must cover it.
// Holds the uncounted splines AND the spread across three vehicles.
HUB_TOL      = 1.0;
// Axial room between the gearbox rotating face and the wheel, mm.
AXIAL_GAP    = 8.0;
// Smallest obstruction radius in that 8 mm slice, mm. NEGATIVE = NOT YET
// MEASURED. Set it and the assert below proves the ring and sensor fit.
RADIAL_ROOM  = -1;

/* [Carrier] */
WALL         = 7.0;         // radial wall thickness, mm
WIDTH        = 6.0;         // axial width, mm — leaves 1 mm each side in AXIAL_GAP
BORE_CLEAR   = 1.0;         // bore = HUB_D + this. CLEARANCE, not interference.

/* [Magnets] */
N_MAG        = 18;          // 9 pole pairs -> 36 counts/rev. Must divide by N_SET.
MAG_D        = 5.0;         // disc diameter, mm
MAG_T        = 2.0;         // disc thickness, mm
MAG_CLEAR    = -0.1;        // NEGATIVE = press fit. Magnets must not turn before the adhesive cures.

/* [Grub screws] */
N_SET        = 3;           // three points centre the ring; four can skew it
SET_PILOT_D  = 3.2;         // M3 clearance, bore to insert — the screw passes through
SET_SCREW_L  = 10.0;        // M3 x this, cup or cone point, no head
INSERT_D     = 4.6;         // M3 heat-set insert, largest OD. CHECK against the part bought.
INSERT_L     = 5.0;         // insert length, mm

/* [Index mark] */
MARK_W       = 1.6;         // groove width, mm
MARK_DEPTH   = 0.8;         // groove depth into one face, mm

/* [Sensors — for the clearance assert only] */
SENSOR_GAP   = 3.0;         // largest air gap the bracket will be set to, mm
SENSOR_T     = 4.0;         // sensor + PCB radial thickness, mm

/* [Hidden] */
$fn = 160;
EPS = 0.01;

// ---- derived -------------------------------------------------------------
BORE_D   = HUB_D + BORE_CLEAR;
OD       = BORE_D + 2 * WALL;
CIRC     = PI * OD;
PITCH    = CIRC / N_MAG;             // magnet pitch along the track
OFFSET   = PITCH / 2;                // quadrature offset: HALF a pole pitch,
                                     // because one electrical cycle spans TWO magnets
COUNTS   = 2 * N_MAG;                // with 4x quadrature decoding
SET_A0   = 180 / N_MAG;              // first screw, half a pitch off magnet 0
SLACK    = BORE_CLEAR + HUB_TOL;     // worst-case gap a screw has to close
REACH    = SET_SCREW_L - WALL;       // how far a flush screw passes the bore
NEED_R   = OD/2 + SENSOR_GAP + SENSOR_T;
MARK_R   = OD/2 - MAG_T - 1.0;       // index groove ends 1 mm short of the pocket
                                     // FLOOR, so it cannot reach the track by
                                     // construction — no assert can fail here

echo(str("bore Ø",        BORE_D, " mm  (hub + ", BORE_CLEAR, " CLEARANCE)"));
echo(str("SWEPT Ø",       OD,     " mm  <- nothing stands proud of this"));
echo(str("track circum.", CIRC,   " mm"));
echo(str("magnet pitch",  PITCH,  " mm"));
echo(str("SENSOR OFFSET", OFFSET, " mm  <- space the two Hall sensors by this"));
echo(str("counts / rev",  COUNTS));
echo(str("screw reach",   REACH,  " mm past the bore, vs ", SLACK, " mm of slack"));
echo(str("radial room needed ", NEED_R, " mm (ring + sensor)"));

assert(WIDTH < AXIAL_GAP,  "carrier is wider than the gap between gearbox and wheel");
assert(MAG_D < WIDTH,      "magnet will not fit inside the carrier width");
assert(MAG_T < WALL,       "magnet pocket would break through the back of the wall");
assert(PITCH > MAG_D + 2,  "magnets too close — reduce N_MAG or increase WALL");
assert(N_MAG % N_SET == 0, "N_MAG must divide by N_SET, or a screw lands on a magnet");
assert(PITCH/2 > (MAG_D + INSERT_D)/2 + 1,
       "insert hole would run into the magnets either side of it");
assert(INSERT_L + 1.5 <= WALL, "no pilot left between the insert and the bore");
assert(REACH >= SLACK, "grub screw cannot reach the hub across the worst-case slack");
assert(RADIAL_ROOM < 0 || RADIAL_ROOM >= NEED_R,
       "ring plus sensor will not clear the obstruction in the axial slice");
if (RADIAL_ROOM < 0)
    echo("NOTE: RADIAL_ROOM unmeasured — the clearance assert is not proving anything yet");

// ---- parts ---------------------------------------------------------------

// Pockets are cut radially from the outside, so the magnet face finishes flush
// with the track and the air gap is set by the bracket alone.
module magnet_pockets() {
    for (i = [0 : N_MAG - 1])
        rotate([0, 0, i * 360 / N_MAG])
            translate([OD/2 - MAG_T, 0, WIDTH/2])
                rotate([0, 90, 0])
                    cylinder(d = MAG_D + MAG_CLEAR, h = MAG_T + EPS);
}

// Each screw sits half a magnet pitch away from its neighbours, in the dead
// space between two magnets. A Hall LATCH holds its state until the opposite
// pole arrives, so a hole in that dead space is invisible to it.
//
// Insert is driven in from the OUTSIDE; the screw then passes through the pilot
// and lands in a spline valley. Flush at the surface it reaches REACH mm past
// the bore, which is what makes the fit tolerant.
module set_screw_holes() {
    for (k = [0 : N_SET - 1])
        rotate([0, 0, SET_A0 + k * 360 / N_SET]) {
            // pilot, bore to surface
            translate([BORE_D/2 - EPS, 0, WIDTH/2]) rotate([0, 90, 0])
                cylinder(d = SET_PILOT_D, h = WALL + 2*EPS);
            // insert seat, open to the surface
            translate([OD/2 - INSERT_L, 0, WIDTH/2]) rotate([0, 90, 0])
                cylinder(d = INSERT_D, h = INSERT_L + EPS);
        }
}

// A witness mark at magnet 0, so the pattern has a named starting point.
// Eighteen identical discs give you no way to say WHICH one went in backwards —
// not while placing them, and not when the hand-turn check in §1.2.3 shows one
// long gap and one short pulse.
//
// It was a Ø2 through-hole until the arithmetic was checked: centred at
// OD/2 - 1.0 with a radius of 1.0, it sat exactly TANGENT to the outer surface,
// leaving zero wall at the tangent point — a feather edge on the one surface
// that has to stay clean, pointed straight at the sensor. A groove in the face
// cannot reach the track at all: it stops 1 mm short of the pocket floor.
module index_mark() {
    translate([BORE_D/2 - EPS, -MARK_W/2, WIDTH - MARK_DEPTH])
        cube([MARK_R - BORE_D/2 + EPS, MARK_W, MARK_DEPTH + EPS]);
}

module carrier() {
    difference() {
        cylinder(d = OD, h = WIDTH);
        translate([0, 0, -EPS]) cylinder(d = BORE_D, h = WIDTH + 2*EPS);
        magnet_pockets();
        set_screw_holes();
        index_mark();
    }
}

// Thin ring, same bore, nothing else. Costs about 2 g and five minutes and
// answers the only question a drawing cannot: does it go on the hub at all.
module gauge() {
    GB = BORE_D + GAUGE_DELTA;
    difference() {
        cylinder(d = GB + 6, h = 3);
        translate([0, 0, -EPS]) cylinder(d = GB, h = 3 + 2*EPS);
    }
}

// ---- output --------------------------------------------------------------
if (PART == "gauge") gauge();
else                 carrier();

// ---- fitting -------------------------------------------------------------
// 1. Measure HUB_D with a paper strip around the spline crests: wrap, mark the
//    overlap, measure the length, divide by pi — then COUNT THE SPLINES and
//    divide by sin(pi/N)*N/pi, because the strip chords the valleys and reads
//    low. Do it on all three vehicles and enter the LARGEST.
// 2. Print PART = "gauge" three times, at GAUGE_DELTA = -0.4, 0 and +0.4.
// 3. The right one slides on by hand over the full 6 mm and rattles slightly.
//    It is SUPPOSED to rattle — the screws remove the rattle, not the bore.
//    If even +0.4 will not go on, HUB_D is wrong; re-measure before printing
//    20 g of carrier.
// 4. Add the winning delta to BORE_CLEAR, then print the carrier.
//
// ---- printing ------------------------------------------------------------
// PETG. 0.2 mm layers, 4 perimeters, 40 % infill. No supports. One ring per
// plate takes about 20 g.
//
// PRINT IT FLAT, ring axis vertical — straight out of PART = "ring". The only
// load this part ever sees is the three grub screws pushing inward, which is
// hoop tension in the ring, and printed flat that tension lies INSIDE the layer
// planes. On edge it would pull the layers apart and need supports as well.
//
// Lay it with the index groove FACING UP. A 0.8 mm recess in the top surface
// prints clean; on the bed it would come out as a bridge over nothing.
//
// The magnet pockets and the insert seats are horizontal holes in this
// orientation, so each bridges across its top and will come out slightly
// flattened. That suits a press fit, and the heat-set inserts melt their own
// seat regardless — but check the FIRST magnet pocket with a magnet before
// populating all eighteen.
//
// ---- assembly ------------------------------------------------------------
// Check the finished track with magnetic viewing film, or by walking a spare
// magnet round it and feeling the attract/repel alternate. Either shows a
// reversed disc directly; the hand-turn signal check only tells you that one
// exists, and then you count from the index groove to find it.
//
// MAGNET ORDER MATTERS. At this pitch every magnet can feel its neighbours and
// the alternating pattern pushes each one toward the wrong orientation. Press
// each magnet fully home, add adhesive, let it cure, then fit the next. Run the
// hand-turn check in §1.2.3 before the carrier goes near the vehicle.
//
// Then: heat-set the three inserts from the outside, slide the ring onto the
// hub, and run the grub screws down in rotation — a turn each, round and round,
// so the ring centres itself rather than being shoved against the hub. Blue
// threadlocker on the screws. Finally spin the wheel by hand and watch the air
// gap: it should not visibly change through a revolution.
//
// FASTENERS, per vehicle: 3 x M3 heat-set insert, 3 x M3 x 10 grub screw
// (cup or cone point — a cone point finds a spline valley on its own).
