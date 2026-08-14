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
C4 entities (id on the wrapper, geometry/style on the inner <mxCell>). Children
of containers store geometry relative to the parent; absolute positions are
resolved by walking the parent chain (waypoints of container-parented edges too).
A page whose payload is compressed (base64 text, no <mxGraphModel>) is an ERROR,
not a pass — decompress first (drawio -x -f xml, or untick File > Properties >
Compressed in the app).

  - Boxes with fillColor=none (C4 boundaries/containers) are NOT obstacles —
    edges are allowed to cross a boundary. Pure text cells and tiny marks
    (legend swatches) are skipped too.
  - PINNED edges (every consecutive route point axis-aligned with the next, i.e.
    you supplied waypoints) get an EXACT verdict.
  - AUTO-ROUTED edges (a non-axis-aligned bend the router resolves) get a
    conservative WARN listing boxes that *a* plausible route crosses — pin the
    edge with waypoints to turn the WARN into a definite yes/no.
  - STRAIGHT edges (no edgeStyle — draw.io's default) render as straight
    polylines, diagonals included, so their segments are intersected exactly
    (Liang-Barsky) -> definite verdicts. curved=1 is approximated by its chord
    and only WARNs.
  - ARROWHEAD orientation (Problem 9): a waypointed edge whose last waypoint isn't
    aligned with a fixed entry point gets a conservative ARROW flag — its arrowhead
    may graze ALONG the target's border instead of pointing in. Drop the fixed
    entryX/entryY (perimeter auto-attach) or align the waypoint. Heuristic on raw
    geometry — confirm flagged edges in the PNG. (Skipped for straight edges,
    which legitimately approach at an angle.)
  - LABEL collisions (Problems 1/3/4/8): every edge label's box is estimated —
    position from the label geometry's relative x along the route, perpendicular
    y, and offset point (sign convention verified by render: on a left-to-right
    edge, negative y sits BELOW the line); size from character count x fontSize
    (default 12). A label overlapping an unrelated box or another edge label gets
    an advisory LABEL line. Text metrics are estimates — confirm in the PNG.

Usage
-----
  python3 check-overlaps.py file1.drawio [file2.drawio ...]

Exit code 0 if no DEFINITE crossings (WARNs/ARROWs/LABELs allowed), 1 otherwise.
Operates on uncompressed .drawio XML (what these skills write).
"""
import html
import re
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


def plain_text(v):
    """HTML label -> plain text ('<b>Load API</b>&amp;<br>daily' -> 'Load API&\\ndaily')."""
    v = re.sub(r"<br\s*/?>|</div>|</p>", "\n", v or "", flags=re.I)
    v = re.sub(r"<[^>]+>", "", v)
    return html.unescape(v).strip()


def snip(s, n=18):
    s = s.split("\n")[0]
    return s if len(s) <= n else s[:n] + "…"


def edge_kind(st):
    es = st.get("edgeStyle")
    if es in (None, "none"):
        return "straight"        # draw.io's default edge: straight polyline
    if es == "orthogonalEdgeStyle":
        return "orthogonal"
    return "other"               # elbow/entityRelation/... — kept on the orthogonal approximation


def offset_point(geo):
    if geo is not None:
        for p in geo.findall("mxPoint"):
            if p.get("as") == "offset":
                return float(p.get("x") or 0), float(p.get("y") or 0)
    return 0.0, 0.0


def collect(diagram):
    """Return (vertices, edges, labels) for one page, coordinates resolved to absolute.

    A cell parented to a container stores geometry RELATIVE to that container;
    absolute positions come from summing the parent chain's origins (a layer has
    no geometry and contributes nothing). Applies to edge waypoints as well.

    Labels are an edge cell's own value plus edgeLabel child cells (vertex=1,
    relative geometry, parented to the edge); each carries the plain text,
    fontSize, and the placement triple (relative x, perpendicular y, offset)."""
    if diagram.tag == "mxGraphModel":
        model = diagram
    else:
        model = diagram.find(".//mxGraphModel")
    root = (model if model is not None else diagram).find("root")
    verts, edges, labels = {}, [], []
    if root is None:
        return verts, edges, labels
    raw, raw_edges, pending_labels = {}, [], []
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
        parent = cell.get("parent")
        value = child.get("label") if child.tag in ("object", "UserObject") else None
        value = plain_text(value or cell.get("value") or "")
        if cell.get("vertex") == "1" and geo is not None and geo.get("width"):
            if geo.get("relative") != "1":
                raw[cid] = dict(parent=parent, x=float(geo.get("x", 0)), y=float(geo.get("y", 0)),
                                w=float(geo.get("width")), h=float(geo.get("height")), style=st)
        if cell.get("vertex") == "1" and geo is not None and geo.get("relative") == "1" and value:
            # edgeLabel child cell — resolved to its edge after the loop
            pending_labels.append(dict(parent=parent, text=value,
                                       fs=float(st.get("fontSize") or 12),
                                       x_rel=float(geo.get("x") or 0),
                                       y_off=float(geo.get("y") or 0),
                                       off=offset_point(geo)))
        if cell.get("edge") == "1":
            pts = []
            if geo is not None:
                arr = geo.find("Array")
                if arr is not None:
                    pts = [(float(p.get("x")), float(p.get("y"))) for p in arr.findall("mxPoint")]
            raw_edges.append(dict(id=cid or "?", src=cell.get("source"), tgt=cell.get("target"),
                                  style=st, pts=pts, parent=parent))
            if value:
                labels.append(dict(edge=cid or "?", text=value,
                                   fs=float(st.get("fontSize") or 12),
                                   x_rel=float(geo.get("x") or 0) if geo is not None else 0.0,
                                   y_off=float(geo.get("y") or 0) if geo is not None else 0.0,
                                   off=offset_point(geo)))

    def offset(pid, seen=()):
        """Absolute origin contributed by parent chain above cell id `pid`."""
        if pid not in raw or pid in seen:
            return 0.0, 0.0
        ox, oy = offset(raw[pid]["parent"], seen + (pid,))
        return ox + raw[pid]["x"], oy + raw[pid]["y"]

    for cid, r in raw.items():
        ox, oy = offset(r["parent"])
        verts[cid] = dict(x=r["x"] + ox, y=r["y"] + oy, w=r["w"], h=r["h"], style=r["style"])
    edge_ids = {e["id"] for e in raw_edges}
    for lab in pending_labels:
        if lab["parent"] in edge_ids:
            lab["edge"] = lab.pop("parent")
            labels.append(lab)
    for e in raw_edges:
        ox, oy = offset(e.pop("parent"))
        e["pts"] = [(px + ox, py + oy) for px, py in e["pts"]]
        edges.append(e)
    return verts, edges, labels


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


def seg_hits_rect(p, q, rect, pad=2):
    """True if segment p->q passes through rect's interior (shrunk by pad).
    Handles arbitrary (diagonal) segments — Liang-Barsky clipping."""
    x0, y0, x1, y1 = rect[0] + pad, rect[1] + pad, rect[2] - pad, rect[3] - pad
    if x1 <= x0 or y1 <= y0:
        return False
    dx, dy = q[0] - p[0], q[1] - p[1]
    t0, t1 = 0.0, 1.0
    for pv, qv in ((-dx, p[0] - x0), (dx, x1 - p[0]), (-dy, p[1] - y0), (dy, y1 - p[1])):
        if abs(pv) < 1e-9:
            if qv < 0:
                return False
            continue
        t = qv / pv
        if pv < 0:
            if t > t0:
                t0 = t
        elif t < t1:
            t1 = t
        if t0 > t1:
            return False
    return (t1 - t0) > 1e-6


def edge_route(e, verts):
    """[start] + waypoints + [end], or None when either terminal is unresolvable."""
    s, t = verts.get(e["src"]), verts.get(e["tgt"])
    if not s or not t:
        return None
    st = e["style"]
    start = conn(s, float(st.get("exitX", 0.5)), float(st.get("exitY", 0.5)))
    end = conn(t, float(st.get("entryX", 0.5)), float(st.get("entryY", 0.5)))
    return [start] + e["pts"] + [end]


def check_page(verts, edges):
    obs = {cid: (v["x"], v["y"], v["x"] + v["w"], v["y"] + v["h"])
           for cid, v in verts.items() if is_obstacle(v)}
    out = []
    for e in edges:
        route = edge_route(e, verts)
        if route is None:
            continue
        st = e["style"]
        kind = edge_kind(st)
        curved = str(st.get("curved", "")) == "1"
        excl = {e["src"], e["tgt"]}
        definite, potential = set(), set()
        for i in range(len(route) - 1):
            a, b = route[i], route[i + 1]
            if kind == "straight":
                # the rendered line IS this segment (exact) — unless curved,
                # where the chord only approximates the bend
                crossed = set(cid for cid, r in obs.items()
                              if cid not in excl and seg_hits_rect(a, b, r))
                (potential if curved else definite).update(crossed)
            else:
                cand = candidates(a, b)
                per = [set(cid for cid, r in obs.items()
                           if cid not in excl and any(hits(p, q, r) for p, q in c)) for c in cand]
                if len(per) == 1:
                    definite |= per[0]
                else:
                    definite |= (per[0] & per[1])
                    potential |= (per[0] | per[1])
        potential -= definite
        if definite or potential:
            out.append((e["id"], sorted(definite), sorted(potential), kind, curved))
    return out


def route_point(route, frac):
    """Point and unit direction at `frac` (0..1) of the polyline's length."""
    segs = [(a, b) for a, b in zip(route, route[1:])]
    lens = [((b[0] - a[0]) ** 2 + (b[1] - a[1]) ** 2) ** 0.5 for a, b in segs]
    total = sum(lens)
    if total <= 0:
        return None
    remaining = max(0.0, min(1.0, frac)) * total
    last = None
    for (a, b), ln in zip(segs, lens):
        if ln <= 0:
            continue
        last = (a, b, ln)
        if remaining <= ln:
            t = remaining / ln
            return ((a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1])),
                    ((b[0] - a[0]) / ln, (b[1] - a[1]) / ln))
        remaining -= ln
    a, b, ln = last
    return (b, ((b[0] - a[0]) / ln, (b[1] - a[1]) / ln))


def label_bbox(lab, route):
    """Estimated label rectangle: centre from the placement triple, size from
    character count x fontSize. Estimates — collisions are advisory only."""
    rp = route_point(route, (lab["x_rel"] + 1) / 2)
    if rp is None:
        return None
    (px, py), (ux, uy) = rp
    nx, ny = uy, -ux    # verified: negative geometry y sits BELOW a left-to-right edge
    cx = px + nx * lab["y_off"] + lab["off"][0]
    cy = py + ny * lab["y_off"] + lab["off"][1]
    lines = [l for l in lab["text"].split("\n") if l] or [""]
    w = 0.55 * lab["fs"] * max(len(l) for l in lines)
    h = 1.3 * lab["fs"] * len(lines)
    return (cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)


def rects_overlap(a, b, min_pen=3):
    """Overlap with real penetration on both axes — grazes don't count."""
    return (min(a[2], b[2]) - max(a[0], b[0]) > min_pen
            and min(a[3], b[3]) - max(a[1], b[1]) > min_pen)


def check_labels(verts, edges, labels):
    """Flag estimated label boxes that land on an unrelated vertex (Problems 1/8)
    or on another edge label (Problems 3/4). Advisory — text metrics are estimates."""
    obs = {cid: (v["x"], v["y"], v["x"] + v["w"], v["y"] + v["h"])
           for cid, v in verts.items() if is_obstacle(v)}
    by_id = {e["id"]: e for e in edges}
    placed = []
    for lab in labels:
        e = by_id.get(lab["edge"])
        if not e:
            continue
        route = edge_route(e, verts)
        if route is None:
            continue
        bb = label_bbox(lab, route)
        if bb:
            placed.append((lab, bb, {e["src"], e["tgt"]}))
    on_box, pairs = [], []
    for lab, bb, excl in placed:
        for cid, r in obs.items():
            if cid not in excl and rects_overlap(bb, r):
                on_box.append((lab, cid))
    for i in range(len(placed)):
        for j in range(i + 1, len(placed)):
            if rects_overlap(placed[i][1], placed[j][1]):
                pairs.append((placed[i][0], placed[j][0]))
    return on_box, pairs


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
    pointing into the box (Problem 9). Only waypointed edges are checked: a
    no-waypoint edge auto-attaches perpendicular at the perimeter (verified). With a
    waypoint, the final segment is perpendicular only if that waypoint is aligned
    with the entry along the edge — same x for a top/bottom entry, same y for a
    left/right entry. Heuristic on raw geometry — confirm flagged edges in the PNG."""
    out = []
    for e in edges:
        if not e["pts"]:                 # no waypoints -> router attaches perpendicular
            continue
        if edge_kind(e["style"]) == "straight":
            continue                     # straight edges legitimately arrive at an angle
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
            page = d.get("name", "")
            tag = f"{name} [{page}]" if page else name
            if (d.tag == "diagram" and d.find(".//mxGraphModel") is None
                    and (d.text or "").strip()):
                clean = False
                failed = True
                print(f"ERROR  {tag}: page payload is compressed (base64, no <mxGraphModel>)"
                      f" — nothing was checked. Decompress first: drawio -x -f xml -o"
                      f" uncompressed.drawio {name} (or untick File > Properties >"
                      f" Compressed in the app), then re-run.")
                continue
            verts, edges, labels = collect(d)
            for eid, definite, potential, kind, curved in check_page(verts, edges):
                clean = False
                if definite:
                    failed = True
                    print(f"ISSUE  {tag}: edge '{eid}' routes THROUGH {', '.join(definite)}")
                if potential:
                    why = ("curved edge approximated by its chord — confirm in PNG"
                           if kind == "straight" and curved
                           else "auto-routed — pin with waypoints to confirm")
                    print(f"WARN   {tag}: edge '{eid}' may cross {', '.join(potential)} ({why})")
            for eid, side in check_arrows(verts, edges):
                clean = False
                print(f"ARROW  {tag}: edge '{eid}' may hit the {side} edge sideways "
                      f"(fixed entry vs approach — see Problem 9; confirm in PNG)")
            on_box, pairs = check_labels(verts, edges, labels)
            for lab, cid in on_box:
                clean = False
                print(f"LABEL  {tag}: label '{snip(lab['text'])}' of edge '{lab['edge']}' "
                      f"sits on '{cid}' (estimated from text metrics — confirm in PNG)")
            for la, lb in pairs:
                clean = False
                print(f"LABEL  {tag}: labels '{snip(la['text'])}' (edge '{la['edge']}') and "
                      f"'{snip(lb['text'])}' (edge '{lb['edge']}') overlap "
                      f"(estimated — confirm in PNG)")
        if clean:
            print(f"CLEAN  {name}")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1:]))
