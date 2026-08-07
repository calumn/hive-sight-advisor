import { spawn } from "node:child_process";
import { once } from "node:events";
import { networkInterfaces } from "node:os";
import { loadAdvisorApiEnv } from "./env.mjs";

const lanHost = localLanAddress();
const mode = process.argv[3] === "--lan" ? "lan" : "local";
const bindHost = mode === "lan" ? "0.0.0.0" : "127.0.0.1";
const browserHost = mode === "lan" ? lanHost : "127.0.0.1";
const advisorApiOrigin = `http://${browserHost}:8010`;
const webOrigin = `http://${browserHost}:5183`;

const services = [
  {
    name: "Advisor API",
    port: 8010,
    url: `${advisorApiOrigin}/health`,
    command: ".venv-advisor-api/bin/python",
    args: [
      "-m",
      "uvicorn",
      "hive_sight_advisor_api.main:app",
      "--app-dir",
      "services/advisor-api/src",
      "--reload",
      "--host",
      bindHost,
      "--port",
      "8010"
    ],
    cwd: ".",
    env: {
      ...loadAdvisorApiEnv(),
      ADVISOR_API_ALLOWED_ORIGINS: [
        "http://localhost:5183",
        "http://127.0.0.1:5183",
        webOrigin
      ].join(",")
    }
  },
  {
    name: "Web UI",
    port: 5183,
    url: webOrigin,
    command: "pnpm",
    args: ["--filter", "hive-sight-advisor-web", "dev", "--host", bindHost, "--port", "5183"],
    cwd: ".",
    env: {
      VITE_ADVISOR_API_URL: advisorApiOrigin,
      VITE_GOOGLE_CLIENT_ID: loadAdvisorApiEnv().ADVISOR_API_GOOGLE_CLIENT_ID ?? ""
    }
  }
];

const command = process.argv[2] ?? "status";

if (command === "status") {
  await printStatus();
} else if (command === "start") {
  await startServices();
} else if (command === "stop") {
  await stopServices();
} else {
  process.stderr.write(
    "Usage: pnpm dev:status | pnpm dev:all | pnpm dev:stop\n"
  );
  process.exitCode = 1;
}

async function printStatus() {
  const results = await Promise.all(services.map(checkService));
  for (const result of results) {
    process.stdout.write(`${result.up ? "up  " : "down"} ${result.name} ${result.url}\n`);
  }
}

async function startServices() {
  process.stdout.write("Starting HiveSight Advisor local servers. Press Ctrl+C to stop them.\n\n");
  if (mode === "lan") {
    process.stdout.write(`LAN Web UI: ${webOrigin}\n`);
    process.stdout.write(`LAN Advisor API: ${advisorApiOrigin}\n\n`);
  }
  const children = services.map(startService);

  const stop = () => {
    for (const child of children) {
      if (!child.killed) {
        child.kill("SIGTERM");
      }
    }
  };

  process.on("SIGINT", () => {
    stop();
    process.exit(130);
  });
  process.on("SIGTERM", () => {
    stop();
    process.exit(143);
  });

  await Promise.race(children.map((child) => once(child, "exit")));
  stop();
}

async function stopServices() {
  for (const service of services) {
    const pids = await pidsListeningOn(service.port);
    if (pids.length === 0) {
      process.stdout.write(`down ${service.name} ${service.url}\n`);
      continue;
    }

    let stoppedCount = 0;
    for (const pid of pids) {
      try {
        process.kill(Number(pid), "SIGTERM");
        stoppedCount += 1;
      } catch (error) {
        process.stderr.write(`[${service.name}] Could not stop process ${pid}: ${error.message}\n`);
      }
    }
    if (stoppedCount > 0) {
      process.stdout.write(`stopped ${service.name} on port ${service.port}\n`);
    } else {
      process.stdout.write(`blocked ${service.name} on port ${service.port}\n`);
    }
  }
}

function startService(service) {
  const child = spawn(service.command, service.args, {
    cwd: service.cwd,
    env: { ...process.env, ...service.env },
    stdio: ["ignore", "pipe", "pipe"]
  });

  child.stdout.on("data", (chunk) => writePrefixed(service.name, chunk));
  child.stderr.on("data", (chunk) => writePrefixed(service.name, chunk));
  child.on("error", (error) => {
    process.stderr.write(`[${service.name}] ${error.message}\n`);
  });
  return child;
}

function writePrefixed(name, chunk) {
  for (const line of chunk.toString().split(/\r?\n/)) {
    if (line.trim().length > 0) {
      process.stdout.write(`[${name}] ${line}\n`);
    }
  }
}

async function pidsListeningOn(port) {
  const child = spawn("lsof", ["-ti", `tcp:${port}`], {
    stdio: ["ignore", "pipe", "pipe"]
  });
  let output = "";
  child.stdout.on("data", (chunk) => {
    output += chunk.toString();
  });
  await once(child, "close");
  return output
    .split(/\s+/)
    .map((pid) => pid.trim())
    .filter(Boolean);
}

async function checkService(service) {
  try {
    const response = await fetch(service.url, { signal: AbortSignal.timeout(1500) });
    return { ...service, up: response.ok };
  } catch {
    return { ...service, up: false };
  }
}

function localLanAddress() {
  for (const addresses of Object.values(networkInterfaces())) {
    for (const address of addresses ?? []) {
      if (address.family === "IPv4" && !address.internal) {
        return address.address;
      }
    }
  }
  return "127.0.0.1";
}
