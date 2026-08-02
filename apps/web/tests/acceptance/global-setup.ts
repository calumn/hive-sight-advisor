import { execSync } from "node:child_process";

export default async function globalSetup(): Promise<void> {
  execSync("../../.venv-advisor-api/bin/python ../../scripts/seed_test_db.py", {
    stdio: "inherit"
  });
}
