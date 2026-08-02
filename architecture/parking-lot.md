# Parking Lot

This document captures important work that is not in the current slice or remediation pass, but should not be forgotten.

Use this when something is out of scope now but expected later. Prefer ADRs or the decision log for settled decisions, and remediation trackers for known active problems.

## Status Values

- `parked`: deliberately deferred.
- `promoted`: moved into an active slice, remediation, ADR, or implementation plan.
- `closed`: no longer needed.
- `superseded`: replaced by another parked item or decision.

## PARK-0001: Playwright For Web UI Acceptance Testing

Status: parked
Date parked: 2026-08-02
Source: Vertical Slice 0001 (manual browser demo pass)
Area: testing

Context:

Slice 0001's implementation plan calls for an end-to-end acceptance test (step 9), and the web UI workflow (`QueryForm`/`AnswerView`) was manually verified in a browser but has no automated coverage yet. HiveSight's own web app uses Playwright specs directly for UI-level acceptance (see HiveSight's `apps/web/tests/acceptance` and its `test:acceptance` script), rather than UI-level Gherkin.

Why parked:

The human's explicit direction is to use Playwright for this project's web UI acceptance testing too, so the two products stay consistent on tooling even though they remain architecturally independent. Not yet implemented — Slice 0001's remaining test coverage (client unit test, UI component test, end-to-end acceptance test) hasn't been built.

Revisit trigger:

When building Slice 0001's end-to-end acceptance test and any subsequent web UI workflow that needs acceptance-level coverage. Set up Playwright in `apps/web` (mirroring HiveSight's `playwright.config.ts` and `tests/acceptance` structure) at that point.

Suggested owner or area:

Delivery test automation and acceptance BDD.
