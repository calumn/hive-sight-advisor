# Vertical Slice 0002: Second Jurisdiction And Non-Blending Proof

## Purpose

Prove FR-003 (jurisdiction-aware retrieval; no blending of guidance across jurisdictions into a single unattributed answer) with a second, genuinely independent Jurisdiction — US — alongside Slice 0001's UK Jurisdiction. Slice 0001 seeded exactly one Jurisdiction, so FR-003's non-blending guarantee was never actually exercised; it existed only as a structural property of the retrieval query (scoped by `jurisdiction_id`), unproven by any real second dataset. This slice adds real US content and demonstrates, end to end, that selecting a Jurisdiction retrieves and cites only that Jurisdiction's Passage — never the other's — even though both now live in the same corpus.

This slice also corrects a factual error introduced in Slice 0001: the decision log (`requirements/decision-log.md`, V1 Jurisdiction Scope) explicitly names **HBHC (Honey Bee Health Coalition) as the US source and APHA BeeBase as the UK source**, but Slice 0001's seed script mislabelled the UK Corpus Document's source as "Healthy Bees Healthy Colonies (HBHC) guide." That is corrected here, at the same moment a real HBHC-sourced US document is added — the point where the mislabelling would otherwise become actively misleading rather than merely inconsistent.

## Source Inputs

- FR-003 (jurisdiction-aware retrieval, non-blending guarantee)
- Decision log: V1 Jurisdiction Scope (US/HBHC, UK/APHA BeeBase), Jurisdiction Resolution (explicit UI selection, no inference)
- `CONTEXT.md`: `Jurisdiction`, `Corpus Document` definitions
- `architecture/domain-model.md`: `Jurisdiction`, `Corpus Document`, cross-jurisdiction invariant on `Answer`
- Slice 0001 (`architecture/vertical-slice-0001-grounded-query-answer-with-seeded-corpus.md`) and its implementation plan — this slice extends that seam rather than building a new one

## User Path

Given a dev-authenticated Beekeeper with a Workspace Membership, and two seeded Corpus Documents — one UK (APHA BeeBase, corrected from Slice 0001), one US (HBHC) — each with at least one Passage
When the Beekeeper selects Jurisdiction = US and submits a Query
Then the Advisor Service retrieves and cites only the US Passage, and the generated Answer is grounded exclusively in US guidance — never mentioning or citing the UK Passage
And when the Beekeeper instead selects Jurisdiction = UK for the same question, the Advisor Service retrieves and cites only the UK Passage

## Preconditions

- Same dev-authenticated User context and Workspace Membership as Slice 0001 — no change.
- Two Jurisdictions seeded (`us`, `uk`), each with exactly one Corpus Document and one Passage, hand-seeded via the existing checked-in seed script (extended, not replaced).

## End-To-End Behaviour

Beekeeper opens the web app, selects Jurisdiction = US (a second option now available alongside United Kingdom), types a Varroa question, submits. The Advisor Service embeds the Query, runs the same pgvector similarity search already built in Slice 0001 — scoped to `jurisdiction_id = US` — retrieves the US Passage, and generates an Answer grounded only in it. Repeating the same question with Jurisdiction = UK selected retrieves and cites only the UK Passage. No code path exists that could retrieve both at once for a single Query, since Jurisdiction is a required, explicit selection made before retrieval runs (confirmed by the Jurisdiction Resolution decision) — this slice's job is to prove that guarantee holds with real data, not to build new prevention logic.

## Layers Touched

- Web UI: `QueryForm`'s Jurisdiction selector gains a second option (US). No other UI change.
- Core API (Advisor Service): No new endpoints or seams — reuses Slice 0001's `POST /queries`, `CorpusRepository.find_similar_passages`, `AnswerQueryWorkflow` unchanged.
- Storage: Postgres — new rows only (US `Jurisdiction`, `Corpus Document`, `Passage`); no schema changes. Existing UK `Corpus Document.source` corrected from "HBHC" to "APHA BeeBase".
- Contracts: Unchanged — `jurisdiction_id` was already a required field on `POST /queries`.
- Queue or async boundary: Not touched.
- Observability: Not touched.

## Test Seams

- Seam: `CorpusRepository.find_similar_passages`, scoped by `jurisdiction_id`. Behaviour verified: with two Passages seeded in different Jurisdictions, a query scoped to Jurisdiction A returns only Jurisdiction A's Passage, never Jurisdiction B's, even when B's embedding is closer by raw vector distance. This is the one genuinely new test case Slice 0001 never exercised (it only ever seeded one Jurisdiction). Test style: integration test against a real Postgres/pgvector test database, extending `test_corpus_repository.py`.
- Seam: End-to-end web UI workflow, Playwright + Gherkin (Slice 0001's harness, extended). Behaviour verified: selecting Jurisdiction = US and asking a question returns an Answer citing only the US Passage; selecting UK returns an Answer citing only the UK Passage. Test style: extend the existing `.feature` file with a second scenario (or a Scenario Outline over both Jurisdictions), seeded via the same `globalSetup` + stub-embedding test-database pattern as Slice 0001.

## Data Shape

No schema changes. New rows only, using the existing `jurisdictions`, `corpus_documents`, and `passages` tables from Slice 0001's migration:

- Jurisdiction: `us` (in addition to Slice 0001's `uk`)
- Corpus Document: US document, source "Honey Bee Health Coalition (HBHC) Tools for Varroa Management guide", licence CC BY-NC-ND
- Passage: US content genuinely distinct from the UK Passage — not just reworded, but naming different jurisdiction-appropriate guidance (e.g. HBHC's rotation among EPA-registered miticide classes such as amitraz strips and formic-acid pads, versus the UK Passage's oxalic acid vaporisation focus) — so a real answer difference is demonstrable, not merely a difference in source label.
- Correction: UK Corpus Document's `source` field updated from "Healthy Bees Healthy Colonies (HBHC) guide" to "APHA BeeBase", matching the decision log.

## Out Of Scope

- EU Jurisdiction (still deferred per V1 Jurisdiction Scope; member-state granularity required when it is eventually added).
- Any UI or backend mechanism for a single Query to span or compare multiple Jurisdictions — Jurisdiction Resolution explicitly rejected inference/multi-jurisdiction handling for v1; each Query still targets exactly one Jurisdiction.
- Source supersession, conflict detection between the two Jurisdictions' documents (FR-005, FR-006) — the two Passages here are jurisdiction-appropriate, not framed as disagreeing sources within the same Jurisdiction.
- Corrections (FR-007), no-grounding behaviour (FR-008) — unchanged from Slice 0001's exclusions.
- A real Corpus Curator ingestion workflow — still a manual, checked-in seed script.
- Displaying the selected Jurisdiction on the Answer itself — the Beekeeper already knows what they picked; not required to prove FR-003.

## Acceptance Criteria

- [ ] A dev-authenticated Beekeeper can select either UK or US as Jurisdiction in the web UI.
- [ ] A Query submitted with Jurisdiction = US retrieves and cites only the US Passage.
- [ ] A Query submitted with Jurisdiction = UK retrieves and cites only the UK Passage.
- [ ] The UK Corpus Document's `source` field reads "APHA BeeBase", not "HBHC".
- [ ] `CorpusRepository.find_similar_passages` has a test proving jurisdiction-scoped retrieval excludes the other Jurisdiction's Passage even when seeded in the same database.
- [ ] The Playwright + Gherkin acceptance suite covers both Jurisdictions, not just UK.

## Open Questions

None — this slice's shape follows directly from decisions already confirmed in Slice 0001 and the existing decision log; no new grilling required before implementation.
