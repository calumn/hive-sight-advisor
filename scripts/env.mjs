import { existsSync, readFileSync } from "node:fs";

export function loadAdvisorApiEnv(path = "services/advisor-api/.env") {
  if (!existsSync(path)) {
    return {};
  }

  const env = {};
  for (const rawLine of readFileSync(path, "utf8").split(/\r?\n/)) {
    const line = rawLine.trim();
    if (line.length === 0 || line.startsWith("#")) {
      continue;
    }
    const separatorIndex = line.indexOf("=");
    if (separatorIndex === -1) {
      continue;
    }
    env[line.slice(0, separatorIndex).trim()] = line.slice(separatorIndex + 1).trim();
  }
  return env;
}
