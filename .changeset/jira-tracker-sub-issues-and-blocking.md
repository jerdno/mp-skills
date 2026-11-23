---
"mattpocock-skills": patch
---

Jira issue-tracker template: sub-issue and blocking conventions outside Wayfinding.

`to-tickets` makes each ticket a sub-issue of its source issue and wires native blocking links, both through "the tracker doc's operation". The Jira template only described those inside its Wayfinding section, so a `to-tickets` or `implement-spec` run on Jira had nothing to follow.

- **Make an issue a sub-issue of a parent.** Set `--parent` at creation, since `acli` cannot re-parent an existing work item. The parent's type fixes the child's type (`Subtask` under a Task, Story or Bug; `Task` under an Epic), with a `Part of <PARENT>` line as the fallback.
- **Blocking.** The `acli jira workitem link create --in <BLOCKER> --out <BLOCKED> --type Blocks` command, plus a read-back check on the first edge of a session, because `--in` and `--out` name Jira's link ends and not a reading order.
- **List a ticket's open blockers.** One `view --fields issuelinks --json | jq` read that returns only blockers not yet Done.
- The Wayfinding section now points at these conventions instead of restating them.

The `setup-matt-pocock-skills` docs page and the README list Jira among the shipped tracker templates.
