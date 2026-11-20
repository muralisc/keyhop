# keyhop

USB keyboard → BLE keyboard converter on an ESP32-S3 (PlatformIO, Arduino core 2.0.x), plus a custom PCB (KiCad 10) in `hardware/`.

**Read `HANDOVER.md` first.** It has the current status, next steps, and the hardware and KiCad findings that took long sessions to establish. For the PCB, read `hardware/DESIGN.md` and `hardware/scripts/README.md`.

Key facts:
- Default firmware target is `olimex` (Olimex ESP32-S3-DevKit-LiPo). The custom PCB is designed to run the same target unchanged. The `waveshare` target builds, but USB host can't work on that board (onboard hub on GPIO19/20).
- EspUsbHost is pinned to commit `9e658fa` on purpose. Don't upgrade to v2 without porting to Arduino core 3.x.
- `usbHost.task()` must be called from `loop()`. Include `EspUsbHost.h` before the NimBLE headers.
- PCB v0.1 is routed and DRC-clean with JLCPCB files in `hardware/fab/`, but not yet ordered. Edit the KiCad files directly. The scripts are a record, and `gen_sch.py` overwrites the schematic.
- **KiCad 10 only, on every machine. Never install or downgrade to KiCad 9 or older.** The project files are KiCad 10 format. On Ubuntu, use KiCad's PPA `ppa:kicad/kicad-10.0-releases`, pinned in `/etc/apt/preferences.d/kicad-10-only` (Ubuntu's own archive only has 9.x). If anything seems to need an older KiCad, stop and ask the owner.
- A 3D-printable snap-fit case is in `hardware/enclosure/` (OpenSCAD source + STLs). The owner will order PCB + case together at JLCPCB/JLC3DP (the Olimex board was verified on 2026-11-20).
- Regenerate Gerbers with `--no-x2 --subtract-soldermask` (see `hardware/DESIGN.md`), not `--board-plot-params`.
- KiCad 10 stores net classes and rules in `.kicad_pro`. When scripting, use `pcbnew.NewBoard`/`SaveBoard`.
- Look at a file before overwriting it. The owner may have it open in KiCad. KiCad keeps snapshots in `hardware/.history/` (git-ignored).
- The owner is new to PCB design: explain plainly, keep answers short, and prefer showing renders over technical detail.
- The owner has limited colour vision: use blink patterns and brightness for status, not red/green/orange colours.
