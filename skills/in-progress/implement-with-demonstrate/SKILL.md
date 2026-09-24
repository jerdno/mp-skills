---
name: implement-with-demonstrate
description: Implement a spec or ticket with /implement, then QA it like a human tester with /demonstrate, at most twice, with one fix round in between. The pull request opens only at the end, carrying the verdict.
disable-model-invocation: true
---

Build the work with /implement, prove it works the way a human QA would, fix what the demonstration finds, and only then open the pull request.

Run /implement on the work the user named, with `--no-pr`. It leaves the work committed on a branch in a worktree of its own, and everything below runs inside that worktree.

Then demonstrate and fix — at most 2 demonstrations:

1. Run /demonstrate against the work just built, naming the worktree as the checkout under test. Its intent is the ticket or spec, plus any scenario the user named.
2. One fix round. Every failed scenario and functional defect is a behaviour bug, so it goes through /tdd and gets a red test first. Fix visual defects directly. Questionable verdicts are judgement calls: fix the ones that matter, record why you dismissed the rest. Blocked scenarios are the user's decision inside /demonstrate, and findings about the environment or the evidence are not code. Both stay in the report. Commit once the full suite is green.
3. Demonstrate again if anything was fixed, so a fresh evidence agent verifies the fix the same way it verified the build. What the second demonstration finds stays open. A named bug beats an unverified fix.

Then commit whatever /demonstrate recorded in `docs/agents/demonstrate.md`, so the record travels with the branch, and open the pull request exactly as /implement's last step describes. The body carries the ticket reference, /implement's close-out, and the final demonstration verdict: `testing_summary`, the per-scenario verdicts, what was fixed between the demonstrations, and every finding still open. In chat, report the PR URL, the demonstrations used, and where each HTML report is.
