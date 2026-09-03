---
name: implement
description: "Build the work described by a spec, ticket, or issue: test-driven at each seam, typecheck and full suite, commit, a bounded code-review fix loop, then a pull request. Use when the user asks to implement or build a ticket, issue, or spec whose design is settled."
---

Implement the work described by the user in the spec or tickets.

First, pin the review baseline: `git rev-parse HEAD`. Every review round below diffs against this SHA. If the tree is dirty, tell the user which pre-existing changes will be swept into the run before continuing. If HEAD is on the default branch, branch off first, named after the work, because the pull request at the end needs a branch of its own.

Invoke /tdd for each implementation seam. Do not write tests directly — let /tdd drive the loop.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Commit the build to the current branch.

Then review and fix — at most 3 rounds:

1. Run /code-review with the pinned SHA as the fixed point.
2. Fix every Spec finding, each through /tdd — they are behaviour changes. Fix every hard standards violation directly — they are refactors under green tests. For judgement-call smells, make your own call on relevance: fix the ones that matter, whatever their size, and record why you dismissed the rest.
3. Commit the fixes — the next review only sees committed work.
4. Stop early if the round reported no hard findings.

Close out by reporting: rounds used, what was fixed, dismissed judgement calls with their reasons, and any hard findings still open after round 3.

Then open the pull request. Push the branch and create the PR the way the project does (`gh pr create`, `glab mr create`), against the default branch, with the ticket or spec reference and the close-out report as its body. Give the user the PR URL. Without a remote or PR tooling, say so and leave the work committed on the branch.
