"""Set JLCPCB-capability design rules, solid-connect J1 to the ground pour,
refill zones, and report track widths per net.

usage: finish.py <in.kicad_pcb> <out.kicad_pcb>
"""
import collections
import sys

import pcbnew


def mm(v):
    return pcbnew.FromMM(v)


b = pcbnew.LoadBoard(sys.argv[1])
ds = b.GetDesignSettings()
# JLCPCB 2-layer standard capabilities: 0.127 mm track/space, 0.3 mm hole,
# 0.3 mm copper to routed edge. Rules are set slightly above those.
ds.m_TrackMinWidth = mm(0.15)
ds.m_CopperEdgeClearance = mm(0.3)
ds.m_MinThroughDrill = mm(0.3)
ds.m_ViasMinSize = mm(0.6)

j1 = b.FindFootprintByReference("J1")
j1.SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)
b.FindFootprintByReference("J2").SetLocalZoneConnection(pcbnew.ZONE_CONNECTION_FULL)  # USB-A shield tabs

# silkscreen tidy: R5/C6/R6 sit in a 3 mm gap with no room for labels
for ref in ("R5", "C6", "R6"):
    b.FindFootprintByReference(ref).Reference().SetVisible(False)
d1 = b.FindFootprintByReference("D1")
d1.Reference().SetPosition(pcbnew.VECTOR2I(mm(138.6), mm(133.4)))
d1.Reference().SetTextAngleDegrees(0)

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(sys.argv[2], b)

widths = collections.defaultdict(collections.Counter)
vias = 0
for t in b.GetTracks():
    if t.GetClass() == "PCB_VIA":
        vias += 1
        continue
    widths[t.GetNetname()][round(pcbnew.ToMM(t.GetWidth()), 3)] += round(pcbnew.ToMM(t.GetLength()), 2)
for net in ("GND", "+5V", "+3V3", "VBUS_A", "HOST_DP", "HOST_DM", "CH_DP", "CH_DM"):
    print(f"{net:8s}", {w: round(l, 1) for w, l in sorted(widths[net].items())}, "(width mm: total length mm)")
print("vias:", vias)
