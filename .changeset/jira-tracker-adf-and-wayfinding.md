---
"mattpocock-skills": patch
---

Jira issue-tracker template: lean ticket reads, native ADF authoring, and a Wayfinding operations section.

- **Lean reads.** "Read an issue" / "fetch the relevant ticket" no longer steer agents to `--fields '*all' --json` (~200 lines of avatar URLs and null custom fields on every read). The default is now the plain-text `view`; structured reads use an explicit `--fields "..." --json | jq` projection (a bare `--json` returns neither `labels` nor `parent`), with a `jq`-free fallback; `*all` remains only as a cautioned escape hatch.
- **Author ADF, not markdown.** Jira stores descriptions/comments as ADF, so pasted markdown renders literally. The template now tells agents to author ADF — always for descriptions, and for comments when formatted — with a minimal ADF primer.
- **Wayfinding operations.** Adds the `/wayfinder` mapping the GitHub/GitLab/local templates already carry: map = `Task` labelled `wayfinder:map` (ADF body), tickets = subtasks labelled `wayfinder:<type>`, native `is blocked by` blocking, the frontier query (per-item `view --fields issuelinks`, since `search` omits links), claim/resolve, and the parallel-safe map-body edit.
