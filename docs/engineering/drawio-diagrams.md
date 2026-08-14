## What it does

`drawio-diagrams` lays out `.drawio` files that read cleanly on the first render — edge routing that keeps labels legible, multiple views as tabs in one file, C4 stencil templates, official AWS icon lookup — and then proves the layout before calling it done.

It does not trust the eyeball. Static export does no obstacle avoidance — whatever route the raw XML implies is exactly what renders, straight through any box in the way — so the skill gates every diagram on a bundled geometric checker that reconstructs each edge's route and flags any segment crossing an unrelated box, the fine clips a fit-to-page PNG hides. Layout and verification are the whole job; XML authoring basics and export mechanics are deliberately out of scope.

## When to reach for it

Type `/drawio-diagrams`, or the agent reaches for it automatically when a task fits — it is model-invoked, and fires on creating, editing, or cleaning up any `.drawio` file, including "this diagram renders with overlapping labels".

| Your situation | Where to go |
| --- | --- |
| A new or edited `.drawio` diagram, any kind | This skill |
| A C4 context / container / component view | This skill — its `C4.md` layer adds stencil rules, entity templates, and the pinned C4 palette |
| An AWS architecture view | This skill — `find-aws-icon.py` looks up official `mxgraph.aws4` stencil styles |
| An existing diagram with edges through boxes or piled-up labels | This skill — run the checker, then fix by re-layout first |
| A quick throwaway sketch (Mermaid, SVG, whiteboard-style) | Not this skill — it is for `.drawio` files you keep and version |
| draw.io XML syntax beyond the patterns shown | The [official XML reference](https://raw.githubusercontent.com/jgraph/drawio-mcp/main/shared/xml-reference.md) the skill links to |

## Prerequisites

The verification gate shells out to three tools: the `drawio` CLI for PNG/XML export (on macOS the desktop app ships it at `/Applications/draw.io.app/Contents/MacOS/draw.io`), `python3` for the bundled checker, and `xmllint` for well-formedness. Without the CLI you can still write XML, but the render-and-inspect half — the half that catches real problems — cannot run.

## The Iron Rule

Plan the entities, shapes, and rough layout **before** writing XML; render to PNG and inspect **before** claiming done. Most diagram iteration loops come from skipping one of those two: layout problems are visible in five seconds in a PNG and invisible in the XML that produced them. The skill front-loads a catalogue of ten recurring layout failures (label collisions, hub corridors, stale waypoints, sideways arrowheads, flush frame margins) so they get dodged at planning time instead of discovered at review time.

## The geometric gate

The defining move. Because the CLI's router draws straight through obstacles, the skill refuses to accept "the PNG looks fine" as a verdict. `check-overlaps.py` reconstructs every edge's route from its exit/entry points and waypoints, then reports any segment that crosses an unrelated box — exact verdicts for pinned edges, conservative `WARN`s for auto-routed ones, `ARROW` flags for arrowheads that graze a border sideways. It resolves container-relative coordinates, and it refuses compressed files rather than passing them unchecked. `CLEAN` on every page is the exit condition; the eyeball is only trusted with what geometry cannot check (direction of arrows, truncated titles, margins).

## One file, many pages

Multiple views of one subject — an overview plus per-flow detail, a C4 zoom ladder — live as pages (tabs) in a single `.drawio` file, exported per page with 1-based `-p`. One file to open, one to version, one diff when something changes.

## Common questions

**The checker says `ERROR … page payload is compressed`.**
The file was saved with draw.io's compression on — its `<diagram>` holds base64 text instead of XML, so there is nothing checkable inside. Decompress once and carry on: `drawio -x -f xml -o uncompressed.drawio file.drawio`, or untick File → Properties → Compressed in the app. The checker errors instead of passing because a silent pass on an unreadable file is a lie.

**Can it look up Azure or GCP icons too?**
No — only AWS ships with a catalogue and lookup script. The layout rules apply to any icon set, but for other clouds you find the stencil names yourself.

**Should each view be its own `.drawio` file?**
No. The skill's rule is one file per subject, views as pages. Separate files mean separate diffs, separate exports, and views that drift apart.

## It's working if

- A planned entity list and rough layout appear before any XML does.
- Every page renders to PNG and `check-overlaps.py` prints `CLEAN` before the agent says done.
- Edge labels stay readable — backed, short, and never sitting on a box or another label.
- Multiple views land as tabs in one `.drawio` file, not as sibling files.
- On a C4 view, people are silhouettes and every box carries its `[Type]` stereotype.

## Where it fits

A reach-for-it-anytime standalone: no state, no prior setup, in and out per diagram. It has no direct sibling in the set — [ask-matt](https://aihero.dev/skills-ask-matt), the router over the whole set, sends any "draw or fix a diagram" work here.
