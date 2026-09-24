# In Progress

Beta. These skills are public on purpose — try them and tell me what breaks. They're excluded from the plugin and the top-level README until they graduate to a stable bucket, they get no docs pages, and they can change or disappear without warning.

The plugin won't give you these. Install one directly:

```bash
npx skills@latest add mattpocock/skills --skill=<name>
```

- **[loop-me](./loop-me/SKILL.md)** — Grill yourself into implementable workflow specs over multiple sessions, using the current directory as a stateful workspace. User-invoked.
- **[writing-beats](./writing-beats/SKILL.md)** — Shape an article as a journey of beats, choose-your-own-adventure style. Pick a starting beat, write only that beat, then pivot to the next, until the article reaches a natural end.
- **[writing-fragments](./writing-fragments/SKILL.md)** — Grilling session that mines you for fragments — heterogeneous nuggets of writing — and appends them to a single document as raw material for a future article.
- **[writing-shape](./writing-shape/SKILL.md)** — Take a markdown file of raw material and shape it into an article paragraph by paragraph, arguing format choices at each step.
- **[writing-for-humans](./writing-for-humans/SKILL.md)** — Write Slack messages, Confluence pages, documents and emails the way one specific author writes: only what the reader needs to decide or act, assumptions marked, one voice across media, with a medium file loaded only for the medium in play. Model-invoked. It encodes one author's voice, so fork it to encode yours.
- **[claude-handoff](./claude-handoff/SKILL.md)** — Hand the current conversation off to a fresh background agent that picks up the work immediately, seeded with a handoff summary via `claude --bg`. User-invoked.
- **[setup-ts-deep-modules](./setup-ts-deep-modules/SKILL.md)** — Wire dependency-cruiser into a TypeScript repo so each package is a deep module — implementation hidden in subfolders, reachable only through its entry-point files, tests exercising it through those. User-invoked.
- **[to-architecture](./to-architecture/SKILL.md)** — Distill a technical design discussion into a single implementation target (modules, seams, invariants, flows, locked vs. discretionary decisions) published to the project tracker. User-invoked.
- **[demonstrate](./demonstrate/SKILL.md)** — QA a change like a human tester: a fresh subagent runs the product in its existing local dev setup, drives the real UI or API through happy-path and edge-case scenarios, and delivers screenshots, videos, and request/response transcripts as a reviewable HTML report. Learns each project's manual-testing setup once, recording it in docs/agents/demonstrate.md.
- **[implement-with-demonstrate](./implement-with-demonstrate/SKILL.md)** — Implement a spec or ticket with `/implement`, then QA it like a human tester with `/demonstrate`, at most twice, with one fix round in between. The pull request opens only at the end, carrying the verdict. Needs `implement` and `demonstrate` installed. User-invoked.
