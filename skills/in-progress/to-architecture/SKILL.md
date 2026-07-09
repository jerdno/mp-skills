---
name: to-architecture
description: Turn a technical design discussion into one coherent implementation target, published through the configured project tracker.
disable-model-invocation: true
---

# To Architecture

Create a **technical target**: the coherent design an implementer needs before work is sliced. It complements a spec (PRD) and decision records; it does not implement code or repeat product discovery.

## Process

### 1. Ground the target

Read the /codebase-design skill first — its vocabulary and principles (deep modules, seams, adapters, the deletion test) govern step 2.

Read the project glossary, relevant decision records, tracker configuration, existing design material, and relevant source. If an issue, URL, spec, or file is supplied, read it fully; otherwise work from the current discussion and repository evidence. Use the project's available discovery tools; do not require a particular tool or provider.

The issue tracker configuration should have been provided to you — run /setup-matt-pocock-skills if not.

Completion criterion: every supplied source and every existing decision record relevant to the target is accounted for.

### 2. Resolve the design

Identify modules, interfaces, seams, adapters, ownership, invariants, state/control/data flow, lifecycle/failure behavior, persistence, and test seams. Apply /codebase-design's deletion test to suspected shallow modules, and its adapter rule: treat one adapter as hypothetical, introducing a real seam only where behavior genuinely varies.

This skill may run its own design interview — it does not require a prior design discussion. When a material architecture decision is unresolved, put it to the user one question at a time, each with a recommended answer. Do not publish while an implementer would need to make a material architecture decision.

Completion criterion: the target distinguishes locked decisions from implementation discretion and leaves no material design choice unresolved.

### 3. Publish the technical target

Fill in [ARCHITECTURE-TEMPLATE.md](ARCHITECTURE-TEMPLATE.md), including its Mermaid diagram. Publish one tracker artifact titled `Architecture: <topic>` through the project's configured tracker. Link the parent spec (PRD) when one exists. Apply the `ready-for-agent` triage label only when the project's tracker guidance defines one.

Read back the published artifact and confirm its title, references, and every template section are present. Do not create code, migrations, or decision records. List decision-record candidates for the user to approve separately.

Completion criterion: a new implementer can identify the target modules, interfaces, seams, invariants, flows, adapters, test surface, and allowed discretion from this artifact alone; the Mermaid diagram makes the primary relationships visually clear.
