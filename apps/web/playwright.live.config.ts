import { defineConfig, devices } from "@playwright/test";
import { defineBddConfig } from "playwright-bdd";

// Runs a small, hand-picked subset of the acceptance suite against the REAL Voyage/Anthropic
// APIs and the real dev database, instead of the stub providers the default `playwright.config.ts`
// uses. This is deliberately NOT part of the default CI/test-acceptance path: it costs real API
// calls, isn't fully deterministic (real LLM output varies), and reuses the dev database as-is
// rather than a clean isolated fixture. Run on demand when you want confidence that the real AI
// integration still behaves well, not just that the retrieval/citation/UI mechanics work.
//
// Requires: the dev Postgres running (`pnpm db:up`) and seeded (`pnpm db:seed`), and
// VOYAGE_API_KEY/ANTHROPIC_API_KEY set in the environment before running this config — it does
// not clear them the way playwright.config.ts does, so whatever is in the shell gets used.
const testDir = defineBddConfig({
  features: "tests/acceptance/features/*.feature",
  steps: "tests/acceptance/steps/*.ts"
});

export default defineConfig({
  testDir,
  fullyParallel: false,
  workers: 1,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report-live" }]],
  // Only the scenarios that meaningfully exercise real AI judgment: grounded citation (FR-001/
  // FR-002), no-grounding behaviour in both its partial and ungrounded forms (FR-008), and
  // treatment trade-off comparison (FR-004). Deliberately excludes scenarios whose behaviour is
  // mostly deterministic/mechanical regardless of provider (jurisdiction isolation, supersession
  // flagging, correction submission) — those are already fully proven by the stub-based suite.
  grep: /Grounded Query Answer With Seeded Corpus|No-Grounding Behaviour|Treatment Trade-Off Comparison/,
  use: {
    baseURL: "http://127.0.0.1:5203",
    screenshot: "only-on-failure",
    trace: "retain-on-failure",
    video: "retain-on-failure"
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] }
    }
  ],
  webServer: [
    {
      command:
        "../../.venv-advisor-api/bin/python -m uvicorn hive_sight_advisor_api.main:app --app-dir ../../services/advisor-api/src --host 127.0.0.1 --port 8030",
      env: {
        ADVISOR_API_ALLOWED_ORIGINS: "http://127.0.0.1:5203"
      },
      reuseExistingServer: false,
      timeout: 30_000,
      url: "http://127.0.0.1:8030/health"
    },
    {
      command: "pnpm dev --host 127.0.0.1 --port 5203",
      env: {
        VITE_ADVISOR_API_URL: "http://127.0.0.1:8030"
      },
      reuseExistingServer: false,
      timeout: 30_000,
      url: "http://127.0.0.1:5203"
    }
  ]
});
