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
| Custom PCB | 📝 Circuit decided, see `hardware/DESIGN.md`. No KiCad files yet |

## Next steps

1. **Bring up the Olimex board.**
   - Wire the USB-A breakout: D- → GPIO19, D+ → GPIO20, VBUS → +5V (EXT1 pin 21), GND → GND.
   - Plug the Mac into the board's **USB-UART** USB-C port (not USB-OTG), then run `pio run -t upload` and `pio device monitor`. Auto-reset through the CH340X should work, so no BOOT/RESET dance. This is untested; if upload fails, hold BOOT and tap RESET.
   - Look for `USB: keyboard ready` in the log, then `key report: ...` lines when typing.
2. **Check the LED polarity.** The schematic suggests the green LED on GPIO38 is active-low (2.2k from +3.3V), and `ledWrite()` assumes that. If the patterns look inverted, flip `ledWrite()` in `src/main.cpp`.
3. Pair with one computer and test typing, including modifiers.
4. Test slot switching (Left Ctrl + Left Alt + 1/2/3) and re-pairing (add Left Shift) across 3 computers.
5. When it works, drop `CORE_DEBUG_LEVEL` back from 3 to 1 in `platformio.ini`.
6. Later: N-key rollover (parse the keyboard's report descriptor), keyboard LED sync, battery (the Olimex LiPo can't supply 5V to the keyboard, so it needs a boost converter), the PCB in `hardware/DESIGN.md`.

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
- `brew install poppler` was used to render schematic PDFs (`pdftoppm`, `pdftotext`).

## Notes for whoever picks this up (human or Claude)

- **The owner has limited colour vision.** For LED or UI status, use blink patterns, brightness, blue/white and off. Don't use red vs green vs orange distinctions. The Olimex LED scheme was designed around this.
- The owner prefers short, plain explanations with concrete next steps and multimeter-style checks they can do themselves.
