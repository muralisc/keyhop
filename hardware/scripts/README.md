# PCB helper scripts

These scripts produced board v0.1. **The KiCad files in `hardware/` are the source of truth now.** Edit them in KiCad. Rerun a script only if you mean to regenerate that stage.

All paths in the scripts assume KiCad 10 on macOS (`/Applications/KiCad/KiCad.app/...`). On Linux, change `LIB` in `sexp.py` and `FPLIB` in `build_pcb.py` to your KiCad share directory (usually `/usr/share/kicad/symbols` and `/usr/share/kicad/footprints`).

| Script | Python | What it does |
|---|---|---|
| `sexp.py` | any | Small KiCad S-expression parser and printer, plus symbol-library helpers. Used by the others. |
| `gen_sch.py` | system `python3 -I` | Generates `keyhop.kicad_sch` from the part and net list inside it. **Overwrites the schematic.** Use it only to start over. Run `kicad-cli sch upgrade` afterwards. |
| `annotate_sch.py` | system `python3 -I` | Adds the plain-English notes (text starting with "•") to the schematic. Safe to rerun: it replaces its own notes. Connectivity is untouched. |
| `build_pcb.py` | KiCad's bundled Python | Builds a placed but unrouted board from a netlist: footprints, nets, placement table, outline, net classes, rules. |
| `route.py` | KiCad's bundled Python | `export` writes the Specctra `.dsn` for Freerouting, `import` reads back the `.ses`, and `pour` adds GND zones on both layers. |
| `finish.py` | KiCad's bundled Python | JLCPCB rules, solid zone connection for J1/J2, label tidy, zone refill. Prints track widths per net. |
| `fix_parity.py` | KiCad's bundled Python | Restores the leading `/` on local net names and copies LCSC/Datasheet/Description fields from the netlist onto footprints, so DRC's schematic-parity check passes. Hide those fields afterwards (see HANDOVER.md). |
| `render_copy.py` | KiCad's bundled Python | Makes a render-only board copy with stand-in 3D models for J1 and J2. |

KiCad's bundled Python on macOS: `/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3`.

## Full pipeline used for v0.1

```sh
K=kicad-cli   # /Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli on macOS
PY=<KiCad bundled python3>
$K sch export netlist --format kicadsexpr -o net.net keyhop.kicad_sch
$PY build_pcb.py net.net work.kicad_pcb            # also writes work.kicad_pro
$PY route.py export work.kicad_pcb work.dsn
java -jar freerouting-2.5.0.jar -de work.dsn -do work.ses -mp 30 --gui.enabled=false
cp work.kicad_pro routed.kicad_pro; cp work.kicad_pro poured.kicad_pro; cp work.kicad_pro final.kicad_pro
$PY route.py import work.kicad_pcb work.ses routed.kicad_pcb
$PY route.py pour routed.kicad_pcb poured.kicad_pcb
$PY finish.py poured.kicad_pcb final.kicad_pcb
# copy final.kicad_pcb -> keyhop.kicad_pcb, work.kicad_pro -> keyhop.kicad_pro (fix meta.filename)
$PY fix_parity.py net.net keyhop.kicad_pcb
$K pcb drc --schematic-parity --severity-all -o drc.rpt keyhop.kicad_pcb
```

Freerouting 2.5.0 comes from github.com/freerouting/freerouting releases and needs Java (`brew install openjdk`). Check the jar's SHA-256 against GitHub's asset digest (`gh api repos/freerouting/freerouting/releases/latest --jq '.assets[].digest'`). In Claude Code, the permission system blocks Claude from running the downloaded jar, so the user runs it with a `!` command.
