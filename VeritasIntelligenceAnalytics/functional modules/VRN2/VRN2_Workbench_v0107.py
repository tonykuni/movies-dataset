#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_Workbench v0107 — 動態前版薄尾(同夾前版一字不改):v0105 的 U/I 後處理全收 + Basic Info 合併檢視 + 欄位標註。

為什麼是自包含:v0105 沒帶加速器標記(第 3 行)→ 桌機 accelfix 自動複製出 v0106(= v0105 換殼)。
本版若再疊在 v0105 / v0106 上,頁面會被同一段後處理做兩次;所以本版找前版時**跳過含 "wb105-css" 的檔**
(v0105 與它的 accelfix 複本),改接再前一版的 render(桌機 = v0104 · 本倉 runtime = v0102),v0105 的功能本版自己做。
本版第 3 行帶 [VIA:ACCEL-BRIDGE:v0111] 標記 → accelfix 不會再複製出 v0108。

v0105 已有(照搬,行為不變):緊湊 / 白字 / 欄寬自動 CSS 蓋版 · 資料驗證紅黃綠燈(逐收據 · 只讀)· 共識資料面板(快照 ASOF 徽章)。
v0107 新增(操作員 2026-11-03「三項一起修」):
  · Basic Info · 合併檢視(F3):Basic Info 冊是「報告原文照抄」(NAME 23/52、ADJ_CLOSE 0/52 是原文就沒寫),Combined 冊已合併
    VDF 清單名稱與 Yahoo 還原收盤(51/52)。本卡逐份報告把兩冊對起來顯示:原文有值用原文(標「原」),原文空才用 Combined(標「合」,
    滑鼠提示寫來源,例 VDF 清單 / Yahoo 還原收盤 日期)。**只在 U/I 合併顯示,兩冊內容一字不改。**
  · 上漲空間小數欄(F2):Combined 新欄 UPSIDE_ADJ(純小數)U/I 乘 100 顯示 %;舊欄 UPSIDE_PCT(ADJ)(百分數)保留,沒新欄的舊輪次才退用並標「舊欄」。
    資料驗證燈多一列「上漲空間 新欄 × 舊欄」:同列兩欄互核(新欄 × 100 與舊欄差 ≤ 0.05)· 不一致 → 紅。
  · 輸出 Parquet(F1):資料驗證燈多一列「歷史對齊 Parquet」:HistoryAlign 收據 written[...].parquet 沒寫 → 黃(JSON / CSV 在)、型別版寫成 → 綠。
  · 欄位標註:讀 output/VRN2_Combined_columns_latest.json(ConsensusJoin v0107 寫),資料頁表頭 UPSIDE_PCT(ADJ) / UPSIDE_ADJ 滑過顯示單位與定義。
動詞同前版:render · logo · --selftest;render(root, out_path, logo, assets_zip) 介面不變。
"""
from __future__ import annotations

import csv
import html
import importlib.util
import json
import re
import sys
from pathlib import Path

VERSION = "v0107"
DISPLAY_NAME = "VRN2_Workbench"
HERE = Path(__file__).resolve().parent
_MYNUM = 107
_RE_VER = re.compile(r"VRN2_Workbench_v(\d{4})\.py$")
_SKIP_MARK = "wb105-css"            # v0105 與桌機 accelfix 的 v0106 複本:本版自己做它的後處理 → 不疊
UPSIDE_NEW, UPSIDE_OLD = "UPSIDE_ADJ", "UPSIDE_PCT(ADJ)"
BASIC_MAX_ROWS = 500


def _prior_path(folder: Path | None = None) -> Path:
    folder = Path(folder) if folder else HERE
    cands = []
    for p in folder.glob("VRN2_Workbench_v[0-9][0-9][0-9][0-9].py"):
        m = _RE_VER.search(p.name)
        if not m or int(m.group(1)) >= _MYNUM:
            continue
        try:
            if _SKIP_MARK in p.read_text(encoding="utf-8", errors="replace"):
                continue
        except OSError:
            continue
        cands.append((int(m.group(1)), p))
    if not cands:
        raise FileNotFoundError("同夾沒有版號 < v%04d 且不是 v0105 系的 VRN2_Workbench 前版(%s)" % (_MYNUM, folder))
    return sorted(cands)[-1][1]


def _load_prior():
    path = _prior_path()
    spec = importlib.util.spec_from_file_location("vrn2_workbench_prior_dyn107", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module, path.name


PRIOR, PRIOR_NAME = _load_prior()

_CSS = """
<style id="wb107-css">/* VRN2_Workbench v0107:緊湊 · 白字 · 欄寬自動(v0105 規則照搬)+ Basic 合併檢視(蓋版 · 前版規則不改) */
main{padding:10px 14px}
.box{padding:10px 12px;margin-bottom:8px}
.stats{gap:8px;margin-bottom:8px}
.stat{padding:8px 10px}
.stat b{font-size:clamp(12px,1vw + 7px,17px)}
h2{font-size:13px;margin:0 0 6px}
h3{margin:6px 0 4px}
.kv{gap:6px}.kv .cell{padding:6px 8px}
.cards{gap:8px}.split{gap:8px}
.sm-hdr{padding-bottom:8px;margin-bottom:8px;gap:12px}
.sm-state{padding:6px 10px;margin-bottom:8px}
.sm-card{padding:10px 12px}
.sm-row>.sm-c{padding:4px 10px}
.sm-row>.sm-c:first-child{padding-top:8px}
.sm-row>.sm-c:last-child{padding-bottom:8px}
.toolbar{padding:5px 0}
.pill{color:#fff;background:var(--am)}
.pill.good{color:#fff}.pill.bad{color:#fff}.pill.gray{color:#fff;background:var(--mut2)}
.sm-st{color:#fff;background:var(--c,var(--mut2));border-color:var(--c,var(--mut2))}
.sm-st .sm-dot{background:#fff}
.matrix table{table-layout:auto;width:auto;min-width:100%;border-collapse:collapse}
.matrix th,.matrix td{padding:3px 8px;white-space:nowrap}
.matrix th{position:sticky;top:0;background:var(--paper2);z-index:2}
td.lampcell{white-space:normal;min-width:120px;max-width:360px}
#wb107 .g{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:4px 14px;font-size:11.5px;line-height:1.45}
#wb107 .g>div{display:flex;gap:7px;align-items:baseline;min-width:0}
#wb107 .g b{flex:none;font-weight:700}
#wb107 .g .d{color:var(--ink2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
#wb107 .g>div:hover .d{white-space:normal;overflow-wrap:anywhere}
#wb107 .asof{display:inline-block;font:700 10px "DM Mono",monospace;letter-spacing:.5px;padding:2px 8px;border-radius:3px;background:var(--up);color:#fff;margin-left:8px}
#wb107 table,#wb107b table{border-collapse:collapse;font-size:11px;margin-top:4px}
#wb107 table th,#wb107b table th{background:var(--blue);color:#fff;padding:3px 8px;text-align:left;white-space:nowrap}
#wb107 table td,#wb107b table td{padding:3px 8px;border-bottom:1px solid var(--soft);white-space:nowrap}
#wb107b td.n{text-align:right;font-variant-numeric:tabular-nums}
#wb107b sup.src{font:700 9px "DM Mono",monospace;padding:0 3px;margin-left:3px;border-radius:2px;color:#fff;background:var(--mut2);cursor:help}
#wb107b sup.src.m{background:var(--blue)}#wb107b sup.src.o{background:var(--am)}
#wb107b .leg{font-size:11px;color:var(--mut);margin:2px 0 4px}
th.wb107-note{text-decoration:underline dotted;cursor:help}
</style>"""


def jread107(p: Path, default):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


_LAMP_OF = {"完成": "GREEN", "PASS": "GREEN", "OK": "GREEN", "GREEN": "GREEN", "YELLOW": "YELLOW", "RED": "RED", "GRAY": "GRAY",
            "REVIEW": "YELLOW", "REVIEW_OCR": "YELLOW", "FAIL": "RED", "BLOCKED": "RED", "DATA_GAP": "YELLOW"}


def _lamp(d: dict) -> str:
    if not isinstance(d, dict) or not d:
        return "GRAY"
    for k in ("lamp", "verdict", "state", "status"):
        v = str(d.get(k) or "").strip()
        if v:
            return _LAMP_OF.get(v, _LAMP_OF.get(v.split()[0], "YELLOW"))
    return "GRAY"


def _detail(d: dict, *keys) -> str:
    if not isinstance(d, dict):
        return "收據不在"
    for k in keys:
        v = d.get(k)
        if isinstance(v, str) and v.strip():
            return v
        if isinstance(v, dict) and v:
            return " · ".join("%s %s" % (a, b) for a, b in list(v.items())[:6])
    return str(d.get("verdict") or d.get("state") or "")


def _book(v2: Path, name: str) -> list | None:
    """output/VRN2_<name>_latest.json(優先)或 .csv;讀不了 → None。"""
    out = Path(v2) / "output"
    rows = jread107(out / ("VRN2_%s_latest.json" % name), None)
    if isinstance(rows, list):
        return [r for r in rows if isinstance(r, dict)]
    p = out / ("VRN2_%s_latest.csv" % name)
    if not p.is_file():
        return None
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as fh:
            return list(csv.DictReader(fh))
    except (OSError, csv.Error, UnicodeError):
        return None


def _s(v) -> str:
    return "" if v is None else str(v).strip()


def _combined_consensus(v2: Path) -> tuple:
    """(總列數, FACTSET 中位數欄有值列數, YFINANCE 中位數欄有值列數)。Combined 讀不了 → (None, 0, 0)。"""
    rows = _book(v2, "Combined")
    if rows is None:
        return None, 0, 0
    fs = sum(1 for r in rows if _s(r.get("FACTSET_TARGET_PRICE_MEDIAN")))
    yf = sum(1 for r in rows if _s(r.get("YFINANCE_TARGET_PRICE_MEDIAN")))
    return len(rows), fs, yf


def _fmt2(v):
    try:
        return "%.2f" % float(v)
    except (TypeError, ValueError):
        return "—"


def _num(v):
    try:
        x = float(str(v).replace(",", "").strip())
    except (TypeError, ValueError):
        return None
    return x if x == x else None


def _closeout_steps(v2: Path) -> dict:
    books = sorted(p for p in Path(v2).glob("VRN2_Closeout_v[0-9][0-9][0-9][0-9].json") if ".before_roundall" not in p.name)
    steps = (jread107(books[-1], {}) or {}).get("steps") if books else None
    out = {}
    for s in steps or []:
        key = str(s.get("step", "")).split(" ")[0]
        if key:
            out.setdefault(key, (str(s.get("lamp") or "GRAY"), str(s.get("detail") or "")))
    return out


def _status_map(text) -> dict:
    """Combined STATUS「KEY: 值 | KEY: 值」→ {KEY: 值}。"""
    out = {}
    for part in _s(text).split(" | "):
        k, sep, v = part.partition(": ")
        if sep and k.strip():
            out[k.strip()] = v.strip()
    return out


def upside_check(combined: list | None) -> tuple:
    """(燈, 說明):新欄 UPSIDE_ADJ(小數)× 舊欄 UPSIDE_PCT(ADJ)(百分數)同列互核。"""
    if combined is None:
        return "GRAY", "Combined 冊不在"
    if not combined:
        return "GRAY", "Combined 0 列"
    if UPSIDE_NEW not in combined[0]:
        return "GRAY", "Combined 還沒有 %s 欄(ConsensusJoin v0107 之前的輪次)· 舊欄 %s 照舊是百分數" % (UPSIDE_NEW, UPSIDE_OLD)
    n_new = n_old = both = bad = 0
    for r in combined:
        a, b = _num(r.get(UPSIDE_NEW)), _num(r.get(UPSIDE_OLD))
        n_new += a is not None
        n_old += b is not None
        if a is not None and b is not None:
            both += 1
            bad += abs(a * 100.0 - b) > 0.051
    note = "新欄(小數)%d · 舊欄(百分數)%d · 兩欄都有 %d 列互核不一致 %d" % (n_new, n_old, both, bad)
    if bad:
        return "RED", note
    return ("GREEN" if n_new == n_old else "YELLOW"), note + ("" if n_new == n_old else " · 兩欄有值列數不同")


def parquet_check(ha: dict) -> tuple:
    w = (ha or {}).get("written") if isinstance(ha, dict) else None
    if not isinstance(w, dict) or not w:
        return "GRAY", "歷史對齊收據沒有 written(這輪沒跑 ⑬b)"
    parts, lamp = [], "GREEN"
    for name in ("FinancialAligned", "Deleted"):
        x = w.get(name) or {}
        pq = _s(x.get("parquet"))
        rows = x.get("rows")
        if pq.startswith("(沒寫"):
            lamp = "YELLOW"
            parts.append("%s Parquet 沒寫(%s · JSON / CSV 在 · %s 列)" % (name, pq.strip("()")[:60], rows))
        elif pq:
            typed = x.get("parquet_typed")
            parts.append("%s Parquet 寫成 %s 列%s" % (name, rows, (" · 型別版(混型轉字串 %d 欄)" % len(typed.get("mixed_as_str") or [])) if isinstance(typed, dict) else ""))
    return lamp, " · ".join(parts) or "收據沒有 Parquet 欄"


def basic_merged(v2: Path) -> dict:
    """Basic Info(原文)× Combined(合併)逐份報告對起來;不改兩冊。回 {rows, n, name, adj, upside, ok}。"""
    basic = _book(v2, "BasicInfo")
    comb = _book(v2, "Combined")
    if basic is None:
        return {"ok": False, "why": "Basic Info 冊不在", "rows": [], "n": 0}
    cmap = {}
    for r in comb or []:
        cmap.setdefault(_s(r.get("FILENAME")), r)
    out = []
    cnt = {"name_basic": 0, "name_merged": 0, "adj_basic": 0, "adj_merged": 0, "upside": 0, "upside_old_only": 0}
    for b in basic:
        fn = _s(b.get("FILENAME"))
        c = cmap.get(fn) or {}
        st = _status_map(c.get("STATUS"))

        def pick(key, src_note):
            bv, cv = _s(b.get(key)), _s(c.get(key))
            if bv:
                return bv, "原", "報告原文(Basic Info 冊)"
            if cv:
                return cv, "合", "Combined 合併冊 · " + (src_note or "合併")
            return "", "", ""

        name = pick("NAME", st.get("NAME") or ("VDF 清單" if c else ""))
        adj = pick("ADJ_CLOSE", st.get("ADJ_CLOSE") or "Yahoo 還原收盤")
        cnt["name_basic"] += bool(_s(b.get("NAME")))
        cnt["name_merged"] += bool(name[0])
        cnt["adj_basic"] += bool(_s(b.get("ADJ_CLOSE")))
        cnt["adj_merged"] += bool(adj[0])
        a = _num(c.get(UPSIDE_NEW))
        if a is not None:
            up = ("%.1f%%" % (a * 100.0), "", "%s = %s(小數)× 100" % (UPSIDE_NEW, _s(c.get(UPSIDE_NEW))))
            cnt["upside"] += 1
        elif _num(c.get(UPSIDE_OLD)) is not None:
            up = ("%s%%" % _s(c.get(UPSIDE_OLD)), "舊", "舊欄 %s(百分數)· 這輪 Combined 沒有 %s" % (UPSIDE_OLD, UPSIDE_NEW))
            cnt["upside_old_only"] += 1
        else:
            up = ("", "", "")
        out.append({"REPORT_DATE": _s(b.get("REPORT_DATE")), "FILENAME": fn, "TICKER": _s(b.get("TICKER")), "NAME": name,
                    "BROKER": _s(b.get("BROKER")), "RATING": _s(b.get("RATING")) or _s(c.get("RATING")), "TARGET_PRICE": _s(b.get("TARGET_PRICE")),
                    "TARGET_PRICE(ADJ)": _s(c.get("TARGET_PRICE(ADJ)")), "ADJ_CLOSE": adj, "UPSIDE": up,
                    "FACTSET": _s(c.get("FACTSET_TARGET_PRICE_MEDIAN")), "YAHOO": _s(c.get("YFINANCE_TARGET_PRICE_MEDIAN")), "in_combined": bool(c)})
    return {"ok": True, "rows": out, "n": len(out), "combined_rows": None if comb is None else len(comb), **cnt}


def verification_rows(v2: Path) -> list:
    """逐收據的 (名稱, 燈, 一行說明) · 只讀,不重算(v0105 九列 + v0107 三列)。"""
    cons = jread107(v2 / "consensus" / "VRN2_Consensus_latest.json", {})
    steps = _closeout_steps(v2)
    vv = jread107(v2 / "VRN2_VerbatimVerify_latest.json", {})
    vv_counts = vv.get("counts") or {}
    total, fs_n, yf_n = _combined_consensus(v2)
    snap = cons.get("snapshot_reused") if isinstance(cons.get("snapshot_reused"), dict) else None
    cons_lamp = _lamp(cons)
    cons_note = ("快照補位 ASOF %s · %d 檔(閘未開 · 非本輪抓)" % (snap["asof"], snap.get("codes", 0))) if snap else \
        ("抓到 %d / 缺 %d" % (len(cons.get("codes_got") or []), len(cons.get("codes_missing") or [])) if cons.get("per_code") else str(cons.get("why") or "")[:160])
    comb_lamp = "GRAY" if total is None else ("GREEN" if total and fs_n == total and yf_n == total else ("YELLOW" if (fs_n or yf_n) else "RED"))
    market = jread107(v2 / "market" / "VRN2_Market_latest.json", {})
    ha = jread107(v2 / "VRN2_HistoryAlign_latest.json", {})
    fe_path = v2 / "VRN2_FailEvidence_latest.json"
    fe = jread107(fe_path, {})
    idem = jread107(v2 / "IDEMPOTENCE_latest.json", {})
    comp = jread107(v2 / "VRN2_Completion_latest.json", {})
    store = jread107(v2 / "VRN2_OutputStore_latest.json", {})
    bm = basic_merged(v2)
    if not bm["ok"]:
        bm_lamp, bm_note = "GRAY", bm["why"]
    else:
        n = bm["n"]
        bm_lamp = "GREEN" if n and bm["name_merged"] == n and bm["adj_merged"] == n else ("YELLOW" if n else "GRAY")
        bm_note = "NAME 原文 %d → 合併 %d / %d · ADJ_CLOSE 原文 %d → 合併 %d / %d(只在 U/I 合併顯示 · 冊不改)" % (
            bm["name_basic"], bm["name_merged"], n, bm["adj_basic"], bm["adj_merged"], n)
    up_lamp, up_note = upside_check(_book(v2, "Combined"))
    pq_lamp, pq_note = parquet_check(ha)
    return [
        ("原文值核對(VerbatimVerify)", _lamp(vv), " · ".join("%s %s" % (k, v) for k, v in list(vv_counts.items())[:5]) or _detail(vv, "why")),
        ("獨立驗證(IndependentVerifier)", _lamp(fe) if fe_path.is_file() else "GRAY", _detail(fe, "why", "counts")),
        ("冪等(同輸入同輸出)", _lamp(idem), _detail(idem, "why") or "見 IDEMPOTENCE_latest.json"),
        ("完成判定", _lamp(comp), _detail(comp, "why", "verdict")),
        ("市場資料 ⑥e(TWSE / TPEX / Yahoo)", _lamp(market) if "lamp" in market else steps.get("⑥e", ("GRAY", ""))[0],
         _detail(market, "why", "detail") or steps.get("⑥e", ("", "market/VRN2_Market_latest.json"))[1][:200]),
        ("共識 ⑥f(FactSet × Yahoo)", cons_lamp, cons_note),
        ("歷史對齊 ⑬b", _lamp(ha), _detail(ha, "why")),
        ("增量庫 ⑬(DuckDB / Parquet)", _lamp(store), _detail(store, "why", "totals")),
        ("Combined 共識欄", comb_lamp, ("%s 列 · FactSet 中位數 %s · Yahoo 中位數 %s%s" % (total, fs_n, yf_n, (" · 快照 ASOF " + snap["asof"]) if snap and fs_n else "")) if total is not None else "Combined 冊不在"),
        ("Basic Info · 合併檢視", bm_lamp, bm_note),
        ("上漲空間 新欄 × 舊欄", up_lamp, up_note),
        ("歷史對齊 Parquet", pq_lamp, pq_note),
    ]


def consensus_block(v2: Path) -> str:
    cons = jread107(v2 / "consensus" / "VRN2_Consensus_latest.json", {})
    per = cons.get("per_code") if isinstance(cons.get("per_code"), dict) else {}
    snap = cons.get("snapshot_reused") if isinstance(cons.get("snapshot_reused"), dict) else None
    e = html.escape
    head = "<h3>共識資料(FactSet × Yahoo 目標價中位數)%s</h3>" % (('<span class="asof">快照 ASOF %s</span>' % e(str(snap["asof"]))) if snap else "")
    meta = '<div class="d" style="font-size:11px;color:var(--mut)">%s</div>' % e(("引擎 %s · 網路工具 %s · " % (Path(str(cons.get("engine") or "—")).name, cons.get("net_tool") or "—")) +
                                                                                 (snap["why"] if snap else str(cons.get("why") or "這輪沒有共識收據")[:220]))
    if not per:
        return head + meta
    rows = []
    for code, c in sorted(per.items())[:40]:
        if not isinstance(c, dict):
            continue
        rows.append("<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>" % (
            e(str(code)), e(str(c.get("company_name") or "")[:16]), _fmt2(c.get("factset_target_median")), _fmt2(c.get("yf_target_median")),
            e(str(c.get("factset_analyst_count") or "—")), e(str(c.get("yf_analyst_count") or "—")), e(str(c.get("source_agreement_gate") or ""))))
    table = ('<div class="matrix" style="max-height:34vh;overflow:auto"><table><thead><tr><th>代號</th><th>名稱</th><th>FactSet 中位數</th><th>Yahoo 中位數</th>'
             "<th>FactSet 人數</th><th>Yahoo 人數</th><th>兩源閘</th></tr></thead><tbody>%s</tbody></table></div>" % "".join(rows))
    return head + meta + table


def _src(tag: str, tip: str) -> str:
    if not tag:
        return ""
    cls = {"原": "", "合": " m", "舊": " o"}.get(tag, "")
    return '<sup class="src%s" title="%s">%s</sup>' % (cls, html.escape(tip), html.escape(tag))


def basic_block_html(v2: Path) -> str:
    e = html.escape
    bm = basic_merged(v2)
    head = '\n<section class="box" id="wb107b"><h2>Basic Info · 合併檢視(原文 × Combined)<span class="pill good">Workbench v0107</span></h2>'
    if not bm["ok"]:
        return head + '<div class="leg">%s</div></section>\n' % e(bm["why"])
    n = bm["n"]
    leg = ('<div class="leg">%d 份 · NAME 原文 %d → 合併 %d · ADJ_CLOSE 原文 %d → 合併 %d · 上漲空間(還原)%d%s。'
           '<b>原</b> = 報告原文(Basic Info 冊)· <b>合</b> = Combined 合併冊補上(滑過看來源)· <b>舊</b> = 舊欄 %s(百分數)· 兩冊內容不改。</div>') % (
        n, bm["name_basic"], bm["name_merged"], bm["adj_basic"], bm["adj_merged"], bm["upside"],
        (" · 舊欄 %d" % bm["upside_old_only"]) if bm["upside_old_only"] else "", e(UPSIDE_OLD))
    body = []
    for r in bm["rows"][:BASIC_MAX_ROWS]:
        nm, adj, up = r["NAME"], r["ADJ_CLOSE"], r["UPSIDE"]
        body.append('<tr><td>%s</td><td title="%s">%s</td><td>%s%s</td><td>%s</td><td>%s</td><td class="n">%s</td><td class="n">%s</td>'
                    '<td class="n">%s%s</td><td class="n" title="%s">%s%s</td><td class="n">%s</td><td class="n">%s</td></tr>' % (
                        e(r["REPORT_DATE"]), e(r["FILENAME"]), e(r["TICKER"]), e(nm[0]), _src(nm[1], nm[2]), e(r["BROKER"]), e(r["RATING"]),
                        e(r["TARGET_PRICE"]), e(r["TARGET_PRICE(ADJ)"]), e(adj[0]), _src(adj[1], adj[2]), e(up[2]), e(up[0]), _src(up[1], up[2]),
                        e(r["FACTSET"]), e(r["YAHOO"])))
    more = ('<div class="leg">只顯示前 %d 份 · 全部見資料頁 Combined 冊</div>' % BASIC_MAX_ROWS) if n > BASIC_MAX_ROWS else ""
    table = ('<div class="matrix" style="max-height:46vh;overflow:auto"><table><thead><tr><th>報告日</th><th>代號</th><th>名稱</th><th>券商</th><th>評等</th>'
             '<th>目標價</th><th>目標價(還原)</th><th>還原收盤</th><th>上漲空間(還原)</th><th>FactSet 中位數</th><th>Yahoo 中位數</th></tr></thead>'
             '<tbody>%s</tbody></table></div>' % "".join(body))
    return head + leg + table + more + "</section>\n"


def column_notes(v2: Path) -> dict:
    """output/VRN2_Combined_columns_latest.json → {欄名: 一行說明};沒有檔就用本版內建兩欄(舊欄 / 新欄)。"""
    got = jread107(Path(v2) / "output" / "VRN2_Combined_columns_latest.json", {})
    cols = got.get("columns") if isinstance(got, dict) and isinstance(got.get("columns"), dict) else {}
    if not cols:
        cols = {UPSIDE_OLD: {"unit": "percent", "status": "舊欄保留", "definition": "上漲空間 × 100 · 小數 1 位(46.0 = 46%)"},
                UPSIDE_NEW: {"unit": "ratio", "status": "新欄", "definition": "TARGET_PRICE(ADJ) ÷ ADJ_CLOSE − 1 · 純小數(0.46 = 46%)"}}
    out = {}
    for k, v in cols.items():
        if isinstance(v, dict):
            out[str(k)] = "%s · 單位 %s · %s" % (v.get("status") or "", v.get("unit") or "—", v.get("definition") or "")
    return out


def _notes_js(notes: dict) -> str:
    data = json.dumps(notes, ensure_ascii=False).replace("</", "<\\/")
    return ('<script id="wb107-js">(function(){var N=%s;function f(){var t=document.querySelectorAll("th");for(var i=0;i<t.length;i++){var k=(t[i].textContent||"").trim();'
            'if(N[k]&&!t[i].title){t[i].title=N[k];t[i].className+=" wb107-note";}}}f();var h=document.getElementById("dsHead");'
            'if(h&&window.MutationObserver){new MutationObserver(f).observe(h,{childList:true,subtree:true});}})();</script>' % data)


def block_html(v2: Path) -> str:
    e = html.escape
    lamps = "".join('<div><span class="lamp %s"></span><b>%s</b><span class="d" title="%s">%s</span></div>'
                    % (lp, e(nm), e(str(dt)[:400]), e(str(dt)[:200])) for nm, lp, dt in verification_rows(v2))
    return ('\n<section class="box" id="wb107"><h2>資料驗證狀況(紅黃綠燈 · 逐收據)<span class="pill good">Workbench v0107</span></h2>'
            '<div class="g">%s</div>%s</section>\n' % (lamps, consensus_block(v2)))


_DATA_TAB = '<section class="tabsec" data-tab="data">'


def augment(page: str, v2: Path) -> str:
    """渲染後處理(純函式 · 可測):CSS 蓋版 + 驗證 / 共識區塊 + Basic 合併卡 + 欄位標註 + 版本註記。前版頁面其他內容一字不動。"""
    if 'id="wb107-css"' in page:                                               # 已做過(重入)→ 不重複
        return page
    if page.count("</head>") == 1:
        page = page.replace("</head>", _CSS + "\n</head>", 1)
    if page.count("</title>") >= 1:
        page = page.replace("</title>", "</title><!-- VRN2_Workbench %s over %s -->" % (VERSION, PRIOR_NAME.rsplit("_", 1)[-1][:-3]), 1)
    block = block_html(v2)
    basic = basic_block_html(v2)
    if page.count(_DATA_TAB) == 1:                                             # Basic 合併卡放資料頁最上面
        page = page.replace(_DATA_TAB, _DATA_TAB + basic, 1)
    else:                                                                      # 前版沒有資料頁 → 跟驗證區塊放一起
        block = block + basic
    if page.count("<main>") == 1:
        page = page.replace("<main>", "<main>" + block, 1)
    elif page.count("</body>") == 1:
        page = page.replace("</body>", block + "</body>", 1)
    js = _notes_js(column_notes(v2))
    if page.count("</body>") == 1:
        page = page.replace("</body>", js + "</body>", 1)
    return page


def _prior_render(root, out_path, logo, assets_zip):
    import inspect
    try:
        params = set(inspect.signature(PRIOR.render).parameters)
    except (TypeError, ValueError):
        params = {"root"}
    kwargs = {k: v for k, v in (("out_path", out_path), ("logo", logo), ("assets_zip", assets_zip)) if v is not None and k in params}
    return PRIOR.render(root, **kwargs)


def render(root: Path, out_path: Path | None = None, logo: str | None = None, assets_zip: Path | None = None) -> Path:
    root = Path(root).resolve()
    out = _prior_render(root, out_path, logo, assets_zip)
    v2 = root / "VIA_Reports" / "vrn2"
    page = Path(out).read_text(encoding="utf-8")
    try:
        page = augment(page, v2)
    except Exception as error:  # noqa: BLE001  後處理失敗不毀前版頁(頁照出 · 印原因)
        print("    [U/I] [YELLOW] Workbench v0107 後處理沒做成(前版頁照出):%s: %s" % (type(error).__name__, str(error)[:160]), flush=True)
        return Path(out)
    tmp = Path(out).with_suffix(".v0107.tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(Path(out))
    return Path(out)


# ── 自測(合成資料 · 不跑前版 render 的網路 / 磁碟以外動作)──────────────────────────────────────────────
def _fixture_v2(v2: Path, with_new_col: bool = True) -> None:
    for d in ("market", "consensus", "output"):
        (v2 / d).mkdir(parents=True, exist_ok=True)
    jw = lambda p, d: (v2 / p).write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")  # noqa: E731
    jw("VRN2_VerbatimVerify_latest.json", {"verdict": "REVIEW_OCR", "counts": {"PASS": 50, "REVIEW_OCR": 2}})
    jw("IDEMPOTENCE_latest.json", {"lamp": "GREEN", "why": "兩次雜湊一致"})
    jw("VRN2_Completion_latest.json", {"verdict": "完成"})
    jw("market/VRN2_Market_latest.json", {"lamp": "YELLOW", "why": "擷取 YELLOW · 失敗 0"})
    jw("VRN2_HistoryAlign_latest.json", {"lamp": "GRAY", "why": "無歷史 3", "written": {
        "FinancialAligned": {"json": "x.json", "csv": "x.csv", "rows": 30, "parquet": "(沒寫:ArrowInvalid)"},
        "Deleted": {"json": "d.json", "csv": "d.csv", "rows": 0, "parquet": "d.parquet"}}})
    jw("VRN2_OutputStore_latest.json", {"lamp": "GREEN", "totals": {"Combined": 3}})
    jw("consensus/VRN2_Consensus_latest.json", {"lamp": "YELLOW", "why": "快照補位", "engine": "ENG_x.py", "net_tool": "SUP_x · 閘 關",
                                                "snapshot_reused": {"asof": "2026-11-01", "codes": 2, "why": "同意閘未開 · 先用碟上 ASOF 2026-11-01 快照補位(2 檔)"},
                                                "per_code": {"1101": {"company_name": "合成公司0", "factset_target_median": 120.0, "yf_target_median": 110.0, "factset_analyst_count": 5, "yf_analyst_count": 7, "source_agreement_gate": "PASS"},
                                                             "2330": {"company_name": "合成公司1", "factset_target_median": 132.0, "yf_target_median": 123.2, "factset_analyst_count": 6, "yf_analyst_count": 8, "source_agreement_gate": "PASS"}}})
    jw("output/VRN2_BasicInfo_latest.json", [
        {"REPORT_DATE": "2026-10-01", "FILENAME": "A-1101.pdf", "TICKER": "1101", "NAME": "", "BROKER": "A", "RATING": "BUY", "TARGET_PRICE": "50", "ADJ_CLOSE": ""},
        {"REPORT_DATE": "2026-10-02", "FILENAME": "B-2330.pdf", "TICKER": "2330", "NAME": "合成公司1", "BROKER": "B", "RATING": "HOLD", "TARGET_PRICE": "1500", "ADJ_CLOSE": ""},
        {"REPORT_DATE": "2026-10-03", "FILENAME": "C-9999.pdf", "TICKER": "9999", "NAME": "", "BROKER": "C", "RATING": "", "TARGET_PRICE": "", "ADJ_CLOSE": ""}])
    comb = [
        {"FILENAME": "A-1101.pdf", "NAME": "合成公司0", "TARGET_PRICE(ADJ)": "49.00", "FACTSET_TARGET_PRICE_MEDIAN": "120.00", "YFINANCE_TARGET_PRICE_MEDIAN": "110.00",
         "UPSIDE_PCT(ADJ)": "46.0", "UPSIDE_ADJ": "0.460000000", "ADJ_CLOSE": "33.56", "STATUS": "NAME: VDF 清單 | ADJ_CLOSE: Yahoo 還原收盤 2026-10-31"},
        {"FILENAME": "B-2330.pdf", "NAME": "合成公司1", "TARGET_PRICE(ADJ)": "1470.00", "FACTSET_TARGET_PRICE_MEDIAN": "132.00", "YFINANCE_TARGET_PRICE_MEDIAN": "123.20",
         "UPSIDE_PCT(ADJ)": "45.5", "UPSIDE_ADJ": "0.454724409", "ADJ_CLOSE": "1010.50", "STATUS": "ADJ_CLOSE: Yahoo 還原收盤 2026-10-31"},
        {"FILENAME": "C-9999.pdf", "NAME": "", "TARGET_PRICE(ADJ)": "", "FACTSET_TARGET_PRICE_MEDIAN": "", "YFINANCE_TARGET_PRICE_MEDIAN": "",
         "UPSIDE_PCT(ADJ)": "", "UPSIDE_ADJ": "", "ADJ_CLOSE": "", "STATUS": ""}]
    if not with_new_col:
        for r in comb:
            r.pop("UPSIDE_ADJ")
    jw("output/VRN2_Combined_latest.json", comb)
    with (v2 / "output" / "VRN2_Combined_latest.csv").open("w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(comb[0]))
        w.writeheader()
        w.writerows(comb)
    if with_new_col:
        jw("output/VRN2_Combined_columns_latest.json", {"engine": "VRN2_ConsensusJoin v0107", "columns": {
            UPSIDE_OLD: {"unit": "percent", "status": "舊欄保留", "definition": "上漲空間 × 100"},
            UPSIDE_NEW: {"unit": "ratio", "status": "新欄(v0107)", "definition": "TARGET_PRICE(ADJ) ÷ ADJ_CLOSE − 1"}}})


def selftest() -> int:
    import tempfile
    fails = []

    def chk(label, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", label))
        if not cond:
            fails.append(label)

    pn = int(_RE_VER.search(PRIOR_NAME).group(1))
    prior_src = (HERE / PRIOR_NAME).read_text(encoding="utf-8", errors="replace")
    chk("① 動態前版:%s(版號 < 107 · 不是 v0105 系)· render / main 都在 · 本檔第 3 行帶加速器標記" % PRIOR_NAME,
        pn < _MYNUM and _SKIP_MARK not in prior_src and callable(getattr(PRIOR, "render", None)) and callable(getattr(PRIOR, "main", None))
        and Path(__file__).read_text(encoding="utf-8").splitlines()[2].strip() == "# [VIA:ACCEL-BRIDGE:v0111]")
    with tempfile.TemporaryDirectory() as td:
        fake = Path(td) / "mods"
        fake.mkdir()
        for nm, body in (("VRN2_Workbench_v0104.py", "# other line\n"), ("VRN2_Workbench_v0105.py", "x = 'wb105-css'\n"),
                         ("VRN2_Workbench_v0106.py", "# accelfix copy\nx = 'wb105-css'\n"), ("VRN2_Workbench_v0108.py", "# newer\n")):
            (fake / nm).write_text(body, encoding="utf-8")
        chosen = _prior_path(fake).name
        chk("② 前版選擇:跳過 v0105 / v0106(含 wb105-css)與 ≥ v0107 → 選 v0104", chosen == "VRN2_Workbench_v0104.py")
        v2 = Path(td) / "VIA_Reports" / "vrn2"
        _fixture_v2(v2)
        rows = verification_rows(v2)
        by = {n: (lp, dt) for n, lp, dt in rows}
        chk("③ 資料驗證燈 12 列(v0105 九列 + 三列新)· 冪等綠 · 市場黃 · 歷史灰", len(rows) == 12 and by["冪等(同輸入同輸出)"][0] == "GREEN"
            and by["市場資料 ⑥e(TWSE / TPEX / Yahoo)"][0] == "YELLOW" and by["歷史對齊 ⑬b"][0] == "GRAY")
        chk("④ Basic 合併:NAME 原文 1 → 合併 2 / 3 · ADJ_CLOSE 原文 0 → 合併 2 / 3 → 黃",
            by["Basic Info · 合併檢視"][0] == "YELLOW" and "NAME 原文 1 → 合併 2 / 3" in by["Basic Info · 合併檢視"][1] and "ADJ_CLOSE 原文 0 → 合併 2 / 3" in by["Basic Info · 合併檢視"][1])
        chk("⑤ 上漲空間互核:新欄 2 · 舊欄 2 · 不一致 0 → 綠", by["上漲空間 新欄 × 舊欄"][0] == "GREEN" and "不一致 0" in by["上漲空間 新欄 × 舊欄"][1])
        chk("⑥ Parquet 列:FinancialAligned 沒寫 → 黃(JSON / CSV 在)", by["歷史對齊 Parquet"][0] == "YELLOW" and "FinancialAligned Parquet 沒寫" in by["歷史對齊 Parquet"][1])
        bad = [dict(r) for r in json.loads((v2 / "output" / "VRN2_Combined_latest.json").read_text(encoding="utf-8"))]
        bad[0]["UPSIDE_ADJ"] = "46.0"                                           # 有人把百分數寫進小數欄
        chk("⑦ 新欄被寫成百分數 → 互核紅", upside_check(bad)[0] == "RED")
        page = ('<!DOCTYPE html>\n<html><head><title>VeritasReportNova · VRN Workbench</title><style>:root{}</style></head><body><main>'
                '<section class="tabsec" data-tab="overview"><div class="box"><h2>報告輸入</h2></div></section>'
                '<section class="tabsec" data-tab="data"><table><thead id="dsHead"><tr><th>UPSIDE_ADJ</th></tr></thead></table></section></main></body></html>')
        got = augment(page, v2)
        chk("⑧ CSS 注入一次 · 驗證區塊在 <main> 開頭 · 版本註記", got.count('id="wb107-css"') == 1 and got.count('id="wb107"') == 1
            and got.index('id="wb107"') < got.index("報告輸入") and "<!-- VRN2_Workbench v0107 over v%04d -->" % pn in got)
        bi = got.index('id="wb107b"')
        chk("⑨ Basic 合併卡在資料頁最上面 · 名稱「合成公司0」標「合」(VDF 清單)· 「合成公司1」標「原」· 還原收盤 33.56 標「合」(Yahoo)",
            got.index(_DATA_TAB) < bi < got.index('id="dsHead"') and 'title="Combined 合併冊 · VDF 清單">合</sup>' in got
            and "合成公司1<sup class=\"src\" title=\"報告原文(Basic Info 冊)\">原</sup>" in got and "33.56<sup class=\"src m\" title=\"Combined 合併冊 · Yahoo 還原收盤 2026-10-31\">合</sup>" in got)
        chk("⑩ 上漲空間由小數欄 × 100 顯示 46.0% / 45.5%(不顯示 0.46)· 舊欄標註 JS 在", ">46.0%<" in got and ">45.5%<" in got and 'id="wb107-js"' in got and "新欄(v0107)" in got)
        chk("⑪ 共識面板:ASOF 徽章 + 兩家中位數", 'class="asof">快照 ASOF 2026-11-01' in got and "123.20" in got)
        chk("⑫ 重入:再 augment 一次不重複插", augment(got, v2) == got)
        nodata = augment("<html><head><title>x</title></head><body><main><div>y</div></main></body></html>", v2)
        chk("⑬ 前版沒有資料頁 → Basic 卡跟驗證區塊放一起 · 不失敗", nodata.count('id="wb107b"') == 1 and nodata.index('id="wb107"') < nodata.index('id="wb107b"'))
        v2o = Path(td) / "old" / "VIA_Reports" / "vrn2"
        _fixture_v2(v2o, with_new_col=False)
        bmo = basic_merged(v2o)
        by_o = {n: (lp, dt) for n, lp, dt in verification_rows(v2o)}
        chk("⑭ 舊輪次(Combined 沒有 UPSIDE_ADJ)→ 退用舊欄並標「舊」· 互核灰(不冒充)",
            bmo["upside_old_only"] == 2 and bmo["rows"][0]["UPSIDE"][:2] == ("46.0%", "舊") and by_o["上漲空間 新欄 × 舊欄"][0] == "GRAY")
        (v2 / "output" / "VRN2_BasicInfo_latest.json").unlink()
        chk("⑮ 沒有 Basic Info 冊 → 合併卡寫實(冊不在)· 燈灰", "Basic Info 冊不在" in basic_block_html(v2)
            and {n: lp for n, lp, _ in verification_rows(v2)}["Basic Info · 合併檢視"] == "GRAY")
    n = 15
    print("[%s] %s %s 自測 %s(%d 項)" % ("GREEN" if not fails else "RED", DISPLAY_NAME, VERSION, "全過" if not fails else "不過:%s" % "; ".join(fails), n))
    return 0 if not fails else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    if argv and argv[0] == "logo":
        return PRIOR.main(argv)
    import argparse
    import os
    ap = argparse.ArgumentParser(prog="VRN2_Workbench_v0107")
    ap.add_argument("verb", nargs="?", default="render")
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--logo", default=None)
    a = ap.parse_args(argv)
    if a.verb != "render":
        return PRIOR.main(argv)
    root = Path(a.root) if a.root else (os.environ.get("VIA_ROOT") and Path(os.environ["VIA_ROOT"])) or HERE.parent.parent
    path = render(root, a.out, a.logo)
    print("[GREEN] %s %s(前版 %s)· %s" % (DISPLAY_NAME, VERSION, PRIOR_NAME.rsplit("_", 1)[-1][:-3], path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
