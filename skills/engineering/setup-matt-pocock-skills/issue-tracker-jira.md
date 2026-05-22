# Issue tracker: Jira

Issues and PRDs for this repo live as Jira work items. Use the [`acli`](https://developer.atlassian.com/cloud/acli/guides/introduction/) (Atlassian CLI) for all operations. Jira calls issues "work items"; the CLI uses that terminology.

## Conventions

- **Create an issue**: `acli jira workitem create --project "<KEY>" --type "Task" --summary "..." --description "..."`. Use `--description-file -` (or a heredoc piped in) for multi-line descriptions. `--type` is required — common values: `Task`, `Story`, `Bug`, `Epic`. `--label "a,b"` sets labels at creation time.
- **Read an issue**: `acli jira workitem view <KEY-123> --fields '*all' --json` for the full work item. The default plain-text output only renders `key/issuetype/summary/status/assignee/description` — extra fields like `labels` and `comment` are returned by the API but not printed unless you pass `--json` and parse the result. For comments specifically, prefer `acli jira workitem comment list --key <KEY-123>`.
- **List issues**: `acli jira workitem search --jql "project = <KEY> AND statusCategory != Done" --json --paginate`. All filtering goes through JQL — e.g. `labels = "needs-triage"`, `assignee = currentUser()`, `status = "In Progress"`. Use `--fields` to control which fields appear; default is `issuetype,key,assignee,priority,status,summary`.
- **Comment on an issue**: `acli jira workitem comment create --key <KEY-123> --body "..."`. Use `--body-file` for multi-line bodies, or `--editor` to open `$EDITOR`.
- **Apply / remove labels**: `acli jira workitem edit --key <KEY-123> --labels "a,b"` adds labels; `--remove-labels "a,b"` removes them. Labels are comma-separated.
- **Close**: `acli jira workitem transition --key <KEY-123> --status "Done"`. The exact status string depends on the project's workflow (commonly `Done`, `Closed`, or `Resolved`) — post the closing rationale as a comment first if you need one, since `transition` doesn't accept a comment.

Jira does not infer the site or project from `git remote -v`. Authenticate once with `acli jira auth login` (this picks a default site, e.g. `vacuum.atlassian.net`) and pass `--project <KEY>` (or include `project = <KEY>` in JQL) on every command that needs one. Work item keys like `RA-123` already encode the project, so per-item commands don't need `--project`.

## When a skill says "publish to the issue tracker"

Create a Jira work item with `acli jira workitem create`.

## When a skill says "fetch the relevant ticket"

Run `acli jira workitem view <KEY> --fields '*all' --json` to get the full work item (parse the JSON to read labels, custom fields, etc.), and `acli jira workitem comment list --key <KEY>` for the comment thread.
