# Slack

The delta for Slack messages, thread replies and DMs. The voice and the tests live in [`SKILL.md`](SKILL.md).

## Shape

- A new post opens with a greeting or a one-line frame that ends in a colon, then the content: "hello, so that everybody is in the loop:", "some important notes:", "@Name re the scope table:". A reply starts with the answer.
- Paragraphs of one to three sentences with a blank line between them. Bullets as the voice rules say, nested to at most three levels; a bullet is one point, its sub-bullets the evidence or the reason.
- TLDR only when the message runs past roughly eight lines. It goes on top ("TLDR:" then two or three bullets) when the message reports, so the reader can stop there. It goes at the bottom ("So TLDR from my point of view: ...") when the message argues toward a conclusion.
- Replying to a message with several points: quote the line you answer with ">" and put the answer under it, one pair per point.
- Commands, payloads, JSON and error output go in a code block, never inline in a sentence.
- Plain text: paragraphs, bullets, quotes and code blocks are the whole toolkit. One :smile: at most, internal chat only.

## What goes in

- A reply answers what was asked and adds only what the asker would ask next.
- An update lists what changed since the last one, what is blocked and by whom, and what happens next.
- A decision message is the decision, one to three reasons, and what it means for the reader.
- A problem description is what you observed, what you tried, what you think is going on (marked as your reading), and the question.
- A mention has a reason the reader can see: an action ("@Name can you please organise the sync"), a question, or adding someone ("I add @Name to the thread so they can comment").

## Register by thread

- Internal channel post: full sentences, greeting optional.
- Internal DM or thread reply: casual is fine (lowercase opener, "fyi", "wdyt"), still complete thoughts.
- Client-facing channel or DM: external register from `SKILL.md`, same shape.
