---
name: implement
description: "Build the work described by a spec, ticket, or issue in its own git worktree: test-driven at each seam, typecheck and full suite, commit, a bounded code-review fix loop, then a pull request. Use when the user asks to implement or build a ticket, issue, or spec whose design is settled."
---

Implement the work described by the user in the spec or tickets.

First, give the work its own checkout: a git worktree on a new branch, both named after the ticket or spec (its key and a short slug), so several runs can share one repository. Under Claude Code, read [CLAUDE-CODE.md](CLAUDE-CODE.md) first, because the harness has its own worktree tool. Elsewhere, from the repository root, `git worktree add .worktrees/<name> -b <name>`, with `.worktrees/` listed in `.git/info/exclude`. Everything from here on runs inside the worktree. Uncommitted changes in the checkout you started from stay behind; tell the user if there are any. Make the worktree runnable the way a fresh clone is made runnable: the project's install command, plus the gitignored local config (`.env.local` and the like) copied over from the main checkout, which `git worktree list` names first.

Pin the review baseline inside the worktree: `git rev-parse HEAD`. Every review round below diffs against this SHA.

Invoke /tdd for each implementation seam. Do not write tests directly — let /tdd drive the loop.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Commit the build to the worktree's branch.

Then review and fix — at most 3 rounds:

1. Run /code-review with the pinned SHA as the fixed point.
2. Fix every Spec finding, each through /tdd — they are behaviour changes. Fix every hard standards violation directly — they are refactors under green tests. For judgement-call smells, make your own call on relevance: fix the ones that matter, whatever their size, and record why you dismissed the rest.
3. Commit the fixes — the next review only sees committed work.
4. Stop early if the round reported no hard findings.

Close out by reporting: the worktree path and branch, rounds used, what was fixed, dismissed judgement calls with their reasons, and any hard findings still open after round 3.

Then, unless the invocation carries `--no-pr`, open the pull request. Push the branch and create the PR the way the project does (`gh pr create`, `glab mr create`), against the default branch, with the ticket or spec reference and the close-out report as its body. Give the user the PR URL. Without a remote or PR tooling, say so and leave the work committed on the branch. With `--no-pr` the run ends at the close-out, and the caller opens the PR.
