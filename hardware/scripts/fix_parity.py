"""Make the board match the schematic exactly: local net names keep their
leading '/', and symbol fields (LCSC, Datasheet, Description) are copied
onto footprints. Run with KiCad's bundled Python.

usage: fix_parity.py <netlist.net> <board.kicad_pcb>
"""
import json
import os
import sys

import pcbnew

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sexp import find, first, parse  # noqa: E402

net = parse(open(sys.argv[1]).read())
board_path = sys.argv[2]
b = pcbnew.LoadBoard(board_path)

sch_names = {first(n, "name")[1] for n in find(first(net, "nets"), "net")}
renamed = 0
for name, ni in list(b.GetNetsByName().items()):
    name = str(name)
    if name and name not in sch_names and "/" + name in sch_names:
        ni.SetNetname("/" + name)
        renamed += 1
b.BuildListOfNets()

fields_set = 0
for c in find(first(net, "components"), "comp"):
    ref = first(c, "ref")[1]
    fp = b.FindFootprintByReference(ref)
    if fp is None:
        continue
    wanted = {}
    ds = first(c, "datasheet")
    if ds is not None:
        wanted["Datasheet"] = ds[1]
    desc = first(c, "description")
    if desc is not None:
        wanted["Description"] = desc[1]
    fields = first(c, "fields")
    if fields is not None:
        for f in find(fields, "field"):
            fname = first(f, "name")[1]
            if fname in ("LCSC", "Datasheet"):
                wanted[fname] = f[2] if len(f) > 2 and not isinstance(f[2], list) else ""
    for key, val in wanted.items():
        fp.SetField(key, val)
        fields_set += 1

pcbnew.ZONE_FILLER(b).Fill(b.Zones())
pcbnew.SaveBoard(board_path, b)

# net-class pattern for the renamed local power net
pro = os.path.splitext(board_path)[0] + ".kicad_pro"
d = json.load(open(pro))
for p in d["net_settings"]["netclass_patterns"]:
    if p["pattern"] == "VBUS_A":
        p["pattern"] = "/VBUS_A"
json.dump(d, open(pro, "w"), indent=2)
print(f"renamed {renamed} nets, set {fields_set} fields")
