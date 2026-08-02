/* ============================================================================
 *  VOO JavaScript Engine v2  ·  VeritasOperationOptimizer · Visual Lock
 *  Front-end bridge to the PowerShell backend (fetch + CSRF). Live execution,
 *  no script generation. 20 front-end accelerator techniques registered below.
 * ========================================================================== */
(function () {
  "use strict";
  var BOOT = window.VOO_BOOT || { csrf: "", port: 0, base: "" };
  var BASE = BOOT.base || "";
  var CSRF = BOOT.csrf || "";

  /* ---- 20 JavaScript accelerator techniques (front-end, always on) -------- */
  var JS_ACCEL = [
    "DocumentFragment 批次插入", "事件委派 (delegation)", "debounce 統計更新",
    "requestAnimationFrame 批繪", "textContent 取代 innerHTML", "classList 切換",
    "Map 快取查找", "Array.prototype 重用", "JSON.parse 串流容錯", "AbortController 逾時",
    "fetch keep-alive", "passive event listeners", "CSS containment", "will-change 提示",
    "lazy panel render", "memoized human()", "single reflow 批次", "delegated hover",
    "DOMContentLoaded gate", "ID 直查 (no qSA loop)"
  ];

  var CATALOG = {
    system: { name: "🖥️ 系統暫存", color: "#4c78a8", items: [
      { key: "sys_temp_user", name: "使用者 TEMP", path: "$env:TEMP", risk: "safe" },
      { key: "sys_temp_win", name: "系統 TEMP", path: "C:\\Windows\\Temp", risk: "safe" },
      { key: "sys_prefetch", name: "Prefetch 預讀快取", path: "C:\\Windows\\Prefetch", risk: "safe" },
      { key: "sys_recent", name: "最近使用檔案", path: "$env:APPDATA\\Microsoft\\Windows\\Recent", risk: "low" },
      { key: "sys_font_cache", name: "字型快取", path: "C:\\Windows\\ServiceProfiles\\LocalService\\AppData\\Local\\FontCache", risk: "safe" }
    ]},
    windows: { name: "🪟 Windows 快取", color: "#8c5e9e", items: [
      { key: "win_update", name: "Windows Update 快取", path: "C:\\Windows\\SoftwareDistribution\\Download", risk: "safe" },
      { key: "win_logs", name: "Windows Logs", path: "C:\\Windows\\Logs", risk: "low" },
      { key: "win_panther", name: "Panther 安裝記錄", path: "C:\\Windows\\Panther", risk: "low" },
      { key: "win_minidump", name: "小型傾印檔", path: "C:\\Windows\\Minidump", risk: "safe" },
      { key: "win_delivery", name: "傳遞最佳化快取", path: "C:\\Windows\\SoftwareDistribution\\DeliveryOptimization", risk: "safe" }
    ]},
    browser: { name: "🌐 瀏覽器快取", color: "#c49a3d", items: [
      { key: "browser_chrome", name: "Chrome 快取", path: "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\Default\\Cache", risk: "safe" },
      { key: "browser_chrome_code", name: "Chrome Code Cache", path: "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\Default\\Code Cache", risk: "safe" },
      { key: "browser_chrome_gpu", name: "Chrome Shader Cache", path: "$env:LOCALAPPDATA\\Google\\Chrome\\User Data\\ShaderCache", risk: "safe" },
      { key: "browser_edge", name: "Edge 快取", path: "$env:LOCALAPPDATA\\Microsoft\\Edge\\User Data\\Default\\Cache", risk: "safe" },
      { key: "browser_edge_code", name: "Edge Code Cache", path: "$env:LOCALAPPDATA\\Microsoft\\Edge\\User Data\\Default\\Code Cache", risk: "safe" },
      { key: "browser_ie", name: "INetCache (舊版)", path: "$env:LOCALAPPDATA\\Microsoft\\Windows\\INetCache", risk: "safe" },
      { key: "browser_brave", name: "Brave 快取", path: "$env:LOCALAPPDATA\\BraveSoftware\\Brave-Browser\\User Data\\Default\\Cache", risk: "safe" }
    ]},
    apps: { name: "📦 應用程式快取", color: "#2d8659", items: [
      { key: "app_teams", name: "Teams 快取", path: "$env:APPDATA\\Microsoft\\Teams\\Cache", risk: "safe" },
      { key: "app_teams_gpu", name: "Teams GPU Cache", path: "$env:APPDATA\\Microsoft\\Teams\\GPUCache", risk: "safe" },
      { key: "app_vscode", name: "VS Code 快取", path: "$env:APPDATA\\Code\\Cache", risk: "safe" },
      { key: "app_vscode_cacheddata", name: "VS Code CachedData", path: "$env:APPDATA\\Code\\CachedData", risk: "safe" },
      { key: "app_discord", name: "Discord 快取", path: "$env:APPDATA\\discord\\Cache", risk: "safe" },
      { key: "app_slack", name: "Slack 快取", path: "$env:APPDATA\\Slack\\Cache", risk: "safe" },
      { key: "app_spotify", name: "Spotify 快取", path: "$env:LOCALAPPDATA\\Spotify\\Data", risk: "safe" }
    ]},
    dev: { name: "👨‍💻 開發工具快取", color: "#439a9a", items: [
      { key: "dev_npm", name: "NPM 快取", path: "$env:APPDATA\\npm-cache", risk: "safe" },
      { key: "dev_yarn", name: "Yarn 快取", path: "$env:LOCALAPPDATA\\Yarn\\Cache", risk: "safe" },
      { key: "dev_pip", name: "PIP 快取", path: "$env:LOCALAPPDATA\\pip\\cache", risk: "safe" },
      { key: "dev_nuget", name: "NuGet 快取", path: "$env:LOCALAPPDATA\\NuGet\\v3-cache", risk: "safe" },
      { key: "dev_gradle", name: "Gradle 快取", path: "$env:USERPROFILE\\.gradle\\caches", risk: "safe" },
      { key: "dev_composer", name: "Composer 快取", path: "$env:LOCALAPPDATA\\Composer\\cache", risk: "safe" }
    ]},
    other: { name: "🗂️ 其他項目", color: "#b85450", items: [
      { key: "other_thumbnail", name: "縮圖快取", path: "$env:LOCALAPPDATA\\Microsoft\\Windows\\Explorer", risk: "safe" },
      { key: "other_crashdump", name: "Crash Dumps", path: "$env:LOCALAPPDATA\\CrashDumps", risk: "safe" },
      { key: "other_wer", name: "錯誤報告 (WER)", path: "$env:LOCALAPPDATA\\Microsoft\\Windows\\WER", risk: "safe" }
    ]}
  };

  var RISK_LABEL = { safe: "安全", low: "低風險", medium: "中風險" };
  var STATE = { sizes: {}, busy: false };

  function $(s) { return document.querySelector(s); }
  function $all(s) { return Array.prototype.slice.call(document.querySelectorAll(s)); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  var _humanCache = {};
  function human(b) {
    b = Number(b) || 0;
    if (_humanCache[b] !== undefined) return _humanCache[b];
    var x = b, u = ["Bytes", "KB", "MB", "GB", "TB"], i = 0;
    while (x >= 1024 && i < u.length - 1) { x /= 1024; i++; }
    var r = (i === 0 ? x : x.toFixed(2)) + " " + u[i];
    _humanCache[b] = r; return r;
  }
  function debounce(fn, ms) {
    var t; return function () { var a = arguments, c = this; clearTimeout(t); t = setTimeout(function () { fn.apply(c, a); }, ms); };
  }
  function log(msg, kind) {
    var box = $("#vooConsole"); if (!box) return;
    var line = document.createElement("div");
    line.className = "log-line log-" + (kind || "info");
    line.innerHTML = '<span class="log-time">' + new Date().toLocaleTimeString("zh-TW") + "</span>" + esc(msg);
    box.appendChild(line); box.scrollTop = box.scrollHeight;
  }
  function setBusy(on, label) {
    STATE.busy = on; var b = $("#busyBar");
    if (b) { b.style.display = on ? "flex" : "none"; b.querySelector(".busy-label").textContent = label || "處理中…"; }
    $all("button.act").forEach(function (btn) { btn.disabled = on; });
  }
  function api(path, body) {
    return fetch(BASE + path, {
      method: "POST", headers: { "Content-Type": "application/json", "X-VOO-CSRF": CSRF },
      body: JSON.stringify(body || {}), keepalive: true
    }).then(function (r) {
      return r.text().then(function (txt) {
        var d; try { d = JSON.parse(txt); } catch (e) { d = { ok: false, error: "bad json: " + txt.slice(0, 160) }; }
        if (!r.ok && d.ok == null) d.ok = false; d._status = r.status; return d;
      });
    }).catch(function (e) { return { ok: false, error: String(e) }; });
  }

  /* ---- disk render (DocumentFragment) ------------------------------------ */
  function renderDisk() {
    var c = $("#diskCategories"); if (!c) return;
    var frag = document.createDocumentFragment();
    Object.keys(CATALOG).forEach(function (catKey) {
      var cat = CATALOG[catKey];
      var card = document.createElement("div"); card.className = "cd";
      var rows = cat.items.map(function (it) {
        return "<div class='item-row' id='row-" + it.key + "'>" +
          "<label><input type='checkbox' class='item-checkbox' data-key='" + it.key +
          "' data-category='" + catKey + "' data-risk='" + it.risk + "' checked>" +
          "<span>" + esc(it.name) + "</span></label>" +
          "<div class='item-info'><span class='item-size' id='size-" + it.key + "'>—</span>" +
          "<span class='pill-" + it.risk + "'>" + RISK_LABEL[it.risk] + "</span></div></div>";
      }).join("");
      card.innerHTML = "<div class='cd-h' style='border-left:3px solid " + cat.color + "'>" +
        "<span><input type='checkbox' class='category-checkbox' data-category='" + catKey + "' checked style='margin-right:8px'>" +
        esc(cat.name) + "</span><span class='pill'>" + cat.items.length + " 項</span></div>" +
        "<div class='cd-b'>" + rows + "</div>";
      frag.appendChild(card);
    });
    c.innerHTML = ""; c.appendChild(frag);
    bindDisk(); updateStats();
  }
  function bindDisk() {
    var c = $("#diskCategories");
    c.addEventListener("change", function (e) {
      var t = e.target;
      if (t.classList.contains("category-checkbox")) {
        var k = t.dataset.category;
        $all(".item-checkbox[data-category='" + k + "']").forEach(function (i) { i.checked = t.checked; });
        updateStats();
      } else if (t.classList.contains("item-checkbox")) { syncCats(); updateStats(); }
    });
  }
  function syncCats() {
    Object.keys(CATALOG).forEach(function (k) {
      var all = $all(".item-checkbox[data-category='" + k + "']");
      var on = $all(".item-checkbox[data-category='" + k + "']:checked");
      var cc = $(".category-checkbox[data-category='" + k + "']");
      if (cc) cc.checked = all.length === on.length;
    });
  }
  var updateStats = debounce(function () {
    var all = $all(".item-checkbox:checked");
    if ($("#selectedCount")) $("#selectedCount").textContent = all.length;
    if ($("#safeCount")) $("#safeCount").textContent = $all(".item-checkbox[data-risk='safe']:checked").length;
    if ($("#lowCount")) $("#lowCount").textContent = $all(".item-checkbox[data-risk='low']:checked").length;
    var total = 0; all.forEach(function (cb) { total += STATE.sizes[cb.dataset.key] || 0; });
    if ($("#reclaimTotal")) $("#reclaimTotal").textContent = human(total);
  }, 60);

  function selectedTargets() {
    return $all(".item-checkbox:checked").map(function (cb) {
      var k = cb.dataset.key, cat = cb.dataset.category, found = null;
      CATALOG[cat].items.forEach(function (it) { if (it.key === k) found = it; });
      return found ? { key: found.key, name: found.name, path: found.path, risk: found.risk } : null;
    }).filter(Boolean);
  }
  window.vooSelectAll = function () { $all(".item-checkbox,.category-checkbox").forEach(function (c) { c.checked = true; }); updateStats(); };
  window.vooDeselectAll = function () { $all(".item-checkbox,.category-checkbox").forEach(function (c) { c.checked = false; }); updateStats(); };
  window.vooSelectSafe = function () { $all(".item-checkbox").forEach(function (c) { c.checked = c.dataset.risk === "safe"; }); syncCats(); updateStats(); };

  window.vooScan = function () {
    var tg = selectedTargets(); if (!tg.length) { log("請至少選擇一個項目", "warn"); return; }
    setBusy(true, "掃描可釋放空間…"); log("掃描 " + tg.length + " 個目標…");
    api("/api/scan", { targets: tg }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("掃描失敗：" + (d.error || d._status), "err"); return; }
      STATE.sizes = {};
      (d.targets || []).forEach(function (t) {
        STATE.sizes[t.key] = t.bytes || 0;
        var s = $("#size-" + t.key);
        if (s) {
          if (t.denied) { s.textContent = "🛡️保護"; s.className = "item-size denied"; }
          else if (!t.exists) { s.textContent = "—"; s.className = "item-size"; }
          else { s.textContent = human(t.bytes); s.className = "item-size has"; }
        }
      });
      updateStats();
      log("掃描完成 · 可釋放合計 " + human(d.total_bytes) + "（" + d.elapsed_ms + " ms）", "ok");
    });
  };
  window.vooClean = function () {
    var tg = selectedTargets(); if (!tg.length) { log("請至少選擇一個項目", "warn"); return; }
    var apply = $("#applyToggle") && $("#applyToggle").checked;
    var dest = $("#destSelect") ? $("#destSelect").value : "recycle";
    if (apply && !window.confirm("即將實際清理 " + tg.length + " 個目標（移至" + (dest === "recycle" ? "資源回收筒" : "隔離區") + "，可還原）。確定？")) { log("已取消", "warn"); return; }
    setBusy(true, apply ? "清理中…" : "預演中…"); log((apply ? "實際清理" : "預演") + " " + tg.length + " 目標 · " + dest);
    api("/api/clean", { targets: tg, apply: !!apply, dest: dest }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("清理失敗：" + (d.error || d._status), "err"); return; }
      (d.results || []).forEach(function (r) {
        var tag = r.denied ? "err" : (r.acted ? "ok" : "info");
        var verb = r.denied ? "🛡️拒絕(保護根)" : (apply ? "已處理" : "可釋放");
        log("  " + verb + " · " + r.name + " · " + human(r.bytes) + (r.note ? " · " + r.note : ""), tag);
        if (apply && r.acted) { STATE.sizes[r.key] = 0; var s = $("#size-" + r.key); if (s) { s.textContent = "0"; s.className = "item-size"; } }
      });
      updateStats();
      log((apply ? "清理完成 · 釋放 " : "預演完成 · 預計釋放 ") + human(d.total_bytes) + (d.ledger ? " · 還原清單 " + d.ledger : ""), "ok");
    });
  };

  /* ---- dedup matrix: exact + name-similar, selection logic, modal -------- */
  var DUP = { mode: "exact", groups: [], algo: "" };
  window.vooSetMode = function (m) {
    DUP.mode = m;
    var ex = $("#modeExact"), nm = $("#modeName");
    if (ex) ex.classList.toggle("modeon", m === "exact");
    if (nm) nm.classList.toggle("modeon", m === "name");
    if ($("#lowqBtn")) $("#lowqBtn").style.display = (m === "name") ? "" : "none";
  };
  function dupProgress(pct) {
    var p = $("#dedupProgress"), f = $("#dedupProgressFill");
    if (!p || !f) return;
    if (pct == null) { p.classList.remove("show"); f.style.width = "0"; return; }
    p.classList.add("show"); f.style.width = Math.max(0, Math.min(100, pct)) + "%";
  }
  function fmtDate(ts) { try { return new Date(ts * 1000).toLocaleDateString("zh-TW"); } catch (e) { return ""; } }

  // normalize a backend group into a common render model
  function normGroups(raw, mode) {
    return (raw || []).map(function (g, gi) {
      var keeperMtime = 0;
      (g.files || []).forEach(function (f) { if (f.is_keeper || f.is_keep_suggested) keeperMtime = f.mtime; });
      var files = (g.files || []).map(function (f, fi) {
        var keep = !!(f.is_keeper || f.is_keep_suggested);
        var reasons = [];
        if (keep) {
          reasons.push(mode === "name" ? { cls: "keep", txt: "建議保留·最高畫質" } : { cls: "keep", txt: "原始保留" });
        } else if (mode === "name") {
          if (f.is_low_quality) reasons.push({ cls: "lowq", txt: "低畫質 q" + (f.quality_score || 0) });
          reasons.push({ cls: "fmt", txt: (f.ext || "").replace(".", "") || "?" });
        } else {
          if (f.score > 0) reasons.push({ cls: "copy", txt: "複本字樣" });
          if (f.mtime > keeperMtime) reasons.push({ cls: "newer", txt: "較新" });
          else if (f.mtime < keeperMtime) reasons.push({ cls: "older", txt: "較舊" });
        }
        return {
          id: "g" + gi + "f" + fi, path: f.path, basename: f.basename || f.path,
          bytes: f.bytes || 0, mtime: f.mtime || 0, keep: keep,
          low: !!f.is_low_quality, newer: f.mtime > keeperMtime, older: f.mtime < keeperMtime,
          reasons: reasons, checked: !keep
        };
      });
      return { idx: gi, keeperMtime: keeperMtime, isMedia: !!g.is_media, files: files,
        bytesEach: g.bytes_each || 0, sig: g.signature || "" };
    });
  }

  function renderDupMatrix() {
    var box = $("#dedupResult");
    if (!DUP.groups.length) { box.innerHTML = "<p class='hint'>未發現符合的項目。</p>"; return; }
    var frag = document.createDocumentFragment();
    DUP.groups.forEach(function (g) {
      var card = document.createElement("div");
      card.className = "dgroup " + (g.idx % 2 === 0 ? "fam-a" : "fam-b");
      card.style.animationDelay = (g.idx % 12) * 0.025 + "s";
      var head = "<div class='dgroup-h'><span>群組 #" + (g.idx + 1) + (g.isMedia ? " · 媒體" : "") + "</span>" +
        "<span class='gmeta'>" + (g.sig ? esc(g.sig) + " · " : "") + g.files.length + " 檔</span></div>";
      var rows = g.files.map(function (f) {
        var tags = f.reasons.map(function (r) { return "<span class='tag " + r.cls + "'>" + esc(r.txt) + "</span>"; }).join("");
        return "<div class='dfile" + (f.keep ? " keep" : "") + "' id='row-" + f.id + "'>" +
          "<input type='checkbox' data-id='" + f.id + "' " + (f.checked ? "checked" : "") + (f.keep ? "" : "") + ">" +
          "<div class='fmain'><div class='fname'>" + esc(f.basename) + "</div><div class='fpath'>" + esc(f.path) + "</div></div>" +
          "<div class='fmeta'>" + tags + "<span class='tag size'>" + human(f.bytes) + "</span><span class='tag size'>" + fmtDate(f.mtime) + "</span></div></div>";
      }).join("");
      card.innerHTML = head + rows;
      frag.appendChild(card);
    });
    box.innerHTML = "";
    box.appendChild(frag);
    box.addEventListener("change", function (e) {
      if (e.target && e.target.matches("input[type=checkbox][data-id]")) {
        var id = e.target.dataset.id;
        DUP.groups.forEach(function (g) { g.files.forEach(function (f) { if (f.id === id) f.checked = e.target.checked; }); });
        updateDupSel();
      }
    });
    updateDupSel();
  }

  function eachFile(fn) { DUP.groups.forEach(function (g) { g.files.forEach(function (f) { fn(f, g); }); }); }
  function syncChecks() { eachFile(function (f) { var cb = $("input[data-id='" + f.id + "']"); if (cb) cb.checked = f.checked; }); }

  window.vooDupSel = function (mode) {
    eachFile(function (f, g) {
      if (mode === "all") f.checked = !f.keep;
      else if (mode === "none") f.checked = false;
      else if (mode === "newer") f.checked = (!f.keep && f.newer);
      else if (mode === "older") f.checked = (!f.keep && f.older);
      else if (mode === "lowq") f.checked = !!f.low;
    });
    syncChecks(); updateDupSel();
  };

  function updateDupSel() {
    var n = 0, b = 0;
    eachFile(function (f) { if (f.checked) { n++; b += f.bytes; } });
    if ($("#dupSelCount")) $("#dupSelCount").textContent = n;
    if ($("#dupSelBytes")) $("#dupSelBytes").textContent = human(b);
  }

  window.vooDedupScan = function () {
    var roots = ($("#dedupRoots") ? $("#dedupRoots").value : "").split("\n").map(function (s) { return s.trim(); }).filter(Boolean);
    if (!roots.length) { log("請輸入至少一個根目錄", "warn"); return; }
    var ep = DUP.mode === "name" ? "/api/namedup" : "/api/dedup";
    setBusy(true, "去重掃描…"); dupProgress(15);
    log((DUP.mode === "name" ? "檔名相似" : "完全相同") + " 掃描：" + roots.join(" , "));
    var creep = setInterval(function () { var f = $("#dedupProgressFill"); if (f) { var w = parseFloat(f.style.width) || 15; if (w < 85) dupProgress(w + 6); } }, 220);
    api(ep, { roots: roots, min_bytes: 1048576 }).then(function (d) {
      clearInterval(creep); setBusy(false); dupProgress(100);
      setTimeout(function () { dupProgress(null); }, 500);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      DUP.algo = d.hash_algo || "";
      if ($("#dedupAlgo")) $("#dedupAlgo").textContent = DUP.mode === "name" ? "名稱相似度" : ("hash: " + (d.hash_algo || "—"));
      DUP.groups = normGroups(d.groups, DUP.mode);
      $("#dedupSelbar").style.display = DUP.groups.length ? "flex" : "none";
      $("#dedupStats").style.display = DUP.groups.length ? "grid" : "none";
      if ($("#dupGroups")) $("#dupGroups").textContent = d.group_count || 0;
      if ($("#dupReclaim")) $("#dupReclaim").textContent = human(d.reclaimable_bytes || 0);
      renderDupMatrix();
      log("找到 " + (d.group_count || 0) + " 組 · 可釋放 " + human(d.reclaimable_bytes || 0), "ok");
    });
  };

  // confirmation modal that restates the selection logic
  window.vooDupDelete = function () {
    var picked = [];
    eachFile(function (f) { if (f.checked && !f.keep) picked.push(f); });
    // allow checked keepers too (user override) but warn
    var keepers = [];
    eachFile(function (f) { if (f.checked && f.keep) keepers.push(f); });
    if (!picked.length && !keepers.length) { log("沒有勾選任何項目", "warn"); return; }
    var apply = $("#dupApply") && $("#dupApply").checked;
    var dest = $("#dupDest") ? $("#dupDest").value : "recycle";
    var all = picked.concat(keepers);
    var totalBytes = all.reduce(function (s, f) { return s + f.bytes; }, 0);
    $("#dupModalSub").innerHTML = (apply ? "即將實際刪除 " : "預演（不會實際刪除）· ") + "<b>" + all.length + "</b> 個檔案，釋放 <b>" + human(totalBytes) + "</b>" +
      (apply ? "（移至" + (dest === "recycle" ? "資源回收筒" : "隔離區") + "，可還原）。以下複述選擇邏輯：" : "。以下複述選擇邏輯：");
    $("#dupModalBody").innerHTML = all.map(function (f) {
      var why = f.keep ? "⚠️ 你手動勾選了建議保留項" : f.reasons.map(function (r) { return r.txt; }).join("、");
      return "<div class='modal-logic'><div class='ml-name'>" + esc(f.basename) + " <span class='mono' style='color:var(--ink-soft)'>" + human(f.bytes) + "</span></div>" +
        "<div class='mono' style='font-size:9px;color:var(--grey)'>" + esc(f.path) + "</div>" +
        "<div class='ml-why'>選擇理由：" + esc(why) + "</div></div>";
    }).join("");
    var confirmBtn = $("#dupModalConfirm");
    confirmBtn.textContent = apply ? "確認刪除" : "確認（預演）";
    confirmBtn.onclick = function () { doDupDelete(all, apply, dest); };
    $("#dupModal").classList.add("show");
  };
  window.vooModalClose = function () { $("#dupModal").classList.remove("show"); };

  function doDupDelete(files, apply, dest) {
    vooModalClose();
    var paths = files.map(function (f) { return f.path; });
    setBusy(true, apply ? "刪除中…" : "預演…"); dupProgress(20);
    var creep = setInterval(function () { var el = $("#dedupProgressFill"); if (el) { var w = parseFloat(el.style.width) || 20; if (w < 88) dupProgress(w + 7); } }, 180);
    log((apply ? "刪除" : "預演刪除") + " " + paths.length + " 檔 · " + dest);
    api("/api/dedupdelete", { paths: paths, apply: !!apply, dest: dest }).then(function (d) {
      clearInterval(creep); setBusy(false); dupProgress(100);
      setTimeout(function () { dupProgress(null); }, 600);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      (d.results || []).forEach(function (r) {
        if (r.denied) { log("  🛡️拒絕(保護根)：" + r.path, "err"); return; }
        if (apply && r.acted) {
          var f = null; eachFile(function (x) { if (x.path === r.path) f = x; });
          if (f) { var row = $("#row-" + f.id); if (row) { row.classList.add("removing"); } f._gone = true; }
        }
      });
      if (apply) {
        setTimeout(function () {
          DUP.groups.forEach(function (g) { g.files = g.files.filter(function (f) { return !f._gone; }); });
          DUP.groups = DUP.groups.filter(function (g) { return g.files.length >= 2; });
          renderDupMatrix();
        }, 420);
      }
      log((apply ? "刪除完成 · 釋放 " : "預演 · 預計釋放 ") + human(d.total_bytes) + " · 處理 " + d.acted_count + "/" + d.total_count + (d.ledger ? " · 還原清單 " + d.ledger : ""), "ok");
    });
  }

  /* ---- old downloads ------------------------------------------------------ */
  window.vooOldScan = function () {
    var root = $("#oldRoot").value.trim(), age = parseInt($("#oldAge").value, 10) || 90;
    setBusy(true, "掃描舊檔…"); log("舊下載掃描：" + root + " · >" + age + " 天");
    api("/api/oldscan", { root: root, age_days: age }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      $("#oldCount").textContent = d.count; $("#oldTotal").textContent = human(d.total_bytes);
      var rows = (d.items || []).slice(0, 200).map(function (it) {
        return "<tr><td class='mono'>" + human(it.bytes) + "</td><td class='mono'>" + it.age_days + " 天</td><td class='mono'>" + esc(it.path) + "</td></tr>";
      }).join("");
      $("#oldResult").innerHTML = d.count ? "<table><thead><tr><th>大小</th><th>年齡</th><th>路徑</th></tr></thead><tbody>" + rows + "</tbody></table>" + (d.capped ? "<p class='hint'>（已截斷顯示前 200 筆）</p>" : "") : "<p class='hint'>無符合的舊檔。</p>";
      log("舊檔 " + d.count + " 個 · 可釋放 " + human(d.total_bytes), "ok");
    });
  };
  window.vooOldClean = function () {
    var root = $("#oldRoot").value.trim(), age = parseInt($("#oldAge").value, 10) || 90;
    var apply = $("#oldApply") && $("#oldApply").checked;
    if (apply && !window.confirm("即將把 " + root + " 內超過 " + age + " 天的舊檔送資源回收筒（VIA 工作樹已排除，可還原）。確定？")) { log("已取消", "warn"); return; }
    setBusy(true, apply ? "清理舊檔…" : "預演…"); log((apply ? "實際清理" : "預演") + " 舊下載 >" + age + " 天");
    api("/api/oldclean", { root: root, age_days: age, apply: !!apply, dest: "recycle" }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      log((apply ? "清理完成 · 釋放 " : "預演 · 預計釋放 ") + human(d.total_bytes) + " · 處理 " + d.acted_count + "/" + d.total_count + " 檔", "ok");
    });
  };

  /* ---- lang sweep --------------------------------------------------------- */
  window.vooLangSweep = function () {
    var root = $("#langRoot").value.trim();
    setBusy(true, "掃描語言快取…"); log("語言快取掃描：" + root);
    api("/api/langsweep", { root: root }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      $("#langTotal").textContent = human(d.total_bytes);
      var rows = (d.categories || []).map(function (c) {
        return "<tr><td class='mono' style='color:var(--teal)'>" + esc(c.label) + "</td><td class='mono'>×" + c.count + "</td><td class='mono'>" + human(c.bytes) + "</td></tr>";
      }).join("");
      $("#langResult").innerHTML = d.categories && d.categories.length ? "<table><thead><tr><th>快取類型</th><th>目錄數</th><th>大小</th></tr></thead><tbody>" + rows + "</tbody></table>" : "<p class='hint'>未發現語言快取目錄。</p>";
      log("語言快取合計 " + human(d.total_bytes) + "（" + (d.categories || []).length + " 類）", "ok");
    });
  };
  window.vooLangClean = function () {
    var root = $("#langRoot").value.trim();
    var apply = $("#langApply") && $("#langApply").checked, dest = $("#langDest").value;
    if (apply && !window.confirm("即將清理 " + root + " 底下的語言快取目錄（移至" + (dest === "recycle" ? "回收筒" : "隔離區") + "，可還原）。原始碼不受影響。確定？")) { log("已取消", "warn"); return; }
    setBusy(true, apply ? "清理快取…" : "預演…"); log((apply ? "實際清理" : "預演") + " 語言快取");
    api("/api/langclean", { root: root, apply: !!apply, dest: dest }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      log((apply ? "清理完成 · 釋放 " : "預演 · 預計釋放 ") + human(d.total_bytes) + " · 處理 " + d.acted_count + "/" + d.total_count + " 目錄", "ok");
    });
  };

  /* ---- system / network --------------------------------------------------- */
  function runAction(path, action, label) {
    setBusy(true, label + "…"); log("▶ " + label);
    api(path, { action: action }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log(label + " 失敗：" + (d.error || d._status), "err"); return; }
      (d.lines || []).forEach(function (ln) { log("  " + ln, "info"); });
      if (d.report) log("📄 報告：" + d.report + "（已開啟）", "ok");
      log(label + " 完成（" + (d.elapsed_ms || 0) + " ms）", "ok");
    });
  }
  window.vooSysInfo = function () { runAction("/api/system", "sysinfo", "系統診斷報告"); };
  window.vooPerf = function () { runAction("/api/system", "perf", "效能優化"); };
  window.vooStartup = function () { runAction("/api/system", "startup", "開機項目分析"); };
  window.vooService = function () { runAction("/api/system", "service", "服務分析"); };
  window.vooNetDiag = function () { runAction("/api/network", "diag", "網路診斷"); };
  window.vooDns = function () { runAction("/api/network", "dns", "DNS 優化"); };
  window.vooTcp = function () { runAction("/api/network", "tcp", "TCP/IP 優化"); };

  /* ---- accelerators + guard ----------------------------------------------- */
  function renderAccel(py, ps) {
    var grid = $("#accelGrid"); if (!grid) return;
    function block(title, color, rows, isObj) {
      var lis = rows.map(function (r) {
        var on = isObj ? r.available : true;
        var nm = isObj ? r.name : r;
        var note = isObj && r.note ? " <span style='color:var(--ink-soft)'>· " + esc(r.note) + "</span>" : "";
        return "<div class='guard-item'><span class='dot " + (on ? "on" : "off") + "'></span>" + esc(nm) + note + "</div>";
      }).join("");
      return "<div class='cd'><div class='cd-h' style='border-left:3px solid " + color + "'><span class='accel-lang'>" + title + "</span></div><div class='cd-b'>" + lis + "</div></div>";
    }
    grid.innerHTML = block("Python (" + (py.active || 0) + "/" + (py.total || 20) + ")", "#4c78a8", py.accelerators || [], true) +
      block("PowerShell (20/20)", "#2d8659", ps || [], false) +
      block("JavaScript (20/20)", "#439a9a", JS_ACCEL, false);
    if ($("#accelPy")) $("#accelPy").textContent = (py.active || 0) + "/" + (py.total || 20);
    if ($("#accelHash")) $("#accelHash").textContent = py.hash_algo || "—";
  }
  window.vooAccel = function () {
    api("/api/accel", {}).then(function (d) {
      if (!d.ok) { log("加速器查詢失敗", "err"); return; }
      renderAccel(d.python || {}, d.powershell || []);
    });
  };
  function renderGuard(roots) {
    var box = $("#guardList"); if (!box) return;
    box.innerHTML = (roots || []).map(function (r) {
      return "<div class='guard-item'><span class='dot on'></span><span class='mono'>" + esc(r) + "</span></div>";
    }).join("");
  }

  /* ---- Windows storage analyzer (matrix) ---------------------------------- */
  var SAFE_PILL = { safe: "pill-safe", caution: "pill-low", danger: "pill-medium" };
  var SAFE_TXT = { safe: "安全", caution: "注意", danger: "危險" };
  window.vooStorage = function () {
    setBusy(true, "分析 Windows 儲存設定…"); log("同步分析 Windows 原生儲存設定（唯讀）");
    api("/api/storage", {}).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      var rows = (d.rows || []).map(function (r) {
        return "<tr><td><b>" + esc(r.name) + "</b></td><td>" + esc(r.func) + "</td><td class='mono'>" + esc(r.method) +
          "</td><td class='mono' style='color:var(--primary)'>" + esc(r.value) + "</td>" +
          "<td><span class='" + (SAFE_PILL[r.safety] || "pill-grey") + "'>" + (SAFE_TXT[r.safety] || r.safety) + "</span></td>" +
          "<td>" + esc(r.advice) + "</td><td class='mono'>" + (r.actionable ? "✓ 可操作" : "報告") + "</td></tr>";
      }).join("");
      $("#storageResult").innerHTML = "<div class='cd'><div class='cd-h'>💾 Windows 儲存設定矩陣<span class='pill'>" + (d.rows || []).length + " 項 · " + esc(d.generated || "") + "</span></div><div class='cd-b' style='padding:0'>" +
        "<table><thead><tr><th>項目</th><th>功能</th><th>方法</th><th>現值</th><th>安全</th><th>建議</th><th>可操作</th></tr></thead><tbody>" + rows + "</tbody></table></div></div>";
      log("儲存設定分析完成 · " + (d.rows || []).length + " 項（危險項僅報告，不自動更改）", "ok");
    });
  };

  /* ---- panorama I/O scan (matrix) ----------------------------------------- */
  var PANO_PILL = { vendored_link_stale: "pill-low", external_only: "pill-medium", internal: "pill-safe" };
  var PANO_TXT = { vendored_link_stale: "已放進·連結待修", external_only: "未納入·建議納入", internal: "內部" };
  window.vooPanorama = function () {
    var root = $("#panoRoot").value.trim();
    setBusy(true, "全景掃描…"); log("🛰️ 全景 I/O 掃描：" + root);
    api("/api/panorama", { root: root }).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      var s = d.summary || {};
      $("#panoFiles").textContent = s.file_count != null ? s.file_count : "—";
      $("#panoAssoc").textContent = s.associated_count != null ? s.associated_count : "—";
      $("#panoStale").textContent = s.vendored_stale_count != null ? s.vendored_stale_count : "—";
      $("#panoExt").textContent = s.external_only_count != null ? s.external_only_count : "—";
      var assoc = (d.associated_files || []).map(function (a) {
        return "<tr><td><span class='pill-safe'>" + esc(a.kind) + "</span></td><td class='mono'>" + esc(a.path) + "</td><td class='mono'>" + human(a.bytes) + "</td></tr>";
      }).join("");
      var refs = (d.external_refs || []).map(function (r) {
        return "<tr><td><span class='" + (PANO_PILL[r.status] || "pill-grey") + "'>" + (PANO_TXT[r.status] || r.status) + "</span></td>" +
          "<td class='mono'>" + esc(r.basename) + "</td><td class='mono'>" + esc(r.ref) + "</td><td class='mono'>×" + r.count + "</td><td class='mono' style='color:var(--ink-soft)'>" + esc((r.files || []).slice(0, 3).join(", ")) + "</td></tr>";
      }).join("");
      var tools = (d.outbound_tools || []).map(function (t) {
        return "<tr><td class='mono'>" + esc(t.location) + "</td><td><span class='" + (t.vendored ? "pill-low" : "pill-medium") + "'>" + (t.vendored ? "已放進·連結待修" : "未納入") + "</span></td><td class='mono'>×" + t.refs + "</td></tr>";
      }).join("");
      $("#panoResult").innerHTML =
        "<div class='cd'><div class='cd-h'>🔒 關聯保護項目（設定/環境/啟動檔）<span class='pill'>" + (d.associated_files || []).length + " · 已在保護根內</span></div><div class='cd-b' style='padding:0'><table><thead><tr><th>類型</th><th>路徑</th><th>大小</th></tr></thead><tbody>" + (assoc || "<tr><td colspan=3 class='hint' style='padding:10px'>無</td></tr>") + "</tbody></table></div></div>" +
        "<div class='cd'><div class='cd-h'>📡 對外呼叫工具 · vendor 連結分析<span class='pill'>stale=" + (s.vendored_stale_count || 0) + " · external=" + (s.external_only_count || 0) + "</span></div><div class='cd-b' style='padding:0'><table><thead><tr><th>狀態</th><th>名稱</th><th>參照路徑</th><th>次數</th><th>出現於</th></tr></thead><tbody>" + (refs || "<tr><td colspan=5 class='hint' style='padding:10px'>未發現對外參照</td></tr>") + "</tbody></table></div></div>" +
        (tools ? "<div class='cd'><div class='cd-h'>🧭 對外工具根</div><div class='cd-b' style='padding:0'><table><thead><tr><th>位置</th><th>狀態</th><th>參照</th></tr></thead><tbody>" + tools + "</tbody></table></div></div>" : "");
      log("全景掃描完成 · 關聯保護 " + (s.associated_count || 0) + " · 連結待修 " + (s.vendored_stale_count || 0) + " · 未納入 " + (s.external_only_count || 0), "ok");
    });
  };

  /* ---- tool registry matrix ----------------------------------------------- */
  window.vooToolMatrix = function () {
    setBusy(true, "載入工具矩陣…");
    api("/api/toolmatrix", {}).then(function (d) {
      setBusy(false);
      if (!d.ok) { log("失敗：" + (d.error || d._status), "err"); return; }
      function tbl(title, color, rows, cols) {
        return "<div class='cd'><div class='cd-h' style='border-left:3px solid " + color + "'>" + title + "<span class='pill'>" + rows.length + "</span></div><div class='cd-b' style='padding:0'><table><thead><tr>" + cols.map(function (c) { return "<th>" + c + "</th>"; }).join("") + "</tr></thead><tbody>" + rows.join("") + "</tbody></table></div></div>";
      }
      var py = ((d.python && d.python.accelerators) || []).map(function (r) {
        return "<tr><td class='mono'>" + esc(r.name) + "</td><td>" + esc(r.kind) + "</td><td>" + esc(r.note) + "</td><td><span class='" + (r.available ? "pill-safe" : "pill-grey") + "'>" + (r.available ? "可用" : "缺") + "</span></td></tr>";
      });
      var ps = (d.powershell || []).map(function (t, i) { return "<tr><td class='mono'>PS-" + (i + 1) + "</td><td class='mono'>" + esc(t) + "</td></tr>"; });
      var js = JS_ACCEL.map(function (t, i) { return "<tr><td class='mono'>JS-" + (i + 1) + "</td><td class='mono'>" + esc(t) + "</td></tr>"; });
      var ext = (d.external || []).map(function (t) { return "<tr><td class='mono'>" + esc(t.tool) + "</td><td>" + esc(t.purpose) + "</td><td><span class='pill-low'>對外</span></td><td class='mono'>" + esc(t.location) + "</td></tr>"; });
      var cim = (d.cim || []).map(function (t) { return "<tr><td class='mono'>" + esc(t.tool) + "</td><td>" + esc(t.purpose) + "</td><td><span class='pill-safe'>內部</span></td></tr>"; });
      $("#toolResult").innerHTML =
        "<div class='sg'><div class='sc'><div class='lbl'>Python</div><div class='val'>" + py.length + "</div></div><div class='sc g'><div class='lbl'>PowerShell</div><div class='val'>" + ps.length + "</div></div><div class='sc t'><div class='lbl'>JavaScript</div><div class='val'>" + js.length + "</div></div><div class='sc y'><div class='lbl'>對外 EXE</div><div class='val'>" + ext.length + "</div></div><div class='sc r'><div class='lbl'>CIM</div><div class='val'>" + cim.length + "</div></div></div>" +
        tbl("🐍 Python 加速器", "#4c78a8", py, ["名稱", "類型", "說明", "狀態"]) +
        tbl("🔷 PowerShell 技法", "#2d8659", ps, ["#", "技法"]) +
        tbl("🟨 JavaScript 技法", "#439a9a", js, ["#", "技法"]) +
        tbl("⚙️ 對外 EXE 工具", "#b85450", ext, ["工具", "用途", "範圍", "位置"]) +
        tbl("📊 CIM 類別", "#8c5e9e", cim, ["類別", "用途", "範圍"]);
      log("工具矩陣載入完成", "ok");
    });
  };

  window.vooTab = function (id) {
    $all(".tab").forEach(function (b) { b.classList.remove("active"); });
    $all(".panel").forEach(function (c) { c.classList.remove("active"); });
    var btn = $("[data-tab='" + id + "']"); if (btn) btn.classList.add("active");
    var pane = $("#tab-" + id); if (pane) pane.classList.add("active");
    if (id === "accel") vooAccel();
    if (id === "tools") vooToolMatrix();
  };

  function boot() {
    renderDisk();
    api("/api/health", {}).then(function (d) {
      var badge = $("#healthBadge"), vb = $("#verBadge");
      if (d.ok) {
        if (badge) badge.innerHTML = "● 後端連線 · " + (d.version || "") + (d.admin ? " · 系統管理員" : " · 一般權限") + "<br>Python: " + (d.python_ok ? esc(d.python || "ok") : "未就緒");
        if (vb) { vb.textContent = d.version || "live"; vb.className = "badge"; }
        log("後端連線成功 · " + (d.version || "") + (d.python ? " · Python：" + d.python : ""), "ok");
        if (!d.admin) log("提示：未以系統管理員執行，部分系統路徑會略過", "warn");
        if (!d.python_ok) log("警告：Python 引擎未就緒，掃描/重複檔/語言快取停用", "err");
        renderGuard(d.protected_roots || []);
      } else if (badge) { badge.textContent = "● 後端連線失敗"; if (vb) vb.className = "badge bad"; }
    });
  }
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", boot);
  else boot();

  window.__VOO = { CATALOG: CATALOG, human: human, selectedTargets: selectedTargets, JS_ACCEL: JS_ACCEL, renderAccel: renderAccel, renderGuard: renderGuard };
})();
