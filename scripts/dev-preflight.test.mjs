import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  databaseTargetFromEnv,
  renderDockerUnavailableMessage,
  renderPostgresStillUnreachableMessage
} from "./dev-preflight.mjs";

describe("dev server Postgres preflight", () => {
  it("uses the Advisor API's default dev database target when no URL is set", () => {
    assert.deepEqual(databaseTargetFromEnv({}), {
      host: "localhost",
      port: 5433
    });
  });

  it("reads the configured Advisor API database target", () => {
    assert.deepEqual(
      databaseTargetFromEnv({
        DATABASE_URL: "postgresql://hive_sight_advisor:hive_sight_advisor@127.0.0.1:15433/hive_sight_advisor_dev"
      }),
      {
        host: "127.0.0.1",
        port: 15433
      }
    );
  });

  it("tells the developer to start Docker Desktop when the daemon is unavailable", () => {
    const message = renderDockerUnavailableMessage({ target: { host: "localhost", port: 5433 } });

    assert.match(message, /Docker does not appear to be running/);
    assert.match(message, /Start Docker Desktop/);
    assert.match(message, /pnpm dev:all/);
  });

  it("tells the developer to check container logs when Postgres stays unreachable after Docker starts it", () => {
    const message = renderPostgresStillUnreachableMessage({ target: { host: "localhost", port: 5433 } });

    assert.match(message, /still isn't reachable/);
    assert.match(message, /docker compose logs postgres/);
  });
});
