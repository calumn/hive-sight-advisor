import { spawn } from "node:child_process";
import { loadAdvisorApiEnv } from "./env.mjs";

const [command, ...args] = process.argv.slice(2);
if (!command) {
  process.stderr.write("Usage: node scripts/run-with-env.mjs <command> [...args]\n");
  process.exit(1);
}

const child = spawn(command, args, {
  stdio: "inherit",
  env: { ...process.env, ...loadAdvisorApiEnv() }
});

child.on("exit", (code) => {
  process.exitCode = code ?? 1;
});
