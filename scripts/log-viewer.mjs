import { createServer } from "node:http";
import { readFileSync, existsSync } from "node:fs";

const logPath = process.env.LOG_PATH ?? "/tmp/hsa-dev-servers.log";
const port = Number(process.env.LOG_VIEWER_PORT ?? 4590);

const EVENT_LINE = /^\[Advisor API\] (\S+ \S+),\d+ (\w+) (\S+) (treatment_plan\.\S+) (.*)$/;

function parseEvents() {
  if (!existsSync(logPath)) {
    return [];
  }
  const lines = readFileSync(logPath, "utf8").split("\n");
  const events = [];
  for (const line of lines) {
    const match = line.match(EVENT_LINE);
    if (!match) continue;
    const [, timestamp, level, logger, event, rest] = match;
    const fields = {};
    for (const pair of rest.trim().split(/\s+/)) {
      const separatorIndex = pair.indexOf("=");
      if (separatorIndex === -1) continue;
      fields[pair.slice(0, separatorIndex)] = pair.slice(separatorIndex + 1);
    }
    events.push({ timestamp, level, logger, event, fields });
  }
  return events;
}

const server = createServer((req, res) => {
  if (req.url === "/events") {
    res.writeHead(200, { "Content-Type": "application/json", "Access-Control-Allow-Origin": "*" });
    res.end(JSON.stringify(parseEvents()));
    return;
  }
  res.writeHead(200, { "Content-Type": "text/html" });
  res.end(HTML);
});

server.listen(port, "127.0.0.1", () => {
  process.stdout.write(`Log viewer running at http://127.0.0.1:${port}\n`);
  process.stdout.write(`Watching: ${logPath}\n`);
});

const HTML = `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Treatment Plan Workflow — Event Timeline</title>
<style>
  :root {
    --bg: #0f1115;
    --panel: #171a21;
    --border: #2a2f3a;
    --text: #e6e9ef;
    --muted: #8b93a3;
    --amber: #e0a72e;
    --blue: #4d8bf5;
    --green: #3fc989;
    --purple: #a374e8;
    --red: #e0596b;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    background: var(--bg);
    color: var(--text);
    padding: 24px;
  }
  h1 {
    font-size: 18px;
    font-weight: 600;
    margin: 0 0 4px 0;
  }
  .subtitle {
    color: var(--muted);
    font-size: 13px;
    margin-bottom: 20px;
  }
  .hive-group {
    margin-bottom: 28px;
    border: 1px solid var(--border);
    border-radius: 10px;
    overflow: hidden;
    background: var(--panel);
  }
  .hive-header {
    padding: 10px 16px;
    font-size: 13px;
    font-weight: 600;
    color: var(--muted);
    border-bottom: 1px solid var(--border);
    display: flex;
    justify-content: space-between;
  }
  .hive-header .hive-id { color: var(--text); font-family: ui-monospace, monospace; }
  .timeline { padding: 14px 16px; }
  .row {
    display: flex;
    align-items: baseline;
    gap: 12px;
    padding: 7px 0;
    border-bottom: 1px dashed rgba(255,255,255,0.06);
    font-size: 13px;
  }
  .row:last-child { border-bottom: none; }
  .time { color: var(--muted); font-family: ui-monospace, monospace; font-size: 11px; width: 68px; flex-shrink: 0; }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    flex-shrink: 0;
    min-width: 150px;
    text-align: center;
  }
  .badge.recommend { background: rgba(163,116,232,0.15); color: var(--purple); }
  .badge.suggest { background: rgba(79,139,245,0.15); color: var(--blue); }
  .badge.suspended { background: rgba(224,167,46,0.15); color: var(--amber); }
  .badge.resumed { background: rgba(224,167,46,0.15); color: var(--amber); }
  .badge.completed, .badge.request { background: rgba(63,201,137,0.15); color: var(--green); }
  .badge.reject, .badge.no_pending, .badge.exhausted { background: rgba(224,89,107,0.15); color: var(--red); }
  .fields { color: var(--muted); font-family: ui-monospace, monospace; font-size: 12px; }
  .fields .k { color: #5b6270; }
  .duration { color: var(--green); font-weight: 600; }
  .empty { color: var(--muted); font-size: 13px; padding: 40px; text-align: center; }
</style>
</head>
<body>
  <h1>Treatment Plan Workflow — Event Timeline</h1>
  <div class="subtitle">Live view of <code>treatment_plan.*</code> structured logs, grouped by hive. Polls every second.</div>
  <div id="root"><div class="empty">Waiting for events…</div></div>
<script>
function badgeClass(event) {
  if (event.includes("suspended")) return "suspended";
  if (event.includes("resumed")) return "resumed";
  if (event.includes("recommend")) return "recommend";
  if (event.includes("suggest")) return "suggest";
  if (event.includes("reject")) return "reject";
  if (event.includes("no_pending")) return "no_pending";
  if (event.includes("exhausted")) return "exhausted";
  if (event.includes("completed") || event.includes("request")) return "completed";
  return "";
}

function render(events) {
  const root = document.getElementById("root");
  if (events.length === 0) {
    root.innerHTML = '<div class="empty">Waiting for events… ask a treatment plan question to see the trace.</div>';
    return;
  }
  const byHive = {};
  for (const e of events) {
    const hiveId = e.fields.hive_id ?? "unknown";
    (byHive[hiveId] ??= []).push(e);
  }
  const hiveIds = Object.keys(byHive).reverse();
  root.innerHTML = hiveIds.map((hiveId) => {
    const rows = byHive[hiveId];
    const rowsHtml = rows.map((e) => {
      const shortEvent = e.event.replace("treatment_plan.", "");
      const time = e.timestamp.split(" ")[1] ?? e.timestamp;
      const otherFields = Object.entries(e.fields).filter(([k]) => k !== "hive_id" && k !== "thread_id");
      const fieldsHtml = otherFields.map(([k, v]) =>
        '<span class="k">' + k + '=</span>' + (k === "duration_ms" ? '<span class="duration">' + v + 'ms</span>' : v)
      ).join(" ");
      return '<div class="row">' +
        '<span class="time">' + time + '</span>' +
        '<span class="badge ' + badgeClass(e.event) + '">' + shortEvent + '</span>' +
        '<span class="fields">' + fieldsHtml + '</span>' +
        '</div>';
    }).join("");
    return '<div class="hive-group">' +
      '<div class="hive-header"><span>Hive</span><span class="hive-id">' + hiveId + '</span></div>' +
      '<div class="timeline">' + rowsHtml + '</div>' +
      '</div>';
  }).join("");
}

async function poll() {
  try {
    const res = await fetch("/events");
    const events = await res.json();
    render(events);
  } catch {}
}
poll();
setInterval(poll, 1000);
</script>
</body>
</html>`;
