# Issue tracker: Jira

- **Project**: `<PROJECT>` (e.g. `RA`)
- **Site**: `<SITE>` (e.g. `vacuum.atlassian.net`)

Issues and PRDs for this repo live as Jira work items in the project above. Use the [`acli`](https://developer.atlassian.com/cloud/acli/guides/introduction/) (Atlassian CLI) for all operations. Jira calls issues "work items"; the CLI uses that terminology.

> Setup note: `setup-matt-pocock-skills` substitutes `<PROJECT>` and `<SITE>` with the values the user provided when writing this file to `docs/agents/issue-tracker.md`. After substitution, the values above are the source of truth for skills that read this file — they should pass `--project <PROJECT>` (or `project = <PROJECT>` in JQL) instead of guessing.

## Conventions

- **Create an issue**: `acli jira workitem create --project "<PROJECT>" --type "Task" --summary "..." --description "..."`. Use `--description-file -` (or a heredoc piped in) for multi-line descriptions. `--type` is required — common values: `Task`, `Story`, `Bug`, `Epic`. `--label "a,b"` sets labels at creation time.
- **Read an issue**: `acli jira workitem view <KEY> --fields '*all' --json` for the full work item (`<KEY>` is a work item key like `<PROJECT>-123`). The default plain-text output only renders `key/issuetype/summary/status/assignee/description` — extra fields like `labels` and `comment` are returned by the API but not printed unless you pass `--json` and parse the result. For comments specifically, prefer `acli jira workitem comment list --key <KEY>`.
- **List issues**: `acli jira workitem search --jql "project = <PROJECT> AND statusCategory != Done" --json --paginate`. All filtering goes through JQL — e.g. `labels = "needs-triage"`, `assignee = currentUser()`, `status = "In Progress"`. Use `--fields` to control which fields appear; default is `issuetype,key,assignee,priority,status,summary`.
- **Comment on an issue**: `acli jira workitem comment create --key <KEY> --body "..."`. Use `--body-file` for multi-line bodies, or `--editor` to open `$EDITOR`.
- **Apply / remove labels**: `acli jira workitem edit --key <KEY> --labels "a,b"` adds labels; `--remove-labels "a,b"` removes them. Labels are comma-separated.
- **Close**: `acli jira workitem transition --key <KEY> --status "Done"`. The exact status string depends on the project's workflow (commonly `Done`, `Closed`, or `Resolved`) — post the closing rationale as a comment first if you need one, since `transition` doesn't accept a comment.

## Inference vs configuration

`acli` does not infer the site or project from `git remote -v` (unlike `gh`/`glab`, which discover the repo from the remote). They have to come from elsewhere:

- **Site** is held globally by `acli` itself — set once with `acli jira auth login --web`, stored in `~/.config/acli/global_auth_config.yaml`. If multiple sites are configured, switch with `acli jira auth switch --site <SITE>`. The `<SITE>` in the header above is the one this repo expects; skills can sanity-check against `acli jira auth status`.
- **Project** is per-repo and lives in this file (`docs/agents/issue-tracker.md`). Skills should read `<PROJECT>` from here rather than asking the user every time. Work item keys like `<PROJECT>-123` already encode the project, so per-item commands (`view`, `edit`, `comment`, `transition`) don't need `--project` — only `create` and JQL queries do.

## When a skill says "publish to the issue tracker"

Create a Jira work item with `acli jira workitem create --project "<PROJECT>" --type "Task" ...`.

## When a skill says "fetch the relevant ticket"

Run `acli jira workitem view <KEY> --fields '*all' --json` to get the full work item (parse the JSON to read labels, custom fields, etc.), and `acli jira workitem comment list --key <KEY>` for the comment thread.
