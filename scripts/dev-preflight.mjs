import { spawn } from "node:child_process";
import { Socket } from "node:net";
import { once } from "node:events";

const defaultDatabaseUrl = "postgresql://hive_sight_advisor:hive_sight_advisor@localhost:5433/hive_sight_advisor_dev";

export async function ensurePostgresRunning({ env = process.env, log = (line) => process.stdout.write(line) } = {}) {
  const target = databaseTargetFromEnv(env);

  if (await canConnectToTcpPort(target)) {
    return true;
  }

  const dockerAvailable = await isDockerDaemonAvailable();
  if (!dockerAvailable) {
    process.stderr.write(renderDockerUnavailableMessage({ target }));
    return false;
  }

  log(`Postgres not reachable at ${target.host}:${target.port} — starting it via Docker (pnpm db:up)...\n`);
  await runDbUp();

  if (await waitForTcpPort(target)) {
    return true;
  }

  process.stderr.write(renderPostgresStillUnreachableMessage({ target }));
  return false;
}

export function databaseTargetFromEnv(env = process.env) {
  const databaseUrl = new URL(env.DATABASE_URL ?? defaultDatabaseUrl);
  return {
    host: databaseUrl.hostname,
    port: Number(databaseUrl.port || 5432)
  };
}

export function renderDockerUnavailableMessage({ target }) {
  const location = `${target.host}:${target.port}`;
  return [
    "",
    `HiveSight Advisor needs Postgres, but it cannot reach ${location} and Docker does not appear to be running.`,
    "Start Docker Desktop, then run: pnpm dev:all",
    ""
  ].join("\n") + "\n";
}

export function renderPostgresStillUnreachableMessage({ target }) {
  const location = `${target.host}:${target.port}`;
  return [
    "",
    `Docker is running, but Postgres still isn't reachable at ${location} after starting the container.`,
    "Check its logs with: docker compose logs postgres",
    ""
  ].join("\n") + "\n";
}

async function runDbUp() {
  const child = spawn("docker", ["compose", "up", "-d", "postgres"], {
    stdio: ["ignore", "pipe", "pipe"]
  });
  await once(child, "close");
}

async function canConnectToTcpPort({ host, port }) {
  const socket = new Socket();
  socket.setTimeout(1000);

  try {
    await new Promise((resolve, reject) => {
      socket.once("connect", resolve);
      socket.once("timeout", () => reject(new Error("Connection timed out")));
      socket.once("error", reject);
      socket.connect(port, host);
    });
    return true;
  } catch {
    return false;
  } finally {
    socket.destroy();
  }
}

async function waitForTcpPort(target, { attempts = 20, delayMs = 500 } = {}) {
  for (let attempt = 0; attempt < attempts; attempt += 1) {
    if (await canConnectToTcpPort(target)) {
      return true;
    }
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
  return false;
}

async function isDockerDaemonAvailable() {
  try {
    const child = spawn("docker", ["info"], {
      stdio: ["ignore", "ignore", "ignore"]
    });
    const [code] = await once(child, "close");
    return code === 0;
  } catch {
    return false;
  }
}
