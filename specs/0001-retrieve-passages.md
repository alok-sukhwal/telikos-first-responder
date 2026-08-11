# Spec 0001 — Retrieve matching passages

- **Status:** Implemented (2026-08-11)
- **Date:** 2026-08-10
- **Relates to:** docs/brief.md § MVP (knowledge base, simplest retrieval); ADR 0001 decisions 4 and 6

## Context

Today `app.py` is a chat shell that echoes a placeholder; nothing reads documents and
`first_responder/` is empty. This spec covers the first slice that is useful on its own: a user
types a question and gets back the paragraphs from the local knowledge base that best match it,
quoted verbatim with their source file.

Answer composition through the `Answerer` seam is deliberately a later slice. Proving the corpus
and the keyword scan first de-risks the quality problem ADR 0001 already flags — a keyword scan
misses meaning-based matches — before any prose is layered on top of it.

## Behaviour

**Loading the knowledge base**

1. At startup the app reads every `*.md` file directly inside `docs/kb/`, decoded as UTF-8.
   Sub-folders and all other extensions are ignored.
2. Each file is split into passages on blank lines. A passage is one block of text with
   surrounding whitespace trimmed; empty blocks are discarded. Markdown is kept exactly as
   written — no rendering, no stripping of `#`, `*` or link syntax.
3. Documents are loaded once per session and held in memory. Editing files in `docs/kb/`
   requires a restart to take effect. *(assumption — flag if you want a reload control)*

**Matching a question**

4. The question is normalised the same way as passage text: lowercased, punctuation stripped,
   split on whitespace, then stop words dropped. The stop-word list is small, hard-coded and
   lives in one constant (listed at the foot of this spec).
5. A passage's **score** is the number of *distinct* remaining question words whose exact token
   appears in that passage. No stemming, no synonyms, no substring matching — `invoices` does
   not match `invoice`.
6. Passages are ranked by score, highest first. Ties are broken by document order: filename
   A→Z, then position within the file.
7. The reply shows the **top 3** passages scoring at least 1, each rendered as its source
   filename followed by the passage text in full. Fewer than three matches shows however many
   there are. Passages are never truncated.

**When there's nothing to show**

8. If no passage scores at least 1, the reply is a short "nothing in the knowledge base matched
   that — try rephrasing" message. No passages are shown.
9. If the question has no words left after normalisation (empty, whitespace, punctuation only,
   or nothing but stop words), retrieval does not run at all; the reply asks the user to type an
   actual question. This is a separate message from the one in 8.
10. If `docs/kb/` is missing or contains no `.md` files, the app still starts and a warning is
    visible in the UI; every question then falls to the message in 8.
11. If an individual file cannot be read or decoded, it is skipped with a warning naming it, and
    the remaining documents still load. *(assumption — carried over from 10 rather than asked)*
12. Questions and replies persist in the chat history for the session, as they do today.

## Edge cases

| Case | Expected behaviour |
| --- | --- |
| `docs/kb/` missing entirely | Warning shown in UI; app runs; all questions get the no-match message |
| `docs/kb/` exists but has no `.md` files | Same as above |
| A `.md` file is empty or only blank lines | Contributes no passages; not an error |
| A file is unreadable or not valid UTF-8 | Skipped, warning names the file, other files still load |
| Question is empty or whitespace | Reply asks for a real question; retrieval never runs |
| Question is only stop words (`the and of`) | Same — asks for a real question |
| Question words appear in no passage | No-match message |
| Fewer than 3 passages score ≥ 1 | Show the 1 or 2 that do; no padding, no apology |
| More than 3 passages tie on the same score | First three by filename A→Z, then position in file |
| A matching passage is very long | Shown in full — no truncation |
| Same word repeated in the question (`invoice invoice`) | Counts once; score is over *distinct* words |
| Question word appears 5× in one passage | Still adds 1 to that passage's score |
| Passage contains Markdown syntax (`## Billing`) | Shown as written; `##` is not stripped and is not searchable text of its own |

## Out of scope

- **LLM-composed answers and the `Answerer` seam** — the next slice; this one returns source text only.
- **Source citations, links or line numbers** beyond the plain filename label — brief's out-of-scope list.
- Sub-folders under `docs/kb/`, and any format other than `.md` — a later change if the corpus grows.
- Stemming, synonyms, spelling correction, embeddings — moving beyond keyword scanning needs a **new ADR** (it changes ADR 0001 decision 4).
- Highlighting the matched words inside a passage, pagination, or a user-configurable result count.
- Conversation memory, streaming, feedback controls, accounts — all on the brief's out-of-scope list.
- Reloading the knowledge base without a restart.

## Acceptance criteria

Checked by automated tests over a fixture corpus. **This adds `pytest` as a development
dependency** (`uv add --dev pytest`) — calling it out per the conventions.

Fixture corpus at `tests/fixtures/kb/`, two files:

- `billing.md` — a paragraph about resetting an invoice, a paragraph about payment terms.
- `setup.md` — a paragraph about installing the client, a paragraph mentioning invoices once.

- [x] Loading `tests/fixtures/kb/` yields passages from both files, split on blank lines, with no empty passages and whitespace trimmed.
- [x] Given the question "how do I reset an invoice", the top passage is the invoice-reset paragraph from `billing.md`.
- [x] A passage matching two distinct question words outranks a passage matching one.
- [x] A passage containing one question word five times scores the same as a passage containing it once.
- [x] Repeating a word in the question ("invoice invoice") produces the same ranking as asking it once.
- [x] When more than three passages score ≥ 1, exactly three are returned, ordered by score then filename then position.
- [x] When two passages tie on score, the one from the alphabetically earlier filename comes first.
- [x] Given a question whose words appear nowhere ("zzzz quantum"), the result set is empty and the caller renders the no-match message.
- [x] Given `""`, `"   "` and `"the and of"`, retrieval is not invoked and the "ask a real question" branch is taken.
- [x] Pointing the loader at a non-existent directory returns zero documents and raises no exception.
- [x] Pointing the loader at a directory containing an undecodable file skips that file, still loads the valid ones, and surfaces a warning naming the skipped file.
- [x] Each returned result carries its source filename, and the passage text is byte-identical to the source paragraph.
- [x] Manual check, once: `uv run streamlit run app.py`, ask a question against real `docs/kb/` content, and see up to three filename-labelled passages in the chat.
- [x] `uv run ruff format .` and `uv run ruff check .` are clean.

## Open questions

- The stop-word list below is a starting point — worth a look, since it decides what counts as a
  "real" question in criterion 9.
- Nothing else outstanding; the two items marked *(assumption)* above are the only places I
  chose rather than asked.

**Proposed stop words:** `a, an, and, are, as, at, be, but, by, can, do, does, for, from, how,
i, in, is, it, of, on, or, that, the, to, what, when, where, which, who, why, with, you`
