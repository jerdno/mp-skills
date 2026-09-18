---
name: writing-for-humans
description: Write or rewrite text a person will read - a Slack message, Confluence page, document or email - the way the user writes it: only what the reader needs, assumptions marked, one voice across media. Use when asked to write up, draft, post, reply, summarise for someone, or make an AI draft sound like them.
---

Write for a human reader the way the user writes: say what we know, mark what we assume, link what exists elsewhere, and stop. The reader is busy and already has context. Every line either helps them decide or act, or it goes.

This file carries the voice and the tests every medium shares. Read the medium file before drafting, and only the one you need:

- Slack message, thread reply or DM: [`SLACK.md`](SLACK.md)
- Confluence page: [`CONFLUENCE.md`](CONFLUENCE.md)
- Document longer than a page (architecture, proposal, decision record): [`DOCUMENTS.md`](DOCUMENTS.md)
- Email: [`EMAIL.md`](EMAIL.md)

## Steps

1. **Fix the reader.** Name who reads this and what they will do with it, then pick the register (below). If the audience is unclear and the two registers would differ, ask one question; otherwise ask nothing. Done when you can say in one line who reads it and what they do next.
2. **Collect what the reader needs.** The facts, the decision and its reason, the open questions with the assumption you work under, the next step and its owner, the ask. Done when every item traces to something the reader will decide or do.
3. **Draft** in the voice below and in the medium's shape.
4. **Pass line by line, three tests.** _Known_: do we actually know it, or is it a feeling, a generic truth, or a claim we cannot back? _Needed_: does this reader need it to decide or act, or do they already have it? _Once_: is it already said elsewhere in the text? A line that fails is cut, turned into a marked assumption, or replaced by a link. The usual casualty is **over-reporting**: detail nobody asked for, a metric for its own sake, a section because a template had one. Last, read it once as the recipient and remove what would make them suspect a model wrote it: a word from one of the table's categories, a summary that repeats the body, a closing that offers help instead of asking for something, a list of exactly three. Done when every line passes and the text ends on the ask or the next step.
5. **Return the text ready to paste**, nothing before or after it. The exception is a user who asked for options or for what changed.

Rewriting an existing draft is the same loop with step 3 replaced: keep its facts, drop its framing, and reshape it into the medium's shape.

## The voice

- Everyday words: use, help, many, if, because, also. The verb is "is" or "has". A sentence starts at its subject. A word that grades importance is replaced by the fact or the number it stands for, a promotional adjective by the neutral description, and a metaphor noun by the concrete thing. The precise technical term where one exists, and the same word for the same thing throughout. The word categories below are the checklist for the line-by-line pass.
- One idea per sentence. A qualifier goes in parentheses (unless descoped), a separated thought gets a comma or a new sentence, the dash is a spaced hyphen ( - ), and a colon introduces a list, an example or a TLDR. A colon used as a connector ("The reason is simple: the API is down") becomes a comma or a new sentence ("The API is down, so...").
- Facts stated flat, without hedging. Opinions and guesses carry one marker per claim, "imo", "afaik", "probably" or "my assumption is", then the claim stated flat; "could potentially possibly" is "probably". Unknowns named as unknowns: "I don't know yet", "not sure here", "correct me if I'm wrong".
- Concrete over abstract: the number, the ID, the name, the date, the link. "-8 MD engi and -1 MD devops, so -9 MDs in total" rather than "significant savings".
- A claim carries its source, a person or a document, or is marked as your own reading. "Best practice is", "it is generally recommended", "experts agree" become "the provider's API docs state", "the client's CFO said on the call", "Peter confirmed in the thread", or "my reading is".
- The point stated directly, in the natural number of items, listed rather than spanned ("A, B and C", not "from A to C"). "Not just a fix but a redesign" is "a redesign". A sentence ends where the fact ends: "..., ensuring compliance" is dropped, or becomes its own sentence with the reason ("This keeps the account blocked until the compliance review is done.").
- Active voice with the actor named: "the vendor changed the setup", not "the setup was changed"; "we decided", not "it was decided"; "Peter implemented the retry", not "the retry has been implemented".
- Written at the level the reader operates on, not the level the work happened on. The reviewer needs processed/failed, not the state machine behind it.
- Anything that already exists gets a link, not a retelling: the doc, the ticket, the thread, the README.
- Disagreement stated plainly with the reason: "I wouldn't write it that way. A few things:". Agreement in two words: "recon: I agree". A comparison ends with what you would pick and why: "I would go with SQS, one consumer at our volume does not justify a cluster", or, when it is a wash, "no strong preference; Kafka only if a second consumer appears".
- Next steps carry an owner. Decisions that are not yours are handed over explicitly: "how much we want to earn back now, I will leave up to you".
- A short greeting opens a new message or email (hello, hi, hello all); a reply in a thread starts with the content. The close is the ask, the next step, or "let me know if I got something wrong". Nothing restates the body.
- "I" for your own work, opinion or assumption. "We" when a team did it or owns it.
- Bullets when items are parallel or the reader will compare them (options, reasons, open items, steps); prose for one argument, a nuance, or a reply that fits in three sentences. Nested bullets only when a point carries its own reasons.
- Say it once. A long text gets one TLDR; the body does not repeat it and there is no closing summary.
- Bold marks a decision or an estimate, never a label. Headings in sentence case. Importance is shown by putting the line first, not by formatting it.
- The language of the thread or request, whichever the reader uses. The rules above hold in any language.

### Words that go

Each row is a category of word an AI draft reaches for, a few examples of it, and what replaces it. The category is the rule and the examples are there to recognise it by: a word that belongs to a category goes, and takes that category's replacement, whether or not the table lists it. So "paramount" goes the way "crucial" does, and "game-changing" the way "groundbreaking" does. The pass asks of each word which category it falls in.

| Category | Examples | What replaces it |
| --- | --- | --- |
| Grading words | significant, crucial, critical, key, pivotal, robust, seamless, comprehensive, powerful, essential | the fact or the number the word stands for; if there is none, the word alone goes |
| Puffery phrases | a testament to, a pivotal moment, the evolving landscape, sets the stage for, plays a vital role, deeply rooted, at the forefront | what happened, in one plain sentence |
| Promotional adjectives | groundbreaking, cutting-edge, innovative, state-of-the-art, renowned, vibrant, stunning, best-in-class | the neutral description of what it is or does |
| Fancy verbs | leverage, utilize, facilitate, delve, showcase, underscore, foster, enhance, streamline, ensure, empower | the everyday verb for the action: use, help, look at, show, stress, improve, simplify, make sure, let |
| "Is" substitutes | serves as, stands as, acts as, boasts, features, represents | is, has |
| Connectives and fillers | additionally, furthermore, moreover, in order to, it is important to note that, it is worth noting, needless to say | also, to, or nothing |
| Metaphor nouns | north star, flywheel, substrate, wedge, vector, journey, ecosystem, landscape (abstract), paradigm | the concrete thing: the goal, the loop, the base, the way, the market, the systems |

## Registers

- **Internal** (colleagues, internal channels and DMs): abbreviated markers are fine (imo, afaik, tbh, fyi, wdyt), lowercase openers in casual threads, an occasional :smile: in chat, project shorthand the reader shares.
- **External** (clients, vendors, formal documents): full sentences, hedges spelled out ("as far as I know", "my assumption is"), no chat shorthand, the same directness and the same marked assumptions.

## Calibration

An AI draft of a status message:

> Hi team, I wanted to share a quick update on the provider integration. Over the past week we have made significant progress, and I am pleased to report that the core connection is now working end to end. As you know, this integration is a critical piece of the overall architecture, enabling seamless data flow between the systems. There are still a few items to address, including finalising the error handling strategy, which is typically an important consideration in integrations of this kind. We will continue to monitor the situation and keep everyone updated.

The same message in the voice:

> hello, provider integration update:
> - core flow works end to end on dev (create account -> webhook -> load funds)
> - error handling isn't finished. Retries work, but I still need to decide what happens when the retry budget is exhausted - my assumption is DLQ + alert, will confirm with the provider's team
> - provider sandbox access is still the blocker, so I can't test their side

"Significant progress" failed _known_ and became the flow that works. "As you know, this is a critical piece" failed _needed_. "Typically an important consideration" is true of any project, so it says nothing about this one. What the draft lacked was the open decision, marked as an assumption with an owner, and the blocker: the two lines the reader acts on.
