---
name: drawio-diagrams
description: Use when creating, editing, or cleaning up any draw.io diagram (.drawio file) — including C4 views (context, container, component) — or when an existing diagram renders with overlapping labels, edges crossing boxes, or unreadable text. Covers layout craft and verification: edge routing that keeps labels readable, multi-page files, a geometric overlap checker, and a render-and-inspect gate before claiming done. Layout and verification only — not XML basics or CLI export mechanics.
---

# Draw.io Diagrams

One job: a publication-ready diagram on the first render instead of after three rounds of iteration. This skill covers **how to lay out a `.drawio` file so the reader can actually read it, and how to prove that before claiming done**. It does not cover XML authoring basics or export mechanics — for draw.io XML reference beyond the patterns here (styles, shapes, containers, edge syntax), fetch https://raw.githubusercontent.com/jgraph/drawio-mcp/main/shared/xml-reference.md.

**If the diagram is a C4 view (context, container, or component — Simon Brown's model), read [C4.md](C4.md) in this skill folder before planning entities.** It carries the stencil rules, entity templates, palette default, and the C4 additions to the verification gate.

## The Iron Rule

> **Plan the entities, shapes, and rough layout BEFORE writing XML. Render to PNG and inspect BEFORE claiming done.**

Most iteration loops come from skipping one of these. Layout problems are visible in 5 seconds in a PNG; they're invisible reading XML.

## Static export does no obstacle avoidance (the assumption that bites)

CLI export (`drawio -x` → PNG/SVG/PDF) runs the plain orthogonal router: it picks endpoints and right-angle paths, but it does **not** route around boxes in the way. The raw route in the XML is what renders — so an auto-routed edge whose straight path crosses an unrelated box is drawn **straight through it**, and a midpoint label lands on whatever it overlaps. (Verified: a no-waypoint edge between two boxes with a third box dead between them renders as a straight line bisecting the middle box.) Some interactive/embedded viewers apply an extra layout pass that nudges edges off boxes; **the CLI export does not, and there's no flag to switch it on.** Three rules follow, in order:

- **Avoid the crossing by layout first.** The cheapest fix is to place boxes so no edge needs to cross an unrelated one — reserve corridors, keep a hub's column clear (Problems 1, 2, 5). An edge that crosses nothing needs no pinning and survives later edits.
- **Pin only the edges that genuinely can't avoid a box.** For those, set `exitX/exitY` + `entryX/entryY` and add waypoints to route down a clear corridor (Problems 1–5). Don't pin edges that already render clean — hard-coded routes go stale the moment you move a shape (Problem 7), so pinning everything just buys future breakage.
- **Don't trust the eyeball alone — it misses fine clips.** A line grazing a tag corner is invisible at fit-to-page zoom and obvious to the reader at 100%. Gate on geometry with the bundled checker (in this skill's `scripts/` folder):

  ```bash
  python3 scripts/check-overlaps.py yourfile.drawio     # one file
  python3 scripts/check-overlaps.py *.drawio            # whole folder
  ```

  It reconstructs every edge's route from its exit/entry points + waypoints and reports any segment crossing an unrelated box, per page (boundaries with `fillColor=none` are correctly ignored). `CLEAN` per file, or it names the offending edge and box. Pinned (waypointed) edges get an exact verdict; auto-routed edges get a `WARN` — resolve it by re-laying-out to remove the crossing, or by pinning that one edge. This is the gate that catches the clips three rounds of eyeballing won't.

## Multiple views → ONE .drawio file with tabs (not separate files)

When the user wants more than one view of the same subject (an overview plus per-flow detail, or several zoom levels), put them as separate **pages** inside a single `.drawio` file. draw.io renders pages as tabs along the bottom. The XML pattern:

```xml
<mxfile>
  <diagram name="1. Overview" id="p1">
    <mxGraphModel ...><root>...</root></mxGraphModel>
  </diagram>
  <diagram name="2. Payment flow" id="p2">
    <mxGraphModel ...><root>...</root></mxGraphModel>
  </diagram>
  <diagram name="3. Deployment" id="p3">
    <mxGraphModel ...><root>...</root></mxGraphModel>
  </diagram>
</mxfile>
```

One file means: one place to open, one place to version, one diff when something changes, views are conceptually grouped. Don't create `overview.drawio`, `payment-flow.drawio`, `deployment.drawio` as separate files — that's three commits, three PRs, three places to forget.

Page-index for CLI export is **1-based**: `-p 1` is the first page.

## Colour palette: pick one, apply it consistently

A diagram needs *some* colour palette to distinguish entity categories (internal vs external, in-focus vs out-of-scope, layer vs layer). The specific hex codes don't matter — what matters is **consistency within one diagram set** and that the four–five categories are visually distinct.

**Ask once at the start of a project** (or use whatever the user's existing diagrams use) and then commit. Don't pick colours per-shape on the fly — that's how a diagram ends up looking like a parrot.

## The layout problems that keep biting (and how to dodge them)

These are the recurring readability failures. Run through them mentally during the layout-planning phase, **before** writing XML.

### Problem 1 — Edge label lands on top of an icon or another shape

Symptom: An edge from A to B passes through C (some unrelated shape), and the auto-placed label sits on top of C's icon or label. The reader can't read either.

Root cause: orthogonal edge routing chose a path through C because it's the shortest one.

Fixes (in order of preference):
1. **Re-layout** so A and B don't need a path that passes through C. Move C to a different column or row.
2. **Add explicit waypoints** to route the edge around C. A two-corner path (`<Array as="points"><mxPoint x="..." y="..."/><mxPoint x="..." y="..."/></Array>`) gives full control.
3. **Always set `labelBackgroundColor=#FFFFFF`** on labelled edges — even with a clean path, you want labels readable when they cross other lines.

### Problem 2 — Vertical edge from the hub passes through an icon in the same column

Symptom: Central service at `x=A`, downstream icon at `x=A` (one row below), observability icon at `x=A` (another row below). The hub→observability edge passes straight through the downstream icon, and the label lands on it.

Root cause: you placed two icons in the same x-column as the hub.

Fix: **reserve the hub's column as a vertical edge corridor.** Place downstream icons LEFT or RIGHT of it, never directly below. If you need to put one directly below, route the longer edge around it with waypoints.

### Problem 3 — Parallel edges from the same source = stacked labels

Symptom: Source S sends two edges to nearby targets P and Q (e.g., observability platform → PagerDuty + Slack). Both edges run almost parallel; their midpoint labels land at near-identical coordinates and overlap.

Root causes:
- Both edges exit S at the same point (default = centre of side).
- Both edges route through the same channel.

Fix: **stagger.**
- Different exit points on S: `exitY=0.25` for one, `exitY=0.75` for the other.
- Different routing channels: waypoints at different y values so the horizontal segments are visibly separated.

### Problem 4 — Two long edges sharing an exit y = labels merge into garbage

Symptom: Two edges from one source S go to far-apart targets (say one to the right, one to the left). Both exit S at the same y. The midpoint labels end up adjacent and run into each other — text like "Metrics, logs, tLoad API + daily report" (two labels jammed together).

Root cause: both edges share `exitY=0.5`.

Fix: route them via different exit points or different y-corridors. Or route one of them via the top/bottom of the canvas as a "long route" so the labels can't possibly collide.

### Problem 5 — Edge routed through a busy band

Symptom: A long edge crosses the middle of the diagram where many other labels already live. Visually it intrudes; its label ends up adjacent to two or three others.

Fix: route long edges via **canvas corridors** (top edge, bottom edge, dedicated lanes between rows of icons). Use waypoints to force the route up/down out of the busy band, across, then back in.

### Problem 6 — `labelBackgroundColor` is missing

Symptom: An edge label is rendered as transparent text. It crosses an edge line or sits in a busy area, and the text is unreadable.

Fix: **every labelled edge gets `labelBackgroundColor=#FFFFFF`**. No exceptions. It's a one-line style addition. Default to white background; if the diagram has a coloured/dark background, use whatever colour the canvas is.

### Problem 7 — Moved an icon, forgot to update its edges' waypoints

Symptom: Icon was at `(800, 500)`, you moved it to `(600, 500)`, but an edge to it still has a hard-coded waypoint at `(800, 400)`. The edge now does a weird detour.

Root cause: explicit waypoints are coordinates, not symbolic references. They don't follow the shape.

Fix: when moving a shape, **search the XML for its old position values and update or delete waypoints** that reference them. Or, where possible, prefer auto-routed orthogonal paths (no waypoints) over manual waypoints — they re-route when the shape moves. *(Caveat: auto-routing re-flows on edit, but in CLI export it does no obstacle avoidance — an auto-routed path can render straight through a box. Fix that by layout where you can; pin with exit/entry + waypoints only if the crossing is unavoidable, and let `check-overlaps.py` confirm. See "Static export does no obstacle avoidance" above.)*

### Problem 8 — Copy-pasted edge, forgot to fix `source` / `target`

Symptom: an edge labelled "X notifies Y" actually connects Z and Y, because you copied another edge's XML and changed the label but not the `source` attribute.

Fix: **after copying any edge, re-read its `source=` and `target=` attributes and confirm they're correct.** This is a 10-second check that catches a class of bug that's invisible in the XML but obvious in the rendered PNG.

### Problem 9 — Text container sized too tightly = truncated label

Symptom: A lane label or boundary title renders truncated ("Data & sto" instead of "Data & storage"). The width on the text mxCell is too small.

Fix: text widths must accommodate the **longest possible string at the chosen font size**. When in doubt, set the width generously (200–300 px for short titles) — empty space is free, truncation isn't.

### Problem 10 — Many edges meet one hub, labels pile up at the midpoints

Symptom: a central node has 5–6 edges; their default midpoint labels cluster on top of each other near the hub (common in overview diagrams where everything points at one system).

Root cause: every edge's label defaults to the geometric midpoint, and the midpoints bunch where the edges converge.

Fixes:
1. **Fan the hub's connection points** — give each edge a distinct `exitX/exitY` (or `entryX/entryY`) so they leave/enter different sides instead of stacking on one.
2. **Move the label off the midpoint** with the edge geometry's own `x` (position along the edge: −1 = source … 0 = middle … 1 = target) and `y` (perpendicular pixel offset):
   ```xml
   <mxGeometry x="-0.4" y="-12" relative="1" as="geometry"/>
   ```
   `x=-0.4` slides the label 40 % toward the source onto a clearer segment; `y=-12` lifts it 12 px off the line.
3. **Keep on-edge labels short** — a step number or 2–3 words. Push figures / long detail into a small positioned tag box next to the edge, not into the edge label. (A short label is also far less likely to overlap anything in the first place.)

### Problem 11 — Arrowhead runs *along* the target's edge instead of pointing into it

Symptom: an edge reaches its target but the arrowhead sits sideways against the border (or floats near a corner), grazing the box rather than landing on it.

Root cause: a fixed `entryX/entryY` pins the arrow to one side, but the route arrives from a direction *parallel* to that side, so draw.io makes the final stub run along the edge — the arrowhead ends up parallel to the border. It bites specifically when **explicit waypoints** force the approach; a no-waypoint edge auto-attaches perpendicular at the perimeter and is fine. (Not a rounded-corner problem — it happens on the flat part of the edge too.)

Fixes:
1. **Drop the fixed `entryX/entryY`** and let draw.io attach at the perimeter — it brings the arrow in perpendicular to whichever side the route approaches. Simplest fix and usually right (see "pin only the edges that genuinely can't avoid a box"); perimeter attach *is* computed in static CLI export, so it's safe here. It may change *which* side the arrow lands on — if a specific side carries meaning, use fix 2.
2. **Align the last waypoint with the entry** — same `x` for a top/bottom entry, same `y` for a left/right entry — so the final segment is perpendicular. Or move the entry to the side the edge actually approaches from.
3. `check-overlaps.py` flags this as a conservative `ARROW` warning. It can over-flag (an arrowhead that's actually fine but whose routing skims the border), so confirm flagged edges in the PNG.

## Pre-flight verification (before saying "done")

1. **XML well-formedness.** `xmllint --noout file.drawio` returns clean. Otherwise the file won't even open in draw.io.
2. **Render each page to PNG.** Page index is 1-based:
   ```bash
   drawio -x -f png -b 20 -p 1 -o page1.png file.drawio
   drawio -x -f png -b 20 -p 2 -o page2.png file.drawio
   ```
3. **Run the geometric overlap checker — the gate the eye fails at:**
   ```bash
   python3 scripts/check-overlaps.py file.drawio
   ```
   Must print `CLEAN` for every page. Fix every `ISSUE` (edge routes through a box) — first by re-laying-out to remove the crossing, then by pinning if it's unavoidable; resolve every `WARN` (auto-routed edge that *may* cross) the same way and re-run. An `ARROW` line flags a likely sideways arrowhead (Problem 11) — fix it or confirm it in the PNG. This is what catches the grazing clips a downscaled PNG hides — don't skip it on the assumption the eyeball covered it.
4. **Eyeball each PNG** for what geometry can't check:
   - [ ] Every relationship's direction matches the verb tense ("X sends to Y" = arrow from X to Y)
   - [ ] Lane labels / boundary titles are visible and not truncated
   - [ ] Page margins look right — no shapes clipped at the edges
   - [ ] (edge-through-box and label-on-box overlaps belong to step 3, not the eye)
5. **Sanity-check edges.** Quick pass through XML: for each edge, confirm `source=` and `target=` are the IDs you actually intend.

If any check fails, fix and re-render. The render-fix loop is ~30 seconds — much cheaper than shipping a diagram the user has to point at and call out problems in.

## What's NOT in this skill (by design)

- **XML authoring basics and CLI export mechanics** (platform install paths, embed flags, format table) — the XML reference linked at the top covers deep syntax; export tooling belongs to your environment.
- **Specific colour hex codes** — pick a palette per project; apply consistently within the project.
- **Specific page sizes** — depends on entity count and aspect ratio. Start with whatever feels right and resize if shapes clip or labels run off.
- **AWS / Azure / GCP icon sets** — the layout rules here apply regardless of icon set; the sets themselves aren't covered.
- **Project-specific entity templates** — every project's entities are different. The patterns above apply universally; the content does not.
