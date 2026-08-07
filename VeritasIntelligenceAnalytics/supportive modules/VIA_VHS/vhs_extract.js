/* ==========================================================================
 *  vhs_extract.js  -  Veritas HTML Spec Reader  (VIA / VPN family)
 *  M02 : render static spec matrix (from VHS_Reader.py JSON)
 *        + LIVE computed-style extraction via hidden iframe
 *  No external deps. Reads ./vhs_specs.json served by the PS7 HttpListener.
 * ======================================================================== */
(function () {
  "use strict";

  var STATE = { data: null, active: 0, filter: "ALL", catFilter: "ALL", q: "" };

  function $(s, r) { return (r || document).querySelector(s); }
  function el(tag, cls, txt) {
    var e = document.createElement(tag);
    if (cls) e.className = cls;
    if (txt != null) e.textContent = txt;
    return e;
  }
  function normColor(c) {
    c = (c || "").trim().toLowerCase();
    if (c[0] === "#" && c.length === 4)
      c = "#" + c[1] + c[1] + c[2] + c[2] + c[3] + c[3];
    return c;
  }
  function rgbToHex(s) {
    var m = (s || "").match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/i);
    if (!m) return null;
    return "#" + [1, 2, 3].map(function (i) {
      return ("0" + parseInt(m[i], 10).toString(16)).slice(-2);
    }).join("");
  }

  /* ---- load JSON ------------------------------------------------------- */
  function load() {
    fetch("./vhs_specs.json?ts=" + Date.now())
      .then(function (r) { return r.json(); })
      .then(function (j) { STATE.data = j; boot(); })
      .catch(function (e) {
        $("#vhs-files").innerHTML =
          '<div class="vhs-empty">\u672a\u80fd\u8f09\u5165 vhs_specs.json\uff1a' + e + "</div>";
      });
  }

  function boot() {
    renderMeta();
    renderTabs();
    renderActive();
    wireToolbar();
  }

  /* ---- meta / summary -------------------------------------------------- */
  function renderMeta() {
    var d = STATE.data, m = d.meta;
    var tl = 0, te = 0;
    d.files.forEach(function (f) {
      if (f.summary) { tl += f.summary.locked; te += f.summary.editable; }
    });
    var s = $("#vhs-summary");
    s.innerHTML = "";
    [["\u6a94\u6848\u6578", m.file_count],
     ["\u4e0d\u53ef\u6539 LOCKED", tl, "lock"],
     ["\u53ef\u6539 EDITABLE", te, "edit"],
     ["\u751f\u6210\u6642\u9593", m.generated]].forEach(function (row) {
      var b = el("div", "vhs-stat" + (row[2] ? " is-" + row[2] : ""));
      b.appendChild(el("div", "vhs-stat-n", String(row[1])));
      b.appendChild(el("div", "vhs-stat-l", row[0]));
      s.appendChild(b);
    });
    $("#vhs-scanpath").textContent = m.scan_path + "   \u00b7   " + m.tool + " " + m.version;
  }

  /* ---- file tabs ------------------------------------------------------- */
  function renderTabs() {
    var t = $("#vhs-tabs");
    t.innerHTML = "";
    STATE.data.files.forEach(function (f, i) {
      var tab = el("button", "vhs-tab" + (i === STATE.active ? " active" : ""));
      tab.appendChild(el("span", "vhs-tab-name", f.file));
      if (f.summary) {
        var badge = el("span", "vhs-tab-badge");
        badge.appendChild(el("span", "vhs-mini lock", String(f.summary.locked)));
        badge.appendChild(el("span", "vhs-mini edit", String(f.summary.editable)));
        tab.appendChild(badge);
      }
      tab.onclick = function () { STATE.active = i; renderTabs(); renderActive(); };
      t.appendChild(tab);
    });
  }

  /* ---- active file matrix --------------------------------------------- */
  var CAT_ORDER = ["HEADER", "LAYOUT", "COLOR", "TYPOGRAPHY",
                   "DIMENSION", "INTERACTIVE", "MARKER"];
  var CAT_LABEL = {
    HEADER: "HEADER \u9801\u9996", LAYOUT: "LAYOUT \u7248\u9762",
    COLOR: "COLOR \u8272\u5f69", TYPOGRAPHY: "TYPOGRAPHY \u5b57\u9ad4",
    DIMENSION: "DIMENSION \u5c3a\u5bf8", INTERACTIVE: "INTERACTIVE \u4e92\u52d5",
    MARKER: "MARKER \u4f5c\u8005\u6a19\u8a18"
  };

  function matchFilter(item) {
    if (STATE.filter === "LOCK" && item.status !== "LOCKED") return false;
    if (STATE.filter === "EDIT" && item.status !== "EDITABLE") return false;
    if (STATE.q) {
      var hay = (item.key + " " + item.value + " " + item.reason).toLowerCase();
      if (hay.indexOf(STATE.q) < 0) return false;
    }
    return true;
  }

  function renderActive() {
    var host = $("#vhs-files");
    host.innerHTML = "";
    var f = STATE.data.files[STATE.active];
    if (!f) { host.innerHTML = '<div class="vhs-empty">\u7121\u6a94\u6848</div>'; return; }
    if (f.error) {
      host.innerHTML = '<div class="vhs-empty">\u89e3\u6790\u932f\u8aa4\uff1a' + f.error + "</div>";
      return;
    }

    var head = el("div", "vhs-filehead");
    head.appendChild(el("div", "vhs-fh-name", f.file));
    head.appendChild(el("div", "vhs-fh-meta",
      (f.size_bytes / 1024).toFixed(1) + " KB  \u00b7  sha " + f.sha256));
    var live = el("button", "vhs-livebtn", "\u26a1 LIVE \u91cd\u8b80\u8a08\u7b97\u6a23\u5f0f");
    live.onclick = function () { liveExtract(f); };
    head.appendChild(live);
    host.appendChild(head);

    CAT_ORDER.forEach(function (cat) {
      if (STATE.catFilter !== "ALL" && STATE.catFilter !== cat) return;
      var items = (f.categories[cat] || []).filter(matchFilter);
      if (!items.length) return;
      var sec = el("section", "vhs-cat");
      var h = el("div", "vhs-cat-h");
      h.appendChild(el("span", "vhs-cat-t", CAT_LABEL[cat] || cat));
      var L = items.filter(function (x) { return x.status === "LOCKED"; }).length;
      h.appendChild(el("span", "vhs-cat-c", "LOCK " + L + " / " + items.length));
      sec.appendChild(h);

      var tbl = el("div", "vhs-table");
      items.forEach(function (it) {
        var row = el("div", "vhs-row " + (it.status === "LOCKED" ? "r-lock" : "r-edit"));
        var badge = el("span", "vhs-badge " + (it.status === "LOCKED" ? "b-lock" : "b-edit"),
                       it.status === "LOCKED" ? "\u4e0d\u53ef\u6539" : "\u53ef\u6539");
        row.appendChild(badge);
        var kv = el("div", "vhs-kv");
        kv.appendChild(el("span", "vhs-k", it.key));
        kv.appendChild(el("span", "vhs-v", it.value));
        row.appendChild(kv);
        row.appendChild(el("div", "vhs-reason", it.reason));
        tbl.appendChild(row);
      });
      sec.appendChild(tbl);
      host.appendChild(sec);
    });

    var liveBox = el("div", "vhs-livebox");
    liveBox.id = "vhs-livebox";
    host.appendChild(liveBox);
  }

  /* ---- LIVE computed-style extraction via hidden iframe ---------------- */
  function liveExtract(f) {
    var reg = STATE.data.lock_registry;
    var box = $("#vhs-livebox");
    box.innerHTML = '<div class="vhs-cat-h"><span class="vhs-cat-t">' +
      "\u26a1 LIVE \u8a08\u7b97\u6a23\u5f0f\uff08\u700f\u89bd\u5668\u5be6\u6e2c\uff09</span></div>" +
      '<div class="vhs-empty">\u8f09\u5165 ' + f.file + " \u4e2d\u2026</div>";
    var ifr = document.createElement("iframe");
    ifr.style.cssText = "position:absolute;width:1280px;height:900px;left:-99999px;top:0;border:0;";
    ifr.src = "./" + encodeURIComponent(f.file);
    ifr.onload = function () {
      var out = [];
      try {
        var doc = ifr.contentDocument, win = ifr.contentWindow;
        var palette = {};
        Object.keys(reg.palette).forEach(function (k) { palette[normColor(k)] = reg.palette[k]; });
        var probes = [["body", doc.body],
                      ["header", doc.querySelector("header")],
                      ["h1", doc.querySelector("h1")],
                      ["button", doc.querySelector("button")]];
        probes.forEach(function (p) {
          if (!p[1]) return;
          var cs = win.getComputedStyle(p[1]);
          var fam = (cs.fontFamily || "").split(",")[0].replace(/['"]/g, "").trim().toLowerCase();
          var famLock = reg.fonts[fam] ? "LOCKED" : "EDITABLE";
          out.push([p[0] + " font", cs.fontFamily, famLock,
                    famLock === "LOCKED" ? "VPN font " + reg.fonts[fam] : "free"]);
          ["color", "backgroundColor"].forEach(function (prop) {
            var hex = rgbToHex(cs[prop]);
            if (!hex || cs[prop] === "rgba(0, 0, 0, 0)") return;
            var lock = palette[normColor(hex)] ? "LOCKED" : "EDITABLE";
            out.push([p[0] + " " + prop, hex, lock,
                      lock === "LOCKED" ? "VPN " + palette[normColor(hex)] : "free"]);
          });
        });
      } catch (e) {
        out.push(["error", String(e), "EDITABLE", "iframe read blocked"]);
      }
      var html = '<div class="vhs-cat-h"><span class="vhs-cat-t">' +
        "\u26a1 LIVE \u8a08\u7b97\u6a23\u5f0f\uff08\u700f\u89bd\u5668\u5be6\u6e2c\uff09</span>" +
        '<span class="vhs-cat-c">' + out.length + " probes</span></div><div class=\"vhs-table\">";
      out.forEach(function (r) {
        html += '<div class="vhs-row ' + (r[2] === "LOCKED" ? "r-lock" : "r-edit") + '">' +
          '<span class="vhs-badge ' + (r[2] === "LOCKED" ? "b-lock" : "b-edit") + '">' +
          (r[2] === "LOCKED" ? "\u4e0d\u53ef\u6539" : "\u53ef\u6539") + "</span>" +
          '<div class="vhs-kv"><span class="vhs-k">' + r[0] +
          '</span><span class="vhs-v">' + r[1] + "</span></div>" +
          '<div class="vhs-reason">' + r[3] + "</div></div>";
      });
      html += "</div>";
      box.innerHTML = html;
      document.body.removeChild(ifr);
    };
    document.body.appendChild(ifr);
  }

  /* ---- toolbar wiring -------------------------------------------------- */
  function wireToolbar() {
    var search = $("#vhs-search");
    search.oninput = function () { STATE.q = this.value.toLowerCase().trim(); renderActive(); };
    document.querySelectorAll("[data-filter]").forEach(function (b) {
      b.onclick = function () {
        STATE.filter = this.getAttribute("data-filter");
        document.querySelectorAll("[data-filter]").forEach(function (x) { x.classList.remove("on"); });
        this.classList.add("on");
        renderActive();
      };
    });
    var catSel = $("#vhs-catsel");
    ["ALL"].concat(CAT_ORDER).forEach(function (c) {
      var o = el("option"); o.value = c; o.textContent = (c === "ALL" ? "\u5168\u90e8\u985e\u5225" : CAT_LABEL[c]); catSel.appendChild(o);
    });
    catSel.onchange = function () { STATE.catFilter = this.value; renderActive(); };
  }

  document.addEventListener("DOMContentLoaded", load);
})();
