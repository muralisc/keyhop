# keyhop handover

Where the project stands, what was learned the hard way, and what to do next.
Last updated 2026-11-16.

## Status at a glance

| Area | State |
|---|---|
| Firmware build | ✅ `pio run -e olimex` and `pio run -e waveshare` both compile (espressif32@6.5.0, Arduino core 2.0.14 / ESP-IDF 4.4.6) |
| Bluetooth side | ✅ Verified on hardware (Waveshare): pairs as "Keyboard 1" and connects |
| USB host side on Waveshare | ❌ Can't work. GPIO19/20 are hard-wired to the board's CH334F hub (details below) |
| Olimex ESP32-S3-DevKit-LiPo | ⏳ Ordered or arriving, **not yet tested**. Firmware target written, untested on real hardware |
| Slot switching, re-pairing, multi-host | ⏳ Untested (needs a working keyboard path first) |
| Custom PCB | ✅ v0.1 routed, DRC-clean, JLCPCB files in `hardware/fab/`. Not ordered yet. See `hardware/DESIGN.md` (check part rotations in JLCPCB's preview when ordering) |

## Next steps

1. **Bring up the Olimex board.**
   - Wire the USB-A breakout: D- → GPIO19, D+ → GPIO20, VBUS → +5V (EXT1 pin 21), GND → GND.
   - Plug the Mac into the board's **USB-UART** USB-C port (not USB-OTG), then run `pio run -t upload` and `pio device monitor`. Auto-reset through the CH340X should work, so no BOOT/RESET dance. This is untested; if upload fails, hold BOOT and tap RESET.
   - Look for `USB: keyboard ready` in the log, then `key report: ...` lines when typing.
2. **Check the LED polarity.** The schematic suggests the green LED on GPIO38 is active-low (2.2k from +3.3V), and `ledWrite()` assumes that. If the patterns look inverted, flip `ledWrite()` in `src/main.cpp`.
3. Pair with one computer and test typing, including modifiers.
4. Test slot switching (Left Ctrl + Left Alt + 1/2/3) and re-pairing (add Left Shift) across 3 computers.
5. When it works, drop `CORE_DEBUG_LEVEL` back from 3 to 1 in `platformio.ini`.
6. **Order the PCB** when ready (`hardware/DESIGN.md` → "Ordering at JLCPCB"). Check part rotations in JLCPCB's placement preview first.
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
- LED: one green LED on GPIO38, very likely active-low.
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
- `NimBLEDevice::deinit(true)` on each slot switch leaks the small `NimBLEHIDDevice` object. That's acceptable for now.
- `usbState()` in `main.cpp` drives both the LED and the `USB: ...` serial lines: `clientHandle` null = host stack failed, `deviceHandle` null = no device, `!isReady` = device without a usable interrupt-IN endpoint, otherwise ready.

## Tooling on the original machine

- PlatformIO installed with `brew install platformio` (6.2.0).
- KiCad 10.0.8 (Homebrew cask). `kicad-cli` is at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`. Its bundled Python (with `pcbnew`) is at `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`.
- Java (`brew install openjdk`) for Freerouting 2.5.0 (`freerouting-2.5.0.jar` from GitHub releases, SHA-256 checked against GitHub's asset digest). Claude Code's permission system blocks Claude from running the downloaded jar, so the user runs that one command with `!`.
- `brew install poppler` was used to render schematic PDFs (`pdftoppm`, `pdftotext`).

## Git state

- **`main` has everything**: firmware, handover notes, schematic, routed board, fab files, renders and scripts. `pcb-schematic` was fast-forwarded into it on 2026-11-16.
- `handover-notes` and `pcb-schematic` are older branches kept on the remote. They're fully contained in `main` and can be deleted.

## Notes for whoever picks this up (human or Claude)

- **The owner has limited colour vision.** For LED or UI status, use blink patterns, brightness, blue/white and off. Don't use red vs green vs orange distinctions. The Olimex LED scheme was designed around this.
- The owner prefers short, plain explanations with concrete next steps and multimeter-style checks they can do themselves.
