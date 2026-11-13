#!/usr/bin/env python3
"""Build bounded, standalone v0106.4 subsystem workspaces from the frozen model.

The source snapshot is parsed as data only.  No uploaded/native source is imported,
executed, registered, started, or written back.  Each workspace receives only rows
whose source ``system`` equals its system exactly, plus a separately-labelled compact
shared-evidence subset.  Outputs are create-once/idempotent: an existing file may
only be reused when its bytes are identical.
"""
from __future__ import annotations

import argparse
import base64
import gzip
import hashlib
import json
import re
import stat
from collections import Counter
from pathlib import Path
from typing import Any

VERSION = "v0106.4"
MODEL_VERSION = "v0105"
SYSTEMS = ("VCGC", "VDF", "VRN", "VQG", "VAP", "Database")
MATRIX_ORDER = (
    "systems",
    "io",
    "commands",
    "files",
    "environment",
    "policy",
    "conflicts",
    "requirements",
    "tests",
)
ALL_MATRIX_NAMES = MATRIX_ORDER
STATUS_CODES = ("RED", "YELLOW", "GREEN")
MAX_GZIP_BYTES = 80 * 1024 * 1024
MAX_RAW_BYTES = 80 * 1024 * 1024
EXPECTED_SOURCE_SHA256 = "c3b2b84d16abbe3ae1ab8984dc6fd933b6aceef18372d1fea16d94d694691ff1"
EXPECTED_SOURCE_BYTES = 1_547_437
EXPECTED_RAW_SHA256 = "c1e5fe44484b746574704cadc1fff727f1f6166d86880bd50cb9542883d000c4"
OBSERVATIONS_PATH = "data/subsystem_live_observations_v0106.json"
TOKEN_CONTEXT_PATH = "artifacts/subsystem_token_context_v0106.json"
TOKEN_TOOLS_PATH = "artifacts/token_tools_v0106_20261106.json"
HISTORICAL_MATRIX_PATH = "data/system_matrix.json"
HISTORICAL_COVERAGE_PATH = "data/system_coverage.json"
EXPECTED_HISTORICAL_MATRIX_SHA256 = "b6e2ee2c50971fc04264295796f8c902a538ee6b4d677ede4183f0683994c75e"
EXPECTED_HISTORICAL_COVERAGE_SHA256 = "94906d90edf30bc1eba8c02bda249ef18cd2c569d23529456f5598080a4a170f"
EXPECTED_OBSERVATIONS_SHA256 = "f7fbee5e7307540d98dece8a43d98d25318e676c48fcd2644e19de3ed5724e70"
EXPECTED_TOKEN_CONTEXT_SHA256 = "7e1f7fa0ec9536d29cc1ec1a43c849db2fe9cfbfb2e6c4939b75a4c8b427e41c"
EXPECTED_TOKEN_TOOLS_SHA256 = "b57ec28a59e235199cf8d6f7faf2d902cf431ada7229676e55041c86864554be"
LOGO_DESCRIPTOR = "data/brand_asset_v0105.json"
LOGO_PATH = "public/veritas_logo_header_v0105.png"
TEMPLATE_PATH = "scripts/subsystem_v0106_4.html"
CSS_PATH = "scripts/subsystem_v0106_4.css"
JS_PATH = "scripts/subsystem_v0106_4.js"


class BuildError(ValueError):
    """Fail-closed source or output error."""


def ensure_regular_path(path: str | Path) -> Path:
    """Reject symlink/reparse paths in the file and existing parent chain."""
    p = Path(path).absolute()
    for item in (p, *p.parents):
        if not item.exists():
            continue
        st = item.lstat()
        if item.is_symlink() or getattr(st, "st_file_attributes", 0) & 0x400:
            raise BuildError(f"reparse/symlink path refused: {item}")
    return p


def _reject_constant(value: str) -> Any:
    raise BuildError(f"NONFINITE_JSON:{value}")


def _strict_pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in items:
        if key in result:
            raise BuildError(f"DUPLICATE_JSON_KEY:{key}")
        result[key] = value
    return result


def strict_json_loads(raw: bytes | str, source: str = "json") -> Any:
    try:
        text = raw.decode("utf-8") if isinstance(raw, bytes) else raw
        return json.loads(
            text,
            object_pairs_hook=_strict_pairs,
            parse_constant=_reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, BuildError) as exc:
        raise BuildError(f"STRICT_JSON_ERROR:{source}:{exc}") from exc


def strict_json_dumps(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise BuildError(f"JSON_SERIALIZE_ERROR:{exc}") from exc


def sha256_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_bounded_json(path: str | Path, label: str, expected_sha256: str | None = None) -> Any:
    p = ensure_regular_path(path)
    if not p.is_file() or p.stat().st_size > MAX_RAW_BYTES:
        raise BuildError(f"OBSERVATION_FILE_LIMIT_OR_MISSING:{label}")
    actual = sha256_file(p)
    if expected_sha256 and actual != expected_sha256:
        raise BuildError(f"OBSERVATION_SHA256_MISMATCH:{label}:expected={expected_sha256}:actual={actual}")
    return strict_json_loads(p.read_bytes(), label)


def load_supplemental_observations(
    root: str | Path,
    observations_path: str | Path | None = None,
    token_context_path: str | Path | None = None,
    token_tools_path: str | Path | None = None,
) -> dict[str, Any]:
    """Return whitelisted session observations without raw argv or token material."""
    root_path = Path(root)
    live_path = Path(observations_path) if observations_path else root_path / OBSERVATIONS_PATH
    context_path = Path(token_context_path) if token_context_path else root_path / TOKEN_CONTEXT_PATH
    tools_path = Path(token_tools_path) if token_tools_path else root_path / TOKEN_TOOLS_PATH
    live = _load_bounded_json(live_path, OBSERVATIONS_PATH, EXPECTED_OBSERVATIONS_SHA256)
    context = _load_bounded_json(context_path, TOKEN_CONTEXT_PATH, EXPECTED_TOKEN_CONTEXT_SHA256)
    tools = _load_bounded_json(tools_path, TOKEN_TOOLS_PATH, EXPECTED_TOKEN_TOOLS_SHA256)
    if not isinstance(live, dict) or not isinstance(context, dict) or not isinstance(tools, dict):
        raise BuildError("OBSERVATIONS_NOT_OBJECTS")
    safe_live = {
        key: live.get(key)
        for key in ("version", "observed_at_utc", "pc", "mcp", "github", "reference", "attachments", "policy", "production_deployment", "existing_engine_modified")
        if key in live
    }
    safe_context_rows = []
    for row in context.get("rows", []):
        if isinstance(row, dict):
            safe_context_rows.append({key: row.get(key) for key in ("system", "management_rows", "status", "semantic_roundtrip", "lossy", "provider_calls", "heuristic_reduction_pct") if key in row})
    safe_tool_rows = []
    result_keys = ("ok", "base_tests_run", "integration_tests_run", "tests_run", "failures", "errors", "skill_count", "case_count", "passed_count", "failed_count", "provider_calls")
    for row in tools.get("rows", []):
        if not isinstance(row, dict):
            continue
        result_value = row.get("result")
        result: dict[str, Any] = result_value if isinstance(result_value, dict) else {}
        safe_tool_rows.append({
            key: row.get(key) for key in ("name", "system", "status") if key in row
        } | {"result_summary": {key: result.get(key) for key in result_keys if key in result}})
    return {
        "kind": "SHARED_CANDIDATE_OR_SESSION_OBSERVATIONS",
        "not_native_test_counts": True,
        "live": safe_live,
        "token_context": {
            "status": context.get("status"), "count": context.get("count"), "rows": safe_context_rows,
            "source_model_sha256": context.get("source_model_sha256"), "script_sha256": context.get("script_sha256"),
            "engine_sha256": context.get("engine_sha256"), "tested_scope": context.get("tested_scope"),
            "measurement": context.get("measurement"), "provider_calls": context.get("provider_calls"),
        },
        "token_tools": {
            "status": tools.get("status"), "count": tools.get("count"), "rows": safe_tool_rows,
            "engine_sha256": tools.get("engine_sha256"), "provider_calls": tools.get("provider_calls"),
            "provider_billing_tokens": tools.get("provider_billing_tokens"), "activated_scope": tools.get("activated_scope"),
        },
        "provenance": {
            "observations": {"path": OBSERVATIONS_PATH, "sha256": EXPECTED_OBSERVATIONS_SHA256, "bytes": Path(live_path).stat().st_size},
            "token_context": {"path": TOKEN_CONTEXT_PATH, "sha256": EXPECTED_TOKEN_CONTEXT_SHA256, "bytes": Path(context_path).stat().st_size},
            "token_tools": {"path": TOKEN_TOOLS_PATH, "sha256": EXPECTED_TOKEN_TOOLS_SHA256, "bytes": Path(tools_path).stat().st_size},
            "label": "supplemental shared candidate/session observations; not native system/test counts",
        },
    }


def load_database_historical_governance(root: str | Path) -> dict[str, Any]:
    """Load prior Database governance records as separate, non-live evidence."""
    root_path = Path(root)
    matrix_path = ensure_regular_path(root_path / HISTORICAL_MATRIX_PATH)
    coverage_path = ensure_regular_path(root_path / HISTORICAL_COVERAGE_PATH)
    matrix = _load_bounded_json(matrix_path, HISTORICAL_MATRIX_PATH, EXPECTED_HISTORICAL_MATRIX_SHA256)
    coverage = _load_bounded_json(coverage_path, HISTORICAL_COVERAGE_PATH, EXPECTED_HISTORICAL_COVERAGE_SHA256)
    matrix_rows = [row for row in matrix.get("systems", []) if isinstance(row, dict) and row.get("id") == "Database"]
    coverage_rows = [row for row in coverage.get("systems", []) if isinstance(row, dict) and row.get("system") == "Database"]
    return {
        "kind": "SEPARATE_SOURCE_PINNED_HISTORICAL_GOVERNANCE",
        "live": False,
        "owned_rows": 0,
        "matrix_records": matrix_rows,
        "coverage_records": coverage_rows,
        "provenance": {
            "matrix": {"path": HISTORICAL_MATRIX_PATH, "sha256": EXPECTED_HISTORICAL_MATRIX_SHA256, "bytes": matrix_path.stat().st_size},
            "coverage": {"path": HISTORICAL_COVERAGE_PATH, "sha256": EXPECTED_HISTORICAL_COVERAGE_SHA256, "bytes": coverage_path.stat().st_size},
            "note": "Historical governance context only; not LAST_MATRIX source rows, live state, connection, or test completion.",
        },
    }


def load_authoritative_model(
    path: str | Path,
    *,
    expected_sha256: str = EXPECTED_SOURCE_SHA256,
    expected_bytes: int | None = EXPECTED_SOURCE_BYTES,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Load the fixed gzip snapshot with raw and total byte caps."""
    p = ensure_regular_path(path)
    if not p.is_file():
        raise FileNotFoundError(f"authoritative model missing: {p}")
    size = p.stat().st_size
    if size > MAX_GZIP_BYTES:
        raise BuildError(f"GZIP_SIZE_LIMIT_EXCEEDED:{size}")
    digest = sha256_file(p)
    if expected_sha256 and digest != expected_sha256:
        raise BuildError(f"SOURCE_SHA256_MISMATCH:expected={expected_sha256}:actual={digest}")
    if expected_bytes is not None and size != expected_bytes:
        raise BuildError(f"SOURCE_BYTES_MISMATCH:expected={expected_bytes}:actual={size}")

    raw_chunks: list[bytes] = []
    raw_total = 0
    try:
        with gzip.open(p, "rb") as stream:
            while True:
                block = stream.read(min(1024 * 1024, MAX_RAW_BYTES - raw_total + 1))
                if not block:
                    break
                raw_total += len(block)
                if raw_total > MAX_RAW_BYTES:
                    raise BuildError(f"RAW_JSON_SIZE_LIMIT_EXCEEDED:{raw_total}")
                raw_chunks.append(block)
    except BuildError:
        raise
    except (OSError, EOFError, gzip.BadGzipFile) as exc:
        raise BuildError(f"GZIP_READ_ERROR:{exc}") from exc
    raw = b"".join(raw_chunks)
    raw_sha = sha256_bytes(raw)
    if raw_sha != EXPECTED_RAW_SHA256 and expected_sha256 == EXPECTED_SOURCE_SHA256:
        raise BuildError(f"RAW_SHA256_MISMATCH:expected={EXPECTED_RAW_SHA256}:actual={raw_sha}")
    model = strict_json_loads(raw, str(p))
    validate_model(model)
    source = {
        "path": str(p),
        "sha256": digest,
        "bytes": size,
        "raw_bytes": len(raw),
        "raw_sha256": raw_sha,
        "model_version": model.get("version"),
    }
    return model, source


def validate_model(model: Any) -> None:
    if not isinstance(model, dict):
        raise BuildError("MODEL_NOT_OBJECT")
    if model.get("version") != MODEL_VERSION:
        raise BuildError(f"MODEL_VERSION_REQUIRED:{MODEL_VERSION}")
    matrices = model.get("matrices")
    if not isinstance(matrices, dict):
        raise BuildError("MATRICES_NOT_OBJECT")
    if tuple(matrices.keys()) != tuple(("files", "io", "commands", "environment", "conflicts", "policy", "tests", "requirements", "systems")):
        # The frozen input is required to retain all original matrix names; order is
        # not semantically significant, but missing/extra names are not accepted.
        if set(matrices) != set(("files", "io", "commands", "environment", "conflicts", "policy", "tests", "requirements", "systems")):
            raise BuildError("MATRIX_CATEGORY_SET_MISMATCH")
    for category in matrices:
        rows = matrices[category]
        if not isinstance(rows, list):
            raise BuildError(f"MATRIX_NOT_ARRAY:{category}")
        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                raise BuildError(f"MATRIX_ROW_NOT_OBJECT:{category}:{index}")
            if any(not isinstance(key, str) for key in row):
                raise BuildError(f"MATRIX_KEY_NOT_STRING:{category}:{index}")
    if not isinstance(model.get("meta"), dict):
        raise BuildError("MODEL_META_NOT_OBJECT")


def is_shared_system(system: Any) -> bool:
    value = str(system)
    upper = value.upper()
    return (
        "VIA_SHARED" in upper
        or "CROSS_SYSTEM" in upper
        or upper == "ALL_SYSTEMS"
        or upper.endswith("_ADDON_CANDIDATE")
    )


def filtered_matrix(model: dict[str, Any], system: str) -> dict[str, list[dict[str, Any]]]:
    """Losslessly retain only rows whose source system equals ``system``."""
    return {
        category: [row for row in model["matrices"][category] if row.get("system") == system]
        for category in ALL_MATRIX_NAMES
    }


def shared_subset(model: dict[str, Any]) -> list[dict[str, Any]]:
    """Keep shared evidence separate, carrying its original category and row."""
    result: list[dict[str, Any]] = []
    for category in ALL_MATRIX_NAMES:
        for row in model["matrices"][category]:
            if is_shared_system(row.get("system")):
                result.append({"category": category, "row": row})
    return result


def status_code(value: Any) -> str:
    upper = str(value if value is not None else "").upper()
    if re.search(r"\bRED\b", upper):
        return "RED"
    if re.search(r"\bGREEN\b", upper):
        return "GREEN"
    return "YELLOW"


def stats_for(system: str, matrix: dict[str, list[dict[str, Any]]], shared: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [row for rows in matrix.values() for row in rows]
    by_category = {category: len(matrix[category]) for category in ALL_MATRIX_NAMES}
    by_status = Counter(status_code(row.get("status")) for row in rows)
    return {
        "system": system,
        "source_system_filter": "r.system == system",
        "rows_total": len(rows),
        "by_category": by_category,
        "status_counts": {code: int(by_status.get(code, 0)) for code in STATUS_CODES},
        "shared_evidence_rows_separate": len(shared),
    }


def safe_script_json(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
    return (
        text.replace("&", r"\u0026")
        .replace("<", r"\u003c")
        .replace(">", r"\u003e")
        .replace("\u2028", r"\u2028")
        .replace("\u2029", r"\u2029")
    )


def read_logo(root: Path) -> tuple[str, dict[str, Any]]:
    logo = ensure_regular_path(root / LOGO_PATH)
    descriptor = strict_json_loads((root / LOGO_DESCRIPTOR).read_bytes(), LOGO_DESCRIPTOR)
    expected = descriptor.get("assets", {}).get("embedded_header", {})
    if expected.get("path") != LOGO_PATH:
        raise BuildError("LOGO_DESCRIPTOR_PATH_MISMATCH")
    if not logo.is_file() or sha256_file(logo) != expected.get("sha256") or logo.stat().st_size != expected.get("bytes"):
        raise BuildError("LOGO_DESCRIPTOR_SHA_OR_SIZE_MISMATCH")
    return base64.b64encode(logo.read_bytes()).decode("ascii"), {
        "path": LOGO_PATH,
        "sha256": expected["sha256"],
        "bytes": expected["bytes"],
        "width": expected.get("width"),
        "height": expected.get("height"),
        "descriptor": LOGO_DESCRIPTOR,
    }


def make_payload(
    model: dict[str, Any],
    source: dict[str, Any],
    system: str,
    shared: list[dict[str, Any]],
    observations: dict[str, Any] | None = None,
    historical_database: dict[str, Any] | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    last_matrix = filtered_matrix(model, system)
    bundle = {
        "version": VERSION,
        "system": system,
        "LAST_MATRIX": last_matrix,
        "SHARED_EVIDENCE": shared,
        "SHARED_CANDIDATE_OR_SESSION_OBSERVATIONS": observations or {},
        "DATABASE_HISTORICAL_GOVERNANCE": historical_database or {},
        "source": {
            "model_version": source["model_version"],
            "model_gzip_path": source["path"],
            "model_gzip_sha256": source["sha256"],
            "model_gzip_bytes": source["bytes"],
            "model_raw_bytes": source["raw_bytes"],
            "model_raw_sha256": source["raw_sha256"],
            "source_snapshot": "original snapshot; as-of 2026-11-06 from source filename; not current GitHub health",
            "source_meta": model["meta"],
        },
    }
    raw = strict_json_dumps(bundle)
    compressed = gzip.compress(raw, compresslevel=9, mtime=0)
    envelope = {
        "encoding": "gzip+base64",
        "raw_bytes": len(raw),
        "raw_sha256": sha256_bytes(raw),
        "gzip_bytes": len(compressed),
        "gzip_sha256": sha256_bytes(compressed),
        "base64": base64.b64encode(compressed).decode("ascii"),
    }
    return envelope, {"raw": raw, "compressed": compressed, "stats": stats_for(system, last_matrix, shared)}


def _create_once(path: Path, data: bytes) -> None:
    path = Path(path).absolute()
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if not path.is_file() or path.read_bytes() != data:
            raise BuildError(f"EXISTING_OUTPUT_DIFFERS:{path}")
        return
    path.write_bytes(data)


def build(
    root: str | Path,
    source_path: str | Path | None = None,
    *,
    expected_sha256: str = EXPECTED_SOURCE_SHA256,
    expected_bytes: int | None = EXPECTED_SOURCE_BYTES,
    observations_path: str | Path | None = None,
    token_context_path: str | Path | None = None,
    token_tools_path: str | Path | None = None,
) -> dict[str, Any]:
    root_path = ensure_regular_path(root)
    if source_path:
        source_candidate = Path(source_path)
    else:
        portable = root_path / "data" / "source_model_v0105.json.gz"
        source_candidate = portable if portable.is_file() else Path("/home/ubuntu/VIA_Matrix_Governance_Full_Model_v0105_1_20261106.json.gz")
    model, source = load_authoritative_model(source_candidate, expected_sha256=expected_sha256, expected_bytes=expected_bytes)
    observations = load_supplemental_observations(root_path, observations_path, token_context_path, token_tools_path)
    historical_database = load_database_historical_governance(root_path)
    logo_b64, logo_source = read_logo(root_path)
    template = (root_path / TEMPLATE_PATH).read_text(encoding="utf-8")
    css = (root_path / CSS_PATH).read_text(encoding="utf-8")
    js = (root_path / JS_PATH).read_text(encoding="utf-8")
    if not all(marker in template for marker in ("__CSP__", "__CSS__", "__JS__", "__PAYLOAD__", "__SYSTEM__", "__BRAND_LOGO__")):
        raise BuildError("TEMPLATE_MARKER_MISSING")
    source_js_hash = base64.b64encode(hashlib.sha256(js.encode("utf-8")).digest()).decode("ascii")
    shared = shared_subset(model)
    pages: dict[str, dict[str, Any]] = {}
    for system in SYSTEMS:
        envelope, details = make_payload(model, source, system, shared, observations, historical_database)
        page_js = js.replace("__SYSTEM__", system)
        if "__SYSTEM__" in page_js:
            raise BuildError("JS_SYSTEM_MARKER_UNRESOLVED")
        js_hash = base64.b64encode(hashlib.sha256(page_js.encode("utf-8")).digest()).decode("ascii")
        csp = (
            "default-src 'none'; script-src 'sha256-" + js_hash + "'; style-src 'unsafe-inline'; "
            "img-src data:; connect-src 'none'; base-uri 'none'; form-action 'none'"
        )
        page = template
        replacements = {
            "__CSP__": csp,
            "__CSS__": css,
            "__JS__": page_js,
            "__PAYLOAD__": safe_script_json(envelope),
            "__SYSTEM__": system,
            "__BRAND_LOGO__": logo_b64,
        }
        for marker, replacement in replacements.items():
            expected_marker_count = 3 if marker == "__SYSTEM__" else 1
            if page.count(marker) != expected_marker_count:
                raise BuildError(f"TEMPLATE_MARKER_COUNT:{marker}")
            page = page.replace(marker, replacement)
        if any(marker in page for marker in replacements):
            raise BuildError("TEMPLATE_MARKER_UNRESOLVED")
        if len(page.encode("utf-8")) >= 3 * 1024 * 1024:
            raise BuildError(f"HTML_SIZE_LIMIT_EXCEEDED:{system}")
        output = root_path / "public" / f"system-v0106.4-{system.lower()}.html"
        _create_once(output, page.encode("utf-8"))
        pages[system] = {
            "path": str(output.relative_to(root_path)),
            "bytes": output.stat().st_size,
            "sha256": sha256_file(output),
            "payload_raw_bytes": envelope["raw_bytes"],
            "payload_content_sha256": envelope["raw_sha256"],
            "payload_gzip_bytes": envelope["gzip_bytes"],
            "payload_gzip_sha256": envelope["gzip_sha256"],
            "csp_sha256_base64": js_hash,
            "stats": details["stats"],
        }

    hub = make_hub(root_path, logo_b64)
    hub_path = root_path / "public" / "subsystems-v0106.4.html"
    _create_once(hub_path, hub.encode("utf-8"))
    manifest = {
        "schema": "VIA-SUBSYSTEM-MANIFEST/1.0",
        "version": VERSION,
        "candidate_status": "v0106.4 CANDIDATE",
        "actual_release": "RED / BLOCKED",
        "formal_registration": False,
        "production": False,
        "runtime_execution": "NOT_RUN",
        "native_runtime": "NOT_RUN",
        "safety_flags": {
            "formal_registration": False,
            "production": False,
            "runtime_execution": False,
            "native_runtime": False,
            "live_database_connection": False,
            "writes_performed": False,
            "source_modified": False,
            "published": False,
            "direct_pdf_download": False,
        },
        "tony_nb": "UNAVAILABLE · original snapshot/source boundary",
        "uploaded_allinone_fixture": "UPLOADED selftest fixture · not production",
        "source_snapshot": {
            "provenance": "authoritative frozen full merged model; original snapshot",
            "asof": "2026-11-06 (source filename)",
            "not_current_github_health": True,
            "source": source,
        },
        "shared_candidate_or_session_observations": observations["provenance"],
        "sources": {
            "authoritative_model": source,
            "branding": logo_source,
            "html_template": {"path": TEMPLATE_PATH, "sha256": sha256_file(root_path / TEMPLATE_PATH)},
            "css": {"path": CSS_PATH, "sha256": sha256_file(root_path / CSS_PATH)},
            "js": {"path": JS_PATH, "sha256": sha256_file(root_path / JS_PATH), "source_csp_sha256_base64": source_js_hash, "note": "page CSP uses per-system substituted JS digest recorded under systems.*.csp_sha256_base64"},
        },
        "original_matrix_totals": {category: len(model["matrices"][category]) for category in model["matrices"]},
        "source_counts": {
            "original_matrix_rows": sum(len(rows) for rows in model["matrices"].values()),
            "owned_rows_total": sum(details["stats"]["rows_total"] for details in pages.values()),
            "shared_rows_separate": len(shared),
            "supplemental_sources": 3,
            "supplemental_token_context_rows": int(observations["token_context"].get("count") or 0),
            "supplemental_token_tools_rows": int(observations["token_tools"].get("count") or 0),
        },
        "shared_subset": {"rows": len(shared), "label": "RELEVANT SHARED EVIDENCE · not counted as owned rows"},
        "database_boundary": {"system": "Database", "owned_rows": 0, "status": "NO_OWNED_SOURCE_ROWS / UNAVAILABLE / NOT_RUN", "live_connection": False, "zero_rows_not_green": True},
        "database_historical_governance": historical_database["provenance"],
        "systems": pages,
        "hub": {"path": str(hub_path.relative_to(root_path)), "bytes": hub_path.stat().st_size, "sha256": sha256_file(hub_path)},
    }
    manifest_path = root_path / "data" / "subsystem_manifest_v0106_4.json"
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    _create_once(manifest_path, manifest_bytes)
    return {
        "version": VERSION,
        "source": source,
        "shared_rows": len(shared),
        "systems": {system: pages[system]["stats"] for system in SYSTEMS},
        "outputs": [str(hub_path), *[str(root_path / pages[s]["path"]) for s in SYSTEMS], str(manifest_path)],
        "published": False,
    }


def make_hub(root: Path, logo_b64: str) -> str:
    cards = []
    for system in SYSTEMS:
        cards.append(
            '<a class="system-card" href="system-v0106.4-' + system.lower() + '.html">'
            '<span class="system-code">' + system + '</span>'
            '<span class="system-name">Open independent subsystem workspace</span>'
            '<span class="system-status">ACTUAL · RED / BLOCKED · v0106.4 CANDIDATE</span>'
            '<span class="system-open">開啟系統畫面 →</span></a>'
        )
    css = """
:root{--bg:#f2f1ec;--ink:#33403f;--line:#dbd9d3;--green:#2c4f4a;--red:#9e2b25;--white:#fff;--serif:'Cormorant Garamond',Georgia,serif;--sans:'Microsoft JhengHei','Segoe UI',sans-serif;--mono:Consolas,monospace}*{box-sizing:border-box}html{background:var(--bg);color:var(--ink);font-family:var(--sans)}body{margin:0}header{display:flex;align-items:center;gap:14px;padding:16px 24px;border-bottom:1px solid var(--line);background:var(--bg)}.logo{height:74px;width:auto;aspect-ratio:420/384;object-fit:contain;border:0;background:transparent;box-shadow:none}.copy{min-width:0}.eyebrow{margin:0;color:#6b6860;font:9px/1.5 var(--mono);letter-spacing:.09em;overflow-wrap:anywhere}h1{margin:4px 0;font:16px/1.25 var(--serif);color:#1b1a17}h2{font:14px/1.3 var(--serif);margin:0 0 5px;color:#1b1a17}.subtitle{margin:0;color:#6b6860;font-size:12px}.badge{display:inline-flex;border:1px solid var(--line);border-radius:999px;background:var(--white);padding:4px 8px;color:var(--red);font:9px/1.4 var(--mono)}main{max-width:1180px;margin:0 auto;padding:28px 20px 60px}.intro{display:flex;justify-content:space-between;align-items:flex-end;gap:15px;border-bottom:1px solid var(--line);padding-bottom:18px}.intro p{max-width:700px;color:#6b6860;margin:0;font-size:13px;line-height:1.7}.legend{margin:16px 0;display:flex;gap:7px;flex-wrap:wrap}.legend span{border:1px solid var(--line);border-radius:999px;background:var(--white);padding:4px 8px;color:#6b6860;font:9px/1.5 var(--mono)}.cards{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin-top:20px}.system-card{display:flex;flex-direction:column;gap:10px;min-height:190px;padding:16px;border:1px solid var(--line);border-radius:9px;background:var(--white);text-decoration:none;color:var(--ink);transition:border-color .15s,transform .15s}.system-card:hover,.system-card:focus-visible{border-color:var(--green);transform:translateY(-2px);outline:2px solid var(--green);outline-offset:2px}.system-code{font:22px/1.1 var(--serif);color:var(--green)}.system-name{font-size:12px;line-height:1.5;flex:1}.system-status{color:var(--red);font:8px/1.5 var(--mono)}.system-open{color:var(--green);font-size:11px}@media(max-width:1180px){.cards{grid-template-columns:repeat(3,minmax(0,1fr))}}@media(max-width:900px){.cards{grid-template-columns:repeat(2,minmax(0,1fr))}}@media(max-width:560px){header{padding:10px 12px}.logo{height:62px}h1{font-size:15px}.intro{display:block}.intro .badge{margin-top:12px}.cards{grid-template-columns:1fr}main{padding:20px 10px 40px}}
"""
    return (
        '<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta name="robots" content="noindex,nofollow"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; img-src data:; style-src \'unsafe-inline\'; base-uri \'none\'; form-action \'none\">'
        '<title>VIA Subsystem Workspaces v0106.4</title><style>' + css + '</style></head><body><header>'
        '<img class="logo" src="data:image/png;base64,' + logo_b64 + '" alt="Veritas Intelligence Analytics"><div class="copy">'
        '<p class="eyebrow">VIA · ARCHITECTURE BASELINE · 2026-11-05 · ENGINE v0103</p><h1>VIA System Architecture &amp; Integration Blueprint</h1><p class="subtitle">Subsystem Workspaces · v0106.4</p></div></header>'
        '<main><section class="intro"><div><h2>六系統獨立工作區</h2><p>唯讀候選證據入口。每個系統畫面以 LAST_MATRIX 原始 system 精確過濾，管理矩陣提供九個原始分類與完整列資料；共享證據另行標示，不混入系統總數。</p><p><a href="governance-preview-v0105.3.html">Global/common governance · existing read-only route</a></p></div><span class="badge">v0106.4 CANDIDATE · ACTUAL RED / BLOCKED</span></section>'
        '<div class="legend"><span>CANDIDATE ≠ FORMAL REGISTRATION</span><span>STATIC AST ≠ RUNTIME COVERAGE</span><span>UPLOADED PASS ≠ THIS-ROUND EXECUTION</span></div><section class="cards" aria-label="Six independent subsystem links">' + ''.join(cards) + '</section></main></body></html>'
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--source", type=Path)
    parser.add_argument("--expected-sha256", default=EXPECTED_SOURCE_SHA256)
    parser.add_argument("--expected-bytes", type=int, default=EXPECTED_SOURCE_BYTES)
    parser.add_argument("--observations", type=Path)
    parser.add_argument("--token-context", type=Path)
    parser.add_argument("--token-tools", type=Path)
    args = parser.parse_args()
    result = build(
        args.root,
        args.source,
        expected_sha256=args.expected_sha256,
        expected_bytes=args.expected_bytes,
        observations_path=args.observations,
        token_context_path=args.token_context,
        token_tools_path=args.token_tools,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
