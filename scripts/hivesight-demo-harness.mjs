import { createServer } from "node:http";
import { readFileSync, existsSync } from "node:fs";
import { loadAdvisorApiEnv } from "./env.mjs";

const logPath = process.env.LOG_PATH ?? "/tmp/hsa-dev-servers.log";
const port = Number(process.env.DEMO_HARNESS_PORT ?? 4590);
const advisorApiEnv = loadAdvisorApiEnv();
const advisorApiUrl = process.env.ADVISOR_API_URL ?? "http://127.0.0.1:8010";
const serviceKey = advisorApiEnv.ADVISOR_API_HIVESIGHT_SERVICE_KEY ?? "";

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

async function proxyToAdvisorApi(path, body) {
  if (!serviceKey) {
    return {
      status: 500,
      body: {
        error:
          "No ADVISOR_API_HIVESIGHT_SERVICE_KEY configured in services/advisor-api/.env — the harness can't authenticate as HiveSight."
      }
    };
  }
  try {
    const response = await fetch(`${advisorApiUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "x-hivesight-service-key": serviceKey },
      body: JSON.stringify(body)
    });
    const payload = await response.json().catch(() => ({}));
    return { status: response.status, body: payload };
  } catch (error) {
    return { status: 502, body: { error: `Could not reach Advisor API at ${advisorApiUrl}: ${error.message}` } };
  }
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let data = "";
    req.on("data", (chunk) => {
      data += chunk;
    });
    req.on("end", () => {
      try {
        resolve(data ? JSON.parse(data) : {});
      } catch (error) {
        reject(error);
      }
    });
    req.on("error", reject);
  });
}

const server = createServer(async (req, res) => {
  if (req.url === "/events") {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(parseEvents()));
    return;
  }

  if (req.method === "POST" && req.url === "/simulate/request-plan") {
    const { hiveId, jurisdictionCode, situationalContext } = await readJsonBody(req);
    const result = await proxyToAdvisorApi("/integrations/hivesight/treatment-plans", {
      hive_id: hiveId,
      jurisdiction_code: jurisdictionCode,
      situational_context: situationalContext
    });
    res.writeHead(result.status, { "Content-Type": "application/json" });
    res.end(JSON.stringify(result.body));
    return;
  }

  if (req.method === "POST" && req.url === "/simulate/accept") {
    const { hiveId } = await readJsonBody(req);
    const result = await proxyToAdvisorApi("/integrations/hivesight/treatment-plans/completions", {
      hive_id: hiveId
    });
    res.writeHead(result.status, { "Content-Type": "application/json" });
    res.end(JSON.stringify(result.body));
    return;
  }

  if (req.method === "POST" && req.url === "/simulate/reject") {
    const { hiveId, reason } = await readJsonBody(req);
    const result = await proxyToAdvisorApi("/integrations/hivesight/treatment-plans/rejections", {
      hive_id: hiveId,
      reason
    });
    res.writeHead(result.status, { "Content-Type": "application/json" });
    res.end(JSON.stringify(result.body));
    return;
  }

  res.writeHead(200, { "Content-Type": "text/html" });
  res.end(HTML);
});

server.listen(port, "127.0.0.1", () => {
  process.stdout.write(`HiveSight demo harness running at http://127.0.0.1:${port}\n`);
  process.stdout.write(`Proxying to Advisor API at ${advisorApiUrl}\n`);
  if (!serviceKey) {
    process.stdout.write(
      "WARNING: no ADVISOR_API_HIVESIGHT_SERVICE_KEY found in services/advisor-api/.env — simulated requests will fail.\n"
    );
  }
});

const HTML = `<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>HiveSight Simulator — Agentic Treatment Plan Demo</title>
<style>
  :root {
    --bg: #0f1115;
    --panel: #171a21;
    --panel-2: #1c202a;
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
    display: grid;
    grid-template-columns: 420px 1fr;
    gap: 24px;
    align-items: start;
  }
  h1 { font-size: 18px; font-weight: 600; margin: 0 0 4px 0; grid-column: 1 / -1; }
  .subtitle { color: var(--muted); font-size: 13px; margin-bottom: 8px; grid-column: 1 / -1; }
  .panel {
    background: var(--panel);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 18px;
  }
  .panel h2 { font-size: 13px; text-transform: uppercase; letter-spacing: 0.04em; color: var(--muted); margin: 0 0 14px 0; }
  label { display: block; font-size: 12px; color: var(--muted); margin: 12px 0 4px; }
  label:first-of-type { margin-top: 0; }
  input, select, textarea {
    width: 100%;
    background: var(--panel-2);
    border: 1px solid var(--border);
    border-radius: 6px;
    color: var(--text);
    padding: 8px 10px;
    font-size: 13px;
    font-family: inherit;
  }
  textarea { min-height: 64px; resize: vertical; }
  button {
    border: none;
    border-radius: 6px;
    padding: 9px 14px;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    margin-top: 12px;
    width: 100%;
  }
  button:disabled { opacity: 0.4; cursor: not-allowed; }
  .btn-primary { background: var(--blue); color: white; }
  .btn-accept { background: var(--green); color: #0a1a12; }
  .btn-reject { background: var(--red); color: #260a0d; }
  .btn-secondary { background: var(--panel-2); color: var(--text); border: 1px solid var(--border); }
  .row-buttons { display: flex; gap: 8px; }
  .row-buttons button { margin-top: 0; }
  .step { border-top: 1px solid var(--border); margin-top: 16px; padding-top: 16px; }
  .step:first-of-type { border-top: none; margin-top: 0; padding-top: 0; }
  .step-title { font-size: 12px; font-weight: 700; color: var(--text); margin-bottom: 8px; }
  .result {
    margin-top: 12px;
    padding: 10px 12px;
    border-radius: 6px;
    background: var(--panel-2);
    font-size: 12px;
    line-height: 1.5;
    white-space: pre-wrap;
  }
  .result.grounded { border-left: 3px solid var(--green); }
  .result.ungrounded { border-left: 3px solid var(--red); }
  .result.partial { border-left: 3px solid var(--amber); }
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 999px;
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 6px;
  }
  .badge.grounded { background: rgba(63,201,137,0.15); color: var(--green); }
  .badge.ungrounded { background: rgba(224,89,107,0.15); color: var(--red); }
  .badge.partial { background: rgba(224,167,46,0.15); color: var(--amber); }
  .badge.status { background: rgba(79,139,245,0.15); color: var(--blue); }
  .badge.error { background: rgba(224,89,107,0.15); color: var(--red); }

  .hive-group { margin-bottom: 20px; border: 1px solid var(--border); border-radius: 10px; overflow: hidden; background: var(--panel); }
  .hive-header { padding: 10px 16px; font-size: 13px; font-weight: 600; color: var(--muted); border-bottom: 1px solid var(--border); display: flex; justify-content: space-between; }
  .hive-header .hive-id { color: var(--text); font-family: ui-monospace, monospace; }
  .timeline { padding: 14px 16px; }
  .event-row { display: flex; align-items: baseline; gap: 12px; padding: 7px 0; border-bottom: 1px dashed rgba(255,255,255,0.06); font-size: 13px; }
  .event-row:last-child { border-bottom: none; }
  .event-time { color: var(--muted); font-family: ui-monospace, monospace; font-size: 11px; width: 68px; flex-shrink: 0; }
  .event-badge { display: inline-block; padding: 2px 8px; border-radius: 999px; font-size: 11px; font-weight: 600; flex-shrink: 0; min-width: 150px; text-align: center; }
  .event-badge.recommend { background: rgba(163,116,232,0.15); color: var(--purple); }
  .event-badge.suggest { background: rgba(79,139,245,0.15); color: var(--blue); }
  .event-badge.suspended { background: rgba(224,167,46,0.15); color: var(--amber); }
  .event-badge.resumed { background: rgba(224,167,46,0.15); color: var(--amber); }
  .event-badge.completed, .event-badge.request { background: rgba(63,201,137,0.15); color: var(--green); }
  .event-badge.reject, .event-badge.no_pending, .event-badge.exhausted { background: rgba(224,89,107,0.15); color: var(--red); }
  .event-fields { color: var(--muted); font-family: ui-monospace, monospace; font-size: 12px; }
  .event-fields .k { color: #5b6270; }
  .event-duration { color: var(--green); font-weight: 600; }
  .empty { color: var(--muted); font-size: 13px; padding: 40px; text-align: center; }
</style>
</head>
<body>
  <h1>HiveSight Simulator — Agentic Treatment Plan Demo</h1>
  <div class="subtitle">Drives the real <code>/integrations/hivesight/*</code> endpoints, standing in for HiveSight, so you can walk the suggest &rarr; suspend &rarr; resume loop step by step and watch the trace on the right.</div>

  <div class="panel">
    <h2>Simulate HiveSight</h2>

    <div class="step">
      <div class="step-title">Hive context</div>
      <label>Hive ID</label>
      <div class="row-buttons">
        <input id="hiveId" readonly />
        <button class="btn-secondary" style="width:auto; white-space:nowrap;" onclick="newHive()">New hive</button>
      </div>
      <label>Jurisdiction</label>
      <select id="jurisdiction">
        <option value="uk">United Kingdom</option>
        <option value="us">United States</option>
      </select>
      <label>Situational context (from HiveSight's inspection data)</label>
      <textarea id="context">High mite count on the last inspection, autumn, colony nearly broodless.</textarea>
    </div>

    <div class="step">
      <div class="step-title">1. Request a treatment plan</div>
      <button class="btn-primary" onclick="requestPlan()" id="requestBtn">Send request &rarr; POST /treatment-plans</button>
      <div id="requestResult"></div>
    </div>

    <div class="step">
      <div class="step-title">2. Beekeeper's decision (HiveSight side)</div>
      <div class="row-buttons">
        <button class="btn-accept" onclick="accept()" id="acceptBtn" disabled>Accept</button>
        <button class="btn-reject" onclick="reject()" id="rejectBtn" disabled>Reject</button>
      </div>
      <label>Rejection reason (used if you click Reject)</label>
      <textarea id="reason">Conflicts with an active honey flow.</textarea>
      <div id="decisionResult"></div>
    </div>
  </div>

  <div>
    <div id="timeline"><div class="empty">Waiting for events&hellip;</div></div>
  </div>

<script>
function randomHiveId() {
  return "sim-hive-" + Math.random().toString(36).slice(2, 8);
}
function newHive() {
  document.getElementById("hiveId").value = randomHiveId();
  document.getElementById("acceptBtn").disabled = true;
  document.getElementById("rejectBtn").disabled = true;
  document.getElementById("requestResult").innerHTML = "";
  document.getElementById("decisionResult").innerHTML = "";
}
newHive();

function renderAnswer(container, payload, status) {
  if (payload.error) {
    container.innerHTML = '<div class="result"><span class="badge error">error</span><br>' + payload.error + '</div>';
    return;
  }
  if (payload.detail) {
    container.innerHTML = '<div class="result"><span class="badge error">error</span><br>' + JSON.stringify(payload.detail) + '</div>';
    return;
  }
  const grounding = payload.grounding_status ?? status ?? "";
  const citationCount = payload.citations ? payload.citations.length : 0;
  const revisionNote = payload.revision_exhausted ? "\\n\\n(Revision limit reached — no further suggestion recorded.)" : "";
  container.innerHTML =
    '<div class="result ' + grounding + '">' +
    '<span class="badge ' + grounding + '">' + grounding + '</span>' +
    (payload.status ? '<span class="badge status">' + payload.status + '</span>' : '') +
    '<br>' +
    (payload.text ? payload.text.slice(0, 500) + (payload.text.length > 500 ? '…' : '') : '') +
    (citationCount ? '\\n\\n' + citationCount + ' citation(s).' : '') +
    revisionNote +
    '</div>';
}

async function requestPlan() {
  const hiveId = document.getElementById("hiveId").value;
  const jurisdictionCode = document.getElementById("jurisdiction").value;
  const situationalContext = document.getElementById("context").value;
  const btn = document.getElementById("requestBtn");
  btn.disabled = true;
  const res = await fetch("/simulate/request-plan", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ hiveId, jurisdictionCode, situationalContext })
  });
  const payload = await res.json();
  renderAnswer(document.getElementById("requestResult"), payload);
  btn.disabled = false;
  if (payload.grounding_status === "grounded") {
    document.getElementById("acceptBtn").disabled = false;
    document.getElementById("rejectBtn").disabled = false;
  }
}

async function accept() {
  const hiveId = document.getElementById("hiveId").value;
  const res = await fetch("/simulate/accept", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ hiveId })
  });
  const payload = await res.json();
  renderAnswer(document.getElementById("decisionResult"), payload);
  document.getElementById("acceptBtn").disabled = true;
  document.getElementById("rejectBtn").disabled = true;
}

async function reject() {
  const hiveId = document.getElementById("hiveId").value;
  const reason = document.getElementById("reason").value;
  const res = await fetch("/simulate/reject", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ hiveId, reason })
  });
  const payload = await res.json();
  renderAnswer(document.getElementById("decisionResult"), payload);
  if (payload.revision_exhausted) {
    document.getElementById("acceptBtn").disabled = true;
    document.getElementById("rejectBtn").disabled = true;
  }
}

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

function renderTimeline(events) {
  const root = document.getElementById("timeline");
  if (events.length === 0) {
    root.innerHTML = '<div class="empty">Waiting for events&hellip; click "Send request" to see the trace.</div>';
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
        '<span class="k">' + k + '=</span>' + (k === "duration_ms" ? '<span class="event-duration">' + v + 'ms</span>' : v)
      ).join(" ");
      return '<div class="event-row">' +
        '<span class="event-time">' + time + '</span>' +
        '<span class="event-badge ' + badgeClass(e.event) + '">' + shortEvent + '</span>' +
        '<span class="event-fields">' + fieldsHtml + '</span>' +
        '</div>';
    }).join("");
    return '<div class="hive-group">' +
      '<div class="hive-header"><span>Hive</span><span class="hive-id">' + hiveId + '</span></div>' +
      '<div class="timeline">' + rowsHtml + '</div>' +
      '</div>';
  }).join("");
}

async function pollEvents() {
  try {
    const res = await fetch("/events");
    const events = await res.json();
    renderTimeline(events);
  } catch {}
}
pollEvents();
setInterval(pollEvents, 1000);
</script>
</body>
</html>`;
