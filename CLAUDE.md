# keyhop

USB keyboard → BLE keyboard converter on an ESP32-S3 (PlatformIO, Arduino core 2.0.x).

**Read `HANDOVER.md` first.** It has the current status, the next steps, and hardware findings that took a long debugging session to establish.

Key facts:
- Default target is `olimex` (Olimex ESP32-S3-DevKit-LiPo). The `waveshare` target builds, but USB host can't work on that board because its GPIO19/20 are wired to an onboard hub.
- EspUsbHost is pinned to commit `9e658fa` on purpose. Don't upgrade to v2 without porting to Arduino core 3.x.
- `usbHost.task()` must be called from `loop()`. Include `EspUsbHost.h` before the NimBLE headers.
- The owner has limited colour vision: use blink patterns and brightness for status, not red/green/orange colours.
