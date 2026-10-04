#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG234_UiLauncher v0100 — VDF 啟動檔:HTML U/I + 自適應式對接任何視覺模板(操作員 2026-10-04)

一支做三件事,零必裝依賴(只用標準庫;fastapi / jinja2 在就用,不在也跑):
  ① 啟動:本機 HTTP(127.0.0.1:8765)· 1.5 秒後開預設瀏覽器 · 內建標準模板(VIA_UI_FormatLock 鎖定色 · 四燈 · 卡片 · 表單 · 資料表 · 參數面板)
  ② 參數:ui_config.json(app_title · theme · layout · active_template · data 範圍);改了重新整理即生效,不重啟
  ③ 自適應對接:templates\ 夾裡丟任何 .html,系統自動 — (a) 讀出模板宣告的變數(Jinja 語法或 {{x.y}} 字面)對映到 config / data;
     (b) 沒有 Jinja 的純 HTML:注入 <script>window.VIA = {config,data}</script> + FormatLock CSS 變數 + 四燈 lamp_css(紅燈慢閃),模板原碼一字不改;
     (c) 模板自帶 :root 色票就不蓋(尊重模板);缺的燈類補上;(d) 清單頁 /templates 列出所有可用模板,點一下切換(寫回 ui_config.json)
資料 API(只讀,零網路,零寫庫):/api/config · /api/universe(OUT-01 再生件)· /api/etf(ActiveTWETF holdings_daily 最新日)· /api/readiness(ENGINE_READINESS_latest)·
  /api/filemap(VIA_FILE_MAP_latest)· /api/panorama(SSOT_PANORAMA latest json 若在)· /api/templates
用法  VIA_FROM_VCGC=YES python VDF_ENG234_UiLauncher_v0100.py serve [--port 8765] [--no-open] [--template X.html]
      python VDF_ENG234_UiLauncher_v0100.py render [--template X.html] → 印出渲染後 HTML(給 CI / 另存)
      python VDF_ENG234_UiLauncher_v0100.py --selftest
"""
from __future__ import annotations
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(批102 全樹導入令;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: N816
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
import csv, html, json, os, re, sys, threading, time, webbrowser
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ENGINE = "VDF_ENG234_UiLauncher_v0100"
HERE = Path(__file__).resolve().parent
VIA = next((p for p in [HERE] + list(HERE.parents) if (p / "supportive modules").is_dir()), HERE)
UI_DIR = VIA / "functional modules" / "VDF" / "ui"; TPL_DIR = UI_DIR / "templates"
CONFIG_PATH = UI_DIR / "ui_config.json"
PAL = {"GREEN": "#16a34a", "YELLOW": "#f59e0b", "RED": "#dc2626", "GRAY": "#9ca3af", "NODATA": "#0891b2", "text_GREEN": "#15803d", "text_YELLOW": "#b45309", "text_RED": "#b91c1c"}
LAMP_CSS = ("@keyframes via-blink{0%,100%{opacity:1}50%{opacity:.25}}.lamp{display:inline-block;width:12px;height:12px;border-radius:50%;vertical-align:middle;margin-right:4px;border:1px solid rgba(0,0,0,.15)}"
            ".lamp.GREEN{background:var(--lamp-green)}.lamp.YELLOW{background:var(--lamp-yellow)}.lamp.RED{background:var(--lamp-red);animation:via-blink 1.8s ease-in-out infinite}.lamp.GRAY,.lamp.SKIP,.lamp.HOLD,.lamp.TIMEOUT{background:var(--lamp-gray)}.lamp.NODATA{background:var(--lamp-nodata)}"
            "@media (prefers-reduced-motion: reduce){.lamp.RED{animation:none}}")

DEFAULT_CONFIG = {"app_title": "VIA · VDF 資料面板", "active_template": None, "port": 8765,
                  "theme": {"primary_color": "#1f2937", "bg_color": "#ffffff", "font_family": "Arial, 'Microsoft JhengHei', sans-serif", "font_px": 12},
                  "layout": {"sidebar_width": "230px", "show_sidebar": True, "show_header": True},
                  "data": {"universe_rows": 50, "etf_rows": 50, "readiness_rows": 200}}

DEFAULT_HTML = """<!doctype html><html lang="zh-TW"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{{ config.app_title }}</title>
<style>
:root{--primary:{{ config.theme.primary_color }};--bg:{{ config.theme.bg_color }};--font:{{ config.theme.font_family }};--fs:{{ config.theme.font_px }}px;--sidebar:{{ config.layout.sidebar_width }};--border:#e0e0e0;
--lamp-green:{{ pal.GREEN }};--lamp-yellow:{{ pal.YELLOW }};--lamp-red:{{ pal.RED }};--lamp-gray:{{ pal.GRAY }};--lamp-nodata:{{ pal.NODATA }}}
body{margin:0;font:var(--fs) var(--font);background:var(--bg);color:#111827;display:flex;height:100vh}
.sidebar{width:var(--sidebar);background:#fff;border-right:1px solid var(--border);display:{{ 'flex' if config.layout.show_sidebar else 'none' }};flex-direction:column}
.sidebar h2{margin:0;padding:16px;font-size:16px;color:var(--primary);border-bottom:1px solid var(--border)}
.menu a{display:block;padding:10px 16px;color:#111827;text-decoration:none}.menu a:hover{background:#f5f5f5;border-left:4px solid var(--primary)}
.main{flex:1;display:flex;flex-direction:column;overflow:hidden}.top{background:#fff;padding:10px 20px;border-bottom:1px solid var(--border);display:{{ 'flex' if config.layout.show_header else 'none' }};justify-content:space-between;align-items:center}
.content{padding:18px;overflow:auto;flex:1}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:14px;margin-bottom:18px}
.card{background:#fff;border:1px solid var(--border);border-radius:8px;padding:14px}.card .t{color:#6b7280;font-size:11px}.card .v{font-size:24px;font-weight:600;color:var(--primary)}
table{border-collapse:collapse;width:100%;background:#fff}th,td{border:1px solid var(--border);padding:4px 7px;text-align:left}th{background:#f7f7f7;position:sticky;top:0}
.btn{background:var(--primary);color:#fff;border:0;padding:7px 14px;border-radius:6px;cursor:pointer}.btn.o{background:transparent;color:var(--primary);border:1px solid var(--primary)}
input,select{padding:6px 8px;border:1px solid var(--border);border-radius:6px;font:inherit}.row{display:grid;grid-template-columns:1fr 2fr;gap:14px;align-items:start}label{display:block;font-size:11px;color:#374151;margin:8px 0 3px}
{{ lamp_css }}
</style></head><body>
<div class="sidebar"><h2>{{ config.app_title }}</h2><div class="menu"><a href="#universe">📋 全台股清單</a><a href="#etf">📈 主動 ETF 持股</a><a href="#readiness">🧪 引擎自測矩陣</a><a href="#filemap">🗂 檔案位置</a><a href="/templates">🎨 模板(自適應)</a></div>
<div style="margin-top:auto;padding:12px;font-size:11px;color:#6b7280">{{ engine }} · 內建標準模板 · 色 = VIA_UI_FormatLock</div></div>
<div class="main"><div class="top"><div style="font-size:15px;font-weight:500">VDF 資料面板</div><div><i class="lamp {{ data.overall }}"></i>{{ data.overall_zh }} · {{ data.at }}</div></div>
<div class="content">
<div class="cards"><div class="card"><div class="t">全台股清單(OUT-01)</div><div class="v">{{ data.universe_n }}</div><div class="t">{{ data.universe_src }}</div></div>
<div class="card"><div class="t">主動 ETF 持股列(最新日)</div><div class="v">{{ data.etf_n }}</div><div class="t">{{ data.etf_date }}</div></div>
<div class="card"><div class="t">引擎自測</div><div class="v"><i class="lamp GREEN"></i>{{ data.r_green }} <i class="lamp RED"></i>{{ data.r_red }} <i class="lamp GRAY"></i>{{ data.r_other }}</div><div class="t">ENGINE_READINESS_latest</div></div>
<div class="card"><div class="t">檔案位置清單</div><div class="v"><i class="lamp GREEN"></i>{{ data.fm_green }} <i class="lamp YELLOW"></i>{{ data.fm_yellow }} <i class="lamp RED"></i>{{ data.fm_red }}</div><div class="t">VIA_FILE_MAP_latest</div></div></div>
<div class="row"><div class="card"><div style="font-weight:600;border-bottom:1px solid var(--border);padding-bottom:6px;margin-bottom:6px">參數面板(ui_config.json)</div>
<form method="post" action="/config"><label>app_title</label><input name="app_title" value="{{ config.app_title }}" style="width:100%"><label>primary_color</label><input name="primary_color" value="{{ config.theme.primary_color }}"><label>sidebar_width</label><input name="sidebar_width" value="{{ config.layout.sidebar_width }}">
<label>active_template(空 = 內建)</label><select name="active_template"><option value="">內建標準模板</option>{% for t in data.templates %}<option value="{{ t }}" {{ 'selected' if t == config.active_template else '' }}>{{ t }}</option>{% endfor %}</select>
<div style="margin-top:12px"><button class="btn" type="submit">套用(寫回 ui_config.json)</button> <a class="btn o" href="/">重新整理</a></div></form></div>
<div class="card" id="readiness"><div style="font-weight:600">引擎自測矩陣(前 {{ data.readiness|length }})</div><div style="max-height:260px;overflow:auto"><table><tr><th>燈</th><th>家族</th><th>引擎</th><th>判決</th></tr>{% for r in data.readiness %}<tr><td><i class="lamp {{ r.lamp }}"></i>{{ r.lamp }}</td><td>{{ r.fam }}</td><td>{{ r.engine }}</td><td>{{ r.verdict }}</td></tr>{% endfor %}</table></div></div></div>
<div class="card" id="universe" style="margin-top:14px"><div style="font-weight:600">全台股清單 OUT-01(前 {{ data.universe|length }} · 介面表頭 Title Case)</div><div style="max-height:300px;overflow:auto"><table><tr>{% for h in data.universe_header %}<th>{{ h }}</th>{% endfor %}</tr>{% for row in data.universe %}<tr>{% for c in row %}<td>{{ c }}</td>{% endfor %}</tr>{% endfor %}</table></div></div>
<div class="card" id="etf" style="margin-top:14px"><div style="font-weight:600">主動 ETF 每日持股 OUT-03(前 {{ data.etf|length }})</div><div style="max-height:300px;overflow:auto"><table><tr>{% for h in data.etf_header %}<th>{{ h }}</th>{% endfor %}</tr>{% for row in data.etf %}<tr>{% for c in row %}<td>{{ c }}</td>{% endfor %}</tr>{% endfor %}</table></div></div>
<div class="card" id="filemap" style="margin-top:14px"><div style="font-weight:600">檔案位置(紅 / 無版號優先)</div><div style="max-height:260px;overflow:auto"><table><tr><th>燈</th><th>系統</th><th>類</th><th>名</th><th>版</th></tr>{% for r in data.filemap %}<tr><td><i class="lamp {{ r.燈 }}"></i>{{ r.燈 }}</td><td>{{ r.系統 }}</td><td>{{ r.類 }}</td><td>{{ r.名 }}</td><td>{{ r.版 }}</td></tr>{% endfor %}</table></div></div>
</div></div>
<script>window.VIA={config:{{ config_json }},data_keys:{{ data_keys_json }}};</script>
</body></html>"""


# ---------------- 迷你渲染器(jinja2 在就用 jinja2;不在用這個:{{ a.b|length }} · {% if %} · {% for %}) ----------------
def _get(ctx, path: str):
    cur = ctx
    for part in path.strip().split("."):
        if isinstance(cur, dict):
            cur = cur.get(part)
        else:
            cur = getattr(cur, part, None)
        if cur is None:
            return ""
    return cur


def _expr(ctx, e: str):
    e = e.strip()
    m = re.match(r"^'([^']*)'\s+if\s+(.+?)\s+else\s+'([^']*)'$", e)
    if m:
        return m.group(1) if _truth(ctx, m.group(2)) else m.group(3)
    if "|length" in e:
        v = _get(ctx, e.split("|")[0]); return len(v) if hasattr(v, "__len__") else 0
    if e.startswith("'") and e.endswith("'"):
        return e[1:-1]
    return _get(ctx, e)


def _truth(ctx, cond: str) -> bool:
    cond = cond.strip()
    m = re.match(r"^(\S+)\s*==\s*(\S+)$", cond)
    if m:
        return str(_expr(ctx, m.group(1))) == str(_expr(ctx, m.group(2)))
    v = _expr(ctx, cond)
    return bool(v) and v not in ("", "None", "False")


def mini_render(tpl: str, ctx: dict) -> str:
    def render_block(s: str) -> str:
        # for loops (innermost first)
        pat = re.compile(r"\{%\s*for\s+(\w+)\s+in\s+([\w\.]+)\s*%\}(.*?)\{%\s*endfor\s*%\}", re.S)
        while True:
            m = pat.search(s)
            if not m:
                break
            var, seq, body = m.group(1), m.group(2), m.group(3)
            items = _get(ctx, seq) or []
            out = []
            for it in items:
                sub = dict(ctx); sub[var] = it
                out.append(mini_render(body, sub))
            s = s[:m.start()] + "".join(out) + s[m.end():]
        pat_if = re.compile(r"\{%\s*if\s+(.+?)\s*%\}(.*?)\{%\s*endif\s*%\}", re.S)
        while True:
            m = pat_if.search(s)
            if not m:
                break
            s = s[:m.start()] + (m.group(2) if _truth(ctx, m.group(1)) else "") + s[m.end():]
        return re.sub(r"\{\{\s*(.+?)\s*\}\}", lambda mm: str(_expr(ctx, mm.group(1))), s)
    return render_block(tpl)


def render(tpl: str, ctx: dict) -> str:
    try:
        import jinja2
        return jinja2.Environment(autoescape=False).from_string(tpl).render(**ctx)
    except ImportError:
        return mini_render(tpl, ctx)


# ---------------- 參數 ----------------
def load_config() -> dict:
    cfg = json.loads(json.dumps(DEFAULT_CONFIG))
    if CONFIG_PATH.is_file():
        try:
            user = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            for k, v in user.items():
                if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                    cfg[k].update(v)
                else:
                    cfg[k] = v
        except Exception:
            pass
    # FormatLock 尾版的字型 / 燈色優先(鎖定色)
    try:
        books = sorted((VIA / "supportive modules" / "registry").glob("VIA_UI_FormatLock_v*.json"))
        if books:
            tk = json.loads(books[-1].read_text(encoding="utf-8")).get("tokens") or {}
            for k in ("GREEN", "YELLOW", "RED", "GRAY", "NODATA"):
                if tk.get("lamp_" + k):
                    PAL[k] = tk["lamp_" + k]
            if tk.get("font_family"):
                cfg["theme"]["font_family"] = tk["font_family"]
    except Exception:
        pass
    return cfg


def save_config(patch: dict) -> None:
    cur = json.loads(CONFIG_PATH.read_text(encoding="utf-8")) if CONFIG_PATH.is_file() else {}
    for k, v in patch.items():
        if isinstance(v, dict):
            cur.setdefault(k, {}).update(v)
        else:
            cur[k] = v
    UI_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(cur, ensure_ascii=False, indent=1), encoding="utf-8")


# ---------------- 資料(只讀) ----------------
def _title(s: str) -> str:
    ACR = {"eps", "etf", "id", "yf", "bb", "twse", "tpex", "pb", "pe", "roe", "nav", "aum", "url"}
    return " ".join(w.upper() if w.lower() in ACR else w[:1].upper() + w[1:].lower() for w in re.split(r"[_\s]+", s) if w)


def _read_csv(path: Path, limit: int):
    if not path.is_file():
        return [], []
    with open(path, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    if not rows:
        return [], []
    return rows[0], rows[1:1 + limit]


def load_data(cfg: dict) -> dict:
    d = {"at": datetime.now().strftime("%Y-%m-%d %H:%M"), "templates": list_templates()}
    uni_json = VIA / "VIA_Reports" / "vdf" / "universe" / "VDF_UNIVERSE_latest.json"; uni_csv = uni_json.with_suffix(".csv")
    hdr, rows = _read_csv(uni_csv, cfg["data"]["universe_rows"])
    d["universe_header"] = [_title(h) for h in hdr]; d["universe"] = rows; d["universe_src"] = uni_csv.name if hdr else "再生件未產(跑 VDF_SystemManager universe)"
    n_all = 0
    if uni_csv.is_file():
        with open(uni_csv, encoding="utf-8-sig") as f:
            n_all = max(0, sum(1 for _ in f) - 1)
    d["universe_n"] = n_all if n_all else "—"
    d["etf_header"], d["etf"], d["etf_date"], d["etf_n"] = [], [], "—", "—"
    try:
        import duckdb
        home = Path(os.environ.get("VIA_DATA_HOME") or r"C:\Users\tonyk\VIA System\via_database")
        for cand in (home / "ActiveTWETF.duckdb", VIA / "functional modules" / "VDF" / "output_hub" / "ActiveTWETF.duckdb"):
            if cand.is_file():
                con = duckdb.connect(str(cand), read_only=True)
                dt = con.execute("SELECT max(portfolio_date) FROM holdings_daily").fetchone()[0]
                cur = con.execute("SELECT etf_ticker, etf_name, holding_ticker, holding_name, weight_pct, shares FROM holdings_daily WHERE portfolio_date = ? ORDER BY etf_ticker, weight_pct DESC LIMIT ?", [dt, cfg["data"]["etf_rows"]])
                d["etf_header"] = [_title(c[0]) for c in cur.description]; d["etf"] = [[str(x) for x in r] for r in cur.fetchall()]
                d["etf_n"] = con.execute("SELECT count(*) FROM holdings_daily WHERE portfolio_date = ?", [dt]).fetchone()[0]; d["etf_date"] = str(dt); con.close(); break
    except Exception as e:  # duckdb 缺 / 庫不在 = 誠實空
        d["etf_date"] = f"NODATA({type(e).__name__})"
    hdr, rows = _read_csv(VIA / "VIA_Reports" / "review" / "ENGINE_READINESS_latest.csv", cfg["data"]["readiness_rows"])
    idx = {h: i for i, h in enumerate(hdr)}
    rd = [{"fam": r[idx.get("家族", 0)], "engine": r[idx.get("引擎", 1)], "lamp": r[idx.get("燈", 2)], "verdict": (r[idx.get("判決", 5)] if len(r) > 5 else "")} for r in rows if len(r) > 2]
    rd.sort(key=lambda x: {"RED": 0, "TIMEOUT": 1, "NODATA": 2, "GREEN": 3}.get(x["lamp"], 4))
    d["readiness"] = rd; d["r_green"] = sum(1 for x in rd if x["lamp"] == "GREEN"); d["r_red"] = sum(1 for x in rd if x["lamp"] == "RED"); d["r_other"] = len(rd) - d["r_green"] - d["r_red"]
    fm = VIA / "VIA_Reports" / "review" / "VIA_FILE_MAP_latest.json"; fmr = []
    if fm.is_file():
        try:
            fmr = json.loads(fm.read_text(encoding="utf-8")); fmr = fmr if isinstance(fmr, list) else []
        except Exception:
            fmr = []
    fmr.sort(key=lambda r: {"RED": 0, "YELLOW": 1}.get(r.get("燈"), 2)); d["filemap"] = fmr[:120]
    d["fm_green"] = sum(1 for r in fmr if r.get("燈") == "GREEN"); d["fm_yellow"] = sum(1 for r in fmr if r.get("燈") == "YELLOW"); d["fm_red"] = sum(1 for r in fmr if r.get("燈") == "RED")
    d["overall"] = "RED" if (d["r_red"] or d["fm_red"]) else ("YELLOW" if d["fm_yellow"] or d["r_other"] else ("GREEN" if rd else "GRAY"))
    d["overall_zh"] = {"RED": "有紅", "YELLOW": "有黃", "GREEN": "全綠", "GRAY": "沒料"}[d["overall"]]
    return d


# ---------------- 自適應模板對接 ----------------
def list_templates() -> list:
    return sorted(p.name for p in TPL_DIR.glob("*.html")) if TPL_DIR.is_dir() else []


def adapt_template(src: str, ctx: dict) -> tuple[str, dict]:
    """任何 HTML → 可渲染頁。回 (html, 報告)。模板原碼不改,只注入缺的東西。"""
    rep = {"jinja_vars": sorted(set(re.findall(r"\{\{\s*([\w\.]+)", src))), "has_root": bool(re.search(r":root\s*\{", src)), "has_lamp": ".lamp" in src, "injected": []}
    out = src
    if rep["jinja_vars"] or "{%" in src:
        out = render(out, ctx)                       # (a) 宣告變數對映:config / data / pal / engine
    inject_css = ""
    if not rep["has_root"]:
        c = ctx["config"]; inject_css += (f":root{{--primary:{c['theme']['primary_color']};--bg:{c['theme']['bg_color']};--font:{c['theme']['font_family']};--sidebar:{c['layout']['sidebar_width']};"
                                            f"--lamp-green:{PAL['GREEN']};--lamp-yellow:{PAL['YELLOW']};--lamp-red:{PAL['RED']};--lamp-gray:{PAL['GRAY']};--lamp-nodata:{PAL['NODATA']}}}"); rep["injected"].append("root-tokens")
    else:
        inject_css += f":root{{--lamp-green:{PAL['GREEN']};--lamp-yellow:{PAL['YELLOW']};--lamp-red:{PAL['RED']};--lamp-gray:{PAL['GRAY']};--lamp-nodata:{PAL['NODATA']}}}"; rep["injected"].append("lamp-tokens-only(尊重模板色票)")
    if not rep["has_lamp"]:
        inject_css += LAMP_CSS; rep["injected"].append("lamp-css")
    bridge = f"<script>window.VIA={{config:{json.dumps(ctx['config'], ensure_ascii=False)},data:{json.dumps({k: v for k, v in ctx['data'].items() if k not in ('templates',)}, ensure_ascii=False, default=str)}}};</script>"
    rep["injected"].append("window.VIA bridge")
    head_block = f"<style data-via='adapt'>{inject_css}</style>{bridge}"
    if re.search(r"</head>", out, re.I):
        out = re.sub(r"</head>", head_block + "</head>", out, count=1, flags=re.I)
    else:
        out = head_block + out; rep["injected"].append("no-head→prepend")
    return out, rep


def build_context(cfg: dict) -> dict:
    data = load_data(cfg)
    return {"config": cfg, "data": data, "pal": PAL, "engine": ENGINE, "lamp_css": LAMP_CSS, "config_json": json.dumps(cfg, ensure_ascii=False), "data_keys_json": json.dumps(sorted(data.keys()), ensure_ascii=False)}


def render_page(template: str | None = None) -> tuple[str, dict]:
    cfg = load_config(); name = template or cfg.get("active_template"); ctx = build_context(cfg)
    if name and (TPL_DIR / name).is_file():
        return adapt_template((TPL_DIR / name).read_text(encoding="utf-8", errors="replace"), ctx)
    return render(DEFAULT_HTML, ctx), {"template": "builtin", "injected": []}


# ---------------- HTTP ----------------
class H(BaseHTTPRequestHandler):
    def log_message(self, *a):  # 安靜
        pass

    def _send(self, body: str, ctype="text/html; charset=utf-8", code=200):
        b = body.encode("utf-8"); self.send_response(code); self.send_header("Content-Type", ctype); self.send_header("Content-Length", str(len(b))); self.end_headers(); self.wfile.write(b)

    def do_GET(self):
        u = urlparse(self.path); q = parse_qs(u.query)
        try:
            if u.path == "/":
                page, _ = render_page(q.get("template", [None])[0]); return self._send(page)
            if u.path == "/templates":
                cfg = load_config(); items = "".join(f"<li><a href='/?template={html.escape(t)}'>{html.escape(t)}</a>{' · 現役' if t == cfg.get('active_template') else ''}</li>" for t in list_templates()) or "<li>(templates\\ 夾還是空的:丟任何 .html 進去就會出現在這裡)</li>"
                return self._send(f"<!doctype html><meta charset='utf-8'><body style='font:12px Arial'><h3>可用模板(自適應對接)</h3><ul>{items}</ul><p>夾:{html.escape(str(TPL_DIR))}</p><a href='/'>回面板</a></body>")
            if u.path == "/api/config":
                return self._send(json.dumps(load_config(), ensure_ascii=False), "application/json; charset=utf-8")
            if u.path == "/api/templates":
                return self._send(json.dumps(list_templates(), ensure_ascii=False), "application/json; charset=utf-8")
            if u.path.startswith("/api/"):
                key = u.path[5:]; d = load_data(load_config())
                return self._send(json.dumps({key: d.get(key, d.get(key + "_header")), "at": d["at"]}, ensure_ascii=False, default=str), "application/json; charset=utf-8")
            self._send("not found", code=404)
        except Exception as e:
            self._send(f"<pre>{html.escape(type(e).__name__ + ': ' + str(e))}</pre>", code=500)

    def do_POST(self):
        if urlparse(self.path).path == "/config":
            n = int(self.headers.get("Content-Length") or 0); form = parse_qs(self.rfile.read(n).decode("utf-8"))
            patch = {"app_title": form.get("app_title", [""])[0], "active_template": (form.get("active_template", [""])[0] or None),
                     "theme": {"primary_color": form.get("primary_color", ["#1f2937"])[0]}, "layout": {"sidebar_width": form.get("sidebar_width", ["230px"])[0]}}
            save_config(patch); self.send_response(303); self.send_header("Location", "/"); self.end_headers(); return
        self._send("not found", code=404)


def serve(port: int, open_browser: bool = True) -> int:
    UI_DIR.mkdir(parents=True, exist_ok=True); TPL_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_PATH.is_file():
        CONFIG_PATH.write_text(json.dumps(DEFAULT_CONFIG, ensure_ascii=False, indent=1), encoding="utf-8")
    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    url = f"http://127.0.0.1:{port}/"
    print(f"[{ENGINE}] U/I 已掛 {url} · 模板夾 {TPL_DIR} · 參數 {CONFIG_PATH} · Ctrl+C 停")
    if open_browser and os.environ.get("VIA_NO_OPEN") != "1":
        threading.Timer(1.5, lambda: webbrowser.open_new(url)).start()
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


# ---------------- 自測 ----------------
def selftest() -> int:
    ok = []
    def chk(name, cond, note=""):
        ok.append(bool(cond)); print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + note) if note else ''}")
    cfg = load_config(); ctx = build_context(cfg)
    page = render(DEFAULT_HTML, ctx)
    chk("① 內建標準模板渲染:標題 · 四燈 CSS · 鎖定色 · 參數面板 · window.VIA 橋", all(s in page for s in (cfg["app_title"], "via-blink", PAL["YELLOW"], "ui_config.json", "window.VIA")) and "{{" not in page)
    chk("② 迷你渲染器(無 jinja2 也能跑):for / if / |length / 三元", mini_render("{% for x in a %}[{{ x.n }}]{% endfor %}{{ a|length }}{{ 'Y' if flag else 'N' }}{% if flag %}T{% endif %}", {"a": [{"n": 1}, {"n": 2}], "flag": True}) == "[1][2]2YT")
    ext_jinja = "<html><head><title>{{ config.app_title }}</title></head><body><div class='lamp {{ data.overall }}'></div></body></html>"
    out, rep = adapt_template(ext_jinja, ctx)
    chk("③ 外部 Jinja 模板:宣告變數自動對映 · 補 :root 色票 + lamp css + 橋", cfg["app_title"] in out and "--lamp-red" in out and "via-blink" in out and "window.VIA" in out and "config.app_title" in rep["jinja_vars"])
    ext_plain = "<html><head><style>:root{--primary:#123456}</style></head><body><h1>My Dashboard</h1><span class='lamp RED'></span></body></html>"
    out2, rep2 = adapt_template(ext_plain, ctx)
    chk("④ 純 HTML 模板:原碼不改 · 尊重模板 :root(不蓋 --primary)· 只補燈色 token · 注入 window.VIA", "--primary:#123456" in out2 and "lamp-tokens-only" in rep2["injected"][0] and "window.VIA" in out2 and "My Dashboard" in out2)
    out3, rep3 = adapt_template("<div>no head at all</div>", ctx)
    chk("⑤ 沒 <head> 的片段:前置注入也能跑", out3.startswith("<style") and "no-head→prepend" in rep3["injected"])
    chk("⑥ 參數合併:ui_config 覆蓋預設,預設鍵不丟", isinstance(cfg["theme"].get("primary_color"), str) and "data" in cfg and cfg["data"]["universe_rows"] > 0)
    chk("⑦ 資料只讀:再生件 / 庫不在時誠實空(不假造列)", isinstance(ctx["data"]["universe"], list) and isinstance(ctx["data"]["readiness"], list))
    import socket
    s = socket.socket(); s.bind(("127.0.0.1", 0)); port = s.getsockname()[1]; s.close()
    srv = ThreadingHTTPServer(("127.0.0.1", port), H); th = threading.Thread(target=srv.serve_forever, daemon=True); th.start()
    try:
        import urllib.request
        body = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=10).read().decode("utf-8")
        api = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/api/config", timeout=10).read().decode("utf-8"))
        chk("⑧ 本機 HTTP 真起得來:/ 回面板 · /api/config 回 JSON", "window.VIA" in body and api.get("app_title") == cfg["app_title"], f"port {port}")
    finally:
        srv.shutdown(); srv.server_close()
    chk("⑨ 加速器橋在 · 零網路 · 零寫庫", "VIA:ACCEL-BRIDGE" in Path(__file__).read_text(encoding="utf-8"))
    print(f"  [計] {ENGINE} 自測 {sum(ok)}/{len(ok)} · {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a:
        return selftest()
    if not a:
        print(__doc__); return 2
    if a[0] == "render":
        page, rep = render_page(a[a.index("--template") + 1] if "--template" in a else None); print(page); print("<!-- adapt:", json.dumps(rep, ensure_ascii=False), "-->", file=sys.stderr); return 0
    if a[0] == "serve":
        if os.environ.get("VIA_FROM_VCGC") != "YES" and os.environ.get("VIA_UI_DIRECT") != "YES":
            print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc(或 VIA_UI_DIRECT=YES 由 Invoke-VIA-VdfUi 帶入)"}, ensure_ascii=False)); return 2
        if "--template" in a:
            save_config({"active_template": a[a.index("--template") + 1]})
        port = int(a[a.index("--port") + 1]) if "--port" in a else int(load_config().get("port") or 8765)
        return serve(port, open_browser="--no-open" not in a)
    print(__doc__); return 2


if __name__ == "__main__":
    raise SystemExit(main())
