---
"mattpocock-skills": patch
---

`writing-for-agents`: name parametric knowledge as a source of truth, so the no-op test catches expository lines and not just instructions.

- Add a **parametric knowledge** bullet to `Pruning`, beside the existing `environment` / `cache` one. The agent has already read the public web, so a passage explaining a widely-documented tool, protocol or language restates what it held before the run began. The keep-condition is the **delta** from the model's priors: the version whose behaviour changed, the fact the cutoff makes stale, the local convention that contradicts the common one, the pick between two conventions it holds equally. The leading word is the house term the dictionary and `teach` already use.
- Widen the **no-op** test from "an instruction the model already obeys by default" to any line the model does not need, so it grades facts as well as instructions. The docs page already claimed this lens — "it spends most of its words explaining what the model already knows" — while `SKILL.md` only ever applied it to instructions, and nobody runs a behavioural test on a paragraph that isn't phrased as one.
- `relevance` drops "mere exposition" from its examples, since the new bullet owns exposition — one meaning, one place.
- Re-sync the docs page: the **delta** in the `Pruning` lever, the question itself in `Common questions`, and a checkable tell in `It's working if`.
