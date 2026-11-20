// keyhop v0.1 enclosure: two-part snap-fit case for the 60 x 35 mm PCB.
//
// Render one part with:   openscad -D 'part="base"' -o base.stl keyhop-case.scad
// part = "base" | "lid" | "lid_print" (lid flipped for printing)
//      | "assembly" | "exploded" | "collisions"
//
// Coordinates: X/Y match the PCB (origin at its bottom-left corner, Y up =
// antenna edge). In KiCad terms X = kx - 100, Y = 135 - ky. Z = 0 is the
// underside of the case floor.

part = "exploded";
$fn = 48;

// ---- PCB -----------------------------------------------------------------
pcb_w = 60;
pcb_h = 35;
pcb_t = 1.6;

// ---- Case ----------------------------------------------------------------
gap      = 0.25;   // PCB edge to inner wall
wall     = 2.4;
floor_t  = 1.6;
top_t    = 1.6;
standoff = 2.6;    // clears the USB shield pins poking through the board
above    = 8.2;    // PCB top to underside of lid (USB-A is the tallest part, ~7 mm)
r_out    = 2.5;    // outer corner radius
lap      = 3.0;    // overlap height of the snap joint
clear    = 0.1;    // clearance between the two lap halves
lap_t    = (wall - clear) / 2;

pcb_z0  = floor_t + standoff;   // underside of PCB
pcb_top = pcb_z0 + pcb_t;       // top of PCB, also where the case splits
ceil_z  = pcb_top + above;      // underside of lid
total_h = ceil_z + top_t;
split_z = pcb_top;

x0 = -gap - wall;  x1 = pcb_w + gap + wall;
y0 = -gap - wall;  y1 = pcb_h + gap + wall;

// ---- Part positions (from the PCB) ----------------------------------------
usbc_y  = 15;            // J1 centre
usbc_zc = pcb_top + 1.63; // USB-C shell 3.26 mm tall, sits on the board
usba_y  = 15;            // J2 centre
usba_h  = 7.0;           // assumed USB-A shell height (datasheet unreadable)
sw   = [[24.6, 3.6], [35.4, 3.6]];   // SW1 RESET, SW2 BOOT (1.5 mm tall)
led  = [42.0, 1.6];                  // D1
posts = [[1.0, 32.6, 2.2], [59.0, 32.6, 2.2], [0.9, 0.9, 1.6], [59.0, 2.4, 2.2]];
bump_x = [12, 48];       // snap bumps along both long sides

// ---- Helpers -------------------------------------------------------------
module rbox(ax, ay, bx, by, z0, z1, r) {
    r2 = max(r, 0.01);
    hull() for (x = [ax + r2, bx - r2], y = [ay + r2, by - r2])
        translate([x, y, z0]) cylinder(r = r2, h = z1 - z0);
}
// rounded rectangle in the YZ plane, extruded along X from xa to xb
module yz_slot(xa, xb, yc, zc, w, h, r) {
    translate([xa, 0, 0]) rotate([0, 90, 0]) linear_extrude(xb - xa)
        translate([-zc, yc]) offset(r) square([h - 2*r, w - 2*r], center = true);
}
module outer_shell(z0, z1) rbox(x0, y0, x1, y1, z0, z1, r_out);
module inner_space(z0, z1, grow = 0)
    rbox(-gap - grow, -gap - grow, pcb_w + gap + grow, pcb_h + gap + grow, z0, z1,
         max(r_out - wall + grow, 0.3));

module openings() {
    // USB-C: cut for the plug's overmold so the plug can reach the socket
    yz_slot(x0 - 1, -gap + 0.01, usbc_y, usbc_zc, 12.4, 6.8, 1.6);
    // USB-A: cut around the socket shell...
    yz_slot(pcb_w + gap - 0.01, x1 + 1, usba_y, pcb_top + (usba_h + 0.3) / 2 - 0.3,
            15.2, usba_h + 0.9, 0.8);
    // ...plus a shallow outer pocket so the plug's overmold sits nearer the socket
    yz_slot(x1 - 1.4, x1 + 1, usba_y, pcb_top + usba_h / 2 + 0.3, 18.0, 9.4, 1.5);
}

// ---- Base ----------------------------------------------------------------
module base() {
    difference() {
        union() {
            outer_shell(0, split_z);
            // inner half of the wall continues up as the snap lap
            difference() {
                inner_space(split_z - 0.01, split_z + lap, lap_t);
                inner_space(split_z - 0.02, split_z + lap + 1);
            }
            // snap bumps on the outer face of the lap, both long sides
            for (x = bump_x, s = [0, 1])
                translate([x, s ? pcb_h + gap + lap_t : -gap - lap_t, split_z + lap / 2])
                    rotate([0, 90, 0]) cylinder(r = 0.4, h = 10, center = true);
        }
        inner_space(floor_t, split_z + lap + 1);
        openings();
    }
    // ledges the PCB rests on, along both long sides
    for (y = [-gap - 0.01, pcb_h - 1.2])
        translate([-gap, y, floor_t - 0.01]) cube([pcb_w + 2*gap, 1.2 + gap + 0.01, standoff + 0.01]);
}

// ---- Lid -----------------------------------------------------------------
module lid() {
    difference() {
        union() {
            outer_shell(split_z + lap, total_h);
            // outer half of the wall continues down over the base's lap
            difference() {
                outer_shell(split_z, split_z + lap + 0.01);
                inner_space(split_z - 1, split_z + lap + 0.02, lap_t + clear);
            }
            // posts that press the PCB down onto the ledges
            for (p = posts) translate([p[0], p[1], pcb_top]) cylinder(d = p[2], h = ceil_z - pcb_top + 0.01);
            // guide tubes for a paperclip to reach RESET / BOOT
            for (s = sw) translate([s[0], s[1], pcb_top + 3.0]) cylinder(d = 4.2, h = ceil_z - pcb_top - 2.99);
            // light tube over the LED (stops light bleeding around inside)
            translate([led[0], led[1], pcb_top + 1.2]) cylinder(d = 3.4, h = ceil_z - pcb_top - 1.19);
        }
        inner_space(split_z - 1, split_z + lap + 0.01, lap_t + clear);   // (redundant, keeps lap clean)
        difference() {                                                      // hollow interior
            inner_space(split_z - 1, ceil_z);
            for (p = posts) translate([p[0], p[1], 0]) cylinder(d = p[2], h = 100);
            for (s = sw) translate([s[0], s[1], 0]) cylinder(d = 4.2, h = 100);
            translate([led[0], led[1], 0]) cylinder(d = 3.4, h = 100);
        }
        // grooves the base's bumps click into
        for (x = bump_x, s = [0, 1])
            translate([x, s ? pcb_h + gap + lap_t : -gap - lap_t, split_z + lap / 2])
                rotate([0, 90, 0]) cylinder(r = 0.5, h = 10.6, center = true);
        // paperclip holes and LED window
        for (s = sw) translate([s[0], s[1], pcb_top]) cylinder(d = 1.8, h = 50);
        translate([led[0], led[1], pcb_top]) cylinder(d = 2.0, h = 50);
        // fingernail notch for prying the lid off (front long side)
        translate([pcb_w / 2 - 5, y0 - 1, split_z - 0.01]) cube([10, wall - lap_t + 1, 1.0]);
        openings();
        // engraved labels on top
        translate([0, 0, total_h - 0.5]) linear_extrude(1) {
            translate([pcb_w / 2, 20]) text("keyhop", size = 6, halign = "center", valign = "center",
                                            font = "Liberation Sans:style=Bold");
            translate([sw[0][0], 8]) text("RST", size = 2.6, halign = "center", valign = "center");
            translate([sw[1][0], 8]) text("BOOT", size = 2.6, halign = "center", valign = "center");
            translate([led[0] + 2.2, led[1]]) text("LED", size = 2.2, halign = "left", valign = "center");
        }
    }
}

// ---- Stand-ins for the board and parts (for previews and collision checks)
module pcb_proxy() {
    color("darkgreen") translate([0, 0, pcb_z0]) cube([pcb_w, pcb_h, pcb_t]);
    color("silver") {
        translate([20.95, 9.45, pcb_top]) cube([18.1, 25.6, 3.2]);           // U1 ESP32 module
        translate([0.6, 10.48, pcb_top]) cube([7.4, 9.04, 3.26]);            // J1 USB-C
        translate([46.45, 7.7, pcb_top]) cube([14.3, 14.6, usba_h]);         // J2 USB-A
        for (s = sw) translate([s[0] - 2.6, s[1] - 2.6, pcb_top]) cube([5.2, 5.2, 1.5]);
        translate([12.66, 6.75, pcb_top]) cube([7.5, 10.5, 1.75]);           // U2 CH340C
        translate([led[0] - 0.8, led[1] - 0.4, pcb_top]) cube([1.6, 0.8, 0.8]);
        // shield pins poking through the underside
        for (p = [[3.25, 10.68], [7.43, 10.68], [3.25, 19.32], [7.43, 19.32], [48.35, 8.6], [48.35, 21.4]])
            translate([p[0], p[1], pcb_z0 - 1.5]) cylinder(d = 1.0, h = 1.5);
    }
}

if (part == "base") base();
else if (part == "lid") lid();
else if (part == "lid_print") translate([0, 0, total_h]) rotate([180, 0, 0]) lid();
else if (part == "assembly") { color("dimgray") base(); pcb_proxy(); color("gray", 0.35) lid(); }
else if (part == "exploded") { color("dimgray") base(); pcb_proxy(); translate([0, 0, 22]) color("gray") lid(); }
else if (part == "collisions") {   // should render as nothing
    intersection() { union() { base(); lid(); } pcb_proxy(); }
    intersection() { base(); lid(); }
}
