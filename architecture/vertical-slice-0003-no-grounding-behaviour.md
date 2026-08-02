# Vertical Slice 0003: No-Grounding Behaviour

## Purpose

Prove FR-008: when a Query has no relevant grounding in the corpus, the Advisor Service does not answer from unsourced general knowledge. It states explicitly that it has no grounded answer, or — when something related but not a direct match exists — offers that closest material, clearly labelled as a partial match rather than a direct answer. Slices 0001 and 0002 only ever exercised the `grounded` path; this slice is what actually makes `grounding_status` mean something.

## Source Inputs

- FR-008 (no-grounding behaviour)
- Decision log: FR-008 Grounding Classification Mechanism
- `architecture/domain-model.md`: `Answer` grounding statuses (`grounded`/`partial`/`ungrounded`) and their Citation-count invariant
- Slices 0001–0002 (`architecture/vertical-slice-0001-grounded-query-answer-with-seeded-corpus.md`, `architecture/vertical-slice-0002-second-jurisdiction-and-non-blending-proof.md`) — this slice extends their retrieval and generation seams rather than building new ones

## User Path

Given a dev-authenticated Beekeeper with a Workspace Membership, and the two seeded Corpus Documents (UK, US) from Slices 0001–0002
When the Beekeeper selects a Jurisdiction and submits a Query unrelated to Varroa management
Then the Advisor Service returns an Answer with `grounding_status = ungrounded`, zero Citations, and text stating explicitly that it has no grounded answer — without ever calling the generation provider
And when the Beekeeper instead submits a Query that is loosely related but not a direct match to the seeded Passage, the Advisor Service returns an Answer with `grounding_status = partial`, citing the closest Passage but clearly labelling it as not a direct answer

## Preconditions

- Same dev-authenticated User context and Workspace Membership as Slices 0001–0002 — no change.
- The two Jurisdictions and Passages already seeded by Slices 0001–0002. No new corpus data is required — this is a retrieval-threshold and classification slice, not a corpus slice.

## End-To-End Behaviour

Beekeeper submits a Query as before. The Advisor Service embeds it, retrieves the closest Passage in the selected Jurisdiction along with its similarity distance, and classifies against two provisional thresholds:

- Distance within the "close enough" threshold → unchanged from Slice 0001/0002: generate and cite normally, `grounding_status = grounded`.
- Distance beyond that but within a wider "still related" threshold → generate an Answer that explicitly signals it may not directly answer the question, citing the Passage, `grounding_status = partial`.
- Distance beyond the wider threshold, or no Passage exists at all for that Jurisdiction → skip the generation call entirely, return a canned "no grounded answer" message, zero Citations, `grounding_status = ungrounded`.

Per the decision log, this classification is a deterministic distance threshold, not a judgment delegated to the generation model — and the threshold values themselves are provisional, calibrated against a handful of real test queries run against the existing two Passages, not a properly tuned dataset.

## Layers Touched

- Web UI: `AnswerView` gains a distinct visual treatment per grounding state — not just a different word in the same layout.
- Core API (Advisor Service): `CorpusRepository.find_similar_passages` now returns each Passage's similarity distance alongside it. `AnswerQueryWorkflow` gains threshold-based classification and conditionally skips the generation call.
- Storage: No schema changes — `answers.grounding_status` already exists as a plain column; this slice is the first to populate it with values other than `grounded`.
- Contracts: No new response fields — `grounding_status` is already part of `POST /queries`'s response shape.
- Queue or async boundary: Not touched.
- Observability: Not touched.

## Test Seams

- Seam: `CorpusRepository.find_similar_passages` returning distance. Behaviour verified: the returned distance reflects genuine cosine distance — a Passage seeded to be semantically far from the query embeds to a large distance value, a close one to a small value. Test style: integration test against a real Postgres/pgvector test database, extending `test_corpus_repository.py`.
- Seam: `AnswerQueryWorkflow`'s threshold classification. Behaviour verified: given controlled distances via test doubles, the workflow selects the correct `grounding_status`, and — this is the behaviour most worth testing thoroughly — the `GenerationProvider` is never called when the result is `ungrounded`. Test style: unit test with test doubles, asserting a call count of zero on a fake `GenerationProvider`, extending `test_answer_query_workflow.py`.
- Seam: End-to-end web UI workflow. Behaviour verified: an off-topic question renders the `ungrounded` UI state; a borderline question renders the `partial` state citing a Passage labelled as such. Test style: Playwright + Gherkin, extending the existing harness with real distance values from the two seeded Passages (no new seed data needed).

## Data Shape

No new tables or columns. `answers.grounding_status` already exists (Slice 0001's migration); this slice is what actually exercises `partial` and `ungrounded` rather than only ever writing `grounded`.

## Out Of Scope

- Empirically tuning the threshold values against a real, larger query set — explicitly provisional per the decision log, not a blocking concern for this slice.
- Any mechanism for the Beekeeper to flag a wrong ungrounded/partial classification — that is FR-007 (Correction), a separate requirement not touched here.
- Cross-jurisdiction fallback when ungrounded in the selected Jurisdiction (e.g. suggesting "try the other Jurisdiction"). The Jurisdiction Resolution decision already rejected inference and blending for v1 — staying ungrounded within the selected Jurisdiction is correct behaviour, not a gap to patch around.
- Source supersession (FR-005) and source conflict surfacing (FR-006) — separate requirements, not touched here.

## Acceptance Criteria

- [ ] `CorpusRepository.find_similar_passages` returns the similarity distance alongside each Passage.
- [ ] A Query whose closest Passage exceeds the "too far" threshold returns `grounding_status = ungrounded`, zero Citations, and never calls the generation provider.
- [ ] A Query whose closest Passage falls between the two thresholds returns `grounding_status = partial`, with a Citation to that Passage and generated text that explicitly signals it may not be a direct answer.
- [ ] A Query whose closest Passage is within the "close enough" threshold behaves exactly as in Slice 0001/0002 (`grounding_status = grounded`), unchanged.
- [ ] The web UI visually distinguishes all three grounding states, not only via a text label.
- [ ] The threshold values are documented in code and in the decision log as provisional, not empirically validated.

## Open Questions

None — all open questions (classification mechanism, ungrounded call-skipping, threshold calibration approach, partial-in-scope) were resolved via grilling before this doc was written; see the decision log entry above.
