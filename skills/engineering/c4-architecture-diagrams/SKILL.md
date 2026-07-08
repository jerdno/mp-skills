---
name: c4-architecture-diagrams
description: Use when creating C4 architecture diagrams (context, container, or component views) in draw.io. Encodes hard-won layout lessons — proper C4 stencils so actors aren't indistinguishable from systems, edge routing that keeps labels readable, and multiple views organised as tabs in one file. Triggers on "C4 diagram", "context view", "container view", "component view", or any diagram following Simon Brown's C4 model.
---

# C4 Architecture Diagrams

A focused companion to the generic `drawio` skill, for one job: producing a publication-ready C4 diagram on the first render instead of after three rounds of iteration. The drawio skill tells you **how** to write `.drawio` XML; this skill tells you **how to lay one out so the reader can actually read it**.

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

When the user wants more than one C4 view (context + container, or container + component, or all three), put them as separate **pages** inside a single `.drawio` file. draw.io renders pages as tabs along the bottom. The XML pattern:

```xml
<mxfile>
  <diagram name="1. Context" id="ctx">
    <mxGraphModel ...><root>...</root></mxGraphModel>
  </diagram>
  <diagram name="2. Container" id="cnt">
    <mxGraphModel ...><root>...</root></mxGraphModel>
  </diagram>
  <diagram name="3. Component (X service)" id="cmp-x">
    <mxGraphModel ...><root>...</root></mxGraphModel>
  </diagram>
</mxfile>
```

One file means: one place to open, one place to version, one diff when something changes, edges between views are conceptually grouped. Don't create `context.drawio`, `container.drawio`, `component.drawio` as separate files — that's three commits, three PRs, three places to forget.

Page-index for CLI export is **1-based**: `-p 1` is the first page.

## Use real C4 stencils where they exist (the actor-vs-system problem)

The cardinal sin of a C4 diagram: every entity is a styled rectangle, so a reader can't tell at a glance which boxes are humans and which are software. The `[Person]` / `[Software System]` stereotype label helps, but it's *text* — the reader has to read every box. A diagram should be parseable by *shape* first.

**draw.io's actual C4 stencil library is narrow.** Only the person silhouette is a dedicated shape:

```
shape=mxgraph.c4.person2   # The person-with-stick-figure shape — use this for every Person
```

For Software System / Container / Component / External System — there's no specialised stencil, just styled rectangles (and cylinders for stores). That's fine, because rectangles are easy to distinguish from a silhouette. The rule:

- **Person (any kind — internal, external, addon) → `mxgraph.c4.person2`. Always.**
- **Software System / Container / Component / Database / External System → rounded rectangle (or `cylinder3` for stores), with the entity type written in the label as `[Type]`.**

Wrap each entity in an `<object>` element carrying C4 metadata (`c4Name`, `c4Type`, `c4Description`), **and put `metaEdit=1` in the shape's style.** The two work together: the `<object>` makes the entity readable by downstream C4-as-code tooling, and `metaEdit=1` makes double-click open the metadata (Edit Data) dialog. The `<object>` wrapper alone is *not* enough — without `metaEdit=1`, double-click opens draw.io's raw HTML label editor and the description can't be edited cleanly. Minimal but worth it.

### Person template (always wrap in `<object>`)

```xml
<object placeholders="1"
        c4Name="Persona Name"
        c4Type="Person"
        c4Description="One-sentence role description."
        label="&lt;font style=&quot;font-size: 16px&quot;&gt;&lt;b&gt;%c4Name%&lt;/b&gt;&lt;/font&gt;&lt;div&gt;[%c4Type%]&lt;/div&gt;&lt;br&gt;&lt;div&gt;&lt;font style=&quot;font-size: 11px&quot;&gt;%c4Description%&lt;/font&gt;&lt;/div&gt;"
        id="ENTITY_ID">
  <mxCell parent="1" vertex="1"
          style="html=1;fontSize=11;dashed=0;whiteSpace=wrap;fontColor=#ffffff;shape=mxgraph.c4.person2;align=center;metaEdit=1;points=[[0.5,0,0],[1,0.5,0],[1,0.75,0],[0.75,1,0],[0.5,1,0],[0.25,1,0],[0,0.75,0],[0,0.5,0]];resizable=0;fillColor=PALETTE_FILL;strokeColor=PALETTE_STROKE;">
    <mxGeometry x="X" y="Y" width="200" height="180" as="geometry"/>
  </mxCell>
</object>
```

Notes:
- `points=[…]` is the connection-anchor array sized for the person silhouette. Copy verbatim or edges will attach at weird offsets.
- `resizable=0` and `width=200 height=180` — do not resize the person shape. If you need more text, use the `c4Description` attribute; the shape stays the same.
- `metaEdit=1` enables the C4 metadata dialog on double-click.

### System / Container template (rectangle in `<object>`)

```xml
<object placeholders="1"
        c4Name="System Name"
        c4Type="Software System"
        c4Description="One- or two-sentence description."
        label="&lt;font style=&quot;font-size: 16px&quot;&gt;&lt;b&gt;%c4Name%&lt;/b&gt;&lt;/font&gt;&lt;div&gt;[%c4Type%]&lt;/div&gt;&lt;br&gt;&lt;div&gt;&lt;font style=&quot;font-size: 11px&quot;&gt;%c4Description%&lt;/font&gt;&lt;/div&gt;"
        id="ENTITY_ID">
  <mxCell parent="1" vertex="1"
          style="rounded=1;whiteSpace=wrap;html=1;fontColor=#FFFFFF;fontSize=12;align=center;verticalAlign=middle;fillColor=PALETTE_FILL;strokeColor=PALETTE_STROKE;metaEdit=1;">
    <mxGeometry x="X" y="Y" width="W" height="H" as="geometry"/>
  </mxCell>
</object>
```

Notes:
- `metaEdit=1` is what makes double-click open the C4 metadata (Edit Data) dialog — Name / Type / Description — instead of draw.io's raw HTML label editor. It is **required on every entity** (systems, containers, components, external systems, stores), not just persons. The `<object>` wrapper alone is not enough.

For a database / object store, swap the style for `shape=cylinder3;...;size=18;...` (keep `metaEdit=1`).

For an external boundary (system, account, environment), use a rectangle with `fillColor=none;strokeColor=...;dashed=1;dashPattern=12 6;` and place it behind the contained shapes (earlier in XML order).

### Colour palette: pick one, apply it consistently

A C4 diagram needs *some* colour palette to distinguish entity types (internal vs external, in-focus vs out-of-scope, addon vs core). The specific hex codes don't matter — what matters is **consistency within one diagram set** and that the four–five categories are visually distinct.

The canonical C4-PlantUML palette is a fine default; the human may prefer slightly different shades. **Ask once at the start of a project** (or use whatever the user's existing diagrams use) and then commit. Don't pick colours per-shape on the fly — that's how a diagram ends up looking like a parrot.

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

Symptom: a central node has 5–6 edges; their default midpoint labels cluster on top of each other near the hub (common in context diagrams and fee maps where everything points at one system).

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
   - [ ] Persons (silhouette) are visually distinguishable from systems (rectangles) at a glance
   - [ ] Every relationship's direction matches the verb tense ("X sends to Y" = arrow from X to Y)
   - [ ] Lane labels / boundary titles are visible and not truncated
   - [ ] Page margins look right — no shapes clipped at the edges
   - [ ] (edge-through-box and label-on-box overlaps belong to step 3, not the eye)
5. **Sanity-check edges.** Quick pass through XML: for each edge, confirm `source=` and `target=` are the IDs you actually intend.

If any check fails, fix and re-render. The render-fix loop is ~30 seconds — much cheaper than shipping a diagram the user has to point at and call out problems in.

## Common pitfalls — compact reference

| Pitfall | Fix |
|---|---|
| Used a plain rectangle for a Person | Switch to `mxgraph.c4.person2`, wrap in `<object>` |
| Tried `mxgraph.c4.softwareSystem` / `mxgraph.c4.container` | These don't exist. Use rounded rectangles with `[Type]` stereotype label |
| Edge label unreadable on a coloured line | Set `labelBackgroundColor=#FFFFFF` |
| Two parallel arrows have overlapping labels | Stagger exit points (`exitY=0.25` vs `0.75`) and route through different channels |
| Vertical edge through a downstream icon | Move the icon out of the hub's x-column |
| Resized `person2` and edges attach weirdly | Don't resize person2; keep `resizable=0`, width 200, height 180 |
| Skipped `<object>` wrapper | Downstream C4 tools can't read the entity, and double-click has no metadata to show. Wrap it |
| Entity wrapped in `<object>` but missing `metaEdit=1` | Double-click opens the raw HTML label editor instead of the Name/Type/Description form, so the description can't be edited cleanly. Add `metaEdit=1` to the style of **every** entity — rectangles and stores, not just persons |
| CLI exported the wrong page | Page index is 1-based (`-p 1` for the first page) |
| Lane label truncated | Increase the width of the text mxCell |
| Edge waypoint references old shape position | Search for the old coordinates and update or delete the waypoint |
| Eyeballed the PNG, shipped a grazing clip | The eye misses fine clips on a downscaled PNG — gate on `check-overlaps.py`, which prints CLEAN or names the edge + box |
| Auto-routed edge sailed through a box in the static export | CLI export does no obstacle avoidance — re-lay-out to clear the crossing, or pin that one edge with exit/entry + waypoints, then confirm with `check-overlaps.py` |
| Hub's edge labels piled up at their midpoints | Fan exit points + move labels off-midpoint with `mxGeometry x/y` (Problem 10) |
| Arrowhead sits sideways against the target's border | Fixed entry fights a waypointed approach — drop `entryX/entryY` (perimeter auto-attach) or align the last waypoint with the entry (Problem 11) |

## What's NOT in this skill (by design)

- **Specific colour hex codes** — pick a palette per project; apply consistently within the project.
- **Specific page sizes** — depends on entity count and aspect ratio. Start with whatever feels right and resize if shapes clip or labels run off.
- **AWS / Azure / GCP icon sets** — those belong in a separate skill (or in the generic `drawio` skill). This skill is about the C4 *notation*, not about cloud iconography.
- **Project-specific entity templates** — every project's entities are different. The patterns above apply universally; the content does not.
