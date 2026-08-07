import { defineConfig, devices } from "@playwright/test";
import { defineBddConfig } from "playwright-bdd";

const testDir = defineBddConfig({
  features: "tests/acceptance/features/**/*.feature",
  steps: "tests/acceptance/steps/*.ts"
});

export default defineConfig({
  testDir,
  fullyParallel: false,
  workers: 1,
  reporter: [["list"], ["html", { open: "never", outputFolder: "playwright-report" }]],
  globalSetup: "./tests/acceptance/global-setup.ts",
  use: {
    baseURL: "http://127.0.0.1:5193",
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
        "../../.venv-advisor-api/bin/python -m uvicorn hive_sight_advisor_api.main:app --app-dir ../../services/advisor-api/src --host 127.0.0.1 --port 8020",
      env: {
        DATABASE_URL:
          "postgresql://hive_sight_advisor:hive_sight_advisor@localhost:5433/hive_sight_advisor_test",
        VOYAGE_API_KEY: "",
        ANTHROPIC_API_KEY: "",
        ADVISOR_API_ALLOWED_ORIGINS: "http://127.0.0.1:5193",
        // The stub embedding provider's word-hash distances sit on a different scale
        // than real Voyage embeddings, so the acceptance suite needs its own
        // stub-calibrated thresholds. See requirements/decision-log.md, FR-008.
        ADVISOR_API_GROUNDED_DISTANCE_THRESHOLD: "0.5",
        ADVISOR_API_PARTIAL_DISTANCE_THRESHOLD: "0.8",
        // Deliberately high: the guest rate limiter is a process-wide singleton and
        // this webServer is shared, sequentially, across every scenario in the suite
        // (workers: 1) — the real 10/hour default would collide with unrelated
        // scenarios' own query traffic. See Slice 0013's Test Seams note on why the
        // rate-limit-exceeded behaviour is proven at the pytest/unit seams instead of
        // a Gherkin scenario.
        ADVISOR_API_GUEST_RATE_LIMIT: "1000"
      },
      reuseExistingServer: false,
      timeout: 30_000,
      url: "http://127.0.0.1:8020/health"
    },
    {
      command: "pnpm dev --host 127.0.0.1 --port 5193",
      env: {
        VITE_ADVISOR_API_URL: "http://127.0.0.1:8020"
      },
      reuseExistingServer: false,
      timeout: 30_000,
      url: "http://127.0.0.1:5193"
    }
  ]
});
