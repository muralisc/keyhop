"""Minimal KiCad S-expression parser/printer plus symbol-library helpers."""
import re

LIB = "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols"

_tok = re.compile(r'\s*(?:(\()|(\))|("(?:[^"\\]|\\.)*")|([^\s()"]+))')


class Sym(str):
    """Unquoted atom."""


def parse(text):
    pos, stack, cur = 0, [], []
    n = len(text)
    while pos < n:
        m = _tok.match(text, pos)
        if not m:
            if text[pos:].strip() == "":
                break
            raise ValueError("parse error at %d" % pos)
        pos = m.end()
        if m.group(1):
            stack.append(cur)
            cur = []
        elif m.group(2):
            done = cur
            cur = stack.pop()
            cur.append(done)
        elif m.group(3) is not None:
            s = m.group(3)[1:-1]
            cur.append(re.sub(r'\\(.)', lambda m: {"n": "\n", '"': '"', "\\": "\\"}.get(m.group(1), m.group(0)), s))
        else:
            cur.append(Sym(m.group(4)))
    return cur[0]


def dump(node, indent=0):
    if isinstance(node, list):
        if all(not isinstance(x, list) for x in node):
            return "(" + " ".join(dump(x) for x in node) + ")"
        out = "(" + " ".join(dump(x) for x in node if not isinstance(x, list))
        for x in node:
            if isinstance(x, list):
                out += "\n" + "\t" * (indent + 1) + dump(x, indent + 1)
        return out + "\n" + "\t" * indent + ")"
    if isinstance(node, Sym):
        return str(node)
    if isinstance(node, bool):
        return "yes" if node else "no"
    if isinstance(node, (int, float)):
        return fmt(node)
    return '"' + str(node).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def fmt(v):
    if isinstance(v, int):
        return str(v)
    s = ("%.4f" % v).rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s


def find(node, key):
    return [x for x in node if isinstance(x, list) and x and x[0] == key]


def first(node, key):
    r = find(node, key)
    return r[0] if r else None


_libcache = {}


def load_lib(name):
    if name not in _libcache:
        with open(f"{LIB}/{name}.kicad_sym") as f:
            _libcache[name] = parse(f.read())
    return _libcache[name]


def get_symbol(lib, name):
    """Return a flattened copy of lib:name (resolving 'extends'), renamed 'lib:name'."""
    import copy

    tree = load_lib(lib)
    syms = {s[1]: s for s in find(tree, "symbol")}
    s = copy.deepcopy(syms[name])
    ext = first(s, "extends")
    if ext:
        parent = get_symbol(lib, ext[1])
        child_props = {p[1]: p for p in find(s, "property")}
        flat = [Sym("symbol"), f"{lib}:{name}"]
        for item in parent[2:]:
            if isinstance(item, list) and item[0] == "property":
                flat.append(child_props.pop(item[1], item))
            elif isinstance(item, list) and item[0] == "symbol":
                sub = copy.deepcopy(item)
                pname = parent[1].split(":")[-1]
                sub[1] = sub[1].replace(pname, name, 1)
                flat.append(sub)
            else:
                flat.append(item)
        flat.extend(child_props.values())
        return flat
    s[1] = f"{lib}:{name}"
    for sub in find(s, "symbol"):
        pass
    return s


def pins(sym):
    """Yield (number, name, type, x, y, angle, length, unit) for every pin."""
    out = []
    for sub in find(sym, "symbol"):
        m = re.search(r"_(\d+)_(\d+)$", sub[1])
        unit = int(m.group(1)) if m else 0
        for p in find(sub, "pin"):
            at = first(p, "at")
            out.append(
                (
                    first(p, "number")[1],
                    first(p, "name")[1],
                    str(p[1]),
                    float(at[1]),
                    float(at[2]),
                    float(at[3]) if len(at) > 3 else 0.0,
                    float(first(p, "length")[1]),
                    unit,
                )
            )
    return out
