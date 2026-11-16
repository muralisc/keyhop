# keyhop PCB: minimal version design notes

Status: circuit decided, no KiCad files yet. Target fab and assembly: JLCPCB, 2-layer board.

## Circuit

- **MCU:** ESP32-S3-WROOM-1-N8. The firmware doesn't use PSRAM.
- **USB-C (J1):** supplies power, flashing and serial logs.
  - VBUS goes to the +5V rail.
  - CC1 and CC2 each have a 5.1k resistor to GND.
  - D+/D− go through a USBLC6-2SC6 (U3) to a CH340C (U2).
- **CH340C (U2):** runs at 3.3V, with VCC and V3 both tied to +3V3, so its logic levels are safe for the ESP32.
  - CH340C TXD goes to ESP RXD0 (IO44). CH340C RXD comes from ESP TXD0 (IO43).
  - DTR/RTS drive the standard esptool auto-reset circuit, built from two NPN transistors (MMBT3904) with 10k base resistors:
    - Q1: base from DTR, emitter to RTS, collector to EN.
    - Q2: base from RTS, emitter to DTR, collector to IO0.
- **EN:** 10k pull-up to 3V3, 1µF to GND, RESET button to GND.
- **IO0:** 10k pull-up, BOOT button to GND.
- **USB-A host port (J2):** D−/D+ go to IO19/IO20 through a second USBLC6-2SC6 (U4).
  - VBUS_A comes from +5V through a 500 mA polyfuse (F1), with 22µF and 100nF capacitors to GND.
- **Regulator (U5):** AP2112K-3.3. VIN and EN both connect to +5V. 1µF input and output capacitors, plus 10µF on each of +5V and +3V3, and 100nF at the module's 3V3 pin.
- **LED:** goes from +3V3 through 1k to the green LED, then to IO38. It is active-low, so it matches `BOARD_OLIMEX` and the firmware runs unchanged.
- **Unused pins:** leave the IO3, IO45 and IO46 strapping pins floating.

## Layout notes

- Put the module's antenna end at the board edge. Keep copper, ground pour and traces out of the antenna keep-out area on both layers.
- Put USB-C and USB-A on opposite short edges. Route D+/D− as short, matched-length pairs.
- Place the ESD chips close to each connector.

## JLCPCB / LCSC parts

| Ref | Part | LCSC | Library type |
|---|---|---|---|
| U1 | ESP32-S3-WROOM-1-N8 | C2913198 | Extended |
| U2 | CH340C | C84681 | check |
| U3, U4 | USBLC6-2SC6 | C7519 | Extended |
| U5 | AP2112K-3.3TRG1 | C51118 | check |
| J1 | HRO TYPE-C-31-M-12 | C165948 | Extended |
| J2 | USB-A female | TBD: choose one whose footprint is in the KiCad library | |
| F1 | 500 mA polyfuse, 1206 | TBD | |
| Q1, Q2 | MMBT3904 | TBD | |
| passives, buttons, LED | basic parts | TBD | |

Check that each part is in stock and confirm its library type on jlcpcb.com before ordering.
