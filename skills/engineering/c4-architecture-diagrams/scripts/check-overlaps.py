#!/usr/bin/env python3
"""check-overlaps.py — flag draw.io edges whose route passes through a box.

Why this exists
---------------
CLI export (drawio -x -> PNG/SVG/PDF) runs the plain orthogonal router: it
draws right-angle paths but does NOT route around boxes in the way. Whatever
route the raw XML implies is exactly what renders — so an auto-routed edge
whose path crosses an unrelated box is drawn straight through it, and a
midpoint label lands on whatever it overlaps. (Some interactive viewers apply
an extra pass that nudges edges off boxes; CLI export does not.) Eyeballing a
fit-to-page PNG misses these fine clips (a line grazing a tag corner is
invisible at zoom but obvious to the reader at 100%). This script is the
geometric gate the eye isn't.

What it does
------------
Reconstructs each edge's route from its exit/entry connection points + explicit
waypoints, then reports any straight segment that passes through an unrelated
box. Handles multi-page files (<diagram> tabs) and <object>/<UserObject>-wrapped
C4 entities (id on the wrapper, geometry/style on the inner <mxCell>).

  - Boxes with fillColor=none (C4 boundaries/containers) are NOT obstacles —
    edges are allowed to cross a boundary. Pure text cells and tiny marks
    (legend swatches) are skipped too.
  - PINNED edges (every consecutive route point axis-aligned with the next, i.e.
    you supplied waypoints) get an EXACT verdict.
  - AUTO-ROUTED edges (a non-axis-aligned bend the router resolves) get a
    conservative WARN listing boxes that *a* plausible route crosses — pin the
    edge with waypoints to turn the WARN into a definite yes/no.
  - ARROWHEAD orientation (Problem 11): a waypointed edge whose last waypoint isn't
    aligned with a fixed entry point gets a conservative ARROW flag — its arrowhead
    may graze ALONG the target's border instead of pointing in. Drop the fixed
    entryX/entryY (perimeter auto-attach) or align the waypoint. Heuristic on raw
    geometry — confirm flagged edges in the PNG.

Usage
-----
  python3 check-overlaps.py file1.drawio [file2.drawio ...]

Exit code 0 if no DEFINITE crossings (WARNs/ARROWs allowed), 1 otherwise.
Operates on uncompressed .drawio XML (what these skills write).
"""
import sys
import xml.etree.ElementTree as ET


def style_dict(s):
    d = {}
    for part in (s or "").split(";"):
        if "=" in part:
            k, v = part.split("=", 1)
            d[k] = v
        elif part:
            d[part] = True
    return d


def collect(diagram):
    """Return (vertices, edges) for one page."""
    if diagram.tag == "mxGraphModel":
        model = diagram
    else:
        model = diagram.find(".//mxGraphModel")
    root = (model if model is not None else diagram).find("root")
    verts, edges = {}, []
    if root is None:
        return verts, edges
    for child in root:
        if child.tag in ("object", "UserObject"):
            cid, cell = child.get("id"), child.find("mxCell")
        elif child.tag == "mxCell":
            cid, cell = child.get("id"), child
        else:
            continue
        if cell is None:
            continue
        st = style_dict(cell.get("style"))
        geo = cell.find("mxGeometry")
        if cell.get("vertex") == "1" and geo is not None and geo.get("width"):
            verts[cid] = dict(x=float(geo.get("x", 0)), y=float(geo.get("y", 0)),
                              w=float(geo.get("width")), h=float(geo.get("height")), style=st)
        if cell.get("edge") == "1":
            pts = []
            if geo is not None:
                arr = geo.find("Array")
                if arr is not None:
                    pts = [(float(p.get("x")), float(p.get("y"))) for p in arr.findall("mxPoint")]
            edges.append(dict(id=cid or "?", src=cell.get("source"), tgt=cell.get("target"),
                              style=st, pts=pts))
    return verts, edges


def is_obstacle(v):
    st = v["style"]
    if any(k.startswith("text") for k in st):          # text;... labels
        return False
    if str(st.get("fillColor", "")).lower() == "none":  # boundary / container
        return False
    if v["w"] < 60 or v["h"] < 28:                      # legend swatches / marks
        return False
    return True


def conn(v, fx, fy):
    return (v["x"] + fx * v["w"], v["y"] + fy * v["h"])


def hits(p, q, rect, pad=2):
    x0, y0, x1, y1 = rect[0] + pad, rect[1] + pad, rect[2] - pad, rect[3] - pad
    if x1 <= x0 or y1 <= y0:
        return False
    if abs(p[1] - q[1]) < 0.5:                          # horizontal segment
        if not (y0 < p[1] < y1):
            return False
        return min(p[0], q[0]) < x1 and max(p[0], q[0]) > x0
    if abs(p[0] - q[0]) < 0.5:                          # vertical segment
        if not (x0 < p[0] < x1):
            return False
        return min(p[1], q[1]) < y1 and max(p[1], q[1]) > y0
    return False                                        # diagonal: handled by caller


def candidates(a, b):
    """Axis-aligned segment lists connecting a->b (1 if already aligned, else 2 L's)."""
    if abs(a[0] - b[0]) < 0.5 or abs(a[1] - b[1]) < 0.5:
        return [[(a, b)]]
    return [[(a, (b[0], a[1])), ((b[0], a[1]), b)],     # horizontal-first
            [(a, (a[0], b[1])), ((a[0], b[1]), b)]]      # vertical-first


def check_page(verts, edges):
    obs = {cid: (v["x"], v["y"], v["x"] + v["w"], v["y"] + v["h"])
           for cid, v in verts.items() if is_obstacle(v)}
    out = []
    for e in edges:
        s, t = verts.get(e["src"]), verts.get(e["tgt"])
        if not s or not t:
            continue
        st = e["style"]
        start = conn(s, float(st.get("exitX", 0.5)), float(st.get("exitY", 0.5)))
        end = conn(t, float(st.get("entryX", 0.5)), float(st.get("entryY", 0.5)))
        route = [start] + e["pts"] + [end]
        excl = {e["src"], e["tgt"]}
        definite, potential = set(), set()
        for i in range(len(route) - 1):
            cand = candidates(route[i], route[i + 1])
            per = [set(cid for cid, r in obs.items()
                       if cid not in excl and any(hits(p, q, r) for p, q in c)) for c in cand]
            if len(per) == 1:
                definite |= per[0]
            else:
                definite |= (per[0] & per[1])
                potential |= (per[0] | per[1])
        potential -= definite
        if definite or potential:
            out.append((e["id"], sorted(definite), sorted(potential)))
    return out


def entry_side(st):
    """Which side a fixed entry point pins the arrow to, or None if not on a side."""
    try:
        ey = st.get("entryY")
        if ey is not None and abs(float(ey)) < 1e-6:
            return "top"
        if ey is not None and abs(float(ey) - 1) < 1e-6:
            return "bottom"
        ex = st.get("entryX")
        if ex is not None and abs(float(ex)) < 1e-6:
            return "left"
        if ex is not None and abs(float(ex) - 1) < 1e-6:
            return "right"
    except ValueError:
        pass
    return None


def check_arrows(verts, edges):
    """Flag edges where an explicit last waypoint forces the final segment PARALLEL
    to a fixed entry edge — the arrowhead then grazes ALONG the border instead of
    pointing into the box (Problem 11). Only waypointed edges are checked: a
    no-waypoint edge auto-attaches perpendicular at the perimeter (verified). With a
    waypoint, the final segment is perpendicular only if that waypoint is aligned
    with the entry along the edge — same x for a top/bottom entry, same y for a
    left/right entry. Heuristic on raw geometry — confirm flagged edges in the PNG."""
    out = []
    for e in edges:
        if not e["pts"]:                 # no waypoints -> router attaches perpendicular
            continue
        st = e["style"]
        side = entry_side(st)
        if side is None:
            continue
        t = verts.get(e["tgt"])
        if not t:
            continue
        end = conn(t, float(st.get("entryX", 0.5)), float(st.get("entryY", 0.5)))
        last = e["pts"][-1]
        if side in ("top", "bottom"):
            parallel = abs(last[0] - end[0]) > 2     # waypoint not directly above/below entry
        else:
            parallel = abs(last[1] - end[1]) > 2     # waypoint not level with entry
        if parallel:
            out.append((e["id"], side))
    return out


def main(paths):
    failed = False
    for path in paths:
        root = ET.parse(path).getroot()
        pages = root.findall("diagram") or [root]
        name = path.split("/")[-1]
        clean = True
        for d in pages:
            verts, edges = collect(d)
            page = d.get("name", "")
            tag = f"{name} [{page}]" if page else name
            for eid, definite, potential in check_page(verts, edges):
                clean = False
                if definite:
                    failed = True
                    print(f"ISSUE  {tag}: edge '{eid}' routes THROUGH {', '.join(definite)}")
                if potential:
                    print(f"WARN   {tag}: edge '{eid}' may cross {', '.join(potential)} "
                          f"(auto-routed — pin with waypoints to confirm)")
            for eid, side in check_arrows(verts, edges):
                clean = False
                print(f"ARROW  {tag}: edge '{eid}' may hit the {side} edge sideways "
                      f"(fixed entry vs approach — see Problem 11; confirm in PNG)")
        if clean:
            print(f"CLEAN  {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
