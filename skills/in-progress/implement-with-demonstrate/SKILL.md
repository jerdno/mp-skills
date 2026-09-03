---
name: implement-with-demonstrate
description: Implement a spec or ticket with /implement, then QA it like a human tester with /demonstrate, at most twice, with one fix round in between. The pull request carries the verdict.
disable-model-invocation: true
---

Build the work with /implement, then prove it works the way a human QA would, and fix what the demonstration finds.

Run /implement on the work the user named. It ends with the pull request open, and every commit below lands on that branch.

Then demonstrate and fix — at most 2 demonstrations:

1. Run /demonstrate against the work just built. Its intent is the ticket or spec, plus any scenario the user named.
2. One fix round. Every failed scenario and functional defect is a behaviour bug, so it goes through /tdd and gets a red test first. Fix visual defects directly. Questionable verdicts are judgement calls: fix the ones that matter, record why you dismissed the rest. Blocked scenarios are the user's decision inside /demonstrate, and findings about the environment or the evidence are not code. Both stay in the report. Commit once the full suite is green, then push. The PR follows the branch.
3. Demonstrate again if anything was fixed, so a fresh evidence agent verifies the fix the same way it verified the build. What the second demonstration finds stays open. A named bug beats an unverified fix.

Close out on the PR and in chat. Comment the verdict on the PR the way the project does (`gh pr comment`, `glab mr note`): the final `testing_summary`, the per-scenario verdicts, what was fixed between the demonstrations, and every finding still open. In chat, report /implement's close-out, the demonstrations used, and where each HTML report is.
