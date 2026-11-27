// SPDX-License-Identifier: Apache-2.0
// Klaint Studio SPA Controller - Bilingual RTL/LTR + SessionStorage Auth + Live Takeover + 'Why' Panel
(function () {
  "use strict";

  const I18N = {
    en: {
      dir: "ltr",
      langBtn: "العربية (RTL)",
      overview: "Overview",
      inbox: "Conversations & Inbox",
      procedures: "Procedures (SOPs)",
      knowledge: "Knowledge (Cited RAG)",
      approvals: "Approvals Queue",
      audit: "Audit & Simulation",
      whyTitle: "Why Explainability Panel",
      takeOver: "Take over conversation",
      returnAi: "Return to AI",
      pausedBanner: "AI paused — you own this conversation",
      verifyChain: "Verify SHA-256 Audit Chain",
      runSim: "Run tau2 Simulation Suite",
    },
    ar: {
      dir: "rtl",
      langBtn: "English (LTR)",
      overview: "نظرة عامة",
      inbox: "المحادثات وصندوق الوارد",
      procedures: "الإجراءات والسياسات",
      knowledge: "قاعدة المعرفة الموثقة",
      approvals: "طابور الموافقات",
      audit: "سجل التدقيق والمحاكاة",
      whyTitle: "لوحة تفسير القرار (لماذا؟)",
      takeOver: "استلام المحادثة فوراً",
      returnAi: "إعادة المحادثة للوكيل الذكي",
      pausedBanner: "تم إيقاف الذكاء الاصطناعي — أنت تملك هذه المحادثة الآن",
      verifyChain: "التحقق من سلسلة التجزئة SHA-256",
      runSim: "تشغيل حزمة محاكاة tau2",
    },
  };

  let currentLang = "en";
  let apiKey = sessionStorage.getItem("klaint_api_key") || "";
  let operatorId = sessionStorage.getItem("klaint_operator_id") || "";
  let operatorToken = sessionStorage.getItem("klaint_operator_token") || "";

  function esc(raw) {
    return String(raw === null || raw === undefined ? "" : raw)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  function showError(err) {
    const banner = document.getElementById("studio-error-banner");
    if (banner) {
      banner.hidden = false;
      banner.textContent = err && err.message ? err.message : String(err);
    }
  }

  function clearError() {
    const banner = document.getElementById("studio-error-banner");
    if (banner) {
      banner.hidden = true;
      banner.textContent = "";
    }
  }

  function updateAuthBadge() {
    const badge = document.getElementById("auth-operator-badge");
    if (badge) {
      badge.textContent = operatorToken && operatorId ? ("operator:" + operatorId) : "signed-out";
    }
    const keyInput = document.getElementById("auth-api-key-input");
    const opInput = document.getElementById("auth-operator-id-input");
    if (keyInput && apiKey && !keyInput.value) keyInput.value = apiKey;
    if (opInput && operatorId && !opInput.value) opInput.value = operatorId;
  }

  function headers() {
    const h = { "Content-Type": "application/json" };
    if (apiKey) {
      h["X-Klaint-Api-Key"] = apiKey;
    }
    if (operatorToken) {
      h["X-Klaint-Operator-Token"] = operatorToken;
    }
    return h;
  }

  async function apiFetch(path, options) {
    const opts = Object.assign({ headers: headers() }, options || {});
    const res = await fetch(path, opts);
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.error || ("HTTP " + res.status));
    }
    clearError();
    return data;
  }

  function downloadBlob(filename, content, mimeType) {
    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  }

  function applyLocale() {
    const dict = I18N[currentLang];
    document.documentElement.lang = currentLang;
    document.documentElement.dir = dict.dir;
    const toggle = document.getElementById("lang-toggle-btn");
    if (toggle) toggle.textContent = dict.langBtn;
    document.querySelectorAll("[data-i18n]").forEach(function (el) {
      const k = el.getAttribute("data-i18n");
      if (k && dict[k]) el.textContent = dict[k];
    });
  }

  async function signInOperator(nextKey, nextOperatorId) {
    apiKey = String(nextKey || "").trim();
    operatorId = String(nextOperatorId || "").trim();
    const login = await apiFetch("/api/v1/auth/operator-login", {
      method: "POST",
      body: JSON.stringify({ operator_id: operatorId, role: "supervisor" }),
    });
    operatorToken = login.operator_token || "";
    sessionStorage.setItem("klaint_api_key", apiKey);
    sessionStorage.setItem("klaint_operator_id", operatorId);
    sessionStorage.setItem("klaint_operator_token", operatorToken);
    updateAuthBadge();
  }

  function resolveVerdictChipClass(why) {
    const decision = why && why.policy_verdict && why.policy_verdict.enforced_decision;
    if (decision === "DENY" || (why && why.resolution_status === "denied")) {
      return "chip chip-deny";
    }
    if (
      decision === "ASK" ||
      (why && (why.resolution_status === "awaiting_approval" || why.resolution_status === "escalated"))
    ) {
      return "chip chip-ask";
    }
    return "chip chip-allow";
  }

  async function loadOverview() {
    try {
      const data = await apiFetch("/api/v1/overview");
      document.getElementById("m-fcr").textContent = (data.fcr_rate * 100).toFixed(1) + "%";
      document.getElementById("m-recontact").textContent = (data.recontact_rate * 100).toFixed(1) + "%";
      document.getElementById("m-compliance").textContent = (data.policy_compliance_rate * 100).toFixed(1) + "%";
      document.getElementById("m-latency").textContent = data.latency_ms.p50 + " / " + data.latency_ms.p95 + " ms";
      const tbody = document.getElementById("lang-breakdown-body");
      tbody.innerHTML = "";
      Object.keys(data.by_language || {}).forEach(function (lang) {
        const row = data.by_language[lang];
        const tr = document.createElement("tr");
        tr.innerHTML =
          '<td><span class="ltr-code">' + esc(lang) + "</span></td>" +
          "<td>" + esc(row.conversations) + "</td>" +
          "<td>" + esc(row.turns) + "</td>" +
          "<td>" + esc((row.fcr_rate * 100).toFixed(1)) + "%</td>" +
          "<td>" + esc(row.latency_ms_p95) + " ms</td>";
        tbody.appendChild(tr);
      });
    } catch (err) {
      showError(err);
    }
  }

  function renderWhyPanel(why) {
    const container = document.getElementById("why-panel-content");
    if (!container) return;
    if (!why) {
      container.textContent = "Select a conversation turn to inspect its 8-stage deterministic trace.";
      return;
    }
    const chipWord = (why.verdict_chip && why.verdict_chip[currentLang]) || "Informational";
    const chipClass = resolveVerdictChipClass(why);
    const stagesHtml = (why.stages || [])
      .map(function (st) {
        return "<li><strong>" + esc(st.stage) + ":</strong> " + esc(st.summary) + " (" + esc(st.duration_ms) + " ms)</li>";
      })
      .join("");
    const citesHtml = (why.citations || [])
      .map(function (c) {
        return '<li><span class="ltr-code">' + esc(c.chunk_id) + "</span> — " + esc(c.quote) + "</li>";
      })
      .join("");
    container.innerHTML =
      '<p><strong>Summary:</strong> <span dir="auto">' + esc(why.plain_summary || "") + "</span></p>" +
      '<p><span class="' + esc(chipClass) + '">' + esc(chipWord) + "</span> " +
      'Epoch: <span class="ltr-code">' + esc(why.ownership_epoch) + "</span> " +
      'RAG: <span class="ltr-code">' + esc(why.rag_status) + "</span></p>" +
      "<details open><summary><strong>Details (8-Stage Trace, SOP Rules, Capability &amp; Receipts)</strong></summary>" +
      '<p>Matched SOP Rules: <span class="ltr-code">' + esc((why.matched_rules || []).join(", ") || "none") + "</span></p>" +
      '<p>Capability Digest: <span class="ltr-code">' + esc(why.capability_args_digest || "n/a") + "</span></p>" +
      '<p>Ledger Receipts: <span class="ltr-code">' + esc((why.receipt_ids || []).join(", ") || "none") + "</span></p>" +
      "<ol>" + stagesHtml + "</ol>" +
      (citesHtml ? "<ul>" + citesHtml + "</ul>" : "") +
      "</details>";
  }

  async function loadInbox() {
    try {
      const data = await apiFetch("/api/v1/conversations");
      const list = document.getElementById("conversations-list");
      list.innerHTML = "";
      (data.conversations || []).forEach(function (conv) {
        const div = document.createElement("div");
        div.className = "panel";
        const isHuman = conv.owner_kind === "human_owned";
        const banner = isHuman
          ? '<div class="takeover-banner">' + esc(I18N[currentLang].pausedBanner) + "</div>"
          : "";
        div.innerHTML =
          banner +
          "<div><strong>" + esc(conv.customer_id) + '</strong> · <span class="ltr-code">' +
          esc(conv.conversation_id) + '</span> · Epoch <span class="ltr-code">' + esc(conv.ownership_epoch) + "</span> · Owner: <strong>" +
          esc(conv.owner_kind) + "</strong></div>";

        const actionBtn = document.createElement("button");
        actionBtn.className = "btn btn-primary";
        actionBtn.textContent = isHuman ? I18N[currentLang].returnAi : I18N[currentLang].takeOver;
        actionBtn.onclick = async function () {
          try {
            const endpoint = isHuman ? "/return-to-ai" : "/takeover";
            await apiFetch("/api/v1/conversations/" + encodeURIComponent(conv.conversation_id) + endpoint, {
              method: "POST",
              body: JSON.stringify({}),
            });
            await loadInbox();
          } catch (err) {
            showError(err);
          }
        };
        div.appendChild(actionBtn);

        (conv.turns || []).forEach(function (turn) {
          const tDiv = document.createElement("div");
          tDiv.innerHTML =
            '<div dir="auto"><em>Customer:</em> ' + esc(turn.customer_text) + "</div>" +
            '<div dir="auto"><strong>Klaint:</strong> ' + esc(turn.assistant_text) + "</div>";
          const whyBtn = document.createElement("button");
          whyBtn.className = "btn";
          whyBtn.textContent = "Why?";
          whyBtn.onclick = function () {
            renderWhyPanel(turn.why);
          };
          tDiv.appendChild(whyBtn);
          div.appendChild(tDiv);
        });
        list.appendChild(div);
      });
    } catch (err) {
      showError(err);
    }
  }

  async function loadProcedures() {
    try {
      const data = await apiFetch("/api/v1/procedures");
      const tbody = document.getElementById("procedures-body");
      tbody.innerHTML = "";
      (data.versions || []).forEach(function (v) {
        const tr = document.createElement("tr");
        tr.innerHTML =
          '<td><span class="ltr-code">' + esc(v.sop_id) + " v" + esc(v.version_num) + "</span></td>" +
          "<td>" + esc(v.domain) + "</td>" +
          "<td>" + esc(v.status) + "</td>" +
          "<td>" + esc(v.author_id) + " / " + esc(v.approver_id || "—") + "</td>" +
          "<td></td>";
        const cell = tr.lastElementChild;
        if (cell && v.status === "draft") {
          const appBtn = document.createElement("button");
          appBtn.className = "btn btn-primary";
          appBtn.textContent = "4-Eyes Approve";
          appBtn.onclick = async function () {
            try {
              await apiFetch("/api/v1/procedures/approve", {
                method: "POST",
                body: JSON.stringify({ sop_id: v.sop_id, version_num: v.version_num }),
              });
              await loadProcedures();
            } catch (err) {
              showError(err);
            }
          };
          cell.appendChild(appBtn);
        } else if (cell && v.status === "archived" && v.approver_id) {
          const rbBtn = document.createElement("button");
          rbBtn.className = "btn";
          rbBtn.textContent = "1-Click Rollback";
          rbBtn.onclick = async function () {
            try {
              await apiFetch("/api/v1/procedures/rollback", {
                method: "POST",
                body: JSON.stringify({ sop_id: v.sop_id, target_version_num: v.version_num }),
              });
              await loadProcedures();
            } catch (err) {
              showError(err);
            }
          };
          cell.appendChild(rbBtn);
        }
        tbody.appendChild(tr);
      });
    } catch (err) {
      showError(err);
    }
  }

  async function loadKnowledge() {
    try {
      const data = await apiFetch("/api/v1/knowledge");
      const list = document.getElementById("knowledge-docs-list");
      list.innerHTML = (data.documents || [])
        .map(function (d) {
          return "<li><strong>" + esc(d.title) + '</strong> (<span class="ltr-code">' + esc(d.doc_id) + "</span>) — ACL: " + esc((d.acl_tags || []).join(", ")) + "</li>";
        })
        .join("");
    } catch (err) {
      showError(err);
    }
  }

  async function loadApprovals() {
    try {
      const data = await apiFetch("/api/v1/approvals");
      const list = document.getElementById("approvals-list");
      list.innerHTML = "";
      (data.approvals || []).forEach(function (item) {
        const card = document.createElement("div");
        card.className = "panel";
        card.innerHTML =
          '<div><span class="ltr-code">' + esc(item.approval_id) + "</span> · <strong>" + esc(item.tool) +
          "</strong> · Status: <strong>" + esc(item.status) + "</strong></div>" +
          "<div>Customer: " + esc(item.customer_id) + " — " + esc(item.reason) + "</div>";
        if (item.status === "pending") {
          ["Approve", "Deny"].forEach(function (label) {
            const btn = document.createElement("button");
            btn.className = label === "Approve" ? "btn btn-primary" : "btn btn-danger";
            btn.textContent = label;
            btn.onclick = async function () {
              try {
                await apiFetch("/api/v1/approvals/" + encodeURIComponent(item.approval_id) + "/decide", {
                  method: "POST",
                  body: JSON.stringify({ approve: label === "Approve", note: "Studio decision" }),
                });
                await loadApprovals();
              } catch (err) {
                showError(err);
              }
            };
            card.appendChild(btn);
          });
        }
        list.appendChild(card);
      });
    } catch (err) {
      showError(err);
    }
  }

  async function loadAudit() {
    try {
      const data = await apiFetch("/api/v1/audit");
      const tbody = document.getElementById("audit-body");
      tbody.innerHTML = (data.events || [])
        .map(function (ev) {
          return (
            "<tr><td>" + esc(ev.seq) + "</td><td>" + esc(ev.event_kind) + "</td><td>" + esc(ev.actor) +
            '</td><td><span class="ltr-code">' + esc(String(ev.entry_digest || "").slice(0, 22)) + "…</span></td></tr>"
          );
        })
        .join("");
    } catch (err) {
      showError(err);
    }
  }

  function bindEvents() {
    const authForm = document.getElementById("studio-auth-form");
    if (authForm) {
      authForm.addEventListener("submit", async function (ev) {
        ev.preventDefault();
        try {
          const nextKey = document.getElementById("auth-api-key-input").value;
          const nextOp = document.getElementById("auth-operator-id-input").value;
          await signInOperator(nextKey, nextOp);
          await loadOverview();
        } catch (err) {
          showError(err);
        }
      });
    }

    const toggle = document.getElementById("lang-toggle-btn");
    if (toggle) {
      toggle.addEventListener("click", function () {
        currentLang = currentLang === "en" ? "ar" : "en";
        applyLocale();
      });
    }

    document.querySelectorAll(".nav-btn").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll(".nav-btn").forEach(function (b) {
          b.classList.remove("active");
        });
        btn.classList.add("active");
        const target = btn.getAttribute("data-view");
        document.querySelectorAll(".view-section").forEach(function (sec) {
          sec.hidden = sec.id !== "view-" + target;
        });
        if (target === "overview") loadOverview();
        if (target === "inbox") loadInbox();
        if (target === "procedures") loadProcedures();
        if (target === "knowledge") loadKnowledge();
        if (target === "approvals") loadApprovals();
        if (target === "audit") loadAudit();
      });
    });

    const sopForm = document.getElementById("create-sop-draft-form");
    if (sopForm) {
      sopForm.addEventListener("submit", async function (ev) {
        ev.preventDefault();
        try {
          const domain = document.getElementById("sop-domain-select").value;
          const title = document.getElementById("sop-title-input").value;
          const nlText = document.getElementById("sop-nl-input").value;
          await apiFetch("/api/v1/procedures/drafts", {
            method: "POST",
            body: JSON.stringify({ domain: domain, title: title, natural_language_text: nlText }),
          });
          document.getElementById("sop-title-input").value = "";
          document.getElementById("sop-nl-input").value = "";
          await loadProcedures();
        } catch (err) {
          showError(err);
        }
      });
    }

    const ragForm = document.getElementById("rag-search-form");
    if (ragForm) {
      ragForm.addEventListener("submit", async function (ev) {
        ev.preventDefault();
        try {
          const q = document.getElementById("rag-query-input").value;
          const res = await apiFetch("/api/v1/knowledge/search", {
            method: "POST",
            body: JSON.stringify({ query: q }),
          });
          document.getElementById("rag-search-output").innerHTML =
            '<p>Epistemic Status: <span class="ltr-code">' + esc(res.status) + "</span></p>" +
            (res.citations || [])
              .map(function (c) {
                return '<blockquote dir="auto"><span class="ltr-code">' + esc(c.chunk_id) + "</span>: " + esc(c.quote) + "</blockquote>";
              })
              .join("");
        } catch (err) {
          showError(err);
        }
      });
    }

    const verifyBtn = document.getElementById("verify-audit-btn");
    if (verifyBtn) {
      verifyBtn.addEventListener("click", async function () {
        try {
          const v = await apiFetch("/api/v1/audit/verify");
          document.getElementById("audit-verify-status").textContent =
            v.valid
              ? ("VALID (" + v.total_entries + " entries, head " + String(v.head_digest || "").slice(0, 20) + "…)")
              : ("TAMPERED at seq " + v.broken_at_seq);
        } catch (err) {
          showError(err);
        }
      });
    }

    const exportJsonBtn = document.getElementById("export-audit-json-btn");
    if (exportJsonBtn) {
      exportJsonBtn.addEventListener("click", async function () {
        try {
          const data = await apiFetch("/api/v1/audit");
          downloadBlob("klaint_audit_log.json", JSON.stringify(data.events || [], null, 2), "application/json");
        } catch (err) {
          showError(err);
        }
      });
    }

    const exportCsvBtn = document.getElementById("export-audit-csv-btn");
    if (exportCsvBtn) {
      exportCsvBtn.addEventListener("click", async function () {
        try {
          const res = await fetch("/api/v1/audit?format=csv", { headers: headers() });
          const csvText = await res.text();
          if (!res.ok) {
            throw new Error("CSV export failed: HTTP " + res.status);
          }
          downloadBlob("klaint_audit_log.csv", csvText, "text/csv;charset=utf-8");
        } catch (err) {
          showError(err);
        }
      });
    }

    const simBtn = document.getElementById("run-sim-btn");
    if (simBtn) {
      simBtn.addEventListener("click", async function () {
        try {
          const res = await apiFetch("/api/v1/simulation/run", { method: "POST", body: "{}" });
          document.getElementById("sim-run-status").textContent =
            "tau2 DB-Hash Suite: " + res.passed_scenarios + "/" + res.total_scenarios + " passed (" + res.simulator_model + ")";
        } catch (err) {
          showError(err);
        }
      });
    }
  }

  document.addEventListener("DOMContentLoaded", async function () {
    if (!document.getElementById("studio-app")) return;
    applyLocale();
    updateAuthBadge();
    bindEvents();
    if (apiKey && operatorToken) {
      await loadOverview();
    }
  });
})();
