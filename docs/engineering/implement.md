## What it does

`implement` builds the work described in a spec or a set of tickets in a git worktree of its own — driving it through test-driven development, typechecking, and the full test suite — then closes its own loop: it commits the green build, runs a bounded review-and-fix cycle over the run's diff, and opens the pull request before reporting out.

It never reopens the plan. There is no interview, no clarifying round, no proposal of a different approach. Whatever was settled upstream is the input, and the skill's whole job is to turn that into a reviewed commit and a pull request. That is what separates it from typing "build this" at a fresh [agent](https://www.aihero.dev/ai-coding-dictionary/agent), which will happily redesign the work while it builds it.

## When to reach for it

Type `/implement`, or the agent reaches for it automatically when you ask it to implement or build a ticket, issue, or spec whose design is settled. Because it is model-invoked, another skill can run it as a step. The in-progress `implement-with-demonstrate` runs it with `--no-pr`, puts the result through a human-style QA loop, and opens the pull request itself at the end. Wherever [ask-matt](https://aihero.dev/skills-ask-matt) or [to-tickets](https://aihero.dev/skills-to-tickets) says "then `/implement` per ticket", typing it yourself still works.

Where the work currently lives decides whether this is the right skill:

| The work is… | Reach for |
| --- | --- |
| A ticket on the tracker | `/implement #42`, one ticket per [session](https://www.aihero.dev/ai-coding-dictionary/session), sequentially with [cleared](https://www.aihero.dev/ai-coding-dictionary/clearing) context or side by side, since each run gets its own worktree |
| A spec, not yet split up, and the build spans sessions | [to-tickets](https://aihero.dev/skills-to-tickets) first, then `/implement` per ticket |
| A spec, and the build is small | `/implement` directly against the spec |
| Only in the conversation you just had, and it's still small | `/implement` right there, in the same window |
| Not written down anywhere yet | [grill-with-docs](https://aihero.dev/skills-grill-with-docs), or [grill-me](https://aihero.dev/skills-grill-me) if there's no codebase |
| One concrete behaviour you want test-first, with no spec | [tdd](https://aihero.dev/skills-tdd) directly |
| Already built, and you want it checked | [code-review](https://aihero.dev/skills-code-review) directly |

The same-session case is worth naming because the skill's own first line doesn't cover it. `SKILL.md` says "the spec or tickets", which nudges the [model](https://www.aihero.dev/ai-coding-dictionary/model) to go hunting for a file that doesn't exist. If the plan lives only in the thread, say so when you invoke it.

## Prerequisites

`implement` never commits to the checkout you run it from. It creates a git worktree and branch named after the work and commits there, so uncommitted changes in your checkout stay behind and several runs can share one repository. The worktree starts the way a fresh clone does, so the run installs dependencies and copies over gitignored local config such as `.env.local` before it builds. Under Claude Code it uses the harness's own worktree tool; elsewhere it runs `git worktree add` into `.worktrees/`. Opening the PR needs the host's CLI, `gh` or `glab`, authenticated against the remote. Without one the run ends at the commit and says so. `--no-pr` asks for that same stop on purpose.

If the tickets came from [to-tickets](https://aihero.dev/skills-to-tickets), the tracker they live on was configured by [setup-matt-pocock-skills](https://aihero.dev/skills-setup-matt-pocock-skills). `code-review` reads the same configuration to find the originating spec at close-out.

## What one run does

A run is seven beats, in order:

1. Create a worktree and branch named after the work, and make the worktree runnable.
2. Read the ticket or spec and work out the seams.
3. Drive [tdd](https://aihero.dev/skills-tdd) at the pre-agreed seams, one red-green slice at a time.
4. Typecheck often, run single test files as it goes.
5. Run the full test suite once, at the end.
6. Commit the green build, then run [code-review](https://aihero.dev/skills-code-review) in a bounded fix loop, committing each round.
7. Push the branch and open the pull request, with the close-out report as its body. `--no-pr` stops before this beat.

One run covers one ticket. The tickets [to-tickets](https://aihero.dev/skills-to-tickets) produces are tracer-bullet vertical slices sized to fit a single fresh [context window](https://www.aihero.dev/ai-coding-dictionary/context-window), so the intended rhythm is: clear context, implement one ticket, commit, clear again. Each ticket is self-contained, which is what makes the previous ticket's context disposable. Because every run has its own worktree, the sessions can also run side by side.

## Pre-agreed seams

The idea the skill runs on is the **seam**: the public boundary you observe behaviour at, without reaching inside. Tests live at seams. Working at a seam agreed before any code is written is what keeps the tests durable, because the implementation underneath can be rewritten without the tests moving.

The word "pre-agreed" is doing real work, and it is also the skill's weakest joint. Nothing inside `implement` agrees the seams. `tdd` is the skill that asks, and it refuses to write a test at an unconfirmed seam. So in practice the agreement happens either upstream in the spec, or in the first exchange of the run. If it happens nowhere, the precondition never fires and the run quietly becomes "just write the code". Naming the seams in the spec is what stops that.

## Common questions

**It finished, but my ticket is still open and the acceptance criteria are still unchecked.**

Correct, and expected. `implement` has no completion step. It ends at the pull request and never touches the work item, confirmed on GitHub Issues and on the local markdown tracker, so it is not a tracker integration problem. It also does not act on the findings `code-review` produced, and does not tick the `- [ ]` boxes on the originating issue. Close the ticket and reconcile the criteria yourself. This bites hardest on a dependency chain, because `to-tickets` defines the frontier as tickets whose blockers are all closed. If nothing gets closed, nothing ever becomes visibly unblocked.

**Can I point it at all my tickets at once, or run several in parallel?**

One invocation still builds one ticket. Batch dispatch across a ticket queue and [subagent](https://www.aihero.dev/ai-coding-dictionary/subagent) fan-out are both requested repeatedly, and neither exists. Parallel sessions, though, are now the intended way to work a frontier of unblocked tickets. Every run creates its own worktree and branch, so two sessions never share a working directory, an index, or a HEAD. That is the fix for a field report of several `/implement` sessions in one checkout, where a `git commit --amend` in one session landed on another session's commit, a stash vanished from `refs/stash`, and commits landed on the wrong branch, all in one afternoon across three issues. One caveat survives: `refs/stash` is shared across worktrees, so keep stash out of parallel runs.

**Does it open a pull request?**

Yes, at the end of every run. Earlier versions committed to the current branch and stopped, which several people found too eager, since the code landed before they had a chance to verify it. The run still commits first, because the review loop only sees committed work. After the last review round it pushes the worktree's branch and opens the PR with the close-out report as its body. Pass `--no-pr` to stop at the close-out instead. The in-progress `implement-with-demonstrate` does exactly that, so its PR appears only once the QA loop is finished rather than while demonstrations are still running. The PR references the ticket, but the run never closes the ticket itself.

**`code-review` says it cannot see my changes.**

`code-review` reviews `git diff <fixed-point>...HEAD`, which excludes staged and working-tree changes. Earlier versions of `implement` ran the review before committing, so the diff was empty, and multiple people reported it. The run now pins HEAD at the start and commits the build before the first review round, so the diff is exactly the run's work. When you run `code-review` by hand, commit first, then review against the point you branched from.

Separately, some people deliberately do not want the review inside the run at all, because an agent reviewing the code it just wrote is biased toward its own solution. Running [code-review](https://aihero.dev/skills-code-review) in a fresh session against a fixed point is a legitimate alternative, and is the same reason that skill runs its two axes in separate sub-agents.

**One ticket burned 150k tokens. Am I using it wrong?**

Probably the ticket is too big rather than the skill being misused. A run does codebase exploration, a red-green loop per seam, a full suite, and a review, so a non-trivial ticket exceeding 100k [tokens](https://www.aihero.dev/ai-coding-dictionary/token) is normal rather than a sign something broke. The lever is upstream: right-size the tickets in [to-tickets](https://aihero.dev/skills-to-tickets) so each fits one fresh window. If a single ticket keeps blowing out, split it rather than raising the [effort](https://www.aihero.dev/ai-coding-dictionary/effort) level.

**`/implement #2` in a fresh session worked on something completely unrelated.**

`#2` is resolved against whatever numbered list the agent can see, which in a fresh session may be a todo file, a checklist, or another work list rather than the configured tracker. The resolution is confident rather than fail-closed, so the mistake is not obvious until it has started. Pass the full reference, the issue URL or `owner/repo#2`, and ask it to confirm the title back before it begins.

## The review-fix loop

A run starts by pinning the worktree's first commit; everything the run produces is reviewed against that SHA. Once the build is committed, [code-review](https://aihero.dev/skills-code-review) runs over the run's diff — up to three rounds. Hard findings are always fixed: Spec findings go back through [tdd](https://aihero.dev/skills-tdd) because they are behaviour changes, standards violations are fixed directly because they are refactors under green tests. Judgement-call smells get exactly that — a judgement: the agent fixes the ones it finds relevant and records why it dismissed the rest. Each round's fixes are committed before the next review, and the loop stops early once a round reports no hard findings. The run closes with a report of what was fixed, what was dismissed and why, and anything still open after the cap. Then it pushes the branch and opens the pull request with that report as its body.

## It's working if

- The session opens by reading the ticket or spec and restating what it will build, rather than asking you what to build.
- A worktree and branch named after the ticket appear before any code is written, and every later command runs inside that worktree.
- You can see an actual `/tdd` invocation in the trace, not just tests appearing in the diff.
- Typechecks and single test files run repeatedly during the run, and the full suite runs once near the end.
- The run reaches a commit on the worktree's branch without you prompting it to carry on.
- It ends with a pull request URL in the chat, and the PR body is the close-out report, unless you passed `--no-pr`.
- The diff is one ticket's worth of change: a vertical slice through every layer, not several tickets swept together.

## Where it fits

`implement` is the build step of the main chain, second from the end:

```txt
grill-with-docs → to-spec → to-tickets → implement → code-review
```

Its neighbours are [to-tickets](https://aihero.dev/skills-to-tickets), which produces the tickets it consumes and declares the blocking edges that decide their order; [tdd](https://aihero.dev/skills-tdd), which it drives internally at each seam; and [code-review](https://aihero.dev/skills-code-review), which it runs in its fix loop before opening the pull request. It sits downstream of the planning skills and trusts them. It does not re-validate the shape of what it was handed, so a badly-structured map or a horizontally-layered ticket gets built as written.

That trust is why [wayfinder](https://aihero.dev/skills-wayfinder) merges onto the chain at [to-spec](https://aihero.dev/skills-to-spec) rather than looping its map straight into `implement`. Go straight to `implement` from a map only when the effort turned out genuinely small.

[ask-matt](https://aihero.dev/skills-ask-matt) is the router over the whole set when you are not sure which flow you are in.
