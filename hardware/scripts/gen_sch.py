"""Generate hardware/keyhop.kicad_sch from the circuit in hardware/DESIGN.md.

Connectivity is by net labels / power symbols on short stubs at each pin, so
placement only affects readability. Every pin of every part must be listed:
a net name, or None for an explicit no-connect flag.
"""
import math
import re
import sys
import uuid
from datetime import date

import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import Sym, dump, find, first, get_symbol, pins  # noqa: E402

OUT = sys.argv[1]
PROJECT = "keyhop"
ROOT = str(uuid.uuid4())
POWER_NETS = {"GND": "GND", "+5V": "+5V", "+3V3": "+3V3"}
STUB = 2.54

FP_R = "Resistor_SMD:R_0603_1608Metric"
FP_C = "Capacitor_SMD:C_0603_1608Metric"


def nc_all(*nums):
    return {str(n): None for n in nums}


esp_nets = {"1": "GND", "40": "GND", "41": "GND", "2": "+3V3", "3": "EN",
            "13": "HOST_DM", "14": "HOST_DP", "27": "IO0", "31": "LED_K",
            "36": "U0RXD", "37": "U0TXD"}
for n in range(1, 42):
    esp_nets.setdefault(str(n), None)

# (ref, lib, symbol, value, footprint, lcsc, x, y, {pin: net|None}, extra)
PARTS = [
    # --- USB-C: power in + CH340C serial --------------------------------
    ("J1", "Connector", "USB_C_Receptacle_USB2.0_16P", "USB-C (power, flash, logs)",
     "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "C165948", 40.64, 76.2,
     {"A1": "GND", "B1": "GND", "A12": "GND", "B12": "GND", "SH": "GND",
      "A4": "+5V", "B4": "+5V", "A9": "+5V", "B9": "+5V",
      "A5": "CC1", "B5": "CC2", "A6": "CH_DP", "B6": "CH_DP",
      "A7": "CH_DM", "B7": "CH_DM", "A8": None, "B8": None}, {}),
    ("R1", "Device", "R", "5.1k", FP_R, "C23186", 25.4, 119.38, {"1": "CC1", "2": "GND"}, {}),
    ("R2", "Device", "R", "5.1k", FP_R, "C23186", 38.1, 119.38, {"1": "CC2", "2": "GND"}, {}),
    ("U3", "Power_Protection", "USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     "C7519", 99.06, 63.5,
     {"1": "CH_DP", "6": "CH_DP", "3": "CH_DM", "4": "CH_DM", "2": "GND", "5": "+5V"}, {}),
    ("U2", "Interface_USB", "CH340C", "CH340C", "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
     "C7464026", 152.4, 73.66,
     {"1": "GND", "2": "U0RXD", "3": "U0TXD", "4": "+3V3", "16": "+3V3",
      "5": "CH_DP", "6": "CH_DM", "13": "DTR", "14": "RTS",
      **nc_all(7, 8, 9, 10, 11, 12, 15)}, {}),
    ("C9", "Device", "C", "100nF", FP_C, "C14663", 182.88, 50.8, {"1": "+3V3", "2": "GND"}, {}),
    # --- auto-reset (esptool DTR/RTS) ------------------------------------
    ("R3", "Device", "R", "10k", FP_R, "C25804", 205.74, 63.5, {"1": "DTR", "2": "Q1_B"}, {}),
    ("Q1", "Transistor_BJT", "MMBT3904", "MMBT3904", "Package_TO_SOT_SMD:SOT-23",
     "C20526", 223.52, 71.12, {"1": "Q1_B", "2": "RTS", "3": "EN"}, {}),
    ("R4", "Device", "R", "10k", FP_R, "C25804", 205.74, 101.6, {"1": "RTS", "2": "Q2_B"}, {}),
    ("Q2", "Transistor_BJT", "MMBT3904", "MMBT3904", "Package_TO_SOT_SMD:SOT-23",
     "C20526", 223.52, 109.22, {"1": "Q2_B", "2": "DTR", "3": "IO0"}, {}),
    # --- power: 3.3 V regulator -------------------------------------------
    ("U5", "Regulator_Linear", "AP2112K-3.3", "AP2112K-3.3", "Package_TO_SOT_SMD:SOT-23-5",
     "C51118", 71.12, 205.74,
     {"1": "+5V", "3": "+5V", "2": "GND", "4": None, "5": "+3V3"}, {}),
    ("C1", "Device", "C", "1uF", FP_C, "C15849", 30.48, 205.74, {"1": "+5V", "2": "GND"}, {}),
    ("C2", "Device", "C", "10uF", FP_C, "C19702", 43.18, 205.74, {"1": "+5V", "2": "GND"}, {}),
    ("C3", "Device", "C", "1uF", FP_C, "C15849", 101.6, 205.74, {"1": "+3V3", "2": "GND"}, {}),
    ("C4", "Device", "C", "10uF", FP_C, "C19702", 114.3, 205.74, {"1": "+3V3", "2": "GND"}, {}),
    ("C5", "Device", "C", "100nF", FP_C, "C14663", 127.0, 205.74, {"1": "+3V3", "2": "GND"}, {}),
    # --- ESP32-S3 ------------------------------------------------------------
    ("U1", "RF_Module", "ESP32-S3-WROOM-1", "ESP32-S3-WROOM-1-N8", "RF_Module:ESP32-S3-WROOM-1",
     "C2913198", 284.48, 165.1, esp_nets, {}),
    ("R5", "Device", "R", "10k", FP_R, "C25804", 175.26, 160.02, {"1": "+3V3", "2": "EN"}, {}),
    ("C6", "Device", "C", "1uF", FP_C, "C15849", 187.96, 172.72, {"1": "EN", "2": "GND"}, {}),
    ("SW1", "Switch", "SW_Push", "RESET", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A",
     "C480267", 208.28, 172.72, {"1": "EN", "2": "GND"}, {}),
    ("R6", "Device", "R", "10k", FP_R, "C25804", 175.26, 205.74, {"1": "+3V3", "2": "IO0"}, {}),
    ("SW2", "Switch", "SW_Push", "BOOT", "Button_Switch_SMD:SW_Push_1P1T_XKB_TS-1187A",
     "C480267", 208.28, 218.44, {"1": "IO0", "2": "GND"}, {}),
    ("R7", "Device", "R", "1k", FP_R, "C21190", 342.9, 167.64, {"1": "+3V3", "2": "LED_A"}, {}),
    ("D1", "Device", "LED", "green", "LED_SMD:LED_0603_1608Metric", "C12624", 342.9, 187.96,
     {"2": "LED_A", "1": "LED_K"}, {}),
    ("J3", "Connector_Generic", "Conn_01x04", "UART: 3V3 TX RX GND",
     "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical", "", 360.68, 220.98,
     {"1": "+3V3", "2": "U0TXD", "3": "U0RXD", "4": "GND"}, {"dnp": True}),
    # --- USB-A host port for the keyboard ------------------------------------
    ("F1", "Device", "Polyfuse", "500mA", "Fuse:Fuse_1206_3216Metric", "C163512",
     317.5, 50.8, {"1": "+5V", "2": "VBUS_A"}, {}),
    ("C7", "Device", "C", "22uF", "Capacitor_SMD:C_0805_2012Metric", "C45783",
     332.74, 50.8, {"1": "VBUS_A", "2": "GND"}, {}),
    ("C8", "Device", "C", "100nF", FP_C, "C14663", 345.44, 50.8, {"1": "VBUS_A", "2": "GND"}, {}),
    ("U4", "Power_Protection", "USBLC6-2SC6", "USBLC6-2SC6", "Package_TO_SOT_SMD:SOT-23-6",
     "C7519", 330.2, 91.44,
     {"1": "HOST_DP", "6": "HOST_DP", "3": "HOST_DM", "4": "HOST_DM", "2": "GND", "5": "VBUS_A"}, {}),
    ("J2", "Connector", "USB_A", "USB-A (keyboard)",
     "Connector_USB:USB_A_Receptacle_XKB_U231-091N-4BLRA00-S", "C2880619", 381.0, 88.9,
     {"1": "VBUS_A", "2": "HOST_DM", "3": "HOST_DP", "4": "GND", "SH": "GND"}, {}),
    # --- power flags (ERC: nets fed only through passive pins) ---------------
    ("#FLG01", "power", "PWR_FLAG", "PWR_FLAG", "", "", 147.32, 251.46, {"1": "+5V"}, {}),
    ("#FLG02", "power", "PWR_FLAG", "PWR_FLAG", "", "", 160.02, 251.46, {"1": "GND"}, {}),
    ("#FLG03", "power", "PWR_FLAG", "PWR_FLAG", "", "", 172.72, 251.46, {"1": "VBUS_A"}, {}),
]

# Variant "usbc": the keyboard port is a USB-C receptacle acting as a power
# source (DFP). Rp = 56k from VBUS_A on each CC pin advertises default USB
# power; D+/D- of both plug orientations are joined.
VARIANT = sys.argv[2] if len(sys.argv) > 2 else ""
if VARIANT == "usbc":
    PARTS = [p for p in PARTS if p[0] != "J2"] + [
        ("J2", "Connector", "USB_C_Receptacle_USB2.0_16P", "USB-C (keyboard)",
         "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12", "C165948", 381.0, 88.9,
         {"A1": "GND", "B1": "GND", "A12": "GND", "B12": "GND", "SH": "GND",
          "A4": "VBUS_A", "B4": "VBUS_A", "A9": "VBUS_A", "B9": "VBUS_A",
          "A5": "KB_CC1", "B5": "KB_CC2", "A6": "HOST_DP", "B6": "HOST_DP",
          "A7": "HOST_DM", "B7": "HOST_DM", "A8": None, "B8": None}, {}),
        ("R8", "Device", "R", "56k", FP_R, "C23206", 360.68, 129.54, {"1": "VBUS_A", "2": "KB_CC1"}, {}),
        ("R9", "Device", "R", "56k", FP_R, "C23206", 373.38, 129.54, {"1": "VBUS_A", "2": "KB_CC2"}, {}),
    ]
elif VARIANT:
    sys.exit(f"unknown variant {VARIANT!r}")

NOTES = [
    (25.4, 30.48, "USB-C: power in, flashing and logs via CH340C (auto-reset like the Olimex board)"),
    (195.58, 45.72, "esptool auto-reset"),
    (63.5, 137.16, "U2 V3 tied to VCC: required when CH340C runs at 3.3 V (datasheet).\nERC flags it as two power outputs joined; exclude that marker."),
    (25.4, 185.42, "5 V -> 3.3 V"),
    (165.1, 147.32, "EN / BOOT"),
    (299.72, 30.48, "USB-A host port: keyboard on IO19/IO20 (native USB, nothing else on these lines)"),
    (330.2, 154.94, "Status LED, active-low on IO38 (matches BOARD_OLIMEX)"),
    (350.52, 236.22, "UART test header (not assembled)"),
]


if VARIANT == "usbc":
    NOTES = [(x, y, "USB-C host port: keyboard on IO19/IO20 (power source, 56k CC pull-ups)")
             if t.startswith("USB-A host port") else (x, y, t) for x, y, t in NOTES]


def u():
    return str(uuid.uuid4())


def effects(hide=False, justify=None, size=1.27):
    e = [Sym("effects"), [Sym("font"), [Sym("size"), size, size]]]
    if justify:
        e.append([Sym("justify")] + [Sym(j) for j in justify.split()])
    if hide:
        e.append([Sym("hide"), Sym("yes")])
    return e


def snap(v):
    return round(v / 1.27) * 1.27


lib_symbols = {}
items = []
pwr_count = [0]


def lib(libname, name):
    key = f"{libname}:{name}"
    if key not in lib_symbols:
        lib_symbols[key] = get_symbol(libname, name)
    return lib_symbols[key]


def place_symbol(ref, libname, name, value, fp, lcsc, x, y, extra):
    sym = lib(libname, name)
    props = {p[1]: p for p in find(sym, "property")}
    node = [Sym("symbol"), [Sym("lib_id"), f"{libname}:{name}"], [Sym("at"), x, y, 0],
            [Sym("unit"), 1], [Sym("exclude_from_sim"), Sym("no")],
            [Sym("in_bom"), Sym("no") if ref.startswith("#") else Sym("yes")],
            [Sym("on_board"), Sym("no") if ref.startswith("#") else Sym("yes")],
            [Sym("dnp"), Sym("yes") if extra.get("dnp") else Sym("no")],
            [Sym("uuid"), u()]]

    def prop(key, val, hide):
        lp = props.get(key)
        if lp is not None:
            at = first(lp, "at")
            px, py, pa = float(at[1]), float(at[2]), float(at[3]) if len(at) > 3 else 0
            lib_eff = first(lp, "effects")
            lib_hidden = lib_eff is not None and any(
                (isinstance(e, list) and e and e[0] == "hide" and (len(e) == 1 or e[1] == "yes"))
                or e == "hide" for e in lib_eff)
            just = first(lib_eff, "justify") if lib_eff else None
            jtxt = " ".join(str(j) for j in just[1:]) if just else None
        else:
            px, py, pa, lib_hidden, jtxt = 0, 0, 0, True, None
        node.append([Sym("property"), key, val, [Sym("at"), x + px, y - py, pa],
                     effects(hide=hide if hide is not None else lib_hidden, justify=jtxt)])

    prop("Reference", ref, True if ref.startswith("#") else False)
    prop("Value", value, False)
    prop("Footprint", fp, True)
    prop("Datasheet", props["Datasheet"][2] if "Datasheet" in props else "", True)
    prop("Description", props["Description"][2] if "Description" in props else "", True)
    if lcsc:
        prop("LCSC", lcsc, True)
    for pn in sorted({p[0] for p in pins(sym)}):
        node.append([Sym("pin"), pn, [Sym("uuid"), u()]])
    node.append([Sym("instances"), [Sym("project"), PROJECT,
                 [Sym("path"), f"/{ROOT}", [Sym("reference"), ref], [Sym("unit"), 1]]]])
    items.append(node)


def place_power(net, x, y, outward):
    pwr_count[0] += 1
    ref = f"#PWR{pwr_count[0]:02d}"
    name = POWER_NETS[net]
    if net == "GND":
        rot = {"down": 0, "up": 180, "right": 90, "left": 270}[outward]
    else:
        rot = {"up": 0, "down": 180, "left": 90, "right": 270}[outward]
    sym = lib("power", name)
    props = {p[1]: p for p in find(sym, "property")}
    vat = first(props["Value"], "at")
    # rotate the value text offset with the symbol (y-up offsets, CCW rotation)
    ox, oy = float(vat[1]), float(vat[2])
    r = math.radians(rot)
    rx, ry = ox * math.cos(r) - oy * math.sin(r), ox * math.sin(r) + oy * math.cos(r)
    node = [Sym("symbol"), [Sym("lib_id"), f"power:{name}"], [Sym("at"), x, y, rot],
            [Sym("unit"), 1], [Sym("exclude_from_sim"), Sym("no")], [Sym("in_bom"), Sym("yes")],
            [Sym("on_board"), Sym("yes")], [Sym("dnp"), Sym("no")], [Sym("uuid"), u()],
            [Sym("property"), "Reference", ref, [Sym("at"), x, y, 0], effects(hide=True)],
            [Sym("property"), "Value", name, [Sym("at"), x + rx, y - ry, 0], effects()],
            [Sym("property"), "Footprint", "", [Sym("at"), x, y, 0], effects(hide=True)],
            [Sym("property"), "Datasheet", "", [Sym("at"), x, y, 0], effects(hide=True)],
            [Sym("pin"), "1", [Sym("uuid"), u()]],
            [Sym("instances"), [Sym("project"), PROJECT,
             [Sym("path"), f"/{ROOT}", [Sym("reference"), ref], [Sym("unit"), 1]]]]]
    items.append(node)


def wire(x1, y1, x2, y2):
    items.append([Sym("wire"), [Sym("pts"), [Sym("xy"), x1, y1], [Sym("xy"), x2, y2]],
                  [Sym("stroke"), [Sym("width"), 0], [Sym("type"), Sym("default")]],
                  [Sym("uuid"), u()]])


def label(net, x, y, outward):
    ang = {"right": 0, "up": 90, "left": 180, "down": 270}[outward]
    just = "left bottom" if ang in (0, 90) else "right bottom"
    items.append([Sym("label"), net, [Sym("at"), x, y, ang],
                  [Sym("fields_autoplaced"), Sym("yes")], effects(justify=just),
                  [Sym("uuid"), u()]])


def no_connect(x, y):
    items.append([Sym("no_connect"), [Sym("at"), x, y], [Sym("uuid"), u()]])


errors = []
for ref, libname, name, value, fp, lcsc, x, y, nets, extra in PARTS:
    x, y = snap(x), snap(y)
    sym = lib(libname, name)
    plist = pins(sym)
    pin_numbers = {p[0] for p in plist}
    missing = pin_numbers - set(nets)
    unknown = set(nets) - pin_numbers
    if missing or unknown:
        errors.append(f"{ref}: missing pins {sorted(missing)} unknown pins {sorted(unknown)}")
        continue
    place_symbol(ref, libname, name, value, fp, lcsc, x, y, extra)
    seen = {}
    for num, pname, ptype, px, py, pa, plen, unit in plist:
        net = nets[num]
        ex, ey = round(x + px, 4), round(y - py, 4)
        key = (ex, ey)
        if key in seen:
            if seen[key] != net:
                errors.append(f"{ref}: stacked pins at {key} on different nets {seen[key]} / {net}")
            continue
        seen[key] = net
        if net is None:
            no_connect(ex, ey)
            continue
        a = math.radians(pa)
        dx, dy = -round(math.cos(a)), round(math.sin(a))
        outward = {(1, 0): "right", (-1, 0): "left", (0, -1): "up", (0, 1): "down"}[(dx, dy)]
        sx, sy = round(ex + dx * STUB, 4), round(ey + dy * STUB, 4)
        wire(ex, ey, sx, sy)
        if net in POWER_NETS:
            place_power(net, sx, sy, outward)
        else:
            label(net, sx, sy, outward)

if errors:
    print("\n".join(errors))
    sys.exit(1)

for x, y, text in NOTES:
    items.append([Sym("text"), text, [Sym("exclude_from_sim"), Sym("no")],
                  [Sym("at"), x, y, 0], effects(size=1.778, justify="left bottom"),
                  [Sym("uuid"), u()]])

doc = [Sym("kicad_sch"), [Sym("version"), 20231120], [Sym("generator"), "eeschema"],
       [Sym("generator_version"), "8.0"], [Sym("uuid"), ROOT], [Sym("paper"), "A3"],
       [Sym("title_block"), [Sym("title"), "keyhop: USB keyboard to BLE"],
        [Sym("date"), date.today().isoformat()], [Sym("rev"), "0.1"],
        [Sym("comment"), 1, "Generated from hardware/DESIGN.md; edit in KiCad from here on"]],
       [Sym("lib_symbols")] + list(lib_symbols.values())]
doc += items
doc.append([Sym("sheet_instances"), [Sym("path"), "/", [Sym("page"), "1"]]])

with open(OUT, "w") as f:
    f.write(dump(doc) + "\n")
print(f"wrote {OUT}: {len(PARTS)} parts, {len(items)} items")
