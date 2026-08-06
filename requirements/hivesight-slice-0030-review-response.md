# Response To HiveSight's Slice 0030 (Dual-Seam Acceptance Specification Pilot) Alignment Request

**Date**: 2026-08-06
**Reviewed from**: HiveSight Slice 0030 pilot summary, plus the already-pushed shared-skill changes to `sdlc-delivery-acceptance-bdd` and `hivesight-project-delivery-context`
**Responding as**: HiveSight Advisor

The shared-skill edits (generic BDD guidance widened to describe client-neutral shared features and seam-specific bindings; HiveSight-specific detail kept in `hivesight-project-delivery-context`) are appropriately scoped — no HiveSight-specific language leaked into the generic skill. No objection to those; they're already merged.

The rest of this responds to the alignment questions and the proposal for the HiveSight ↔ Advisor boundary specifically.

## The core structural point the proposal doesn't address

HiveSight's dual-seam pilot proves something real, but it's a different problem than the one being proposed for this boundary. HiveSight's pattern is **one repo, one behaviour, two clients of that same repo** (Core API and Web UI both belong to HiveSight) — a single canonical `.feature` file living in one codebase, bound twice. The HiveSight ↔ Advisor boundary is **two independently-versioned repos**, with no shared client at all — Advisor has no browser client in this flow, and the "seam" on Advisor's side is purely an inbound API call from a system Advisor doesn't own or deploy.

Concretely: where would a canonical `hivesight-advisor` `.feature` file physically live so both repos can execute it without drift? A copy in each repo re-introduces exactly the drift risk the pilot was built to eliminate (that's the failure mode the pilot's own "two markers vs. one" example describes). A git submodule or shared package is real infrastructure neither repo has today, for a two-endpoint surface. This isn't a reason to reject the pattern — the underlying value ("describe cross-boundary behaviour once, in domain language, reviewable without reading code") is worth having — but it means literally sharing an executable file isn't the right implementation of that value here.

**Recommendation**: keep the shared behaviour description as **plain-English prose in the living contract artifact** (`hivesight-advisor-integration-contract`), not as an executable `.feature` file — the same domain-language spirit the pilot wants, without inventing cross-repo file-sharing infrastructure for a boundary this small. Each repo keeps its own executable tests, in whatever style that repo already uses, provably implementing its half of that shared prose. If the pilot's actual dual-seam mechanism proves itself further within HiveSight (more capabilities, more seams), worth revisiting whether the investment in a real shared-file mechanism is justified — not before.

## Answers to the four open alignment questions

**1. Which Advisor behaviours should become canonical Gherkin scenarios rather than API-only contract tests?**

None, under the recommendation above — Advisor's existing convention (plain, descriptively-named pytest functions with the exact scenario text quoted in each docstring, `tests/test_hivesight_*.py`) already gives the same reviewability the pilot is after, without a `.feature` file. This was a deliberate choice made at Slice 0008 (API-only integration, no UI on Advisor's side to justify a second binding), not an oversight — worth stating plainly rather than treating it as a gap to close.

**2. What endpoint and response fields should Advisor expose for treatment recommendation intake and replayable evidence?**

Already built (Slice 0011), current and stable:

```
POST /integrations/hivesight/treatment-plans
  → { contract_version, answer_id, text, grounding_status, citations }
POST /integrations/hivesight/treatment-plans/completions
  → { contract_version, id, answer_id, status }
POST /integrations/hivesight/treatment-plans/rejections
  → { contract_version, answer_id, text, grounding_status, citations, revision_exhausted }
```

One real gap for "replayable evidence" specifically: Advisor only exposes the **current** pending/latest recommendation per hive (`find_latest_suggested_by_hive`) — there's no endpoint to list a hive's full recommendation history. If HiveSight's Treatment Evidence Chain needs to replay or audit past (superseded/rejected) recommendations from Advisor directly, rather than relying entirely on what it already snapshotted on receipt, that's new work on Advisor's side, not something to assume exists. Flagging rather than building speculatively — say if it's actually needed.

**3. What stable `advisor_answer_id` and `contract_version` format should HiveSight store?**

`answer_id`: a standard UUID (v4), serialized as a JSON string — safe to store as an opaque identifier, no internal structure to parse.

`contract_version`: currently an **opaque string** (`"treatment_plan_v1"`), not a parsed semver. Advisor hasn't yet decided a versioning *scheme* (semver vs. simple increment vs. date-based) — only picked a pragmatic label. Recommend HiveSight treat it as an opaque equality check for now (store it, compare for exact match, don't parse major/minor out of it) until Advisor commits to an actual scheme — which, per the shared skill update from Slice 0011, would itself now need to be a grilled design decision, not something decided implicitly by whatever string happens to get shipped next.

**4. Which scenarios should run in both repos, and which should remain repo-local?**

Given the recommendation above (prose-shared, not file-shared), this question mostly dissolves: everything stays repo-local and repo-styled; what's shared is the *description* of the five cross-project behaviours HiveSight already listed (request → recommend, accept/decline, evidence-chain linkage, etc.), living in the contract skill as domain-language prose both sides can review against their own tests.

## One behavioural mismatch worth resolving before this goes further

The proposal states "a beekeeper accepts or declines the recommendation without rewriting the original advice" as a shared behaviour. But HiveSight's own Slice 0029.5 explicitly scoped out calling Advisor's completion/rejection endpoints at all ("does not notify HiveSight Advisor when a recommendation is accepted or declined... belongs to a later slice"). If that's still the plan, "accept/decline" is currently a HiveSight-only behaviour with no Advisor-side counterpart to describe jointly — worth clarifying which is actually true before this becomes a "shared" scenario: (a) HiveSight now intends to call Advisor's `completions`/`rejections` endpoints as part of accept/decline (a real scope change from 0029.5, and — happily — this is exactly the scenario Advisor's idempotency fix in Slice 0011 was built to support cleanly), or (b) accept/decline stays HiveSight-internal for now and this bullet should be described as repo-local, not cross-project, until that changes.

## What this does and doesn't require from Advisor right now

No code changes. This is a scoping/alignment response. The one real candidate for future work is the recommendation-history/replay endpoint (question 2) — not building it speculatively, flagging it for confirmation first.
