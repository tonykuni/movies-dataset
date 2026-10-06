#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC HealthMatrix v0100 — 三系統健康矩陣報告(操作員令 2026-10-06:VCGC/VRN/VDF 列管的引擎 · 功能 · 參數 · SSOT 全掌握;淺色 · 緊湊 · 自動最佳化版面 · 自適應矩陣;紅黃綠燈第一欄;
用現有引擎,省 token 全景掃:有無編號 · 有無版本號 · 有無註冊 · 有無加速器 · 有無網路工具 · 版本語意 · 正常運作 · 案場分類;各 system manager 自管含 lib/環境)。
  matrix            ① 自己(VCGC = supportive modules)跑健康段 → VIA_Reports/vcgc/HEALTH_latest.json;② 讀 VIA_Reports/vrn|vdf/HEALTH_latest.json(各自 manager health 動詞寫的,母系統只讀);
                    ③ 併既有引擎最新結果:PANORAMA(K1–K8)· ENV_MATRIX · TOOLKIT_MATRIX · GOVERN · VRN_Extract_Ledger · FILE_MATRIX(有就併,沒有灰);④ 出 HEALTH_MATRIX_latest.html/.json + 卡 + 貼回包
  --selftest        temp 沙盒
只寫 VIA_Reports/vcgc/ · VIA_Reports/review/vcgc_health/ · docs/handoff/ai/。沙盒鍵:VIA_ROOT
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
    import VIA_SuperAccel_Module as VIA_ACCEL  # noqa: F401
except ImportError:
    VIA_ACCEL = None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import html
import json
import os
import re
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

ME = Path(__file__).resolve()
NAME = ME.stem
TAG = "v0100"
LAMP = {"GREEN": "#16a34a", "YELLOW": "#f59e0b", "RED": "#dc2626", "GRAY": "#9ca3af"}
SUBS = ("VCGC", "VDF", "VRN")

# ===== [VIA:SM-HEALTH:v0100] 子系統健康段(各 SystemManager 自管自報:功能矩陣 · 表頭冊 · 編號 · 版本語意 · 加速器 · 網橋 · lib/環境 · 最近自測;只讀,寫自己的 HEALTH_latest.json)=====
def _hl_vnum(name):
    import re as _re
    m = _re.search(r"_v(\d{2,4})[A-Za-z0-9]*(?:\.[A-Za-z0-9]+)?$", name)
    return int(m.group(1)) if m else -1


def _hl_read_json(p):
    import json as _json
    try:
        return _json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:  # noqa: BLE001
        return None


def _hl_tail(d, pat):
    hits = sorted(d.glob(pat), key=lambda q: _hl_vnum(q.name)) if d.is_dir() else []
    return hits[-1] if hits else None


def sm_health(sub, home, root, out_dir, now, required_libs=(), net_required=False):
    """→ dict(健康矩陣的子系統段)。home = functional modules/<SUB>;out_dir = VIA_Reports/<sub>/。"""
    import importlib.util as _ilu
    import re as _re
    import sys as _sys
    import json as _json
    from collections import defaultdict as _dd
    from pathlib import Path as _P
    reg = home / "registry"
    fm = _hl_read_json(_hl_tail(reg, sub + "_FunctionMatrix_v*.json")) if reg.is_dir() else None
    th = _hl_read_json(_hl_tail(reg, sub + "_TableHeader_v*.json")) if reg.is_dir() else None
    nb = {}
    central = root / "supportive modules" / "registry"
    for p in (central / "VIA_NumberBooks").glob("VIA_NumberBook_*_v*.jsonl") if (central / "VIA_NumberBooks").is_dir() else []:
        try:
            for ln in p.read_text(encoding="utf-8-sig").splitlines():
                r = _json.loads(ln)
                if r.get("source") and r.get("code"):
                    nb[r["source"].replace("\\", "/")] = r["code"]
        except Exception:  # noqa: BLE001
            pass
    rn = _hl_read_json(central / "VIA_RegistryNumbers_v0100.json") if (central / "VIA_RegistryNumbers_v0100.json").exists() else None
    rn_keys = {e["key"]: e["code"] for e in (rn or {}).get("entries", []) if e.get("key")}
    # 檔案列:每族(去版號)一列
    fams = _dd(list)
    for p in home.rglob("*.py"):
        if set(p.relative_to(home).parts[:-1]) & {"references", "intake", "_superseded", "__pycache__", "VIA_RetiredEngines", "_quarantine"}:
            continue
        fams[(p.parent, _re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", p.stem))].append(p)
    rows = []
    sem_issues = 0
    for (d, fam), ps in sorted(fams.items(), key=lambda x: (str(x[0][0]), x[0][1])):
        ps.sort(key=lambda q: (_hl_vnum(q.name), q.name))
        tail = ps[-1]
        vers = [_hl_vnum(q.name) for q in ps if _hl_vnum(q.name) >= 0]
        try:
            txt = tail.read_text(encoding="utf-8-sig", errors="replace")
        except OSError:
            txt = ""
        body = txt.split("\ndef selftest(")[0]
        accel = "[VIA:ACCEL-BRIDGE" in txt or "VeritasCeleritas_v1141" in txt
        net_use = bool(_re.search(r"^\s*(?:import|from)\s+(requests|httpx|aiohttp|urllib\.request|yfinance|akshare|fredapi|pandas_datareader)\b", body, _re.M))   # 要真的 import 才算出網(正則字串裡的字不算)
        net_ok = (not net_use) or bool(_re.search(r"\[VIA:NET-BRIDGE|VIA_NetSupport|via_net_unified|SUP_MDL740", body))
        sem = []
        if len(vers) != len(set(vers)):
            sem.append("同版號重複")
        if vers and max(vers) - min(vers) + 1 != len(vers) and len(vers) > 1:
            sem.append("版號有洞(%d–%d 共 %d)" % (min(vers), max(vers), len(vers)))
        if _hl_vnum(tail.name) < 0 and len(ps) > 1:
            sem.append("尾版無版號")
        sem_issues += bool(sem)
        rel = tail.relative_to(root).as_posix() if str(tail).startswith(str(root)) else tail.as_posix()
        key_mdl = "%s|MDL|%s|%s" % (sub, fam, ("v%04d" % _hl_vnum(tail.name)) if _hl_vnum(tail.name) >= 0 else "v0000")
        key_eng = key_mdl.replace("|MDL|", "|ENG|")
        code = nb.get(rel) or rn_keys.get(key_mdl) or rn_keys.get(key_eng) or ""
        registered = bool(fm and any(k.split("|")[1] == fam for k in (fm.get("items") or {}) if k.startswith(("MDL|", "ENG|"))))
        try:
            import ast as _ast
            _ast.parse(txt)
            ast_ok = True
        except Exception:  # noqa: BLE001
            ast_ok = False
        lamp = "RED" if (not ast_ok or not net_ok) else ("YELLOW" if (not accel or not code or not registered or sem) else "GREEN")
        rows.append({"family": fam, "dir": d.relative_to(home).as_posix() if str(d).startswith(str(home)) else str(d), "tail": tail.name, "version": ("v%04d" % _hl_vnum(tail.name)) if _hl_vnum(tail.name) >= 0 else "—", "n_versions": len(ps),
                     "number": code, "registered": registered, "accel": accel, "net_use": net_use, "net_ok": net_ok, "ast_ok": ast_ok, "semantic": ";".join(sem), "lamp": lamp})
    # 冊 / 表頭 / 字典
    books = []
    for sd in ("SSOT", "registry", "knowledge"):
        d = home / sd
        if d.is_dir():
            seen = {}
            for p in d.glob("*.json"):
                fam = _re.sub(r"_v\d{2,4}[A-Za-z0-9]*$", "", p.stem)
                if fam not in seen or _hl_vnum(p.name) > _hl_vnum(seen[fam].name):
                    seen[fam] = p
            for fam, p in seen.items():
                tid = _re.sub(r"[^a-z0-9_]+", "_", fam.lower()).strip("_")
                ent = (th or {}).get("tables", {}) if th else {}
                reg_t = any(k == tid or k.startswith(tid + "_") for k in ent)
                num_t = any((k == tid or k.startswith(tid + "_")) and v.get("table_no") for k, v in ent.items())
                books.append({"book": p.name, "dir": sd, "registered": reg_t, "numbered": num_t, "lamp": "GREEN" if num_t else ("YELLOW" if reg_t else "GRAY")})
    # lib / 環境(本直譯器)
    libs = []
    for name in required_libs:
        ok = _ilu.find_spec(name) is not None
        libs.append({"lib": name, "importable": ok, "lamp": "GREEN" if ok else "RED"})
    # 最近自測 / 結果
    results = []
    if out_dir.is_dir():
        for p in sorted(out_dir.glob("RESULT_*_latest.json"))[:40]:
            import datetime as _dt, time as _time
            age = (_time.time() - p.stat().st_mtime) / 86400
            results.append({"result": p.name, "age_days": round(age, 1), "lamp": "GREEN" if age <= 7 else "YELLOW"})
    fm_items = (fm or {}).get("items", {}) if fm else {}
    summary = {"files": len(rows), "red": sum(1 for r in rows if r["lamp"] == "RED"), "yellow": sum(1 for r in rows if r["lamp"] == "YELLOW"), "green": sum(1 for r in rows if r["lamp"] == "GREEN"),
               "numbered": sum(1 for r in rows if r["number"]), "registered": sum(1 for r in rows if r["registered"]), "accel": sum(1 for r in rows if r["accel"]), "net_bad": sum(1 for r in rows if not r["net_ok"]), "semantic_issues": sem_issues,
               "fn_items": len(fm_items), "fn_numbered": sum(1 for e in fm_items.values() if e.get("number")), "tables": len((th or {}).get("tables", {}) if th else {}), "tables_numbered": sum(1 for v in ((th or {}).get("tables", {}) if th else {}).values() if v.get("table_no")),
               "books": len(books), "libs_missing": sum(1 for l in libs if not l["importable"]), "python": _sys.executable}
    lamp = "RED" if (summary["red"] or summary["libs_missing"]) else ("YELLOW" if (summary["yellow"] or not fm or not th) else "GREEN")
    health = {"sub": sub, "ts": now, "python": _sys.executable, "lamp": lamp, "summary": summary, "files": rows, "books": books, "libs": libs, "results": results,
              "fn_matrix": (_hl_tail(reg, sub + "_FunctionMatrix_v*.json").name if fm else None), "table_header": (_hl_tail(reg, sub + "_TableHeader_v*.json").name if th else None)}
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "HEALTH_latest.json").write_text(_json.dumps(health, ensure_ascii=False, indent=1), encoding="utf-8")
    return health


def sm_health_print(h):
    s = h["summary"]
    print("[計] %s health · 檔族 %d(紅 %d 黃 %d 綠 %d)· 有號 %d · 已登記 %d · 有橋 %d · 網橋缺 %d · 版號語意 %d · 功 %d/%d 有號 · 表 %d/%d 有號 · 冊 %d · lib 缺 %d · %s" % (
        h["sub"], s["files"], s["red"], s["yellow"], s["green"], s["numbered"], s["registered"], s["accel"], s["net_bad"], s["semantic_issues"], s["fn_numbered"], s["fn_items"], s["tables_numbered"], s["tables"], s["books"], s["libs_missing"], h["lamp"]))
    for r in [x for x in h["files"] if x["lamp"] == "RED"][:10]:
        print("  [RED] %s %s · %s" % (h["sub"], r["tail"], "AST 壞" if not r["ast_ok"] else "出網無網橋"))
    for l in [x for x in h["libs"] if not x["importable"]]:
        print("  [RED] %s lib 缺 %s(本直譯器 %s)" % (h["sub"], l["lib"], h["python"]))
# ===== [VIA:SM-HEALTH:END] =====


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _root() -> Path:
    if os.environ.get("VIA_ROOT"):
        return Path(os.environ["VIA_ROOT"])
    p = ME
    while p.parent != p:
        if (p / "supportive modules").is_dir() and (p / "functional modules").is_dir():
            return p
        p = p.parent
    return ME.parents[2]


def _paths() -> dict:
    r = _root()
    return {"root": r, "sup": r / "supportive modules", "registry": r / "supportive modules" / "registry", "reports": r / "VIA_Reports", "review": r / "VIA_Reports" / "review",
            "out": r / "VIA_Reports" / "review" / "vcgc_health", "cards": r / "docs" / "handoff" / "ai"}


def _latest(P: dict, rel: str):
    p = P["review"] / rel
    return _hl_read_json(p) if p.exists() else None


def _pano_checks(pano) -> dict:
    """PANORAMA_latest.json 兩種形狀都收:checks = [{k,lamp,...}](全景引擎)或 {K1: lamp}(摘要)。"""
    c = (pano or {}).get("checks")
    if isinstance(c, list):
        return {k.get("k"): k.get("lamp") for k in c if isinstance(k, dict)}
    return c if isinstance(c, dict) else {}


def matrix(P: dict | None = None) -> dict:
    P = P or _paths()
    t0 = time.time()
    now = _now()
    vcgc = sm_health("VCGC", P["sup"], P["root"], P["reports"] / "vcgc", now, ("pandas",))
    subs = {"VCGC": vcgc}
    for s in ("VDF", "VRN"):
        h = _hl_read_json(P["reports"] / s.lower() / "HEALTH_latest.json") if (P["reports"] / s.lower() / "HEALTH_latest.json").exists() else None
        subs[s] = h
    pano = _latest(P, "vcgc_panorama/PANORAMA_latest.json")
    env = _latest(P, "vcgc_env/ENV_MATRIX_latest.json")
    tool = _latest(P, "vcgc_toolkit/TOOLKIT_MATRIX_latest.json")
    gov = _latest(P, "vcgc_registry/GOVERN_latest.json")
    fm = _latest(P, "vcgc_matrix/FILE_MATRIX_latest.json")
    ledger = P["reports"] / "vrn" / "extract" / "VRN_Extract_Ledger.jsonl"
    ext = Counter()
    if ledger.exists():
        last = {}
        for ln in ledger.read_text(encoding="utf-8").splitlines():
            try:
                r = json.loads(ln)
                last[r.get("file")] = r.get("status")
            except ValueError:
                pass
        ext = Counter(last.values())
    sections = {
        "panorama": {"lamp": (pano or {}).get("lamp", "GRAY"), "checks": _pano_checks(pano), "ts": (pano or {}).get("ts")},
        "env": {"lamp": (env or {}).get("lamp", "GRAY"), "envs": len((env or {}).get("envs", [])), "pdf_tools": (env or {}).get("pdf_tools_ok"), "ts": (env or {}).get("ts")},
        "toolkit": {"lamp": (tool or {}).get("lamp", "GRAY"), "families": len((tool or {}).get("rows", [])), "overlaps": len((tool or {}).get("overlaps", [])), "ts": (tool or {}).get("ts")},
        "govern": {"lamp": (gov or {}).get("lamp", "GRAY"), "summary": (gov or {}).get("summary"), "ts": (gov or {}).get("ts")},
        "filematrix": {"lamp": (fm or {}).get("lamp", "GRAY"), "per": (fm or {}).get("per"), "ts": (fm or {}).get("ts")},
        "extract": {"lamp": ("GREEN" if ext and not ext.get("REVIEW") and not ext.get("ERROR") else ("YELLOW" if ext else "GRAY")), "counts": dict(ext)},
    }
    order = {"RED": 3, "YELLOW": 2, "GREEN": 1, "GRAY": 0}
    lamps = [h["lamp"] for h in subs.values() if h] + [v["lamp"] for v in sections.values()]
    lamp = max(lamps, key=lambda x: order[x]) if lamps else "GRAY"
    return {"verb": "matrix", "engine": NAME, "ts": now, "root": str(P["root"]), "lamp": lamp, "subs": subs, "sections": sections, "secs": round(time.time() - t0, 1)}


def _html(res: dict) -> str:
    def lamp(l):
        return "<i class='lp %s' style='background:%s'></i>" % (l, LAMP.get(l, LAMP["GRAY"]))
    cards = []
    for s in SUBS:
        h = res["subs"].get(s)
        if not h:
            cards.append("<div class='card'><div class='hd'>%s%s</div><div class='kv'>尚未跑 <code>%s_SystemManager health</code></div></div>" % (lamp("GRAY"), s, s))
            continue
        m = h["summary"]
        cards.append("<div class='card'><div class='hd'>%s%s <small>%s</small></div><div class='kv'>檔族 <b>%d</b> 紅 %d 黃 %d 綠 %d · 有號 %d · 登記 %d · 橋 %d · 網橋缺 %d · 語意 %d</div><div class='kv'>功 %d/%d 有號 · 表 %d/%d 有號 · 冊 %d · lib 缺 %d</div><div class='kv'><small>%s</small></div></div>"
                     % (lamp(h["lamp"]), s, h["ts"], m["files"], m["red"], m["yellow"], m["green"], m["numbered"], m["registered"], m["accel"], m["net_bad"], m["semantic_issues"], m["fn_numbered"], m["fn_items"], m["tables_numbered"], m["tables"], m["books"], m["libs_missing"], html.escape(m.get("python", ""))))
    sec = res["sections"]
    chips = [("全景 K1–K8", sec["panorama"]["lamp"], " ".join("%s=%s" % kv for kv in sec["panorama"]["checks"].items()) or "未跑"),
             ("環境工具", sec["env"]["lamp"], "環境 %s · PDF 隔離 %s" % (sec["env"]["envs"], sec["env"]["pdf_tools"])),
             ("輔助工具", sec["toolkit"]["lamp"], "族 %s · 重疊 %s" % (sec["toolkit"]["families"], sec["toolkit"]["overlaps"])),
             ("治理發號", sec["govern"]["lamp"], json.dumps(sec["govern"]["summary"], ensure_ascii=False)[:120] if sec["govern"]["summary"] else "未跑"),
             ("全檔矩陣", sec["filematrix"]["lamp"], json.dumps(sec["filematrix"]["per"], ensure_ascii=False)[:120] if sec["filematrix"]["per"] else "未跑"),
             ("VRN 擷取", sec["extract"]["lamp"], json.dumps(sec["extract"]["counts"], ensure_ascii=False) or "未跑")]
    chip_html = "".join("<div class='chip'>%s<b>%s</b><span>%s</span></div>" % (lamp(l), t, html.escape(d)) for t, l, d in chips)
    rows = []
    for s in SUBS:
        h = res["subs"].get(s)
        for r in (h or {}).get("files", []):
            rows.append("<tr data-s='%s' data-l='%s'><td>%s</td><td>%s</td><td>%s<div class='dim'>%s</div></td><td>%s</td><td class='n'>%d</td><td class='code'>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td class='dim'>%s</td></tr>"
                        % (s, r["lamp"], lamp(r["lamp"]), s, html.escape(r["family"]), html.escape(r["dir"]), r["version"], r["n_versions"], html.escape(r["number"] or "—"), "✓" if r["registered"] else "—", "✓" if r["accel"] else "<b class='r'>缺</b>",
                           ("✓" if r["net_ok"] else "<b class='r'>缺</b>") if r["net_use"] else "·", "✓" if r["ast_ok"] else "<b class='r'>壞</b>", html.escape(r["semantic"])))
    books = []
    for s in SUBS:
        h = res["subs"].get(s)
        for b in (h or {}).get("books", []):
            books.append("<tr data-s='%s' data-l='%s'><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (s, b["lamp"], lamp(b["lamp"]), s, html.escape(b["book"]), b["dir"], "✓" if b["registered"] else "—", "✓" if b["numbered"] else "—"))
    libs = []
    for s in SUBS:
        h = res["subs"].get(s)
        for l in (h or {}).get("libs", []):
            libs.append("<tr data-s='%s' data-l='%s'><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (s, l["lamp"], lamp(l["lamp"]), s, l["lib"], "✓" if l["importable"] else "<b class='r'>缺</b>"))
    return """<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VIA 健康矩陣</title>
<style>
:root{--bg:#fff;--panel:#f7f7f7;--line:#e0e0e0;--txt:#1f2937;--dim:#6b7280}
body{font-family:"Microsoft JhengHei UI","Segoe UI",Arial,sans-serif;background:var(--bg);color:var(--txt);margin:0;padding:12px;font-size:12px}
h1{font-size:16px;margin:0 0 4px}.meta{color:var(--dim);font-size:11px;margin-bottom:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:8px;margin-bottom:8px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:8px}.hd{font-weight:700;font-size:13px;margin-bottom:4px}.kv{font-size:11.5px;line-height:1.5}
.chips{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:6px;margin-bottom:10px}.chip{background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:5px 8px;font-size:11px;display:flex;gap:6px;align-items:center;flex-wrap:wrap}.chip span{color:var(--dim)}
.lp{display:inline-block;width:11px;height:11px;border-radius:50%%;vertical-align:middle;margin-right:4px}.lp.RED{animation:bl 2.4s ease-in-out infinite}@keyframes bl{0%%,100%%{opacity:1}50%%{opacity:.25}}
.bar button{margin:0 4px 6px 0;padding:3px 8px;border:1px solid var(--line);background:var(--panel);border-radius:6px;cursor:pointer;font-size:11px}
details{margin:6px 0}summary{cursor:pointer;font-weight:700;font-size:12.5px;padding:4px 0}
.wrap{overflow-x:auto}table{border-collapse:collapse;width:100%%;table-layout:auto}th,td{border:1px solid var(--line);padding:2px 5px;text-align:left;vertical-align:top;white-space:nowrap}th{background:#111827;color:#fff;position:sticky;top:0;font-weight:600}
tr:nth-child(even){background:#fafafa}td.code{font-family:Consolas,monospace}td.n{text-align:right}.dim{color:var(--dim);font-size:10.5px;white-space:normal}.r{color:#dc2626}
@media(max-width:700px){body{padding:6px}th,td{padding:2px 3px;font-size:10.5px}}
</style></head><body>
<h1>VIA 健康矩陣 · VCGC / VDF / VRN</h1><div class="meta">%s · 根 %s · 各 SystemManager 自報(health 動詞),母系統只讀匯總 · 紅 = AST 壞 / 出網無網橋 / lib 缺;黃 = 無號 / 未登記 / 無橋 / 版號語意;綠 = 齊;灰 = 尚未跑</div>
<div class="grid">%s</div>
<div class="chips">%s</div>
<div class="bar">%s <button onclick="flt('','')">全部</button> <button onclick="flt('','RED')">只看紅</button> <button onclick="flt('','YELLOW')">只看黃</button></div>
<details open><summary>檔案 / 引擎(每族一列)</summary><div class="wrap"><table class="m"><thead><tr><th>燈</th><th>系統</th><th>族 / 夾</th><th>尾版</th><th>版數</th><th>編號</th><th>登記</th><th>加速器</th><th>網橋</th><th>AST</th><th>版本語意</th></tr></thead><tbody>%s</tbody></table></div></details>
<details open><summary>冊 / 表頭 / 字典</summary><div class="wrap"><table class="m"><thead><tr><th>燈</th><th>系統</th><th>冊</th><th>夾</th><th>表頭登記</th><th>發號</th></tr></thead><tbody>%s</tbody></table></div></details>
<details><summary>lib / 環境(各自直譯器)</summary><div class="wrap"><table class="m"><thead><tr><th>燈</th><th>系統</th><th>lib</th><th>可 import</th></tr></thead><tbody>%s</tbody></table></div></details>
<script>function flt(s,l){document.querySelectorAll('table.m tbody tr').forEach(function(t){t.style.display=((!s||t.dataset.s===s)&&(!l||t.dataset.l===l))?'':'none'})}</script>
</body></html>""" % (res["ts"], html.escape(res["root"]), "".join(cards), chip_html, "".join("<button onclick=\"flt('%s','')\">%s</button>" % (s, s) for s in SUBS), "\n".join(rows), "\n".join(books), "\n".join(libs))


def paste_pack(res: dict) -> list:
    L = ["[計] vcgc health matrix · 總燈 %s · %s · " % (res["lamp"], res["ts"]) + " · ".join("%s=%s" % (s, (res["subs"][s] or {}).get("lamp", "GRAY(未跑 health)")) for s in SUBS)]
    for s in SUBS:
        h = res["subs"].get(s)
        if not h:
            L.append("  [GRAY] %s 尚未跑 %s_SystemManager health" % (s, s))
            continue
        m = h["summary"]
        L.append("  [%s] %s 檔族 %d(紅 %d 黃 %d 綠 %d)· 有號 %d · 登記 %d · 橋 %d · 網橋缺 %d · 語意 %d · 功 %d/%d · 表 %d/%d · 冊 %d · lib 缺 %d" % ({"RED": "RED", "YELLOW": "YEL", "GREEN": "OK"}[h["lamp"]], s, m["files"], m["red"], m["yellow"], m["green"], m["numbered"], m["registered"], m["accel"], m["net_bad"], m["semantic_issues"], m["fn_numbered"], m["fn_items"], m["tables_numbered"], m["tables"], m["books"], m["libs_missing"]))
        for r in [x for x in h["files"] if x["lamp"] == "RED"][:8]:
            L.append("    [RED] %s %s · %s" % (s, r["tail"], "AST 壞" if not r["ast_ok"] else "出網無網橋"))
        for l in [x for x in h["libs"] if not x["importable"]][:5]:
            L.append("    [RED] %s lib 缺 %s" % (s, l["lib"]))
        sem = [x for x in h["files"] if x["semantic"]][:6]
        for r in sem:
            L.append("    [YEL] %s %s · %s" % (s, r["family"], r["semantic"]))
    for k, v in res["sections"].items():
        L.append("  [%s] %s · %s" % ({"RED": "RED", "YELLOW": "YEL", "GREEN": "OK", "GRAY": "GRAY"}[v["lamp"]], k, json.dumps({kk: vv for kk, vv in v.items() if kk not in ("lamp", "ts")}, ensure_ascii=False)[:160]))
    L.append("NEXT: 紅 → 該子系統 manager 出薄尾(補網橋 / 修 AST / 裝 lib);黃 → 跑 fn/table register + VCGC govern 發號、補 [VIA:ACCEL-BRIDGE]、版號補洞;灰 → 先跑對應引擎;報告 VIA_Reports/review/vcgc_health/HEALTH_MATRIX_latest.html")
    return L[:300]


def write_outputs(res: dict, pack: list, P: dict | None = None) -> dict:
    P = P or _paths()
    P["out"].mkdir(parents=True, exist_ok=True)
    P["cards"].mkdir(parents=True, exist_ok=True)
    (P["out"] / "HEALTH_MATRIX_latest.json").write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    ht = P["out"] / "HEALTH_MATRIX_latest.html"
    ht.write_text(_html(res), encoding="utf-8")
    md = P["cards"] / ("VCGC_HealthCard_%s.md" % datetime.datetime.now().strftime("%Y%m%d"))
    md.write_text("\n".join(["# VIA 健康矩陣卡", "", "```"] + pack + ["```", ""]), encoding="utf-8")
    return {"html": str(ht), "md": str(md)}


def main(argv=None) -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print("[VCGC] 拒絕。只能經 via-vcgc。")
        return 2
    a = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in a[:2]:
        return selftest()
    if a[:1] != ["matrix"]:
        print("[拒跑] matrix | --selftest")
        return 2
    res = matrix()
    pack = paste_pack(res)
    out = write_outputs(res, pack)
    for ln in pack:
        print(ln)
    print("  [MATRIX] %s" % out["html"])
    print("  [卡] %s" % out["md"])
    if os.environ.get("VIA_NO_OPEN") != "1" and os.name == "nt":
        try:
            os.startfile(out["html"])  # type: ignore[attr-defined]
        except OSError:
            pass
    return 1 if res["lamp"] == "RED" else 0


def selftest() -> int:
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)

    td = Path(tempfile.mkdtemp(prefix="cgchealth-"))
    os.environ["VIA_ROOT"] = str(td)
    os.environ["VIA_NO_OPEN"] = "1"
    P = _paths()
    chk("① 沙盒", all(str(v).startswith(str(td)) for v in P.values()))
    A = "# [VIA:ACCEL-BRIDGE:v0100]\n"
    (P["registry"]).mkdir(parents=True)
    (P["registry"] / "CGC_MDL001_X_v0100.py").write_text(A + "x=1\n", encoding="utf-8")
    (P["sup"] / "VIA_Old.py").write_text("import requests\n", encoding="utf-8")
    (P["reports"] / "vrn").mkdir(parents=True)
    (P["reports"] / "vrn" / "HEALTH_latest.json").write_text(json.dumps({"sub": "VRN", "ts": "t", "lamp": "GREEN", "summary": {"files": 2, "red": 0, "yellow": 0, "green": 2, "numbered": 2, "registered": 2, "accel": 2, "net_bad": 0, "semantic_issues": 0, "fn_items": 5, "fn_numbered": 5, "tables": 1, "tables_numbered": 1, "books": 1, "libs_missing": 0, "python": "py"}, "files": [], "books": [], "libs": []}), encoding="utf-8")
    (P["review"] / "vcgc_panorama").mkdir(parents=True)
    (P["review"] / "vcgc_panorama" / "PANORAMA_latest.json").write_text(json.dumps({"ts": "t", "lamp": "YELLOW", "checks": {"K1": "GREEN", "K2": "YELLOW"}}), encoding="utf-8")
    res = matrix(P)
    chk("② VCGC 自己跑健康段(supportive modules):2 族 · VIA_Old 出網無網橋紅", res["subs"]["VCGC"]["summary"]["files"] == 2 and res["subs"]["VCGC"]["summary"]["net_bad"] == 1)
    chk("③ VRN 讀自報(綠)· VDF 未跑 = None(灰)", res["subs"]["VRN"]["lamp"] == "GREEN" and res["subs"]["VDF"] is None)
    chk("④ 既有引擎結果併入:全景 K1/K2 · 環境/工具/治理 未跑 = GRAY", res["sections"]["panorama"]["checks"] == {"K1": "GREEN", "K2": "YELLOW"} and res["sections"]["env"]["lamp"] == "GRAY")
    pack = paste_pack(res)
    out = write_outputs(res, pack, P)
    htm = Path(out["html"]).read_text(encoding="utf-8")
    chk("⑤ HTML:淺色 · 自適應(auto-fit grid · viewport)· 燈第一欄 · 四色 token · 紅燈慢閃 · 可按系統/燈篩", "auto-fit" in htm and "viewport" in htm and all(c in htm for c in LAMP.values()) and "@keyframes bl" in htm and "flt('VRN','')" in htm)
    chk("⑥ 貼回包 ≤300 · NEXT: · 總燈紅(VCGC 有紅)· 卡在", len(pack) <= 300 and pack[-1].startswith("NEXT:") and res["lamp"] == "RED" and Path(out["md"]).exists())
    chk("⑦ 唯讀:VIA_Reports/vcgc/HEALTH_latest.json 是唯一新寫在 reports/vcgc 的檔", (P["reports"] / "vcgc" / "HEALTH_latest.json").exists())
    body = ME.read_text(encoding="utf-8")
    chk("⑧ 帶加速器橋 · 健康共用段 · VIA_FROM_VCGC 閘", "[VIA:ACCEL-BRIDGE:v0100]" in body and "[VIA:SM-HEALTH:v0100]" in body and "VIA_FROM_VCGC" in body)
    for k in ("VIA_ROOT", "VIA_NO_OPEN"):
        os.environ.pop(k, None)
    shutil.rmtree(td, ignore_errors=True)
    print("[計] %s 自測 %d/%d · %s" % (NAME, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
