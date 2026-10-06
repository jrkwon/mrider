// MRider — drive encoder magnet carrier
// ======================================
// A two-piece clamp that grips the gearbox output hub and presents a plain
// cylinder carrying the encoder magnets.
//
// WHY A CLAMP AND NOT A SPLINED SLEEVE
//   The carrier transmits no torque — it only has to ride along — so there is
//   nothing to gain from matching the hub's spline form, and matching it would
//   mean measuring tooth count, form and undercut and then printing to a
//   tolerance FDM does not hold. The clamp supplies grip; the spline crests
//   supply anti-slip. One diameter is all that has to be measured.
//
// WHY PRINTED
//   No load path, three identical copies from one file, and PETG is already in
//   the BOM for #14. PETG and not PLA: this sits beside a gearbox and a motor,
//   and PLA is soft by 60 °C.
//
//   Build:  openscad -o carrier.stl drive_encoder_carrier.scad
//   Preview a half:  set PART = "half"
//
// Spec: docs/build/01-bom-sourcing.md  §1.2.3
// Figure: docs/images/drive-encoder-carrier.svg

/* [What to build] */
// "print" = two halves laid out on the bed · "half" = one of them · "ring" = assembled, for checking fit only
PART = "print";             // [print, half, ring]

/* [Measured on the vehicle] */
// Spline crest diameter of the gearbox output hub, mm. THE ONE MEASUREMENT THIS NEEDS.
HUB_D        = 63.5;
// Axial room between the gearbox rotating face and the wheel, mm. The carrier must be narrower.
AXIAL_GAP    = 8.0;

/* [Carrier] */
WALL         = 4.0;         // radial wall thickness, mm
WIDTH        = 6.0;         // axial width, mm — leaves 1 mm each side inside AXIAL_GAP
BORE_CLEAR   = 0.4;         // added to HUB_D so the halves close onto the splines rather than bottoming out
SPLIT_GAP    = 1.2;         // gap at each split line, so clamping actually tightens
PRINT_GAP    = 5.0;         // clearance between the two halves when laid out to print

/* [Magnets] */
N_MAG        = 16;          // 8 pole pairs -> 32 counts/rev
MAG_D        = 5.0;         // disc diameter, mm
MAG_T        = 2.0;         // disc thickness, mm
MAG_CLEAR    = -0.1;        // NEGATIVE = press fit. Magnets must not be free to rotate before adhesive cures.

/* [Clamp screws] */
SCREW_D      = 3.2;         // M3 clearance
NUT_AF       = 5.5;         // M3 nut across flats
NUT_T        = 2.6;         // M3 nut thickness
HEAD_D       = 6.2;         // M3 socket-head clearance
HEAD_T       = 3.2;         // counterbore depth
EAR_W        = 9.0;         // flange width (radial), mm
EAR_L        = 7.0;         // flange length each side of the split, mm

/* [Hidden] */
$fn = 160;
EPS = 0.01;

// ---- derived -------------------------------------------------------------
BORE_D  = HUB_D + BORE_CLEAR;
OD      = BORE_D + 2 * WALL;
CIRC    = PI * OD;
PITCH   = CIRC / N_MAG;              // magnet pitch along the track
OFFSET  = PITCH / 2;                 // quadrature offset: HALF a pole pitch,
                                     // because one electrical cycle spans TWO magnets
COUNTS  = 2 * N_MAG;                 // with 4x quadrature decoding

echo(str("bore Ø",        BORE_D, " mm"));
echo(str("outside Ø",     OD,     " mm"));
echo(str("track circum.", CIRC,   " mm"));
echo(str("magnet pitch",  PITCH,  " mm"));
echo(str("SENSOR OFFSET", OFFSET, " mm  <- space the two Hall sensors by this"));
echo(str("counts / rev",  COUNTS));

assert(WIDTH < AXIAL_GAP,  "carrier is wider than the gap between gearbox and wheel");
assert(MAG_D < WIDTH,      "magnet will not fit inside the carrier width");
assert(MAG_T < WALL,       "magnet pocket would break through the back of the wall");
assert(PITCH > MAG_D + 2,  "magnets too close — reduce N_MAG or increase OD");
assert(EAR_L > HEAD_T + 2, "ear too short for the screw-head counterbore");
assert(EAR_L > NUT_T + 2,  "ear too short for the nut pocket");

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

// A witness notch beside magnet 0. The acceptance test is to turn the carrier
// by hand and watch one channel — a reversed magnet shows as one long gap and
// one short pulse, and this marks where in the revolution to look.
module index_notch() {
    // placed HALF a pitch round from magnet 0, so it cannot clash with a pocket
    rotate([0, 0, 180 / N_MAG])
        translate([OD/2 - 1.0, 0, -EPS])
            cylinder(d = 2.0, h = WIDTH + 2*EPS);
}

// One flange straddling a split line. Mirrored for the far side, so BOTH ears
// project outward — an earlier revision translated the second one inward, where
// it vanished into the ring and cut its nut pocket into the wall.
//
// The two halves stay IDENTICAL: one ear carries the nut, the other carries the
// screw-head counterbore. After the 180° assembly rotation every joint then has
// a head on one side and a nut on the other, from two copies of one print.
module ear_body(with_nut) {
    // reaches WALL deep into the ring so it merges with full wall thickness
    // rather than touching the curve tangentially at a single line
    translate([0, OD/2 - WALL, 0])
        difference() {
            translate([-EAR_L, 0, 0])
                cube([EAR_L * 2, EAR_W + WALL, WIDTH]);

            // clamp screw, through both halves, parallel to the split line
            translate([0, WALL + EAR_W/2, WIDTH/2]) rotate([0, 90, 0])
                translate([0, 0, -EAR_L - EPS])
                    cylinder(d = SCREW_D, h = EAR_L * 2 + 2*EPS);

            if (with_nut)
                // captive hex pocket, open to the outer face
                translate([EAR_L - NUT_T, WALL + EAR_W/2, WIDTH/2]) rotate([0, 90, 0])
                    rotate([0, 0, 30])
                        cylinder(d = NUT_AF / cos(30), h = NUT_T + EPS, $fn = 6);
            else
                // counterbore so the screw head finishes below the surface
                translate([EAR_L - HEAD_T, WALL + EAR_W/2, WIDTH/2]) rotate([0, 90, 0])
                    cylinder(d = HEAD_D, h = HEAD_T + EPS);
        }
}

module ear(sign, with_nut) {
    if (sign > 0) ear_body(with_nut);
    else          mirror([0, 1, 0]) ear_body(with_nut);
}

module full_ring() {
    difference() {
        union() {
            cylinder(d = OD, h = WIDTH);
            ear( 1, true);    // nut side
            ear(-1, false);   // screw-head side
        }
        translate([0, 0, -EPS]) cylinder(d = BORE_D, h = WIDTH + 2*EPS);
        magnet_pockets();
        index_notch();
    }
}

// One half: everything on +X, minus half the split gap on each face.
module carrier_half() {
    intersection() {
        full_ring();
        translate([SPLIT_GAP/2, -OD, -OD]) cube([OD * 2, OD * 2, OD * 2]);
    }
}

// ---- output --------------------------------------------------------------
// Both halves lie FLAT, ring axis vertical. See the printing note below for why
// that is the orientation and not a convenience.
if (PART == "ring") {
    // assembled preview — for checking fit, not for printing
    carrier_half();
    rotate([0, 0, 180]) carrier_half();
} else if (PART == "half") {
    carrier_half();
} else {                                          // "print" — two halves, laid out
    carrier_half();
    translate([-PRINT_GAP, 0, 0]) rotate([0, 0, 180]) carrier_half();
}

// ---- printing ------------------------------------------------------------
// PETG. 0.2 mm layers, 4 perimeters, 40 % infill. No supports.
//
// PRINT IT FLAT, exactly as it comes out of PART = "print". The clamp screws
// pull along X, so with the part flat that load sits INSIDE the layer planes.
// Standing a half on its split face would put the same load NORMAL to the
// layers — the one direction FDM is weak in — and leave a 4 x 6 mm footprint
// holding up a 36 mm tall part. (An earlier revision of this file recommended
// exactly that. It was wrong on both counts.)
//
// The magnet pockets are horizontal holes in this orientation, so each one
// bridges across its top. Over a 5 mm span that is a short bridge and the top
// will come out slightly flattened — which suits a press fit, but check the
// first pocket with a magnet before populating all sixteen.
//
// ASSEMBLY ORDER MATTERS. At this pitch every magnet can feel its neighbours,
// and the alternating pattern pushes each one toward the orientation that is
// wrong. Press each magnet fully home, add adhesive, and let it cure before
// fitting the next. Then run the hand-turn check in §1.2.3 before the carrier
// goes anywhere near the vehicle.
//
// FASTENERS: 2 x M3 socket cap, about 16 mm, and 2 x M3 nut. Both halves are the
// same print — one ear has the nut pocket and the other the head counterbore, so
// two copies rotated 180° give every joint a head and a nut.
