#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== VDF_ENG093_LaunchConsole_v0100(側線 2026-09-23;主線批號由併線的手指定 L25)=====
# 操作員 2026-09-23 令:「給我一個指令含進入環境一件開啟 VDF 的 POWERSHELL CODE 實測 · 應先跳出 HTML U/I 問我要不要改參數啟動 ·
#   然後看到資料庫狀況」。這支是那個指令(Open-VIA-VDF-v*.ps1)背後的兩頁:
#   ask    —— 啟動前:參數(預設讀自啟動器 Invoke-VIA-VdfFetch 尾版的 param 區塊,不另寫一份)· 啟動就緒(VDF_SystemManager launch)·
#             資料庫狀況(目錄新鮮度 · 分類燈 · 增量缺口);你按「用預設參數啟動 / 用上面的參數啟動 / 不啟動」,決定寫成一個 JSON 交回 PowerShell。
#   status —— 抓完之後:先委派 CGC_MDL123 重點目錄,再把分類燈(CGC_MDL153 db_summary)與增量缺口(VDF_ENG089 plan)排成一頁。
# 逐格委派正主,本支一條判準都不自己寫(Zero-Hydra / LL316)。本機頁只綁 127.0.0.1、一次性權杖、同源 POST、每欄驗證;
# 同意閘只讀不寫(擷取車道 CGC_MDL134 在自己的子行程開閘;直呼類才要操作員開閘二)。零 CDN、零網路。
# 開頁:本支只在帶 --open 時試 webbrowser(house 零跳出律;短令冊設的 VIA_NO_OPEN=1 會讓它靜默不開)。
#   一鍵腳本 Open-VIA-VDF 不帶 --open:它從 stdout 取「頁:」那一行(網址或絕對路徑,已 flush),交給短令冊的 via-open
#   (只走瀏覽器 exe、永不經 .html 預設程式 = VS Code)。那一令是操作員親手打的,打了就該跳(批474 B:分界線是誰要求的)。
"""
VDF_ENG093_LaunchConsole — VDF 一鍵啟動台(問參數頁 + 資料庫狀況頁)
用法見 USAGE(python VDF_ENG093_LaunchConsole_v0100.py help)。
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====
# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import contextlib
import hmac
import html
import importlib.util
import io
import json
import os
import re
import secrets
import sys
import tempfile
import threading
from datetime import date, datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
REPORTS = VIA / "VIA_Reports"
OUT_DIR = REPORTS / "vdf_console"
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
YEAR_MIN = 1990
LIMIT_MAX = 5000
BODY_MAX = 4096
ACTIONS = ("launch", "cancel")
MODES = ("default", "custom")
FLAGS = ("dry", "noheal")

# 正主(尾版律現解;本台一條規則都不自己寫)
OWNERS = {
    "gate":    (("functional modules", "VDF", "engine"), "VDF_ENG089_IncrementalFetchGate_v*.py"),
    "door":    (("functional modules", "VDF"), "VDF_SystemManager_v*.py"),
    "summary": (("supportive modules", "registry"), "CGC_MDL153_WorkflowComposer_v*.py"),
    "home":    (("supportive modules", "registry"), "CGC_MDL123_DataHome_v*.py"),
}
_OWN: dict = {}


def _newest(folder: Path, pat: str):
    hits = sorted(p for p in folder.glob(pat) if "__pycache__" not in p.parts)
    return hits[-1] if hits else None


def _load(tag: str, path: Path):
    spec = importlib.util.spec_from_file_location(tag, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[tag] = mod
    with contextlib.redirect_stdout(io.StringIO()):
        spec.loader.exec_module(mod)
    return mod


def owner(key: str):
    """正主尾版;不在 → None(因由在 _OWN[key]['why']);載入就炸 → None + BROKEN 因由(兩件事不壓成一態)。"""
    st = _OWN.setdefault(key, {"mod": None, "why": "", "src": ""})
    if st["mod"] is not None or st["why"]:
        return st["mod"]
    rel, pat = OWNERS[key]
    p = _newest(VIA.joinpath(*rel), pat)
    if not p:
        st["why"] = "/".join(rel) + "/" + pat + " 缺"
        return None
    st["src"] = p.name
    try:
        st["mod"] = _load("vdf_eng093_" + key, p)
    except Exception as exc:
        st["why"] = f"BROKEN {type(exc).__name__}:{str(exc)[:80]}"
    return st["mod"]


def _quiet(fn, *a, **k):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        return fn(*a, **k)


# ---------------------------------------------------------------- 參數:預設讀自啟動器正本
def launcher_defaults(text: str | None = None) -> dict:
    """預設值不在這裡另寫一份:讀尾版 Invoke-VIA-VdfFetch-v*.ps1 的 param() 區塊。讀不到就講明、退回 2023 / 0。"""
    src = ""
    if text is None:
        p = _newest(VIA, "Invoke-VIA-VdfFetch-v*.ps1")
        src = p.name if p else ""
        try:
            text = p.read_text(encoding="utf-8", errors="replace") if p else ""
        except Exception:
            text = ""
    out = {"year": "2023", "limit": 0, "dry": False, "noheal": False, "launcher": src, "from_launcher": False, "why": ""}
    m_year = re.search(r'\[string\]\s*\$Year\s*=\s*"(\d{4})"', text or "")
    m_lim = re.search(r"\[int\]\s*\$Limit\s*=\s*(\d+)", text or "")
    if m_year and m_lim:
        out.update(year=m_year.group(1), limit=int(m_lim.group(1)), from_launcher=True)
    else:
        out["why"] = "啟動器 param() 讀不到 Year/Limit 預設,暫用 2023 / 0" if text else "啟動器不在,暫用 2023 / 0"
    return out


def validate(body: dict, defaults: dict, this_year: int | None = None) -> tuple:
    """頁上交回來的決定逐欄驗證;不認得的鍵、越界的值一律拒絕並點名欄位(絕不靜默吞掉)。"""
    this_year = this_year or date.today().year
    if not isinstance(body, dict):
        return False, {"field": "body", "why": "不是 JSON 物件"}
    allowed = {"t", "action", "mode", "year", "limit", "dry", "noheal"}
    extra = sorted(set(body) - allowed)
    if extra:
        return False, {"field": ",".join(extra), "why": "不認得的欄位"}
    action = body.get("action")
    if action not in ACTIONS:
        return False, {"field": "action", "why": "只收 launch / cancel"}
    if action == "cancel":
        return True, {"action": "cancel"}
    mode = body.get("mode", "custom")
    if mode not in MODES:
        return False, {"field": "mode", "why": "只收 default / custom"}
    if mode == "default":
        return True, {"action": "launch", "mode": "default", "year": str(defaults["year"]), "limit": int(defaults["limit"]),
                      "dry": bool(defaults["dry"]), "noheal": bool(defaults["noheal"])}
    year = str(body.get("year", "")).strip()
    if not re.fullmatch(r"\d{4}", year) or not (YEAR_MIN <= int(year) <= this_year):
        return False, {"field": "year", "why": f"要四位數年份,{YEAR_MIN}–{this_year}"}
    raw = body.get("limit", 0)
    if isinstance(raw, bool) or not re.fullmatch(r"\d{1,5}", str(raw).strip()):
        return False, {"field": "limit", "why": f"要 0–{LIMIT_MAX} 的整數(0=全市場)"}
    limit = int(str(raw).strip())
    if limit > LIMIT_MAX:
        return False, {"field": "limit", "why": f"要 0–{LIMIT_MAX} 的整數(0=全市場)"}
    flags = {}
    for k in FLAGS:
        v = body.get(k, False)
        if not isinstance(v, bool):
            return False, {"field": k, "why": "只收 true / false"}
        flags[k] = v
    return True, {"action": "launch", "mode": "custom", "year": year, "limit": limit, **flags}


# ---------------------------------------------------------------- 資料庫狀況:逐格委派
def read_catalog(path: Path | None = None):
    g = owner("gate")
    p = Path(path) if path else (Path(getattr(g, "CATALOG")) if g is not None and getattr(g, "CATALOG", None)
                                 else REPORTS / "datahome" / "DATAHOME_CATALOG_latest.json")
    try:
        return json.loads(p.read_text(encoding="utf-8-sig")), p
    except Exception:
        return None, p


def tables_from_catalog(cat: dict, today: date | None = None) -> tuple:
    """目錄(CGC_MDL123)→ CGC_MDL153 db_summary 吃的形狀 {表: rows/max/lag_days};同名表在兩本庫 → 取最新那一本,另列。"""
    today = today or date.today()
    out, dup = {}, []
    for db in (cat or {}).get("dbs") or []:
        for t in db.get("tables") or []:
            name = str(t.get("table") or "")
            if not name:
                continue
            hi = str(t.get("hi") or "")[:10]
            lag = None
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", hi):
                try:
                    lag = (today - date.fromisoformat(hi)).days
                except ValueError:
                    lag = None
            row = {"rows": int(t.get("rows") or 0), "max": hi, "lag_days": lag, "db": db.get("name") or ""}
            if name in out:
                dup.append(name)
                if (row["max"], row["rows"]) <= (out[name]["max"], out[name]["rows"]):
                    continue
            out[name] = row
    return out, sorted(set(dup))


def db_state(catalog_path: Path | None = None, refresh: bool = False) -> dict:
    res = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "why": [], "refresh": None}
    if refresh:
        h = owner("home")
        if h is None:
            res["refresh"] = {"state": "ABSENT", "why": _OWN["home"]["why"]}
        else:
            try:
                r = _quiet(h.catalog, write=True, do_print=False)
                res["refresh"] = {"state": "OK", "dbs": len((r or {}).get("dbs") or []), "src": _OWN["home"]["src"]}
            except Exception as exc:
                res["refresh"] = {"state": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:120]}"}
    cat, p = read_catalog(catalog_path)
    res["catalog_path"] = str(p)
    g = owner("gate")
    if g is not None and hasattr(g, "catalog_freshness"):
        try:
            res["fresh"] = g.catalog_freshness(cat)
        except Exception as exc:
            res["fresh"] = {"state": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:120]}"}
    else:
        res["fresh"] = {"state": "ABSENT", "why": _OWN.get("gate", {}).get("why", "")}
    tables, dup = tables_from_catalog(cat) if cat else ({}, [])
    res["tables"], res["dup"] = tables, dup
    s = owner("summary")
    if s is not None and hasattr(s, "db_summary") and cat:
        try:
            res["summary"] = s.db_summary(tables=tables)
        except Exception as exc:
            res["summary"] = {"verdict": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:120]}", "categories": []}
    else:
        res["summary"] = {"verdict": "ABSENT", "categories": [], "why": "目錄不在" if not cat else _OWN.get("summary", {}).get("why", "")}
    if g is not None and hasattr(g, "plan") and cat:
        saved = getattr(g, "CATALOG", None)
        try:
            if catalog_path:
                g.CATALOG = Path(catalog_path)
            res["plan"] = _quiet(g.plan)
        except Exception as exc:
            res["plan"] = {"state": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:120]}"}
        finally:
            if catalog_path:
                g.CATALOG = saved
    else:
        res["plan"] = {"state": "ABSENT", "why": "目錄不在" if not cat else _OWN.get("gate", {}).get("why", "")}
    res["dbs"] = [{"name": d.get("name"), "tables": d.get("tables") or []} for d in ((cat or {}).get("dbs") or [])]
    res["verdict"], res["rc"] = verdict(res)
    return res


def verdict(res: dict) -> tuple:
    """整頁一句話:目錄不在=ABSENT rc3;分類紅/黃或目錄過期=STALE rc2(資料落後不是壞掉);全綠=GREEN rc0。"""
    sv = str((res.get("summary") or {}).get("verdict") or "")
    fr = str((res.get("fresh") or {}).get("state") or "")
    if sv == "ABSENT" or fr == "ABSENT":
        return "ABSENT", 3
    if sv.startswith("BROKEN") or fr.startswith("BROKEN"):
        return "BROKEN", 1
    if sv in ("RED", "YELLOW") or fr in ("STALE", "UNKNOWN"):
        return "STALE", 2
    return "GREEN", 0


def readiness() -> dict:
    d = owner("door")
    if d is None or not hasattr(d, "read_launch"):
        return {"state": "ABSENT", "why": _OWN.get("door", {}).get("why", "")}
    try:
        r = _quiet(d.read_launch, probe=False)
    except Exception as exc:
        return {"state": "BROKEN", "why": f"{type(exc).__name__}:{str(exc)[:120]}"}
    c = r.get("consent") or {}
    py = r.get("python") or {}
    hl = r.get("hist_limit") or {}
    return {"state": r.get("state"), "rc": r.get("rc"), "src": _OWN["door"]["src"],
            "python": {"state": py.get("state"), "path": py.get("python"), "source": py.get("source")},
            "gates": {"VIA_NET_CONSENT": c.get("VIA_NET_CONSENT"), "VIA_SCRAPE_CONSENT": c.get("VIA_SCRAPE_CONSENT")},
            "hist_limit": {"set": hl.get("set"), "n": hl.get("n"), "launcher": hl.get("launcher"), "restores": hl.get("launcher_restores")},
            "next": [str(x) for x in (r.get("next") or [])][:6], "why": r.get("why")}


# ---------------------------------------------------------------- 頁(零 CDN · 零外部資源 · 淺深兩色)
_CSS = """
:root{--bg:#fbfbfa;--fg:#1d1d1b;--muted:#6b6b66;--card:#ffffff;--line:#e4e3de;--g:#1f7a3f;--y:#9a6b00;--r:#b3261e;--n:#5c5c57;--acc:#2f5dab}
@media (prefers-color-scheme:dark){:root{--bg:#161615;--fg:#ecebe6;--muted:#a3a29c;--card:#1f1f1d;--line:#34332f;--g:#5cc47f;--y:#e0b04a;--r:#f08a80;--n:#a3a29c;--acc:#8fb0ec}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:14px/1.55 system-ui,"Segoe UI","Microsoft JhengHei",sans-serif}
main{max-width:980px;margin:0 auto;padding:20px 16px 40px}h1{font-size:20px;margin:0 0 4px}h2{font-size:15px;margin:0 0 10px}
.sub{color:var(--muted);font-size:13px;margin-bottom:16px}.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px 16px;margin:0 0 14px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{text-align:left;padding:5px 8px;border-bottom:1px solid var(--line);vertical-align:top;word-break:break-all}
th{color:var(--muted);font-weight:600}.num{text-align:right;font-variant-numeric:tabular-nums}
.chip{display:inline-block;min-width:58px;text-align:center;border-radius:999px;padding:1px 8px;font-size:12px;font-weight:600;border:1px solid currentColor}
.GREEN,.FRESH,.OK,.PASS{color:var(--g)}.YELLOW,.STALE,.UNKNOWN{color:var(--y)}.RED,.BROKEN{color:var(--r)}.ABSENT,.NODATA,.GATED{color:var(--n)}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:10px 16px}label{display:block;font-size:13px;color:var(--muted)}
input[type=number]{width:100%;padding:6px 8px;border:1px solid var(--line);border-radius:6px;background:var(--bg);color:var(--fg);font:inherit}
.chk{display:flex;gap:8px;align-items:center;color:var(--fg);margin-top:6px}.btns{display:flex;flex-wrap:wrap;gap:10px;margin-top:14px}
button{font:inherit;padding:8px 14px;border-radius:8px;border:1px solid var(--line);background:var(--card);color:var(--fg);cursor:pointer}
button.primary{background:var(--acc);border-color:var(--acc);color:#fff}button:disabled{opacity:.5;cursor:default}
.msg{margin-top:12px;font-size:13px}.muted{color:var(--muted)}ul{margin:6px 0 0 18px;padding:0}code{font-size:12px}
"""


def _e(x) -> str:
    return html.escape("" if x is None else str(x))


def _chip(state) -> str:
    s = str(state or "NODATA")
    cls = re.sub(r"[^A-Z]", "", s.upper())[:12] or "NODATA"
    return f"<span class='chip {cls}'>{_e(s)}</span>"


def _db_cards(st: dict, gap_rows: int) -> str:
    fr = st.get("fresh") or {}
    age = fr.get("age_h")   # 欄名照 VDF_ENG089 catalog_freshness(catalog_ts / age_h)
    age_txt = (f" · {round(age * 60)} 分鐘前" if isinstance(age, (int, float)) and age < 1
               else (f" · {age:g} 小時前" if isinstance(age, (int, float)) else ""))
    head = (f"<div class='card'><h2>資料庫目錄 {_chip(fr.get('state'))}</h2>"
            f"<div class='muted'>目錄時間 {_e(fr.get('catalog_ts') or '-')}"
            + age_txt
            + f" · 來源 CGC_MDL123(<code>{_e(st.get('catalog_path'))}</code>)</div>"
            + (f"<div class='msg'>{_e(fr.get('why'))}</div>" if fr.get("why") else "") + "</div>")
    sm = st.get("summary") or {}
    rows = "".join(
        f"<tr><td>{_e(c.get('cat'))}</td><td>{_chip(c.get('lamp'))}</td><td class='num'>{_e(c.get('n'))}</td>"
        f"<td class='num'>{int(c.get('rows') or 0):,}</td><td>{_e(c.get('newest') or '-')}</td>"
        f"<td class='num'>{_e(c.get('worst_lag') if c.get('worst_lag') is not None else '?')}</td></tr>"
        for c in (sm.get("categories") or []))
    cats = (f"<div class='card'><h2>分類燈 {_chip(sm.get('verdict'))}</h2>"
            + (f"<table><tr><th>類別</th><th>燈</th><th class='num'>表</th><th class='num'>列</th><th>最新日</th><th class='num'>最壞滯後(日)</th></tr>{rows}</table>"
               if rows else f"<div class='muted'>{_e(sm.get('why') or '沒有可分類的表')}</div>")
            + "<div class='muted' style='margin-top:6px'>分類與燈號門檻:CGC_MDL153 db_summary(本頁不另算)</div></div>")
    pl = st.get("plan") or {}
    gaps = pl.get("gaps") or []
    grow = "".join(
        f"<tr><td>{_e(g.get('db'))}</td><td>{_e(g.get('table'))}</td><td>{_e(g.get('have'))}</td>"
        f"<td class='num'>{_e(g.get('missing_days'))}</td></tr>" for g in gaps[:gap_rows])
    plan = (f"<div class='card'><h2>增量缺口 {_chip(pl.get('state'))}</h2>"
            + (f"<div class='muted'>自 {_e(pl.get('since'))} 起 · 表 {_e(pl.get('n_tables'))} · 有缺口 {_e(pl.get('n_gap'))} · 齊 {_e(pl.get('n_covered'))}"
               f" · 紀錄表 {len(pl.get('records') or [])} · 哨兵 {len(pl.get('sentinels') or [])}</div>"
               if pl.get("state") not in ("ABSENT",) else f"<div class='muted'>{_e(pl.get('why'))}</div>")
            + (f"<table style='margin-top:8px'><tr><th>庫</th><th>表</th><th>現有</th><th class='num'>缺(日)</th></tr>{grow}</table>" if grow else "")
            + (f"<div class='muted'>另 {len(gaps) - gap_rows} 張沒列</div>" if len(gaps) > gap_rows else "")
            + "<div class='muted' style='margin-top:6px'>缺口與哨兵判讀:VDF_ENG089 plan(本頁不另算)</div></div>")
    return head + cats + plan


def render_ask(ctx: dict, token: str) -> str:
    d, st, rd = ctx["defaults"], ctx["db"], ctx["ready"]
    gates = rd.get("gates") or {}
    hl = rd.get("hist_limit") or {}
    nxt = "".join(f"<li>{_e(x)}</li>" for x in (rd.get("next") or []))
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VDF 一鍵啟動</title><style>{_CSS}</style></head><body><main>
<h1>VDF 一鍵啟動</h1><div class="sub">VDF_ENG093 v{_e(VERSION)} · {_e(ctx['ts'])} · 先看資料庫,再決定參數。按下啟動之後,擷取在 PowerShell 視窗裡跑,進度印在那裡。</div>
<div class="card"><h2>啟動參數</h2>
<div class="muted" style="margin-bottom:8px">預設值讀自啟動器 <code>{_e(d.get('launcher') or '(不在)')}</code>{'' if d.get('from_launcher') else ' · ' + _e(d.get('why'))}</div>
<div class="grid">
<div><label for="year">起始年(-Year)</label><input id="year" type="number" min="{YEAR_MIN}" max="{date.today().year}" value="{_e(d['year'])}"></div>
<div><label for="limit">每道上限檔數(-Limit;0 = 全市場)</label><input id="limit" type="number" min="0" max="{LIMIT_MAX}" value="{_e(d['limit'])}"></div>
<div><label class="chk"><input id="dry" type="checkbox"{' checked' if d.get('dry') else ''}> 只看計畫,不抓(-Dry)</label>
<label class="chk"><input id="noheal" type="checkbox"{' checked' if d.get('noheal') else ''}> 不做倉庫自癒(-NoHeal)</label></div>
</div>
<div class="btns"><button class="primary" id="b_default">用預設參數啟動</button><button id="b_custom">用上面的參數啟動</button><button id="b_cancel">不啟動</button></div>
<div class="msg" id="msg" role="status"></div></div>
<div class="card"><h2>啟動就緒 {_chip(rd.get('state'))}</h2><div class="muted">來源 {_e(rd.get('src') or rd.get('why') or '-')}(VDF 子系統管理對接口 launch;只讀)</div>
<table style="margin-top:8px"><tr><th>項</th><th>現況</th></tr>
<tr><td>家族境 python</td><td>{_chip((rd.get('python') or {}).get('state'))} <code>{_e((rd.get('python') or {}).get('path'))}</code></td></tr>
<tr><td>同意閘</td><td>VIA_NET_CONSENT {_chip(gates.get('VIA_NET_CONSENT'))} · VIA_SCRAPE_CONSENT {_chip(gates.get('VIA_SCRAPE_CONSENT'))}<div class="muted">擷取車道在自己的子行程開閘(CGC_MDL134),所以這裡沒開也能抓;直呼 via-price / via-chip 才要你在視窗開閘二。本頁只讀,不代開。</div></td></tr>
<tr><td>視窗限量</td><td>{'VIA_HIST_LIMIT=' + _e(hl.get('n')) if hl.get('set') else '未設'} · 啟動器 {_e(hl.get('launcher'))} 跑完{'會' if hl.get('restores') else '不會'}還原</td></tr>
</table>{('<div style="margin-top:8px"><b>下一步</b><ul>' + nxt + '</ul></div>') if nxt else ''}</div>
<h2 style="margin:18px 0 10px">啟動前的資料庫狀況</h2>{_db_cards(st, 12)}
</main><script>
const T={json.dumps(token)};
const q=id=>document.getElementById(id);
function send(body){{
  ["b_default","b_custom","b_cancel"].forEach(i=>q(i).disabled=true);
  q("msg").textContent="送出中…";
  body.t=T;
  fetch("/decide",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify(body)}})
   .then(r=>r.json().then(j=>({{ok:r.ok,j}})))
   .then(({{ok,j}})=>{{
     if(ok){{q("msg").textContent=j.decision.action==="cancel"?"已選「不啟動」。本頁可以關了。":"已送出:回 PowerShell 視窗看擷取進度。跑完會自動開資料庫狀況頁。本頁可以關了。";}}
     else{{q("msg").textContent="沒收:"+(j.field||"")+" "+(j.why||"");["b_default","b_custom","b_cancel"].forEach(i=>q(i).disabled=false);}}
   }}).catch(e=>{{q("msg").textContent="送不出去:"+e;}});
}}
q("b_default").onclick=()=>send({{action:"launch",mode:"default"}});
q("b_custom").onclick=()=>send({{action:"launch",mode:"custom",year:String(q("year").value),limit:String(q("limit").value),dry:q("dry").checked,noheal:q("noheal").checked}});
q("b_cancel").onclick=()=>send({{action:"cancel"}});
</script></body></html>"""


def render_status(st: dict) -> str:
    dbs = ""
    n = 0
    for d in st.get("dbs") or []:
        for t in d.get("tables") or []:
            if n >= 80:
                break
            n += 1
            dbs += (f"<tr><td>{_e(d.get('name'))}</td><td>{_e(t.get('table'))}</td><td class='num'>{int(t.get('rows') or 0):,}</td>"
                    f"<td>{_e(t.get('lo') or '-')}</td><td>{_e(t.get('hi') or '-')}</td><td>{_e(t.get('err') or '')}</td></tr>")
    rf = st.get("refresh") or {}
    return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VDF 資料庫狀況</title><style>{_CSS}</style></head><body><main>
<h1>VDF 資料庫狀況 {_chip(st.get('verdict'))}</h1><div class="sub">VDF_ENG093 v{_e(VERSION)} · {_e(st.get('ts'))}{(' · 目錄剛重點:' + _e(rf.get('state')) + (' ' + _e(rf.get('why')) if rf.get('why') else '')) if rf else ''}</div>
{_db_cards(st, 30)}
<div class="card"><h2>逐表(前 80 張)</h2>{('<table><tr><th>庫</th><th>表</th><th class="num">列</th><th>最早</th><th>最新</th><th>錯</th></tr>' + dbs + '</table>') if dbs else '<div class="muted">目錄裡沒有表</div>'}
{('<div class="muted" style="margin-top:6px">同名表出現在兩本以上的庫:' + _e(', '.join(st.get('dup') or [])) + '(分類取最新那一本)</div>') if st.get('dup') else ''}</div>
<div class="muted">資料來源:CGC_MDL123 目錄 · CGC_MDL153 分類 · VDF_ENG089 缺口與新鮮度(逐格委派,本頁不另算)。</div>
</main></body></html>"""


# ---------------------------------------------------------------- 問:本機頁(127.0.0.1 · 一次性權杖 · 同源 POST)
def _write_json(path: Path, obj: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=".ask_", suffix=".json", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
    os.replace(tmp, path)


def make_server(page: str, token: str, defaults: dict, port: int = 0):
    state = {"decision": None, "event": threading.Event()}

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            return

        def _hdr(self, code: int, ctype: str, n: int):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(n))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy",
                             "default-src 'none'; style-src 'unsafe-inline'; script-src 'unsafe-inline'; connect-src 'self'; "
                             "form-action 'none'; frame-ancestors 'none'; base-uri 'none'")
            self.end_headers()

        def _send(self, code: int, obj):
            b = (json.dumps(obj, ensure_ascii=False) if not isinstance(obj, str) else obj).encode("utf-8")
            self._hdr(code, "application/json; charset=utf-8" if not isinstance(obj, str) else "text/plain; charset=utf-8", len(b))
            self.wfile.write(b)

        def _host_ok(self) -> bool:
            return self.headers.get("Host", "") == f"127.0.0.1:{self.server.server_port}"

        def do_GET(self):
            u = urlparse(self.path)
            if not self._host_ok():
                return self._send(403, "host")
            if u.path == "/decide":
                return self._send(405, "POST only")
            if u.path != "/":
                return self._send(404, "not found")
            if not hmac.compare_digest((parse_qs(u.query).get("t") or [""])[0], token):
                return self._send(403, "token")
            b = page.encode("utf-8")
            self._hdr(200, "text/html; charset=utf-8", len(b))
            self.wfile.write(b)

        def do_POST(self):
            u = urlparse(self.path)
            if u.path != "/decide":
                return self._send(404, {"why": "not found"})
            if not self._host_ok() or self.headers.get("Origin", "") != f"http://127.0.0.1:{self.server.server_port}":
                return self._send(403, {"field": "origin", "why": "只收本頁同源送出"})
            if not self.headers.get("Content-Type", "").startswith("application/json"):
                return self._send(415, {"field": "content-type", "why": "只收 JSON"})
            n = int(self.headers.get("Content-Length") or 0)
            if n <= 0 or n > BODY_MAX:
                return self._send(413, {"field": "body", "why": "空的或太大"})
            try:
                body = json.loads(self.rfile.read(n).decode("utf-8"))
            except Exception:
                return self._send(400, {"field": "body", "why": "不是 JSON"})
            if not isinstance(body, dict) or not hmac.compare_digest(str(body.get("t", "")), token):
                return self._send(403, {"field": "t", "why": "權杖不對"})
            if state["decision"] is not None:
                return self._send(409, {"field": "action", "why": "已經決定過了"})
            ok, res = validate(body, defaults)
            if not ok:
                return self._send(400, res)
            res["ts"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            res["source"] = "ui"
            state["decision"] = res
            self._send(200, {"ok": True, "decision": res})
            state["event"].set()

    srv = ThreadingHTTPServer(("127.0.0.1", port), H)
    srv.daemon_threads = True
    return srv, state


def serve_ask(page: str, token: str, defaults: dict, out: Path, open_browser: bool, timeout: int, port: int = 0) -> tuple:
    srv, state = make_server(page, token, defaults, port)
    url = f"http://127.0.0.1:{srv.server_port}/?t={token}"
    th = threading.Thread(target=srv.serve_forever, daemon=True)
    th.start()
    # 一定要 flush:在 Invoke-VIAPython 底下 stdout 導到檔(區塊緩衝),不 flush 這行要等行程結束才落檔——
    # Open-VIA-VDF 就拿不到網址去 via-open,操作員也看不到網址(頁不跳、等滿逾時)。自測 ⑨ 把這件事釘住。
    print(f"  [VDF 啟動台] 頁:{url}", flush=True)
    print("  [VDF 啟動台] 等你在頁上選「用預設參數啟動 / 用上面的參數啟動 / 不啟動」" + (f"(最多 {timeout // 60} 分鐘)" if timeout >= 60 else ""), flush=True)
    if open_browser:
        try:
            import webbrowser
            if not webbrowser.open(url):   # 零跳出閘 VIA_NO_OPEN=1(SUP_MDL737)會讓它靜默回 False
                print("  [VDF 啟動台] 沒開成瀏覽器(零跳出閘或沒有瀏覽器):via-open <上面的網址>,或手動貼進瀏覽器", flush=True)
        except Exception as exc:
            print(f"  [VDF 啟動台] 沒開成瀏覽器({type(exc).__name__}):via-open <上面的網址>,或手動貼進瀏覽器", flush=True)
    got = state["event"].wait(timeout if timeout > 0 else None)
    srv.shutdown()
    srv.server_close()
    decision = state["decision"] if got and state["decision"] else {"action": "timeout", "ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "source": "ui"}
    _write_json(out, decision)
    return decision, url


# ---------------------------------------------------------------- 動詞
def _arg(a: list, flag: str, default=None):
    if flag in a:
        i = a.index(flag)
        if i + 1 < len(a) and not a[i + 1].startswith("--"):
            return a[i + 1]
    return default


def cmd_ask(a: list) -> int:
    out = Path(_arg(a, "--out") or (OUT_DIR / "ASK_DECISION_latest.json"))
    timeout = int(_arg(a, "--timeout", "900"))
    port = int(_arg(a, "--port", "0"))
    cat = _arg(a, "--catalog")
    ctx = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "defaults": launcher_defaults(),
           "db": db_state(Path(cat) if cat else None), "ready": readiness()}
    token = secrets.token_urlsafe(24)
    page = render_ask(ctx, token)
    decision, _url = serve_ask(page, token, ctx["defaults"], out, open_browser=("--open" in a), timeout=timeout, port=port)
    act = decision.get("action")
    if act == "launch":
        print(f"  [VDF 啟動台] 決定:啟動 · 起始年 {decision['year']} · 上限 {decision['limit'] or '全市場'} · "
              f"{'只看計畫' if decision['dry'] else '真跑'}{' · 不自癒' if decision['noheal'] else ''}({decision.get('mode')})→ {out}")
        return 0
    if act == "cancel":
        print(f"  [VDF 啟動台] 決定:不啟動 → {out}")
        return 0
    print(f"  [VDF 啟動台] 逾時沒收到決定 → 不啟動(NODATA)· {out}")
    return 2


def cmd_status(a: list) -> int:
    cat = _arg(a, "--catalog")
    out_dir = Path(_arg(a, "--out-dir") or OUT_DIR)
    st = db_state(Path(cat) if cat else None, refresh=("--refresh" in a))
    out_dir.mkdir(parents=True, exist_ok=True)
    page = out_dir / "VDF_DB_STATUS_latest.html"
    page.write_text(render_status(st), encoding="utf-8")
    _write_json(out_dir / "VDF_DB_STATUS_latest.json", {k: v for k, v in st.items() if k not in ("dbs",)})
    fr, sm, pl = st.get("fresh") or {}, st.get("summary") or {}, st.get("plan") or {}
    print(f"  [VDF 資料庫狀況] {st['verdict']} · 目錄 {fr.get('state')} {fr.get('catalog_ts') or ''} · 分類 {sm.get('verdict')} · "
          f"缺口 {pl.get('n_gap', '-')}/{pl.get('n_tables', '-')}")
    for c in (sm.get("categories") or [])[:9]:
        print(f"     [{c.get('lamp'):<6}] {c.get('cat')} · 表 {c.get('n')} · 最新 {c.get('newest') or '-'} · 最壞滯後 {c.get('worst_lag') if c.get('worst_lag') is not None else '?'} 日")
    # 頁路徑獨佔一行、絕對路徑、flush:Open-VIA-VDF 從這一行取路徑交給 via-open(只走瀏覽器 exe,不經 .html 預設程式)
    print(f"  [VDF 資料庫狀況] 頁:{page.resolve()}", flush=True)
    if "--json" in a:
        print(json.dumps({k: v for k, v in st.items() if k not in ("dbs", "tables")}, ensure_ascii=False, indent=1, default=str))
    if "--open" in a:
        try:
            import webbrowser
            if not webbrowser.open(page.resolve().as_uri()):   # 零跳出閘 VIA_NO_OPEN=1 會讓它靜默回 False
                print("  [VDF 資料庫狀況] 沒開成瀏覽器(零跳出閘或沒有瀏覽器):via-open <上面的頁>", flush=True)
        except Exception as exc:
            print(f"  [VDF 資料庫狀況] 沒開成瀏覽器({type(exc).__name__}):via-open <上面的頁>", flush=True)
    return st["rc"]


USAGE = f"""VDF_ENG093_LaunchConsole v{VERSION} — VDF 一鍵啟動台
  ask    [--open] [--out <決定.json>] [--timeout 900] [--port 0] [--catalog <目錄.json>]
         起本機頁(127.0.0.1 · 一次性權杖 · 同源 POST):參數(預設讀自啟動器)· 啟動就緒 · 啟動前資料庫狀況;
         你選「用預設參數啟動 / 用上面的參數啟動 / 不啟動」→ 寫決定檔 → rc0;逾時 rc2(不啟動)
  status [--refresh] [--open] [--out-dir <夾>] [--catalog <目錄.json>] [--json]
         (--refresh 先委派 CGC_MDL123 重點目錄)→ 分類燈 · 增量缺口 · 逐表 → VIA_Reports/vdf_console/VDF_DB_STATUS_latest.html
         rc:0 全綠 · 2 落後或過期 · 3 沒有目錄 · 1 正主壞
  --selftest
  --open 才試開瀏覽器(house 零跳出律;VIA_NO_OPEN=1 時靜默不開)。兩個動詞都把「頁:<網址或絕對路徑>」獨佔一行印出並 flush,
         一鍵啟動腳本 Open-VIA-VDF 取那一行交給 via-open(只走瀏覽器 exe)"""


def main() -> int:
    a = sys.argv[1:]
    if "--selftest" in a or "--self-test" in a:
        return selftest()
    verb = a[0] if a else ""
    if verb == "ask":
        return cmd_ask(a[1:])
    if verb == "status":
        return cmd_status(a[1:])
    print(USAGE)
    return 0 if verb in ("help", "-h", "--help") else 2


# ---------------------------------------------------------------- 自測(零網路 · 只寫暫存 · 正負控)
def selftest() -> int:
    import ast
    import socket
    import urllib.error
    import urllib.request
    okn, bad, nod = [], [], []

    def chk(name, cond, why=""):
        (okn if cond else bad).append(name)
        print(("  ✓ " + name) if cond else f"  [FAIL] {name} — {why}")

    print(f"🧪 VDF_ENG093_LaunchConsole v{VERSION} --selftest(零網路 · 只寫暫存)")
    src = Path(__file__).read_text(encoding="utf-8")
    need = ["main", "cmd_ask", "cmd_status", "validate", "render_ask", "render_status", "serve_ask", "tables_from_catalog", "db_state", "launcher_defaults"]
    miss = [n for n in need if n not in globals()]
    chk(f"① 宣告符號齊備({len(need)} 個)", not miss, f"缺 {miss}")
    chk("② 橋接件完好(ACCEL/NET)", "[VIA:ACCEL-BRIDGE:" in src and "[VIA:NET-BRIDGE:" in src, "檔頭橋標記不全")

    d_real = launcher_defaults()
    d_neg = launcher_defaults("param([switch]$Dry)")
    chk("③ 參數預設讀自啟動器正本(尾版 param 區塊)· 負控:讀不到就講明並退 2023/0",
        (d_real["from_launcher"] or not d_real["launcher"]) and not d_neg["from_launcher"] and bool(d_neg["why"])
        and d_neg["year"] == "2023" and d_neg["limit"] == 0,
        f"real {d_real} neg {d_neg}")

    dfl = {"year": "2023", "limit": 0, "dry": False, "noheal": False}
    ok1, r1 = validate({"action": "launch", "mode": "custom", "year": "2024", "limit": "100", "dry": True, "noheal": False}, dfl, 2026)
    ok2, r2 = validate({"action": "launch", "mode": "default", "year": "abc"}, dfl, 2026)
    negs = [({"action": "launch", "mode": "custom", "year": "abc", "limit": 0}, "year"),
            ({"action": "launch", "mode": "custom", "year": "1899", "limit": 0}, "year"),
            ({"action": "launch", "mode": "custom", "year": "2031", "limit": 0}, "year"),
            ({"action": "launch", "mode": "custom", "year": "2024", "limit": "-1"}, "limit"),
            ({"action": "launch", "mode": "custom", "year": "2024", "limit": "99999"}, "limit"),
            ({"action": "launch", "mode": "custom", "year": "2024", "limit": 0, "dry": "yes"}, "dry"),
            ({"action": "launch", "mode": "custom", "year": "2024", "limit": 0, "consent": True}, "consent"),
            ({"action": "rm -rf"}, "action")]
    neg_ok = all((not validate(b, dfl, 2026)[0]) and validate(b, dfl, 2026)[1].get("field") == f for b, f in negs)
    chk("④ 參數驗證:正控(自訂 2024/100/只看計畫;預設模式忽略頁上亂填)· 負控 8 條逐欄點名(含想塞 consent 鍵)",
        ok1 and r1 == {"action": "launch", "mode": "custom", "year": "2024", "limit": 100, "dry": True, "noheal": False}
        and ok2 and r2["year"] == "2023" and r2["limit"] == 0 and neg_ok,
        f"{r1} {r2} neg {neg_ok}")

    # ⑤ 本機頁往返(真 HTTP;回送介面不在=NODATA 不是壞掉)
    try:   # 回送介面要真的連得上(只綁得上不算:網路命名空間裡 lo 沒起時綁得上、連不上)
        _ls = socket.socket()
        _ls.bind(("127.0.0.1", 0))
        _ls.listen(1)
        socket.create_connection(_ls.getsockname(), timeout=2).close()
        _ls.close()
        loop_ok = True
    except OSError:
        loop_ok = False
    if not loop_ok:
        nod.append("⑤")
        print("  ⑤ 本機頁往返 — NODATA(本境沒有回送介面)")
    else:
        td = Path(tempfile.mkdtemp(prefix="eng093_"))
        tok = "T" + secrets.token_urlsafe(12)
        srv, state = make_server("<!doctype html><p>ok</p>", tok, dfl)
        port = srv.server_port
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        base = f"http://127.0.0.1:{port}"

        def req(method, path, body=None, origin=base, ctype="application/json"):
            data = json.dumps(body).encode("utf-8") if body is not None else None
            r = urllib.request.Request(base + path, data=data, method=method)
            if origin:
                r.add_header("Origin", origin)
            if data is not None:
                r.add_header("Content-Type", ctype)
            try:
                with opener.open(r, timeout=5) as resp:
                    return resp.status, resp.read().decode("utf-8")
            except urllib.error.HTTPError as e:
                return e.code, e.read().decode("utf-8", "replace")
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # 本機往返不走任何代理(不改環境變數)
        try:
            g_no, _ = req("GET", "/")
            g_ok, g_body = req("GET", "/?t=" + tok)
            g_dec, _ = req("GET", "/decide")
            p_badtok, _ = req("POST", "/decide", {"t": "x", "action": "cancel"})
            p_xorigin, _ = req("POST", "/decide", {"t": tok, "action": "cancel"}, origin="http://evil.example")
            p_bad, pb = req("POST", "/decide", {"t": tok, "action": "launch", "mode": "custom", "year": "abc", "limit": 0})
            p_ok, po = req("POST", "/decide", {"t": tok, "action": "launch", "mode": "custom", "year": "2024", "limit": 50, "dry": True, "noheal": False})
            p_again, _ = req("POST", "/decide", {"t": tok, "action": "cancel"})
        finally:
            srv.shutdown()
            srv.server_close()
        dec = state["decision"] or {}
        chk("⑤ 本機頁往返:無權杖 403 · 帶權杖 200 · GET /decide 405 · 錯權杖 403 · 跨源 403 · 壞年份 400 點名 year · 正確 200 · 第二次 409",
            (g_no, g_ok, g_dec, p_badtok, p_xorigin, p_bad, p_ok, p_again) == (403, 200, 405, 403, 403, 400, 200, 409)
            and '"year"' in pb and dec.get("year") == "2024" and dec.get("limit") == 50 and dec.get("dry") is True,
            f"{(g_no, g_ok, g_dec, p_badtok, p_xorigin, p_bad, p_ok, p_again)} dec {dec}")
        # ⑥ 逾時誠實:沒人按 → action=timeout、決定檔照寫(PowerShell 靠它判斷不啟動)
        out6 = td / "ask.json"
        with contextlib.redirect_stdout(io.StringIO()):
            d6, _u = serve_ask("<p>x</p>", "t6", dfl, out6, open_browser=False, timeout=1)
        j6 = json.loads(out6.read_text(encoding="utf-8")) if out6.exists() else {}
        chk("⑥ 逾時 → action=timeout 且決定檔照寫(不啟動)", d6.get("action") == "timeout" and j6.get("action") == "timeout", f"{d6} {j6}")

    # ⑦ 資料庫狀況委派:合成目錄(暫存)→ 去重 · 分類燈(CGC_MDL153)· 缺口(VDF_ENG089)· 頁寫暫存;負控:目錄不在 → ABSENT rc3
    td7 = Path(tempfile.mkdtemp(prefix="eng093c_"))
    today = date.today()
    d1 = today.fromordinal(today.toordinal() - 1).isoformat()
    d30 = today.fromordinal(today.toordinal() - 30).isoformat()
    cat = {"ts": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "dbs": [
        {"name": "vdf_tw_market.duckdb", "path": "x", "tables": [
            {"table": "tw_daily_prices", "rows": 1000, "date_col": "date", "lo": "2023-01-03", "hi": d1, "err": ""},
            {"table": "tw_chip_daily", "rows": 500, "date_col": "date", "lo": "2023-01-03", "hi": d30, "err": ""}]},
        {"name": "legacy.duckdb", "path": "y", "tables": [
            {"table": "tw_daily_prices", "rows": 10, "date_col": "date", "lo": "2020-01-02", "hi": "2020-12-31", "err": ""}]}]}
    cp = td7 / "cat.json"
    cp.write_text(json.dumps(cat), encoding="utf-8")
    tbl, dup = tables_from_catalog(cat, today)
    st7 = db_state(cp)
    gate_ok = owner("gate") is not None and owner("summary") is not None
    buf7 = io.StringIO()
    with contextlib.redirect_stdout(buf7):
        rc7 = cmd_status(["--catalog", str(cp), "--out-dir", str(td7 / "out")])
    page7 = (td7 / "out" / "VDF_DB_STATUS_latest.html")
    m7 = re.search(r"^\s*\[VDF 資料庫狀況\] 頁:(.+?)\s*$", buf7.getvalue(), re.M)
    line7 = bool(m7) and Path(m7.group(1)).is_absolute() and Path(m7.group(1)).resolve() == page7.resolve()
    txt7 = page7.read_text(encoding="utf-8") if page7.exists() else ""
    absent = db_state(td7 / "no_such_catalog.json")
    if not gate_ok:
        nod.append("⑦")
        print("  ⑦ 資料庫狀況委派 — NODATA(正主不在:" + str({k: v.get("why") for k, v in _OWN.items() if v.get("why")}) + ")")
    else:
        chk("⑦ 資料庫狀況:同名表取最新那一本 · 分類燈委派 CGC_MDL153(籌碼 30 日=紅)· 缺口委派 VDF_ENG089 · 頁落暫存 · 「頁:」獨佔一行絕對路徑(給 via-open)· 負控:目錄不在=ABSENT rc3",
            line7 and tbl["tw_daily_prices"]["db"] == "vdf_tw_market.duckdb" and dup == ["tw_daily_prices"]
            and any(c.get("cat") == "籌碼" and c.get("lamp") == "RED" for c in (st7.get("summary") or {}).get("categories") or [])
            and (st7.get("plan") or {}).get("state") == "OK" and rc7 == 2 and "分類燈" in txt7 and "增量缺口" in txt7
            and absent["verdict"] == "ABSENT" and absent["rc"] == 3,
            f"summary {(st7.get('summary') or {}).get('verdict')} plan {(st7.get('plan') or {}).get('state')} rc {rc7} absent {absent['verdict']} 頁行 {line7}")

    # ⑧ 零寫同意閘 · 零 CDN:本檔沒有任何對 CONSENT 環境變數的賦值;兩頁 HTML 無外部網址
    tree = ast.parse(src)
    writes = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AugAssign)):
            for t in (node.targets if isinstance(node, ast.Assign) else [node.target]):
                if isinstance(t, ast.Subscript) and "CONSENT" in ast.dump(t):
                    writes.append(getattr(node, "lineno", 0))
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr in ("putenv", "setdefault", "update"):
            if "CONSENT" in ast.dump(node):
                writes.append(getattr(node, "lineno", 0))
    ctx = {"ts": "t", "defaults": dfl | {"launcher": "x", "from_launcher": True}, "db": st7, "ready": {"state": "OK", "gates": {}, "hist_limit": {}}}
    pages = render_ask(ctx, "tok") + render_status(st7)
    ext = re.findall(r"(?:src|href)\s*=\s*[\"']?(https?://[^\"' >]+)", pages)
    chk("⑧ 本檔零寫同意閘(AST)· 兩頁零外部資源(零 CDN)", not writes and not ext, f"寫閘行 {writes} 外部 {ext[:3]}")

    # ⑨ 呼叫端拿得到網址:stdout 導到檔(同 Invoke-VIAPython:Start-Process -RedirectStandardOutput,區塊緩衝)時,
    #    「頁:網址」那一行必須在還沒決定之前就落檔——否則 Open-VIA-VDF 等不到網址去 via-open,頁永遠不跳(初稿就缺這個 flush)
    if not loop_ok:
        nod.append("⑨")
        print("  ⑨ 導檔 stdout 先見網址 — NODATA(本境沒有回送介面)")
    else:
        import subprocess
        import time
        td9 = Path(tempfile.mkdtemp(prefix="eng093p_"))
        so9, se9, dec9 = td9 / "stdout.txt", td9 / "stderr.txt", td9 / "ask.json"
        env9 = {k: v for k, v in os.environ.items() if k != "PYTHONUNBUFFERED"}   # 不讓環境替本檔 flush:照 Invoke-VIAPython 的樣子跑
        env9["PYTHONIOENCODING"] = "utf-8"
        seen9, code9, rc9, why9 = False, None, None, ""
        with open(so9, "wb") as fo, open(se9, "wb") as fe:
            p9 = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), "ask", "--out", str(dec9), "--timeout", "60", "--catalog", str(cp)],
                                  stdout=fo, stderr=fe, env=env9)
            try:
                m9, t_end = None, time.monotonic() + 90
                while m9 is None and p9.poll() is None and time.monotonic() < t_end:
                    m9 = re.search(r"頁:(http://127\.0\.0\.1:(\d+)/\?t=([A-Za-z0-9_\-]+))", so9.read_text(encoding="utf-8", errors="replace"))
                    if m9 is None:
                        time.sleep(0.1)
                seen9 = m9 is not None and not dec9.exists()
                if m9:
                    base9 = f"http://127.0.0.1:{m9.group(2)}"
                    r9 = urllib.request.Request(base9 + "/decide", data=json.dumps({"t": m9.group(3), "action": "cancel"}).encode("utf-8"), method="POST")
                    r9.add_header("Origin", base9)
                    r9.add_header("Content-Type", "application/json")
                    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(r9, timeout=5) as resp:
                        code9 = resp.status
                rc9 = p9.wait(timeout=30)
            except Exception as exc:
                why9 = f"{type(exc).__name__}: {exc}"
            finally:
                if p9.poll() is None:
                    p9.kill()
                    p9.wait()
        j9 = json.loads(dec9.read_text(encoding="utf-8")) if dec9.exists() else {}
        chk("⑨ stdout 導到檔(同 Invoke-VIAPython)·「頁:網址」在決定之前就落檔 · 頁上送「不啟動」→ 200 · rc 0 · 決定檔 cancel",
            seen9 and code9 == 200 and rc9 == 0 and j9.get("action") == "cancel",
            f"先見網址 {seen9} 送出 {code9} rc {rc9} 決定 {j9} {why9} stderr 末段 {se9.read_text(encoding='utf-8', errors='replace')[-200:]!r}")

    rc = 1 if bad else (2 if nod else 0)
    print(f"[計] OK {len(okn)} · FAIL {len(bad)} · NODATA {len(nod)} → rc={rc} ({ {0: 'GREEN', 1: 'RED', 2: 'NODATA'}[rc] })")
    return rc


if __name__ == "__main__":
    sys.exit(main())
