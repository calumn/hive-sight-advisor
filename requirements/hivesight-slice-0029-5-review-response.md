# Response To HiveSight's Slice 0029.5 (Advisor Treatment Recommendation Intake) Review Request

**Date**: 2026-08-06
**Reviewed from**: `calumn/hive-sight`, `architecture/vertical-slice-0029-5-advisor-treatment-recommendation-intake.md`
**Responding as**: HiveSight Advisor

This slice asks Advisor to confirm six specific things under "HiveSight Advisor Review Questions." Answers below, verified directly against the actual built code (not recalled from memory) — plus one significant gap this review surfaced empirically in Advisor's own implementation, not in HiveSight's design.

## First, a confirmation worth stating plainly

Slice 0029.5's design has HiveSight remain the sole caller into Advisor (`HiveSightAdvisorTreatmentPlanAdapter` calls `POST /integrations/hivesight/treatment-plans`; Advisor never calls back into HiveSight; no notification on accept/decline). This is exactly the approach recommended in the Slice 0029 review response — good to see it adopted, and it means the architectural-independence concern from that review is settled.

## Answers to the six review questions

**1. Should HiveSight continue to call `POST /integrations/hivesight/treatment-plans`?**

Yes, confirmed — that endpoint is built, tested, and stable (Slice 0008).

**2. Exact expected request shape for `hive_id`, `jurisdiction_id`, `situational_context`?**

From the actual Pydantic model (`routers/hivesight_integration.py`):

```
hive_id: str                 # opaque — Advisor never interprets it
jurisdiction_id: UUID        # see the flagged issue below — this is Advisor's *internal* primary key, not a stable public code
situational_context: str     # free text; becomes the RAG query text verbatim
```

**3. Embed Varroa context under `situational_context`, or a narrower structure?**

There is no other option today — `situational_context` is the only field Advisor's endpoint accepts; there is no structured evidence field. So yes, embed as well-written prose, per the Slice 0029 review's recommendation that HiveSight (which holds the richer domain context — temperature, brood status, honey supers) is better positioned to write that prose than Advisor would be to reconstruct it from JSON.

**4. Exact response shape to persist — text/grounding/citations only, or a structured schedule too?**

Text, grounding status, and structured citations only — there is no structured treatment schedule (no dates, doses, or step list). Exact shape, from `routers/hivesight_integration.py`:

```json
{
  "text": "string",
  "grounding_status": "grounded | partial | ungrounded",
  "citations": [
    {
      "passage_id": "uuid",
      "document_title": "string",
      "document_source": "string",
      "document_source_url": "string | null",
      "document_licence_terms": "string",
      "is_superseded": "boolean",
      "superseded_by_document_title": "string | null"
    }
  ]
}
```

One rendering detail worth knowing: the `text` field is free prose and does **not** contain inline citation markers (no `[1]`-style references tied positionally to the `citations` array — verified against the actual generation prompt/schema in `adapters/generation_claude.py`). `citations` is simply "the passages this answer drew on," meant to be displayed as a separate reference list (as Advisor's own web UI does), not cross-referenced inline. If HiveSight's UI eventually wants inline citation markers, that would need a prompt/schema change on Advisor's side — not something to assume exists today.

**5. What `contract_version` name should HiveSight record?**

None exists yet — Advisor's responses currently have no version field at all. This was already flagged as a gap in the Slice 0029 review. **Recommend Advisor add one (e.g. `treatment_plan_v1`) before HiveSight builds Slice 0029.5 against this contract**, so there's an actual value for `advisor_response_contract_version` to record rather than an empty/inferred one. Low effort, and much cheaper to add now than after HiveSight has already built persistence around its absence.

**6. Additional provenance fields for audit or later governed learning?**

Everything Advisor returns for provenance is already in the citations array above (title, source, source URL, licence terms, supersession status). One gap: Advisor does not currently return its own internal `answer_id` (or `query_id`) in the response — there's no stable Advisor-side identifier HiveSight could store to correlate its own snapshot back to Advisor's internal record for audit. If audit correlation matters (and Slice 0029.5's provenance-snapshot design suggests it does), recommend Advisor add `answer_id` to the response payload.

## A gap this review found in Advisor's own implementation, verified empirically

Slice 0029.5 deliberately does **not** call Advisor's completion or rejection endpoints in this slice ("Slice 0029.5 does not notify HiveSight Advisor when a recommendation is accepted or declined... belongs to a later cross-system workflow slice"). That's a reasonable scoping choice on its own — but combined with how Advisor's graph is keyed today, it produces a real gap.

Advisor keys its LangGraph thread purely by `hive_id` (`treatment-plan-{hive_id}`, permanent, never rotated). I tested directly what happens if `request_treatment_plan` is called a second time for the same `hive_id` while the first suggestion was never confirmed or rejected — exactly the situation Slice 0029.5's own scoping guarantees will happen (since it never resolves the first one, and HiveSight's "one open course blocks a new request" guard is on HiveSight's own course concept, not on Advisor's unresolved suggestion state):

```
First call:  proposed_treatment id=8e20affc..., status=suggested
Second call: proposed_treatment id=675cb27b..., status=suggested   # a brand new, unrelated row
Same row reused? False
```

The second call silently starts a fresh graph run on the *same* thread, creating a second, unlinked `proposed_treatments` row — no `supersedes_proposed_treatment_id` back to the first (that link only gets set on the reject-and-revise path, not a fresh top-level request). The first suggestion doesn't error, doesn't get superseded, doesn't get flagged — it just becomes permanently unreachable (only the newest `suggested` row is ever returned by lookup) while still sitting in the database forever as `suggested`, never resolvable.

This is an Advisor-side bug, not something HiveSight needs to design around. **Recommended fix, before Slice 0029.5 goes live for real**: make `request_treatment_plan` idempotent per-hive when an unresolved suggestion already exists — if a `suggested` `Proposed Treatment` already exists for a `hive_id`, return it instead of starting a new graph run, mirroring exactly the idempotency HiveSight has already chosen for its own side ("retrying the same pending request returns the existing pending recommendation"). This is symmetric with HiveSight's design rather than introducing a new pattern, and would need to be an Advisor-side slice, scoped and grilled properly, before this integration is exercised for real — not something to patch silently.

## The `jurisdiction_id` contract shape is worth reconsidering before HiveSight builds against it

Advisor's `jurisdiction_id` is a raw internal primary key (a UUID from Advisor's own `jurisdictions` table), and there is currently no endpoint anywhere on Advisor for a caller to discover what those UUIDs actually are (confirmed — no jurisdiction-listing route exists). For HiveSight to send a valid `jurisdiction_id`, it would need to know Advisor's specific internal UUIDs out of band (hardcoded), which would silently break if Advisor ever reseeds or regenerates that data.

Recommend Advisor accept a stable **jurisdiction code** (`"uk"` / `"us"`) instead of — or in addition to — the internal UUID, since a code is the kind of identifier meant to be stable across a service boundary, unlike a primary key. This is squarely an Advisor-side contract fix, not something HiveSight can work around on its own.

## Everything else in the design: no objections

The rest of Slice 0029.5's grilling decisions — separate `TreatmentRecommendation` vs `HiveTreatmentCourse` records, the explicit `TreatmentEvidenceChain` id, blocked/failed attempts recorded without creating a recommendation, accept/decline idempotency on HiveSight's own side, stub-vs-real adapter provenance blocking stub-backed advice in production — are all HiveSight-side domain modelling and don't require anything from Advisor. No concerns from this side.

## Summary of what Advisor should do before this integration is exercised for real

1. **Fix the idempotent-request gap** (found above) — a real correctness bug, not a nice-to-have, since Slice 0029.5's own design guarantees it will be hit.
2. **Add `contract_version` to response payloads.**
3. **Consider accepting a jurisdiction code, not just an internal UUID.**
4. **Consider adding `answer_id` to the response** for audit correlation, if that matters to HiveSight's provenance model.

None of these require input from HiveSight to resolve — they're all Advisor-side follow-up work. Happy to scope them as proper vertical slices (grilled, tested) rather than quick patches, given #1 in particular is a real correctness issue.
