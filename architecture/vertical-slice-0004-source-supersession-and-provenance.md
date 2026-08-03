# Vertical Slice 0004: Source Supersession Flagging And Provenance Display

## Purpose

Prove FR-005 and NFR-003 together: when the source behind a citation has been superseded, the Beekeeper is told clearly rather than being shown outdated guidance as if it were current — and every citation, regardless of status, carries the provenance and licence metadata NFR-003 requires. Slices 0001–0003 built retrieval, jurisdiction isolation, and no-grounding behaviour; this slice is the first to expose anything about a Corpus Document beyond its passage text.

## Source Inputs

- FR-005 (source supersession), NFR-003 (provenance/licence metadata)
- Decision log: Source Supersession Mechanism And Provenance Display (this slice)
- `architecture/domain-model.md`: `Corpus Document` (status, `superseded_by_corpus_document_id`, licence terms) and `Citation` (denormalised corpus document reference) entities
- Existing schema: `corpus_documents.source`, `licence_terms`, `status`, `superseded_by_corpus_document_id` already exist from Slice 0001's migration, populated with real values by the seed script but never surfaced past the repository layer

## User Path

Given a dev-authenticated Beekeeper with a Workspace Membership, and a Corpus Document seeded as superseded by a newer one
When the Beekeeper asks a question whose closest match is the superseded document's Passage
Then the Advisor Service still answers and cites it (grounding is otherwise unaffected), but the Citation is clearly flagged as superseded, and the UI displays that warning clearly rather than presenting the guidance as current
And every Citation, superseded or not, displays its source, licence terms, and document title in the response and the UI

## Preconditions

- Same dev-authenticated User context and Workspace Membership as Slices 0001–0003 — no change.
- The two active Jurisdictions/Passages from Slices 0001–0002 remain unchanged. One new, deliberately outdated Corpus Document + Passage is added (UK jurisdiction), seeded with `status = 'superseded'` and `superseded_by_corpus_document_id` pointing at the existing current UK document.

## End-To-End Behaviour

Retrieval is otherwise unchanged from Slice 0003 (embed, find nearest Passage by jurisdiction, classify by distance). The new behaviour sits on top:

- `CorpusRepository.find_similar_passages` also returns each Passage's parent Corpus Document's title, source, licence terms, status, and (when superseded) the superseding document's title.
- `AnswerQueryWorkflow` attaches this provenance to every Citation unconditionally (NFR-003 applies regardless of status), and marks the Citation itself as superseded when its document's status is `superseded`. This is pure metadata — the generation provider and its prompt are untouched; grounding_status is unaffected, since a superseded source can still produce a `grounded` answer ("is this well-matched" and "is this current" are independent questions).
- Retrieval does not exclude superseded documents from the nearest-neighbor search — a superseded document remains citable, just never presented as current (per the domain model's existing rule). Chasing down and citing the superseding document's own content instead is explicitly out of scope for this slice.
- The web UI renders each citation as a real attribution block (document title, source, licence terms) instead of a raw passage UUID, with a distinct visual treatment when superseded (mirroring the grounding-state banners from Slice 0003).

## Layers Touched

- Web UI: citation rendering upgraded from a raw passage UUID to a title/source/licence attribution block, with a superseded-source warning treatment.
- Core API (Advisor Service): `CorpusRepository.find_similar_passages` returns document provenance alongside each Passage; `AnswerQueryWorkflow` attaches it to every Citation and informs generation when the source is superseded.
- Storage: `corpus_documents` gains one new column, `source_url` (nullable text, populated for both existing documents with real reference URLs). No other schema change — `status`/`licence_terms`/`superseded_by_corpus_document_id` already exist. `created_at` is treated as the "retrieved/version date" NFR-003 calls for for v1 — no new column, since this corpus is manually curated and seeded once, so the two are the same instant for every document that exists today. Revisit if a document is ever updated in place without a status change.
- Contracts: `CitationResponse` gains `document_title`, `source`, `source_url`, `licence_terms`, and `is_superseded` (plus `superseded_by_document_title` when applicable).
- Queue or async boundary: Not touched.
- Observability: Not touched.

## Test Seams

- Seam: `CorpusRepository.find_similar_passages` returning document provenance. Behaviour verified: the returned data reflects the actual parent Corpus Document's fields, including status and supersession, for both a current and a superseded document. Test style: integration test against a real Postgres/pgvector test database, extending `test_corpus_repository.py`.
- Seam: `AnswerQueryWorkflow`'s citation enrichment and superseded-source handling. Behaviour verified: given a test double returning a superseded document's Passage as closest, the Citation is marked superseded, and grounding_status is unaffected (still `grounded` if the distance is close enough). Also verified: every Citation carries provenance regardless of status. Test style: unit test with test doubles, extending `test_answer_query_workflow.py`.
- Seam: End-to-end web UI workflow. Behaviour verified: a citation displays its title/source/licence; a superseded source's citation additionally shows a clear warning. Test style: Playwright + Gherkin, extending the existing harness with a query worded to match the newly-seeded outdated UK passage more closely than the current one.

## Data Shape

- New column: `corpus_documents.source_url` (nullable text).
- New seed data: one additional UK Corpus Document + Passage, deliberately outdated content, `status = 'superseded'`, `superseded_by_corpus_document_id` pointing at the existing current UK document (`UK_GUIDE_DOCUMENT_ID`).
- No changes to `citations` table — corpus document provenance is joined through `passages.corpus_document_id` at read time, not denormalised onto the `citations` row. The domain model's "denormalised for convenience" note is not followed here; the join is cheap and avoids a migration plus a data-consistency invariant (denormalised column must match the passage's parent) that would need enforcing for no real benefit at this scale.

## Out Of Scope

- Chasing down and citing the superseding document's own content when a superseded source is the closest match — flagging only, per the grilled decision.
- A dedicated `retrieved_date`/version-date column distinct from `created_at` — deferred, per the grilled decision; revisit if a document is ever updated in place.
- The `retired` status value (as opposed to `superseded`) — no `retired` document is being seeded, and nothing in FR-005 requires distinguishing the two for v1.
- Source Conflict detection (FR-006) — a separate requirement, not touched here, despite touching the same `corpus_documents` table.
- Any Corpus Curator-facing tooling for marking a document superseded — remains a manual seed-script/SQL operation, consistent with the existing "manual, Corpus Curator-triggered" ingestion decision.

## Acceptance Criteria

- [x] `CorpusRepository.find_similar_passages` returns each Passage's parent Corpus Document's title, source, source URL, licence terms, and status.
- [x] Every Citation in every Answer carries provenance and licence metadata, regardless of the cited document's status.
- [x] A Query whose closest Passage belongs to a superseded Corpus Document still produces a normal grounding classification, but the Citation is marked superseded and the UI displays that warning clearly rather than presenting it as current.
- [x] The web UI displays real attribution (title, source, licence) for every citation, with a distinct visual treatment for a superseded source.
- [x] Retrieval does not exclude superseded documents from the nearest-neighbor search.

## Open Questions

None — all six open questions (retrieval semantics for superseded documents, whether to chase the superseding document's content, where the superseded signal lives in the contract, NFR-003's unconditional display scope, retrieved/version date vs. `created_at`, and adding `source_url`) were resolved via grilling before this doc was written; see the decision log entry above.
