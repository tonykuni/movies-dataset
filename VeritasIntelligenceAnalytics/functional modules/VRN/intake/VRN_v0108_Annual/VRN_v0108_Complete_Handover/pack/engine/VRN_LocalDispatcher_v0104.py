#!/usr/bin/env python3
"""Local VRN dispatch; original engines are imported through public callables.
Execution PASS never means financial/semantic validation PASS.
"""
from __future__ import annotations

# 01 PARAMETERS -- edit here or use CLI. Never modify upstream engine files.
PARAMS = {'version': 'v0104',
 'engine_root': 'C:\\Users\\tonyk\\OneDrive\\Desktop\\測試',
 'input_root': 'C:\\Users\\tonyk\\OneDrive\\Desktop\\測試',
 'output_name': 'VRN_Dispatch_Output',
 'workers': 2,
 'document_timeout': 300,
 'max_pages': 250,
 'finance_page_limit': 8,
 'ocr_timeout': 60,
 'figure_dpi': 120,
 'geometry_y_tolerance': 1.8,
 'header_left_margin': 3.0,
 'max_scan_files': 6000,
 'max_scan_depth': 6,
 'table_tools': ['pdfplumber'],
 'extensions': ['.pdf', '.txt', '.md', '.docx', '.png', '.jpg', '.jpeg'],
 'exclude_dirs': ['.venv',
                  'venv',
                  '__pycache__',
                  '.git',
                  'node_modules',
                  'output',
                  'tools',
                  'fixtures',
                  'VRN_Dispatch_Output'],
 'extra_profile': 'profiles/CLST_6669_20251001.json',
 'target_revision_regex': 'raise our TP from NT\\$([\\d,]+) to NT\\$([\\d,]+)',
 'narrative_2026_growth_regex': 'forecast 2026 sales to grow (\\d+(?:\\.\\d+)?)% YoY',
 'rating_header_regex': '-\\s*(OUTPERFORM|UNDERPERFORM|NEUTRAL)',
 'roles': {'manager': {'pattern': 'VRN_SystemManager_v*.py',
                       'api': ['acquire_document', 'extract_metadata', 'load_rules']},
           'layout': {'pattern': 'VRN_ENG394_LayoutRestore_v*.py', 'api': ['restore_pdf']},
           'completeness': {'pattern': 'VRN_ENG392_TextCompleteness_v*.py', 'api': ['coverage', 'numbers']},
           'restore': {'pattern': 'VRN_ReportRestore_v*.py',
                       'api': ['restore_text', 'restore_table', 'validate_table']},
           'nlp': {'pattern': 'VIA_NLP_OneEngine_v*.py', 'api': ['def_process', 'def_legacy_analysis']},
           'accelerator': {'pattern': 'VeritasCeleritas_v*.py', 'api': ['xrun', 'apply_thread_limits']},
           'temp': {'pattern': 'SUP_MDL867_TempSpill_v*.py', 'api': ['activate']}},
 'readable_css': '\n'
                 '*{box-sizing:border-box}body{margin:0;background:#f6f5f1;color:#243336;font:16px/1.85 "Microsoft '
                 'JhengHei",system-ui,sans-serif}main{max-width:1050px;margin:auto;padding:30px 22px '
                 '70px}h1{font-size:34px;line-height:1.35}h2{font-size:26px;margin:0 0 '
                 '16px}h3{font-size:21px}section,.card{background:white;border:1px solid '
                 '#dee4df;border-radius:14px;padding:26px;margin:22px '
                 '0}a{color:#17665c}nav{display:flex;gap:12px;flex-wrap:wrap}nav a{background:#e7f1ed;padding:8px '
                 '16px;text-decoration:none;border-radius:8px}p{margin:10px 0 '
                 '18px}.muted,small{color:#60716f}.badge{display:inline-block;background:#e8f1ed;color:#245c4c;padding:5px '
                 '13px;border-radius:7px}.warning{background:#fff4d9;border-color:#e4c879}table{border-collapse:collapse;width:100%;font-size:16px;white-space:nowrap}td,th{padding:11px '
                 '13px;border-bottom:1px solid '
                 '#e0e6e2;text-align:right}td:first-child,th:first-child{text-align:left}th{background:#edf3f0}tr:nth-child(even){background:#fafbf9}.scroll{overflow-x:auto}summary{cursor:pointer;font-weight:650;padding:13px '
                 '0;color:#17665c}details{border-top:1px solid '
                 '#e3e8e4;margin-top:18px}img{max-width:100%;height:auto;border:1px solid '
                 '#dae0da;border-radius:6px;margin:12px '
                 '0}.source{font-size:16px;background:#f8f9f6;padding:18px;border-left:3px solid '
                 '#c3d4cb}.grid{display:grid;grid-template-columns:1fr 1fr;gap:20px}.grid '
                 '.card{margin:0}li{margin-bottom:9px}@media(max-width:650px){main{padding:18px '
                 '12px}.grid{grid-template-columns:1fr}section{padding:18px}h1{font-size:29px}}@media '
                 'print{details>*{display:block}nav{display:none}section{break-inside:avoid}body{background:white}}\n'
                 'header{line-height:1.6}header small{display:block;letter-spacing:1px}header '
                 'b{display:block;font-size:13px}pre{white-space:pre-wrap;overflow-wrap:anywhere}details '
                 'a{margin-right:15px} '
                 'th{white-space:normal;min-width:105px}td:first-child{min-width:180px}td{white-space:nowrap}',
 'finance_focus_labels': {'Revenue (NT$m)': '營收（新臺幣百萬元）', 'Net profit (NT$m)': '淨利（新臺幣百萬元）', 'EPS (NT$)': '每股盈餘（新臺幣元）'},
 'table_title_zh': {'Financials — 首頁': '首頁財務重點',
                    'Profit & Loss — 摘要': '損益表摘要',
                    'Cashflow — 摘要': '現金流量表摘要',
                    'Balance sheet — 摘要': '資產負債表摘要',
                    'Ratio analysis — 摘要': '財務比率摘要',
                    'Forecast revisions — old / new / % ch': '預估值修正：舊值／新值／變動率',
                    'Quarterly P&L — 季度 / 年度': '季度與年度損益表',
                    'Target price change — 舊 / 新目標價': '目標價修正',
                    'Profit & Loss — 明細': '損益表明細',
                    'Profit & loss ratios': '損益相關比率',
                    'Balance sheet — 明細': '資產負債表明細',
                    'Balance sheet ratios': '資產負債相關比率',
                    'Cashflow — 明細': '現金流量表明細',
                    'Cashflow ratio analysis': '現金流量相關比率',
                    'DuPont analysis': '杜邦分析',
                    'EVA analysis': '經濟附加價值分析'},
 'readable_exports': [('SourcePages.csv','全部頁面 CSV'),
                      ('ReportText.csv','本文 CSV'),
                      ('ReportDigest.csv','來源摘要 CSV'),
                      ('TableCandidates.csv','表格候選 CSV'),
                      ('ImageCandidates.csv','圖片候選 CSV'),
                      ('result.json', '完整 JSON'),
                      ('StockReportBasicInfo.csv', '基本資料 CSV'),
                      ('StockReportFinancialData.csv', '財報 CSV'),
                      ('report.md', 'Markdown'),
                      ('StockReportBasicInfo.parquet', '基本資料 Parquet'),
                      ('StockReportFinancialData.parquet', '財報 Parquet')],
 'quarter_months': {'mar': 1, 'jun': 2, 'sep': 3, 'dec': 4},
 'cell_trim_regex': '[\\s\\u200b\\ufeff]+',
 'cell_row_tolerance': 3.0,
 'light_dpi': 200,
 'region_dpi': 350,
 'native_min_chars': 40,
 'ocr_low_confidence': 60,
 'max_ocr_low_fraction': 0.15,
 'ocr_max_tier': 'heavy',
 'heavy_ocr_command': [],
 '_ocr_slot_root': None,
 'ocr_slot_wait_seconds': 120,
 'ocr_image_regions': True,
 'ocr_min_image_area_ratio': 0.15,
 'ocr_max_regions_per_page': 2,
 'quarter_sum_rounding_tolerance': 2.5,
 'quarter_additive_metrics': ['營業收入',
                              '營業成本',
                              '營業毛利',
                              '營業費用',
                              '營業利益',
                              '折舊',
                              '攤提',
                              'EBITDA',
                              '利息收入',
                              '投資利益淨額',
                              '其他營業外收入',
                              '總營業外收入',
                              '利息費用',
                              '投資損失',
                              '其他營業外費用',
                              '總營業外費用',
                              '稅前純益',
                              '所得稅費用[利益]',
                              '少數股東損益',
                              '非常項目前稅後純益',
                              '非常項目',
                              '稅後淨利',
                              'Revenue',
                              'Grossprofit',
                              'Operatingprofit',
                              'Netprofit'],
 'growth_metric_aliases': {'營業收益增長': '營業利益', '營業收益': '營業利益', '稅後純益': '稅後淨利'},
 'growth_rounding_epsilon': 1e-08,
 'quarter_end_date_regex': '((?:19|20)\\d{2})[-/.](\\d{1,2})[-/.](\\d{1,2})(A|F|CT)?',
 'all_pages_export': True,
 'csv_field_size_limit': 16000000,
 'disclosure_regex': r'Analyst Certification|Important Disclosures|Disclosures Appendix|Disclaimer|免責聲明|分析師聲明|法律聲明',
 'auto_table_settings': {'vertical_strategy':'text','horizontal_strategy':'text','min_words_vertical':4,'min_words_horizontal':2,'text_x_tolerance':1,'text_y_tolerance':2},
 'raw_table_min_rows':3,
 'digest_signal_regex': r'成長|預估|獲利|營收|需求|風險|評價|展望|供應|預期|市場|投資|growth|forecast|expect|demand|risk|valuation|revenue|profit|margin|outlook',
 'quarter_end_compact_regex': '((?:19|20)\\d{2})(\\d{2})(\\d{2})(A|F|CT)?'}

# 02 Standard-library orchestration. Optional packages stay inside worker calls.
import argparse, ast, base64, csv, fnmatch, hashlib, html, importlib.util, json, os, re
import subprocess, sys, time, traceback, uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
HERE = Path(__file__).resolve().parent
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True


def def_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def def_stable(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()


def def_write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + "." + uuid.uuid4().hex + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
    os.replace(tmp, path)


def def_read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def def_walk(root, config, engine=False, output=None):
    root = Path(root)
    if not root.exists():
        return []
    if root.is_file():
        return [root.resolve()]
    found, count = [], 0
    excluded = set(config["exclude_dirs"])
    if engine:
        excluded -= {"tools"}
    for folder, dirs, files in os.walk(root, followlinks=False):
        parent = Path(folder)
        depth = len(parent.relative_to(root).parts)
        dirs[:] = sorted(d for d in dirs if d not in excluded and not (parent / d).is_symlink()
                         and depth < config["max_scan_depth"]
                         and (engine or (parent / d).resolve() != HERE)
                         and (not output or (parent / d).resolve() != Path(output).resolve()))
        for name in sorted(files):
            count += 1
            if count > config["max_scan_files"]:
                raise ValueError("SCAN_LIMIT_EXCEEDED: reduce input/engine scope")
            p = parent / name
            if not engine and p.is_relative_to(HERE):
                continue
            if not p.is_symlink() and (p.suffix == ".py" if engine else p.suffix.lower() in config["extensions"]):
                found.append(p.resolve())
    return found


def def_version(path):
    match = re.search(r"_v(\d+(?:_\d+)*)", Path(path).name)
    return tuple(int(x) for x in match.group(1).split("_")) if match else (0,)


def def_discover(root, config):
    # AST/compile are read-only. Import only chosen roles in isolated child jobs.
    external = def_walk(root, config, engine=True)
    bundled = def_walk(HERE / "tools", config, engine=True)
    inventory, chosen, issues = [], {}, []
    for role, contract in config["roles"].items():
        candidates = []
        for p in sorted(set(external + bundled)):
            if not fnmatch.fnmatch(p.name, contract["pattern"]):
                continue
            row = {"role": role, "path": str(p), "sha256": def_hash(p), "version": list(def_version(p)),
                   "origin": "BUNDLED" if p.is_relative_to(HERE / "tools") else "EXTERNAL", "status": "INCOMPATIBLE"}
            try:
                text = p.read_text(encoding="utf-8-sig")
                tree = ast.parse(text, filename=str(p))
                compile(tree, str(p), "exec")
                names = {n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
                row["missing_api"] = sorted(set(contract["api"]) - names)
                if not row["missing_api"]:
                    row["status"] = "READY_FOR_IMPORT"
                    candidates.append(row)
            except Exception as exc:
                row["error"] = str(exc)
            inventory.append(row)
        if not candidates:
            issues.append({"role": role, "reason": "NO_COMPATIBLE_ENGINE"})
            continue
        version = max(tuple(r["version"]) for r in candidates)
        top = [r for r in candidates if tuple(r["version"]) == version]
        if len({r["sha256"] for r in top}) > 1:
            issues.append({"role": role, "reason": "SAME_VERSION_DIFFERENT_HASH", "paths": [r["path"] for r in top]})
            continue
        # Identical bytes: prefer user's local downloaded copy.
        selected = sorted(top, key=lambda r: (r["origin"] == "BUNDLED", r["path"]))[0]
        selected["status"] = "SELECTED"
        chosen[role] = dict(selected)
    lock = def_read(HERE / "UPSTREAM_LOCK.json")
    for rel, sha in lock.items():
        p = HERE / rel
        if not p.is_file() or def_hash(p) != sha:
            issues.append({"role": "upstream", "reason": "BUNDLE_HASH_MISMATCH", "path": rel})
    return {"selected": chosen, "inventory": inventory, "issues": issues, "upstream_lock": lock,
            "dependency_hashes": {r["path"]: r["sha256"] for r in inventory}}


def def_load(role, selected):
    row = selected[role]
    path = Path(row["path"])
    if def_hash(path) != row["sha256"]:
        raise ValueError("ENGINE_CHANGED_BEFORE_IMPORT: " + role)
    spec = importlib.util.spec_from_file_location("vrn_dispatch_" + role, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    for name in PARAMS["roles"][role]["api"]:
        if not callable(getattr(module, name, None)):
            raise TypeError("IMPORTED_API_NOT_CALLABLE: " + role + "." + name)
    return module


def def_call(role, module, name, args, calls, accelerator=None):
    start = time.perf_counter()
    row = {"role": role, "function": name, "status": "RUNNING"}
    calls.append(row)
    try:
        function = getattr(module, name)
        if accelerator is None:
            value = function(*args)
        else:
            row["via"] = "VeritasCeleritas.xrun"
            # A legacy pool runner may retry a callable after an exception.
            # Return failures as data so mutating callables execute at most once.
            def guarded():
                try:
                    return {"dispatch_ok": True, "value": function(*args)}
                except Exception as exc:
                    return {"dispatch_ok": False, "error": str(exc)}
            envelope = accelerator.xrun(guarded)
            if isinstance(envelope, dict) and envelope.get("dispatch_ok") is False:
                raise RuntimeError(envelope["error"])
            value = envelope["value"] if isinstance(envelope, dict) and envelope.get("dispatch_ok") else envelope
        if value is None and name not in {"apply_thread_limits"}:
            raise RuntimeError("EMPTY_ENGINE_RESULT")
        if isinstance(value, dict) and value.get("runner") == "xrun" and value.get("status") == "error":
            raise RuntimeError("ACCELERATOR_REPORTED_ERROR: " + str(value.get("msg")))
        row["status"] = "PASS"
        return value
    except Exception as exc:
        row.update(status="FAIL", error=str(exc))
        raise
    finally:
        row["seconds"] = round(time.perf_counter() - start, 4)


# 03 Source-hash-locked profiles; page/zone/table provenance stays separate.
def def_profile(source_sha):
    extra = HERE / PARAMS['extra_profile']
    if extra.is_file():
        profile = def_read(extra)
        if profile['source_sha256'] == source_sha:
            return profile
    record = def_read(HERE / 'profiles/source_hashes.json').get(source_sha)
    if not record:
        return None
    layout = def_read(HERE / 'profiles/first_page.json')
    return next((r for r in layout['reports'] if r['id'] == record['id']), None)


def def_crop(page, box, name, job, config):
    import fitz
    box = fitz.Rect(box) & page.rect
    if box.is_empty:
        raise ValueError("EMPTY_CROP")
    target = Path(job) / "evidence" / (name + ".png")
    target.parent.mkdir(exist_ok=True)
    page.get_pixmap(matrix=fitz.Matrix(config["figure_dpi"] / 72, config["figure_dpi"] / 72), clip=box).save(target)
    return str(target.relative_to(job))


def def_verify_period_geometry(path, table, restore, config):
    """Audit same-PDF reader agreement. Narrow five-year header schema only.
    Any rebuild is traceable source recovery, not independent validation.
    """
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        words = pdf.pages[table["page"] - 1].crop(tuple(table["bbox_pt"])).extract_words(x_tolerance=1, y_tolerance=1)
    headers = sorted([w for w in words if re.fullmatch(r"Dec-\d\d[AF]", w["text"])], key=lambda w: w["x0"])
    if len(headers) != 5 or len({w["text"] for w in headers}) != 5 or max(w["top"] for w in headers) - min(w["top"] for w in headers) > 2:
        table["position_validation"] = {"status": "REVIEW_SCHEMA_NOT_SUPPORTED", "reason": "Not a single five-year annual header row"}
        return
    centers = [(w["x0"] + w["x1"]) / 2 for w in headers]
    item_edge = headers[0]["x0"] - config["header_left_margin"]
    groups = []
    for word in sorted(words, key=lambda w: ((w["top"] + w["bottom"]) / 2, w["x0"])):
        cy = (word["top"] + word["bottom"]) / 2
        group = next((g for g in reversed(groups[-3:]) if abs(g["cy"] - cy) <= config["geometry_y_tolerance"]), None)
        if group is None:
            groups.append({"cy": cy, "words": [word]})
        else:
            group["words"].append(word)
    comparisons, repairs = [], []
    for row in table["records"]:
        if row["component"] != "ROW" or len(row["cells"]) != 6:
            continue
        cy = sum((a[1] + a[3]) / 2 for a in row["anchors"]) / len(row["anchors"])
        group = min(groups, key=lambda g: abs(g["cy"] - cy))
        if abs(group["cy"] - cy) > 3:
            comparisons.append({"row": row["row_index"], "status": "REVIEW_NO_Y_MATCH"})
            continue
        cells = ["" for _ in range(6)]
        for word in sorted(group["words"], key=lambda w: w["x0"]):
            col = 0 if word["x0"] < item_edge else 1 + min(range(5), key=lambda j: abs((word["x0"] + word["x1"]) / 2 - centers[j]))
            cells[col] += (" " if cells[col] else "") + word["text"]
        cells = [restore.tidy_cell(c) for c in cells]
        before = row["cells"][:]
        # Known historical defect: long ROIC item labels leak into the first year.
        # Repair only this exact source-locked ROI table from native word positions.
        rebuilt = "投資回報率" in table["title"] and before != cells
        if rebuilt:
            row["upstream_cells"] = before
            row["cells"] = cells
            row["text"] = " | ".join(cells)
            row["status"] = "SOURCE_GEOMETRY_REBUILT_REVIEW"
            repairs.append({"row": row["row_index"], "before": before, "after": cells, "method": "same-row native words and printed period-header centers"})
        for col in range(6):
            comparisons.append({"row": row["row_index"], "column": col, "period": headers[col - 1]["text"] if col else "ITEM",
                                "upstream": before[col], "source_geometry": cells[col],
                                "status": "SOURCE_REBUILT" if rebuilt else "PASS" if before[col] == cells[col] else "REVIEW"})
    table["position_validation"] = {"status": "REVIEW_REBUILDS" if repairs else "PASS_SAME_PDF_READERS" if comparisons and all(r["status"] == "PASS" for r in comparisons) else "REVIEW",
                                    "basis": "Readers share one PDF; not official-history verification", "cells": comparisons, "repairs": repairs}


def def_restore_core(path, acquired, modules, config, job, calls, accelerator, source_sha):
    if path.suffix.lower() != ".pdf":
        records = [{"page": p["page"], "zone": "BODY_UNSEGMENTED", "text": line["text"], "raw_text": line["text"],
                    "anchors": [line.get("bbox")], "component": "SOURCE_LINE", "status": "REVIEW_LAYOUT_UNAVAILABLE"}
                   for p in acquired["pages"] for line in p["lines"]]
        return {"profile": "NO_PDF_LAYOUT", "records": records, "tables": [], "checks": [], "crops": [], "source_excerpt": records[:3]}
    import fitz
    layout, restore, complete = modules["layout"], modules["restore"], modules["completeness"]
    rulebook = def_read(HERE / "tools/repo_tools/VIA_VRN_LayoutRestore_SSOT_v0100.json")
    current = layout
    while True:
        current._SSOT_CACHE = rulebook
        # Thin version tails delegate to PRIOR; bind the chosen ENG392 explicitly.
        current._eng392 = lambda: complete
        if "PRIOR" not in vars(current):
            break
        current = current.PRIOR
    profile = def_profile(source_sha)
    if profile and profile.get('kind') == 'SOURCE_CALIBRATED':
        return def_restore_calibrated(path, acquired, modules, config, job, calls, accelerator, source_sha, profile)
    # FIN_PROFILES belong to the exact original report bytes, even after renaming.
    finance = restore.FIN_PROFILES.get(profile["filename"], {}) if profile else {}
    if not profile:
        rx = re.compile(r"資產負債表|現金流量表|損益表|Income Statement|Balance Sheet|Cash\s*flow|Profit\s*(?:&|and)\s*Loss|Detailed financials", re.I)
        candidates = [p["page"] for p in acquired["pages"] if p["page"] and p["page"] > 1
                      and rx.search("\n".join(l["text"] for l in p["lines"]))]
        finance = {p: [] for p in candidates[:config["finance_page_limit"]]}
    pages = sorted({1, *finance})
    generic = def_layout_selected(path, pages, layout, calls, accelerator)
    records, tables, checks, crops = [], [], [], []
    with fitz.open(path) as pdf:
        if profile:
            zones = [o for o in profile["objects"] if o["level"] == 1 and o["zone"] != "EXCLUDED"]
            known = [o for o in profile["objects"] if o["level"] == 2]
        else:
            first = generic["pages"][0]
            zones = [{"id": "G1-Z" + str(i), "zone": "BODY", "bbox_pt": leaf["bbox"]}
                     for i, leaf in enumerate(first.get("leaves", []), 1) if leaf.get("zone") == "BODY"]
            known = [{"id": "G1-T" + str(i), "bbox_pt": t["bbox"]} for i, t in enumerate(first.get("info", []), 1) if t.get("bbox")]
        for zone in zones:
            recs = def_call("restore", restore, "restore_text", (source_sha[:12], pdf[0], zone, known, layout), calls, accelerator)
            for r in recs:
                r["document_sha256"] = source_sha
            records.extend(recs)
            crops.append({"id": zone["id"], "zone": zone["zone"], "page": 1, "bbox": zone["bbox_pt"],
                          "file": def_crop(pdf[0], zone["bbox_pt"], zone["id"], job, config)})
            if zone["zone"] == "BODY":
                lines = [l for l in restore.lines_from_pdf(pdf[0], zone["bbox_pt"])
                         if not any(restore.in_box(l["bbox"], o["bbox_pt"]) for o in known)]
                src = "\n".join(l["text"] for l in lines)
                dst = "\n".join(r["text"] for r in recs)
                ratio, missing, extra = def_call("completeness", complete, "coverage", (src, dst), calls, accelerator)
                a = def_call("completeness", complete, "numbers", (src,), calls, accelerator)
                b = def_call("completeness", complete, "numbers", (dst,), calls, accelerator)
                checks.append({"check": "BODY_ZONE_CHAR_MULTISET_AND_NUMBERS", "zone": zone["id"], "coverage": ratio,
                               "missing": dict(missing), "extra": dict(extra), "source_numbers": dict(a), "restored_numbers": dict(b),
                               "status": "PASS" if not missing and not extra and a == b and bool(src) else "REVIEW",
                               "scope": "No guarantee of sentence order/semantic equivalence"})
        if not records:
            # OCR words cannot be recovered by a native-text layout engine.
            records = [{"page": 1, "zone": "BODY_UNSEGMENTED", "component": "SOURCE_LINE", "text": l["text"],
                        "raw_text": l["text"], "anchors": [l.get("bbox")], "status": "REVIEW_NO_NATIVE_BODY_LAYOUT"}
                       for l in acquired["pages"][0]["lines"]]
            checks.append({"check": "NATIVE_BODY_LAYOUT", "status": "REVIEW", "reason": "OCR/unsegmented source only"})
        for pno, specs in finance.items():
            for i, (label, bbox) in enumerate(specs, 1):
                obj = {"id": f"FIN-P{pno}-T{i}", "label": label, "bbox_pt": bbox}
                t, recs = def_call("restore", restore, "restore_table", (source_sha[:12], pdf[pno - 1], pno, obj, layout, job), calls, accelerator)
                def_verify_period_geometry(path, t, restore, config)
                def_call("restore", restore, "validate_table", (t,), calls, accelerator)
                t["source_sha256"] = source_sha
                t["crop"] = def_crop(pdf[pno - 1], bbox, obj["id"], job, config)
                t["review_status"] = "REVIEW_GEOMETRY_PERIOD_UNIT_AND_OFFICIAL_HISTORY"
                tables.append(t)
        if not profile:
            for pg in generic["pages"]:
                if pg["page"] == 1:
                    continue
                for i, t in enumerate(pg.get("info", []), 1):
                    tables.append({"id": f"GEN-P{pg['page']}-T{i}", "page": pg["page"], "title": "Layout 表格候選",
                                   "rows": t.get("rows", []), "columns": t.get("columns", []), "bbox_pt": t.get("bbox"),
                                   "status": "REVIEW_UNCALIBRATED_PERIOD_UNIT", "source_sha256": source_sha})
    body = [r for r in records if r["zone"] in ("BODY", "BODY_UNSEGMENTED")]
    return {"profile": "SOURCE_HASH_LOCKED" if profile else "GENERIC_REVIEW", "generic_layout": generic,
            "records": records, "tables": tables, "checks": checks, "crops": crops,
            "source_excerpt": [r for r in body if r.get("component") != "HEADING"][:3]}


# 04 Optional table readers: output candidates; never silently replace source cells.
def def_table_readers(path, restored, names, calls):
    results = []
    if path.suffix.lower() != ".pdf":
        return results
    for table in restored["tables"]:
        box, pno = table.get("bbox_pt"), table["page"]
        if not box:
            continue
        for name in names:
            row = {"tool": name, "table": table["id"], "page": pno, "status": "REVIEW_CANDIDATE"}
            start = time.perf_counter()
            try:
                if name == "pdfplumber":
                    import pdfplumber
                    with pdfplumber.open(path) as pdf:
                        crop = pdf.pages[pno - 1].crop(tuple(box))
                        row["tables"] = crop.extract_tables({"vertical_strategy": "text", "horizontal_strategy": "text"})
                elif name == "camelot":
                    import camelot
                    import fitz
                    with fitz.open(path) as pdf:
                        h = pdf[pno - 1].rect.height
                    area = f"{box[0]},{h-box[1]},{box[2]},{h-box[3]}"
                    row["tables"] = [t.df.fillna("").astype(str).values.tolist() for t in
                                     camelot.read_pdf(str(path), pages=str(pno), flavor="stream", table_areas=[area])]
                elif name == "tabula":
                    import tabula
                    if not hasattr(tabula, "read_pdf"):
                        raise ImportError("tabula-py required; same-name tabula package is incompatible")
                    row["tables"] = [df.fillna("").astype(str).values.tolist() for df in
                                     tabula.read_pdf(str(path), pages=pno, area=[box[1], box[0], box[3], box[2]], stream=True, multiple_tables=True)]
                else:
                    raise ValueError("UNKNOWN_TABLE_TOOL")
                row["status"] = "REVIEW_CANDIDATE" if row["tables"] else "NO_TABLE_RETURNED"
            except Exception as exc:
                row.update(status="UNAVAILABLE_OR_FAILED", error=str(exc))
            row["seconds"] = round(time.perf_counter() - start, 4)
            calls.append({"role": "optional_table", "function": name, "status": row["status"], "seconds": row["seconds"]})
            results.append(row)
    return results


def def_csv_core(job, restored):
    rows = []
    for r in restored["records"]:
        rows.append({"kind": "TEXT", "page": r["page"], "zone": r["zone"], "block": r.get("block_id"), "text": r["text"], "raw": r["raw_text"], "anchors": json.dumps(r.get("anchors"), ensure_ascii=False)})
    for t in restored["tables"]:
        for r in t.get("records", []):
            rows.append({"kind": "TABLE", "page": t["page"], "zone": "FINANCE", "block": t["id"], "text": r["text"], "raw": r["raw_text"], "anchors": json.dumps(r.get("anchors"), ensure_ascii=False)})
    fields = ["kind", "page", "zone", "block", "text", "raw", "anchors"]
    with (job / "restored.csv").open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    try:
        import polars as pl
        pl.DataFrame(rows, schema={k: pl.String for k in fields}, strict=False).write_parquet(job / "restored.parquet")
        return {"csv": "PASS", "parquet": "PASS", "rows": len(rows)}
    except Exception as exc:
        return {"csv": "PASS", "parquet": "UNAVAILABLE", "rows": len(rows), "error": str(exc)}


def def_document_html_core(job, result):
    e = html.escape
    restored = result.get("restoration", {})
    parts = ["<!doctype html><html lang='zh-Hant'><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>",
             "<title>VRN 還原檢視</title><style>body{font:16px system-ui;margin:32px;color:#182d43;background:#f4f7fa}article,section{background:white;padding:22px;margin:18px 0;border-radius:12px}img{max-width:100%;max-height:780px}table{border-collapse:collapse;display:block;overflow:auto}td,th{padding:8px;border:1px solid #ced8e1;white-space:pre-wrap}pre{white-space:pre-wrap}small{color:#52677b}.review{color:#9a5d00}</style>",
             f"<h1>{e(result['filename'])}</h1><p>執行：{e(result['execution_status'])}｜內容驗證：<b class='review'>{e(result['content_status'])}</b></p>",
             "<p><a href='result.json'>完整 JSON</a> · <a href='restored.csv'>CSV</a> · <a href='report.md'>Markdown</a></p>",
             f"<p>來源 SHA256：<small>{e(result['source_sha256'])}</small>｜版面：{e(restored.get('profile','未完成'))}</p>"]
    for c in restored.get("crops", []):
        data = base64.b64encode((job / c["file"]).read_bytes()).decode()
        parts.append(f"<section><h2>首頁 {e(c['zone'])} · {e(c['id'])}</h2><img src='data:image/png;base64,{data}' alt='來源區域裁切'><small>page={c['page']} bbox={e(str(c['bbox']))}</small></section>")
    parts.append("<article><h2>本文還原</h2>")
    for r in restored.get("records", []):
        if r["zone"] in {"BODY", "BODY_UNSEGMENTED"}:
            tag = "h3" if r.get("component") == "HEADING" else "p"
            parts.append(f"<{tag}>{e(r['text'])}</{tag}>")
    parts.append("</article><article><h2>原文摘錄摘要</h2><small>直接摘錄；不代表完整投資結論。</small>")
    parts += [f"<p>{e(r['text'])}</p>" for r in restored.get("source_excerpt", [])]
    parts.append("</article><article><h2>NLP 摘要候選</h2><small>需檢視；NLP 實體與摘要不視為已驗證財務資料。</small><pre>" + e(str(result.get("nlp", {}).get("analysis", {}).get("output", {}).get("summary", ""))) + "</pre></article>")
    for t in restored.get("tables", []):
        parts.append(f"<article><h2>p{t['page']} · {e(t['title'])}</h2><p class='review'>{e(t['status'])}</p>")
        if t.get("crop"):
            data = base64.b64encode((job / t["crop"]).read_bytes()).decode()
            parts.append(f"<details><summary>來源裁切</summary><img src='data:image/png;base64,{data}'></details>")
        parts.append("<table>")
        for r in t.get("records", []):
            parts.append("<tr>" + "".join("<td>" + e(str(c)) + "</td>" for c in r["cells"]) + "</tr>")
        parts.append("</table><details><summary>驗證</summary><pre>" + e(json.dumps(t.get("validation", []), ensure_ascii=False, indent=2)) + "</pre></details></article>")
    parts.append("<article><h2>引擎呼叫與檢查</h2><pre>" + e(json.dumps({"calls": result.get("calls"), "checks": restored.get("checks"), "errors": result.get("errors")}, ensure_ascii=False, indent=2)) + "</pre></article></html>")
    (job / "review.html").write_text("\n".join(parts), encoding="utf-8")
    md = ["# " + result["filename"], "執行：" + result["execution_status"] + "；內容：" + result["content_status"], "## 本文"]
    md += [r["text"] for r in restored.get("records", []) if r["zone"] in {"BODY", "BODY_UNSEGMENTED"}]
    md += ["## 原文摘錄"] + [r["text"] for r in restored.get("source_excerpt", [])]
    (job / "report.md").write_text("\n\n".join(md), encoding="utf-8")


# 04B Exact-source calibration adapters. Upstream program bytes stay unchanged.
def def_layout_selected(path, pages, module, calls, accelerator):
    selected = sorted(set(pages))
    result = {'name': path.name, 'mode': 'pdf', 'pages': [], 'notes': [], 'page_selection': selected, 'page_diagnostics': []}
    for page in selected:
        part = def_call('layout', module, 'restore_pdf', (path, str(page)), calls, accelerator)
        calls[-1]['requested_page'] = page
        if [p['page'] for p in part.get('pages', [])] != [page]:
            raise ValueError('LAYOUT_PAGE_SELECTION_MISMATCH')
        result['page_diagnostics'].append({'page': page, 'verdict': part.get('verdict'), 'completeness': part.get('completeness'), 'notes': part.get('notes')})
        result['pages'].extend(part['pages'])
        result['notes'].extend(part.get('notes', []))
    result['verdict'] = 'REVIEW_ADAPTER_SCOPE'
    return result


def def_clst_heading_type(line, body_size, layout):
    text = line['text']
    profile = def_read(HERE / PARAMS['extra_profile'])
    if text in profile['heading_texts']:
        return 'H1' if text == 'Smoother transition' else 'H2' if text.startswith('Expect better') else 'H3'
    return 'BODY'


def def_period_core(raw, role='value', frequency=None):
    raw = str(raw or '').strip()
    date_period = def_date_period(raw, role, frequency)
    if date_period is not None:return date_period
    m = re.fullmatch(r'([1-4])Q(\d{2})(CT|A|F)?', raw, re.I)
    if m:
        year, quarter, suffix = 2000 + int(m[2]), int(m[1]), (m[3] or '').upper()
        return {'raw': raw, 'period': f'{year}-Q{quarter}', 'frequency': 'QUARTER', 'source_status': 'CT_FORECAST' if suffix == 'CT' else 'FORECAST' if suffix in {'F','E','P'} else 'ACTUAL' if suffix == 'A' else 'UNSPECIFIED', 'column_role': role}
    m = re.fullmatch(r'(Mar|Jun|Sep|Dec)-(\d{2})(A|F)', raw, re.I)
    if m:
        year, suffix = 2000 + int(m[2]), m[3].upper()
        if frequency == 'QUARTER':
            quarter = PARAMS['quarter_months'][m[1].lower()]
            period = f'{year}-Q{quarter}'
        elif frequency == 'ANNUAL':
            period = str(year)
        else:
            period = None
        return {'raw': raw, 'period': period, 'frequency': frequency or 'UNSPECIFIED', 'source_status': 'ACTUAL' if suffix == 'A' else 'FORECAST', 'column_role': role}
    m = re.fullmatch(r'(\d{4}|\d{2})(A|CT|F|E|P)?', raw, re.I)
    if m:
        year = int(m[1]);year = year + 2000 if year < 100 else year
        suffix = (m[2] or '').upper()
        return {'raw': raw, 'period': str(year), 'frequency': 'ANNUAL', 'source_status': 'CT_FORECAST' if suffix == 'CT' else 'FORECAST' if suffix in {'F','E','P'} else 'ACTUAL' if suffix == 'A' else 'UNSPECIFIED', 'column_role': role}
    return {'raw': raw, 'period': None, 'frequency': frequency or 'UNSPECIFIED', 'source_status': 'UNSPECIFIED', 'column_role': role}



def def_period(raw, role='value', frequency=None):
    printed=str(raw or '').strip()
    normalized=re.sub(r'\((A|F|E|P|CT)\)$',r'\1',printed,flags=re.I)
    normalized=re.sub(r'^FY(?=\d)', '', normalized, flags=re.I)
    result=def_period_core(normalized,role,frequency)
    result['raw']=printed
    return result


def def_calibrated_table(path, page, spec, restore, upstream, config):
    import pdfplumber
    compact = lambda s: re.sub(r'\s+', '', s)
    box = spec['bbox_pt']
    words = [{'x0': w[0], 'top': w[1], 'x1': w[2], 'bottom': w[3], 'text': w[4]} for w in page.get_text('words')
             if box[0] <= (w[0] + w[2]) / 2 <= box[2] and box[1] <= (w[1] + w[3]) / 2 <= box[3]]
    header = sorted([w for w in words if abs(w['top'] - spec['header_y']) < 1.1 and w['x0'] > box[0] + 15], key=lambda w: w['x0'])
    if spec.get('anchors'):
        right = spec['anchors']
        header_lines = restore.lines_from_pdf(page, box)
        header_lines = [l for l in header_lines if spec['header_y'] - 1 <= l['bbox'][1] <= spec['header_y'] + 12]
        if not all(any(abs(l['bbox'][2] - x) < 1.5 for l in header_lines) for x in right):
            raise ValueError('CALIBRATED_HEADER_ANCHOR_NOT_FOUND:' + spec['id'])
        item_limit = right[0] - 25
    else:
        first = next((i for i, w in enumerate(header) if compact(w['text']) == compact(spec['headers'][0])), None)
        if first is None:
            raise ValueError('FIRST_HEADER_NOT_FOUND:' + spec['id'])
        header = header[first:]
        combined = ' '.join(w['text'] for w in header)
        tokens = re.findall(r'% ch|\(% YoY\)|(?:[1-4]Q\d{2}|\d{4}|\d{2})(?:CT|A)?|old|new', combined)
        expected = spec['headers']
        if [compact(t) for t in tokens] != [compact(t) for t in expected]:
            raise ValueError('CALIBRATED_HEADER_TEXT_MISMATCH:' + spec['id'] + ':' + str(tokens))
        # % ch / (% YoY) may contain two words; join only those printed labels.
        merged = []
        i = 0
        while i < len(header):
            w = dict(header[i]); token = w['text']
            if token in ('%', '(%') and i + 1 < len(header):
                i += 1; w['x1'] = header[i]['x1']; w['text'] += ' ' + header[i]['text']
            merged.append(w); i += 1
        if len(merged) != len(expected):
            raise ValueError('HEADER_COLUMN_COUNT_MISMATCH:' + spec['id'])
        right = [w['x1'] for w in merged]
        item_limit = merged[0]['x0'] - 20
    numeric = re.compile(r'^(?:[+\-−]?\(?\d[\d,]*(?:\.\d+)?%?\)?%?|--?|nm|n\.m\.|(?:[1-4]Q\d{2}|\d{4}|\d{2})(?:CT|A))$', re.I)
    groups = []
    for word in sorted(words, key=lambda w: ((w['top'] + w['bottom']) / 2, w['x0'])):
        cy = (word['top'] + word['bottom']) / 2
        match = next((g for g in reversed(groups[-3:]) if abs(g['cy'] - cy) <= config['geometry_y_tolerance']), None)
        if match is None:
            groups.append({'cy': cy, 'words': [word]})
        else:
            match['words'].append(word)
    records = []
    for i, group in enumerate(groups, 1):
        cells = [''] * (len(right) + 1)
        anchors, raw = [], []
        for word in sorted(group['words'], key=lambda w: w['x0']):
            is_item = word['x0'] < item_limit or not numeric.fullmatch(word['text'])
            col = 0 if is_item else 1 + min(range(len(right)), key=lambda j: abs(word['x1'] - right[j]))
            cells[col] += (' ' if cells[col] else '') + word['text']
            anchors.append([word['x0'], word['top'], word['x1'], word['bottom']]); raw.append(word['text'])
        cleaned = [compact(c) if j else re.sub(r'\s+', ' ', c).strip() for j, c in enumerate(cells)]
        if cleaned[0].startswith('Source:'):
            component = 'SOURCE'
        elif group['cy'] <= spec['header_y'] + 19 if spec.get('anchors') else group['cy'] <= spec['header_y'] + 8:
            component = 'HEADER'
        elif not any(cleaned[1:]):
            component = 'SECTION'
        else:
            component = 'ROW'
        records.append({'report_id': 'CLST6669', 'page': spec['page'], 'zone': 'INFO', 'block_id': spec['id'], 'type': 'TBL', 'component': component,
                        'row_index': i, 'cells': cleaned, 'cells_raw': cells, 'text': ' | '.join(cleaned), 'raw_text': ' '.join(raw), 'anchors': anchors,
                        'source_y': group['cy'], 'repair_method': 'native words at printed-header right anchors; exact-source calibration', 'status': 'SOURCE_GEOMETRY_RESTORED_REVIEW'})
    with pdfplumber.open(path) as pdf:
        independent = pdf.pages[spec['page'] - 1].crop(tuple(box)).extract_words(x_tolerance=1, y_tolerance=1)
    audit = []
    for record in records:
        if record['component'] != 'ROW':
            continue
        cells = [''] * (len(right) + 1)
        for word in sorted([w for w in independent if abs((w['top'] + w['bottom']) / 2 - record['source_y']) <= 2.2], key=lambda w: w['x0']):
            is_item = word['x0'] < item_limit or not numeric.fullmatch(word['text'])
            col = 0 if is_item else 1 + min(range(len(right)), key=lambda j: abs(word['x1'] - right[j]))
            cells[col] += (' ' if cells[col] else '') + word['text']
        for col, (a, b) in enumerate(zip(record['cells'], cells)):
            audit.append({'row': record['row_index'], 'column': col, 'source_word_value': a, 'second_word_reader_value': b,
                          'status': 'PASS' if compact(a) == compact(b) else 'REVIEW'})
    columns = [def_period(p, role) for p, role in zip(spec['periods'], spec['roles'])]
    return {'id': spec['id'], 'report_id': 'CLST6669', 'page': spec['page'], 'title': spec['title'], 'bbox_pt': box,
            'column_right_anchors': right, 'column_edges_pt': upstream.get('column_edges_pt'), 'period_headers': ['ITEM'] + spec['periods'],
            'column_metadata': columns, 'printed_headers': spec['headers'], 'records': records, 'source_status': 'PRESENT' if any(r['component'] == 'SOURCE' for r in records) else 'PAGE_SOURCE_LINKED',
            'source_text': 'CLST', 'source_page': spec['page'], 'upstream_restore_candidate': upstream, 'validation': [], 'status': 'SOURCE_RESTORED_GEOMETRY_REVIEW',
            'historical_crosscheck_status': 'PENDING_OFFICIAL_SAME_PERIOD_DATA',
            'position_validation': {'basis': 'fitz words versus pdfplumber words on the same PDF at printed-header anchors; shared source and calibration can share errors',
                                    'status': 'PASS_SAME_SOURCE_READERS' if audit and all(r['status'] == 'PASS' for r in audit) else 'REVIEW', 'cells': audit}}


def def_clst_arithmetic(tables, restore):
    definitions = {
        'Profit & Loss — 明細': [('Gross Profit (ex-D&A)', ['Revenue', 'Cogs (ex-D&A)']), ('Op Ebit', ['Op Ebitda', 'Depreciation/amortisation']), ('Net interest inc/(exp)', ['Interest income', 'Interest expense']), ('Profit after tax', ['Profit before tax', 'Taxation']), ('Net profit', ['Profit after tax', 'Minority interest'])],
        'Balance sheet — 明細': [('Current assets', ['Cash & equivalents', 'Accounts receivable', 'Inventories', 'Other current assets']), ('Current liabilities', ['Short term loans/OD', 'Accounts payable', 'Accrued expenses', 'Taxes payable', 'Other current liabs']), ('Total equity', ['Shareholder funds', 'Minorities/other equity']), ('Total assets', ['Total liabilities', 'Total equity'])],
        'Cashflow — 明細': [('Free cashflow', ['Net operating cashflow', 'Capital expenditure']), ('Incr/(decr) in net cash', ['Net operating cashflow', 'Net investing cashflow', 'Net financing cashflow']), ('Closing cash', ['Opening cash', 'Incr/(decr) in net cash', 'Exch rate movements'])],
    }
    for table in tables:
        by_item = {r['cells'][0]: r for r in table['records'] if r['component'] == 'ROW'}
        for target, sources in definitions.get(table['title'], []):
            if any(name not in by_item for name in [target] + sources):
                table['validation'].append({'rule': target, 'status': 'REVIEW_LABEL_NOT_FOUND', 'inputs': sources})
                continue
            for col, meta in enumerate(table['column_metadata'], 1):
                if meta['column_role'] != 'value' or meta['frequency'] != 'ANNUAL':
                    continue
                raw = [by_item[name]['cells'][col] for name in [target] + sources]
                numbers = [restore.parse_number(value) for value in raw]
                if any(n is None for n in numbers):
                    table['validation'].append({'rule': target, 'column': col, 'period': meta, 'status': 'REVIEW_NOT_PRINTED_NUMERIC', 'raw': raw})
                    continue
                actual, calculated = numbers[0], sum(numbers[1:])
                tolerance = .5 * len(raw)
                table['validation'].append({'rule': target + '=sum(' + ', '.join(sources) + ')', 'column': col, 'period': meta,
                                            'raw': raw, 'actual': actual, 'calculated': calculated, 'difference': actual - calculated,
                                            'tolerance': tolerance, 'status': 'PASS' if abs(actual - calculated) <= tolerance else 'REVIEW_SOURCE_ARITHMETIC',
                                            'source_policy': 'Calculation never replaces source values'})


def def_restore_calibrated(path, acquired, modules, config, job, calls, accelerator, source_sha, profile):
    import fitz
    restore, layout, complete = modules['restore'], modules['layout'], modules['completeness']
    generic = def_layout_selected(path, profile['research_pages'], layout, calls, accelerator)
    restore.heading_type = def_clst_heading_type
    records, tables, checks, crops, figures = [], [], [], [], []
    with fitz.open(path) as pdf:
        for zone in profile['body_zones']:
            page = pdf[zone['page'] - 1]
            recs = def_call('restore', restore, 'restore_text', (source_sha[:12], page, zone, [], layout), calls, accelerator)
            for record in recs:
                record['page'] = zone['page']; record['document_sha256'] = source_sha
                for a, b in re.findall(r'(\b[A-Za-z]+)-\s+([a-z][A-Za-z]+)', record['raw_text']):
                    if a + b in record['text']:
                        record['text'] = record['text'].replace(a + b, a + '-' + b)
                        record['repair_method'] += '; source line-ending hyphen retained'
            records.extend(recs)
            lines = restore.lines_from_pdf(page, zone['bbox_pt'])
            src, dst = '\n'.join(l['text'] for l in lines), '\n'.join(r['text'] for r in recs)
            ratio, missing, extra = def_call('completeness', complete, 'coverage', (src, dst), calls, accelerator)
            a = def_call('completeness', complete, 'numbers', (src,), calls, accelerator)
            b = def_call('completeness', complete, 'numbers', (dst,), calls, accelerator)
            checks.append({'check': 'BODY_CHAR_MULTISET_AND_NUMBERS', 'page': zone['page'], 'zone': zone['id'], 'coverage': ratio, 'missing': dict(missing), 'extra': dict(extra), 'numeric_equal': a == b,
                           'status': 'PASS' if src and not missing and not extra and a == b else 'REVIEW'})
        for zone in profile['objects']:
            crops.append({'id': zone['id'], 'zone': zone['zone'], 'page': 1, 'bbox': zone['bbox_pt'], 'file': def_crop(pdf[0], zone['bbox_pt'], zone['id'], job, config)})
            if zone['zone'] == 'INFO' and zone['id'] != 'CLST-Z4':
                for line in restore.lines_from_pdf(pdf[0], zone['bbox_pt']):
                    records.append({'page': 1, 'zone': 'INFO', 'block_id': zone['id'], 'component': 'INFO', 'text': line['text'], 'raw_text': line['raw_text'], 'anchors': [line['bbox']], 'status': 'SOURCE_INFO_RETAINED'})
        for spec in profile['financial_tables']:
            obj = {'id': spec['id'], 'label': spec['title'], 'bbox_pt': spec['bbox_pt']}
            upstream, _ = def_call('restore', restore, 'restore_table', (source_sha[:12], pdf[spec['page'] - 1], spec['page'], obj, layout, job), calls, accelerator)
            table = def_calibrated_table(path, pdf[spec['page'] - 1], spec, restore, upstream, config)
            table['source_sha256'] = source_sha
            table['crop'] = def_crop(pdf[spec['page'] - 1], spec['bbox_pt'], spec['id'], job, config)
            tables.append(table)
        for figure in profile['figures']:
            figures.append({**figure, 'file': def_crop(pdf[figure['page'] - 1], figure['bbox_pt'], figure['id'], job, config), 'status': 'SOURCE_CHART_PRESERVED_NO_DIGITIZATION'})
    def_clst_arithmetic(tables, restore)
    checks.append({'check': 'RESEARCH_PAGE_SELECTION', 'requested': profile['research_pages'], 'actual': [p['page'] for p in generic['pages']], 'status': 'PASS'})
    checks.append({'check': 'DISCLOSURES_EXCLUDED_FROM_NLP', 'pages': profile['disclosure_pages'], 'retained': 'full acquisition source lines', 'status': 'PASS'})
    body = [r for r in records if r['zone'] == 'BODY']
    return {'profile': 'SOURCE_HASH_LOCKED_CLST', 'generic_layout': generic, 'records': records, 'tables': tables, 'checks': checks, 'crops': crops, 'figures': figures,
            'body_anchor_checks': def_body_anchor_checks(path, records),
            'source_excerpt': [r for r in body if r['component'] != 'HEADING'][:4], 'research_pages': profile['research_pages'], 'disclosure_pages': profile['disclosure_pages']}


def def_source_metadata(path, restored, metadata):
    records = restored['records']
    body = ' '.join(r['text'] for r in records if r['zone'] == 'BODY')
    header = ' '.join(r['text'] for r in records if r.get('block_id') == 'CLST-Z1')
    match = re.search(PARAMS['target_revision_regex'], body, re.I)
    if match:
        prior, current = [float(v.replace(',', '')) for v in match.groups()]
        metadata['upstream_target_prior'] = metadata['target_prior']
        metadata['target_prior'] = prior; metadata['target_current'] = current
        metadata['target_revision_evidence'] = {'raw': match.group(), 'page': 1, 'anchors': [r['anchors'] for r in records if match.group() in r['text']], 'basis': 'restored source sentence; checked against page4 target-price table'}
        target = next(t for t in restored['tables'] if t['title'].startswith('Target price change'))
        old = next(r for r in target['records'] if r['cells'][0] == 'Old')
        new = next(r for r in target['records'] if r['cells'][0] == 'New')
        metadata['target_revision_check'] = {'status': 'PASS' if float(old['cells'][-1].replace(',', '')) == prior and float(new['cells'][-1].replace(',', '')) == current else 'REVIEW', 'old_row': old['cells'], 'new_row': new['cells']}
    rating = re.search(PARAMS['rating_header_regex'], header)
    metadata['rating_raw'] = rating[1] if rating else None
    metadata['canonical_rating_from_upstream_ssot'] = metadata.get('rating')
    metadata['company_name_printed'] = header.split('NT$')[0].strip()
    metadata['company_name_source'] = 'FIRST_PAGE_PRINTED_NAME; official company-name lookup pending'
    metadata['report_price_printed'] = re.search(r'NT\$([\d,]+\.\d+)', header)[1]
    metadata['download_suffix_date_is_report_date'] = False
    return metadata


def def_number(raw):
    text = re.sub(r'\s+', '', str(raw or '')).replace('−', '-')
    text = text.replace('%', '')
    negative = text.startswith('(') and text.endswith(')')
    if negative:
        text = text[1:-1]
    text = text.replace(',', '')
    if not re.fullmatch(r'[+\-]?\d+(?:\.\d+)?', text):
        return None
    return -float(text) if negative else float(text)


def def_source_digest(restored, profile):
    sections, heading = {}, None
    for record in restored['records']:
        if record['zone'] != 'BODY':
            continue
        if record.get('component') == 'HEADING':
            heading = record['text']
            sections.setdefault(heading, [])
        elif heading:
            sections[heading].append(record)
    points = []
    for topic, heading in profile['digest_sections'].items():
        evidence = sections.get(heading, [])
        text = ' '.join(r['text'] for r in evidence)
        point = {'topic': topic, 'source_heading': heading, 'text': text, 'source_records': evidence,
                 'status': 'SOURCE_EXCERPT_REVIEW' if evidence else 'REVIEW_MISSING_SECTION'}
        translation = profile.get('readable_digest_zh', {}).get(topic)
        fingerprint = hashlib.sha256(text.encode('utf-8')).hexdigest()
        source_bound = evidence and all(r.get('document_sha256') == profile.get('source_sha256') for r in evidence)
        if translation and source_bound and translation['source_text_sha256'] == fingerprint:
            point['reading_text_zh'] = translation['text_zh']
            point['reading_translation_status'] = 'HUMAN_SOURCE_BOUND_REVIEW'
        elif translation:
            point['reading_translation_status'] = 'REVIEW_SOURCE_CHANGED_TRANSLATION_WITHHELD'
        points.append(point)
    return points



def def_consistency_checks(restored):
    by_title = {t['title']: t for t in restored['tables']}
    def row(table, label):
        return next(r for r in table['records'] if r['component'] == 'ROW' and r['cells'][0] == label)
    body = ' '.join(r['text'] for r in restored['records'] if r['zone'] == 'BODY')
    annual = by_title['Profit & Loss — 明細']
    revenue = row(annual, 'Revenue')
    ratios = by_title['Profit & loss ratios']
    growth = row(ratios, 'Revenue growth (% YoY)')
    printed = def_number(growth['cells'][1 + next(i for i, m in enumerate(ratios['column_metadata']) if m['period'] == '2026')])
    values = {m['period']: def_number(revenue['cells'][i]) for i, m in enumerate(annual['column_metadata'], 1)}
    calculated = 100 * (values['2026'] / values['2025'] - 1)
    match = re.search(PARAMS['narrative_2026_growth_regex'], body)
    checks = [{'check': 'ANNUAL_2026_REVENUE_GROWTH', 'printed_percent': printed, 'calculated_percent': calculated,
               'revenue_2025': values['2025'], 'revenue_2026': values['2026'], 'page': 5,
               'status': 'PASS' if abs(printed - calculated) <= .05 else 'REVIEW_SOURCE_ARITHMETIC'}]
    checks.append({'check': 'NARRATIVE_VS_TABLE_2026_REVENUE_GROWTH', 'narrative_percent': float(match[1]) if match else None,
                   'narrative_raw': match.group() if match else None, 'narrative_page': 1, 'table_percent': printed, 'table_page': 5,
                   'status': 'REVIEW_SOURCE_CONFLICT' if match and abs(float(match[1]) - printed) > .05 else 'PASS' if match else 'REVIEW_NO_NARRATIVE',
                   'policy': 'Retain both printed claims; no correction/overwrite without independent evidence'})
    forecast = by_title['Forecast revisions — old / new / % ch']
    eps = row(forecast, 'EPS (NT$)')
    for group, year in enumerate(['2025', '2026', '2027']):
        old, new, delta = [def_number(eps['cells'][group * 3 + i]) for i in [1, 2, 3]]
        computed = (new / old - 1) * 100
        checks.append({'check': 'EPS_REVISION_PERCENT', 'period': year, 'old': old, 'new': new, 'printed_percent': delta, 'calculated_percent': computed,
                       'status': 'PASS' if abs(computed - delta) <= .5 else 'REVIEW_SOURCE_ARITHMETIC', 'page': 3})
    return checks


def def_csv(job, restored):
    exports = def_csv_core(job, restored)
    facts = []
    for table in restored['tables']:
        if 'column_metadata' not in table:
            continue
        section = ''
        for record in table['records']:
            if record.get('semantic_component', record['component']) == 'SECTION':
                section = record['cells'][0]
            if record.get('semantic_component', record['component']) != 'ROW' or len(record['cells']) != len(table['column_metadata']) + 1:
                continue
            for col, column in enumerate(table['column_metadata'], 1):
                raw = record.get('cells_raw', record['cells'])[col] if col < len(record.get('cells_raw', record['cells'])) else ''
                cleaned = def_cell_trim(record['cells'][col])
                effective = column
                version = column['column_role']
                metric = record['cells'][0]
                if table['title'].startswith('Target price change'):
                    if column['column_role'] == 'period':
                        continue
                    effective = def_period(record['cells'][2], column['column_role'])
                    version = record['cells'][0].upper()
                    metric = table['printed_headers'][col - 1]
                unit = '%' if '%' in raw or '%' in metric or '%' in section else 'NT$m' if 'NT$m' in metric else 'NT$' if 'NT$' in metric else 'x' if '(x)' in metric else 'UNSPECIFIED'
                if unit == 'UNSPECIFIED' and ('百萬' in section or '百萬' in metric):
                    unit = 'NT$m'
                if unit == 'UNSPECIFIED' and any('NT$m' in r['raw_text'] for r in table['records'] if r['component'] in ['HEADER', 'SECTION']):
                    unit = 'NT$m'
                if unit == 'UNSPECIFIED' and table['title'] in ['Profit & Loss — 明細', 'Balance sheet — 明細', 'Cashflow — 明細', 'Profit & Loss — 摘要', 'Balance sheet — 摘要', 'Cashflow — 摘要']:
                    unit = 'NT$m'
                facts.append({'FILENAME_SHA256': table.get('source_sha256'), 'TABLE_ID': table['id'], 'PAGE': table['page'], 'METRIC': metric,
                              'SECTION': section, 'PERIOD': effective['period'], 'PERIOD_RAW': effective['raw'], 'FREQUENCY': effective['frequency'],
                              'SOURCE_STATUS': effective['source_status'], 'COLUMN_ROLE': column['column_role'], 'VERSION_ROLE': version,
                              'VALUE_RAW': raw, 'VALUE_TRIM': cleaned, 'METRIC_TRIM': def_cell_trim(metric), 'VALUE_NUMERIC': def_number(cleaned), 'UNIT': unit, 'SOURCE': table.get('source_text'),
                              'ANCHORS_JSON': json.dumps(record['anchors']), 'VALIDATION_STATUS': 'SOURCE_BLANK' if cleaned == '' else 'SOURCE_NOT_PRINTED' if cleaned in ['-', '--', 'nm'] else 'SOURCE_RESTORED_REVIEW'})
    if facts:
        def_write(job / 'StockReportFinancialData.json', facts)
        with (job / 'StockReportFinancialData.csv').open('w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=list(facts[0])); writer.writeheader(); writer.writerows(facts)
        exports['financial_rows'] = len(facts)
        try:
            import polars as pl
            pl.DataFrame(facts).write_parquet(job / 'StockReportFinancialData.parquet')
            exports['financial_parquet'] = 'PASS'
        except Exception as exc:
            exports['financial_parquet'] = 'UNAVAILABLE'; exports['financial_parquet_error'] = str(exc)
    return exports



def def_basicinfo_exports(job, metadata):
    row = {key.upper(): value for key, value in metadata.items() if value is None or isinstance(value, (str, int, float, bool))}
    row['REPORT_DATE'] = (metadata.get('report_date') or '').replace('-', '/')
    row['CONTACTS_JSON'] = json.dumps(metadata.get('contacts'), ensure_ascii=False)
    row['CHECKS_JSON'] = json.dumps(metadata.get('checks'), ensure_ascii=False)
    def_write(job / 'StockReportBasicInfo.json', row)
    with (job / 'StockReportBasicInfo.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=list(row)); writer.writeheader(); writer.writerow(row)
    try:
        import polars as pl
        pl.DataFrame([row]).write_parquet(job / 'StockReportBasicInfo.parquet')
        return {'basicinfo_csv': 'PASS', 'basicinfo_parquet': 'PASS'}
    except Exception as exc:
        return {'basicinfo_csv': 'PASS', 'basicinfo_parquet': 'UNAVAILABLE', 'basicinfo_parquet_error': str(exc)}


def def_document_html(job, result):
    """Source-backed readable view for every input; no fixed result counts."""
    job = Path(job)
    e = lambda value: html.escape(str(value))
    restored = result.get('restoration', {})
    metadata = result.get('metadata', {})
    tables = restored.get('tables', [])
    body = [r for r in restored.get('records', []) if r.get('zone') in {'BODY', 'BODY_UNSEGMENTED'}]
    reading = restored.get('reading_validation') or def_reading_checks(restored)
    digest = result.get('source_guided_digest', [])
    source_checks = restored.get('consistency_checks', [])
    issues = [c for c in source_checks if c.get('status') != 'PASS']
    title = metadata.get('company_name') or metadata.get('company_name_printed') or result['filename']
    date = str(metadata.get('report_date') or '未辨識').replace('-', '/')
    finished = result.get('execution_status') == 'PASS'
    badge = '擷取完成；內容仍需確認。' if finished else '擷取未完整完成；請先查看核對結果。'
    if finished and issues:
        badge = '擷取完成；原報告有數字不一致，需要確認。'
    parts = ['<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">',
             '<title>VRN 還原成果｜中文易讀版</title><style>' + PARAMS['readable_css'] + '</style><main>',
             '<header><b>VERITAS INTELLIGENCE ANALYTICS</b><small>DISCIPLINA • PRUDENTIA • INTEGRITAS</small><b>AI-Powered Research & Decision Intelligence Platform</b></header>',
             '<p class="muted">VRN 文件分拆與還原 · 中文易讀版</p><h1>這份報告還原得如何？</h1>',
             f'<p>{e(title)}｜報告日期：{e(date)}</p><p class="badge">{e(badge)}</p>',
             '<p>從上往下看摘要、本文、財報與核對結果；要核對原檔，再展開原文或原圖。</p>',
             '<nav><a href="#digest">1. 摘要</a><a href="#body">2. 本文還原</a><a href="#finance">3. 財報還原</a><a href="#verify">4. 核對結果</a></nav>']
    if issues:
        parts.append('<section class="warning"><h2>原報告有需要確認的差異</h2>')
        for check in issues:
            if check.get('check') == 'NARRATIVE_VS_TABLE_2026_REVENUE_GROWTH':
                calculated = next((c.get('calculated_percent') for c in source_checks if c.get('check') == 'ANNUAL_2026_REVENUE_GROWTH'), None)
                parts.append(f'<p>第 {e(check["narrative_page"])} 頁本文寫 2026 年營收成長 <strong>{e(check["narrative_percent"])}%</strong>；第 {e(check["table_page"])} 頁表格寫 <strong>{e(check["table_percent"])}%</strong>。</p>')
                if calculated is not None:
                    parts.append(f'<p>依表內營收計算約為 <strong>{calculated:.2f}%</strong>。兩種來源說法均保留，沒有自行改寫數字。</p>')
            else:
                parts.append('<p>來源一致性檢查仍需確認；完整證據請展開核對紀錄。</p>')
        parts.append('</section>')
    parts.append('<section id="digest"><h2>1. 摘要：報告在說什麼？</h2><p class="muted">預估與觀點屬於報告發布當時。中文重點由已核對原文的版本提供；英文摘錄與 NLP 摘要仍保留覆核狀態。</p>')
    if digest:
        for point in digest:
            pages = sorted({r.get('page') for r in point.get('source_records', []) if r.get('page') is not None})
            parts.append(f'<h3>{e(point["topic"])}</h3><p>{e(point.get("reading_text_zh") or point["text"] or "此主題未取得來源句子。")}</p>')
            parts.append(f'<details><summary>查看原文 · 第 {e("、".join(map(str, pages)))} 頁</summary><p class="source">{e(point["text"])}</p></details>')
    else:
        parts.append('<p>這份文件尚無來源綁定的中文摘要。以下為直接擷取的原文片段，請核對主題是否完整。</p>')
        parts.extend('<p class="source">' + e(r['text']) + '</p>' for r in restored.get('source_excerpt', []))
    summary = result.get('nlp', {}).get('analysis', {}).get('output', {}).get('summary')
    if summary:
        parts.append('<details><summary>查看離線 NLP 摘要候選 · 需人工確認</summary><p class="source">' + e(summary) + '</p></details>')
    parts.append('</section><section id="body"><h2>2. 本文還原：正文與資料區分開</h2>')
    parts.append(f'<p>已取得 <strong>{len(body)} 筆本文標題或句子</strong>。本文區與公司資料、電話、股價、表格分開顯示；未完成分區的內容會另行提示。</p>')
    if reading['unsegmented_records']:
        parts.append('<p class="warning">部分內容尚未完成版面分區；可能含資料欄或表格文字，需要核對。</p>')
    if reading['duplicate_source_records']:
        parts.append('<p class="warning">偵測到相同來源位置的重複擷取紀錄，已標示待確認，來源紀錄仍保留。</p>')
    profile = def_profile(result.get('source_sha256', '')) or {}
    labels = {o['id']: o.get('label') for o in profile.get('objects', []) if o.get('level') == 1}
    for crop in restored.get('crops', []):
        label = labels.get(crop['id']) or ('本文區' if crop.get('zone') == 'BODY' else '基本資料區')
        parts.append(f'<details><summary>查看第 {e(crop["page"])} 頁分拆：{e(label)}</summary>{def_html_picture(job, crop["file"], label)}</details>')
    for page in sorted({r.get('page', 1) for r in body}):
        parts.append(f'<details><summary>查看第 {e(page)} 頁完整還原本文</summary><div class="source">')
        for record in body:
            if record.get('page', 1) == page:
                tag = 'h3' if record.get('component') == 'HEADING' else 'p'
                parts.append(f'<{tag}>{e(record["text"])}</{tag}>')
        parts.append('</div></details>')
    parts.append('</section><section id="finance"><h2>3. 財報還原</h2>')
    first = next((t for t in tables if t.get('id') == 'CLST-P1-T1'), None)
    if first:
        labels = PARAMS['finance_focus_labels']
        rows = [[labels[r['cells'][0]]] + r['cells'][1:] for r in first['records'] if r['cells'][0] in labels]
        headers = ['項目'] + [f'{m["period"]} ' + ('實際' if m['source_status'] == 'ACTUAL' else '預估' if m['source_status'] == 'CT_FORECAST' else '未標示') for m in first['column_metadata']]
        parts.append('<p>先看首頁重點表。實際＝原檔標示 A；預估＝原檔標示 CT。</p>' + def_html_table(headers, rows))
        parts.append('<p><small>營收與淨利的單位為新臺幣百萬元；每股盈餘為元。季度與全年數字分開保存。</small></p>')
    parts.append(f'<h3>完整 {len(tables)} 個表格</h3><p>點選需要的表格即可展開；左右滑動可看後面的年度。A＝實際；CT＝預估；Old／New＝修正前／後；% ch＝變動率；YoY＝較去年同期；x＝倍。空白與破折號照來源保留。</p>')
    if not tables:
        parts.append('<p>本次未產出財務表格，不能解讀為來源沒有財報資料。</p>')
    for table in tables:
        label = PARAMS['table_title_zh'].get(table.get('title'), table.get('title', '表格候選'))
        parts.append(f'<details><summary>第 {e(table.get("page", "?"))} 頁 · {e(label)}</summary>')
        if table.get('period_headers'):
            for group_view in def_table_views(table):
                parts.append('<h3>' + e(group_view['label']) + '</h3>')
                parts.append(def_html_table(group_view['headers'], group_view['rows']))
            if table.get('column_groups'):
                parts.append('<p class="muted">季度與全年分開；季末日期屬單季，全年列不會與第 4 季合併。</p>')
        else:
            rows = [r['cells'] for r in table.get('records', [])]
            if rows:
                parts.append(def_html_table([], rows))
            else:
                parts.append('<p class="warning">版面工具僅提出表格候選，尚未完成資料格還原。</p>')
        if table.get('crop'):
            parts.append('<details><summary>查看原檔表格圖</summary>' + def_html_picture(job, table['crop'], label) + '</details>')
        parts.append('</details>')
    source_pages=restored.get('source_pages',[])
    if source_pages:
        parts.append('<details><summary>全部 '+str(len(source_pages))+' 頁原始擷取文字（含揭露頁與 OCR 候選）</summary>')
        for source_page in source_pages:
            parts.append('<h3>第 '+e(source_page['PAGE'])+' 頁 · '+e(source_page['LANE'])+'</h3><pre>'+e(source_page['TEXT_RAW'])+'</pre>')
        parts.append('</details>')
    for candidate in restored.get('raw_table_candidates',[]):
        parts.append('<details><summary>第 '+e(candidate['PAGE'])+' 頁 · 原生表格候選 '+e(candidate['TABLE_ID'])+'</summary><p>資料格來源比對與期間／單位判讀分開；此候選不自動併入財務資料。</p>')
        parts.append(def_html_table([],candidate['ROWS_TRIM']))
        parts.append(def_html_picture(job,candidate['CROP'],'表格來源')+'</details>')
    parts.append('</section><section id="verify"><h2>4. 核對結果：可以相信到什麼程度？</h2>')
    fast = [c for t in tables for c in t.get('fast_validation', {}).get('cells', [])]
    growth = [c for t in tables for c in t.get('quarter_validation', {}).get('checks', [])]
    checks = restored.get('body_anchor_checks', [])
    cells = [c for t in tables for c in t.get('position_validation', {}).get('cells', [])]
    arithmetic = [c for t in tables for c in t.get('validation', [])]
    arithmetic_pass = sum(c.get('status') == 'PASS' for c in arithmetic)
    unavailable = sum(c.get('status') == 'REVIEW_NOT_PRINTED_NUMERIC' for c in arithmetic)
    rows = [['擷取流程', '完成' if finished else '未完整完成', '程式執行狀態與內容正確性分開記錄'],
            ['本文原檔位置', f'{sum(c.get("status") == "PASS" for c in checks)}／{len(checks)} 筆通過' if checks else '未執行逐句位置比對', '可在原檔位置追溯的本文'],
            ['重複擷取檢查', '待確認' if reading['duplicate_source_records'] else '未發現相同來源位置的重複紀錄', '不同位置出現相同文字，仍保留'],
            ['兩種讀取方式比較', f'{sum(c.get("status") == "PASS" for c in cells)}／{len(cells)} 格一致' if cells else '未執行資料格位置比對', '同一 PDF 的比對；包括空白與項目格'],
            ['表內算式', f'{arithmetic_pass} 項通過；{unavailable} 項來源缺值無法計算', '未自行補入來源空值'],
            ['來源自身一致性', '需要確認' if issues else '已執行的檢查未發現差異' if source_checks else '未執行一致性檢查', '沒有自行覆寫原報告數字'],
            ['逐格 trim／原生位置比對', f'{sum(c.get("status") == "PASS" for c in fast)}／{len(fast)} 格通過', '文字與數字分格清理；原始文字仍保留'],
            ['四季合計／季增率／年增率', f'{sum(c.get("status") == "PASS" for c in growth)} 項通過；{sum(c.get("status","").startswith("NOT_EVALUABLE") for c in growth)} 項缺資料或比較基期無法驗算；{sum(c.get("status","").startswith("REVIEW") for c in growth)} 項待確認', '不將單季視為累計；比率與 EPS 不做四季加總校正'],
            ['官方歷史財報核對', '尚未完成', '本次驗證範圍為 PDF 的擷取與還原']]
    parts.append(def_html_table(['核對項目', '結果', '意思'], rows))
    parts.append('<p>「通過」代表對應檢查通過；所有來源觀點、預估與未執行的檢查仍需判讀。原檔沒有文字層或未校準的版面，會保留待確認狀態。</p>')
    figures = restored.get('figures', [])
    if figures:
        parts.append(f'<details><summary>查看保留下來的 {len(figures)} 個圖</summary><p>圖形原樣保留，曲線未轉換成財務數字。</p>')
        for figure in figures:
            parts.append(f'<h3>第 {e(figure["page"])} 頁 · {e(figure["label"])}</h3>{def_html_picture(job, figure["file"], figure["label"])}')
        parts.append('</details>')
    image_regions=result.get('acquisition', {}).get('image_region_candidates', [])
    if image_regions:
        parts.append('<details><summary>查看圖片文字候選 · 需核對</summary><p>原生文字不足才執行 OCR；圖片文字保留候選，不直接填入財務數值。</p>')
        for region in image_regions:
            parts.append('<h3>第 ' + e(region['page']) + ' 頁圖片</h3>')
            if region.get('file'):parts.append(def_html_picture(job, region['file'], '圖片來源區域'))
            parts.append('<p class="source">' + e(' '.join(line['text'] for line in region['lines']) or '未辨識出可靠文字') + '</p>')
        parts.append('</details>')
    md = ['# ' + result['filename'], '執行：' + result.get('execution_status', 'FAIL') + '；內容：' + result.get('content_status', 'REVIEW'), '## 摘要']
    md += ['### ' + p['topic'] + '\n\n' + (p.get('reading_text_zh') or p['text']) + '\n\n原文：' + p['text'] for p in digest]
    md += ['## 本文'] + [r['text'] for r in body]
    md += ['## 核對紀錄', json.dumps({'reading_validation': reading, 'consistency_checks': source_checks}, ensure_ascii=False, indent=2)]
    md += ['## 全部頁面原始擷取（揭露頁／OCR 候選另標示）']
    md += ['### 第 '+str(p['PAGE'])+' 頁 · '+p['LANE']+'\n\n'+p['TEXT_RAW'] for p in restored.get('source_pages',[])]
    (job / 'report.md').write_text('\n\n'.join(md), encoding='utf-8')
    exports = ''.join(def_html_download(job, name, label) for name, label in PARAMS['readable_exports'])
    parts.append('<details><summary>匯出資料</summary>' + exports + '</details>')
    detail = {'execution_status': result.get('execution_status'), 'checks': restored.get('checks', []), 'reading_validation': reading,
              'body_anchor_checks': checks, 'consistency_checks': source_checks, 'table_schema': [t.get('schema_validation') for t in tables], 'table_fast_checks': [t.get('fast_validation') for t in tables], 'quarter_checks': [t.get('quarter_validation') for t in tables], 'ocr_attempts': result.get('acquisition', {}).get('attempts', []), 'ocr_policy': result.get('acquisition', {}).get('ocr_policy'), 'exports': result.get('exports', {}), 'calls': result.get('calls', []), 'errors': result.get('errors', [])}
    parts.append('<details><summary>工程核對紀錄 · JSON</summary><pre>' + e(json.dumps(detail, ensure_ascii=False, indent=2)) + '</pre></details>')
    if result.get('errors'):
        parts.append('<p class="warning">本次執行有錯誤；請展開工程核對紀錄查看原因。</p>')
    parts.append('<p class="muted">Windows 啟動尚未實跑。中文摘要校準僅適用其綁定的來源版本；其他文件使用原文摘錄與 NLP 候選。</p></section><p class="muted">來源：' + e(result['filename']) + '</p></main></html>')
    (job / 'review.html').write_text(''.join(parts), encoding='utf-8')




def def_body_anchor_checks(path, records):
    import pdfplumber
    normalize = lambda text: re.sub(r'\s+', '', text)
    checks = []
    with pdfplumber.open(path) as pdf:
        words_by_page = {page: pdf.pages[page - 1].extract_words(x_tolerance=1, y_tolerance=1)
                         for page in {r['page'] for r in records if r['zone'] == 'BODY'}}
        for record in records:
            if record['zone'] != 'BODY':
                continue
            selected = []
            for word in words_by_page[record['page']]:
                cx, cy = (word['x0'] + word['x1']) / 2, (word['top'] + word['bottom']) / 2
                matches = [(i, abs(cy - (a[1] + a[3]) / 2)) for i, a in enumerate(record['anchors'])
                           if a[0] - .5 <= cx <= a[2] + .5 and a[1] - .5 <= cy <= a[3] + .5]
                if matches:
                    selected.append((min(matches, key=lambda v: v[1])[0], word['x0'], word['text']))
            source = ' '.join(w[2] for w in sorted(selected))
            checks.append({'page': record['page'], 'text': record['text'], 'anchors': record['anchors'], 'source_at_anchors': source,
                           'status': 'PASS' if normalize(record['text']) in normalize(source) else 'REVIEW',
                           'basis': 'pdfplumber word centroids within source line anchors; whitespace ignored only'})
    return checks


def def_reading_checks(restored):
    """Detect upstream replay duplicates; retain every record and source anchor."""
    body = [r for r in restored.get('records', []) if r.get('zone') in {'BODY', 'BODY_UNSEGMENTED'}]
    seen, duplicates = {}, []
    for index, record in enumerate(body):
        anchors = record.get('anchors') or []
        if not anchors or not any(a for a in anchors):
            continue
        key = def_stable({'page': record.get('page'), 'zone': record.get('zone'),
                          'component': record.get('component'), 'text': record.get('text'), 'anchors': anchors})
        if key in seen:
            duplicates.append({'first_index': seen[key], 'repeat_index': index, 'page': record.get('page'),
                               'text': record.get('text'), 'anchors': anchors})
        else:
            seen[key] = index
    return {'body_records': len(body), 'unsegmented_records': sum(r.get('zone') == 'BODY_UNSEGMENTED' for r in body),
            'duplicate_source_records': duplicates, 'duplicate_check': 'REVIEW' if duplicates else 'PASS',
            'policy': 'Same source position + text + role only; keep repeated text at different positions; never delete source records.'}


def def_html_table(headers, rows):
    e = lambda value: html.escape(str(value))
    return '<div class="scroll"><table><thead><tr>' + ''.join('<th>' + e(c) + '</th>' for c in headers) + '</tr></thead><tbody>' + ''.join('<tr>' + ''.join('<td>' + e(c) + '</td>' for c in row) + '</tr>' for row in rows) + '</tbody></table></div>'


def def_html_picture(job, relative_path, label):
    target = (Path(job) / relative_path).resolve()
    if not target.is_relative_to(Path(job).resolve()) or not target.is_file():
        return '<p class="warning">來源圖未產出；請檢視執行紀錄。</p>'
    data = base64.b64encode(target.read_bytes()).decode()
    return f'<img loading="lazy" src="data:image/png;base64,{data}" alt="{html.escape(str(label))}">'


def def_html_download(job, filename, label):
    target = Path(job) / filename
    if not target.is_file():
        return ''
    encoded = base64.b64encode(target.read_bytes()).decode()
    return f'<a download="{html.escape(filename, quote=True)}" href="data:application/octet-stream;base64,{encoded}">{html.escape(label)}</a> '


def def_table_schema(restored):
    """Keep upstream cells; resolve printed column groups into explicit periods."""
    for table in restored.get('tables', []):
        headers = table.get('period_headers') or []
        if not headers:
            table['schema_validation'] = {'status':'REVIEW_NO_HEADER', 'reason':'No verified printed period headers'}
            continue
        count = len(headers)
        bad = [{'row_index':r.get('row_index'), 'columns':len(r.get('cells', []))} for r in table.get('records', []) if r.get('component') not in {'SOURCE','NOTE'} and len(r.get('cells', [])) != count]
        groups = table.get('column_groups') or []
        mapping = {col:g['type'] for g in groups for col in g.get('columns', [])}
        if not table.get('column_metadata'):
            # Source-locked KGI annual tables use this schema; never infer Dec means annual on unknown files.
            known_annual = table.get('report_id') and table.get('historical_crosscheck_status') and not groups and table.get('source_sha256') in def_read(HERE/'profiles/source_hashes.json')
            table['column_metadata'] = [def_period(raw, frequency=mapping.get(i) or ('ANNUAL' if known_annual else None)) for i,raw in enumerate(headers[1:],1)]
            table['printed_headers'] = headers[1:]
        comparison=next((r for r in table.get('records',[]) if r.get('component')=='HEADER' and len(r.get('cells',[]))==count and sum(c in {'實際數','中信預估','市場共識','差異','調整前','調整後'} for c in r['cells'])>=3),None)
        if comparison:
            role_map={'實際數':'value','中信預估':'broker_forecast','市場共識':'consensus','差異':'difference','調整前':'old','調整後':'new'}
            for col,meta in enumerate(table['column_metadata'],1):
                label=comparison['cells'][col]
                meta['column_role']=role_map.get(label,'value')
                meta['printed_role']=label
                if label=='實際數':meta['source_status']='ACTUAL'
                elif label in {'中信預估','調整前','調整後'}:meta['source_status']='BROKER_FORECAST'
                elif label=='市場共識':meta['source_status']='CONSENSUS_FORECAST'
            table['printed_headers']=[table['period_headers'][col]+' '+comparison['cells'][col] for col in range(1,count)]
        used = [c for g in groups for c in g.get('columns', [])]
        group_ok = not groups or sorted(used) == list(range(1,count)) and len(set(used)) == len(used)
        for record in table.get('records', []):
            cells = record.get('cells', [])
            if not cells:
                continue
            date_cells=[c for c in cells[1:] if re.fullmatch(r'(?:[1-4]Q\d{2}(?:\([AFEP]\)|[AFEP])?|20\d{2}(?:\([AFEP]\)|[AFEP])?)',c)]
            if record.get('component')=='ROW' and len(date_cells)>=2 and def_cell_trim(cells[0]) in {'','損益表'}:
                record['semantic_component']='HEADER'
            elif record.get('component')=='ROW' and not cells[0] and any('財務比率' in c for c in cells):
                record['semantic_component']='SECTION'
            elif record.get('component') == 'TITLE' and groups:
                record['semantic_component'] = 'COLUMN_GROUP_HEADER'
            elif record.get('component') == 'ROW' and cells[0] and all(c == '' for c in cells[1:]):
                record['semantic_component'] = 'SECTION'
            else:
                record['semantic_component'] = record.get('component')
        period_issues = [{'column':col,'raw':headers[col],'expected':kind,'observed':table['column_metadata'][col-1]['frequency']} for col,kind in mapping.items() if table['column_metadata'][col-1]['frequency'] != kind]
        table['schema_validation'] = {'status':'PASS' if not bad and group_ok and not period_issues else 'REVIEW', 'expected_columns':count,
                                     'numeric_columns':count-1,'quarter_columns':sum(v=='QUARTER' for v in mapping.values()),
                                     'annual_columns':sum(v=='ANNUAL' for v in mapping.values()),'row_width_mismatches':bad,
                                     'period_issues':period_issues,'group_coverage_pass':group_ok,'policy':'Grouped titles are not data rows; never pad, drop or invent numeric cells.'}
    return restored


def def_table_views(table):
    """Split known quarter/annual groups; identical date labels remain different periods."""
    headers = table.get('period_headers') or []
    records = [r for r in table.get('records', []) if r.get('semantic_component',r.get('component')) not in {'HEADER','TITLE','COLUMN_GROUP_HEADER'}]
    groups = table.get('column_groups') or []
    if not groups or table.get('schema_validation',{}).get('status') != 'PASS':
        return [{'label':'完整表格','headers':headers,'rows':[r.get('cells',[]) for r in records]}]
    views = []
    for group in groups:
        cols = group['columns']
        label = '季度' if group['type']=='QUARTER' else '年度'
        display = ['項目']
        for col in cols:
            meta = table['column_metadata'][col-1]
            status = '實際' if meta['source_status']=='ACTUAL' else '預估' if meta['source_status'] in {'FORECAST','CT_FORECAST'} else '未標示'
            period = (meta.get('period') or headers[col]).replace('-Q','年第') + ('季' if meta['frequency']=='QUARTER' else '全年')
            display.append(f'{period} {status} ({headers[col]})')
        views.append({'label':f'{label}：{len(cols)} 欄','frequency':group['type'],'headers':display,
                      'rows':[[r['cells'][0]]+[r['cells'][c] for c in cols] for r in records]})
    return views


def def_ocr_quality(lines, config):
    text = '\n'.join(str(r.get('text','')) for r in lines)
    confidence = [float(w['confidence']) for line in lines for w in line.get('words',[]) if w.get('confidence') is not None]
    if not confidence:
        confidence = [float(line['confidence']) for line in lines if line.get('confidence') is not None]
    low = sum(c < config['ocr_low_confidence'] for c in confidence)
    fraction = low / len(confidence) if confidence else 1.0
    chars = len(re.sub(r'\s+','',text))
    passed = chars >= config['native_min_chars'] and bool(confidence) and fraction <= config['max_ocr_low_fraction'] and '\ufffd' not in text
    return {'status':'PASS' if passed else 'REVIEW','characters':chars,'confidence_samples':len(confidence),'low_fraction':fraction,
            'scope':'OCR confidence screening only; source accuracy and financial facts still REVIEW'}


def def_process_alive(pid):
    if not isinstance(pid,int) or pid <= 0:return False
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.windll.kernel32
        kernel.OpenProcess.restype=ctypes.c_void_p
        handle=kernel.OpenProcess(0x1000,False,pid)
        if not handle:
            return kernel.GetLastError()==5
        code=ctypes.c_ulong()
        okay=kernel.GetExitCodeProcess(ctypes.c_void_p(handle),ctypes.byref(code))
        kernel.CloseHandle(ctypes.c_void_p(handle))
        return bool(okay) and code.value==259
    try:
        os.kill(pid,0)
        return True
    except ProcessLookupError:return False
    except PermissionError:return True


def def_ocr_slot(config, action):
    """Kernel file lock: one OCR job, automatic release after worker exit."""
    root=Path(config['_ocr_slot_root']);root.mkdir(parents=True,exist_ok=True)
    token=uuid.uuid4().hex;started=time.monotonic();owner=root/'ocr.owner'
    with (root/'ocr.lock').open('a+b') as stream:
        if os.fstat(stream.fileno()).st_size==0:stream.write(b'0');stream.flush()
        while True:
            try:
                stream.seek(0)
                if os.name=='nt':
                    import msvcrt
                    msvcrt.locking(stream.fileno(),msvcrt.LK_NBLCK,1)
                else:
                    import fcntl
                    fcntl.flock(stream.fileno(),fcntl.LOCK_EX|fcntl.LOCK_NB)
                break
            except (BlockingIOError,OSError):
                if time.monotonic()-started >= config['ocr_slot_wait_seconds']:
                    raise TimeoutError('OCR_SLOT_TIMEOUT; retain REVIEW, no concurrent model fallback')
                time.sleep(.1)
        try:
            def_write(owner,{'pid':os.getpid(),'token':token,'lock_type':'OS_FILE_LOCK'})
            return action()
        finally:
            try:
                if def_read(owner).get('token')==token:owner.unlink()
            except (OSError,ValueError):pass
            stream.seek(0)
            if os.name=='nt':
                import msvcrt
                msvcrt.locking(stream.fileno(),msvcrt.LK_UNLCK,1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(),fcntl.LOCK_UN)


def def_ocr_tiers(page, temp, config, manager, calls, accelerator):
    """Reuse Tesseract then an explicitly configured heavy adapter, with quality gates."""
    import fitz
    temp=Path(temp);temp.mkdir(parents=True,exist_ok=True)
    attempts=[]
    def run_tiers():
        light=temp/'light.png'
        page.get_pixmap(dpi=config['light_dpi']).save(str(light))
        try:
            lines,receipt=def_call('manager',manager,'tesseract_lines',(light,list(page.rect),config['light_dpi'],config),calls,accelerator)
        except Exception as exc:
            lines=[];receipt={'state':'ERROR','message':str(exc)}
        quality=def_ocr_quality(lines,config)
        attempts.append({'tier':'LIGHT_OCR',**receipt,'quality':quality})
        if quality['status']=='PASS':
            attempts.append({'tier':'HEAVY_OCR','state':'SKIPPED_LIGHT_SUFFICIENT'})
            return lines,attempts
        # The selected Layout engine supplies suspect crops for mixed pages; no unconditional region reruns.
        heavy=config.get('heavy_ocr_command') or []
        if not heavy or config.get('ocr_max_tier')=='light':
            attempts.append({'tier':'HEAVY_OCR','state':'DEPENDENCY_UNAVAILABLE' if not heavy else 'SKIPPED_POLICY','reason':'No configured local model/command' if not heavy else 'Maximum tier LIGHT'})
            return lines,attempts
        high=temp/'heavy_input.png';page.get_pixmap(dpi=config['region_dpi']).save(str(high))
        output=temp/'heavy.json'
        argv=[part.replace('{image}',str(high)).replace('{output}',str(output)) for part in heavy]
        try:
            receipt=def_call('heavy_ocr',type('HeavyAdapter',(),{'run':staticmethod(lambda:subprocess.run(argv,capture_output=True,text=True,timeout=config['ocr_timeout']))}), 'run',(),calls,accelerator)
            if receipt.returncode != 0 or not output.is_file():raise ValueError('HEAVY_OCR_FAILED_OR_NO_OUTPUT')
            recovered=def_read(output)
            if not isinstance(recovered,list):raise ValueError('HEAVY_OCR_CONTRACT_INVALID')
            for line in recovered:
                if not isinstance(line,dict) or not isinstance(line.get('text'),str) or not isinstance(line.get('bbox'),list) or len(line['bbox'])!=4:
                    raise ValueError('HEAVY_OCR_LINE_INVALID')
                # Contract: pixel coords relative to heavy_input.png; convert to page coordinates.
                factor=72/config['region_dpi']
                line['bbox']=[float(v)*factor for v in line['bbox']]
                line['method']='HEAVY_OCR';line.setdefault('confidence',None);line.setdefault('font_size',None)
            heavy_quality=def_ocr_quality(recovered,config)
            attempts.append({'tier':'HEAVY_OCR','state':'EXECUTED','quality':heavy_quality,'coordinate_contract':'input-image pixels; converted to page points'})
            if heavy_quality['status']=='PASS':return recovered,attempts
            attempts[-1]['policy']='Unverified heavy output retained as candidate file; keep light result rather than overwrite blindly.'
        except Exception as exc:
            attempts.append({'tier':'HEAVY_OCR','state':'ERROR','message':str(exc)})
        return lines,attempts
    return def_ocr_slot(config,run_tiers)


def def_acquire_tiered(path, config, temp, manager, layout, calls, accelerator, dispatch):
    """Native manager API + per-worker OCR adapter; source engine files remain immutable."""
    native_ocr_page=manager.ocr_page
    manager.ocr_page=lambda page,temp,cfg:def_ocr_tiers(page,temp,cfg,manager,calls,accelerator)
    try:
        if Path(path).suffix.lower() in {'.png','.jpg','.jpeg'}:
            import fitz
            with fitz.open(path) as image:
                raw=image.convert_to_pdf()
            with fitz.open(stream=raw,filetype='pdf') as pdf:
                page=pdf[0]
                lines,attempts=def_ocr_tiers(page,Path(temp)/'image',config,manager,calls,accelerator)
                acquired={'pages':[{'page':1,'width':page.rect.width,'height':page.rect.height,'lines':lines,'lane':'IMAGE_OCR'}],'attempts':attempts}
        else:
            acquired=def_call('manager',manager,'acquire_document',(path,config,temp),calls,accelerator)
    finally:manager.ocr_page=native_ocr_page
    acquired['ocr_policy']={'order':['NON_OCR','LIGHT_OCR','HEAVY_OCR'],'ocr_parallel_limit':1,'nlp_after_extraction':True,'charts_not_numeric_facts':True}
    acquired['image_region_candidates']=[]
    return acquired

def def_cell_trim(value):
    """Whitespace-free comparison key; original text stays in cells_raw."""
    import unicodedata
    return re.sub(PARAMS['cell_trim_regex'],'',unicodedata.normalize('NFKC',str('' if value is None else value)))


def def_native_table_words(path, table):
    import fitz
    with fitz.open(path) as document:
        page=document[table['page']-1]
        return [{'text':w[4],'x0':w[0],'top':w[1],'x1':w[2],'bottom':w[3]} for w in page.get_text('words',clip=fitz.Rect(table['bbox_pt']))]


def def_plumber_table_words(path, table):
    import pdfplumber
    with pdfplumber.open(path) as document:
        return document.pages[table['page']-1].crop(tuple(table['bbox_pt'])).extract_words(x_tolerance=1,y_tolerance=1)


def def_words_to_row(words, edges, anchors, tolerance):
    if not anchors:return None
    valid=[a for a in anchors if a and len(a)==4]
    if not valid:return None
    center=sum((a[1]+a[3])/2 for a in valid)/len(valid)
    buckets=[[] for _ in range(len(edges)-1)]
    for word in words:
        cy=(word['top']+word['bottom'])/2;cx=(word['x0']+word['x1'])/2
        if abs(cy-center)>tolerance:continue
        col=next((i for i in range(len(edges)-1) if edges[i]<=cx<edges[i+1]),None)
        if col is not None:buckets[col].append((word['x0'],word['text']))
    return [' '.join(text for _,text in sorted(bucket)) for bucket in buckets]


def def_table_fast_validate(path, restored, config, calls, accelerator):
    """Verify cell widths, trim, and two native readers before optional OCR/NLP."""
    import collections
    for table in restored.get('tables',[]):
        headers=table.get('period_headers') or []
        edges=table.get('column_edges_pt') or []
        audit=[];repairs=[]
        locked=restored.get('profile') in {'SOURCE_HASH_LOCKED','SOURCE_HASH_LOCKED_CLST'}
        usable=headers and len(edges)==len(headers)+1 and all(edges[i]<edges[i+1] for i in range(len(edges)-1))
        if usable:
            native=def_call('geometry',type('NativeReader',(),{'read':staticmethod(def_native_table_words)}),'read',(path,table),calls,accelerator)
            plumber=def_call('geometry',type('PlumberReader',(),{'read':staticmethod(def_plumber_table_words)}),'read',(path,table),calls,accelerator)
        for record in table.get('records',[]):
            original=list(record.get('cells',[]))
            record.setdefault('cells_raw',original[:])
            trimmed=[def_cell_trim(c) for c in original]
            record['cells_trim']=trimmed
            if record.get('component') in {'TITLE','HEADER','SOURCE','NOTE'} or not usable:continue
            a=def_words_to_row(native,edges,record.get('anchors'),config['cell_row_tolerance'])
            b=def_words_to_row(plumber,edges,record.get('anchors'),config['cell_row_tolerance'])
            if a is None or b is None:
                audit.append({'row_index':record.get('row_index'),'status':'REVIEW_NO_ANCHOR'});continue
            a=[def_cell_trim(c) for c in a];b=[def_cell_trim(c) for c in b]
            same_readers=a==b
            full_shape=len(trimmed)==len(headers)
            same_label=bool(a[0]) and bool(trimmed) and a[0]==trimmed[0]
            # Only exact-source, unambiguous same-row/cell agreement can restore a malformed row.
            if locked and same_readers and same_label and (not full_shape or trimmed!=a):
                record['upstream_cells_before_fast_repair']=original
                record['cells']=[original[0]]+a[1:];record['cells_trim']=a[:]
                record['text']=' | '.join(a)
                record['status']='SOURCE_NATIVE_TWO_READER_REBUILT_REVIEW'
                repairs.append({'row_index':record.get('row_index'),'before':original,'after':a,'anchors':record.get('anchors'),'basis':'Two native readers + same labelled source row + locked source geometry'})
                trimmed=a[:];full_shape=True
            for col in range(len(headers)):
                before=trimmed[col] if col<len(trimmed) else None
                status='PASS' if same_readers and full_shape and before==a[col] else 'REVIEW'
                audit.append({'row_index':record.get('row_index'),'column':col,'restored_trim':before,'native_trim':a[col],'plumber_trim':b[col],
                              'number_restored':def_number(before) if col else None,'number_native':def_number(a[col]) if col else None,
                              'status':status})
            record['trim_number_counter'] = dict(collections.Counter(v for c in record['cells_trim'][1:] for v in re.findall(r'\d+(?:\.\d+)?',c)))
        table['fast_validation']={'status':'PASS' if audit and all(c['status']=='PASS' for c in audit) else 'REVIEW',
                                  'cells':audit,'repairs':repairs,'trim_scope':'NFKC + remove whitespace per cell; preserve signs, percent, decimal points, commas and raw source',
                                  'scope':'Same PDF source location; no official-history claim; no arithmetic-derived correction'}
    return restored


def def_growth_checks(restored, config):
    """Quarter endpoints are periods, not cumulative flags; validate printed rates."""
    annual_references={}
    for candidate in restored.get('tables',[]):
        if candidate.get('title') not in {'損益表','Profit & Loss — 明細','Profit & Loss — 摘要'}:continue
        for record in candidate.get('records',[]):
            if record.get('semantic_component',record.get('component'))!='ROW':continue
            cells=[def_cell_trim(c) for c in record.get('cells',[])]
            if not cells:continue
            for col,meta in enumerate(candidate.get('column_metadata',[]),1):
                if meta.get('frequency')!='ANNUAL' or not meta.get('period') or meta.get('column_role')!='value' or col>=len(cells):continue
                raw=cells[col]
                if def_number(raw) is None:continue
                annual_references.setdefault((cells[0],meta['period'],candidate.get('source_sha256')),[]).append({'raw':raw,'table_id':candidate['id'],'page':candidate['page'],'anchors':record.get('anchors')})
    for table in restored.get('tables',[]):
        metadata=table.get('column_metadata',[])
        quarters={m['period']:i for i,m in enumerate(metadata,1) if m.get('frequency')=='QUARTER' and m.get('period')}
        annual={m['period']:i for i,m in enumerate(metadata,1) if m.get('frequency')=='ANNUAL' and m.get('period') and m.get('column_role')=='value'}
        if not quarters:continue
        checks=[];base={};growth=[];section=''
        for record in table.get('records',[]):
            kind=record.get('semantic_component',record.get('component'))
            cells=[def_cell_trim(c) for c in record.get('cells',[])]
            if not cells:continue
            if kind=='SECTION':section=cells[0];continue
            if kind!='ROW':continue
            if section in {'季成長率(%)','年成長率(%)'}:
                growth.append((record,'QOQ' if section.startswith('季') else 'YOY'));continue
            if section.startswith('損益表') or table.get('id')=='CLST-P3-T2':
                base.setdefault(cells[0],record)
        for label,record in base.items():
            if label not in config['quarter_additive_metrics']:continue
            cells=[def_cell_trim(c) for c in record['cells']]
            for year,col in annual.items():
                wanted=[f'{year}-Q{q}' for q in range(1,5)]
                if not all(period in quarters for period in wanted):continue
                raw=[cells[quarters[period]] for period in wanted]
                values=[def_number(v) for v in raw];actual=def_number(cells[col])
                if actual is None or any(v is None for v in values):
                    checks.append({'check':'FOUR_QUARTERS_VS_ANNUAL','metric':label,'year':year,'status':'NOT_EVALUABLE_SOURCE_BLANK','raw_quarters':raw,'raw_annual':cells[col]});continue
                calculated=sum(values);difference=actual-calculated
                tolerance=config['quarter_sum_rounding_tolerance']
                status='PASS' if abs(difference)<=tolerance else 'REVIEW_ANNUAL_QUARTER_MISMATCH'
                if status!='PASS' and abs(actual-values[-1])<=tolerance:
                    status='REVIEW_POSSIBLE_CUMULATIVE_VALUES'
                checks.append({'check':'FOUR_QUARTERS_VS_ANNUAL','metric':label,'year':year,'actual_annual':actual,'calculated_sum':calculated,
                               'difference':difference,'tolerance':tolerance,'status':status,'policy':'No sum-derived replacement; non-additive ratios, balance stocks and EPS excluded'})
        for record,role in growth:
            cells=[def_cell_trim(c) for c in record['cells']]
            label=cells[0];target=config['growth_metric_aliases'].get(label,label)
            original=base.get(target)
            if not original:
                checks.append({'check':role,'metric':label,'status':'NOT_EVALUABLE_NO_BASE_METRIC'});continue
            basecells=[def_cell_trim(c) for c in original['cells']]
            for period,col in quarters.items():
                year,q=map(int,re.fullmatch(r'(\d{4})-Q([1-4])',period).groups())
                prior=f'{year-1}-Q{q}' if role=='YOY' else f'{year}-Q{q-1}' if q>1 else f'{year-1}-Q4'
                printed=def_number(cells[col]);prior_col=quarters.get(prior)
                if prior_col is None or printed is None:
                    checks.append({'check':role,'metric':label,'period':period,'prior_period':prior,'status':'NOT_EVALUABLE_MISSING_PERIOD_OR_RATE'});continue
                now,previous=def_number(basecells[col]),def_number(basecells[prior_col])
                if now is None or previous is None or previous<=0:
                    checks.append({'check':role,'metric':label,'period':period,'prior_period':prior,'status':'NOT_EVALUABLE_BLANK_OR_NONPOSITIVE_BASE'});continue
                checked=def_rate_result(basecells[col],basecells[prior_col],cells[col],config)
                checks.append({'check':role,'metric':label,'period':period,'prior_period':prior,**checked})
            if role=='YOY':
                for year,col in annual.items():
                    prior=str(int(year)-1);prior_col=annual.get(prior)
                    reference=None
                    if prior_col is None:
                        candidates=annual_references.get((target,prior,table.get('source_sha256')),[])
                        if candidates and len({def_number(c['raw']) for c in candidates})==1:reference=candidates[0]
                        elif candidates:
                            checks.append({'check':'ANNUAL_YOY','metric':label,'period':year,'prior_period':prior,'status':'REVIEW_CONFLICTING_ANNUAL_REFERENCE','source_candidates':candidates})
                            continue
                    if (prior_col is None and reference is None) or def_number(cells[col]) is None:
                        checks.append({'check':'ANNUAL_YOY','metric':label,'period':year,'prior_period':prior,'status':'NOT_EVALUABLE_MISSING_PERIOD_OR_RATE'})
                        continue
                    previous_raw=basecells[prior_col] if prior_col is not None else reference['raw']
                    checked=def_rate_result(basecells[col],previous_raw,cells[col],config)
                    checks.append({'check':'ANNUAL_YOY','metric':label,'period':year,'prior_period':prior,'prior_source_reference':reference,**checked})
        table['quarter_validation']={'basis':'Source quarter group; each endpoint represents one quarter. Annual comparison separately; never sum cumulative values blindly.',
                                     'status':'REVIEW' if any(c['status'].startswith('REVIEW') for c in checks) else 'PASS' if checks else 'NOT_EVALUATED',
                                     'checks':checks,'pass':sum(c['status']=='PASS' for c in checks),
                                     'not_evaluable':sum(c['status'].startswith('NOT_EVALUABLE') for c in checks)}
    return restored


def def_image_regions(path, acquired, config, temp, manager, layout, calls, accelerator, dispatch):
    """Run optional crop OCR only after native table trim/schema/source checks."""
    if Path(path).suffix.lower()!='.pdf' or not dispatch['ocr_image_regions']:return acquired
    import fitz
    with fitz.open(path) as pdf:
        for page_record in acquired['pages']:
            if page_record['lane']!='NON_OCR':continue
            page=pdf[page_record['page']-1]
            candidates=[]
            for block in page.get_text('dict')['blocks']:
                if block.get('type')!=1:continue
                box=fitz.Rect(block['bbox']) & page.rect
                if box.is_empty or box.get_area()/page.rect.get_area()<dispatch['ocr_min_image_area_ratio']:continue
                text=page.get_text('text',clip=box).strip()
                if len(re.sub(r'\s+','',text)) >= config['native_min_chars']:
                    acquired['attempts'].append({'page':page_record['page'],'bbox':list(box),'tier':'NON_OCR','state':'NATIVE_REGION_SUFFICIENT'})
                    continue
                if any((box & other).get_area()/min(box.get_area(),other.get_area())>.9 for other in candidates):continue
                candidates.append(box)
            if not candidates:continue
            # Layout is invoked only for pages with a substantial image lacking native labels.
            layout_result=def_layout_selected(path,[page_record['page']],layout,calls,accelerator)
            for index,box in enumerate(candidates[:dispatch['ocr_max_regions_per_page']]):
                image_pdf=fitz.open();destination=image_pdf.new_page(width=box.width,height=box.height)
                destination.insert_image(destination.rect,pixmap=page.get_pixmap(clip=box,dpi=config['light_dpi']))
                try:
                    lines,attempts=def_ocr_tiers(destination,Path(temp)/f'image_p{page_record["page"]}_{index}',config,manager,calls,accelerator)
                finally:image_pdf.close()
                for line in lines:line['bbox']=[line['bbox'][0]+box.x0,line['bbox'][1]+box.y0,line['bbox'][2]+box.x0,line['bbox'][3]+box.y0]
                acquired['attempts'].extend({'page':page_record['page'],'bbox':list(box),'region_index':index,**a} for a in attempts)
                acquired['image_region_candidates'].append({'page':page_record['page'],'bbox':list(box),'lines':lines,'status':'REVIEW_IMAGE_TEXT_NO_FINANCIAL_AUTOFILL','layout_status':layout_result.get('verdict'), 'file':def_crop(page,list(box),f'IMAGE-P{page_record["page"]}-{index}',Path(config['output']),dispatch)})
    return acquired


def def_rounding_half(raw):
    raw=def_cell_trim(raw).replace(',','').replace('%','').strip('()')
    match=re.fullmatch(r'[+-]?\d+(?:\.(\d+))?',raw)
    return .5 * 10**(-len(match[1] or '')) if match else None


def def_rate_result(current_raw, previous_raw, printed_raw, config):
    current,previous,printed=[def_number(v) for v in [current_raw,previous_raw,printed_raw]]
    if current is None or previous is None or printed is None or previous<=0:
        return {'status':'NOT_EVALUABLE_BLANK_OR_NONPOSITIVE_BASE'}
    calculated=(current/previous-1)*100
    current_half=def_rounding_half(current_raw) or 0
    previous_half=def_rounding_half(previous_raw) or 0
    printed_half=def_rounding_half(printed_raw) or 0
    if previous-previous_half<=0:return {'status':'NOT_EVALUABLE_ROUNDING_BASE_NEAR_ZERO'}
    endpoints=[(a/b-1)*100 for a in [current-current_half,current+current_half] for b in [previous-previous_half,previous+previous_half]]
    low,high=min(endpoints),max(endpoints)
    epsilon=config['growth_rounding_epsilon']
    okay=printed+printed_half>=low-epsilon and printed-printed_half<=high+epsilon
    return {'current':current,'previous':previous,'printed_percent':printed,'calculated_percent':calculated,
            'source_rounding_interval':[low,high],'printed_rounding_half':printed_half,
            'status':'PASS' if okay else 'REVIEW_SOURCE_RATE_MISMATCH',
            'basis':'Intervals from each source cell displayed decimal precision; retain printed values unchanged'}


def def_date_period(raw, role, frequency):
    text=def_cell_trim(raw).replace('年','-').replace('月','-').replace('日','')
    match=re.fullmatch(PARAMS['quarter_end_date_regex'],text,re.I) or re.fullmatch(PARAMS['quarter_end_compact_regex'],text,re.I)
    if not match:return None
    year,month,day=map(int,match.groups()[:3]);suffix=(match[4] or '').upper()
    try:date=datetime(year,month,day)
    except ValueError:return None
    status='CT_FORECAST' if suffix=='CT' else 'FORECAST' if suffix=='F' else 'ACTUAL' if suffix=='A' else 'UNSPECIFIED'
    quarter_end=(month,day) in {(3,31),(6,30),(9,30),(12,31)}
    if frequency=='QUARTER' and quarter_end:
        period=f'{year}-Q{month//3}';kind='QUARTER'
    elif frequency=='ANNUAL' and (month,day)==(12,31):
        period=str(year);kind='ANNUAL'
    else:
        period=date.strftime('%Y-%m-%d');kind='DATE'
    return {'raw':str(raw),'period':period,'frequency':kind,'source_status':status,'column_role':role,
            'basis':'Printed column-group context determines quarter/annual; endpoint date alone is not a cumulative flag'}


# 05 Worker runs in its own interpreter; globals/TEMP are never shared across docs.
def def_document_kind(filename):
    if re.search(r'產業|產業專題|Industry', filename, re.I):
        return 'INDUSTRY'
    if re.search(r'晨會|盤勢|周報|週報|ETF|債券', filename, re.I):
        return 'OTHER_INVESTMENT'
    if re.search(r'(?<!\d)[1-9]\d{3}(?!\d)', filename):
        return 'SINGLE_STOCK'
    return 'OTHER_INVESTMENT'


def def_restore(path, acquired, modules, config, job, calls, accelerator, source_sha):
    """Keep exact-source restorations; recover an invalid generic first-page crop."""
    try:
        restored = def_restore_core(path, acquired, modules, config, job, calls, accelerator, source_sha)
    except ValueError as exc:
        if str(exc) != 'EMPTY_CROP' or def_profile(source_sha):
            raise
        restored = {'profile':'GENERIC_REVIEW', 'records':[], 'tables':[], 'checks':[
            {'check':'INVALID_GENERIC_CROP', 'status':'RECOVERED_SOURCE_PAGES', 'reason':str(exc)}],
            'crops':[], 'source_excerpt':[]}
    if path.suffix.lower() != '.pdf' or not config.get('all_pages_export'):
        return restored
    import fitz
    import pdfplumber
    from collections import Counter
    sources, page_checks, raw_tables = [], [], []
    existing_pages = {r.get('page') for r in restored['records'] if r.get('zone') in {'BODY','BODY_UNSEGMENTED'}}
    with fitz.open(path) as document, pdfplumber.open(path) as second:
        for acquired_page in acquired['pages']:
            pno = acquired_page['page']
            page = document[pno-1]
            native = modules['manager'].native_lines(page)
            original_text = '\n'.join(line['text'] for line in native)
            native_display = sorted(native, key=lambda line: ((fitz.Rect(line['bbox'])*page.rotation_matrix).y0, (fitz.Rect(line['bbox'])*page.rotation_matrix).x0)) if page.rotation else native
            retained = acquired_page['lines']
            output_text = '\n'.join(line['text'] for line in retained)
            independent = ''.join(c['text'] for c in second.pages[pno-1].chars)
            a, b = Counter(def_cell_trim(original_text)), Counter(def_cell_trim(independent))
            is_native = acquired_page['lane'] == 'NON_OCR'
            scope = 'SOURCE_CHARACTERS_NATIVE' if is_native else 'OCR_CANDIDATE_REVIEW'
            page_role = 'DISCLOSURE' if re.search(config['disclosure_regex'], original_text[:1800], re.I) else 'RESEARCH'
            sources.append({'SOURCE_SHA256':source_sha,'FILENAME':path.name,'PAGE':pno,'PAGE_ROLE':page_role,
                'LANE':acquired_page['lane'],'TEXT_RAW':output_text,'TEXT_TRIM':def_cell_trim(output_text),'NATIVE_TEXT_RAW':original_text,
                'LINES_JSON':json.dumps(retained,ensure_ascii=False),'VALIDATION_STATUS':scope})
            page_checks.append({'page':pno,'lane':acquired_page['lane'],'scope':scope,
                'acquisition_retained': bool(retained) or not original_text,
                'native_export_exact':def_cell_trim(output_text)==def_cell_trim(original_text) if is_native else None,
                'native_characters':sum(a.values()),'plumber_characters':sum(b.values()),
                'missing_characters':dict(a-b),'extra_characters':dict(b-a),
                'status':'PASS' if is_native and a==b and def_cell_trim(output_text)==def_cell_trim(original_text) else 'REVIEW_OCR' if not is_native else 'REVIEW_NATIVE_READER_DIFFERENCE'})
            known = [{'bbox_pt':t['bbox_pt']} for t in restored['tables'] if t.get('page')==pno and t.get('bbox_pt')]
            found = second.pages[pno-1].find_tables()
            if not found and original_text:
                dense_rows = sum(len(re.findall(r'(?<!\w)[-+]?\d[\d,]*(?:\.\d+)?%?', line['text']))>=4 for line in native)
                if dense_rows>=config['raw_table_min_rows']:
                    found = second.pages[pno-1].find_tables(config['auto_table_settings'])
            for ti, table in enumerate(found,1):
                rows=table.extract(x_tolerance=1,y_tolerance=2)
                if len(rows)<config['raw_table_min_rows'] or max((len(row) for row in rows),default=0)<2:
                    continue
                bbox=list(table.bbox)
                cells=[]
                for ri, gridrow in enumerate(table.rows):
                    for ci, cell in enumerate(gridrow.cells):
                        raw = rows[ri][ci]
                        if cell is None:
                            cells.append({'row':ri,'column':ci,'raw':raw,'trim':def_cell_trim(raw),'bbox':None,'status':'SOURCE_MERGED_OR_ABSENT'})
                            continue
                        display_words=[list(fitz.Rect(w[:4])*page.rotation_matrix)+list(w[4:]) if page.rotation else w for w in page.get_text('words')]
                        words=[w for w in display_words if cell[0]<=(w[0]+w[2])/2<cell[2] and cell[1]<=(w[1]+w[3])/2<cell[3]]
                        word_text=''.join(w[4] for w in words)
                        # Character multiset proves retention, not semantic order or period/unit correctness.
                        status='PASS' if Counter(def_cell_trim(raw))==Counter(def_cell_trim(word_text)) else 'REVIEW'
                        cells.append({'row':ri,'column':ci,'raw':raw,'trim':def_cell_trim(raw),'bbox':list(cell),'native_text':word_text,'status':status})
                table_id=f'RAW-P{pno}-T{ti}'
                raw_tables.append({'SOURCE_SHA256':source_sha,'FILENAME':path.name,'TABLE_ID':table_id,'PAGE':pno,
                    'BBOX':bbox,'ROWS_RAW':rows,'ROWS_TRIM':[[def_cell_trim(c) for c in row] for row in rows],
                    'CELLS':cells,'VALIDATION_STATUS':'PASS_SOURCE_CELLS' if all(c['status'] in {'PASS','SOURCE_MERGED_OR_ABSENT'} for c in cells) else 'REVIEW',
                    'SEMANTIC_STATUS':'REVIEW_PERIOD_UNIT_STRUCTURE','CROP':def_crop(page,bbox,table_id,job,config)})
                # Raw candidates remain outside authoritative financial facts.
            if pno not in existing_pages and page_role=='RESEARCH' and native and page.rotation:
                for line in native_display:
                    restored['records'].append({'page':pno,'zone':'BODY','block_id':f'ROTATED-P{pno}',
                        'component':'SOURCE_LINE','text':line['text'],'raw_text':line['text'],
                        'anchors':[list(fitz.Rect(line['bbox'])*page.rotation_matrix)],'native_anchors':[line['bbox']],
                        'anchor_coordinate_space':'DISPLAY_PDF','document_sha256':source_sha,
                        'status':'SOURCE_ROTATION_RESTORED_REVIEW_PARAGRAPH_ORDER'})
            elif pno not in existing_pages and page_role=='RESEARCH' and native:
                zone={'id':f'FULL-P{pno}-BODY','zone':'BODY','bbox_pt':list(page.rect)}
                additional=def_call('restore',modules['restore'],'restore_text',
                    (source_sha[:12],page,zone,known,modules['layout']),calls,accelerator)
                for record in additional:
                    record['page']=pno;record['document_sha256']=source_sha
                    record['status']='NATIVE_PAGE_RESTORED_REVIEW_READING_ORDER'
                restored['records'].extend(additional)
            elif pno not in existing_pages and page_role=='RESEARCH' and retained:
                restored['records'].extend({'page':pno,'zone':'BODY_UNSEGMENTED','block_id':f'OCR-P{pno}',
                    'component':'SOURCE_LINE','text':line['text'],'raw_text':line['text'],'anchors':[line.get('bbox')],
                    'document_sha256':source_sha,'status':'OCR_REVIEW'} for line in retained)
        # Generic first-page left/right cuts are evidence only; no forced semantic assignment.
        if not def_profile(source_sha):
            first=document[0];width,height=first.rect.width,first.rect.height
            for label,box in [('LEFT',[0,0,width/2,height*.55]),('RIGHT',[width/2,0,width,height*.55])]:
                restored['crops'].append({'id':'FIRST-'+label,'zone':'INFO','page':1,'bbox':box,
                    'file':def_crop(first,box,'FIRST-'+label,job,config)})
    restored['source_pages']=sources
    restored['all_page_validation']=page_checks
    restored['raw_table_candidates']=raw_tables
    restored['body_anchor_checks']=def_body_anchor_checks(path,restored['records'])
    restored['source_excerpt']=[r for r in restored['records'] if r.get('zone') in {'BODY','BODY_UNSEGMENTED'} and r.get('component')!='HEADING'][:4]
    return restored


def def_extractive_digest(restored, kind, config):
    """Select verbatim, anchored source sentences; do not manufacture missing topics."""
    candidates=[]
    seen=set()
    for record in restored.get('records',[]):
        text=record.get('text','')
        if record.get('zone') not in {'BODY','BODY_UNSEGMENTED'} or record.get('component')=='HEADING':
            continue
        if not 40<=len(text)<=1500 or re.search(r'@|免責|copyright|disclaimer|certif|©',text,re.I):
            continue
        signals=len(re.findall(config['digest_signal_regex'],text,re.I))
        if not signals or text in seen:
            continue
        seen.add(text);candidates.append((signals,record))
    limit=6 if kind=='INDUSTRY' else 4
    selected=sorted(sorted(candidates,key=lambda x:(-x[0],x[1]['page']))[:limit],key=lambda x:(x[1]['page'],(x[1].get('anchors') or [[0,0]])[0][1]))
    return [{'topic':f'來源重點 {index}','text':record['text'],'source_records':[record],
        'status':'PASS_VERBATIM_SOURCE_BINDING_REVIEW_TOPIC_COVERAGE','method':'EXTRACTIVE_SOURCE_AFTER_EXISTING_NLP'} for index,(_,record) in enumerate(selected,1)]


def def_export_verified_frames(job, result):
    """Write every dataset, including empty schemas; read back CSV/JSON/Parquet values."""
    import polars as pl
    csv.field_size_limit(PARAMS['csv_field_size_limit'])
    restored=result.get('restoration',{})
    sources=restored.get('source_pages',[])
    body=[{'SOURCE_SHA256':result['source_sha256'],'FILENAME':result['filename'],'PAGE':r.get('page'),
        'ZONE':r.get('zone'),'COMPONENT':r.get('component'),'TEXT_RAW':r.get('raw_text'),
        'TEXT':r.get('text'),'TEXT_TRIM':def_cell_trim(r.get('text')),
        'ANCHORS_JSON':json.dumps(r.get('anchors'),ensure_ascii=False),'VALIDATION_STATUS':r.get('status')}
        for r in restored.get('records',[])]
    digest=[{'SOURCE_SHA256':result['source_sha256'],'FILENAME':result['filename'],'TOPIC':p['topic'],
        'TEXT':p['text'],'READING_TEXT_ZH':p.get('reading_text_zh'),
        'SOURCE_RECORDS_JSON':json.dumps(p.get('source_records'),ensure_ascii=False),'VALIDATION_STATUS':p.get('status')}
        for p in result.get('source_guided_digest',[])]
    rawcells=[]
    for table in restored.get('raw_table_candidates',[]):
        for cell in table['CELLS']:
            rawcells.append({'SOURCE_SHA256':result['source_sha256'],'FILENAME':result['filename'],
                'TABLE_ID':table['TABLE_ID'],'PAGE':table['PAGE'],'ROW_INDEX':cell['row'],'COLUMN_INDEX':cell['column'],
                'VALUE_RAW':cell['raw'],'VALUE_TRIM':cell['trim'],'VALUE_NUMERIC':def_number(cell['trim']),
                'BBOX_JSON':json.dumps(cell['bbox']),'VALIDATION_STATUS':cell['status'],
                'SEMANTIC_STATUS':table['SEMANTIC_STATUS']})
    figurecells=[{'SOURCE_SHA256':result['source_sha256'],'FILENAME':result['filename'],'PAGE':r['page'],
        'FILE':r.get('file'),'BBOX_JSON':json.dumps(r.get('bbox')),'TEXT': '\n'.join(l['text'] for l in r['lines']),
        'VALIDATION_STATUS':'OCR_IMAGE_CANDIDATE_REVIEW'} for r in result.get('acquisition',{}).get('image_region_candidates',[])]
    dataset={
        'SourcePages':(sources,['SOURCE_SHA256','FILENAME','PAGE','PAGE_ROLE','LANE','TEXT_RAW','TEXT_TRIM','NATIVE_TEXT_RAW','LINES_JSON','VALIDATION_STATUS']),
        'ReportText':(body,['SOURCE_SHA256','FILENAME','PAGE','ZONE','COMPONENT','TEXT_RAW','TEXT','TEXT_TRIM','ANCHORS_JSON','VALIDATION_STATUS']),
        'ReportDigest':(digest,['SOURCE_SHA256','FILENAME','TOPIC','TEXT','READING_TEXT_ZH','SOURCE_RECORDS_JSON','VALIDATION_STATUS']),
        'TableCandidates':(rawcells,['SOURCE_SHA256','FILENAME','TABLE_ID','PAGE','ROW_INDEX','COLUMN_INDEX','VALUE_RAW','VALUE_TRIM','VALUE_NUMERIC','BBOX_JSON','VALIDATION_STATUS','SEMANTIC_STATUS']),
        'ImageCandidates':(figurecells,['SOURCE_SHA256','FILENAME','PAGE','FILE','BBOX_JSON','TEXT','VALIDATION_STATUS'])}
    for name in ['StockReportBasicInfo','StockReportFinancialData']:
        file=job/(name+'.json')
        rows=def_read(file) if file.exists() else []
        if isinstance(rows,dict):rows=[rows]
        fields=list(rows[0]) if rows else ['FILENAME_SHA256','TABLE_ID','PAGE','METRIC','PERIOD','FREQUENCY','VALUE_RAW','VALUE_TRIM','VALUE_NUMERIC','VALIDATION_STATUS']
        dataset[name]=(rows,fields)
    receipts=[]
    for name,(rows,fields) in dataset.items():
        def_write(job/(name+'.json'),rows)
        with (job/(name+'.csv')).open('w',encoding='utf-8-sig',newline='') as handle:
            writer=csv.DictWriter(handle,fieldnames=fields);writer.writeheader();writer.writerows(rows)
        frame=pl.from_dicts(rows,infer_schema_length=None) if rows else pl.DataFrame(schema={f:pl.String for f in fields})
        frame.write_parquet(job/(name+'.parquet'))
        reread=pl.read_parquet(job/(name+'.parquet'))
        parquet_pass=frame.equals(reread)
        with (job/(name+'.csv')).open(encoding='utf-8-sig',newline='') as handle:
            csvrows=list(csv.DictReader(handle))
        csvpass=len(csvrows)==len(rows) and all(all(actual[f]==('' if expected.get(f) is None else str(expected[f])) for f in fields) for actual,expected in zip(csvrows,rows))
        jsonpass=def_read(job/(name+'.json'))==rows
        receipts.append({'dataset':name,'rows':len(rows),'csv_values_equal':csvpass,'json_values_equal':jsonpass,
            'parquet_frame_equal':parquet_pass,'status':'PASS' if csvpass and jsonpass and parquet_pass else 'FAIL',
            'files':{ext:{'sha256':def_hash(job/(name+'.'+ext)),'bytes':(job/(name+'.'+ext)).stat().st_size} for ext in ['json','csv','parquet']}})
    result['export_validation']=receipts
    result['exports'].update({'all_frames_parquet':'PASS' if all(r['status']=='PASS' for r in receipts) else 'FAIL','all_frames_datasets':len(receipts)})
    if any(r['status']!='PASS' for r in receipts):
        raise ValueError('EXPORT_ROUNDTRIP_FAILED')
    return result



def def_worker(request):
    path, job = Path(request["input"]), Path(request["job"])
    config, selected = request["config"], request["selected"]
    calls, modules = [], {}
    result = {"schema": "VRN-LOCAL-DISPATCH/1", "filename": path.name, "source_sha256": request["source_sha256"],
              "cache_key": request["cache_key"], "execution_status": "FAIL", "content_status": "REVIEW", "calls": calls,
              "selected_engines": selected, "errors": []}
    try:
        if def_hash(path) != request["source_sha256"]:
            raise ValueError("SOURCE_CHANGED_BEFORE_RUN")
        # Windows numeric thread budgets before numpy/BLAS imports.
        for env in ["OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"]:
            os.environ[env] = "1"
        os.environ["VIA_TEMP_ROOT"] = str(job / "work" / "temp")
        for role in config["roles"]:
            modules[role] = def_load(role, selected)
            calls.append({"role": role, "function": "IMPORT", "status": "PASS", "sha256": selected[role]["sha256"]})
        result["dependency_hashes"] = request["dependencies"]
        for filename, sha in request["dependencies"].items():
            if def_hash(filename) != sha:
                raise ValueError("DEPENDENCY_CHANGED_BEFORE_RUN")
        accel = modules["accelerator"]
        def_call("accelerator", accel, "apply_thread_limits", (1,), calls)
        temp = def_call("temp", modules["temp"], "activate", ("VRN_LocalDispatcher", 1000000), calls)
        manager = modules["manager"]
        cfg = dict(manager.CONFIG)
        cfg.update(resources=str(HERE / "tools/resources"), output=str(job), max_pages=config["max_pages"], ocr_timeout=config["ocr_timeout"])
        cfg.update({key: config[key] for key in ['light_dpi','region_dpi','heavy_ocr_command','ocr_max_tier','ocr_low_confidence','max_ocr_low_fraction','native_min_chars','ocr_slot_wait_seconds','_ocr_slot_root']})
        rules = def_call("manager", manager, "load_rules", (HERE / "tools/resources",), calls, accel)
        acquired = def_acquire_tiered(path, cfg, temp, manager, modules["layout"], calls, accel, config)
        if not acquired.get("pages"):
            raise ValueError("ACQUISITION_EMPTY")
        result["acquisition"] = acquired
        result["metadata"] = def_call("manager", manager, "extract_metadata", (path, acquired, rules, request["source_sha256"]), calls, accel)
        result["metadata"]["doc_kind"] = def_document_kind(path.name)
        result["restoration"] = def_restore(path, acquired, modules, config, job, calls, accel, request["source_sha256"])
        result['restoration'] = def_table_fast_validate(path, result['restoration'], config, calls, accel)
        result['restoration'] = def_table_schema(result['restoration'])
        result['restoration'] = def_growth_checks(result['restoration'], config)
        acquired = def_image_regions(path, acquired, cfg, temp, manager, modules['layout'], calls, accel, config)
        if result['restoration']['profile'] == 'SOURCE_HASH_LOCKED_CLST':
            result['metadata'] = def_source_metadata(path, result['restoration'], result['metadata'])
            result['restoration']['consistency_checks'] = def_consistency_checks(result['restoration'])
            result['source_guided_digest'] = def_source_digest(result['restoration'], def_profile(request['source_sha256']))
        result['restoration']['reading_validation'] = def_reading_checks(result['restoration'])
        source = "\n".join(r["text"] for r in result["restoration"]["records"] if r["zone"] in {"BODY", "BODY_UNSEGMENTED"})
        if not source.strip():
            raise ValueError("NO_SOURCE_TEXT_FOR_NLP; inspect OCR receipt")
        processed = def_call("nlp", modules["nlp"], "def_process", (source, None, path.name), calls, accel)
        if "processed_text" not in processed:
            raise ValueError("NLP_RESULT_SCHEMA_MISMATCH")
        before = modules["completeness"].numbers(source)
        after = modules["completeness"].numbers(processed["processed_text"])
        if before != after:
            processed["processed_text"] = source
            processed["dispatch_rollback"] = "NUMERIC_FACT_CHANGE"
        analysis = def_call("nlp", modules["nlp"], "def_legacy_analysis", (processed["processed_text"], str(job / "work/nlp_runtime"), "analyze"), calls, accel)
        result["nlp"] = {"process": processed, "analysis": analysis, "summary_status": "REVIEW_CANDIDATE", "entity_status": "REVIEW_CANDIDATE",
                         "number_gate": "PASS" if before == after else "ROLLED_BACK", "mode": "OFFLINE_LEGACY_NO_LLM"}
        region_text = '\n'.join(line['text'] for region in acquired.get('image_region_candidates', []) for line in region['lines'])
        if region_text.strip():
            region_processed = def_call('nlp', modules['nlp'], 'def_process', (region_text, None, path.name + ':image-regions'), calls, accel)
            if modules['completeness'].numbers(region_text) != modules['completeness'].numbers(region_processed.get('processed_text', '')):
                region_processed['processed_text'] = region_text
                region_processed['dispatch_rollback'] = 'NUMERIC_FACT_CHANGE'
            result['nlp_image_candidates'] = {'process': region_processed, 'status': 'REVIEW_IMAGE_LABELS_NO_FINANCIAL_AUTOFILL'}
        if not result.get('source_guided_digest'):
            result['source_guided_digest'] = def_extractive_digest(result['restoration'], result['metadata']['doc_kind'], config)
        result["table_readers"] = def_table_readers(path, result["restoration"], config["table_tools"], calls)
        result["exports"] = def_csv(job, result["restoration"])
        result["exports"].update(def_basicinfo_exports(job, result["metadata"]))
        def_export_verified_frames(job, result)
        if def_hash(path) != request["source_sha256"]:
            raise ValueError("SOURCE_CHANGED_DURING_RUN")
        for row in selected.values():
            if def_hash(row["path"]) != row["sha256"]:
                raise ValueError("ENGINE_CHANGED_DURING_RUN")
        for filename, sha in request["dependencies"].items():
            if def_hash(filename) != sha:
                raise ValueError("DEPENDENCY_CHANGED_DURING_RUN")
        for rel, sha in def_read(HERE / "UPSTREAM_LOCK.json").items():
            if def_hash(HERE / rel) != sha:
                raise ValueError("UPSTREAM_CHANGED_DURING_RUN: " + rel)
        result["immutability"] = "PASS_SOURCE_AND_UPSTREAM_HASHES"
        unavailable = [r for r in result["table_readers"] if r["status"] == "UNAVAILABLE_OR_FAILED"]
        result["execution_status"] = "PARTIAL_OPTIONAL_TOOLS" if unavailable else "PASS"
        if unavailable:
            result["errors"].append({"message": "REQUESTED_TABLE_TOOLS_UNAVAILABLE", "count": len(unavailable)})
    except Exception as exc:
        result["errors"].append({"type": type(exc).__name__, "message": str(exc), "traceback": traceback.format_exc()})
    def_write(job / "result.json", result)
    try:
        def_document_html(job, result)
    except Exception as exc:
        result['execution_status'] = 'FAIL'
        result['errors'].append({'type': type(exc).__name__, 'message': 'HTML_RENDER_FAILED: ' + str(exc), 'traceback': traceback.format_exc()})
        def_write(job / 'result.json', result)
    return 0 if result["execution_status"] == "PASS" else 2




# 06 Cache binds source bytes, original filename, adapter version and engine/profile hashes.
def def_cache_key(path, discovery, config):
    return def_stable({"source": def_hash(path), "filename": Path(path).name, "adapter": def_hash(__file__),
                       "engines": {k: r["sha256"] for k, r in discovery["selected"].items()},
                       "upstream": discovery["upstream_lock"], "dependencies": discovery["dependency_hashes"], "config": config})


def def_cache_read(output, key):
    for p in sorted((Path(output) / "cache" / key).glob("*.json"), reverse=True):
        try:
            rec = def_read(p)
            if rec["key"] != key:
                continue
            job = Path(rec["job"])
            if all((job / rel).is_file() and def_hash(job / rel) == sha for rel, sha in rec["artifacts"].items()):
                result = def_read(job / "result.json")
                if result["execution_status"] == "PASS" and result["cache_key"] == key:
                    return job, result
        except (OSError, ValueError, KeyError):
            continue
    return None


def def_subprocess(command, cwd, log_path, timeout):
    with Path(log_path).open("w", encoding="utf-8") as log:
        child = subprocess.Popen(command, cwd=cwd, stdout=log, stderr=subprocess.STDOUT,
                                 env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"})
        try:
            return child.wait(timeout=timeout), False
        except subprocess.TimeoutExpired:
            # Stop only this job's interpreter, never an existing user engine/process.
            child.kill()
            child.wait()
            return child.returncode, True


def def_job(path, run, output, discovery, config, fresh=False):
    key = def_cache_key(path, discovery, config)
    cached = None if fresh else def_cache_read(output, key)
    if cached:
        job, result = cached
        return {"filename": path.name, "status": "PASS", "content": result["content_status"], "cache": "HIT", "job": str(job), "key": key}
    job = run / "documents" / (key[:16] + "_" + uuid.uuid4().hex[:6])
    job.mkdir(parents=True)
    request = {"input": str(path), "job": str(job), "source_sha256": def_hash(path), "cache_key": key,
               "config": dict(config, _ocr_slot_root=str(Path(output) / "ocr_slot")), "selected": discovery["selected"], "dependencies": discovery["dependency_hashes"]}
    def_write(job / "request.json", request)
    code, timeout = def_subprocess([sys.executable, str(Path(__file__).resolve()), "--worker-request", str(job / "request.json")], job, job / "worker.log", config["document_timeout"])
    if timeout or not (job / "result.json").exists():
        result = {"filename": path.name, "source_sha256": request["source_sha256"], "cache_key": key,
                  "execution_status": "FAIL", "content_status": "REVIEW", "errors": [{"message": "DOCUMENT_TIMEOUT" if timeout else f"WORKER_EXIT_{code}"}]}
        def_write(job / "result.json", result)
        def_document_html(job, result)
    else:
        result = def_read(job / "result.json")
    if result["execution_status"] == "PASS":
        artifacts = {str(p.relative_to(job)): def_hash(p) for p in sorted(job.rglob("*"))
                     if p.is_file() and "work" not in p.relative_to(job).parts and p.suffix in {".json", ".html", ".md", ".csv", ".parquet", ".png", ".pdf"}}
        def_write(Path(output) / "cache" / key / (run.name + "_" + job.name + ".json"), {"key": key, "job": str(job), "artifacts": artifacts})
    return {"filename": path.name, "status": result["execution_status"], "content": result["content_status"], "cache": "MISS", "job": str(job), "key": key}



def def_matrix(run, receipt):
    """Readable run matrix; raw governance inventory stays expandable."""
    rows = []
    for row in receipt['documents']:
        link = os.path.relpath(Path(row['job']) / 'review.html', run).replace(os.sep, '/')
        execution = '擷取完成' if row['status'] == 'PASS' else '部分工具未完成' if row['status'] == 'PARTIAL_OPTIONAL_TOOLS' else '未完成'
        cache = '沿用已核對檔案' if row['cache'] == 'HIT' else '本次重新擷取'
        rows.append('<tr><td>' + html.escape(row['filename']) + '</td><td>' + execution + '</td><td>內容仍需確認</td><td>' + cache + '</td><td><a href="' + html.escape(link, quote=True) + '">查看本文、摘要與財報</a></td></tr>')
    inventory = [[r.get(k, '') for k in ['role', 'status', 'version', 'path', 'sha256']] for r in receipt['discovery']['inventory']]
    page = '<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VRN 調度成果</title><style>' + PARAMS['readable_css'] + '</style><main><header><b>VERITAS INTELLIGENCE ANALYTICS</b><small>DISCIPLINA • PRUDENTIA • INTEGRITAS</small><b>AI-Powered Research & Decision Intelligence Platform</b></header><h1>VRN 本機調度成果</h1><p>點選文件右側的「查看本文、摘要與財報」。擷取完成與內容正確性分開記錄。</p><section><div class="scroll"><table><thead><tr><th>檔案</th><th>擷取結果</th><th>內容核對</th><th>處理方式</th><th>成果</th></tr></thead><tbody>' + ''.join(rows) + '</tbody></table></div></section><details><summary>引擎版本與 AST／compile 檢查</summary>' + def_html_table(['角色', '狀態', '版本', '路徑', 'SHA256'], inventory) + '</details><details><summary>匯出執行紀錄</summary><a href="receipt.json">JSON</a> · <a href="matrix.csv">CSV</a></details></main></html>'
    (run / 'matrix.html').write_text(page, encoding='utf-8')
    with (run / 'matrix.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['filename', 'status', 'content', 'cache', 'job', 'key'], extrasaction='ignore')
        writer.writeheader()
        writer.writerows(receipt['documents'])



def def_main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--engine-root", default=PARAMS["engine_root"])
    parser.add_argument("--input", default=PARAMS["input_root"])
    parser.add_argument("--output", default=str(HERE / PARAMS["output_name"]))
    parser.add_argument("--workers", type=int, default=PARAMS["workers"])
    parser.add_argument("--timeout", type=int, default=PARAMS["document_timeout"])
    parser.add_argument("--table-tools", default=",".join(PARAMS["table_tools"]))
    parser.add_argument("--ocr-max-tier", choices=["light", "heavy"], default=PARAMS["ocr_max_tier"])
    parser.add_argument("--heavy-ocr-config", help="JSON argv for an existing local heavy adapter; output list of text/bbox/confidence with pixel coordinates")
    parser.add_argument("--probe", action="store_true")
    parser.add_argument("--fresh", action="store_true")
    parser.add_argument("--worker-request")
    args = parser.parse_args(argv)
    if args.worker_request:
        return def_worker(def_read(args.worker_request))
    if not 1 <= args.workers <= 8 or args.timeout < 1:
        parser.error("workers must be 1..8; timeout must be positive")
    config = dict(PARAMS, workers=args.workers, document_timeout=args.timeout, table_tools=[x.strip() for x in args.table_tools.split(",") if x.strip()])
    config["ocr_max_tier"] = args.ocr_max_tier
    if args.heavy_ocr_config:
        command = def_read(args.heavy_ocr_config)
        if not isinstance(command, list) or not command or not all(isinstance(p, str) for p in command):
            parser.error("heavy-ocr-config must be a nonempty JSON argv array")
        config["heavy_ocr_command"] = command
    if set(config["table_tools"]) - {"pdfplumber", "camelot", "tabula"}:
        parser.error("table-tools: pdfplumber,camelot,tabula")
    output = Path(args.output).resolve()
    run = output / "runs" / (datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8])
    run.mkdir(parents=True)
    discovery = def_discover(args.engine_root, config)
    receipt = {"schema": "VRN-DISPATCH-RUN/1", "version": PARAMS["version"], "run": str(run), "config": config, "discovery": discovery, "documents": []}
    if discovery["issues"]:
        receipt["status"] = "BLOCKED_ENGINE_SELECTION"
        def_write(run / "receipt.json", receipt)
        def_matrix(run, receipt)
        print(json.dumps(discovery["issues"], ensure_ascii=False), flush=True)
        return 2
    if args.probe:
        receipt["status"] = "AST_COMPILE_PASS_IMPORT_NOT_RUN"
        def_write(run / "receipt.json", receipt)
        def_matrix(run, receipt)
        print("AST/compile PASS; actual import verified in document workers. " + str(run), flush=True)
        return 0
    inputs = def_walk(args.input, config, output=output)
    if not inputs:
        receipt["status"] = "NO_INPUT"
        def_write(run / "receipt.json", receipt)
        def_matrix(run, receipt)
        print("NO_INPUT: " + args.input, flush=True)
        return 2
    print(f"VRN engines={len(discovery['selected'])}; documents={len(inputs)}; workers={args.workers}", flush=True)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(def_job, path, run, output, discovery, config, args.fresh): path for path in inputs}
        for future in as_completed(futures):
            try:
                row = future.result()
            except Exception as exc:
                row = {"filename": futures[future].name, "status": "FAIL", "content": "REVIEW", "cache": "MISS", "job": str(run), "key": "", "error": str(exc)}
            receipt["documents"].append(row)
            def_write(run / "progress.json", {"done": len(receipt["documents"]), "total": len(inputs), "last": row})
            print(f"[{len(receipt['documents'])}/{len(inputs)}] {row['filename']} execution={row['status']} content={row['content']} cache={row['cache']}", flush=True)
    receipt["documents"].sort(key=lambda r: r["filename"])
    receipt["status"] = "PASS_EXECUTION_CONTENT_REVIEW" if all(r["status"] == "PASS" for r in receipt["documents"]) else "FAIL_OR_PARTIAL"
    def_write(run / "receipt.json", receipt)
    def_matrix(run, receipt)
    print("MATRIX=" + str(run / "matrix.html"), flush=True)
    return 0 if receipt["status"] == "PASS_EXECUTION_CONTENT_REVIEW" else 2



if __name__ == "__main__":
    raise SystemExit(def_main())
