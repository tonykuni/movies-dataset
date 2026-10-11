#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0158 — 薄尾(操作員 2026-10-10):第二步儘量 100% 還原首頁與財報頁 · 第三步輕型 OCR · 第四步重型 OCR · 只增不減。
  layout [--workers N] [--no-ocr] [--tabula] [--max N] [--only 片段] [--register] [--no-audit]
   第二步 LAYOUT NON-OCR:版面只負責切割與分類(輕工具 pdfplumber),擷取 / 修復 / 還原交給專職工具:
       表格 → TableRepair(上傳 v0100;intake 落地 + v0101 加速器橋)雙讀 PyMuPDF + pdfplumber · 字詞守恆 · 跨格 / 白字檢查;雙讀一致 = 表格還原過
              缺 PyMuPDF 時退回 v0157 驗證(依表型:財務 / 估值表嚴格,資訊 / 數據表看字還原)
       資訊區 → 同列配對(標籤欄 / 值欄分開的排版)· 評等 / 目標價字典改讀中央同義字冊(RATING_* · RATING_CODEBOOK_MASTER · TARGET_PRICE · 剝詞 · 目標價 Regex)· 修飾詞(維持 / 調升 …)不當評等
       電郵名:數字與單段不硬還原;價格庫比報告日舊 >7 天 → 標過舊,不比收盤 / 不算 TP(adj);檔名缺券商 → 由頁尾 / 電郵網域補
   第三步 輕型 OCR(單引擎 rapidocr → 雙引擎 tesseract 投票)· 第四步 重型 OCR(paddleocr / easyocr)
       只做第二步標出的區:年度頁圖區無文字層(影像表格)· 首頁大圖區 · 雙讀問題表(NO_TEXT / READERS_DISAGREE / 跨格)· 掃描件首頁
       DPI:輕型 300(表格 / 小字 400)· 雙引擎 ≥400 · 重型 500(超過 2500 萬像素自動降)
       還原修正驗證:數字混淆修正(O→0 · l/I→1 · S→5 …)· 欄數一致 · 年度表頭 · 與原生數字比對 ≥90% · 信心 ≥0.85
       工具在哪個 Python 就用哪個(本身 · 設定冊 ocr_python · envs\\via_vrn_312);缺的寫 registry\\VRN_ToolRequest_v####(給 VCGC 安裝,VRN 不自己裝)
   SUMMARIZER 閘:文字與表格都還原過、OCR 區全接受才放行(SUMMARIZER_GATE.json;summarize / brief / digest 動詞先查閘)
   TEMP:每輪唯一目錄 + .vrn_owner.json 標記;開跑前只清 VRN 自己標記的舊輪(留最新 3 · 超 48 小時 · 總量 >2 GB);本輪與別人的不碰
   加速器到細節:每個工作程序鎖 BLAS / OpenMP / ONNX 執行緒(有 VeritasCeleritas.apply_thread_limits 就用);OCR 子程序也限執行緒
   速度:圖區分群改格網(取代 O(n²))· 格線表直接取 find_tables 結果(不再每表重找三次)· 各段計時列入第二步頁
   多程序墊片:當 __main__ 的尾版要帶 _job_entry / _init_entry(兩行),否則 spawn 解不開 → 自動退單程序
  engines [--register]  稽核略過隔離區 / 測試;加入 intake 的 TableRepair 兩族
VRN SystemManager 獨立運作:只讀 VDF 資料庫(價格 / 總清單)與中央同義字冊;同步整合只由操作員與 AI 做。
其餘動詞照前版鏈。
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
import hashlib
import html
import importlib.util
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0158"


def _vnum_v0158(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0158(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0158(p) < _vnum_v0158(__file__)), key=_vnum_v0158)
PRIOR = _load_v0158(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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
    """把鏈上原函式換成本版(只換函式參照,不改前版檔案)。回傳原函式。"""
    m = _owner(name)
    if not m:
        return None
    old = vars(m)[name]
    setattr(m, name, fn)
    return old


_home, _rep = _resolve("_home"), _resolve("_rep")


# ───────── 多程序墊片:當 __main__ 的版本必須自帶這兩個函式(spawn 只能從 __main__ 解開)─────────
def _job_entry(kind, item):
    return _resolve("_job")(kind, item)


def _init_entry(*args):
    _ACC["worker"] = accel_threads()
    return _resolve("_init_worker")(*args)


_ACC = {}


def accel_threads(n: int = 1) -> str:
    """加速器到細節:每個工作程序把 BLAS / OpenMP / ONNX 執行緒鎖成 n(多程序時避免超訂);有 VeritasCeleritas 的 apply_thread_limits 就用它。"""
    for k in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS", "ORT_NUM_THREADS"):
        os.environ[k] = str(n)
    note = "env 執行緒上限 %d" % n
    acc = globals().get("VIA_ACCEL")
    fn = getattr(acc, "apply_thread_limits", None) if acc else None
    if not fn:
        try:
            sup = _home().parents[1] / "supportive modules"
            for p in sorted(sup.rglob("VeritasCeleritas_v*.py"))[-1:]:
                vc = _load_v0158(p, "veritas_celeritas_for_vrn")
                fn = getattr(vc, "apply_thread_limits", None)
        except Exception:  # noqa: BLE001
            fn = None
    if callable(fn):
        try:
            fn(n)
            note += " + VeritasCeleritas.apply_thread_limits"
        except Exception:  # noqa: BLE001
            pass
    return note


def _pool_map_v158(kind: str, items: list, workers: int, initargs: tuple) -> tuple:
    out = []
    main = sys.modules.get("__main__")
    job, init = getattr(main, "_job_entry", None), getattr(main, "_init_entry", None)
    shim_ok = callable(job) and callable(init) and getattr(job, "__module__", "") == "__main__" and getattr(init, "__module__", "") == "__main__"
    note = "單程序"
    if workers > 1 and len(items) > 1 and shim_ok:
        try:
            import multiprocessing as _mp
            from concurrent.futures import ProcessPoolExecutor, as_completed
            with ProcessPoolExecutor(max_workers=workers, initializer=init, initargs=initargs, mp_context=_mp.get_context("spawn")) as ex:
                futs = {ex.submit(job, kind, it): it for it in items}
                for i, fu in enumerate(as_completed(futs), 1):
                    it = futs[fu]
                    try:
                        out.append(fu.result())
                    except Exception as exc:  # noqa: BLE001
                        out.append({"file": Path(it if isinstance(it, str) else it.get("path", "?")).name, "path": it if isinstance(it, str) else it.get("path"), "lamp": "RED", "status": "ERROR", "notes": ["%s:%s" % (type(exc).__name__, str(exc)[:80])]})
                    if kind == "l2":
                        print("  [進度] %d/%d · %s · %s" % (i, len(items), out[-1].get("lamp"), str(out[-1].get("file", ""))[:50]), flush=True)
            return out, "多程序 ×%d(%s)" % (workers, accel_threads.__doc__ and "加速器執行緒上限")
        except Exception as exc:  # noqa: BLE001
            out = []
            note = "多程序失敗(%s)→ 單程序" % type(exc).__name__
    elif workers > 1 and not shim_ok:
        note = "單程序(__main__ 沒帶墊片)"
    _init_entry(*initargs)
    for i, it in enumerate(items, 1):
        try:
            out.append(_resolve("_job")(kind, it))
        except Exception as exc:  # noqa: BLE001
            out.append({"file": Path(it if isinstance(it, str) else it.get("path", "?")).name, "lamp": "RED", "notes": ["%s:%s" % (type(exc).__name__, str(exc)[:80])]})
        if kind == "l2":
            print("  [進度] %d/%d · %s · %s" % (i, len(items), out[-1].get("lamp"), str(out[-1].get("file", ""))[:50]), flush=True)
    return out, note


_patch("_pool_map", _pool_map_v158)


# ───────── TEMP:每輪唯一目錄 + 擁有者標記 + 清舊(只清 VRN 自己的舊輪,絕不碰本輪與別人的)─────────
_RUN = {"id": datetime.datetime.now().strftime("%Y%m%dT%H%M%S") + "_" + secrets.token_hex(3)}
_KEEP_RUNS, _MAX_AGE_H, _CAP_GB = 3, 48, 2.0


def _temp_base() -> Path:
    return Path(os.environ.get("VIA_SPILL_DIR") or (Path(tempfile.gettempdir()) / "VIA_progress"))


def _temp_root_v158(stamp: str) -> Path:
    d = _temp_base() / ("vrn_stage_" + _RUN["id"])
    d.mkdir(parents=True, exist_ok=True)
    mk = d / ".vrn_owner.json"
    if not mk.exists():
        mk.write_text(json.dumps({"owner": "VRN_SystemManager", "run_id": _RUN["id"], "created": datetime.datetime.now().isoformat(timespec="seconds"), "pid": os.getpid()}), encoding="utf-8")
    return d


_patch("_temp_root", _temp_root_v158)


def temp_gc() -> dict:
    """只清帶 .vrn_owner.json 的 VRN 舊輪(TEMP\\VIA_progress\\vrn_stage_* 與各 ps_*\\spill\\vrn_stage_*):保留最新 3 輪 · 超過 48 小時 · 總量超過 2 GB 從舊的刪;本輪不刪。"""
    roots = {_temp_base(), Path(tempfile.gettempdir()) / "VIA_progress"}
    dirs = []
    for r in roots:
        if not r.is_dir():
            continue
        for d in list(r.glob("vrn_stage_*")) + list(r.glob("ps_*/spill/vrn_stage_*")):
            mk = d / ".vrn_owner.json"
            if d.is_dir() and mk.exists() and _RUN["id"] not in d.name:
                try:
                    size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
                    dirs.append((mk.stat().st_mtime, d, size))
                except OSError:
                    continue
    dirs = sorted(set(dirs), key=lambda x: -x[0])
    now, removed, freed, total = time.time(), 0, 0, sum(x[2] for x in dirs)
    for i, (mt, d, size) in enumerate(dirs):
        old = i >= _KEEP_RUNS or (now - mt) > _MAX_AGE_H * 3600 or total > _CAP_GB * 1024 ** 3
        if old:
            try:
                shutil.rmtree(d)
                removed += 1
                freed += size
                total -= size
            except OSError:
                pass
    return {"kept": len(dirs) - removed, "removed": removed, "freed_mb": round(freed / 1024 ** 2, 1), "run_id": _RUN["id"]}


# ───────── 速度:圖區分群改格網(取代 O(n²))· 格線表列直接取 find_tables 結果(不再每表重找三次)─────────
def _figures_v158(page, tables: list) -> list:
    W, H = float(page.width), float(page.height)
    out = []
    for im in page.images:
        bx = (float(im["x0"]), float(im["top"]), float(im["x1"]), float(im["bottom"]))
        if (bx[2] - bx[0]) * (bx[3] - bx[1]) >= 0.015 * W * H:
            out.append(bx)
    objs = []
    for o in page.curves + page.lines:
        b = (float(o["x0"]), float(o["top"]), float(o["x1"]), float(o["bottom"]))
        if not any(t[0] - 2 <= b[0] and b[2] <= t[2] + 2 and t[1] - 2 <= b[1] and b[3] <= t[3] + 2 for t in tables):
            objs.append(b)
    if not objs:
        return out
    G = 24.0
    parent = list(range(len(objs)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    grid = defaultdict(list)
    for i, b in enumerate(objs):
        for gx in range(int((b[0] - 12) // G), int((b[2] + 12) // G) + 1):
            for gy in range(int((b[1] - 12) // G), int((b[3] + 12) // G) + 1):
                for j in grid[(gx, gy)]:
                    ri, rj = find(i), find(j)
                    if ri != rj:
                        parent[ri] = rj
                grid[(gx, gy)].append(i)
    cl = defaultdict(list)
    for i in range(len(objs)):
        cl[find(i)].append(objs[i])
    for bs in cl.values():
        x0, t, x1, b = min(x[0] for x in bs), min(x[1] for x in bs), max(x[2] for x in bs), max(x[3] for x in bs)
        if len(bs) >= 12 and (x1 - x0) * (b - t) >= 0.015 * W * H:
            out.append((x0, t, x1, b))
    return out


_patch("_figures", _figures_v158)
_TCACHE = {}
_NUM_RX = re.compile(r"^[\(\-–+]?[\d,]+(?:\.\d+)?%?\)?$")


def _table_boxes_v158(page, annual: bool) -> list:
    boxes = []
    try:
        for t in page.find_tables():
            bb = tuple(float(v) for v in t.bbox)
            boxes.append(("lines", bb))
            try:
                _TCACHE[(id(page), tuple(round(v, 1) for v in bb))] = t.extract()
            except Exception:  # noqa: BLE001
                pass
    except Exception:  # noqa: BLE001
        pass
    if annual and not boxes:
        try:
            for t in page.find_tables({"vertical_strategy": "text", "horizontal_strategy": "text", "min_words_vertical": 3, "min_words_horizontal": 2}):
                rows = t.extract() or []
                cells = [c for r in rows for c in r if c and str(c).strip()]
                num = sum(1 for c in cells if _NUM_RX.match(str(c).replace(" ", "")))
                if len(rows) >= 3 and max((len(r) for r in rows), default=0) >= 3 and cells and num / len(cells) >= 0.35:
                    bb = tuple(float(v) for v in t.bbox)
                    boxes.append(("text", bb))
                    _TCACHE[(id(page), tuple(round(v, 1) for v in bb))] = rows
        except Exception:  # noqa: BLE001
            pass
    return boxes


_patch("_table_boxes", _table_boxes_v158)
_PREV_ET = _resolve("_extract_table")


def _extract_table_v158(page, bbox, how, pdf_path, pno, tabula_ok):
    rows = _TCACHE.get((id(page), tuple(round(float(v), 1) for v in bbox)))
    if rows:
        rr, fixes = _resolve("_repair_rows")(rows)
        cells = [c for x in rr for c in x]
        if len(rr) >= 2 and rr and len(rr[0]) >= 2 and cells and sum(1 for c in cells if c) / len(cells) >= 0.6:
            return {"engine": "pdfplumber-%s(快取)" % how, "rows": rr, "fixes": fixes, "alts": []}
    return _PREV_ET(page, bbox, how, pdf_path, pno, tabula_ok)


_patch("_extract_table", _extract_table_v158)


# ───────── 表格還原修正:TableRepair(雙讀 PyMuPDF + pdfplumber · 字詞守恆 · 跨格 · 白字)─────────
_TR = {}


def tablerepair() -> dict:
    if _TR:
        return _TR
    d = _home() / "intake" / "VRN_TableRepair"
    _TR.update(ok=False, err="", files=[])
    if importlib.util.find_spec("fitz") is None:
        _TR["err"] = "缺 PyMuPDF(VCGC 安裝 pymupdf)"
        return _TR
    g = sorted(d.glob("VRN_TableGeometry_v*.py"), key=lambda q: _vnum_v0158(q.stem))
    v = sorted(d.glob("VRN_TableValidation_v*.py"), key=lambda q: _vnum_v0158(q.stem))
    if not g or not v:
        _TR["err"] = "VRN\\intake\\VRN_TableRepair 不在"
        return _TR
    try:
        if str(d) not in sys.path:
            sys.path.insert(0, str(d))
        import importlib as _il
        _TR.update(geo=_il.import_module(g[-1].stem), val=_il.import_module(v[-1].stem), ok=True, files=[g[-1].name, v[-1].name])
    except Exception as exc:  # noqa: BLE001
        _TR["err"] = "載入失敗 %s:%s" % (type(exc).__name__, str(exc)[:60])
    return _TR


def tr_check(fpage, ppage, bbox, words, other, neighbors) -> dict | None:
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
    xs = geo.def_snap([x for b in boxes for x in (b[0], b[2])])
    ys = geo.def_snap([y for b in boxes for y in (b[1], b[3])])
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


# ───────── 數字正規化 · 依表型驗證(財務 / 估值嚴格;資訊 / 數據表看字還原)─────────
_YR158 = re.compile(r"(?<![\d.])(?:(?:19|20)\d{2}[AEFPC]?|FY\s?\d{2,4}[AEFP]?|\d{2}[AEFP]|[1-4]Q\s?\d{2}[AEF]?|\d[HQ]\s?\d{2}[AEF]?|(?:Dec|Mar|Jun|Sep)[-/ ]?\d{2}[AEF]?|\d{4}/\d{1,2}|20\d{2}年)(?![\d])", re.I)


def parse_number_v158(s: str):
    t = str(s).strip()
    t = re.sub(r"^(?:NT\$|US\$|HK\$|RMB|TWD|NTD|\$|＄)\s*", "", t)
    t = re.sub(r"[*†‡#^]+$", "", t)
    t = re.sub(r"(?<=\d)\s*(?:x|X|倍|pp|bp|bps|ppt|元)$", "", t)
    t = t.replace("，", ",").replace("−", "-").replace("–", "-").replace("—", "-").replace("（", "(").replace("）", ")")
    if t.lower() in ("", "-", "--", "n.a.", "na", "n/a", "nm", "n.m.", "nmf", "neg.", "neg"):
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").rstrip("%").lstrip("+").replace(",", "")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


_PREV_VT = _resolve("verify_table")


def verify_table_v158(b: dict, page=None) -> dict:
    v = _PREV_VT(b, page)
    rows = b.get("rows", [])
    sub = b.get("sub", "")
    strict = sub.startswith(("財務表", "估值表"))
    if rows:
        v["header"] = v["header"] or sum(1 for c in rows[0] if _YR158.search(c or "")) >= 2
    if not strict:
        v["ok"] = (max((len(r) for r in rows), default=0) >= 2 and v["multi_left"] == 0 and (v["text_cov"] is None or v["text_cov"] >= 98.0))
        v["rule"] = "資訊/數據表:≥2 欄 · 無合併數字格 · 表內字還原 ≥98%"
    else:
        v["ok"] = v["header"] and v["rect"] and v["multi_left"] == 0 and v["parse_rate"] >= 0.9 and (v["text_cov"] is None or v["text_cov"] >= 98.0) and v["arith"] != "有問題"
        v["rule"] = "財務/估值表:表頭年度 · 列長齊 · 無合併數字格 · 可解析 ≥90% · 表內字還原 ≥98% · 算術"
    if v["ok"]:
        v["issues"] = []
    return v


_patch("parse_number", parse_number_v158)
_patch("verify_table", verify_table_v158)


# ───────── 中央同義字冊(評等字典 · 目標價字典 · 剝詞 · 目標價 Regex)─────────
_CB = {}
_MODIFIERS = ("維持", "調升", "調降", "重申", "初次", "首次", "首評", "maintain", "maintained", "upgrade", "upgraded", "downgrade", "downgraded", "reiterate", "initiate", "initiation")


def central_book() -> dict:
    if _CB:
        return _CB
    reg = _home().parents[1] / "supportive modules" / "registry"
    hits = sorted(reg.glob("VIA_Central_Synonym_Regex_v*.json"), key=lambda q: _vnum_v0158(q.stem)) if reg.is_dir() else []
    syn, rx, src = {}, {}, ""
    if hits:
        try:
            d = json.loads(hits[-1].read_text(encoding="utf-8-sig"))
            syn = d.get("synonyms") or d.get("central_synonyms") or {k: v for k, v in d.items() if isinstance(v, (list, dict)) and str(k).isupper()}
            rx = {k: (v.get("pattern") if isinstance(v, dict) else v) for k, v in (d.get("regex") or d.get("central_regex_inventory") or {}).items()}
            src = hits[-1].name
        except (OSError, ValueError):
            pass
    norm = {}
    groups = {"RATING_STRONG_BUY_MASTER": "Strong Buy", "RATING_BUY": "Buy", "RATING_HOLD": "Hold", "RATING_SELL": "Sell", "RATING_STRONG_SELL_MASTER": "Strong Sell", "RATING_NOT_RATED": "Not Rated"}
    for g, label in groups.items():
        for w in syn.get(g, []) or []:
            if isinstance(w, str) and w.strip() and w.strip().lower() not in _MODIFIERS:
                norm.setdefault(w.strip(), label)
    cbm = syn.get("RATING_CODEBOOK_MASTER") or {}
    if isinstance(cbm, dict):
        for label, ent in cbm.items():
            for w in (ent or {}).get("aliases", []) if isinstance(ent, dict) else []:
                if isinstance(w, str) and w.strip().lower() not in _MODIFIERS:
                    norm.setdefault(w.strip(), label.replace("_", " "))
    seed = _resolve("RATING_NORM") or {}
    for w, label in seed.items():
        norm.setdefault(w, label)
    for w, label in (("增加持股", "Overweight"), ("降低持股", "Underweight"), ("加碼", "Overweight"), ("減碼", "Underweight"), ("Market Perform", "Neutral"), ("Sector Perform", "Neutral"), ("Equal Weight", "Equal-weight"), ("中性", "Neutral"), ("觀望", "Hold")):
        norm.setdefault(w, label)
    for amb in ("N", "B", "OP", "UP", "MP", "EW", "CD", "UR", "SB", "SS", "FV", "PT"):
        norm.pop(amb, None)          # 單字母 / 縮寫只在「評等」標籤旁才採用(見 extract_info)
    tp_words = [w for w in (syn.get("TARGET_PRICE") or []) if isinstance(w, str) and len(w) >= 2 and w not in ("Target", "TARGET", "Valuation", "Base Case", "Bull Case", "Bear Case", "FV", "PT", "目標")]
    tp_words = sorted(set(tp_words + ["目標價", "目標股價", "Target Price", "Price Target", "Target price", "12M TP", "12-month TP", "TP", "合理價", "合理股價", "Fair Value"]), key=len, reverse=True)
    strips = [w for w in (syn.get("TARGET_PRICE_STRIPS") or ["NT$", "TWD", "元"]) if isinstance(w, str)]
    _CB.update(src=src, rating=norm, rating_abbr={"OW": "Overweight", "UW": "Underweight", "N": "Neutral", "B": "Buy", "OP": "Outperform", "UP": "Underperform", "MP": "Neutral", "EW": "Equal-weight", "NR": "Not Rated", "SB": "Strong Buy", "SS": "Strong Sell"},
               tp_words=tp_words, strips=strips, tp_rx=[x for x in (rx.get("RX_TARGET_PRICE_NTD"), rx.get("RX_TARGET_PRICE_DEFENSE")) if x])
    return _CB


# ───────── 資訊區:同列配對(標籤在左 · 值在右的欄位表)· 評等修飾詞 · 目標價字典 ─────────
def _rows_p1(p1: dict) -> list:
    segs = []
    for b in p1["blocks"]:
        if b["role"] == "FOOTER":
            continue
        if b["kind"] == "text":
            for l in b.get("lines", []):
                segs.append({"text": l["text"], "x0": l["x0"], "x1": l["x1"], "top": l["top"], "bottom": l["bottom"], "role": b["role"], "zone": b["zone"]})
        elif b["kind"] == "table":
            for i, r in enumerate(b.get("rows", [])):
                segs.append({"text": " ".join(c for c in r if c), "x0": b["x0"], "x1": b["x1"], "top": b["top"] + i * 0.01, "bottom": b["top"] + i * 0.01, "role": b["role"], "zone": b["zone"], "table": True})
    rows = []
    for s in sorted(segs, key=lambda s: (s["zone"] if s["zone"] in "LR" else "M", s["top"], s["x0"])):
        if rows and not s.get("table") and not rows[-1][-1].get("table") and rows[-1][-1]["zone"] == s["zone"] and abs(rows[-1][-1]["top"] - s["top"]) <= 2.5:
            rows[-1].append(s)
        else:
            rows.append([s])
    return [{"text": " ".join(x["text"] for x in sorted(r, key=lambda x: x["x0"])), "role": r[0]["role"], "top": r[0]["top"], "zone": r[0]["zone"]} for r in rows]


_PREV_EI = _resolve("extract_info")


def extract_info_v158(p1: dict, book: dict, rating_words: list) -> dict:
    out = _PREV_EI(p1, book, rating_words)
    cb = central_book()
    rows = _rows_p1(p1)
    info_rows = [r for r in rows if r["role"] in ("INFO", "HEADER")] + [r for r in rows if r["role"] == "BODY" and r["top"] < 0.35 * p1["H"]]
    words = sorted(cb["rating"], key=len, reverse=True)
    out["rating"], out["rating_raw"], out["rating_src"] = "", "", ""
    lab_rx = re.compile(r"(?i)(?:投資評等|評等|投資建議|Rating|Recommendation|Stock Rating)\s*[:：]?\s*(.{0,40})")
    for r in info_rows:
        m = lab_rx.search(r["text"])
        if not m:
            continue
        cand = m.group(1)
        for w in words:
            rx = (r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(w)) if w.isascii() else re.escape(w)
            if re.search(rx, cand, re.I if w.isascii() else 0):
                out.update(rating_raw=w, rating=cb["rating"][w], rating_src="標籤旁")
                break
        if not out["rating"]:
            for ab, label in cb["rating_abbr"].items():
                if re.match(r"\s*%s(?![A-Za-z])" % re.escape(ab), cand):
                    out.update(rating_raw=ab, rating=label, rating_src="標籤旁縮寫")
                    break
        if out["rating"]:
            break
    if not out["rating"]:
        txt = " ".join(r["text"] for r in info_rows if r["role"] == "INFO")
        for w in words:
            rx = (r"(?<![A-Za-z])%s(?![A-Za-z])" % re.escape(w)) if w.isascii() else re.escape(w)
            if len(w) >= 2 and re.search(rx, txt, re.I if w.isascii() else 0):
                out.update(rating_raw=w, rating=cb["rating"][w], rating_src="資訊區")
                break
    tp_alt = "|".join(re.escape(w) for w in cb["tp_words"])
    tp_rx = re.compile(r"(?i)(?:%s)\s*(?:\([^)]{0,24}\))?\s*[:：]?\s*(?:NT\$|NT|TWD|NTD|US\$|HK\$|\$|新台幣|上看)?\s*([\d,]+(?:\.\d+)?)" % tp_alt)
    close_rx = _resolve("CLOSE_RX")
    out["tp"], out["close"] = None, None
    for r in info_rows:
        if out["tp"] is None:
            m = tp_rx.search(r["text"])
            if m:
                out["tp"] = parse_number_v158(m.group(1))
                out["tp_src"] = "同列:" + r["text"][:40]
        if out["close"] is None and close_rx:
            m = close_rx.search(r["text"])
            if m and not tp_rx.search(r["text"][:m.start() + 1]):
                val = parse_number_v158(m.group(1))
                if val and not re.search(r"(?i)52[- ]?w|52週|high|low", r["text"][max(0, m.start() - 12):m.end()]):
                    out["close"] = val
                    out["close_src"] = "同列:" + r["text"][:40]
    for pat in cb.get("tp_rx", []):
        if out["tp"] is None:
            try:
                m = re.search(pat, " ".join(r["text"] for r in info_rows))
                if m:
                    out["tp"] = parse_number_v158(m.group(m.lastindex or 0))
                    out["tp_src"] = "中央冊 Regex"
            except re.error:
                pass
    return out


def email_name_v158(local: str) -> str:
    parts = [re.sub(r"\d+", "", p) for p in re.split(r"[._\-]+", local)]
    parts = [p for p in parts if len(p) >= 2]
    return " ".join(p.capitalize() for p in parts) if len(parts) >= 2 else ""


_patch("extract_info", extract_info_v158)
_patch("email_name", email_name_v158)
_PREV_DB = _resolve("db_check")


def db_check_v158(row: dict, info: dict, px: dict, master: dict) -> dict:
    r = _PREV_DB(row, info, px, master)
    rd = row.get("date", "")
    if r.get("date_before") and rd:
        try:
            gap = (datetime.date.fromisoformat(rd) - datetime.date.fromisoformat(r["date_before"])).days
            r["gap_days"] = gap
            if gap > 7:
                r["stale"] = True
                r["close_ok"] = None
                r["tp_adj"] = None
                r["note"] = ("價格庫只到 %s(報告日前缺 %d 天)→ 收盤 / TP(adj)不比對" % (r["date_before"], gap))
        except ValueError:
            pass
    return r


_patch("db_check", db_check_v158)


# ───────── 第二步核心(v0158):TableRepair 雙讀 · 各段計時 · run_id · 第三步候選區 ─────────
_TR_SOFT = {"UNASSIGNED_SOURCE_WORD_IN_TABLE", "CONTEXT_HAS_POSSIBLE_OMITTED_ROW"}
_TR_OCR = {"NO_TEXT_NEEDS_OCR", "READERS_DISAGREE", "GLYPH_CROSSES_CELL_BOUNDARY", "INVALID_GLYPH", "AMBIGUOUS_SPACED_NUMBER"}


def l2_one_v158(row: dict) -> dict:
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
            if fdoc is not None:
                try:
                    words, other = tr["geo"].def_read_page(fdoc[lp - 1], page)
                except Exception:  # noqa: BLE001
                    words = None
            tbls = [b for b in pg["blocks"] if b["kind"] == "table"]
            for b in tbls:
                b["page"] = orig
                rr = rpt(b, page)
                b["rows"], b["fixes"] = rr["rows"], rr["fixes"]
                b["sub"] = tcat(b["rows"], b["role"])
                if words is not None:
                    neigh = [[x["x0"], x["top"], x["x1"], x["bottom"]] for x in tbls if x is not b]
                    trr = tr_check(fdoc[lp - 1], page, (b["x0"], b["top"], b["x1"], b["bottom"]), words, other, neigh)
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


_patch("l2_one", l2_one_v158)


# ───────── 第三步 輕型 OCR(單引擎 → 雙引擎)· 第四步 重型 OCR · 自動選工具 · DPI 政策 · 還原修正驗證 ─────────
_PROBE_CODE = r'''
import json, importlib, sys
out = {"python": sys.executable, "engines": {}}
def has(m):
    try:
        importlib.import_module(m); return True
    except Exception:
        return False
if has("rapidocr_onnxruntime") or has("rapidocr"):
    out["engines"]["rapidocr"] = {"ok": True}
if has("pytesseract"):
    try:
        import pytesseract
        out["engines"]["tesseract"] = {"ok": True, "version": str(pytesseract.get_tesseract_version()), "langs": sorted(pytesseract.get_languages(config=""))}
    except Exception as e:
        out["engines"]["tesseract"] = {"ok": False, "err": "沒有 tesseract 執行檔:" + str(e)[:60]}
for m in ("paddleocr", "easyocr"):
    if has(m):
        out["engines"][m] = {"ok": True}
out["fitz"] = has("fitz"); out["cv2"] = has("cv2"); out["PIL"] = has("PIL")
print(json.dumps(out))
'''
_WORKER_CODE = r'''
import json, sys
jobs = json.load(open(sys.argv[1], encoding="utf-8"))
res = []
cache = {}
def eng(name):
    if name in cache:
        return cache[name]
    if name == "rapidocr":
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError:
            from rapidocr import RapidOCR
        cache[name] = RapidOCR()
    elif name == "paddleocr":
        from paddleocr import PaddleOCR
        cache[name] = PaddleOCR(use_angle_cls=True, lang="chinese_cht", show_log=False)
    elif name == "easyocr":
        import easyocr
        cache[name] = easyocr.Reader(["ch_tra", "en"], gpu=False)
    else:
        cache[name] = None
    return cache[name]
for j in jobs:
    lines, err = [], ""
    try:
        if j["engine"] == "tesseract":
            import pytesseract
            from PIL import Image
            d = pytesseract.image_to_data(Image.open(j["img"]), lang=j.get("lang", "eng"), output_type=pytesseract.Output.DICT, config="--psm 6")
            grp = {}
            for i, t in enumerate(d["text"]):
                if str(t).strip():
                    k = (d["block_num"][i], d["par_num"][i], d["line_num"][i])
                    g = grp.setdefault(k, {"t": [], "c": [], "box": [10**9, 10**9, 0, 0]})
                    g["t"].append(t); g["c"].append(max(0.0, float(d["conf"][i])) / 100.0)
                    x, y, w, h = d["left"][i], d["top"][i], d["width"][i], d["height"][i]
                    b = g["box"]; g["box"] = [min(b[0], x), min(b[1], y), max(b[2], x + w), max(b[3], y + h)]
            for k in sorted(grp, key=lambda k: (grp[k]["box"][1], grp[k]["box"][0])):
                g = grp[k]; lines.append({"text": " ".join(g["t"]), "conf": sum(g["c"]) / len(g["c"]), "box": g["box"]})
        elif j["engine"] == "rapidocr":
            r, _ = eng("rapidocr")(j["img"])
            for box, text, score in (r or []):
                xs = [p[0] for p in box]; ys = [p[1] for p in box]
                lines.append({"text": text, "conf": float(score), "box": [min(xs), min(ys), max(xs), max(ys)]})
        elif j["engine"] == "paddleocr":
            r = eng("paddleocr").ocr(j["img"], cls=True)
            for page in (r or []):
                for box, (text, score) in (page or []):
                    xs = [p[0] for p in box]; ys = [p[1] for p in box]
                    lines.append({"text": text, "conf": float(score), "box": [min(xs), min(ys), max(xs), max(ys)]})
        elif j["engine"] == "easyocr":
            for box, text, score in eng("easyocr").readtext(j["img"]):
                xs = [p[0] for p in box]; ys = [p[1] for p in box]
                lines.append({"text": text, "conf": float(score), "box": [min(xs), min(ys), max(xs), max(ys)]})
        lines.sort(key=lambda l: (round(l["box"][1] / 8), l["box"][0]))
    except Exception as e:
        err = type(e).__name__ + ":" + str(e)[:120]
    res.append({"id": j["id"], "engine": j["engine"], "dpi": j["dpi"], "lines": lines, "err": err})
json.dump(res, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False)
'''
_LIGHT, _HEAVY = ("rapidocr", "tesseract"), ("paddleocr", "easyocr")


def ocr_probe() -> dict:
    cfg = (_resolve("config_get") or (lambda: {}))()
    cands = [sys.executable] + [x for x in [cfg.get("ocr_python")] if x]
    up = Path(os.environ.get("USERPROFILE", str(Path.home())))
    for p in (up / "envs" / "via_vrn_312" / "Scripts" / "python.exe", up / "envs" / "via_vrn_312" / "bin" / "python"):
        if p.exists():
            cands.append(str(p))
    seen, runtimes = set(), []
    for py in cands:
        if py in seen or not Path(py).exists():
            continue
        seen.add(py)
        try:
            r = subprocess.run([py, "-c", _PROBE_CODE], capture_output=True, text=True, timeout=90)
            runtimes.append(json.loads(r.stdout.strip().splitlines()[-1]))
        except Exception as exc:  # noqa: BLE001
            runtimes.append({"python": py, "engines": {}, "err": type(exc).__name__})
    avail = {}
    for rt in runtimes:
        for name, e in rt.get("engines", {}).items():
            if e.get("ok") and name not in avail:
                avail[name] = {"python": rt["python"], **e}
    return {"runtimes": runtimes, "avail": avail}


def _tess_lang(probe: dict, mode: str) -> str:
    langs = (probe["avail"].get("tesseract") or {}).get("langs", [])
    use = [l for l in ("chi_tra", "eng") if l in langs]
    return "+".join(use) or "eng"


def ocr_plan(region: dict, avail: dict) -> list:
    """自動選工具:輕 1(單引擎)→ 輕 2(雙引擎投票)→ 重(結構化);表格 / 小字提高 DPI。"""
    small = region.get("small_font", False)
    base = 400 if (region["mode"] == "table" or small) else 300
    light = [e for e in _LIGHT if e in avail]
    heavy = [e for e in _HEAVY if e in avail]
    plan = []
    if light:
        plan.append(("輕型·單引擎", light[0], base))
    if len(light) >= 2:
        plan.append(("輕型·雙引擎", light[1], max(base, 400)))
    if heavy:
        plan.append(("重型", heavy[0], 500))
    return plan


def _render(pdf_path: str, local_page: int, bbox: list, dpi: int, out: Path) -> str:
    import pypdfium2 as pdfium  # noqa: WPS433
    doc = pdfium.PdfDocument(pdf_path)
    pg = doc[local_page - 1]
    W, H = pg.get_size()
    area_px = ((bbox[2] - bbox[0]) * dpi / 72) * ((bbox[3] - bbox[1]) * dpi / 72)
    if area_px > 25e6:
        dpi = int(dpi * (25e6 / area_px) ** 0.5)
    sc = dpi / 72.0
    img = pg.render(scale=sc, crop=(max(0, bbox[0] - 2), max(0, H - bbox[3] - 2), max(0, W - bbox[2] - 2), max(0, bbox[1] - 2))).to_pil()
    img.save(out)
    return str(out)


_CONFUSE = str.maketrans({"O": "0", "o": "0", "l": "1", "I": "1", "|": "1", "S": "5", "B": "8", "，": ",", "。": "."})


def ocr_fix_numbers(text: str) -> tuple:
    fixes = 0

    def fx(m):
        nonlocal fixes
        s = m.group(0)
        t = s.translate(_CONFUSE)
        if t != s:
            fixes += 1
        return t
    out = re.sub(r"(?<![A-Za-z])[\(\-]?[\dOolIS|B]{1,3}(?:[,，][\dOolIS|B]{3})+(?:[.。][\dOolIS|B]+)?\)?(?![A-Za-z])|(?<![A-Za-z])\d+[.。][\dOolIS]+(?![A-Za-z])", fx, text)
    return out, fixes


def ocr_verify(region: dict, lines: list) -> dict:
    txt = " ".join(l["text"] for l in lines)
    conf = (sum(l["conf"] for l in lines) / len(lines)) if lines else 0.0
    v = {"conf": round(conf, 3), "lines": len(lines), "chars": len(re.sub(r"\s", "", txt))}
    if region["mode"] == "table":
        nums = [n for l in lines for n in re.findall(r"[\(\-]?\d[\d,]*\.?\d*\)?%?", l["text"])]
        v["numbers"] = len(nums)
        per = [len(re.findall(r"[\(\-]?\d[\d,]*\.?\d*\)?%?", l["text"])) for l in lines if re.search(r"\d", l["text"])]
        mode_n = Counter(per).most_common(1)[0][0] if per else 0
        v["col_consistency"] = round(sum(1 for n in per if n == mode_n) / len(per), 2) if per else 0.0
        v["years"] = len(_YR158.findall(txt))
        native = [c for r in region.get("native_rows") or [] for c in r[1:] if c and parse_number_v158(c) is not None]
        if native:
            ocr_set = Counter(re.sub(r"[^\d.\-]", "", n) for n in nums)
            nat_set = Counter(re.sub(r"[^\d.\-]", "", n) for n in native)
            v["native_match"] = round(sum(min(ocr_set[k], nat_set[k]) for k in nat_set) / max(1, sum(nat_set.values())), 3)
        v["ok"] = conf >= 0.85 and v["numbers"] >= 4 and v["col_consistency"] >= 0.7 and v.get("native_match", 1.0) >= 0.9
    else:
        v["ok"] = conf >= 0.85 and v["chars"] >= 4
    return v


def ocr_stage(regions: list, probe: dict, tmp_root: str) -> dict:
    avail = probe["avail"]
    out_dir = Path(tmp_root) / "ocr"
    out_dir.mkdir(parents=True, exist_ok=True)
    state = {r["rid"]: {"region": r, "tries": [], "status": "SKIP_NO_TOOL" if not ocr_plan(r, avail) else "PENDING"} for r in regions}
    stages = {}
    for r in regions:
        for k, (stage, engine, dpi) in enumerate(ocr_plan(r, avail)):
            stages.setdefault(k, []).append((r["rid"], stage, engine, dpi))
    for k in sorted(stages):
        todo = [(rid, st, en, dpi) for rid, st, en, dpi in stages[k] if state[rid]["status"] == "PENDING"]
        if not todo:
            continue
        by_py = defaultdict(list)
        for rid, st, en, dpi in todo:
            r = state[rid]["region"]
            img = out_dir / ("%s_%s_%d.png" % (rid, en, dpi))
            try:
                _render(r["pdf"], r["local"], r["bbox"], dpi, img)
            except Exception as exc:  # noqa: BLE001
                state[rid]["tries"].append({"stage": st, "engine": en, "dpi": dpi, "err": "render:%s" % type(exc).__name__})
                continue
            by_py[avail[en]["python"]].append({"id": rid, "img": str(img), "engine": en, "dpi": dpi, "lang": _tess_lang(probe, r["mode"]), "stage": st})
        for py, jobs in by_py.items():
            jf, rf = out_dir / ("jobs_%d_%s.json" % (k, hashlib.md5(py.encode()).hexdigest()[:6])), out_dir / ("res_%d_%s.json" % (k, hashlib.md5(py.encode()).hexdigest()[:6]))
            jf.write_text(json.dumps(jobs, ensure_ascii=False), encoding="utf-8")
            wf = out_dir / "_ocr_worker.py"
            wf.write_text(_WORKER_CODE, encoding="utf-8")
            env = dict(os.environ, OMP_NUM_THREADS="2", ORT_NUM_THREADS="2")
            try:
                subprocess.run([py, str(wf), str(jf), str(rf)], capture_output=True, text=True, timeout=1800, env=env)
                got = json.loads(rf.read_text(encoding="utf-8")) if rf.exists() else []
            except Exception as exc:  # noqa: BLE001
                got = [{"id": j["id"], "engine": j["engine"], "dpi": j["dpi"], "lines": [], "err": type(exc).__name__} for j in jobs]
            stg = {j["id"]: j["stage"] for j in jobs}
            for g in got:
                s = state[g["id"]]
                fixed = 0
                for l in g["lines"]:
                    l["text"], n = ocr_fix_numbers(l["text"]) if s["region"]["mode"] == "table" else (l["text"], 0)
                    fixed += n
                v = ocr_verify(s["region"], g["lines"])
                s["tries"].append({"stage": stg[g["id"]], "engine": g["engine"], "dpi": g["dpi"], "verify": v, "fixes": fixed, "err": g.get("err", ""), "lines": g["lines"][:200]})
                prev = [t for t in s["tries"][:-1] if t.get("verify")]
                if prev and stg[g["id"]] == "輕型·雙引擎":
                    import difflib
                    a = re.sub(r"\s", "", " ".join(l["text"] for l in prev[-1].get("lines", [])))
                    b = re.sub(r"\s", "", " ".join(l["text"] for l in g["lines"]))
                    agree = difflib.SequenceMatcher(None, a, b).ratio() if a or b else 0.0
                    s["tries"][-1]["agree"] = round(agree, 3)
                    if agree >= 0.9 and (v["ok"] or prev[-1]["verify"]["ok"]):
                        s["status"] = "ACCEPTED"
                        continue
                if v["ok"] and stg[g["id"]] != "輕型·雙引擎":
                    s["status"] = "ACCEPTED"
        for rid, st, en, dpi in todo:
            if state[rid]["status"] == "PENDING" and k == max(stages):
                state[rid]["status"] = "REVIEW"
    for s in state.values():
        if s["status"] == "PENDING":
            s["status"] = "REVIEW" if s["tries"] else "SKIP_NO_TOOL"
        best = max((t for t in s["tries"] if t.get("verify")), key=lambda t: (t["verify"]["ok"], t["verify"]["conf"]), default=None)
        s["best"] = {k: best[k] for k in ("stage", "engine", "dpi", "verify", "fixes")} if best else None
        s["text"] = "\n".join(l["text"] for l in (best or {}).get("lines", []))[:4000]
    return state


def tool_request(probe: dict, tr_ok: bool) -> dict:
    need = []
    if not tr_ok:
        need.append({"pip": "pymupdf", "for": "第二步 TableRepair 雙讀(表格還原修正)", "python": sys.executable})
    av = probe["avail"]
    if "rapidocr" not in av:
        need.append({"pip": "rapidocr_onnxruntime", "for": "第三步 輕型 OCR 引擎一(中英 · CPU)", "python": sys.executable})
    t = next((rt["engines"].get("tesseract") for rt in probe["runtimes"] if rt.get("engines", {}).get("tesseract")), None)
    if not t:
        need.append({"pip": "pytesseract", "binary": "Tesseract-OCR 5(UB-Mannheim Windows 版)", "for": "第三步 輕型 OCR 引擎二(雙引擎投票)", "python": sys.executable})
    elif not t.get("ok"):
        need.append({"binary": "Tesseract-OCR 5(UB-Mannheim Windows 版)", "for": "第三步 輕型 OCR 引擎二:pytesseract 在但找不到執行檔", "python": sys.executable})
    elif "chi_tra" not in (t.get("langs") or []):
        need.append({"tessdata": "chi_tra.traineddata", "for": "第三步 tesseract 繁中", "python": sys.executable})
    if not any(h in av for h in _HEAVY):
        need.append({"pip": "paddleocr paddlepaddle(或 easyocr)", "for": "第四步 重型 OCR(結構化表格)", "python": sys.executable, "note": "重型套件大,建議裝在獨立 OCR 環境,再用 VRN 設定冊 ocr_python 指過去"})
    reg = _home() / "registry"
    reg.mkdir(exist_ok=True)
    hits = sorted(reg.glob("VRN_ToolRequest_v*.json"), key=lambda q: _vnum_v0158(q.stem))
    prev = json.loads(hits[-1].read_text(encoding="utf-8")).get("need") if hits else None
    fname = hits[-1].name if hits else ""
    if need and prev != need:
        nv = "v%04d" % ((_vnum_v0158(hits[-1].stem) + 1) if hits else 100)
        fp = reg / ("VRN_ToolRequest_%s.json" % nv)
        fp.write_text(json.dumps({"schema": "VIA.VRN.ToolRequest.v1", "to": "VCGC", "from": "VRN_SystemManager_v0158", "ts": datetime.datetime.now().isoformat(timespec="seconds"), "rule": "VRN 不自己裝工具;缺的由 VCGC 安裝(操作員 2026-10-10)", "need": need}, ensure_ascii=False, indent=1), encoding="utf-8")
        fname = fp.name
    return {"need": need, "file": fname}


# ───────── SUMMARIZER 閘:文字與表格都還原過才放行(OCR 區也要 ACCEPTED)─────────
_SUMZ_VERBS = ("summarize", "summarizer", "summary", "brief", "digest", "fourpoint", "sumz")


def summarizer_gate(l2: list, ocr: dict) -> dict:
    by_file = defaultdict(list)
    for s in ocr.values():
        by_file[s["region"]["file"]].append(s["status"])
    rows = {}
    for r in l2:
        if "cov_min" not in r:
            continue
        o = by_file.get(r["file"], [])
        ocr_ok = all(x == "ACCEPTED" for x in o)
        allowed = bool(r.get("text_ok") and r.get("table_ok") and ocr_ok)
        rows[r["file"]] = {"allowed": allowed, "text_ok": r.get("text_ok"), "table_ok": r.get("table_ok"), "ocr": dict(Counter(o)), "why": "" if allowed else "; ".join(x for x in (("文字未還原" if not r.get("text_ok") else ""), ("表格未還原" if not r.get("table_ok") else ""), ("OCR 區未接受" if not ocr_ok else "")) if x)}
    gate = {"rule": "文字還原過 且 表格還原過 且 OCR 區全接受 → 才可啟動 SUMMARIZER(操作員 2026-10-10)", "run_id": _RUN["id"], "ts": datetime.datetime.now().isoformat(timespec="seconds"), "files": rows, "allowed": sum(1 for v in rows.values() if v["allowed"]), "total": len(rows)}
    p = _rep() / "layout" / "SUMMARIZER_GATE.json"
    p.write_text(json.dumps(gate, ensure_ascii=False, indent=1), encoding="utf-8")
    gate["path"] = str(p)
    return gate


# ───────── 頁:第二步(加雙讀 · 計時)· 第三步 OCR · 交互驗證(券商大小寫 / 檔名缺券商由頁尾補 / 價格庫過舊)─────────
def _step2_page(l2: list, s: dict) -> str:
    page, link = _resolve("_page"), _resolve("_link")
    rows = []
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2, "GRAY": 3}
    for r in sorted(l2, key=lambda x: (order.get(x.get("lamp"), 9), x.get("file", ""))):
        if "cov_min" not in r:
            rows.append(("RED", [r.get("file", ""), "—", "—", "—", "—", "—", "—", "—", "—", "; ".join(r.get("notes", []))]))
            continue
        inf = r["info"]
        ana = "; ".join("%s%s" % (a.get("name") or a.get("name_from_email") or "?", ("(%s)" % a["title"]) if a.get("title") else "") for a in inf.get("analysts", [])) or "—"
        rows.append((r["lamp"], [link(r), "%.2f%%%s" % (r["cov_min"], " · 全影像" if r.get("image_only") else ""), " ".join("%s%d" % kv for kv in sorted(r["units"].items())), "%d / %d" % (r["joins"], r["sus"]),
                                 "%d/%d" % (r["tables_ok"], r["tables"]), " ".join("%s%d" % kv for kv in sorted(r.get("tr_status", {}).items())) or "—", " ".join("%s×%d" % kv for kv in sorted({**r.get("verify_issues", {})}.items())) or "—",
                                 "%s / %s" % ("✓" if r["text_ok"] else "✗", "✓" if r["table_ok"] else "✗"), " ".join("%s %.0fs" % kv for kv in sorted(r.get("timing", {}).items(), key=lambda kv: -kv[1])[:3]),
                                 "%s · %s · TP %s · 收 %s" % (ana, inf.get("rating") or "—", inf.get("tp") or "—", inf.get("close") or "—")]))
    meta = "%s · 處理 %d · 第二步成功 %d(文字 %d · 表格 %d)· 表 %d(過 %d · 雙讀一致 %d · 雙讀待審 %d)· %s · %.0f 秒 · 結果在 TEMP(run %s)" % (s["ts"], s["staged"], s["ok"], s["text_ok"], s["table_ok"], s["tables"], s["tables_ok"], s["tr_pass"], s["tr_review"], html.escape(s["mode"]), s["secs"], _RUN["id"])
    p = _rep() / "layout" / "STEP2_latest.html"
    p.write_text(page("第二步 · LAYOUT NON-OCR 識別 · 文字還原 / 表格還原(TableRepair 雙讀)/ 修復與驗證", meta, ["檔(點開看版面)", "文字覆蓋", "單位", "連接斷句 / 疑錯接", "表過", "雙讀(TableRepair)", "未過原因", "文字 / 表格", "耗時前三", "資訊區"], rows), encoding="utf-8")
    return str(p)


def _step3_page(ocr: dict, probe: dict, req: dict) -> str:
    page = _resolve("_page")
    rows = []
    for s in sorted(ocr.values(), key=lambda s: (s["status"] != "REVIEW", s["region"]["file"], s["region"]["page"])):
        r, b = s["region"], s.get("best") or {}
        v = b.get("verify") or {}
        lamp = {"ACCEPTED": "GREEN", "REVIEW": "YELLOW", "SKIP_NO_TOOL": "GRAY"}.get(s["status"], "RED")
        tries = " → ".join("%s %s@%d%s" % (t["stage"], t["engine"], t["dpi"], (" 合 %.2f" % t["agree"]) if "agree" in t else "") for t in s["tries"]) or "—"
        rows.append((lamp, [r["file"], "P%d %s" % (r["page"], r.get("id", "")), "%s · %s" % (r["kind"], r["mode"]), r["why"], tries, v.get("conf", "—"), " · ".join("%s %s" % (k, v[k]) for k in ("numbers", "col_consistency", "years", "native_match") if k in v) or "—", b.get("fixes", 0), s["status"], s.get("text", "")[:120]]))
    av = probe["avail"]
    meta = "工具:%s · VCGC 安裝請求 %s(%d 項)· DPI:輕型 300(表格 / 小字 400)· 雙引擎 ≥400 · 重型 500" % (" ".join("%s@%s" % (k, Path(v["python"]).name) for k, v in av.items()) or "無", html.escape(req.get("file") or "—"), len(req.get("need", [])))
    p = _rep() / "layout" / "STEP3_latest.html"
    p.write_text(page("第三步 輕型 OCR(單引擎 → 雙引擎)· 第四步 重型 OCR · 自動選工具 · 還原修正驗證", meta, ["檔", "頁 · 區", "類型 · 模式", "為何要 OCR", "執行(階段 引擎@DPI)", "信心", "驗證", "數字修正", "狀態", "文字預覽"], rows), encoding="utf-8")
    return str(p)


def _xcheck_page(l2: list, xc: dict, s: dict) -> str:
    page, link = _resolve("_page"), _resolve("_link")
    rows = []
    order = {"RED": 0, "YELLOW": 1, "GREEN": 2, "GRAY": 3}
    mark = lambda v: "✓" if v else ("✗" if v is False else "—")  # noqa: E731
    for r in sorted(l2, key=lambda x: x.get("file", "")):
        if "cov_min" not in r:
            continue
        x, inf = xc.get(r["path"], {}), r["info"]
        fb, ft = (r["broker"] or "").upper(), (r["footer_broker"] or "").upper()
        doms = sorted({(a.get("domain_broker") or "").upper() for a in inf.get("analysts", []) if a.get("domain_broker")})
        broker_note = ""
        if not fb and (ft or doms):
            broker_note = "檔名無券商 → 由%s補 %s" % ("頁尾" if ft else "電郵網域", ft or doms[0])
        checks = {"代號首頁": r["confirm"].get("代號"), "代號在清單": x.get("in_master"), "名稱": x.get("name_ok") if x.get("in_master") else r["confirm"].get("名稱"),
                  "頁尾券商": (ft == fb) if (ft and fb) else None, "電郵網域券商": (fb in doms) if (doms and fb) else None, "首頁日期": (inf.get("date_p1") == r["date"]) if (inf.get("date_p1") and r["date"]) else None, "收盤 vs DB": x.get("close_ok")}
        bad = [k for k, v in checks.items() if v is False]
        lamp = "YELLOW" if bad else ("GREEN" if any(v for v in checks.values()) else "GRAY")
        rows.append((lamp, [link(r), "%s %s · 首頁%s · 清單%s" % (r["code"], r["yf"], mark(checks["代號首頁"]), mark(checks["代號在清單"])), "%s · %s%s" % (r["name"] or "—", x.get("master_name") or "—", mark(checks["名稱"])),
                            "檔名 %s · 頁尾 %s%s · 網域 %s%s%s" % (fb or "—", ft or "—", mark(checks["頁尾券商"]), ",".join(doms) or "—", mark(checks["電郵網域券商"]), (" · " + broker_note) if broker_note else ""),
                            "%s · 首頁 %s%s" % (r["date"] or "—", inf.get("date_p1") or "—", mark(checks["首頁日期"])), "%s%s" % (inf.get("rating") or "—", (" ← " + inf["rating_raw"]) if inf.get("rating_raw") and inf.get("rating_raw") != inf.get("rating") else ""),
                            inf.get("tp") or "—", x.get("tp_adj") or "—", "%s · DB %s(%s)%s" % (inf.get("close") or "—", x.get("close_before") or "—", x.get("date_before") or "—", mark(checks["收盤 vs DB"])),
                            "%s(%s)" % (round(x["adj_before"], 2) if x.get("adj_before") else "—", x.get("date_before") or "—"), "%s(%s)" % (round(x["adj_latest"], 2) if x.get("adj_latest") else "—", x.get("date_latest") or "—"), "; ".join(bad) or x.get("note", "")]))
    rows.sort(key=lambda x: (order.get(x[0], 9), x[1][0]))
    p = _rep() / "layout" / "XCHECK_latest.html"
    p.write_text(page("交互驗證 · 檔名 ↔ 首頁 ↔ 頁尾/電郵 ↔ 資料庫", "%s · 價格表 %s · 總清單 %d 碼 · 價格庫比報告日舊 >7 天的不比收盤 / TP(adj)" % (s["ts"], html.escape(s["price_src"]), s["master_n"]),
                     ["檔", "代號(yfinance)", "名稱(清單)", "券商(檔名 · 頁尾 · 電郵網域)", "報告日", "評等", "目標價", "TP(adj)", "收盤 vs DB 報告日前", "adj close 報告日前", "最新 adj close", "不符 / 註"], rows), encoding="utf-8")
    return str(p)


# ───────── 引擎稽核:略過 _quarantine* / tests;加入 intake 的 TableRepair ─────────
_PREV_EA = _resolve("engines_audit")


def engines_audit_v158(register: bool = False) -> dict:
    o = _PREV_EA(register)
    keep = [r for r in o["rows"] if not re.search(r"(^|[\\/])(_quarantine[^\\/]*|tests)[\\/]", r["tail"]) and not r["family"].startswith(("test_", "UserTest-"))]
    home = _home()
    acc = re.compile(r"\[VIA:ACCEL-BRIDGE")
    for p in sorted((home / "intake" / "VRN_TableRepair").glob("VRN_Table*_v*.py")) if (home / "intake" / "VRN_TableRepair").is_dir() else []:
        fam = re.sub(r"_v\d{4}$", "", p.stem)
        if any(r["family"] == fam for r in keep):
            continue
        fams = sorted((home / "intake" / "VRN_TableRepair").glob(fam + "_v*.py"), key=lambda q: _vnum_v0158(q.stem))
        tail = fams[-1]
        keep.append({"family": fam, "ext": ".py", "tail": str(tail.relative_to(home)), "n": len(fams), "version": True, "registered": register, "accel": bool(acc.search(tail.read_text(encoding="utf-8", errors="replace"))), "pipeline": "第二步表格還原修正(雙讀)", "sha8": hashlib.sha256(tail.read_bytes()).hexdigest()[:8]})
    for r in keep:
        r["lamp"] = "GREEN" if r["version"] and r["registered"] and r["accel"] else ("YELLOW" if r["accel"] else "RED")
    py = [r for r in keep if r["ext"] == ".py"]
    psr = [r for r in keep if r["ext"] == ".ps1"]
    s = dict(o["summary"], families=len(keep), py=len(py), ps1=len(psr), no_version=sum(1 for r in keep if not r["version"]), not_registered=sum(1 for r in keep if not r["registered"]), no_accel_py=sum(1 for r in py if not r["accel"]), no_accel_ps=sum(1 for r in psr if not r["accel"]), excluded=len(o["rows"]) - len([r for r in keep if r["pipeline"] != "第二步表格還原修正(雙讀)"]))
    page = _resolve("_page")
    mark = lambda v: "✓" if v else "✗"  # noqa: E731
    Path(o["html"]).write_text(page("VRN 引擎稽核 · 版本 · 註冊(VRN SSOT)· 加速器(PY / PS)", "族 %d(py %d · ps1 %d · 略過隔離區與測試 %d)· 無版號 %d · 未註冊 %d · py 無加速器 %d · ps1 無加速器 %d · 註冊冊 %s" % (s["families"], s["py"], s["ps1"], s["excluded"], s["no_version"], s["not_registered"], s["no_accel_py"], s["no_accel_ps"], html.escape(s.get("register") or "未寫(加 --register)")),
                                    ["族", "類", "尾版", "版數", "版號", "註冊", "加速器", "管線用途"], [(r["lamp"], [r["family"], r["ext"], r["tail"], r["n"], mark(r["version"]), mark(r["registered"]), mark(r["accel"]), r["pipeline"]]) for r in sorted(keep, key=lambda r: ({"RED": 0, "YELLOW": 1, "GREEN": 2}[r["lamp"]], r["family"]))]), encoding="utf-8")
    return {"summary": s, "rows": keep, "html": o["html"]}


_patch("engines_audit", engines_audit_v158)


# ───────── 總流程 ─────────
def layout_run_v158(d: Path, opts: dict) -> dict:
    gc = temp_gc()
    o = _resolve("layout_run_v157")(d, opts)
    l2 = o["rows"]
    s = o["summary"]
    s["tr_pass"] = sum(r.get("tr_status", {}).get("PASS", 0) + r.get("tr_status", {}).get("PASS_SOFT", 0) for r in l2)
    s["tr_review"] = sum(r.get("tr_status", {}).get("REVIEW", 0) for r in l2)
    T = Counter()
    for r in l2:
        for k, v in (r.get("timing") or {}).items():
            T[k] += v
    s["timing"] = dict(T)
    regions = []
    mini = {r["path"]: (r.get("mini") or r.get("src_pdf") or r["path"]) for r in o["stage"]["rows"]}
    for r in l2:
        for rg in r.get("ocr_regions", []):
            rg = dict(rg, pdf=mini.get(r["path"], r["path"]), rid="%s_%s" % (hashlib.sha256(r["path"].encode("utf-8")).hexdigest()[:6], re.sub(r"\W", "", rg["id"])))
            regions.append(rg)
    for st in o["stage"]["rows"]:
        if st.get("code") and "掃描件" in st.get("status", "") and str(st.get("path", "")).lower().endswith(".pdf"):
            try:
                import pdfplumber
                with pdfplumber.open(st["path"]) as pdf:
                    W, H = float(pdf.pages[0].width), float(pdf.pages[0].height)
                regions.append({"file": st["file"], "page": 1, "local": 1, "bbox": [0, 0, W, H], "kind": "page", "mode": "text", "id": "P1·全頁", "why": "掃描件首頁(無文字層)", "pdf": st["path"], "rid": "%s_P1" % hashlib.sha256(st["path"].encode("utf-8")).hexdigest()[:6]})
            except Exception:  # noqa: BLE001
                pass
    probe = ocr_probe()
    ocr = ocr_stage(regions, probe, o["stage"]["temp"]) if (regions and not opts.get("no_ocr")) else {}
    req = tool_request(probe, bool(tablerepair().get("ok")))
    gate = summarizer_gate(l2, ocr)
    xc = o["xc"]
    pages = dict(o["pages"], step2=_step2_page(l2, s), step3=_step3_page(ocr, probe, req), xcheck=_xcheck_page(l2, xc, s))
    return dict(o, pages=pages, ocr=ocr, probe=probe, req=req, gate=gate, gc=gc, regions=regions)


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default
    if args[:1] and args[0] in _SUMZ_VERBS:
        gp = _rep() / "layout" / "SUMMARIZER_GATE.json"
        g = json.loads(gp.read_text(encoding="utf-8")) if gp.exists() else {}
        if not g or not g.get("allowed"):
            print("[計] SUMMARIZER 閘 · 拒絕啟動 · %s · RED" % ("還沒跑第二步" if not g else "允許 0/%d(文字與表格都還原過才放行)" % g.get("total", 0)))
            print("NEXT: 先跑 layout,文字與表格還原都過的檔才可以 summarizer")
            return 2
        os.environ["VRN_SUMMARIZER_ALLOWED"] = json.dumps([f for f, v in g["files"].items() if v["allowed"]], ensure_ascii=False)
        print("[計] SUMMARIZER 閘 · 允許 %d/%d(只放行還原過的檔)· GREEN" % (g["allowed"], g["total"]))
        return PRIOR.main(args)
    if args[:1] == ["layout"] and len(args) >= 2 and "--dir" not in args and Path(args[-1]).is_dir():
        args = args[:-1] + ["--dir", args[-1]]
    cfg = (_resolve("config_get") or (lambda: {}))()
    if args[:1] == ["layout"]:
        w = int(opt("--workers", "0") or 0) or max(1, min(3, (os.cpu_count() or 2) - 1))
        o = layout_run_v158(Path(opt("--dir") or cfg.get("input_dir") or r"C:\測試樣本報告"), {"workers": w, "tabula": "--tabula" in args, "max": int(opt("--max", "0") or 0), "only": opt("--only", "") or "", "no_ocr": "--no-ocr" in args})
        s, e = o["summary"], o["summary"]["e394"]
        tr = tablerepair()
        print("[計] 第一步 · 檔 %d · 個股報告處理 %d · 分類器 %s · TEMP 本輪 %s(清舊 %d 輪 · 釋放 %s MB · 保留 %d)" % (len(o["stage"]["rows"]), s["staged"], Path(s["classifier"]).name if ("\\" in s["classifier"] or "/" in s["classifier"]) else s["classifier"], o["gc"]["run_id"], o["gc"]["removed"], o["gc"]["freed_mb"], o["gc"]["kept"]))
        tops = " · ".join("%s %.0fs" % kv for kv in sorted(s["timing"].items(), key=lambda kv: -kv[1])[:4])
        print("[計] 第二步 LAYOUT NON-OCR · 成功 %d/%d(文字 %d · 表格 %d)· 表 %d 過 %d(TableRepair 雙讀一致 %d · 待審 %d)· 修補 %d · 疑錯接 %d · %s · %.0f 秒(%s)· %s" % (s["ok"], s["staged"], s["text_ok"], s["table_ok"], s["tables"], s["tables_ok"], s["tr_pass"], s["tr_review"], s["repairs"], s["sus"], s["mode"], s["secs"], tops, "GREEN" if s["ok"] == s["staged"] and s["staged"] else "YELLOW"))
        vi = Counter()
        tri = Counter()
        for r in o["rows"]:
            vi.update(r.get("verify_issues", {}))
            tri.update(r.get("tr_issues", {}))
        if vi:
            print("[計] 表格未過原因 · %s" % " · ".join("%s×%d" % kv for kv in vi.most_common(6)))
        if tri:
            print("[計] TableRepair 雙讀問題 · %s" % " · ".join("%s×%d" % kv for kv in tri.most_common(6)))
        oc = Counter(x["status"] for x in o["ocr"].values())
        av = o["probe"]["avail"]
        print("[計] 第三 / 四步 OCR · 候選區 %d(圖 %d · 表 %d · 掃描頁 %d)· 工具 %s · 接受 %d · 待審 %d · 缺工具略過 %d" % (len(o["regions"]), sum(1 for r in o["regions"] if r["kind"] == "figure"), sum(1 for r in o["regions"] if r["kind"] == "table"), sum(1 for r in o["regions"] if r["kind"] == "page"),
                                                                                                         " ".join(sorted(av)) or "無", oc.get("ACCEPTED", 0), oc.get("REVIEW", 0), oc.get("SKIP_NO_TOOL", 0)))
        for n in o["req"]["need"]:
            print("[計] 請 VCGC 安裝 · %s · 給 %s · 請求單 %s" % (n.get("pip") or n.get("binary") or n.get("tessdata"), n["for"], o["req"]["file"]))
        print("[計] SUMMARIZER 閘 · 允許 %d/%d(文字與表格都還原過 · OCR 區全接受才放行)· %s" % (o["gate"]["allowed"], o["gate"]["total"], o["gate"]["path"]))
        print("[計] ENG394 %s · _subcat %s · TableRepair %s · 價格表 %s · 總清單 %d 碼" % (e.get("file") or "無", "已接" if e.get("ok") else "未接", "已接(%s)" % "+".join(tr.get("files", [])) if tr.get("ok") else "未接 · " + tr.get("err", ""), s["price_src"], s["master_n"]))
        for k in ("step1", "step2", "step3", "xcheck"):
            print("  [U/I] %s" % o["pages"][k])
        if "--no-audit" not in args:
            ea = engines_audit_v158(register="--register" in args)
            es = ea["summary"]
            print("[計] VRN 引擎稽核 · 族 %d(py %d · ps1 %d · 略過隔離區與測試)· 無版號 %d · 未註冊 %d · py 無加速器 %d · ps1 無加速器 %d · 註冊冊 %s" % (es["families"], es["py"], es["ps1"], es["no_version"], es["not_registered"], es["no_accel_py"], es["no_accel_ps"], es.get("register") or "未寫(加 --register)"))
            for r in [r for r in ea["rows"] if r["pipeline"]]:
                print("[計] 管線 %s · %s · 版號%s 註冊%s 加速器%s" % (r["family"], r["pipeline"], "✓" if r["version"] else "✗", "✓" if r["registered"] else "✗", "✓" if r["accel"] else "✗"))
            print("  [U/I] %s" % ea["html"])
        print("NEXT: %s" % ("第二步全過 → 可啟動 SUMMARIZER" if s["ok"] == s["staged"] else "看第二步頁「未過原因」與「雙讀」欄;第三步頁看 OCR 區;缺工具照黃字請 VCGC 裝"))
        return 0
    return PRIOR.main(args)


def _mk_pdf_v158(path: Path, img_dir: Path) -> None:
    from PIL import Image, ImageDraw, ImageFont
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfgen import canvas
    from reportlab.platypus import Table, TableStyle
    cjk = "MSung-Light"
    for fp in ("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", r"C:\Windows\Fonts\msjh.ttc", r"C:\Windows\Fonts\mingliu.ttc"):
        if Path(fp).exists():
            try:
                from reportlab.pdfbase.ttfonts import TTFont
                pdfmetrics.registerFont(TTFont("CJKT8", fp, subfontIndex=0))
                cjk = "CJKT8"
                break
            except Exception:  # noqa: BLE001
                continue
    if cjk == "MSung-Light":
        pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
    W, H = A4
    c = canvas.Canvas(str(path), pagesize=A4)
    c.setFont("Helvetica", 7)
    c.drawString(40, H - 28, "KGI Research | Taiwan Equity | 2026/09/17")
    c.setFont(cjk, 20)
    c.drawString(40, H - 80, "健策 3653:液冷題材發酵 營運動能強勁")
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, H - 120, "Investment highlights")
    c.setFont("Helvetica", 9.5)
    for i, t in enumerate(("Jentech (3653 TT) benefits from liquid cooling adoption across AI servers and we", "expect revenue to grow strongly in 2026. Margins should expand as the product mix", "shifts toward vapor chambers. We reiterate our positive view on the stock.")):
        c.drawString(40, H - 140 - i * 13, t)
    c.setFont("Helvetica", 8)
    for j, (k, v) in enumerate((("Stock Rating", "Overweight"), ("Price target", "NT$1,200"), ("Price (2026/09/16)", "NT$980"), ("52-Week Range", "720-1,100"))):
        c.drawString(400, H - 120 - j * 12, k)
        c.drawRightString(560, H - 120 - j * 12, v)
    for j, t in enumerate(("Amy Wang", "Senior Analyst", "+886-2-2181-8888", "amy.wang@kgi.com")):
        c.drawString(400, H - 190 - j * 12, t)
    c.setFont("Helvetica", 6)
    c.drawString(40, 30, "KGI Securities Investment Advisory Co., Ltd. | Disclaimer: for information only.")
    c.showPage()
    c.setFont("Helvetica", 10)
    for i in range(25):
        c.drawString(40, H - 60 - i * 14, "Industry discussion paragraph %d without financial numbers." % i)
    c.showPage()
    c.setFont("Helvetica-Bold", 13)
    c.drawString(40, H - 70, "Financial summary (NT$m)")
    rows = [["Income statement", "2023A", "2024A", "2025F", "2026F"], ["Revenue", "12,345", "15,678", "19,012", "23,456"], ["Gross profit", "4,321", "5,678", "7,012", "8,765"], ["Net income", "1,876", "2,654", "3,456", "4,321"], ["EPS (NT$)", "15.2", "21.5", "28.0", "35.1"]]
    t = Table(rows, colWidths=[90, 50, 50, 50, 50])
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("FONT", (0, 0), (-1, -1), "Helvetica", 7.5)]))
    t.wrapOn(c, W, H)
    t.drawOn(c, 40, H - 200)
    img = Image.new("RGB", (1400, 320), "white")
    dr = ImageDraw.Draw(img)
    try:
        fnt = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 34)
    except OSError:
        fnt = ImageFont.load_default()
    for r_i, row in enumerate((["Balance sheet", "2023A", "2024A", "2025F"], ["Cash", "3,210", "4,321", "5,432"], ["Total assets", "20,000", "24,000", "29,000"], ["Total equity", "12,000", "14,500", "17,800"])):
        for c_i, cell in enumerate(row):
            dr.text((20 + c_i * (420 if c_i == 0 else 300) - (0 if c_i < 2 else 120 * (c_i - 1)), 20 + r_i * 72), cell, fill="black", font=fnt)
    ip = img_dir / "bs_table.png"
    img.save(ip)
    c.drawImage(str(ip), 40, H - 400, width=500, height=114)
    c.setFont("Helvetica", 6)
    c.drawString(40, 30, "KGI Securities Investment Advisory Co., Ltd.")
    c.showPage()
    c.save()


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

    td = Path(tempfile.mkdtemp(prefix="vrnl3-"))
    home = td / "functional modules" / "VRN"
    for x in ("SSOT", "knowledge", "registry", "intake/VRN_ReportClassifier", "intake/VRN_TableRepair"):
        (home / x).mkdir(parents=True, exist_ok=True)
    (td / "supportive modules" / "registry").mkdir(parents=True)
    rep = td / "VIA_Reports" / "vrn"
    base = td / "VIA"
    vdb = base / "via_database" / "vdf_database"
    vdb.mkdir(parents=True)
    spill = td / "TEMP"
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT", "VIA_VDF_HOME", "VIA_ROOTS_BASE", "VIA_SPILL_DIR", "VIA_VRN_MASTER_LISTS", "USERPROFILE")}
    os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(rep), "VIA_VDF_HOME": str(td / "nope"), "VIA_ROOTS_BASE": str(base), "VIA_SPILL_DIR": str(spill), "USERPROFILE": str(td)})
    with (vdb / "vdf_tw_all_stocks.csv").open("w", encoding="utf-8") as fh:
        fh.write("stock_id,name,market\n3653,健策,上市\n")
        for i in range(1100, 1950):
            fh.write("%d,測%d,上市\n" % (i, i))
    with (vdb / "vdf_daily_prices.csv").open("w", encoding="utf-8") as fh:
        fh.write("ticker,date,close,adj_close\n3653.TW,2026-08-24,960,950\n3653.TW,2026-08-25,970,960\n")
    (home / "knowledge" / "VRN_Broker_Dict_v0100.json").write_text(json.dumps({"brokers": {"凱基": {"abbr": "KGI", "aliases": ["凱基", "凱基投顧", "KGI", "KGI Securities"]}, "國泰": {"abbr": "CT", "aliases": ["國泰", "Cathay"]}}}, ensure_ascii=False), encoding="utf-8")
    (td / "supportive modules" / "registry" / "VIA_Central_Synonym_Regex_v0105.json").write_text(json.dumps({"synonyms": {"RATING_BUY": ["買進", "Buy", "加碼", "Overweight", "Outperform", "OW", "增持"], "RATING_HOLD": ["持有", "Hold", "中立", "Neutral", "維持", "N"], "RATING_SELL": ["賣出", "Sell", "Underweight"], "RATING_NOT_RATED": ["未評等", "NR", "Not Rated"],
                                                                                                                  "TARGET_PRICE": ["目標價", "Target Price", "Price Target", "TP", "合理價", "Target"], "TARGET_PRICE_STRIPS": ["NT$", "TWD", "元"]},
                                                                                                     "regex": {"RX_TARGET_PRICE_NTD": {"pattern": r"(?:NT\$|NT\s?\$|目標價[:：]?\s*)\s*([0-9][0-9,]*\.?\d*)"}}}, ensure_ascii=False), encoding="utf-8")
    (home / "VRN_ENG394_LayoutRestore_v0102.py").write_text("def _subcat(size: float, bold: bool, body: float, nchar: int, text: str):\n    return 'HEAD' if (size > body + 1 or bold) and nchar < 80 else 'BODY'\n", encoding="utf-8")
    for src_dir in (HERE / "intake" / "VRN_TableRepair", Path("/tmp/out")):
        for fn in ("VRN_TableGeometry_v0100.py", "VRN_TableValidation_v0100.py", "VRN_TableGeometry_v0101.py", "VRN_TableValidation_v0101.py"):
            if (src_dir / fn).exists() and not (home / "intake" / "VRN_TableRepair" / fn).exists():
                shutil.copy(src_dir / fn, home / "intake" / "VRN_TableRepair" / fn)
    for src_dir in (HERE / "intake" / "VRN_ReportClassifier", Path("/tmp/out")):
        if (src_dir / "VRN_ReportClassifier_v0101.py").exists() and not (home / "intake" / "VRN_ReportClassifier" / "VRN_ReportClassifier_v0101.py").exists():
            shutil.copy(src_dir / "VRN_ReportClassifier_v0101.py", home / "intake" / "VRN_ReportClassifier" / "VRN_ReportClassifier_v0101.py")
    spill.mkdir()
    for i in range(5):
        d = spill / ("vrn_stage_old%d" % i)
        d.mkdir()
        (d / ".vrn_owner.json").write_text("{}", encoding="utf-8")
        os.utime(d / ".vrn_owner.json", (time.time() - 3600 * (i + 1), time.time() - 3600 * (i + 1)))
    (spill / "vrn_stage_NOT_MINE").mkdir()
    inp = td / "inbox"
    inp.mkdir()
    rpt = inp / "凱基投顧_3653 健策_向子慧_20260917.pdf"
    _mk_pdf_v158(rpt, td)
    rpt2 = inp / "凱基投顧_3653 健策_copy_20260917.pdf"
    shutil.copy(rpt, rpt2)
    o = layout_run_v158(inp, {"workers": 2, "tabula": False, "max": 0, "only": "", "no_ocr": False})
    R = {r["file"]: r for r in o["rows"]}
    r = R[rpt.name]
    chk("① 多程序(spawn)走 __main__ 墊片 · 加速器執行緒上限", o["summary"]["mode"].startswith("多程序 ×2"))
    full = json.loads(Path(r["temp_json"]).read_text(encoding="utf-8"))
    tb = [b for pg in full["pages"] for b in pg["blocks"] if b["kind"] == "table" and b.get("sub", "").startswith("財務表")]
    is_rows = next((b["rows"] for b in tb if b.get("sub") == "財務表·損益"), [])
    chk("② 表格還原修正:TableRepair 雙讀一致(PyMuPDF = pdfplumber · 字詞守恆)→ 損益表過 · 5 列全在(含 EPS,裁切不掉列)", tablerepair().get("ok") and any(b.get("engine") == "TableRepair(雙讀一致)" and b["verify"]["ok"] for b in tb) and o["summary"]["tr_pass"] >= 2 and len(is_rows) == 5 and is_rows[-1][0].startswith("EPS"))
    inf = r["info"]
    chk("③ 資訊區同列配對:標籤欄 / 值欄分開排版 → 評等 Overweight(中央冊歸 Buy)· 目標價 1200 · 收盤 980(不再誤抓 52-Week 的 52)", inf["rating"] == "Buy" and inf["rating_raw"] == "Overweight" and inf["tp"] == 1200 and inf["close"] == 980)
    chk("④ 電郵名:數字 + 單段 → 不硬還原(空)· amy.wang → Amy Wang · 網域 cathaysec → CT", email_name_v158("7960minchilu") == "" and email_name_v158("amy.wang") == "Amy Wang" and _resolve("domain_broker")("cathaysec.com.tw", {}) == "CT")
    x = o["xc"][str(rpt)]
    chk("⑤ 價格庫比報告日舊(只到 08-25)→ 標過舊 · 不比收盤 · 不算 TP(adj)", x.get("stale") and x.get("close_ok") is None and x.get("tp_adj") is None and "價格庫只到" in x.get("note", ""))
    figs = [s for s in o["ocr"].values() if s["region"]["file"] == rpt.name and s["region"]["kind"] == "figure"]
    engines = {t["engine"] for s in figs for t in s["tries"]}
    best = (figs[0].get("best") or {}) if figs else {}
    t1 = figs[0]["tries"][0] if figs and figs[0]["tries"] else {}
    escalated_ok = (figs and figs[0]["status"] == "ACCEPTED" and len(figs[0]["tries"]) == 1) or ("tesseract" in engines)
    chk("⑥ 第三步 OCR:影像表格(P3 圖區無文字層)→ 自動選 輕型單引擎 rapidocr@400(表格提高 DPI)· 驗證過就不升級,沒過才雙引擎 · 數字 ≥ 4 · 狀態 %s" % (figs[0]["status"] if figs else "—"), bool(figs) and t1.get("engine") == "rapidocr" and t1.get("dpi") == 400 and escalated_ok and (best.get("verify") or {}).get("numbers", 0) >= 4)
    reg = {"rid": "x", "mode": "table", "file": "f", "page": 3, "bbox": [0, 0, 1, 1]}
    plan = ocr_plan(reg, {"rapidocr": {}, "tesseract": {}, "paddleocr": {}})
    chk("⑥b 自動選工具順序:輕型單引擎 → 輕型雙引擎 → 重型;DPI 表格 400 / 雙引擎 ≥400 / 重型 500", [(st, en, dpi) for st, en, dpi in plan] == [("輕型·單引擎", "rapidocr", 400), ("輕型·雙引擎", "tesseract", 400), ("重型", "paddleocr", 500)] and ocr_plan(dict(reg, mode="text"), {"tesseract": {}})[0][2] == 300)
    gc = o["gc"]
    left = sorted(d.name for d in spill.glob("vrn_stage_*"))
    chk("⑦ TEMP:清舊只清 VRN 標記的舊輪(5 → 留 3)· 沒標記的不碰 · 本輪目錄有標記", gc["removed"] == 2 and "vrn_stage_NOT_MINE" in left and any(_RUN["id"] in n for n in left) and (spill / ("vrn_stage_" + _RUN["id"]) / ".vrn_owner.json").exists())
    g = json.loads(Path(o["gate"]["path"]).read_text(encoding="utf-8"))
    Path(o["gate"]["path"]).write_text(json.dumps(dict(g, allowed=0)), encoding="utf-8")
    rc_refuse = main(["summarize"])
    chk("⑧ SUMMARIZER 閘:文字表格沒修好不啟動(閘 0 → 拒絕 rc 2)· 閘檔每檔列原因", rc_refuse == 2 and all("allowed" in v for v in g["files"].values()))
    req = o["req"]
    chk("⑨ 缺工具 → VCGC 安裝請求(VRN 不自己裝):重型 OCR · tesseract 繁中", req["file"].startswith("VRN_ToolRequest_v") and any("重型" in n["for"] for n in req["need"]) and any("繁中" in n["for"] for n in req["need"]))
    pages_ok = all(Path(o["pages"][k]).exists() for k in ("step1", "step2", "step3", "xcheck")) and "雙讀(TableRepair)" in Path(o["pages"]["step2"]).read_text(encoding="utf-8")
    chk("⑩ 四頁:第一步 · 第二步(雙讀 / 未過原因 / 耗時)· 第三步 OCR · 交互驗證 · 各段計時", pages_ok and set(r["timing"]) >= {"版面切割", "文字還原", "表格還原"})
    ea = engines_audit_v158()
    fams = {x["family"]: x for x in ea["rows"]}
    chk("⑪ 引擎稽核:TableRepair 兩族在列且有加速器(v0101)· 隔離區 / 測試不計", fams.get("VRN_TableGeometry", {}).get("accel") and fams.get("VRN_TableValidation", {}).get("accel") and not any(k.startswith("test_") for k in fams))
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑫ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    chk("⑬ 帶加速器橋 · 自帶多程序墊片", "[VIA:ACCEL-BRIDGE:v0100]" in Path(__file__).read_text(encoding="utf-8") and _job_entry.__module__ in ("__main__", __name__))
    for k, val in saved.items():
        if val is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = val
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0158 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
