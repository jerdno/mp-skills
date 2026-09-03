# The worktree under Claude Code

How the first step of [SKILL.md](SKILL.md), the work's own worktree, runs when this skill runs in Claude Code.

## Use the harness's worktree tool

Claude Code has native worktree support. The `EnterWorktree` tool creates a worktree under `.claude/worktrees/` on a new branch and switches the session's working directory into it, so every later command, subagent, and skill run (/tdd, /code-review, a /demonstrate that follows) happens inside the worktree with nothing to `cd` into. The tool asks to be used only on explicit instruction, and this skill is that instruction. Call it with `name` set to the work's name (letters, digits, dots, underscores, and dashes). It replaces both the manual `git worktree add` and the `.git/info/exclude` entry.

The branch's base follows the `worktree.baseRef` setting: `fresh`, the default, branches from `origin/<default-branch>`; `head` branches from the current local HEAD. Either way the review baseline is `git rev-parse HEAD` inside the worktree once it exists.

## Leave it in place

Stay in the worktree through the close-out. `ExitWorktree` is the user's call: at session end Claude Code asks them whether to keep or remove the worktree, and a skill that follows this one, such as /demonstrate, needs it still there.
