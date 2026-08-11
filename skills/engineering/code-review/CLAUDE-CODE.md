# Dispatch under Claude Code

Engine routing for the two axis sub-agents of [SKILL.md](SKILL.md) step 4 when this skill runs in Claude Code.

## Engine — Codex by default, `general-purpose` as backup

If the `codex:codex-rescue` agent type is available (the OpenAI Codex plugin is installed), use it for both axes. Use `general-purpose` only when that agent type isn't listed.

`codex:codex-rescue` is a thin forwarder to the Codex CLI, so when using it shape each axis prompt accordingly:

- Include the routing flag `--wait` in the request so the run stays in the foreground and the full review comes back as the agent's reply — a background run returns only a job stub, which breaks step 5. Also tell the agent to give its Bash call the maximum timeout (600000 ms); a Codex review can outlive the default.
- State explicitly that this is a **read-only review — make no edits** (the forwarder otherwise defaults to a write-capable run).
- Keep the prompt fully self-contained. Codex runs in the same working directory, so the diff command, standards-file paths, and spec path work as-is — but paste the smell baseline and any tracker-fetched spec contents in full, exactly as you would for `general-purpose`.

The axis briefs in step 4 are engine-agnostic — include the same content either way.

## Fallback

If a Codex axis run errors, returns nothing, or returns a setup/auth-required message instead of findings, re-run just that axis on `general-purpose` with the same brief (minus the Codex routing lines). Note the substitution in the final report, and if the cause was setup/auth, point the user at `/codex:setup` once so the default path works next time.
