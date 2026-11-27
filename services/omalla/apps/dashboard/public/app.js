/* Omalla local console — vanilla ES module, no build step. */
const state = {
  token: localStorage.getItem("omalla.key") ?? "",
  me: null,
  view: "overview",
  route: [],
  cache: { calls: [], workflows: [], templates: [], metrics: {}, tasks: [], bookings: [], escalations: [], credentials: [], agents: [], numbers: [], sms: [], providers: [] },
  socket: null,
  refreshTimer: null,
};

const $ = (sel, root = document) => root.querySelector(sel);

function el(tag, props = {}, ...children) {
  const node = document.createElement(tag);
  for (const [key, value] of Object.entries(props)) {
    if (value === undefined || value === null) continue;
    if (key === "class") node.className = value;
    else if (key === "text") node.textContent = value;
    else if (key === "html") node.innerHTML = value;
    else if (key.startsWith("on") && typeof value === "function") node.addEventListener(key.slice(2), value);
    else if (key === "dataset") Object.assign(node.dataset, value);
    else if (key in node) node[key] = value;
    else node.setAttribute(key, value);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

function toast(message, bad = false) {
  const node = el("div", { class: `toast${bad ? " bad" : ""}`, text: message });
  $("#toasts").append(node);
  setTimeout(() => node.remove(), 4200);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: {
      ...(options.body ? { "content-type": "application/json" } : {}),
      ...(state.token ? { authorization: `Bearer ${state.token}` } : {}),
      ...(options.headers ?? {}),
    },
  });
  if (response.status === 204) return null;
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload?.error?.message ?? `request failed (${response.status})`;
    const error = new Error(message);
    error.status = response.status;
    if (response.status === 401) showLogin("Your API key was rejected.");
    throw error;
  }
  return payload;
}

/* ------------------------------------------------------------------ */
/* formatting                                                          */
/* ------------------------------------------------------------------ */

const fmtTime = (iso) => (iso ? new Date(iso).toLocaleString(undefined, { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" }) : "—");
const fmtMs = (ms) => (ms ? `${ms} ms` : "—");
const shortId = (id) => (id ? String(id).split("_")[1]?.slice(0, 8) ?? id : "—");

function duration(call) {
  if (!call.endedAt || !call.startedAt) return call.status === "in_progress" ? "live" : "—";
  const seconds = Math.max(0, Math.round((Date.parse(call.endedAt) - Date.parse(call.startedAt)) / 1000));
  return `${Math.floor(seconds / 60)}:${String(seconds % 60).padStart(2, "0")}`;
}

function statusBadge(status) {
  const map = {
    ended: ["good", "ended"],
    in_progress: ["live", "live"],
    ringing: ["warn", "ringing"],
    failed: ["bad", "failed"],
    active: ["good", "active"],
    draft: ["", "draft"],
    archived: ["", "archived"],
    succeeded: ["good", "succeeded"],
    running: ["live", "running"],
    skipped: ["warn", "skipped"],
    open: ["warn", "open"],
    acknowledged: ["", "acknowledged"],
    closed: ["good", "closed"],
    queued: ["warn", "queued"],
    sent: ["good", "sent"],
    delivered: ["good", "delivered"],
    received: ["good", "received"],
    undelivered: ["bad", "undelivered"],
    released: ["", "released"],
    provisioning: ["warn", "provisioning"],
  };
  const [tone, label] = map[status] ?? ["", status];
  return el("span", { class: `badge ${tone}`, text: label ?? "—" });
}

/* ------------------------------------------------------------------ */
/* auth                                                                */
/* ------------------------------------------------------------------ */

function showLogin(message) {
  $("#shell").hidden = true;
  $("#boot").hidden = true;
  $("#login").hidden = false;
  if (message) {
    const node = $("#login-error");
    node.textContent = message;
    node.hidden = false;
  }
  $("#login-key").focus();
}

async function boot() {
  if (!state.token) return showLogin();
  try {
    state.me = await api("/v1/me");
  } catch {
    return showLogin();
  }
  $("#boot").hidden = true;
  $("#login").hidden = true;
  $("#shell").hidden = false;
  $("#tenant-name").textContent = state.me.tenant?.name ?? "Workspace";
  route();
}

$("#login-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const key = $("#login-key").value.trim();
  if (!key) return;
  state.token = key;
  try {
    state.me = await api("/v1/me");
    localStorage.setItem("omalla.key", key);
    $("#boot").hidden = true;
    $("#login").hidden = true;
    $("#shell").hidden = false;
    $("#tenant-name").textContent = state.me.tenant?.name ?? "Workspace";
    route();
  } catch (error) {
    showLogin(error.message);
  }
});

/* ------------------------------------------------------------------ */
/* routing                                                             */
/* ------------------------------------------------------------------ */

const VIEWS = {
  overview: renderOverview,
  calls: renderCalls,
  workflows: renderWorkflows,
  automations: renderAutomations,
  telephony: renderTelephony,
  settings: renderSettings,
};

function route() {
  const hash = location.hash.replace(/^#\/?/, "");
  const parts = hash.split("/").filter(Boolean);
  state.view = VIEWS[parts[0]] ? parts[0] : "overview";
  state.route = parts.slice(1);
  document.querySelectorAll(".nav-item").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === state.view);
  });
  clearInterval(state.refreshTimer);
  closeSocket();
  $("#main").replaceChildren();
  VIEWS[state.view]();
}

window.addEventListener("hashchange", route);
$("#nav").addEventListener("click", (event) => {
  const button = event.target.closest(".nav-item");
  if (!button) return;
  location.hash = `#/${button.dataset.view}`;
});

function closeSocket() {
  if (state.socket) {
    try { state.socket.close(); } catch { /* ignore */ }
    state.socket = null;
  }
}

/* ------------------------------------------------------------------ */
/* overview                                                            */
/* ------------------------------------------------------------------ */

async function renderOverview() {
  const main = $("#main");
  main.append(el("div", { class: "page-head" },
    el("div", {}, el("h1", { text: "Overview" }), el("p", { class: "sub", text: "Everything here runs on this machine. Calls are simulated; no carrier is contacted." })),
    el("button", { class: "primary", text: "Simulate a call", onclick: () => { location.hash = "#/calls"; } }),
  ));

  const [metrics, calls, workflows] = await Promise.all([
    api("/v1/metrics"),
    api("/v1/calls?limit=8"),
    api("/v1/workflows"),
  ]);
  state.cache.metrics = metrics;
  state.cache.calls = calls;

  const cards = [
    ["Calls", metrics.calls, `${metrics.callsToday} in 24h`],
    ["Answer latency", metrics.avgTurnLatencyMs || "—", "ms to first audio"],
    ["Workflow runs", metrics.workflowRuns, `${metrics.workflowFailures} failed`],
    ["Bookings", metrics.bookings, `${metrics.openTasks} open tasks`],
  ];
  main.append(el("div", { class: "grid cols-4" },
    cards.map(([label, value, note]) =>
      el("div", { class: "card metric" },
        el("div", { class: "label", text: label }),
        el("div", { class: "value", text: String(value) }),
        el("div", { class: "muted small", text: note }),
      )),
  ));

  const recent = el("div", { class: "card panel" });
  recent.append(el("div", { class: "panel-head" }, el("h2", { text: "Recent calls" }), el("button", { class: "ghost", text: "All calls", onclick: () => { location.hash = "#/calls"; } })));
  if (calls.length === 0) {
    recent.append(el("div", { class: "empty", text: "No calls yet. Start one from the Calls page — it takes one click and costs nothing." }));
  } else {
    const table = el("table");
    table.append(el("thead", {}, el("tr", {},
      el("th", { text: "Started" }), el("th", { text: "From" }), el("th", { text: "Status" }), el("th", { text: "Turns" }), el("th", { text: "Length" }),
    )));
    const body = el("tbody");
    for (const call of calls) {
      body.append(el("tr", { class: "clickable", onclick: () => { location.hash = `#/calls/${call.id}`; } },
        el("td", { text: fmtTime(call.startedAt) }),
        el("td", { class: "mono", text: call.from }),
        el("td", {}, statusBadge(call.status)),
        el("td", { text: String(call.metrics?.turnCount ?? 0) }),
        el("td", { class: "mono", text: duration(call) }),
      ));
    }
    table.append(body);
    recent.append(table);
  }

  const automation = el("div", { class: "card panel" });
  automation.append(el("div", { class: "panel-head" }, el("h2", { text: "Automation" }), el("span", { class: "muted small", text: `${workflows.filter((w) => w.status === "active").length} active flows` })));
  const list = el("div", { class: "list" });
  if (workflows.length === 0) {
    list.append(el("div", { class: "empty", text: "No workflows yet. Install one from the template gallery." }));
  }
  for (const workflow of workflows.slice(0, 5)) {
    list.append(el("div", { class: "list-item" },
      el("div", { class: "grow" },
        el("div", { text: workflow.name }),
        el("div", { class: "muted small", text: `${workflow.trigger.type} · v${workflow.version}` }),
      ),
      statusBadge(workflow.status),
    ));
  }
  automation.append(list);

  main.append(el("div", { class: "grid cols-2" }, recent, automation));
  main.append(el("div", { class: "card panel" },
    el("div", { class: "panel-head" }, el("h2", { text: "Simulation boundary" })),
    el("div", { class: "panel-body stack" },
      el("p", { class: "muted", text: "Omalla never dials a real phone number in this build. Inbound and outbound calls run through an in-process carrier simulator, so tests are deterministic and free. Connecting a real SIP trunk is a deployment decision that requires a provider and a reviewed security configuration." }),
      el("p", { class: "muted", text: "Local speech uses Windows SAPI where available; otherwise the voice provider returns silence and the transcript carries the conversation." }),
    ),
  ));

  state.refreshTimer = setInterval(() => {
    if (state.view === "overview") route();
  }, 15000);
}

/* ------------------------------------------------------------------ */
/* calls                                                               */
/* ------------------------------------------------------------------ */

async function renderCalls() {
  const main = $("#main");
  const callId = state.route[0];
  if (callId) return renderCallDetail(callId);

  main.append(el("div", { class: "page-head" },
    el("div", {}, el("h1", { text: "Calls" }), el("p", { class: "sub", text: "Simulated inbound and outbound conversations, with live transcripts." })),
    el("button", { class: "primary", text: "New simulated call", onclick: openNewCall }),
  ));

  const calls = await api("/v1/calls?limit=100");
  state.cache.calls = calls;

  const panel = el("div", { class: "card panel" });
  if (calls.length === 0) {
    panel.append(el("div", { class: "empty", text: "No calls yet." }));
  } else {
    const table = el("table");
    table.append(el("thead", {}, el("tr", {},
      el("th", { text: "Started" }), el("th", { text: "Direction" }), el("th", { text: "From" }), el("th", { text: "To" }), el("th", { text: "Status" }), el("th", { text: "Turns" }), el("th", { text: "Length" }), el("th", { text: "Ended because" }),
    )));
    const body = el("tbody");
    for (const call of calls) {
      body.append(el("tr", { class: "clickable", onclick: () => { location.hash = `#/calls/${call.id}`; } },
        el("td", { text: fmtTime(call.startedAt) }),
        el("td", {}, el("span", { class: "badge", text: call.direction })),
        el("td", { class: "mono", text: call.from }),
        el("td", { class: "mono", text: call.to }),
        el("td", {}, statusBadge(call.status)),
        el("td", { text: String(call.metrics?.turnCount ?? 0) }),
        el("td", { class: "mono", text: duration(call) }),
        el("td", { class: "muted", text: call.endedReason ?? "—" }),
      ));
    }
    table.append(body);
    panel.append(table);
  }
  main.append(panel);
  main.append(el("p", { class: "hint", text: "All calls use the simulated carrier. The agent's tools write to this workspace's local task, booking and contact stores." }));
}

function openNewCall() {
  const dialog = el("dialog");
  const form = el("form", { class: "dialog-body" });
  const to = el("input", { value: "+15550001234" });
  const from = el("input", { value: "+15550112233" });
  const say = el("textarea", { placeholder: "One caller utterance per line, e.g.\nI'd like to book an appointment\nMy name is Sam Rivera\nTomorrow at 3pm\nYes please" });
  const press = el("input", { placeholder: "Optional DTMF keys, e.g. 1" });

  form.append(
    el("div", { class: "form-grid" },
      el("label", { class: "field" }, el("span", { text: "Business number" }), to),
      el("label", { class: "field" }, el("span", { text: "Caller number" }), from),
    ),
    el("label", { class: "field" }, el("span", { text: "Caller utterances" }), say),
    el("label", { class: "field" }, el("span", { text: "DTMF (before speech)" }), press),
    el("p", { class: "hint", text: "The call runs immediately; you can keep talking from the call screen." }),
  );
  const actions = el("div", { class: "row" }, el("div", { class: "spacer" }));
  const submit = el("button", { class: "primary", type: "submit", text: "Start call" });
  const cancel = el("button", { type: "button", text: "Cancel", onclick: () => dialog.close() });
  actions.append(cancel, submit);
  form.append(actions);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    submit.disabled = true;
    try {
      const call = await api("/v1/calls", {
        method: "POST",
        body: JSON.stringify({
          to: to.value.trim(),
          from: from.value.trim(),
          say: say.value.split("\n").map((line) => line.trim()).filter(Boolean),
          press: press.value.trim() ? [press.value.trim()] : [],
        }),
      });
      dialog.close();
      location.hash = `#/calls/${call.id}`;
    } catch (error) {
      toast(error.message, true);
      submit.disabled = false;
    }
  });

  dialog.append(el("div", { class: "dialog-head" }, el("h2", { text: "Simulated inbound call" }), el("button", { class: "ghost", text: "Close", onclick: () => dialog.close() })), form);
  document.body.append(dialog);
  dialog.addEventListener("close", () => dialog.remove());
  dialog.showModal();
}

async function renderCallDetail(callId) {
  const main = $("#main");
  const call = await api(`/v1/calls/${callId}`);
  const live = call.status === "in_progress" || call.status === "ringing";

  main.append(el("div", { class: "page-head" },
    el("div", {},
      el("button", { class: "ghost", text: "← All calls", onclick: () => { location.hash = "#/calls"; } }),
      el("h1", { text: live ? "Live call" : "Call detail", style: "margin-top:8px" }),
      el("p", { class: "sub mono", text: `${call.from} → ${call.to} · ${call.id}` }),
    ),
    el("div", { class: "row" }, statusBadge(call.status), el("span", { class: "muted small", text: duration(call) })),
  ));

  const transcriptCard = el("div", { class: "card panel" });
  const transcriptHead = el("div", { class: "panel-head" },
    el("h2", { text: "Transcript" }),
    el("span", { class: "muted small", id: "live-dot", text: live ? "listening" : "complete" }),
  );
  const transcript = el("div", { class: "transcript", id: "transcript" });
  transcriptCard.append(transcriptHead, transcript);
  renderTranscript(transcript, call);

  const controls = el("div", { class: "card panel" });
  controls.append(el("div", { class: "panel-head" }, el("h2", { text: "Call controls" })));
  const controlsBody = el("div", { class: "panel-body stack" });
  const input = el("input", { placeholder: "Speak as the caller…", disabled: !live });
  const send = el("button", { class: "primary", text: "Say", disabled: !live, onclick: async () => {
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    send.disabled = true;
    try {
      const updated = await api(`/v1/calls/${call.id}/say`, { method: "POST", body: JSON.stringify({ text }) });
      renderTranscript(transcript, updated);
    } catch (error) { toast(error.message, true); }
    send.disabled = !live;
  }});
  input.addEventListener("keydown", (event) => { if (event.key === "Enter") send.click(); });

  const hangup = el("button", { class: "danger", text: "Hang up", disabled: !live, onclick: async () => {
    try {
      const updated = await api(`/v1/calls/${call.id}/hangup`, { method: "POST" });
      renderTranscript(transcript, updated);
      toast("Call ended.");
      route();
    } catch (error) { toast(error.message, true); }
  }});

  const keypad = el("div", { class: "row" });
  for (const key of ["1", "2", "3", "4", "5", "6", "7", "8", "9", "*", "0", "#"]) {
    keypad.append(el("button", { class: "mono", text: key, disabled: !live, onclick: async () => {
      try {
        const updated = await api(`/v1/calls/${call.id}/dtmf`, { method: "POST", body: JSON.stringify({ digits: key }) });
        renderTranscript(transcript, updated);
      } catch (error) { toast(error.message, true); }
    }}));
  }

  controlsBody.append(el("div", { class: "row" }, el("div", { style: "flex:1" }, input), send, hangup), el("div", { class: "muted small", text: "DTMF (IVR menus only):" }), keypad);
  controls.append(controlsBody);

  const side = el("div", { class: "stack" });
  side.append(controls);
  side.append(el("div", { class: "card panel" },
    el("div", { class: "panel-head" }, el("h2", { text: "Signals" })),
    el("div", { class: "panel-body stack" },
      signalRow("Turns", String(call.metrics?.turnCount ?? 0)),
      signalRow("Tool calls", String(call.metrics?.toolCalls ?? 0)),
      signalRow("Interruptions", String(call.metrics?.interruptions ?? 0)),
      signalRow("Avg latency", fmtMs(call.metrics?.turnLatenciesMs?.length ? Math.round(call.metrics.turnLatenciesMs.reduce((a, b) => a + b, 0) / call.metrics.turnLatenciesMs.length) : 0)),
      signalRow("Ended because", call.endedReason ?? "—"),
    ),
  ));

  main.append(el("div", { class: "grid", style: "grid-template-columns: minmax(0,1.6fr) minmax(280px,0.9fr)" }, transcriptCard, side));

  if (live) connectCallSocket(call.id, transcript);
}

function signalRow(label, value) {
  return el("div", { class: "row" },
    el("span", { class: "muted small", text: label }),
    el("div", { class: "spacer" }),
    el("span", { class: "mono", text: value }),
  );
}

function renderTranscript(container, call) {
  container.replaceChildren();
  if (!call.transcript || call.transcript.length === 0) {
    container.append(el("div", { class: "empty", text: "Waiting for the first turn…" }));
    return;
  }
  for (const turn of call.transcript) {
    const assistant = turn.role !== "caller";
    container.append(el("div", { class: `turn ${assistant ? "assistant" : "caller"}` },
      el("div", { class: "who", text: assistant ? "assistant" : "caller" }),
      el("div", { class: "text", text: turn.text }),
      el("div", { class: "meta", text: `${Math.round((turn.offsetMs ?? 0) / 1000)}s${turn.latencyMs ? ` · ${turn.latencyMs} ms` : ""}${turn.interrupted ? " · interrupted" : ""}` }),
    ));
  }
  container.scrollTop = container.scrollHeight;
}

function connectCallSocket(callId, transcript) {
  closeSocket();
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const socket = new WebSocket(`${protocol}//${location.host}/v1/calls/${callId}/stream?token=${encodeURIComponent(state.token)}`);
  state.socket = socket;

  socket.addEventListener("message", (message) => {
    let event;
    try { event = JSON.parse(message.data); } catch { return; }
    if (event.type === "snapshot") {
      renderTranscript(transcript, event.call);
      return;
    }
    if (event.type === "caller.transcript" || event.type === "assistant.speech") {
      const call = { transcript: [] };
      const existing = transcript.dataset.transcript ? JSON.parse(transcript.dataset.transcript) : [];
      const turn = {
        role: event.type === "caller.transcript" ? "caller" : "assistant",
        text: event.data.text,
        offsetMs: 0,
      };
      call.transcript = [...existing, turn];
      transcript.dataset.transcript = JSON.stringify(call.transcript);
      renderTranscript(transcript, call);
      const dot = $("#live-dot");
      if (dot) dot.classList.toggle("speaking", event.type === "assistant.speech");
    }
    if (event.type === "call.ended") {
      const dot = $("#live-dot");
      if (dot) { dot.textContent = "complete"; dot.classList.remove("speaking"); }
      toast("Call ended.");
      setTimeout(() => { if (location.hash.startsWith("#/calls/")) route(); }, 700);
    }
  });

  socket.addEventListener("close", () => {
    const dot = $("#live-dot");
    if (dot) { dot.textContent = "disconnected"; dot.classList.remove("speaking"); }
  });
}

/* ------------------------------------------------------------------ */
/* workflows                                                           */
/* ------------------------------------------------------------------ */

async function renderWorkflows() {
  const main = $("#main");
  const runId = state.route[0];
  if (runId) return renderRunDetail(runId);

  main.append(el("div", { class: "page-head" },
    el("div", {}, el("h1", { text: "Workflows" }), el("p", { class: "sub", text: "Native automation, n8n-compatible import and export, and post-call flows." })),
    el("button", { class: "primary", text: "Install template", onclick: openTemplates }),
  ));

  const [workflows, runs, templates] = await Promise.all([
    api("/v1/workflows"),
    api("/v1/runs"),
    api("/v1/templates"),
  ]);
  state.cache.workflows = workflows;
  state.cache.templates = templates;

  const panel = el("div", { class: "card panel" });
  panel.append(el("div", { class: "panel-head" }, el("h2", { text: "Flows" }), el("span", { class: "muted small", text: `${workflows.length} installed` })));
  if (workflows.length === 0) {
    panel.append(el("div", { class: "empty", text: "Install a template to get a working automation in one click." }));
  } else {
    const table = el("table");
    table.append(el("thead", {}, el("tr", {},
      el("th", { text: "Name" }), el("th", { text: "Trigger" }), el("th", { text: "Status" }), el("th", { text: "Version" }), el("th", { text: "Updated" }), el("th", { text: "" }),
    )));
    const body = el("tbody");
    for (const workflow of workflows) {
      const toggle = el("button", { class: "ghost", text: workflow.status === "active" ? "Pause" : "Activate", onclick: async (event) => {
        event.stopPropagation();
        try {
          await api(`/v1/workflows/${workflow.id}`, { method: "PATCH", body: JSON.stringify({ status: workflow.status === "active" ? "draft" : "active" }) });
          route();
        } catch (error) { toast(error.message, true); }
      }});
      const runButton = el("button", { text: "Run", onclick: (event) => { event.stopPropagation(); openRun(workflow); } });
      body.append(el("tr", {},
        el("td", { text: workflow.name }),
        el("td", {}, el("span", { class: "badge", text: workflow.trigger.type })),
        el("td", {}, statusBadge(workflow.status)),
        el("td", { class: "mono", text: `v${workflow.version}` }),
        el("td", { class: "muted", text: fmtTime(workflow.updatedAt) }),
        el("td", {}, el("div", { class: "row" }, toggle, runButton)),
      ));
    }
    table.append(body);
    panel.append(table);
  }
  main.append(panel);

  const runsPanel = el("div", { class: "card panel", style: "margin-top:14px" });
  runsPanel.append(el("div", { class: "panel-head" }, el("h2", { text: "Recent runs" }), el("span", { class: "muted small", text: "newest first" })));
  if (runs.length === 0) {
    runsPanel.append(el("div", { class: "empty", text: "No runs yet. Run a flow or finish a call that has a post-call workflow." }));
  } else {
    const table = el("table");
    table.append(el("thead", {}, el("tr", {}, el("th", { text: "Started" }), el("th", { text: "Workflow" }), el("th", { text: "Status" }), el("th", { text: "Steps" }), el("th", { text: "Error" }))));
    const body = el("tbody");
    for (const run of runs.slice(0, 20)) {
      const workflow = state.cache.workflows.find((candidate) => candidate.id === run.workflowId);
      body.append(el("tr", { class: "clickable", onclick: () => { location.hash = `#/workflows/${run.id}`; } },
        el("td", { text: fmtTime(run.startedAt) }),
        el("td", { text: workflow?.name ?? shortId(run.workflowId) }),
        el("td", {}, statusBadge(run.status)),
        el("td", { text: String(run.steps.length) }),
        el("td", { class: "muted truncate", text: run.error ?? "—" }),
      ));
    }
    table.append(body);
    runsPanel.append(table);
  }
  main.append(runsPanel);
}

function openTemplates() {
  const dialog = el("dialog");
  const body = el("div", { class: "dialog-body" });
  body.append(el("p", { class: "muted", text: "Templates use local stores by default. Trello, Google, Slack and WhatsApp nodes run when those credentials are present and are skipped or fail visibly otherwise." }));
  for (const template of state.cache.templates) {
    body.append(el("div", { class: "list-item" },
      el("div", { class: "grow" },
        el("div", { text: template.name }),
        el("div", { class: "muted small", text: template.description }),
      ),
      el("button", { class: "primary", text: "Install", onclick: async () => {
        try {
          await api(`/v1/templates/${template.id}/install`, { method: "POST", body: JSON.stringify({ activate: false }) });
          dialog.close();
          toast(`Installed ${template.name}.`);
          route();
        } catch (error) { toast(error.message, true); }
      }}),
    ));
  }
  dialog.append(el("div", { class: "dialog-head" }, el("h2", { text: "Template gallery" }), el("button", { class: "ghost", text: "Close", onclick: () => dialog.close() })), body);
  document.body.append(dialog);
  dialog.addEventListener("close", () => dialog.remove());
  dialog.showModal();
}

function openRun(workflow) {
  const dialog = el("dialog");
  const payload = el("textarea", { placeholder: '{ "name": "Sam", "phone": "+15550112233" }' });
  const dryRun = el("input", { type: "checkbox", checked: false });
  const form = el("form", { class: "dialog-body" });
  form.append(
    el("p", { class: "muted", text: `Trigger: ${workflow.trigger.type}. Payload is available as {{trigger.*}} inside the flow.` }),
    el("label", { class: "field" }, el("span", { text: "Trigger payload (JSON)" }), payload),
    el("label", { class: "row" }, dryRun, el("span", { class: "muted small", text: "Dry run — external HTTP is recorded, never sent" })),
  );
  const actions = el("div", { class: "row" }, el("div", { class: "spacer" }));
  const start = el("button", { class: "primary", type: "submit", text: "Run" });
  actions.append(el("button", { type: "button", text: "Cancel", onclick: () => dialog.close() }), start);
  form.append(actions);
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    start.disabled = true;
    try {
      let parsed = {};
      if (payload.value.trim()) parsed = JSON.parse(payload.value);
      const run = await api(`/v1/workflows/${workflow.id}/run`, {
        method: "POST",
        body: JSON.stringify({ payload: parsed, dryRun: dryRun.checked }),
      });
      dialog.close();
      toast(run.status === "succeeded" ? "Run succeeded." : `Run ${run.status}.`, run.status !== "succeeded");
      location.hash = `#/workflows/${run.id}`;
    } catch (error) {
      toast(error.message, true);
      start.disabled = false;
    }
  });
  dialog.append(el("div", { class: "dialog-head" }, el("h2", { text: `Run ${workflow.name}` }), el("button", { class: "ghost", text: "Close", onclick: () => dialog.close() })), form);
  document.body.append(dialog);
  dialog.addEventListener("close", () => dialog.remove());
  dialog.showModal();
}

async function renderRunDetail(runId) {
  const main = $("#main");
  const runs = await api("/v1/runs");
  const run = runs.find((candidate) => candidate.id === runId);
  if (!run) {
    main.append(el("div", { class: "empty", text: "Run not found." }));
    return;
  }
  const workflows = await api("/v1/workflows");
  const workflow = workflows.find((candidate) => candidate.id === run.workflowId);

  main.append(el("div", { class: "page-head" },
    el("div", {},
      el("button", { class: "ghost", text: "← Workflows", onclick: () => { location.hash = "#/workflows"; } }),
      el("h1", { text: workflow?.name ?? "Run", style: "margin-top:8px" }),
      el("p", { class: "sub mono", text: run.id }),
    ),
    el("div", { class: "row" }, statusBadge(run.status), el("span", { class: "muted small", text: fmtTime(run.startedAt) })),
  ));

  if (run.error) {
    main.append(el("div", { class: "card", style: "border-color:#3a2028" }, el("p", { class: "error", text: run.error })));
  }

  const steps = el("div", { class: "steps" });
  run.steps.forEach((step, index) => {
    steps.append(el("div", { class: "step" },
      el("span", { class: "idx", text: String(index + 1).padStart(2, "0") }),
      el("div", {},
        el("div", { text: `${step.nodeId} · ${step.nodeType}` }),
        el("div", { class: "muted small", text: step.error ? step.error : `${step.attempts} attempt${step.attempts === 1 ? "" : "s"}` }),
      ),
      statusBadge(step.status === "succeeded" ? "succeeded" : "failed"),
    ));
  });
  main.append(el("div", { class: "card panel" },
    el("div", { class: "panel-head" }, el("h2", { text: "Steps" })),
    el("div", { class: "panel-body" }, steps),
  ));

  main.append(el("div", { class: "card panel", style: "margin-top:14px" },
    el("div", { class: "panel-head" }, el("h2", { text: "Trigger" })),
    el("div", { class: "panel-body" }, el("pre", { class: "mono", style: "overflow:auto;margin:0", text: JSON.stringify(run.trigger, null, 2) })),
  ));
}

/* ------------------------------------------------------------------ */
/* automations                                                         */
/* ------------------------------------------------------------------ */

async function renderAutomations() {
  const main = $("#main");
  const tab = state.route[0] ?? "tasks";
  main.append(el("div", { class: "page-head" },
    el("div", {}, el("h1", { text: "Automations" }), el("p", { class: "sub", text: "The local system of record: tasks, bookings, contacts and escalations created by voice agents and workflows." })),
  ));

  const tabs = el("div", { class: "tabs" });
  for (const [id, label] of [["tasks", "Tasks"], ["bookings", "Bookings"], ["escalations", "Escalations"], ["contacts", "Contacts"]]) {
    tabs.append(el("button", { class: `tab${tab === id ? " active" : ""}`, text: label, onclick: () => { location.hash = `#/automations/${id}`; } }));
  }
  main.append(tabs);

  if (tab === "tasks") {
    const tasks = await api("/v1/tasks");
    const panel = el("div", { class: "card panel" });
    if (tasks.length === 0) panel.append(el("div", { class: "empty", text: "No tasks yet. Finish a call where nothing was booked, or run the task template." }));
    for (const task of tasks) {
      panel.append(el("div", { class: "list-item" },
        el("div", { class: "grow" },
          el("div", { text: task.title }),
          el("div", { class: "muted small truncate", text: task.description || "—" }),
          el("div", { class: "row", style: "margin-top:6px" },
            el("span", { class: "badge", text: task.priority }),
            ...task.labels.map((label) => el("span", { class: "badge", text: label })),
          ),
        ),
        el("select", { value: task.status, onchange: async (event) => {
          try {
            await api(`/v1/tasks/${task.id}`, { method: "PATCH", body: JSON.stringify({ status: event.target.value }) });
            toast("Task updated.");
          } catch (error) { toast(error.message, true); }
        }}, ...["todo", "doing", "done"].map((status) => el("option", { value: status, text: status, selected: task.status === status }))),
      ));
    }
    main.append(panel);
  }

  if (tab === "bookings") {
    const bookings = await api("/v1/bookings");
    const panel = el("div", { class: "card panel" });
    if (bookings.length === 0) panel.append(el("div", { class: "empty", text: "No bookings yet. Ask the receptionist agent to book an appointment." }));
    for (const booking of bookings) {
      panel.append(el("div", { class: "list-item" },
        el("div", { class: "grow" },
          el("div", { text: `${booking.name} — ${booking.title}` }),
          el("div", { class: "muted small", text: `${fmtTime(booking.startAt)} · ${booking.durationMin} min · ${booking.phone ?? booking.email ?? "no contact"}` }),
        ),
        statusBadge(booking.status === "confirmed" ? "good" : booking.status),
      ));
    }
    main.append(panel);
  }

  if (tab === "escalations") {
    const escalations = await api("/v1/escalations");
    const panel = el("div", { class: "card panel" });
    if (escalations.length === 0) panel.append(el("div", { class: "empty", text: "No escalations. Urgent calls and large parties land here." }));
    for (const escalation of escalations) {
      panel.append(el("div", { class: "list-item" },
        el("div", { class: "grow" },
          el("div", { text: escalation.reason }),
          el("div", { class: "muted small", text: fmtTime(escalation.createdAt) }),
        ),
        statusBadge(escalation.status),
        el("button", { text: "Acknowledge", disabled: escalation.status !== "open", onclick: async () => {
          try {
            await api(`/v1/escalations/${escalation.id}`, { method: "PATCH", body: JSON.stringify({ status: "acknowledged" }) });
            route();
          } catch (error) { toast(error.message, true); }
        }}),
      ));
    }
    main.append(panel);
  }

  if (tab === "contacts") {
    const contacts = await api("/v1/contacts");
    const panel = el("div", { class: "card panel" });
    if (contacts.length === 0) panel.append(el("div", { class: "empty", text: "No contacts yet. Lead qualification and CRM flows create them." }));
    for (const contact of contacts) {
      panel.append(el("div", { class: "list-item" },
        el("div", { class: "grow" },
          el("div", { text: contact.name }),
          el("div", { class: "muted small", text: contact.email ?? contact.phone ?? "no contact details" }),
        ),
        ...contact.tags.map((tag) => el("span", { class: "badge", text: tag })),
      ));
    }
    main.append(panel);
  }
}

/* ------------------------------------------------------------------ */
/* telephony                                                           */
/* ------------------------------------------------------------------ */

async function renderTelephony() {
  const main = $("#main");
  const tab = state.route[0] ?? "numbers";

  main.append(el("div", { class: "page-head" },
    el("div", {},
      el("h1", { text: "Telephony" }),
      el("p", { class: "sub", text: "Simulated numbers are free and default. Carrier numbers are optional, billed by the carrier, and never purchased without an explicit confirmation." }),
    ),
  ));

  const tabs = el("div", { class: "tabs" });
  for (const [id, label] of [["numbers", "Numbers"], ["sms", "Messages"], ["providers", "Providers"]]) {
    tabs.append(el("button", {
      class: `tab${tab === id ? " active" : ""}`,
      text: label,
      onclick: () => { location.hash = `#/telephony/${id}`; },
    }));
  }
  main.append(tabs);

  if (tab === "numbers") return renderNumbers(main);
  if (tab === "sms") return renderSms(main);
  return renderProviders(main);
}

async function renderNumbers(main) {
  const [numbers, agents] = await Promise.all([api("/v1/numbers"), api("/v1/agents")]);
  state.cache.numbers = numbers;
  state.cache.agents = agents;

  const panel = el("div", { class: "card panel" });
  panel.append(el("div", { class: "panel-head" },
    el("h2", { text: "Phone numbers" }),
    el("div", { class: "row" },
      el("span", { class: "muted small", text: `${numbers.length} in this workspace` }),
      el("button", { class: "primary", text: "Find a number", onclick: openNumberSearch }),
    ),
  ));

  if (numbers.length === 0) {
    panel.append(el("div", { class: "empty", text: "No numbers yet. Search for a free simulated number to test inbound calls and IVR menus." }));
  } else {
    const table = el("table");
    table.append(el("thead", {}, el("tr", {},
      el("th", { text: "Number" }), el("th", { text: "Provider" }), el("th", { text: "Label" }),
      el("th", { text: "Inbound agent" }), el("th", { text: "State" }), el("th", { text: "" }),
    )));
    const body = el("tbody");
    for (const number of numbers) {
      const release = el("button", { class: "ghost", text: "Release", onclick: async (event) => {
        event.stopPropagation();
        const warning = number.simulated
          ? `Release ${number.e164}? It is simulated, so nothing is billed.`
          : `Release ${number.e164}? The carrier may charge for the release and the number may not be recoverable.`;
        if (!confirm(warning)) return;
        try {
          await api(`/v1/numbers/${number.id}?confirm=true`, { method: "DELETE" });
          toast(`Released ${number.e164}.`);
          route();
        } catch (error) { toast(error.message, true); }
      }});
      body.append(el("tr", {},
        el("td", { class: "mono", text: number.e164 }),
        el("td", {}, el("span", { class: "badge", text: number.provider })),
        el("td", { text: number.label }),
        el("td", { class: "muted", text: number.inboundAgentId ? shortId(number.inboundAgentId) : "-" }),
        el("td", {}, statusBadge(number.status)),
        el("td", {}, release),
      ));
    }
    table.append(body);
    panel.append(table);
  }
  main.append(panel);

  const note = el("div", { class: "card panel", style: "margin-top:14px" });
  note.append(el("div", { class: "panel-head" }, el("h2", { text: "How billing works" })));
  note.append(el("div", { class: "panel-body stack" },
    el("p", { class: "muted", text: "Omalla never bills for telephony. Simulated numbers cost nothing. A real carrier number is billed by that carrier: monthly rental, inbound minutes, outbound minutes and SMS are all charged on your carrier account, not here." }),
    el("p", { class: "muted", text: "Carrier purchases are disabled unless the server is started with allowCarrierPurchases enabled, and every purchase still requires a confirmation in this console or the API." }),
  ));
  main.append(note);
}

function openNumberSearch() {
  const dialog = el("dialog");
  const provider = el("select");
  for (const [value, label] of [["simulated", "Simulated - free"], ["twilio", "Twilio - carrier charges"], ["signalwire", "SignalWire - carrier charges"]]) {
    provider.append(el("option", { value, text: label }));
  }
  const country = el("input", { value: "US", maxlength: "2", spellcheck: "false" });
  const area = el("input", { placeholder: "415", maxlength: "3", inputmode: "numeric" });
  const results = el("div", { class: "stack", style: "margin-top:12px" });

  const search = el("button", { class: "primary", type: "button", text: "Search" });
  const form = el("div", { class: "dialog-body" });
  form.append(
    el("p", { class: "muted", text: "Simulated numbers are generated locally and are free. Selecting a carrier searches that carrier's inventory; provisioning it starts carrier billing." }),
    el("div", { class: "form-grid" },
      el("label", { class: "field" }, el("span", { text: "Provider" }), provider),
      el("label", { class: "field" }, el("span", { text: "Country" }), country),
      el("label", { class: "field" }, el("span", { text: "Area code" }), area),
    ),
    el("div", { class: "row", style: "margin-top:10px" }, search),
    results,
  );

  search.addEventListener("click", async () => {
    search.disabled = true;
    results.replaceChildren(el("div", { class: "muted small", text: "Searching..." }));
    try {
      const found = await api("/v1/numbers/search", {
        method: "POST",
        body: JSON.stringify({
          provider: provider.value,
          countryCode: country.value.trim().toUpperCase() || "US",
          ...(area.value.trim() ? { areaCode: area.value.trim() } : {}),
          limit: 8,
        }),
      });
      results.replaceChildren();
      results.append(el("p", { class: found.carrierCharges ? "error" : "muted small", text: found.carrierCharges ? "Carrier charges apply. Prices are set by the carrier." : "Free simulated numbers." }));
      if (found.offers.length === 0) {
        results.append(el("div", { class: "empty", text: "No numbers matched. Try another area code or provider." }));
      }
      for (const offer of found.offers) {
        results.append(el("div", { class: "list-item" },
          el("div", { class: "grow" },
            el("div", { class: "mono", text: offer.e164 }),
            el("div", { class: "muted small", text: `${offer.locality ?? "unknown locality"} - ${offer.capabilities.join(", ")} - ${offer.costNote}` }),
          ),
          el("button", { text: "Provision", onclick: () => openProvision(offer, provider.value, dialog) }),
        ));
      }
    } catch (error) {
      results.replaceChildren(el("p", { class: "error", text: error.message }));
    } finally {
      search.disabled = false;
    }
  });

  dialog.append(el("div", { class: "dialog-head" }, el("h2", { text: "Find a number" }), el("button", { class: "ghost", text: "Close", onclick: () => dialog.close() })), form);
  document.body.append(dialog);
  dialog.addEventListener("close", () => dialog.remove());
  dialog.showModal();
}

function openProvision(offer, provider, parent) {
  const dialog = el("dialog");
  const label = el("input", { placeholder: "Front desk", maxlength: "120" });
  const agents = state.cache.agents;
  const agent = el("select");
  agent.append(el("option", { value: "", text: "No inbound agent yet" }));
  for (const candidate of agents) agent.append(el("option", { value: candidate.id, text: candidate.name }));
  const confirmBox = el("input", { type: "checkbox" });
  const submit = el("button", { class: "primary", type: "submit", text: "Provision", disabled: true });
  const carrier = provider !== "simulated";
  confirmBox.addEventListener("change", () => { submit.disabled = !confirmBox.checked; });

  const form = el("form", { class: "dialog-body" });
  form.append(
    el("p", { class: "mono", text: offer.e164 }),
    el("p", { class: carrier ? "error" : "muted", text: carrier
      ? "This provisions a real carrier number. The carrier charges a monthly fee and per-minute or per-message usage. The charge appears on your carrier account."
      : "This simulated number is free. No carrier is contacted." }),
    el("label", { class: "field" }, el("span", { text: "Label" }), label),
    el("label", { class: "field" }, el("span", { text: "Inbound agent" }), agent),
    el("label", { class: "row" }, confirmBox, el("span", { class: "muted small", text: "I understand the billing and want to provision this number" })),
  );
  const actions = el("div", { class: "row" }, el("div", { class: "spacer" }));
  actions.append(el("button", { type: "button", text: "Cancel", onclick: () => dialog.close() }), submit);
  form.append(actions);

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    submit.disabled = true;
    try {
      const created = await api("/v1/numbers/provision", {
        method: "POST",
        body: JSON.stringify({
          e164: offer.e164,
          provider,
          ...(label.value.trim() ? { label: label.value.trim() } : {}),
          ...(agent.value ? { agentId: agent.value } : {}),
          confirm: true,
        }),
      });
      dialog.close();
      if (parent) parent.close();
      toast(`Provisioned ${created.number.e164}. ${created.billing.note}`);
      route();
    } catch (error) {
      toast(error.message, true);
      submit.disabled = false;
    }
  });

  dialog.append(el("div", { class: "dialog-head" }, el("h2", { text: "Provision number" }), el("button", { class: "ghost", text: "Close", onclick: () => dialog.close() })), form);
  document.body.append(dialog);
  dialog.addEventListener("close", () => dialog.remove());
  dialog.showModal();
}

async function renderSms(main) {
  const messages = await api("/v1/sms?limit=100");
  state.cache.sms = messages;

  const panel = el("div", { class: "card panel" });
  panel.append(el("div", { class: "panel-head" },
    el("h2", { text: "Messages" }),
    el("span", { class: "muted small", text: "inbound and outbound" }),
  ));
  if (messages.length === 0) {
    panel.append(el("div", { class: "empty", text: "No messages yet. Send one below; simulated messages never leave this machine." }));
  } else {
    const table = el("table");
    table.append(el("thead", {}, el("tr", {},
      el("th", { text: "Time" }), el("th", { text: "Direction" }), el("th", { text: "From" }),
      el("th", { text: "To" }), el("th", { text: "Body" }), el("th", { text: "State" }),
    )));
    const body = el("tbody");
    for (const message of messages) {
      body.append(el("tr", {},
        el("td", { class: "muted", text: fmtTime(message.createdAt) }),
        el("td", {}, el("span", { class: "badge", text: message.direction })),
        el("td", { class: "mono", text: message.from }),
        el("td", { class: "mono", text: message.to }),
        el("td", { class: "truncate", text: message.body }),
        el("td", {}, statusBadge(message.status)),
      ));
    }
    table.append(body);
    panel.append(table);
  }
  main.append(panel);

  const compose = el("div", { class: "card panel", style: "margin-top:14px" });
  compose.append(el("div", { class: "panel-head" }, el("h2", { text: "Send a message" }), el("span", { class: "muted small", text: "consent required" })));
  const to = el("input", { placeholder: "+15550112233", spellcheck: "false" });
  const from = el("input", { placeholder: "leave empty to use a workspace number", spellcheck: "false" });
  const text = el("textarea", { placeholder: "Your appointment is confirmed for Tuesday at 3pm.", rows: "3" });
  const consent = el("input", { type: "checkbox" });
  const send = el("button", { class: "primary", type: "submit", text: "Send" });
  const form = el("form", { class: "panel-body form-grid" });
  form.append(
    el("label", { class: "field" }, el("span", { text: "To (E.164)" }), to),
    el("label", { class: "field" }, el("span", { text: "From" }), from),
    el("label", { class: "field full" }, el("span", { text: "Message" }), text),
    el("label", { class: "row full" }, consent, el("span", { class: "muted small", text: "The recipient agreed to receive messages from this workspace" })),
    el("div", { class: "full row" }, send),
  );
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!consent.checked) return toast("Record the recipient's consent before sending.", true);
    send.disabled = true;
    try {
      const message = await api("/v1/sms", {
        method: "POST",
        body: JSON.stringify({
          to: to.value.trim(),
          body: text.value,
          ...(from.value.trim() ? { from: from.value.trim() } : {}),
          consent: true,
        }),
      });
      toast(`Message ${message.status}${message.simulated ? " (simulated)" : ""}.`);
      route();
    } catch (error) {
      toast(error.message, true);
      send.disabled = false;
    }
  });
  compose.append(form);
  main.append(compose);
}

async function renderProviders(main) {
  const providers = await api("/v1/telephony/providers");
  state.cache.providers = providers;

  const panel = el("div", { class: "card panel" });
  panel.append(el("div", { class: "panel-head" },
    el("h2", { text: "Carrier adapters" }),
    el("span", { class: "muted small", text: "availability is reported honestly" }),
  ));
  const table = el("table");
  table.append(el("thead", {}, el("tr", {},
    el("th", { text: "Provider" }), el("th", { text: "Available" }), el("th", { text: "Detail" }), el("th", { text: "Required credentials" }),
  )));
  const body = el("tbody");
  for (const entry of providers) {
    body.append(el("tr", {},
      el("td", {}, el("strong", { text: entry.label }), el("div", { class: "muted small mono", text: entry.id })),
      el("td", {}, el("span", { class: `badge ${entry.available ? "good" : ""}`, text: entry.available ? "yes" : "no" })),
      el("td", { class: "muted", text: entry.detail }),
      el("td", { class: "mono small", text: entry.requiredEnv.length ? entry.requiredEnv.join(", ") : "-" }),
    ));
  }
  table.append(body);
  panel.append(table);
  main.append(panel);

  const help = el("div", { class: "card panel", style: "margin-top:14px" });
  help.append(el("div", { class: "panel-head" }, el("h2", { text: "Self-hosted SIP" })));
  help.append(el("div", { class: "panel-body stack" },
    el("p", { class: "muted", text: "Asterisk, FreeSWITCH, LiveKit SIP and Jambonz can sit behind the SIP gateway contract so calls never touch a paid carrier. That path needs Docker and has not been verified in this build." }),
    el("p", { class: "muted small", text: "Set credentials in Settings. Twilio needs TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN plus TWILIO_PHONE_NUMBER for outbound calls." }),
  ));
  main.append(help);
}

/* ------------------------------------------------------------------ */
/* settings                                                            */
/* ------------------------------------------------------------------ */

async function renderSettings() {
  const main = $("#main");
  main.append(el("div", { class: "page-head" },
    el("div", {}, el("h1", { text: "Settings" }), el("p", { class: "sub", text: "Credentials are encrypted at rest with this host's master key and never returned by the API." })),
  ));

  const [credentials, agents, me] = await Promise.all([
    api("/v1/credentials"),
    api("/v1/agents"),
    api("/v1/me"),
  ]);

  const tenantCard = el("div", { class: "card panel" });
  tenantCard.append(el("div", { class: "panel-head" }, el("h2", { text: "Workspace" })));
  tenantCard.append(el("div", { class: "panel-body stack" },
    signalRow("Tenant", me.tenant?.name ?? "—"),
    signalRow("Timezone", me.tenant?.settings?.timezone ?? "—"),
    signalRow("Outbound", me.tenant?.settings?.outboundEnabled ? "enabled (consent still required)" : "disabled"),
    signalRow("Daily outbound cap", String(me.tenant?.settings?.dailyOutboundCap ?? 0)),
    signalRow("Reach", location.host),
  ));

  const agentsCard = el("div", { class: "card panel" });
  agentsCard.append(el("div", { class: "panel-head" }, el("h2", { text: "Agents" })));
  for (const agent of agents) {
    agentsCard.append(el("div", { class: "list-item" },
      el("div", { class: "grow" },
        el("div", { text: agent.name }),
        el("div", { class: "muted small", text: `${agent.config.model.provider}/${agent.config.model.model} · voice ${agent.config.voice.provider}` }),
      ),
      statusBadge(agent.status),
    ));
  }

  const credCard = el("div", { class: "card panel" });
  credCard.append(el("div", { class: "panel-head" }, el("h2", { text: "Credentials" }), el("span", { class: "muted small", text: "BYOK, optional" })));
  const form = el("form", { class: "panel-body form-grid" });
  const name = el("input", { placeholder: "TRELLO_KEY", spellcheck: "false" });
  const value = el("input", { type: "password", placeholder: "value", autocomplete: "off" });
  const submit = el("button", { class: "primary", type: "submit", text: "Save credential" });
  form.append(
    el("label", { class: "field" }, el("span", { text: "Name (UPPER_SNAKE_CASE)" }), name),
    el("label", { class: "field" }, el("span", { text: "Value" }), value),
    el("div", { class: "full row" }, submit, el("span", { class: "hint", text: "Trello: TRELLO_KEY, TRELLO_TOKEN. Google: GOOGLE_ACCESS_TOKEN. Slack: SLACK_BOT_TOKEN." })),
  );
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      await api(`/v1/credentials/${encodeURIComponent(name.value.trim().toUpperCase())}`, {
        method: "PUT",
        body: JSON.stringify({ value: value.value }),
      });
      name.value = "";
      value.value = "";
      toast("Credential stored.");
      route();
    } catch (error) { toast(error.message, true); }
  });
  credCard.append(form);
  for (const credential of credentials) {
    credCard.append(el("div", { class: "list-item" },
      el("div", { class: "grow" },
        el("div", { class: "mono", text: credential.name }),
        el("div", { class: "muted small", text: `${credential.provider} · added ${fmtTime(credential.createdAt)}` }),
      ),
      el("button", { class: "danger", text: "Remove", onclick: async () => {
        try {
          await api(`/v1/credentials/${encodeURIComponent(credential.name)}`, { method: "DELETE" });
          route();
        } catch (error) { toast(error.message, true); }
      }}),
    ));
  }
  if (credentials.length === 0) {
    credCard.append(el("div", { class: "empty", text: "No credentials stored. The zero-cost path needs none." }));
  }

  main.append(el("div", { class: "grid cols-2" }, tenantCard, agentsCard));
  main.append(el("div", { style: "margin-top:14px" }, credCard));
}

/* ------------------------------------------------------------------ */

boot();
