// ========================================================================
// VeritasDataForge Cockpit — interactive logic
// ========================================================================

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

const STATE = {
  matrix: null,
  categories: [],
  isRunning: false,
  sse: null,
  runningCat: null,
  pollTimer: null,
};

// ---------- API helpers ----------
async function api(path, opts = {}) {
  const res = await fetch(path, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok && res.status !== 409) throw new Error(`API ${path} → ${res.status}`);
  return res.json();
}

// ---------- Tabs ----------
function initTabs() {
  $$(".tab").forEach(t => {
    t.addEventListener("click", () => {
      $$(".tab").forEach(x => x.classList.remove("active"));
      $$(".pane").forEach(x => x.classList.remove("active"));
      t.classList.add("active");
      const which = t.dataset.tab;
      $("#pane" + which.charAt(0).toUpperCase() + which.slice(1)).classList.add("active");
      if (which === "outputs") refreshOutputs();
      if (which === "integrity") refreshIntegrity();
    });
  });
}

// ---------- Segmented controls ----------
function initSegs() {
  $$(".seg").forEach(seg => {
    seg.querySelectorAll(".seg-btn").forEach(b => {
      b.addEventListener("click", () => {
        seg.querySelectorAll(".seg-btn").forEach(x => x.classList.remove("active"));
        b.classList.add("active");
        if (seg.id === "segMode") onModeChange(b.dataset.val);
      });
    });
  });
}

function getSegValue(seg) {
  return seg.querySelector(".seg-btn.active")?.dataset.val;
}

function onModeChange(mode) {
  $("#catWrap").style.display = (mode === "category") ? "" : "none";
  $("#tkWrap").style.display = (mode === "ticker") ? "" : "none";
}

// ---------- Load matrix ----------
async function loadMatrix() {
  try {
    const res = await api("/api/matrix");
    if (res.ok) {
      STATE.matrix = res.matrix;
      renderMatrix();
      // Pre-fill the FRED API key field placeholder with the matrix default
      const fredInp = $("#inpFredKey");
      const fredDefault = res.matrix?.global?.fred_api_key_default || "";
      if (fredInp && fredDefault && !fredInp.value) {
        fredInp.placeholder = `default: ${fredDefault.slice(0,8)}...${fredDefault.slice(-4)} (matrix)`;
      }
      await loadCategories();
    }
  } catch (e) {
    setStatus("Failed to load matrix: " + e.message, "fail");
  }
}

async function loadCategories() {
  try {
    const res = await api("/api/categories");
    if (res.ok) {
      STATE.categories = res.categories;
      const sel = $("#selCat");
      sel.innerHTML = STATE.categories
        .map(c => `<option value="${c.id}">${c.id} · ${c.name}</option>`)
        .join("");
      $("#pillCats").textContent = `${STATE.categories.length} categories`;
      const totalItems = STATE.categories.reduce((s, c) => s + c.n_items, 0);
      $("#pillItems").textContent = `${totalItems} items`;
      renderMatrix();
    }
  } catch (e) {
    setStatus("Failed to load categories: " + e.message, "fail");
  }
}

// ---------- Render matrix grid ----------
function renderMatrix() {
  if (!STATE.matrix) return;
  const grid = $("#matrixGrid");
  const cats = STATE.matrix.categories || [];
  const readiness = {};
  STATE.categories.forEach(c => readiness[c.id] = c.ready);

  grid.innerHTML = cats.map((c, idx) => {
    const items = (c.tickers || []).concat(c.indicators || []);
    const ready = readiness[c.id];
    const displayName = c.name_zh || c.name || c.id;
    const subName = c.name_zh && c.name ? `<span style="color:var(--muted); font-size:.85em; font-weight:500"> ${escapeHtml(c.name)}</span>` : '';
    const sources = c.data_sources || [];
    const sourceBadges = sources.length ? `
      <div class="src-badges">
        ${sources.map(s => {
          const lc = s.toLowerCase();
          return `<span class="src-badge src-${lc}"><span class="dot"></span>${escapeHtml(s)}</span>`;
        }).join('')}
      </div>` : '';
    return `
    <div class="cat-card cat-${c.id}" data-cat="${c.id}" data-idx="${idx}">
      <div class="cat-head">
        <div>
          <div class="cat-name">${escapeHtml(displayName)}${subName}</div>
          <div class="cat-id">${escapeHtml(c.id)} · ${escapeHtml(c.output_file)}</div>
        </div>
        <span class="cat-ready ${ready ? 'ok' : ''}">${ready ? 'READY' : 'NO-FETCHER'}</span>
      </div>
      <div class="cat-desc">${escapeHtml(c.description || '')}</div>
      ${sourceBadges}
      <div class="cat-meta">
        <span class="chip b-blue">${items.length} items</span>
        <span class="chip">${escapeHtml(c.update_frequency || '—')}</span>
      </div>
      <div class="cat-actions">
        <button class="btn-mini cat-edit" data-cat="${c.id}">EDIT</button>
        <button class="btn-mini btn-run" data-cat="${c.id}">▶ RUN</button>
      </div>
      <div class="cat-items" data-cat="${c.id}">
        ${renderItemsTable(c)}
      </div>
    </div>
    `;
  }).join("");

  // wire actions
  $$(".cat-card .cat-edit").forEach(b => {
    b.addEventListener("click", e => {
      e.stopPropagation();
      const card = b.closest(".cat-card");
      card.classList.toggle("expanded");
    });
  });
  $$(".cat-card .btn-run").forEach(b => {
    b.addEventListener("click", e => {
      e.stopPropagation();
      runOneCategory(b.dataset.cat);
    });
  });

  // delegate item edit/remove inside cards
  $$(".items-table").forEach(t => {
    t.addEventListener("input", onItemEdit);
    t.querySelectorAll(".rm").forEach(btn => {
      btn.addEventListener("click", e => {
        e.stopPropagation();
        removeItem(btn.dataset.cat, parseInt(btn.dataset.row, 10), btn.dataset.kind);
      });
    });
  });
  // add buttons
  $$(".items-add").forEach(box => {
    box.querySelector(".btn-mini").addEventListener("click", e => {
      const cat = box.dataset.cat;
      const ticker = box.querySelector(".add-tk").value.trim();
      const name = box.querySelector(".add-nm").value.trim();
      if (!ticker) return;
      addItem(cat, ticker, name);
    });
  });
}

function renderItemsTable(c) {
  const isMacroLike = (c.indicators && c.indicators.length > 0);
  const items = isMacroLike ? c.indicators : (c.tickers || []);
  const kind = isMacroLike ? "indicator" : "ticker";
  if (items.length === 0 && !c.universe_source) {
    return `
      <div class="muted" style="padding:6px 0">No items configured.</div>
      ${renderAddRow(c.id, kind)}
    `;
  }
  const idCol = isMacroLike ? "series_id" : "ticker";
  return `
    <table class="items-table">
      <thead><tr><th style="width:34%">${kind.toUpperCase()}</th><th>NAME</th><th style="width:30px"></th></tr></thead>
      <tbody>
      ${items.map((it, i) => `
        <tr data-row="${i}">
          <td><input data-cat="${c.id}" data-row="${i}" data-field="${idCol}" data-kind="${kind}" value="${escapeAttr(it[idCol] || it.ticker || '')}"></td>
          <td><input data-cat="${c.id}" data-row="${i}" data-field="name" data-kind="${kind}" value="${escapeAttr(it.name || '')}"></td>
          <td><button class="rm" data-cat="${c.id}" data-row="${i}" data-kind="${kind}" title="Remove">×</button></td>
        </tr>
      `).join("")}
      </tbody>
    </table>
    ${c.universe_source ? `<div class="muted" style="padding:4px 0">+ external universe: <code>${escapeHtml(c.universe_source)}</code></div>` : ""}
    ${renderAddRow(c.id, kind)}
  `;
}

function renderAddRow(catId, kind) {
  return `
    <div class="items-add" data-cat="${catId}" data-kind="${kind}">
      <input class="add-tk" placeholder="${kind === 'indicator' ? 'series_id' : 'ticker'} (e.g. 2330.TW)">
      <input class="add-nm" placeholder="name (optional)">
      <button class="btn-mini">+ ADD</button>
    </div>
  `;
}

function onItemEdit(e) {
  const inp = e.target;
  if (!inp.dataset.cat) return;
  const cat = STATE.matrix.categories.find(x => x.id === inp.dataset.cat);
  if (!cat) return;
  const list = (inp.dataset.kind === "indicator") ? cat.indicators : cat.tickers;
  const row = list[parseInt(inp.dataset.row, 10)];
  if (!row) return;
  row[inp.dataset.field] = inp.value;
}

function removeItem(catId, row, kind) {
  const cat = STATE.matrix.categories.find(x => x.id === catId);
  if (!cat) return;
  const list = (kind === "indicator") ? cat.indicators : cat.tickers;
  list.splice(row, 1);
  renderMatrix();
  $$(`[data-cat="${catId}"]`).forEach(el => {
    if (el.classList.contains("cat-card")) el.classList.add("expanded");
  });
}

function addItem(catId, ticker, name) {
  const cat = STATE.matrix.categories.find(x => x.id === catId);
  if (!cat) return;
  const isMacro = (cat.indicators && cat.indicators.length > 0) ||
                  (cat.tickers || []).length === 0 && cat.id === "macro";
  if (isMacro || cat.id === "macro" || cat.id === "sentiment" || cat.id === "shipping") {
    if (!cat.indicators) cat.indicators = [];
    cat.indicators.push({ series_id: ticker, name: name || ticker });
  } else {
    if (!cat.tickers) cat.tickers = [];
    cat.tickers.push({ ticker, name: name || ticker });
  }
  renderMatrix();
  $$(`[data-cat="${catId}"]`).forEach(el => {
    if (el.classList.contains("cat-card")) el.classList.add("expanded");
  });
}

// ---------- Save matrix ----------
async function saveMatrix() {
  if (!STATE.matrix) return;
  try {
    setStatus("Saving matrix…", "running");
    const res = await api("/api/matrix", {
      method: "POST",
      body: JSON.stringify({ matrix: STATE.matrix }),
    });
    if (res.ok) {
      setStatus(`Matrix saved (${res.bytes} bytes, backup created)`, "ok");
      await loadCategories();
    } else {
      setStatus("Save failed: " + res.error, "fail");
    }
  } catch (e) {
    setStatus("Save error: " + e.message, "fail");
  }
}

// ---------- Add new category ----------
function openAddCatModal() {
  $("#modalAddCat").classList.add("open");
  $("#newCatId").value = "";
  $("#newCatName").value = "";
  $("#newCatOut").value = "";
  $("#newCatSchema").value = "prices";
  $("#newCatId").focus();
}
function closeAddCatModal() { $("#modalAddCat").classList.remove("open"); }

function confirmAddCat() {
  const id = $("#newCatId").value.trim().toLowerCase().replace(/\s+/g, "_");
  const name = $("#newCatName").value.trim();
  const out = $("#newCatOut").value.trim();
  const schema = $("#newCatSchema").value.trim() || "prices";
  if (!id || !name || !out) { alert("ID, Name, and Output Filename are required"); return; }
  STATE.matrix.categories.push({
    id, name,
    description: "User-defined category",
    output_file: out,
    schema_group: schema,
    primary_key: ["Date", "Ticker"],
    update_frequency: "daily",
    source_pipeline: [{ step: "prices", primary: "yfinance", fallback: [], required: true }],
    tickers: [],
  });
  closeAddCatModal();
  renderMatrix();
  setStatus(`Added category: ${id}. Click SAVE MATRIX to persist.`, "ok");
}

// ---------- Run ----------
async function startRun() {
  const seg = $("#segMode");
  const mode = getSegValue(seg);
  const fredKey = $("#inpFredKey")?.value?.trim();
  const body = {
    mode,
    category: mode === "category" ? $("#selCat").value : undefined,
    ticker: mode === "ticker" ? $("#inpTicker").value.trim() : undefined,
    start: $("#inpStart").value || undefined,
    end: $("#inpEnd").value || undefined,
    output_format: getSegValue($("#segFmt")) || "parquet",
    prod_paths: $("#chkProd").checked,
    full_refresh: $("#chkFull").checked,
    skip_chips: $("#chkSkipChip").checked,
    limit: parseInt($("#inpLimit").value, 10) || undefined,
    fred_api_key: fredKey || undefined,
  };

  if (mode === "category" && !body.category) { alert("Category required"); return; }
  if (mode === "ticker" && !body.ticker) { alert("Ticker required"); return; }

  $("#logBox").textContent = "";
  setRunningUI(true);

  try {
    const res = await api("/api/run", { method: "POST", body: JSON.stringify(body) });
    if (!res.ok) {
      setStatus("Run failed to start: " + res.error, "fail");
      setRunningUI(false);
      return;
    }
    setStatus(`Run started (${mode}${body.category ? ":" + body.category : ""}${body.ticker ? ":" + body.ticker : ""})`, "running");
    startSSE();
    startStatusPoll();
    // visual feedback on cards being run
    if (body.category) {
      $$(`.cat-card[data-cat="${body.category}"]`).forEach(c => c.classList.add("is-running"));
      STATE.runningCat = body.category;
    } else if (mode === "full") {
      $$(".cat-card").forEach(c => c.classList.add("is-running"));
    }
    switchToLogTab();
  } catch (e) {
    setStatus("Run error: " + e.message, "fail");
    setRunningUI(false);
  }
}

function switchToLogTab() {
  $$(".tab").forEach(t => t.classList.remove("active"));
  $$(".pane").forEach(p => p.classList.remove("active"));
  $$(".tab[data-tab='log']")[0]?.classList.add("active");
  $("#paneLog").classList.add("active");
}

async function cancelRun() {
  try {
    await api("/api/run/cancel", { method: "POST" });
    setStatus("Cancel requested. Current category will finish.", "running");
  } catch (e) {
    setStatus("Cancel error: " + e.message, "fail");
  }
}

function setRunningUI(on) {
  STATE.isRunning = on;
  $("#btnRun").disabled = on;
  $("#btnCancel").disabled = !on;
  $("#pillStatus").innerHTML = on
    ? '<span class="dot" style="background:var(--blue);box-shadow:0 0 0 3px rgba(76,120,168,.2)"></span>RUNNING'
    : '<span class="dot"></span>READY';
}

// ---------- SSE log stream ----------
function startSSE() {
  if (STATE.sse) { STATE.sse.close(); STATE.sse = null; }
  STATE.sse = new EventSource("/api/log/stream");
  STATE.sse.onmessage = ev => {
    appendLog(ev.data);
  };
  STATE.sse.onerror = () => {
    // browser will auto-retry, no action needed
  };
}

function appendLog(line) {
  const box = $("#logBox");
  // colorize by level
  let html = escapeHtml(line);
  html = html.replace(/\[(INFO|WARNING|ERROR|DEBUG)\]/g, (m, lvl) => `<span class="lvl-${lvl}">[${lvl}]</span>`);
  html = html.replace(/^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,.\d]*)/, '<span class="ts">$1</span>');
  html = html.replace(/\bOK\b|\bok rows=/g, m => `<span class="ok">${m}</span>`);
  box.innerHTML += html + "\n";
  // scroll bottom
  box.scrollTop = box.scrollHeight;
  // count
  const cnt = (box.textContent.match(/\n/g) || []).length;
  $("#logCount").textContent = `${cnt} lines`;
}

// ---------- Status polling ----------
function startStatusPoll() {
  if (STATE.pollTimer) clearInterval(STATE.pollTimer);
  STATE.pollTimer = setInterval(async () => {
    try {
      const res = await fetch("/api/run/status").then(r => r.json());
      const tNow = new Date().toLocaleTimeString();
      $("#sTime").textContent = tNow;
      if (!res.is_running && STATE.isRunning) {
        setRunningUI(false);
        clearInterval(STATE.pollTimer);
        STATE.pollTimer = null;
        const ok = res.last_result?.ok;
        setStatus(ok ? "Run completed successfully." : `Run failed: ${res.last_result?.error || "unknown"}`, ok ? "ok" : "fail");
        // update card states
        if (res.last_result?.report?.categories) {
          const cats = res.last_result.report.categories;
          $$(".cat-card").forEach(card => {
            card.classList.remove("is-running");
            const cat = card.dataset.cat;
            const r = cats[cat];
            if (r) {
              if (r.ok) card.classList.add("is-done");
              else card.classList.add("is-fail");
            }
          });
        } else {
          $$(".cat-card").forEach(c => c.classList.remove("is-running"));
        }
        await refreshOutputs();
        if (typeof refreshIntegrity === "function") {
          try { await refreshIntegrity(); } catch (e) {}
        }
      }
    } catch (e) {
      // ignore transient errors
    }
  }, 1500);
}

// ---------- Outputs ----------
// ---------- Integrity dashboard ----------
async function refreshIntegrity() {
  try {
    const [matrixRes, outRes, catsRes] = await Promise.all([
      api("/api/matrix"),
      api("/api/outputs"),
      api("/api/categories"),
    ]);
    if (!matrixRes.ok || !outRes.ok) return;
    const cats = matrixRes.matrix.categories || [];
    const outputs = outRes.outputs || [];
    const outByName = {};
    outputs.forEach(o => { outByName[o.name] = o; });
    const ready = {};
    (catsRes.categories || []).forEach(c => { ready[c.id] = c.ready; });

    let n_ok = 0, n_warn = 0, n_empty = 0;
    const now = Date.now();
    const grid = $("#integrityGrid");
    grid.innerHTML = cats.map(c => {
      const out = outByName[c.output_file];
      let status = "empty", statusLabel = "EMPTY";
      let rows = 0, bytes = 0, mtimeStr = "—", ageHours = null;
      if (out) {
        rows = out.rows || 0;
        bytes = out.bytes || 0;
        mtimeStr = out.mtime ? new Date(out.mtime).toLocaleString() : "—";
        if (out.mtime) {
          ageHours = (now - new Date(out.mtime).getTime()) / (3600 * 1000);
        }
        if (rows > 0) {
          if (ageHours !== null && ageHours < 48) {
            status = "ok"; statusLabel = "FRESH";
          } else {
            status = "warn"; statusLabel = "STALE";
          }
        }
      }
      if (!ready[c.id]) {
        status = status === "empty" ? "unknown" : status;
        if (status === "unknown") statusLabel = "NO FETCHER";
      }
      if (status === "ok") n_ok++;
      else if (status === "warn") n_warn++;
      else if (status === "empty") n_empty++;

      const items = (c.tickers || []).concat(c.indicators || []);
      const sources = c.data_sources || [];
      return `
        <div class="int-card ${status}" data-cat="${c.id}">
          <div class="int-head">
            <div>
              <div class="int-title">${escapeHtml(c.name_zh || c.name || c.id)}</div>
              <div class="int-id">${escapeHtml(c.id)}</div>
            </div>
            <span class="int-status">${statusLabel}</span>
          </div>
          <div class="int-desc">${escapeHtml(c.description || '')}</div>
          <div class="int-metrics">
            <div class="int-metric">
              <span class="int-metric-label">Rows</span>
              <span class="int-metric-value">${rows ? rows.toLocaleString() : "—"}</span>
            </div>
            <div class="int-metric">
              <span class="int-metric-label">Size</span>
              <span class="int-metric-value">${bytes ? fmtBytes(bytes) : "—"}</span>
            </div>
            <div class="int-metric">
              <span class="int-metric-label">Items</span>
              <span class="int-metric-value">${items.length}</span>
            </div>
          </div>
          <div class="src-badges">
            ${sources.map(s => {
              const lc = s.toLowerCase();
              return `<span class="src-badge src-${lc}"><span class="dot"></span>${escapeHtml(s)}</span>`;
            }).join('')}
          </div>
          <div class="int-file">${escapeHtml(c.output_file)}</div>
          <div class="int-metric">
            <span class="int-metric-label">Last Updated</span>
            <span class="int-metric-value" style="font-size:11px;">${mtimeStr}</span>
          </div>
        </div>
      `;
    }).join("");

    // Summary numbers
    $("#intTotal").textContent = cats.length;
    $("#intOk").textContent = n_ok;
    $("#intWarn").textContent = n_warn;
    $("#intEmpty").textContent = n_empty;
  } catch (e) {
    setStatus("Integrity refresh failed: " + e.message, "fail");
  }
}

async function refreshOutputs() {
  try {
    const res = await api("/api/outputs");
    if (!res.ok) return;
    const list = $("#outList");
    if (res.outputs.length === 0) {
      list.innerHTML = `<div class="out-empty">No output files yet. Run a category to generate.</div>`;
      $("#pillOutputs").textContent = "0 outputs";
      return;
    }
    $("#pillOutputs").textContent = `${res.outputs.length} outputs`;
    list.innerHTML = res.outputs.map(o => `
      <div class="out-row">
        <div class="out-name">${escapeHtml(o.name)}</div>
        <div class="out-stat">${o.rows != null ? o.rows.toLocaleString() : "—"} rows</div>
        <div class="out-stat">${fmtBytes(o.bytes)}</div>
        <div class="out-stat">${new Date(o.mtime).toLocaleString()}</div>
      </div>
    `).join("");
  } catch (e) {
    setStatus("Outputs refresh failed: " + e.message, "fail");
  }
}

// ---------- Status bar ----------
function setStatus(text, kind = "ok") {
  $("#sText").textContent = text;
  const icon = $("#sIcon");
  icon.className = "s-icon " + kind;
  icon.textContent = kind === "running" ? "◐" : "●";
}

// ---------- Helpers ----------
function escapeHtml(s) {
  if (s == null) return "";
  return String(s).replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
}
function escapeAttr(s) {
  if (s == null) return "";
  return String(s).replace(/"/g, "&quot;");
}
function fmtBytes(n) {
  if (n < 1024) return n + " B";
  if (n < 1024*1024) return (n/1024).toFixed(1) + " KB";
  if (n < 1024*1024*1024) return (n/1024/1024).toFixed(2) + " MB";
  return (n/1024/1024/1024).toFixed(2) + " GB";
}

// ---------- Health ----------
async function checkHealth() {
  try {
    const res = await api("/api/health");
    setStatus(`Healthy · API ${res.version}`, "ok");
  } catch (e) {
    setStatus("Health check failed: " + e.message, "fail");
  }
}

// quick-run a single category (called from card)
async function runOneCategory(catId) {
  // set the UI controls to match
  $$("#segMode .seg-btn").forEach(b => b.classList.toggle("active", b.dataset.val === "category"));
  onModeChange("category");
  $("#selCat").value = catId;
  startRun();
}

// ---------- Init ----------
window.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initSegs();
  loadMatrix();
  refreshOutputs();

  // wire control buttons
  $("#btnRun").addEventListener("click", startRun);
  $("#btnCancel").addEventListener("click", cancelRun);
  $("#btnHealth").addEventListener("click", checkHealth);
  $("#btnReloadMatrix").addEventListener("click", () => { loadMatrix(); refreshOutputs(); });
  $("#btnSaveMatrix").addEventListener("click", saveMatrix);
  $("#btnAddCat").addEventListener("click", openAddCatModal);
  $("#newCatCancel").addEventListener("click", closeAddCatModal);
  $("#newCatConfirm").addEventListener("click", confirmAddCat);
  $("#btnRefreshOut").addEventListener("click", refreshOutputs);
  const intBtn = $("#btnRefreshIntegrity");
  if (intBtn) intBtn.addEventListener("click", refreshIntegrity);
  $("#btnClearLog").addEventListener("click", () => { $("#logBox").innerHTML = ""; $("#logCount").textContent = "0 lines"; });

  // default dates: last 30 days
  const today = new Date();
  const past = new Date(); past.setDate(past.getDate() - 30);
  $("#inpStart").value = past.toISOString().slice(0,10);
  $("#inpEnd").value = today.toISOString().slice(0,10);

  // status time tick
  setInterval(() => { $("#sTime").textContent = new Date().toLocaleTimeString(); }, 1000);
});
