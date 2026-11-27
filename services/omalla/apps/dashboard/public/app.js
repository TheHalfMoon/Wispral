/* Omalla Studio — local-first voice, realtime & SIP console (vanilla ES module, zero build step). */

const I18N = {
  en: {
    "nav.overview": "Overview",
    "nav.studio": "Voice Studio",
    "nav.agents": "Agents & Versions",
    "nav.calls": "Calls",
    "nav.workflows": "Workflows",
    "nav.automations": "Automations",
    "nav.telephony": "Telephony & SIP",
    "nav.settings": "Settings",
    "studio.title": "Omalla Voice Studio",
    "studio.sub": "Full-duplex AudioWorklet WebSocket & WebRTC console with live waveform and sink-confirmed T0..T6 latency telemetry.",
    "studio.connectWs": "Connect Duplex WS",
    "studio.connectRtc": "Connect WebRTC",
    "studio.startMic": "Start Mic (AudioWorklet)",
    "studio.stopSession": "Disconnect",
    "studio.bargeIn": "Trigger Barge-In (OM-T8)",
    "studio.latency": "T0..T6 Audio-Boundary Latency Inspector",
    "agents.title": "Agents & Version History",
    "agents.sub": "Immutable agent snapshots (v1, v2, …), deterministic test runner, and 1-click rollback.",
    "rollback": "Rollback",
  },
  ar: {
    "nav.overview": "نظرة عامة",
    "nav.studio": "استوديو الصوت المباشر",
    "nav.agents": "الوكلاء والإصدارات",
    "nav.calls": "المكالمات",
    "nav.workflows": "سير العمل",
    "nav.automations": "الأتمتة والسجلات",
    "nav.telephony": "الهاتف و SIP",
    "nav.settings": "الإعدادات",
    "studio.title": "استوديو أومالا الصوتي المباشر",
    "studio.sub": "وحدة اختبار صوتية ثنائية الاتجاه عبر WebSocket و WebRTC مع مخطط الموجة وقياس زمن الاستجابة T0..T6 المؤكد.",
    "studio.connectWs": "اتصال WebSocket مزدوج",
    "studio.connectRtc": "اتصال WebRTC",
    "studio.startMic": "تشغيل الميكروفون (AudioWorklet)",
    "studio.stopSession": "قطع الاتصال",
    "studio.bargeIn": "اختبار المقاطعة (OM-T8)",
    "studio.latency": "محلل زمن الاستجابة الصوتي T0..T6",
    "agents.title": "الوكلاء وسجل الإصدارات",
    "agents.sub": "لقطات إصدارات غير قابلة للتغيير، فحص تجريبي، واسترجاع فوري بنقرة واحدة.",
    "rollback": "استرجاع الإصدار",
  },
};

const state = {
  token: localStorage.getItem("omalla.key") ?? "",
  lang: localStorage.getItem("omalla.lang") ?? "en",
  theme: localStorage.getItem("omalla.theme") ?? "dark",
  me: null,
  view: "overview",
  route: [],
  cache: {
    calls: [],
    workflows: [],
    templates: [],
    metrics: {},
    tasks: [],
    bookings: [],
    escalations: [],
    credentials: [],
    agents: [],
    numbers: [],
    sms: [],
    providers: [],
  },
  socket: null,
  refreshTimer: null,
  studio: {
    ws: null,
    webrtcSessionId: null,
    audioCtx: null,
    workletNode: null,
    micStream: null,
    activeSources: [],
    seq: 0,
    turnEpoch: 0,
    waveformHistory: new Array(64).fill(0.02),
    lastTelemetry: null,
    events: [],
  },
};

const $ = (sel, root = document) => root.querySelector(sel);
const t = (key) => I18N[state.lang]?.[key] ?? I18N.en[key] ?? key;

function applyLocaleAndTheme() {
  const html = document.documentElement;
  html.dataset.theme = state.theme;
  html.lang = state.lang;
  html.dir = state.lang === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((node) => {
    const key = node.dataset.i18n;
    if (key) node.textContent = t(key);
  });
  const langBtn = $("#lang-toggle");
  if (langBtn) langBtn.textContent = state.lang === "ar" ? "English (LTR)" : "العربية (RTL)";
  const themeBtn = $("#theme-toggle");
  if (themeBtn) themeBtn.textContent = state.theme === "dark" ? "Light (#7E22CE)" : "Dark (#D8B4FE)";
}

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
  const node = el("div", { class: `toast${bad ? " bad" : ""}`, dir: "auto", text: message });
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
const fmtMs = (ms) => (ms !== null && ms !== undefined && ms !== "" ? `${ms} ms` : "—");
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
    published: ["good", "published"],
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
    observed_audio_halt: ["good", "observed_audio_halt"],
    stopped_unconfirmed: ["warn", "stopped_unconfirmed"],
    pending_sink_ack: ["live", "pending_sink_ack"],
  };
  const [tone, label] = map[status] ?? ["", status];
  return el("span", { class: `badge ${tone}`, text: label ?? "—" });
}

/* ------------------------------------------------------------------ */
/* auth & shell controls                                               */
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
  applyLocaleAndTheme();
  $("#lang-toggle")?.addEventListener("click", () => {
    state.lang = state.lang === "en" ? "ar" : "en";
    localStorage.setItem("omalla.lang", state.lang);
    applyLocaleAndTheme();
    if (!$("#shell").hidden) route();
  });
  $("#theme-toggle")?.addEventListener("click", () => {
    state.theme = state.theme === "dark" ? "light" : "dark";
    localStorage.setItem("omalla.theme", state.theme);
    applyLocaleAndTheme();
  });

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
  studio: renderStudio,
  agents: renderAgents,
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
  if (state.view !== "studio") teardownStudioSession();
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
    el("div", {},
      el("h1", { dir: "auto", text: t("nav.overview") }),
      el("p", { class: "sub", dir: "auto", text: "Local-first voice AI, SQLite WAL persistence, and deterministic telephony simulation." }),
    ),
    el("div", { class: "row" },
      el("button", { text: t("nav.studio"), onclick: () => { location.hash = "#/studio"; } }),
      el("button", { class: "primary", text: "Simulate a call", onclick: () => { location.hash = "#/calls"; } }),
    ),
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
    recent.append(el("div", { class: "empty", text: "No calls yet. Start one from Voice Studio or Calls." }));
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
        el("div", { dir: "auto", text: workflow.name }),
        el("div", { class: "muted small", text: `${workflow.trigger.type} · v${workflow.version}` }),
      ),
      statusBadge(workflow.status),
    ));
  }
  automation.append(list);

  main.append(el("div", { class: "grid cols-2" }, recent, automation));

  state.refreshTimer = setInterval(() => {
    if (state.view === "overview") route();
  }, 15000);
}

/* ------------------------------------------------------------------ */
/* Voice Studio (AudioWorklet + Duplex WS + WebRTC + T0..T6 Inspector) */
/* ------------------------------------------------------------------ */

function teardownStudioSession() {
  const s = state.studio;
  for (const src of s.activeSources) {
    try { src.stop(); } catch { /* ignore */ }
  }
  s.activeSources = [];
  if (s.workletNode) {
    try { s.workletNode.disconnect(); } catch { /* ignore */ }
    s.workletNode = null;
  }
  if (s.micStream) {
    s.micStream.getTracks().forEach((tr) => tr.stop());
    s.micStream = null;
  }
  if (s.audioCtx) {
    try { void s.audioCtx.close(); } catch { /* ignore */ }
    s.audioCtx = null;
  }
  if (s.ws) {
    try { s.ws.close(); } catch { /* ignore */ }
    s.ws = null;
  }
  if (s.webrtcSessionId) {
    const id = s.webrtcSessionId;
    s.webrtcSessionId = null;
    void api(`/v1/realtime/webrtc/${id}`, { method: "DELETE" }).catch(() => {});
  }
}

async function renderStudio() {
  const main = $("#main");
  const [agents, sipStatus] = await Promise.all([
    api("/v1/agents"),
    api("/v1/telephony/sip/status"),
  ]);
  state.cache.agents = agents;

  main.append(el("div", { class: "page-head" },
    el("div", {},
      el("h1", { dir: "auto", text: t("studio.title") }),
      el("p", { class: "sub", dir: "auto", text: t("studio.sub") }),
    ),
    el("span", { class: "badge live", id: "studio-conn-badge", text: "idle" }),
  ));

  const agentSelect = el("select", { id: "studio-agent" });
  for (const ag of agents) {
    agentSelect.append(el("option", { value: ag.id, text: `${ag.name} (v${ag.version} · ${ag.config.language})` }));
  }
  const codecSelect = el("select", { id: "studio-codec" },
    el("option", { value: "pcm16", text: "PCM16 · 16 kHz (20 ms = 640 B)" }),
    el("option", { value: "pcmu", text: "G.711 PCMU μ-law · 8 kHz (20 ms = 160 B)" }),
    el("option", { value: "pcma", text: "G.711 PCMA A-law · 8 kHz (20 ms = 160 B)" }),
  );
  const sinkAckBox = el("input", { type: "checkbox", checked: true, id: "studio-sink-ack" });

  const canvas = el("canvas", { id: "studio-waveform", class: "waveform-canvas", width: 640, height: 92 });
  const transcriptBox = el("div", { class: "transcript", id: "studio-transcript" },
    el("div", { class: "empty", dir: "auto", text: "Connect Duplex WebSocket or WebRTC to begin live voice testing." }),
  );
  const latencyContainer = el("div", { id: "studio-latency-cards", class: "latency-grid" });
  renderLatencyCards(latencyContainer, state.studio.lastTelemetry);

  const utteranceInput = el("input", {
    dir: "auto",
    placeholder: state.lang === "ar"
      ? "اكتب عبارة صوتية أو بالعربية: مرحبا أريد حجز موعد غداً الساعة 3"
      : "Speak via AudioWorklet or send utterance (e.g. مرحبا أريد حجز موعد غداً الساعة 3)…",
  });

  const pushWaveSample = (rms) => {
    state.studio.waveformHistory.push(Math.min(1, Math.max(0.015, rms * 3.2)));
    if (state.studio.waveformHistory.length > 64) state.studio.waveformHistory.shift();
    drawWaveform(canvas, state.studio.waveformHistory);
  };
  drawWaveform(canvas, state.studio.waveformHistory);

  const appendTurnBubble = (role, text, meta = "") => {
    if (transcriptBox.querySelector(".empty")) transcriptBox.replaceChildren();
    transcriptBox.append(el("div", { class: `turn ${role}` },
      el("div", { class: "who", text: role }),
      el("div", { class: "text", dir: "auto", text }),
      ...(meta ? [el("div", { class: "meta mono", text: meta })] : []),
    ));
    transcriptBox.scrollTop = transcriptBox.scrollHeight;
  };

  const handleServerRealtimeEvent = (ev) => {
    if (typeof ev.turnEpoch === "number") state.studio.turnEpoch = ev.turnEpoch;
    if (ev.type === "session.ready") {
      $("#studio-conn-badge").textContent = `live · epoch ${ev.turnEpoch}`;
    } else if (ev.type === "stt.final") {
      appendTurnBubble("caller", ev.text, `T4=${ev.atMs}ms · epoch ${ev.turnEpoch}`);
    } else if (ev.type === "assistant.speech") {
      appendTurnBubble("assistant", ev.text, ev.interrupted ? "interrupted (barge-in)" : `epoch ${ev.turnEpoch}`);
    } else if (ev.type === "audio.clear") {
      // Stop local Web Audio playback immediately and send sink confirmation (OM-T8)!
      for (const src of state.studio.activeSources) {
        try { src.stop(); } catch { /* ignore */ }
      }
      state.studio.activeSources = [];
      if (sinkAckBox.checked) {
        sendControl({ type: "clear.ack", turnEpoch: ev.turnEpoch });
      }
    } else if (ev.type === "barge_in.halt") {
      state.studio.lastTelemetry = {
        ...(state.studio.lastTelemetry ?? {}),
        turnEpoch: ev.turnEpoch,
        t1BargeInOnsetMs: ev.t1BargeInOnsetMs,
        t2AudioHaltMs: ev.t2AudioHaltMs,
        t2HaltStatus: ev.t2HaltStatus,
        deltasMs: {
          ...(state.studio.lastTelemetry?.deltasMs ?? {}),
          bargeInHaltMs: ev.bargeInHaltMs,
        },
      };
      renderLatencyCards(latencyContainer, state.studio.lastTelemetry);
    } else if (ev.type === "telemetry.latency" && ev.telemetry) {
      state.studio.lastTelemetry = ev.telemetry;
      renderLatencyCards(latencyContainer, ev.telemetry);
    }
  };

  const sendControl = (obj) => {
    if (state.studio.ws && state.studio.ws.readyState === WebSocket.OPEN) {
      state.studio.ws.send(JSON.stringify(obj));
      return;
    }
    if (state.studio.webrtcSessionId) {
      void api(`/v1/realtime/webrtc/${state.studio.webrtcSessionId}/control`, {
        method: "POST",
        body: JSON.stringify(obj),
      }).then((res) => {
        if (res?.events) res.events.forEach(handleServerRealtimeEvent);
        if (res?.telemetry?.turns?.length) {
          state.studio.lastTelemetry = res.telemetry.turns[res.telemetry.turns.length - 1];
          renderLatencyCards(latencyContainer, state.studio.lastTelemetry);
        }
      }).catch((err) => toast(err.message, true));
    }
  };

  const connectWsBtn = el("button", {
    class: "primary",
    text: t("studio.connectWs"),
    onclick: async () => {
      teardownStudioSession();
      const agentId = agentSelect.value;
      if (!agentId) return toast("Select an agent first.", true);
      try {
        const issued = await api("/v1/realtime/token", {
          method: "POST",
          body: JSON.stringify({ agentId }),
        });
        const proto = location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${proto}//${location.host}/v1/realtime/ws?token=${encodeURIComponent(issued.token)}&codec=${encodeURIComponent(codecSelect.value)}&sinkAck=${sinkAckBox.checked ? "1" : "0"}`;
        const ws = new WebSocket(wsUrl);
        ws.binaryType = "arraybuffer";
        state.studio.ws = ws;

        ws.addEventListener("message", (msg) => {
          if (typeof msg.data === "string") {
            try { handleServerRealtimeEvent(JSON.parse(msg.data)); } catch { /* ignore */ }
            return;
          }
          const bytes = new Uint8Array(msg.data);
          let energy = 0;
          for (let i = 0; i < bytes.length; i += 2) energy += Math.abs((bytes[i] ?? 0) - 128) / 128;
          pushWaveSample(bytes.length ? energy / (bytes.length / 2) : 0.05);
          playOutboundFrame(bytes, codecSelect.value);
        });
        ws.addEventListener("close", () => {
          const badge = $("#studio-conn-badge");
          if (badge) badge.textContent = "disconnected";
        });
        toast("Connected to /v1/realtime/ws with single-use media token.");
      } catch (err) {
        toast(err.message, true);
      }
    },
  });

  const connectRtcBtn = el("button", {
    text: t("studio.connectRtc"),
    onclick: async () => {
      teardownStudioSession();
      const agentId = agentSelect.value;
      if (!agentId) return toast("Select an agent first.", true);
      try {
        const keySalt = new Uint8Array(30);
        crypto.getRandomValues(keySalt);
        const inlineKey = btoa(String.fromCharCode(...keySalt));
        const sdpOffer = [
          "v=0",
          "o=- 1000 2 IN IP4 127.0.0.1",
          "s=-",
          "t=0 0",
          "m=audio 9 RTP/SAVP 0 8 101",
          "c=IN IP4 127.0.0.1",
          "a=ice-ufrag:studio",
          "a=ice-pwd:studiopassword1234567890",
          "a=rtpmap:0 PCMU/8000",
          "a=rtpmap:8 PCMA/8000",
          "a=rtpmap:101 telephone-event/8000",
          `a=crypto:1 AES_CM_128_HMAC_SHA1_80 inline:${inlineKey}`,
          "m=application 9 UDP/DTLS/SCTP webrtc-datachannel",
          "a=sctp-port:5000",
        ].join("\r\n") + "\r\n";

        const negotiated = await api("/v1/realtime/webrtc/offer", {
          method: "POST",
          body: JSON.stringify({
            agentId,
            sdp: sdpOffer,
            sinkAckSupported: sinkAckBox.checked,
          }),
        });
        state.studio.webrtcSessionId = negotiated.sessionId;
        $("#studio-conn-badge").textContent = `webrtc · ${negotiated.codec.toUpperCase()} :${negotiated.localUdpPort}`;
        toast(`WebRTC ICE-lite negotiated (${negotiated.sessionId}).`);
      } catch (err) {
        toast(err.message, true);
      }
    },
  });

  const micBtn = el("button", {
    text: t("studio.startMic"),
    onclick: async () => {
      if (!state.studio.ws || state.studio.ws.readyState !== WebSocket.OPEN) {
        return toast("Connect Duplex WS first, then enable AudioWorklet microphone.", true);
      }
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        const ctx = new AudioCtx();
        state.studio.audioCtx = ctx;
        await ctx.audioWorklet.addModule("/audio-worklet.js");
        const stream = await navigator.mediaDevices.getUserMedia({
          audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true },
        });
        state.studio.micStream = stream;
        const source = ctx.createMediaStreamSource(stream);
        const worklet = new AudioWorkletNode(ctx, "omalla-pcm16-worklet");
        state.studio.workletNode = worklet;
        worklet.port.onmessage = (ev) => {
          if (ev.data?.type !== "pcm16") return;
          pushWaveSample(ev.data.rms ?? 0.03);
          if (state.studio.ws?.readyState === WebSocket.OPEN) {
            const pcmBytes = new Uint8Array(ev.data.pcm16Buffer);
            const framed = new Uint8Array(4 + pcmBytes.length);
            framed[0] = 0x4f; // 'O'
            framed[1] = 0x4d; // 'M'
            const seq = state.studio.seq & 0xffff;
            state.studio.seq = (seq + 1) & 0xffff;
            framed[2] = (seq >> 8) & 0xff;
            framed[3] = seq & 0xff;
            framed.set(pcmBytes, 4);
            state.studio.ws.send(framed.buffer);
          }
        };
        source.connect(worklet);
        toast("AudioWorklet streaming 20 ms 16 kHz PCM16 frames.");
      } catch (err) {
        toast(`Microphone unavailable (${err.message}); use simulated utterance probe below.`, true);
      }
    },
  });

  const bargeBtn = el("button", {
    class: "danger",
    text: t("studio.bargeIn"),
    onclick: () => {
      sendControl({ type: "barge_in" });
      pushWaveSample(0.65);
    },
  });

  const stopBtn = el("button", {
    class: "ghost",
    text: t("studio.stopSession"),
    onclick: () => {
      teardownStudioSession();
      $("#studio-conn-badge").textContent = "idle";
    },
  });

  const sendUtteranceBtn = el("button", {
    class: "primary",
    text: "Send Voice Turn",
    onclick: () => {
      const text = utteranceInput.value.trim();
      if (!text) return;
      utteranceInput.value = "";
      pushWaveSample(0.45);
      sendControl({ type: "utterance.text", text });
    },
  });
  utteranceInput.addEventListener("keydown", (e) => { if (e.key === "Enter") sendUtteranceBtn.click(); });

  const arabicPresetBtn = el("button", {
    class: "ghost",
    dir: "rtl",
    text: "تجربة بالعربية: حجز موعد غداً الساعة 3",
    onclick: () => {
      utteranceInput.value = "مرحبا أريد حجز موعد غداً الساعة 3 باسم سارة";
      sendUtteranceBtn.click();
    },
  });

  const controlCard = el("div", { class: "card panel" },
    el("div", { class: "panel-head" },
      el("h2", { text: "Live Duplex Console" }),
      el("div", { class: "row" }, connectWsBtn, connectRtcBtn, micBtn, bargeBtn, stopBtn),
    ),
    el("div", { class: "panel-body stack" },
      el("div", { class: "form-grid" },
        el("label", { class: "field" }, el("span", { text: "Agent" }), agentSelect),
        el("label", { class: "field" }, el("span", { text: "Wire Codec" }), codecSelect),
      ),
      el("label", { class: "row" },
        sinkAckBox,
        el("span", { class: "muted small", text: "Client sends clear.ack on barge-in (uncheck to simulate unacknowledged PSTN trunk -> stopped_unconfirmed per OM-T8)" }),
      ),
      canvas,
      el("div", { class: "row" },
        el("div", { style: "flex:1" }, utteranceInput),
        sendUtteranceBtn,
        arabicPresetBtn,
      ),
    ),
  );

  const latencyCard = el("div", { class: "card panel" },
    el("div", { class: "panel-head" },
      el("h2", { dir: "auto", text: t("studio.latency") }),
      el("span", { class: "muted small mono", text: "OM-T8 sink-confirmed audio boundaries" }),
    ),
    el("div", { class: "panel-body" }, latencyContainer),
  );

  const sipSummaryCard = buildSipMonitorCard(sipStatus);

  main.append(el("div", { class: "stack" },
    controlCard,
    latencyCard,
    el("div", { class: "grid cols-2" },
      el("div", { class: "card panel" },
        el("div", { class: "panel-head" }, el("h2", { text: "Live Turn Transcript" })),
        transcriptBox,
      ),
      sipSummaryCard,
    ),
  ));
}

function renderLatencyCards(container, tlm) {
  container.replaceChildren();
  const stages = [
    ["T0 · Speech End", tlm?.t0SpeechEndMs, "Caller VAD final"],
    ["T1 · Barge-In Onset", tlm?.t1BargeInOnsetMs, "turn_epoch++"],
    ["T2 · Audio Halt", tlm?.t2AudioHaltMs, tlm?.t2HaltStatus ?? "not_applicable"],
    ["T3 · Partial STT", tlm?.t3PartialSttMs, "Streaming partial"],
    ["T4 · Final STT", tlm?.t4FinalSttMs, tlm?.deltasMs?.sttFinalMs != null ? `+${tlm.deltasMs.sttFinalMs} ms` : "—"],
    ["T5 · First Token", tlm?.t5FirstTokenMs, tlm?.deltasMs?.llmFirstTokenMs != null ? `+${tlm.deltasMs.llmFirstTokenMs} ms` : "—"],
    ["T6 · First TTS Frame", tlm?.t6FirstAudioFrameMs, tlm?.deltasMs?.ttsFirstFrameFromSpeechEndMs != null ? `E2E ${tlm.deltasMs.ttsFirstFrameFromSpeechEndMs} ms` : "20 ms pacer"],
  ];
  for (const [label, ms, sub] of stages) {
    const stageEl = el("div", { class: "latency-stage" },
      el("span", { class: "code-tag", text: label }),
      el("span", { class: "ms-val", text: ms !== null && ms !== undefined ? `${ms} ms` : "—" }),
    );
    if (sub === "observed_audio_halt" || sub === "stopped_unconfirmed" || sub === "pending_sink_ack") {
      stageEl.append(statusBadge(sub));
    } else {
      stageEl.append(el("span", { class: "muted small", text: sub }));
    }
    container.append(stageEl);
  }
}

function drawWaveform(canvas, samples) {
  const ctx = canvas.getContext?.("2d");
  if (!ctx) return;
  const w = canvas.width;
  const h = canvas.height;
  ctx.clearRect(0, 0, w, h);
  const accent = state.theme === "light" ? "#7E22CE" : "#D8B4FE";
  ctx.fillStyle = accent;
  const barW = Math.max(3, Math.floor(w / samples.length) - 3);
  samples.forEach((amp, i) => {
    const bh = Math.max(4, Math.round(amp * (h - 14)));
    const x = i * (barW + 3) + 4;
    const y = Math.round((h - bh) / 2);
    ctx.fillRect(x, y, barW, bh);
  });
}

function playOutboundFrame(bytes, codec) {
  try {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    if (!AudioCtx) return;
    if (!state.studio.audioCtx) state.studio.audioCtx = new AudioCtx();
    const ctx = state.studio.audioCtx;
    if (codec !== "pcm16" || bytes.byteLength < 4) return;
    const sampleCount = Math.floor(bytes.byteLength / 2);
    const audioBuf = ctx.createBuffer(1, sampleCount, 16000);
    const chan = audioBuf.getChannelData(0);
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    for (let i = 0; i < sampleCount; i += 1) {
      chan[i] = view.getInt16(i * 2, true) / 32768;
    }
    const src = ctx.createBufferSource();
    src.buffer = audioBuf;
    src.connect(ctx.destination);
    state.studio.activeSources.push(src);
    src.onended = () => {
      state.studio.activeSources = state.studio.activeSources.filter((s) => s !== src);
    };
    src.start();
  } catch {
    /* Headless / autoplay restricted environments ignore Web Audio output */
  }
}

/* ------------------------------------------------------------------ */
/* Agents & Immutable Version Rollback UI                              */
/* ------------------------------------------------------------------ */

async function renderAgents() {
  const main = $("#main");
  const agents = await api("/v1/agents");
  state.cache.agents = agents;

  main.append(el("div", { class: "page-head" },
    el("div", {},
      el("h1", { dir: "auto", text: t("agents.title") }),
      el("p", { class: "sub", dir: "auto", text: t("agents.sub") }),
    ),
  ));

  for (const agent of agents) {
    const versions = await api(`/v1/agents/${agent.id}/versions`);
    const card = el("div", { class: "card panel", style: "margin-bottom:14px" });
    const testBtn = el("button", {
      text: "Run Eval Test",
      onclick: async () => {
        try {
          const res = await api(`/v1/agents/${agent.id}/test`, {
            method: "POST",
            body: JSON.stringify({
              callerTurns: ["What are your opening hours?", "مع السلامة"],
            }),
          });
          toast(`Agent v${res.versionTested} passed=${res.passed} (${(res.transcript ?? []).length} turns).`);
        } catch (err) {
          toast(err.message, true);
        }
      },
    });
    const bumpBtn = el("button", {
      class: "primary",
      text: "Publish New Snapshot",
      onclick: async () => {
        try {
          await api(`/v1/agents/${agent.id}/publish`, { method: "POST" });
          toast(`Published new snapshot for ${agent.name}.`);
          route();
        } catch (err) {
          toast(err.message, true);
        }
      },
    });

    card.append(el("div", { class: "panel-head" },
      el("div", {},
        el("h2", { dir: "auto", text: `${agent.name} · v${agent.version}` }),
        el("div", { class: "muted small", text: `${agent.config.language} · model ${agent.config.model.provider}/${agent.config.model.model} · silenceTimeout ${agent.config.silenceTimeoutSec}s` }),
      ),
      el("div", { class: "row" }, statusBadge(agent.status), testBtn, bumpBtn),
    ));

    const vTable = el("table");
    vTable.append(el("thead", {}, el("tr", {},
      el("th", { text: "Version" }),
      el("th", { text: "Created" }),
      el("th", { text: "Actor" }),
      el("th", { text: "Note" }),
      el("th", { text: "" }),
    )));
    const vBody = el("tbody");
    for (const ver of versions) {
      const rbBtn = el("button", {
        class: "ghost",
        disabled: ver.version === agent.version,
        text: t("rollback"),
        onclick: async () => {
          try {
            const updated = await api(`/v1/agents/${agent.id}/rollback`, {
              method: "POST",
              body: JSON.stringify({ version: ver.version, note: `Studio 1-click rollback to v${ver.version}` }),
            });
            toast(`Rolled back ${updated.name} to v${ver.version} (now v${updated.version}).`);
            route();
          } catch (err) {
            toast(err.message, true);
          }
        },
      });
      vBody.append(el("tr", {},
        el("td", { class: "mono", text: `v${ver.version}` }),
        el("td", { class: "muted", text: fmtTime(ver.createdAt) }),
        el("td", { class: "mono small", text: ver.createdBy }),
        el("td", { dir: "auto", class: "muted small", text: ver.note ?? "—" }),
        el("td", {}, rbBtn),
      ));
    }
    vTable.append(vBody);
    card.append(vTable);
    main.append(card);
  }
}

/* ------------------------------------------------------------------ */
/* calls                                                               */
/* ------------------------------------------------------------------ */

async function renderCalls() {
  const main = $("#main");
  const callId = state.route[0];
  if (callId) return renderCallDetail(callId);

  main.append(el("div", { class: "page-head" },
    el("div", {}, el("h1", { dir: "auto", text: t("nav.calls") }), el("p", { class: "sub", text: "Simulated, Realtime WS/WebRTC, and carrier conversations with live transcripts." })),
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
}

function openNewCall() {
  const dialog = el("dialog");
  const form = el("form", { class: "dialog-body" });
  const to = el("input", { value: "+15550001234" });
  const from = el("input", { value: "+15550112233" });
  const say = el("textarea", { dir: "auto", placeholder: "One caller utterance per line, e.g.\nI'd like to book an appointment\nMy name is Sam Rivera\nTomorrow at 3pm" });
  const press = el("input", { placeholder: "Optional DTMF keys, e.g. 1" });

  form.append(
    el("div", { class: "form-grid" },
      el("label", { class: "field" }, el("span", { text: "Business number" }), to),
      el("label", { class: "field" }, el("span", { text: "Caller number" }), from),
    ),
    el("label", { class: "field" }, el("span", { text: "Caller utterances" }), say),
    el("label", { class: "field" }, el("span", { text: "DTMF (before speech)" }), press),
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
  const input = el("input", { dir: "auto", placeholder: "Speak as the caller…", disabled: !live });
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
      signalRow("Avg latency", fmtMs(call.metrics?.turnLatenciesMs?.length ? Math.round(call.metrics.turnLatenciesMs.reduce((a, b) => a + b, 0) / call.metrics.turnLatenciesMs.length) : null)),
      signalRow("Caller verified (OM-T2)", String(Boolean(call.metadata?.callerNumberVerified))),
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
      el("div", { class: "text", dir: "auto", text: turn.text }),
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
}

/* ------------------------------------------------------------------ */
/* workflows + version rollback                                        */
/* ------------------------------------------------------------------ */

async function renderWorkflows() {
  const main = $("#main");
  const runId = state.route[0];
  if (runId) return renderRunDetail(runId);

  main.append(el("div", { class: "page-head" },
    el("div", {}, el("h1", { dir: "auto", text: t("nav.workflows") }), el("p", { class: "sub", text: "Native automation, n8n import/export, immutable versions, and 1-click rollback." })),
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
      const versionsBtn = el("button", { class: "ghost", text: "Versions / Rollback", onclick: (event) => { event.stopPropagation(); void openWorkflowVersions(workflow); } });
      const runButton = el("button", { text: "Run", onclick: (event) => { event.stopPropagation(); openRun(workflow); } });
      body.append(el("tr", {},
        el("td", { dir: "auto", text: workflow.name }),
        el("td", {}, el("span", { class: "badge", text: workflow.trigger.type })),
        el("td", {}, statusBadge(workflow.status)),
        el("td", { class: "mono", text: `v${workflow.version}` }),
        el("td", { class: "muted", text: fmtTime(workflow.updatedAt) }),
        el("td", {}, el("div", { class: "row" }, toggle, versionsBtn, runButton)),
      ));
    }
    table.append(body);
    panel.append(table);
  }
  main.append(panel);

  const runsPanel = el("div", { class: "card panel", style: "margin-top:14px" });
  runsPanel.append(el("div", { class: "panel-head" }, el("h2", { text: "Recent runs" }), el("span", { class: "muted small", text: "newest first" })));
  if (runs.length === 0) {
    runsPanel.append(el("div", { class: "empty", text: "No runs yet." }));
  } else {
    const table = el("table");
    table.append(el("thead", {}, el("tr", {}, el("th", { text: "Started" }), el("th", { text: "Workflow" }), el("th", { text: "Status" }), el("th", { text: "Steps" }), el("th", { text: "Error" }))));
    const body = el("tbody");
    for (const run of runs.slice(0, 20)) {
      const workflow = state.cache.workflows.find((candidate) => candidate.id === run.workflowId);
      body.append(el("tr", { class: "clickable", onclick: () => { location.hash = `#/workflows/${run.id}`; } },
        el("td", { text: fmtTime(run.startedAt) }),
        el("td", { dir: "auto", text: workflow?.name ?? shortId(run.workflowId) }),
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

async function openWorkflowVersions(workflow) {
  const versions = await api(`/v1/workflows/${workflow.id}/versions`);
  const dialog = el("dialog");
  const body = el("div", { class: "dialog-body" });
  for (const ver of versions) {
    body.append(el("div", { class: "list-item" },
      el("div", { class: "grow" },
        el("div", { class: "mono", text: `v${ver.version} · ${fmtTime(ver.createdAt)}` }),
        el("div", { class: "muted small", text: `${ver.createdBy}${ver.note ? ` · ${ver.note}` : ""}` }),
      ),
      el("button", {
        class: "primary",
        disabled: ver.version === workflow.version,
        text: t("rollback"),
        onclick: async () => {
          try {
            const updated = await api(`/v1/workflows/${workflow.id}/rollback`, {
              method: "POST",
              body: JSON.stringify({ version: ver.version, note: `Studio rollback to v${ver.version}` }),
            });
            dialog.close();
            toast(`Workflow rolled back to v${ver.version} (now v${updated.version}).`);
            route();
          } catch (err) {
            toast(err.message, true);
          }
        },
      }),
    ));
  }
  dialog.append(
    el("div", { class: "dialog-head" }, el("h2", { text: `${workflow.name} · Versions` }), el("button", { class: "ghost", text: "Close", onclick: () => dialog.close() })),
    body,
  );
  document.body.append(dialog);
  dialog.addEventListener("close", () => dialog.remove());
  dialog.showModal();
}

function openTemplates() {
  const dialog = el("dialog");
  const body = el("div", { class: "dialog-body" });
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

  const steps = el("div", { class: "steps" });
  run.steps.forEach((step, index) => {
    steps.append(el("div", { class: "step" },
      el("span", { class: "idx", text: String(index + 1).padStart(2, "0") }),
      el("div", {},
        el("div", { text: `${step.nodeId} · ${step.nodeType}` }),
        el("div", { class: "muted small", text: step.error ? step.error : `${step.attempts} attempt(s)` }),
      ),
      statusBadge(step.status === "succeeded" ? "succeeded" : "failed"),
    ));
  });
  main.append(el("div", { class: "card panel" },
    el("div", { class: "panel-head" }, el("h2", { text: "Steps" })),
    el("div", { class: "panel-body" }, steps),
  ));
}

/* ------------------------------------------------------------------ */
/* automations                                                         */
/* ------------------------------------------------------------------ */

async function renderAutomations() {
  const main = $("#main");
  const tab = state.route[0] ?? "tasks";
  main.append(el("div", { class: "page-head" },
    el("div", {}, el("h1", { dir: "auto", text: t("nav.automations") }), el("p", { class: "sub", text: "Tasks, bookings, contacts and escalations created by voice agents and workflows." })),
  ));

  const tabs = el("div", { class: "tabs" });
  for (const [id, label] of [["tasks", "Tasks"], ["bookings", "Bookings"], ["escalations", "Escalations"], ["contacts", "Contacts"]]) {
    tabs.append(el("button", { class: `tab${tab === id ? " active" : ""}`, text: label, onclick: () => { location.hash = `#/automations/${id}`; } }));
  }
  main.append(tabs);

  if (tab === "tasks") {
    const tasks = await api("/v1/tasks");
    const panel = el("div", { class: "card panel" });
    if (tasks.length === 0) panel.append(el("div", { class: "empty", text: "No tasks yet." }));
    for (const task of tasks) {
      panel.append(el("div", { class: "list-item" },
        el("div", { class: "grow" },
          el("div", { dir: "auto", text: task.title }),
          el("div", { dir: "auto", class: "muted small truncate", text: task.description || "—" }),
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
    if (bookings.length === 0) panel.append(el("div", { class: "empty", text: "No bookings yet." }));
    for (const booking of bookings) {
      panel.append(el("div", { class: "list-item" },
        el("div", { class: "grow" },
          el("div", { dir: "auto", text: `${booking.name} — ${booking.title}` }),
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
    if (escalations.length === 0) panel.append(el("div", { class: "empty", text: "No escalations." }));
    for (const escalation of escalations) {
      panel.append(el("div", { class: "list-item" },
        el("div", { class: "grow" },
          el("div", { dir: "auto", text: escalation.reason }),
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
    if (contacts.length === 0) panel.append(el("div", { class: "empty", text: "No contacts yet." }));
    for (const contact of contacts) {
      panel.append(el("div", { class: "list-item" },
        el("div", { class: "grow" },
          el("div", { dir: "auto", text: contact.name }),
          el("div", { class: "muted small", text: contact.email ?? contact.phone ?? "no contact details" }),
        ),
        ...contact.tags.map((tag) => el("span", { class: "badge", text: tag })),
      ));
    }
    main.append(panel);
  }
}

/* ------------------------------------------------------------------ */
/* telephony & SIP status monitor                                      */
/* ------------------------------------------------------------------ */

async function renderTelephony() {
  const main = $("#main");
  const tab = state.route[0] ?? "numbers";

  main.append(el("div", { class: "page-head" },
    el("div", {},
      el("h1", { dir: "auto", text: t("nav.telephony") }),
      el("p", { class: "sub", text: "Simulated numbers, RFC 3261 SIP/SRTP monitor (OM-T7), and Twilio/Telnyx/Vonage carrier adapters." }),
    ),
  ));

  const tabs = el("div", { class: "tabs" });
  for (const [id, label] of [["numbers", "Numbers"], ["sip", "SIP & SRTP Monitor"], ["sms", "Messages"], ["providers", "Providers"]]) {
    tabs.append(el("button", {
      class: `tab${tab === id ? " active" : ""}`,
      text: label,
      onclick: () => { location.hash = `#/telephony/${id}`; },
    }));
  }
  main.append(tabs);

  if (tab === "numbers") return renderNumbers(main);
  if (tab === "sip") {
    const sipStatus = await api("/v1/telephony/sip/status");
    main.append(buildSipMonitorCard(sipStatus));
    return;
  }
  if (tab === "sms") return renderSms(main);
  return renderProviders(main);
}

function buildSipMonitorCard(sipStatus) {
  const card = el("div", { class: "card panel" });
  card.append(el("div", { class: "panel-head" },
    el("h2", { text: "SIP / SRTP / OM-T7 Monitor" }),
    el("span", { class: "badge good", text: sipStatus.defaultBindHost }),
  ));
  card.append(el("div", { class: "panel-body stack" },
    signalRow("SIP Stack", sipStatus.stack),
    signalRow("Transports", (sipStatus.transports ?? []).join(", ")),
    signalRow("SIP Methods", (sipStatus.methods ?? []).join(", ")),
    signalRow("SRTP Suite", (sipStatus.srtpSuites ?? []).join(", ")),
    signalRow("DTMF", sipStatus.dtmf),
    signalRow("OM-T7 Non-Loopback SRTP", String(sipStatus.omT7Policy?.nonLoopbackRequiresSrtp)),
    signalRow("OM-T7 SDES/Token TLS Guard", String(sipStatus.omT7Policy?.nonLoopbackSdesRequiresSipsTlsOrAttestedTunnel)),
    signalRow("Symmetric RTP Latch", String(sipStatus.omT7Policy?.symmetricRtpLatchAfterAuthenticatedSdp)),
    signalRow("Active Duplex WS / WebRTC", `${sipStatus.activeRealtimeWs ?? 0} WS · ${sipStatus.activeWebRtcSessions ?? 0} WebRTC`),
  ));
  return card;
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
    panel.append(el("div", { class: "empty", text: "No numbers yet." }));
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
        if (!confirm(`Release ${number.e164}?`)) return;
        try {
          await api(`/v1/numbers/${number.id}?confirm=true`, { method: "DELETE" });
          toast(`Released ${number.e164}.`);
          route();
        } catch (error) { toast(error.message, true); }
      }});
      body.append(el("tr", {},
        el("td", { class: "mono", text: number.e164 }),
        el("td", {}, el("span", { class: "badge", text: number.provider })),
        el("td", { dir: "auto", text: number.label }),
        el("td", { class: "muted", text: number.inboundAgentId ? shortId(number.inboundAgentId) : "-" }),
        el("td", {}, statusBadge(number.status)),
        el("td", {}, release),
      ));
    }
    table.append(body);
    panel.append(table);
  }
  main.append(panel);
}

function openNumberSearch() {
  const dialog = el("dialog");
  const provider = el("select");
  for (const [value, label] of [
    ["simulated", "Simulated - free"],
    ["twilio", "Twilio - carrier charges"],
    ["telnyx", "Telnyx - carrier charges"],
    ["signalwire", "SignalWire - carrier charges"],
  ]) {
    provider.append(el("option", { value, text: label }));
  }
  const country = el("input", { value: "US", maxlength: "2", spellcheck: "false" });
  const area = el("input", { placeholder: "415", maxlength: "3", inputmode: "numeric" });
  const results = el("div", { class: "stack", style: "margin-top:12px" });

  const search = el("button", { class: "primary", type: "button", text: "Search" });
  const form = el("div", { class: "dialog-body" });
  form.append(
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
      for (const offer of found.offers) {
        results.append(el("div", { class: "list-item" },
          el("div", { class: "grow" },
            el("div", { class: "mono", text: offer.e164 }),
            el("div", { class: "muted small", text: `${offer.capabilities.join(", ")} · ${offer.costNote}` }),
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
  const agent = el("select");
  agent.append(el("option", { value: "", text: "No inbound agent yet" }));
  for (const candidate of state.cache.agents) agent.append(el("option", { value: candidate.id, text: candidate.name }));
  const confirmBox = el("input", { type: "checkbox" });
  const submit = el("button", { class: "primary", type: "submit", text: "Provision", disabled: true });
  confirmBox.addEventListener("change", () => { submit.disabled = !confirmBox.checked; });

  const form = el("form", { class: "dialog-body" });
  form.append(
    el("p", { class: "mono", text: offer.e164 }),
    el("label", { class: "field" }, el("span", { text: "Label" }), label),
    el("label", { class: "field" }, el("span", { text: "Inbound agent" }), agent),
    el("label", { class: "row" }, confirmBox, el("span", { class: "muted small", text: "I confirm provisioning this number" })),
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
      toast(`Provisioned ${created.number.e164}.`);
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
  panel.append(el("div", { class: "panel-head" }, el("h2", { text: "Messages" })));
  if (messages.length === 0) {
    panel.append(el("div", { class: "empty", text: "No messages yet." }));
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
        el("td", { dir: "auto", class: "truncate", text: message.body }),
        el("td", {}, statusBadge(message.status)),
      ));
    }
    table.append(body);
    panel.append(table);
  }
  main.append(panel);
}

async function renderProviders(main) {
  const providers = await api("/v1/telephony/providers");
  state.cache.providers = providers;

  const panel = el("div", { class: "card panel" });
  panel.append(el("div", { class: "panel-head" }, el("h2", { text: "Carrier adapters" })));
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
}

/* ------------------------------------------------------------------ */
/* settings                                                            */
/* ------------------------------------------------------------------ */

async function renderSettings() {
  const main = $("#main");
  main.append(el("div", { class: "page-head" },
    el("div", {}, el("h1", { dir: "auto", text: t("nav.settings") }), el("p", { class: "sub", text: "Encrypted BYOK credentials and tenant outbound policy." })),
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
    signalRow("Outbound", me.tenant?.settings?.outboundEnabled ? "enabled (consent + OM-T6 enforced)" : "disabled"),
    signalRow("Daily outbound cap", String(me.tenant?.settings?.dailyOutboundCap ?? 0)),
    signalRow("Reach", location.host),
  ));

  const agentsCard = el("div", { class: "card panel" });
  agentsCard.append(el("div", { class: "panel-head" }, el("h2", { text: "Agents" })));
  for (const agent of agents) {
    agentsCard.append(el("div", { class: "list-item" },
      el("div", { class: "grow" },
        el("div", { dir: "auto", text: `${agent.name} · v${agent.version}` }),
        el("div", { class: "muted small", text: `${agent.config.model.provider}/${agent.config.model.model} · voice ${agent.config.voice.provider}` }),
      ),
      statusBadge(agent.status),
    ));
  }

  const credCard = el("div", { class: "card panel" });
  credCard.append(el("div", { class: "panel-head" }, el("h2", { text: "Credentials" }), el("span", { class: "muted small", text: "BYOK, encrypted at rest" })));
  const form = el("form", { class: "panel-body form-grid" });
  const name = el("input", { placeholder: "OPENAI_API_KEY", spellcheck: "false" });
  const value = el("input", { type: "password", placeholder: "value", autocomplete: "off" });
  const submit = el("button", { class: "primary", type: "submit", text: "Save credential" });
  form.append(
    el("label", { class: "field" }, el("span", { text: "Name (UPPER_SNAKE_CASE)" }), name),
    el("label", { class: "field" }, el("span", { text: "Value" }), value),
    el("div", { class: "full row" }, submit),
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

  main.append(el("div", { class: "grid cols-2" }, tenantCard, agentsCard));
  main.append(el("div", { style: "margin-top:14px" }, credCard));
}

/* ------------------------------------------------------------------ */

boot();
