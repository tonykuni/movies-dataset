#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SystemManager v0156 — 薄尾(操作員 2026-10-10):
  paths     登記 VIA 路徑(via_database · vdf_database · via_00_vcgc · via_01_vdf · via_02_vrn)進 VRN_Config;
            VDF 資料庫 via_database\\vdf_database = 總清單契約來源(唯讀;csv · json · parquet · DuckDB 都讀)
  stage     第一步加一個功能:只取個股報告(單一股票)→ 先辨識第一頁 + 年度財報頁 → 只把這幾頁抽成小 PDF 放 TEMP(其他頁不碰);
            Word / TXT 個股 memo 先轉 PDF 也放 TEMP;非個股 · 掃描件 · 其他檔型這次不碰
  layout    = stage → 版面(只讀小 PDF);版面引擎辨識小字頁尾(底部 20% 內比內文小 1 級以上 + 頁尾帶)→ 頁尾不擷取,只取出券商跟檔名券商互證(✓ / ≠)
            版面編號仍用原頁碼(P1 · P4 …)
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
import shutil
import sys
import tempfile
import time
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VRN_SystemManager"
TAG = "v0156"


def _vnum_v0156(path) -> int:
    m = re.search(r"_v(\d{4})$", Path(path).stem)
    return int(m.group(1)) if m else -1


def _load_v0156(path: Path, name: str):
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
    return sys.modules[name]


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum_v0156(p) < _vnum_v0156(__file__)), key=_vnum_v0156)
PRIOR = _load_v0156(PRIOR_PATH, _STEM + "_prior_for_" + Path(__file__).stem)


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


_home, _rep = _resolve("_home"), _resolve("_rep")

# ───────── 路徑(操作員 2026-10-10)· VDF 資料庫 = 總清單契約來源(唯讀)─────────
_ROOT_DEFAULT = r"C:\Users\tonyk\OneDrive\Documents\VeritasIntelligenceAnalytics"


def via_roots() -> dict:
    base = Path(os.environ.get("VIA_ROOTS_BASE") or _ROOT_DEFAULT)
    return {"via_root": base, "via_database": base / "via_database", "vdf_database": base / "via_database" / "vdf_database", "via_00_vcgc": base / "via_00_vcgc", "via_01_vdf": base / "via_01_vdf", "via_02_vrn": base / "via_02_vrn"}


_LIST_EXT = (".csv", ".json", ".parquet", ".duckdb", ".db")
_OWN_CP = _owner("_contract_paths")
_ORIG_CP = _resolve("_contract_paths")
_OWN_FML = _owner("find_master_lists")
_ORIG_FML = _resolve("find_master_lists")


def _contract_paths_v156() -> list:
    ps = list(_ORIG_CP() if _ORIG_CP else [])
    vdb = via_roots()["vdf_database"]
    if vdb.is_dir() and str(vdb) not in ps:
        ps.append(str(vdb))
    return ps


def _find_master_lists_v156(paths=None) -> dict:
    """契約路徑可以是資料夾(VDF 資料庫):展開成裡面的 csv / json / parquet / DuckDB(唯讀)。"""
    if paths is None:
        return _ORIG_FML(None)
    files = []
    for x in paths:
        p = Path(x)
        if p.is_file():
            files.append(p)
        elif p.is_dir():
            for q in p.rglob("*"):
                try:
                    if q.is_file() and q.suffix.lower() in _LIST_EXT and not any(s.startswith(("_superseded", "_quarantine")) for s in q.parts) and (q.suffix.lower() in (".duckdb", ".db") or q.stat().st_size < 500 * 1024 ** 2):
                        files.append(q)
                except OSError:
                    continue
    files = sorted(set(files), key=lambda q: q.stat().st_mtime, reverse=True)[:150]
    return _ORIG_FML([str(q) for q in files])


if _OWN_CP and _ORIG_CP:
    _OWN_CP._contract_paths = _contract_paths_v156
if _OWN_FML and _ORIG_FML:
    _OWN_FML.find_master_lists = _find_master_lists_v156

# ───────── 表格:有格線的表以格線為準(座標分欄只在沒格線時用)─────────
_OWN_ET, _ORIG_ET = _owner("_extract_table"), _resolve("_extract_table")


def _extract_table_v156(page, bbox, how, pdf_path, pno, tabula_ok):
    r = _ORIG_ET(page, bbox, how, pdf_path, pno, tabula_ok)
    if how == "lines" and r.get("engine") != "pdfplumber-lines":
        try:
            rr, fixes = _resolve("_repair_rows")(page.crop(bbox).extract_table())
            cells = [c for x in rr for c in x]
            if len(rr) >= 2 and len(rr[0]) >= 2 and cells and sum(1 for c in cells if c) / len(cells) >= 0.85:
                return {"engine": "pdfplumber-lines(格線優先)", "rows": rr, "fixes": fixes, "alts": list(r.get("alts", [])) + [r.get("engine", "")]}
        except Exception:  # noqa: BLE001
            pass
    return r


if _OWN_ET and _ORIG_ET:
    _OWN_ET._extract_table = _extract_table_v156

# ───────── stage:只取個股報告的第一頁 + 年度財報頁 → TEMP ─────────


def _temp_root(stamp: str) -> Path:
    base = Path(os.environ.get("VIA_SPILL_DIR") or (Path(tempfile.gettempdir()) / "VIA_progress"))
    d = base / ("vrn_stage_" + stamp)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _subset_pdf(src: Path, pages: list, dst: Path) -> str:
    """只把指定頁抽成一份小 PDF(其他頁不碰):pypdfium2(pdfplumber 自帶)→ pypdf → pikepdf。"""
    try:
        import pypdfium2 as pdfium  # noqa: WPS433
        s = pdfium.PdfDocument(str(src))
        d = pdfium.PdfDocument.new()
        d.import_pages(s, [p - 1 for p in pages])
        d.save(str(dst))
        if dst.exists():
            return "pypdfium2"
    except Exception:  # noqa: BLE001
        pass
    try:
        from pypdf import PdfReader, PdfWriter  # noqa: WPS433
        r, w = PdfReader(str(src)), PdfWriter()
        for p in pages:
            w.add_page(r.pages[p - 1])
        with dst.open("wb") as fh:
            w.write(fh)
        return "pypdf"
    except Exception:  # noqa: BLE001
        pass
    try:
        import pikepdf  # noqa: WPS433
        with pikepdf.open(str(src)) as s:
            d = pikepdf.new()
            for p in pages:
                d.pages.append(s.pages[p - 1])
            d.save(str(dst))
        return "pikepdf"
    except Exception:  # noqa: BLE001
        return ""


def stage_run(d: Path, recursive: bool = False, only: str = "") -> dict:
    import pdfplumber
    stamp = datetime.datetime.now().strftime("%Y%m%dT%H%M%S")
    tmp = _temp_root(stamp)
    (tmp / "conv").mkdir(exist_ok=True)
    (tmp / "pages").mkdir(exist_ok=True)
    master, _ = _resolve("_load_roster_v154")(True)
    book, _ = _resolve("load_brokers_v154")()
    fparse = _resolve("fname_parse")
    nonstock = _resolve("_nonstock_type") or (lambda n: "")
    it = d.rglob("*") if recursive else (d.iterdir() if d.is_dir() else [])
    files = sorted(p for p in it if p.is_file() and not p.name.startswith("~$"))
    if only:
        files = [p for p in files if only.lower() in p.name.lower()]
    rows = []
    for p in files:
        ext = p.suffix.lower()
        f = fparse(p.name, master, book, p.stat().st_mtime, None)
        r = {"file": p.name, "path": str(p), "code": f.get("code", ""), "name": f.get("name", ""), "broker": f.get("broker", ""), "date": f.get("date", ""), "yf": f.get("yf", ""), "bbg": f.get("bbg", ""), "status": "", "lamp": "GRAY"}
        if not f.get("code") or nonstock(p.name):
            r["status"] = "非個股(或多檔)→ 這次不碰"
            rows.append(r)
            continue
        if ext not in (".pdf", ".docx", ".doc", ".rtf", ".odt", ".txt", ".md"):
            r["status"] = "檔型 %s 這次不碰" % ext
            rows.append(r)
            continue
        src = p
        if ext != ".pdf":
            dst = tmp / "conv" / (p.stem + ".pdf")
            if ext == ".txt" or ext == ".md":
                how, err = _resolve("text_to_pdf")(_resolve("_read_text_any")(p), dst)
            else:
                how, err = _resolve("word_to_pdf")(p, dst, tmp)
            if not dst.exists():
                r.update(status="轉 PDF 失敗:%s" % err, lamp="RED")
                rows.append(r)
                continue
            src = dst
            r["convert"] = how
        try:
            with pdfplumber.open(str(src)) as pdf:
                n = len(pdf.pages)
                t1 = (pdf.pages[0].extract_text() or "") if n else ""
                if len(t1.strip()) < 40:
                    r.update(status="首頁無文字層(掃描件 → OCR 閘)", pages_total=n)
                    rows.append(r)
                    continue
                ann = [x for x in _resolve("_annual_pages")(pdf) if x != 1]
        except Exception as exc:  # noqa: BLE001
            r.update(status="開不了:%s" % str(exc)[:60], lamp="RED")
            rows.append(r)
            continue
        pick = sorted(set([1] + ann))
        sha8 = hashlib.sha256(str(p).encode("utf-8")).hexdigest()[:8]
        mini = tmp / "pages" / ("%s_%s_p%s.pdf" % (sha8, re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", p.stem)[:40], "-".join(map(str, pick))))
        how = _subset_pdf(src, pick, mini)
        r.update(pages_total=n, picked=pick, annual=ann, src_pdf=str(src), mini=str(mini) if how else "", subset=how or "原檔直讀(無抽頁工具)", status="第一頁 + 年度財報頁 %s" % (",".join("P%d" % x for x in ann) or "(沒找到)"), lamp="GREEN" if ann else "YELLOW")
        rows.append(r)
    man = {"ts": datetime.datetime.now().isoformat(timespec="seconds"), "dir": str(d), "temp": str(tmp), "rows": rows}
    out = _rep() / "stage"
    out.mkdir(parents=True, exist_ok=True)
    (out / "STAGE_latest.json").write_text(json.dumps(man, ensure_ascii=False, indent=1), encoding="utf-8")
    return man


# ───────── 頁尾(小字)辨識 → 不擷取,只取券商做互證 ─────────


def _footer_fix(pg: dict) -> int:
    H = pg["H"]
    sizes = Counter()
    for b in pg["blocks"]:
        if b["kind"] == "text":
            for l in b.get("lines", []):
                sizes[round(l["size"] * 2) / 2] += len(l["text"])
    body = max(sizes.items(), key=lambda kv: kv[1])[0] if sizes else 9
    moved = 0
    for b in pg["blocks"]:
        if b["kind"] == "text" and b["zone"] in ("L", "R", "F") and b["top"] >= 0.80 * H and b.get("size", 99) <= body - 1.0:
            b["zone"], b["role"], b["sub"] = "B", "FOOTER", "頁尾/免責"
            moved += 1
    k = 0
    for b in sorted((b for b in pg["blocks"] if b["zone"] == "B"), key=lambda b: b["top"]):
        k += 1
        b["id"] = "P%d·B·%02d" % (pg["page"], k)
    return moved


def layout_one_v156(row: dict, book: dict, tabula_ok: bool, deep=None) -> dict:
    import pdfplumber
    t0 = time.time()
    src = Path(row.get("mini") or row.get("src_pdf") or row["path"])
    pick = row.get("picked") or [1]
    out = {"file": row["file"], "path": row["path"], "source": str(src), "lamp": "GRAY", "notes": [], "id": {k: row.get(k, "") for k in ("code", "yf", "bbg", "name", "broker", "date")}}
    out["id"]["date_src"] = ""
    with pdfplumber.open(str(src)) as pdf:
        local = list(range(1, len(pdf.pages) + 1)) if row.get("mini") else pick
        p1t = pdf.pages[local[0] - 1].extract_text() or ""
        conf = {}
        if row.get("code"):
            conf["代號"] = bool(re.search(r"(?<!\d)%s(?!\d)" % re.escape(row["code"]), p1t))
        if row.get("name"):
            conf["名稱"] = row["name"].replace("-KY", "") in p1t
        pages = []
        an = _resolve("analyze_page")
        for i, lp in enumerate(local):
            pg = an(pdf, lp, str(src), annual=(i > 0), tabula_ok=tabula_ok)
            orig = pick[i] if i < len(pick) else lp
            if orig != pg["page"]:
                for b in pg["blocks"]:
                    b["id"] = re.sub(r"^P\d+·", "P%d·" % orig, b["id"])
                pg["page"] = orig
            pages.append(pg)
    moved = sum(_footer_fix(pg) for pg in pages)
    hier = _resolve("_hierarchy")(pages)
    for pg in pages:
        for b in pg["blocks"]:
            if b["kind"] == "text":
                b["sub"] = "頁尾/免責" if b["role"] == "FOOTER" else _resolve("_text_subcat")(b, hier)
            b["eng394"] = _resolve("_eng_subcat")(b["kind"], b.get("text", "")[:300])
    ftxt = " ".join(b.get("text", "") for pg in pages for b in pg["blocks"] if b["role"] == "FOOTER")
    htxt = " ".join(b.get("text", "") for pg in pages for b in pg["blocks"] if b["role"] == "HEADER")
    mb = _resolve("match_broker")
    canon, alias, _ = mb(ftxt, book) if ftxt else ("", "", "")
    where = "頁尾"
    if not canon and htxt:
        canon, alias, _ = mb(htxt, book)
        where = "頁首"
    ab = _resolve("_abbr_of")(book, canon)[0] if canon else ""
    xc = ("✓" if ab and ab == row.get("broker") else ("≠ 檔名 %s" % (row.get("broker") or "—"))) if ab else "頁尾無券商"
    n_foot = sum(1 for pg in pages for b in pg["blocks"] if b["role"] == "FOOTER")
    out["footer"] = {"blocks": n_foot, "moved_small": moved, "chars": len(ftxt), "broker": ab, "canon": canon, "alias": alias, "where": where if ab else "", "xcheck": xc}
    for pg in pages:
        pg["blocks"] = [b for b in pg["blocks"] if b["role"] != "FOOTER"]       # 頁尾不擷取
    f = {"code": row.get("code"), "broker": row.get("broker")}
    title = _resolve("_main_title")(pages[0], hier, f, book)
    for b in pages[0]["blocks"]:
        if b["id"] == title.get("id"):
            b["sub"] = "主標題"
    info = {}
    if deep:
        try:
            os.environ["VIA_NO_NET"] = "1"
            rr = deep(src)
            info = {k: v for k, v in (rr or {}).items() if isinstance(v, (str, int, float)) and v not in ("", None) and re.search(r"(?i)rating|target|tp|analyst|email|tel|close|price|評等|目標", k)}
        except Exception as exc:  # noqa: BLE001
            info = {"_deepread": "沒跑:%s" % str(exc)[:60]}
    if ab:
        conf["頁尾券商"] = (xc == "✓")
    p1 = pages[0]
    n_tables = sum(1 for pg in pages for b in pg["blocks"] if b["kind"] == "table")
    n_fix = sum(len(b.get("fixes", [])) for pg in pages for b in pg["blocks"] if b["kind"] == "table")
    split = "INFO" in p1["roles"].values() and "BODY" in p1["roles"].values()
    ann = [pg["page"] for pg in pages[1:]]
    out.update(pages=pages, hier=hier, title=title, info=info, annual=ann, n_tables=n_tables, n_fixes=n_fix, split=split, confirm=conf, pages_total=row.get("pages_total"), secs=round(time.time() - t0, 1))
    y = []
    if not all(v for k, v in conf.items() if k != "頁尾券商"):
        y.append("首頁沒對到" + "/".join(k for k, v in conf.items() if not v and k != "頁尾券商"))
    if ab and xc != "✓":
        y.append("頁尾券商 %s %s" % (ab, xc))
    if not title["text"]:
        y.append("主標題沒找到")
    if not split:
        y.append("首頁本文/資訊區沒切開")
    if not ann:
        y.append("年度財報頁沒找到")
    elif not n_tables:
        y.append("年度財報頁沒抽到表")
    out["notes"] = y
    out["lamp"] = "YELLOW" if y else "GREEN"
    return out


def layout_run_v156(d: Path, max_files: int = 0, only: str = "", recursive: bool = False) -> dict:
    now = datetime.datetime.now()
    man = stage_run(d, recursive, only)
    out_dir = _rep() / "layout"
    out_dir.mkdir(parents=True, exist_ok=True)
    book, _ = _resolve("load_brokers_v154")()
    tabula_ok = bool(shutil.which("java")) and importlib.util.find_spec("tabula") is not None
    deep = _resolve("deepread_one")
    todo = [r for r in man["rows"] if r.get("picked")]
    if max_files:
        todo = todo[:max_files]
    rows = []
    for i, st in enumerate(todo, 1):
        try:
            r = layout_one_v156(st, book, tabula_ok, deep)
        except Exception as exc:  # noqa: BLE001
            r = {"file": st["file"], "path": st["path"], "lamp": "RED", "notes": ["%s:%s" % (type(exc).__name__, str(exc)[:100])], "id": {}}
        page = out_dir / ("%s_%s.html" % (hashlib.sha256(st["path"].encode("utf-8")).hexdigest()[:8], re.sub(r"[^\w\u4e00-\u9fff\-]+", "_", Path(st["file"]).stem)[:60]))
        if r.get("pages"):
            h = _resolve("_file_html")(r)
            fb = r.get("footer", {})
            chip = "<span class='chip' style='background:%s'>頁尾小字 %d 段 · 不擷取 · %s券商 %s %s</span>" % ("#dcfce7" if fb.get("xcheck") == "✓" else "#fef3c7", fb.get("blocks", 0), fb.get("where", ""), html.escape(fb.get("broker") or "—"), html.escape(fb.get("xcheck", "")))
            chip += "<span class='chip'>只取 %s(共 %s 頁)· 小 PDF 在 TEMP</span>" % (html.escape(",".join("P%d" % x for x in st.get("picked", []))), st.get("pages_total", "?"))
            h = h.replace("<div class='meta yel'>", chip + "<div class='meta yel'>", 1).replace("資訊區(首頁 INFO · 頁首 · 頁尾)", "資訊區(首頁 INFO · 頁首;頁尾小字不擷取,只做券商互證)")
            page.write_text(h, encoding="utf-8")
            r["html"] = str(page)
        (out_dir / (page.stem + ".json")).write_text(json.dumps(r, ensure_ascii=False, default=str), encoding="utf-8")
        rows.append({k: r.get(k) for k in ("file", "lamp", "notes", "html", "annual", "n_tables", "n_fixes", "split", "secs", "pages_total")} | {"id": r.get("id", {}), "title": (r.get("title") or {}).get("text", ""), "confirm": r.get("confirm", {}), "levels": len((r.get("hier") or {}).get("levels", {})), "eng394": sum(1 for pg in r.get("pages", []) for b in pg["blocks"] if b.get("eng394")), "footer": r.get("footer", {})})
        print("  [進度] %d/%d · %s · %s" % (i, len(todo), r.get("lamp"), st["file"][:50]), flush=True)
    for st in man["rows"]:
        if not st.get("picked"):
            rows.append({"file": st["file"], "lamp": "RED" if st.get("lamp") == "RED" else "GRAY", "notes": [st.get("status", "")], "id": {k: st.get(k, "") for k in ("code", "name", "broker")}, "title": "", "confirm": {}, "annual": [], "n_tables": 0, "n_fixes": 0, "levels": 0, "eng394": 0})
    e = _resolve("eng394")()
    did = [r for r in rows if r.get("html")]
    s = {"ts": now.isoformat(timespec="seconds"), "dir": str(d), "files": len(rows), "lamps": dict(Counter(r["lamp"] for r in rows)), "titles": sum(1 for r in did if r["title"]), "split": sum(1 for r in did if r.get("split")),
         "annual": sum(1 for r in did if r.get("annual")), "tables": sum(r.get("n_tables") or 0 for r in did), "fixes": sum(r.get("n_fixes") or 0 for r in did), "eng394": e.get("file") or "無", "eng394_ok": bool(e.get("subcat")), "eng394_err": e.get("err", ""),
         "rulebook": e.get("rulebook", ""), "tabula": tabula_ok, "deepread": bool(deep), "staged": len(todo), "skipped": len(man["rows"]) - len([r for r in man["rows"] if r.get("picked")]), "temp": man["temp"],
         "footer_ok": sum(1 for r in did if (r.get("footer") or {}).get("xcheck") == "✓"), "footer_diff": sum(1 for r in did if (r.get("footer") or {}).get("broker") and (r.get("footer") or {}).get("xcheck") != "✓"), "footer_none": sum(1 for r in did if not (r.get("footer") or {}).get("broker"))}
    idx = out_dir / "LAYOUT_MATRIX_latest.html"
    ih = _resolve("_index_html")(s, rows)
    ih = ih.replace("<div class='bar'", "<div class='meta'>這次只取個股報告的第一頁 + 年度財報頁:處理 %d 份 · 不碰 %d 份(非個股 / 掃描件 / 其他檔型)· 小 PDF 在 TEMP %s · 頁尾券商互證 ✓%d ≠%d 無%d</div><div class='bar'" % (s["staged"], s["skipped"], html.escape(s["temp"]), s["footer_ok"], s["footer_diff"], s["footer_none"]), 1)
    idx.write_text(ih, encoding="utf-8")
    (out_dir / "LAYOUT_latest.json").write_text(json.dumps({"summary": s, "rows": rows}, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    lamp = "YELLOW" if s["lamps"].get("YELLOW") or s["lamps"].get("RED") else ("GREEN" if did else "GRAY")
    return {"verb": "layout", "summary": s, "rows": rows, "html": str(idx), "lamp": lamp}


def _print_v156(o: dict) -> None:
    s = o["summary"]
    print("[計] VRN layout · 個股報告 %d 份只取第一頁+年度財報頁(不碰 %d 份)· 燈 %s · 主標題 %d · 首頁左右切 %d · 有年度頁 %d · 表 %d · 修補 %d · %s" % (s["staged"], s["skipped"], " ".join("%s=%d" % kv for kv in sorted(s["lamps"].items())), s["titles"], s["split"], s["annual"], s["tables"], s["fixes"], o["lamp"]))
    print("[計] 頁尾小字(不擷取)券商互證 ✓%d ≠%d 無%d · 小 PDF 在 TEMP %s" % (s["footer_ok"], s["footer_diff"], s["footer_none"], s["temp"]))
    print("[計] 版面引擎 ENG394 %s · 子分類 %s%s · 規則冊 %s · tabula %s · deepread %s" % (s["eng394"], "已接" if s["eng394_ok"] else "未接", (" · " + s["eng394_err"]) if s["eng394_err"] else "", s["rulebook"] or "無", "有" if s["tabula"] else "無", "有" if s["deepread"] else "無"))
    for k, v in Counter(n for r in o["rows"] if r.get("html") for n in (r.get("notes") or [])).most_common(10):
        print("  [YEL] %s · %d 檔" % (k, v))
    print("  [U/I] %s" % o["html"])
    print("NEXT: %s" % ("全綠 → 表格接 FinLexicon 標準列" if o["lamp"] == "GREEN" else "點開黃的檔看版面圖;頁尾券商 ≠ 的貼檔名給 AI"))


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    os.environ.setdefault("VIA_FROM_VCGC", "YES")
    if "--selftest" in args[:2]:
        return selftest()

    def opt(flag, default=None):
        return args[args.index(flag) + 1] if flag in args and args.index(flag) + 1 < len(args) else default
    if args[:1] in (["stage"], ["layout"]) and len(args) >= 2 and "--dir" not in args and Path(args[-1]).is_dir():
        args = args[:-1] + ["--dir", args[-1]]
    cfg = (_resolve("config_get") or (lambda: {}))()
    d = Path(opt("--dir") or cfg.get("input_dir") or r"C:\測試樣本報告")
    if args[:1] == ["paths"]:
        rs = via_roots()
        cs = _resolve("config_set")
        if cs:
            cs("via_roots", {k: str(v) for k, v in rs.items()})
        print("[計] VRN paths · 登進 VRN_Config via_roots · %s" % ("GREEN" if all(v.exists() for v in rs.values()) else "YELLOW"))
        for k, v in rs.items():
            print("  [%s] %s · %s" % ("OK" if v.exists() else "YEL", k, v))
        print("  [注] 總清單契約 = %s(唯讀;VDF 公布清單的地方)" % rs["vdf_database"])
        return 0
    if args[:1] == ["stage"]:
        man = stage_run(d, "--recursive" in args, opt("--only", "") or "")
        rows = man["rows"]
        st = [r for r in rows if r.get("picked")]
        print("[計] VRN stage · 檔 %d · 個股報告 %d 份抽頁進 TEMP · 不碰 %d · TEMP %s" % (len(rows), len(st), len(rows) - len(st), man["temp"]))
        for r in st[:30]:
            print("  [%s] %s · %s · %s" % ("OK" if r["lamp"] == "GREEN" else "YEL", r["file"][:50], r["status"], r.get("subset", "")))
        for k, v in Counter(r["status"] for r in rows if not r.get("picked")).most_common(6):
            print("  [注] 不碰:%s · %d 檔" % (k, v))
        return 0
    if args[:1] == ["layout"]:
        o = layout_run_v156(d, int(opt("--max", "0") or 0), opt("--only", "") or "", "--recursive" in args)
        _print_v156(o)
        return 0
    return PRIOR.main(args)


def _mk_pdf_v156(path: Path, footer: str) -> None:
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
                pdfmetrics.registerFont(TTFont("CJKT6", fp, subfontIndex=0))
                cjk = "CJKT6"
                break
            except Exception:  # noqa: BLE001
                continue
    if cjk == "MSung-Light":
        pdfmetrics.registerFont(UnicodeCIDFont("MSung-Light"))
    W, H = A4
    c = canvas.Canvas(str(path), pagesize=A4)
    for pno in range(1, 6):
        if pno == 1:
            c.setFont(cjk, 20)
            c.drawString(40, H - 80, "健策 3653:液冷題材發酵 營運動能強勁")
            c.setFont("Helvetica-Bold", 13)
            c.drawString(40, H - 120, "Investment highlights")
            c.setFont("Helvetica", 9.5)
            for i in range(16):
                c.drawString(40, H - 140 - i * 13, "Jentech (3653 TT) benefits from liquid cooling adoption across AI servers, line %d." % i)
            c.setFont("Helvetica", 8)
            for j, (k, v) in enumerate((("Rating", "Buy"), ("Target price", "NT$1,200"), ("Close", "NT$980"), ("Bloomberg", "3653 TT"), ("Analyst", "Amy Wang"), ("Tel", "02-2181-8888"))):
                c.drawString(420, H - 120 - j * 12, "%s: %s" % (k, v))
            c.setFont("Helvetica", 6.5)
            c.drawString(40, 95, "Important disclosures and analyst certification are on the last page of this report.")
        elif pno == 4:
            c.setFont("Helvetica-Bold", 13)
            c.drawString(40, H - 70, "Financial summary")
            for rows, x in (([["Income statement", "2023A", "2024A", "2025F", "2026F"], ["Revenue", "12,345", "15,678", "19,012", "23,456"], ["Net income", "1,876", "2,654", "3,456", "4,321"], ["EPS", "15.2", "21.5", "28.0", "35.1"]], 40),
                             ([["Balance sheet", "2023A", "2024A", "2025F", "2026F"], ["Cash", "3,210", "4,321", "5,432", "6,543"], ["Total assets", "20,000", "24,000", "29,000", "35,000"]], 310)):
                t = Table(rows, colWidths=[80, 42, 42, 42, 42])
                t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black), ("FONT", (0, 0), (-1, -1), "Helvetica", 7.5)]))
                t.wrapOn(c, W, H)
                t.drawOn(c, x, H - 180)
        else:
            c.setFont("Helvetica", 10)
            for i in range(28):
                c.drawString(40, H - 60 - i * 14, "Page %d discussion paragraph %d without financial numbers." % (pno, i))
        c.setFont("Helvetica", 6)
        c.drawString(40, 30, footer)
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

    td = Path(tempfile.mkdtemp(prefix="vrnstage-"))
    home = td / "functional modules" / "VRN"
    (home / "SSOT").mkdir(parents=True)
    (home / "knowledge").mkdir()
    rep = td / "VIA_Reports" / "vrn"
    base = td / "VeritasIntelligenceAnalytics"
    vdb = base / "via_database" / "vdf_database"
    vdb.mkdir(parents=True)
    for x in ("via_00_vcgc", "via_01_vdf", "via_02_vrn"):
        (base / x).mkdir()
    inp = td / "inbox"
    (inp / "sub").mkdir(parents=True)
    saved = {k: os.environ.get(k) for k in ("VIA_VRN_SSOT_HOME", "VIA_VRN_HEALTH_OUT", "VIA_VDF_HOME", "VIA_ROOTS_BASE", "VIA_SPILL_DIR", "VIA_VRN_MASTER_LISTS")}
    os.environ.update({"VIA_VRN_SSOT_HOME": str(home), "VIA_VRN_HEALTH_OUT": str(rep), "VIA_VDF_HOME": str(td / "nope"), "VIA_ROOTS_BASE": str(base), "VIA_SPILL_DIR": str(td / "TEMP" / "spill")})
    os.environ.pop("VIA_VRN_MASTER_LISTS", None)
    with (vdb / "vdf_tw_all_stocks.csv").open("w", encoding="utf-8") as fh:
        fh.write("stock_id,name,market\n3653,健策,上市\n3038,全台,上市\n")
        for i in range(1100, 1950):
            fh.write("%d,測%d,上市\n" % (i, i))
    (home / "knowledge" / "VRN_Broker_Dict_v0100.json").write_text(json.dumps({"brokers": {"凱基": {"abbr": "KGI", "aliases": ["凱基", "凱基投顧", "KGI", "KGI Securities"]}, "華南": {"abbr": "HNSC", "aliases": ["華南投顧", "華南"]}}}, ensure_ascii=False), encoding="utf-8")
    ml = _resolve("master_lists")()
    chk("① 路徑:VDF 資料庫(via_database\\vdf_database)= 總清單契約 · 唯讀讀到全台股", ml["origin"] == "live" and any(x["kind"] == "stock" for x in ml["sources"]) and "3653" in ml["entries"])
    good = inp / "凱基投顧_3653 健策_向子慧_20260917.pdf"
    _mk_pdf_v156(good, "KGI Securities Investment Advisory Co., Ltd. | Disclaimer: for information only.")
    bad = inp / "MS-3653 20260917.pdf"
    _mk_pdf_v156(bad, "KGI Securities Investment Advisory Co., Ltd. | Disclaimer: for information only.")
    _mk_pdf_v156(inp / "20260916兆豐台灣產業專題-航太產業.pdf", "Mega Securities")
    (inp / "華南投顧-3038-全台-Memo-20251209.txt").write_text("全台 3038 公司訪談 Memo\n營收成長 毛利率改善\n" * 8, encoding="utf-8")
    (inp / "sub" / "凱基投顧_3653 hidden.pdf").write_bytes(b"%PDF-1.4\n%%EOF\n")
    man = stage_run(inp)
    R = {r["file"]: r for r in man["rows"]}
    g = R[good.name]
    chk("② stage:只取個股報告 · 第一頁 + 年度財報頁 = [1,4](P2/P3/P5 不碰)· 小 PDF 在 TEMP · 產業專題不碰 · 子夾不掃", g["picked"] == [1, 4] and g["mini"] and Path(g["mini"]).exists() and str(td / "TEMP") in g["mini"] and R["20260916兆豐台灣產業專題-航太產業.pdf"].get("picked") is None and not any("hidden" in k for k in R))
    import pdfplumber
    with pdfplumber.open(g["mini"]) as pdf:
        n_mini = len(pdf.pages)
    tx = R["華南投顧-3038-全台-Memo-20251209.txt"]
    chk("③ 小 PDF 只有 2 頁 · TXT 個股 memo 轉 PDF 也在 TEMP", n_mini == 2 and tx.get("src_pdf", "").startswith(str(td / "TEMP")))
    o = layout_run_v156(inp)
    J = {r["file"]: r for r in json.loads((Path(o["html"]).with_name("LAYOUT_latest.json")).read_text(encoding="utf-8"))["rows"]}
    gr = J[good.name]
    full = json.loads(Path(gr["html"]).with_suffix(".json").read_text(encoding="utf-8"))
    ids = [b["id"] for pg in full["pages"] for b in pg["blocks"]]
    chk("④ 頁尾小字辨識 → 不擷取(版面裡沒有 FOOTER 段)· 底部小字 disclosures 也歸頁尾 · 編號用原頁碼 P4", full["footer"]["blocks"] >= 2 and full["footer"]["moved_small"] >= 1 and not any(b["role"] == "FOOTER" for pg in full["pages"] for b in pg["blocks"]) and any(i.startswith("P4·") for i in ids) and not any("disclosures" in b.get("text", "") for pg in full["pages"] for b in pg["blocks"]))
    chk("⑤ 頁尾券商互證:凱基檔 → KGI ✓ · MS 檔頁尾是 KGI → ≠ 檔名 MS(黃)", full["footer"]["broker"] == "KGI" and full["footer"]["xcheck"] == "✓" and J[bad.name]["footer"]["xcheck"].startswith("≠") and J[bad.name]["lamp"] == "YELLOW")
    h = Path(gr["html"]).read_text(encoding="utf-8")
    t1 = next(b for pg in full["pages"] for b in pg["blocks"] if b["kind"] == "table")
    chk("⑥ HTML:頁尾小字不擷取 chip · 只取 P1,P4 · 主標題 · 年度表(格線表以格線為準:表頭「Income statement」不被拆)", "不擷取" in h and "只取 P1,P4" in h and "液冷" in h and "Income statement" in h and t1["rows"][0][0] == "Income statement" and len(t1["rows"][0]) == 5 and gr["lamp"] == "GREEN")
    print("  ── 前版鏈自測(原樣印出)──")
    prc = 0 if os.environ.get("VIA_SKIP_PRIOR_SELFTEST") == "1" else PRIOR.selftest()
    chk("⑦ 前版鏈 %s 自測 rc 0" % PRIOR_PATH.stem, prc == 0)
    chk("⑧ 帶加速器橋", "[VIA:ACCEL-BRIDGE:v0100]" in Path(__file__).read_text(encoding="utf-8"))
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v
    shutil.rmtree(td, ignore_errors=True)
    print("[計] VRN_SystemManager_v0156 自測 %d/%d · %s" % (p, p + f, "PASS" if f == 0 else "FAIL"))
    return 0 if f == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
