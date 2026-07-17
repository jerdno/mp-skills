# Issue tracker: Jira

- **Project**: `<PROJECT>` (e.g. `RA`)
- **Site**: `<SITE>` (e.g. `vacuum.atlassian.net`)

Issues and PRDs for this repo live as Jira work items in the project above. Use the [`acli`](https://developer.atlassian.com/cloud/acli/guides/introduction/) (Atlassian CLI) for all operations. Jira calls issues "work items"; the CLI uses that terminology.

> Setup note: `setup-matt-pocock-skills` substitutes `<PROJECT>` and `<SITE>` with the values the user provided when writing this file to `docs/agents/issue-tracker.md`. After substitution, the values above are the source of truth for skills that read this file — they should pass `--project <PROJECT>` (or `project = <PROJECT>` in JQL) instead of guessing.

## Conventions

- **Create an issue**: `acli jira workitem create --project "<PROJECT>" --type "Task" --summary "..." --description "..."`. Use `--description-file -` (or a heredoc piped in) for multi-line descriptions. `--type` is required — common values: `Task`, `Story`, `Bug`, `Epic`. `--label "a,b"` sets labels at creation time.
- **Formatting — author ADF, not markdown**: Jira stores descriptions and comments as **ADF** (Atlassian Document Format — a JSON document tree), *not* markdown. Plain text or markdown passed to `--description`/`--body` is stored and rendered **literally** (a pasted `## Heading` shows the `##`; `[text](url)` stays dead text). So author **ADF** for structured content — **always for descriptions**, and for comments **when they carry formatting** (headings, lists, links, code); plain-prose comments can stay plain text. Pass it via `--description-file <adf.json>` / `--body-file <adf.json>` (both accept plain text or ADF). Minimal document: `{"version":1,"type":"doc","content":[{"type":"paragraph","content":[{"type":"text","text":"..."}]}]}`; a heading is `{"type":"heading","attrs":{"level":2},"content":[...]}`, a link is a `{"type":"link","attrs":{"href":"..."}}` mark on a text node, and a bullet list nests `bulletList` → `listItem` → `paragraph`.
- **Read an issue**: default to the plain-text view — `acli jira workitem view <KEY>` (`<KEY>` is a work item key like `<PROJECT>-123`). It renders `key/issuetype/summary/status/assignee/description` (the ADF description as readable text), which is what a read usually needs. Escalate only when you need more:
    - **Structured fields** — notably `labels` and `parent`, which the plain view omits: select them explicitly and trim with `jq`, e.g. `acli jira workitem view <KEY> --fields "summary,status,labels,parent,description" --json | jq '{key, summary: .fields.summary, status: .fields.status.name, labels: .fields.labels, parent: .fields.parent.key}'`. Both halves matter — `--fields` *fetches* the fields (a bare `--json` returns neither `labels` nor `parent`) and `jq` *trims* the response. No `jq` installed? Drop the pipe and read `--fields "..." --json` directly: verbose, but far leaner than `*all`.
    - **Avoid `acli jira workitem view <KEY> --fields '*all' --json`** unless you genuinely need a rarely-used custom field — it returns ~200 lines of avatar URLs, null custom fields, and fully-expanded parent objects, which is context waste on every read.
    - For the comment thread, use `acli jira workitem comment list --key <KEY>`.
- **List issues**: `acli jira workitem search --jql "project = <PROJECT> AND statusCategory != Done" --json --paginate`. All filtering goes through JQL — e.g. `labels = "needs-triage"`, `assignee = currentUser()`, `status = "In Progress"`. Use `--fields` to control which fields appear; default is `issuetype,key,assignee,priority,status,summary`.
- **Comment on an issue**: `acli jira workitem comment create --key <KEY> --body "..."`. Use `--body-file` for multi-line bodies (author ADF when the comment carries formatting — see *Formatting* above), or `--editor` to open `$EDITOR`.
- **Apply / remove labels**: `acli jira workitem edit --key <KEY> --labels "a,b"` adds labels; `--remove-labels "a,b"` removes them. Labels are comma-separated.
- **Close**: `acli jira workitem transition --key <KEY> --status "Done"`. The exact status string depends on the project's workflow (commonly `Done`, `Closed`, or `Resolved`) — post the closing rationale as a comment first if you need one, since `transition` doesn't accept a comment.

## Inference vs configuration

`acli` does not infer the site or project from `git remote -v` (unlike `gh`/`glab`, which discover the repo from the remote). They have to come from elsewhere:

- **Site** is held globally by `acli` itself — set once with `acli jira auth login --web`, stored in `~/.config/acli/global_auth_config.yaml`. If multiple sites are configured, switch with `acli jira auth switch --site <SITE>`. The `<SITE>` in the header above is the one this repo expects; skills can sanity-check against `acli jira auth status`.
- **Project** is per-repo and lives in this file (`docs/agents/issue-tracker.md`). Skills should read `<PROJECT>` from here rather than asking the user every time. Work item keys like `<PROJECT>-123` already encode the project, so per-item commands (`view`, `edit`, `comment`, `transition`) don't need `--project` — only `create` and JQL queries do.

## When a skill says "publish to the issue tracker"

Create a Jira work item with `acli jira workitem create --project "<PROJECT>" --type "Task" ...` (author the description as ADF — see *Formatting* above).

## When a skill says "fetch the relevant ticket"

Default to the plain-text view — `acli jira workitem view <KEY>` (summary / status / description / assignee). When you need structured fields like `labels` or `parent`, use the lean structured read (`--fields "..." --json | jq '{...}'`, see **Read an issue** under Conventions above) rather than `--fields '*all' --json`. Read the comment thread with `acli jira workitem comment list --key <KEY>`.

## Wayfinding operations

Used by `/wayfinder`. The **map** is a single work item whose **subtasks** are its tickets.

- **Map**: a `Task` labelled `wayfinder:map`, holding the Notes / Decisions-so-far / Fog body in its **description**. Create with `acli jira workitem create --project "<PROJECT>" --type "Task" --label "wayfinder:map" --description-file <adf.json>`. The body is **ADF** (see *Formatting — author ADF*) — author it as ADF so it renders; read it back with `acli jira workitem view <MAP>` (plain view renders the ADF as text), and only reach for `--fields description --json` when you need to edit it.
- **Ticket**: a **subtask** of the map — `acli jira workitem create --project "<PROJECT>" --type "Subtask" --parent <MAP> --label "wayfinder:<type>" ...`, where `<type>` is one of `research`/`prototype`/`grilling`/`task`. Once claimed, the subtask is assigned to the driving dev.
- **Blocking**: Jira's native **`is blocked by`** link — the canonical, UI-visible representation. A ticket is unblocked when every ticket that blocks it is Done.
- **Frontier query**: list the map's open children with `acli jira workitem search --jql "parent = <MAP> AND statusCategory != Done"`, then read each candidate's blockers **per item** with `acli jira workitem view <KEY> --fields issuelinks --json` — a `search` with `--fields issuelinks` does **not** return the links. The frontier is the open children with no open blocker and no assignee; first in map order wins.
- **Claim**: `acli jira workitem assign --key <KEY> --assignee @me` — the session's first write, before any work.
- **Resolve**: post the answer as a comment (`acli jira workitem comment create --key <KEY> --body-file <adf.json>`), then `acli jira workitem transition --key <KEY> --status "Done"`, then append a context pointer (gist + link) to the map's Decisions-so-far.

**Editing the map body.** The description is one ADF document. To append to Decisions-so-far: fetch it (`acli jira workitem view <MAP> --fields description --json`), insert your entry into the tree (add a `listItem` to the relevant `bulletList`), and write the whole document back with `acli jira workitem edit --key <MAP> --description-file <adf.json>`. **Re-fetch and diff immediately before writing** — unblocked tickets run in parallel sessions, so the map can change under you.
