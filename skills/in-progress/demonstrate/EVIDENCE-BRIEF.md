# Evidence brief

Fill `{{INTENT}}`, `{{ENVIRONMENT}}`, and `{{EVIDENCE_DIR}}`, then send everything below the rule, verbatim, as the evidence agent's prompt.

---

You are validating a code change by demonstrating it. Examine the repository and produce the evidence yourself.

Intent — what success means:

{{INTENT}}

Environment — how to exercise this system, resolved from the project's records and the user:

{{ENVIRONMENT}}

Task:

- Decide what evidence or artifacts would clearly demonstrate the intent is satisfied. Unit tests passing is not sufficient evidence by itself.
- Demonstrate the intent working end-to-end in a way consistent with how an end user would actually experience it.
- Prefer product-level artifacts: screenshots, GIFs, videos, rendered UI, CLI transcripts, API responses, persisted database state, logs, or other outputs that directly show the intended behaviour working.
- For UI, HTML, CSS, browser, visual-layout, or copy-placement changes, capture reviewer-visible visual evidence: screenshots, images, videos, GIFs, or rendered HTML showing the actual end-user surface. DOM snapshots, selector assertions, and text-only render summaries are not substitutes for visual evidence when a rendered surface is available. If a UI-facing change ends up with no visual artifact, state why in `testing_summary`.
- Write evidence files into this directory and nowhere else: {{EVIDENCE_DIR}}
- Do not move, commit, or modify source files only to make evidence linkable; record evidence file paths exactly where you created them.
- Only use command output as an artifact when that output directly demonstrates the end-user experience or the intended behaviour. Generic pass/fail, coverage, or clean-worktree output is not sufficient evidence.

Strategy — take the first rung that yields sufficient evidence:

1. Look for existing tests that would generate sufficient evidence; if they exist, run the smallest relevant set.
2. If no existing test produces sufficient evidence, write or improve a test so that it does.
3. If automated testing cannot produce the needed evidence, execute manual verification steps — using the tooling, entry points, and auth method from the environment section — and record the evidence-producing steps you performed.
4. If sufficient evidence is not possible, report a warning finding explaining what evidence is missing and what the user must decide.

Rules:

- Manual verification follows the environment section. When an instruction there fails or a surface you need isn't covered, do not guess credentials, brute-force logins, or hunt for auth bypasses — report the gap as a `warning` finding stating exactly what is missing or broken, so the calling session can correct the project's record.
- Never quote secret values (passwords, tokens, API keys) in artifacts or in your report; reference where they live instead.
- If tests fail, determine whether the problem is a real product/code failure, a setup/environment problem, or a flaky/infrastructure issue. Fix setup and environment problems and retry. Product code is not yours to fix: a change that genuinely doesn't work becomes an `error` finding.
- Any test you wrote or improved to produce evidence must be flagged as an `info` finding naming the test file — a just-written test is not independent proof, and the user must see it for what it is.
- Do NOT run linters, formatters, or static analysis tools; stay on demonstrating the intent.
- Before finishing, remove any transient artifacts your work created in the working tree (downloaded models, caches, build outputs, large binaries, generated data directories). Keep intentional source or test-file changes, and leave the evidence directory untouched.

Report — your final message is consumed by the calling session, so return exactly these four sections:

## testing_summary

One high-signal natural-language sentence accounting for the complete run: what you exercised, the evidence gathered, and the overall result. No raw logs, no noisy counts.

## tested

The exact tests, manual checks, and evidence-producing steps you ran, as concrete commands or test selectors wrapped in backticks. Never empty.

## artifacts

One entry per artifact: `kind` (screenshot | gif | video | image | log | command-output | other), `label`, `path` (files — visuals go in the evidence directory), `url` (when externally visible), `content` (short text worth showing inline). Empty when you produced no reviewer-visible evidence.

## findings

Actionable items only: test failures, unfixable setup issues, environment instructions that failed or were missing, flaky tests you identified, missing evidence that prevents demonstrating the intent, or tests you wrote yourself. Each: `severity` (error | warning | info), `file` and `line` where relevant, `description`. Passing tests, test counts, and coverage are not findings. Empty when clean.
