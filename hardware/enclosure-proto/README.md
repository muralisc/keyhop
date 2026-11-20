# keyhop proto case

A 3D-printed box for the no-solder build: an **Olimex ESP32-S3-DevKit-LiPo** and a
**Pi Hut USB-A breakout (horizontal)**, joined by female-female jumper wires.

![exploded view](renders/case-exploded.png)

- Outside size about 70 × 55 × 33 mm, with 3 mm walls (MJF needs at least 1 mm everywhere, including beside the snap grooves). Most of the height is the space under the boards
  for the jumper wires.
- Both boards sit right side up with their pins pointing down. The Olimex rests on two
  blocks under its short ends, and the breakout on two strips under its sides. Posts and a
  fin on the lid hold both boards down and apart.
- Openings: both Olimex USB-C ports (one slot) on one end, the USB-A socket on the other,
  and a window in the lid over the Olimex LEDs and buttons.
- Snap-fit lid (same lap joint as `../enclosure/`), with a fingernail notch on the front.

## Files

| File | What it is |
|---|---|
| `keyhop-proto-case.scad` | OpenSCAD source; every dimension is a named value at the top |
| `keyhop-proto-case-base.stl` | Base, ready to print |
| `keyhop-proto-case-lid.stl` | Lid, flipped for printing |
| `renders/` | Pictures |

## Check before printing

Dimensions marked "photo" in the `.scad` were estimated from phone photos with a ruler
(about ±1 mm). Most likely to need a tweak once printed:

- `under` (21 mm): room under the boards for the header plastic, jumper housings and the
  wire bend.
- `usbc_y`: where the two USB-C ports sit along the Olimex edge.
- `win`: where the LED/button window sits.
- USB-A breakout size (`br_l`, `br_w`) and socket size.

## Build (nuc)

OpenSCAD is a snap on nuc and can't write to `/tmp`, so work in the home folder:

    openscad -D 'part="base"' -o keyhop-proto-case-base.stl keyhop-proto-case.scad
    openscad -D 'part="lid_print"' -o keyhop-proto-case-lid.stl keyhop-proto-case.scad
    openscad -D 'part="collisions"' -o c.stl keyhop-proto-case.scad   # should be empty

The collision check only finds flat contact (boards resting on supports) as of 2026-11-20.
