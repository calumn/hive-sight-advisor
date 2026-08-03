# Vertical Slice 0007: Treatment Trade-Off Comparison

## Purpose

Prove FR-004: given a question about Varroa treatment, the system compares applicable treatment options and surfaces trade-offs (temperature constraints, organic-certification compatibility, treatment duration) rather than always grounding on a single passage and staying silent about alternatives. The UK jurisdiction now has three real treatment-option documents (Slice 0002 corpus growth) and the US jurisdiction has two (the original guide plus Formic Pro, added via Slice 0006's tooling) — this slice is what actually makes use of that breadth.

## Source Inputs

- FR-004 (treatment trade-off comparison)
- Decision log: Treatment Trade-Off Comparison Mechanism (this slice)
- Corpus content already in place: UK (oxalic acid, Apivar/amitraz, Apiguard/thymol), US (HBHC rotation guidance, Formic Pro)

## User Path

Given a dev-authenticated Beekeeper with a Workspace Membership, and a Jurisdiction with more than one genuinely relevant treatment-option Passage
When the Beekeeper asks a question about Varroa treatment
Then the Advisor Service retrieves the several closest Passages in that Jurisdiction (not just the single closest), and the generated Answer compares whichever of them are genuinely relevant — highlighting differences like temperature constraints, organic-certification compatibility, and treatment duration — citing each Passage it actually drew on
And when only one Passage is genuinely relevant, the Answer reads exactly as it did before this slice — a single grounded answer, not a forced comparison

## Preconditions

- Same dev-authenticated User context and Workspace Membership as prior slices — no change.
- Existing corpus content (UK and US), no new seeding required for this slice specifically.

## End-To-End Behaviour

- `CorpusRepository.find_similar_passages` is called with a raised limit (5, up from 1) instead of only the single closest Passage — no change to the repository itself, which already accepted a `limit` parameter.
- `AnswerQueryWorkflow`'s grounding classification is unchanged: `grounding_status` is still derived purely from the single closest Passage's distance, exactly as Slice 0003 built it. Comparison and grounding are independent questions — a Beekeeper getting a genuinely useful comparison across three so-so matches shouldn't be penalised as `partial`, and a single excellent match shouldn't be forced into a comparison it doesn't need.
- `ClaudeGenerationProvider`'s prompt is extended to explicitly compare across the given Passages when more than one is genuinely relevant, calling out temperature constraints, organic-certification compatibility, and treatment duration where the Passages describe them — but is not instructed to force a comparison when only one Passage actually applies.
- Citations already support more than one entry (no change needed — `Citation` has always been a list); a comparison Answer simply ends up citing more than one Passage, exactly like the existing citation-rendering UI already handles.
- The stub generation provider is unchanged: it already joins and cites every Passage it's given, which is sufficient to exercise the multi-passage retrieval mechanism in tests and the acceptance suite, even though it doesn't produce a qualitatively "smart" comparison the way the real Claude adapter does.

## Layers Touched

- Core API (Advisor Service): `AnswerQueryWorkflow` retrieves up to 5 Passages instead of 1; `ClaudeGenerationProvider`'s system prompt gains explicit comparison instructions.
- Web UI: Not touched — the existing prose answer plus citations list already renders multiple citations correctly (built in Slices 0004–0005).
- Storage: Not touched — no new columns; trade-off attributes stay as prose within `passages.text_content`, not structured fields, per the grilled decision.
- Contracts: Not touched — `AnswerResponse`/`CitationResponse` already support multiple citations.
- Queue or async boundary: Not touched.
- Observability: Not touched.

## Test Seams

- Seam: `AnswerQueryWorkflow` retrieval width. Behaviour verified: given a fake `CorpusRepository` returning multiple Passages, the workflow retrieves and passes all of them to the generation provider (not just the closest), and grounding_status is still computed from the closest one only. Test style: unit test with test doubles, extending `test_answer_query_workflow.py`.
- Seam: `ClaudeGenerationProvider`'s comparison prompt (live, not in the default suite). Behaviour verified: given two genuinely distinct real treatment Passages (e.g. Apivar and Apiguard), the generated text mentions both and draws out at least one real difference between them, rather than silently picking one. Test style: live contract test skipped without `ANTHROPIC_API_KEY`, matching the existing `test_generation_claude_live.py` pattern.
- Seam: End-to-end web UI workflow. Behaviour verified: a UK query about Varroa treatment options results in an Answer citing more than one of the UK jurisdiction's real treatment documents. Test style: Playwright + Gherkin, extending the existing harness — the stub generation provider's "cite everything it's given" behaviour is sufficient to prove the retrieval-and-citation mechanism works end-to-end, even without the real comparison-quality prose.

## Data Shape

No schema changes. No new seed data — this slice makes use of Passage content already in the corpus from Slices 0002 and 0006.

## Out Of Scope

- Structured trade-off attributes (temperature/organic-certification/duration as columns rather than prose) — per the grilled decision, deferred until prose-based comparison proves insufficient.
- Any explicit "is this a comparison question" intent detection — per the grilled decision, retrieval simply always widens; the model naturally produces a single answer or a comparison depending on what's genuinely relevant.
- A structured comparison UI (e.g. a trade-off table) — per the grilled decision, the existing prose-plus-citations rendering is unchanged.
- FR-006 (source conflict detection) — a related but separate requirement; this slice's wider retrieval is not itself the conflict-detection mechanism, even though it retrieves more of the same content that mechanism would eventually need.

## Acceptance Criteria

- [x] `AnswerQueryWorkflow` retrieves up to 5 Passages per Query instead of 1.
- [x] `grounding_status` remains based purely on the single closest Passage's distance, unaffected by how many Passages were retrieved for comparison purposes.
- [x] Given multiple genuinely relevant treatment-option Passages, the real Claude adapter's generated Answer compares them, citing more than one.
- [x] Given only one genuinely relevant Passage, the Answer reads as a single grounded answer, not a forced comparison.
- [x] The web UI displays a multi-citation Answer correctly using its existing rendering, with no new UI code required.

## Open Questions

None — all five open questions (prose vs. structured trade-off attributes, always-widen vs. intent-detected retrieval, how many Passages to retrieve, whether grounding semantics change, and whether the UI needs new structure) were resolved via grilling before this doc was written; see the decision log entry above.
