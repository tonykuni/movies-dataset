#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# ===== [VRN:ID:v0100] VRN-ENG015 · VRN_Focus_v0100 v0100 · ENGINE =====
# AST 注入（只加註解，AST 不變）：類別 0 · 函式 19；逐一編號在 ssot/VRN_ID_SSOT_v0100.json
# ===== [VRN:ID:END] =====
"""
VRN_Focus v0100 -- only what the operator asked for is processed: the file name, page 1 and the annual financial pages of
stock reports.  Everything else is left out before any engine reads it.

Operator 2026-10-11:
  「只擷取個股報告中的FILENAME / 1ST PAGE / 年度財報頁進行處理 其他多餘的」

Rules: ssot/VRN_TitleTrim_SSOT_v0100.json "focus" (thresholds) and "annual" (statement words).
  1. file name  mother ENG393 DocClass (through VRN_PageRegions.decompose): not STOCK -> not processed, listed with the reason
  2. pages      every page of a stock-report PDF is read as text once (PyMuPDF, cheap) and TRIMmed (VRN_TitleTrim.trim):
                page 1 is kept; a page with >= 2 fiscal-year periods, >= 8 numbers and enough row labels the financial books can
                name is an annual financial page and is kept; every other page (body text, charts, disclaimers, quarter-only
                tables) is left out
  3. copy       the kept pages are saved as a focus copy under the run's TEMP folder with the same file name (same file-name
                decomposition), saved the same way every time (same pages -> same bytes); DOCX / TXT have no pages and go
                whole; a stock image goes as it is (the engines list it OCR_REQUIRED); the original is only read
  4. manifest   file -> original path, SHA-256, kept pages, focus page -> original page; the outputs are put back on the
                original page numbers with it

No engine logic changes: the engines read less, nothing else.  No network, LIVE off, no consent variable read or set.
"""

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

import argparse
import csv
import hashlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

FOCUS_VERSION = "v0100"
VRN_ROOT = Path(__file__).resolve().parents[1]
TITLETRIM_FILE = VRN_ROOT / "engine" / "VRN_TitleTrim_v0100.py"
EVIDENCE_FILE = VRN_ROOT / "engine" / "VRN_Evidence_Core.py"
MANIFEST_JSON = "VRN_Focus_Manifest_v0100.json"
MANIFEST_CSV = "VRN_Focus_Manifest_v0100.csv"
IMAGE_EXT = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp"}
TEXT_EXT = {".txt", ".docx"}


# [VRN-ID] VRN-ENG015-FNC001 · LOGIC
def _titletrim():
    name = "VRN_TitleTrim_v0100"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, TITLETRIM_FILE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-ENG015-FNC002 · LOGIC
def rules():
    T = _titletrim()
    book = T.books().book
    return book["focus"], book["annual"]


# [VRN-ID] VRN-ENG015-FNC014 · EXTRACT
def _evidence():
    """VRN_Evidence_Core：受評公司的代號規則在它身上，這裡不重寫第二套。"""
    name = "VRN_Evidence_Core"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, EVIDENCE_FILE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


# [VRN-ID] VRN-ENG015-FNC015 · LOGIC
def class_policy(focus, doc_class):
    """ENG393 的 doc_class → 這一類怎麼處理。

    判斷本體在 VRN_PageRegions.class_policy，這裡只是轉呼叫 —— 兩個地方各寫一份，
    遲早會各說各話。PageRegions 是最底層（TitleTrim 載入它），所以判斷放那裡不會成環。
    """
    T = _titletrim()
    R, _M = T.regions()
    return R.class_policy(focus, doc_class)


# [VRN-ID] VRN-ENG015-FNC016 · LOGIC
def covered_companies(texts, focus):
    """產業／展望報告涵蓋哪幾家：逐頁問 Evidence_Core.page_codes，去重後照頁序排。"""
    cfg = focus.get("coverage") or {}
    core = _evidence()
    seen, covered, pages = {}, [], []
    for pno, text in enumerate(texts, 1):
        codes = core.page_codes((text or "").splitlines())
        if len(codes) < int(cfg.get("min_codes_on_page", 1) or 1):
            continue
        pages.append(pno)
        for hit in codes:
            code = hit.get("core") or ""
            if not code or code in seen:
                continue
            seen[code] = True
            covered.append({"ticker": code, "name_on_page": hit.get("name_before") or "",
                            "market": hit.get("market") or "", "first_page": pno, "kind": hit.get("kind") or ""})
    return covered, pages


# [VRN-ID] VRN-ENG015-FNC003 · LOGIC
def _sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


# =====================================================================
# 1 . ONE PAGE: IS IT AN ANNUAL FINANCIAL PAGE?
# =====================================================================
# [VRN-ID] VRN-ENG015-FNC004 · EXTRACT
def page_kind(text):
    """Page text -> {years, labels, numbers, statements, annual, why} (TRIMmed lines; the books name the labels)."""
    T = _titletrim()
    R, M = T.regions()
    focus, annual = rules()
    th = focus["annual_page"]
    strip_rx = re.compile(focus["label_strip_rx"])
    number_rx = re.compile(focus["number_rx"])
    period_like = re.compile(focus["period_like_rx"], re.I)
    lines = [T.trim(x)["clean"] for x in str(text or "").splitlines() if x.strip()]
    years, labels, numbers = set(), set(), 0
    unparsed, unmapped = [], []                       # what a real page had that the books could not read (the fix list shows it)
    for line in lines:
        for tok in line.split():
            p = R.period_of(tok)
            if p and p.get("key") and not p.get("part"):
                years.add(p["key"])
            elif period_like.match(tok) and not (p and p.get("part")) and tok not in unparsed and len(unparsed) < 12:
                unparsed.append(tok)
        numbers += sum(1 for m in number_rx.finditer(line) if re.search(r"\d", m.group(0)))
        hit = ""
        for cand in (line, strip_rx.sub("", line).strip()):
            hit = M.ledger.lookup(cand) if cand and not re.fullmatch(r"[\W\d_]+", cand) else ""
            if hit:
                labels.add(hit)
                break
        bare = strip_rx.sub("", line).strip()
        if (not hit and 2 <= len(bare) <= 30 and re.search(r"[A-Za-z一-鿿]", bare) and not period_like.match(bare)
                and not R.period_of(bare) and bare not in unmapped and len(unmapped) < 15):
            unmapped.append(bare)
    fold = T.trim(" ".join(lines))["fold"]
    statements = sorted(k for k, words in annual["statement_words"].items() if any(w.casefold() in fold for w in words))
    enough_labels = len(labels) >= th["min_labels"] or (statements and len(labels) >= th["statement_min_labels"])
    is_annual = len(years) >= th["min_years"] and numbers >= th["min_numbers"] and bool(enough_labels)
    why = (f"年度期別 {len(years)}（{', '.join(sorted(years)[:6])}）· 數字 {numbers} · 對得到的列標 {len(labels)}"
           + (f" · 報表名稱 {'/'.join(statements)}" if statements else ""))
    return {"years": sorted(years), "labels": sorted(labels), "numbers": numbers, "statements": statements, "annual": is_annual,
            "why": why, "unparsed_periods": unparsed, "unmapped_labels": unmapped}


# =====================================================================
# 2 . ONE FILE: WHAT IS KEPT
# =====================================================================
# [VRN-ID] VRN-ENG015-FNC005 · LOGIC
def plan(path, name=None):
    """-> {file, doc_class, kept (bool), mode (PAGES / WHOLE / NONE), why, pages_total, keep (1-based), pages [...]}."""
    T = _titletrim()
    R, M = T.regions()
    focus, _annual = rules()
    path = Path(path)
    name = name or path.name
    suffix = Path(name).suffix.lower()
    dec = R.decompose(M, name)
    cls = dec.get("doc_class") or ""
    rule = class_policy(focus, cls)
    process = rule.get("process") or "SKIP"
    out = {"file": name, "original": str(path), "doc_class": cls, "class_rule": dec.get("class_rule") or "",
           "kept": False, "mode": "NONE", "why": "", "pages_total": None, "keep": [], "pages": [], "review": "",
           "process": process, "rows": rule.get("rows") or "ONE_PER_REPORT", "covered": []}
    if process == "SKIP":
        out["why"] = f"ENG393 DocClass {cls or '?'} · {dec.get('class_rule') or ''}：{rule.get('why') or '不處理'}"
        return out
    if suffix in IMAGE_EXT:
        out.update(kept=True, mode="WHOLE", why=focus["images"] if process == "FULL" else
                   f"{cls}（{process}）：影像整份帶過去取後設資料（引擎照實列 OCR_REQUIRED）")
        return out
    if suffix in TEXT_EXT:
        out.update(kept=True, mode="WHOLE", why=focus["text_files"] if process == "FULL" else
                   f"{cls}（{process}）：DOCX／TXT 沒有頁，整份帶過去")
        return out
    if suffix != ".pdf":
        out["why"] = f"{suffix} 不在 PDF / DOCX / TXT / 影像：不處理"
        return out
    try:
        import fitz  # type: ignore
        with fitz.open(str(path)) as doc:
            texts = [page.get_text("text") for page in doc]
    except Exception as error:  # noqa: BLE001
        out.update(kept=True, mode="WHOLE", why=focus["scan_error"], review=f"掃頁失敗 {error.__class__.__name__}: {error}"[:200])
        return out
    out["pages_total"] = len(texts)
    if process == "REGISTER":
        # 只分類登錄：留首頁取後設資料（檔名、型別、報告日、券商、頁數），不抽財務。
        out.update(kept=True, mode="PAGES", keep=[1],
                   why=f"{cls}（REGISTER）：只留首頁登錄報告層，不抽財務數字與目標價評等；全文 {len(texts)} 頁")
        return out
    if process == "COVERAGE":
        cfg = focus.get("coverage") or {}
        covered, code_pages = covered_companies(texts, focus)
        keep = sorted(set(([1] if cfg.get("keep_first_page", True) else []) + code_pages))
        out["covered"] = covered
        out.update(kept=True, mode="PAGES", keep=keep,
                   why=f"{cls}（COVERAGE）：首頁 + 帶受評公司代號的 {len(code_pages)} 頁；"
                       f"受評公司 {len(covered)} 家；略過 {len(texts) - len(keep)} 頁")
        cap = int(cfg.get("max_covered", 60) or 60)
        if not covered:
            out["review"] = cfg.get("none_found") or "產業／展望報告掃不到任何代號"
        elif len(covered) > cap:
            out["review"] = f"受評公司 {len(covered)} 家超過上限 {cap}：請確認是不是把內文提到的代號也算進來了"
        return out
    keep = []
    for pno, text in enumerate(texts, 1):
        kind = page_kind(text)
        first = pno == 1 and focus["keep_first_page"]
        role = "FIRST+ANNUAL" if first and kind["annual"] else ("FIRST" if first else ("ANNUAL" if kind["annual"] else "SKIP"))
        if role != "SKIP":
            keep.append(pno)
        out["pages"].append({"page": pno, "role": role, "years": kind["years"], "labels": len(kind["labels"]), "numbers": kind["numbers"],
                             "statements": kind["statements"], "why": kind["why"], "unparsed_periods": kind["unparsed_periods"],
                             "unmapped_labels": kind["unmapped_labels"]})
    out.update(kept=True, mode="PAGES", keep=keep,
               why=f"首頁 + 年度財報頁 {sum(1 for p in out['pages'] if 'ANNUAL' in p['role'])} 頁；略過 {len(texts) - len(keep)} 頁")
    if not any("ANNUAL" in p["role"] for p in out["pages"]):
        rest = [p for p in out["pages"] if p["page"] > 1] or out["pages"]
        best = max(rest, key=lambda p: (p["labels"] + 2 * len(p["years"]) + p["numbers"] / 20.0, -p["page"]))
        out["review"] = (focus["no_annual"] + f"｜最像的是第 {best['page']} 頁：{best['why']}"
                         + (f"｜沒認出的期別：{' '.join(best['unparsed_periods'][:8])}" if best["unparsed_periods"] else "")
                         + (f"｜對不到科目的列標：{'、'.join(best['unmapped_labels'][:10])}" if best["unmapped_labels"] else ""))
    return out


# [VRN-ID] VRN-ENG015-FNC013 · IO
def write_copy_file(src, dst, keep, save):
    """The kept pages of `src` saved to `dst` (same pages -> same bytes).  Every page kept = a byte copy."""
    import fitz  # type: ignore
    dst.parent.mkdir(parents=True, exist_ok=True)
    with fitz.open(str(src)) as doc:
        if list(keep) == list(range(1, doc.page_count + 1)):
            shutil.copyfile(src, dst)
            return
        out = fitz.open()
        try:
            for pno in keep:
                out.insert_pdf(doc, from_page=pno - 1, to_page=pno - 1)
            out.set_metadata(doc.metadata or {})
            out.save(str(dst), garbage=int(save.get("garbage", 3)), deflate=bool(save.get("deflate", True)),
                     no_new_id=bool(save.get("no_new_id", True)))
        finally:
            out.close()


# =====================================================================
# 3 . MANY FILES: THE FOCUS FOLDER AND ITS MANIFEST
# =====================================================================
# [VRN-ID] VRN-ENG015-FNC017 · LOGIC
def one(path, name, folder, focus=None):
    """一份報告的完整處理：分類 → 決定留哪幾頁 → 另存聚焦副本 → 原檔前後 SHA 比對。

    本行程與子行程走的是**同一支函式**，所以兩條路不可能給出不同答案 —— 一個判斷一份實作。
    """
    focus = focus or rules()[0]
    path = Path(path)
    name = name or path.name
    before = _sha256(path)
    p = plan(path, name)
    p["sha256"] = before
    if p["kept"]:
        dst = Path(folder) / name
        try:
            if p["mode"] == "PAGES":
                write_copy_file(path, dst, p["keep"], focus["save"])
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(path, dst)
            p["focus_copy"] = str(dst)
            p["page_map"] = {str(i): pno for i, pno in enumerate(p["keep"], 1)} if p["mode"] == "PAGES" else {}
        except Exception as error:  # noqa: BLE001
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dst)
            p.update(mode="WHOLE", focus_copy=str(dst), page_map={},
                     review=f"另存聚焦副本失敗，整份帶過去：{error.__class__.__name__}: {error}"[:200])
    p["untouched"] = _sha256(path) == before
    return p


# [VRN-ID] VRN-ENG015-FNC007 · LOGIC
def build(items, folder, workers=None, mapper=None, timeout=1800):
    """[(path, name)] -> manifest; the focus copies are written under `folder` (relative names kept).

    每頁都要讀一次文字，所以成本是按頁走的 —— 操作員 534 檔的實測裡這一關 232 秒，是第三大的閘。
    PyMuPDF 不能多執行緒共用，所以走的是 G06／P14 已經證過的那條路：**每塊一個子行程**。
    一塊垮掉就在本行程重做那幾份，絕不靜靜少掉幾檔（結果少一份比慢一點嚴重得多）。
    檔少、只有一核、或 VRN_FOCUS_INPROC=1 時照舊逐一跑 —— 開子行程的成本會比省下來的多。
    """
    focus, _annual = rules()
    folder = Path(folder)
    if folder.exists():
        shutil.rmtree(folder)
    folder.mkdir(parents=True)
    started = time.perf_counter()
    items = [(str(p), n or Path(p).name) for p, n in items]
    workers = workers or min(8, max(1, (os.cpu_count() or 2)))
    lane, failed_chunks = "sequential", 0
    if len(items) < 3 or workers < 2 or os.environ.get("VRN_FOCUS_INPROC") == "1":
        files = [one(p, n, folder, focus) for p, n in items]
    else:
        lane, files, failed_chunks = _build_in_workers(items, folder, focus, workers, mapper, timeout)
    kept = [f for f in files if f["kept"]]
    # pages_* / annual_pages 只算 FULL（個股）—— 它們的語意從一開始就是「個股報告的頁」，
    # 2026-10-15 加進 COVERAGE／REGISTER 之後若把別類的頁混進來，同一個數字會悄悄換意思。
    full = [f for f in kept if f.get("process", "FULL") == "FULL"]
    pages_total = sum(f["pages_total"] or 0 for f in full if f["mode"] == "PAGES")
    pages_kept = sum(len(f["keep"]) for f in full if f["mode"] == "PAGES")
    annual_pages = sum(1 for f in full for p in f["pages"] if "ANNUAL" in p["role"])
    by_process = {}
    for f in files:
        key = f.get("process") or "SKIP"
        by_process[key] = by_process.get(key, 0) + 1
    covered_rows = sum(len(f.get("covered") or []) for f in files)
    manifest = {"version": FOCUS_VERSION, "rule": focus["rule"], "operator": focus["operator"], "folder": str(folder),
                "seconds": round(time.perf_counter() - started, 3), "lane": lane, "workers": workers if lane != "sequential" else 1,
                "failed_chunks": failed_chunks, "files": files,
                "counts": {"files": len(files), "stock": len(full), "excluded": sum(1 for f in files if not f["kept"]),
                           "pages_total": pages_total, "pages_kept": pages_kept, "annual_pages": annual_pages,
                           "whole": sum(1 for f in kept if f["mode"] == "WHOLE"), "review": sum(1 for f in kept if f["review"]),
                           "by_process": by_process,
                           "coverage": by_process.get("COVERAGE", 0), "register": by_process.get("REGISTER", 0),
                           "covered_rows": covered_rows,
                           "all_pages_total": sum(f["pages_total"] or 0 for f in kept if f["mode"] == "PAGES"),
                           "all_pages_kept": sum(len(f["keep"]) for f in kept if f["mode"] == "PAGES"),
                           "originals_untouched": all(f["untouched"] for f in files)}}
    return manifest


# [VRN-ID] VRN-ENG015-FNC018 · LOGIC
def _build_in_workers(items, folder, focus, workers, mapper, timeout):
    """把 items 切成 workers 塊,每塊丟一支子行程;回 (車道, 依輸入順序的結果, 垮掉的塊數)。

    切法與回收的形狀照 VRN_PageRegions.analyze_many —— 那一條已經證過,不另外發明一種。
    """
    chunks = [list(range(i, len(items), workers)) for i in range(min(workers, len(items)))]
    work = Path(tempfile.mkdtemp(prefix="vrn_focus_w_"))

    # [VRN-ID] VRN-ENG015-FNC019 · LOGIC
    def run_chunk(index):
        idx = chunks[index]
        src = work / f"focus_in_{index:02d}.json"
        dst = work / f"focus_out_{index:02d}.jsonl"
        src.write_text(json.dumps([[i, items[i][0], items[i][1]] for i in idx], ensure_ascii=False), encoding="utf-8")
        env = dict(os.environ, PYTHONIOENCODING="utf-8", VRN_FOCUS_INPROC="1")
        try:
            done = subprocess.run([sys.executable, str(Path(__file__).resolve()), "worker",
                                   "--input", str(src), "--output", str(dst), "--folder", str(folder)],
                                  capture_output=True, text=True, encoding="utf-8", errors="replace",
                                  timeout=timeout, env=env)
            return {"index": index, "ok": done.returncode == 0 and dst.is_file(), "out": str(dst),
                    "err": (done.stderr or "")[-400:]}
        except Exception as error:  # noqa: BLE001
            return {"index": index, "ok": False, "out": str(dst), "err": f"{error.__class__.__name__}: {error}"}

    status = (mapper or _plain_map)(run_chunk, list(range(len(chunks))), "G19 聚焦：子行程逐塊")
    results = [None] * len(items)
    failed = 0
    for st in status:
        if not st.get("ok"):
            failed += 1
            continue
        for line in Path(st["out"]).read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                results[rec["index"]] = rec["result"]
    for i, r in enumerate(results):          # 垮掉的那幾份在本行程重做,絕不靜靜少掉
        if r is None:
            results[i] = one(items[i][0], items[i][1], folder, focus)
    shutil.rmtree(work, ignore_errors=True)
    return "worker_process", results, failed


# [VRN-ID] VRN-ENG015-FNC020 · LOGIC
def _plain_map(fn, xs, _action=""):
    """呼叫端沒給車道時的預設：stdlib 執行緒池。每支執行緒只是在等子行程,PyMuPDF 都在子行程裡。"""
    from concurrent.futures import ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max(1, len(xs))) as pool:
        return list(pool.map(fn, xs))


# [VRN-ID] VRN-ENG015-FNC008 · IO
def write_manifest(manifest, out_dir):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / MANIFEST_JSON).write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    with open(out / MANIFEST_CSV, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["檔案", "類別", "路徑", "處理", "方式", "原檔頁數", "保留頁（原檔頁碼）", "年度財報頁", "略過頁數",
                    "受評公司", "說明", "要人看"])
        for f in manifest["files"]:
            annual = [p["page"] for p in f["pages"] if "ANNUAL" in p["role"]]
            covered = " ".join(c["ticker"] for c in (f.get("covered") or []))
            w.writerow([f["file"], f["doc_class"], f.get("process") or "", "是" if f["kept"] else "否", f["mode"],
                        f["pages_total"] or "", " ".join(map(str, f["keep"])), " ".join(map(str, annual)),
                        (f["pages_total"] - len(f["keep"])) if f["mode"] == "PAGES" else "", covered, f["why"], f["review"]])
    return {"json": str(out / MANIFEST_JSON), "csv": str(out / MANIFEST_CSV)}


# [VRN-ID] VRN-ENG015-FNC009 · LOGIC
def original_page(manifest_row, focus_page):
    """Focus-copy page -> the original's page number (WHOLE copies keep their numbers)."""
    if focus_page is None:
        return None
    return (manifest_row or {}).get("page_map", {}).get(str(focus_page), focus_page)


# =====================================================================
# 4 . KNOWN ANSWERS
# =====================================================================
# [VRN-ID] VRN-ENG015-FNC010 · BUILD
def build_fixtures(folder):
    """A five-page stock report (cover, body, annual tables, quarter-only table, disclaimer) and an industry report."""
    try:
        import fitz  # type: ignore
    except Exception:  # noqa: BLE001
        return []
    T = _titletrim()
    R, _M = T.regions()
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    src_dir = folder / "_src"
    truths = R.build_fixtures(src_dir)
    annual_src = src_dir / next(t["file"] for t in truths if t["kind"] == "annual")
    quarter_src = src_dir / next(t["file"] for t in truths if t["kind"] == "chart")
    name = "凱基_2330台積電_20260905_公司更新.pdf"
    doc = fitz.open()
    p = doc.new_page(width=595, height=842)
    p.insert_text((40, 60), "台積電(2330 TT)  先進製程需求強勁", fontname="china-t", fontsize=18)
    p.insert_text((40, 100), "投資評等：買進    目標價：NT$1,200", fontname="china-t", fontsize=10)
    p = doc.new_page(width=595, height=842)
    for i in range(12):
        p.insert_text((40, 60 + 18 * i), "先進製程與先進封裝需求延續，2026 年營收成長動能明確。", fontname="china-t", fontsize=10)
    with fitz.open(str(annual_src)) as a:
        doc.insert_pdf(a)
    with fitz.open(str(quarter_src)) as q:
        doc.insert_pdf(q)
    p = doc.new_page(width=595, height=842)
    for i in range(10):
        p.insert_text((40, 60 + 14 * i), "免責聲明：本報告僅供參考，不構成投資建議。", fontname="china-t", fontsize=8)
    doc.set_metadata({"title": "fixture", "creationDate": "D:20260905000000", "modDate": "D:20260905000000"})
    doc.save(str(folder / name))
    doc.close()
    shutil.copyfile(src_dir / next(t["file"] for t in truths if t["kind"] == "not_stock"), folder / "元大_半導體產業_20260901_產業報告.pdf")
    (folder / "2330台積電_凱基_20260906_快報.txt").write_text("台積電(2330 TT) 營運更新\n投資評等：買進\n", encoding="utf-8")
    shutil.rmtree(src_dir)
    return [{"file": name, "kept": True, "keep": [1, 3], "annual": [3]},
            # 2026-10-15 起產業報告也處理（COVERAGE）：這份合成語料沒有印代號，所以受評 0 家、列 REVIEW
            {"file": "元大_半導體產業_20260901_產業報告.pdf", "kept": True, "process": "COVERAGE"},
            {"file": "2330台積電_凱基_20260906_快報.txt", "kept": True, "mode": "WHOLE"}]


# [VRN-ID] VRN-ENG015-FNC011 · ENTRY
def selftest(verbose=True):
    checks = []
    try:
        import fitz  # type: ignore
    except Exception:  # noqa: BLE001
        if verbose:
            print("  [SKIP] PyMuPDF 沒有安裝：pip install pymupdf（安裝是操作員的手）")
        return 0, [("PyMuPDF", True, "略過")]
    with tempfile.TemporaryDirectory(prefix="vrn_focus_") as tmp:
        src = Path(tmp) / "samples"
        truths = build_fixtures(src)
        items = [(src / t["file"], t["file"]) for t in truths]
        m1 = build(items, Path(tmp) / "focus1")
        m2 = build(items, Path(tmp) / "focus2")
        by = {f["file"]: f for f in m1["files"]}
        for t in truths:
            f = by[t["file"]]
            checks.append((f"{t['file'][:16]} 處理 = {t['kept']}", f["kept"] == t["kept"], f["why"]))
            if t.get("process"):
                checks.append((f"{t['file'][:16]} 路徑 = {t['process']}", f.get("process") == t["process"], f.get("process", "?")))
            if "keep" in t:
                checks.append((f"{t['file'][:16]} 保留第 {t['keep']} 頁", f["keep"] == t["keep"],
                               json.dumps([(p["page"], p["role"], p["why"]) for p in f["pages"]], ensure_ascii=False)[:400]))
                annual = [p["page"] for p in f["pages"] if "ANNUAL" in p["role"]]
                checks.append(("季表、本文、免責不算年度財報頁", annual == t["annual"], str(annual)))
                with fitz.open(f["focus_copy"]) as d, fitz.open(str(src / t["file"])) as o:
                    same = d.page_count == len(t["keep"]) and all(d[i].get_text("text") == o[pno - 1].get_text("text")
                                                                  for i, pno in enumerate(t["keep"]))
                checks.append(("聚焦副本的每一頁和原檔那一頁的文字一字不差", same, f["focus_copy"]))
                checks.append(("副本第 2 頁 = 原檔第 3 頁", original_page(f, 2) == 3, str(f.get("page_map"))))
            if t.get("mode"):
                checks.append((f"{t['file'][:16]} 整份帶過去", f["mode"] == t["mode"], f["mode"]))
        f2 = {f["file"]: f for f in m2["files"]}
        stable = all(_sha256(by[n]["focus_copy"]) == _sha256(f2[n]["focus_copy"]) for n in by if by[n].get("focus_copy"))
        checks.append(("同樣的頁存兩次，位元組相同", stable, ""))
        checks.append(("原檔一個位元組都沒動", m1["counts"]["originals_untouched"], ""))
        # 2026-10-15：非個股不再被丟掉，改成各走各的路徑。這一案從「不進資料夾」改成「進得來，而且路徑正確」。
        industry = by.get("元大_半導體產業_20260901_產業報告.pdf")
        checks.append(("產業報告進得了聚焦資料夾",
                       bool(industry) and (Path(tmp) / "focus1" / "元大_半導體產業_20260901_產業報告.pdf").exists(),
                       "" if industry else "清單裡找不到它"))
        checks.append(("產業報告走 COVERAGE、每家受評公司一列",
                       bool(industry) and industry.get("process") == "COVERAGE"
                       and industry.get("rows") == "ONE_PER_COVERED_COMPANY",
                       (industry or {}).get("process", "?")))
        checks.append(("個股仍走 FULL（舊行為沒被改掉）",
                       all(f.get("process") == "FULL" for f in m1["files"] if f["doc_class"] == "STOCK"),
                       ""))
    bad = [c for c in checks if not c[1]]
    if verbose:
        for name, ok, detail in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + ("" if ok else f" · {detail}"))
        print(f"[FOCUS] {FOCUS_VERSION} · {len(checks) - len(bad)}/{len(checks)}")
    return (1 if bad else 0), checks


# [VRN-ID] VRN-ENG015-FNC012 · ENTRY
def main(argv=None):
    parser = argparse.ArgumentParser(description="VRN Focus: stock reports only -- file name, page 1, annual financial pages")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("selftest")
    w = sub.add_parser("worker", help="內部用：處理一塊檔案並寫出 JSONL（build 的子行程）")
    w.add_argument("--input", required=True)
    w.add_argument("--output", required=True)
    w.add_argument("--folder", required=True)
    run = sub.add_parser("plan")
    run.add_argument("paths", nargs="+")
    run.add_argument("--out", default="")
    args = parser.parse_args(argv)
    if args.command == "worker":
        focus = rules()[0]
        with Path(args.output).open("w", encoding="utf-8", newline="\n") as fh:
            for index, path, name in json.loads(Path(args.input).read_text(encoding="utf-8")):
                fh.write(json.dumps({"index": index, "result": one(path, name, args.folder, focus)},
                                    ensure_ascii=False) + "\n")
        return 0
    if args.command == "plan":
        files = []
        for p in args.paths:
            p = Path(p)
            files += [(q, q.relative_to(p).as_posix()) for q in sorted(p.rglob("*")) if q.is_file()] if p.is_dir() else [(p, p.name)]
        folder = Path(args.out or tempfile.mkdtemp(prefix="vrn_focus_")) / "focus"
        manifest = build(files, folder)
        paths = write_manifest(manifest, folder.parent)
        print(json.dumps(dict(manifest["counts"], manifest=paths["csv"]), ensure_ascii=False, indent=1))
        for f in manifest["files"]:
            print(f"  {'KEEP' if f['kept'] else 'SKIP'} {f['file']} · {f['mode']} · {f['keep'] or ''} · {f['why']}"
                  + (f" · 要人看：{f['review']}" if f["review"] else ""))
        return 0
    return selftest()[0]


if __name__ == "__main__":
    sys.exit(main())
