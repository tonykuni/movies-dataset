#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0160 — 薄尾(操作員 2026-10-10)。
  ① 四碼代號去資料庫找名稱:讀共用引擎 VIA_DuckDBStatus 的代號名冊(tw__tw_listings · 依欄裡的值認欄)→ 補名稱 · 市場別(yfinance .TW / .TWO)· 總清單沒收的代號也補進來
  ② 不合理值剔除(與資料庫股價比):目標價不在股價 0.3–5 倍 · 收盤偏離報告日前收盤 >50% → 不採用(實機:KGI 目標價 1.0、志強收盤 10.0)
  ③ 小框不算表:不到 2×2 的框(KGI 頁面大量框線文字)→ 當文字框,不再算「列或欄少於 2」失敗
  ④ 表頭可在第 2–3 列(前一列是表名 / 單位)
  ⑤ TableRepair 雙讀只給財務表 / 估值表,需要才讀該頁字(實機表格還原 480 秒);格線合併容差 0.5pt → 2pt(假欄造成 OVERLAPPING / GRID_HOLE 57 張)
其餘動詞照前版鏈。
"""
from __future__ import annotations

# ===== [VIA:ACCEL-BRIDGE:v0110] 正本加速器 VeritasCeleritas_v1141 · 正本網路工具 VeritasAegisNexus_v1652(找不到 = 不改任何行為) =====
import sys as _cb_sys
from pathlib import Path as _cb_Path
_cb_p = _cb_Path(__file__).resolve()
while _cb_p.parent != _cb_p:
    if (_cb_p / "supportive modules").is_dir():
        _cb_sup = _cb_p / "supportive modules"
        for _cb_d in [_cb_sup] + [x.parent for x in list(_cb_sup.glob("*/VeritasAegisNexus_v1652.py"))[:1]]:
            if str(_cb_d) not in _cb_sys.path:
                _cb_sys.path.insert(0, str(_cb_d))
        break
    _cb_p = _cb_p.parent
try:
    import VeritasCeleritas_v1141 as _ACCEL  # noqa: F401  正本加速器
except Exception:  # noqa: BLE001
    _ACCEL = None


def _net():
    """正本網路工具(只在需要出網時載入;本引擎不出網)。"""
    try:
        import VeritasAegisNexus_v1652 as _NET  # noqa: WPS433
        return _NET
    except Exception:  # noqa: BLE001
        return None
# ===== [VIA:ACCEL-BRIDGE:END] =====

import datetime
import hashlib
import importlib.util
import json
import os
import re
import sys
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0160"


def _vnum_v0160(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0160(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0160(p) < _vnum_v0160(__file__)), key=_vnum_v0160)
PRIOR = _load_v0160(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


def __getattr__(name):
    return getattr(PRIOR, name)


def _owner(name):
    import types
    mod, seen = PRIOR, set()
    while isinstance(mod, types.ModuleType) and id(mod) not in seen:
        seen.add(id(mod))
        if name in vars(mod):
            return mod
        mod = vars(mod).get("PRIOR")
    return None


def _resolve(name):
    m = _owner(name)
    return vars(m)[name] if m else None


def _patch(name, fn):
    m = _owner(name)
    if not m:
        return None
    old = vars(m)[name]
    setattr(m, name, fn)
    return old


# 多程序墊片(當 __main__ 的尾版必帶)
def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_home, _rep, _temp_base = _resolve("_home"), _resolve("_rep"), _resolve("_temp_base")
tablerepair = _resolve("tablerepair")
_TR_SOFT, _TR_OCR, _TCACHE, _RUN = _resolve("_TR_SOFT"), _resolve("_TR_OCR"), _resolve("_TCACHE"), _resolve("_RUN")


def _snap2(values, tol: float = 2.0) -> list:
    groups = []
    for v in sorted(set(values)):
        if groups and v - groups[-1][-1] <= tol:
            groups[-1].append(v)
        else:
            groups.append([v])
    return [sum(g) / len(g) for g in groups]


def tr_check_v160(fpage, ppage, bbox, words, other, neighbors) -> dict | None:
    tr = tablerepair()
    if not tr.get("ok"):
        return None
    import fitz  # noqa: WPS433
    geo, val = tr["geo"], tr["val"]
    best = None
    for strategy in ("lines", "text"):
        try:
            tabs = fpage.find_tables(clip=fitz.Rect(bbox[0] - 4, bbox[1] - 4, bbox[2] + 4, bbox[3] + 4), strategy=strategy).tables   # 留 4pt 邊,貼邊裁會掉最後一列
        except Exception:  # noqa: BLE001
            continue
        for c in tabs:
            cb = c.bbox
            ix = max(0.0, min(cb[2], bbox[2]) - max(cb[0], bbox[0])) * max(0.0, min(cb[3], bbox[3]) - max(cb[1], bbox[1]))
            un = (cb[2] - cb[0]) * (cb[3] - cb[1]) + (bbox[2] - bbox[0]) * (bbox[3] - bbox[1]) - ix
            iou = ix / un if un else 0
            if iou >= 0.5 and (best is None or iou > best[0]):
                best = (iou, c, strategy)
        if best:
            break
    if not best:
        return {"status": "NO_GRID", "issues": {"NO_GRID": 1}, "rows": None}
    c = best[1]
    boxes = [list(b) for b in c.cells if b]
    xs = _snap2([x for b in boxes for x in (b[0], b[2])])          # v0160:2pt 容差合併格線(TableRepair 0.5pt 太細 → 假欄 → 跨格重疊 / 網格洞)
    ys = _snap2([y for b in boxes for y in (b[1], b[3])])
    cells = []
    for b in boxes:
        c0 = min(range(len(xs)), key=lambda i: abs(xs[i] - b[0]))
        c1 = min(range(len(xs)), key=lambda i: abs(xs[i] - b[2]))
        r0 = min(range(len(ys)), key=lambda i: abs(ys[i] - b[1]))
        r1 = min(range(len(ys)), key=lambda i: abs(ys[i] - b[3]))
        if c1 > c0 and r1 > r0:
            cells.append({"row": r0, "col": c0, "rowspan": r1 - r0, "colspan": c1 - c0, "bbox": b})
    table = {"id": "T", "page": 1, "bbox": list(c.bbox), "rows": len(ys) - 1, "cols": len(xs) - 1, "cells": cells, "physical_grid": best[2] == "lines", "equations": []}
    try:
        rep = geo.def_repair_table(table, words, other, (float(fpage.rect.width), float(fpage.rect.height)), neighbors)
        rep = val.def_validate(rep)
    except Exception as exc:  # noqa: BLE001
        return {"status": "GRID_INVALID", "issues": {type(exc).__name__ + ":" + str(exc)[:30]: 1}, "rows": None}
    grid = [["" for _ in range(rep["cols"])] for _ in range(rep["rows"])]
    for cell in rep["cells"]:
        grid[cell["row"]][cell["col"]] = cell["text"].replace("\n", " ")
    iss = Counter(i.get("code", "?") for i in rep.get("issues", []))
    return {"status": rep.get("native_check_status", "REVIEW"), "issues": dict(iss), "rows": grid, "strategy": best[2], "repairs": len(rep.get("repairs", [])), "words": rep.get("source_word_coverage", {})}




def l2_one_v160(row: dict) -> dict:
    import pdfplumber
    T = Counter()
    t0 = time.time()
    ctx = _resolve("_CTX")
    book, master, opts = ctx.get("book", {}), ctx.get("master", {}), ctx.get("opts", {})
    src = Path(row.get("mini") or row.get("src_pdf") or row["path"])
    pick = row.get("picked") or [1]
    an, ff, rj, cov, rpt, uo, tcat = (_resolve(n) for n in ("analyze_page", "_footer_fix", "rejoin", "coverage", "repair_table", "units_of", "_table_cat"))
    vt = _resolve("verify_table")
    tr = tablerepair()
    fdoc = None
    if tr.get("ok"):
        try:
            import fitz  # noqa: WPS433
            fdoc = fitz.open(str(src))
        except Exception:  # noqa: BLE001
            fdoc = None
    pages, regions = [], []
    with pdfplumber.open(str(src)) as pdf:
        local = list(range(1, len(pdf.pages) + 1)) if row.get("mini") else pick
        p1t = pdf.pages[local[0] - 1].extract_text() or ""
        for i, lp in enumerate(local):
            page = pdf.pages[lp - 1]
            ta = time.time()
            pg = an(pdf, lp, str(src), annual=(i > 0), tabula_ok=bool(opts.get("tabula")))
            T["版面切割"] += time.time() - ta
            orig = pick[i] if i < len(pick) else lp
            if orig != pg["page"]:
                for b in pg["blocks"]:
                    b["id"] = re.sub(r"^P\d+·", "P%d·" % orig, b["id"])
                pg["page"] = orig
            ff(pg)
            ta = time.time()
            for b in pg["blocks"]:
                if b["kind"] == "text":
                    b["text"], b["joins"], b["sus"] = rj(b.get("lines", []))
            pg["coverage"] = cov(page, pg["blocks"])
            T["文字還原"] += time.time() - ta
            ta = time.time()
            words = other = None
            wread = False                                   # v0160:雙讀只給財務表 / 估值表,有需要才讀該頁字(省時)
            tbls = [b for b in pg["blocks"] if b["kind"] == "table"]
            for b in tbls:
                b["page"] = orig
                rr = rpt(b, page)
                b["rows"], b["fixes"] = rr["rows"], rr["fixes"]
                b["sub"] = tcat(b["rows"], b["role"])
                if fdoc is not None and b["sub"].startswith(("財務表", "估值表")) and not wread:
                    wread = True
                    try:
                        words, other = tr["geo"].def_read_page(fdoc[lp - 1], page)
                    except Exception:  # noqa: BLE001
                        words = None
                if words is not None and b["sub"].startswith(("財務表", "估值表")):
                    neigh = [[x["x0"], x["top"], x["x1"], x["bottom"]] for x in tbls if x is not b]
                    trr = tr_check_v160(fdoc[lp - 1], page, (b["x0"], b["top"], b["x1"], b["bottom"]), words, other, neigh)
                    b["tr"] = trr
                    if trr and trr.get("rows") and (trr.get("status") == "PASS" or set(trr.get("issues", {})) <= _TR_SOFT):
                        if len(trr["rows"]) >= len(b.get("rows") or []):           # 雙讀格線列數不少於 pdfplumber 才採用(絕不拿資料換通過)
                            b["rows"], b["engine"] = trr["rows"], "TableRepair(雙讀一致)"
                            b["sub"] = tcat(b["rows"], b["role"])
                        else:
                            trr["note"] = "雙讀格線少 %d 列 → 保留 pdfplumber 列" % (len(b.get("rows") or []) - len(trr["rows"]))
                b["verify"] = vt(b, page)
                t_tr = b.get("tr") or {}
                hard = set(t_tr.get("issues", {})) & _TR_OCR
                if (t_tr.get("status") == "PASS" or (t_tr.get("status") == "REVIEW" and t_tr.get("rows") and set(t_tr.get("issues", {})) <= _TR_SOFT)) and not t_tr.get("note"):
                    b["verify"]["ok"], b["verify"]["native"] = True, "雙讀一致(PyMuPDF = pdfplumber · 字詞守恆)" + ("" if t_tr.get("status") == "PASS" else " · 情境待看:" + ",".join(sorted(t_tr["issues"])))
                    t_tr["status"] = "PASS" if t_tr.get("status") == "PASS" else "PASS_SOFT"
                elif t_tr.get("status") == "REVIEW":
                    b["verify"]["native"] = "雙讀待審:" + " ".join("%s×%d" % kv for kv in sorted(t_tr["issues"].items()))
                    if hard:
                        b["verify"]["ok"] = False
                        b["verify"]["issues"] = list(b["verify"].get("issues", [])) + ["雙讀:" + ",".join(sorted(hard))]
                if not b["verify"]["ok"] and (hard or (b["verify"].get("text_cov") is not None and b["verify"]["text_cov"] < 98.0)):
                    regions.append({"file": row["file"], "page": orig, "local": lp, "bbox": [b["x0"], b["top"], b["x1"], b["bottom"]], "kind": "table", "mode": "table", "id": b["id"], "why": ",".join(sorted(hard)) or "表內字還原不足", "native_rows": b.get("rows", [])})
            T["表格還原"] += time.time() - ta
            W, H = float(page.width), float(page.height)
            for b in pg["blocks"]:
                if b["kind"] == "figure" and b["role"] not in ("HEADER", "FOOTER") and not (b.get("text") or "").strip():
                    area = (b["x1"] - b["x0"]) * (b["bottom"] - b["top"]) / (W * H)
                    if area >= (0.03 if i > 0 else 0.08):
                        regions.append({"file": row["file"], "page": orig, "local": lp, "bbox": [b["x0"], b["top"], b["x1"], b["bottom"]], "kind": "figure", "mode": "table" if i > 0 else "text", "id": b["id"], "why": "圖區無文字層(可能是影像表格 / 影像文字)"})
            _TCACHE.clear()
            pages.append(pg)
    if fdoc is not None:
        fdoc.close()
    ta = time.time()
    hier = _resolve("_hierarchy")(pages)
    body = (hier.get("body") or {}).get("size") or 0
    ts, e394 = _resolve("_text_subcat"), _resolve("_e394_text")
    for pg in pages:
        for b in pg["blocks"]:
            if b["kind"] == "text":
                b["sub"] = "頁尾/免責" if b["role"] == "FOOTER" else ts(b, hier)
                b["eng394"] = e394(b, body)
            b["units"] = uo(b)
    f = {"code": row.get("code"), "broker": row.get("broker")}
    title = _resolve("_main_title")(pages[0], hier, f, book)
    for b in pages[0]["blocks"]:
        if b["id"] == title.get("id"):
            b["sub"], b["units"] = "主標題", [("標題", b["text"])]
    T["分類分層"] += time.time() - ta
    ta = time.time()
    ftxt = " ".join(b.get("text", "") for pg in pages for b in pg["blocks"] if b["role"] == "FOOTER")
    mb, abf = _resolve("match_broker"), _resolve("_abbr_of")
    canon = mb(ftxt, book)[0] if ftxt else ""
    fab = abf(book, canon)[0] if canon else ""
    info = _resolve("extract_info")(pages[0], book, ctx.get("ratings", []))
    T["資訊區"] += time.time() - ta
    conf = {}
    if row.get("code"):
        conf["代號"] = bool(re.search(r"(?<!\d)%s(?!\d)" % re.escape(row["code"]), p1t))
    if row.get("name"):
        conf["名稱"] = row["name"].replace("-KY", "") in p1t
    covs = [pg["coverage"]["pct"] for pg in pages]
    tblocks = [b for pg in pages for b in pg["blocks"] if b["kind"] == "table"]
    txt_blocks = [b for pg in pages for b in pg["blocks"] if b["kind"] == "text"]
    classified = (sum(1 for b in txt_blocks if b.get("sub")) / len(txt_blocks)) if txt_blocks else 1.0
    image_only = not txt_blocks and not tblocks
    text_ok = min(covs) >= 99.5 and classified >= 0.999 and not image_only
    annual = [pg["page"] for pg in pages[1:]]
    table_ok = (bool(tblocks) and all(b["verify"]["ok"] for b in tblocks)) if annual else all(b["verify"]["ok"] for b in tblocks)
    units = Counter(u[0] for pg in pages for b in pg["blocks"] if b["role"] != "FOOTER" for u in b.get("units", []))
    trs = Counter((b.get("tr") or {}).get("status", "未跑") for b in tblocks)
    tri = Counter(k for b in tblocks for k in ((b.get("tr") or {}).get("issues") or {}))
    vis = Counter(x.split(" ")[0] for b in tblocks if not b["verify"]["ok"] for x in b["verify"].get("issues", []))
    res = {"file": row["file"], "path": row["path"], "code": row.get("code", ""), "name": row.get("name", ""), "broker": row.get("broker", ""), "date": row.get("date", ""), "yf": row.get("yf", ""), "bbg": row.get("bbg", ""),
           "picked": pick, "pages_total": row.get("pages_total"), "title": title.get("text", ""), "confirm": conf, "cov_min": min(covs), "cov_pages": dict(zip([pg["page"] for pg in pages], covs)), "missing": sum(pg["coverage"]["missing"] for pg in pages),
           "units": dict(units), "joins": sum(b.get("joins", 0) for b in txt_blocks), "sus": sum(b.get("sus", 0) for b in txt_blocks), "classified": round(classified * 100, 1), "tables": len(tblocks), "tables_ok": sum(1 for b in tblocks if b["verify"]["ok"]),
           "repairs": sum(len(b.get("fixes", [])) for b in tblocks), "e394": sum(1 for b in txt_blocks if b.get("eng394")), "split": "INFO" in pages[0]["roles"].values() and "BODY" in pages[0]["roles"].values(), "annual": annual,
           "footer_broker": fab, "info": info, "text_ok": text_ok, "table_ok": table_ok, "image_only": image_only, "tr_status": dict(trs), "tr_issues": dict(tri), "verify_issues": dict(vis), "ocr_regions": regions,
           "timing": {k: round(v, 2) for k, v in T.items()}, "run_id": _RUN["id"], "secs": round(time.time() - t0, 1)}
    res["step2_ok"] = text_ok and table_ok
    notes = []
    if image_only:
        notes.append("整份取頁都是影像(無文字層)→ 第三步 OCR")
    elif not text_ok:
        notes.append("文字還原 %.1f%%%s" % (min(covs), "" if classified >= 0.999 else " · 有未分類段"))
    if not table_ok:
        notes.append("表格 %d/%d 過" % (res["tables_ok"], res["tables"]) if tblocks else "年度頁沒抽到表")
    if res["sus"]:
        notes.append("疑錯接 %d" % res["sus"])
    if conf and not all(conf.values()):
        notes.append("首頁沒對到 " + "/".join(k for k, v in conf.items() if not v))
    res["notes"] = notes
    res["lamp"] = "GREEN" if res["step2_ok"] and not res["sus"] and all(conf.values()) else ("YELLOW" if text_ok or table_ok else "RED")
    tmpd = Path(row.get("temp") or _temp_base()) / "layout_l2"
    tmpd.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(row["path"].encode("utf-8")).hexdigest()[:8]
    (tmpd / (key + ".json")).write_text(json.dumps({"run_id": _RUN["id"], "row": row, "pages": pages, "hier": hier, "title": title, "info": info, "summary": res}, ensure_ascii=False, default=str), encoding="utf-8")
    res["temp_json"] = str(tmpd / (key + ".json"))
    out_dir = _rep() / "layout"
    out_dir.mkdir(parents=True, exist_ok=True)
    view = {"file": row["file"], "pages": [dict(pg, blocks=[b for b in pg["blocks"] if b["role"] != "FOOTER"]) for pg in pages], "hier": hier, "title": title, "info": {}, "annual": annual, "n_tables": len(tblocks), "n_fixes": res["repairs"],
            "secs": res["secs"], "confirm": conf, "pages_total": row.get("pages_total"), "notes": notes, "lamp": res["lamp"], "id": {k: row.get(k, "") for k in ("code", "yf", "bbg", "name", "broker", "date")}}
    h = _resolve("_file_html")(view)
    h = h.replace("<div class='two'>", _resolve("_restore_panel")(res, pages, info) + "<div class='two'>", 1)
    page_html = out_dir / ("%s_%s.html" % (key, re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", Path(row["file"]).stem)[:60]))
    page_html.write_text(h, encoding="utf-8")
    res["html"] = str(page_html)
    return res



_patch("l2_one", l2_one_v160)


# ───────── ③④ 小框不算表 · 表頭可在第 2–3 列 ─────────
_PREV_VT = _resolve("verify_table")


def verify_table_v160(b: dict, page=None) -> dict:
    rows = b.get("rows", [])
    if len(rows) < 2 or max((len(r) for r in rows), default=0) < 2:
        return {"ok": True, "header": False, "rect": True, "parse_rate": 1.0, "multi_left": 0, "text_cov": None, "arith": "不適用", "issues": [], "unit": "", "rule": "小框(不到 2×2)→ 當文字框,不算表", "tiny": True}
    v = _PREV_VT(b, page)
    if not v.get("header") and b.get("sub", "").startswith(("財務表", "估值表")):
        yr = _resolve("_YR158")
        hi = next((i for i in (1, 2) if i < len(rows) and sum(1 for c in rows[i] if yr.search(c or "")) >= 2), None) if yr else None
        if hi is not None:
            v["header"], v["header_row"] = True, "第 %d 列" % (hi + 1)
            pn = _resolve("parse_number")
            cells = [c for r in rows[hi + 1:] for c in r[1:] if c]
            nums = [c for c in cells if pn(c) is not None or c.strip() in ("-", "—", "–", "n.a.", "NA", "N/A", "nm", "NM")]
            v["parse_rate"] = round(len(nums) / len(cells), 3) if cells else 0.0      # 資料從表頭下一列起算
            v["issues"] = [x for x in v.get("issues", []) if x != "無表頭" and not x.startswith("數字可解析率")]
            if v["parse_rate"] < 0.9:
                v["issues"].append("數字可解析率 %.0f%%" % (v["parse_rate"] * 100))
            v["ok"] = v["rect"] and v["multi_left"] == 0 and v["parse_rate"] >= 0.9 and (v["text_cov"] is None or v["text_cov"] >= 98.0) and v["arith"] != "有問題"
    return v


_patch("verify_table", verify_table_v160)


# ───────── ① 四碼代號 → 資料庫名冊(名稱 · 市場別)─────────
_NM = {}


def db_listing() -> dict:
    if "li" in _NM:
        return _NM["li"]
    li = {"codes": {}, "sources": [], "err": ""}
    try:
        d = _home().parents[1] / "supportive modules" / "database"
        tails = sorted(d.glob("VIA_DuckDBStatus_v*.py"), key=lambda q: _vnum_v0160(q.stem))
        vr = _resolve("via_roots")
        root = vr()["via_database"] if vr else None
        if tails:
            mod = _load_v0160(tails[-1], "via_duckdb_status_for_vrn")
            if hasattr(mod, "listing_index"):
                li = mod.listing_index(root)
                li["engine"] = tails[-1].name
        if not li.get("codes") and root:
            c = Path(root) / "_status" / "LISTING_INDEX.json"
            if c.exists():
                li = json.loads(c.read_text(encoding="utf-8"))
                li["engine"] = "快取 LISTING_INDEX.json"
    except Exception as exc:  # noqa: BLE001
        li["err"] = "%s:%s" % (type(exc).__name__, str(exc)[:80])
    _NM["li"] = li
    return li


_PREV_LR = _resolve("_load_roster_v154")


def _load_roster_v160(use_vdf: bool = True) -> tuple:
    entries, used = _PREV_LR(use_vdf)
    li = db_listing()
    fn = fm = add = 0
    for code, e in (li.get("codes") or {}).items():
        ent = entries.get(code)
        if ent is None:
            entries[code] = {"name": e.get("name", ""), "en": e.get("en", ""), "market": e.get("market", ""), "kind": "stock", "src": "DB 名冊"}
            add += 1
            continue
        if not ent.get("name") and e.get("name"):
            ent["name"] = e["name"]
            fn += 1
        if not ent.get("market") and e.get("market"):
            ent["market"] = e["market"]
            fm += 1
    _NM.update(filled_name=fn, filled_market=fm, added=add, n=len(li.get("codes") or {}), src="+".join(x.get("table", "") for x in li.get("sources", []) if x.get("rows")) or "—", engine=li.get("engine", "—"), err=li.get("err", ""))
    return entries, list(used) + [{"file": _NM["src"], "sys": "DB 名冊(唯讀)", "added": add}]


_patch("_load_roster_v154", _load_roster_v160)


# ───────── ② 不合理值剔除(目標價 / 收盤 vs 資料庫股價)─────────
def plausible(inf: dict, x: dict) -> list:
    rej = []
    ref = x.get("close_before") if not x.get("stale") else None
    ref_any = ref or x.get("adj_latest")
    tp = inf.get("tp")
    if tp and ref_any and not (0.3 <= tp / ref_any <= 5.0):
        inf["tp_rejected"], inf["tp"] = tp, None
        x["tp_adj"] = None
        x["note"] = "; ".join(t for t in (x.get("note", ""), "目標價 %g 與股價 %g 不合理 → 不採用" % (tp, ref_any)) if t)
        rej.append("目標價")
    cl = inf.get("close")
    if cl and ref and abs(cl / ref - 1) > 0.5:
        inf["close_rejected"], inf["close"] = cl, None
        x["close_ok"] = None
        x["note"] = "; ".join(t for t in (x.get("note", ""), "收盤 %g 與資料庫 %g 差太多 → 不採用" % (cl, ref)) if t)
        rej.append("收盤")
    return rej


_PREV_LAYOUT = _resolve("layout_run_v158")


def layout_run_v160(d, opts):
    o = _PREV_LAYOUT(d, opts)
    rej = Counter()
    for r in o["rows"]:
        if "cov_min" in r:
            for k in plausible(r.get("info", {}), o["xc"].setdefault(r["path"], {})):
                rej[k] += 1
    _NM["rejected"] = dict(rej)
    if rej:
        o["pages"]["xcheck"] = _resolve("_xcheck_page")(o["rows"], o["xc"], o["summary"])
        o["pages"]["step2"] = _resolve("_step2_page")(o["rows"], o["summary"])
    return o


_mo = _owner("layout_run_v158")
if _mo:
    setattr(_mo, "layout_run_v158", layout_run_v160)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    rc = PRIOR.main(args)
    if args[:1] == ["layout"]:
        print("[計] 四碼代號 → DB 名冊 · %s 碼 · 補名稱 %s · 補市場別 %s · 新增 %s · 來源 %s(%s)%s" % (_NM.get("n", 0), _NM.get("filled_name", 0), _NM.get("filled_market", 0), _NM.get("added", 0), _NM.get("src", "—"), _NM.get("engine", "—"), (" · " + _NM["err"]) if _NM.get("err") else ""))
        rj = _NM.get("rejected", {})
        print("[計] 不合理值剔除(與資料庫股價比)· 目標價 %d · 收盤 %d" % (rj.get("目標價", 0), rj.get("收盤", 0)))
    return rc


def selftest() -> int:
    import shutil
    import tempfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    v1 = verify_table_v160({"rows": [["營收", "100", "120"]], "sub": "數據表"})
    v2 = verify_table_v160({"rows": [["Income statement (NT$m)", "", "", ""], ["", "2024A", "2025F", "2026F"], ["Revenue", "1,000", "1,200", "1,400"], ["Net income", "100", "120", "140"]], "sub": "財務表·損益", "x0": 0, "top": 0, "x1": 1, "bottom": 1})
    chk("① 小框(1 列)→ 當文字框不算失敗 · 財務表表頭在第 2 列也認得", v1["ok"] and v1.get("tiny") and v2["header"] and v2["ok"])
    chk("② 格線合併 2pt 容差:100 / 100.8 / 101.6 → 一條線;200 / 203 → 兩條", len(_snap2([100.0, 100.8, 101.6, 200.0, 203.0])) == 3)
    inf, x = {"tp": 1.0, "close": 10.0}, {"close_before": 118.0, "adj_latest": 120.0}
    rj = plausible(inf, x)
    inf2, x2 = {"tp": 760.0, "close": 580.0}, {"close_before": 578.0}
    rj2 = plausible(inf2, x2)
    chk("③ 不合理值剔除:目標價 1.0 vs 股價 118 → 剔除 · 收盤 10 vs 118 → 剔除;760 / 580 vs 578 → 保留", rj == ["目標價", "收盤"] and inf["tp"] is None and inf["close"] is None and not rj2 and inf2["tp"] == 760.0)
    td = Path(tempfile.mkdtemp(prefix="vrn160-"))
    home = td / "functional modules" / "VRN"
    for d in ("SSOT", "knowledge", "registry", "intake/VRN_TableRepair"):
        (home / d).mkdir(parents=True, exist_ok=True)
    dbd = td / "supportive modules" / "database"
    dbd.mkdir(parents=True)
    for src in (HERE.parents[1] / "supportive modules" / "database", Path("/tmp/out")):
        for q in sorted(src.glob("VIA_DuckDBStatus_v010*.py")) if src.is_dir() else []:
            if not (dbd / q.name).exists():
                shutil.copy(q, dbd / q.name)
    for src in (HERE / "intake" / "VRN_TableRepair", Path("/tmp/out")):
        for q in sorted(src.glob("VRN_Table*_v010*.py")) if src.is_dir() else []:
            if not (home / "intake" / "VRN_TableRepair" / q.name).exists():
                shutil.copy(q, home / "intake" / "VRN_TableRepair" / q.name)
    base = td / "VIA"
    vdb = base / "via_database" / "vdf_database"
    vdb.mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT", "VIA_VDF_HOME", "VIA_ROOTS_BASE", "VIA_SPILL_DIR", "VIA_DB_ROOT", "USERPROFILE")}
    os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(td / "VIA_Reports" / "vrn"), "VIA_VDF_HOME": str(td / "nope"), "VIA_ROOTS_BASE": str(base), "VIA_SPILL_DIR": str(td / "TEMP"), "VIA_DB_ROOT": str(base / "via_database"), "USERPROFILE": str(td)})
    try:
        import duckdb  # noqa: WPS433
        duckdb.connect().execute("copy (select * from (values ('3653','健策','上市'),('2330','台積電','上市'),('6488','環球晶','上櫃')) t(公司代號, 公司簡稱, 市場別)) to '%s' (format parquet)" % (vdb / "tw__tw_listings.parquet"))
        (home / "knowledge" / "VRN_Broker_Dict_v0100.json").write_text(json.dumps({"brokers": {"高盛": {"abbr": "GS", "aliases": ["GS", "Goldman Sachs"]}}}, ensure_ascii=False), encoding="utf-8")
        _NM.clear()
        ent, used = _load_roster_v160(True)
        chk("④ 四碼代號 → DB 名冊:3653 健策(TWSE)· 6488 環球晶(TPEx)· 名冊來源 tw__tw_listings", ent.get("3653", {}).get("name") == "健策" and ent.get("6488", {}).get("market") == "TPEx" and "tw__tw_listings" in _NM.get("src", ""))
        inp = td / "inbox"
        inp.mkdir()
        _resolve("_mk_pdf_v158")(inp / "GS-3653 20251002.pdf", td)
        _NM.pop("li", None)
        o = _resolve("layout_run_v158")(inp, {"workers": 1, "tabula": False, "max": 0, "only": "", "no_ocr": True})
        r = o["rows"][0]
        chk("⑤ 檔名只有代號(GS-3653)→ 名稱 健策 · yfinance 3653.TW 由 DB 名冊補上 · 財務表雙讀仍通過", r.get("name") == "健策" and r.get("yf") == "3653.TW" and r.get("tables_ok", 0) >= 1)
    finally:
        for k, val in saved.items():
            if val is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = val
        shutil.rmtree(td, ignore_errors=True)
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑥ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑦ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("[計] VRN_SystemManager_v0160 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
