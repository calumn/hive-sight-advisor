# Vertical Slice 0012: Passage Chunking

## Purpose

Prove that a single Corpus Document can be curated as multiple, topically-focused Passages instead of exactly one whole-document Passage — and that retrieval cites the specific Passage a query is actually about, not the whole source document.

## Source Inputs

- `requirements/roadmap.md`, "Passage chunking strategy" (Retrieval quality)
- `requirements/decision-log.md`, 2026-08-07 "Grounding Threshold Recalibration" — named coarse (one-Passage-per-Document) granularity as the structural root cause behind the threshold-drift finding, and passage chunking as the real prerequisite to revisit it
- Grilled 2026-08-07: chunking only matters once a document has genuinely distinct sub-topics — today's seeded documents are each a single short paragraph with nothing to split. Resolved by adding one deliberately multi-topic document as part of this slice, so chunking has real material to prove itself against, rather than building the mechanism speculatively
- Grilled 2026-08-07: chunking is Curator-driven (the Curator authors each passage chunk by hand, same reviewed workflow as today), not an automatic paragraph/token splitter — consistent with this project's existing curated, reviewed-ingestion philosophy (Slice 0006) and avoiding new unreviewed automated-ingestion machinery this project doesn't otherwise have

## User Path

Given the UK corpus has a new curated document — a seasonal Varroa IPM guide covering monitoring, multiple treatment options, and timing, added as several distinct Passages (one per sub-topic)
When a Beekeeper asks a question that's really about only one of those sub-topics (e.g. "when should I monitor mite drop before treating?")
Then the Answer is grounded in and cites the specific Passage about monitoring — not a passage about an unrelated sub-topic (e.g. treatment product selection) from the same document

## Preconditions

- Existing dev-authenticated Workspace Membership (implicit, as with every other scenario)
- The new multi-topic document is added via `corpus_admin add-document`, extended to accept multiple passage chunks in one invocation

## End-To-End Behaviour

1. Curator authors the new multi-topic document's content as N separate passage texts (one per sub-topic), each getting its own AI-assisted advisory review (same per-chunk review already used for single-passage documents) before commit.
2. `corpus_admin add-document` is extended to accept repeated `--text`/`--text-file` chunk arguments for a single document, inserting one `corpus_documents` row and N `passages` rows (using the existing but currently-unused `position` column to record chunk order).
3. `find_similar_passages` needs no change — it already queries the flat `passages` table with no per-document uniqueness assumption, so multiple Passages per Document retrieve and rank correctly today.
4. A Beekeeper query that's specific to one sub-topic retrieves and cites the matching Passage (verified via distance — the sub-topic-specific Passage should score closer than the whole-document Passage would have).

## Layers Touched

- Web UI: Not touched (existing citation rendering already displays whichever Passage(s) an Answer cites, regardless of count)
- Core API: Not touched (`/queries` already returns whichever Passages the workflow retrieves)
- Analysis Service: Not touched (`AnswerQueryWorkflow` already handles however many Passages retrieval returns)
- Storage: `passages.position` (already exists, currently always 0) becomes meaningful; no migration needed
- Corpus Curator CLI: `corpus_admin add-document` extended to accept multiple passage chunks per document; `PreparedCandidate` and `commit_candidate` change from a single `passage_id`/`passage_text` to a list; `curator_added_documents.yaml` schema changes from a single `passage_id`/`passage_text` field per document to a `passages: [...]` list
- Queue or async boundary: Not touched
- Contracts: Not touched (no external API surface changes — this is corpus authoring tooling and internal retrieval, nothing HiveSight-facing)
- Observability: Not touched

## Test Seams

- Seam: `corpus_admin.prepare_candidate` / `commit_candidate` / `apply_curator_documents`
  Behaviour verified: a document with multiple passage chunks inserts one `corpus_documents` row and N `passages` rows with correct `position` ordering; `curator_added_documents.yaml` round-trips the new multi-passage schema
  Test style: pytest, real test-database transaction (existing pattern in `test_corpus_admin.py` if present, else new)
- Seam: `CorpusRepository.find_similar_passages`
  Behaviour verified: given a document with multiple Passages, a query specific to one sub-topic returns that Passage ranked first, not a sibling Passage from the same document
  Test style: pytest, stub embedding provider with deterministic per-text vectors (existing pattern)
- Seam: Web acceptance (Gherkin) — **descoped during implementation, see note below**

## Data Shape

- `passages.position` (existing column, integer, default 0) — now populated 0..N-1 per document to record curator-authored chunk order
- `curator_added_documents.yaml`: each document entry's `passage_id`/`passage_text` fields become a `passages: [{id, text, position}, ...]` list (breaking change to this internal, non-external file format — acceptable since it's project-local tooling data, not a declared API surface)

## Out Of Scope

- Automatic/algorithmic text splitting (paragraph or token-based) — explicitly rejected in grilling; Curator authors each chunk by hand
- Re-running the threshold-recalibration measurement against the new multi-topic document — a natural follow-up once this slice lands, but not required for this slice to be complete; the decision log's "revisit after chunking" trigger fires once this slice exists, not automatically within it
- Migrating existing single-passage documents to multiple passages — none of today's seeded documents have genuinely distinct sub-topics worth splitting; only the new document uses multiple passages
- Any change to `/integrations/hivesight/*` or other external contract surface — this slice is corpus tooling and internal retrieval only

## Acceptance Criteria

- [x] `corpus_admin add-document` accepts multiple passage chunks for one document and commits them with correct `position` ordering
- [x] One new multi-topic UK document (seasonal Varroa IPM guide: monitoring, treatment options, timing) is curated as 3 distinct Passages — the AI-assisted review caught a real drafting contradiction on the first attempt (claimed Apivar had a temperature restriction, contradicting the existing Apivar passage), which was fixed before commit
- [x] A sub-topic-specific query retrieves the matching Passage, not a sibling Passage from the same document, verified at the `CorpusRepository` seam (the only seam that can actually distinguish this — see Open Questions / implementation note below)
- [x] `curator_added_documents.yaml` schema and `apply_curator_documents` (idempotent re-apply) both round-trip the new multi-passage-per-document shape
- [ ] Traceability and roadmap updated: roadmap's "Passage chunking strategy" item marked done, with an explicit note that the threshold-recalibration revisit is now unblocked but not yet re-run

## Open Questions

None outstanding at design time — both real design forks (chunking mechanism, whether to add new content first) were grilled and resolved before writing this doc.

**Implementation-time finding**: the web citation UI (`AnswerView.tsx`) renders only `document_title`/source/licence per citation — never Passage text. Since sibling Passages in the same Document share an identical `document_title`, a browser-level scenario cannot distinguish "cited the monitoring Passage" from "cited the timing Passage" — the citation renders identically either way. Building new UI to expose Passage-level citation text was not scoped or grilled here, so the planned Gherkin scenario for sub-topic precision was dropped rather than forced onto a claim the UI genuinely cannot observe. The `CorpusRepository.find_similar_passages` test is the correct and sufficient seam for this claim — it is the layer where chunking's actual value lives. If Passage-level citation display becomes a real product need later, that is its own UI slice, not an extension of this one.
