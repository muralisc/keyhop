"""Render-only copy: stand-in 3D models for parts the KiCad library has no model for."""
import sys
import pcbnew
M = "${KICAD10_3DMODEL_DIR}/Connector_USB.3dshapes/"
b = pcbnew.LoadBoard(sys.argv[1])
for ref, model, off in (
    ("J1", M + "USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal.step", (0.0, 0.025, 0.0)),
    ("J2", M + "USB_A_Molex_67643_Horizontal.step", (-3.5, 7.96, 0.0)),
):
    fp = b.FindFootprintByReference(ref)
    m = fp.Models()[0]
    m.m_Filename = model
    m.m_Offset = pcbnew.VECTOR3D(*off)
pcbnew.SaveBoard(sys.argv[2], b)
print("render copy saved")
