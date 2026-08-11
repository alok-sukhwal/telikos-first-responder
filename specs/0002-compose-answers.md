# Spec 0002 — Compose answers through the `Answerer` seam

- **Status:** Proposed
- **Date:** 2026-08-11
- **Relates to:** docs/brief.md § MVP (LLM composes the answer); ADR 0001 decision 5;
  spec 0001 § Out of scope (this is the slice it defers to)

## Context

Spec 0001 ships retrieval: a question returns the top three matching passages, quoted verbatim
with their source filename. The user reads raw source text and does the last step themselves.

This slice closes that gap. It introduces the `Answerer` seam ADR 0001 decision 5 records, and a
local stub behind it that composes a short plain-language answer from the retrieved passages. No
API key, no network, no new dependency — the app keeps running for everyone, and swapping in a
real model later is the one-file change the ADR promises.

The stub is deliberately **extractive**: it selects and reorders sentences that are already in the
passages. It never paraphrases and never writes a sentence of its own beyond a fixed lead-in. So it
cannot invent a fact that is not in the corpus. It can still mislead in two narrower ways, both
accepted here and recorded under Open questions: a naively split sentence may be *truncated*, and
composed prose reads more confidently than raw passages even when the underlying match is weak.

### What the review of spec 0001 changed here

Two findings from reviewing `eb3b660` shaped this spec and are worth stating, because the obvious
design is wrong for the real corpus:

- **Headings carry most of the topical signal.** 30 of the 32 passages in `docs/kb/` begin with a
  Markdown heading (`## Default invoice trigger`), and `retrieval.normalise` strips `#`, so heading
  words are already searchable. An earlier draft of this spec discarded heading lines when
  extracting sentences; that would throw away the best signal in the corpus and could leave a
  matched passage with no sentences at all. Rules 5 and 9 below treat a heading as a passage label
  instead, with an explicit fallback chain.
- **Weak matches are indistinguishable from strong ones.** When a question's discriminating term
  matches nothing, every passage containing a common word ties on score 1 and the top three are
  simply the first three in document order. Composing fluent prose on top of that makes a bad
  result *look* better than the raw passages did. This slice does not fix it — see Open questions.

### Does this need a new ADR?

I judge **no**, and want that confirmed rather than assumed. `.claude/rules/architecture.md`
requires an ADR before introducing "a public interface contract", which the `Answerer` signature
is. But ADR 0001 decision 5 already records both halves of this slice — the seam and the local
stub default — so the decision is made and this spec implements it.

A **new ADR is required** before wiring in a real LLM provider: that adds secrets, network, cost,
latency and a failure mode, and is costly to reverse. This slice deliberately stops short of it.

## Behaviour

**The seam**

1. `first_responder/answerer.py` defines `Answerer` as a `typing.Protocol` with a single method:
   `answer(question: str, passages: Sequence[Passage]) -> str`. Structural typing — an
   implementation satisfies it by shape, with no base class to inherit.
2. The seam takes `Passage`, not `Match`. An answerer composes from source text; a passage's
   keyword score is a retrieval implementation detail it has no use for.
   *(decision — flag if you'd rather the seam saw scores)*
3. `compose_reply` calls the answerer **only** with a non-empty passage list. The no-match and
   "ask a real question" branches never reach it. This is part of the contract: an implementation
   may assume at least one passage.
4. `compose_reply(question, knowledge_base, answerer=DEFAULT_ANSWERER)` gains a third parameter
   defaulting to a module-level `StubAnswerer` instance, so existing callers and `app.py` are
   unchanged. Tests and a future real provider inject their own.

**Heading and body**

5. A passage may open with one or more Markdown heading lines (`^#+\s`). Those lines are the
   passage's **heading**; everything after them is its **body**. A passage with no leading heading
   has an empty heading and is all body; a passage that is nothing but a heading has an empty body.
6. Sentences are extracted from the **body only**. A sentence ends at `.`, `!` or `?` followed by
   whitespace or end of text. A bullet or numbered list item (`-`, `*`, `1.`) is one sentence
   regardless of how it terminates, since list items routinely have no full stop.
7. The heading is never emitted as a sentence — it is a topic label, not prose — but it is not
   discarded either. It is the last resort in the fallback chain at rule 10.

**What the stub selects**

8. Each body sentence scores the number of *distinct* question words it contains, reusing
   `retrieval.normalise` so scoring is identical to the layer below. The heading does not score;
   it has already done its work at the retrieval layer.
9. The best `MAX_SENTENCES = 4` sentences overall are selected by score, ties broken by source
   filename A→Z, then passage position, then sentence position. Selection is purely by sentence
   score across all passages, so one strong passage may legitimately supply all four while another
   contributes none. *(decision — 4 sentences over up to 3 passages is a deliberately tight budget;
   see Open questions)*
10. **Fallback chain, so the stub never returns an empty answer.** In order:
    1. body sentences scoring at least 1, best `MAX_SENTENCES` of them;
    2. if no body sentence in any passage scores at least 1 — the first body sentence of the first
       passage;
    3. if that passage has no body at all (heading-only) — its heading text, with leading `#`
       characters and whitespace stripped.
11. Selected sentences are then **regrouped into document order** for rendering, not left in score
    order — one paragraph per contributing passage, sentences space-joined within it. Prose that
    jumps between documents in score order reads as noise.
12. Sentence text is reproduced **byte-identically** to the source, Markdown included. The stub
    selects; it does not rewrite, re-wrap or clean up. The one exception is the stripped `#` in
    rule 10.3.

**What the reply looks like**

13. The reply is a fixed lead-in line, a blank line, the composed paragraphs, then a final
    `From: <filenames>` line naming the distinct source files of the passages that contributed
    sentences, in filename order.
14. The `From:` line is the same plain filename label spec 0001 already shipped, carried forward —
    not the citations, links or line numbers the brief lists as out of scope.

```
Here's what I found on that:

The default invoice trigger in Telikos is: - **Imports** — On Estimated Time of Arrival (ETA)
of cargo delivery for each shipment.

For each billing frequency Telikos supports supplementary invoices.

From: billing-and-invoicing.md
```

**When the answerer fails**

15. If the answerer raises, `compose_reply` catches `Exception` — deliberately not
    `BaseException`, so `KeyboardInterrupt` and `SystemExit` still propagate — and falls back to
    spec 0001's verbatim passage rendering, preceded by a short line saying the answer could not be
    composed and the source text follows. No exception reaches Streamlit; the chat stays usable.
    *(decision — the stub cannot realistically fail, but a real LLM will, and building the fallback
    now is what makes the later swap a one-file change)*
16. The no-match, empty-question and knowledge-base-warning behaviours of spec 0001 are unchanged.

## Edge cases

| Case | Expected behaviour |
| --- | --- |
| Passage opens with `## Heading` then a body | Heading labels the passage and does not score or render; body sentences are selected |
| Passage is **only** a heading, and is the first passage with nothing scoring | Rule 10.3 — heading text rendered with `#` stripped |
| Passage matched only on words in its heading | No body sentence scores; rule 10.2 gives the first body sentence |
| A passage is one sentence with no terminator | Treated as a single sentence; shown in full |
| A passage is a bullet list | Each bullet is one sentence; `-` / `1.` prefixes kept as written |
| Fewer than 4 sentences available in total | Uses however many there are; no padding |
| One passage supplies all 4 sentences | Single paragraph, single filename in `From:` |
| Sentences selected from 3 different files | 3 paragraphs in filename order; all 3 named in `From:` |
| Two sentences tie on score | Filename A→Z, then passage position, then sentence position |
| A selected sentence is very long | Shown in full; no truncation (as spec 0001) |
| Passage contains `e.g.` or `3.5` | Naive splitting may cut the sentence early — accepted, see Open questions |
| Answerer raises `Exception` | Verbatim passages plus a "couldn't compose" line; no crash |
| Answerer raises `KeyboardInterrupt` | Propagates; not caught |
| No passages matched | `NO_MATCH` as today; answerer never called |
| Question normalises to nothing | `ASK_A_REAL_QUESTION` as today; retrieval and answerer never called |

## Out of scope

- **Any real LLM provider** — Claude, a local model, anything over the network. Needs a new ADR
  (see § Does this need a new ADR).
- **Provider selection via environment variable or config**, and any credential loading. Nothing
  to select until there is a second implementation.
- **Abstractive summarisation, paraphrasing or rewriting** — the stub extracts only.
- **Signalling weak or partial matches to the user** — the inherited risk described above. Real, but
  it belongs to retrieval, not to answer composition; see Open questions.
- Per-sentence attribution, links, line numbers, anchors — brief's out-of-scope list.
- Highlighting matched words, a user-configurable sentence count, answer length controls.
- Streaming, feedback controls, conversation memory, accounts — brief's out-of-scope list.
- Changing retrieval in any way: the scan, scoring, stop words and the top-3 limit are spec 0001's
  and stay as they are.
- Prompt templates or token budgeting — they belong with the first real provider.

## Acceptance criteria

Automated tests over spec 0001's existing fixture corpus at `tests/fixtures/kb/`, in
`tests/test_answerer.py` plus additions to `tests/test_replies.py`. **No new dependency** — the
stub is standard library only.

**The seam**

- [ ] A fake answerer injected into `compose_reply` is the one that produces the reply, proving the seam is real.
- [ ] The fake answerer receives the question and a non-empty `Sequence[Passage]`.
- [ ] The answerer is **not** called for an unmatched question, nor for `""`, `"   "` or `"the and of"`.

**Selection and grounding**

- [ ] Every sentence in a stub answer appears byte-identically in the passages it was given. *(This proves provenance, not coherence — a truncated fragment would also pass; see Open questions.)*
- [ ] The stub is deterministic: the same question and passages twice produce identical output.
- [ ] Given "how do I reset an invoice" over the **fixture** corpus, the answer contains the invoice-reset sentence from `billing.md`.
- [ ] A sentence matching two distinct question words is selected over one matching a single word.
- [ ] At most 4 sentences appear when more than 4 score at least 1.
- [ ] A bullet list yields one sentence per bullet, with the `-` prefix preserved.

**Ordering — must be tested where score order and document order genuinely conflict**

- [ ] Rendered sentence order follows document order using a fixture where the highest-scoring sentence is **not** the earliest in the document, so a stub that skipped the rule 11 regrouping would fail.
- [ ] Sentences from two files render as two paragraphs in filename order, using a fixture where the higher-scoring sentence comes from the alphabetically *later* file.
- [ ] The `From:` line names exactly the distinct files that contributed sentences, in filename order.

**Headings and the fallback chain**

- [ ] A passage opening with `## Heading` does not render the heading when its body supplies sentences.
- [ ] A passage matched only on heading words falls back to its first body sentence (rule 10.2).
- [ ] A heading-only first passage with nothing scoring renders its heading text with `#` stripped (rule 10.3).
- [ ] The stub never returns an empty string for a non-empty passage list, including a passage list of one heading-only passage.

**Failure**

- [ ] An answerer raising `Exception` yields the verbatim-passage fallback, and `compose_reply` raises nothing.
- [ ] An answerer raising `KeyboardInterrupt` propagates out of `compose_reply`.

**Regression and hygiene**

- [ ] Spec 0001's `NO_MATCH` and `ASK_A_REAL_QUESTION` tests still pass unchanged.
- [ ] All 32 existing tests still pass.
- [ ] Manual check, once: `uv run streamlit run app.py`, ask a real question against `docs/kb/`, and see a composed answer with a `From:` line rather than raw passages.
- [ ] `uv run ruff format .`, `uv run ruff check .` and `uv run pytest` are clean.

## Open questions

1. **Composed prose makes weak matches look strong.** Reviewing spec 0001 showed that when a
   question's discriminating term matches nothing, all candidates tie on score 1 and the top three
   are just the first three passages mentioning a common word — "how do I reset an invoice" against
   the real corpus returns the document's title block. Fluent prose over that reads as a confident
   wrong answer where raw passages at least looked like raw passages. I have scoped a fix **out** of
   this slice because the cause is in retrieval, not composition, but it arguably makes this slice a
   net regression in honesty until it is addressed. Worth a decision: ship this and fix retrieval
   next, or fix retrieval first?

   **Resolved by spec 0004 (retrieval first).** Matched words now carry a rarity weight, and any
   question word absent from the corpus is named in the reply. The score-1 tie itself survives
   where passages match the identical word set — see spec 0004 § "What this does and does not
   fix" — so when this slice is implemented, its prose must carry the caveat through rather than
   smoothing it away.
2. **The `From:` line** (rules 13–14) — keeping it preserves the provenance spec 0001 shipped, but
   the brief calls citations a nice-to-have. Drop it if you'd rather the answer stood alone.
3. **Naive sentence splitting** breaks on `e.g.`, `Inc.` and decimals like `3.5`, occasionally
   cutting a sentence early. The fix is a real sentence tokeniser, which means a new dependency for
   a corpus this small. I'd accept the imperfection for the MVP — say if you disagree.
4. **`MAX_SENTENCES = 4`** across up to 3 passages is a guess at "long enough to answer, short
   enough to read". It is tight enough that a single rich passage can consume the whole budget.
   Easy to change; worth an opinion.
5. **The lead-in wording** ("Here's what I found on that:") is placeholder-grade. It is the only
   prose in the app that isn't from the knowledge base, so it sets the agent's tone.
6. The items marked *(decision)* above — the `Passage`-not-`Match` seam signature, the sentence
   budget, and the `except Exception` failure fallback — are where I chose rather than asked.
