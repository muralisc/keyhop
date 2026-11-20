// keyhop "proto" enclosure: holds an Olimex ESP32-S3-DevKit-LiPo and a Pi Hut
// USB-A breakout (horizontal), joined by female-female jumper wires. No soldering.
//
// Render one part with:   openscad -D 'part="base"' -o base.stl keyhop-proto-case.scad
// part = "base" | "lid" | "lid_print" (lid flipped for printing)
//      | "assembly" | "exploded" | "inside" | "collisions"
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
sock_into = 1.5;                      // socket pushed this far into the end wall, so a plug reaches it
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
br_x1 = L + sock_into - br_sock_over; br_x0 = br_x1 - br_l;

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
    // (no partial-depth outer pocket: it left sub-0.5 mm slivers where it met the snap lap)
    yz_slot(L - 0.01, x1 + 1, br_y0 + br_w / 2, pcb_top + sock_h / 2, sock_w + 1.5, sock_h + 1.2, 0.8);
    // shallow recess inside the end wall for the breakout's board edge (below the split, base only)
    translate([L - 0.01, br_y0 - 0.5, pcb_z0 - 0.3]) cube([br_x1 - L + 0.3 + 0.01, br_w + 1.0, pcb_t + 0.3]);
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
    olimex_model();
    breakout_model();
}

// Olimex ESP32-S3-DevKit-LiPo at roughly "20% realism" for the pictures: the parts
// you'd recognise, placed from the photos. It stays inside the space the case was
// designed around (USB-C shells, module, tallest connector top_h, header below).
module olimex_model() {
    X = ol_x0;  Y = ol_y0;
    pitch = 2.54;
    pin_xs = [for (k = [0:21]) X + 1.27 + k * pitch];
    rows = [Y + 1.27, Y + ol_w - 1.27];
    // red PCB with rounded corners and 44 header holes along the long edges
    color([0.72, 0.10, 0.10]) difference() {
        translate([X, Y, pcb_z0]) rbox(0, 0, ol_l, ol_w, 0, pcb_t, 1.0);
        for (x = pin_xs, y = rows) translate([x, y, pcb_z0 - 1]) cylinder(d = 1.0, h = 5);
    }
    // header: pin stubs above the board, black plastic and long pins below
    color("gold") for (x = pin_xs, y = rows) {
        translate([x - 0.32, y - 0.32, pcb_z0 - hdr_t - 6]) cube([0.64, 0.64, hdr_t + 6 + pcb_t + 1.5]);
        translate([x, y, pcb_top - 0.02]) difference() { cylinder(d = 1.7, h = 0.05); translate([0, 0, -1]) cylinder(d = 1.0, h = 2); }
    }
    color("black") for (y = rows) translate([X, y - 1.27, pcb_z0 - hdr_t]) cube([ol_l, pitch, hdr_t]);
    // two USB-C receptacles at the left edge: rounded metal shell, open at the front, with a tongue
    for (yc = usbc_y) {
        x0 = X - usbc_over;
        color([0.78, 0.79, 0.80]) difference() {
            yz_slot(x0, x0 + 7.4, Y + yc, pcb_top + usbc_h / 2, 8.94, 3.26, 1.6);
            yz_slot(x0 - 1, x0 + 6.6, Y + yc, pcb_top + usbc_h / 2, 8.34, 2.66, 1.3);
        }
        color([0.1, 0.1, 0.1]) translate([x0 + 1.2, Y + yc - 3.3, pcb_top + usbc_h / 2 - 0.35]) cube([5.5, 6.6, 0.7]);
    }
    // ESP32-S3-WROOM-1: module PCB (antenna end overhangs the board) with a metal can
    mx0 = ol_x1 - 18.5;  my0 = Y + mod_y[0];  mw = mod_y[1] - mod_y[0];
    color([0.12, 0.12, 0.14]) translate([mx0, my0, pcb_top]) cube([18.5 + ant, mw, 0.8]);
    color([0.80, 0.80, 0.82]) translate([mx0 + 0.6, my0 + 0.6, pcb_top + 0.8]) cube([17.2, mw - 1.2, mod_h - 0.8]);
    color([0.25, 0.25, 0.27]) translate([mx0 + 9, my0 + mw / 2, pcb_top + mod_h]) linear_extrude(0.05)
        rotate(90) text("ESP32-S3-WROOM-1", size = 1.25, halign = "center", valign = "center");
    // meandering antenna trace on the overhang
    color("gold") translate([0, 0, pcb_top + 0.8]) linear_extrude(0.05) {
        ax = ol_x1 + 0.6;
        for (i = [0:4]) translate([ax, my0 + 2 + i * 3.2]) square([ant - 1.4, 0.5]);
        for (i = [0:3]) translate([i % 2 == 0 ? ax + ant - 1.9 : ax, my0 + 2 + i * 3.2]) square([0.5, 3.7]);
    }
    // RESET and BOOT buttons, two small LEDs, near the top edge (under the lid window)
    for (bx = [17.6, 31.3]) {
        color([0.85, 0.85, 0.86]) translate([X + bx - 1.75, Y + 24.3 - 1.5, pcb_top]) cube([3.5, 3.0, 0.9]);
        color([0.93, 0.88, 0.75]) translate([X + bx, Y + 24.3, pcb_top + 0.9]) cylinder(d = 1.8, h = 0.8);
    }
    for (lx = [23.5, 27.0]) color([0.95, 0.95, 0.80]) translate([X + lx - 0.8, Y + 25.2 - 0.4, pcb_top]) cube([1.6, 0.8, 0.6]);
    // white connectors: battery (JST-PH, horizontal) and a narrow vertical one
    color([0.95, 0.95, 0.93]) {
        translate([X + 28.0, Y + 4.4, pcb_top]) difference() {
            cube([6.0, 4.5, 6.0]); translate([0.6, -1, 0.8]) cube([4.8, 4.0, 4.6]);
        }
        translate([X + 27.6, Y + 9.0, pcb_top]) cube([3.0, 11.0, 4.2]);
    }
    // a few small chips and passives
    color([0.15, 0.15, 0.15]) {
        translate([X + 10.5, Y + 12.5, pcb_top]) cube([4.0, 4.0, 1.0]);     // CH340X
        translate([X + 15.5, Y + 6.0, pcb_top]) cube([3.0, 3.0, 1.0]);      // charger
        translate([X + 19.5, Y + 15.0, pcb_top]) cube([3.0, 1.6, 1.1]);     // regulator
    }
    color([0.55, 0.45, 0.30]) for (p = [[9, 6], [9, 21], [13, 21.5], [20, 11], [22.5, 19], [25, 6.5], [14.5, 9.5]])
        translate([X + p[0], Y + p[1], pcb_top]) cube([1.6, 0.8, 0.5]);
    // white silkscreen
    color("white") translate([0, 0, pcb_top]) linear_extrude(0.05) {
        translate([X + ol_l - 9.5, Y + 2.6]) text("ESP32-S3-DevKit-Lipo", size = 1.2, halign = "center", valign = "bottom");
        translate([X + 33.0, Y + 21.0]) text("Rev B", size = 1.1, halign = "left", valign = "center");
    }
    // jumper housings on four pins (illustrative positions) with short wires
    for (pin = [[8, 0], [9, 0], [10, 0], [11, 1]]) {
        px = pin_xs[pin[0]];  py = rows[pin[1]];
        color([0.12, 0.12, 0.12]) translate([px - 1.25, py - 1.25, pcb_z0 - hdr_t - 14]) cube([2.5, 2.5, 14]);
        color("dimgray") {
            translate([px, py, pcb_z0 - hdr_t - 16]) cylinder(d = 1.4, h = 2.01);
            translate([px, py, pcb_z0 - hdr_t - 16]) rotate([0, 90, 0]) cylinder(d = 1.4, h = 8);
        }
    }
}

// Pi Hut USB-A breakout, drawn in more detail for the pictures. It stays inside the
// box the case was designed around (sock_w x sock_l x sock_h socket, header below).
module breakout_model() {
    sx0 = br_x1 + br_sock_over;                 // socket front face
    yc  = br_y0 + br_w / 2;
    sh_w = 13.1; sh_h = 5.7;                    // standard USB-A receptacle shell
    pin_x = br_x0 + 2.5;
    pins = [-3.81, -1.27, 1.27, 3.81];          // G, D+, D-, 5V (2.54 mm pitch)
    // black PCB with rounded corners, two mounting holes and four plated pin holes
    color([0.08, 0.08, 0.09]) difference() {
        translate([br_x0, br_y0, pcb_z0]) rbox(0, 0, br_l, br_w, 0, pcb_t, 1.0);
        for (y = [br_y0 + 2.0, br_y1 - 2.0]) translate([br_x0 + 4.3, y, pcb_z0 - 1]) cylinder(d = 2.6, h = 5);
        for (dy = pins) translate([pin_x, yc + dy, pcb_z0 - 1]) cylinder(d = 1.0, h = 5);
    }
    color("gold") for (dy = pins) translate([pin_x, yc + dy, pcb_top - 0.02]) difference() {
        cylinder(d = 1.8, h = 0.05); translate([0, 0, -1]) cylinder(d = 1.0, h = 2);
    }
    // white silkscreen labels next to the pins
    color("white") translate([0, 0, pcb_top]) linear_extrude(0.05) for (i = [0:3])
        translate([pin_x + 2.4, yc + pins[i]]) text(["G", "D+", "D-", "5V"][i], size = 1.3, halign = "left", valign = "center");
    // metal shell: open at the front, with the plastic tongue and four gold contacts inside
    color([0.78, 0.79, 0.80]) translate([sx0 - sock_l, yc - sh_w / 2, pcb_top]) difference() {
        cube([sock_l, sh_w, sh_h]);
        translate([0.8, 0.3, 0.3]) cube([sock_l, sh_w - 0.6, sh_h - 0.6]);
        translate([sock_l - 2.5, -1, sh_h - 0.31]) cube([1.2, 3.0, 0.32]);           // spring latches
        translate([sock_l - 2.5, sh_w - 2.0, sh_h - 0.31]) cube([1.2, 3.0, 0.32]);
    }
    color([0.92, 0.92, 0.92]) translate([sx0 - sock_l + 0.8, yc - 5.5, pcb_top + 3.2]) cube([sock_l - 1.6, 11.0, 1.6]);
    color("gold") for (dy = [-3.5, -1.0, 1.0, 3.5])
        translate([sx0 - sock_l + 2.5, yc + dy - 0.5, pcb_top + 3.1]) cube([sock_l - 4.5, 1.0, 0.1]);
    // solder tabs on the shell sides
    color([0.78, 0.79, 0.80]) for (s = [-1, 1])
        translate([sx0 - 9, yc + s * (sh_w / 2 + 0.25) - 0.25, pcb_top]) cube([2.5, 0.5, 1.2]);
    // header below the board: black plastic, gold pins, then the jumper housings
    color("black") translate([pin_x - 1.27, yc - 5.08, pcb_z0 - hdr_t]) cube([2.54, 10.16, hdr_t]);
    color("gold") for (dy = pins) translate([pin_x - 0.32, yc + dy - 0.32, pcb_z0 - hdr_t - 6]) cube([0.64, 0.64, hdr_t + 6 + pcb_t + 0.8]);
    for (i = [0:3]) {
        translate([pin_x - 1.25, yc + pins[i] - 1.25, pcb_z0 - hdr_t - 14]) color([0.12, 0.12, 0.12]) cube([2.5, 2.5, 14]);
        // wire out of each housing, bending toward the Olimex side
        color(["black", "white", "lightgray", "dimgray"][i]) {
            translate([pin_x, yc + pins[i], pcb_z0 - hdr_t - 16]) cylinder(d = 1.4, h = 2.01);
            translate([pin_x, yc + pins[i], pcb_z0 - hdr_t - 16]) rotate([0, -90, 0]) cylinder(d = 1.4, h = 8);
        }
    }
}

if (part == "base") base();
else if (part == "lid") lid();
else if (part == "lid_print") translate([0, 0, total_h]) rotate([180, 0, 0]) lid();
else if (part == "assembly") { color("dimgray") base(); proxies(); color("gray") lid(); }
else if (part == "exploded") { color("dimgray") base(); proxies(); translate([0, 0, 30]) color("gray") lid(); }
else if (part == "inside") { color("lightgray") base(); proxies(); }   // base with boards, lid off
else if (part == "collisions") {   // should render as nothing
    intersection() { union() { base(); lid(); } proxies(); }
    intersection() { base(); lid(); }
}
