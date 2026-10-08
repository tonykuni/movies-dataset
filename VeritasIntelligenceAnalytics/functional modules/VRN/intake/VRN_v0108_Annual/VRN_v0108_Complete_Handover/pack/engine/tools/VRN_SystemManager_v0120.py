"""VRN System Manager v0120: independent local runtime, immutable evidence and rules.

Upstream v0119 remains frozen. This runtime does not call Git, VDF or a hosted API.
Local rule/observation identities are not central VIA registration numbers.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import importlib.util
import inspect
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import unicodedata
import uuid
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
from pathlib import Path

# 1. All configurable defaults live here; CLI options override them.
VERSION = "v0120"
HERE = Path(__file__).resolve().parent
CONFIG = {
    "resources": str(HERE / "resources"),
    "output": str(HERE / "output"),
    "workers": 2,
    "native_min_chars": 40,
    "max_pages": 250,
    "light_dpi": 200,
    "region_dpi": 350,
    "ocr_timeout": 60,
    "ocr_psm": 6,
    "ocr_low_confidence": 60,
    "max_ocr_low_fraction": 0.15,
    "memory_limit": "512MB",
    "line_tolerance": 2.5,
    "heavy_ocr_command": [],  # Optional argv: {image}, {output}; no shell, no installation.
    "table_min_columns": 3,
    "include_extensions": [".pdf", ".docx", ".txt", ".md", ".png", ".jpg", ".jpeg"],
}
MONTHS = {name.lower(): i for i, name in enumerate(
    ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], 1)}
CHINESE_MONTHS = {s: i for i, s in enumerate(["一", "二", "三", "四", "五", "六", "七", "八", "九", "十", "十一", "十二"], 1)}
DOMAIN_BROKERS = {"jpmorgan.com": "JPM", "morganstanley.com": "MS", "kgi.com": "KGI", "ctbcsis.com": "CTBC", "entrust.com.tw": "HUANAN", "citi.com": "CITI", "gs.com": "GS", "ubs.com": "UBS", "macquarie.com": "MACQUARIE", "cl-sec.com": "CLSA", "daiwacm-cathay.com.tw": "DAIWA", "cathayfut.com.tw": "CATHAY"}
LOCAL_RULES = {
    "broker": {"MEGA": ["兆豐", "MEGA", "MKC"]},
    "rating": {"Buy": ["增加持股"]},
    "financial_metric": {
        "REVENUE": ["營業收入淨額", "營業收入", "Revenue", "Net sales"],
        "GROSS_PROFIT": ["營業毛利淨額", "營業毛利", "Gross profit"],
        "OPERATING_PROFIT": ["營業利益", "Operating profit", "Operating income"],
        "NET_PROFIT": ["稅後純益", "稅後淨利", "Net income", "Adjusted profit"],
        "EPS": ["每股盈餘", "調整後EPS", "Adj. EPS", "EPS rep", "EPS adj"],
        "GROSS_MARGIN": ["毛利率", "Gross margin"],
        "OPERATING_MARGIN": ["營益率", "Operating margin"],
        "NET_MARGIN": ["稅後淨利率", "Net margin"],
        "ASSETS": ["資產總計", "Total assets"],
        "LIABILITIES": ["負債總計", "Total liabilities"],
        "EQUITY": ["股東權益總計", "Total equity"]
    },
    "target_label": {"CURRENT": ["12-month target", "12 個月目標價", "Price Target", "Target Price", "目標價"]},
    "regex": {"email_ascii": r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"},
}
GENERIC_MAILBOXES = {"research", "service", "info", "sales", "media_request", "contact", "support"}
NAME_STOP = {"Taiwan", "Limited", "Securities", "Technologies", "Neutral", "Research", "Disclaimer", "Analyst", "收盤價", "目標價", "個股報告", "投資風險", "研究員", "維持評等", "未評等"}
RUNTIME = {}


# 2. Identity, runtime limits and immutable writes.
def stable_hash(value):
    data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(data).hexdigest()


def file_hash(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path, value):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.name + "." + uuid.uuid4().hex + ".tmp")
    tmp.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    os.replace(tmp, p)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(str(path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def initialize_runtime(config):
    resources = Path(config["resources"])
    state = {"python": sys.version, "standalone": True, "network": "DISABLED", "accelerator": "UNAVAILABLE", "temp": "UNAVAILABLE"}
    for name in ["fitz", "docx", "polars", "duckdb", "pdfplumber"]:
        try:
            module = __import__(name)
            state[name] = getattr(module, "__version__", getattr(module, "VersionBind", "AVAILABLE"))
        except ImportError as exc:
            state[name] = "UNAVAILABLE: " + str(exc)
    manifest = resources / "UPSTREAM_SHA256.json"
    expected = json.loads(manifest.read_text()) if manifest.exists() else {}
    for name, key in [("VeritasCeleritas_v1141.py", "accelerator"), ("SUP_MDL867_TempSpill_v0100.py", "temp")]:
        p = resources / name
        if not p.exists():
            continue
        if expected.get(name) != file_hash(p):
            raise ValueError("LOCK_HASH_MISMATCH: " + name)
        try:
            module = load_module(p, "vrn_" + key)
            if key == "accelerator":
                module.apply_thread_limits(config["workers"])
                state[key] = name + ": apply_thread_limits EXECUTED"
                RUNTIME["accelerator"] = module
            else:
                # Keep prior TEMP runs: append-only retention for this task.
                run_dir = module.activate("VRN_v0120", keep=1000000)
                RUNTIME["temp_dir"] = str(run_dir)
                state[key] = name + ": activate EXECUTED"
        except Exception as exc:
            state[key] = "ERROR: " + type(exc).__name__ + ": " + str(exc)
    RUNTIME["state"] = state
    return state


def accelerated_call(function, *args):
    module = RUNTIME.get("accelerator")
    if module is None:
        return function(*args)
    result = module.xrun(lambda: function(*args))
    if isinstance(result, dict) and result.get("runner") == "xrun" and result.get("status") == "error":
        raise RuntimeError("ACCELERATOR_TASK_FAILED: " + result.get("msg", "unknown"))
    return result


# 3. SSOT accumulation with explicit conflict quarantine.
def norm_alias(value):
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def add_alias(index, namespace, canonical, alias, source, conflicts):
    key = namespace + ":" + norm_alias(alias)
    prior = index.get(key)
    if prior and prior["canonical"] != canonical:
        conflicts.append({"kind": "ALIAS_COLLISION", "key": key, "existing": prior, "candidate": {"canonical": canonical, "alias": alias, "source": source}})
        return False
    if prior:
        if source not in prior["sources"]:
            prior["sources"].append(source)
        return True
    index[key] = {"rule_id": "LOCAL-RULE-" + stable_hash([namespace, canonical, norm_alias(alias)])[:20], "namespace": namespace, "canonical": canonical, "alias": alias, "sources": [source]}
    return True


def load_rules(resources, candidate=None):
    resources = Path(resources)
    manifest = json.loads((resources / "UPSTREAM_SHA256.json").read_text(encoding="utf-8"))
    for name in ["upstream_rules.json", "VIA_Central_Synonym_Regex_v0106.json"]:
        if manifest.get(name) != file_hash(resources / name):
            raise ValueError("RULE_SOURCE_HASH_MISMATCH: " + name)
    upstream = json.loads((resources / "upstream_rules.json").read_text(encoding="utf-8"))
    central = json.loads((resources / "VIA_Central_Synonym_Regex_v0106.json").read_text(encoding="utf-8"))
    index, conflicts, pending, patterns = {}, [], [], {}
    for alias, canonical in upstream["broker_aliases"].items():
        if canonical is None:
            pending.append({"alias": alias, "reason": "UPSTREAM_CANONICAL_MISSING"})
            continue
        # Existing upstream aliases disagree on MEGA/MKC; explicit operator convention wins locally.
        if canonical == "MKC":
            canonical = "MEGA"
        add_alias(index, "broker", canonical, alias, "UPSTREAM_v0119", conflicts)
    for canonical, entry in central["synonyms"]["RATING_CODEBOOK_MASTER"].items():
        for alias in entry["aliases"]:
            add_alias(index, "rating", canonical, alias, "CENTRAL_v0106_MASTER", conflicts)
    for namespace, values in [("valuation", upstream["valuation_methods"]), ("job_title", upstream["job_titles"])]:
        for canonical, aliases in values.items():
            for alias in aliases:
                add_alias(index, namespace, canonical, alias, "UPSTREAM_v0119", conflicts)
    for key, entry in central["regex"].items():
        if not isinstance(entry, dict) or not entry.get("pattern"):
            continue
        try:
            re.compile(entry["pattern"])
            patterns[key] = entry["pattern"]
        except re.error as exc:
            conflicts.append({"kind": "INVALID_UPSTREAM_REGEX", "key": key, "reason": str(exc)})
    additions = [("LOCAL_v0120", LOCAL_RULES)]
    for path in (candidate if isinstance(candidate, list) else [candidate] if candidate else []):
        additions.append(("CANDIDATE:" + file_hash(path), json.loads(Path(path).read_text(encoding="utf-8"))))
    for source, addition in additions:
        for namespace, values in addition.items():
            if namespace == "regex":
                for key, pattern in values.items():
                    try:
                        re.compile(pattern)
                        if key in patterns and patterns[key] != pattern:
                            conflicts.append({"kind": "REGEX_REDEFINITION", "key": key, "source": source})
                        else:
                            patterns[key] = pattern
                    except re.error as exc:
                        conflicts.append({"kind": "INVALID_REGEX", "key": key, "reason": str(exc)})
            else:
                for canonical, aliases in values.items():
                    for alias in aliases:
                        add_alias(index, namespace, canonical, alias, source, conflicts)
    # Exact alias and named regex conflicts are decidable; arbitrary regex intersection is not.
    blocked = sorted({r["key"] for r in conflicts if r["kind"] == "ALIAS_COLLISION"})
    result = {"schema": "VRN-LOCAL-SSOT-1", "version": VERSION, "index": index, "patterns": patterns, "blocked_aliases": blocked, "active_aliases": len(index) - len(blocked), "conflicts": conflicts, "pending": pending, "source_commit": upstream["baseline_commit"], "canonical_rulings": [{"scope": "LOCAL_ONLY", "from": "MKC", "to": "MEGA", "reason": "Operator company/broker spelling convention; immutable upstream snapshot retained"}], "semantic_overlap": "FINITE_WITNESS_TESTS_ONLY", "central_registration": "PENDING"}
    result["sha256"] = stable_hash(result)
    return result


def active_candidates(output):
    root = Path(output) / "SSOT"
    pointer = root / "active.json"
    if not pointer.exists():
        return []
    values = json.loads(pointer.read_text(encoding="utf-8"))["candidates"]
    paths = []
    for item in values:
        # Filename is a SHA, never an arbitrary path from the pointer.
        if not re.fullmatch(r"[a-f0-9]{64}", item["sha256"]):
            raise ValueError("ACTIVE_RULE_ID_INVALID")
        p = root / "candidates" / (item["sha256"] + ".json")
        if not p.exists() or file_hash(p) != item["sha256"]:
            raise ValueError("ACTIVE_RULE_HASH_MISMATCH")
        paths.append(p)
    return paths


def accumulate_rules(output, resources, candidate):
    """Atomic local accumulation. Reject a conflicting candidate without changing active rules."""
    root = Path(output) / "SSOT"
    root.mkdir(parents=True, exist_ok=True)
    lock = root / "writer.lock"
    fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.write(fd, str(os.getpid()).encode())
        current = active_candidates(output)
        before = load_rules(resources, current)
        proposed = load_rules(resources, current + [Path(candidate)])
        sha = file_hash(candidate)
        new_conflicts = [r for r in proposed["conflicts"] if r not in before["conflicts"]]
        status = "QUARANTINED" if new_conflicts else "ACCUMULATED"
        folder = root / ("quarantine" if new_conflicts else "candidates")
        folder.mkdir(exist_ok=True)
        destination = folder / (sha + ".json")
        if not destination.exists():
            shutil.copyfile(candidate, destination)
        if not new_conflicts:
            items = [{"sha256": file_hash(p)} for p in current]
            if sha not in {item["sha256"] for item in items}:
                items.append({"sha256": sha})
            write_json(root / "active.json", {"schema": "VRN-ACTIVE-RULES-1", "candidates": items, "updated_at": datetime.now(timezone.utc).isoformat()})
        record = {"at": datetime.now(timezone.utc).isoformat(), "candidate_sha256": sha, "status": status, "prior_rules_sha256": before["sha256"], "proposed_rules_sha256": proposed["sha256"], "new_conflicts": new_conflicts, "central_registration": "PENDING"}
        with (root / "ledger.jsonl").open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        return record
    finally:
        os.close(fd)
        lock.unlink()


def match_aliases(text, rules, namespace, allow_short=False):
    hits = []
    normalized = unicodedata.normalize("NFKC", text)
    for entry in rules["index"].values():
        if entry["namespace"] != namespace:
            continue
        if namespace + ":" + norm_alias(entry["alias"]) in rules.get("blocked_aliases", []):
            continue
        alias = entry["alias"]
        if alias.isascii():
            if not allow_short and len(alias) <= 2:
                continue
            boundary = "A-Za-z" if allow_short else "A-Za-z0-9"
            pattern = r"(?<![" + boundary + r"])" + re.escape(alias) + r"(?![" + boundary + r"])"
        else:
            pattern = re.escape(alias)
        m = re.search(pattern, normalized, re.I)
        if m:
            hits.append((m.start(), -len(alias), entry["canonical"], m.group(0), entry["rule_id"]))
    return sorted(hits)


# 4. Canonical dates/periods and filename logic; impossible dates never propagate.
def valid_date(year, month, day):
    try:
        return date(int(year), int(month), int(day)).isoformat()
    except (ValueError, TypeError):
        return None


def find_dates(text):
    result = []
    specs = [
        (r"(?<!\d)(20\d{2})[年./\-](\d{1,2})[月./\-](\d{1,2})日?(?!\d)", "numeric"),
        (r"(?<!\d)(20\d{2})(\d{2})(\d{2})(?!\d)", "compact"),
        (r"(?<!\d)(1[01]\d)[年./\-]?(\d{2})[月./\-]?(\d{2})日?(?!\d)", "roc"),
        (r"(?<!\d)(?:\(20\))?(2\d)(\d{2})(\d{2})(?!\d)", "short"),
    ]
    for pattern, kind in specs:
        for m in re.finditer(pattern, text):
            year, month, day = map(int, m.groups())
            year += 1911 if kind == "roc" else (2000 if kind == "short" else 0)
            value = valid_date(year, month, day)
            if value:
                result.append({"value": value, "raw": m.group(0), "start": m.start()})
    english = r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b"
    for pattern, reverse in [(english + r"\s+(\d{1,2}),?\s+(20\d{2})", False), (r"\b(\d{1,2})\s+" + english + r"\s+(20\d{2})", True)]:
        for m in re.finditer(pattern, text, re.I):
            a, b, year = m.groups()
            month_text, day_text = (b, a) if reverse else (a, b)
            month = next(v for k, v in MONTHS.items() if k.startswith(month_text.lower()[:3]))
            value = valid_date(year, month, day_text)
            if value:
                result.append({"value": value, "raw": m.group(0), "start": m.start()})
    for m in re.finditer(r"(十一|十二|十|[一二三四五六七八九])月\s*(\d{1,2}),?\s*(20\d{2})", text):
        value = valid_date(m.group(3), CHINESE_MONTHS[m.group(1)], m.group(2))
        if value:
            result.append({"value": value, "raw": m.group(0), "start": m.start()})
    return sorted({(r["value"], r["start"]): r for r in result}.values(), key=lambda r: r["start"])


def normalize_period(raw, context=None):
    s = unicodedata.normalize("NFKC", raw).strip()
    forecast = "ESTIMATE" if re.search(r"(?:E|F|\(F\))$", s, re.I) else ("ACTUAL" if re.search(r"A$", s, re.I) else "UNKNOWN")
    clean = re.sub(r"^(?:FY[- ]?)|(?:\(F\)|[AEF])$", "", s, flags=re.I)
    q = re.fullmatch(r"([1-4])Q(\d{2}|20\d{2})|Q([1-4])[- ]?(\d{2}|20\d{2})|(20\d{2})Q([1-4])", clean, re.I)
    if q:
        if q.group(1):
            quarter, year = q.group(1), int(q.group(2))
        elif q.group(3):
            quarter, year = q.group(3), int(q.group(4))
        else:
            year, quarter = int(q.group(5)), q.group(6)
        year += 2000 if year < 100 else 0
        return {"value": f"{quarter}Q{year % 100:02d}", "kind": "QUARTER", "year": year, "forecast_status": forecast, "raw": raw}
    if re.fullmatch(r"\d{2}|20\d{2}", clean):
        year = int(clean) + (2000 if len(clean) == 2 else 0)
        return {"value": str(year), "kind": "YEAR", "year": year, "forecast_status": forecast, "raw": raw}
    full = find_dates(clean)
    if full and full[0]["raw"] == clean:
        return {"value": full[0]["value"], "kind": "DAY", "forecast_status": forecast, "raw": raw}
    m = re.fullmatch(r"(20\d{2})[-/](\d{1,2})", clean)
    if m and 1 <= int(m.group(2)) <= 12:
        return {"value": f"{m.group(1)}-{int(m.group(2)):02d}", "kind": "MONTH", "forecast_status": forecast, "raw": raw}
    m = re.fullmatch(r"([A-Za-z]{3})[- ](\d{2}|20\d{2})", clean)
    if m and m.group(1).lower() in {k[:3] for k in MONTHS}:
        year = int(m.group(2)) + (2000 if len(m.group(2)) == 2 else 0)
        month = next(v for k, v in MONTHS.items() if k.startswith(m.group(1).lower()))
        if context == "annual":
            return {"value": str(year), "kind": "YEAR", "year": year, "fiscal_year_end_month": month, "forecast_status": forecast, "raw": raw}
        if context == "monthly":
            return {"value": f"{year}-{month:02d}", "kind": "MONTH", "forecast_status": forecast, "raw": raw}
    return {"value": None, "kind": "REVIEW", "forecast_status": forecast, "raw": raw}


def parse_filename(path, rules):
    stem = Path(path).stem
    ds = find_dates(stem)
    masked = stem
    for item in ds:
        masked = masked.replace(item["raw"], " ")
    codes = list(dict.fromkeys(re.findall(r"(?<!\d)([1-9]\d{3})(?!\d)", masked)))
    broker_hits = match_aliases(masked, rules, "broker", True)
    # A longer alias beginning at the same position is more specific (CTBC over CT).
    broker = broker_hits[0][2] if broker_hits else None
    company = analyst = None
    if len(codes) == 1:
        code = re.escape(codes[0])
        patterns = [rf"([^_\-\s（）()]+(?:-KY)?)\s*[（(]{code}", rf"{code}[ _\-]+([^_()（）]+?)(?=[_]|-Memo|-1\d{{6}}|-20\d{{6}}|$)"]
        for pattern in patterns:
            m = re.search(pattern, masked)
            if m:
                candidate = m.group(1).strip(" _-")
                if candidate and candidate not in {"TT", "TW", "TWO"} and not re.search(r"(?:個股|介紹|報告)", candidate):
                    company = candidate
                    break
        parts = stem.split("_")
        if broker == "KGI" and len(parts) >= 4 and re.fullmatch(r"[\u3400-\u9fff]{2,4}", parts[-2]):
            analyst = parts[-2]
    if len(codes) == 1:
        kind = "STOCK"
    elif re.search(r"產業|展望|industry|sector", stem, re.I):
        kind = "INDUSTRY"
    elif re.search(r"新聞|news", stem, re.I):
        kind = "NEWS"
    else:
        kind = "MULTI_TOPIC"
    return {"codes": codes, "broker": broker, "date": ds[0]["value"] if ds else None, "company_candidate": company, "analyst_candidate": analyst, "doc_kind": kind}


# 5. The only acquisition path, shared by every verb; retain source geometry.
def native_lines(page):
    output = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = " ".join(s["text"] for s in spans).strip()
            if text:
                output.append({"text": text, "bbox": list(line["bbox"]), "font_size": max((s["size"] for s in spans), default=0), "confidence": None, "method": "NATIVE"})
    return sorted(output, key=lambda r: (r["bbox"][1], r["bbox"][0]))


def tesseract_lines(image_path, bbox, dpi, config):
    executable = shutil.which("tesseract")
    if executable is None:
        return [], {"state": "DEPENDENCY_UNAVAILABLE", "engine": "tesseract"}
    probe = subprocess.run([executable, "--list-langs"], capture_output=True, text=True, timeout=10)
    lang = "chi_tra+eng" if "chi_tra" in probe.stdout else "eng"
    command = [executable, str(image_path), "stdout", "-l", lang, "--psm", str(config["ocr_psm"]), "tsv"]
    result = subprocess.run(command, capture_output=True, text=True, timeout=config["ocr_timeout"])
    if result.returncode:
        return [], {"state": "OCR_ERROR", "rc": result.returncode, "stderr": result.stderr[-500:], "command": command}
    groups = {}
    for row in csv.DictReader(io.StringIO(result.stdout), delimiter="\t"):
        if row["level"] != "5" or not row["text"].strip():
            continue
        key = tuple(row[x] for x in ["page_num", "block_num", "par_num", "line_num"])
        factor = 72 / dpi
        x, y, w, h = [float(row[k]) * factor for k in ["left", "top", "width", "height"]]
        groups.setdefault(key, []).append({"text": row["text"], "bbox": [bbox[0] + x, bbox[1] + y, bbox[0] + x + w, bbox[1] + y + h], "confidence": float(row["conf"])})
    lines = []
    for words in groups.values():
        lines.append({"text": " ".join(w["text"] for w in words), "bbox": [min(w["bbox"][0] for w in words), min(w["bbox"][1] for w in words), max(w["bbox"][2] for w in words), max(w["bbox"][3] for w in words)], "confidence": sum(w["confidence"] for w in words) / len(words), "font_size": None, "method": f"TESSERACT_{dpi}", "words": words})
    words = [w for line in lines for w in line["words"]]
    low = sum(w["confidence"] < config["ocr_low_confidence"] for w in words)
    return lines, {"state": "EXECUTED", "engine": "tesseract", "lang": lang, "dpi": dpi, "words": len(words), "low_confidence_words": low, "low_fraction": low / len(words) if words else 1, "command": command}


def ocr_page(page, temp, config):
    import fitz
    temp = Path(temp)
    attempts, all_lines = [], []
    light = temp / "light.png"
    page.get_pixmap(dpi=config["light_dpi"]).save(str(light))
    lines, receipt = tesseract_lines(light, list(page.rect), config["light_dpi"], config)
    attempts.append(receipt)
    all_lines.extend(lines)
    # Geometry-aware region pass protects small tables/date against whole-page OCR loss.
    width, height = page.rect.width, page.rect.height
    regions = [fitz.Rect(0, 0, width, height * .22), fitz.Rect(width * .58, height * .22, width, height * .64)]
    for index, bbox in enumerate(regions):
        image_path = temp / f"region_{index}.png"
        page.get_pixmap(dpi=config["region_dpi"], clip=bbox).save(str(image_path))
        recovered, receipt = tesseract_lines(image_path, list(bbox), config["region_dpi"], config)
        attempts.append(receipt)
        # Replace only text inside the crop, never duplicate two OCR readings as two facts.
        if recovered:
            all_lines = [r for r in all_lines if not (bbox.y0 <= (r["bbox"][1] + r["bbox"][3]) / 2 <= bbox.y1 and bbox.x0 <= (r["bbox"][0] + r["bbox"][2]) / 2 <= bbox.x1)]
            all_lines.extend(recovered)
    heavy = config["heavy_ocr_command"]
    if heavy:
        output_path = temp / "heavy.json"
        command = [part.replace("{image}", str(light)).replace("{output}", str(output_path)) for part in heavy]
        result = subprocess.run(command, capture_output=True, text=True, timeout=config["ocr_timeout"])
        attempts.append({"state": "EXECUTED" if result.returncode == 0 else "ERROR", "engine": "EXTERNAL_HEAVY", "rc": result.returncode, "command": command})
        if result.returncode == 0 and output_path.exists():
            heavy_lines = json.loads(output_path.read_text())
            if not isinstance(heavy_lines, list) or any(not all(k in x for k in ["text", "bbox"]) for x in heavy_lines):
                raise ValueError("HEAVY_OCR_CONTRACT_INVALID")
            all_lines = heavy_lines
    else:
        attempts.append({"state": "DEPENDENCY_UNAVAILABLE", "engine": "HEAVY_OCR", "reason": "No configured local model/command"})
    return sorted(all_lines, key=lambda r: (r["bbox"][1], r["bbox"][0])), attempts


def acquire_document(path, config, temp):
    path = Path(path)
    pages, attempts = [], []
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        import fitz
        with fitz.open(path) as document:
            if len(document) > config["max_pages"]:
                raise ValueError("PAGE_LIMIT_EXCEEDED")
            for index, page in enumerate(document):
                lines = native_lines(page)
                text = "\n".join(r["text"] for r in lines)
                lane = "NON_OCR"
                if len(text.strip()) < config["native_min_chars"] or text.count("�") > max(2, len(text) * .01):
                    subdir = Path(temp) / f"page_{index + 1}"
                    subdir.mkdir(parents=True, exist_ok=True)
                    lines, ocr_attempts = ocr_page(page, subdir, config)
                    attempts.extend({"page": index + 1, **r} for r in ocr_attempts)
                    lane = "OCR_REGION" if lines else "NO_TEXT_LAYER"
                pages.append({"page": index + 1, "width": page.rect.width, "height": page.rect.height, "lines": lines, "lane": lane})
    elif suffix == ".docx":
        from docx import Document
        from docx.oxml.ns import qn
        document = Document(path)
        lines, n = [], 0
        for element in document.element.body.iterchildren():
            tag = element.tag
            if tag == qn("w:p"):
                # Direct XML text preserves paragraphs without duplicate itertext expansion.
                text = "".join(x.text or "" for x in element.iter(qn("w:t")))
            elif tag == qn("w:tbl"):
                for row in element.iter(qn("w:tr")):
                    text = " | ".join("".join(x.text or "" for x in cell.iter(qn("w:t"))) for cell in row.iterchildren() if cell.tag == qn("w:tc"))
                    lines.append({"text": text, "bbox": None, "paragraph": n, "method": "DOCX_TABLE", "confidence": None})
                    n += 1
                continue
            else:
                continue
            if text.strip():
                lines.append({"text": text.strip(), "bbox": None, "paragraph": n, "method": "DOCX_XML", "confidence": None})
                n += 1
        pages = [{"page": None, "lines": lines, "lane": "DOCX_XML", "pagination": "UNKNOWN"}]
    elif suffix in {".txt", ".md"}:
        raw = path.read_bytes()
        for encoding in ["utf-8-sig", "cp950", "utf-16"]:
            try:
                text = raw.decode(encoding)
                break
            except UnicodeDecodeError:
                text = None
        if text is None:
            raise ValueError("TEXT_ENCODING_UNRESOLVED")
        pages = [{"page": None, "lane": "TEXT", "lines": [{"text": t, "bbox": None, "paragraph": i, "method": encoding, "confidence": None} for i, t in enumerate(text.splitlines()) if t.strip()]}]
    else:
        from PIL import Image
        image = Image.open(path)
        lines, receipt = tesseract_lines(path, [0, 0, image.width, image.height], 72, config)
        pages = [{"page": 1, "lines": lines, "lane": "IMAGE_OCR", "width": image.width, "height": image.height}]
        attempts = [receipt]
    return {"pages": pages, "attempts": attempts}


# 6. Independent source observations and metadata validation.
def observation(role, value, raw, line, document_sha, page):
    anchor = {"page": page, "bbox": line.get("bbox"), "paragraph": line.get("paragraph")}
    return {"observation_id": "LOCAL-OBS-" + stable_hash([document_sha, role, anchor, raw])[:24], "central_observation_id": None, "role": role, "value": value, "raw": raw, "source_file_sha256": document_sha, **anchor, "extraction_method": line.get("method"), "engine_version": VERSION}


def contact_records(lines, rules, sha, page):
    output = []
    email_rx = re.compile(rules["patterns"]["email_ascii"])
    telephone = re.compile(r"(?:(?:\+?\(?886[-. ]?2\)?|\+?\(?852\)?|\(02\)|02)[-. ]?\d{4}[-. ]?\d{4})(?:\s*(?:ext\.?|分機)\s*\d+)?", re.I)
    for index, line in enumerate(lines):
        for match in email_rx.finditer(line["text"]):
            email = match.group(0)
            local, domain = email.split("@")
            generic = local.isdigit() or local.casefold() in GENERIC_MAILBOXES
            bbox = line.get("bbox")
            near = []
            for other in lines:
                if other is line:
                    continue
                ob = other.get("bbox")
                if bbox and ob:
                    same_row_phone = bool(telephone.search(other["text"])) and abs(ob[1] - bbox[1]) <= 8
                    if ob[1] > bbox[3] + 8 or bbox[1] - ob[3] > 75 or (not same_row_phone and (ob[2] < bbox[0] or ob[0] > bbox[2])):
                        continue
                    distance = abs(bbox[1] - ob[3])
                else:
                    distance = abs(lines.index(other) - index) * 10
                    if distance > 40:
                        continue
                near.append((distance, other))
            near.sort(key=lambda item: item[0])
            printed = None
            tel = None
            title = None
            for _, other in near:
                text = other["text"].strip()
                if tel is None:
                    tm = telephone.search(text)
                    tel = tm.group(0) if tm else None
                if title is None:
                    title_hits = match_aliases(text, rules, "job_title")
                    title = title_hits[0][2] if title_hits else None
                cleaned = re.sub(r"\s+(?:CFA|AC)\b.*$|,\s*CFA$", "", text).strip()
                if printed is None and (re.fullmatch(r"[\u3400-\u9fff]{2,4}", cleaned) or re.fullmatch(r"[A-Z][A-Za-z'\-]+(?:\s+[A-Z][A-Za-z.'\-]+){1,3}", cleaned)) and not any(word in cleaned for word in NAME_STOP):
                    printed = cleaned
            tokens = [x.capitalize() for x in re.split(r"[._\-]+", local) if x] if not generic else []
            inferred = " ".join(tokens) if len(tokens) >= 2 else None
            name_en = printed if printed and printed.isascii() else inferred
            english = name_en.split() if name_en else []
            broker = next((canonical for key, canonical in DOMAIN_BROKERS.items() if domain.casefold() == key or domain.casefold().endswith("." + key)), None)
            output.append({"name_printed": printed, "name_en": name_en, "name_en_source": "PRINTED" if printed and printed.isascii() else ("EMAIL_INFERRED" if inferred else None), "first_name": english[0] if len(english) >= 2 else None, "family_name": english[-1] if len(english) >= 2 else None, "email": email, "tel": tel, "title": title, "broker": broker, "generic": generic, "source": observation("analyst_email", email, email, line, sha, page)})
    return output


def target_observations(lines, rules, sha, page):
    targets = []
    labels = ["12-month target", "12 個月目標價", "Price Target", "Target Price", "目標價", "目標股價", "PT"]
    for index, line in enumerate(lines):
        text = unicodedata.normalize("NFKC", line["text"])
        label = next((x for x in labels if re.search(r"(?<![A-Za-z])" + re.escape(x) + r"(?![A-Za-z])", text, re.I)), None)
        if not label:
            continue
        # Only fields headed by a target label are eligible; narrative movement is separate.
        position = text.lower().find(label.lower())
        if position > 24 and not text.lstrip().startswith("前次"):
            continue
        suffix = text[position + len(label):]
        suffix = re.sub(r"\([^)]*\)", "", suffix)
        suffix = re.sub(r"(?:NT\$|TWD|USD|HK\$|NTD|T W D)", "", suffix, flags=re.I)
        match = re.search(r"(?<![A-Za-z0-9])([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)(?![A-Za-z])", suffix)
        source_line = line
        if match is None and line.get("bbox"):
            bbox = line["bbox"]
            neighbors = [r for r in lines if r is not line and r.get("bbox") and abs(r["bbox"][1] - bbox[1]) < 8 and r["bbox"][0] >= bbox[2] - 10]
            for r in sorted(neighbors, key=lambda r: r["bbox"][0]):
                match = re.search(r"(?:NT\$|TWD|USD|HK\$)?\s*(\d+(?:,\d{3})*(?:\.\d+)?)", r["text"])
                if match:
                    source_line = r
                    break
        if match:
            value = float(match.group(1).replace(",", ""))
            if value > 0:
                role = "target_prior" if re.search(r"前次|previous|prior|old", text[:position + len(label)], re.I) else "target_current"
                targets.append(observation(role, value, source_line["text"], source_line, sha, page))
    return targets


def extract_metadata(path, acquired, rules, sha):
    fn = parse_filename(path, rules)
    pages = acquired["pages"]
    first = pages[0] if pages else {"lines": [], "page": None}
    lines = first["lines"]
    text = "\n".join(r["text"] for r in lines)
    dates = []
    for line in lines:
        for found in find_dates(line["text"]):
            dates.append(observation("report_date_candidate", found["value"], found["raw"], line, sha, first["page"]))
    # Date at top/bottom of a page is stronger than a financial date in the middle.
    dates.sort(key=lambda r: (0 if r["bbox"] and (r["bbox"][1] < first.get("height", 1000) * .18 or r["bbox"][1] > first.get("height", 1000) * .9) else 1, r["bbox"][1] if r["bbox"] else r.get("paragraph", 0)))
    content_date = dates[0]["value"] if dates else None
    content_codes = list(dict.fromkeys(re.findall(r"(?<!\d)([1-9]\d{3})\s*(?:\.TW(?:O)?\b|\s+TT\b)", text)))
    if not content_codes:
        # Company(3038) is a printed code; dates/financial amounts are not.
        content_codes = list(dict.fromkeys(re.findall(r"[\u3400-\u9fffA-Za-z][\u3400-\u9fffA-Za-z\- ]{0,20}[（(]([1-9]\d{3})[)）]", text)))
    contacts = contact_records(lines, rules, sha, first["page"])
    domains = list(dict.fromkeys(r["broker"] for r in contacts if r["broker"]))
    broker_hits = match_aliases(text, rules, "broker")
    content_broker = domains[0] if len(domains) == 1 else (broker_hits[0][2] if broker_hits else None)
    targets = target_observations(lines, rules, sha, first["page"])
    current = [r for r in targets if r["role"] == "target_current"]
    prior = [r for r in targets if r["role"] == "target_prior"]
    rating_hits = match_aliases(text, rules, "rating")
    rating = rating_hits[0][2] if rating_hits else None
    checks = []
    for field, a, b in [("date", fn["date"], content_date), ("ticker", fn["codes"][0] if len(fn["codes"]) == 1 else None, content_codes[0] if len(content_codes) == 1 else None), ("broker", fn["broker"], content_broker)]:
        checks.append({"field": field, "filename_value": a, "content_value": b, "status": "MATCH" if a and b and a == b else ("MISMATCH" if a and b else "ONE_SIDE")})
    ocr = first.get("lane") in {"OCR_REGION", "IMAGE_OCR"}
    document_ocr = any(p["lane"] in {"OCR_REGION", "IMAGE_OCR", "NO_TEXT_LAYER"} for p in pages)
    issues = ["IDENTITY_" + c["field"].upper() + "_MISMATCH" for c in checks if c["status"] == "MISMATCH"]
    if ocr:
        issues.append("OCR_FULL_CONTENT_REVIEW_REQUIRED")
    if not text.strip():
        issues.append("NO_CONTENT")
    # ONE_SIDE does not become an independent agreement by borrowing the filename.
    metadata_status = "REVIEW" if issues or any(c["status"] == "ONE_SIDE" for c in checks) else "PASS"
    result = {"filename": Path(path).name, "size_bytes": Path(path).stat().st_size, "size_h": f"{Path(path).stat().st_size / 1024:.1f} KB", "sha256": sha, "doc_kind": fn["doc_kind"], "filename_identity": fn, "content_date": content_date, "content_codes": content_codes, "content_broker": content_broker, "report_date": content_date or fn["date"], "company_name": fn["company_candidate"], "company_source": "FILENAME_CANDIDATE" if fn["company_candidate"] else "OFFICIAL_CACHE_PENDING", "market": None, "market_source": "OFFICIAL_CACHE_PENDING", "rating": rating, "target_current": current[0]["value"] if current else None, "target_prior": prior[0]["value"] if prior else None, "contacts": contacts, "analyst_name_filename": fn["analyst_candidate"], "date_observations": dates, "target_observations": targets, "checks": checks, "metadata_status": metadata_status, "document_content_status": "OCR_REVIEW" if document_ocr else "ACQUIRED_NOT_SEMANTICALLY_VALIDATED", "issues": issues, "extract_lanes": sorted({p["lane"] for p in pages}), "page_count": len(pages), "external_validation": "PENDING_OFFICIAL_HISTORY_AND_PRICES", "validation_scope": "DOCUMENT_IDENTITY_AND_SELECTED_FIELDS"}
    return result


# 7. Shared reconstruction, actual source-only reverify, and loss-preserving tables.
def reconstruct_source(acquired):
    sections = []
    for page in acquired["pages"]:
        lines = page["lines"]
        # Leave raw source spans intact. Column order is a presentation view only.
        sections.append("PAGE " + str(page["page"] if page["page"] is not None else "UNPAGINATED"))
        if page.get("width"):
            width = page["width"]
            for side in ["left", "right"]:
                selected = [r for r in lines if r.get("bbox") and ((r["bbox"][0] < width * .58) == (side == "left"))]
                sections.append("ZONE " + side.upper())
                sections.extend(r["text"] for r in selected)
        else:
            sections.extend(r["text"] for r in lines)
    return "\n".join(sections)


def table_rows(acquired, sha, rules):
    output = []
    for page in acquired["pages"]:
        groups = []
        for line in page["lines"]:
            bbox = line.get("bbox")
            if bbox is None:
                if " | " in line["text"]:
                    output.append({"source_file_sha256": sha, "page": None, "raw_cells": line["text"].split(" | "), "status": "RAW_GRID", "basis": "UNKNOWN", "unit": None, "periods": []})
                continue
            y = (bbox[1] + bbox[3]) / 2
            group = next((g for g in groups if abs(g["y"] - y) <= CONFIG["line_tolerance"]), None)
            if group is None:
                group = {"y": y, "lines": []}
                groups.append(group)
            group["lines"].append(line)
        for group in groups:
            cells = [r["text"] for r in sorted(group["lines"], key=lambda r: r["bbox"][0])]
            digits = sum(bool(re.fullmatch(r"\(?[-+]?\d+(?:,\d{3})*(?:\.\d+)?%?\)?[AEF]?", c)) for c in cells)
            if len(cells) >= CONFIG["table_min_columns"] and digits >= 2:
                output.append({"source_file_sha256": sha, "page": page["page"], "raw_cells": cells, "bbox": [min(r["bbox"][0] for r in group["lines"]), min(r["bbox"][1] for r in group["lines"]), max(r["bbox"][2] for r in group["lines"]), max(r["bbox"][3] for r in group["lines"])], "status": "GEOMETRY_CANDIDATE_REVIEW", "basis": "UNKNOWN", "unit": None, "periods": [normalize_period(c) for c in cells if re.fullmatch(r"(?:FY)?(?:[1-4]Q)?(?:20)?\d{2}(?:[AEF]|\(F\))?|Dec-\d{2}[AEF]?", c, re.I)]})
    return output


def financial_observations(acquired, sha, rules):
    """Extract supported metric rows only. Unknown period/unit stays explicit REVIEW."""
    result = []
    numeric = re.compile(r"^\(?[-+]?\d+(?:,\d{3})*(?:\.\d+)?%?\)?[AEF]?$")
    for page in acquired["pages"]:
        lines = page["lines"]
        headers = []
        for line in lines:
            period = normalize_period(line["text"])
            if line.get("bbox") and period["kind"] in {"YEAR", "QUARTER"}:
                headers.append((line, period))
        for line in lines:
            matches = match_aliases(line["text"], rules, "financial_metric")
            if not matches or matches[0][0] > 3 or len(line["text"]) > 75:
                continue
            metric = matches[0][2]
            if re.search(r"growth|YoY|QoQ|成長", line["text"], re.I):
                continue
            bbox = line.get("bbox")
            if not bbox:
                continue
            values = []
            if line.get("words"):
                values = [w for w in line["words"] if numeric.fullmatch(w["text"])]
            else:
                values = [r for r in lines if r.get("bbox") and abs((r["bbox"][1] + r["bbox"][3]) / 2 - (bbox[1] + bbox[3]) / 2) <= CONFIG["line_tolerance"] and r["bbox"][0] >= bbox[2] - 10 and numeric.fullmatch(r["text"])]
            if len(values) < 2:
                continue
            for value_line in sorted(values, key=lambda r: r["bbox"][0]):
                raw = value_line["text"]
                cleaned = re.sub(r"[AEF]$", "", raw)
                negative = cleaned.startswith("(") and cleaned.endswith(")")
                cleaned = cleaned.strip("()").rstrip("%")
                value = float(cleaned.replace(",", "")) * (-1 if negative else 1)
                vb = value_line["bbox"]
                compatible = [(h, period) for h, period in headers if 0 < bbox[1] - h["bbox"][3] < 220 and abs((h["bbox"][0] + h["bbox"][2]) / 2 - (vb[0] + vb[2]) / 2) < 22]
                compatible.sort(key=lambda x: bbox[1] - x[0]["bbox"][3])
                period = compatible[0][1] if compatible else {"value": None, "kind": "REVIEW", "forecast_status": "UNKNOWN"}
                unit = "%" if "%" in raw or metric.endswith("MARGIN") else ("TWD_MILLION" if "NT$百萬" in line["text"] else "TWD_PER_SHARE" if metric == "EPS" and "NT$" in line["text"] else None)
                evidence_line = {**line, **value_line}
                evidence = observation("financial_" + metric, value, raw, evidence_line, sha, page["page"])
                result.append({**evidence, "metric": metric, "period": period["value"], "period_kind": period["kind"], "period_raw": period.get("raw"), "forecast_status": period["forecast_status"], "unit": unit, "basis": "BROKER_REPORT", "row_label_raw": line["text"], "status": "CANDIDATE_REVIEW", "official_crosscheck": "PENDING"})
    return result


def arithmetic_check(metric, inputs, printed, tolerance=0.5):
    if any(v is None for v in inputs.values()):
        return {"metric": metric, "status": "NODATA", "inputs": inputs, "printed": printed}
    if metric == "gross_margin":
        denominator = inputs["revenue"]
        calculated = inputs["gross_profit"] / denominator * 100 if denominator else None
    elif metric == "operating_margin":
        denominator = inputs["revenue"]
        calculated = inputs["operating_profit"] / denominator * 100 if denominator else None
    elif metric == "net_margin":
        denominator = inputs["revenue"]
        calculated = inputs["net_profit"] / denominator * 100 if denominator else None
    elif metric == "balance_sheet":
        calculated = inputs["liabilities"] + inputs["equity"]
    else:
        raise ValueError("UNKNOWN_IDENTITY")
    status = "UNDEFINED" if calculated is None else ("PASS" if printed is not None and abs(calculated - printed) <= tolerance else "FAIL_REVIEW")
    return {"metric": metric, "inputs": dict(inputs), "printed": printed, "calculated": calculated, "tolerance": tolerance, "status": status, "source_overwrite": False}


def topic_digest(acquired, kind):
    texts = [r["text"] for p in acquired["pages"] for r in p["lines"]]
    limit = 6 if kind == "INDUSTRY" else 4
    headings = [t for t in texts if 3 <= len(t) <= 45 and not re.search(r"@|\d{4}.*\d{4}", t)]
    sentences = [s.strip() for t in texts for s in re.split(r"(?<=[。!?；])|(?<=[.!?])\s+(?=[A-Z])", t) if len(s.strip()) >= 30]
    keywords = Counter(re.findall(r"\b[A-Za-z][A-Za-z\-]{2,20}\b", " ".join(texts)))
    return {"method": "EXTRACTIVE_RULE_NLP", "topic_candidates": list(dict.fromkeys(headings))[:20], "source_sentences": list(dict.fromkeys(sentences))[:limit], "keywords": [k for k, _ in keywords.most_common(20)], "status": "REVIEW", "reason": "Extractive candidates; semantic multi-topic classification requires review"}


def process_document(path, rules, config, cache):
    path = Path(path)
    sha = file_hash(path)
    key = stable_hash([sha, file_hash(__file__), rules["sha256"], config, RUNTIME.get("state")])
    cache_path = Path(cache) / (key + ".json")
    if cache_path.exists():
        result = json.loads(cache_path.read_text(encoding="utf-8"))
        result["cache_reused"] = True
        return result
    started = time.monotonic()
    acquisition_key = stable_hash([sha, {f.__name__: stable_hash(inspect.getsource(f)) for f in [acquire_document, native_lines, tesseract_lines, ocr_page]}, {k: config[k] for k in ["native_min_chars", "max_pages", "light_dpi", "region_dpi", "ocr_timeout", "ocr_psm", "ocr_low_confidence", "heavy_ocr_command"]}, {k: RUNTIME.get("state", {}).get(k) for k in ["fitz", "docx"]}, shutil.which("tesseract")])
    acquisition_cache = Path(cache) / "acquisition" / (acquisition_key + ".json")
    if acquisition_cache.exists():
        acquired = json.loads(acquisition_cache.read_text(encoding="utf-8"))
        acquisition_reused = True
    else:
        with tempfile.TemporaryDirectory(prefix="VRN_", dir=RUNTIME.get("temp_dir")) as temp:
            acquired = accelerated_call(acquire_document, path, config, temp)
        write_json(acquisition_cache, acquired)
        acquisition_reused = False
    metadata = extract_metadata(path, acquired, rules, sha)
    source_text = reconstruct_source(acquired)
    source_lines = Counter(piece for p in acquired["pages"] for line in p["lines"] for piece in line["text"].splitlines() if piece)
    rendered_lines = Counter(piece for piece in source_text.splitlines() if piece and not re.fullmatch(r"PAGE (?:\d+|UNPAGINATED)|ZONE (?:LEFT|RIGHT)", piece))
    rendering_integrity = "PASS" if source_lines == rendered_lines else "FAIL"
    # Reverify identity from acquisition records, never header/SUMMARY/display output.
    repeated = extract_metadata(path, acquired, rules, sha)
    keys = ["content_date", "content_codes", "content_broker", "target_current", "target_prior"]
    reverify = {k: "STABLE" if metadata[k] == repeated[k] else "MISMATCH" for k in keys}
    result = {"metadata": metadata, "acquisition": acquired, "acquisition_cache_reused": acquisition_reused, "source_text": source_text, "rendering_integrity": rendering_integrity, "reverify": reverify, "reverify_scope": "DETERMINISTIC_REEXTRACTION_FROM_IMMUTABLE_SOURCE_RECORDS; NOT_INDEPENDENT_SOURCE_VALIDATION", "tables": table_rows(acquired, sha, rules), "financial_observations": financial_observations(acquired, sha, rules), "digest": topic_digest(acquired, metadata["doc_kind"]), "engine_version": VERSION, "rules_sha256": rules["sha256"], "engine_sha256": file_hash(__file__), "cache_reused": False, "elapsed_seconds": round(time.monotonic() - started, 3)}
    write_json(cache_path, result)
    return result


# 8. Incremental output, verification receipts, and the local HTML control view.
def export_frames(run_dir, records, config):
    import polars as pl
    import duckdb
    run_dir = Path(run_dir)
    metadata = []
    observations = []
    text_rows = []
    financial_rows = []
    for record in records:
        m = record["metadata"]
        row = {k: v for k, v in m.items() if not isinstance(v, (dict, list))}
        row["ticker"] = m["filename_identity"]["codes"][0] if len(m["filename_identity"]["codes"]) == 1 else None
        row["broker"] = m["filename_identity"]["broker"] or m["content_broker"]
        row["filename_date"] = m["filename_identity"]["date"]
        row["analyst_first_name"] = next((c["first_name"] for c in m["contacts"] if c["first_name"]), None)
        row["analyst_family_name"] = next((c["family_name"] for c in m["contacts"] if c["family_name"]), None)
        metadata.append(row)
        observations.extend(m["date_observations"] + m["target_observations"] + [c["source"] for c in m["contacts"]])
        financial_rows.extend(record["financial_observations"])
        for page in record["acquisition"]["pages"]:
            for line in page["lines"]:
                obs = observation("source_text", line["text"], line["text"], line, m["sha256"], page["page"])
                text_rows.append({"filename": m["filename"], **obs})
    paths = []
    for name, values in [("StockReportBasicInfo", metadata), ("StockReportFinancialData", financial_rows), ("SourceObservations", observations), ("TextRecords", text_rows)]:
        normalized = [{k: json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v for k, v in row.items()} for row in values]
        frame = pl.DataFrame(normalized, infer_schema_length=None) if normalized else pl.DataFrame({"status": []}, schema={"status": pl.String})
        frame.write_parquet(run_dir / (name + ".parquet"))
        frame.write_csv(run_dir / (name + ".csv"), include_bom=True)
        paths.append(name)
    db = duckdb.connect(str(run_dir / "VRN.duckdb"))
    try:
        db.execute("SET memory_limit = ?", [config["memory_limit"]])
        db.execute("SET temp_directory = ?", [str(Path(RUNTIME.get("temp_dir", tempfile.gettempdir())) / "duckdb")])
        for name in paths:
            db.execute('CREATE TABLE "' + name + '" AS SELECT * FROM read_parquet(?)', [str(run_dir / (name + ".parquet"))])
        count = db.execute('SELECT count(*) FROM "StockReportBasicInfo"').fetchone()[0]
        if count != len(records):
            raise ValueError("EXPORT_ROW_COUNT_MISMATCH")
        db.execute("CHECKPOINT")
    finally:
        db.close()
    reopened = duckdb.connect(str(run_dir / "VRN.duckdb"), read_only=True)
    try:
        for name in paths:
            actual = reopened.execute('SELECT count(*) FROM "' + name + '"').fetchone()[0]
            expected = pl.read_parquet(run_dir / (name + ".parquet")).height
            if actual != expected:
                raise ValueError("PERSISTED_EXPORT_ROW_COUNT_MISMATCH: " + name)
    finally:
        reopened.close()
    return {"rows": len(records), "observations": len(observations), "text_records": len(text_rows), "financial_candidates": len(financial_rows), "formats": ["JSON", "CSV_UTF8_BOM", "PARQUET", "DUCKDB"], "verification": "ROW_COUNTS_PASS"}


def html_matrix(run_dir, result):
    mrows = [r["metadata"] for r in result["records"]]
    columns = ["filename", "metadata_status", "doc_kind", "report_date", "rating", "target_current", "target_prior", "size_h", "page_count", "issues"]
    body = "".join("<tr>" + "".join("<td>" + html.escape(str(row.get(k, ""))) + "</td>" for k in columns) + "</tr>" for row in mrows)
    payload = json.dumps({"summary": result["summary"], "rows": mrows}, ensure_ascii=False).replace("<", "\\u003c")
    text = """<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>VRN v0120</title><style>body{background:#faf8f3;color:#252a30;font:12px system-ui;margin:22px}h1{font-size:23px}table{border-collapse:collapse;width:100%}td,th{padding:8px;border:1px solid #d9d5cb;text-align:left;overflow-wrap:anywhere}th{background:#eee9de;position:sticky;top:0}button,select{padding:8px;margin:4px}.bar{height:6px;background:#927d55}.scroll{overflow:auto}.stamp{color:#9b2826;float:right;border:2px solid;padding:5px;font-size:24px}@media(max-width:700px){td,th{max-width:140px}body{margin:10px}}</style><span class="stamp">理</span><b>VERITAS INTELLIGENCE ANALYTICS</b><div>DISCIPLINA • PRUDENTIA • INTEGRITAS</div><b>AI-Powered Research &amp; Decision Intelligence Platform</b><h1>VeritasReportNova · System Manager v0120</h1><div class="bar"></div><p>獨立執行 · 本地 SSOT · 來源保留 · GitHub 未更新</p><select id="filter"><option value="">全部</option><option>PASS</option><option>REVIEW</option></select><select id="format"><option>JSON</option><option>Markdown</option></select><button id="download">匯出矩陣</button><p id="summary"></p><div class="scroll"><table><thead><tr>""" + "".join("<th>" + html.escape(k) + "</th>" for k in columns) + "</tr></thead><tbody>" + body + "</tbody></table></div><p>PASS 僅限文件身分與所列欄位。官方歷史值、價格與全表格語義另行驗收；REVIEW 保留原始資料。</p><script>const data=" + payload + ";document.getElementById('summary').textContent=JSON.stringify(data.summary);document.getElementById('filter').onchange=e=>{document.querySelectorAll('tbody tr').forEach(r=>r.hidden=!!e.target.value&&r.children[1].textContent!==e.target.value)};document.getElementById('download').onclick=()=>{const md=document.getElementById('format').value==='Markdown';let s=md?'|檔名|驗證|日期|\\n|---|---|---|\\n'+data.rows.map(r=>'|'+r.filename+'|'+r.metadata_status+'|'+r.report_date+'|').join('\\n'):JSON.stringify(data,null,2);let a=document.createElement('a');a.href=URL.createObjectURL(new Blob([s],{type:'text/plain;charset=utf-8'}));a.download='VRN_Matrix.'+(md?'md':'json');a.click();URL.revokeObjectURL(a.href)};</script></html>"
    (Path(run_dir) / "index.html").write_text(text, encoding="utf-8")


def run_pipeline(input_path, output, config, rules, verb="run"):
    root = Path(input_path)
    if not root.exists():
        raise FileNotFoundError(str(root))
    files = sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in config["include_extensions"]) if root.is_dir() else [root]
    if not files:
        raise ValueError("NO_SUPPORTED_INPUT")
    out = Path(output).resolve()
    if root.is_dir() and (out == root.resolve() or root.resolve() in out.parents):
        raise ValueError("OUTPUT_MUST_NOT_BE_INSIDE_INPUT")
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex[:8]
    run_dir = out / "runs" / run_id
    run_dir.mkdir(parents=True)
    write_json(run_dir / "SSOT.json", rules)
    records, errors = [], []
    with ThreadPoolExecutor(max_workers=config["workers"]) as pool:
        # Only workers files can hold pages concurrently; submit bounded batches.
        for start in range(0, len(files), config["workers"]):
            batch = files[start:start + config["workers"]]
            futures = [(p, pool.submit(process_document, p, rules, config, out / "cache")) for p in batch]
            for path, future in futures:
                try:
                    records.append(future.result())
                except Exception as exc:
                    errors.append({"filename": path.name, "status": "ERROR", "why": type(exc).__name__ + ": " + str(exc)})
                done = len(records) + len(errors)
                print(f"[PROGRESS] {done}/{len(files)} {done / len(files):.0%} {path.name}", file=sys.stderr, flush=True)
    summary = {"inputs": len(files), "processed": len(records), "errors": len(errors), "metadata_pass": sum(r["metadata"]["metadata_status"] == "PASS" for r in records), "metadata_review": sum(r["metadata"]["metadata_status"] == "REVIEW" for r in records), "rules_conflicts_quarantined": len(rules["conflicts"]), "active_alias_conflicts": 0, "central_registration": "PENDING", "windows_host": "NOT_TESTED", "official_history": "PENDING", "closeout": "ERROR" if errors else "REVIEW"}
    result = {"version": VERSION, "verb": verb, "run_id": run_id, "runtime": RUNTIME.get("state"), "config": config, "summary": summary, "records": records, "errors": errors}
    write_json(run_dir / "result.json", result)
    for record in records:
        stem = Path(record["metadata"]["filename"]).stem
        name = stable_hash(record["metadata"]["filename"])[:8]
        (run_dir / (name + "_RECON_" + stem + ".txt")).write_text(record["source_text"], encoding="utf-8")
    # A writer runs exactly once. Celeritas xrun may retry a failed pool task;
    # global thread limits still cover this sequential mutation.
    result["exports"] = export_frames(run_dir, records, config)
    write_json(run_dir / "result.json", result)
    html_matrix(run_dir, result)
    write_json(out / "latest.json", {"run_id": run_id, "run_dir": str(run_dir), "summary": summary})
    manifest = {p.name: file_hash(p) for p in run_dir.iterdir() if p.is_file()}
    write_json(run_dir / "SHA256.json", manifest)
    print(json.dumps({"summary": summary, "run_dir": str(run_dir)}, ensure_ascii=False))
    return (1 if errors else 2 if summary["metadata_review"] or rules["conflicts"] else 0), run_dir


# 9. The authorized independent entry; no VIA_FROM_VCGC impersonation.
def main(argv=None):
    actual = list(sys.argv[1:] if argv is None else argv)
    if actual == ["--selftest"]:
        actual = ["test"]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("verb", choices=["run", "deepread", "reconstruct", "layout-check", "status", "ssot", "test"])
    parser.add_argument("input", nargs="?")
    parser.add_argument("--output", default=CONFIG["output"])
    parser.add_argument("--resources", default=CONFIG["resources"])
    parser.add_argument("--workers", type=int, default=CONFIG["workers"])
    parser.add_argument("--candidate", help="Additive rule candidate JSON; conflicts quarantined")
    parser.add_argument("--heavy-ocr-config", help="JSON argv for a preinstalled local OCR adapter")
    parser.add_argument("--open", action="store_true", help="Open report in the default browser after processing")
    args = parser.parse_args(actual)
    config = dict(CONFIG, resources=args.resources, output=args.output, workers=max(1, min(args.workers, 4)))
    if args.heavy_ocr_config:
        config["heavy_ocr_command"] = json.loads(Path(args.heavy_ocr_config).read_text())
    if args.verb == "test":
        return subprocess.run([sys.executable, "-m", "pytest", str(HERE / "test_vrn_v0120.py"), "-q", "-k", "not real and not exports", "--tb=short"]).returncode
    candidates = active_candidates(args.output)
    if args.verb == "ssot" and args.candidate:
        receipt = accumulate_rules(args.output, config["resources"], args.candidate)
        candidates = active_candidates(args.output)
    else:
        receipt = None
        if args.candidate:
            candidates.append(Path(args.candidate))
    rules = load_rules(config["resources"], candidates)
    initialize_runtime(config)
    if args.verb == "status":
        print(json.dumps({"version": VERSION, "standalone": True, "runtime": RUNTIME["state"], "rules": len(rules["index"]), "conflicts": rules["conflicts"], "pending": rules["pending"]}, ensure_ascii=False, indent=2))
        return 0
    if args.verb == "ssot":
        write_json(Path(args.output) / "SSOT" / (rules["sha256"] + ".json"), rules)
        print(json.dumps({"rules": len(rules["index"]), "active_aliases": rules["active_aliases"], "regex": len(rules["patterns"]), "conflicts": rules["conflicts"], "sha256": rules["sha256"], "candidate_receipt": receipt}, ensure_ascii=False))
        return 2 if receipt and receipt["status"] == "QUARANTINED" else 0
    if not args.input:
        parser.error("input path required")
    rc, run_dir = run_pipeline(args.input, args.output, config, rules, args.verb)
    if args.open:
        import webbrowser
        webbrowser.open((run_dir / "index.html").as_uri())
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
