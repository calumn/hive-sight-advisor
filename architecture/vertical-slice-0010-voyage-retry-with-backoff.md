# Vertical Slice 0010: Voyage Retry With Backoff

## Purpose

`VoyageEmbeddingProvider.embed()` has no retry/backoff handling — a transient Voyage error (most concretely, the free-tier rate limit this project has hit for real during threshold calibration) currently propagates straight up and fails the whole request. This slice adds retry-with-backoff at the adapter level, so a transient failure is retried automatically and invisibly to every caller — both the plain web-UI query flow and the agentic `TreatmentPlanWorkflow` — rather than needing a LangGraph-specific fix that would only cover one of the two.

## Source Inputs

- `requirements/roadmap.md`, "Handle Voyage AI's free-tier rate limits properly" — the item this slice closes; explicitly notes the rate limit was hit manually during threshold calibration and worked around with a backgrounded script and manual sleeps, not real handling.
- Grilling session (2026-08-05), five questions: adapter-level vs. LangGraph-level placement, which exceptions are retryable, retry count/backoff shape, scope (Voyage only), and the test seam.
- Existing constructor-injection pattern already used throughout this codebase's adapters (e.g. `ClaudeGenerationProvider`, `CorpusRepository`) — this slice's test seam follows the same shape, not a new one.

## User Path

No new Gherkin scenario — this is an internal-only reliability change with no new Beekeeper-visible behaviour. The Answer a Beekeeper receives is identical whether Voyage succeeded on the first attempt or the fourth; nothing about grounding, citations, or response shape changes. Per the existing acceptance-scenario-signoff convention, a scenario is skipped here rather than forced into existence.

## Preconditions

- None beyond what already exists (a configured Voyage API key selects `VoyageEmbeddingProvider` over the stub, per existing `dependencies.py` wiring — unchanged by this slice).

## End-To-End Behaviour

1. `VoyageEmbeddingProvider.embed()` calls the underlying Voyage client as before.
2. If the call raises a **retryable** error (`RateLimitError`, `ServiceUnavailableError`, `Timeout`, `APIConnectionError`, `TryAgain`), the call is retried automatically: up to 3 retries (4 attempts total), exponential backoff starting at 1 second and doubling, capped at 8 seconds, with jitter.
3. If the call raises a **non-retryable** error (`AuthenticationError`, `InvalidRequestError`, `MalformedRequestError`), it propagates immediately, exactly as today — retrying a bad API key or a malformed request would only waste time before failing anyway.
4. If all retries are exhausted, the final exception propagates to the caller exactly as an unretried failure would today — this slice changes *when* a failure surfaces, not what happens once retries are genuinely exhausted.
5. Every other caller (`AnswerQueryWorkflow`, and therefore both the plain web query flow and `TreatmentPlanWorkflow`'s `Recommend` node) is unaffected by this change beyond becoming more resilient to transient failures — no caller-side code changes.

## Layers Touched

- Web UI: Not touched.
- Advisor API: Not touched.
- Service Workflow: Not touched — deliberately, per the grilled decision to fix this at the adapter level rather than inside the LangGraph graph.
- Storage: Not touched.
- Contracts: Not touched.
- Observability: Not touched (a future, separate item — logging retry attempts is worth doing but isn't required to prove this slice's behaviour).
- Adapter: `VoyageEmbeddingProvider` gains a `tenacity`-based retry decorator around the Voyage client call. `tenacity` moves from an implicit transitive dependency (currently pulled in via `langchain-core`) to an explicit direct dependency in `pyproject.toml`, since this slice imports it directly.

## Test Seams

- Seam: `VoyageEmbeddingProvider.__init__`'s client parameter (new, optional — defaults to constructing the real `voyageai.Client`, following the same injectable-collaborator pattern already used elsewhere in this codebase).
  Behaviour verified: a fake client that raises a retryable error N times before succeeding results in `embed()` eventually returning the successful result, having been called N+1 times; a fake client that always raises a retryable error results in the final exception propagating after exactly 4 total attempts; a fake client that raises a non-retryable error results in immediate propagation with exactly 1 attempt (no retry).
  Test style: unit, with tenacity configured for near-zero wait in tests (via a constructor-level override) so the test suite doesn't actually sleep for up to 8 seconds per case.

## Data Shape

None — no schema, contract, or persisted-data changes.

## Out Of Scope

- `ClaudeGenerationProvider` retry handling — no real problem has surfaced there yet; parked as a separate future item rather than bundled in speculatively.
- Structured retry logging/observability (e.g. a structured event per retry attempt) — real value, but not required to prove this slice's core behaviour; the existing roadmap item on API observability is the more natural home for it.
- Any change to the stub embedding provider — it never talks to a real API and has nothing to retry.
- Any LangGraph-level retry pattern — considered and explicitly rejected during grilling in favour of the adapter-level fix, since a graph-level retry would only protect the agentic flow and leave the more heavily used plain query flow exactly as exposed as it is today.

## Acceptance Criteria

- [x] Retrying-then-succeeding, always-failing, and non-retryable-error paths are all covered by unit tests against an injected fake client — no real Voyage API calls in the default test suite. See `tests/test_embedding_voyage_retry.py`.
- [x] The test suite does not incur real multi-second sleeps (tenacity's wait is overridable for tests).
- [x] `tenacity` is added as an explicit direct dependency in `pyproject.toml`.
- [x] No behavioural change to any caller of `AnswerQueryWorkflow` — the full existing backend suite (including `test_treatment_plan_workflow.py` and `test_hivesight_*` router tests) passes unmodified. 75 passed, 4 skipped.
- [x] `requirements/roadmap.md`'s "Handle Voyage AI's free-tier rate limits properly" item is marked done, pointing at this slice.

## Open Questions

None outstanding — all design questions from scoping were resolved and signed off (2026-08-05).
