# HiveSight Advisor — Orientation

Read this first in any new session. It's a pointer file, not a restatement — the docs below are the actual source of truth and stay more current than anything summarized here.

## Start here, in order

1. [`README.md`](README.md) — what this is, current status, dev setup.
2. [`CONTEXT.md`](CONTEXT.md) — domain language. Use these terms exactly; if a term conflicts with this file, resolve it before writing code or docs.
3. [`requirements/roadmap.md`](requirements/roadmap.md) — candidate future work. Check this before proposing "what's next."
4. [`requirements/decision-log.md`](requirements/decision-log.md) — every real design fork, what was decided, and why. Check this before re-deciding something that may already be settled.
5. [`requirements/traceability.md`](requirements/traceability.md) — maps functional requirements to the Gherkin scenario that proves them. The user does not read code; this doc is their confidence mechanism.
6. [`requirements/ai-sdlc-observations.md`](requirements/ai-sdlc-observations.md) — a running log of how AI-assisted delivery has actually gone on this project: what worked, what needed correcting, real findings from live verification passes.
7. `architecture/vertical-slice-*.md` — one doc per shipped slice, in delivery order. Each records its own grilled design questions, not just the final shape.

## Process this project follows

- New work gets scoped as a vertical slice (`sdlc-delivery-vertical-slice-planning` skill) before implementation — thin, demoable, TDD'd.
- Real design forks (not mechanical defaults) get grilled explicitly before being decided — see the `productivity-grilling` skill and the pattern throughout `decision-log.md`.
- The project-local `requirements-traceability` skill (`.claude/skills/`) governs when and how `traceability.md` gets updated, including how to handle a claim that can't cleanly be proven at browser/Gherkin level.
- Shared, cross-project skills live in a separate repo at `~/.agents/skills` (not this repo) — see `SKILLS_INDEX.md` there.
- This project is architecturally independent of the sibling project `hive-sight` (HiveSight) — shared domain territory, separate codebases, separate databases. See the integration contract skill (`hivesight-advisor-integration-contract`) for the current cross-app API surface.

## Standing conventions

- Never read or print `services/advisor-api/.env` directly — check existence with `test -f`, edit with targeted operations, never full-file reads/dumps. All dev env vars (backend and frontend) live in this one file; `scripts/dev-servers.mjs` forwards specific keys to each process.
- Commit and push routine work (docs, roadmap/decision-log updates, already-directed code) without asking each time — still confirm before anything destructive or a PR action.
