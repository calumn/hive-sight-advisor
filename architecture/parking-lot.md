# Parking Lot

This document captures important work that is not in the current slice or remediation pass, but should not be forgotten.

Use this when something is out of scope now but expected later. Prefer ADRs or the decision log for settled decisions, and remediation trackers for known active problems.

## Status Values

- `parked`: deliberately deferred.
- `promoted`: moved into an active slice, remediation, ADR, or implementation plan.
- `closed`: no longer needed.
- `superseded`: replaced by another parked item or decision.

## PARK-0001: Playwright + Gherkin For Web UI Acceptance Testing

Status: promoted
Date parked: 2026-08-02
Date promoted: 2026-08-02
Source: Vertical Slice 0001 (manual browser demo pass); promoted into Slice 0001's end-to-end acceptance test
Area: testing

Context:

Slice 0001's implementation plan calls for an end-to-end acceptance test (step 9), and the web UI workflow (`QueryForm`/`AnswerView`) was manually verified in a browser but had no automated coverage yet. HiveSight's own web app uses Playwright specs written directly (see HiveSight's `apps/web/tests/acceptance` and its `test:acceptance` script) — HiveSight deliberately decided against UI-level Gherkin (see HiveSight's own parking lot, PARK-0001), keeping Playwright specs plus generated verification reports instead.

Why parked (then promoted):

The human's explicit direction for this project was to use Playwright as the execution engine (aligning with HiveSight's tooling choice) but to define the tests themselves in Gherkin — a deliberate divergence from HiveSight's own UI-testing approach, not a straight adoption of it.

Resolution:

Implemented via `playwright-bdd` (chosen over hand-rolled `@cucumber/cucumber` + Playwright wiring, since it integrates directly with the existing `@playwright/test` runner and config rather than requiring a second, separate test runner). See `apps/web/playwright.config.ts` (`defineBddConfig`), `apps/web/tests/acceptance/features/vertical_slice_0001_grounded_query_answer.feature`, and `apps/web/tests/acceptance/steps/vertical_slice_0001.steps.ts`. Run via `pnpm test:acceptance` (`bddgen && playwright test` — this playwright-bdd version needed the explicit `bddgen` generation step; auto-generation via `defineBddConfig` alone did not trigger it).

The harness seeds a dedicated `_test`-suffixed Postgres database via a `globalSetup` hook, using the stub embedding adapter (no live Voyage/Claude calls, no API keys passed to the server under test) — consistent with the Slice 0001 Test And Seed Approach decision. Runs on its own ports (8020/5193), distinct from both this project's own dev ports (8010/5183) and HiveSight's (8000/5173).

Suggested owner or area:

Delivery test automation and acceptance BDD.
