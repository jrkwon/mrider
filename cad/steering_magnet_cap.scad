// MRider — steering angle magnet cap
// ==================================
// A cap that drops over the kingpin bolt head and presents a diametrically
// magnetised magnet on the steering axis for an AS5600.
//
// WHY THIS PART EXISTS, AND WHY IT IS A CAP
//   ADR B wants the absolute angle measured LOAD-SIDE, so that gearbox backlash
//   and linkage slop show up as measured error instead of invisible bias. This
//   vehicle refused an end-mounted magnet three times — no motor rear stub, no
//   free drive output, no free steering output, every axis occupied. The kingpin
//   bolt is the first one that is free, and its head TURNS WITH THE ROAD WHEEL
//   (mark test, 2026-10-16), with about 100 mm of clear air above it.
//
// WHY IT REGISTERS ON THE HEX AND NOT ON THE BOSS
//   An AS5600 wants its magnet concentric with the die to about +-0.25 mm. A hex
//   socket locates on six formed flats and centres itself; the boss below may or
//   may not even rotate. Nothing is drilled, nothing is cut, and pulling the cap
//   off returns the vehicle to stock — which 02-mechanical 2.8 asks for.
//
//   Build:  openscad -o cap.stl steering_magnet_cap.scad
//
// Spec: docs/order-log.md #13 · Sensor: docs/order-log.md #5

/* [Measured on the vehicle] */
// Kingpin bolt head, across the flats, mm. THE ONE MEASUREMENT THIS NEEDS.
// 13.3 measured 2026-10-16 — an M8 head is 13.0 nominal, so this is M8 plus paint.
HEAD_AF      = 13.3;
// How deep the socket has to be: from the WASHER'S TOP FACE to the very top of
// everything above it — the hex head plus the small raised pip on top of it.
//
// A caliper across the whole stack read 10.0 mm on 2026-10-16, but that span
// INCLUDED THE WASHER, so it over-states this number by the washer's thickness.
// 8.0 is that reading less a nominal 2 mm washer and is a placeholder. Measure
// from the washer's top face and set it:
//   too shallow -> the cap stops on the pip and rocks on the hex
//   too deep    -> it pushes past the washer onto whatever is underneath, which
//                  may not be turning with the wheel
STACK_H      = 8.0;
// Hex height alone, mm — only used to check there is enough flat to locate on.
// 5.3 is the ISO 4017 figure for M8. Confirm with the same caliper pass.
HEAD_H       = 5.3;
// Clear air above the head, mm. 100 measured — the sensor bracket is unconstrained.
HEAD_CLEAR   = 100.0;

/* [Magnet — DIAMETRICALLY magnetised, not axial] */
MAG_D        = 4.04;        // disc diameter, mm — MEASURED 2026-10-26
MAG_T        = 1.63;        // disc thickness, mm — MEASURED 2026-10-26
//
// The AS5600 kit shipped a Ø4 disc, not the Ø6 this file first assumed, and it is
// DIAMETRIC: the poles are on the rim, checked 2026-10-26. That was the one failure
// that would have presented as a dead sensor rather than as a wrong part.
//
// A Ø4 is small for an AS5600 — AMS's reference is Ø6 x 2.5 — so the field is weaker,
// the usable air gap is narrower, and the +/-0.25 mm concentricity matters MORE, not
// less. Do not treat the smaller magnet as a smaller problem.
//
// Acceptance is a register read, not a guess: with the magnet fitted, read AGC (0x1A).
// At 3.3 V it runs 0-128 and MID-SCALE IS CORRECT -- railed low means too strong or too
// close, railed high means too weak or too far. Check MD/ML/MH at the same time. Tune
// the gap until AGC sits mid-range, then RECORD THE GAP: that is the number the other
// two vehicles are built to.
MAG_CLEAR    = 0.1;         // POSITIVE = slip fit, bonded with thin CA
//
// The carrier uses -0.1 and presses its magnets in. This part does not, and the
// reason is the disc: 4.04 x 1.63 is both small and THIN, and neodymium is brittle.
// Pressing a 1.63 mm disc into an interference pocket is how you chip the one
// magnet the kit gave you. A 0.1 mm slip fit leaves 0.05 mm of radial float, and
// the AS5600's concentricity budget is +/-0.25 -- five times that. Bond it with the
// same thin CA as the carrier, degreased with IPA first.
MAG_BACK     = 1.2;         // floor under the magnet, mm

/* [Cap] */
WALL         = 3.0;         // radial wall around the hex, mm
SOCKET_CLEAR = 0.3;         // added across flats so it slips on by hand
SEAT_EXTRA   = 1.0;         // socket deeper than the head, so it seats on the head

/* [Hidden] */
$fn = 120;
EPS = 0.01;

// ---- derived -------------------------------------------------------------
SOCK_AF = HEAD_AF + SOCKET_CLEAR;
SOCK_AC = SOCK_AF / cos(30);          // across corners
OD      = SOCK_AC + 2 * WALL;
SOCK_H  = STACK_H + SEAT_EXTRA;
TOTAL_H = SOCK_H + MAG_BACK + MAG_T;

echo(str("socket across flats ", SOCK_AF, " mm"));
echo(str("cap outside Ø",        OD,      " mm"));
echo(str("cap height",           TOTAL_H, " mm"));
echo(str("magnet face sits ",    TOTAL_H - STACK_H, " mm above the top of the bolt"));
echo(str("hex engaged",          HEAD_H, " mm of the ", SOCK_H, " mm socket"));
echo(str("wall at the flats",    (OD - SOCK_AF)/2, " mm"));

assert(MAG_D < SOCK_AF,
       "magnet pocket is wider than the socket — its floor would have nothing to sit on");
assert(MAG_BACK >= 0.8, "floor under the magnet too thin to print");
assert(TOTAL_H < HEAD_CLEAR, "cap is taller than the room above the bolt head");
assert(SOCKET_CLEAR > 0, "socket must slip on by hand — this part is removed to return the vehicle to stock");
assert(HEAD_H >= 4.0, "too little hex for the cap to locate on without rocking");
assert(STACK_H >= HEAD_H, "the stack cannot be shorter than the hex inside it");

// ---- parts ---------------------------------------------------------------
module hex(af, h) { cylinder(d = af / cos(30), h = h, $fn = 6); }

module cap() {
    difference() {
        cylinder(d = OD, h = TOTAL_H);
        // hex socket, open at the bottom
        translate([0, 0, -EPS]) hex(SOCK_AF, SOCK_H + EPS);
        // magnet pocket, open at the top
        translate([0, 0, TOTAL_H - MAG_T])
            cylinder(d = MAG_D + MAG_CLEAR, h = MAG_T + EPS);
    }
}
cap();

// ---- printing ------------------------------------------------------------
// PETG, 0.2 mm layers, 4 perimeters, 40 % infill, no supports.
//
// PRINT IT MAGNET-FACE DOWN, socket opening upward. The floor under the magnet
// then bridges only the 6 mm pocket instead of the 13.6 mm socket, and the
// magnet face comes off the bed flat, which is the face the sensor reads across.
//
// ---- fitting -------------------------------------------------------------
// 1. The bolt SPINS ON THE SPOT rather than orbiting — confirmed 2026-10-16, so
//    it sits on the steering axis and this cap is viable at all.
// 2. Measure STACK_H FROM THE WASHER'S TOP FACE. The 10.0 mm caliper pass
//    spanned the washer as well, and a socket cut to 10 would push past the
//    washer onto whatever is under it.
// 3. Press the cap on by hand. It should need a push and come off with a pull.
//    No adhesive on the BOLT, ever — the cap comes off to return the vehicle to
//    stock. If it ever works loose, glue the magnet, not the cap.
// 4. Press the magnet in flush. A diametric magnet has its poles across the
//    disc, so which way round it goes does not matter: the AS5600's zero is
//    programmable and firmware carries the offset anyway.
// 5. The sensor faces the magnet across 0.5-3 mm, die centred on the axis,
//    on a bracket fixed to the CHASSIS.
