#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VRN2_Workbench v0103 — v0102 薄尾(v0102 / v0101 / v0100 留著一字不改):右面板第一頁「00 系統現況」SUMMARY。

操作員 2026-11-01:
  「taiwan_stock_data_matrix.html 顯現部分資料擷取的端點來源 但並未顯示 DATAFRAME HEADERS · 這種呈現方式更詳細更整合更優化可讓人一目了然 ·
    放在右面版第一個頁面的系統現況 SUMMARY 供 VRN-2 / VDF / VCGC 參考 · 以目前 HTML U/I 為基礎 · 附件根據 LAYOUT 及字體階層大小視覺鎖定進行更新 ·
    原有功能設定不改 只是將此 U/I SUMMARY 及相對大小及視覺優點加入視覺鎖定更新」

做法(只增不減 · 範本視覺鎖的色盤 / 字型不換 · 只借附件的版面與字體階層):
  ① 右面板分頁最前面多一頁「00 系統現況」,開頁預設就是它;01 ~ 04 原樣(按鈕、區塊、資料、匯出都不動)。
  ② 版面照附件:徽章(DM Mono 10px · 大寫 · 字距 .14em)→ 標題(22px / 600)→ 等寬副標(12px)· 右上統計數字(DM Mono 20px)·
     來源圖例(可點 · 篩選列)· 每一區一個矩陣(區標 DM Mono 10px 大寫 · 欄頭 DM Mono 10px 大寫 · 列名 13px / 500 · 小字 DM Mono 10px)·
     點一列展開明細(ESC 關)· 最後四張摘要卡(數字 DM Mono 26px)。顏色用範本鎖定的變數(--blue · --vi · --am · --teal · --co · --down · --up · --mut2)。
  ③ 附件沒有的 **DataFrame 表頭**:每本輸出冊列出真實欄名(取自本輪 VRN2_<冊>_latest.json 的欄 · 跟 02 資料冊分頁同一份資料);
     矩陣格顯示前 10 欄、其餘「+N 欄」,明細列出全部欄(雙語名稱取 v0102 的表頭對照表)。
  ④ 三個矩陣:VRN-2 輸出冊(資料冊 · 來源 · 端點 · DataFrame 表頭 · 狀態)· VRN-2 本輪流程步驟(收據每一步的燈)·
     其他系統只讀互看(VDF · VCGC · VRN-1:只看對方自報的燈與已登記入口 · 不代修 · 找不到就灰燈寫原因 · 不猜路徑)。
  ⑤ 結案狀態取 RoundAll 的收尾頁收據 VRN2_CloseoutUI_latest.json(OPEN / BLOCKED / REVIEW / DATA_GAP / PASS · 照實寫 · REVIEW 不寫成成功)。
  ⑥ 匯出本頁(Markdown / JSON)在 00 頁時匯出矩陣列;PDF 照舊用列印。窄螢幕(< 760px)矩陣改成一列一卡。
動詞同 v0102:render [--root] [--out] [--logo] · logo <來源> <輸出> · --selftest
[VIA:AST-CLASS] 類別 = 前端渲染器(VRN-2 工作台 · 薄尾)· 入口 = ActivateVRN-2 收尾後 / RoundAll ⑤ 重渲染 / vrn2:// rerender / 本檔 CLI
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

VERSION = "v0103"
DISPLAY_NAME = "VRN2_Workbench"
PRIOR_NAME = "VRN2_Workbench_v0102.py"
HERE = Path(__file__).resolve().parent


def _load_prior():
    path = HERE / PRIOR_NAME
    if not path.is_file():
        raise FileNotFoundError("前版 %s 不在 %s" % (PRIOR_NAME, HERE))
    spec = importlib.util.spec_from_file_location("vrn2_workbench_prior_v0102", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


PRIOR = _load_prior()
for _name in dir(PRIOR):
    if not _name.startswith("__") and _name not in globals():
        globals()[_name] = getattr(PRIOR, _name)
esc = PRIOR.esc
jread = PRIOR.jread

# ===== 來源分類(圖例 / 篩選)· 顏色用範本鎖定的變數 =====
SOURCES = (("PDF", "PDF 擷取", "--co"), ("TWSE", "TWSE", "--blue"), ("TPEX", "TPEX", "--vi"), ("YAHOO", "Yahoo", "--am"),
           ("CONS", "共識 鉅亨 / FactSet", "--teal"), ("VRN2", "VRN-2 內部", "--ink2"), ("VDF", "VDF", "--down"), ("VCGC", "VCGC", "--mut"))
_SRC_VAR = {k: v for k, _, v in SOURCES}

# 每本輸出冊:(中文名, [(來源類, 徽章字)], [端點], 備註)。端點寫 VRN-2 實際走的路(交接 v0168 · 啟動器 v0166 · 不用 MOPS)。
BOOK_SPEC = {
    "BasicInfo": ("基本資料", [("PDF", "ENG397 首頁"), ("TWSE", "TWSE 日線"), ("TPEX", "TPEX 日線"), ("YAHOO", "Yahoo 還原價")],
                  ["首頁區塊 + pypdfium2 雙讀", "VRN2_MarketFetch_v0112 → VDF_TW_AllInOne_v039"], "正式英文 CSV 40 欄 · 最後一欄 SOURCE · 股價一律 Adj Close"),
    "FinancialData": ("年度財報數據", [("PDF", "ENG397 年度表"), ("PDF", "第二讀取器")],
                      ["年度財報頁表格 → 期間欄對齊", "pdfplumber / pypdfium2 回查 · 管理器 v0258 表格修補"], "主冊只收兩個讀取器對得上的值 · 一列一科目"),
    "Summary": ("一標題四重點", [("PDF", "ENG062 摘要器")], ["本文 → 一標題四重點 · 每點附原文證據"], "四點原文核對(VerbatimVerifier)"),
    "Combined": ("合併摘要", [("VRN2", "三冊合併"), ("CONS", "鉅亨 FactSet"), ("YAHOO", "Yahoo quoteSummary")],
                 ["ConsensusJoin v0105 · 經 VIA 網路工具 + 加速器", "TARGET_PRICE(ADJ) 同步還原 · TWSE / TPEX 格式合併"], "一代號一列 · 可回溯 FILES"),
    "Quarterly": ("季度數據", [("PDF", "ENG397 季度表")], ["季度表 → 季度冊"], "季度不進年度主冊"),
    "Rejected": ("剔除冊", [("VRN2", "驗證未過")], ["主冊未過的值 · 帶理由"], "不消失 · 二次回查過才回主冊"),
    "Restored": ("還原帳本", [("VRN2", "二次回查")], ["pdfplumber 數值相等 / 重算相符 → 回主冊"], "只增"),
    "FinancialAligned": ("歷史對齊", [("TWSE", "TWSE 年度實際"), ("TPEX", "TPEX 年度實際"), ("VDF", "VDF 引擎")],
                         ["HistoryAlign · 實際蓋過預估 · 加減 / 乘除檢驗"], "不用 MOPS(操作員 2026-10-31)"),
    "Deleted": ("刪除區", [("VRN2", "被歷史否定")], ["與歷史數據差 > 門檻 → 刪除區 · 帶理由"], "不刪原值"),
}
# 流程步驟 → 來源類(其餘算 VRN-2 內部)
STEP_SRC = (("⑥e", ["TWSE", "TPEX", "YAHOO", "VDF"]), ("⑥f", ["CONS", "YAHOO"]), ("⑬b", ["TWSE", "TPEX", "VDF"]), ("⑤b", ["VCGC"]), ("③", ["VCGC"]))
STATE_LAMP = {"PASS": "GREEN", "DATA_GAP": "GRAY", "REVIEW": "YELLOW", "BLOCKED": "YELLOW", "OPEN": "RED"}


def _hdr_map() -> dict:
    """v0102 的雙語表頭對照表(JS 物件 · 只讀它的字串 · 不另抄一份)。"""
    m = re.search(r"var HDR = \{(.*?)\};", getattr(PRIOR, "JS_V0102", "") or "", re.S)
    return dict(re.findall(r"([A-Z0-9_()]+):'([^']*)'", m.group(1))) if m else {}


HDR = _hdr_map()


def _cols(rows: list) -> list:
    cols = []
    for r in rows[:200]:
        for k in r:
            if k not in cols:
                cols.append(k)
    return cols


def _lamp(code: str) -> str:
    return '<span class="sm-st %s"><span class="sm-dot"></span>%s</span>' % (esc(code), esc(code))


def _badges(items) -> str:
    return "".join('<span class="sm-src" style="--c:var(%s)"><span class="sm-dot"></span>%s</span>' % (_SRC_VAR.get(k, "--mut"), esc(t)) for k, t in items)


def _closeout_state(v2: Path) -> dict:
    c = jread(v2 / "VRN2_CloseoutUI_latest.json", {}) or {}
    per = {}
    for it in c.get("items") or []:
        if isinstance(it, dict):
            per[str(it.get("owner", "?"))] = per.get(str(it.get("owner", "?")), 0) + 1
    return {"state": c.get("state") or "", "label": c.get("state_label") or "", "text": c.get("state_text") or "", "per": per, "at": c.get("generated") or c.get("ts") or ""}


def _freeze(root: Path) -> dict:
    locks = sorted((root / "docs" / "handoff" / "ai").glob("VRN2_FreezeLock_v[0-9][0-9][0-9][0-9].json")) if (root / "docs" / "handoff" / "ai").is_dir() else []
    return (dict(jread(locks[-1], {}) or {}, _name=locks[-1].name) if locks else {})


def others(root: Path, data: dict) -> list:
    """只讀互看:VCGC 交接快照自報的燈 · VDF 自報收據(固定位置才讀)· VRN-1 只看已登記入口。找不到 → 灰燈寫原因。"""
    gates = {g["label"].split(" ")[0]: g for g in PRIOR.gates(root, data)}
    rows = []
    hv = jread(root / "docs" / "handoff" / "HANDOFF_latest.json", {}) or {}
    if hv:
        lamp = str(hv.get("closeout_lamp") or hv.get("lamp") or "GRAY").upper()
        pend = (hv.get("summary") or {}).get("pending")
        rows.append({"sys": "VCGC", "entry": gates.get("VCGC", {}).get("tip", ""), "self": "交接閘 %s · 驗收 closeout_lamp %s · 待辦 %s · %s" % (hv.get("lamp", "—"), hv.get("closeout_lamp", "—"), pend if pend is not None else "—", hv.get("at", "")),
                     "lamp": lamp if lamp in ("GREEN", "YELLOW", "RED") else "GRAY", "path": "docs/handoff/HANDOFF_latest.json"})
    else:
        rows.append({"sys": "VCGC", "entry": gates.get("VCGC", {}).get("tip", ""), "self": "沒有交接快照 docs/handoff/HANDOFF_latest.json(不猜)", "lamp": "GRAY", "path": ""})
    vdf = None
    for cand in ("VIA_Reports/vdf/VDF_Closeout_latest.json", "VIA_Reports/vdf/VDF_Status_latest.json"):
        if (root / cand).is_file():
            vdf = (cand, jread(root / cand, {}) or {})
            break
    if vdf:
        lamp = str(vdf[1].get("lamp") or vdf[1].get("closeout_lamp") or "GRAY").upper()
        rows.append({"sys": "VDF", "entry": gates.get("VDF", {}).get("tip", ""), "self": "自報 %s · %s" % (lamp, str(vdf[1].get("detail") or vdf[1].get("state") or "")[:120]), "lamp": lamp if lamp in ("GREEN", "YELLOW", "RED") else "GRAY", "path": vdf[0]})
    else:
        rows.append({"sys": "VDF", "entry": gates.get("VDF", {}).get("tip", ""), "self": "固定位置沒有 VDF 自報收據(VIA_Reports/vdf/VDF_Closeout_latest.json)· 不猜 · VRN-2 只借 VDF 引擎的擷取方法", "lamp": "GRAY", "path": ""})
    rows.append({"sys": "VRN-1", "entry": gates.get("VRN-1", {}).get("tip", ""), "self": "另一團隊的倉 · 只讀 · 只看已登記入口", "lamp": "GRAY" if gates.get("VRN-1", {}).get("off", True) else "GREEN", "path": ""})
    return rows


def summary_model(root: Path, data: dict) -> dict:
    v2 = data["v2"]
    steps = PRIOR._steps(data)
    close = data.get("closeout") or {}
    comp = data.get("completion") or {}
    co = _closeout_state(v2)
    lock = _freeze(root)
    books = []
    for book in list(PRIOR.BOOKS) + [b for b in BOOK_SPEC if b not in PRIOR.BOOKS]:
        rows = data["books"].get(book)
        if rows is None:
            continue
        zh, src, ends, note = BOOK_SPEC.get(book, (book, [("VRN2", "VRN-2")], ["—"], ""))
        cols = _cols(rows)
        related = [PRIOR._step(steps, p) for p in (("⑥e",) if book == "BasicInfo" else ("⑥f",) if book == "Combined" else ("⑬b",) if book == "FinancialAligned" else ())]
        lamp = "GRAY" if not rows else "GREEN"
        for s in related:
            if s.get("lamp") in ("YELLOW", "RED") and lamp == "GREEN":
                lamp = s["lamp"]
        books.append({"group": "VRN-2 輸出冊", "table": book, "zh": zh, "key": PRIOR.KEYS.get(book, ""), "source": [t for _, t in src], "src": sorted({k for k, _ in src}),
                      "badges": src, "endpoint": ends, "headers": cols, "rows": len(rows), "lamp": lamp, "note": note,
                      "file": "VIA_Reports/vrn2/output/VRN2_%s_latest.json" % book, "parquet": book in data.get("parquet", {})})
    flow = []
    for s in steps:
        name = str(s.get("step", ""))
        cls = next((c for p, c in STEP_SRC if name.startswith(p)), ["VRN2"])
        flow.append({"step": name, "detail": str(s.get("detail", ""))[:300], "lamp": str(s.get("lamp") or "GRAY"), "src": cls})
    oth = others(root, data)
    lamps = [s["lamp"] for s in flow]
    return {"version": VERSION, "launcher": close.get("version") or (data.get("activate") or {}).get("version") or "—", "manager": comp.get("manager") or "—",
            "receipt": data.get("closeout_name") or "—", "closeout": co, "lock": {"name": lock.get("_name", ""), "state": lock.get("closeout_state", ""), "freeze": lock.get("freeze_status", "")},
            "books": books, "flow": flow, "others": oth,
            "count": {"books": len(books), "rows": sum(b["rows"] for b in books), "headers": sum(len(b["headers"]) for b in books),
                      "GREEN": lamps.count("GREEN"), "YELLOW": lamps.count("YELLOW"), "RED": lamps.count("RED")}}


def _hcell(cols: list, n: int = 10) -> str:
    chips = "".join('<span class="sm-h" title="%s">%s</span>' % (esc(c), esc(str(c).replace("_", " "))) for c in cols[:n])
    more = ('<span class="sm-h more">+%d 欄</span>' % (len(cols) - n)) if len(cols) > n else ""
    return '<div class="sm-hs">%s%s</div>' % (chips, more) if cols else '<span class="sm-mut">(冊是空的 · 沒有欄)</span>'


def summary_section(m: dict) -> str:
    co, cnt = m["closeout"], m["count"]
    st = co["state"] or "—"
    state_lamp = STATE_LAMP.get(co["state"], "GRAY")
    per = " · ".join("%s %d" % (k, v) for k, v in sorted(co["per"].items())) or "沒有收尾頁收據(RoundAll 還沒跑)"
    sub = "%s · %s · 收據 %s · Workbench %s" % (m["launcher"], m["manager"], m["receipt"], VERSION)
    legend = '<button class="sm-leg on" data-sum="f" data-src="all"><span class="sm-dot" style="background:var(--ink)"></span>全部</button>' + "".join(
        '<button class="sm-leg" data-sum="f" data-src="%s"><span class="sm-dot" style="background:var(%s)"></span>%s</button>' % (k, v, esc(t)) for k, t, v in SOURCES)
    hdr = '<div class="sm-colh">資料冊 / Table</div><div class="sm-colh">來源 / Source</div><div class="sm-colh">端點 / Endpoint</div><div class="sm-colh">表頭 / DataFrame Headers</div><div class="sm-colh">狀態</div>'
    rows = []
    for i, b in enumerate(m["books"]):
        rows.append('<div class="sm-row" data-sum="row" data-kind="book" data-i="%d" data-src="%s" tabindex="0">'
                    '<div class="sm-c"><div class="sm-lb">%s · %s</div><div class="sm-sb">%s</div><div class="sm-db">%s · %s 列</div></div>'
                    '<div class="sm-c">%s</div><div class="sm-c">%s</div><div class="sm-c">%s</div><div class="sm-c">%s</div></div>'
                    % (i, " ".join(b["src"]), esc(b["zh"]), esc(b["table"]), esc(b["key"] or "—"), esc(b["file"].split("/")[-1]), "{:,}".format(b["rows"]),
                       _badges(b["badges"]), "".join('<div class="sm-ep">%s</div>' % esc(e) for e in b["endpoint"]), _hcell(b["headers"]), _lamp(b["lamp"])))
    books = '<div class="sm-mx b5">%s%s</div>' % (hdr, "".join(rows) or '<div class="sm-empty">本輪沒有輸出冊(VIA_Reports/vrn2/output)</div>')
    fh = '<div class="sm-colh">步驟 / Step</div><div class="sm-colh">來源 / Source</div><div class="sm-colh">細節 / Detail</div><div class="sm-colh">狀態</div>'
    frows = "".join('<div class="sm-row" data-sum="row" data-kind="flow" data-i="%d" data-src="%s" tabindex="0"><div class="sm-c"><div class="sm-lb">%s</div></div><div class="sm-c">%s</div>'
                    '<div class="sm-c"><div class="sm-ep wrap">%s</div></div><div class="sm-c">%s</div></div>'
                    % (i, " ".join(f["src"]), esc(f["step"][:46]), _badges([(k, dict((a, b) for a, b, _ in SOURCES).get(k, k)) for k in f["src"]]), esc(f["detail"][:220]), _lamp(f["lamp"]))
                    for i, f in enumerate(m["flow"]))
    flow = '<div class="sm-mx b4">%s%s</div>' % (fh, frows or '<div class="sm-empty">尚無本輪步驟收據</div>')
    oh = '<div class="sm-colh">系統 / System</div><div class="sm-colh">已登記入口</div><div class="sm-colh">自報 / Self-report</div><div class="sm-colh">狀態</div>'
    orows = "".join('<div class="sm-row" data-sum="row" data-kind="other" data-i="%d" data-src="%s" tabindex="0"><div class="sm-c"><div class="sm-lb">%s</div><div class="sm-sb">只讀 · 不代修</div></div>'
                    '<div class="sm-c"><div class="sm-ep wrap">%s</div></div><div class="sm-c"><div class="sm-ep wrap">%s</div></div><div class="sm-c">%s</div></div>'
                    % (i, "VDF" if o["sys"] == "VDF" else "VCGC" if o["sys"] == "VCGC" else "VRN2", esc(o["sys"]), esc(o["entry"] or "未登記入口(不猜路徑)"), esc(o["self"]), _lamp(o["lamp"]))
                    for i, o in enumerate(m["others"]))
    oth = '<div class="sm-mx b4">%s%s</div>' % (oh, orows)
    lock = m["lock"]
    cards = ('<div class="sm-card" style="--c:var(--co)"><div class="sm-n">%s</div><div class="sm-l">輸出冊 · %s 列 · %s 個表頭欄</div><div class="sm-bar"></div></div>'
             '<div class="sm-card" style="--c:var(--%s)"><div class="sm-n">%s</div><div class="sm-l">結案狀態 · %s</div><div class="sm-bar"></div></div>'
             '<div class="sm-card" style="--c:var(--down)"><div class="sm-n">%d / %d / %d</div><div class="sm-l">本輪步驟 綠 / 黃 / 紅</div><div class="sm-bar"></div></div>'
             '<div class="sm-card" style="--c:var(--teal)"><div class="sm-n">%s</div><div class="sm-l">版本鎖 %s · %s</div><div class="sm-bar"></div></div>'
             % (cnt["books"], "{:,}".format(cnt["rows"]), cnt["headers"], {"GREEN": "down", "YELLOW": "am", "RED": "up"}.get(state_lamp, "mut2"), esc(st), esc(per),
                cnt["GREEN"], cnt["YELLOW"], cnt["RED"], esc(lock["freeze"] or "—"), esc(lock["name"] or "沒有鎖檔"), esc(("收尾 " + lock["state"]) if lock["state"] else "")))
    return ('<section class="tabsec on" data-tab="summary">\n<div class="box sm" id="sysmatrix">'
            '<div class="sm-hdr"><div class="sm-hl"><div class="sm-badge">VRN-2 · VIA SYSTEM MATRIX</div><div class="sm-title">系統現況 Summary</div><div class="sm-sub">%s</div></div>'
            '<div class="sm-stats"><div class="sm-stat"><div class="sm-sn">%d</div><div class="sm-sl">輸出冊</div></div><div class="sm-stat"><div class="sm-sn">%s</div><div class="sm-sl">資料列</div></div>'
            '<div class="sm-stat"><div class="sm-sn" style="color:var(--down)">%d</div><div class="sm-sl">綠</div></div><div class="sm-stat"><div class="sm-sn" style="color:var(--am)">%d</div><div class="sm-sl">黃</div></div>'
            '<div class="sm-stat"><div class="sm-sn" style="color:var(--up)">%d</div><div class="sm-sl">紅</div></div></div></div>'
            '<div class="sm-state %s"><b>收尾 %s</b> %s · %s<span class="sm-mut"> · BLOCKED / REVIEW / DATA_GAP 都不是成功 · VCGC 的 closeout_lamp 才是 VCGC 驗收</span></div>'
            '<div class="sm-legend">%s</div>'
            '<div class="sm-detail" id="smDetail" hidden><div class="sm-dh"><div class="sm-dt" id="smDetailT">—</div><button class="sm-x" data-sum="close">ESC</button></div><div class="sm-db2" id="smDetailB"></div></div>'
            '<div class="sm-sec"><div class="sm-sect">VRN-2 · 輸出冊 DataFrame · VIA_Reports/vrn2/output</div>%s</div>'
            '<div class="sm-sec"><div class="sm-sect">VRN-2 · 本輪流程步驟 · %s</div>%s</div>'
            '<div class="sm-sec"><div class="sm-sect">其他系統 · 只讀互看 · 四系統對等(VRN-1 · VRN-2 · VDF · VCGC)</div>%s</div>'
            '<div class="sm-sum">%s</div></div>\n</section>\n'
            % (esc(sub), cnt["books"], "{:,}".format(cnt["rows"]), cnt["GREEN"], cnt["YELLOW"], cnt["RED"], esc(state_lamp), esc(st), esc(co["label"] or ""), esc(per),
               legend, books, esc(m["receipt"]), flow, oth, cards))


CSS_V0103 = r"""
/* v0103 操作員 2026-11-01:00 系統現況 · 版面與字體階層照 taiwan_stock_data_matrix · 顏色 / 字型仍是範本鎖定的 */
.sm{padding:22px 22px 18px}
.sm-hdr{display:flex;align-items:flex-end;gap:24px;border-bottom:1px solid var(--line);padding-bottom:16px;margin-bottom:14px;flex-wrap:wrap}
.sm-badge{display:inline-block;font:500 10px "DM Mono",monospace;letter-spacing:.14em;text-transform:uppercase;color:var(--co);background:rgba(181,41,26,.06);border:1px solid rgba(181,41,26,.22);padding:3px 8px;border-radius:3px;margin-bottom:6px;white-space:nowrap}
.sm-title{font:600 22px/1.2 "DM Sans","Noto Sans TC",sans-serif;letter-spacing:-.01em;color:var(--ink)}
.sm-sub{font:400 12px "DM Mono","Noto Sans TC",monospace;color:var(--mut);margin-top:4px;overflow-wrap:anywhere}
.sm-stats{margin-left:auto;display:flex;gap:20px;flex-shrink:0}
.sm-stat{text-align:right}
.sm-sn{font:500 20px/1 "DM Mono",monospace;color:var(--ink);font-variant-numeric:tabular-nums}
.sm-sl{font-size:11px;color:var(--mut);margin-top:3px}
.sm-state{border:1px solid var(--line);border-left:3px solid var(--mut2);border-radius:0 7px 7px 0;padding:8px 12px;margin-bottom:12px;font-size:11.5px;background:var(--paper2)}
.sm-state.GREEN{border-left-color:var(--down)}.sm-state.YELLOW{border-left-color:var(--am)}.sm-state.RED{border-left-color:var(--up)}
.sm-state b{font:600 12px "DM Mono",monospace;margin-right:6px}
.sm-mut{color:var(--mut)}
.sm-legend{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:16px}
.sm-leg{display:flex;align-items:center;gap:7px;font:500 11.5px "DM Sans","Noto Sans TC",sans-serif;color:var(--mut);cursor:pointer;padding:5px 10px 5px 8px;border-radius:5px;border:1px solid transparent;background:transparent;transition:all .18s}
.sm-leg:hover{background:var(--soft);border-color:var(--line)}
.sm-leg.on{border-color:var(--line);background:var(--paper2);color:var(--ink)}
.sm-dot{width:8px;height:8px;border-radius:50%;display:inline-block;flex-shrink:0;background:var(--c,var(--mut2))}
.sm-sec{margin-bottom:18px}
.sm-sect{font:500 10px "DM Mono",monospace;letter-spacing:.12em;text-transform:uppercase;color:var(--mut2);margin:0 0 8px 2px}
.sm-mx{display:grid;border:1px solid var(--line);border-radius:8px;overflow:hidden;background:var(--paper)}
.sm-mx.b5{grid-template-columns:minmax(170px,1.1fr) minmax(130px,.9fr) minmax(150px,1fr) minmax(220px,1.8fr) 92px}
.sm-mx.b4{grid-template-columns:minmax(170px,1fr) minmax(130px,.8fr) minmax(220px,2fr) 92px}
.sm-colh{font:500 10px "DM Mono",monospace;letter-spacing:.1em;text-transform:uppercase;color:var(--mut2);padding:9px 12px;background:var(--paper2);border-bottom:1px solid var(--line)}
.sm-colh:not(:last-of-type){border-right:1px solid var(--line)}
.sm-row{display:contents;cursor:pointer}
.sm-row>.sm-c{padding:11px 12px;border-bottom:1px solid var(--soft);min-width:0;transition:background .15s,opacity .15s}
.sm-row>.sm-c:not(:last-child){border-right:1px solid var(--soft)}
.sm-row:hover>.sm-c,.sm-row:focus>.sm-c,.sm-row.sel>.sm-c{background:var(--zebra)}
.sm-row:focus{outline:none}
.sm-row.dim>.sm-c{opacity:.25}
.sm-lb{font:500 13px/1.3 "DM Sans","Noto Sans TC",sans-serif;color:var(--ink)}
.sm-sb{font:400 10px "DM Mono",monospace;color:var(--mut);margin-top:3px;overflow-wrap:anywhere}
.sm-db{font:400 10.5px "DM Mono",monospace;color:var(--mut2);margin-top:4px}
.sm-src{display:inline-flex;align-items:center;gap:6px;font:500 11px/1 "DM Mono","Noto Sans TC",monospace;padding:4px 8px;border-radius:4px;border:1px solid color-mix(in srgb,var(--c) 35%,transparent);color:var(--c);background:color-mix(in srgb,var(--c) 7%,transparent);white-space:nowrap;margin:0 4px 4px 0}
.sm-src .sm-dot{width:6px;height:6px}
.sm-ep{font:400 10px/1.45 "DM Mono","Noto Sans TC",monospace;color:var(--ink2);overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sm-ep+.sm-ep{margin-top:4px}
.sm-ep.wrap,.sm-ep:hover{white-space:normal;overflow-wrap:anywhere}
.sm-hs{display:flex;flex-wrap:wrap;gap:4px}
.sm-h{font:500 10px/1 "DM Mono",monospace;color:var(--ink2);background:var(--paper2);border:1px solid var(--line);border-radius:3px;padding:3px 6px;white-space:nowrap}
.sm-h.more{color:var(--mut);border-style:dashed}
.sm-st{display:inline-flex;align-items:center;gap:5px;font:500 10.5px "DM Mono",monospace;padding:3px 7px;border-radius:4px;border:1px solid;white-space:nowrap;--c:var(--mut2);color:var(--c);border-color:color-mix(in srgb,var(--c) 35%,transparent);background:color-mix(in srgb,var(--c) 8%,transparent)}
.sm-st .sm-dot{width:6px;height:6px}
.sm-st.GREEN{--c:var(--down)}.sm-st.YELLOW{--c:var(--am)}.sm-st.RED{--c:var(--up)}
.sm-empty{grid-column:1/-1;padding:12px;color:var(--mut);font-size:11.5px}
.sm-detail{border:1px solid var(--line);border-radius:8px;background:var(--paper);margin-bottom:16px;overflow:hidden;animation:smDown .2s ease}
.sm-detail[hidden]{display:none}
@keyframes smDown{from{opacity:0;transform:translateY(-6px)}to{opacity:1;transform:none}}
.sm-dh{display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid var(--line);gap:10px}
.sm-dt{font:600 13px "DM Sans","Noto Sans TC",sans-serif}
.sm-x{font:500 11px "DM Mono",monospace;color:var(--mut);padding:3px 7px;border:1px solid var(--line);border-radius:3px;background:transparent;cursor:pointer}
.sm-db2{padding:14px 16px;display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:12px}
.sm-kv{display:flex;flex-direction:column;gap:3px;min-width:0}
.sm-kv.full{grid-column:1/-1}
.sm-k{font:500 10px "DM Mono",monospace;color:var(--mut2);text-transform:uppercase;letter-spacing:.08em}
.sm-v{font:400 12.5px/1.5 "DM Mono","Noto Sans TC",monospace;color:var(--ink);overflow-wrap:anywhere}
.sm-v table{font-size:11px}
.sm-v td,.sm-v th{padding:3px 8px}
.sm-sum{display:grid;grid-template-columns:repeat(auto-fit,minmax(190px,1fr));gap:12px;margin-top:6px}
.sm-card{background:var(--paper2);border:1px solid var(--line);border-radius:7px;padding:14px 16px;min-width:0}
.sm-n{font:500 26px/1 "DM Mono",monospace;color:var(--c);font-variant-numeric:tabular-nums;overflow-wrap:anywhere}
.sm-l{font-size:11px;color:var(--mut);margin-top:6px;overflow-wrap:anywhere}
.sm-bar{height:2px;border-radius:2px;margin-top:10px;background:var(--c);opacity:.5}
@media (max-width:760px){
  .sm{padding:14px}
  .sm-stats{margin-left:0;width:100%;justify-content:space-between;gap:10px}
  .sm-mx.b5,.sm-mx.b4{grid-template-columns:1fr}
  .sm-colh{display:none}
  .sm-row>.sm-c{border-right:none!important;border-bottom:none;padding:6px 12px}
  .sm-row>.sm-c:first-child{padding-top:12px}
  .sm-row>.sm-c:last-child{border-bottom:1px solid var(--line);padding-bottom:12px}
}
@media print{.sm-legend,.sm-x{display:none}}
"""

JS_V0103 = r"""
<script>
(function(){
  var M = window.VRN2_SUMMARY || {books: [], flow: [], others: []}, HDR = window.VRN2_SUMMARY_HDR || {};
  function q(s){ return document.querySelector(s); } function qa(s){ return Array.prototype.slice.call(document.querySelectorAll(s)); }
  function h(v){ return String(v == null ? '' : v).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function kv(k, v, full){ return '<div class="sm-kv' + (full ? ' full' : '') + '"><div class="sm-k">' + h(k) + '</div><div class="sm-v">' + v + '</div></div>'; }
  function show(row){
    var kind = row.getAttribute('data-kind'), i = +row.getAttribute('data-i'), d, t, body = '';
    qa('.sm-row.sel').forEach(function(r){ r.classList.remove('sel'); }); row.classList.add('sel');
    if (kind === 'book') { d = M.books[i]; t = d.zh + ' · ' + d.table + ' — ' + d.headers.length + ' 欄 · ' + d.rows.toLocaleString('en-US') + ' 列';
      body = kv('資料冊', h(d.table) + ' · ' + h(d.zh)) + kv('鍵 / Key', h(d.key || '—')) + kv('來源', h(d.source.join(' · '))) + kv('端點', h(d.endpoint.join(' · '))) +
             kv('檔案', h(d.file) + (d.parquet ? ' · 有 Parquet' : '')) + kv('狀態', h(d.lamp)) + kv('備註', h(d.note || '—')) +
             kv('DataFrame 表頭(' + d.headers.length + ' 欄 · 順序照冊)', d.headers.length ? '<table><thead><tr><th>#</th><th>欄名</th><th>顯示名稱</th></tr></thead><tbody>' + d.headers.map(function(c, n){ return '<tr><td>' + (n + 1) + '</td><td>' + h(c) + '</td><td>' + h(HDR[c] || String(c).replace(/_/g, ' ')) + '</td></tr>'; }).join('') + '</tbody></table>' : '(冊是空的)', true); }
    else if (kind === 'flow') { d = M.flow[i]; t = d.step; body = kv('狀態', h(d.lamp)) + kv('來源', h(d.src.join(' · '))) + kv('細節', h(d.detail), true); }
    else { d = M.others[i]; t = d.sys + ' · 只讀互看'; body = kv('狀態', h(d.lamp)) + kv('已登記入口', h(d.entry || '未登記(不猜路徑)')) + kv('自報', h(d.self), true) + kv('收據', h(d.path || '—')); }
    q('#smDetailT').textContent = t; q('#smDetailB').innerHTML = body; q('#smDetail').hidden = false;
    q('#smDetail').scrollIntoView({behavior: 'smooth', block: 'nearest'});
  }
  function close(){ var p = q('#smDetail'); if (p) p.hidden = true; qa('.sm-row.sel').forEach(function(r){ r.classList.remove('sel'); }); }
  function filt(b){ var s = b.getAttribute('data-src'); qa('.sm-leg').forEach(function(x){ x.classList.toggle('on', x === b); });
    qa('.sm-row').forEach(function(r){ var rs = (r.getAttribute('data-src') || '').split(' '); r.classList.toggle('dim', s !== 'all' && rs.indexOf(s) < 0); }); }
  document.addEventListener('click', function(e){ var b = e.target.closest('[data-sum]'); if (!b) return; var a = b.getAttribute('data-sum');
    if (a === 'row') show(b); else if (a === 'f') filt(b); else if (a === 'close') close(); });
  document.addEventListener('keydown', function(e){ if (e.key === 'Escape') close(); else if ((e.key === 'Enter' || e.key === ' ') && e.target.classList && e.target.classList.contains('sm-row')) { e.preventDefault(); show(e.target); } });
})();
</script>
"""

# v0102 頁面上的錨點(每個恰一次 · 找不到就停,不猜)
_A_TAB = '<button class="active" data-act="tab" data-tab="overview">01 輸入總覽</button>'
_A_SEC = '    <section class="tabsec on" data-tab="overview">\n'
_A_STATE = "st = {tab:'overview',"
_A_BOOT = "  setTab('overview'); renderData(); renderX(); selCount();"
_A_EXPORT = "else if (st.tab === 'overview') { data = D.files;"
_A_STYLE = "</style>"
_A_BODY = "</body>"


def export_rows(m: dict) -> list:
    out = [{"group": "VRN-2 輸出冊", "table": b["table"], "source": " · ".join(b["source"]), "endpoint": " · ".join(b["endpoint"]), "headers": " | ".join(b["headers"]), "rows": b["rows"], "lamp": b["lamp"]} for b in m["books"]]
    out += [{"group": "VRN-2 流程步驟", "table": f["step"], "source": " · ".join(f["src"]), "endpoint": f["detail"], "headers": "", "rows": "", "lamp": f["lamp"]} for f in m["flow"]]
    out += [{"group": "只讀互看", "table": o["sys"], "source": o["entry"], "endpoint": o["self"], "headers": "", "rows": "", "lamp": o["lamp"]} for o in m["others"]]
    return out


def _js_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def render(root: Path, out_path: Path | None = None, logo: str | None = None, assets_zip: Path | None = None) -> Path:
    root = Path(root).resolve()
    out = PRIOR.render(root, out_path, logo, assets_zip)
    page = Path(out).read_text(encoding="utf-8")
    data = PRIOR.collect(root)
    m = summary_model(root, data)
    data_js = "<script>window.VRN2_SUMMARY = %s; window.VRN2_SUMMARY.rows = %s; window.VRN2_SUMMARY_HDR = %s;</script>\n" % (_js_json(m), _js_json(export_rows(m)), _js_json(HDR))
    edits = ((_A_TAB, '<button class="active" data-act="tab" data-tab="summary">00 系統現況</button><button data-act="tab" data-tab="overview">01 輸入總覽</button>'),
             (_A_SEC, summary_section(m) + '    <section class="tabsec" data-tab="overview">\n'),
             (_A_STATE, "st = {tab:'summary',"),
             (_A_BOOT, "  setTab('summary'); renderData(); renderX(); selCount();"),
             (_A_EXPORT, "else if (st.tab === 'summary') { data = (window.VRN2_SUMMARY || {}).rows || []; C = ['group', 'table', 'source', 'endpoint', 'headers', 'rows', 'lamp']; } " + _A_EXPORT),
             (_A_STYLE, CSS_V0103 + _A_STYLE),
             (_A_BODY, data_js + JS_V0103 + _A_BODY))
    for anchor, new in edits:
        if page.count(anchor) != 1:
            raise RuntimeError("v0102 頁面錨點找不到(恰一次):%s(%d 次)" % (anchor.strip()[:50], page.count(anchor)))
        page = page.replace(anchor, new)
    page = page.replace("<title>VRN-2 Workbench</title>", "<title>VRN-2 Workbench</title><!-- VRN2_Workbench %s over v0102 -->" % VERSION, 1)
    tmp = Path(out).with_suffix(".tmp")
    tmp.write_text(page, encoding="utf-8")
    tmp.replace(Path(out))
    return Path(out)


def _strip_v0103(page: str) -> str:
    """把 v0103 加的東西拿掉 → 應該跟 v0102 的頁面逐字相同(自測:原有功能設定不改)。"""
    page = re.sub(r'<section class="tabsec on" data-tab="summary">\n.*?\n</section>\n', "", page, count=1, flags=re.S)
    page = page.replace('<button class="active" data-act="tab" data-tab="summary">00 系統現況</button><button data-act="tab" data-tab="overview">01 輸入總覽</button>', _A_TAB, 1)
    page = page.replace('    <section class="tabsec" data-tab="overview">\n', _A_SEC, 1)
    page = page.replace("st = {tab:'summary',", _A_STATE, 1).replace("  setTab('summary'); renderData(); renderX(); selCount();", _A_BOOT, 1)
    page = re.sub(r"else if \(st\.tab === 'summary'\) \{.*?\} (?=else if \(st\.tab === 'overview'\))", "", page, count=1, flags=re.S)
    page = page.replace(CSS_V0103, "", 1)
    page = re.sub(r"<script>window\.VRN2_SUMMARY = .*?</script>\n", "", page, count=1, flags=re.S)
    page = page.replace(JS_V0103, "", 1)
    page = page.replace("<!-- VRN2_Workbench %s over v0102 -->" % VERSION, "", 1)
    return page


def selftest() -> int:
    bad = []

    def chk(label, cond):
        print("[%s] %s" % ("PASS" if cond else "FAIL", label))
        if not cond:
            bad.append(label)

    with tempfile.TemporaryDirectory() as t:
        root = Path(t)
        PRIOR._fixture_v0102(root)
        v2 = root / "VIA_Reports" / "vrn2"
        json.dump({"state": "REVIEW", "state_label": "等人工核對", "state_text": "VRN-2 側沒有待修", "items": [{"owner": "人工", "step": "四點"}, {"owner": "人工", "step": "缺項"}, {"owner": "資料源", "step": "⑥e"}]},
                  open(v2 / "VRN2_CloseoutUI_latest.json", "w", encoding="utf-8"), ensure_ascii=False)
        (root / "docs" / "handoff").mkdir(parents=True, exist_ok=True)
        json.dump({"lamp": "GREEN", "closeout_lamp": "YELLOW", "at": "2026-11-01T00:00:00Z", "summary": {"pending": 104}}, open(root / "docs" / "handoff" / "HANDOFF_latest.json", "w", encoding="utf-8"))
        o = Path(PRIOR.render(root, root / "wb.html")).read_text(encoding="utf-8")
        n = Path(render(root, root / "wb.html")).read_text(encoding="utf-8")
        ts = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z")   # 兩次渲染只差產生時間
        chk("① 右面板第一個分頁是「00 系統現況」且預設開它 · 01 不再 active", n.index('data-tab="summary">00 系統現況') < n.index('data-tab="overview">01 輸入總覽')
            and '<button class="active" data-act="tab" data-tab="summary">' in n and '<button class="active" data-act="tab" data-tab="overview">' not in n)
        chk("① 00 區塊恰一個且是 on · 01 區塊恰一個不是 on", n.count('data-tab="summary">\n<div class="box sm"') == 1 and n.count('<section class="tabsec on"') == 1 and n.count('<section class="tabsec" data-tab="overview">') == 1)
        chk("① JS 起始分頁 summary(st.tab 與開頁 setTab)", "st = {tab:'summary'," in n and "setTab('summary'); renderData();" in n and "setTab('overview'); renderData();" not in n)
        chk("② 原有功能設定不改:把 v0103 加的拿掉 = v0102 頁面逐字相同(01 ~ 04 分頁 · 資料 · 匯出 · 左面板)", ts.sub("TS", _strip_v0103(n)) == ts.sub("TS", o))
        mm = json.loads(re.search(r"window\.VRN2_SUMMARY = (\{.*?\}); window\.VRN2_SUMMARY\.rows", n, re.S).group(1))
        names = [b["table"] for b in mm["books"]]
        fd = next(b for b in mm["books"] if b["table"] == "FinancialData")
        chk("③ DataFrame 表頭 = 冊裡真實欄名(每本冊 · 順序照冊)", set(names) >= {"BasicInfo", "FinancialData", "Summary", "Rejected", "FinancialAligned", "Deleted"} and fd["headers"][:3] == list(json.load(open(v2 / "output" / "VRN2_FinancialData_latest.json", encoding="utf-8"))[0].keys())[:3])
        chk("③ 矩陣格顯示表頭欄名(底線 → 空格 · title 原欄名)", 'class="sm-h" title="FILENAME">FILENAME</span>' in n and ('title="REPORT_DATE">REPORT DATE</span>' in n))
        chk("③ 雙語表頭沿用 v0102 對照表(不另抄)", HDR.get("REPORT_DATE", "").startswith("Report Date") and '"REPORT_DATE": "Report Date' in n)
        chk("④ 三個矩陣:輸出冊 · 本輪流程步驟 · 只讀互看", n.count('<div class="sm-mx b5">') == 1 and n.count('<div class="sm-mx b4">') == 2 and "VRN-2 · 本輪流程步驟" in n and "只讀互看" in n)
        chk("④ 只讀互看:VCGC 讀交接快照自報的燈 · VDF 沒自報 → 灰燈寫原因 · VRN-1 只看入口", [o_["sys"] for o_ in mm["others"]] == ["VCGC", "VDF", "VRN-1"] and mm["others"][0]["lamp"] == "YELLOW" and mm["others"][1]["lamp"] == "GRAY" and "不猜" in mm["others"][1]["self"])
        chk("⑤ 結案狀態照收尾頁收據寫(REVIEW = 黃 · 不寫成成功)", mm["closeout"]["state"] == "REVIEW" and 'sm-state YELLOW"><b>收尾 REVIEW</b>' in n and "人工 2 · 資料源 1" in n)
        chk("⑥ 匯出本頁:00 頁有自己的分支(矩陣列)· 01 分支照舊", "else if (st.tab === 'summary') { data = (window.VRN2_SUMMARY || {}).rows" in n and n.count("else if (st.tab === 'overview') { data = D.files;") == 1)
        chk("⑥ 窄螢幕一列一卡 · 列印隱藏圖例", "@media (max-width:760px)" in n and ".sm-mx.b5,.sm-mx.b4{grid-template-columns:1fr}" in n)
        chk("② 視覺鎖:只用範本的色變數與字型(DM Sans · DM Mono · Noto Sans TC)· 不引外部字型 / 不換色盤", "fonts.googleapis" not in CSS_V0103 and not re.search(r"#[0-9a-fA-F]{6}", CSS_V0103) and "var(--blue)" in n and "var(--vi)" in n)
        chk("⑦ JS 與 v0101 的事件分開(data-sum · 不碰 data-act)· 嵌入資料可解析", 'data-sum="row"' in n and 'data-act="sum' not in n and isinstance(mm["count"]["rows"], int))
        shutil_ok = True
        try:
            (root / "VIA_Reports" / "vrn2" / "output" / "VRN2_Summary_latest.json").write_text("[]", encoding="utf-8")
            n2 = Path(render(root, root / "v0103b.html")).read_text(encoding="utf-8")
            shutil_ok = "(冊是空的 · 沒有欄)" in n2
        except Exception as error:  # noqa: BLE001
            shutil_ok = False
            print("    ", type(error).__name__, error)
        chk("⑧ 空冊照列(灰燈 · 寫沒有欄)· 不當掉", shutil_ok)
    print("[%s] VRN2_Workbench %s --selftest · %d 項 · 不過 %d" % ("PASS" if not bad else "FAIL", VERSION, 15, len(bad)))
    return 0 if not bad else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if "--selftest" in argv:
        return selftest()
    if argv and argv[0] == "logo":
        return PRIOR.main(argv)
    import argparse
    ap = argparse.ArgumentParser(prog="VRN2_Workbench_v0103")
    ap.add_argument("verb", nargs="?", default="render")
    ap.add_argument("--root", default=None)
    ap.add_argument("--out", default=None)
    ap.add_argument("--logo", default=None)
    a = ap.parse_args(argv)
    if a.verb != "render":
        return PRIOR.main(argv)
    root = Path(a.root) if a.root else (os.environ.get("VIA_ROOT") and Path(os.environ["VIA_ROOT"])) or HERE.parent.parent
    path = render(root, a.out, a.logo)
    print("[GREEN] %s %s · %s" % (DISPLAY_NAME, VERSION, path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
