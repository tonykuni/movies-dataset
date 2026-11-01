#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VDF_ENG236_FetchMatrixUI v0100 — VDF 擷取矩陣 HTML U/I:依資料庫分段 · 每表一列 · 來源徽章 · 端點與實測狀態 · 庫況燈 · 點列看明細

操作員令(2026-11-01):「參考這種方式有架構地呈現擷取項目於 HTML U/I」(範本 taiwan_stock_data_matrix.html:表頭統計 · 來源圖例篩選 ·
  每個 DuckDB 一段矩陣「資料 / 來源 / 端點 / 狀態」· 點一列展開明細 · 底部來源總結卡)。
本引擎只讀 VDF 自己的冊與報告,組成一份模型(JSON)再畫成一頁(HTML;零 CDN · 系統字型 · 窄螢幕自動改單欄):
  ① 表 · 庫 · 寫入者 · 角色:VIA_DB_Table_SSOT 尾版(只讀)+ VDF_FetchGroups_SSOT 族群裡的表(含 VDF_TWIndex_Daily · parquet · VAKE)。
  ② 族群 · 大類 · 頻率 · 成員規則 · 補料來源:VDF_FetchGroups_SSOT 尾版。
  ③ 引擎(檔名 · 角色 · 分組):VDF_FetchSystem_SSOT 尾版;引擎自測燈:VIA_Reports/vdf/RESULT_engine_launch_latest.json(有才讀)。
  ④ 中文名 · 來源 · 端點引用:VDF_FetchMatrixUI_SSOT 尾版(顯示冊);端點路徑與實測狀態回 VIA_VDF_TWMarketEndpoints_SSOT 讀
     (VERIFIED · CANDIDATE · TREE_EVIDENCE · DEAD · UNKNOWN 照抄,不另判)。顯示冊沒登的表 → 依擷取冊引擎分組推定來源,頁上標「推定」。
  ⑤ 庫況:VIA_Reports/vdf/DB_CHECK_latest.json(VDF db check;燈 · 列數 · 最新日 · 落後天);沒有 → 「未量」(不冒充綠)。
  ⑥ 他系統寫的表(vrn_ · via_policy_ · via_handover)另成一段,只攤開不代修(L123 四系統互不干涉)。
用法:python VDF_ENG236_FetchMatrixUI_v0100.py build [--out 夾] [--db-check DB_CHECK.json] [--json] · --selftest
輸出:<out>/FETCH_MATRIX_latest.html · FETCH_MATRIX_latest.json(預設 out = VIA_Reports/vdf)。
VDF 自己的模組:只讀冊 / 報告,只寫上面兩個檔;零網路;不匯入他系統程式;同意閘不讀不寫;不碰 TA-Lib;不裝套件。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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


import datetime
import html
import json
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent if HERE.name == "engine" else HERE
VIA = VDF.parents[1]
REG = VIA / "supportive modules" / "registry"
TAG = "VDF_ENG236_FetchMatrixUI v" + Path(__file__).stem.rsplit("_v", 1)[-1]
STATE_RANK = {"VERIFIED": 0, "TREE_EVIDENCE": 1, "CANDIDATE": 2, "UNKNOWN": 3, "DEAD": 4}
LAMP_ZH = {"GREEN": "到齊", "YELLOW": "待補", "RED": "缺", "INFO": "他系統", "NONE": "未量"}


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


def tail(folder: Path, glob: str) -> Path | None:
    hits = [p for p in Path(folder).glob(glob) if _vnum(p) >= 0]
    return max(hits, key=_vnum) if hits else None


def _load(p: Path | None):
    if not p or not Path(p).is_file():
        return None
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def load_books(via: Path | None = None) -> dict:
    """各冊尾版(只讀)→ {名: (路徑, 內容)};缺冊回 (None, None),模型照實標。"""
    via = Path(via or VIA)
    vdf, reg = via / "functional modules" / "VDF", via / "supportive modules" / "registry"
    out = {}
    for key, folder, glob in (("ui", vdf, "VDF_FetchMatrixUI_SSOT_v*.json"), ("groups", vdf, "VDF_FetchGroups_SSOT_v*.json"),
                              ("fetch", vdf, "VDF_FetchSystem_SSOT_v*.json"), ("tables", reg, "VIA_DB_Table_SSOT_v*.json"),
                              ("endpoints", reg, "VIA_VDF_TWMarketEndpoints_SSOT_v*.json")):
        p = tail(folder, glob)
        out[key] = (p.name if p else None, _load(p))
    th = vdf / "registry" / "VDF_TableHeader_v0100.json"
    out["headers"] = (th.name if th.is_file() else None, _load(th))
    return out


def _dig(obj, ref: str):
    for part in ref.split("."):
        if not isinstance(obj, dict) or part not in obj:
            return None
        obj = obj[part]
    return obj


def endpoint_of(src: dict, ep_book: dict | None) -> dict:
    """顯示冊的一個來源 → {path, state, base, zh, gives, evidence};ep 引用回端點冊讀,讀不到 = UNKNOWN(照實)。"""
    if src.get("ep"):
        node = _dig(ep_book or {}, src["ep"])
        ex = src["ep"].split(".", 1)[0]
        base = _dig(ep_book or {}, ex + ".base") if ex in ("twse", "tpex") else None
        if isinstance(node, dict):
            path = node.get("path") or ""
            state = node.get("state") or "UNKNOWN"
            if not path and isinstance(node.get("twse"), str):
                path = node["twse"]
            return {"path": path or "路徑未知(不編)", "state": state, "base": base if path else None, "zh": node.get("zh"), "gives": node.get("gives") or [],
                    "evidence": node.get("evidence") or node.get("why_unknown") or node.get("probe_error") or node.get("note"), "ref": src["ep"]}
        if isinstance(node, str):
            parent = _dig(ep_book or {}, src["ep"].rsplit(".", 1)[0]) or {}
            return {"path": node, "state": parent.get("state") or "UNKNOWN", "base": base, "zh": parent.get("zh"), "gives": [],
                    "evidence": parent.get("evidence") or parent.get("note"), "ref": src["ep"]}
        return {"path": "路徑未知(不編)", "state": "UNKNOWN", "base": None, "zh": None, "gives": [], "evidence": "端點冊沒有 %s(不編一條)" % src["ep"], "ref": src["ep"]}
    if src.get("endpoint"):
        return {"path": src["endpoint"], "state": src.get("state") or "UNKNOWN", "base": None, "zh": None, "gives": [], "evidence": None, "ref": None}
    return {"path": "", "state": None, "base": None, "zh": None, "gives": [], "evidence": None, "ref": None}


def _eid(name: str) -> str:
    """VDF_ENG073 / ENG073 / e073 / 073 / 009 → 擷取冊的引擎鍵(e073 · 009)。"""
    m = re.search(r"ENG(\d{3})", str(name))
    if m:
        return "e" + m.group(1)
    m = re.search(r"MDL(\d{3})", str(name))
    return m.group(1) if m else str(name)


def _db_check_index(dbc: dict | None) -> dict:
    idx = {}
    for r in (dbc or {}).get("rows") or []:
        db, tb = r.get("庫") or r.get("db"), r.get("表") or r.get("table")
        if db and tb:
            idx[(db, tb)] = r
    return idx


def build_model(books: dict, dbc: dict | None = None, launch: dict | None = None, now: str | None = None) -> dict:
    ui = (books.get("ui") or (None, None))[1] or {}
    groups_book = (books.get("groups") or (None, None))[1] or {}
    fetch_book = (books.get("fetch") or (None, None))[1] or {}
    tables_book = (books.get("tables") or (None, None))[1] or {}
    ep_book = (books.get("endpoints") or (None, None))[1] or {}
    hdr_book = (books.get("headers") or (None, None))[1] or {}
    provs = ui.get("providers") or {}
    eng = {e.get("id"): e for e in fetch_book.get("engines") or [] if isinstance(e, dict)}
    eng_by_table = {}                             # 擷取冊引擎自己登的 tables(例 OmniFetch e055* 寫 etf_stats_daily)
    for k, e in eng.items():
        for tt in e.get("tables") or []:
            eng_by_table.setdefault(tt if isinstance(tt, str) else (tt or {}).get("table"), []).append(k)
    egp = ui.get("engine_group_providers") or {}
    cats = {c["id"]: c for c in groups_book.get("categories") or [] if isinstance(c, dict) and c.get("id")}
    gmeta, tab_groups, gorder = {}, {}, {}
    for g in groups_book.get("groups") or []:
        gmeta[g["id"]] = g
        gorder[g["id"]] = len(gorder)
        for s in g.get("sources") or []:
            if s.get("type") == "duckdb" and s.get("table"):
                tab_groups.setdefault((s["db"], s["table"]), []).append(g["id"])
            elif s.get("type") == "parquet" and s.get("glob"):
                tab_groups.setdefault(("parquet", Path(s["glob"]).stem), []).append(g["id"])
            elif s.get("type") == "vake":
                tab_groups.setdefault(("vake", g["id"]), []).append(g["id"])
    launch_idx = {}
    for p in (launch or {}).get("per") or []:
        launch_idx[_eid(p.get("eid") or p.get("family") or "")] = p.get("selftest_lamp")
    rows_src = [dict(t) for t in tables_book.get("tables") or [] if isinstance(t, dict) and t.get("db") and t.get("table")]
    have = {(t["db"], t["table"]) for t in rows_src}
    for (db, tb), gids in tab_groups.items():
        if (db, tb) not in have:
            rows_src.append({"db": db, "table": tb, "role": "族群冊", "writers": [], "from_groups_only": True})
            have.add((db, tb))
    dbc_idx = _db_check_index(dbc)
    other_px = tuple(ui.get("other_system_prefixes") or ("vrn_", "via_policy_", "via_handover"))
    hdr_tables = hdr_book.get("tables") or {}
    rows = []
    for t in rows_src:
        db, tb = t["db"], t["table"]
        gids = tab_groups.get((db, tb), [])
        g = gmeta.get(gids[0]) if gids else None
        cur = (ui.get("tables") or {}).get(tb) or ((ui.get("vake_groups") or {}).get(tb) and {"label": ui["vake_groups"][tb]}) or {}
        writers = list(t.get("writers") or [])
        other = tb.startswith(other_px) or any(str(w).startswith(("VRN_", "VIA_VRN")) for w in writers)
        engines = []
        for e in list(g.get("engines") or []) if g else []:
            engines.append(e)
        for w in writers:
            k = _eid(w)
            if k not in engines:
                engines.append(k)
        for k in eng_by_table.get(tb, []):
            if k not in engines:
                engines.append(k)
        srcs, basis = [], "冊"
        if cur.get("sources"):
            for s in cur["sources"]:
                ep = endpoint_of(s, ep_book)
                srcs.append({"provider": s["provider"], "role": s.get("role") or "primary", "label": s.get("label"), "engines": s.get("engines") or [], **ep})
        elif g and g.get("refill"):
            basis = "族群冊補料來源(推定)"
            for r in g["refill"]:
                pv = r.get("provider")
                plist = (["MOPS"] if "MOPS" in (r.get("label") or "") else ["TWSE", "TPEX"]) if pv == "GOV" else [pv if pv in provs else "OTHER"]
                for pp in plist:
                    srcs.append({"provider": pp, "role": "primary", "label": r.get("label"), "engines": r.get("engines") or [], "path": "", "state": None,
                                 "base": None, "zh": None, "gives": [], "evidence": r.get("note"), "ref": None})
        elif not other:
            basis = "擷取冊引擎分組(推定)"
            seen = set()
            for k in engines:
                for pp in egp.get((eng.get(k) or {}).get("group") or "", []):
                    if pp not in seen:
                        seen.add(pp)
                        srcs.append({"provider": pp, "role": "primary", "label": "引擎 %s 分組 %s" % (k, eng[k].get("group")), "engines": [k], "path": "",
                                     "state": None, "base": None, "zh": None, "gives": [], "evidence": None, "ref": None})
            if not srcs:
                basis = "未登(冊上找不到來源)"
        providers = sorted({s["provider"] for s in srcs}, key=lambda x: list(provs).index(x) if x in provs else 99)
        chk = dbc_idx.get((db, tb))
        lamp = (chk or {}).get("燈") or ("NONE" if db not in ("parquet", "vake") else "NONE")
        cols = []
        for key, h in hdr_tables.items():
            if h.get("table") == tb or key == tb:
                cols = [c.get("name") for c in h.get("columns") or []][:40]
                break
        eps = [s for s in srcs if s.get("state")]
        worst = max((STATE_RANK.get(s["state"], 3) for s in eps), default=None)
        rows.append({
            "db": db, "table": tb, "label": cur.get("label") or t.get("role") or tb, "role": t.get("role"), "note": t.get("note"),
            "groups": gids, "group_zh": [gmeta[x].get("zh") for x in gids if x in gmeta], "category": (g or {}).get("category") or ("OTHER_SYSTEM" if other else ("DERIVED" if providers == ["DERIVED"] else "")),
            "cadence": (g or {}).get("cadence"), "membership": (g or {}).get("membership"), "writers": writers,
            "engines": [{"id": k, "file": (eng.get(k) or {}).get("file"), "role": (eng.get(k) or {}).get("role"), "group": (eng.get(k) or {}).get("group"),
                         "selftest": launch_idx.get(k)} for k in engines],
            "sources": srcs, "providers": providers, "basis": basis, "other_system": other,
            "endpoint_worst": [k for k, v in STATE_RANK.items() if v == worst][0] if worst is not None else None,
            "check": {"lamp": lamp, "state": (chk or {}).get("狀態"), "rows": (chk or {}).get("列數"), "min": (chk or {}).get("最少"),
                      "last_rows": (chk or {}).get("上次列數"), "latest": (chk or {}).get("最新日"), "lag": (chk or {}).get("落後天")} if chk else {"lamp": "NONE"},
            "rows_seen": t.get("rows_seen"), "date_hi": t.get("date_hi"), "columns": cols,
        })
    order = ui.get("db_order") or []
    rows.sort(key=lambda r: (order.index(r["db"]) if r["db"] in order else 50, r["other_system"], r["providers"] == ["DERIVED"],
                             gorder.get(r["groups"][0], 90) if r["groups"] else 99, r["table"]))       # 族群冊的順序(量價 → 籌碼 → 月營收 …)
    secs = []
    for r in rows:
        key = ("他系統表(只攤開不代修)", "other") if r["other_system"] else (r["db"], "own")
        if not secs or secs[-1]["key"] != key:
            secs.append({"key": key, "db": r["db"], "own": key[1] == "own", "label": (ui.get("db_labels") or {}).get(r["db"], "") if key[1] == "own" else "VRN(未分辨)/ VRN-2 寫進 VDF 庫的表", "rows": []})
        secs[-1]["rows"].append(r)
    merged = []
    for s in secs:                              # 他系統表各庫零散 → 合成一段放最後
        if not s["own"] and merged and not merged[-1]["own"]:
            merged[-1]["rows"] += s["rows"]
        else:
            merged.append(s)
    merged.sort(key=lambda s: (not s["own"],))
    own = [r for r in rows if not r["other_system"]]
    cnt = {k: sum(1 for r in own if r["check"]["lamp"] == k) for k in ("GREEN", "YELLOW", "RED", "NONE")}
    eps = {}
    for r in own:
        for s in r["sources"]:
            if s.get("state") and s.get("path"):
                eps[(s["provider"], s["path"])] = s["state"]
    by_prov = {}
    for r in own:
        for p in r["providers"]:
            by_prov.setdefault(p, {"tables": 0, "endpoints": set()})["tables"] += 1
        for s in r["sources"]:
            if s.get("path"):
                by_prov.setdefault(s["provider"], {"tables": 0, "endpoints": set()})["endpoints"].add(s["path"])
    mgr = None
    vdf_dir = Path(books.get("_vdf_dir") or VDF)
    mh = [x for x in vdf_dir.glob("VDF_SystemManager_v*.py") if _vnum(x) >= 0]
    if mh:
        mgr = str(max(mh, key=_vnum))
    return {
        "export": {"manager": mgr, "python": "python", "formats": ["csv", "parquet", "json", "xlsx", "md"], "home": (dbc or {}).get("home") or None,
                   "dests": [["onedrive", "OneDrive 雲端硬碟"], ["gdrive", "Google 雲端硬碟"], ["", "本機(VIA_Reports/vdf/export)"], ["custom", "自訂資料夾"]]},
        "tag": TAG, "ts": now or datetime.datetime.now().isoformat(timespec="seconds"),
        "books": {k: v[0] for k, v in books.items()}, "db_check": {"ts": (dbc or {}).get("ts"), "home": (dbc or {}).get("home"), "tag": (dbc or {}).get("tag")} if dbc else None,
        "providers": provs, "categories": {k: v.get("zh") for k, v in cats.items()},
        "counts": {"tables": len(own), "other_system": len(rows) - len(own), "dbs": len({r["db"] for r in own}), "groups": len(gmeta),
                   "engines": len(eng), **cnt, "endpoints": len(eps), "endpoints_verified": sum(1 for v in eps.values() if v == "VERIFIED")},
        "by_provider": {k: {"tables": v["tables"], "endpoints": sorted(v["endpoints"])[:12]} for k, v in by_prov.items()},
        "sections": [{"db": s["db"], "own": s["own"], "label": s["label"], "rows": s["rows"]} for s in merged],
    }


# ---------------------------------------------------------------- HTML
CSS_LAYOUT = r"""
:root{--bg:%(bg)s;--surface:%(card)s;--border:%(row_border)s;--border2:%(card_border)s;--panel:%(panel)s;--th:%(th_bg)s;--text:%(text)s;--muted:#5d6966;--dim:#8a938f;
--ok:%(GREEN)s;--warn:%(YELLOW)s;--fix:%(RED)s;--none:%(GRAY)s;--mono:ui-monospace,"SFMono-Regular","Cascadia Mono",Consolas,"Liberation Mono",monospace;--sans:%(font)s}
*,*::before,*::after{box-sizing:border-box}
body{font-family:var(--sans);background:var(--bg);color:var(--text);margin:0}
.wrap{max-width:1180px;margin:0 auto;padding:6px 4px 48px}
.hdr{display:flex;align-items:flex-end;gap:20px;border-bottom:1px solid var(--border2);padding-bottom:14px;margin-bottom:16px;flex-wrap:wrap}
.hdr-badge{font-family:var(--mono);font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--ok);border:1px solid color-mix(in srgb,var(--ok) 35%%,transparent);background:color-mix(in srgb,var(--ok) 7%%,transparent);padding:2px 7px;border-radius:4px;display:inline-block;margin-bottom:6px}
.hdr h1{margin:0}
.hdr-sub{font-size:10.5px;color:var(--muted);margin-top:4px;font-family:var(--mono);word-break:break-all}
.hdr-stats{margin-left:auto;display:flex;gap:16px;flex-wrap:wrap}
.stat{text-align:right}.stat-n{font-family:var(--mono);font-size:19px;font-weight:600;line-height:1}.stat-l{font-size:10.5px;color:var(--muted);margin-top:3px}
.bar{display:flex;gap:6px;flex-wrap:wrap;align-items:center;margin-bottom:8px}
.leg{display:flex;align-items:center;gap:6px;font-size:11.5px;color:var(--muted);cursor:pointer;padding:4px 9px 4px 7px;border-radius:5px;border:1px solid transparent;user-select:none}
.leg:hover{background:var(--panel);border-color:var(--border2)}.leg.active{border-color:var(--border2);background:var(--surface);color:var(--text);font-weight:600}
.leg-dot{width:8px;height:8px;border-radius:50%%;flex-shrink:0}.leg .n{font-family:var(--mono);font-size:10px;color:var(--dim)}
.search{margin-left:auto;min-width:220px;border:1px solid var(--border2);background:var(--surface);color:var(--text);padding:5px 9px}
.section{margin:0 0 18px}
.section-title{font-family:var(--mono);font-size:10.5px;letter-spacing:.06em;color:var(--muted);margin:0 0 6px 2px}
.section-title b{color:var(--text);font-family:var(--sans);font-weight:600;letter-spacing:0}
.matrix{display:grid;grid-template-columns:minmax(200px,1.2fr) minmax(150px,1fr) minmax(210px,1.35fr) 110px;border:1px solid var(--border2);border-radius:8px;overflow:hidden;background:var(--surface)}
.col-hdr{font-size:10.5px;letter-spacing:.025em;color:var(--muted);padding:8px 10px;background:var(--th);border-bottom:1px solid var(--border)}
.col-hdr:not(:nth-child(4n)){border-right:1px solid var(--border)}
.row{display:contents;cursor:pointer}
.row>.cell{padding:8px 10px;border-bottom:1px solid var(--border);min-width:0;transition:background .12s,opacity .12s}
.row:last-child>.cell{border-bottom:none}.row>.cell:not(:last-child){border-right:1px solid var(--border)}
.row:hover>.cell{background:var(--panel)}.row.sel>.cell{background:color-mix(in srgb,#2563eb 6%%,var(--surface))}
.row.dimmed>.cell{opacity:.28}.row.hidden{display:none}
.cell-label{font-size:12px;font-weight:600;line-height:1.35}
.cell-sub{font-family:var(--mono);font-size:10.5px;color:var(--muted);margin-top:2px;word-break:break-all}
.cell-db{font-family:var(--mono);font-size:10px;color:var(--dim);margin-top:3px}
.src-wrap{display:flex;flex-direction:column;align-items:flex-start;gap:4px}
.src-badge{display:inline-flex;align-items:center;gap:5px;font-family:var(--mono);font-size:10.5px;padding:3px 8px;border-radius:5px;border:1px solid;line-height:1.1;white-space:nowrap}
.src-fallback{font-size:10px;color:#92400e;font-family:var(--mono)}
.basis{font-size:10px;color:var(--dim);font-family:var(--mono)}
.endpoint{font-family:var(--mono);font-size:10.5px;color:var(--text);display:flex;gap:6px;align-items:center;min-width:0}
.endpoint+.endpoint{margin-top:4px}.endpoint .p{overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.endpoint:hover .p{white-space:normal;word-break:break-all}
.st{font-family:var(--mono);font-size:9px;padding:1px 5px;border-radius:3px;border:1px solid;flex-shrink:0}
.st-VERIFIED{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 40%%,transparent);background:color-mix(in srgb,var(--ok) 8%%,transparent)}
.st-TREE_EVIDENCE,.st-CANDIDATE{color:#b45309;border-color:color-mix(in srgb,var(--warn) 45%%,transparent);background:color-mix(in srgb,var(--warn) 10%%,transparent)}
.st-DEAD{color:var(--fix);border-color:color-mix(in srgb,var(--fix) 40%%,transparent);background:color-mix(in srgb,var(--fix) 8%%,transparent)}
.st-UNKNOWN{color:#6b7280;border-color:color-mix(in srgb,var(--none) 50%%,transparent);background:color-mix(in srgb,var(--none) 10%%,transparent)}
.status{display:inline-flex;align-items:center;gap:5px;font-size:11px;padding:2px 8px;border-radius:5px;border:1px solid;white-space:nowrap;font-weight:600}
.status-GREEN{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 40%%,transparent);background:color-mix(in srgb,var(--ok) 8%%,transparent)}
.status-YELLOW{color:#b45309;border-color:color-mix(in srgb,var(--warn) 45%%,transparent);background:color-mix(in srgb,var(--warn) 10%%,transparent)}
.status-RED{color:var(--fix);border-color:color-mix(in srgb,var(--fix) 40%%,transparent);background:color-mix(in srgb,var(--fix) 8%%,transparent)}
.status-NONE,.status-INFO{color:#6b7280;border-color:color-mix(in srgb,var(--none) 50%%,transparent);background:color-mix(in srgb,var(--none) 10%%,transparent)}
.dot{width:6px;height:6px;border-radius:50%%;display:inline-block;flex-shrink:0;background:currentColor}
.meta{font-family:var(--mono);font-size:10px;color:var(--dim);margin-top:4px;line-height:1.5}
.detail-panel{background:var(--surface);border:1px solid var(--border2);border-radius:8px;display:none;margin:0 0 16px}
.detail-panel.open{display:block}
.detail-hdr{padding:10px 14px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;gap:10px;background:var(--panel);border-radius:8px 8px 0 0}
.detail-hdr-title{font-size:13px;font-weight:600}
.detail-body{padding:12px 14px;display:grid;grid-template-columns:1fr 1fr;gap:12px}
.detail-kv{display:flex;flex-direction:column;gap:3px;min-width:0}.detail-kv.full{grid-column:1/-1}
.detail-k{font-size:10.5px;color:var(--muted);letter-spacing:.025em}
.detail-v{font-size:11.5px;font-family:var(--mono);word-break:break-word;white-space:pre-wrap;line-height:1.55}
.xp{grid-column:1/-1;border-top:1px dashed var(--border2);padding-top:10px;margin-top:2px}
.xp-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:8px;align-items:end}
.xp label{display:flex;flex-direction:column;gap:3px;font-size:10.5px;color:var(--muted)}
.xp input,.xp select{border:1px solid var(--border2);background:#fff;color:var(--text);padding:5px 7px;min-width:0}
.xp textarea{width:100%%;margin-top:8px;font-family:var(--mono);font-size:11px;border:1px solid var(--border2);background:var(--panel);color:var(--text);padding:7px;border-radius:5px;resize:vertical}
.xp .act{display:flex;gap:8px;align-items:center;margin-top:6px}.xp .act span{font-size:10.5px;color:var(--muted)}
.xp button{border:1px solid var(--border2);background:var(--text);color:#fff;cursor:pointer}
.summary{margin:20px 0 0;display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px}
.sum-card{background:var(--surface);border:1px solid var(--border2);border-radius:8px;padding:12px 14px;min-width:0}
.sum-n{font-size:16px;font-weight:700;line-height:1}.sum-l{font-size:11px;color:var(--muted);margin-top:6px;line-height:1.5;word-break:break-word}.sum-bar{height:3px;border-radius:2px;margin-top:10px;opacity:.55}
.foot{margin-top:18px;font-size:10.5px;color:var(--muted);line-height:1.7}
@media(max-width:640px){.xp-grid{grid-template-columns:1fr 1fr}.matrix{grid-template-columns:minmax(0,1fr)}.col-hdr{display:none}.row>.cell{border-right:none!important}
.row>.cell:last-child{border-bottom:2px solid var(--border2)}.summary{grid-template-columns:1fr 1fr}.detail-body{grid-template-columns:1fr}.search{margin-left:0;width:100%%;min-width:0}.hdr-stats{margin-left:0}}
"""


def visual_spec(via: Path | None = None) -> dict:
    """VDF 視覺規格冊尾版(= VRN-2 vrn2-professional-v0242 原文 + 鎖)。鎖對不上 → ok False(不套,照實標)。"""
    import hashlib
    p = tail(Path(via or VIA) / "functional modules" / "VDF", "VDF_UI_VisualSpec_SSOT_v*.json")
    d = _load(p) or {}
    css = d.get("css") or ""
    ok = bool(css) and hashlib.sha256(css.encode("utf-8")).hexdigest() == d.get("css_sha256")
    return {"book": p.name if p else None, "ok": ok, "css": css if ok else "", "style_id": d.get("style_id") or "vrn2-professional",
            "tokens": d.get("tokens") or {}, "lamps": d.get("lamps") or {}, "why": "" if ok else ("規格冊不在" if not p else "鎖對不上(css_sha256)")}


def css_for(spec: dict) -> str:
    t = dict({"bg": "#f8f7f2", "card": "#fffefb", "row_border": "#e1e4dc", "card_border": "#dedfd5", "panel": "#f1f3ec", "th_bg": "#eeeee7",
              "text": "#26312f", "font": 'Inter,"Segoe UI","Noto Sans CJK TC","Microsoft JhengHei",sans-serif'}, **(spec.get("tokens") or {}))
    lam = dict({"GREEN": "#16a34a", "YELLOW": "#f59e0b", "RED": "#dc2626", "GRAY": "#9ca3af"}, **{k: v for k, v in (spec.get("lamps") or {}).items() if k != "note"})
    return CSS_LAYOUT % dict(t, **lam)

JS = r"""
(function(){
var cur={p:'all',c:'all',q:''};
function apply(){var shown=0;document.querySelectorAll('.row').forEach(function(r){
 var pv=(r.getAttribute('data-providers')||'').split(' ');var ok=(cur.p==='all'||pv.indexOf(cur.p)>=0)&&(cur.c==='all'||r.getAttribute('data-cat')===cur.c);
 var q=cur.q;if(q){ok=ok&&(r.getAttribute('data-search')||'').indexOf(q)>=0;}
 r.classList.toggle('dimmed',!ok&&!q);r.classList.toggle('hidden',!ok&&!!q);if(ok)shown++;});
 var s=document.getElementById('shown');if(s)s.textContent=shown;}
document.querySelectorAll('.leg[data-p]').forEach(function(el){el.addEventListener('click',function(){
 document.querySelectorAll('.leg[data-p]').forEach(function(x){x.classList.remove('active')});el.classList.add('active');cur.p=el.getAttribute('data-p');apply();});});
document.querySelectorAll('.leg[data-c]').forEach(function(el){el.addEventListener('click',function(){
 document.querySelectorAll('.leg[data-c]').forEach(function(x){x.classList.remove('active')});el.classList.add('active');cur.c=el.getAttribute('data-c');apply();});});
var sq=document.getElementById('q');if(sq)sq.addEventListener('input',function(){cur.q=sq.value.trim().toLowerCase();apply();});
var panel=document.getElementById('detail');
function kv(k,v,full){var d=document.createElement('div');d.className='detail-kv'+(full?' full':'');var a=document.createElement('div');a.className='detail-k';a.textContent=k;
 var b=document.createElement('div');b.className='detail-v';b.textContent=(v===null||v===undefined||v==='')?'—':v;d.appendChild(a);d.appendChild(b);return d;}
function show(row){var d=JSON.parse(row.getAttribute('data-detail'));document.querySelectorAll('.row.sel').forEach(function(x){x.classList.remove('sel')});row.classList.add('sel');
 document.getElementById('detail-title').textContent=d.table+' — '+d.label;var body=document.getElementById('detail-body');body.innerHTML='';
 var src=(d.sources||[]).map(function(s){return s.provider+(s.role==='fallback'?'(備援)':'')+' · '+(s.base?s.base:'')+(s.path||'')+(s.state?' ['+s.state+']':'')+(s.label?' · '+s.label:'')+(s.evidence?'\n    '+s.evidence:'');}).join('\n');
 var eng=(d.engines||[]).map(function(e){return e.id+(e.file?' · '+e.file:'')+(e.group?' · '+e.group:'')+(e.selftest?' · 自測 '+e.selftest:'')+(e.role?'\n    '+e.role:'');}).join('\n');
 var c=d.check||{};var chk=c.lamp==='NONE'?'未量(沒有 db check 報告這一列)':(c.lamp+' · '+(c.state||'')+' · 列數 '+(c.rows==null?'—':c.rows)+'(最少 '+(c.min==null?'—':c.min)+' · 上次 '+(c.last_rows==null?'—':c.last_rows)+')· 最新日 '+(c.latest||'—')+' · 落後 '+(c.lag==null?'—':c.lag)+' 天');
 [['資料表',d.table],['資料庫',d.db],['族群',(d.groups||[]).map(function(g,i){return g+((d.group_zh||[])[i]?' '+d.group_zh[i]:'')}).join(' · ')],['大類 · 頻率 · 成員',[d.category,d.cadence,d.membership].filter(Boolean).join(' · ')],
  ['庫況',chk],['寫入者',(d.writers||[]).join(' · ')],['來源與端點(依據:'+d.basis+')',src,true],['引擎',eng,true],['欄位',(d.columns||[]).join(', '),true],['角色 · 備註',[d.role,d.note].filter(Boolean).join('\n'),true]]
  .forEach(function(x){body.appendChild(kv(x[0],x[1],x[2]));});
 body.appendChild(exportBlock(d));
 panel.classList.add('open');panel.scrollIntoView({behavior:'smooth',block:'nearest'});}
var XP={};try{XP=JSON.parse(document.getElementById('xp-conf').textContent)}catch(e){}
function q(v){return "'"+String(v).replace(/'/g,"''")+"'";}
function el(tag,attrs,text){var e=document.createElement(tag);for(var k in (attrs||{}))e.setAttribute(k,attrs[k]);if(text!==undefined)e.textContent=text;return e;}
function field(lab,node){var l=el('label');l.appendChild(document.createTextNode(lab));l.appendChild(node);return l;}
function exportBlock(d){var box=el('div',{'class':'xp'});box.appendChild(el('div',{'class':'detail-k'},'取出資料(範圍 → 格式 → 存放;組好指令貼到 PowerShell)'));
 if(!/\.duckdb$/.test(d.db||'')){box.appendChild(el('div',{'class':'detail-v'},'這一列不是 DuckDB 表('+d.db+')→ 用檔庫本身(parquet / VAKE)'));return box;}
 if(!XP.manager){box.appendChild(el('div',{'class':'detail-v'},'找不到 VDF_SystemManager(產頁時)'));return box;}
 var g=el('div',{'class':'xp-grid'});var f=el('input',{type:'date'}),t=el('input',{type:'date'}),c=el('input',{placeholder:'2330,2317(可空)'}),
  co=el('input',{placeholder:'欄位(可空 = 全部)'}),fm=el('select'),ds=el('select'),cu=el('input',{placeholder:'自訂資料夾(選「自訂」時)'});
 (XP.formats||['csv']).forEach(function(x){fm.appendChild(el('option',{value:x},x));});
 (XP.dests||[]).forEach(function(x){ds.appendChild(el('option',{value:x[0]},x[1]));});
 if((d.columns||[]).length)co.value='';co.setAttribute('list','');
 [['起日',f],['訖日',t],['代號',c],['欄位',co],['格式',fm],['存放',ds]].forEach(function(x){g.appendChild(field(x[0],x[1]));});
 box.appendChild(g);box.appendChild(field('自訂資料夾',cu));
 var ta=el('textarea',{rows:'3',readonly:'readonly'});box.appendChild(ta);
 var act=el('div',{'class':'act'}),btn=el('button',{type:'button'},'複製指令'),msg=el('span',{},'');act.appendChild(btn);act.appendChild(msg);box.appendChild(act);
 function upd(){var a=["$env:VIA_FROM_VCGC='YES';",XP.python||'python',q(XP.manager),'export','--table',q(d.table),'--db',q(d.db)];if(XP.home)a.push('--home',q(XP.home));
  if(f.value)a.push('--from',f.value);if(t.value)a.push('--to',t.value);if(c.value.trim())a.push('--codes',q(c.value.replace(/\s+/g,'')));
  if(co.value.trim())a.push('--cols',q(co.value.replace(/\s+/g,'')));a.push('--format',fm.value);
  var dv=ds.value==='custom'?cu.value.trim():ds.value;if(dv)a.push('--dest',q(dv));ta.value=a.join(' ');}
 [f,t,c,co,fm,ds,cu].forEach(function(x){x.addEventListener('input',upd);x.addEventListener('change',upd);});upd();
 btn.addEventListener('click',function(e){e.stopPropagation();ta.select();var ok=false;try{ok=document.execCommand('copy')}catch(err){}
  if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(ta.value).then(function(){msg.textContent='已複製';},function(){msg.textContent=ok?'已複製':'請手動複製(Ctrl+C)';});}
  else{msg.textContent=ok?'已複製':'請手動複製(Ctrl+C)';}});
 box.addEventListener('click',function(e){e.stopPropagation();});return box;}
document.querySelectorAll('.row').forEach(function(r){r.addEventListener('click',function(){show(r)});r.addEventListener('keydown',function(e){if(e.key==='Enter')show(r)});});
document.getElementById('detail-close').addEventListener('click',function(){panel.classList.remove('open')});
document.addEventListener('keydown',function(e){if(e.key==='Escape')panel.classList.remove('open')});
})();
"""


def _e(s) -> str:
    return html.escape("" if s is None else str(s), quote=True)


def _badge(prov: str, provs: dict, label: str | None = None) -> str:
    p = provs.get(prov) or {"short": prov, "color": "#9aa4b2"}
    c = p.get("color") or "#9aa4b2"
    return ('<span class="src-badge" style="color:%s;background:%s12;border-color:%s55"><span class="dot"></span>%s</span>'
            % (_e(c), _e(c), _e(c), _e(label or p.get("short") or prov)))


def render_html(m: dict, spec: dict | None = None) -> str:
    spec = spec if spec is not None else visual_spec()
    provs, c = m["providers"], m["counts"]
    own_rows = [r for s in m["sections"] if s["own"] for r in s["rows"]]
    pc = {p: sum(1 for r in own_rows if p in r["providers"]) for p in provs}
    cats = [("TW_MARKET", "台股"), ("FIN", "財報"), ("MACRO", "總經 · 情緒"), ("OTHER", "國際行情"), ("DERIVED", "衍生"), ("OTHER_SYSTEM", "他系統")]
    out = ['<!DOCTYPE html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">',
           '<title>VDF 擷取矩陣</title><style id="%s">%s</style><style id="vdf-fetchmatrix-layout">%s</style></head><body><div class="wrap">' % (
               _e(spec.get("style_id")), spec.get("css") or "", css_for(spec))]
    dbc = m.get("db_check") or {}
    sub = "%s · %s" % (m["tag"], m["ts"])
    vs = ("視覺規格 %s(= VRN-2 %s · 鎖驗過)" % (spec.get("book"), spec.get("style_id"))) if spec.get("ok") else ("視覺規格未套:%s" % spec.get("why"))
    out.append('<div class="hdr"><div><div class="hdr-badge">VDF · DATA FETCH MATRIX</div><h1>VDF 擷取矩陣</h1>'
               '<div class="hdr-sub">%s</div><div class="hdr-sub">庫況:%s</div><div class="hdr-sub">%s</div></div><div class="hdr-stats">' % (
                   _e(sub), _e(("db check %s · 家 %s" % (dbc.get("ts"), dbc.get("home"))) if dbc else "未量(沒有 DB_CHECK_latest.json;燈照實灰)"), _e(vs)))
    for n, lab, col in ((c["tables"], "資料表", "var(--text)"), (c["GREEN"], "到齊", "var(--ok)"), (c["YELLOW"], "待補", "#b45309"),
                        (c["RED"], "缺", "var(--fix)"), (c["NONE"], "未量", "var(--none)"),
                        ("%d/%d" % (c["endpoints_verified"], c["endpoints"]), "端點實測", "var(--muted)"), (c["engines"], "引擎", "var(--muted)")):
        out.append('<div class="stat"><div class="stat-n" style="color:%s">%s</div><div class="stat-l">%s</div></div>' % (col, _e(n), _e(lab)))
    out.append('</div></div>')
    out.append('<div class="bar"><div class="leg active" data-p="all"><span class="leg-dot" style="background:var(--text)"></span>全部來源 <span class="n">%d</span></div>' % len(own_rows))
    for p, meta in provs.items():
        if pc.get(p):
            out.append('<div class="leg" data-p="%s" title="%s"><span class="leg-dot" style="background:%s"></span>%s <span class="n">%d</span></div>' % (
                _e(p), _e(meta.get("zh")), _e(meta.get("color")), _e(meta.get("short") or p), pc[p]))
    out.append('<input class="search" id="q" placeholder="搜尋表名 / 中文名 / 引擎…" aria-label="搜尋"></div>')
    out.append('<div class="bar"><div class="leg active" data-c="all">全部大類</div>')
    for cid, zh in cats:
        n = sum(1 for s in m["sections"] for r in s["rows"] if r["category"] == cid)
        if n:
            out.append('<div class="leg" data-c="%s">%s <span class="n">%d</span></div>' % (_e(cid), _e(zh), n))
    out.append('<div class="leg" style="cursor:default">顯示 <span class="n" id="shown">%d</span></div></div>' % sum(len(s["rows"]) for s in m["sections"]))
    out.append('<script type="application/json" id="xp-conf">%s</script>' % json.dumps(m.get("export") or {}, ensure_ascii=False).replace("</", "<\\/"))
    out.append('<div class="detail-panel" id="detail"><div class="detail-hdr"><div class="detail-hdr-title" id="detail-title">—</div>'
               '<button class="detail-close" id="detail-close" type="button">關閉 ESC</button></div><div class="detail-body" id="detail-body"></div></div>')
    for i, s in enumerate(m["sections"], 1):
        title = ("DB-%d · %s" % (i, s["db"])) if s["own"] else "他系統 · 只攤開不代修(L123)"
        out.append('<div class="section"><div class="section-title">%s <b>%s · %d 表</b></div><div class="matrix">' % (_e(title), _e(s["label"]), len(s["rows"])))
        for h in ("資料 / Table", "來源 / Source", "端點 / Endpoint", "庫況"):
            out.append('<div class="col-hdr">%s</div>' % h)
        for r in s["rows"]:
            det = {k: r[k] for k in ("table", "label", "db", "groups", "group_zh", "category", "cadence", "membership", "writers", "engines", "sources",
                                     "basis", "check", "columns", "role", "note")}
            search = " ".join([r["table"], r["label"], r["db"], " ".join(r["groups"]), " ".join(e["id"] for e in r["engines"]), " ".join(r["writers"])]).lower()
            out.append('<div class="row" tabindex="0" data-providers="%s" data-cat="%s" data-search="%s" data-detail="%s">' % (
                _e(" ".join(r["providers"])), _e(r["category"]), _e(search), _e(json.dumps(det, ensure_ascii=False, default=str))))
            meta = " · ".join(x for x in [(" ".join(r["groups"]) or None), r.get("cadence")] if x)
            out.append('<div class="cell"><div class="cell-label">%s</div><div class="cell-sub">%s</div><div class="cell-db">%s</div></div>' % (
                _e(r["label"]), _e(r["table"]), _e(meta or (r.get("role") or "")[:28])))
            prim = [x for x in r["sources"] if x.get("role") != "fallback"]
            fb = [x for x in r["sources"] if x.get("role") == "fallback"]
            seen, badges = set(), []
            for x in prim:
                if x["provider"] not in seen:
                    seen.add(x["provider"])
                    badges.append(_badge(x["provider"], provs))
            cell = '<div class="src-wrap">%s</div>' % "".join(badges) if badges else '<div class="basis">未登來源</div>'
            for x in fb:
                cell += '<div class="src-fallback">▸ 備援:%s%s</div>' % (_e((provs.get(x["provider"]) or {}).get("short") or x["provider"]), _e(" · " + x["label"]) if x.get("label") else "")
            if "推定" in r["basis"] or "未登" in r["basis"]:
                cell += '<div class="basis">%s</div>' % _e(r["basis"])
            out.append('<div class="cell">%s</div>' % cell)
            eps = [x for x in r["sources"] if x.get("path")]
            ecell = "".join('<div class="endpoint"><span class="st st-%s">%s</span><span class="p" title="%s">%s</span></div>' % (
                _e(x["state"] or "UNKNOWN"), _e(x["state"] or "—"), _e((x.get("base") or "") + x["path"]), _e(x["path"])) for x in eps)
            if not eps:
                ecell = '<div class="endpoint"><span class="p">%s</span></div>' % _e(
                    "庫內計算 · 不出網" if r["providers"] == ["DERIVED"] else ("引擎 " + " · ".join(e["id"] for e in r["engines"][:4]) if r["engines"] else "—"))
            out.append('<div class="cell">%s</div>' % ecell)
            ck = r["check"]
            lab = LAMP_ZH.get(ck["lamp"], ck["lamp"])
            sm = ""
            if ck["lamp"] != "NONE" and ck.get("rows") is not None:
                sm = '<div class="meta">%s 列%s%s</div>' % (_e(ck["rows"]), _e(" · " + str(ck["latest"])) if ck.get("latest") else "",
                                                              _e(" · 落後 %s 天" % ck["lag"]) if ck.get("lag") not in (None, "", 0) else "")
            elif ck["lamp"] != "NONE":
                sm = '<div class="meta">%s</div>' % _e(str(ck.get("state") or "").split("·")[0].strip()[:24])
            out.append('<div class="cell"><span class="status status-%s"><span class="dot"></span>%s</span>%s</div>' % (_e(ck["lamp"]), _e(lab), sm))
            out.append('</div>')
        out.append('</div></div>')
    out.append('<div class="summary">')
    for p, meta in provs.items():
        b = m["by_provider"].get(p)
        if not b:
            continue
        out.append('<div class="sum-card"><div class="sum-n" style="color:%s">%s</div><div class="sum-l">%d 表%s</div><div class="sum-bar" style="background:%s"></div></div>' % (
            _e(meta.get("color")), _e(meta.get("short") or p), b["tables"], _e(" · " + " / ".join(b["endpoints"][:6])) if b["endpoints"] else "", _e(meta.get("color"))))
    out.append('</div><div class="foot">端點狀態照 VIA_VDF_TWMarketEndpoints_SSOT(VERIFIED 實測抓到 · TREE_EVIDENCE 樹上有產物 · CANDIDATE 依命名推出未測 · '
               'DEAD 證偽 · UNKNOWN 不知道不編)。庫況照 VDF db check(到齊 = 冊上最少列數以上且不落後 · 未量 = 這一輪沒有報告)。'
               '「推定」= 顯示冊沒登,依族群冊補料來源或擷取冊引擎分組推定。他系統表只攤開不代修。<br>冊:%s</div>' % _e(" · ".join(str(v) for v in m["books"].values() if v)))
    out.append('</div><script>%s</script></body></html>' % JS)
    return "".join(out)


BRIDGE_ID = "vdf-vrn2-bridge"


def bridge_css(spec: dict) -> str:
    """VDF 既有頁的 CSS 變數(via-theme · typekit)對到 VRN-2 規格色票;版面不動,只換色票 / 字型 / 字級基準。"""
    t = dict({"bg": "#f8f7f2", "card": "#fffefb", "card_border": "#dedfd5", "panel": "#f1f3ec", "th_bg": "#eeeee7", "row_border": "#e1e4dc",
              "text": "#26312f", "font": 'Inter,"Segoe UI","Noto Sans CJK TC","Microsoft JhengHei",sans-serif'}, **(spec.get("tokens") or {}))
    return (":root{--bg:%(bg)s;--panel:%(card)s;--line:%(card_border)s;--txt:%(text)s;--dim:#5d6966;--head:%(panel)s;--head-txt:%(text)s;--zebra:%(bg)s;"
            "--font:%(font)s;--via-font:%(font)s}"
            "body{background:%(bg)s!important;color:%(text)s!important}header{background:%(panel)s!important;color:%(text)s!important;border-bottom:1px solid %(card_border)s!important}"
            "aside{background:%(panel)s!important;border-right:1px solid %(card_border)s!important}.tabs button{border-radius:5px!important}"
            "th{background:%(th_bg)s!important}td{border-bottom-color:%(row_border)s!important}"
            "h1,h2,h3,.via-serif,.brand{font-family:%(font)s!important}" % t)         # VDF 舊設計稿的襯線標題 → VRN-2 同一字型


def apply_spec(page, spec: dict | None = None) -> str:
    """任一 VDF 頁套 VRN-2 視覺規格(鎖定原文 + 色票對照);冪等(換新不疊)。回 inserted / replaced / same / missing / lock-bad。"""
    spec = spec if spec is not None else visual_spec()
    page = Path(page)
    if not page.is_file():
        return "missing"
    if not spec.get("ok"):
        return "lock-bad"
    h = page.read_text(encoding="utf-8")
    sid = spec.get("style_id") or "vrn2-professional"
    base = re.sub(r'<style id="%s">.*?</style>' % re.escape(sid), "", h, flags=re.S)
    base = re.sub(r'<style id="%s">.*?</style>' % re.escape(BRIDGE_ID), "", base, flags=re.S)
    block = '<style id="%s">%s</style>' % (sid, spec["css"])
    if 'id="vdf-fetchmatrix-layout"' not in base:          # 矩陣頁自己就是規格色票,不必再對照
        block += '<style id="%s">%s</style>' % (BRIDGE_ID, bridge_css(spec))
    i = base.lower().rfind("</head>")
    new = (base[:i] + block + base[i:]) if i >= 0 else (block + base)
    if new == h:
        return "same"
    page.write_text(new, encoding="utf-8")
    return "replaced" if ('<style id="%s">' % sid) in h else "inserted"


def build(out: Path | None = None, db_check: Path | None = None, via: Path | None = None, launch: Path | None = None) -> dict:
    via = Path(via or VIA)
    out = Path(out or (via / "VIA_Reports" / "vdf"))
    rep = via / "VIA_Reports" / "vdf"
    dbc = _load(Path(db_check) if db_check else rep / "DB_CHECK_latest.json")
    lch = _load(Path(launch) if launch else rep / "RESULT_engine_launch_latest.json")
    m = build_model(load_books(via), dbc, lch)
    out.mkdir(parents=True, exist_ok=True)
    fh, fj = out / "FETCH_MATRIX_latest.html", out / "FETCH_MATRIX_latest.json"
    fh.write_text(render_html(m), encoding="utf-8")
    fj.write_text(json.dumps(m, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    c = m["counts"]
    return {"html": str(fh), "json": str(fj), "counts": c, "lamp": "RED" if c["RED"] else ("YELLOW" if c["YELLOW"] or c["NONE"] else "GREEN"),
            "line": "[擷取矩陣] 表 %d(他系統 %d)· 庫 %d · 族群 %d · 引擎 %d · 到齊 %d · 待補 %d · 缺 %d · 未量 %d · 端點實測 %d/%d · 頁 %s" % (
                c["tables"], c["other_system"], c["dbs"], c["groups"], c["engines"], c["GREEN"], c["YELLOW"], c["RED"], c["NONE"],
                c["endpoints_verified"], c["endpoints"], fh)}


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] == ["--selftest"]:
        return selftest()
    if not a or a[0] not in ("build",):
        print("用法:python %s build [--out 夾] [--db-check DB_CHECK.json] [--json] · --selftest" % Path(__file__).name)
        return 2

    def opt(k):
        return a[a.index(k) + 1] if k in a and a.index(k) + 1 < len(a) else None
    r = build(out=opt("--out"), db_check=opt("--db-check"))
    print(json.dumps(r, ensure_ascii=False, indent=1) if "--json" in a else r["line"])
    return 0


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond, note=""):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s%s" % (name, (" · " + str(note)[:300]) if note else ""))

    print("=== %s · 自測(冊 → 模型 → 頁;零網路)===" % TAG)
    books = load_books()
    chk("① 五本冊尾版都讀得到(顯示冊 %s · 族群冊 %s · 擷取冊 %s · 表冊 %s · 端點冊 %s)" % tuple(books[k][0] for k in ("ui", "groups", "fetch", "tables", "endpoints")),
        all(books[k][1] for k in ("ui", "groups", "fetch", "tables", "endpoints")))
    fake_dbc = {"ts": "2026-11-01T00:00:00", "home": "/x", "rows": [
        {"庫": "vdf_tw_market.duckdb", "表": "tw_daily_prices", "燈": "GREEN", "狀態": "OK", "列數": 2128169, "最少": 1, "最新日": "2026-10-31", "落後天": 0},
        {"庫": "vdf_tw_market.duckdb", "表": "tw_chip_margin", "燈": "RED", "狀態": "缺庫", "列數": None}]}
    m = build_model(books, fake_dbc, {"per": [{"eid": "ENG054", "selftest_lamp": "GREEN"}]})
    rows = [r for s in m["sections"] for r in s["rows"]]
    by = {(r["db"], r["table"]): r for r in rows}
    gb = books["groups"][1]
    want = {(s["db"], s["table"]) for g in gb["groups"] for s in g.get("sources") or [] if s.get("type") == "duckdb"}
    tb = {(t["db"], t["table"]) for t in books["tables"][1]["tables"]}
    chk("② 族群冊每張表(%d)與表冊每張表(%d)都在矩陣裡(共 %d 列 · 他系統 %d)" % (len(want), len(tb), len(rows), m["counts"]["other_system"]),
        want <= set(by) and tb <= set(by))
    tdp = by[("vdf_tw_market.duckdb", "tw_daily_prices")]
    t86 = by[("vdf_tw_market.duckdb", "tw_chip_inst")]
    chk("③ 端點狀態照端點冊:日行情 STOCK_DAY_ALL = VERIFIED · 三大法人 T86 = DEAD · 櫃買三大法人 UNKNOWN(不編路徑)· yfinance 標備援",
        any(s["path"] == "/exchangeReport/STOCK_DAY_ALL" and s["state"] == "VERIFIED" for s in tdp["sources"])
        and any(s["path"] == "/fund/T86" and s["state"] == "DEAD" for s in t86["sources"])
        and any(s["provider"] == "TPEX" and s["state"] == "UNKNOWN" for s in t86["sources"])
        and any(s["provider"] == "YFINANCE" and s["role"] == "fallback" for s in tdp["sources"]), [(s["provider"], s["path"], s["state"]) for s in t86["sources"]])
    chk("④ 庫況照 db check:日行情 GREEN 2128169 列 · 融資融券 RED 缺庫 · 報告沒有的表 = 未量(NONE,不冒充綠)",
        tdp["check"]["lamp"] == "GREEN" and tdp["check"]["rows"] == 2128169 and by[("vdf_tw_market.duckdb", "tw_chip_margin")]["check"]["lamp"] == "RED"
        and by[("vdf_global_market.duckdb", "global_daily")]["check"]["lamp"] == "NONE")
    chk("⑤ 引擎:族群冊引擎 + 表冊寫入者 → 擷取冊檔名與角色 · 自測燈(ENG054 GREEN)",
        any(e["id"] == "e054" and e["selftest"] == "GREEN" and "VDF_ENG054" in (e["file"] or "") for e in tdp["engines"]), tdp["engines"][:3])
    other = [r for r in rows if r["other_system"]]
    chk("⑥ 他系統表(vrn_ · via_policy_ · via_handover)另成最後一段 · 不算 VDF 的燈(%d 表)" % len(other),
        other and all(r["table"].startswith(("vrn_", "via_")) for r in other) and not m["sections"][-1]["own"] and all(s["own"] for s in m["sections"][:-1]))
    tw_idx = by.get(("VDF_TWIndex_Daily.duckdb", "tw_index_daily"))
    chk("⑦ 族群冊才有的表也收:VDF_TWIndex_Daily.tw_index_daily(TWSE MI_INDEX CANDIDATE)· parquet 國際財報 · VAKE 四組",
        tw_idx and any(s["state"] == "CANDIDATE" for s in tw_idx["sources"]) and ("parquet", "income_statement_quarterly") in by
        and sum(1 for k in by if k[0] == "vake") == 4)
    ui2 = dict(books["ui"][1], tables={k: v for k, v in books["ui"][1]["tables"].items() if k != "etf_stats_daily"})
    m2 = build_model(dict(books, ui=("x", ui2)))
    es = next(r for s in m2["sections"] for r in s["rows"] if r["table"] == "etf_stats_daily")
    chk("⑧ 顯示冊沒登 → 依族群冊 / 擷取冊引擎(含引擎自登的 tables)分組推定來源,頁上標「推定」(etf_stats_daily → %s · %s)" % (es["providers"], es["basis"]),
        "推定" in es["basis"] and "YFINANCE" in es["providers"] and any(e["id"].startswith("e055") for e in es["engines"]), es["basis"])
    evil = dict(books["ui"][1], tables=dict(books["ui"][1]["tables"], tw_daily_prices={"label": "<script>alert(1)</script>", "sources": []}))
    page = render_html(build_model(dict(books, ui=("x", evil)), fake_dbc))
    chk("⑨ 頁面跳脫:冊裡的 <script> 不會變成標籤 · 明細用 textContent 寫入",
        "<script>alert(1)</script>" not in page and "&lt;script&gt;alert(1)&lt;/script&gt;" in page and "textContent" in page)
    page = render_html(m)
    chk("⑩ 零 CDN:頁裡沒有外部 <link> / <script src> / @import / url(http)· 兩段 <style>(VRN-2 規格原文 + 矩陣版面)· 一段 <script> · 窄螢幕單欄",
        not re.search(r"<link|<script[^>]+src=|@import|url\(\s*['\"]?https?:", page, re.I) and page.count("<style") == 2 and page.count("<script>") == 1
        and "@media(max-width:640px)" in page)
    spec = visual_spec()
    bad = dict(spec, ok=False, css="", why="鎖對不上(css_sha256)")
    page_bad = render_html(m, bad)
    chk("⑬ 視覺規格 = VRN-2 vrn2-professional-v0242 鎖定原文(%s · 鎖驗過)· 頁裡原樣帶那段 css · 鎖對不上就不套並在頁首照寫" % spec["book"],
        spec["ok"] and ('<style id="vrn2-professional-v0242">' + spec["css"] + "</style>") in page and "#f8f7f2" in page
        and "視覺規格未套" in page_bad and spec["css"] not in page_bad)
    tmp = Path(tempfile.mkdtemp(prefix="vdf_fm236_"))
    try:
        dbf = tmp / "dbc.json"
        dbf.write_text(json.dumps(fake_dbc, ensure_ascii=False), encoding="utf-8")
        r = build(out=tmp / "out", db_check=dbf)
        j = json.loads(Path(r["json"]).read_text(encoding="utf-8"))
        chk("⑪ build 寫兩個檔(HTML · JSON)· 總結一行 %s" % r["line"][:90], Path(r["html"]).is_file() and j["counts"]["GREEN"] == 1 and j["counts"]["RED"] == 1
            and r["lamp"] == "RED")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    src = Path(__file__).read_text(encoding="utf-8")
    body = src.split("def selftest", 1)[0]
    chk("⑫ VDF 獨立:不匯入他系統程式 · 兩座橋在 · 零網路(不 import 抓取套件)· 同意閘不讀不寫 · 不碰 TA-Lib",
        not re.search(r"^\s*(import|from)\s+(CGC_|VRN_|VCGC|requests|httpx|urllib\.request)", src, re.M) and "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and "CONSENT" not in body and "talib" not in body.lower())
    conf = re.search(r'<script type="application/json" id="xp-conf">(.*?)</script>', page, re.S)
    xp = json.loads(conf.group(1).replace("<\\/", "</")) if conf else {}
    chk("⑮ 取出資料:明細區組 export 指令(期間 · 代號 · 欄位 · 格式 · OneDrive / Google 雲端 / 本機 / 自訂)· 指令走 VDF 管理員 %s · 值用 PowerShell 單引號跳脫"
        % Path(xp.get("manager") or "?").name, xp.get("manager") and "VDF_SystemManager_v" in xp["manager"] and {"onedrive", "gdrive"} <= {x[0] for x in xp.get("dests") or []}
        and "exportBlock" in page and "replace(/'/g,\"''\")" in page)
    chk("⑮b 匯出指令帶 db check 的資料庫家(--home %s):矩陣看到哪本庫,指令就取哪本(不另行猜家)" % xp.get("home"),
        xp.get("home") == fake_dbc["home"] and "a.push('--home',q(XP.home))" in page)
    tmp2 = Path(tempfile.mkdtemp(prefix="vdf_fm236s_"))
    try:
        pg = tmp2 / "X_latest.html"
        pg.write_text("<html><head><style id=\"via-theme\">:root{--bg:#fff}</style></head><body><header>x</header></body></html>", encoding="utf-8")
        h1, h2 = apply_spec(pg), apply_spec(pg)
        txt = pg.read_text(encoding="utf-8")
        chk("⑭ 任一 VDF 頁套 VRN-2 規格:鎖定原文 + 色票對照插在 </head> 前 · 再套一次不疊(%s → %s)· 鎖壞不套 · 頁不在照報" % (h1, h2),
            h1 == "inserted" and h2 == "same" and txt.count('<style id="vrn2-professional-v0242">') == 1 and txt.count(BRIDGE_ID) == 1
            and txt.index("vrn2-professional-v0242") > txt.index("via-theme") and apply_spec(pg, dict(spec, ok=False)) == "lock-bad"
            and apply_spec(tmp2 / "nope.html") == "missing")
    finally:
        shutil.rmtree(tmp2, ignore_errors=True)
    print("[計] %s 自測 %d/%d · %s" % (TAG, p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
