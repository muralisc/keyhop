# keyhop handover

Where the project stands, what was learned the hard way, and what to do next.
Last updated 2026-11-17.

## Status at a glance

| Area | State |
|---|---|
| Firmware build | ✅ `pio run -e olimex` and `pio run -e waveshare` both compile (espressif32@6.5.0, Arduino core 2.0.14 / ESP-IDF 4.4.6) |
| Bluetooth side | ✅ Verified on Waveshare and Olimex. Advertises as `keyhop <tag> <slot>` (was "Keyboard N" before 2026-11-20) |
| USB host side on Waveshare | ❌ Can't work. GPIO19/20 are hard-wired to the board's CH334F hub (details below) |
| Olimex ESP32-S3-DevKit-LiPo | 🟡 Arrived 2026-11-20. Flashes via USB-UART1 with auto-reset (`/dev/cu.usbserial-10` on the Mac), boots, BLE up, USB host starts (`no device detected`). LED polarity confirmed. **USB host works**: KBDFans DZ60 (QMK) enumerates, `USB: keyboard ready`, key reports arrive with correct keycodes and modifiers. **End to end works**: paired with the Mac, typing works in TextEdit. This board's tag is **C398** |
| Slot switching, re-pairing, multi-host | ⏳ Untested (keyboard path now works, so this is next) |
| Custom PCB | ✅ v0.1 routed, DRC-clean, JLCPCB files in `hardware/fab/`. 2026-11-17: USB-C edge notch added (on nuc), fab files regenerated. 2026-11-20: 4 out-of-stock parts swapped, CPL rotations fixed from JLCPCB's preview. **On hold:** JLCPCB marks every ESP32-S3-WROOM-1 variant "Standard Only", so Economic assembly isn't possible; Standard needs ≥70×70 mm (a custom panel with 5 mm gaps for the overhanging USB sockets). Owner chose the no-solder proto build for now |
| Enclosure | ✅ v0.1 snap-fit case designed (`hardware/enclosure/`), STLs ready for JLC3DP. Being ordered with the PCB 2026-11-20; not printed or test-fitted yet |
| Proto case | ✅ 2026-11-20: case for the no-solder build (Olimex + USB-A breakout + jumpers) in `hardware/enclosure-proto/`. Dimensions estimated from photos; not printed yet |

## Next steps

1. ~~**Bring up the Olimex board.**~~ Done 2026-11-20 (flash, USB host, BLE typing all work).
   - Wire the USB-A breakout: D- → GPIO19, D+ → GPIO20, VBUS → +5V (EXT1 pin 21), GND → GND.
   - Plug the Mac into the board's **USB-UART** USB-C port (not USB-OTG), then run `pio run -t upload` and `pio device monitor`. Auto-reset through the CH340X works (confirmed), so no BOOT/RESET dance. On the Mac the port is `/dev/cu.usbserial-10`. Note: opening the serial port also resets the board.
   - Look for `USB: keyboard ready` in the log, then `key report: ...` lines when typing.
2. ~~Check the LED polarity.~~ Done 2026-11-20: GPIO38 LED is active-low as assumed ("no device" shows a short blip each second).
3. ~~Pair with one computer and test typing.~~ Done 2026-11-20 on the Mac. Still check modifier shortcuts (Cmd+C/V, Shift) in real use.
4. Test slot switching (Ctrl + Alt + 1/2/3, either side; changed 2026-11-20 because left-only didn't work for the owner) and re-pairing (add Shift) across 3 computers.
5. When it works, drop `CORE_DEBUG_LEVEL` back from 3 to 1 in `platformio.ini`.
6. **Order the PCB and case together** when ready. The owner waited until the Olimex board worked (done 2026-11-20); ordering is in progress.
   - PCB: `hardware/DESIGN.md` → "Ordering at JLCPCB". Check part rotations in JLCPCB's placement preview first; if any part is out of stock, don't accept a substitute without checking.
   - Case: upload `hardware/enclosure/keyhop-case-base.stl` and `keyhop-case-lid.stl` to JLC3DP in the same checkout (SLA resin, e.g. black; MJF nylon if the snap feels too stiff).
7. Later: N-key rollover (parse the keyboard's report descriptor), keyboard LED sync, battery (the Olimex LiPo can't supply 5V to the keyboard, so it needs a boost converter).

## Custom PCB (v0.1)

Everything is in `hardware/`. `DESIGN.md` has the circuit, parts list with LCSC numbers, board summary and ordering steps. `scripts/README.md` has the pipeline that produced the board.

- **Schematic:** `keyhop.kicad_sch`, also `keyhop-schematic.pdf` and a labelled `keyhop-schematic.png` with plain-English notes on every part. It uses only stock KiCad 10 symbols, with net labels on short stubs (no long wires). ERC has one expected error: CH340C V3 tied to VCC, which the datasheet requires at 3.3 V.
- **Board:** `keyhop.kicad_pcb`, 60 × 35 mm, 2 layers. It's 60 × 35 rather than the planned 50 × 30 because the ESP32 footprint's 48 mm-wide antenna keep-out and the 15.6 mm USB-A footprint didn't fit. Routed with Freerouting 2.5.0, with GND pours on both layers. DRC: 0 errors, 0 unconnected, 0 schematic-parity issues. Remaining warnings are cosmetic silkscreen plus "U1 differs from library" (thermal vias enlarged to 0.3 mm on purpose).
- **Fab files:** `fab/keyhop-gerbers.zip` (separate PTH/NPTH drill files), `fab/keyhop-bom.csv`, `fab/keyhop-cpl.csv`, all in JLCPCB format. J3 (UART header) is DNP and excluded.
- **Renders:** `renders/`. J1 and J2 use stand-in 3D models on a render-only copy, because the stock library has no models for those exact parts. The buttons show as outlines.
- **Firmware compatibility:** the PCB matches the `olimex` firmware target (CH340C auto-reset, active-low LED on IO38, keyboard on IO19/IO20), so no firmware change should be needed.

### PCB gotchas learned (KiCad 10 scripting)

- KiCad 10 keeps **net classes and design rules in `.kicad_pro`**, not the board. A board made with `pcbnew.BOARD()` and `board.Save()` loses them. Use `pcbnew.NewBoard(path)` and `pcbnew.SaveBoard(path, board)`, which also write the project file.
- Netlist local nets have a leading `/` (`/EN`, `/VBUS_A`). Keep it on board nets, or DRC's schematic-parity check flags every pad. Net-class patterns must use `/VBUS_A` too.
- `FOOTPRINT.SetField(name, value)` creates the field **visible on silkscreen**. Hide it and move it to F.Fab afterwards.
- `kicad-cli pcb drc --schematic-parity` only compares against a schematic with the same base name in the same folder. In a scratch folder the check is silently skipped.
- KiCad 10 auto-creates `hardware/.history/` (a nested git repo of local snapshots). It's in `.gitignore`. Restore from it via KiCad's File → Local History.
- Freerouting narrows tracks into fine-pitch pads (0.15–0.19 mm), so the min-track rule is 0.15 mm (JLCPCB can do 0.127 mm).
- Specctra export or import functions exist in KiCad 10's Python: `pcbnew.ExportSpecctraDSN`, `pcbnew.ImportSpecctraSES`.

## Enclosure (v0.1)

Everything is in `hardware/enclosure/`. `keyhop-case.scad` is the source (OpenSCAD, parametric, comments at the top); the STLs are exports.

- **Design:** two-part box, 65.3 × 40.3 × 15.6 mm, 2.4 mm walls. The board rests on two ledges along the long sides (2.6 mm above the floor, clearing the USB shield pins) and four posts under the lid press it down at free corner spots. No PCB holes needed.
- **Snap:** the walls split at the PCB top with a 3 mm lap joint (base inner half up, lid outer half down). Two bumps per long side click into grooves. Fingernail notch on the front long side.
- **Openings:** USB-C cut sized for the plug overmold (12.4 × 6.8). USB-A cut 15.2 wide around the shell, plus a 1.4 mm outer pocket so the plug body gets near the socket. Paperclip pinholes (1.8 mm, with guide tubes) for RESET/BOOT, and a 2 mm LED window with a light tube. Engraved labels on top.
- **Unverified dimensions:** the USB-A and USB-C datasheets couldn't be fetched (LCSC/krhro links fail), so the openings use standard sizes plus clearance. The USB-A shell height was assumed 7.0 mm (`usba_h`); the C2880619 (-F, flat front, 12.8 mm wide) datasheet read on 2026-11-20 confirms 7.00 mm, so the 15.2 × 7.9 mm cut fits. Check against the real part once boards arrive; each opening is a single `yz_slot(...)` line in `openings()`.
- **Collision check:** `part="collisions"` intersects the case with stand-in boxes for the board and parts; it should render as nothing (flat touching contact from the posts and ledges is expected).
- **Build commands (Linux NUC):** OpenSCAD 2021.01 is a snap (`/snap/bin/openscad`). The snap can't write to `/tmp`, so export into the repo. PNG renders need a virtual display: `xvfb-run -a -s '-screen 0 1600x1200x24' openscad --render --colorscheme=Tomorrow -D 'part="exploded"' --imgsize=1400,1000 --camera=30,17,12,58,0,32,190 -o renders/case-exploded.png keyhop-case.scad`. STLs: `openscad -D 'part="base"' -o keyhop-case-base.stl keyhop-case.scad` and `part="lid_print"` → `keyhop-case-lid.stl`.

## Hardware learned the hard way

### Waveshare ESP32-S3-DEV-KIT-N8R8: no USB host on GPIO19/20

From Waveshare's schematic: USB-C → **CH334F hub** → port 1 = GPIO20 (DP1) / GPIO19 (DM1), port 2 = CH343P USB-serial → UART0. The traces are direct, with no resistors to remove. The hub is powered whenever the board is, and its downstream port has its own host pull-downs, so there are two hosts on one D+/D- pair.

Symptoms seen (so you recognise them on any board):
- A QMK keyboard **and** a plain USB mouse both never enumerated. The LED stayed "no device" (`deviceHandle` null), while the BLE side worked fine.
- Multimeter: 5V at the USB-A VBUS was fine, and continuity on D-/D+/GND was fine, with no shorts.
- D+ (GPIO20) read **2.10–2.45V, fluctuating** while running: the ESP32 detects attach and keeps retrying enumeration. It read **2.65V steady with RESET held**, where ~3.3V was expected with nothing else loading D+. The extra load is the hub's pull-down. D- read 0V, so the lines weren't swapped.

Workarounds considered: removing the CH334F with hot air would work, but the board then loses its USB-C flashing (flash via UART0 instead). Cutting traces or holding the hub in reset aren't practical. Software USB host on other pins only handles low-speed devices. Decision: switch boards.

### Olimex ESP32-S3-DevKit-LiPo (Rev B), checked from its schematic

- **USB-OTG** USB-C: D-/D+ go straight to GPIO19/20, no hub. GPIO19/20 are also on the EXT header.
- That port's VBUS goes *into* the board through a 1N5819 diode, so **it can't power a keyboard**. Keep the keyboard on the USB-A breakout fed from +5V.
- **USB-UART** USB-C: a CH340X to UART0 (GPIO43/44) with auto-reset. You can flash and see logs while the keyboard is connected.
- LED: one green LED on GPIO38, active-low (confirmed on hardware).
- +5V on EXT1 pin 21 works as an input or an output. The LiPo charger is built in, but on battery the rail isn't 5V.

### Other wiring facts

- Power is a 5V phone charger → Pi Hut USB-C breakout (CC resistors fitted, so it's a power *sink*: input only) → 5V rail. A breakout with sink CC resistors can't act as a keyboard socket.
- A QMK keyboard stays **dark until a host enumerates it**, even on a plain charger. A dark keyboard isn't evidence of missing power. Measure VBUS instead.
- Never plug a computer or charger into the board's native-USB port while the keyboard is in use. Two hosts on GPIO19/20 conflict, and some chargers short D+ to D-.

## Firmware decisions and gotchas

- **EspUsbHost is pinned to `9e658fa`**, the last commit before the v2 rewrite. v2.x needs Arduino core 3.x, has a different (callback) API, and fails to compile on core 2.0.x. Tag `1.0.1` is too old (no `onKeyboard`).
- This EspUsbHost version **has no background task**: `usbHost.task()` must be called from `loop()`. The original draft forgot this, which would have meant no keys ever.
- **Include order matters**: `EspUsbHost.h` must come before the NimBLE headers. NimBLE's `HIDTypes.h` `#define`s names (`HID_SUBCLASS_NONE`, ...) that TinyUSB's `hid.h` uses as enum members.
- **USB-OTG mode**: `build_unflags = -DARDUINO_USB_MODE=1`, `-DARDUINO_USB_MODE=0`, so the OTG controller owns GPIO19/20 instead of USB-Serial/JTAG. It didn't fix the Waveshare (hardware problem), but it's correct for host mode.
- The library only calls `onKeyboard` for HID boot-subclass keyboard interfaces. It never sends SET_PROTOCOL(boot), so it relies on the keyboard sending 8-byte boot reports by default. It also **drops any report whose first keycode is Num Lock**, and doesn't handle unplugging and replugging the keyboard well (power-cycle instead).
- **Bluetooth names** are `keyhop <tag> <slot>`. The tag is 4 hex digits from the chip's factory MAC (unique per board), or `-DKEYHOP_TAG=\"name\"` (max 6 chars, checked at compile time) via `PLATFORMIO_BUILD_FLAGS`. Name buffer is 16 bytes.
- **Slot-switch crash (fixed 2026-11-20):** `server->setCallbacks(&serverCallbacks)` let NimBLE `delete` the static callbacks object on `deinit`, which asserted in `heap_caps_free` and rebooted. Now passes `false`. Harmless leftover: `E NimBLEAdvertising: Error enabling advertising; rc=30` during the switch.
- `NimBLEDevice::deinit(true)` on each slot switch leaks the small `NimBLEHIDDevice` object. That's acceptable for now.
- `usbState()` in `main.cpp` drives both the LED and the `USB: ...` serial lines: `clientHandle` null = host stack failed, `deviceHandle` null = no device, `!isReady` = device without a usable interrupt-IN endpoint, otherwise ready.

## Tooling on the Linux NUC (2026-11-17)

- KiCad 10.0.8 from the Ubuntu package: `kicad-cli` is on the PATH and the **system `/usr/bin/python3` has `pcbnew`** (no bundled Python needed). Footprint library at `/usr/share/kicad/footprints`.
- OpenSCAD via snap, `xvfb-run` for headless PNG renders (see Enclosure above).
- The owner may connect over Remote Control from another device; send renders with SendUserFile.

## Tooling on the original machine

- PlatformIO installed with `brew install platformio` (6.2.0).
- KiCad 10.0.8 (Homebrew cask). `kicad-cli` is at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`. Its bundled Python (with `pcbnew`) is at `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`.
- Java (`brew install openjdk`) for Freerouting 2.5.0 (`freerouting-2.5.0.jar` from GitHub releases, SHA-256 checked against GitHub's asset digest). Claude Code's permission system blocks Claude from running the downloaded jar, so the user runs that one command with `!`.
- `brew install poppler` was used to render schematic PDFs (`pdftoppm`, `pdftotext`).

## Tooling on nuc (Linux build machine)

nuc (`murali-NUC7PJYH`, Ubuntu 26.04 LTS, reachable as `ssh nuc`, passwordless sudo) was set up on 2026-11-16. Repo at `~/src/keyhop`.

- **KiCad 10.0.8** from KiCad's PPA `ppa:kicad/kicad-10.0-releases`, with symbols, footprints, 3D models and templates. Ubuntu 26.04's own archive only has KiCad 9.0.8, which can't open these files. `/etc/apt/preferences.d/kicad-10-only` pins KiCad packages to the PPA (priority 1001) and blocks Ubuntu's (−1), so updates can never drop to 9.x. **Never downgrade KiCad; stop and ask the owner instead.**
- KiCad's Python module works with the system `python3` (`import pcbnew`), so the scripts in `hardware/scripts/` run with plain `python3` on nuc. Change the macOS library paths in `sexp.py`/`build_pcb.py` to `/usr/share/kicad/symbols` and `/usr/share/kicad/footprints`.
- KiCad's global library tables were copied from `/usr/share/kicad/template/` into `~/.config/kicad/10.0/` (what the first GUI launch would do). Without them ERC reports ~100 "library not included" warnings.
- **PlatformIO 6.2.0** via `pipx` (`~/.local/bin/pio`).
- **Java** (OpenJDK 25, `default-jre-headless`) and **Freerouting 2.5.0** at `~/tools/freerouting/freerouting-2.5.0.jar`, SHA-256 checked against GitHub's digest.
- Pillow (`python3-pil`) for `label_top.py`; poppler (`pdftoppm`) was already there.
- User `murali` added to `dialout` for serial access (needs a fresh login). `brltty` is installed and is known to grab CH340 serial adapters on Ubuntu. Removing it (`sudo apt remove brltty`) is pending the owner's OK.
- Verified on nuc: ERC (1 expected V3 error) and DRC (0 errors, 0 unconnected, 0 parity issues) give the same results as the Mac.

## Git state

- **`main` has everything**: firmware, handover notes, schematic, routed board, fab files, renders and scripts. `pcb-schematic` was fast-forwarded into it on 2026-11-16.
- `handover-notes` and `pcb-schematic` are older branches kept on the remote. They're fully contained in `main` and can be deleted.

## Notes for whoever picks this up (human or Claude)

- **The owner has limited colour vision.** For LED or UI status, use blink patterns, brightness, blue/white and off. Don't use red vs green vs orange distinctions. The Olimex LED scheme was designed around this.
- The owner prefers short, plain explanations with concrete next steps and multimeter-style checks they can do themselves.
