---
"mattpocock-skills": patch
---

setup-matt-pocock-skills docs: list Jira as a supported issue tracker.

The skill has supported Jira (via `acli`) for a while, but the docs page still enumerated only GitHub, GitLab, local-markdown, and "other". Added Jira and `acli` to the tracker list, and noted that — unlike `gh`/`glab` — `acli` can't infer the project from `git remote`, so setup asks for the project key and site.
