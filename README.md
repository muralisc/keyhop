# keyhop

Turn any wired USB keyboard into a Bluetooth LE keyboard that can hop between three computers.

An ESP32-S3 acts as a USB host for the keyboard and re-sends every keystroke over Bluetooth LE HID. It stores three host slots, and you switch between them with a key chord, like the multi-device buttons on commercial Bluetooth keyboards.

## Features

- **Any USB boot-protocol keyboard.** No drivers and no software on the computer.
- **Three host slots.** Each slot shows up with its own Bluetooth address and name (`keyhop A3F2 1`, `keyhop A3F2 2`, `keyhop A3F2 3`), so every computer pairs with what it sees as a separate keyboard. `A3F2` is a tag unique to each board (from its chip, printed in the serial log at startup), so several keyhops can be told apart. To choose your own tag (up to 6 characters), flash with `PLATFORMIO_BUILD_FLAGS='-DKEYHOP_TAG=\"desk\"' pio run -t upload`.
- **Chord switching.** The chord is swallowed and never reaches the computer.
- **Per-slot re-pairing.** Forget one slot's host without touching the others.
- **Remembers the last slot** across power cycles. Bonds are kept in flash.
- **LED diagnostics** for USB and Bluetooth state, plus serial logging.

## Key chords

| Chord | Action |
|---|---|
| `Ctrl` + `Alt` + `1` / `2` / `3` | Switch to slot 1 / 2 / 3 (left or right Ctrl/Alt) |
| `Ctrl` + `Alt` + `Shift` + `1` / `2` / `3` | Forget that slot's host and start pairing again |

When you switch slots, keyhop releases any held keys on the old host first.

## Hardware

| Board | Status | Notes |
|---|---|---|
| [Olimex ESP32-S3-DevKit-LiPo](https://www.olimex.com/Products/IoT/ESP32-S3/ESP32-S3-DevKit-LiPo/) | ⏳ Default target, not yet tested on hardware | Keyboard on GPIO19 (D−) / GPIO20 (D+) through a USB-A breakout. Flash and monitor through the **USB-UART** USB-C port (CH340X, auto-reset). |
| Waveshare ESP32-S3-DEV-KIT-N8R8 | ⚠️ USB host does not work | GPIO19/20 are hard-wired to the board's CH334F hub. Bluetooth and the LED code build and run. |

### Wiring (Olimex)

Connect a USB-A female breakout to the board:

| USB-A | ESP32-S3 |
|---|---|
| VBUS | 5V |
| D− | GPIO19 |
| D+ | GPIO20 |
| GND | GND |

The keyboard draws its power from the board's 5V rail.

## Building and flashing

You need [PlatformIO](https://platformio.org/).

```sh
# Olimex (default)
pio run -e olimex -t upload
pio device monitor

# Waveshare: hold BOOT, tap RESET, release BOOT, then
pio run -e waveshare -t upload
```

The firmware runs the ESP32-S3 in USB-OTG mode (`ARDUINO_USB_MODE=0`) so the OTG controller can own GPIO19/20. That means native USB CDC is unavailable, and serial logs go out on UART0 (GPIO43/44) at 115200 baud.

Dependencies (installed by PlatformIO):

- [NimBLE-Arduino](https://github.com/h2zero/NimBLE-Arduino) `^1.4.1`
- [EspUsbHost](https://github.com/tanakamasayuki/EspUsbHost) pinned to `9e658fa`, the last commit before v2. v2 needs Arduino core 3.x and has a different API.

## Pairing

1. Power the board with a keyboard plugged in.
2. Press `Ctrl` + `Alt` + `1` to choose slot 1.
3. On the computer, open the Bluetooth settings and pair with **keyhop XXXX 1** (XXXX is the board's tag). No PIN is needed.
4. Repeat with slots 2 and 3 on other computers.

If a computer forgets the keyboard, or you want to give the slot to a different computer, press `Ctrl` + `Alt` + `Shift` + slot number to clear that slot's bond and pair again.

## LED guide

### Olimex (single green LED)

Listed from highest priority to lowest:

| Pattern | Meaning |
|---|---|
| 1–3 quick blinks, then a pause | Slot number, shown for about 2 s after boot or a slot switch |
| Very fast flicker | USB host stack failed to start (firmware problem) |
| Short blip every second | No USB keyboard detected (check wiring or power) |
| Double blip every second | USB device detected but unusable (for example, a keyboard with a built-in hub) |
| Slow even blink | Keyboard OK, Bluetooth waiting to pair or connect |
| Solid on | Keyboard OK, Bluetooth connected |
| Brief inverted flick | A key report arrived from the keyboard |

### Waveshare (RGB LED)

| Colour | Meaning |
|---|---|
| White flash | Keyboard report received and forwarded |
| Red flash | USB data received, but not a boot-keyboard report |
| Blue | No USB device enumerated |
| Blue flicker | USB host stack failed to start |
| Blue / white alternating | USB device enumerated but no usable interface |
| Green / blue / magenta | Slot 1 / 2 / 3, keyboard idle |

Blinking means Bluetooth is advertising. Solid means a host is connected.

## Limitations

- Only boot-protocol keyboard reports are forwarded: 6-key rollover, no media keys.
- Keyboards with a built-in USB hub (common on models with a USB passthrough port) may not enumerate.
- The battery level is always reported as 100%.
- Caps Lock and other indicator LEDs on the keyboard are not driven from the host.

## License

MIT
