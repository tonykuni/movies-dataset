# -*- coding: utf-8 -*-
"""
def VIA_ParametersConsolidation_Engine
Read-only panoramic parameter extractor for VIA/VDF/VRN/VPF/VHS/VIS files.
No external dependencies.
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====

import argparse
import base64
import csv
import hashlib
import html
import json
import os
import re
import sys
import zipfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


def def_read_json(path: str | Path) -> dict:
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def def_write_json(obj: Any, path: str | Path) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2, default=str)


def def_write_csv(rows: list[dict], path: str | Path, fieldnames: list[str] | None = None) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    if fieldnames is None:
        keys = []
        seen = set()
        for row in rows:
            for k in row.keys():
                if k not in seen:
                    seen.add(k)
                    keys.append(k)
        fieldnames = keys

    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def def_sha12(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(1024 * 1024)
            if not b:
                break
            h.update(b)
    return h.hexdigest()[:12]


def def_read_text(path: str | Path, max_bytes: int = 6000000) -> tuple[str, str]:
    p = Path(path)
    data = p.read_bytes()[:max_bytes]

    for enc in ["utf-8-sig", "utf-8", "utf-16", "cp950", "big5", "latin-1"]:
        try:
            return data.decode(enc), enc
        except Exception:
            continue

    return data.decode("utf-8", errors="replace"), "utf-8-replace"


def def_extract_docx_text(path: str | Path) -> str:
    try:
        with zipfile.ZipFile(path) as z:
            xml_bytes = z.read("word/document.xml")
        root = ET.fromstring(xml_bytes)
        texts = []
        for elem in root.iter():
            if elem.tag.endswith("}t") and elem.text:
                texts.append(elem.text)
        return "\n".join(texts)
    except Exception as exc:
        return f"[DOCX_EXTRACT_ERROR] {exc}"


def def_safe_preview(value: Any, n: int = 240) -> str:
    s = str(value)
    s = re.sub(r"\s+", " ", s).strip()
    if len(s) > n:
        return s[:n] + "..."
    return s


def def_norm_key(key: str) -> str:
    s = str(key).strip()
    s = re.sub(r"^[\$]+", "", s)
    s = re.sub(r"^(def_PARAM_|DEF_PARAM_|PARAM_|param_|def_|DEF_)", "", s)
    s = re.sub(r"[^A-Za-z0-9一-龥]+", "_", s)
    s = re.sub(r"_+", "_", s).strip("_").lower()
    return s


def def_classify_project(path: str) -> str:
    name = Path(path).name.lower()
    full = path.lower()

    if "vdf" in name or "\\vdf\\" in full:
        return "VDF"
    if "vrn" in name or "\\vrn\\" in full:
        return "VRN"
    if "vpf" in name:
        return "VPF"
    if "vhs" in name:
        return "VHS"
    if "vis" in name:
        return "VIS"
    if "vef" in name or "engineforge" in name:
        return "VEF"
    if "veritaspulse" in name or "vpl" in name:
        return "VPL"
    if "via" in name:
        return "VIA"
    if "ll34" in name:
        return "LL34"
    return "UNKNOWN"


def def_classify_file_role(path: str) -> str:
    name = Path(path).name.lower()
    ext = Path(path).suffix.lower()

    if "registry" in name:
        return "REGISTRY"
    if "config" in name or "template" in name:
        return "CONFIG_TEMPLATE"
    if "engine" in name or "mdl" in name:
        return "ENGINE_MODULE"
    if "field" in name:
        return "FIELD_SCHEMA"
    if "lock" in name:
        return "LOCK_REGISTRY"
    if "visual" in name or "ui" in name or ext in [".html", ".htm", ".png"]:
        return "UI_VISUAL"
    if "manifest" in name:
        return "MANIFEST"
    if "health" in name or "summary" in name or "report" in name:
        return "REPORT"
    if "test" in name or "verify" in name or "lint" in name:
        return "TEST_VALIDATION"
    if ext == ".docx" or "methodology" in name:
        return "METHODOLOGY"
    return "SOURCE"


def def_classify_param_group(key: str, value: str = "") -> str:
    s = f"{key} {value}".lower()

    if any(x in s for x in ["path", "dir", "folder", "root", "output", "input", "file"]):
        return "PATH_IO"
    if any(x in s for x in ["ticker", "symbol", "stock", "etf", "twse", "tpex"]):
        return "MARKET_UNIVERSE"
    if any(x in s for x in ["api", "url", "endpoint", "yfinance", "akshare", "fred", "fetch"]):
        return "DATA_SOURCE"
    if any(x in s for x in ["engine", "module", "mdl", "router", "resolver"]):
        return "ENGINE"
    if any(x in s for x in ["field", "schema", "column", "dtype", "type"]):
        return "SCHEMA_FIELD"
    if any(x in s for x in ["theme", "color", "visual", "html", "css", "ui", "lock"]):
        return "VISUAL_LOCK"
    if any(x in s for x in ["risk", "policy", "hardgate", "validation", "safe", "no_delete", "no_stop"]):
        return "GOVERNANCE_POLICY"
    if any(x in s for x in ["version", "v0", "release", "run_id", "generated_at"]):
        return "VERSION_RELEASE"
    if any(x in s for x in ["rate", "cpi", "gdp", "macro", "sentiment", "aaii", "cnn", "fear", "greed"]):
        return "MACRO_SENTIMENT"
    return "GENERAL"


def def_new_param(
    file_id: str,
    path: str,
    project: str,
    role: str,
    source_type: str,
    key: str,
    value: Any,
    line_no: int | None = None,
    context: str = "",
    confidence: str = "MEDIUM",
) -> dict:
    value_preview = def_safe_preview(value)
    nk = def_norm_key(key)

    return {
        "def_file_id": file_id,
        "def_path": path,
        "def_project": project,
        "def_file_role": role,
        "def_source_type": source_type,
        "def_line_no": line_no if line_no is not None else "",
        "def_key": str(key),
        "def_normalized_key": nk,
        "def_value_preview": value_preview,
        "def_group": def_classify_param_group(str(key), value_preview),
        "def_context": def_safe_preview(context),
        "def_confidence": confidence,
    }


def def_flatten_json(obj: Any, prefix: str = "") -> list[tuple[str, Any]]:
    rows = []

    if isinstance(obj, dict):
        for k, v in obj.items():
            new_key = f"{prefix}.{k}" if prefix else str(k)
            rows.extend(def_flatten_json(v, new_key))
    elif isinstance(obj, list):
        if len(obj) == 0:
            rows.append((prefix, "[]"))
        else:
            for i, v in enumerate(obj[:2000]):
                new_key = f"{prefix}[{i}]"
                rows.extend(def_flatten_json(v, new_key))
            if len(obj) > 2000:
                rows.append((f"{prefix}.__truncated_count", len(obj)))
    else:
        rows.append((prefix, obj))

    return rows


def def_extract_json_params(path: str, file_id: str, project: str, role: str, max_bytes: int) -> tuple[list[dict], dict]:
    params = []
    meta = {"json_valid": False, "json_error": ""}

    try:
        text, enc = def_read_text(path, max_bytes=max_bytes)
        obj = json.loads(text)
        meta["json_valid"] = True
        meta["encoding"] = enc

        for key, value in def_flatten_json(obj):
            if key:
                params.append(def_new_param(file_id, path, project, role, "json", key, value, None, "json_flatten", "HIGH"))
    except Exception as exc:
        meta["json_error"] = str(exc)

    return params, meta


def def_extract_csv_params(path: str, file_id: str, project: str, role: str, max_bytes: int) -> tuple[list[dict], dict]:
    params = []
    meta = {"csv_valid": False, "csv_error": ""}

    try:
        text, enc = def_read_text(path, max_bytes=max_bytes)
        lines = text.splitlines()
        sample = "\n".join(lines[:50])
        dialect = csv.Sniffer().sniff(sample) if sample.strip() else csv.excel
        reader = csv.reader(lines, dialect)
        header = next(reader, [])
        meta["csv_valid"] = True
        meta["encoding"] = enc
        meta["columns"] = header

        for i, col in enumerate(header):
            params.append(def_new_param(file_id, path, project, role, "csv_header", f"column_{i:03d}", col, 1, "csv header", "HIGH"))
    except Exception as exc:
        meta["csv_error"] = str(exc)

    return params, meta


def def_extract_python_params(text: str, path: str, file_id: str, project: str, role: str) -> list[dict]:
    params = []
    lines = text.splitlines()

    re_assign = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*(#.*)?$")
    re_def = re.compile(r"^\s*def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\((.*?)\)\s*:")
    re_class = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)")
    re_add_arg = re.compile(r"\.add_argument\s*\((.*?)\)")
    re_import = re.compile(r"^\s*(?:from\s+([A-Za-z0-9_\.]+)\s+import|import\s+(.+))")

    for i, line in enumerate(lines, start=1):
        m = re_assign.match(line)
        if m:
            key = m.group(1)
            val = m.group(2)
            is_param = (
                key.startswith("def_PARAM_")
                or key.startswith("PARAM_")
                or key.isupper()
                or any(x in key.lower() for x in ["path", "dir", "config", "registry", "engine", "ticker", "source", "output", "input"])
            )
            if is_param:
                params.append(def_new_param(file_id, path, project, role, "python_assignment", key, val, i, line, "HIGH"))

        m = re_def.match(line)
        if m:
            params.append(def_new_param(file_id, path, project, role, "python_function", f"function.{m.group(1)}", m.group(2), i, line, "HIGH"))

        m = re_class.match(line)
        if m:
            params.append(def_new_param(file_id, path, project, role, "python_class", f"class.{m.group(1)}", m.group(1), i, line, "HIGH"))

        m = re_add_arg.search(line)
        if m:
            params.append(def_new_param(file_id, path, project, role, "python_argparse", "argparse.add_argument", m.group(1), i, line, "HIGH"))

        m = re_import.match(line)
        if m:
            val = m.group(1) or m.group(2)
            params.append(def_new_param(file_id, path, project, role, "python_import", "import", val, i, line, "MEDIUM"))

    return params


def def_extract_powershell_params(text: str, path: str, file_id: str, project: str, role: str) -> list[dict]:
    params = []
    lines = text.splitlines()

    re_assign = re.compile(r"^\s*\$([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+?)\s*$")
    re_func = re.compile(r"^\s*function\s+([A-Za-z_][A-Za-z0-9_\-]*)")
    re_param_var = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")
    re_validate = re.compile(r"ValidateSet\s*\((.*?)\)", re.IGNORECASE)

    in_param = False
    depth = 0

    for i, line in enumerate(lines, start=1):
        low = line.strip().lower()

        if low.startswith("param"):
            in_param = True
            depth += line.count("(") - line.count(")")
            params.append(def_new_param(file_id, path, project, role, "powershell_param_block", "param_block.start", line.strip(), i, line, "HIGH"))
            continue

        if in_param:
            for vm in re_param_var.finditer(line):
                key = vm.group(1)
                params.append(def_new_param(file_id, path, project, role, "powershell_param", key, "", i, line, "HIGH"))

            vm = re_validate.search(line)
            if vm:
                params.append(def_new_param(file_id, path, project, role, "powershell_validateset", "ValidateSet", vm.group(1), i, line, "HIGH"))

            depth += line.count("(") - line.count(")")
            if depth <= 0:
                in_param = False
                depth = 0

        m = re_assign.match(line)
        if m:
            key = m.group(1)
            val = m.group(2)
            is_param = (
                key.startswith("def_PARAM_")
                or key.startswith("PARAM_")
                or any(x in key.lower() for x in ["path", "dir", "config", "registry", "engine", "input", "output", "root", "enable"])
            )
            if is_param:
                params.append(def_new_param(file_id, path, project, role, "powershell_assignment", key, val, i, line, "HIGH"))

        m = re_func.match(line)
        if m:
            params.append(def_new_param(file_id, path, project, role, "powershell_function", f"function.{m.group(1)}", m.group(1), i, line, "HIGH"))

    return params


def def_extract_js_params(text: str, path: str, file_id: str, project: str, role: str) -> list[dict]:
    params = []
    lines = text.splitlines()

    re_assign = re.compile(r"^\s*(const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(.+?);?\s*$")
    re_func = re.compile(r"^\s*function\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*\((.*?)\)")
    re_class = re.compile(r"^\s*class\s+([A-Za-z_$][A-Za-z0-9_$]*)")

    for i, line in enumerate(lines, start=1):
        m = re_assign.match(line)
        if m:
            key = m.group(2)
            val = m.group(3)
            if key.isupper() or any(x in key.lower() for x in ["config", "path", "registry", "api", "url", "selector", "engine", "lock"]):
                params.append(def_new_param(file_id, path, project, role, "js_assignment", key, val, i, line, "HIGH"))

        m = re_func.match(line)
        if m:
            params.append(def_new_param(file_id, path, project, role, "js_function", f"function.{m.group(1)}", m.group(2), i, line, "HIGH"))

        m = re_class.match(line)
        if m:
            params.append(def_new_param(file_id, path, project, role, "js_class", f"class.{m.group(1)}", m.group(1), i, line, "HIGH"))

    return params


def def_extract_html_params(text: str, path: str, file_id: str, project: str, role: str) -> list[dict]:
    params = []
    lines = text.splitlines()

    re_id = re.compile(r'\b(id|name|data-[A-Za-z0-9_\-]+|aria-label)\s*=\s*["\']([^"\']+)["\']', re.IGNORECASE)
    re_css_var = re.compile(r"(--[A-Za-z0-9_\-]+)\s*:\s*([^;]+);")
    re_js_assign = re.compile(r"\b(const|let|var)\s+([A-Za-z_$][A-Za-z0-9_$]*)\s*=\s*(.+?);")

    for i, line in enumerate(lines, start=1):
        for m in re_id.finditer(line):
            params.append(def_new_param(file_id, path, project, role, "html_attribute", m.group(1), m.group(2), i, line, "MEDIUM"))

        for m in re_css_var.finditer(line):
            params.append(def_new_param(file_id, path, project, role, "css_variable", m.group(1), m.group(2), i, line, "HIGH"))

        for m in re_js_assign.finditer(line):
            key = m.group(2)
            val = m.group(3)
            if any(x in key.lower() for x in ["config", "registry", "api", "path", "engine", "theme", "lock", "data"]):
                params.append(def_new_param(file_id, path, project, role, "html_script_assignment", key, val, i, line, "MEDIUM"))

    return params


def def_extract_markdown_like_params(text: str, path: str, file_id: str, project: str, role: str) -> list[dict]:
    params = []
    lines = text.splitlines()

    re_heading = re.compile(r"^\s{0,3}(#{1,6})\s+(.+)")
    re_keyval = re.compile(r"^\s*([A-Za-z0-9_\-一-龥\. ]{2,80})\s*[:：=]\s*(.+?)\s*$")
    re_path = re.compile(r"([A-Za-z]:\\[^\s\"'`]+)")
    re_url = re.compile(r"https?://[^\s\"'`]+")

    for i, line in enumerate(lines, start=1):
        m = re_heading.match(line)
        if m:
            params.append(def_new_param(file_id, path, project, role, "md_heading", f"heading.{len(m.group(1))}", m.group(2), i, line, "MEDIUM"))

        m = re_keyval.match(line)
        if m:
            key = m.group(1).strip()
            val = m.group(2).strip()
            if len(key) <= 80:
                params.append(def_new_param(file_id, path, project, role, "text_key_value", key, val, i, line, "MEDIUM"))

        for p in re_path.findall(line):
            params.append(def_new_param(file_id, path, project, role, "text_windows_path", "windows_path", p, i, line, "HIGH"))

        for u in re_url.findall(line):
            params.append(def_new_param(file_id, path, project, role, "text_url", "url", u, i, line, "HIGH"))

    return params


def def_extract_file(path: str, config: dict) -> tuple[dict, list[dict]]:
    p = Path(path)
    exists = p.exists()
    ext = p.suffix.lower()
    project = def_classify_project(path)
    role = def_classify_file_role(path)

    file_meta = {
        "def_path": path,
        "def_exists": exists,
        "def_file_name": p.name,
        "def_ext": ext,
        "def_project": project,
        "def_file_role": role,
        "def_size_bytes": "",
        "def_sha12": "",
        "def_status": "MISSING" if not exists else "OK",
        "def_encoding": "",
        "def_error": "",
    }

    params = []

    if not exists:
        return file_meta, params

    try:
        file_meta["def_size_bytes"] = p.stat().st_size
        file_meta["def_sha12"] = def_sha12(path)
        file_id = f"{p.name}::{file_meta['def_sha12']}"

        max_bytes = int(config.get("policy", {}).get("max_text_bytes", 6000000))
        docx_enabled = bool(config.get("policy", {}).get("docx_text_extraction", True))

        if ext == ".json":
            p1, meta = def_extract_json_params(path, file_id, project, role, max_bytes)
            params.extend(p1)
            file_meta.update({f"def_{k}": v for k, v in meta.items()})

        elif ext == ".csv":
            p1, meta = def_extract_csv_params(path, file_id, project, role, max_bytes)
            params.extend(p1)
            file_meta.update({f"def_{k}": v for k, v in meta.items()})

        elif ext == ".docx" and docx_enabled:
            text = def_extract_docx_text(path)
            file_meta["def_encoding"] = "docx_zip_xml"
            params.extend(def_extract_markdown_like_params(text, path, file_id, project, role))

        elif ext in [".png", ".jpg", ".jpeg", ".webp"]:
            params.append(def_new_param(file_id, path, project, role, "image_file", "image_file", p.name, None, "metadata only", "LOW"))

        else:
            text, enc = def_read_text(path, max_bytes=max_bytes)
            file_meta["def_encoding"] = enc

            if ext == ".py":
                params.extend(def_extract_python_params(text, path, file_id, project, role))
            elif ext == ".ps1":
                params.extend(def_extract_powershell_params(text, path, file_id, project, role))
            elif ext == ".js":
                params.extend(def_extract_js_params(text, path, file_id, project, role))
            elif ext in [".html", ".htm"]:
                params.extend(def_extract_html_params(text, path, file_id, project, role))
                params.extend(def_extract_markdown_like_params(text, path, file_id, project, role))
            else:
                params.extend(def_extract_markdown_like_params(text, path, file_id, project, role))

        file_meta["def_param_count"] = len(params)

    except Exception as exc:
        file_meta["def_status"] = "ERROR"
        file_meta["def_error"] = str(exc)

    return file_meta, params


def def_build_engine_matrix(params: list[dict], file_rows: list[dict]) -> list[dict]:
    engine_rows = []
    by_file = defaultdict(list)

    for p in params:
        by_file[p["def_path"]].append(p)

    for f in file_rows:
        role = f.get("def_file_role", "")
        path = f.get("def_path", "")
        name = f.get("def_file_name", "")

        related = by_file.get(path, [])
        engine_hits = [
            x for x in related
            if x.get("def_group") == "ENGINE"
            or "engine" in x.get("def_key", "").lower()
            or "function." in x.get("def_key", "").lower()
            or "class." in x.get("def_key", "").lower()
        ]

        if role == "ENGINE_MODULE" or engine_hits:
            engine_rows.append({
                "def_engine_file": name,
                "def_path": path,
                "def_project": f.get("def_project", ""),
                "def_file_role": role,
                "def_ext": f.get("def_ext", ""),
                "def_sha12": f.get("def_sha12", ""),
                "def_engine_param_count": len(engine_hits),
                "def_total_param_count": f.get("def_param_count", 0),
                "def_engine_keys_preview": "; ".join([x.get("def_key", "") for x in engine_hits[:20]]),
            })

    return engine_rows


def def_build_conflicts(params: list[dict]) -> list[dict]:
    bucket = defaultdict(list)

    for p in params:
        nk = p.get("def_normalized_key", "")
        if nk:
            bucket[nk].append(p)

    conflicts = []

    for nk, rows in bucket.items():
        values = defaultdict(list)
        for r in rows:
            values[r.get("def_value_preview", "")].append(r)

        if len(values) > 1 and len(rows) > 1:
            sample_values = []
            sample_files = []

            for val, val_rows in list(values.items())[:8]:
                sample_values.append(val)
                sample_files.extend([Path(x["def_path"]).name for x in val_rows[:3]])

            conflicts.append({
                "def_normalized_key": nk,
                "def_occurrences": len(rows),
                "def_distinct_values": len(values),
                "def_groups": ";".join(sorted(set([x.get("def_group", "") for x in rows]))),
                "def_projects": ";".join(sorted(set([x.get("def_project", "") for x in rows]))),
                "def_sample_values": " || ".join(sample_values[:8]),
                "def_sample_files": "; ".join(sorted(set(sample_files))[:20]),
                "def_severity": "HIGH" if len(values) >= 4 else "MEDIUM",
            })

    conflicts.sort(key=lambda x: (x["def_severity"] != "HIGH", -x["def_distinct_values"], -x["def_occurrences"]))
    return conflicts


def def_build_ssot(params: list[dict], conflicts: list[dict]) -> dict:
    conflict_keys = set([x["def_normalized_key"] for x in conflicts])
    grouped = defaultdict(list)

    for p in params:
        grouped[p["def_normalized_key"]].append(p)

    ssot_rows = []

    for nk, rows in grouped.items():
        if not nk:
            continue

        score_rows = sorted(
            rows,
            key=lambda r: (
                {"HIGH": 3, "MEDIUM": 2, "LOW": 1}.get(r.get("def_confidence", ""), 0),
                len(r.get("def_value_preview", "")),
            ),
            reverse=True,
        )

        best = score_rows[0]

        ssot_rows.append({
            "def_normalized_key": nk,
            "def_preferred_key": best.get("def_key", ""),
            "def_preferred_value": best.get("def_value_preview", ""),
            "def_group": best.get("def_group", ""),
            "def_project": best.get("def_project", ""),
            "def_source_file": Path(best.get("def_path", "")).name,
            "def_source_path": best.get("def_path", ""),
            "def_confidence": best.get("def_confidence", ""),
            "def_occurrences": len(rows),
            "def_has_conflict": nk in conflict_keys,
            "def_policy": "REVIEW_CONFLICT" if nk in conflict_keys else "SSOT_CANDIDATE",
        })

    ssot_rows.sort(key=lambda x: (x["def_group"], x["def_normalized_key"]))

    return {
        "schema_version": "VIA_Parameters_SSOT_v0100",
        "rows": ssot_rows,
        "group_counts": dict(Counter([x["def_group"] for x in ssot_rows])),
        "conflict_count": len(conflicts),
    }


def def_write_html_report(
    summary: dict,
    file_rows: list[dict],
    params: list[dict],
    engine_rows: list[dict],
    conflicts: list[dict],
    html_path: str,
) -> None:
    project_counts = Counter([x.get("def_project", "") for x in file_rows])
    group_counts = Counter([x.get("def_group", "") for x in params])
    role_counts = Counter([x.get("def_file_role", "") for x in file_rows])

    def table_rows(rows: list[dict], columns: list[str], limit: int = 300) -> str:
        out = []
        for row in rows[:limit]:
            tds = []
            for c in columns:
                tds.append(f"<td>{html.escape(def_safe_preview(row.get(c, ''), 220))}</td>")
            out.append("<tr>" + "".join(tds) + "</tr>")
        return "\n".join(out)

    def counter_html(counter: Counter) -> str:
        rows = []
        for k, v in counter.most_common(30):
            rows.append(f"<tr><td>{html.escape(str(k))}</td><td>{v}</td></tr>")
        return "\n".join(rows)

    file_cols = ["def_project", "def_file_role", "def_file_name", "def_ext", "def_status", "def_param_count", "def_path"]
    param_cols = ["def_project", "def_file_role", "def_group", "def_key", "def_value_preview", "def_source_type", "def_file_id"]
    engine_cols = ["def_project", "def_engine_file", "def_file_role", "def_engine_param_count", "def_total_param_count", "def_engine_keys_preview"]
    conflict_cols = ["def_severity", "def_normalized_key", "def_occurrences", "def_distinct_values", "def_groups", "def_sample_values", "def_sample_files"]

    html_text = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<title>VIA Parameters Consolidation Panorama</title>
<style>
body {{
    margin: 32px;
    background: #f8faf7;
    color: #203238;
    font-family: "Noto Sans TC", "Microsoft JhengHei", Arial, sans-serif;
}}
h1, h2 {{
    color: #007f73;
    font-weight: 500;
}}
.card {{
    background: #fff;
    border: 1px solid #d9e7e2;
    border-radius: 16px;
    padding: 18px 22px;
    margin: 18px 0;
    box-shadow: 0 10px 28px rgba(31,47,54,.06);
}}
.kpi {{
    display: grid;
    grid-template-columns: repeat(5, minmax(150px, 1fr));
    gap: 14px;
}}
.kpi div {{
    background: #fff;
    border-top: 4px solid #00a889;
    border-radius: 14px;
    padding: 16px;
}}
.big {{
    font-size: 30px;
    color: #536b78;
}}
table {{
    width: 100%;
    border-collapse: collapse;
    background: #fff;
}}
th, td {{
    border-bottom: 1px solid #e4ece8;
    padding: 8px 9px;
    text-align: left;
    vertical-align: top;
    font-size: 12px;
}}
th {{
    color: #006b60;
    background: #f3f8f6;
    position: sticky;
    top: 0;
}}
.grid2 {{
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 14px;
}}
pre {{
    white-space: pre-wrap;
    background: #f4f8f7;
    padding: 14px;
    border-radius: 12px;
}}
</style>
</head>
<body>
<h1>def VIA Parameters Consolidation Panorama</h1>

<div class="kpi">
<div><b>Status</b><br><span class="big">{html.escape(summary.get("status", ""))}</span></div>
<div><b>Files</b><br><span class="big">{summary.get("file_count", 0)}</span></div>
<div><b>Params</b><br><span class="big">{summary.get("parameter_count", 0)}</span></div>
<div><b>Engines</b><br><span class="big">{summary.get("engine_count", 0)}</span></div>
<div><b>Conflicts</b><br><span class="big">{summary.get("conflict_count", 0)}</span></div>
</div>

<div class="grid2">
<div class="card">
<h2>def Project Counts</h2>
<table><thead><tr><th>Project</th><th>Count</th></tr></thead><tbody>{counter_html(project_counts)}</tbody></table>
</div>
<div class="card">
<h2>def Parameter Groups</h2>
<table><thead><tr><th>Group</th><th>Count</th></tr></thead><tbody>{counter_html(group_counts)}</tbody></table>
</div>
<div class="card">
<h2>def File Roles</h2>
<table><thead><tr><th>Role</th><th>Count</th></tr></thead><tbody>{counter_html(role_counts)}</tbody></table>
</div>
</div>

<div class="card">
<h2>def File Matrix</h2>
<table>
<thead><tr>{''.join([f'<th>{c}</th>' for c in file_cols])}</tr></thead>
<tbody>{table_rows(file_rows, file_cols, 500)}</tbody>
</table>
</div>

<div class="card">
<h2>def Engine Matrix</h2>
<table>
<thead><tr>{''.join([f'<th>{c}</th>' for c in engine_cols])}</tr></thead>
<tbody>{table_rows(engine_rows, engine_cols, 300)}</tbody>
</table>
</div>

<div class="card">
<h2>def Conflict Matrix</h2>
<table>
<thead><tr>{''.join([f'<th>{c}</th>' for c in conflict_cols])}</tr></thead>
<tbody>{table_rows(conflicts, conflict_cols, 300)}</tbody>
</table>
</div>

<div class="card">
<h2>def Parameter Matrix Preview</h2>
<table>
<thead><tr>{''.join([f'<th>{c}</th>' for c in param_cols])}</tr></thead>
<tbody>{table_rows(params, param_cols, 800)}</tbody>
</table>
</div>

<div class="card">
<h2>def Output Paths</h2>
<pre>{html.escape(json.dumps(summary.get("outputs", {}), ensure_ascii=False, indent=2))}</pre>
</div>

</body>
</html>
"""
    Path(html_path).parent.mkdir(parents=True, exist_ok=True)
    Path(html_path).write_text(html_text, encoding="utf-8")


def def_run(input_json: str) -> dict:
    config = def_read_json(input_json)

    out_dir = Path(config["paths"]["output_dir"])
    out_dir.mkdir(parents=True, exist_ok=True)

    source_paths = config.get("source_paths", [])
    file_rows = []
    all_params = []

    for path in source_paths:
        file_meta, params = def_extract_file(path, config)
        file_rows.append(file_meta)
        all_params.extend(params)

    engine_rows = def_build_engine_matrix(all_params, file_rows)
    conflicts = def_build_conflicts(all_params) if config.get("policy", {}).get("conflict_detection", True) else []
    ssot = def_build_ssot(all_params, conflicts)

    parameter_csv = out_dir / "VIA_ParametersConsolidated_Registry.csv"
    parameter_json = out_dir / "VIA_ParametersConsolidated_Registry.json"
    file_csv = out_dir / "VIA_Parameters_FileMatrix.csv"
    engine_csv = out_dir / "VIA_Parameters_EngineMatrix.csv"
    conflict_csv = out_dir / "VIA_Parameters_ConflictMatrix.csv"
    ssot_json = out_dir / "VIA_Parameters_SSOT.json"
    summary_json = out_dir / "VIA_ParametersConsolidation_Summary.json"
    report_html = config["paths"]["report_html"]

    def_write_csv(all_params, parameter_csv)
    def_write_json({"schema_version": "VIA_ParametersConsolidated_Registry_v0100", "rows": all_params}, parameter_json)
    def_write_csv(file_rows, file_csv)
    def_write_csv(engine_rows, engine_csv)
    def_write_csv(conflicts, conflict_csv)
    def_write_json(ssot, ssot_json)

    missing_count = len([x for x in file_rows if not x.get("def_exists")])
    error_count = len([x for x in file_rows if x.get("def_status") == "ERROR"])

    summary = {
        "schema_version": "VIA_ParametersConsolidation_Summary_v0100",
        "status": "VIA_PARAMETERS_CONSOLIDATION_READY" if error_count == 0 else "VIA_PARAMETERS_CONSOLIDATION_READY_WITH_REVIEW",
        "risk": "LOW" if error_count == 0 and missing_count == 0 else "MEDIUM",
        "input_json": input_json,
        "file_count": len(file_rows),
        "missing_count": missing_count,
        "error_count": error_count,
        "parameter_count": len(all_params),
        "engine_count": len(engine_rows),
        "conflict_count": len(conflicts),
        "project_counts": dict(Counter([x.get("def_project", "") for x in file_rows])),
        "group_counts": dict(Counter([x.get("def_group", "") for x in all_params])),
        "role_counts": dict(Counter([x.get("def_file_role", "") for x in file_rows])),
        "outputs": {
            "parameter_csv": str(parameter_csv),
            "parameter_json": str(parameter_json),
            "file_matrix_csv": str(file_csv),
            "engine_matrix_csv": str(engine_csv),
            "conflict_csv": str(conflict_csv),
            "ssot_json": str(ssot_json),
            "summary_json": str(summary_json),
            "report_html": str(report_html),
        },
    }

    def_write_json(summary, summary_json)
    def_write_html_report(summary, file_rows, all_params, engine_rows, conflicts, report_html)

    return summary


def def_main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-json", required=True)
    args = parser.parse_args()

    summary = def_run(args.input_json)

    print("=" * 80)
    print("def VIA Parameters Consolidation Complete")
    print("=" * 80)
    print(f"Status    : {summary['status']}")
    print(f"Risk      : {summary['risk']}")
    print(f"Files     : {summary['file_count']}")
    print(f"Missing   : {summary['missing_count']}")
    print(f"Params    : {summary['parameter_count']}")
    print(f"Engines   : {summary['engine_count']}")
    print(f"Conflicts : {summary['conflict_count']}")
    print(f"HTML      : {summary['outputs']['report_html']}")


if __name__ == "__main__":
    def_main()
