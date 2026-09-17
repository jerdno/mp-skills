# Confluence

The delta for Confluence pages. The voice and the tests live in [`SKILL.md`](SKILL.md). A page is found by search and read by someone with no context, so the page carries its own frame.

## Page shape

- First paragraph, one to three sentences: what the page is, who it is for, and when to reach for it. A page that argues for something opens with a "Background" or "Rationale" section instead: the situation, the past attempts, then the proposal.
- One topic per heading. Headings in sentence case, saying the thing in plain words ("Only two environments", "Why two layers?"). H1 for the sections of a long page, H2 within them, three levels at most. A table of contents only past roughly eight sections.
- Short paragraphs. A bullet list where items are parallel, a numbered list where order matters, a table where the same fields repeat across items.
- Link to the source of truth (repo README, vendor docs, Jira, the sibling page) instead of restating it. Material that changes often (entity attributes, configuration) stays in code, and the page says so and links there.
- Gaps are marked, not filled: an inline task ("TODO: link the release script") or a one-line placeholder ("Not planned for phase 1, this page is a placeholder"). A section exists because a reader needs it, not because a template had it.

## Patterns by page type

- **Principle or guideline**: the principle as the heading, the rule in one sentence inside an info panel, then one paragraph of why and what it rules out. Repeat per principle. Normative verbs where they help: must, should, is not allowed.
- **Decision**: Background, then Options considered (pros and cons per option, a table when there are more than two), then the Decision in bold with the reason in the same sentence ("Decision: one project - we do not want to overcomplicate the pilot setup, and migrating later is possible"), then what follows from it. Rationale for a design goes under question headings ("Why two layers?", "Why a single Lambda?"), each answered in two or three bullets.
- **Comparison or evaluation**: what was compared and the decision factors first, then one table with one row per feature and one column per option, cells short (Yes, No, Partially plus a few words) and a notes column for the nuance. Strengths and weaknesses per option as bullets after the table.
- **How-to or setup**: numbered steps, one action per step, "(Optional)" prefixed where a step can be skipped, a screenshot where the UI matters, the gotcha you hit as a note panel next to the step that triggers it.

## Panels and macros

- **Info**: a clarification, an example, or a pointer ("A Jira task exists to include this in the Terraform blueprint").
- **Note**: a caveat or a gotcha learned the hard way ("Enabling biometry via Terraform did not activate it in the SDK; we had to toggle it manually in the dashboard").
- **Warning**: only when acting on the page without reading it causes damage.
- **Expand**: reference blocks most readers skip (requirement lists, entity fields, long configuration examples).
- **Code**: configuration, JSON, commands, queries.
- Icons only in yes/no table cells.

Produce the panels in whatever the target tool takes: markdown callouts for a paste, storage-format macros for the API.
