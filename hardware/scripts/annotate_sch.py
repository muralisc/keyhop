"""Add plain-English annotation text to hardware/keyhop.kicad_sch (text only,
no connectivity changes). Idempotent: removes earlier annotations first.

usage: annotate_sch.py <keyhop.kicad_sch> [usbc]
"""
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import Sym, dump, find, parse  # noqa: E402

TAG = "• "  # every annotation starts with a bullet so reruns can find them

NOTES = [
    # (x, y, text)
    (63.5, 101.6, "J1 USB-C socket: 5 V power in, plus USB data\nto the CH340C for flashing and serial logs"),
    (17.78, 137.16, "R1/R2 5.1k: tell the charger or\ncomputer to supply 5 V"),
    (86.36, 83.82, "U3 ESD protection for the\nUSB-C data lines"),
    (139.7, 104.14, "U2 CH340C: USB-to-serial chip.\nFlashing and logs go through it."),
    (158.75, 48.26, "C9 100nF: CH340C\ndecoupling"),
    (198.12, 129.54, "Q1/Q2 + R3/R4: auto-reset. The CH340C's\nDTR/RTS lines pulse EN and IO0 so\nflashing needs no button presses."),
    (20.32, 226.06, "C1/C2: 5 V input\ncapacitors"),
    (55.88, 228.6, "U5 AP2112K: 5 V to 3.3 V\nregulator (600 mA)"),
    (96.52, 226.06, "C3/C4/C5: 3.3 V output\nand ESP32 decoupling"),
    (162.56, 187.96, "R5/C6: EN pull-up + power-on delay.\nSW1 RESET restarts the ESP32."),
    (162.56, 231.14, "R6: IO0 pull-up. SW2 BOOT:\nhold while pressing RESET to\nforce flashing mode."),
    (297.18, 213.36, "U1 ESP32-S3 module: Bluetooth LE + USB host.\nIO19/IO20 = keyboard USB D-/D+, TXD0/RXD0 = serial,\nIO38 = status LED. Unused pins have X (no-connect) marks."),
    (322.58, 200.66, "R7 1k + D1 green LED:\nstatus light, on when IO38 is low"),
    (297.18, 68.58, "F1 500 mA resettable fuse + C7/C8 capacitors:\nthe 5 V supply for the keyboard (VBUS_A)"),
    (314.96, 113.03, "U4 ESD protection for the\nkeyboard data lines"),
    (365.76, 113.03, "J2 USB-A socket:\nplug the keyboard in here"),
    (137.16, 271.78, "PWR_FLAG: marks for the electrical rules\ncheck only. They aren't real parts."),
    (20.32, 251.46, "How to read this sheet: wires end in net labels (e.g. HOST_DP, EN).\n"
                    "Every label with the same name is connected, as are all GND,\n"
                    "+5V and +3V3 symbols. Values: k = kilo-ohm, nF/uF = capacitance."),
]


if len(sys.argv) > 2 and sys.argv[2] == "usbc":
    NOTES = [n for n in NOTES if not n[2].startswith("J2 USB-A")] + [
        (372.11, 58.42, "J2 USB-C socket:\nplug the keyboard in here"),
        (353.06, 147.32, "R8/R9 56k: tell the keyboard\nthat 5 V power is available"),
    ]


def text_node(x, y, text):
    return [Sym("text"), TAG + text, [Sym("exclude_from_sim"), Sym("no")],
            [Sym("at"), x, y, 0],
            [Sym("effects"), [Sym("font"), [Sym("size"), 1.524, 1.524], [Sym("italic"), Sym("yes")]],
             [Sym("justify"), Sym("left"), Sym("bottom")]],
            [Sym("uuid"), str(uuid.uuid4())]]


path = sys.argv[1]
tree = parse(open(path).read())
tree[:] = [x for x in tree if not (isinstance(x, list) and x and x[0] == "text"
                                   and isinstance(x[1], str) and x[1].startswith(TAG))]
idx = max(i for i, x in enumerate(tree) if isinstance(x, list) and x and x[0] == "sheet_instances")
for x, y, t in NOTES:
    tree.insert(idx, text_node(x, y, t))
    idx += 1
open(path, "w").write(dump(tree) + "\n")
print("annotations:", len(NOTES))
