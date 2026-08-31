#requires -Version 7.0
<#
==============================================================================
  VHS_Launch.ps1  -  Veritas HTML Spec Reader  (VIA / VPN family)
  One paste-and-run PS7 launcher.
    M01 SUP_MDL164_VHSReader.py        full-spec extractor + LOCK/EDITABLE classifier
    M02 vhs_extract.js       matrix render + LIVE computed-style extraction
    M03 VHS_ControlCenter    VPN v3.5 dark enterprise viewer
    Registry  VHS_LockRegistry.json   editable lock rules (append-only)
  Pipeline : write files -> run Python (ProcessStartInfo) -> HttpListener -> browser
  Rules    : UTF-8 No BOM, append-only, full cmdlets, no aliases, script scope.
  Usage    : just paste and run. Drop more *.html into ui_samples then re-run.
            -ScanPath to point at any folder of HTML U/I files.
==============================================================================
#>
param(
    [string]$OutRoot  = (Join-Path $env:USERPROFILE 'Downloads\VHS_HtmlSpecReader'),
    [string]$ScanPath = '',
    [int]$Port        = 8871,
    [switch]$NoLaunch
)
# ===== [VIA:PS-ACCEL:v0100] PS 20 加速器橋(批255 全樹導入;graceful 缺席零影響) =====
try {
    $VIAPSAccelProbe = $PSScriptRoot
    while ($VIAPSAccelProbe -and (Split-Path $VIAPSAccelProbe -Parent)) {
        $VIAPSAccelMod = Join-Path $VIAPSAccelProbe "supportive modules\VIA_PS_Accel_Module.ps1"
        if (Test-Path $VIAPSAccelMod) { . $VIAPSAccelMod; break }
        $VIAPSAccelProbe = Split-Path $VIAPSAccelProbe -Parent
    }
} catch { }
# ===== [VIA:PS-ACCEL:END] =====

$ErrorActionPreference = 'Stop'
$script:Root = $OutRoot
$script:Scan = if ([string]::IsNullOrWhiteSpace($ScanPath)) { Join-Path $script:Root 'ui_samples' } else { $ScanPath }
$script:Utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Write-VhsFile {
    param([string]$Path, [string]$Content)
    $dir = Split-Path -Parent $Path
    if (-not (Test-Path -LiteralPath $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    [System.IO.File]::WriteAllText($Path, $Content, $script:Utf8NoBom)
}

function Write-Step {
    param([string]$Msg, [string]$Color = 'Gray')
    Write-Host ('  ' + $Msg) -ForegroundColor $Color
}


# ---- 0. embedded modules (UTF-8 No BOM on write) ----
$script:PY_READER = @'
# -*- coding: utf-8 -*-
# ============================================================================
#  SUP_MDL164_VHSReader.py  -  Veritas HTML Spec Reader  (VIA / VPN family)
#  M01 : HTML U/I full-spec extractor + LOCK/EDITABLE classifier
#  Stdlib only (re, json, pathlib, html.parser, argparse, datetime, hashlib)
#  Append-only (zhi-zeng-bu-jian). UTF-8 No BOM in/out.
# ============================================================================
import re
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime
from html.parser import HTMLParser

VHS_VERSION = "v01.0"

# ----------------------------------------------------------------------------
#  Built-in LOCK registry (VPN v3.5 visual lock). Overridable via JSON, add-only.
# ----------------------------------------------------------------------------
DEFAULT_LOCK_REGISTRY = {
    "palette": {
        "#4c78a8": "VPN.blue",
        "#9c9890": "VPN.grey",
        "#439a9a": "VPN.teal",
    },
    "fonts": {
        "dm mono": "VPN.mono",
        "dm sans": "VPN.sans",
        "syne": "VPN.display",
    },
    "header_text": [
        "VeritasIntelligenceAnalytics Environment Governance Nexus (VEGN)",
        "VERITAS INTELLIGENCE SYSTEM",
    ],
    "marker_attrs": ["data-lock", "data-locked", "data-immutable"],
    "marker_comments": ["@lock", "lock:", "immutable", "do not edit", "\u4e0d\u53ef\u6539"],
    "var_lock_keywords": ["lock", "locked", "fixed", "brand", "vpn"],
}

HEX_RE = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
RGB_RE = re.compile(r"rgba?\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+(?:\s*,\s*[\d.]+)?\s*\)")
VAR_RE = re.compile(r"(--[a-zA-Z0-9_-]+)\s*:\s*([^;}{]+)")
FONTFAM_RE = re.compile(r"font-family\s*:\s*([^;}{]+)", re.IGNORECASE)
FONTSIZE_RE = re.compile(r"font-size\s*:\s*([^;}{]+)", re.IGNORECASE)
FONTWEIGHT_RE = re.compile(r"font-weight\s*:\s*([^;}{]+)", re.IGNORECASE)
DISPLAY_RE = re.compile(r"(?<![\w-])display\s*:\s*([^;}{]+)", re.IGNORECASE)
GRIDCOL_RE = re.compile(r"(?<![\w-])grid-template-columns\s*:\s*([^;}{]+)", re.IGNORECASE)
MAXW_RE = re.compile(r"(?<![\w-])max-width\s*:\s*([^;}{]+)", re.IGNORECASE)
GAP_RE = re.compile(r"(?<![\w-])gap\s*:\s*([^;}{]+)", re.IGNORECASE)
RADIUS_RE = re.compile(r"(?<![\w-])border-radius\s*:\s*([^;}{]+)", re.IGNORECASE)
PAD_RE = re.compile(r"(?<![\w-])padding\s*:\s*([^;}{]+)", re.IGNORECASE)
MARGIN_RE = re.compile(r"(?<![\w-])margin\s*:\s*([^;}{]+)", re.IGNORECASE)
COMMENT_RE = re.compile(r"<!--(.*?)-->", re.DOTALL)


def norm_color(c):
    c = c.strip().lower()
    if c.startswith("#") and len(c) == 4:  # expand #abc -> #aabbcc
        c = "#" + "".join(ch * 2 for ch in c[1:])
    return c


def first_font(decl):
    # first family token from a font-family declaration
    token = decl.split(",")[0].strip().strip("'\"")
    return token.lower()


class _Tag(HTMLParser):
    """Collect lightweight structural facts: title, h1, header text, logo, counts."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.title = ""
        self.h1 = ""
        self.header_texts = []
        self.logos = 0
        self.buttons = 0
        self.inputs = 0
        self.selects = 0
        self.toggles = 0
        self.sections = 0
        self.cards = 0
        self.tabs = 0
        self._stack = []
        self._cap = None  # 'title' or 'h1' or 'header'
        self._in_header_depth = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").lower()
        if tag == "title":
            self._cap = "title"
        elif tag == "h1":
            self._cap = "h1"
        elif tag in ("header",) or "header" in cls or "topbar" in cls or "masthead" in cls:
            self._in_header_depth += 1
        elif tag == "img" and self._in_header_depth > 0:
            self.logos += 1
        elif tag == "svg" and self._in_header_depth > 0:
            self.logos += 1
        if tag == "button" or a.get("role") == "button":
            self.buttons += 1
        if tag == "input":
            self.inputs += 1
            if a.get("type", "").lower() in ("checkbox", "radio"):
                self.toggles += 1
        if tag == "select":
            self.selects += 1
        if "toggle" in cls or "switch" in cls:
            self.toggles += 1
        if tag == "section" or "section" in cls:
            self.sections += 1
        if "card" in cls:
            self.cards += 1
        if "tab" in cls and "table" not in cls:
            self.tabs += 1

    def handle_endtag(self, tag):
        if tag in ("header",):
            self._in_header_depth = max(0, self._in_header_depth - 1)
        if tag == "title" and self._cap == "title":
            self._cap = None
        if tag == "h1" and self._cap == "h1":
            self._cap = None

    def handle_data(self, data):
        txt = data.strip()
        if not txt:
            return
        if self._cap == "title":
            self.title = (self.title + " " + txt).strip()
        elif self._cap == "h1":
            self.h1 = (self.h1 + " " + txt).strip()
        if self._in_header_depth > 0 and len(txt) > 1:
            self.header_texts.append(txt)


def classify_color(value, reg):
    nv = norm_color(value)
    pal = {norm_color(k): v for k, v in reg["palette"].items()}
    if nv in pal:
        return "LOCKED", "VPN palette: %s" % pal[nv]
    return "EDITABLE", "non-brand color"


def classify_font(fam, reg):
    if fam in reg["fonts"]:
        return "LOCKED", "VPN font: %s" % reg["fonts"][fam]
    return "EDITABLE", "non-brand font"


def classify_var(name, value, reg):
    low = name.lower()
    for kw in reg["var_lock_keywords"]:
        if kw in low:
            return "LOCKED", "var name keyword '%s'" % kw
    # if value resolves to a brand color -> locked
    for m in HEX_RE.findall(value) + RGB_RE.findall(value):
        st, _ = classify_color(m, reg)
        if st == "LOCKED":
            return "LOCKED", "var resolves to brand color"
    return "EDITABLE", "free token"


def classify_header(text, reg):
    t = text.strip()
    for locked in reg["header_text"]:
        if locked.lower() in t.lower() or t.lower() in locked.lower():
            return "LOCKED", "VEGN/VIS locked header string"
    return "EDITABLE", "free header text"


def spec(key, value, status, reason):
    return {"key": key, "value": value, "status": status, "reason": reason}


def scan_file(path, reg):
    raw = Path(path).read_text(encoding="utf-8", errors="replace")
    p = _Tag()
    try:
        p.feed(raw)
    except Exception:
        pass

    comments = " ".join(COMMENT_RE.findall(raw)).lower()
    has_lock_comment = any(m in comments for m in reg["marker_comments"])
    has_lock_attr = any(attr in raw.lower() for attr in reg["marker_attrs"])

    cats = {"HEADER": [], "LAYOUT": [], "COLOR": [], "TYPOGRAPHY": [],
            "DIMENSION": [], "INTERACTIVE": [], "MARKER": []}

    # ---- HEADER ----
    if p.title:
        st, rs = classify_header(p.title, reg)
        cats["HEADER"].append(spec("title", p.title, st, rs))
    if p.h1:
        st, rs = classify_header(p.h1, reg)
        cats["HEADER"].append(spec("h1", p.h1, st, rs))
    seen_h = set()
    for ht in p.header_texts[:12]:
        if ht in seen_h:
            continue
        seen_h.add(ht)
        st, rs = classify_header(ht, reg)
        cats["HEADER"].append(spec("header_text", ht, st, rs))
    cats["HEADER"].append(spec("logo_count", str(p.logos),
                               "EDITABLE", "swap allowed, keep aspect"))

    # ---- COLOR ----
    colors = {}
    for c in HEX_RE.findall(raw) + RGB_RE.findall(raw):
        nc = norm_color(c)
        colors[nc] = colors.get(nc, 0) + 1
    for c, cnt in sorted(colors.items(), key=lambda kv: -kv[1])[:40]:
        st, rs = classify_color(c, reg)
        cats["COLOR"].append(spec(c, "x%d uses" % cnt, st, rs))

    # ---- CSS VARS (mixed: color/typography/dimension parents) ----
    for name, val in VAR_RE.findall(raw):
        val = val.strip()
        st, rs = classify_var(name, val, reg)
        cats["COLOR"].append(spec(name, val, st, rs + " [css var]"))

    # ---- TYPOGRAPHY ----
    fams = {}
    for decl in FONTFAM_RE.findall(raw):
        fams[first_font(decl)] = decl.strip()
    for fam, decl in fams.items():
        st, rs = classify_font(fam, reg)
        cats["TYPOGRAPHY"].append(spec("font-family", decl, st, rs))
    for sz in sorted(set(s.strip() for s in FONTSIZE_RE.findall(raw)))[:20]:
        cats["TYPOGRAPHY"].append(spec("font-size", sz, "EDITABLE", "scale tunable"))
    for w in sorted(set(s.strip() for s in FONTWEIGHT_RE.findall(raw)))[:12]:
        cats["TYPOGRAPHY"].append(spec("font-weight", w, "EDITABLE", "weight tunable"))

    # ---- LAYOUT ----
    disp = sorted(set(s.strip() for s in DISPLAY_RE.findall(raw)))
    if disp:
        cats["LAYOUT"].append(spec("display", ", ".join(disp[:8]), "EDITABLE", "layout mode"))
    for g in sorted(set(s.strip() for s in GRIDCOL_RE.findall(raw)))[:8]:
        cats["LAYOUT"].append(spec("grid-template-columns", g, "EDITABLE", "grid structure"))
    for mw in sorted(set(s.strip() for s in MAXW_RE.findall(raw)))[:8]:
        cats["LAYOUT"].append(spec("max-width", mw, "EDITABLE", "container width"))
    for gp in sorted(set(s.strip() for s in GAP_RE.findall(raw)))[:8]:
        cats["LAYOUT"].append(spec("gap", gp, "EDITABLE", "spacing"))
    cats["LAYOUT"].append(spec("sections", str(p.sections), "EDITABLE", "count"))
    cats["LAYOUT"].append(spec("cards", str(p.cards), "EDITABLE", "count"))
    cats["LAYOUT"].append(spec("tabs", str(p.tabs), "EDITABLE", "count"))

    # ---- DIMENSION ----
    for r in sorted(set(s.strip() for s in RADIUS_RE.findall(raw)))[:12]:
        cats["DIMENSION"].append(spec("border-radius", r, "EDITABLE", "corner"))
    for pd in sorted(set(s.strip() for s in PAD_RE.findall(raw)))[:12]:
        cats["DIMENSION"].append(spec("padding", pd, "EDITABLE", "inner spacing"))
    for mg in sorted(set(s.strip() for s in MARGIN_RE.findall(raw)))[:12]:
        cats["DIMENSION"].append(spec("margin", mg, "EDITABLE", "outer spacing"))

    # ---- INTERACTIVE ----
    cats["INTERACTIVE"].append(spec("buttons", str(p.buttons), "EDITABLE", "controls"))
    cats["INTERACTIVE"].append(spec("inputs", str(p.inputs), "EDITABLE", "controls"))
    cats["INTERACTIVE"].append(spec("selects", str(p.selects), "EDITABLE", "controls"))
    cats["INTERACTIVE"].append(spec("toggles", str(p.toggles), "EDITABLE", "controls"))

    # ---- MARKER (explicit author intent) ----
    if has_lock_comment:
        cats["MARKER"].append(spec("lock-comment", "present", "LOCKED",
                                   "author marked @lock/immutable"))
    if has_lock_attr:
        cats["MARKER"].append(spec("lock-attr", "present", "LOCKED",
                                   "data-lock attribute present"))
    if not cats["MARKER"]:
        cats["MARKER"].append(spec("explicit-markers", "none", "EDITABLE",
                                   "no author lock markers"))

    locked = sum(1 for c in cats.values() for s in c if s["status"] == "LOCKED")
    editable = sum(1 for c in cats.values() for s in c if s["status"] == "EDITABLE")

    return {
        "file": Path(path).name,
        "path": str(path),
        "size_bytes": Path(path).stat().st_size,
        "sha256": hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()[:16],
        "summary": {"locked": locked, "editable": editable, "total": locked + editable},
        "categories": cats,
    }


def scan_folder(folder, reg):
    files = sorted(Path(folder).rglob("*.html"))
    out = []
    for f in files:
        if f.name.lower() in ("vhs_controlcenter.html",):
            continue  # never scan the viewer itself
        try:
            out.append(scan_file(f, reg))
        except Exception as e:
            out.append({"file": f.name, "path": str(f), "error": str(e)})
    return out


def merge_registry(base, override):
    if not override:
        return base
    out = json.loads(json.dumps(base))
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k].update(v)  # add-only merge
        elif isinstance(v, list) and isinstance(out.get(k), list):
            out[k] = sorted(set(out[k]) | set(v))
        else:
            out[k] = v
    return out


def main():
    ap = argparse.ArgumentParser(description="VHS HTML Spec Reader (M01)")
    ap.add_argument("--scan", required=True, help="folder containing HTML U/I files")
    ap.add_argument("--out", required=True, help="output JSON path")
    ap.add_argument("--registry", default="", help="optional lock-registry JSON (add-only)")
    args = ap.parse_args()

    reg = DEFAULT_LOCK_REGISTRY
    if args.registry and Path(args.registry).exists():
        try:
            ov = json.loads(Path(args.registry).read_text(encoding="utf-8"))
            reg = merge_registry(reg, ov)
        except Exception as e:
            print("[WARN] registry load failed: %s" % e)

    files = scan_folder(args.scan, reg)
    payload = {
        "meta": {
            "tool": "VHS Reader",
            "version": VHS_VERSION,
            "generated": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "scan_path": str(Path(args.scan).resolve()),
            "file_count": len(files),
        },
        "lock_registry": reg,
        "files": files,
    }
    Path(args.out).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    tl = sum(f.get("summary", {}).get("locked", 0) for f in files)
    te = sum(f.get("summary", {}).get("editable", 0) for f in files)
    print("[VHS] scanned %d file(s)  LOCKED=%d  EDITABLE=%d  -> %s"
          % (len(files), tl, te, args.out))


if __name__ == "__main__":
    main()

'@

$script:JS_EXTRACT = @'
/* ==========================================================================
 *  vhs_extract.js  -  Veritas HTML Spec Reader  (VIA / VPN family)
 *  M02 : render static spec matrix (from SUP_MDL164_VHSReader.py JSON)
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

'@

$script:HTML_CC = @'
<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>VERITAS INTELLIGENCE SYSTEM</title>
<!-- @lock VPN v3.5 visual identity : palette + fonts immutable -->
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Syne:wght@600;700;800&display=swap" rel="stylesheet">
<style>
:root{
  /* VPN v3.5 locked palette */
  --vpn-blue:#4c78a8; --vpn-grey:#9c9890; --vpn-teal:#439a9a;
  /* dark enterprise shell */
  --bg:#0f1318; --bg2:#141a21; --panel:#1a212a; --panel2:#202a35;
  --line:#2a3540; --ink:#e7ecf1; --ink-dim:#9aa7b4; --ink-faint:#6b7886;
  --lock:#d8654f; --edit:#5bb38a;
  --font-display:"Syne",sans-serif; --font-body:"DM Sans",sans-serif; --font-mono:"DM Mono",monospace;
}
*{box-sizing:border-box;}
html,body{margin:0;background:var(--bg);color:var(--ink);font-family:var(--font-body);}
a{color:inherit;}

/* header --------------------------------------------------------------- */
header.vhs-top{
  background:linear-gradient(90deg,var(--vpn-blue),#3c5f86);
  padding:16px 26px;display:flex;align-items:center;gap:16px;
  border-bottom:1px solid var(--line);
}
.vhs-mark{width:38px;height:38px;border-radius:9px;background:var(--vpn-teal);
  display:grid;place-items:center;font-family:var(--font-display);font-weight:800;
  color:#0f1318;font-size:18px;flex:0 0 auto;}
.vhs-tt{display:flex;flex-direction:column;}
.vhs-tt h1{margin:0;font-family:var(--font-display);font-weight:800;font-size:19px;letter-spacing:.3px;}
.vhs-tt p{margin:2px 0 0;font-size:12px;color:#dbe6f2;letter-spacing:1.5px;text-transform:uppercase;}

/* summary -------------------------------------------------------------- */
.vhs-summary{display:flex;gap:14px;padding:18px 26px 6px;flex-wrap:wrap;}
.vhs-stat{background:var(--panel);border:1px solid var(--line);border-radius:12px;
  padding:13px 18px;min-width:120px;}
.vhs-stat-n{font-family:var(--font-mono);font-size:22px;font-weight:500;}
.vhs-stat-l{font-size:11px;color:var(--ink-dim);margin-top:3px;letter-spacing:.4px;}
.vhs-stat.is-lock .vhs-stat-n{color:var(--lock);}
.vhs-stat.is-edit .vhs-stat-n{color:var(--edit);}
.vhs-scanpath{padding:2px 26px 14px;font-family:var(--font-mono);font-size:11px;color:var(--ink-faint);}

/* toolbar -------------------------------------------------------------- */
.vhs-bar{display:flex;gap:10px;padding:0 26px 14px;flex-wrap:wrap;align-items:center;}
.vhs-bar input,.vhs-bar select{
  background:var(--bg2);border:1px solid var(--line);color:var(--ink);
  border-radius:9px;padding:8px 12px;font-family:var(--font-body);font-size:13px;}
.vhs-bar input{min-width:240px;flex:1;}
.vhs-seg{display:flex;border:1px solid var(--line);border-radius:9px;overflow:hidden;}
.vhs-seg button{background:var(--bg2);color:var(--ink-dim);border:0;padding:8px 14px;
  font-size:12px;cursor:pointer;font-family:var(--font-body);}
.vhs-seg button.on{background:var(--vpn-blue);color:#fff;}

/* tabs ----------------------------------------------------------------- */
.vhs-tabs{display:flex;gap:8px;padding:0 26px;flex-wrap:wrap;border-bottom:1px solid var(--line);}
.vhs-tab{background:transparent;border:1px solid var(--line);border-bottom:0;
  border-radius:10px 10px 0 0;padding:9px 14px;color:var(--ink-dim);cursor:pointer;
  display:flex;align-items:center;gap:9px;font-family:var(--font-mono);font-size:12px;
  transform:translateY(1px);}
.vhs-tab.active{background:var(--panel);color:var(--ink);border-color:var(--vpn-teal);}
.vhs-mini{font-family:var(--font-mono);font-size:11px;padding:1px 6px;border-radius:6px;}
.vhs-mini.lock{background:rgba(216,101,79,.16);color:var(--lock);}
.vhs-mini.edit{background:rgba(91,179,138,.16);color:var(--edit);}
.vhs-tab-badge{display:flex;gap:4px;}

/* body ----------------------------------------------------------------- */
.vhs-stage{padding:18px 26px 60px;}
.vhs-filehead{display:flex;align-items:center;gap:14px;margin-bottom:14px;flex-wrap:wrap;}
.vhs-fh-name{font-family:var(--font-display);font-size:18px;font-weight:700;}
.vhs-fh-meta{font-family:var(--font-mono);font-size:11px;color:var(--ink-faint);}
.vhs-livebtn{margin-left:auto;background:var(--vpn-teal);color:#0f1318;border:0;
  padding:8px 14px;border-radius:9px;font-weight:600;cursor:pointer;font-size:12px;}

.vhs-cat{margin-bottom:18px;border:1px solid var(--line);border-radius:13px;overflow:hidden;background:var(--bg2);}
.vhs-cat-h{display:flex;align-items:center;justify-content:space-between;
  padding:11px 16px;background:var(--panel);border-bottom:1px solid var(--line);}
.vhs-cat-t{font-family:var(--font-mono);font-size:13px;letter-spacing:.5px;color:var(--ink);}
.vhs-cat-c{font-family:var(--font-mono);font-size:11px;color:var(--ink-faint);}

.vhs-table{display:flex;flex-direction:column;}
.vhs-row{display:grid;grid-template-columns:78px minmax(0,1.6fr) minmax(0,1fr);
  gap:14px;padding:9px 16px;align-items:center;border-bottom:1px solid rgba(42,53,64,.5);}
.vhs-row:last-child{border-bottom:0;}
.vhs-row.r-lock{background:rgba(216,101,79,.05);}
.vhs-badge{font-size:11px;text-align:center;padding:3px 0;border-radius:7px;font-weight:600;}
.b-lock{background:rgba(216,101,79,.16);color:var(--lock);border:1px solid rgba(216,101,79,.4);}
.b-edit{background:rgba(91,179,138,.13);color:var(--edit);border:1px solid rgba(91,179,138,.35);}
.vhs-kv{display:flex;flex-direction:column;gap:2px;min-width:0;}
.vhs-k{font-family:var(--font-mono);font-size:12px;color:var(--ink);}
.vhs-v{font-size:12px;color:var(--ink-dim);word-break:break-all;}
.vhs-reason{font-size:11px;color:var(--ink-faint);}

.vhs-empty{padding:30px;text-align:center;color:var(--ink-faint);font-size:13px;}
.vhs-livebox{margin-top:8px;}

@media(max-width:720px){
  .vhs-row{grid-template-columns:64px 1fr;}
  .vhs-reason{grid-column:1/-1;padding-left:78px;}
}
</style>
</head>
<body>
<header class="vhs-top" data-lock="true">
  <div class="vhs-mark">V</div>
  <div class="vhs-tt">
    <h1>VHS \u00b7 HTML U/I \u5168\u898f\u683c\u8b80\u53d6\u5668</h1>
    <p>VERITAS INTELLIGENCE SYSTEM</p>
  </div>
</header>

<div class="vhs-summary" id="vhs-summary"></div>
<div class="vhs-scanpath" id="vhs-scanpath"></div>

<div class="vhs-bar">
  <input id="vhs-search" placeholder="\u641c\u5c0b key / value / reason\u2026">
  <select id="vhs-catsel"></select>
  <div class="vhs-seg">
    <button data-filter="ALL" class="on">\u5168\u90e8</button>
    <button data-filter="LOCK">\u50c5\u4e0d\u53ef\u6539</button>
    <button data-filter="EDIT">\u50c5\u53ef\u6539</button>
  </div>
</div>

<div class="vhs-tabs" id="vhs-tabs"></div>
<div class="vhs-stage"><div id="vhs-files"></div></div>

<script src="./vhs_extract.js"></script>
</body>
</html>

'@

$script:HTML_SAMPLE1 = @'
<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="utf-8">
<title>VERITAS INTELLIGENCE SYSTEM</title>
<!-- @lock brand visual identity VPN v3.5 -->
<style>
:root{
  --vpn-blue:#4c78a8; --vpn-grey:#9c9890; --vpn-teal:#439a9a;
  --bg:#14181d; --panel:#1c232b; --accent:#e0b450;
  --font-display:"Syne",sans-serif; --font-body:"DM Sans",sans-serif; --font-mono:"DM Mono",monospace;
}
body{background:var(--bg);font-family:var(--font-body);margin:0;color:#e8e8e8;}
header{display:flex;background:var(--vpn-blue);padding:18px 28px;}
.wrap{max-width:1240px;margin:0 auto;display:grid;grid-template-columns:repeat(3,1fr);gap:20px;}
.card{background:var(--panel);border-radius:12px;padding:20px;}
h1{font-family:var(--font-display);font-size:22px;font-weight:700;}
.tab{font-size:14px;}
button{font-weight:600;border-radius:8px;}
</style></head>
<body>
<header data-lock="true"><img src="logo.svg" alt="logo"><h1>VERITAS INTELLIGENCE SYSTEM</h1></header>
<div class="wrap">
  <section class="card"><div class="tab">Overview</div><button>Run scan</button></section>
  <section class="card"><input type="text"><select><option>A</option></select></section>
  <section class="card"><label class="toggle"><input type="checkbox"></label></section>
</div>
</body></html>

'@

$script:HTML_SAMPLE2 = @'
<!DOCTYPE html>
<html lang="zh-TW"><head><meta charset="utf-8">
<title>My Custom Report</title>
<style>
:root{--brand-primary:#4c78a8;--free-accent:#ff6b35;--free-bg:#fafafa;}
body{background:var(--free-bg);font-family:"Inter",sans-serif;color:#222;margin:0;}
header{display:block;background:#ff6b35;padding:24px;}
.container{max-width:980px;margin:0 auto;}
.card{border-radius:6px;padding:16px;margin:12px;}
h1{font-family:"Georgia",serif;font-size:28px;font-weight:400;}
button{border-radius:4px;}
</style></head>
<body>
<header><h1>My Custom Report</h1></header>
<div class="container">
  <section class="card">free editable content</section>
  <button>Export</button><button>Print</button>
  <input type="search"><input type="checkbox">
</div>
</body></html>

'@

$script:JSON_REGISTRY = @'
{
  "palette": {
    "#4c78a8": "VPN.blue",
    "#9c9890": "VPN.grey",
    "#439a9a": "VPN.teal"
  },
  "fonts": {
    "dm mono": "VPN.mono",
    "dm sans": "VPN.sans",
    "syne": "VPN.display"
  },
  "header_text": [
    "VeritasIntelligenceAnalytics Environment Governance Nexus (VEGN)",
    "VERITAS INTELLIGENCE SYSTEM"
  ],
  "marker_attrs": [
    "data-lock",
    "data-locked",
    "data-immutable"
  ],
  "marker_comments": [
    "@lock",
    "lock:",
    "immutable",
    "do not edit",
    "不可改"
  ],
  "var_lock_keywords": [
    "lock",
    "locked",
    "fixed",
    "brand",
    "vpn"
  ]
}
'@


# ---- 1. materialise files -------------------------------------------------
Write-Host ''
Write-Host '  VHS  HTML U/I Full-Spec Reader  (VPN v3.5)' -ForegroundColor Cyan
Write-Host '  ------------------------------------------' -ForegroundColor DarkGray

if (-not (Test-Path -LiteralPath $script:Root)) {
    New-Item -ItemType Directory -Path $script:Root -Force | Out-Null
}
$script:SampleDir = Join-Path $script:Root 'ui_samples'
if (-not (Test-Path -LiteralPath $script:SampleDir)) {
    New-Item -ItemType Directory -Path $script:SampleDir -Force | Out-Null
}

Write-VhsFile (Join-Path $script:Root 'SUP_MDL164_VHSReader.py')          $script:PY_READER
Write-VhsFile (Join-Path $script:Root 'vhs_extract.js')         $script:JS_EXTRACT
Write-VhsFile (Join-Path $script:Root 'VHS_ControlCenter.html') $script:HTML_CC
Write-VhsFile (Join-Path $script:Root 'VHS_LockRegistry.json')  $script:JSON_REGISTRY

# sample U/I files are written ONLY if absent (append-only, never overwrite user files)
$script:Smp1 = Join-Path $script:SampleDir 'dashboard.html'
$script:Smp2 = Join-Path $script:SampleDir 'report.html'
if (-not (Test-Path -LiteralPath $script:Smp1)) { Write-VhsFile $script:Smp1 $script:HTML_SAMPLE1 }
if (-not (Test-Path -LiteralPath $script:Smp2)) { Write-VhsFile $script:Smp2 $script:HTML_SAMPLE2 }
Write-Step ('files ready  -> ' + $script:Root) 'DarkGray'

# ---- 2. resolve python (py launcher first, per VIA convention) ------------
function Test-PyCandidate {
    param([string]$Exe, [string]$Lead)
    try {
        $p = [System.Diagnostics.ProcessStartInfo]::new()
        $p.FileName = $Exe
        $p.Arguments = (($Lead + ' --version').Trim())
        $p.UseShellExecute = $false
        $p.RedirectStandardOutput = $true
        $p.RedirectStandardError = $true
        $p.CreateNoWindow = $true
        $proc = [System.Diagnostics.Process]::Start($p)
        $proc.WaitForExit(5000) | Out-Null
        return ($proc.ExitCode -eq 0)
    } catch { return $false }
}

$script:PyExe = $null
$script:PyLead = ''
foreach ($cand in @(
        @{ Exe = 'py';      Lead = '-3.12' },
        @{ Exe = 'py';      Lead = '-3.11' },
        @{ Exe = 'py';      Lead = '-3'    },
        @{ Exe = 'python';  Lead = ''      },
        @{ Exe = 'python3'; Lead = ''      })) {
    if (Test-PyCandidate -Exe $cand.Exe -Lead $cand.Lead) {
        $script:PyExe = $cand.Exe
        $script:PyLead = $cand.Lead
        break
    }
}
if ($null -eq $script:PyExe) {
    Write-Host '  [ERROR] No Python 3 found (py / python / python3). Install Python 3.x and re-run.' -ForegroundColor Red
    return
}
Write-Step ('python    -> ' + ($script:PyExe + ' ' + $script:PyLead).Trim()) 'DarkGray'

# ---- 3. run the extractor (ProcessStartInfo) ------------------------------
$script:OutJson = Join-Path $script:Root 'vhs_specs.json'
$script:ReaderPy = Join-Path $script:Root 'SUP_MDL164_VHSReader.py'
$script:RegPath = Join-Path $script:Root 'VHS_LockRegistry.json'
$argStr = ($script:PyLead + ' "' + $script:ReaderPy + '" --scan "' + $script:Scan +
           '" --out "' + $script:OutJson + '" --registry "' + $script:RegPath + '"').Trim()

$psi = [System.Diagnostics.ProcessStartInfo]::new()
$psi.FileName = $script:PyExe
$psi.Arguments = $argStr
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.CreateNoWindow = $true
$proc = [System.Diagnostics.Process]::Start($psi)
$stdout = $proc.StandardOutput.ReadToEnd()
$stderr = $proc.StandardError.ReadToEnd()
$proc.WaitForExit()
if ($stdout) { Write-Step $stdout.Trim() 'Green' }
if ($proc.ExitCode -ne 0) {
    Write-Host '  [ERROR] extractor failed:' -ForegroundColor Red
    Write-Host $stderr -ForegroundColor DarkRed
    return
}

# ---- 4. pick a free port --------------------------------------------------
function Get-Mime {
    param([string]$Path)
    $map = [ordered]@{
        '.html' = 'text/html; charset=utf-8'
        '.js'   = 'application/javascript; charset=utf-8'
        '.json' = 'application/json; charset=utf-8'
        '.css'  = 'text/css; charset=utf-8'
        '.svg'  = 'image/svg+xml'
        '.png'  = 'image/png'
        '.ico'  = 'image/x-icon'
    }
    $ext = [System.IO.Path]::GetExtension($Path).ToLower()
    if ($map.Contains($ext)) { return $map[$ext] }
    return 'application/octet-stream'
}

$script:Listener = $null
$script:UsePort = $Port
for ($i = 0; $i -lt 25; $i++) {
    $try = $Port + $i
    try {
        $l = [System.Net.HttpListener]::new()
        $l.Prefixes.Add("http://127.0.0.1:$try/")
        $l.Start()
        $script:Listener = $l
        $script:UsePort = $try
        break
    } catch {
        if ($null -ne $l) { $l.Close() }
    }
}
if ($null -eq $script:Listener) {
    Write-Host '  [ERROR] No free port in range.' -ForegroundColor Red
    return
}
$script:Url = "http://127.0.0.1:$($script:UsePort)/VHS_ControlCenter.html"
Write-Step ('server    -> ' + $script:Url) 'Cyan'

# ---- 5. open browser + serve ---------------------------------------------
if (-not $NoLaunch) { Start-Process $script:Url }
Write-Host ''
Write-Host '  LIVE. Press Ctrl+C to stop the server.' -ForegroundColor Yellow
Write-Host ''

try {
    while ($script:Listener.IsListening) {
        $ctx = $script:Listener.GetContext()
        $rel = [Uri]::UnescapeDataString($ctx.Request.Url.AbsolutePath.TrimStart('/'))
        if ([string]::IsNullOrWhiteSpace($rel)) { $rel = 'VHS_ControlCenter.html' }
        $full = Join-Path $script:Root $rel
        try {
            if (Test-Path -LiteralPath $full -PathType Leaf) {
                $bytes = [System.IO.File]::ReadAllBytes($full)
                $ctx.Response.ContentType = (Get-Mime $full)
                $ctx.Response.ContentLength64 = $bytes.Length
                $ctx.Response.OutputStream.Write($bytes, 0, $bytes.Length)
            } else {
                $ctx.Response.StatusCode = 404
                $nf = [System.Text.Encoding]::UTF8.GetBytes('404 not found: ' + $rel)
                $ctx.Response.OutputStream.Write($nf, 0, $nf.Length)
            }
        } catch {
            $ctx.Response.StatusCode = 500
        } finally {
            $ctx.Response.Close()
        }
    }
} finally {
    if ($null -ne $script:Listener) { $script:Listener.Stop(); $script:Listener.Close() }
    Write-Host '  server stopped.' -ForegroundColor DarkGray
}

