// keyhop "proto" enclosure: holds an Olimex ESP32-S3-DevKit-LiPo and a Pi Hut
// USB-A breakout (horizontal), joined by female-female jumper wires. No soldering.
//
// Render one part with:   openscad -D 'part="base"' -o base.stl keyhop-proto-case.scad
// part = "base" | "lid" | "lid_print" (lid flipped for printing)
//      | "assembly" | "exploded" | "collisions"
//
// Layout (top view, X right, Y up; origin = inside corner of the base):
//
//    +------------------------------------------------------+
//    | [USB-C x2]  Olimex 56 x 28, buttons/LEDs near top edge|antenna
//    +------------------------------------------------------+
//    |                     (lid fin between the boards)      |
//    |                                   [breakout] [USB-A]> |
//    +------------------------------------------------------+
//
// Both boards sit right side up with their header pins pointing down. The
// jumpers plug onto those pins and fold into the deep space under the boards.
//
// Dimensions marked "photo" were estimated from photos with a ruler
// (2026-11-20, about +/-1 mm). Check them on the real parts before printing.

part = "exploded";
$fn = 48;

// ---- Boards ----------------------------------------------------------------
ol_l = 56;  ol_w = 28;  pcb_t = 1.6;  // Olimex board (datasheet)
ant  = 6.3;                           // antenna overhang past the board end (photo)
usbc_over = 1.0;                      // USB-C ports overhang the board edge (photo)
usbc_y = [9.6, 21.4];                 // port centres from the Olimex bottom edge (photo)
usbc_w = 9.0;  usbc_h = 3.3;          // USB-C receptacle size
mod_y = [5, 23];  mod_h = 3.1;        // WROOM module span across the board, height
top_h = 6.5;                          // tallest Olimex top part (white connectors) (photo)
hdr_t = 2.5;                          // header plastic under the board
win = [14, 35];                       // LED/button strip, X from USB-C edge (photo)

br_l = 17.3; br_w = 17.2;             // breakout board, X along socket axis (photo)
br_sock_over = 0.8;                   // socket front past the breakout edge (photo)
sock_w = 14.1; sock_h = 7.0; sock_l = 14.0;  // USB-A shell (photo / standard)

// ---- Case ------------------------------------------------------------------
gap     = 0.5;    // clearance around boards
wall    = 3.0;    // thick enough that the snap lap halves stay >= 1 mm after the grooves
floor_t = 1.6;
top_t   = 1.6;
under   = 21.0;   // floor to board underside: header 2.5 + jumper housing ~14 + wire bend
above   = 7.6;    // board top to underside of lid (USB-A shell ~7 mm is the tallest)
r_out   = 2.5;
lap     = 3.0;
clear   = 0.1;
lap_t   = (wall - clear) / 2;

// Board positions inside the case
br_y0 = gap;                         br_y1 = br_y0 + br_w;
fin_t = 1.4;  fin_y = br_y1 + 0.8;   // lid fin keeps the boards apart
ol_y0 = fin_y + fin_t + 0.8;         ol_y1 = ol_y0 + ol_w;
ol_x0 = usbc_over + 0.2;             ol_x1 = ol_x0 + ol_l;
L = ol_x1 + ant + gap;               // inside length
W = ol_y1 + gap;                     // inside width
br_x1 = L - br_sock_over;            br_x0 = br_x1 - br_l;

pcb_z0  = floor_t + under;
pcb_top = pcb_z0 + pcb_t;
ceil_z  = pcb_top + above;
total_h = ceil_z + top_t;
split_z = pcb_top;

x0 = -wall;  x1 = L + wall;
y0 = -wall;  y1 = W + wall;
bump_x = [L * 0.25, L * 0.75];

// Lid posts that press the boards down: [x, y, diameter, height above board top]
posts = [
    [ol_x0 + 3.5, ol_y0 + usbc_y[1], 3.0, usbc_h + 0.2],  // on the upper USB-C shell
    [ol_x0 + 3.5, ol_y0 + usbc_y[0], 3.0, usbc_h + 0.2],  // on the lower USB-C shell
    [ol_x1 - 6,   ol_y0 + 14,        4.0, mod_h + 0.2],   // on the ESP32 module can
    [br_x1 - 6,   br_y0 + br_w / 2,  4.0, sock_h + 0.2],  // on the USB-A shell
    [br_x0 + 1.4, br_y0 + 1.4,       2.4, 0.2],           // breakout corners at the pin end
    [br_x0 + 1.4, br_y1 - 1.4,       2.4, 0.2],
];

// ---- Helpers -----------------------------------------------------------------
module rbox(ax, ay, bx, by, z0, z1, r) {
    r2 = max(r, 0.01);
    hull() for (x = [ax + r2, bx - r2], y = [ay + r2, by - r2])
        translate([x, y, z0]) cylinder(r = r2, h = z1 - z0);
}
module yz_slot(xa, xb, yc, zc, w, h, r) {
    translate([xa, 0, 0]) rotate([0, 90, 0]) linear_extrude(xb - xa)
        translate([-zc, yc]) offset(r) square([h - 2*r, w - 2*r], center = true);
}
module outer_shell(z0, z1) rbox(x0, y0, x1, y1, z0, z1, r_out);
module inner_space(z0, z1, grow = 0)
    rbox(-grow, -grow, L + grow, W + grow, z0, z1, max(r_out - wall + grow, 0.3));

module openings() {
    // USB-C: one slot covering both ports, sized for a cable plug's overmold
    yz_slot(x0 - 1, 0.01, ol_y0 + (usbc_y[0] + usbc_y[1]) / 2, pcb_top + usbc_h / 2,
            usbc_y[1] - usbc_y[0] + 12.6, 7.6, 1.6);
    // USB-A: around the socket shell, plus a shallow outer pocket for the plug body
    yz_slot(L - 0.01, x1 + 1, br_y0 + br_w / 2, pcb_top + sock_h / 2, sock_w + 1.5, sock_h + 1.2, 0.8);
    yz_slot(x1 - 1.4, x1 + 1, br_y0 + br_w / 2, pcb_top + sock_h / 2, 18.5, 10.0, 1.5);
}

// ---- Base ------------------------------------------------------------------
module base() {
    difference() {
        union() {
            outer_shell(0, split_z);
            difference() {                                   // inner half of the wall: snap lap
                inner_space(split_z - 0.01, split_z + lap, lap_t);
                inner_space(split_z - 0.02, split_z + lap + 1);
            }
            for (x = bump_x, s = [0, 1])                     // snap bumps, both long sides
                translate([x, s ? W + lap_t : -lap_t, split_z + lap / 2])
                    rotate([0, 90, 0]) cylinder(r = 0.35, h = 10, center = true);
        }
        inner_space(floor_t, split_z + lap + 1);
        openings();
    }
    // Olimex rests on two blocks under its short ends, between the header rows
    translate([ol_x0, ol_y0 + 4, floor_t - 0.01]) cube([2.2, ol_w - 8, under + 0.01]);
    translate([ol_x1 - 2.2, ol_y0 + 4, floor_t - 0.01]) cube([2.2, ol_w - 8, under + 0.01]);
    // ...and a lip past the antenna end stops it sliding away from the USB-C slot
    translate([ol_x1 + gap, ol_y0 + mod_y[0], floor_t - 0.01]) cube([1.2, mod_y[1] - mod_y[0], under + pcb_t - 0.2]);
    // Breakout rests on strips under its two side edges, with stops at the pin end
    for (y = [br_y0 - gap - 0.01, br_y1 - 1.4]) {
        translate([br_x0, y, floor_t - 0.01]) cube([br_l, 1.4 + (y < br_y0 ? gap : 0) + 0.01, under + 0.01]);
        translate([br_x0 - 1.4 - gap, y, floor_t - 0.01]) cube([1.4, 1.4 + (y < br_y0 ? gap : 0) + 0.01, under + pcb_t + 1.0]);
    }
}

// ---- Lid -------------------------------------------------------------------
module lid() {
    difference() {
        union() {
            outer_shell(split_z + lap, total_h);
            difference() {                                   // outer half of the wall
                outer_shell(split_z, split_z + lap + 0.01);
                inner_space(split_z - 1, split_z + lap + 0.02, lap_t + clear);
            }
            for (p = posts) translate([p[0], p[1], pcb_top + p[3]]) cylinder(d = p[2], h = ceil_z - pcb_top - p[3] + 0.01);
            // fin between the boards: keeps them apart sideways
            translate([br_x0 - 4, fin_y, pcb_z0 - 1.0]) cube([L - br_x0 + 4, fin_t, ceil_z - pcb_z0 + 1.01]);
            translate([8, fin_y, pcb_top + 0.2]) cube([br_x0 - 4 - 8 + 0.01, fin_t, ceil_z - pcb_top - 0.19]);
        }
        difference() {                                       // hollow interior
            inner_space(split_z - 1, ceil_z);
            for (p = posts) translate([p[0], p[1], pcb_top + p[3]]) cylinder(d = p[2], h = 100);
            translate([br_x0 - 4, fin_y, 0]) cube([L - br_x0 + 4, fin_t, 100]);
            translate([8, fin_y, pcb_top + 0.2]) cube([br_x0 - 4 - 8, fin_t, 100]);
        }
        for (x = bump_x, s = [0, 1])                         // grooves for the snap bumps
            translate([x, s ? W + lap_t : -lap_t, split_z + lap / 2])
                rotate([0, 90, 0]) cylinder(r = 0.45, h = 10.6, center = true);
        // window over the Olimex LEDs and buttons (status blinks, RESET/BOOT with a paperclip)
        translate([ol_x0 + win[0], ol_y1 - 7.5, ceil_z - 1]) rbox(0, 0, win[1] - win[0], 7.0, 0, 10, 1.0);
        // fingernail notch (front long side)
        translate([L / 2 - 5, y0 - 1, split_z - 0.01]) cube([10, wall - lap_t + 1, 1.0]);
        openings();
        translate([0, 0, total_h - 0.5]) linear_extrude(1) {
            translate([L / 2 - 6, br_y0 + br_w / 2]) text("keyhop", size = 7, halign = "center", valign = "center",
                                                         font = "Liberation Sans:style=Bold");
            translate([ol_x0 + win[1] + 1.5, ol_y1 - 4]) text("LED", size = 2.6, halign = "left", valign = "center");
        }
    }
}

// ---- Stand-ins for the boards (previews and collision checks) ---------------
module proxies() {
    color("firebrick") translate([ol_x0, ol_y0, pcb_z0]) cube([ol_l, ol_w, pcb_t]);
    color("darkslategray") translate([br_x0, br_y0, pcb_z0]) cube([br_l, br_w, pcb_t]);
    color("silver") {
        for (y = usbc_y) translate([ol_x0 - usbc_over, ol_y0 + y - usbc_w / 2, pcb_top]) cube([7.4, usbc_w, usbc_h]);
        translate([ol_x1 - 18.5, ol_y0 + mod_y[0], pcb_top]) cube([18.5 + ant, mod_y[1] - mod_y[0], mod_h]);
        translate([ol_x0 + 22, ol_y0 + 5, pcb_top]) cube([6, 6, top_h]);   // tallest white connector (approx.)
        translate([br_x1 + br_sock_over - sock_l, br_y0 + (br_w - sock_w) / 2, pcb_top]) cube([sock_l, sock_w, sock_h]);
    }
    color("black") {
        // Olimex header rows under both long edges, and the jumper housings on four pins
        for (y = [0, ol_w - 2.54]) translate([ol_x0, ol_y0 + y, pcb_z0 - hdr_t]) cube([ol_l, 2.54, hdr_t]);
        for (x = [20, 23, 26]) translate([ol_x0 + x, ol_y0, pcb_z0 - hdr_t - 14]) cube([2.54, 2.54, 14]);
        translate([ol_x0 + 30, ol_y1 - 2.54, pcb_z0 - hdr_t - 14]) cube([2.54, 2.54, 14]);
        // breakout header and housings (pin row ~2.5 mm in from the pin-end edge)
        translate([br_x0 + 1.25, br_y0 + br_w / 2 - 5.08, pcb_z0 - hdr_t - 14]) cube([2.54, 10.16, hdr_t + 14]);
    }
}

if (part == "base") base();
else if (part == "lid") lid();
else if (part == "lid_print") translate([0, 0, total_h]) rotate([180, 0, 0]) lid();
else if (part == "assembly") { color("dimgray") base(); proxies(); color("gray", 0.35) lid(); }
else if (part == "exploded") { color("dimgray") base(); proxies(); translate([0, 0, 30]) color("gray") lid(); }
else if (part == "collisions") {   // should render as nothing
    intersection() { union() { base(); lid(); } proxies(); }
    intersection() { base(); lid(); }
}
