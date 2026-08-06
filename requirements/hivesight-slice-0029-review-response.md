# Response To HiveSight's Slice 0029 (Advisor Varroa Context API) Review Request

**Date**: 2026-08-06
**Reviewed from**: `calumn/hive-sight`, `architecture/vertical-slice-0029-advisor-varroa-context-api.md` and `requirements/roadmap.md`
**Responding as**: HiveSight Advisor

HiveSight's Slice 0029 doc asked four direct questions of the Advisor side under "Open Questions For Advisor Review." Answers below, plus a recommended approach for how the two systems' calls should actually compose — the doc doesn't settle this, and it changes what (if anything) Advisor needs to build.

## Answers to the four questions

**1. Does `advisor_varroa_context_v1` carry enough aggregate Varroa evidence to decide whether a treatment-plan request could later be grounded?**

Partially. It establishes *that* real, trustworthy evidence exists (coverage, warnings, whether it's test data) — but Advisor's grounding doesn't run on mite counts. Advisor's corpus differentiates guidance by situational/treatment-method attributes (temperature, brood presence, honey-super status, organic-certification standing), not by infestation severity, and none of those fields are in this payload. So: sufficient to judge whether the evidence itself is trustworthy, not sufficient alone to write a good `situational_context` query. Jurisdiction and real-world treatment conditions still need to come from somewhere else in the flow.

Separately: correctly omitting severity language ("high/medium/low/threshold crossed") is the right call — that's exactly the kind of pre-judgment Advisor's own no-unaided-generation discipline (FR-008) would refuse to build on top of.

**2. Should per-bee detections, image URLs, and detector boxes stay inside HiveSight?**

Yes, unambiguously. Advisor's query text already leaves the system boundary to third parties (Voyage, Claude) on every request — see `architecture/system-context.md`'s Retrieval And Generation Boundary. Any raw image/detection data handed to Advisor would transit further to those providers for zero grounding benefit, since Advisor's retrieval pipeline has no use for detector-level geometry. Pure exposure, no corresponding value.

**3. Are `jurisdiction_not_provided`, `source_intent_not_varroa_assessment`, `treatment_history_not_modelled` good blocking-reason names?**

Agree, no changes needed. They don't collide with or contradict Advisor's own vocabulary (`grounding_status`'s `grounded`/`partial`/`ungrounded` is a separate, unrelated concern). Suggestion: since these strings are effectively part of the contract, they should fall under the same `contract_version` bump discipline as everything else — a silent rename would be a breaking change for any consumer that pattern-matches on them.

**4. Does `treatment_history.status = not_modelled` + `recent_treatment_count = null` correctly distinguish missing domain modelling from no recent treatment?**

Strongly agree. This mirrors a principle already applied on the Advisor side in two places: `grounding_status: ungrounded` is always an explicit state, never a silently empty answer, and the superseded/retired distinction on corpus documents exists for exactly the same reason — absence of information must never be represented the same way as confirmed absence of the thing itself. Good, independently-arrived-at consistency between the two systems.

## Recommended approach: HiveSight stays the sole caller into Advisor

**Recommendation**: HiveSight should treat the Slice 0029 context endpoint as its own internal evidence-assembly step — whether exposed as a real HTTP endpoint for testability/observability, or kept as internal service logic — and continue to be the party that calls Advisor's existing `POST /integrations/hivesight/treatment-plans` with an assembled `situational_context` and a resolved `jurisdiction_id`. Advisor should not become an outbound caller into HiveSight's API.

**Why**:

1. **Preserves Advisor's already-decided architectural independence.** The V1 Scope Boundary decision (Advisor repo, `requirements/decision-log.md`, 2026-07-31) explicitly settled that Advisor is architecturally independent of HiveSight. Advisor calling into HiveSight's API to do its own job would be new, real coupling that has never been scoped or grilled on the Advisor side — a bigger decision than it looks from HiveSight's side alone.
2. **Zero new work required on Advisor's side.** The existing `/integrations/hivesight/treatment-plans` contract (Slice 0008) is already built and tested exactly as-is; this approach needs no change to it.
3. **Keeps the trust boundary one-directional.** One caller, one callee — not a two-way dependency between two systems each meant to remain independently replaceable. This matches the general pattern in the shared `sdlc-architecture-service-integration-contract` skill: scope the integration narrowly, don't let it grow into mutual coupling by default.
4. **HiveSight is better positioned to write good `situational_context` prose than Advisor is to reconstruct it from structured JSON.** HiveSight holds the richer domain data (temperature, brood status, honey-super status, treatment history) that question 1 above shows Advisor's grounding actually needs. Assembling that into a well-written query at the source — where all of that context already lives — beats having Advisor try to synthesize an equivalent query from an evidence payload it wasn't designed to interpret directly.
5. **Directly closes the question-1 gap.** If HiveSight assembles the query text, it can naturally fold in the missing situational fields (weather, brood status, supers) alongside the mite-count evidence in the same prose — solving the gap at the one place that actually has that data, rather than pushing the problem onto Advisor.

## One issue worth fixing regardless of the composition decision

**Header name collision.** Advisor checks `X-HiveSight-Service-Key` on requests it receives *from* HiveSight (Advisor's own configured secret; HiveSight must send it). Slice 0029 has HiveSight check the *same header name* on requests it receives *from* Advisor — a different secret, opposite direction. Reusing the header name across two directions is a real footgun: nothing in the name itself signals whose secret it is, so a misconfigured client sending the wrong value gets a generically unhelpful 401 either way, and it becomes easy to accidentally send the same value in both directions during testing. Recommend HiveSight name its own inbound header something direction-specific, e.g. `X-Advisor-Service-Key` — the name should say "this authenticates Advisor calling in," distinct from the existing header's "this authenticates HiveSight calling in."

## What this does and doesn't require from Advisor right now

If the recommended approach above is accepted, **no code changes are required on the Advisor side** as a result of Slice 0029 — the existing `/integrations/hivesight/treatment-plans` contract already covers what HiveSight needs to call. This response is scoping/architecture feedback only, not a request for a new Advisor slice.
