# Documents

The delta for documents longer than a page: architecture and solution documents, proposals, decision records, anything delivered as a .docx or Google Doc. The voice and the tests live in [`SKILL.md`](SKILL.md). Documents are external register.

## Default shape

Four to six top-level sections, each readable on its own by someone who opens the document in the middle:

1. **Introduction and purpose**: what the system or proposal is in one paragraph, who the document is for, what it covers, and what it deliberately leaves out.
2. **Overview**: one diagram, a two-column table of components (Component | Role, one line each), the main flows as numbered steps with the actor first ("The worker calls the load API..."), and a **boundaries** list of what the system does not do.
3. **Data** (or the core section of a proposal): per store or per topic, what is kept, why, and for how long.
4. **Security** or **Risks**, then **Assumptions and open questions**, each assumption stated so the reader can confirm or reject it.

A header carries title, date, version and authors. The document starts with its subject, never with its own importance.

## Depth

The default is the compact shape above. Go deeper (table of contents, C4 context and container views, a subsection per entity, data flows each with an overview, an explanation and diagrams) only when the reader asked for that depth: a compliance reviewer, a client CTO who wants a technical blueprint. Depth is added per section the reader needs, not uniformly.

## References inside the document

- A section makes sense without following any reference.
- References go by section name ("see Failed-event replay"), one hop only: the referenced section holds the answer itself.
- A decision record opens with an executive summary that is the decision plus its reason in a few sentences; the options and the evidence follow once, in the body.

## Recommendations

A recommendation states the perspective it was made from and what it did not consider ("from a risk and effort perspective; regulatory requirements were not assessed"), so the reader knows which part is theirs to verify.
