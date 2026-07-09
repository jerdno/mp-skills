---
name: implement
description: "Implement a piece of work based on a spec or set of tickets."
disable-model-invocation: true
---

Implement the work described by the user in the spec or tickets.

First, pin the review baseline: `git rev-parse HEAD`. Every review round below diffs against this SHA. If the tree is dirty, tell the user which pre-existing changes will be swept into the run before continuing.

Invoke /tdd for each implementation seam. Do not write tests directly — let /tdd drive the loop.

Run typechecking regularly, single test files regularly, and the full test suite once at the end.

Commit the build to the current branch.

Then review and fix — at most 3 rounds:

1. Run /code-review with the pinned SHA as the fixed point.
2. Fix every Spec finding, each through /tdd — they are behaviour changes. Fix every hard standards violation directly — they are refactors under green tests. For judgement-call smells, make your own call on relevance: fix the ones that matter, whatever their size, and record why you dismissed the rest.
3. Commit the fixes — the next review only sees committed work.
4. Stop early if the round reported no hard findings.

Close out by reporting: rounds used, what was fixed, dismissed judgement calls with their reasons, and any hard findings still open after round 3.
