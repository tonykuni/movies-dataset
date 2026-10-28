#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0163 — 薄尾(操作員 2026-10-10):依 GitHub 成功紀錄調配工具(v0108 年度包 · FirstPageEngine v0130 · LocalDispatcher v0104 · TableRouter v0101)。
  layout:
    ① 藏在文字中的表格:沿用已驗證的 ReportRestore v0101 文字幾何(geometry_rows · infer_column_edges)→ 文字行裡對齊的數字欄還原成表(唯讀載入,找不到 = 不做不壞)
    ② TableRouter 律:每張表先單讀驗證,只有單讀沒過的財務 / 估值表才動 TableRepair 雙讀(最少資源)
    ③ 文件預算(LocalDispatcher 同律 300 秒,VIA_VRN_DOC_BUDGET 可調):超過 → 停下剩下的頁 / 表、記失敗(跑太慢也算失敗)
    ④ 工具效益帳:每表記工具 · 毫秒 · 過否 → TEMP\\VRN_ToolStats_Ledger.jsonl + [計] 工具效益(依實績調配)
  curate(via_02_vrn = 重新建立的獨立 VRN):
    ⑤ SSOT / 正則 / 同義字 聯集整合:同族多版 → 新版號一冊(鍵合併 · 清單依鍵或值去重 · 純值新為準)· 一筆不丟;衝突舊值、一字多主、壞正則寫在 <冊>.integration.json 待裁
    ⑥ 真刪改「先壓縮歸檔、驗證過才刪」:_retired → _archive\\VRN02_retired_<時間>.zip
    ⑦ references\\VRN_SuccessReference_v0100.md(GitHub 成功紀錄邏輯與版本)+ VRN_ToolRecipe_v0100.json(工具調配配方)
    ⑧ 成功紀錄的工具(ReportRestore v0101 · TableRouter v0101 · LocalDispatcher v0104)補進 02_engines\\reference_v0108(唯讀參考)
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
import shutil
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0163"


def _vnum_v0163(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0163(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0163(p) < _vnum_v0163(__file__)), key=_vnum_v0163)
PRIOR = _load_v0163(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    return _resolve("_init_entry")(*args)


_home, _rep, _temp_base = _resolve("_home"), _resolve("_rep"), _resolve("_temp_base")
tablerepair = _resolve("tablerepair")
tr_check_v160 = _resolve("tr_check_v160")
_TR_SOFT, _TR_OCR, _TCACHE, _RUN = _resolve("_TR_SOFT"), _resolve("_TR_OCR"), _resolve("_TCACHE"), _resolve("_RUN")


# ───────── ① 藏在文字中的表格:ReportRestore v0101 文字幾何(geometry_rows · infer_column_edges)─────────
_RR = {}
_NUMTOK3 = re.compile(r"[\(\-−]?\d[\d,]*(?:\.\d+)?\)?%?")


def _rr_cands() -> list:
    cands = []
    env = os.environ.get("VIA_VRN_REPORTRESTORE")
    if env:
        cands.append(Path(env))
    home = _home()
    cands += sorted(home.glob("intake/*/*/pack/engine/tools/VRN_ReportRestore_v0*.py")) + sorted(home.glob("02_engines/reference_v0108/VRN_ReportRestore_v0*.py"))
    cands += sorted(home.parent.glob("02_engines/reference_v0108/VRN_ReportRestore_v0*.py"))
    return [c for c in cands if c.is_file()]


def _rr():
    """載入已驗證的 ReportRestore v0101(v0108 交接包工具;唯讀使用)。找不到 = 不做,不壞。"""
    if "mod" in _RR:
        return _RR["mod"]
    mod, src = None, ""
    for c in _rr_cands():
        if c.is_file():
            try:
                mod = _load_v0163(c, "vrn_reportrestore_ref")
                if hasattr(mod, "geometry_rows") and hasattr(mod, "infer_column_edges"):
                    src = str(c)
                    break
            except Exception as exc:  # noqa: BLE001
                _RR["err"] = "%s:%s" % (type(exc).__name__, str(exc)[:80])
                mod = None
    _RR.update(mod=mod, src=src)
    return mod


_FZ = {}


def _fitz_page(path: str, pno: int):
    import fitz  # noqa: WPS433
    if _FZ.get("path") != path:
        if _FZ.get("doc") is not None:
            try:
                _FZ["doc"].close()
            except Exception:  # noqa: BLE001
                pass
        _FZ.update(path=path, doc=fitz.open(path))
    return _FZ["doc"][pno - 1]


def hidden_tables(p: dict, pdf_path: str, pno: int) -> int:
    rr = _rr()
    if rr is None:
        return 0
    cand = [b for b in p.get("blocks", []) if b.get("kind") == "text" and b.get("role") == "BODY"]

    def txt(b):
        return b.get("text") or " ".join(ln.get("text", "") for ln in b.get("lines", []) if isinstance(ln, dict))
    cand = [b for b in cand if len(_NUMTOK3.findall(txt(b))) >= 2]
    cand.sort(key=lambda b: (b.get("zone", ""), b["top"]))
    groups, cur = [], []
    for b in cand:
        if cur and b.get("zone") == cur[-1].get("zone") and b["top"] - cur[-1]["bottom"] <= 2.2 * max(cur[-1].get("size") or 8, 6) and min(b["x1"], max(x["x1"] for x in cur)) > max(b["x0"], min(x["x0"] for x in cur)) - 40:
            cur.append(b)
        else:
            if cur:
                groups.append(cur)
            cur = [b]
    if cur:
        groups.append(cur)
    try:
        fpage = _fitz_page(pdf_path, pno)
    except Exception:  # noqa: BLE001
        return 0
    n = 0
    for g in groups:
        if sum(max(1, len(b.get("lines", []))) for b in g) < 3:
            continue
        bbox = [min(b["x0"] for b in g) - 2, min(b["top"] for b in g) - 2, max(b["x1"] for b in g) + 2, max(b["bottom"] for b in g) + 2]
        try:
            rows = rr.geometry_rows(fpage, bbox)
            if len(rows) < 3:
                continue
            edges, anchors = rr.infer_column_edges(rows, bbox)
        except Exception:  # noqa: BLE001
            continue
        if len(anchors) < 2:
            continue
        if sum(1 for r in rows if sum(1 for w in r["words"] if re.fullmatch(rr.NUMBER_RX, w[4], re.I)) >= 2) < 3:
            continue
        grid = []
        for r in rows:
            cells = ["" for _ in range(len(edges) - 1)]
            for w in r["words"]:
                x = (w[0] + w[2]) / 2
                ci = next((i for i in range(len(edges) - 1) if edges[i] <= x < edges[i + 1]), len(cells) - 1)
                cells[ci] = (cells[ci] + " " + w[4]).strip()
            grid.append(cells)
        keep = [j for j in range(len(edges) - 1) if any(row[j] for row in grid)]
        grid = [[row[j] for j in keep] for row in grid]
        if len(keep) < 3:
            continue
        n += 1
        tb = {"zone": g[0].get("zone"), "kind": "table", "how": "text-geometry", "x0": bbox[0], "top": bbox[1], "x1": bbox[2], "bottom": bbox[3], "rows": grid, "role": "BODY",
              "id": "%s·HT%d" % (g[0]["id"], n), "engine": "ReportRestore v0101(文字幾何)", "hidden": True, "lines": [], "text": "", "size": g[0].get("size"), "bold": False}
        ids = {id(b) for b in g}
        pos = min(i for i, b in enumerate(p["blocks"]) if id(b) in ids)
        p["blocks"] = [b for b in p["blocks"] if id(b) not in ids]
        p["blocks"].insert(pos, tb)
    p["hidden_tables"] = n
    return n


_PREV_AP163 = _resolve("analyze_page")


def analyze_page_v163(pdf, pno: int, pdf_path: str, annual: bool, tabula_ok: bool) -> dict:
    p = _PREV_AP163(pdf, pno, pdf_path, annual, tabula_ok)
    try:
        hidden_tables(p, pdf_path, pno)
    except Exception as exc:  # noqa: BLE001
        p["hidden_err"] = "%s:%s" % (type(exc).__name__, str(exc)[:80])
    return p


_ma = _owner("analyze_page")
if _ma:
    setattr(_ma, "analyze_page", analyze_page_v163)


def _doc_budget() -> int:
    try:
        return int(os.environ.get("VIA_VRN_DOC_BUDGET") or 300)
    except ValueError:
        return 300


def l2_one_v163(row: dict) -> dict:
    import pdfplumber
    T = Counter()
    t0 = time.time()
    budget = _doc_budget()
    tools, timed_out = [], False
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
            if i > 0 and time.time() - t0 > budget:         # v0163:文件預算(LocalDispatcher 300 秒同律)→ 超時停、記失敗(首頁一定跑完)
                timed_out = True
                break
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
                tt = time.time()
                b["page"] = orig
                if time.time() - t0 > budget:
                    timed_out = True
                    b.setdefault("rows", b.get("rows") or [])
                    b["sub"] = b.get("sub") or "未分類"
                    b["verify"] = {"ok": False, "issues": ["逾時(文件預算 %d 秒)" % budget], "rect": False, "header": False, "parse_rate": 0.0, "multi_left": 0, "text_cov": None, "arith": "未跑"}
                    tools.append({"page": orig, "table": b["id"], "sub": b["sub"], "tool": "逾時略過", "ms": 0, "ok": False})
                    continue
                rr = rpt(b, page)
                b["rows"], b["fixes"] = rr["rows"], rr["fixes"]
                b["sub"] = tcat(b["rows"], b["role"])
                b["verify"] = vt(b, page)                    # v0163:TableRouter 律 —— 單一引擎先驗
                tool = "文字幾何(ReportRestore v0101)" if b.get("how") == "text-geometry" else "單讀(pdfplumber)"
                fin = b["sub"].startswith(("財務表", "估值表"))
                if fin and not b["verify"]["ok"] and fdoc is not None:       # 單讀沒過才動雙讀
                    if not wread:
                        wread = True
                        try:
                            words, other = tr["geo"].def_read_page(fdoc[lp - 1], page)
                        except Exception:  # noqa: BLE001
                            words = None
                    if words is not None:
                        tool += " → 雙讀(TableRepair)"
                        neigh = [[x["x0"], x["top"], x["x1"], x["bottom"]] for x in tbls if x is not b]
                        trr = tr_check_v160(fdoc[lp - 1], page, (b["x0"], b["top"], b["x1"], b["bottom"]), words, other, neigh)
                        b["tr"] = trr
                        if trr and trr.get("rows") and (trr.get("status") == "PASS" or set(trr.get("issues", {})) <= _TR_SOFT):
                            if len(trr["rows"]) >= len(b.get("rows") or []):
                                b["rows"], b["engine"] = trr["rows"], "TableRepair(雙讀一致)"
                                b["sub"] = tcat(b["rows"], b["role"])
                                b["verify"] = vt(b, page)
                            else:
                                trr["note"] = "雙讀格線少 %d 列 → 保留 pdfplumber 列" % (len(b.get("rows") or []) - len(trr["rows"]))
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
                tools.append({"page": orig, "table": b["id"], "sub": b["sub"], "tool": tool, "ms": int((time.time() - tt) * 1000), "ok": bool(b["verify"]["ok"])})
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
           "timing": {k: round(v, 2) for k, v in T.items()}, "run_id": _RUN["id"], "secs": round(time.time() - t0, 1), "tools": tools, "timeout": timed_out, "budget": budget,
           "hidden_tables": sum(1 for b in tblocks if b.get("how") == "text-geometry")}
    res["step2_ok"] = text_ok and table_ok
    notes = []
    if image_only:
        notes.append("整份取頁都是影像(無文字層)→ 第三步 OCR")
    elif not text_ok:
        notes.append("文字還原 %.1f%%%s" % (min(covs), "" if classified >= 0.999 else " · 有未分類段"))
    if timed_out:
        notes.append("逾時(文件預算 %d 秒)→ 這份記失敗,剩下的頁 / 表沒跑" % budget)
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




_PREV_L2 = _resolve("l2_one")


def l2_one_router(row: dict) -> dict:
    """VIA_VRN_ROUTER=legacy → 前版流程(雙讀先於驗證;給前版自測驗前版行為);預設 = v0163 單讀先 · 預算 · 工具帳。"""
    if os.environ.get("VIA_VRN_ROUTER") == "legacy":
        return _PREV_L2(row)
    return l2_one_v163(row)


_patch("l2_one", l2_one_router)


# ───────── ② 工具效益帳(每表:用了哪個工具 · 毫秒 · 過沒過)→ 依實績調配 ─────────
_PREV_LAYOUT163 = _resolve("layout_run_v158")


def layout_run_v163(d, opts):
    o = _PREV_LAYOUT163(d, opts)
    agg = defaultdict(lambda: {"n": 0, "ok": 0, "ms": 0})
    for r in o["rows"]:
        for t in r.get("tools", []) or []:
            a = agg[t["tool"]]
            a["n"] += 1
            a["ok"] += 1 if t["ok"] else 0
            a["ms"] += t["ms"]
    _ST163["tools"] = {k: dict(v, avg_ms=int(v["ms"] / max(v["n"], 1)), rate=round(100.0 * v["ok"] / max(v["n"], 1), 1)) for k, v in agg.items()}
    _ST163["timeouts"] = sum(1 for r in o["rows"] if r.get("timeout"))
    _ST163["hidden"] = sum(r.get("hidden_tables", 0) for r in o["rows"])
    _ST163["budget"] = _doc_budget()
    rc = _rr_cands()
    _ST163["rr"] = str(rc[0]) if rc else "— 找不到 ReportRestore v0101(v0108 交接包工具)"
    led = _temp_base() / "VRN_ToolStats_Ledger.jsonl"
    try:
        led.parent.mkdir(parents=True, exist_ok=True)
        with led.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "tools": _ST163["tools"], "timeouts": _ST163["timeouts"], "hidden": _ST163["hidden"]}, ensure_ascii=False) + "\n")
    except OSError:
        pass
    return o


_ST163 = {}
_ml = _owner("layout_run_v158")
if _ml:
    setattr(_ml, "layout_run_v158", layout_run_v163)


# ───────── ③ curate:SSOT / 正則 / 同義字 聯集整合(一筆不丟)· 真刪改「壓縮歸檔後刪」· 參考卡 ─────────
_META = {"version", "ts", "generated", "generated_at", "updated", "schema_version", "batch", "book_edited", "created", "prior", "built_at",
         "origin", "rule", "note", "notes", "description", "changelog", "purpose", "summary", "comment"}
_GROUP_KEYS = ("std", "canonical", "canon", "key", "id", "code", "term", "metric", "label", "pattern", "name")
_CAT_KEYS = ("cat", "category", "type", "kind", "section")
_C162 = _owner("curate")                                    # v0162 模組(curate 的家)


def _group_fields(items: list):
    """清單分組鍵:九成以上元素都有的正典欄(std / canonical / key / id / term …);有分類欄(cat / type …)就組合 → 同組合併。"""
    ds = [x for x in items if isinstance(x, dict)]
    if not ds or len(ds) < 0.9 * len(items):
        return None
    for k in _GROUP_KEYS:
        if sum(1 for x in ds if isinstance(x.get(k), (str, int))) >= 0.9 * len(ds):
            c = next((c for c in _CAT_KEYS if c != k and sum(1 for x in ds if isinstance(x.get(c), (str, int))) >= 0.9 * len(ds)), None)
            return (k, c)
    return None


def _gk(x: dict, kf: tuple) -> tuple:
    return (str(x.get(kf[0])), str(x.get(kf[1])) if kf[1] else "")


def deep_union(a, b, path: str, conflicts: list, stats: dict | None = None):
    """b 較新:dict 鍵聯集 · 清單依正典鍵分組合併(別名清單取聯集,一個不丟;同冊內同組重複且純值一致 → 合一列)· 純值以新為準,不同記衝突(舊值留帳)。"""
    stats = stats if stats is not None else {}
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(a)
        for k, v in b.items():
            out[k] = deep_union(a[k], v, "%s.%s" % (path, k), conflicts, stats) if k in a else v
        return out
    if isinstance(a, list) and isinstance(b, list):
        kf = _group_fields(a + b)
        if kf:
            out, origin, idx = [], [], {}
            for tag, lst in (("a", a), ("b", b)):
                for x in lst:
                    if not isinstance(x, dict) or kf[0] not in x:
                        if x not in out:
                            out.append(x)
                            origin.append(tag)
                        continue
                    g = _gk(x, kf)
                    if g in idx:
                        i = idx[g]
                        loc = []
                        merged = deep_union(out[i], x, "%s[%s]" % (path, "/".join(v for v in g if v)), loc, stats)
                        if loc and (origin[i] == tag or x in out):  # 同一冊內兩列同組但純值打架 → 不合,列疑似重複(已有一模一樣的列就不再加)
                            if x not in out:
                                stats.setdefault("suspect", []).append({"path": path, "group": list(g), "conflicts": loc[:3]})
                                out.append(x)
                                origin.append(tag)
                            continue
                        if merged != out[i]:
                            stats["merged"] = stats.get("merged", 0) + 1
                        elif origin[i] == tag:
                            stats["dup_removed"] = stats.get("dup_removed", 0) + 1
                        out[i] = merged
                        origin[i] = tag
                        conflicts.extend(loc)
                    else:
                        idx[g] = len(out)
                        out.append(x)
                        origin.append(tag)
            return out
        seen, out = set(), []
        for x in a + b:
            s_ = json.dumps(x, sort_keys=True, ensure_ascii=False)
            if s_ not in seen:
                seen.add(s_)
                out.append(x)
        return out
    if a != b and path.split(".")[-1].split("[")[0] not in _META:
        conflicts.append({"path": path, "older": a, "newer": b, "kept": "newer"})
    return b


def restored_from_older(u, tail, path: str = "$") -> list:
    """聯集比尾版多出的東西(舊版有、尾版沒有)→ 列給操作員判斷是誤刪(補回對)還是刻意刪(要再刪)。"""
    out = []
    if isinstance(u, dict) and isinstance(tail, dict):
        for k, v in u.items():
            if k in _META:
                continue
            if k not in tail:
                out.append({"path": "%s.%s" % (path, k), "added": str(v)[:120]})
            else:
                out += restored_from_older(v, tail[k], "%s.%s" % (path, k))
    elif isinstance(u, list) and isinstance(tail, list):
        kf = _group_fields(u + tail)
        if kf:
            tm = defaultdict(lambda: defaultdict(set))
            for x in tail:
                if isinstance(x, dict):
                    for fk, fv in x.items():
                        if isinstance(fv, list):
                            tm[_gk(x, kf)][fk].update(json.dumps(e, ensure_ascii=False) for e in fv)
            for x in u:
                if not isinstance(x, dict):
                    continue
                g = _gk(x, kf)
                if g not in tm:
                    out.append({"path": path, "group": list(g), "added": "整列(尾版沒有這一組)"})
                    continue
                for fk, fv in x.items():
                    if isinstance(fv, list):
                        extra = [e for e in fv if json.dumps(e, ensure_ascii=False) not in tm[g][fk]]
                        if extra:
                            out.append({"path": path, "group": list(g), "field": fk, "added": extra[:10]})
        else:
            ts = {json.dumps(e, sort_keys=True, ensure_ascii=False) for e in tail}
            out += [{"path": path, "added": str(e)[:120]} for e in u if json.dumps(e, sort_keys=True, ensure_ascii=False) not in ts][:50]
    return out[:300]


def _strip_meta(x):
    if isinstance(x, dict):
        return {k: _strip_meta(v) for k, v in x.items() if k not in _META}
    if isinstance(x, list):
        return [_strip_meta(v) for v in x]
    return x


def synonym_conflicts(d) -> list:
    """同義字一字多主:{正典: [別名…]} 型的字典裡,同一個別名掛在兩個以上正典 → 列待裁(不自動改)。"""
    out = []

    def walk(x, path):
        if isinstance(x, dict):
            if x and all(isinstance(v, (list, dict)) for v in x.values()):
                amap = defaultdict(set)
                for canon, v in x.items():
                    al = v if isinstance(v, list) else (v.get("aliases") if isinstance(v.get("aliases"), list) else [])
                    for a in al:
                        if isinstance(a, str) and a.strip():
                            amap[a.strip().lower()].add(canon)
                for a, cs in amap.items():
                    if len(cs) > 1:
                        out.append({"path": path, "alias": a, "canonicals": sorted(cs)})
            for k, v in x.items():
                walk(v, "%s.%s" % (path, k))
    walk(d, "$")
    return out[:200]


def bad_regex(d) -> list:
    out = []

    def walk(x, path, rxctx):
        if isinstance(x, dict):
            for k, v in x.items():
                walk(v, "%s.%s" % (path, k), rxctx or bool(re.search(r"(?i)regex|pattern|rx$|_rx|re$", str(k))))
        elif isinstance(x, list):
            for i, v in enumerate(x):
                walk(v, "%s[%d]" % (path, i), rxctx)
        elif rxctx and isinstance(x, str):
            try:
                re.compile(x)
            except re.error as exc:
                out.append({"path": path, "regex": x[:120], "err": str(exc)[:60]})
    walk(d, "$", False)
    return out[:100]


_PREV_DECIDE = vars(_C162)["decide"] if _C162 else None


def decide_v163(rows: list) -> list:
    rows = _PREV_DECIDE(rows)
    fam_v = vars(_C162)["fam_ver"]
    groups = defaultdict(list)
    for r in rows:
        if r.get("ext") == ".json" and r.get("role") in ("SSOT", "REGISTRY", "RULE") and r.get("_json") is not None and not r.get("virtual") and not r.get("copy") and not r["name"].endswith(".integration.json") and ".integration_v" not in r["name"]:
            groups[(r["fam"], str(Path(r["rel"]).parent))].append(r)
    for (fam, folder), grp in groups.items():
        live = [r for r in grp if r["action"] != "退役" or r["why"].startswith(("舊版", "舊冊"))]
        if not live:
            continue
        live.sort(key=lambda r: (r["ver"], r["mtime"]))
        conflicts, stats = [], {}
        u = live[0]["_json"]
        for r in live[1:] if len(live) > 1 else live:               # 單版也做:同冊內重複列合併
            u = deep_union(u, r["_json"], "$", conflicts, stats)
        tail = live[-1]
        if _strip_meta(u) == _strip_meta(tail["_json"]):
            continue                                                # 尾版已含全部且無冊內重複 → 不出新版
        nv = max(r["ver"] for r in grp) + 1 if max(r["ver"] for r in grp) >= 0 else 100
        new_rel = (Path(folder) / ("%s_v%04d.json" % (fam, nv))).as_posix()
        syn = synonym_conflicts(u)
        brx = bad_regex(u)
        rest = restored_from_older(u, tail["_json"])
        for r in live:
            r["action"], r["why"] = "退役", "已併入整合新版 %s(聯集 · 一筆不少)" % Path(new_rel).name
        rows.append({"rel": new_rel, "name": Path(new_rel).name, "ext": ".json", "size": 0, "mtime": 0, "sha": "", "fam": fam, "ver": nv, "copy": False, "role": tail["role"], "card": {"doc": "整合新版"}, "virtual": True,
                     "action": "整合新版", "why": "聯集 %d 版 · 同組合併 %d · 冊內重複併 %d · 疑似重複待裁 %d · 從舊版補回 %d · 衝突 %d · 一字多主 %d · 壞正則 %d" % (len(live), stats.get("merged", 0), stats.get("dup_removed", 0), len(stats.get("suspect", [])), len(rest), len(conflicts), len(syn), len(brx)),
                     "doc": "整合新版 · %d 版 · 合併 %d · 補回 %d · 衝突 %d · 一字多主 %d" % (len(live), stats.get("merged", 0), len(rest), len(conflicts), len(syn)), "_union": u,
                     "_integration": {"schema": "VIA.VRN02.Integration.v1", "from": [r["rel"] for r in live], "merged_groups": stats.get("merged", 0), "dup_removed": stats.get("dup_removed", 0), "suspect_duplicates": stats.get("suspect", [])[:200],
                                      "restored_from_older": rest, "conflicts": conflicts[:500], "synonym_conflicts": syn, "bad_regex": brx,
                                      "rule": "聯集:鍵合併 · 清單依正典鍵(std / canonical / key …,有 cat 則組合)分組,別名清單取聯集 · 純值以新版為準;冊內同組純值打架不合併(疑似重複);補回、衝突、一字多主、壞正則列給操作員裁定"}})
    return rows


_PREV_APPLY = vars(_C162)["apply"] if _C162 else None


def apply_v163(T: Path, gp: list, rows: list, ts: str) -> dict:
    n = 0
    led = T / "_curate" / "VRN02_Curate_Ledger.jsonl"
    for r in rows:
        if r.get("action") == "整合新版" and r.get("_union") is not None:
            dst = T / r["rel"]
            if dst.exists():
                continue
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(json.dumps(r["_union"], ensure_ascii=False, indent=1), encoding="utf-8")
            dst.with_name(dst.stem + ".integration.json").write_text(json.dumps(dict(r["_integration"], ts=ts, out=r["rel"]), ensure_ascii=False, indent=1, default=str), encoding="utf-8")
            led.parent.mkdir(parents=True, exist_ok=True)
            with led.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps({"ts": ts, "op": "整合", "rel": r["rel"], "from": r["_integration"]["from"], "conflicts": len(r["_integration"]["conflicts"]), "synonym_conflicts": len(r["_integration"]["synonym_conflicts"])}, ensure_ascii=False) + "\n")
            n += 1
    res = _PREV_APPLY(T, gp, rows, ts)
    res["integrated"] = n
    return res


def purge_v163(T: Path) -> dict:
    """真刪改成「先壓縮歸檔、驗證過才刪」:_retired → _archive\\VRN02_retired_<時間>.zip(一個檔都不丟)。"""
    import zipfile
    rd = T / "_retired"
    files = [p for p in rd.rglob("*") if p.is_file()] if rd.is_dir() else []
    if not files:
        return {"files": 0, "mb": 0.0, "archive": "—"}
    ad = T / "_archive"
    ad.mkdir(parents=True, exist_ok=True)
    zp = ad / ("VRN02_retired_%s.zip" % datetime.datetime.now().strftime("%Y%m%dT%H%M%S"))
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, p.relative_to(rd).as_posix())
    with zipfile.ZipFile(zp) as z:
        ok = z.testzip() is None and len(z.namelist()) == len(files)
    size = sum(p.stat().st_size for p in files)
    if ok:
        shutil.rmtree(rd, ignore_errors=True)
    led = T / "_curate" / "VRN02_Curate_Ledger.jsonl"
    with led.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": datetime.datetime.now().isoformat(timespec="seconds"), "op": "清除(先壓縮歸檔)" if ok else "歸檔驗證失敗(未刪)", "files": len(files), "bytes": size, "archive": zp.name, "sha256": hashlib.sha256(zp.read_bytes()).hexdigest()}, ensure_ascii=False) + "\n")
    return {"files": len(files) if ok else 0, "mb": round(size / 1024 ** 2, 1), "archive": str(zp), "ok": ok}


if _C162:
    setattr(_C162, "decide", decide_v163)
    setattr(_C162, "apply", apply_v163)
    setattr(_C162, "purge", purge_v163)
    _PREV_PLAN = vars(_C162)["snapshot_plan"]

    def snapshot_plan_v163() -> list:
        plan = _PREV_PLAN()
        for name in ("VRN_ReportRestore_v0101.py", "VRN_TableRouter_v0101.py", "VRN_LocalDispatcher_v0104.py"):   # 成功紀錄的工具(唯讀參考)也帶進新 VRN
            hits = sorted(_home().glob("intake/*/*/pack/engine/**/%s" % name))
            if hits:
                plan.append(("02_engines/reference_v0108/" + name, hits[0]))
        return plan
    setattr(_C162, "snapshot_plan", snapshot_plan_v163)
    _PREV_CURATE = vars(_C162)["curate"]

    def curate_v163(T: Path, do_apply: bool = False, fill: bool = True) -> dict:
        if do_apply:
            write_refs(T)                                      # 先寫參考卡再掃描(下一輪不會因為新卡而變動)
        return _PREV_CURATE(T, do_apply=do_apply, fill=fill)
    setattr(_C162, "curate", curate_v163)


REF_MD = """# VRN02 成功紀錄參考(GitHub tonykuni/movies-dataset · 唯讀抓取 2026-10-10)

本卡只記「做成過的邏輯與版本」,不推 GitHub;母系統完成後才上船。

## A. 財報頁表格還原 —— 目前最佳:VRN v0108 年度交接包(commit 92e1f912 · 2026-10-08)
- 結果:9 份報告 · 12 個年度頁 · 43 表 · 4,415 年度格 · 來源逐格 5,462 PASS / 0 REVIEW · 年度算式 409 PASS / 0 FAIL · 品質閘 17 PASS · 單位未判定 0
- 工具(只用這些):PyMuPDF + pdfplumber + 既有 geometry / restore;**沒用 OCR / Camelot / Tabula / NLP 推論**;讀取器每份開一次、做完即關
- 版本:VRN_AnnualFinancial / AnnualLayouts / AnnualAmounts / AnnualCloseout / AnnualAudit v0108 · VRN_LocalDispatcher v0104 · VRN_ReportRestore v0101 · VRN_TableRouter v0101 · VIA_Central_Synonym_Regex v0106 · VeritasCeleritas v1141
- 關鍵做法:
  1. 依券商**鎖定版面**(GS / MS / Daiwa 校準;ReportRestore FIN_PROFILES 每份每頁裁切框)= 分群後才擷取
  2. 先選年度表與年度欄(表頭判 actual / forecast,季度排除)
  3. 逐格保留 VALUE_RAW + 座標;**不把跨欄數字拼成一格**;重複列名靠 SOURCE_ROW_INDEX
  4. 每欄用自己的字形座標比對(中文標籤與數字基線不同);fitz 與 pdfplumber 重讀比對
  5. 單位判定(貨幣 / % / 倍 / 天 / 元每股 / 百萬股)· 千元 ×0.001 · Decimal 50 位 · **全部驗算完才捨入**
  6. 表內與跨表算式(毛利 = 營收 − 成本 · 資產 = 負債 + 權益 · 各利潤率 …)· 來源缺值不可算另列,不算 PASS
- 界線:固定資料集,不是任意 PDF 自動支援;新版面要先校準

## B. 首頁(資訊區 / 文字)—— VIA_VRN_FirstPageEngine v0130(四十二檢 41 OK · 1 NODATA)
- 已付學費的規則(本系統必須沿用,不重踩):
  - 同一家券商加**別名**,不新增**正典**(CLST / CLSA)
  - 兩讀取器比**目標價**,不比原始數字袋(欄界黏字會讓數字袋互不相同)
  - 現價假值:MS 讀成 2025(日期年份)、JP / Citi 讀成 25、發佈時刻 05:30 讀成 5、「5 日漲跌幅」讀成 5;「Up/downside to price target (%)」的觸發詞要剔
  - 年份剔除要有年份跡證(真目標價可能是 2000);貨幣記號屬於後面的數,不能被前面的年份借走
  - 四碼裸代號要有邊界(檔名雜湊前綴 1379 不是代號);期間記號 2025(F) / 25Q4(F) / 26Q1(E)
  - 摘要 quote-or-abstain:原句照抄,不改寫
- 輔助:VRN_ENG086 FirstPageLogicBridge v0120 · ENG072 / ENG073 v0139 · DocStructure 列化(CATEGORY 表/圖/文 · TYPE 字體階層)

## C. 調度原則(LocalDispatcher v0104 / TableRouter v0101)
- 單一引擎先,結構檢查沒過才雙讀;所有候選保留;兩讀一致 ≠ 原 PDF 正確
- 文件預算 300 秒 · 財報頁上限 8 · OCR 分層(輕 → 重)每層 60 秒 · 結果快取 · 子行程 worker
- OCR 只給版面識別後的局部區域:非 OCR → 輕 OCR → 重 OCR,保留信心與人工覆核,不得用 NLP 猜數字

## D. 對應到新 VRN(via_02_vrn)的管線
第一步 分類(個股)→ 取首頁 + 年度頁進 TEMP → 第二步 版面切割 · 分頁分類分群編號 → 表格:單讀 → (沒過)雙讀 → 文字幾何還原藏在文字的表 → 驗證(結構 + 算式)→ 第三 / 四步 OCR 只補沒過的區(輕 → 雙 → 重)→ 三區分開輸出 → SUMMARIZER 閘
"""

RECIPE = {"schema": "VIA.VRN02.ToolRecipe.v1", "version": "v0100", "source": "GitHub 成功紀錄(v0108 年度包 · FirstPageEngine v0130 · LocalDispatcher v0104 · TableRouter v0101)+ VRN v0152–v0163 實測",
          "principle": "工具不是全用:每段先跑最便宜且有實績的工具,沒過才升級;超過預算的工具這一輪記失敗、下一輪不優先",
          "budgets": {"document_s": 300, "ocr_tier_s": 60, "finance_pages_max": 8},
          "stages": [
              {"id": "S1", "name": "分類取頁", "tools": ["VRN_ReportClassifier v0102"], "exit": "個股報告 → 首頁 + 年度頁進 TEMP;其他不碰"},
              {"id": "S2", "name": "版面切割 · 分頁分類分群編號", "tools": ["pdfplumber 字詞", "ENG394 _subcat", "首頁資訊區辨識(關鍵詞 + 鄰接值)"], "exit": "每區有編號 P#·區·序;首頁 BODY / INFO / 頁首 / 頁尾分開"},
              {"id": "S3", "name": "表格還原(NON-OCR)", "ladder": ["單讀 pdfplumber(格線 → 文字分欄)", "文字幾何 ReportRestore v0101(藏在文字裡的表)", "雙讀 TableRepair v0102(只給財務 / 估值表且單讀沒過)"], "verify": ["結構(表頭年度 · 列長齊 · 可解析 ≥90%)", "字還原 ≥98%", "算式(validate_table 會計恆等式)"]},
              {"id": "S4", "name": "文字還原", "tools": ["rejoin 斷句", "ENG394 子分類"], "verify": ["覆蓋 ≥99.5%", "分類 100%"]},
              {"id": "S5", "name": "OCR(只補 S3 / S4 沒過的區)", "ladder": ["rapidocr(輕)", "tesseract 雙引擎投票", "paddleocr / easyocr(重)"], "verify": ["與原生數字吻合 ≥90%", "信心 ≥0.85", "欄數一致"]},
              {"id": "S6", "name": "三區輸出", "tools": ["extract3"], "exit": "文字 / 資訊區 / 財務報表各自資料集與燈"}],
          "lessons": "見 VRN_SuccessReference_v0100.md B 段(首頁 11 條)"}


def write_refs(T: Path) -> int:
    d = T / "references"
    d.mkdir(parents=True, exist_ok=True)
    n = 0
    for name, content in (("VRN_SuccessReference_v0100.md", REF_MD), ("VRN_ToolRecipe_v0100.json", json.dumps(RECIPE, ensure_ascii=False, indent=1))):
        p = d / name
        if not p.exists():
            p.write_text(content, encoding="utf-8")
            n += 1
    return n


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()
    if args[:1] == ["curate"] and "--purge" in args:
        vr = _resolve("via_roots")
        T = Path(args[args.index("--to") + 1]) if "--to" in args and args.index("--to") + 1 < len(args) else (vr()["via_02_vrn"] if vr else None)
        if not T or not T.is_dir():
            print("[計] curate · 夾不在 %s · RED" % T)
            return 1
        o = purge_v163(T)
        print("[計] curate --purge · 先壓縮歸檔再刪:%d 檔 · %.1f MB → %s(驗證 %s)· 一個檔都不丟 · GREEN" % (o["files"], o["mb"], o.get("archive", "—"), "過" if o.get("ok", True) else "失敗,沒刪"))
        return 0
    rc = PRIOR.main(args)
    if args[:1] == ["layout"] and _ST163.get("tools") is not None:
        tl = sorted(_ST163["tools"].items(), key=lambda kv: -kv[1]["n"])
        print("[計] 工具效益(每表)· " + " · ".join("%s %d 表 過 %.0f%% 平均 %d ms" % (k, v["n"], v["rate"], v["avg_ms"]) for k, v in tl[:5]))
        print("[計] 藏在文字中的表格 · 還原 %d 張(%s)· 文件預算 %d 秒 · 逾時 %d 份(記失敗)" % (_ST163["hidden"], Path(_ST163["rr"]).name if not str(_ST163["rr"]).startswith("—") else _ST163["rr"], _ST163["budget"], _ST163["timeouts"]))
    if args[:1] == ["curate"]:
        print("[計] curate v0163 · SSOT / 正則 / 同義字聯集整合(新版號 · 一筆不丟 · 衝突與一字多主列待裁)· 真刪改壓縮歸檔 · 參考卡 references\\VRN_SuccessReference_v0100.md + VRN_ToolRecipe_v0100.json")
    return rc


if _C162:
    _PREV_WO = vars(_C162)["write_outputs"]

    def write_outputs_v163(T, rows, mc, gp, s, into_T=True):
        integ = [r for r in rows if r.get("action") == "整合新版"]
        _ST163["integ"] = {"n": len(integ), "conflicts": sum(len(r["_integration"]["conflicts"]) for r in integ), "syn": sum(len(r["_integration"]["synonym_conflicts"]) for r in integ), "badrx": sum(len(r["_integration"]["bad_regex"]) for r in integ)}
        slim = [{k: v for k, v in r.items() if k not in ("_union", "_integration")} for r in rows]
        return _PREV_WO(T, slim, mc, gp, s, into_T)
    setattr(_C162, "write_outputs", write_outputs_v163)


def _mk_hidden_pdf(path: Path) -> None:
    import fitz  # noqa: WPS433
    doc = fitz.open()
    p1 = doc.new_page(width=595, height=842)
    p1.insert_text((50, 60), "Jentech (3653 TT) Liquid cooling ramp drives growth", fontsize=15, fontname="helv")
    for i in range(10):
        p1.insert_text((50, 110 + i * 14), "We expect revenue to keep growing as AI servers ramp; margin outlook stays solid in line %d." % i, fontsize=9, fontname="helv")
    p1.insert_text((50, 800), "KGI Securities Investment Advisory. Please see disclaimer.", fontsize=6, fontname="helv")
    p2 = doc.new_page(width=595, height=842)
    p2.insert_text((50, 60), "Income statement (NT$m)", fontsize=11, fontname="helv")

    def rt(page, xr, y, s):
        page.insert_text((xr - fitz.get_text_length(s, fontname="helv", fontsize=9), y), s, fontsize=9, fontname="helv")
    rights = [300, 370, 440, 510]
    for x, yv in zip(rights, ("2023A", "2024A", "2025F", "2026F")):
        rt(p2, x, 90, yv)
    data = [("Revenue", "12,345", "15,678", "19,012", "23,456"), ("Gross profit", "4,000", "5,100", "6,300", "7,800"), ("Operating income", "2,000", "2,600", "3,200", "4,000"),
            ("Net income", "1,500", "1,950", "2,400", "3,000"), ("EPS (NT$)", "10.5", "13.6", "16.8", "21.0")]
    for k, (lab, *vals) in enumerate(data):
        y = 106 + k * 14
        p2.insert_text((50, y), lab, fontsize=9, fontname="helv")
        for x, v in zip(rights, vals):
            rt(p2, x, y, v)
    doc.save(str(path))


def selftest() -> int:
    import tempfile
    import zipfile
    p = f = 0

    def chk(name, cond):
        nonlocal p, f
        if cond:
            p += 1
            print("  [OK] %s" % name)
        else:
            f += 1
            print("  [FAIL] %s" % name)
    real_home = _home()
    rr_src = next(iter(sorted(real_home.glob("intake/*/*/pack/engine/tools/VRN_ReportRestore_v0*.py"))), None) or (Path("/tmp/ref_VRN_ReportRestore_v0101.py") if Path("/tmp/ref_VRN_ReportRestore_v0101.py").exists() else None)
    prc = 0
    if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") != "1":
        print("  ── 前版鏈自測(v0162 起 · 快取隔離 · VIA_VRN_ROUTER=legacy 讓前版驗前版行為)──")
        os.environ["VIA_VRN_ROUTER"] = "legacy"
        try:
            prc = PRIOR.selftest()
        except Exception as exc:  # noqa: BLE001
            prc = 1
            print("  [前版鏈中斷] %s: %s" % (type(exc).__name__, str(exc)[:120]))
        finally:
            os.environ.pop("VIA_VRN_ROUTER", None)
    rc_ = _resolve("_reset_chain_caches")
    if rc_:
        rc_()
    for d in (_RR, _FZ, _ST163):
        d.clear()
    td = Path(tempfile.mkdtemp(prefix="vrn163-"))
    home = td / "functional modules" / "VRN"
    for d in ("SSOT", "knowledge", "registry", "intake/VRN_TableRepair"):
        (home / d).mkdir(parents=True, exist_ok=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT", "VIA_VDF_HOME", "VIA_ROOTS_BASE", "VIA_SPILL_DIR", "USERPROFILE", "VIA_VRN_REPORTRESTORE", "VIA_VRN_DOC_BUDGET")}
    try:
        for src in (real_home / "intake" / "VRN_TableRepair", Path("/tmp/out")):
            for q in sorted(src.glob("VRN_Table*_v010*.py")) if src.is_dir() else []:
                if not (home / "intake" / "VRN_TableRepair" / q.name).exists():
                    shutil.copy(q, home / "intake" / "VRN_TableRepair" / q.name)
        if rr_src:
            rp = home / "intake" / "VRN_v0108_Annual" / "VRN_v0108_Complete_Handover" / "pack" / "engine" / "tools"
            rp.mkdir(parents=True)
            shutil.copy(rr_src, rp / "VRN_ReportRestore_v0101.py")
        os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(td / "VIA_Reports" / "vrn"), "VIA_VDF_HOME": str(td / "nope"), "VIA_ROOTS_BASE": str(td / "VIA"), "VIA_SPILL_DIR": str(td / "TEMP"), "USERPROFILE": str(td)})
        os.environ.pop("VIA_VRN_REPORTRESTORE", None)
        (home / "knowledge" / "VRN_Broker_Dict_v0100.json").write_text(json.dumps({"brokers": {"凱基": {"abbr": "KGI", "aliases": ["凱基", "凱基投顧", "KGI", "KGI Securities"]}}}, ensure_ascii=False), encoding="utf-8")
        (home / "VRN_TWRoster_Offline_v0100.json").write_text(json.dumps({"rows": [{"code": "3653", "name": "健策", "market": "上市"}]}, ensure_ascii=False), encoding="utf-8")
        pdfp = td / "hidden.pdf"
        _mk_hidden_pdf(pdfp)
        if rr_src:
            import fitz  # noqa: WPS433
            fp = fitz.open(str(pdfp))[1]
            rowsw = {}
            for w in fp.get_text("words"):
                if w[1] < 80:
                    continue
                rowsw.setdefault(round((w[1] + w[3]) / 2 / 4), []).append(w)
            blocks = []
            for i, (k, ws) in enumerate(sorted(rowsw.items())):
                ws.sort(key=lambda w: w[0])
                t = " ".join(w[4] for w in ws)
                blocks.append({"kind": "text", "role": "BODY", "zone": "F", "x0": min(w[0] for w in ws), "top": min(w[1] for w in ws), "x1": max(w[2] for w in ws), "bottom": max(w[3] for w in ws), "size": 9, "id": "P2·F·%02d" % (i + 1), "text": t, "lines": [{"text": t}]})
            pg = {"blocks": blocks}
            _FZ.clear()
            n = hidden_tables(pg, str(pdfp), 2)
            tb = [b for b in pg["blocks"] if b.get("how") == "text-geometry"]
            rev = next((r for r in (tb[0]["rows"] if tb else []) if r and r[0] == "Revenue"), None)
            chk("① 藏在文字中的表格(只有文字行 · 無格線):ReportRestore v0101 文字幾何還原 → 1 表 · Revenue 列 = 12,345 / 15,678 / 19,012 / 23,456 · 年度表頭在", n == 1 and rev == ["Revenue", "12,345", "15,678", "19,012", "23,456"] and any("2024A" in c for c in tb[0]["rows"][0]))
        else:
            print("  [NODATA] ① 找不到 ReportRestore v0101(v0108 交接包工具)→ 藏在文字的表格不做,不判紅")
        inp = td / "inbox"
        inp.mkdir()
        shutil.copy(pdfp, inp / "凱基投顧_3653 健策_向子慧_20260917.pdf")
        _resolve("_mk_pdf_v158")(inp / "凱基投顧_3653 健策_copy_20260917.pdf", td)
        o = _resolve("layout_run_v158")(inp, {"workers": 1, "tabula": False, "max": 0, "only": "", "no_ocr": True})
        R = {r["file"]: r for r in o["rows"] if "cov_min" in r}
        rh = R.get("凱基投顧_3653 健策_向子慧_20260917.pdf", {})
        full = json.loads(Path(rh["temp_json"]).read_text(encoding="utf-8")) if rh.get("temp_json") else {"pages": []}
        tbs = [b for pg in full["pages"] for b in pg["blocks"] if b["kind"] == "table"]
        rev2 = next((r for b in tbs for r in b.get("rows", []) if r and str(r[0]).strip() == "Revenue"), None)
        chk("② 整條管線:財報頁的表(版面切割或文字幾何任一抓到)· Revenue 列四期完整 · 表驗證過", rev2 is not None and [c for c in rev2[1:] if c][:4] == ["12,345", "15,678", "19,012", "23,456"] and any(b["verify"]["ok"] for b in tbs))
        consistent = all(("tr" in b) == ("雙讀" in t["tool"]) for r in o["rows"] for t in r.get("tools", []) for pg in json.loads(Path(r["temp_json"]).read_text(encoding="utf-8"))["pages"] for b in pg["blocks"] if b.get("id") == t["table"])
        alltools = [t for r in o["rows"] for t in r.get("tools", [])]
        chk("③ TableRouter 律:單讀先驗 · 只有單讀沒過的財務 / 估值表才動雙讀(帳與表一致)· 工具效益帳有毫秒與過否", consistent and alltools and all("ms" in t and "ok" in t for t in alltools) and _ST163.get("tools"))
        os.environ["VIA_VRN_DOC_BUDGET"] = "0"
        o2 = _resolve("layout_run_v158")(inp, {"workers": 1, "tabula": False, "max": 0, "only": "", "no_ocr": True})
        os.environ.pop("VIA_VRN_DOC_BUDGET", None)
        chk("④ 文件預算(LocalDispatcher 300 秒同律;測試設 0):超過 → 停下剩下的頁 / 表 · 記失敗 · 註明逾時", all(r.get("timeout") and any("逾時" in n for n in r.get("notes", [])) for r in o2["rows"] if "cov_min" in r) and _ST163.get("timeouts", 0) >= 1)
        cur = vars(_C162)["curate"]
        T = td / "via_02_vrn"

        def w(rel, obj):
            q = T / rel
            q.parent.mkdir(parents=True, exist_ok=True)
            q.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        w("03_ssot/VRN_Book_v0100.json", {"schema": "B", "items": {"a": 1, "c": 3}, "x": 1})
        w("03_ssot/VRN_Book_v0101.json", {"schema": "B", "items": {"a": 1, "b": 2}, "x": 2})
        w("03_ssot/VRN_Syn_v0100.json", {"brokers": {"MS": ["大摩", "Morgan Stanley"]}})
        w("03_ssot/VRN_Syn_v0101.json", {"brokers": {"MS": ["Morgan Stanley"], "MSX": ["大摩"]}})
        w("03_ssot/VRN_Lex_v0100.json", {"rows": [{"term": "營收", "en": "Revenue"}, {"term": "毛利", "en": "GP"}]})
        w("03_ssot/VRN_Lex_v0101.json", {"rows": [{"term": "營收", "en": "Sales"}]})
        w("03_ssot/VRN_Fin_v0100.json", {"rows": [{"std": "net_income", "cat": "IS", "zh": ["稅後淨利"], "en": ["PAT"]}, {"std": "total_equity", "cat": "BS", "zh": ["權益"], "en": ["Total equity"]}]})
        w("03_ssot/VRN_Fin_v0101.json", {"rows": [{"std": "net_income", "cat": "IS", "zh": ["本期淨利"], "en": ["Net income"]}, {"std": "total_equity", "cat": "BS", "zh": ["權益"], "en": ["Total equity"]}, {"std": "total_equity", "cat": "BS", "zh": ["母公司業主權益"], "en": ["Shareholders' funds"]}]})
        w("05_rules/VRN_Rx_v0100.json", {"patterns": ["^\\d+$", "(bad"]})
        w("05_rules/VRN_Rx_v0101.json", {"patterns": ["^\\d+$", "^[A-Z]+$"]})
        w("03_ssot/VRN_Dc_v0100.json", {"rows": [{"key": "A", "cat": "x", "lvl": 1, "al": ["a"]}, {"key": "A", "cat": "x", "lvl": 2, "al": ["b"]}, {"key": "B", "cat": "x", "lvl": 1, "al": ["c"]}, {"key": "B", "cat": "x", "lvl": 1, "al": ["d"]}]})
        w("03_ssot/VRN_Sub_v0100.json", {"items": {"a": 1}})
        w("03_ssot/VRN_Sub_v0101.json", {"items": {"a": 1, "b": 2}})
        s0 = cur(T, do_apply=False, fill=False)
        chk("⑤ 只列:整合新版 6 冊(Book / Syn / Lex / Fin / Rx + 單版冊內重複的 Dc)· 子集冊不出新版(Sub v0100 照退)· 快照夾沒動", _ST163.get("integ", {}).get("n") == 6 and not (T / "03_ssot" / "VRN_Book_v0102.json").exists() and (T / "03_ssot" / "VRN_Book_v0100.json").exists())
        s1 = cur(T, do_apply=True, fill=False)
        bk = json.loads((T / "03_ssot" / "VRN_Book_v0102.json").read_text(encoding="utf-8"))
        side = json.loads((T / "03_ssot" / "VRN_Book_v0102.integration.json").read_text(encoding="utf-8"))
        lex = json.loads((T / "03_ssot" / "VRN_Lex_v0102.json").read_text(encoding="utf-8"))
        syn = json.loads((T / "03_ssot" / "VRN_Syn_v0102.integration.json").read_text(encoding="utf-8"))
        rx = json.loads((T / "05_rules" / "VRN_Rx_v0102.integration.json").read_text(encoding="utf-8"))
        fin = json.loads((T / "03_ssot" / "VRN_Fin_v0102.json").read_text(encoding="utf-8"))
        fins = json.loads((T / "03_ssot" / "VRN_Fin_v0102.integration.json").read_text(encoding="utf-8"))
        fm = {(r["std"], r["cat"]): r for r in fin["rows"]}
        chk("⑦-1 科目字典(std + cat 分組):同科目合成一列 · 別名聯集一個不丟(net_income zh = 稅後淨利 + 本期淨利 · en = PAT + Net income;total_equity 兩列合一)· 補回清單列出 PAT / 稅後淨利",
            len(fin["rows"]) == 2 and set(fm[("net_income", "IS")]["zh"]) == {"稅後淨利", "本期淨利"} and set(fm[("net_income", "IS")]["en"]) == {"PAT", "Net income"}
            and set(fm[("total_equity", "BS")]["zh"]) == {"權益", "母公司業主權益"} and any("PAT" in str(x.get("added")) for x in fins["restored_from_older"]))
        chk("⑥ 聯集一筆不丟:Book items = a/b/c · x 衝突新值為準(舊值 1 留在整合帳)· 兩個舊版退役",
            bk["items"] == {"a": 1, "c": 3, "b": 2} and bk["x"] == 2 and any(c["path"] == "$.x" and c["older"] == 1 for c in side["conflicts"]) and not (T / "03_ssot" / "VRN_Book_v0100.json").exists() and not (T / "03_ssot" / "VRN_Book_v0101.json").exists())
        chk("⑦ 清單依鍵合併不重複(營收 只一列 · en 取新值 Sales · 毛利 保留)· 同義字一字多主(大摩 → MS / MSX)列待裁 · 壞正則 (bad 列出",
            len(lex["rows"]) == 2 and {r["term"]: r["en"] for r in lex["rows"]} == {"營收": "Sales", "毛利": "GP"} and any(c["alias"] == "大摩" and set(c["canonicals"]) == {"MS", "MSX"} for c in syn["synonym_conflicts"]) and any(b["regex"] == "(bad" for b in rx["bad_regex"]))
        dc = json.loads((T / "03_ssot" / "VRN_Dc_v0101.json").read_text(encoding="utf-8"))
        dcs = json.loads((T / "03_ssot" / "VRN_Dc_v0101.integration.json").read_text(encoding="utf-8"))
        chk("⑦-2 單版冊內重複:B 兩列純值一致 → 合一列(別名 c + d)· A 兩列 lvl 打架 → 不合併、列疑似重複待裁", len(dc["rows"]) == 3 and any(r["key"] == "B" and set(r["al"]) == {"c", "d"} for r in dc["rows"]) and len(dcs["suspect_duplicates"]) == 1)
        s2 = cur(T, do_apply=True, fill=False)
        chk("⑧ 再跑:已唯一 → 整合 0 · 退役 0(不拉鋸;疑似重複不重複加;整合帳不被當冊再整合)· 參考卡與調配配方已寫(只增)", _ST163.get("integ", {}).get("n") == 0 and s2["retire"] == 0 and (T / "references" / "VRN_SuccessReference_v0100.md").exists() and (T / "references" / "VRN_ToolRecipe_v0100.json").exists())
        nret = sum(1 for x in (T / "_retired").rglob("*") if x.is_file())
        po = purge_v163(T)
        zp = Path(po["archive"])
        with zipfile.ZipFile(zp) as z:
            zn = len(z.namelist())
        chk("⑨ 真刪改「先壓縮歸檔、驗證過才刪」:%d 檔進 %s · _retired 清空 · 一個檔都不丟" % (nret, zp.name), po.get("ok") and zn == nret and nret >= 9 and not (T / "_retired").exists())
    finally:
        for k, val in saved.items():
            if val is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = val
        for d in (_FZ,):
            if d.get("doc") is not None:
                try:
                    d["doc"].close()
                except Exception:  # noqa: BLE001
                    pass
            d.clear()
        _RR.clear()
        shutil.rmtree(td, ignore_errors=True)
    chk("⑩ 前版鏈(v0162 起)自測 rc 0%s" % ("(本次略過)" if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else ""), prc == 0)
    me = Path(__file__).read_text(encoding="utf-8")
    chk("⑪ 正本加速器橋 · 自帶多程序墊片", "import VeritasCeleritas_v1141" in me and _job_entry.__module__ in ("__main__", __name__))
    print("[計] VRN_SystemManager_v0163 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
