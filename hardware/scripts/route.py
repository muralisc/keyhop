"""Specctra round trip and ground pours. Run with KiCad's bundled Python.

usage: route.py export <board> <out.dsn>
       route.py import <board> <in.ses> <out_board>
       route.py pour   <board> <out_board>
"""
import sys

import pcbnew


def mm(v):
    return pcbnew.FromMM(v)


cmd = sys.argv[1]
board = pcbnew.LoadBoard(sys.argv[2])

if cmd == "export":
    ok = pcbnew.ExportSpecctraDSN(board, sys.argv[3])
    print("export", ok)

elif cmd == "import":
    ok = pcbnew.ImportSpecctraSES(board, sys.argv[3])
    pcbnew.SaveBoard(sys.argv[4], board)
    print("import", ok, "tracks:", len(board.GetTracks()))

elif cmd == "pour":
    gnd = board.FindNet("GND")
    outline = board.GetBoardEdgesBoundingBox()
    inset = mm(0.3)
    for layer in (pcbnew.F_Cu, pcbnew.B_Cu):
        z = pcbnew.ZONE(board)
        z.SetLayer(layer)
        z.SetNet(gnd)
        z.SetLocalClearance(mm(0.25))
        z.SetMinThickness(mm(0.25))
        z.SetPadConnection(pcbnew.ZONE_CONNECTION_THERMAL)
        z.SetThermalReliefGap(mm(0.3))
        z.SetThermalReliefSpokeWidth(mm(0.4))
        z.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
        poly = z.Outline()
        poly.NewOutline()
        l, t = outline.GetLeft() + inset, outline.GetTop() + inset
        r, btm = outline.GetRight() - inset, outline.GetBottom() - inset
        for x, y in ((l, t), (r, t), (r, btm), (l, btm)):
            poly.Append(x, y)
        board.Add(z)
    filler = pcbnew.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcbnew.SaveBoard(sys.argv[3], board)
    print("poured", len(board.Zones()), "zones")
