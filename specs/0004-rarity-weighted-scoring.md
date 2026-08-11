# Spec 0004 — Rarity-weighted scoring, and saying what we don't know

- **Status:** Implemented (2026-08-11)
- **Date:** 2026-08-11
- **Relates to:** spec 0001 § Behaviour rules 5 and 7 (**superseded**); spec 0002 § Open
  questions 1 (**resolved**); ADR 0001 decision 4; docs/brief.md § north star

## Context

Spec 0001 rule 5 scored a passage by *counting* the distinct question words in it, one point
each. Every word was worth the same, which broke down on the real corpus.

Measured over the 38 passages in `docs/kb/`:

| term | appears in |
| --- | --- |
| `invoice` | 21/38 passages (55%) |
| `telikos` | 15/38 (39%) |
| `2026` | 12/38 (32%) |
| `default` | 3/38 (8%) |
| `reset` | **0/38** |

So for "how do I reset an invoice", `reset` matched nothing and `invoice` matched most of the
corpus. Every candidate tied on score 1, the tie broke on document order, and the reply was the
document's **title block** followed by the next two sections — presented exactly as a confident
answer would be. The brief's north star is "well enough that a person would have been happy to
receive it", and that answer fails it: the user asked about resetting invoices and the corpus has
nothing on resetting anything.

Flat counting also mis-ranks partial matches. For "default invoice 2026" it put the title block
first, because matching two *common* words (`2026`, `invoice`) beat matching one rare and one
common (`default`, `invoice`) — even though `## Default invoice trigger` is plainly the answer.

Two separate defects, so two separate fixes.

## Behaviour

Replacing spec 0001 rule 5:

1. Each distinct question word found in a passage contributes its **weight**, not one point.
   A word's weight is `log(1 + N / df)`, where `N` is the number of passages in the corpus and
   `df` is how many of them contain that word. A passage's score is the sum over its matched
   words. Rarer words are worth more; a word in every passage is worth the least.
2. The weight is always **positive**. A word in all `N` passages weighs `log(2)`, not zero, so
   weighting can never silence a word entirely and hide every passage that contains it.
3. `df` is counted over the passages passed to the search, and recomputed per query. Nothing is
   stored or cached — ADR 0001 decision 4's "no storage" holds.

Replacing spec 0001 rule 7's threshold:

4. A passage is a candidate if it contains **at least one** question word. Ranking is by score
   descending, then filename A→Z, then position — unchanged. Top 3, untruncated — unchanged.
   Since every weight is positive, "contains a question word" and "scores above zero" are the
   same condition; the wording changes, the behaviour does not.

New, and independent of scoring:

5. Question words that appear in **no passage at all** are reported in the reply, before the
   passages, naming them: *"Nothing in the knowledge base mentions **reset**. Here's what
   matched:"*. Words are listed in the order asked, de-duplicated, comma-separated with `and`
   before the last.
6. The caveat appears only when there is something to caveat: if every question word matched,
   the reply is exactly as before, with no preamble. If *no* word matched anything, there are no
   passages and spec 0001 rule 8's no-match message applies unchanged.

Rule 5 is the honesty fix; rules 1–4 are the ranking fix. Neither depends on the other.

## What this does and does not fix

It **does** stop a partial match reading as a whole one, and it does re-rank partial matches by
how discriminating the matched words are.

It **does not** break a tie between passages that match the *identical* set of words. For "how do
I reset an invoice" all three results still score `1.033` — they each match `invoice` and nothing
else, so no weighting scheme can separate them. What changed is that the reply now says `reset`
matched nothing, which is the part that misled. Ordering within such a tie remains document
order, deliberately: it is stable and explainable, and inventing a secondary signal (position in
document, passage length) would be a guess dressed as relevance.

## Edge cases

| Case | Expected behaviour |
| --- | --- |
| A question word appears in every passage | Still scores, at `log(2)`; its passages are still returned |
| A question word appears in no passage | Named in the reply's caveat; contributes no score |
| Every question word appears in no passage | No candidates; no-match message, no caveat (nothing to show) |
| Question is empty or only stop words | Unchanged — ask-a-real-question, retrieval never runs |
| Two passages match the identical word set | Scores are equal; filename then position decides, as before |
| A word repeated in one passage | Counted once — `df` counts passages, not occurrences |
| A word repeated in the question | Counted once — the query is a set |
| Empty corpus | No candidates; no-match message |
| One passage in the corpus | `N=1`; any matched word weighs `log(2)`; that passage is returned |

## Does this need a new ADR?

**No, on balance.** ADR 0001 decision 4 chose "in-memory keyword scan, no storage" over
embeddings and a vector DB. This is still exactly that: exact-token matching, computed in memory
per query, nothing persisted, no new dependency (`math.log` and `collections.Counter`). Spec 0001
listed what *would* need an ADR — "stemming, synonyms, spelling correction, embeddings" — and
weighting by rarity is none of them. Reverting is replacing one `sum()` with `len()`.

The honest counter-argument: scoring is closer to the heart of decision 4 than passage-splitting
was in spec 0003, and "how relevance is computed" is a defensible reading of "retrieval approach".
If you read it that way, this becomes ADR 0002 and spec 0003 probably joins it. I have flagged
this rather than decided it quietly.

## Acceptance criteria

- [x] A passage matching one rare word outranks passages matching one corpus-wide word.
- [x] A word appearing in every passage still scores above zero, and its passages are returned.
- [x] `term_weight` decreases as a word gets more common and stays positive at `df == N`.
- [x] `document_frequencies` counts passages, not occurrences.
- [x] A passage matching two distinct words still outranks one matching a single word — spec
      0001's criterion, still true under weighting.
- [x] A word repeated five times in a passage scores the same as once — spec 0001's criterion,
      still true.
- [x] Ties on score still break by filename A→Z then position — spec 0001's criterion, unchanged.
- [x] `unmatched_terms` names words absent from the corpus, in question order, de-duplicated,
      and returns empty when everything matched.
- [x] The reply names a missing word and still shows the passages that did match.
- [x] The reply has no caveat when every question word matched.
- [x] Several missing words are listed together with `and` before the last.
- [x] A question matching nothing at all still gets spec 0001 rule 8's no-match message.
- [x] Manual, once: "how do I reset an invoice" against the real corpus names `reset` as missing;
      "default invoice 2026" ranks `## Default invoice trigger` first where flat scoring ranked
      the title block first.
- [x] `uv run ruff format .`, `uv run ruff check .` clean; `uv run pytest --cov` green at 90%+.

## Open questions

- **The remaining tie is untouched.** Three passages scoring `1.033` for "how do I reset an
  invoice" are still ordered by document position. Length normalisation or match density would
  separate them, but both are guesses about relevance rather than measurements of it; the caveat
  seemed the honest fix. Worth revisiting if it still reads badly in use.
- **`invoice` at 55% of the corpus is arguably a stop word for this domain.** Weighting handles it
  softly. A domain stop-word list would handle it bluntly, and would be one more hand-maintained
  thing to get wrong — the same trap spec 0003 removed. Not done.
- **`Match.score` is now a float**, so scores are no longer human-countable ("scored 2 of 3
  words"). Spec 0002's rule 8 says the heading "has already done its work at the retrieval
  layer" and does not display scores, so nothing user-facing regresses. If a future slice wants
  to show *why* a passage matched, the matched-word set — not the score — is the thing to surface.
- The weight formula is the textbook shape, not a tuned one. No corpus large enough to tune on.
