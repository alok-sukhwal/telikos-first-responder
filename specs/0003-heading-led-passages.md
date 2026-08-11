# Spec 0003 — Heading-led passages

- **Status:** Implemented (2026-08-11)
- **Date:** 2026-08-11
- **Relates to:** spec 0001 § Behaviour rule 2 (**superseded**), spec 0001 criteria on splitting and
  byte-identity (**amended**); spec 0002 rules 5–7 and 10; ADR 0001 decision 4; docs/brief.md § MVP

## Context

The brief describes the knowledge base as "built from a small set of local documents **dropped into
the project**". Until this spec that was not true.

Spec 0001 rule 2 splits a document into passages on blank lines, and rule 5 scores a passage by how
many distinct question words appear *in that passage*. Idiomatic Markdown puts a blank line after a
heading, so `## Default invoice trigger` became one passage and the sentence answering it became
another. The heading then matched the question's topic words while containing no answer, and the
body matched nothing. A document dropped in unmodified was largely unreachable.

This was not hypothetical. `offer-search.mdx` was dropped into `docs/kb/` on 2026-08-11 and would
have produced 13 passages, 5 of them bare headings — every heading in the file orphaned from its
body. It was made reachable by hand-editing the document, which is how `billing-and-invoicing.md`
had been prepared too: 30 of its 69 blank-line blocks were headings alone before reshaping.

That requirement on the corpus was recorded nowhere — not in the brief, the ADR, spec 0001, the
code, or the tests. The only description of it lived in a subagent prompt. So the next document
dropped in would have regressed silently, and no test would have noticed.

## Behaviour

Replacing spec 0001 rule 2:

1. A document is split into blocks on blank lines, each block trimmed, empty blocks discarded — as
   before.
2. A block whose **every** line is a Markdown ATX heading (`^ {0,3}#{1,6}(\s|$)`) is a *label*: it
   names a topic but answers nothing. Such a block is joined, with a single newline, to the next
   block that has a body.
3. Consecutive heading-only blocks join to that same following body, so `## A` / `### B` / body
   becomes one passage.
4. A heading-only block with nothing after it stays a passage of its own — there is nothing to join
   it to, and discarding it would lose content.
5. **Invariant:** no passage is heading-only except possibly the last one in a file.
6. Passage text remains verbatim source text. The precise claim, amending spec 0001's criterion
   that a passage is "byte-identical to the source paragraph": **every line of every passage is
   byte-identical to a line of its source file.** The loader removes blank lines between blocks and
   rewrites nothing.

Additionally, and separately from splitting:

7. When `docs/kb/` contains files that look like documents but are not `.md` — `.mdx`, `.markdown`,
   `.rst` — one warning names them, surfaced in the UI like every other load warning. They are
   still not loaded; spec 0001's out-of-scope list stands. The point is that a dropped-in file that
   will never be searched says so instead of disappearing. `.txt` is deliberately excluded: it is
   as often a note as a document, and warning about it would cry wolf.

## Edge cases

| Case | Expected behaviour |
| --- | --- |
| `## Head` blank `Body.` | One passage, `"## Head\nBody."` |
| Several blank lines between heading and body | Same one passage; no empty passage |
| `## A` blank `### B` blank `Body.` | One passage, `"## A\n### B\nBody."` |
| `## A\n### B` already in one block, then body | Same one passage |
| Heading-only block at end of file | Survives as its own passage |
| Block that already has a body, followed by another block | Not joined — two passages, as before |
| Document with no headings at all | Unchanged from spec 0001 rule 2 |
| `#hashtag topic`, `####### seven` | Body text, not headings — never joined |
| Empty or whitespace-only document | No passages |
| Document already hand-joined (no blank line after headings) | Unchanged — the rule is idempotent |
| `docs/kb/` contains `notes.mdx` alongside `.md` files | One warning naming `notes.mdx`; the `.md` files load |

## Out of scope

- **Fenced code blocks.** A blank line inside a ``` fence is split like any other, and a `#` line
  inside a fence looks exactly like a heading to rule 2's pattern. This is pre-existing — rule 1
  has always shredded fences — and there are no fences in the corpus today. Making `split_passages`
  fence-aware is a later change.
- **Setext headings** (`Title` over `====`). None exist in the corpus, and the underline makes the
  block non-heading-only in any case.
- **Heading-*section* chunking** — one passage per `##` section, swallowing every block until the
  next heading. Measured and rejected: it collapses `billing-and-invoicing.md` from 32 passages to
  roughly 11, and because scoring counts word *presence* with no length normalisation, long
  passages would dominate nearly every question. It also breaks spec 0002 rules 5–7, which assume
  one heading and one body per passage.
- **Orphans that are not heading-led.** `billing-and-invoicing.md` has a frequency table whose
  lead-in ends in `:`, and two trailing sentences that sit under no heading of their own. They
  remain passages matching only their own words. This spec fixes heading orphaning, not every form
  of it — worth knowing so a partial fix is not mistaken for a complete one.
- **Loading `.mdx`.** Rule 7 warns; it does not widen the glob. Spec 0001's out-of-scope list stands.
- **Reverting the hand-joined blank lines in `docs/kb/`.** Both documents already read correctly
  under this rule and produce identical passages either way, so re-inserting the blank lines would
  be churn with no behavioural effect.

## Does this need a new ADR?

**No.** ADR 0001 decision 4 constrains the retrieval *mechanism* — "in-memory keyword scan, no
storage" — and this changes neither: no storage, no index, no dependency, no new layer. `Passage`
and the `KnowledgeBase` shape are unchanged, `load_knowledge_base` is untouched, and reverting is
deleting a dozen lines from one function.

The counter-argument, recorded honestly: how a document is divided into retrievable units is
arguably part of the retrieval design rather than an implementation detail of it, and someone
reading decision 4 as "the whole retrieval approach" would want this as ADR 0002. If a reviewer
sees it that way, promote it — the content above is the ADR's Decision section either way.

## Acceptance criteria

- [x] `## Head` blank `Body.` yields one passage containing both.
- [x] Several blank lines after a heading still yield the one joined passage, and no empty passage.
- [x] Consecutive heading blocks join to the same following body.
- [x] A multi-line heading block joins as one.
- [x] A heading-only block at end of file survives as its own passage, with no exception.
- [x] A block that already has a body is not joined onward — the rule is idempotent, so an
      already-hand-joined document is unaffected.
- [x] A document with no headings splits exactly as it did under spec 0001 rule 2.
- [x] `#hashtag` and `#######` are body text, not headings.
- [x] Empty and whitespace-only documents yield no passages.
- [x] The loaded fixture corpus includes a document written in **idiomatic** Markdown — blank line
      after each heading — so the rule is exercised through `load_knowledge_base`, not only in
      unit tests. Spec 0001's fixtures contained no headings at all, which is why its 14 criteria
      all passed against a corpus that had the defect.
- [x] A question whose discriminating word appears **only in a heading** returns a passage
      containing the body sentence that answers it. Verified to fail under the old splitter, which
      returned the bare heading.
- [x] Every line of every passage is byte-identical to a line of its source file.
- [x] A directory with one `.md` and one `.mdx` produces exactly one warning, naming the `.mdx`.
- [x] Manual, once: the passage lists for both `docs/kb/` documents are byte-identical before and
      after this change — the change is a no-op on the corpus as it stands.
- [x] Manual, once: with a blank line re-inserted after every heading in a scratch copy of both
      documents, the loader yields the **same 38 passages, byte-identical**. Before this change the
      same input gave 73 passages, 35 of them bare headings. This is the claim the spec rests on.
- [x] `uv run ruff format .`, `uv run ruff check .` and `uv run pytest` are clean.

## Open questions

- **Does joining improve scoring, or just lengthen passages?** A merged passage has more words and
  so more chances to match, and score is not length-normalised. It makes previously unreachable
  bodies reachable, which is the point — but it may also make spec 0002's first open question
  ("everything ties on score 1") more common, since more passages now contain any given word. Not
  measured. An adversarial review of this question was attempted and lost to an API error before
  it reported.
- **Should the `:` lead-in case join too?** A block ending in `:` introduces the block after it as
  plainly as a heading does. Left alone deliberately — it is a guess about prose, where a heading
  is a syntactic fact — but it is the same class of orphaning.
- The `.txt` exclusion in rule 7 is a judgement call, not a measurement.
