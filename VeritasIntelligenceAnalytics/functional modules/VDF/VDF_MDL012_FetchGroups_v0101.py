#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL012_FetchGroups v0101 — 薄尾:+ ui 動詞(族群操作頁:左面板功能 · 右面板多頁)

操作員 2026-10-04:「功能都在左邊面板,包含跳到其他系統跟回到母系統;顯示都用右邊面板多頁呈現。
  第一頁一定是輸入一欄、引擎狀況、運作、結果;左面板多一個 Live log;第二頁以後都是分類結果;
  最後一頁是 HTML U/I 及相關數據:編號 · 引擎編號 · SSOT · regex · 同義字 · 各輸入輸出的參數邏輯等全部彙整成多個矩陣,
  最上面是流程 workflow chart」。(VCGC-REQ040 U/I 面板設計的細化;L39 U/I 對接契約 · L100 零 server)
  ui [--home H] [--out F] [--as-of D] [--watch N] [--watch-max S]
    · 頁 = 引擎 → JSON 快照(SNAPSHOT 內嵌)→ 頁;頁不直讀庫、零 CDN、file:// 開、產生器不開瀏覽器。
    · 左面板:回母系統(VIA 中央 launcher · 總控)· 跳其他系統(VCGC · CGC / VDF / VRN / VAP 殼;不在 = ABSENT 照實)·
      功能(每個動詞一鈕,組出可貼上的指令;本頁不執行指令)· 頁籤 · Live log(擷取日誌尾段;擷取進行中頁每 15 秒自動重載)。
    · 右面板:① 輸入 · 引擎狀況 · 運作 · 結果 ② 起每族群一頁 ③ 末頁:流程圖(最上)+ 編號 / 引擎 / SSOT / regex / 同義字 / 輸入輸出參數邏輯 六個矩陣。
    · --watch N:每 N 秒重產一次(Live log 跟著更新),擷取停了 30 分鐘或到 --watch-max 秒就停。
其餘動詞(groups · members · add · remove · asof · run · monitor · query · optimize)全照 v0100。
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
    """統包唯一網路工具惰性載入;本頁產生器零網路,橋只為全樹一致。"""
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

import hashlib
import html
import importlib.util
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
PRIOR_PATH = HERE / "VDF_MDL012_FetchGroups_v0100.py"
_spec = importlib.util.spec_from_file_location("VDF_MDL012_FetchGroups_v0100_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

VIA = PRIOR.VIA
TAG = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
PRIOR.TAG = TAG
UI_DIR = VIA / "supportive modules" / "ui_support"
UI_PAGE = UI_DIR / "VIA_UI_VDF_FetchGroups_v0100.html"
NUMBER_DIR = VIA / "supportive modules" / "registry" / "VIA_NumberBooks"
REG = VIA / "supportive modules" / "registry"
LIVE_SEC = 120
NAV_PARENT = [("VIA 中央(母系統)", "VIA_HTML_UI/ui/VIA-Complete-System.html"),
              ("總控台 MasterControl", "supportive modules/ui_support/VIA_UI_MasterControl_v0100.html")]
NAV_SYSTEMS = [("VCGC 中央治理", "supportive modules/ui_support/VIA_UI_CentralGovernanceConsole_v0100.html"),
               ("CGC 殼", "supportive modules/ui_support/VIA_UI_Shell_CGC_v0100.html"),
               ("VDF 殼", "supportive modules/ui_support/VIA_UI_Shell_VDF_v0100.html"),
               ("VRN 殼", "supportive modules/ui_support/VIA_UI_Shell_VRN_v0100.html"),
               ("VAP 殼", "supportive modules/ui_support/VIA_UI_Shell_VAP_v0100.html"),
               ("VDF 資料架構", "supportive modules/ui_support/VIA_UI_VDFArchitecture_v0100.html")]
FUNCS = [("groups", "族群清單", "列族群 · 名單種類 · 引擎 · 有效成員數"),
         ("members", "成員", "列某族群的有效成員(固定全部 = 給總數)"),
         ("add", "增加成員", "可增減族群加成員(--apply 才寫)"),
         ("remove", "移出成員", "可增減族群移成員(軟移除 / 帳本,可找回)"),
         ("asof", "設定 as-of", "全族群共用同一天(latest 或 YYYY-MM-DD)"),
         ("run", "跑族群", "經 MDL008 跑勾選族群的引擎(live 要雙閘)"),
         ("monitor", "監控", "逐族群逐表:≤ as-of 筆數 · 最晚 · 落後 · 燈 → DuckDB fg_status"),
         ("query", "查詢", "DuckDB 族群視圖 g_<族群>__<表>(截到 as-of)"),
         ("optimize", "最佳化", "CHECKPOINT + ANALYZE · VAKE 小分片合併"),
         ("ui", "重產本頁", "重產本頁(--watch 15 = 擷取中自動更新)")]


# 前版全部公開名稱照轉接(TAILAPI:尾版不少名)
for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


# ---------- 蒐集 ----------
def _sha(p: Path) -> str:
    try:
        return hashlib.sha256(p.read_bytes()).hexdigest()[:12]
    except OSError:
        return ""


def _rel(target: Path, frm: Path) -> str:
    return Path(os.path.relpath(target, frm.parent)).as_posix()


def _tail_lines(p: Path, n: int) -> list:
    try:
        with p.open("rb") as fh:
            fh.seek(0, 2)
            size = fh.tell()
            fh.seek(max(0, size - 200_000))
            data = fh.read().decode("utf-8", "replace")
        return data.splitlines()[-n:]
    except OSError:
        return []


def engine_status(rows: list, home: Path) -> list:
    logs = home.parent / "_logs"
    out = []
    for r in rows:
        hits = sorted(logs.glob(f"{r['id']}_*.log"), key=lambda p: p.stat().st_mtime) if logs.is_dir() else []
        last = hits[-1] if hits else None
        rc, when, mode = None, None, None
        if last:
            when = datetime.fromtimestamp(last.stat().st_mtime).strftime("%Y-%m-%d %H:%M")
            mode = last.stem.split("_", 1)[-1]
            for ln in reversed(_tail_lines(last, 60)):
                m = re.search(r"\brc[=:]\s*(-?\d+)", ln)
                if m:
                    rc = int(m.group(1))
                    break
        state = "NODATA" if not last else ("RUNNING" if time.time() - last.stat().st_mtime < LIVE_SEC and rc is None
                                           else ("GREEN" if rc == 0 else ("YELLOW" if rc in (2, 4) else ("RED" if rc is not None else "NODATE"))))
        out.append({"id": r["id"], "file": r.get("file", ""), "group": r.get("group", ""), "role": (r.get("role") or "")[:80],
                    "run_args": " ".join(r.get("run_args") or []), "needs": ",".join(r.get("needs") or []),
                    "last": when, "mode": mode, "rc": rc, "state": state})
    return out


def live_log(home: Path, n: int = 160) -> dict:
    srcs = []
    vk = home / "vake" / "logs" / "vake_detail.log"
    if vk.is_file():
        srcs.append(vk)
    logs = home.parent / "_logs"
    if logs.is_dir():
        srcs += sorted(logs.glob("*.log"), key=lambda p: p.stat().st_mtime)[-3:]
    rep = home.parent / "_reports"
    lines, running, newest = [], False, 0.0
    for p in srcs:
        mt = p.stat().st_mtime
        newest = max(newest, mt)
        running = running or (time.time() - mt < LIVE_SEC)
        for ln in _tail_lines(p, n if p == vk else 40):
            lines.append(f"[{p.name}] {ln}")
    return {"lines": lines[-n * 2:], "running": running, "newest": datetime.fromtimestamp(newest).strftime("%Y-%m-%d %H:%M:%S") if newest else None,
            "sources": [str(p) for p in srcs], "reports": str(rep)}


def fg_runs(home: Path) -> list:
    p = home / PRIOR.CATALOG
    if not p.is_file():
        return []
    try:
        con = PRIOR._duck().connect()
        con.execute(f"ATTACH '{p.as_posix()}' AS c (READ_ONLY)")
        rows = con.execute("SELECT run_id, started, finished, as_of, mode, groups, rc_json FROM c.fg_runs ORDER BY started DESC LIMIT 20").fetchall()
        con.close()
        return [{"run_id": a, "started": str(b), "finished": str(c), "as_of": str(d), "mode": e, "groups": f, "rc": g} for a, b, c, d, e, f, g in rows]
    except Exception as exc:
        return [{"run_id": "-", "note": f"目錄庫讀不到:{type(exc).__name__}"}]


def vake_runs(home: Path) -> list:
    p = home / "vake" / "db" / "vake.duckdb"
    if not p.is_file():
        return []
    try:
        con = PRIOR._duck().connect()
        con.execute(f"ATTACH '{p.as_posix()}' AS v (READ_ONLY)")
        rows = con.execute("SELECT run_id, started, finished, tasks, ok, fail, rows_new FROM v.vake_runs ORDER BY started DESC LIMIT 10").fetchall()
        con.close()
        return [{"run_id": a, "started": str(b), "finished": str(c), "tasks": d, "ok": e, "fail": f, "rows_new": g} for a, b, c, d, e, f, g in rows]
    except Exception as exc:
        return [{"run_id": "-", "note": ("目錄庫被鎖(擷取進行中)" if PRIOR._busy(exc) else "讀不到") + f" · {type(exc).__name__}"}]


def numbering(files: list, codes: list) -> list:
    """編號冊(只增 jsonl;同鍵後列為準):模組 / 引擎依 source 檔對;工作流 / 步 / 需求依宣告碼對。"""
    want_src = {f.replace("\\", "/") for f in files}
    found = {}
    if not NUMBER_DIR.is_dir():
        return []
    for book in ("MDL", "ENG", "WKF", "STP", "REQ", "LGC"):
        p = NUMBER_DIR / f"VIA_NumberBook_{book}_v0100.jsonl"
        if not p.is_file():
            continue
        for ln in p.open(encoding="utf-8"):
            if not any(k in ln for k in codes) and not any(s in ln for s in want_src):
                continue
            try:
                r = json.loads(ln)
            except ValueError:
                continue
            src = str(r.get("source", "")).replace("\\", "/")
            hit = src in want_src or any(str(r.get(k, "")).startswith(c) for c in codes for k in ("declared", "name"))
            if hit:
                key = r.get("key") or r.get("code")
                found[key] = {"code": r.get("code"), "kind": r.get("kind"), "name": r.get("name"), "source": src,
                              "version": r.get("version"), "lamp": r.get("lamp"), "updated_at": r.get("updated_at")}
    return sorted(found.values(), key=lambda x: (x["kind"] or "", x["code"] or ""))


def ssot_matrix(paths: list) -> list:
    out = []
    for p in paths:
        p = Path(p)
        if not p.is_file():
            out.append({"book": p.name, "version": "", "state": "ABSENT", "path": str(p)})
            continue
        ver = re.search(r"_v(\d+)", p.stem)
        out.append({"book": p.name, "version": "v" + ver.group(1) if ver else "", "kb": round(p.stat().st_size / 1024, 1),
                    "sha12": _sha(p), "mtime": datetime.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M"),
                    "state": "PRESENT", "path": _rel(p, VIA / "x")})
    return out


def regex_matrix(book: dict) -> list:
    out = []
    for g in book["groups"]:
        for k in ("include", "exclude"):
            if g.get(k):
                out.append({"scope": f"族群 {g['id']}", "name": k, "pattern": g[k], "use": f"AkShare 選單組 {g.get('selection_group')} 切成員"})
    det = book.get("detect", {})
    out.append({"scope": "日期欄偵測", "name": "date_cols", "pattern": " | ".join(det.get("date_cols", [])), "use": "監控 / 視圖截到 as-of"})
    out.append({"scope": "代號欄偵測", "name": "key_cols", "pattern": " | ".join(det.get("key_cols", [])), "use": "可增減族群篩成員"})
    out.append({"scope": "NBS 寬表", "name": "_PERIOD", "pattern": PRIOR._PERIOD.pattern, "use": "期別在欄名時取最晚期"})
    iu = PRIOR.tail("VDF_InputUniverse_SSOT_v*.json")
    if iu:
        for x in PRIOR._json(iu).get("inputs", []):
            if x.get("regex"):
                out.append({"scope": f"輸入宇宙 {iu.name}", "name": f"{x.get('id')} {x.get('name', '')}", "pattern": x["regex"], "use": x.get("reader") or x.get("note") or ""})
    cr = PRIOR.tail("VIA_Central_Synonym_Regex_v*.json", REG)
    if cr:
        for k, v in PRIOR._json(cr).get("regex", {}).items():
            if re.search(r"TICKER|ETF|DATE|INDEX|CODE|YEAR|PERIOD", k):
                out.append({"scope": f"中央 {cr.name}", "name": k, "pattern": v.get("pattern", "") if isinstance(v, dict) else str(v),
                            "use": (v.get("note") or v.get("owner") or "") if isinstance(v, dict) else ""})
    return out


def synonym_matrix() -> list:
    cr = PRIOR.tail("VIA_Central_Synonym_Regex_v*.json", REG)
    if not cr:
        return []
    d = PRIOR._json(cr)
    out = []
    meta = d.get("synonyms_meta", {})
    for k, v in d.get("synonyms", {}).items():
        m = meta.get(k, {})
        if m.get("namespace") == "column_param" or re.search(r"DATE|TICKER|CODE|SYMBOL|PERIOD|INDEX", k):
            out.append({"key": k, "canonical": m.get("canonical", ""), "namespace": m.get("namespace", ""),
                        "aliases": " · ".join(map(str, v if isinstance(v, list) else [v])), "book": cr.name})
    return out


def io_matrix(book: dict, ledger: list, sel: dict, matrix: dict, as_of: str) -> list:
    tol = book.get("cadence_tolerance_days", {})
    out = []
    for g in book["groups"]:
        eff = PRIOR.effective_members(g, ledger, sel, matrix)
        outs = []
        for s in g.get("sources", []):
            outs.append("VAKE parquet(_vake_date)" if s["type"] == "vake" else
                        (f"{s.get('db')}::{s.get('table')}" if s["type"] == "duckdb" else f"parquet {s.get('glob')}"))
        asof_args = "; ".join(f"{k} {' '.join(v)}".replace("{as_of}", as_of) for k, v in (g.get("asof_args") or {}).items())
        out.append({"group": g["id"], "zh": g["zh"], "membership": g["membership"],
                    "input": eff["origin"] + ("" if eff["members"] is None else f" · {len(eff['members'])} 個"),
                    "filter": "include " + g["include"] if g.get("include") else ("exclude " + g["exclude"] if g.get("exclude") else ""),
                    "engines": ",".join(g.get("engines", [])), "asof_args": asof_args or "(視圖截齊)",
                    "output": " | ".join(outs), "date_key": " | ".join(f"{s.get('date_col') or '自動'} / {s.get('key_col') or '自動'}" for s in g.get("sources", []) if s["type"] != "vake") or "_vake_date / fn",
                    "cadence": f"{g.get('cadence')}(容忍 {tol.get(g.get('cadence'), 0)} 天或資料間隔 ×1.5)",
                    "fetch_follows": "是" if g.get("fetch_follows_members") else ("全部" if g["membership"] == "FIXED_ALL" else "否(只篩視圖 / 監控)")})
    return out


def gather(home: Path, as_of_arg: str | None = None) -> dict:
    book = PRIOR.load_book()
    fb_p = PRIOR.tail(PRIOR.FETCH_GLOB)
    fb = PRIOR._json(fb_p) if fb_p else {}
    ledger = PRIOR.read_ledger()
    sel, matrix, sel_p, mat_p = PRIOR.load_inputs(book)
    setting = PRIOR.current_asof_setting(book, ledger)
    as_of = PRIOR.resolve_asof(as_of_arg or setting)
    gids = [g["id"] for g in book["groups"]]
    rows = PRIOR.monitor(book, gids, as_of, home, ledger, sel, matrix)
    summ = PRIOR.group_summary(rows)
    plan = PRIOR.plan_rows(book, fb, gids, as_of, "<有效選單>")
    eng = engine_status([r for r in plan if not r.get("missing")], home)
    groups = []
    for g in book["groups"]:
        eff = PRIOR.effective_members(g, ledger, sel, matrix)
        mem = eff["members"]
        groups.append({"id": g["id"], "zh": g["zh"], "en": g["en"], "membership": g["membership"], "engines": g.get("engines", []),
                       "cadence": g.get("cadence"), "origin": eff["origin"], "n": None if mem is None else len(mem),
                       "members": (mem or [])[:400], "exclude": eff["exclude"], "fetch_follows": bool(g.get("fetch_follows_members")),
                       "summary": summ.get(g["id"], {}), "rows": [r for r in rows if r["group_id"] == g["id"]]})
    files = [str(Path(p).relative_to(VIA)).replace("\\", "/") for p in (PRIOR.tail("VDF_MDL012_FetchGroups_v*.py"), PRIOR.tail(PRIOR.MDL008_GLOB), PRIOR.tail(PRIOR.MDL011_GLOB)) if p]
    files += [str(p.relative_to(VIA)).replace("\\", "/") for p in HERE.glob("VDF_MDL012_FetchGroups_v*.py")]   # 整條版本鏈(尾版還沒發號時前版的號照列)
    files += ["functional modules/VDF/" + r["file"] for r in plan if r.get("file")]
    wf_p = PRIOR.tail("VIA_Workflow_VDF_SSOT_v*.json", REG)
    wf = next((w for w in PRIOR._json(wf_p).get("workflows", []) if w.get("alias") == "fetch_groups"), {}) if wf_p else {}
    books = [book["_path"], fb_p, sel_p, mat_p, PRIOR.tail("VDF_InputUniverse_SSOT_v*.json"), PRIOR.tail("VIA_Central_Synonym_Regex_v*.json", REG),
             wf_p, PRIOR.tail("VIA_Requirements_SSOT_v*.json", REG), PRIOR.LEDGER]
    return {"tool": TAG, "built": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "home": str(home), "as_of": as_of, "asof_setting": setting,
            "groups": groups, "engines": eng, "fg_runs": fg_runs(home), "vake_runs": vake_runs(home), "live": live_log(home),
            "workflow": wf, "numbering": numbering(files, ["VDF-WKF014", "VCGC-REQ150", "vdf_fetch_groups", "VCGC-REQ150:"]),
            "ssot": ssot_matrix([p for p in books if p]), "regex": regex_matrix(book), "synonyms": synonym_matrix(),
            "io": io_matrix(book, ledger, sel, matrix, as_of), "tail": Path(PRIOR.tail("VDF_MDL012_FetchGroups_v*.py") or __file__).name}


# ---------- 流程圖(行內 SVG;零 CDN) ----------
def workflow_svg(snap: dict) -> str:
    steps = [s.strip() for s in str((snap.get("workflow") or {}).get("plan", {}).get("order", "")).split("→") if s.strip()] or \
            ["冊", "groups / members", "add|remove --apply", "asof", "run --groups", "monitor", "optimize"]
    bw, bh, gap, x0, y0 = 150, 40, 26, 10, 12
    parts = []
    for i, s in enumerate(steps):
        x = x0 + i * (bw + gap)
        parts.append(f'<rect x="{x}" y="{y0}" width="{bw}" height="{bh}" rx="6" class="wf-box"/>'
                     f'<text x="{x + bw / 2}" y="{y0 + 25}" text-anchor="middle" class="wf-t">{html.escape(s[:22])}</text>')
        if i:
            parts.append(f'<line x1="{x - gap + 2}" y1="{y0 + bh / 2}" x2="{x - 4}" y2="{y0 + bh / 2}" class="wf-a" marker-end="url(#ah)"/>')
    lanes = snap["groups"]
    ly = y0 + bh + 34
    cols = [("族群(輸入名單)", 10), ("引擎", 250), ("輸出 庫 · 表", 470), ("監控燈(as-of " + snap["as_of"] + ")", 800)]
    for t, x in cols:
        parts.append(f'<text x="{x}" y="{ly - 10}" class="wf-h">{html.escape(t)}</text>')
    for i, g in enumerate(lanes):
        y = ly + i * 30
        st = (g.get("summary") or {}).get("worst", "NODATA")
        outs = sorted({(r.get("table_name") if r["source"] != "vake" else "VAKE parquet") for r in g["rows"]})[:3]
        lock = "🔒 " if g["membership"] == "FIXED_ALL" else ""
        parts.append(f'<rect x="10" y="{y}" width="220" height="24" rx="4" class="wf-box"/><text x="18" y="{y + 16}" class="wf-t2">{html.escape(lock + g["zh"])}</text>'
                     f'<line x1="232" y1="{y + 12}" x2="246" y2="{y + 12}" class="wf-a" marker-end="url(#ah)"/>'
                     f'<rect x="250" y="{y}" width="200" height="24" rx="4" class="wf-box"/><text x="258" y="{y + 16}" class="wf-t2">{html.escape(",".join(g["engines"])[:30])}</text>'
                     f'<line x1="452" y1="{y + 12}" x2="466" y2="{y + 12}" class="wf-a" marker-end="url(#ah)"/>'
                     f'<rect x="470" y="{y}" width="310" height="24" rx="4" class="wf-box"/><text x="478" y="{y + 16}" class="wf-t2">{html.escape(" · ".join(o or "-" for o in outs)[:48])}</text>'
                     f'<line x1="782" y1="{y + 12}" x2="796" y2="{y + 12}" class="wf-a" marker-end="url(#ah)"/>'
                     f'<rect x="800" y="{y}" width="110" height="24" rx="4" class="lamp-{st}"/><text x="855" y="{y + 16}" text-anchor="middle" class="wf-t2 wf-lamp">{st}</text>')
    w = max(x0 + len(steps) * (bw + gap), 920)
    h = ly + len(lanes) * 30 + 6
    return (f'<svg class="wf" viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="VDF-WKF014 流程">'
            '<defs><marker id="ah" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" class="wf-ah"/></marker></defs>'
            + "".join(parts) + "</svg>")


# ---------- 頁 ----------
_CSS = """
.fg{display:grid;grid-template-columns:260px minmax(0,1fr);gap:0;min-height:calc(100vh - 140px);font-size:12.5px;line-height:1.35}
.fg-left{border-right:1px solid var(--via-rule);padding:12px;display:flex;flex-direction:column;gap:4px;background:var(--via-card);min-width:0}
.fg-left h3{margin:8px 0 2px;font-size:11px;letter-spacing:1px;color:var(--via-muted);text-transform:uppercase}
.fg-left a,.fg-left button{display:block;width:100%;text-align:left;margin:2px 0;padding:5px 8px;border-radius:5px;border:1px solid var(--via-rule);
  background:transparent;color:var(--via-fg);font:inherit;cursor:pointer;text-decoration:none;padding:3px 8px;margin:1px 0}
.fg-left a:hover,.fg-left button:hover{border-color:#7FB2FF}
.fg-left button.on{background:rgba(127,178,255,.14);border-color:#7FB2FF}
.fg-left .absent{opacity:.5;cursor:not-allowed}
.fg-right{padding:12px 16px;overflow:auto;min-width:0}
.tabs{display:flex;flex-wrap:wrap;gap:4px;margin-bottom:10px}
.tabs button{padding:4px 9px;border:1px solid var(--via-rule);border-radius:5px;background:transparent;color:var(--via-fg);font:inherit;cursor:pointer}
.tabs button.on{background:rgba(127,178,255,.14);border-color:#7FB2FF}
.pg{display:none}.pg.on{display:block}
.card{background:var(--via-card);border:1px solid var(--via-rule);border-radius:8px;padding:10px 12px;margin:0 0 12px;min-width:0;overflow:auto}
.card h2{font-size:13px;margin:0 0 8px}
.grid2{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:12px}
table{border-collapse:collapse;width:100%}th,td{border-bottom:1px solid var(--via-rule);padding:3px 6px;text-align:left;vertical-align:top}
th{color:var(--via-muted);font-weight:500;position:sticky;top:0;background:var(--via-card)}
td.num{text-align:right;font-variant-numeric:tabular-nums}
td{word-break:break-word}td.nw{white-space:nowrap}
.lamp{display:inline-block;min-width:58px;text-align:center;border-radius:4px;padding:0 5px;font-size:11px}
.l-GREEN{background:rgba(63,185,132,.18);color:var(--via-ok)}.l-YELLOW{background:rgba(224,179,65,.18);color:var(--via-warn)}
.l-RED{background:rgba(224,108,96,.18);color:var(--via-bad)}.l-NODATA,.l-NODATE,.l-LOCKED,.l-RUNNING{background:rgba(140,153,166,.16);color:var(--via-muted)}
.l-RUNNING{color:#7FB2FF}
input,select,textarea{background:transparent;color:var(--via-fg);border:1px solid var(--via-rule);border-radius:5px;padding:4px 6px;font:inherit}
label{margin-right:10px;white-space:nowrap}
pre{white-space:pre-wrap;word-break:break-all;margin:0}
.cmd{font-family:ui-monospace,Menlo,Consolas,monospace;background:rgba(0,0,0,.25);border-radius:6px;padding:8px}
.log{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:10.5px;max-height:260px;overflow:auto;background:rgba(0,0,0,.25);border-radius:6px;padding:6px}
.mut{color:var(--via-muted)}
.scroll{max-height:420px;overflow:auto}
svg.wf .wf-box{fill:var(--via-card);stroke:#7FB2FF;stroke-width:1}svg.wf .wf-t{fill:var(--via-fg);font-size:12px}
svg.wf .wf-t2{fill:var(--via-fg);font-size:11px}svg.wf .wf-h{fill:var(--via-muted);font-size:11px}
svg.wf .wf-a{stroke:var(--via-muted);stroke-width:1.2}svg.wf .wf-ah{fill:var(--via-muted)}
svg.wf .lamp-GREEN{fill:rgba(63,185,132,.25)}svg.wf .lamp-YELLOW{fill:rgba(224,179,65,.25)}svg.wf .lamp-RED{fill:rgba(224,108,96,.25)}
svg.wf .lamp-NODATA,svg.wf .lamp-NODATE,svg.wf .lamp-LOCKED{fill:rgba(140,153,166,.2)}
@media (max-width:900px){.fg{grid-template-columns:1fr}.grid2{grid-template-columns:1fr}}
"""

_JS = r"""
const S = JSON.parse(document.getElementById('SNAPSHOT').textContent);
const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const esc = v => (v === null || v === undefined) ? '' : String(v).replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const lamp = s => `<span class="lamp l-${esc(s)}">${esc(s)}</span>`;
const KEY = 'via.vdf.fetchgroups.v0100';
let st = {}; try { st = JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (e) { st = {}; }
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(st)); } catch (e) {} };
function table(rows, cols, opt) {
  opt = opt || {};
  if (!rows || !rows.length) return '<div class="mut">(無資料)</div>';
  let h = '<table><tr>' + cols.map(c => `<th>${esc(c[1])}</th>`).join('') + '</tr>';
  for (const r of rows) h += '<tr>' + cols.map(c => {
    const v = r[c[0]];
    if (c[2] === 'lamp') return `<td>${lamp(v)}</td>`;
    if (c[2] === 'num') return `<td class="num">${v === null || v === undefined ? '' : Number(v).toLocaleString()}</td>`;
    return `<td${c[2] === 'nw' ? ' class="nw"' : ''}>${esc(v)}</td>`; }).join('') + '</tr>';
  return h + '</table>';
}
function show(id) {
  $$('.pg').forEach(p => p.classList.toggle('on', p.id === id));
  $$('[data-pg]').forEach(b => b.classList.toggle('on', b.dataset.pg === id));
  st.page = id; save();
}
const PY = 'functional modules/VDF/' + S.tail;
function cmdOf(verb) {
  const gs = $$('.gsel:checked').map(x => x.value).join(',');
  const asof = $('#asof').value || 'latest', mode = $('#mode').value, home = $('#home').value;
  const mg = $('#mgroup').value, mv = $('#mvals').value.trim();
  const H = home ? ` --home "${home}"` : '';
  const a = {groups:'groups' + H, members:`members ${mg}` + H, add:`add ${mg} ${mv} --apply`, remove:`remove ${mg} ${mv} --apply`,
    asof:`asof --set ${asof} --apply`, run:`run --groups ${gs || 'ALL'} --as-of ${asof} --mode ${mode}` + H,
    monitor:`monitor --groups ${gs || 'ALL'} --as-of ${asof}` + H, query:`query --groups ${gs || 'ALL'} --as-of ${asof}` + H,
    optimize:'optimize --apply' + H, ui:'ui --watch 15' + H}[verb];
  const bash = `VIA_FROM_VCGC=YES python3 "${PY}" ${a}`;
  const ps = `$env:VIA_FROM_VCGC='YES'; python ".\\${PY.replace(/\//g, '\\')}" ${a}`;
  const gate = (verb === 'run' && mode === 'live') ? "\n# live 先在本視窗開雙閘(操作員的手,頁與產生器永不代設):\n# bash: export VIA_NET_CONSENT=YES VIA_SCRAPE_CONSENT=YES\n# PS:   $env:VIA_NET_CONSENT='YES'; $env:VIA_SCRAPE_CONSENT='YES'" : '';
  return `# ${verb}\n${bash}\n${ps}${gate}`;
}
function setCmd(verb) {
  st.verb = verb; save();
  $('#cmd').textContent = cmdOf(verb);
  $$('[data-fn]').forEach(b => b.classList.toggle('on', b.dataset.fn === verb));
  show('pg-1');
}
function engines() {
  const gs = new Set($$('.gsel:checked').map(x => x.value));
  const want = new Set(); S.groups.forEach(g => { if (!gs.size || gs.has(g.id)) g.engines.forEach(e => want.add(e)); });
  $('#eng').innerHTML = table(S.engines.filter(e => want.has(e.id)), [['id','引擎','nw'],['file','檔'],['run_args','參數(含 as-of)'],['needs','相依'],['last','最後跑','nw'],['mode','模式','nw'],['rc','rc','num'],['state','燈','lamp']]);
}
function build() {
  $('#gsel').innerHTML = S.groups.map(g => `<label><input type="checkbox" class="gsel" value="${g.id}" ${(st.groups || []).includes(g.id) ? 'checked' : ''}>${g.membership === 'FIXED_ALL' ? '🔒' : ''}${esc(g.zh)}</label>`).join('');
  $('#mgroup').innerHTML = S.groups.filter(g => g.membership !== 'FIXED_ALL').map(g => `<option value="${g.id}">${esc(g.zh)}(${g.id})</option>`).join('');
  $('#asof').value = st.asof || S.as_of; $('#home').value = st.home || '';
  $$('.gsel,#asof,#mode,#home,#mgroup,#mvals').forEach(x => x.addEventListener('input', () => {
    st.groups = $$('.gsel:checked').map(x => x.value); st.asof = $('#asof').value; st.home = $('#home').value; save();
    engines(); if (st.verb) $('#cmd').textContent = cmdOf(st.verb); }));
  engines();
  $('#res').innerHTML = table(S.groups.map(g => Object.assign({id: g.id, zh: g.zh, membership: g.membership, n: g.n === null ? '全部' : g.n}, g.summary)),
    [['id','族群'],['zh','名稱'],['membership','名單'],['n','成員'],['sources','來源','num'],['rows_asof','≤as-of 筆數','num'],['max_date','最晚'],['worst','燈','lamp']]);
  $('#runs').innerHTML = '<div class="mut">族群執行(fg_runs)</div>' + table(S.fg_runs, [['run_id','run','nw'],['as_of','as-of','nw'],['mode','模式'],['groups','族群'],['rc','rc'],['started','開始'],['finished','結束']])
    + '<div class="mut" style="margin-top:8px">AkShare 執行(vake_runs)</div>' + table(S.vake_runs, [['run_id','run','nw'],['started','開始'],['finished','結束'],['tasks','任務','num'],['ok','成功','num'],['fail','失敗','num'],['rows_new','新增列','num'],['note','註']]);
  for (const g of S.groups) {
    const el = document.getElementById('pg-g-' + g.id);
    el.innerHTML = `<div class="card"><h2>${esc(g.zh)} · ${g.id} ${lamp((g.summary || {}).worst || 'NODATA')}</h2>
      <div class="mut">${esc(g.en)} · 名單 ${esc(g.membership)} · ${esc(g.origin)} · 引擎 ${esc(g.engines.join(','))} · 頻率 ${esc(g.cadence)} · 抓取跟著名單:${g.fetch_follows ? '是' : (g.membership === 'FIXED_ALL' ? '全部' : '否(只篩視圖 / 監控)')} · as-of ${esc(S.as_of)}</div></div>
      <div class="card"><h2>結果(逐表 / 逐函式,截到 as-of)</h2><div class="scroll">${table(g.rows, [['table_name','表 / 函式','nw'],['date_col','日期欄'],['key_col','代號欄'],['rows_asof','≤as-of','num'],['min_date','最早','nw'],['max_date','最晚','nw'],['lag_days','落後天','num'],['gap_days','更新間隔','num'],['members_missing','缺成員','num'],['state','燈','lamp'],['note','註']])}</div></div>
      <div class="card"><h2>成員(${g.n === null ? '全部 · 固定顯示全部' : g.n + ' 個'})</h2><div class="scroll mut">${g.n === null ? esc(g.origin) : esc(g.members.join(' · '))}${g.exclude && g.exclude.length ? '<br>排除:' + esc(g.exclude.join(' · ')) : ''}</div></div>`;
  }
  $('#m-num').innerHTML = table(S.numbering, [['code','編號','nw'],['kind','類','nw'],['name','名稱'],['source','來源'],['version','版','nw'],['lamp','燈','lamp'],['updated_at','時間','nw']]);
  $('#m-eng').innerHTML = table(S.engines, [['id','引擎 id','nw'],['file','檔'],['group','擷取冊分組','nw'],['role','角色'],['run_args','參數'],['needs','相依']]);
  $('#m-ssot').innerHTML = table(S.ssot, [['book','冊'],['version','版','nw'],['kb','KB','num'],['sha12','sha256[:12]','nw'],['mtime','時間','nw'],['state','狀態','nw'],['path','路徑']]);
  $('#m-rx').innerHTML = table(S.regex, [['scope','範圍'],['name','名'],['pattern','式'],['use','用途']]);
  $('#m-syn').innerHTML = table(S.synonyms, [['key','鍵'],['canonical','正典'],['namespace','命名空間'],['aliases','同義字'],['book','冊']]);
  $('#m-io').innerHTML = table(S.io, [['group','族群','nw'],['zh','名稱','nw'],['membership','名單','nw'],['input','輸入(名單來源)'],['filter','切分式'],['engines','引擎'],['asof_args','as-of 參數'],['output','輸出 庫::表'],['date_key','日期 / 代號欄'],['cadence','頻率 · 容忍'],['fetch_follows','抓取跟名單']]);
  $('#loglines').textContent = S.live.lines.join('\n') || '(沒有日誌)';
  const lg = $('#loglines'); lg.scrollTop = lg.scrollHeight;
  $('#livest').innerHTML = S.live.running ? lamp('RUNNING') + ' 擷取進行中 · 每 15 秒重載' : lamp('NODATE') + ' 閒置';
  $('#autoreload').checked = st.autoreload !== false;
  $('#autoreload').addEventListener('change', e => { st.autoreload = e.target.checked; save(); });
  $$('[data-pg]').forEach(b => b.addEventListener('click', () => show(b.dataset.pg)));
  $$('[data-fn]').forEach(b => b.addEventListener('click', () => setCmd(b.dataset.fn)));
  $('#copy').addEventListener('click', () => { navigator.clipboard && navigator.clipboard.writeText($('#cmd').textContent); });
  show(st.page && document.getElementById(st.page) ? st.page : 'pg-1');
  if (st.verb) setCmd(st.verb), show(st.page || 'pg-1');
  if (S.live.running && st.autoreload !== false) setTimeout(() => location.reload(), 15000);
  try { const bc = new BroadcastChannel('via-ui'); bc.postMessage({page: 'VIA_UI_VDF_FetchGroups', as_of: S.as_of, built: S.built}); } catch (e) {}
}
document.addEventListener('DOMContentLoaded', build);
"""


def _nav_links(out: Path) -> str:
    def link(label, rel):
        p = VIA / rel
        if p.is_file():
            return f'<a href="{html.escape(_rel(p, out))}">{html.escape(label)}</a>'
        return f'<a class="absent" title="ABSENT:{html.escape(rel)}">{html.escape(label)} · ABSENT</a>'
    return ("<h3>回母系統</h3>" + "".join(link(a, b) for a, b in NAV_PARENT)
            + "<h3>跳到其他系統</h3>" + "".join(link(a, b) for a, b in NAV_SYSTEMS))


def render(snap: dict, out: Path) -> str:
    groups = snap["groups"]
    worst = "GREEN"
    for g in groups:
        w = (g.get("summary") or {}).get("worst", "NODATA")
        if PRIOR.LAMP_ORDER.get(w, 5) > PRIOR.LAMP_ORDER.get(worst, 0):
            worst = w
    pages = [("pg-1", "① 輸入 · 引擎 · 運作 · 結果")] + [(f"pg-g-{g['id']}", g["zh"]) for g in groups] + [("pg-ref", "HTML U/I · 編號 · SSOT · 參數")]
    left = ('<aside class="fg-left">' + _nav_links(out)
            + "<h3>功能</h3>" + "".join(f'<button data-fn="{v}" title="{html.escape(d)}">{html.escape(z)}</button>' for v, z, d in FUNCS)
            + '<h3>Live log</h3><div id="livest" class="mut"></div><label class="mut"><input type="checkbox" id="autoreload"> 擷取中自動重載</label>'
            + '<pre id="loglines" class="log"></pre>'
            + f'<div class="mut">日誌 {html.escape(str(snap["live"].get("newest") or "—"))} · 頁 {html.escape(snap["built"])}</div>'
            + "<h3>頁</h3>" + "".join(f'<button data-pg="{pid}">{html.escape(t)}</button>' for pid, t in pages) + "</aside>")
    p1 = f"""<section class="pg" id="pg-1">
<div class="card"><h2>輸入</h2>
 <div>as-of(全族群同一天):<input id="asof" size="12"> <span class="mut">設定 {html.escape(snap['asof_setting'])} → {html.escape(snap['as_of'])}</span>
  模式 <select id="mode"><option>live</option><option>fixture</option><option>block</option></select>
  輸出根 <input id="home" size="40" placeholder="(預設 {html.escape(snap['home'])})"></div>
 <div style="margin-top:6px">族群(🔒 = 固定全部,不給增減):<div id="gsel"></div></div>
 <div style="margin-top:6px">成員增減:<select id="mgroup"></select> <input id="mvals" size="40" placeholder="代號或函式名,空白分隔"></div>
</div>
<div class="grid2">
 <div class="card"><h2>引擎狀況(勾選族群的引擎;as-of 參數已帶入)</h2><div id="eng" class="scroll"></div></div>
 <div class="card"><h2>運作(左面板按功能 → 這裡出可貼上的指令;本頁不執行)</h2><pre id="cmd" class="cmd">(按左面板「功能」)</pre>
  <button id="copy">複製</button><div id="runs" style="margin-top:8px" class="scroll"></div></div>
</div>
<div class="card"><h2>結果(各族群燈 · as-of {html.escape(snap['as_of'])})</h2><div id="res"></div></div>
</section>"""
    gp = "".join(f'<section class="pg" id="pg-g-{g["id"]}"></section>' for g in groups)
    ref = f"""<section class="pg" id="pg-ref">
<div class="card"><h2>流程 workflow chart · {html.escape(str((snap.get('workflow') or {}).get('code', 'VDF-WKF014')))} {html.escape(str((snap.get('workflow') or {}).get('name', '')))}</h2>{workflow_svg(snap)}</div>
<div class="card"><h2>① 編號矩陣(模組 · 引擎 · 工作流 · 步 · 需求 · 交接)</h2><div id="m-num" class="scroll"></div></div>
<div class="card"><h2>② 引擎矩陣(擷取冊列)</h2><div id="m-eng" class="scroll"></div></div>
<div class="card"><h2>③ SSOT 矩陣</h2><div id="m-ssot" class="scroll"></div></div>
<div class="card"><h2>④ regex 矩陣</h2><div id="m-rx" class="scroll"></div></div>
<div class="card"><h2>⑤ 同義字矩陣(欄位參數 · 日期 / 代號)</h2><div id="m-syn" class="scroll"></div></div>
<div class="card"><h2>⑥ 輸入輸出參數邏輯矩陣</h2><div id="m-io" class="scroll"></div></div>
</section>"""
    body = (f'<div class="fg">{left}<div class="fg-right"><div class="tabs">'
            + "".join(f'<button data-pg="{pid}">{html.escape(t)}</button>' for pid, t in pages)
            + f"</div>{p1}{gp}{ref}</div></div>"
            + '<script type="application/json" id="SNAPSHOT">' + json.dumps(snap, ensure_ascii=False, default=str).replace("</", "<\\/") + "</script>"
            + f"<script>{_JS}</script>")
    head_mod = None
    hp = UI_DIR / "SUP_MDL750_VeritasUIHead_v0102.py"
    hits = sorted(UI_DIR.glob("SUP_MDL750_VeritasUIHead_v*.py"), key=PRIOR._vnum)
    if hits:
        hp = hits[-1]
        try:
            sp = importlib.util.spec_from_file_location("veritas_ui_head_for_mdl012", hp)
            head_mod = importlib.util.module_from_spec(sp)
            sp.loader.exec_module(head_mod)
        except Exception:
            head_mod = None
    dot = {"GREEN": "ok", "YELLOW": "warn", "RED": "bad"}.get(worst, "")
    lamp_html = f'<span class="vh-dot {dot}"></span><span>{worst} · as-of {html.escape(snap["as_of"])}</span>'
    title = "VDF 擷取大族群 · 同一 as-of · DuckDB 監控"
    if head_mod:
        return head_mod.page(title, body, subsystem="VeritasDataForge", lamp=lamp_html, extra_css=_CSS,
                             foot_note=f"{TAG} · 產生器 ui · 引擎→JSON→頁(SNAPSHOT 內嵌)· 零 CDN · file://")
    return (f'<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><title>{html.escape(title)}</title>'
            f'<style>:root{{--via-rule:#ddd;--via-card:#fff;--via-fg:#111;--via-muted:#666;--via-ok:#15803d;--via-warn:#a16207;--via-bad:#b91c1c}}{_CSS}</style></head>'
            f'<body><header><b>VERITAS INTELLIGENCE ANALYTICS · VeritasDataForge</b> {lamp_html}</header>{body}</body></html>')


def build_page(home: Path, out: Path, as_of: str | None = None) -> dict:
    snap = gather(home, as_of)
    page = render(snap, out)
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp = out.with_suffix(".tmp")
    tmp.write_text(page, encoding="utf-8")
    os.replace(tmp, out)
    return snap


def cmd_ui(args) -> int:
    book, fb, ledger, sel, matrix, sel_p, mat_p, home = PRIOR._ctx(args)
    out = Path(args.out) if args.out else UI_PAGE
    t_end = time.time() + (args.watch_max or 4 * 3600)
    idle_since = None
    while True:
        t0 = time.time()
        snap = build_page(home, out, args.as_of)
        n = sum(len(g["rows"]) for g in snap["groups"])
        print(f"[ui] {out} · {round(out.stat().st_size / 1024, 1)} KB · 族群 {len(snap['groups'])} · 表/函式 {n} · as-of {snap['as_of']} · "
              f"Live log {'擷取中' if snap['live']['running'] else '閒置'} · {time.time() - t0:.1f}s(不開瀏覽器;via-open 才開)")
        if not args.watch:
            return 0
        idle_since = None if snap["live"]["running"] else (idle_since or time.time())
        if time.time() > t_end or (idle_since and time.time() - idle_since > 1800):
            print("[ui] watch 結束(擷取停了 30 分鐘或到上限)")
            return 0
        time.sleep(max(5, args.watch))


# ---------- 自測 ----------
def selftest() -> int:
    import shutil
    import tempfile
    res = []

    def chk(name, cond, note=""):
        res.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}" + (f" · {str(note)[:400]}" if note and not cond else ""))

    import contextlib
    import io
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        prior_rc = PRIOR.selftest()
    PRIOR.TAG = TAG
    chk("① v0100 自測照過(14 檢)", prior_rc == 0, buf.getvalue()[-300:])
    tmp = Path(tempfile.mkdtemp(prefix="mdl012ui_"))
    try:
        home = tmp / "home"
        (home / "output_hub" / "mega").mkdir(parents=True)
        (home.parent / "_logs").mkdir(parents=True)
        (home / "vake" / "logs").mkdir(parents=True)
        duck = PRIOR._duck()
        c = duck.connect(str(home / "output_hub" / "mega" / "vdf_global_market.duckdb"))
        c.execute("CREATE TABLE global_daily(date DATE, ticker VARCHAR, close DOUBLE)")
        c.execute("INSERT INTO global_daily VALUES ('2026-10-02','AAPL',1)")
        c.close()
        (home.parent / "_logs" / "e066_live.log").write_text("fetch ...\n[MDL008] e066 rc=0\n", encoding="utf-8")
        (home / "vake" / "logs" / "vake_detail.log").write_text("[INFO] run start\n[INFO] OK macro_x rows=3\n", encoding="utf-8")
        out = tmp / "ui" / "page.html"
        snap = build_page(home, out, "2026-10-02")
        page = out.read_text(encoding="utf-8")
        ids = re.findall(r'<section class="pg" id="([^"]+)"', page)
        chk("② 右面板多頁:第一頁 = 輸入 · 引擎 · 運作 · 結果;第二頁起每族群一頁;末頁 = HTML U/I 參照",
            ids[0] == "pg-1" and ids[-1] == "pg-ref" and len(ids) == len(snap["groups"]) + 2
            and all(k in page for k in ('id="asof"', 'id="eng"', 'id="cmd"', 'id="res"')), ids[:3])
        left = page[page.index('<aside class="fg-left">'):page.index("</aside>")]
        chk("③ 左面板:回母系統 · 跳其他系統(不在 = ABSENT)· 功能 10 鈕 · 頁籤 · Live log",
            "回母系統" in left and "跳到其他系統" in left and left.count("data-fn=") == len(FUNCS) and "Live log" in left
            and 'id="loglines"' in left and "VIA-Complete-System.html" in left, left[:300])
        ref = page[page.index('id="pg-ref"'):]
        chk("④ 末頁:流程圖在最上(SVG)· 六矩陣(編號 · 引擎 · SSOT · regex · 同義字 · 輸入輸出參數邏輯)",
            ref.index("<svg") < ref.index('id="m-num"') and all(f'id="m-{k}"' in ref for k in ("num", "eng", "ssot", "rx", "syn", "io")))
        chk("⑤ 零 CDN / 零 fetch:無外部 src / href、無 fetch( / XMLHttpRequest;SNAPSHOT 內嵌",
            not re.search(r'(src|href)="https?://', page) and "fetch(" not in page and "XMLHttpRequest" not in page
            and 'id="SNAPSHOT"' in page)
        s2 = json.loads(re.search(r'<script type="application/json" id="SNAPSHOT">(.*?)</script>', page, re.S).group(1).replace("<\\/", "</"))
        g = {x["id"]: x for x in s2["groups"]}
        e66 = next(e for e in s2["engines"] if e["id"] == "e066")
        chk("⑥ 快照:as-of 同一天 · 國際每日 1 列到齊 · e066 參數帶 --end as-of · 日誌 rc=0 → GREEN · Live log 有兩個來源",
            s2["as_of"] == "2026-10-02" and g["INTL_DAILY"]["rows"][0]["rows_asof"] == 1 and "--end 2026-10-02" in e66["run_args"]
            and e66["state"] == "GREEN" and len(s2["live"]["sources"]) == 2, (e66, s2["live"]["sources"]))
        chk("⑦ 參照矩陣有料:編號(含 MDL012)· SSOT ≥ 8 本 · regex 含族群切分式 · 輸入輸出 13 族群 · 流程取自 VDF-WKF014",
            any("MDL012" in str(n.get("name")) for n in s2["numbering"]) and len(s2["ssot"]) >= 8
            and any(r["name"] == "include" for r in s2["regex"]) and len(s2["io"]) == len(s2["groups"])
            and s2["workflow"].get("code") == "VDF-WKF014", (len(s2["numbering"]), len(s2["ssot"])))
        chk("⑧ 頁頭件 SUP_MDL750(Veritas 三行頭 + 令牌)· 產生器不開瀏覽器", "veritas-header" in page and "--via-rule" in page)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ok = sum(res)
    print(f"[計] {TAG} 本版 {ok}/{len(res)} · v0100 {'PASS' if prior_rc == 0 else 'FAIL'} · 合計 {'PASS' if ok == len(res) else 'FAIL'}")
    return 0 if ok == len(res) else 1


def main(argv=None) -> int:
    import argparse
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    if argv and argv[0] == "ui":
        ap = argparse.ArgumentParser(prog=f"{TAG} ui")
        ap.add_argument("--home"); ap.add_argument("--out"); ap.add_argument("--as-of")
        ap.add_argument("--watch", type=int, default=0); ap.add_argument("--watch-max", type=int, default=0)
        return cmd_ui(ap.parse_args(argv[1:]))
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
