"""Build hardware/keyhop.kicad_pcb from the schematic netlist: footprints, nets,
placement, outline, net classes. Run with KiCad's bundled Python.

usage: build_pcb.py <netlist.net> <out.kicad_pcb> [usbc]
"""
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import find, first, parse  # noqa: E402

NETLIST, OUT = sys.argv[1], sys.argv[2]
VARIANT = sys.argv[3] if len(sys.argv) > 3 else ""
FPLIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"

X0, Y0, W, H = 100.0, 100.0, 60.0, 35.0  # board outline, mm

# ref: (x, y, rotation_deg). Rotation is KiCad's (counter-clockwise on screen).
PLACE = {
    # ESP32 module: antenna flush with the top edge, keep-out mostly off-board
    "U1": (130.0, 112.75, 0),
    # left: USB-C, ESD, CH340C, auto-reset
    "J1": (104.3, 120.0, 270),
    "R1": (103.5, 112.0, 0),
    "R2": (103.5, 128.0, 0),
    "U3": (112.0, 113.0, 0),
    "U2": (116.4, 123.0, 0),
    "C9": (112.0, 117.2, 0),
    "Q1": (109.5, 108.6, 0),
    "Q2": (114.5, 108.6, 0),
    "R3": (118.6, 108.0, 90),
    "R4": (118.6, 112.3, 90),
    # bottom-left: regulator and its capacitors
    "U5": (104.0, 132.0, 0),
    "C1": (108.4, 130.6, 0),
    "C2": (108.4, 133.0, 0),
    "C3": (112.2, 130.6, 0),
    "C4": (112.2, 133.0, 0),
    "C5": (116.0, 133.0, 0),
    # under the module: EN / BOOT
    "SW1": (124.6, 131.4, 0),
    "SW2": (135.4, 131.4, 0),
    "R5": (130.0, 128.2, 0),
    "C6": (130.0, 130.4, 0),
    "R6": (130.0, 132.6, 0),
    # right: USB-A host port
    "J2": (153.6, 120.0, 90),
    "F1": (142.6, 108.6, 0),
    "C7": (147.4, 108.6, 0),
    "C8": (151.0, 108.6, 0),
    "U4": (142.4, 120.0, 90),
    # bottom-right: LED and the (unassembled) UART header
    "R7": (142.0, 131.2, 0),
    "D1": (142.0, 133.4, 180),
    "J3": (148.0, 132.6, 90),
}

FOOTPRINT_OVERRIDES = {}

if VARIANT == "usbc":
    # keyboard port is a USB-C receptacle mirrored from J1 onto the right edge
    PLACE.update({
        "J2": (155.7, 120.0, 90),
        "U4": (146.5, 120.0, 90),
        "R8": (156.5, 112.0, 0),
        "R9": (156.5, 128.0, 0),
    })
elif VARIANT:
    sys.exit(f"unknown variant {VARIANT!r}")

# Net classes: power nets get wider tracks.
POWER_NETS = {"GND", "+5V", "+3V3", "VBUS_A"}


def mm(v):
    return pcbnew.FromMM(v)


def main():
    net = parse(open(NETLIST).read())
    comps = find(first(net, "components"), "comp")
    nets = find(first(net, "nets"), "net")

    board = pcbnew.NewBoard(OUT)  # also creates the matching .kicad_pro
    ds = board.GetDesignSettings()
    ds.SetCopperLayerCount(2)

    # outline
    rect = pcbnew.PCB_SHAPE(board)
    rect.SetShape(pcbnew.SHAPE_T_RECT)
    rect.SetStart(pcbnew.VECTOR2I(mm(X0), mm(Y0)))
    rect.SetEnd(pcbnew.VECTOR2I(mm(X0 + W), mm(Y0 + H)))
    rect.SetLayer(pcbnew.Edge_Cuts)
    rect.SetWidth(mm(0.05))
    board.Add(rect)

    # nets
    netinfo = {}
    for n in nets:
        name = first(n, "name")[1]
        clean = name.lstrip("/")
        ni = pcbnew.NETINFO_ITEM(board, clean)
        board.Add(ni)
        netinfo[name] = ni

    pad_net = {}
    for n in nets:
        name = first(n, "name")[1]
        for node in find(n, "node"):
            pad_net[(first(node, "ref")[1], first(node, "pin")[1])] = netinfo[name]

    for c in comps:
        ref = first(c, "ref")[1]
        value = first(c, "value")[1]
        fpid = first(c, "footprint")[1] if first(c, "footprint") else ""
        if not fpid:
            continue
        lib, name = fpid.split(":")
        fp = pcbnew.FootprintLoad(f"{FPLIB}/{lib}.pretty", name)
        fp.SetFPIDAsString(fpid)
        fp.SetReference(ref)
        fp.SetValue(value)
        # link to the schematic symbol so "Update PCB from Schematic" keeps working
        tstamps = first(c, "tstamps")
        sheet = first(c, "sheetpath")
        if tstamps is not None:
            path = (first(sheet, "tstamps")[1] if sheet is not None else "/") + tstamps[1]
            fp.SetPath(pcbnew.KIID_PATH(path))
        x, y, rot = PLACE[ref]
        board.Add(fp)
        fp.SetPosition(pcbnew.VECTOR2I(mm(x), mm(y)))
        fp.SetOrientationDegrees(rot)
        for pad in fp.Pads():
            key = (ref, pad.GetNumber())
            if key in pad_net:
                pad.SetNet(pad_net[key])
        if ref == "U1":
            # thermal vias in the GND pad: 0.2 mm -> 0.3 mm (JLCPCB standard minimum)
            for pad in fp.Pads():
                if 0 < pad.GetDrillSize().x < mm(0.3):
                    pad.SetDrillSize(pcbnew.VECTOR2I(mm(0.3), mm(0.3)))
        if ref == "J3":
            fp.SetDNP(True)
            fp.SetExcludedFromPosFiles(True)
            fp.SetExcludedFromBOM(False)

    # net classes
    ns = ds.m_NetSettings
    power = pcbnew.NETCLASS("Power")
    power.SetTrackWidth(mm(0.5))
    power.SetClearance(mm(0.2))
    power.SetViaDiameter(mm(0.8))
    power.SetViaDrill(mm(0.4))
    ns.SetNetclass("Power", power)
    default = ns.GetDefaultNetclass()
    default.SetTrackWidth(mm(0.25))
    default.SetClearance(mm(0.2))
    default.SetViaDiameter(mm(0.6))
    default.SetViaDrill(mm(0.3))
    for name in POWER_NETS:
        ns.SetNetclassPatternAssignment(name, "Power")

    # small silkscreen title
    txt = pcbnew.PCB_TEXT(board)
    txt.SetText("keyhop v0.1")
    txt.SetLayer(pcbnew.F_SilkS)
    txt.SetPosition(pcbnew.VECTOR2I(mm(107.0), mm(103.2)))
    txt.SetTextSize(pcbnew.VECTOR2I(mm(1.0), mm(1.0)))
    txt.SetTextThickness(mm(0.15))
    board.Add(txt)

    # JLCPCB 2-layer capabilities (0.127 mm track, 0.3 mm hole, 0.3 mm to edge), set with margin
    ds.m_TrackMinWidth = mm(0.15)
    ds.m_CopperEdgeClearance = mm(0.3)
    ds.m_MinThroughDrill = mm(0.3)
    ds.m_ViasMinSize = mm(0.6)
    # SaveBoard also writes the .kicad_pro, where KiCad keeps net classes and rules
    pcbnew.SaveBoard(OUT, board)
    print("saved", OUT, "footprints:", len(board.GetFootprints()), "nets:", board.GetNetCount())


main()
