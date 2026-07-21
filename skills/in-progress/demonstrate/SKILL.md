---
name: demonstrate
description: Demonstrate that a change does what was intended — a fresh subagent exercises the behaviour end-to-end and reports product-level evidence (screenshots, CLI transcripts, API responses), not green tests. Learns each project's manual-testing setup (tooling, auth) once and records it in CLAUDE.md.
disable-model-invocation: true
---

# Demonstrate

Produce **evidence** that the *intent* behind a change works — proof an end user would accept, not a green test run. The skill is intent-scoped: it demonstrates the intended behaviour end-to-end regardless of exactly what changed. The diff is at most a hint to where to look — never a baseline to pin, a merge-base to compute, or a gate on what may be exercised.

## Process

### 1. Resolve the intent

Establish what success means from the first source that yields it. A rung whose tool is missing (tracker connector unauthenticated, `gh` absent, no open PR) falls through to the next:

1. **The live session** — invoked mid-conversation, the user's request and the work just discussed are the intent.
2. **The linked tracker issue** — ticket keys from commit messages or the branch name, fetched via the workflow in `docs/agents/issue-tracker.md` (run /setup-matt-pocock-skills if that file is missing).
3. **The open PR's description** — via `gh`.
4. **Inference floor** — derive the intent from the diff and commit messages, and state it explicitly as inferred so the user can correct it.

Condense the result into an **intent brief**: the behaviour to demonstrate, phrased in end-user terms, plus optional where-to-look hints — hints, not boundaries.

**Skip-guard:** when the intent names nothing runtime-observable — documentation, comments, formatting — report that there is nothing to demonstrate and stop. Evidence is gathered, never fabricated.

Completion criterion: an intent brief in end-user terms with its source named (flagged as inferred on rung 4), or a declared nothing-to-demonstrate.

### 2. Resolve the environment brief

Manual demonstration stands on project knowledge the diff can't supply. For each surface the intent touches — backend API, web UI, mobile app, CLI — two questions need answers before the evidence agent is dispatched:

- **Tooling and entry point.** What exercises the surface by hand — `curl` against which base URL, a browser at which URL, which emulator or simulator command — and how to start the system locally when it isn't already running.
- **Auth.** Whether the surface is auth-gated for local testing, and if gated, the working way past the gate: a seeded test user and where its credentials live, a token-minting command, a dev bypass flag. *Not gated* is an answer too — record it and the question never gets asked again.

Only chase answers the intent actually needs: a pure library change demonstrable with a scratch script has no auth question to ask.

Consult sources in order, stopping at the first that answers each question:

1. **The project's CLAUDE.md** — the `## Manual testing` section a previous invocation recorded, and anything it points to.
2. **The live session** — the user already explained it, or the system is already running in this conversation. A fresh statement from the user beats a stale record; update the record when they conflict.
3. **The repo's own docs** — README run instructions, launch configs, Makefile targets. Documented knowledge counts; inferring an auth method from source code does not.
4. **Ask the user** — one round of questions covering exactly the gaps that remain. Never guess credentials or hunt for auth bypasses instead of asking.

Every answer found below rung 1 gets **recorded** in the project's CLAUDE.md under a `## Manual testing` section (create the file or the section if missing), so the next invocation self-serves at rung 1. Record pointers, never secret values — CLAUDE.md is committed: `credentials in .env.local under TEST_USER_*` belongs there; the password itself never does. Shape it like:

```markdown
## Manual testing

- **API**: `pnpm dev` serves http://localhost:3000; exercise with `curl`.
- **Web UI**: browser at http://localhost:3000 after `pnpm dev`.
- **Auth**: gated; log in as the seeded user from `pnpm db:seed` — credentials in `.env.local` (`TEST_USER_EMAIL` / `TEST_USER_PASSWORD`).
```

Condense the answers into an **environment brief**: per touched surface, the tooling, entry point, start-up command, and auth method.

Completion criterion: tooling and auth answered for every surface the intent touches, and every newly-learned answer persisted to CLAUDE.md.

### 3. Run the evidence agent

Evidence always comes from a fresh `general-purpose` subagent — even when this session wrote the change. A verifier that didn't write the code carries none of the author's assumptions about why it works, and its exploration stays out of this context.

1. Create the evidence directory: `mktemp -d` — never a hardcoded `/tmp` path.
2. In [EVIDENCE-BRIEF.md](EVIDENCE-BRIEF.md), fill `{{INTENT}}` with the intent brief, `{{ENVIRONMENT}}` with the environment brief, and `{{EVIDENCE_DIR}}` with that directory, then send everything below its rule as the subagent's prompt, verbatim.

Completion criterion: the subagent returned all four report sections — `testing_summary`, `tested`, `artifacts`, `findings`.

### 4. Relay the evidence

A subagent that Reads a screenshot renders it only into its own context; the user sees an image only when *this* session Reads it.

- `Read` every artifact path the subagent returned, so visuals render inline to the user.
- Relay `testing_summary` verbatim, the `tested` list, short text evidence inline, and every finding.
- When a finding reports that the recorded environment knowledge failed — the documented auth method no longer works, the entry point moved — get the correction from the user and update the `## Manual testing` record before finishing, so the record heals instead of rotting.
- The evidence directory is ephemeral by design: the session is the delivery surface, and the OS reclaims the temp dir on its own schedule. Nothing is copied into the repo, the PR, or a ticket; no cleanup step exists.

Completion criterion: every returned artifact Read into this session, and `testing_summary` plus all findings relayed — no evidence left stranded in the subagent.
