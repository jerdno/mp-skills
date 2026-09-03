---
name: demonstrate
description: QA a change like a human tester — a fresh subagent runs the product in its existing local dev setup, drives the real UI or API through happy-path and edge-case scenarios, and delivers screenshots, videos, and request/response transcripts as a reviewable HTML report. Learns each project's manual-testing setup once and records it in docs/agents/demonstrate.md. Use when the user asks to demonstrate, QA, or manually test a change, or wants evidence that it works in the running product.
---

# Demonstrate

Demonstrate that the *intent* behind a change works the way a human QA would establish it: by using the running product — clicking the real UI, calling the real API — and reporting what actually happened, scenario by scenario, so a PR reviewer can judge whether the feature works. Tests assert; a demonstration *shows*. An automated test run — existing, newly written, or generated for the occasion — is never demonstration evidence.

The skill is intent-scoped: it demonstrates the intended behaviour end-to-end regardless of exactly what changed. The diff is at most a hint to where to look — never a baseline to pin, a merge-base to compute, or a gate on what may be exercised.

## Process

### 1. Resolve the intent

Establish what success means from the first source that yields it. A rung whose tool is missing (tracker connector unauthenticated, `gh` absent, no open PR) falls through to the next:

1. **The live session** — invoked mid-conversation, the user's request and the work just discussed are the intent.
2. **The linked tracker issue** — ticket keys from commit messages or the branch name, fetched via the workflow in `docs/agents/issue-tracker.md` (run /setup-matt-pocock-skills if that file is missing).
3. **The open PR's description** — via `gh`.
4. **Inference floor** — derive the intent from the diff and commit messages, and state it explicitly as inferred so the user can correct it.

Condense the result into an **intent brief**: the behaviour to demonstrate, phrased in end-user terms, any must-try scenarios the user named, plus optional where-to-look hints — hints, not boundaries.

**Skip-guard:** when the intent names nothing runtime-observable — documentation, comments, formatting — report that there is nothing to demonstrate and stop. Evidence is gathered, never fabricated.

Completion criterion: an intent brief in end-user terms with its source named (flagged as inferred on rung 4), or a declared nothing-to-demonstrate.

### 2. Resolve the environment brief

The demonstration runs in the project's existing local dev setup, exactly as a developer runs it — the evidence agent takes the environment as found, so everything it needs must be resolved here first. For each surface the intent touches — backend API, web UI, mobile app — four questions need answers before the evidence agent is dispatched:

- **Start.** The command that brings the system up locally when it isn't already running, including documented seed steps.
- **Exercise.** How a human works the surface by hand — `curl` against which base URL; a browser at which URL, driven by which tool; which simulator or emulator and which scheme.
- **Auth.** Whether the surface is auth-gated for local testing, and if gated, the working way past the gate: a seeded test user and where its credentials live, a token-minting command, a dev bypass flag. *Not gated* is an answer too — record it and the question never gets asked again.
- **Wiring.** What the local setup is connected to, per provider: a sandbox tenant of the real service, a provider-official emulator, an existing stub config. The local env config already answers this (docker compose, `.env`, `application-local.yaml`) — read it there, and record only where to look, never a copy of its contents. The report states what the demo ran against, so the reviewer can weigh the evidence.

Only chase answers the intent actually needs: a pure library change demonstrable with a scratch script has no auth question to ask.

Consult sources in order, stopping at the first that answers each question:

1. **The [record](#the-record)** — the project's `docs/agents/demonstrate.md`: what a previous invocation learned, and anything it points to.
2. **The live session** — the user already explained it, or the system is already running in this conversation. A fresh statement from the user beats a stale record; update the record when they conflict.
3. **The repo's own docs** — README run instructions, launch configs, Makefile targets. Documented knowledge counts; inferring an auth method from source code does not.
4. **Ask the user** — one round of questions covering exactly the gaps that remain. Never guess credentials or hunt for auth bypasses instead of asking.

Every answer found below rung 1 gets written into [the record](#the-record), so the next invocation self-serves at rung 1.

Condense the answers into an **environment brief**: per touched surface, the start command, exercise recipe, auth method, and wiring.

Completion criterion: start, exercise, auth, and wiring answered for every surface the intent touches, and every newly-learned answer written into the record.

### 3. Run the evidence agent

Evidence always comes from a fresh `general-purpose` subagent — even when this session wrote the change. A verifier that didn't write the code carries none of the author's assumptions about why it works, it designs the QA scenarios with fresh eyes, and its exploration stays out of this context.

1. Create the evidence directory: `mktemp -d` — never a hardcoded `/tmp` path.
2. In [EVIDENCE-BRIEF.md](EVIDENCE-BRIEF.md), fill `{{INTENT}}` with the intent brief, `{{ENVIRONMENT}}` with the environment brief, and `{{EVIDENCE_DIR}}` with that directory, then send everything below its rule as the subagent's prompt, verbatim.

Completion criterion: the subagent returned either a QA report (`testing_summary`, `ran_against`, `scenarios`, `artifacts`, `findings`) or a `blocked` report.

### 4. Decide on blockers

The evidence agent never builds its way around a blocker — it escalates, and the user decides before more time is spent. When the report is `blocked`, or any scenario carries a `blocked` verdict:

- Relay what the agent tried, the exact failure, and each offered option with the evidence fidelity it sacrifices.
- The user picks: stop the demonstration, fix the environment themselves, or approve a workaround.
- Fold the decision into the environment brief — naming any approved workaround explicitly, which is what triggers the brief's degraded-evidence labelling — and re-dispatch a fresh evidence agent.
- A blocker rooted in a stale record heals the record before re-dispatch.

Completion criterion: no `blocked` report or verdict left without a user decision, and every approved decision folded into a re-dispatch (or the user chose to stop).

### 5. Deliver the demonstration

The demonstration is delivered as an HTML report the user can review scenario by scenario, plus a short chat summary.

- **Render the report** with the `/lavish` skill when the session has it; otherwise hand-write a plain HTML page into the evidence directory and give the user its path. Either way it carries: the intent; what the demo ran against (`ran_against`, degraded labels included); a per-scenario table — expected vs. actual, the concrete steps, the verdict; screenshots embedded beside their scenarios; videos embedded or linked; request/response JSONs formatted; the findings.
- **Summarise in chat**: relay `testing_summary` verbatim, the per-scenario verdict list, every finding, and where the report is.
- When a finding reports that the recorded environment knowledge failed — the documented auth method no longer works, the entry point moved — get the correction from the user and heal the record before finishing, rather than leaving it to rot.
- The evidence directory is ephemeral by design: the session is the delivery surface, and the OS reclaims the temp dir on its own schedule. Nothing is copied into the repo, the PR, or a ticket; no cleanup step exists.

Completion criterion: the HTML report delivered with every scenario, artifact, and finding in it — no evidence left stranded in the subagent.

## The record

`docs/agents/demonstrate.md` is the project's **manual-testing record**: the start, exercise, auth, and wiring answers earlier invocations learned. A skill-owned file rather than a CLAUDE.md section, so knowledge needed only when demonstrating never rides in every conversation's context.

Write the record — creating it, adding an answer, or healing a stale entry — with the `/writing-for-agents` skill: it is a document an agent consumes. The record adds one rule of its own: pointers, never secret values, because the file is committed — `credentials in .env.local under TEST_USER_*` belongs there; the password itself never does. Shape it like:

```markdown
# Manual testing

- **API**: `pnpm dev` serves http://localhost:3000; exercise with `curl`.
- **Web UI**: drive http://localhost:3000 with the session's browser tools.
- **Auth**: gated; log in as the seeded user from `pnpm db:seed` — credentials in `.env.local` (`TEST_USER_EMAIL` / `TEST_USER_PASSWORD`).
- **Wiring**: `docker-compose.yml` and `.env.local` name each provider connection.
```
