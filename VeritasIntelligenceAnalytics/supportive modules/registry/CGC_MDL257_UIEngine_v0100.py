#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""CGC_MDL257_UIEngine v0100 — 中央 U/I 引擎:自適應任何範本 · 參數檔可調 · 內建標準範本 · DuckDB 顯式資料庫面板

操作員 2026-10-04:「DuckDB 顯式資料庫於 U/I 功能;建立一個 U/I 架構會自適應式吻合任何模板設計;參數可調整;
  啟動檔兼最簡單的 HTML 標準模板,未來的拿來套用;一個引擎自動安裝所有工具與環境(照我測過的結果)再啟動 HTML U/I,
  操作介面全部在上面實習而不動系統」。
  · 參數:正本 supportive modules\ui_support\VIA_UI_EngineConfig_v*.json(尾版)← 操作員工作副本 VIA_Reports\ui_engine\ui_config.json ← --config F ← --set a.b=值
    (app_title · active_template · theme 顏色 / 字 · layout 側欄寬 / 顯示 / 密度 · sources 快照 · duckdb 掃描根 · nav 母系統與其他系統)
  · active_template = null → 內建標準範本(左面板 功能 + 頁籤 + 母系統 / 其他系統;右面板 儀表板 · 資料來源 · DuckDB · 環境 · 參數;
    卡片 · 表單 · 按鈕 · 表格 · 狀態標籤 · 參數面板即時套色並可匯出 ui_config.json);
    = X.html → 範本夾(template_dirs)找 X,Jinja 沙盒渲染(本境沒 jinja2 → 只代換雙大括號變數並照實註明),
    一律注入 window.VIA(資料)· window.VIA_CONFIG(參數)· :root 色票變數;範本原檔零觸碰。
  · DuckDB 顯式:掃 duckdb.roots 下的 *.duckdb(唯讀 ATTACH;別的行程鎖著 = LOCKED,不搶)→ 每庫 表 / 視圖 · 估計列數(小表精算)·
    欄位型別 · 日期欄最早 / 最晚 · 前 N 列樣本;頁不直讀庫(引擎 → JSON → 頁)。
  · 環境:讀 LKGC_latest(EnvGovernance 照測過版本的鎖)判定 / 時間;安裝由 PS 啟動器經 VCGC 呼叫 MDL135 / MDL137,本檔不裝東西。
  動詞:build [--config F] [--set k=v …] [--template X] [--home H] [--out F] · serve [--port N](只綁 127.0.0.1;只讀 GET;每次請求重讀參數)
        · config [--init](列有效參數;--init 寫工作副本)· templates · duck [--home H](列 DuckDB 盤點)· --selftest
  不開瀏覽器(PS 啟動器 Start-VIA-UIEngine-v0100.ps1 才開);零 CDN;不碰 TA-Lib;不讀寫同意閘。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 全導入令;graceful 零行為變更) =====
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
    """統包唯一網路工具惰性載入;本檔零網路(serve 只聽本機),橋只為全樹一致。"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import copy
import html
import json
import os
import re
import sys
import time
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
UI_DIR = VIA / "supportive modules" / "ui_support"
TAG = f"CGC_MDL257_UIEngine v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
CONFIG_GLOB = "VIA_UI_EngineConfig_v*.json"
WORK_DIR = VIA / "VIA_Reports" / "ui_engine"
WORK_CONFIG = WORK_DIR / "ui_config.json"
_VAR = re.compile(r"\{\{\s*([A-Za-z_][\w]*(?:\.[\w]+)*)\s*(?:\|[^}]*)?\}\}")
_BLOCK = re.compile(r"\{%")
_SAFE_HOSTS = ("127.0.0.1", "localhost", "::1")


# ---------- 參數 ----------
def _vnum(p: Path) -> int:
    m = re.search(r"_v(\d+)$", p.stem)
    return int(m.group(1)) if m else -1


def _deep_merge(base: dict, over: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in (over or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def _coerce(v: str):
    low = v.strip().lower()
    if low in ("true", "false"):
        return low == "true"
    if low in ("null", "none"):
        return None
    if re.fullmatch(r"-?\d+", v.strip()):
        return int(v)
    if v.strip().startswith(("[", "{")):
        try:
            return json.loads(v)
        except ValueError:
            pass
    return v


def apply_sets(cfg: dict, sets: list) -> dict:
    cfg = copy.deepcopy(cfg)
    for s in sets or []:
        if "=" not in s:
            raise ValueError(f"--set 要 a.b=值,收到 {s!r}")
        k, v = s.split("=", 1)
        cur = cfg
        parts = [p for p in k.strip().split(".") if p]
        for p in parts[:-1]:
            cur = cur.setdefault(p, {})
            if not isinstance(cur, dict):
                raise ValueError(f"--set {k}:{p} 不是物件")
        cur[parts[-1]] = _coerce(v)
    return cfg


def load_config(path: str | None = None, sets: list | None = None) -> dict:
    hits = sorted(UI_DIR.glob(CONFIG_GLOB), key=_vnum)
    base = json.loads(hits[-1].read_text(encoding="utf-8")) if hits else {}
    layers = [str(hits[-1]) if hits else "(無正本)"]
    if WORK_CONFIG.is_file():
        base = _deep_merge(base, json.loads(WORK_CONFIG.read_text(encoding="utf-8")))
        layers.append(str(WORK_CONFIG))
    if path:
        base = _deep_merge(base, json.loads(Path(path).read_text(encoding="utf-8")))
        layers.append(str(path))
    if sets:
        base = apply_sets(base, sets)
        layers.append("--set " + " ".join(sets))
    base["_layers"] = layers
    return base


def _abs(p: str, home: Path | None) -> Path:
    s = str(p).replace("{home}", str(home) if home else "{home}")
    q = Path(s)
    return q if q.is_absolute() else VIA / q


def default_home() -> Path | None:
    env = os.environ.get("VIA_VDF_FETCH_HOME")
    return Path(env) if env else None


# ---------- DuckDB 顯式 ----------
def _duck():
    import duckdb
    return duckdb


def _busy(exc: Exception) -> bool:
    t = str(exc).lower()
    return "lock" in t or "conflict" in t


def find_dbs(cfg: dict, home: Path | None) -> list:
    dc = cfg.get("duckdb", {})
    out, seen = [], set()
    for r in dc.get("roots", []):
        if "{home}" in r and not home:
            continue
        root = _abs(r, home)
        if not root.is_dir():
            continue
        for p in sorted(root.glob(dc.get("glob", "**/*.duckdb"))):
            if not p.is_file() or any(x in str(p) for x in dc.get("exclude", [])):
                continue
            rp = p.resolve()
            if rp in seen:
                continue
            seen.add(rp)
            out.append(p)
            if len(out) >= int(dc.get("max_dbs", 40)):
                return out
    return out


def _jsonable(v):
    if v is None or isinstance(v, (bool, int, float, str)):
        return v
    return str(v)


def inspect_db(p: Path, cfg: dict) -> dict:
    dc = cfg.get("duckdb", {})
    n_sample = int(cfg.get("layout", {}).get("sample_rows") or dc.get("sample_rows", 5))
    rec = {"db": str(p), "name": p.name, "mb": round(p.stat().st_size / 1e6, 2),
           "wal": Path(str(p) + ".wal").is_file(), "state": "OK", "tables": [], "note": ""}
    con = _duck().connect()
    try:
        try:
            con.execute(f"ATTACH '{p.as_posix()}' AS d (READ_ONLY)")
        except Exception as exc:
            rec["state"] = "LOCKED" if _busy(exc) else "ERR"
            rec["note"] = f"{type(exc).__name__}: {str(exc)[:120]}"
            return rec
        rows = con.execute("SELECT schema_name, table_name, estimated_size, 'table' FROM duckdb_tables() WHERE database_name='d' "
                           "UNION ALL SELECT schema_name, view_name, NULL, 'view' FROM duckdb_views() WHERE database_name='d' AND NOT internal "
                           "ORDER BY 4, 2").fetchall()
        for schema, name, est, kind in rows[: int(dc.get("max_tables_per_db", 200))]:
            fq = f'd."{schema}"."{name}"'
            t = {"schema": schema, "table": name, "kind": kind, "est_rows": int(est) if est is not None else None,
                 "rows": None, "columns": [], "date_col": None, "min_date": None, "max_date": None, "sample": [], "note": ""}
            try:
                cols = con.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_catalog='d' "
                                   "AND table_schema=? AND table_name=? ORDER BY ordinal_position", [schema, name]).fetchall()
                t["columns"] = [{"name": c, "type": ty} for c, ty in cols]
                if kind == "table" and (est or 0) <= int(dc.get("exact_count_max_est", 5_000_000)):
                    t["rows"] = con.execute(f"SELECT count(*) FROM {fq}").fetchone()[0]
                dcol = next((c for c, ty in cols if str(ty).upper() in ("DATE",) or str(ty).upper().startswith("TIMESTAMP")), None) \
                    or next((c for c, _ in cols if c.lower() in ("date", "trade_date", "日期", "as_of")), None)
                if dcol and (t["rows"] is not None or kind == "table"):
                    lo, hi = con.execute(f'SELECT min(TRY_CAST("{dcol}" AS DATE)), max(TRY_CAST("{dcol}" AS DATE)) FROM {fq}').fetchone()
                    t.update(date_col=dcol, min_date=_jsonable(lo), max_date=_jsonable(hi))
                cur = con.execute(f"SELECT * FROM {fq} LIMIT {n_sample}")
                t["sample"] = [[_jsonable(v) for v in r] for r in cur.fetchall()]
            except Exception as exc:
                t["note"] = f"{type(exc).__name__}: {str(exc)[:100]}"
            rec["tables"].append(t)
    finally:
        con.close()
    return rec


def duck_inventory(cfg: dict, home: Path | None) -> dict:
    t0 = time.time()
    dbs = [inspect_db(p, cfg) for p in find_dbs(cfg, home)]
    return {"dbs": dbs, "n_dbs": len(dbs), "n_tables": sum(len(d["tables"]) for d in dbs),
            "rows": sum((t["rows"] if t["rows"] is not None else (t["est_rows"] or 0)) for d in dbs for t in d["tables"]),
            "locked": sum(1 for d in dbs if d["state"] == "LOCKED"), "sec": round(time.time() - t0, 2)}


# ---------- 資料來源 · 環境 ----------
def load_sources(cfg: dict, home: Path | None) -> dict:
    out = {}
    for s in cfg.get("sources", []):
        p = _abs(s.get("path", ""), home)
        rec = {"id": s.get("id"), "title": s.get("title", s.get("id")), "path": str(p), "state": "NODATA", "data": None}
        if p.is_file():
            try:
                rec["data"] = json.loads(p.read_text(encoding="utf-8"))
                rec["state"] = "OK"
                rec["mtime"] = datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            except ValueError as exc:
                rec["state"] = "ERR"
                rec["note"] = f"JSON 壞:{exc}"
        out[rec["id"]] = rec
    return out


def env_status(cfg: dict) -> dict:
    p = _abs(cfg.get("env", {}).get("lkgc", "VIA_Reports/env_governance/LKGC_latest.json"), None)
    if not p.is_file():
        return {"lkgc": "NODATA", "note": "還沒有 LKGC(EnvGovernance 跑全綠才存)", "path": str(p)}
    try:
        d = json.loads(p.read_text(encoding="utf-8"))
    except ValueError:
        return {"lkgc": "ERR", "path": str(p)}
    envs = d.get("envs") or {}
    return {"lkgc": d.get("verdict", "?"), "eligible": d.get("eligible"), "ts": d.get("ts"), "per_env_at": d.get("per_env_at"),
            "envs": sorted(envs) if isinstance(envs, dict) else envs, "machine": d.get("machine"), "path": str(p)}


def snapshot(cfg: dict, home: Path | None) -> dict:
    return {"tool": TAG, "built": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "home": str(home) if home else None,
            "config": {k: v for k, v in cfg.items() if not k.startswith("_")}, "config_layers": cfg.get("_layers", []),
            "sources": load_sources(cfg, home), "duckdb": duck_inventory(cfg, home), "env": env_status(cfg)}


# ---------- 範本 ----------
def find_template(name: str, cfg: dict) -> Path | None:
    p = Path(name)
    if p.is_file():
        return p
    for d in cfg.get("template_dirs", []):
        for cand in (_abs(d, None) / name, _abs(d, None) / (name + ".html")):
            if cand.is_file():
                return cand
    return None


def list_templates(cfg: dict) -> list:
    out = []
    for d in cfg.get("template_dirs", []):
        dd = _abs(d, None)
        for p in sorted(dd.glob("*.html")) if dd.is_dir() else []:
            t = p.read_text(encoding="utf-8", errors="replace")
            out.append({"name": p.name, "dir": str(dd), "vars": sorted(set(_VAR.findall(t)))[:30], "jinja": bool(_BLOCK.search(t))})
    return out


def _lookup(ctx: dict, dotted: str):
    cur = ctx
    for part in dotted.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.isdigit() and int(part) < len(cur):
            cur = cur[int(part)]
        else:
            return KeyError
    return cur


def theme_css(cfg: dict) -> str:
    th, lay = cfg.get("theme", {}), cfg.get("layout", {})
    v = {"--via-primary": th.get("primary_color", "#3B82F6"), "--via-bg": th.get("bg_color", "#F6F8FA"),
         "--via-fg": th.get("fg_color", "#172033"), "--via-card": th.get("card_color", "#FFFFFF"),
         "--via-muted": th.get("muted_color", "#6B7785"), "--via-font": th.get("font_family", "system-ui, sans-serif"),
         "--via-fs": th.get("font_size", "12.5px"), "--via-sidebar": lay.get("sidebar_width", "260px"),
         "--via-cards-min": lay.get("cards_min", "200px")}
    safe = {k: re.sub(r"[;{}<>]", "", str(x)) for k, x in v.items()}
    body = ";".join(f"{k}:{x}" for k, x in safe.items())
    dark = ""
    if th.get("mode", "auto") in ("auto", "dark"):
        dk = "--via-bg:#0B0D10;--via-fg:#E6EBF2;--via-card:#14181C;--via-muted:#8C99A6"
        dark = (f":root[data-theme=dark]{{{dk}}}" + (f"@media (prefers-color-scheme: dark){{:root:not([data-theme=light]){{{dk}}}}}"
                                                       if th.get("mode", "auto") == "auto" else ""))
    return f":root{{{body}}}{dark}"


def inject(page: str, snap: dict, cfg: dict) -> str:
    js = lambda o: json.dumps(o, ensure_ascii=False, default=str).replace("</", "<\\/")
    block = (f"<!-- [VIA:UI-ENGINE-INJECT:v0100] {TAG} --><style>{theme_css(cfg)}</style>"
             f"<script>window.VIA = {js(snap)};window.VIA_CONFIG = {js(snap['config'])};</script>")
    if re.search(r"</head>", page, re.I):
        return re.sub(r"</head>", lambda m: block + m.group(0), page, count=1, flags=re.I)
    return block + page


def render_custom(tpl: str, snap: dict, cfg: dict) -> tuple:
    ctx = {"config": snap["config"], "VIA": snap, **snap}
    rep = {"engine": "", "missing": [], "note": ""}
    used = sorted(set(_VAR.findall(tpl)))
    out = None
    try:
        from jinja2 import Undefined
        from jinja2.sandbox import SandboxedEnvironment
        out = SandboxedEnvironment(autoescape=True, undefined=Undefined).from_string(tpl).render(**ctx)
        rep["engine"] = "jinja2(沙盒)"
    except ImportError:
        pass
    except Exception as exc:
        rep["engine"] = f"jinja2 失敗 → 逐變數代換({type(exc).__name__}: {str(exc)[:80]})"
    bound = set(re.findall(r"\{%-?\s*(?:for|set)\s+([A-Za-z_]\w*)", tpl)) | {"loop"}
    if out is None:
        rep["engine"] = rep["engine"] or "逐變數代換"

        def sub(m):
            v = _lookup(ctx, m.group(1))
            if v is KeyError:
                return m.group(0)
            return html.escape(v if isinstance(v, str) else json.dumps(v, ensure_ascii=False, default=str))
        out = _VAR.sub(sub, tpl)
        if _BLOCK.search(tpl):
            rep["note"] = "本境缺 jinja2:{% %} 區塊原樣留著沒渲染(裝 jinja2,或範本改用 window.VIA 由 JS 畫)"
    rep["missing"] = sorted({v for v in used if _lookup(ctx, v) is KeyError and v.split(".")[0] not in bound})
    return inject(out, snap, cfg), rep


# ---------- 內建標準範本(零依賴;JS 從 window.VIA 畫)----------
BUILTIN = r"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TITLE__</title>
<style>
*{box-sizing:border-box}html,body{margin:0;height:100%}
body{background:var(--via-bg);color:var(--via-fg);font:var(--via-fs)/1.4 var(--via-font)}
.app{display:grid;grid-template-columns:var(--via-sidebar) minmax(0,1fr);min-height:100vh}
.app.noside{grid-template-columns:minmax(0,1fr)}.app.noside .side{display:none}
.side{background:var(--via-card);border-right:1px solid rgba(127,127,127,.2);padding:12px;display:flex;flex-direction:column;gap:3px;min-width:0}
.side h3{margin:10px 0 2px;font-size:10.5px;letter-spacing:1px;color:var(--via-muted);text-transform:uppercase}
.side .brand{font-weight:600;font-size:15px;color:var(--via-primary)}
.side a,.side button{display:block;width:100%;text-align:left;padding:4px 8px;border:1px solid transparent;border-radius:5px;background:none;color:var(--via-fg);font:inherit;cursor:pointer;text-decoration:none}
.side a:hover,.side button:hover{border-color:var(--via-primary)}.side button.on{background:color-mix(in srgb,var(--via-primary) 14%,transparent);border-color:var(--via-primary)}
.side .absent{opacity:.45;cursor:not-allowed}
.main{display:flex;flex-direction:column;min-width:0}
.top{display:flex;justify-content:space-between;align-items:center;gap:10px;padding:10px 18px;border-bottom:1px solid rgba(127,127,127,.2);background:var(--via-card)}
.top.hide{display:none}.top b{font-size:15px}
.tabs{display:flex;gap:4px;flex-wrap:wrap;padding:8px 18px 0}
.tabs button{padding:4px 10px;border:1px solid rgba(127,127,127,.3);border-radius:5px;background:none;color:var(--via-fg);font:inherit;cursor:pointer}
.tabs button.on{border-color:var(--via-primary);background:color-mix(in srgb,var(--via-primary) 14%,transparent)}
.pg{display:none;padding:12px 18px}.pg.on{display:block}
.cards{display:grid;grid-template-columns:repeat(auto-fill,minmax(var(--via-cards-min),1fr));gap:10px;margin-bottom:12px}
.card{background:var(--via-card);border:1px solid rgba(127,127,127,.2);border-radius:8px;padding:10px 12px;min-width:0;overflow:auto}
.card h4{margin:0 0 6px;font-size:12px;color:var(--via-muted);font-weight:500}.kpi{font-size:22px;font-weight:600;color:var(--via-primary)}
.grid2{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,2fr);gap:10px}
table{border-collapse:collapse;width:100%}th,td{padding:3px 6px;border-bottom:1px solid rgba(127,127,127,.18);text-align:left;vertical-align:top;word-break:break-word}
th{color:var(--via-muted);font-weight:500;position:sticky;top:0;background:var(--via-card)}td.n{text-align:right;font-variant-numeric:tabular-nums}
.badge{display:inline-block;padding:0 7px;border-radius:9px;font-size:11px}
.b-OK,.b-GREEN{background:rgba(63,185,132,.18);color:#2f9e6e}.b-YELLOW,.b-LOCKED{background:rgba(224,179,65,.2);color:#b7861b}
.b-RED,.b-ERR{background:rgba(224,108,96,.2);color:#c2483d}.b-NODATA,.b-NODATE{background:rgba(140,153,166,.2);color:var(--via-muted)}
label{display:block;margin:6px 0 2px;color:var(--via-muted)}input,select{width:100%;padding:4px 6px;border:1px solid rgba(127,127,127,.35);border-radius:5px;background:var(--via-card);color:var(--via-fg);font:inherit}
input[type=color]{height:28px;padding:1px}input[type=checkbox]{width:auto}
.btn{background:var(--via-primary);color:#fff;border:0;border-radius:5px;padding:5px 12px;font:inherit;cursor:pointer;margin:6px 6px 0 0}.btn.o{background:none;color:var(--via-primary);border:1px solid var(--via-primary)}
.mut{color:var(--via-muted)}.scroll{max-height:420px;overflow:auto}pre{white-space:pre-wrap;margin:0;font:10.5px/1.35 ui-monospace,Consolas,monospace}
.dbl{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr) minmax(0,2fr);gap:10px}
.pick{cursor:pointer}.pick:hover{background:color-mix(in srgb,var(--via-primary) 8%,transparent)}.pick.on{background:color-mix(in srgb,var(--via-primary) 16%,transparent)}
@media (max-width:900px){.app{grid-template-columns:1fr}.grid2,.dbl{grid-template-columns:1fr}}
</style></head>
<body><div class="app" id="app">
<aside class="side" id="side"></aside>
<div class="main"><div class="top" id="top"></div><div class="tabs" id="tabs"></div>
<section class="pg" id="pg-dash"></section><section class="pg" id="pg-src"></section><section class="pg" id="pg-duck"></section>
<section class="pg" id="pg-env"></section><section class="pg" id="pg-param"></section></div></div>
<script>
(function(){
var S=window.VIA||{},C=window.VIA_CONFIG||{},$=function(s){return document.querySelector(s)};
var esc=function(v){return v===null||v===undefined?'':String(v).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})};
var badge=function(s){return '<span class="badge b-'+esc(s)+'">'+esc(s)+'</span>'};
var num=function(v){return v===null||v===undefined?'':Number(v).toLocaleString()};
var KEY='via.ui.engine.v0100',st={};try{st=JSON.parse(localStorage.getItem(KEY)||'{}')}catch(e){}
var save=function(){try{localStorage.setItem(KEY,JSON.stringify(st))}catch(e){}};
function table(rows,cols){if(!rows||!rows.length)return '<div class="mut">(無資料)</div>';var h='<table><tr>'+cols.map(function(c){return '<th>'+esc(c[1])+'</th>'}).join('')+'</tr>';
rows.forEach(function(r){h+='<tr>'+cols.map(function(c){var v=r[c[0]];return c[2]==='b'?'<td>'+badge(v)+'</td>':c[2]==='n'?'<td class="n">'+num(v)+'</td>':'<td>'+esc(v)+'</td>'}).join('')+'</tr>'});return h+'</table>'}
var D=S.duckdb||{dbs:[]},SRC=S.sources||{},E=S.env||{},L=C.layout||{};
var pages=[['pg-dash','📊 儀表板'],['pg-src','🗂 資料來源'],['pg-duck','🦆 DuckDB 資料庫'],['pg-env','🧰 環境'],['pg-param','⚙️ 參數']];
var link=function(x){return x.exists?'<a href="'+esc(x.href)+'">'+esc(x.label)+'</a>':'<a class="absent" title="ABSENT">'+esc(x.label)+' · ABSENT</a>'};
$('#side').innerHTML='<div class="brand">'+esc(C.app_title||'VIA')+'</div><div class="mut">'+esc(S.tool||'')+'</div>'
 +'<h3>回母系統</h3>'+(S.nav&&S.nav.parent||[]).map(link).join('')+'<h3>其他系統</h3>'+(S.nav&&S.nav.systems||[]).map(link).join('')
 +'<h3>功能 / 頁</h3>'+pages.map(function(p){return '<button data-pg="'+p[0]+'">'+p[1]+'</button>'}).join('')
 +'<h3>Live log</h3><pre class="scroll" style="max-height:220px">'+esc(Object.keys(SRC).map(function(k){var d=SRC[k].data;return d&&d.live?(d.live.lines||[]).slice(-30).join('\n'):''}).join('\n')||'(來源沒有日誌)')+'</pre>';
var worst=D.locked?'LOCKED':(D.n_dbs?'OK':'NODATA');
$('#top').innerHTML='<b>'+esc(C.app_title||'VIA')+'</b><span>DuckDB '+badge(worst)+' · LKGC '+badge(E.lkgc||'NODATA')+' · 產生 '+esc(S.built||'')+'</span>';
if(L.show_header===false)$('#top').classList.add('hide');if(L.show_sidebar===false)$('#app').classList.add('noside');
$('#tabs').innerHTML=pages.map(function(p){return '<button data-pg="'+p[0]+'">'+p[1]+'</button>'}).join('');
var srcRows=Object.keys(SRC).map(function(k){var s=SRC[k],d=s.data||{};return{id:k,title:s.title,state:s.state,mtime:s.mtime,as_of:d.as_of,groups:d.groups?d.groups.length:null,path:s.path}});
$('#pg-dash').innerHTML='<div class="cards"><div class="card"><h4>DuckDB 庫</h4><div class="kpi">'+num(D.n_dbs)+'</div></div><div class="card"><h4>表 / 視圖</h4><div class="kpi">'+num(D.n_tables)+'</div></div>'
 +'<div class="card"><h4>總列數(估)</h4><div class="kpi">'+num(D.rows)+'</div></div><div class="card"><h4>資料來源</h4><div class="kpi">'+srcRows.filter(function(r){return r.state==='OK'}).length+' / '+srcRows.length+'</div></div>'
 +'<div class="card"><h4>環境 LKGC</h4><div class="kpi">'+badge(E.lkgc||'NODATA')+'</div><div class="mut">'+esc(E.ts||E.note||'')+'</div></div></div>'
 +'<div class="grid2"><div class="card"><h4>資料來源</h4>'+table(srcRows,[['title','來源'],['state','燈','b'],['as_of','as-of'],['mtime','時間']])+'</div>'
 +'<div class="card"><h4>DuckDB 概覽</h4><div class="scroll">'+table(D.dbs.map(function(d){return{name:d.name,state:d.state,mb:d.mb,n:d.tables.length,rows:d.tables.reduce(function(a,t){return a+(t.rows!==null&&t.rows!==undefined?t.rows:(t.est_rows||0))},0)}}),[['name','庫'],['state','燈','b'],['mb','MB','n'],['n','表','n'],['rows','列','n']])+'</div></div></div>';
var src='';Object.keys(SRC).forEach(function(k){var s=SRC[k],d=s.data||{};src+='<div class="card"><h4>'+esc(s.title)+' '+badge(s.state)+'</h4><div class="mut">'+esc(s.path)+'</div>';
 if(d.groups)src+=table(d.groups.map(function(g){var m=g.summary||{};return{id:g.id,zh:g.zh,membership:g.membership,n:g.n===null?'全部':g.n,rows:m.rows_asof,max:m.max_date,w:m.worst||'NODATA'}}),[['id','族群'],['zh','名稱'],['membership','名單'],['n','成員'],['rows','≤as-of 筆數','n'],['max','最晚'],['w','燈','b']]);
 src+='</div>'});$('#pg-src').innerHTML=src||'<div class="mut">(參數 sources 沒設)</div>';
$('#pg-duck').innerHTML='<div class="dbl"><div class="card"><h4>庫('+num(D.n_dbs)+')· '+esc(D.sec)+'s</h4><div id="dl" class="scroll"></div></div><div class="card"><h4>表 / 視圖</h4><div id="tl" class="scroll"></div></div><div class="card"><h4 id="th">欄位 · 樣本</h4><div id="td" class="scroll"></div></div></div>';
function showDb(i){st.db=i;save();var d=D.dbs[i];if(!d)return;document.querySelectorAll('#dl .pick').forEach(function(e,j){e.classList.toggle('on',j===i)});
 $('#tl').innerHTML=d.state!=='OK'?badge(d.state)+' '+esc(d.note):d.tables.map(function(t,j){return '<div class="pick" data-t="'+j+'">'+esc(t.table)+' <span class="mut">'+esc(t.kind)+' · '+num(t.rows!==null?t.rows:t.est_rows)+'</span></div>'}).join('');
 document.querySelectorAll('#tl .pick').forEach(function(e){e.onclick=function(){showT(i,+e.dataset.t)}});showT(i,st.t&&st.db===i?st.t:0)}
function showT(i,j){st.t=j;save();var t=(D.dbs[i]||{}).tables?D.dbs[i].tables[j]:null;if(!t){$('#td').innerHTML='';return}
 document.querySelectorAll('#tl .pick').forEach(function(e,k){e.classList.toggle('on',k===j)});
 $('#th').textContent=t.table+' · '+(t.date_col?('日期 '+(t.min_date||'')+' → '+(t.max_date||'')):'無日期欄');
 var cols=t.columns.map(function(c){return c.name});var h='<div class="mut">'+t.columns.map(function(c){return esc(c.name)+':'+esc(c.type)}).join(' · ')+'</div>';
 h+='<table><tr>'+cols.map(function(c){return '<th>'+esc(c)+'</th>'}).join('')+'</tr>'+t.sample.map(function(r){return '<tr>'+r.map(function(v){return '<td>'+esc(v)+'</td>'}).join('')+'</tr>'}).join('')+'</table>'+(t.note?'<div class="mut">'+esc(t.note)+'</div>':'');$('#td').innerHTML=h}
$('#dl').innerHTML=D.dbs.map(function(d,i){return '<div class="pick">'+esc(d.name)+' '+badge(d.state)+' <span class="mut">'+num(d.tables.length)+' 表 · '+esc(d.mb)+' MB'+(d.wal?' · WAL':'')+'</span></div>'}).join('')||'<div class="mut">(找不到 .duckdb:參數 duckdb.roots / 輸出根)</div>';
document.querySelectorAll('#dl .pick').forEach(function(e,i){e.onclick=function(){showDb(i)}});if(D.dbs.length)showDb(st.db&&st.db<D.dbs.length?st.db:0);
$('#pg-env').innerHTML='<div class="card"><h4>照測過的版本安裝(LKGC)</h4>'+table([E],[['lkgc','判定','b'],['eligible','可用'],['ts','時間'],['per_env_at','逐境'],['path','檔']])
 +'<div class="mut" style="margin-top:6px">安裝 / 回到測過版本由 PS 啟動器 Start-VIA-UIEngine-v0100.ps1 -Install 經 VCGC 呼叫 EnvGovernance(LKGC rollback,裝進 via_* 隔離境,不動 base)與 RunGate;本頁只讀。</div></div>';
var th=C.theme||{};
$('#pg-param').innerHTML='<div class="grid2"><div class="card"><h4>參數(即時套用;匯出存成 ui_config.json 才永久)</h4>'
 +'<label>標題</label><input id="p_title" value="'+esc(C.app_title||'')+'">'
 +'<label>主色</label><input type="color" id="p_primary" value="'+esc(th.primary_color||'#3B82F6')+'"><label>背景</label><input type="color" id="p_bg" value="'+esc(th.bg_color||'#F6F8FA')+'">'
 +'<label>側欄寬(px)</label><input type="range" min="180" max="420" id="p_side" value="'+parseInt(L.sidebar_width||260)+'">'
 +'<label>字級</label><select id="p_fs"><option>11.5px</option><option>12.5px</option><option>13.5px</option><option>15px</option></select>'
 +'<label>主題</label><select id="p_mode"><option value="auto">跟系統</option><option value="light">淺色</option><option value="dark">深色</option></select>'
 +'<label><input type="checkbox" id="p_sidebar" '+(L.show_sidebar===false?'':'checked')+'> 顯示側欄</label><label><input type="checkbox" id="p_header" '+(L.show_header===false?'':'checked')+'> 顯示頂列</label>'
 +'<button class="btn" id="p_export">匯出 ui_config.json</button><button class="btn o" id="p_reset">還原</button></div>'
 +'<div class="card"><h4>有效參數(疊層:'+esc((S.config_layers||[]).join(' ← '))+')</h4><pre class="scroll">'+esc(JSON.stringify(C,null,1))+'</pre></div></div>';
var R=document.documentElement;$('#p_fs').value=th.font_size||'12.5px';$('#p_mode').value=th.mode||'auto';
function applyP(){R.style.setProperty('--via-primary',$('#p_primary').value);R.style.setProperty('--via-bg',$('#p_bg').value);R.style.setProperty('--via-sidebar',$('#p_side').value+'px');
 R.style.setProperty('--via-fs',$('#p_fs').value);var m=$('#p_mode').value;if(m==='auto')R.removeAttribute('data-theme');else R.setAttribute('data-theme',m);
 $('#app').classList.toggle('noside',!$('#p_sidebar').checked);$('#top').classList.toggle('hide',!$('#p_header').checked);
 st.p={t:$('#p_title').value,pr:$('#p_primary').value,bg:$('#p_bg').value,sd:$('#p_side').value,fs:$('#p_fs').value,m:m,sb:$('#p_sidebar').checked,hd:$('#p_header').checked};save()}
['#p_primary','#p_bg','#p_side','#p_fs','#p_mode','#p_sidebar','#p_header','#p_title'].forEach(function(s){$(s).addEventListener('input',applyP)});
if(st.p){$('#p_primary').value=st.p.pr;$('#p_bg').value=st.p.bg;$('#p_side').value=st.p.sd;$('#p_fs').value=st.p.fs;$('#p_mode').value=st.p.m;$('#p_sidebar').checked=st.p.sb;$('#p_header').checked=st.p.hd;applyP()}
$('#p_export').onclick=function(){var o=JSON.parse(JSON.stringify(C));o.app_title=$('#p_title').value;o.theme=o.theme||{};o.layout=o.layout||{};o.theme.primary_color=$('#p_primary').value;o.theme.bg_color=$('#p_bg').value;
 o.theme.font_size=$('#p_fs').value;o.theme.mode=$('#p_mode').value;o.layout.sidebar_width=$('#p_side').value+'px';o.layout.show_sidebar=$('#p_sidebar').checked;o.layout.show_header=$('#p_header').checked;
 var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([JSON.stringify(o,null,1)],{type:'application/json'}));a.download='ui_config.json';a.click()};
$('#p_reset').onclick=function(){delete st.p;save();location.reload()};
function show(id){document.querySelectorAll('.pg').forEach(function(p){p.classList.toggle('on',p.id===id)});document.querySelectorAll('[data-pg]').forEach(function(b){b.classList.toggle('on',b.dataset.pg===id)});st.page=id;save()}
document.querySelectorAll('[data-pg]').forEach(function(b){b.onclick=function(){show(b.dataset.pg)}});show(st.page&&document.getElementById(st.page)?st.page:'pg-dash');
if(S.live_reload)setTimeout(function(){location.reload()},S.live_reload*1000);
})();
</script></body></html>
"""


def nav_links(cfg: dict, out: Path) -> dict:
    res = {}
    for key in ("parent", "systems"):
        rows = []
        for label, rel in (cfg.get("nav", {}).get(key) or []):
            p = _abs(rel, None)
            rows.append({"label": label, "exists": p.is_file(), "href": Path(os.path.relpath(p, out.parent)).as_posix(), "rel": rel})
        res[key] = rows
    return res


def build(cfg: dict, home: Path | None, out: Path | None = None, template: str | None = None) -> tuple:
    out = out or _abs(cfg.get("output", "VIA_Reports/ui_engine/VIA_UI_Engine_latest.html"), home)
    snap = snapshot(cfg, home)
    snap["nav"] = nav_links(cfg, out)
    tname = template or cfg.get("active_template")
    rep = {"engine": "內建標準範本", "missing": [], "note": "", "template": None}
    if tname:
        tp = find_template(tname, cfg)
        if not tp:
            raise FileNotFoundError(f"找不到範本 {tname}(找過:{' · '.join(cfg.get('template_dirs', []))});要用內建請設 active_template=null")
        page, r2 = render_custom(tp.read_text(encoding="utf-8", errors="replace"), snap, cfg)
        rep.update(r2, template=str(tp))
    else:
        page = inject(BUILTIN.replace("__TITLE__", html.escape(str(cfg.get("app_title", "VIA")))), snap, cfg)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(page, encoding="utf-8")
    os.replace(tmp, out)
    (out.parent / "VIA_UI_Engine_SNAPSHOT_latest.json").write_text(json.dumps(snap, ensure_ascii=False, default=str), encoding="utf-8")
    return snap, out, rep


# ---------- serve(只綁本機 · 只讀) ----------
def make_server(cfg_args: dict, host: str, port: int):
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    if host not in _SAFE_HOSTS:
        raise ValueError(f"serve 只綁本機({' / '.join(_SAFE_HOSTS)}),拒絕 {host}")

    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, code, body: bytes, ctype: str):
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            path = self.path.split("?", 1)[0]
            try:
                cfg = load_config(cfg_args.get("config"), cfg_args.get("sets"))
                if path in ("/", "/index.html"):
                    snap, out, rep = build(cfg, cfg_args.get("home"), cfg_args.get("out"), cfg_args.get("template"))
                    self._send(200, out.read_bytes(), "text/html; charset=utf-8")
                elif path == "/snapshot.json":
                    s = snapshot(cfg, cfg_args.get("home"))
                    self._send(200, json.dumps(s, ensure_ascii=False, default=str).encode("utf-8"), "application/json; charset=utf-8")
                elif path == "/config.json":
                    self._send(200, json.dumps({k: v for k, v in cfg.items()}, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")
                else:
                    self._send(404, b"not found", "text/plain; charset=utf-8")
            except Exception as exc:
                self._send(500, f"{type(exc).__name__}: {exc}".encode("utf-8"), "text/plain; charset=utf-8")

        def do_POST(self):
            self._send(405, "本引擎只讀:不收 POST(操作走 PS 啟動器 / VCGC)".encode("utf-8"), "text/plain; charset=utf-8")

    return ThreadingHTTPServer((host, port), H)


# ---------- CLI ----------
def _args(argv: list):
    import argparse
    ap = argparse.ArgumentParser(prog=TAG)
    ap.add_argument("verb", choices=["build", "serve", "config", "templates", "duck"])
    ap.add_argument("--config"); ap.add_argument("--set", action="append", default=[]); ap.add_argument("--template")
    ap.add_argument("--home"); ap.add_argument("--out"); ap.add_argument("--port", type=int); ap.add_argument("--host")
    ap.add_argument("--init", action="store_true"); ap.add_argument("--json", action="store_true")
    return ap.parse_args(argv)


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    a = _args(argv)
    try:
        cfg = load_config(a.config, a.set)
    except (ValueError, OSError) as exc:
        print(f"[參數] {exc}")
        return 2
    home = Path(a.home) if a.home else default_home()
    if a.verb == "config":
        if a.init:
            WORK_DIR.mkdir(parents=True, exist_ok=True)
            if WORK_CONFIG.exists():
                print(f"[參數] 工作副本已在 {WORK_CONFIG}(不覆蓋)")
            else:
                WORK_CONFIG.write_text(json.dumps({k: v for k, v in cfg.items() if not k.startswith("_")}, ensure_ascii=False, indent=1), encoding="utf-8")
                print(f"[參數] 工作副本寫好 {WORK_CONFIG}(改它 → 重產 / 重新整理即生效)")
        print(json.dumps({k: v for k, v in cfg.items()}, ensure_ascii=False, indent=1))
        return 0
    if a.verb == "templates":
        rows = list_templates(cfg)
        print(f"[範本] {len(rows)} 份 · 夾:{' · '.join(cfg.get('template_dirs', []))} · 目前 active_template = {cfg.get('active_template')}")
        for r in rows:
            print(f"  {r['name']:<44} Jinja 區塊 {'有' if r['jinja'] else '無'} · 變數 {', '.join(r['vars'][:8])}")
        return 0
    if a.verb == "duck":
        inv = duck_inventory(cfg, home)
        if a.json:
            print(json.dumps(inv, ensure_ascii=False, default=str))
            return 0
        print(f"[DuckDB] 庫 {inv['n_dbs']} · 表/視圖 {inv['n_tables']} · 列(估){inv['rows']:,} · 被鎖 {inv['locked']} · {inv['sec']}s")
        for d in inv["dbs"]:
            print(f"  [{d['state']}] {d['name']:<36} {d['mb']:>8} MB · 表 {len(d['tables'])}" + (f" · {d['note']}" if d["note"] else ""))
            for t in d["tables"][:12]:
                print(f"      {t['kind']:<5} {t['table']:<34} 列 {t['rows'] if t['rows'] is not None else t['est_rows']} · 欄 {len(t['columns'])}"
                      + (f" · {t['date_col']} {t['min_date']} → {t['max_date']}" if t["date_col"] else ""))
        return 0
    out = Path(a.out) if a.out else None
    if a.verb == "build":
        try:
            snap, out, rep = build(cfg, home, out, a.template)
        except FileNotFoundError as exc:
            print(f"[範本] {exc}")
            return 2
        d = snap["duckdb"]
        print(f"[ui-engine] {out} · {round(out.stat().st_size / 1024, 1)} KB · {rep['engine']}" + (f" · 範本 {Path(rep['template']).name}" if rep.get("template") else "")
              + f" · DuckDB 庫 {d['n_dbs']} / 表 {d['n_tables']} / 列 {d['rows']:,}" + (f" · 被鎖 {d['locked']}" if d["locked"] else "")
              + f" · 來源 {sum(1 for s in snap['sources'].values() if s['state'] == 'OK')}/{len(snap['sources'])} · LKGC {snap['env']['lkgc']}"
              + (f" · 找不到變數 {', '.join(rep['missing'][:6])}" if rep.get("missing") else "") + (f" · ⚠ {rep['note']}" if rep.get("note") else "")
              + " · 不開瀏覽器(PS 啟動器才開)")
        return 0
    host = a.host or cfg.get("serve", {}).get("host", "127.0.0.1")
    port = a.port or int(cfg.get("serve", {}).get("port", 8766))
    try:
        srv = make_server({"config": a.config, "sets": a.set, "home": home, "out": out, "template": a.template}, host, port)
    except (ValueError, OSError) as exc:
        print(f"[serve] {exc}")
        return 2
    print(f"[serve] http://{host}:{port}/ · 只讀(GET / · /snapshot.json · /config.json)· 每次請求重讀參數 · Ctrl+C 停", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        srv.server_close()
    return 0


# ---------- 自測 ----------
def selftest() -> int:
    import shutil
    import tempfile
    import threading
    import urllib.request
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""))

    global WORK_CONFIG, WORK_DIR
    keep = (WORK_CONFIG, WORK_DIR)
    tmp = Path(tempfile.mkdtemp(prefix="mdl257_"))
    try:
        WORK_DIR = tmp / "work"
        WORK_CONFIG = WORK_DIR / "ui_config.json"
        cfg0 = load_config()
        chk("① 參數正本在:預設 = 內建範本(active_template null)· 只綁本機 · duckdb / sources / nav 段齊",
            cfg0.get("active_template") is None and cfg0["serve"]["host"] == "127.0.0.1" and all(k in cfg0 for k in ("duckdb", "sources", "nav", "theme", "layout")))
        WORK_DIR.mkdir(parents=True)
        WORK_CONFIG.write_text(json.dumps({"app_title": "工作副本", "theme": {"primary_color": "#112233"}}), encoding="utf-8")
        cfg = load_config(sets=["layout.sidebar_width=300px", "layout.show_sidebar=false", "duckdb.max_dbs=5"])
        chk("② 參數疊層:正本 ← 工作副本 ← --set(深合併:其他鍵保留 · 布林 / 數字自動轉型)",
            cfg["app_title"] == "工作副本" and cfg["theme"]["primary_color"] == "#112233" and cfg["theme"].get("bg_color")
            and cfg["layout"]["sidebar_width"] == "300px" and cfg["layout"]["show_sidebar"] is False and cfg["duckdb"]["max_dbs"] == 5, cfg["_layers"])
        home = tmp / "home"
        (home / "output_hub" / "mega").mkdir(parents=True)
        duck = _duck()
        c = duck.connect(str(home / "output_hub" / "mega" / "demo.duckdb"))
        c.execute("CREATE TABLE prices(date DATE, ticker VARCHAR, close DOUBLE)")
        c.execute("INSERT INTO prices VALUES ('2026-09-30','2330',1),('2026-10-02','2330',2),('2026-10-02','2317',3)")
        c.execute("CREATE VIEW v_last AS SELECT * FROM prices WHERE date = (SELECT max(date) FROM prices)")
        c.close()
        lk = duck.connect(str(home / "output_hub" / "mega" / "busy.duckdb"))
        lk.execute("CREATE TABLE t(x INT)")
        cfg["duckdb"]["roots"] = ["{home}"]
        inv = duck_inventory(cfg, home)
        dm = {d["name"]: d for d in inv["dbs"]}
        pr = next(t for t in dm["demo.duckdb"]["tables"] if t["table"] == "prices")
        vw = next(t for t in dm["demo.duckdb"]["tables"] if t["table"] == "v_last")
        chk("③ DuckDB 顯式:表 + 視圖 · 精算列數 · 欄位型別 · 日期欄最早 / 最晚 · 前 N 列樣本",
            pr["rows"] == 3 and [x["name"] for x in pr["columns"]] == ["date", "ticker", "close"] and pr["min_date"] == "2026-09-30"
            and pr["max_date"] == "2026-10-02" and len(pr["sample"]) == 3 and vw["kind"] == "view" and len(vw["sample"]) == 2, (pr, vw))
        chk("④ 別人寫鎖中的庫 = LOCKED(照實,不搶鎖、不崩)", dm["busy.duckdb"]["state"] == "LOCKED", dm["busy.duckdb"])
        lk.close()
        src = tmp / "snap.json"
        src.write_text(json.dumps({"as_of": "2026-10-02", "groups": [{"id": "G1", "zh": "台股", "summary": {"worst": "GREEN"}}],
                                   "live": {"lines": ["a", "b"]}}), encoding="utf-8")
        cfg["sources"] = [{"id": "s1", "title": "測試來源", "path": str(src)}, {"id": "s2", "title": "不在", "path": str(tmp / "no.json")}]
        out = tmp / "ui" / "page.html"
        snap, out, rep = build(cfg, home, out)
        page = out.read_text(encoding="utf-8")
        chk("⑤ 內建標準範本:左面板(回母系統 / 其他系統 / 功能頁 / Live log)· 五頁(儀表板 · 來源 · DuckDB · 環境 · 參數)· 參數面板可匯出 · 零 CDN",
            all(k in page for k in ('id="pg-dash"', 'id="pg-duck"', 'id="pg-param"', "p_export", "回母系統", "Live log"))
            and "window.VIA = " in page and "--via-sidebar:300px" in page and not re.search(r'(src|href)="https?://', page)
            and snap["sources"]["s1"]["state"] == "OK" and snap["sources"]["s2"]["state"] == "NODATA", rep)
        tdir = tmp / "tpl"
        tdir.mkdir()
        (tdir / "Mine.html").write_text("<html><head><title>{{ config.app_title }}</title></head><body>{{ sources.s1.data.as_of }} "
                                        "{{ duckdb.n_dbs }} {{ nope.x }}<i id=c></i><script>document.getElementById('c').textContent=window.VIA_CONFIG.theme.primary_color</script></body></html>",
                                        encoding="utf-8")
        cfg["template_dirs"] = [str(tdir)]
        snap2, out2, rep2 = build(cfg, home, tmp / "ui" / "mine.html", "Mine")
        p2 = out2.read_text(encoding="utf-8")
        chk("⑥ 未來範本:active_template / --template 換版不改程式 · {{ config.x }} / {{ sources… }} 代換 · 注入 window.VIA_CONFIG + 色票 · 找不到變數照留並列出",
            "<title>工作副本</title>" in p2 and "2026-10-02 2" in p2 and "nope.x" in rep2["missing"] and "window.VIA_CONFIG = " in p2
            and "--via-primary:#112233" in p2, rep2)
        try:
            build(cfg, home, tmp / "x.html", "NoSuch")
            ok = False
        except FileNotFoundError as exc:
            ok = "找不到範本" in str(exc)
        chk("⑦ 範本不在 = 誠實報找不到,不退內建假裝成功", ok)
        bad = apply_sets(cfg, ["theme.primary_color=red;}body{display:none"])
        css = theme_css(bad)
        val = re.search(r"--via-primary:([^;]*);", css).group(1)
        chk("⑧ 色票注入防跑版:參數裡的 ; { } < > 會被濾掉(值關在同一個變數裡,跳不出 :root)",
            not any(ch in val for ch in ";{}<>") and css.count("{") == css.count("}"), css[:160])
        try:
            make_server({}, "0.0.0.0", 0)
            ok9 = False
        except ValueError:
            ok9 = True
        srv = make_server({"config": None, "sets": ["duckdb.roots=[\"{home}\"]", "app_title=LIVE"], "home": home, "out": tmp / "srv.html", "template": None}, "127.0.0.1", 0)
        th = threading.Thread(target=srv.serve_forever, daemon=True)
        th.start()
        port = srv.server_address[1]
        body = urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=20).read().decode("utf-8")
        cj = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/config.json", timeout=20).read().decode("utf-8"))
        try:
            urllib.request.urlopen(urllib.request.Request(f"http://127.0.0.1:{port}/", data=b"x", method="POST"), timeout=10)
            post = 200
        except Exception as exc:
            post = getattr(exc, "code", 0)
        srv.shutdown()
        srv.server_close()
        chk("⑨ serve:只綁本機(0.0.0.0 拒)· GET / 每次重讀參數重產 · /config.json · POST 一律 405(只讀)",
            ok9 and "<title>LIVE</title>" in body and cj["app_title"] == "LIVE" and post == 405, (ok9, post))
    finally:
        WORK_CONFIG, WORK_DIR = keep
        shutil.rmtree(tmp, ignore_errors=True)
    ok = sum(res)
    print(f"[計] {TAG} 本版 {ok}/{len(res)} · 合計 {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


if __name__ == "__main__":
    raise SystemExit(main())
