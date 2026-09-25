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

import argparse
import csv
import ctypes
import datetime as dt
import hashlib
import html
import io
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable


# =============================================================================
# def 00. PARAMETERS / GATES / OWNERS
# =============================================================================

DEF_VERSION = "v0140B-WH1"
DEF_APPROVAL_TOKEN = "VIA_APPROVE_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_READ_ONLY"
DEF_PREDECESSOR_GATE = "VIA_V0140B_CROSS_SUBSYSTEM_SIX_ENGINE_LOCAL_READER_PATH_REPAIR_PROPOSAL_PASS_READY_NO_SYSTEM_MUTATION"
DEF_PASS_GATE = "VIA_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_PASS_HANDLE_EVIDENCE_READY_NO_SYSTEM_MUTATION"
DEF_ALL_FAILED_GATE = "VIA_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_HOLD_ALL_HANDLE_STRATEGIES_FAILED_NO_SYSTEM_MUTATION"
DEF_HYDRATION_GATE = "VIA_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_HOLD_IMPLICIT_HYDRATION_RISK_NO_SYSTEM_MUTATION"
DEF_FAIL_GATE = "VIA_V0140B_WINDOWS_FILE_HANDLE_ACQUISITION_SANDBOX_VALIDATION_HOLD_FAIL_CLOSED"
DEF_SUBSYSTEMS = ("VRN", "VDF", "VAP")
DEF_ENGINE_NAMES = {
    "H01": "ONEDRIVE_ATTRIBUTE_RECALL_PREFLIGHT",
    "H02": "PYTHON_PATHLIB_BINARY_OPEN",
    "H03": "PYTHON_OS_OPEN_BINARY",
    "H04": "WIN32_CREATEFILEW_EXACT",
    "H05": "WIN32_CREATEFILEW_EXTENDED_PATH",
    "H06": "DOTNET_FILESTREAM_EXACT",
}
DEF_WRAPPERS = {
    "H01": "via_v0140b_handle01_onedrive_attribute_recall_preflight.py",
    "H02": "via_v0140b_handle02_python_pathlib_binary_open.py",
    "H03": "via_v0140b_handle03_python_os_open_binary.py",
    "H04": "via_v0140b_handle04_win32_createfilew_exact.py",
    "H05": "via_v0140b_handle05_win32_createfilew_extended_path.py",
    "H06": "via_v0140b_handle06_dotnet_filestream_exact.py",
}
DEF_DOTNET_SCRIPT = "via_v0140b_handle06_dotnet_filestream_exact.ps1"
DEF_EVIDENCE_FIELDS = (
    "ENGINE_ID", "EVIDENCE_ID", "DIMENSION", "STATUS", "CHECK", "OBSERVED",
    "EXPECTED", "SOURCE_OPEN_ATTEMPTS", "SOURCE_OPEN_SUCCESSES", "SOURCE_BYTES_READ",
)
DEF_FINDING_FIELDS = (
    "ENGINE_ID", "FINDING_ID", "SEVERITY", "BLOCKING", "CLASSIFICATION",
    "FINDING", "EVIDENCE", "RISK", "LIKELY_CAUSE", "REMEDIATION",
)
DEF_SUBSYSTEM_FIELDS = (
    "ENGINE_ID", "ENGINE_NAME", "SUBSYSTEM", "STATUS", "HANDLE_STRATEGY",
    "OUTCOME", "APPLICABILITY", "HYDRA_BOUNDARY", "OUTPUT_OWNER",
)
DEF_ENGINE_FIELDS = (
    "SEQUENCE_INDEX", "ENGINE_ID", "ENGINE_NAME", "STATUS", "TERMINAL", "OUTCOME",
    "CONTENT_READ_AUTHORIZED", "SOURCE_METADATA_READS", "SOURCE_OPEN_ATTEMPTS",
    "SOURCE_OPEN_SUCCESSES", "SOURCE_BYTES_READ", "SOURCE_HASHES", "SOURCE_WRITES",
    "SOURCE_COPIES", "SOURCE_CONTENT_ARTIFACTS", "NETWORK_REQUESTS",
    "CANONICAL_RUNTIME", "REGISTRY_WRITES", "EXISTING_MUTATION",
    "PATCH_APPLICATIONS", "CANDIDATE_PROMOTIONS", "HYDRATION_RISK",
    "LANE_ROOT", "SUMMARY_SHA256",
)


# =============================================================================
# def 01. ATOMIC RUN-LOCAL OUTPUT / SERIALIZATION
# =============================================================================

def def_utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def def_text(def_value: Any) -> str:
    if def_value is None:
        return ""
    if isinstance(def_value, (dict, list, tuple)):
        return json.dumps(def_value, ensure_ascii=False, sort_keys=True, default=str)
    return str(def_value)


def def_sha256_file(def_path: Path) -> str:
    def_hash = hashlib.sha256()
    with def_path.open("rb") as def_file:
        while True:
            def_chunk = def_file.read(1024 * 1024)
            if not def_chunk:
                break
            def_hash.update(def_chunk)
    return def_hash.hexdigest()


def def_write_bytes_atomic(def_path: Path, def_payload: bytes) -> None:
    def_path.parent.mkdir(parents=True, exist_ok=True)
    def_temp = def_path.with_name(f".{def_path.name}.{os.getpid()}.tmp")
    with def_temp.open("wb") as def_file:
        def_file.write(def_payload)
        def_file.flush()
        os.fsync(def_file.fileno())
    os.replace(def_temp, def_path)


def def_write_json_atomic(def_path: Path, def_data: Any) -> None:
    def_write_bytes_atomic(
        def_path,
        json.dumps(def_data, ensure_ascii=False, indent=2, sort_keys=True, default=str).encode("utf-8"),
    )


def def_write_csv_atomic(def_path: Path, def_rows: list[dict[str, Any]], def_fields: tuple[str, ...]) -> None:
    def_buffer = io.StringIO(newline="")
    def_writer = csv.DictWriter(def_buffer, fieldnames=list(def_fields), extrasaction="ignore", lineterminator="\n")
    def_writer.writeheader()
    for def_row in def_rows:
        def_writer.writerow({def_field: def_text(def_row.get(def_field)) for def_field in def_fields})
    def_write_bytes_atomic(def_path, ("\ufeff" + def_buffer.getvalue()).encode("utf-8"))


def def_write_parquet_atomic(def_path: Path, def_rows: list[dict[str, Any]], def_fields: tuple[str, ...]) -> None:
    try:
        import pyarrow as def_pa
        import pyarrow.parquet as def_pq
    except Exception as def_error:
        if os.environ.get("VIA_ALLOW_PARQUET_UNAVAILABLE_FOR_PACKAGE_TEST") == "1":
            def_write_json_atomic(
                def_path.with_suffix(def_path.suffix + ".unavailable.json"),
                {"status": "PACKAGE_TEST_ONLY_PYARROW_UNAVAILABLE", "error": str(def_error)},
            )
            return
        raise RuntimeError(f"Governed PyArrow is required for paired CSV/Parquet output: {def_error}") from def_error
    def_columns = {def_field: [def_text(def_row.get(def_field)) for def_row in def_rows] for def_field in def_fields}
    def_table = (
        def_pa.table(def_columns)
        if def_rows
        else def_pa.table({def_field: def_pa.array([], type=def_pa.string()) for def_field in def_fields})
    )
    def_path.parent.mkdir(parents=True, exist_ok=True)
    def_temp = def_path.with_name(f".{def_path.name}.{os.getpid()}.tmp")
    def_pq.write_table(def_table, def_temp, compression="zstd")
    os.replace(def_temp, def_path)


def def_read_json(def_path: Path, def_maximum_bytes: int = 25_000_000) -> Any:
    def_payload = def_path.read_bytes()
    if len(def_payload) > def_maximum_bytes:
        raise ValueError(f"JSON exceeds byte bound: {def_path}")
    return json.loads(def_payload.decode("utf-8-sig"))


def def_read_csv(def_path: Path) -> list[dict[str, str]]:
    with def_path.open("r", encoding="utf-8-sig", newline="") as def_file:
        return list(csv.DictReader(def_file))


# =============================================================================
# def 02. ARGUMENT / CONTRACT / PREDECESSOR
# =============================================================================

def def_parse_args() -> argparse.Namespace:
    def_parser = argparse.ArgumentParser(description="VIA v0140B Windows handle acquisition")
    def_parser.add_argument("--lane", choices=sorted(DEF_ENGINE_NAMES))
    def_parser.add_argument("--aggregate", action="store_true")
    def_parser.add_argument("--run-dir", default="")
    def_parser.add_argument("--lane-root", default="")
    def_parser.add_argument("--package-root", required=True)
    def_parser.add_argument("--contract", required=True)
    def_parser.add_argument("--rules", required=True)
    def_parser.add_argument("--source-path", default="")
    def_parser.add_argument("--predecessor-run-dir", default="")
    def_parser.add_argument("--approval-token", required=True)
    def_parser.add_argument("--sequence-index", type=int, default=0)
    def_parser.add_argument("--content-read-authorized", choices=("true", "false"), default="false")
    def_parser.add_argument("--pwsh-path", default="")
    def_parser.add_argument("--self-test", action="store_true")
    return def_parser.parse_args()


def def_validate_contract(def_args: argparse.Namespace) -> tuple[dict[str, Any], dict[str, Any]]:
    def_contract = def_read_json(Path(def_args.contract))
    def_rules = def_read_json(Path(def_args.rules))
    if def_args.approval_token != DEF_APPROVAL_TOKEN:
        raise PermissionError("Approval token mismatch.")
    if def_contract.get("approval_token") != DEF_APPROVAL_TOKEN:
        raise ValueError("Contract token mismatch.")
    if def_contract.get("predecessor_gate") != DEF_PREDECESSOR_GATE:
        raise ValueError("Predecessor gate mismatch.")
    if [def_item["id"] for def_item in def_contract["engines"]] != list(DEF_ENGINE_NAMES):
        raise ValueError("Six-engine identity/order mismatch.")
    if def_contract["coordination_model"]["execution"] != "SEQUENTIAL_POWERSHELL7_PROCESS_ISOLATION":
        raise ValueError("Sequential execution is required.")
    if tuple(def_rules["expected_subsystems"]) != DEF_SUBSYSTEMS:
        raise ValueError("Subsystem contract mismatch.")
    if def_rules["maximum_parallel_content_opens"] != 1:
        raise ValueError("Maximum parallel content opens must be one.")
    return def_contract, def_rules


def def_validate_predecessor(def_path_text: str, def_self_test: bool) -> dict[str, Any]:
    if def_self_test:
        return {"final_gate": DEF_PREDECESSOR_GATE, "self_test": True}
    if not def_path_text:
        raise FileNotFoundError("Predecessor run directory is required.")
    def_path = Path(def_path_text)
    for def_name in (
        "VIA_v0140B_LOCAL_READER_PATH_PROPOSAL_FORMAL_RECORD.json",
        "VIA_v0140B_LocalReaderPath_Summary.json",
    ):
        def_candidate = def_path / def_name
        if not def_candidate.is_file():
            continue
        def_record = def_read_json(def_candidate)
        if (
            def_record.get("final_gate") == DEF_PREDECESSOR_GATE
            and int(def_record.get("hydra_violations", -1)) == 0
            and int(def_record.get("source_writes", -1)) == 0
            and int(def_record.get("canonical_runtime_executions", -1)) == 0
            and int(def_record.get("patch_applications", -1)) == 0
        ):
            return def_record
    raise ValueError("Accepted local-reader proposal predecessor not found.")


# =============================================================================
# def 03. EVIDENCE HELPERS / NON-PERSISTENT BUFFER PROFILE
# =============================================================================

def def_add_evidence(
    def_rows: list[dict[str, Any]],
    def_engine: str,
    def_id: str,
    def_dimension: str,
    def_status: str,
    def_check: str,
    def_observed: Any,
    def_expected: Any,
    def_attempts: int = 0,
    def_successes: int = 0,
    def_bytes: int = 0,
) -> None:
    def_rows.append({
        "ENGINE_ID": def_engine,
        "EVIDENCE_ID": def_id,
        "DIMENSION": def_dimension,
        "STATUS": def_status,
        "CHECK": def_check,
        "OBSERVED": def_observed,
        "EXPECTED": def_expected,
        "SOURCE_OPEN_ATTEMPTS": def_attempts,
        "SOURCE_OPEN_SUCCESSES": def_successes,
        "SOURCE_BYTES_READ": def_bytes,
    })


def def_add_finding(
    def_rows: list[dict[str, Any]],
    def_engine: str,
    def_id: str,
    def_severity: str,
    def_blocking: bool,
    def_classification: str,
    def_finding: str,
    def_evidence: Any,
    def_risk: str,
    def_cause: str,
    def_remediation: str,
) -> None:
    def_rows.append({
        "ENGINE_ID": def_engine,
        "FINDING_ID": def_id,
        "SEVERITY": def_severity,
        "BLOCKING": def_blocking,
        "CLASSIFICATION": def_classification,
        "FINDING": def_finding,
        "EVIDENCE": def_evidence,
        "RISK": def_risk,
        "LIKELY_CAUSE": def_cause,
        "REMEDIATION": def_remediation,
    })


def def_buffer_profile(def_payload: bytes) -> dict[str, Any]:
    def_bom = "NONE"
    if def_payload.startswith(b"\xef\xbb\xbf"):
        def_bom = "UTF8"
    elif def_payload.startswith(b"\xff\xfe"):
        def_bom = "UTF16_LE"
    elif def_payload.startswith(b"\xfe\xff"):
        def_bom = "UTF16_BE"
    return {
        "bytes_read": len(def_payload),
        "bom": def_bom,
        "newline_count": def_payload.count(b"\n"),
        "comma_count": def_payload.count(b","),
        "contains_nul": b"\x00" in def_payload,
        "raw_content_persisted": False,
        "content_hash_computed": False,
    }


def def_subsystem_rows(
    def_engine: str,
    def_status: str,
    def_strategy: str,
    def_outcome: str,
    def_lane_root: Path,
) -> list[dict[str, Any]]:
    def_applicability = {
        "VRN": "Document/table ingestion can use the validated handle strategy through a common read-only adapter.",
        "VDF": "CSV ingestion can receive an in-memory bounded buffer from the validated handle strategy.",
        "VAP": "Visualization remains downstream of a normalized in-memory table and never opens the candidate directly.",
    }
    return [{
        "ENGINE_ID": def_engine,
        "ENGINE_NAME": DEF_ENGINE_NAMES[def_engine],
        "SUBSYSTEM": def_subsystem,
        "STATUS": def_status,
        "HANDLE_STRATEGY": def_strategy,
        "OUTCOME": def_outcome,
        "APPLICABILITY": def_applicability[def_subsystem],
        "HYDRA_BOUNDARY": "SEQUENTIAL; RUN_LOCAL METADATA ONLY; NO SOURCE CONTENT ARTIFACT",
        "OUTPUT_OWNER": str(def_lane_root),
    } for def_subsystem in DEF_SUBSYSTEMS]


def def_probe_result(
    def_outcome: str,
    def_attempts: int,
    def_successes: int,
    def_bytes: int,
    def_profile: dict[str, Any] | None = None,
    def_error: str = "",
    def_errno: int | None = None,
    def_winerror: int | None = None,
) -> dict[str, Any]:
    return {
        "outcome": def_outcome,
        "source_open_attempts": def_attempts,
        "source_open_successes": def_successes,
        "source_bytes_read": def_bytes,
        "buffer_profile": def_profile or {},
        "error": def_error,
        "errno": def_errno,
        "winerror": def_winerror,
        "source_hashes": 0,
        "source_writes": 0,
        "source_copies": 0,
        "source_content_artifacts": 0,
    }


def def_validate_content_probe_result(def_result: dict[str, Any], def_maximum_bytes: int) -> None:
    def_attempts = int(def_result.get("source_open_attempts", -1))
    def_successes = int(def_result.get("source_open_successes", -1))
    def_bytes = int(def_result.get("source_bytes_read", -1))
    if def_attempts not in (0, 1):
        raise ValueError("Content probe attempt count is outside 0..1.")
    if def_successes not in (0, 1) or def_successes > def_attempts:
        raise ValueError("Content probe success count is inconsistent with attempts.")
    if def_bytes < 0 or def_bytes > def_maximum_bytes:
        raise ValueError("Content probe byte count exceeds its bounded buffer.")
    if def_bytes > 0 and def_successes != 1:
        raise ValueError("Positive source bytes require a successful source open.")
    for def_field in (
        "source_hashes", "source_writes", "source_copies", "source_content_artifacts",
    ):
        if int(def_result.get(def_field, -1)) != 0:
            raise ValueError(f"Content probe violated zero-effect field: {def_field}")
    def_profile = def_result.get("buffer_profile") or {}
    if def_profile:
        if bool(def_profile.get("raw_content_persisted", True)):
            raise ValueError("Content probe persisted raw source content.")
        if bool(def_profile.get("content_hash_computed", True)):
            raise ValueError("Content probe computed a source-content hash.")
        if int(def_profile.get("bytes_read", -1)) != def_bytes:
            raise ValueError("Buffer profile bytes do not match source_bytes_read.")


# =============================================================================
# def 04. H01 ONEDRIVE / FILE ATTRIBUTE PREFLIGHT
# =============================================================================

def def_decode_file_attributes(def_value: int, def_rules: dict[str, Any]) -> list[str]:
    return [
        def_name
        for def_name, def_mask in def_rules["windows_file_attributes"].items()
        if def_value & int(def_mask)
    ]


def def_attribute_profile(def_path_text: str, def_rules: dict[str, Any]) -> dict[str, Any]:
    def_profile: dict[str, Any] = {
        "path_repr": repr(def_path_text),
        "platform": platform.system(),
        "exists": False,
        "is_file": False,
        "file_attributes_value": 0,
        "file_attributes": [],
        "reparse_tag": None,
        "metadata_error": "",
        "content_read_safe": False,
        "implicit_hydration_risk": False,
    }
    try:
        def_path = Path(def_path_text)
        def_stat = os.lstat(def_path)
        def_profile["exists"] = True
        def_profile["is_file"] = def_path.is_file()
        def_profile["bytes"] = int(def_stat.st_size)
        def_profile["modified_utc"] = dt.datetime.fromtimestamp(def_stat.st_mtime, tz=dt.timezone.utc).isoformat()
        def_attributes = int(getattr(def_stat, "st_file_attributes", 0))
        if os.name == "nt":
            def_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            def_kernel32.GetFileAttributesW.argtypes = [ctypes.c_wchar_p]
            def_kernel32.GetFileAttributesW.restype = ctypes.c_uint32
            def_native = int(def_kernel32.GetFileAttributesW(def_path_text))
            if def_native != 0xFFFFFFFF:
                def_attributes = def_native
        def_profile["file_attributes_value"] = def_attributes
        def_profile["file_attributes"] = def_decode_file_attributes(def_attributes, def_rules)
        def_profile["reparse_tag"] = getattr(def_stat, "st_reparse_tag", None)
        def_block = set(def_rules["implicit_hydration_block_flags"])
        def_detected = sorted(def_block.intersection(def_profile["file_attributes"]))
        def_profile["blocking_recall_flags"] = def_detected
        def_profile["implicit_hydration_risk"] = bool(def_detected)
        def_profile["content_read_safe"] = bool(def_profile["is_file"] and not def_detected)
    except Exception as def_error:
        def_profile["metadata_error"] = f"{type(def_error).__name__}: {def_error}"
        def_profile["errno"] = getattr(def_error, "errno", None)
        def_profile["winerror"] = getattr(def_error, "winerror", None)
    return def_profile


def def_engine01(def_context: dict[str, Any]) -> tuple[str, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    def_profile = def_attribute_profile(def_context["source_path"], def_context["rules"])
    def_outcome = (
        "PREFLIGHT_SAFE"
        if def_profile["content_read_safe"]
        else "PREFLIGHT_BLOCKED_IMPLICIT_HYDRATION_RISK"
        if def_profile["implicit_hydration_risk"]
        else "PREFLIGHT_METADATA_INSUFFICIENT"
    )
    def_evidence: list[dict[str, Any]] = []
    def_findings: list[dict[str, Any]] = []
    def_add_evidence(
        def_evidence, "H01", "H01_C01", "FILE_ATTRIBUTES", "PASS",
        "Content-open guard is decided before any source open", def_profile,
        "No OFFLINE/RECALL flag and regular file", 0, 0, 0,
    )
    if def_profile["implicit_hydration_risk"]:
        def_add_finding(
            def_findings, "H01", "H01_F01", "HIGH", True,
            "IMPLICIT_HYDRATION_RISK", "OneDrive recall/offline attributes prohibit content open.",
            def_profile, "A nominal read could change local hydration state.",
            "Files On-Demand placeholder or recall-on-access state.",
            "Stop at HOLD and request manual OneDrive state review; do not pin, hydrate, copy, or open content.",
        )
    elif not def_profile["content_read_safe"]:
        def_add_finding(
            def_findings, "H01", "H01_F02", "HIGH", True,
            "METADATA_PREFLIGHT_INSUFFICIENT", "Safe content-open eligibility cannot be proven.",
            def_profile, "Handle probes could act on the wrong or unavailable object.",
            "Missing path, metadata error, or non-file candidate.",
            "Resolve the exact local candidate metadata before any content open.",
        )
    def_result = def_probe_result(def_outcome, 0, 0, 0)
    def_result.update({
        "source_metadata_reads": 1,
        "content_read_safe": def_profile["content_read_safe"],
        "implicit_hydration_risk": def_profile["implicit_hydration_risk"],
        "attribute_profile": def_profile,
    })
    return "PASS", def_result, def_evidence, def_findings


# =============================================================================
# def 05. H02/H03 PYTHON OPEN STRATEGIES
# =============================================================================

def def_guarded_skip() -> dict[str, Any]:
    return def_probe_result("SKIPPED_IMPLICIT_HYDRATION_OR_PREFLIGHT_RISK", 0, 0, 0)


def def_probe_pathlib(def_path_text: str, def_maximum_bytes: int, def_authorized: bool) -> dict[str, Any]:
    if not def_authorized:
        return def_guarded_skip()
    try:
        with Path(def_path_text).open("rb") as def_file:
            def_payload = def_file.read(def_maximum_bytes)
        return def_probe_result("OPEN_SUCCESS", 1, 1, len(def_payload), def_buffer_profile(def_payload))
    except OSError as def_error:
        return def_probe_result(
            "OPEN_FAILED", 1, 0, 0, def_error=f"{type(def_error).__name__}: {def_error}",
            def_errno=getattr(def_error, "errno", None), def_winerror=getattr(def_error, "winerror", None),
        )


def def_probe_os_open(def_path_text: str, def_maximum_bytes: int, def_authorized: bool) -> dict[str, Any]:
    if not def_authorized:
        return def_guarded_skip()
    def_fd = None
    try:
        def_flags = os.O_RDONLY | getattr(os, "O_BINARY", 0)
        def_fd = os.open(def_path_text, def_flags)
        def_payload = os.read(def_fd, def_maximum_bytes)
        return def_probe_result("OPEN_SUCCESS", 1, 1, len(def_payload), def_buffer_profile(def_payload))
    except OSError as def_error:
        return def_probe_result(
            "OPEN_FAILED", 1, 0, 0, def_error=f"{type(def_error).__name__}: {def_error}",
            def_errno=getattr(def_error, "errno", None), def_winerror=getattr(def_error, "winerror", None),
        )
    finally:
        if def_fd is not None:
            os.close(def_fd)


# =============================================================================
# def 06. H04/H05 WIN32 CREATEFILEW
# =============================================================================

def def_extended_windows_path(def_path_text: str) -> str:
    if def_path_text.startswith("\\\\?\\"):
        return def_path_text
    if def_path_text.startswith("\\\\"):
        return "\\\\?\\UNC\\" + def_path_text[2:]
    return "\\\\?\\" + os.path.abspath(def_path_text)


def def_win32_message(def_code: int) -> str:
    try:
        return ctypes.FormatError(def_code).strip()
    except Exception:
        return f"Win32 error {def_code}"


def def_probe_createfilew(
    def_path_text: str,
    def_maximum_bytes: int,
    def_authorized: bool,
    def_extended: bool,
) -> dict[str, Any]:
    if not def_authorized:
        return def_guarded_skip()
    if os.name != "nt":
        return def_probe_result("UNAVAILABLE_NON_WINDOWS_PACKAGE_TEST", 0, 0, 0)
    def_handle = None
    try:
        def_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        def_kernel32.CreateFileW.argtypes = [
            ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
            ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p,
        ]
        def_kernel32.CreateFileW.restype = ctypes.c_void_p
        def_kernel32.ReadFile.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32,
            ctypes.POINTER(ctypes.c_uint32), ctypes.c_void_p,
        ]
        def_kernel32.ReadFile.restype = ctypes.c_int
        def_kernel32.CloseHandle.argtypes = [ctypes.c_void_p]
        def_kernel32.CloseHandle.restype = ctypes.c_int
        def_effective = def_extended_windows_path(def_path_text) if def_extended else def_path_text
        def_handle = def_kernel32.CreateFileW(
            def_effective,
            0x80000000,
            0x00000001 | 0x00000002 | 0x00000004,
            None,
            3,
            0x00000080 | 0x08000000,
            None,
        )
        def_invalid = ctypes.c_void_p(-1).value
        if def_handle == def_invalid or def_handle is None:
            def_code = ctypes.get_last_error()
            return def_probe_result(
                "OPEN_FAILED", 1, 0, 0,
                def_error=def_win32_message(def_code), def_winerror=def_code,
            )
        def_buffer = ctypes.create_string_buffer(def_maximum_bytes)
        def_read = ctypes.c_uint32(0)
        if not def_kernel32.ReadFile(def_handle, def_buffer, def_maximum_bytes, ctypes.byref(def_read), None):
            def_code = ctypes.get_last_error()
            return def_probe_result(
                "READ_FAILED_AFTER_OPEN", 1, 1, 0,
                def_error=def_win32_message(def_code), def_winerror=def_code,
            )
        def_payload = bytes(def_buffer.raw[: def_read.value])
        return def_probe_result("OPEN_SUCCESS", 1, 1, len(def_payload), def_buffer_profile(def_payload))
    except Exception as def_error:
        return def_probe_result(
            "PROBE_EXCEPTION", 1, 0, 0, def_error=f"{type(def_error).__name__}: {def_error}",
            def_errno=getattr(def_error, "errno", None), def_winerror=getattr(def_error, "winerror", None),
        )
    finally:
        if def_handle not in (None, ctypes.c_void_p(-1).value):
            try:
                def_kernel32.CloseHandle(def_handle)
            except Exception:
                pass


# =============================================================================
# def 07. H06 .NET FILESTREAM VIA STATIC POWERSHELL SCRIPT
# =============================================================================

def def_probe_dotnet(
    def_path_text: str,
    def_maximum_bytes: int,
    def_authorized: bool,
    def_pwsh_path: str,
    def_package_root: Path,
    def_lane_root: Path,
) -> dict[str, Any]:
    if not def_authorized:
        return def_guarded_skip()
    def_pwsh = def_pwsh_path or shutil.which("pwsh") or ""
    if not def_pwsh:
        return def_probe_result("UNAVAILABLE_POWERSHELL_PACKAGE_TEST", 0, 0, 0)
    def_result_path = def_lane_root / "H06_DOTNET_RESULT.json"
    def_command = [
        def_pwsh,
        "-NoProfile",
        "-NonInteractive",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(def_package_root / DEF_DOTNET_SCRIPT),
        "-SourcePath",
        def_path_text,
        "-MaximumBytes",
        str(def_maximum_bytes),
        "-OutputPath",
        str(def_result_path),
        "-ContentReadAuthorized",
        "true",
    ]
    def_process = subprocess.run(def_command, text=True, capture_output=True, check=False)
    if not def_result_path.is_file():
        return def_probe_result(
            "DOTNET_PROCESS_FAILED", 1, 0, 0,
            def_error=f"exit={def_process.returncode}; stderr={def_process.stderr[:500]}",
        )
    def_result = def_read_json(def_result_path)
    def_result["dotnet_process_exit_code"] = def_process.returncode
    return def_result


# =============================================================================
# def 08. COMMON CONTENT ENGINE / DISPATCH
# =============================================================================

def def_content_engine(
    def_engine: str,
    def_context: dict[str, Any],
    def_probe: Callable[[], dict[str, Any]],
) -> tuple[str, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    def_result = def_probe()
    def_validate_content_probe_result(def_result, def_context["maximum_bytes"])
    def_evidence: list[dict[str, Any]] = []
    def_findings: list[dict[str, Any]] = []
    def_add_evidence(
        def_evidence, def_engine, f"{def_engine}_C01", "HANDLE_ACQUISITION", "PASS",
        DEF_ENGINE_NAMES[def_engine], def_result,
        "One or zero guarded attempt; no raw content/hash/write/copy",
        int(def_result["source_open_attempts"]),
        int(def_result["source_open_successes"]),
        int(def_result["source_bytes_read"]),
    )
    if def_result["outcome"] in {"OPEN_FAILED", "READ_FAILED_AFTER_OPEN", "PROBE_EXCEPTION", "DOTNET_PROCESS_FAILED"}:
        def_add_finding(
            def_findings, def_engine, f"{def_engine}_F01", "HIGH", False,
            def_result["outcome"], f"{DEF_ENGINE_NAMES[def_engine]} did not acquire readable bytes.",
            def_result, "This strategy cannot support a reader patch on the current source state.",
            "Windows handle semantics, OneDrive state, path form, sharing flags, or runtime-specific boundary.",
            "Retain the failure and compare with later sequential strategies; do not retry automatically.",
        )
    elif def_result["outcome"].startswith("SKIPPED"):
        def_add_finding(
            def_findings, def_engine, f"{def_engine}_F02", "HIGH", False,
            "IMPLICIT_HYDRATION_GUARD", "Probe was skipped because preflight did not authorize content open.",
            def_result, "Opening could alter OneDrive hydration state.",
            "OFFLINE/RECALL attribute or insufficient metadata.",
            "Keep source untouched and route to manual OneDrive state review.",
        )
    def_result.setdefault("source_metadata_reads", 0)
    def_result.setdefault("content_read_safe", def_context["content_read_authorized"])
    def_result.setdefault("implicit_hydration_risk", not def_context["content_read_authorized"])
    return "PASS", def_result, def_evidence, def_findings


def def_engine02(def_context: dict[str, Any]) -> tuple[str, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    return def_content_engine(
        "H02", def_context,
        lambda: def_probe_pathlib(def_context["source_path"], def_context["maximum_bytes"], def_context["content_read_authorized"]),
    )


def def_engine03(def_context: dict[str, Any]) -> tuple[str, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    return def_content_engine(
        "H03", def_context,
        lambda: def_probe_os_open(def_context["source_path"], def_context["maximum_bytes"], def_context["content_read_authorized"]),
    )


def def_engine04(def_context: dict[str, Any]) -> tuple[str, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    return def_content_engine(
        "H04", def_context,
        lambda: def_probe_createfilew(def_context["source_path"], def_context["maximum_bytes"], def_context["content_read_authorized"], False),
    )


def def_engine05(def_context: dict[str, Any]) -> tuple[str, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    return def_content_engine(
        "H05", def_context,
        lambda: def_probe_createfilew(def_context["source_path"], def_context["maximum_bytes"], def_context["content_read_authorized"], True),
    )


def def_engine06(def_context: dict[str, Any]) -> tuple[str, dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    return def_content_engine(
        "H06", def_context,
        lambda: def_probe_dotnet(
            def_context["source_path"], def_context["maximum_bytes"], def_context["content_read_authorized"],
            def_context["pwsh_path"], def_context["package_root"], def_context["lane_root"],
        ),
    )


DEF_ENGINE_FUNCTIONS = {
    "H01": def_engine01,
    "H02": def_engine02,
    "H03": def_engine03,
    "H04": def_engine04,
    "H05": def_engine05,
    "H06": def_engine06,
}


# =============================================================================
# def 09. TERMINAL SUMMARY WRITER / LANE ENTRY
# =============================================================================

def def_write_lane(
    def_engine: str,
    def_lane_root: Path,
    def_sequence_index: int,
    def_status: str,
    def_result: dict[str, Any],
    def_evidence: list[dict[str, Any]],
    def_findings: list[dict[str, Any]],
    def_error: str = "",
) -> dict[str, Any]:
    def_subsystems = def_subsystem_rows(
        def_engine, def_status, DEF_ENGINE_NAMES[def_engine], def_result.get("outcome", ""), def_lane_root,
    )
    def_write_json_atomic(def_lane_root / "PROBE_RESULT.json", def_result)
    def_write_csv_atomic(def_lane_root / "ENGINE_EVIDENCE.csv", def_evidence, DEF_EVIDENCE_FIELDS)
    def_write_parquet_atomic(def_lane_root / "ENGINE_EVIDENCE.parquet", def_evidence, DEF_EVIDENCE_FIELDS)
    def_write_csv_atomic(def_lane_root / "ENGINE_FINDINGS.csv", def_findings, DEF_FINDING_FIELDS)
    def_write_csv_atomic(def_lane_root / "ENGINE_SUBSYSTEM_MATRIX.csv", def_subsystems, DEF_SUBSYSTEM_FIELDS)
    def_write_parquet_atomic(def_lane_root / "ENGINE_SUBSYSTEM_MATRIX.parquet", def_subsystems, DEF_SUBSYSTEM_FIELDS)
    def_summary = {
        "schema": "VIA_V0140B_WINDOWS_HANDLE_ENGINE_TERMINAL_V1",
        "version": DEF_VERSION,
        "sequence_index": def_sequence_index,
        "engine_id": def_engine,
        "engine_name": DEF_ENGINE_NAMES[def_engine],
        "status": def_status,
        "terminal": True,
        "outcome": def_result.get("outcome", "FAIL_CLOSED"),
        "content_read_authorized": bool(def_result.get("content_read_safe", False)),
        "source_metadata_reads": int(def_result.get("source_metadata_reads", 0)),
        "source_open_attempts": int(def_result.get("source_open_attempts", 0)),
        "source_open_successes": int(def_result.get("source_open_successes", 0)),
        "source_bytes_read": int(def_result.get("source_bytes_read", 0)),
        "source_hashes": 0,
        "source_writes": 0,
        "source_copies": 0,
        "source_content_artifacts": 0,
        "network_requests": 0,
        "canonical_runtime": 0,
        "registry_writes": 0,
        "existing_mutation": 0,
        "patch_applications": 0,
        "candidate_promotions": 0,
        "hydration_risk": bool(def_result.get("implicit_hydration_risk", False)),
        "subsystem_rows": len(def_subsystems),
        "findings": len(def_findings),
        "lane_root": str(def_lane_root),
        "error": def_error,
        "generated_utc": def_utc_now(),
    }
    def_write_json_atomic(def_lane_root / "TERMINAL_SUMMARY.json", def_summary)
    return def_summary


def def_run_lane(def_args: argparse.Namespace) -> int:
    if not def_args.lane or not def_args.lane_root:
        raise ValueError("--lane and --lane-root are required.")
    def_lane_root = Path(def_args.lane_root).resolve()
    def_lane_root.mkdir(parents=True, exist_ok=True)
    try:
        def_contract, def_rules = def_validate_contract(def_args)
        def_validate_predecessor(def_args.predecessor_run_dir, def_args.self_test)
        if def_args.sequence_index != list(DEF_ENGINE_NAMES).index(def_args.lane) + 1:
            raise ValueError("Engine sequence index mismatch.")
        def_context = {
            "contract": def_contract,
            "rules": def_rules,
            "source_path": def_args.source_path,
            "package_root": Path(def_args.package_root).resolve(),
            "lane_root": def_lane_root,
            "maximum_bytes": int(def_rules["maximum_bytes_per_successful_probe"]),
            "content_read_authorized": def_args.content_read_authorized == "true",
            "pwsh_path": def_args.pwsh_path,
            "self_test": def_args.self_test,
        }
        def_status, def_result, def_evidence, def_findings = DEF_ENGINE_FUNCTIONS[def_args.lane](def_context)
        def_summary = def_write_lane(
            def_args.lane, def_lane_root, def_args.sequence_index,
            def_status, def_result, def_evidence, def_findings,
        )
        print(f"def Handle Engine : {def_args.lane}_{def_summary['outcome']}")
        return 0 if def_status == "PASS" else 2
    except Exception as def_error:
        def_result = def_probe_result("FAIL_CLOSED", 0, 0, 0, def_error=f"{type(def_error).__name__}: {def_error}")
        def_result.update({"content_read_safe": False, "implicit_hydration_risk": False})
        def_findings: list[dict[str, Any]] = []
        def_add_finding(
            def_findings, def_args.lane, f"{def_args.lane}_FAIL_CLOSED", "CRITICAL", True,
            "ENGINE_FAIL_CLOSED", "Engine failed before valid terminal evidence.",
            def_result, "Handle evidence is not trustworthy.", "Package/input/runtime contract failure.",
            "Repair run-local package evidence only; do not retry source open automatically.",
        )
        def_write_lane(
            def_args.lane, def_lane_root, def_args.sequence_index,
            "FAIL", def_result, [], def_findings, f"{type(def_error).__name__}: {def_error}",
        )
        print(f"def Handle Engine : {def_args.lane}_FAIL_CLOSED", file=sys.stderr)
        return 2


# =============================================================================
# def 10. AGGREGATE / GATE / HTML
# =============================================================================

def def_html_table(def_rows: list[dict[str, Any]], def_fields: tuple[str, ...]) -> str:
    def_head = "".join(f"<th>{html.escape(def_field)}</th>" for def_field in def_fields)
    def_body = "".join(
        "<tr>" + "".join(f"<td>{html.escape(def_text(def_row.get(def_field)))}</td>" for def_field in def_fields) + "</tr>"
        for def_row in def_rows
    )
    if not def_body:
        def_body = f"<tr><td colspan='{len(def_fields)}'>No rows</td></tr>"
    return f"<div class='table-wrap'><table><thead><tr>{def_head}</tr></thead><tbody>{def_body}</tbody></table></div>"


def def_write_report(
    def_path: Path,
    def_summary: dict[str, Any],
    def_engines: list[dict[str, Any]],
    def_subsystems: list[dict[str, Any]],
    def_findings: list[dict[str, Any]],
) -> None:
    def_cards = (
        ("Engines", "6/6"),
        ("Open Attempts", def_summary["source_open_attempts"]),
        ("Successes", def_summary["source_open_successes"]),
        ("Bytes Read", def_summary["source_bytes_read"]),
        ("Hydration Risk", int(def_summary["implicit_hydration_risk_detected"])),
        ("Hydra", def_summary["hydra_violations"]),
    )
    def_cards_html = "".join(
        f"<article><span>{html.escape(str(def_label))}</span><b>{html.escape(str(def_value))}</b></article>"
        for def_label, def_value in def_cards
    )
    def_document = f"""<!doctype html><html lang='zh-Hant'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>VIA v0140B Windows Handle Validation</title><style>
    :root{{--bg:#06101c;--panel:#0c1929;--ink:#e8f0f7;--muted:#91a5ba;--line:#243a52;--cyan:#43d6df;--amber:#f2bb50}}
    *{{box-sizing:border-box}}body{{margin:0;background:linear-gradient(135deg,#050e18,#091625 55%,#0d1928);color:var(--ink);font:11px/1.46 Inter,'Noto Sans TC','Segoe UI',sans-serif}}main{{max-width:1580px;margin:auto;padding:22px}}header{{background:rgba(12,25,41,.94);border:1px solid var(--line);border-radius:16px;padding:20px}}h1{{font-size:19px;letter-spacing:.08em;margin:2px 0}}h2{{font-size:14px;color:var(--cyan);letter-spacing:.08em;text-transform:uppercase;margin:24px 0 8px}}.muted{{color:var(--muted)}}.gate{{margin-top:12px;background:#102136;border-left:3px solid var(--amber);padding:9px;font:600 10px/1.45 ui-monospace,Consolas;overflow-wrap:anywhere}}.cards{{display:grid;grid-template-columns:repeat(6,minmax(105px,1fr));gap:8px;margin:13px 0}}article{{background:var(--panel);border:1px solid var(--line);border-radius:10px;padding:11px}}article span{{display:block;color:var(--muted);font-size:9px;text-transform:uppercase}}article b{{font-size:17px}}.table-wrap{{overflow:auto;border:1px solid var(--line);border-radius:10px}}table{{width:100%;border-collapse:collapse;background:rgba(12,25,41,.78)}}th,td{{padding:7px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top;white-space:normal;overflow-wrap:anywhere;max-width:440px}}th{{position:sticky;top:0;background:#14263c;color:#a5dce3;font-size:8px}}td{{font-size:9px}}footer{{color:var(--muted);margin:22px 0}}@media(max-width:900px){{.cards{{grid-template-columns:repeat(2,1fr)}}main{{padding:11px}}}}
    </style></head><body><main><header><div class='muted'>DISCIPLINA • PRUDENTIA • INTEGRITAS</div><h1>VERITAS INTELLIGENCE ANALYTICS</h1><div class='muted'>Windows Handle Acquisition · Sequential Isolation · Hydration Guard · Read Only</div><div class='gate'>{html.escape(def_summary['final_gate'])}</div></header><div class='cards'>{def_cards_html}</div>
    <h2>Technical Summary</h2><p>H01 先判斷 OneDrive OFFLINE／RECALL 屬性；只有 guard 安全時才依序執行五種 handle strategy。Open attempt、open success 與 bytes read 分別計量；沒有任何來源內容被保存或雜湊。</p>
    <h2>ENGINE · Sequential Handle Matrix</h2>{def_html_table(def_engines, DEF_ENGINE_FIELDS)}
    <h2>MODULE · VRN × VDF × VAP Applicability</h2>{def_html_table(def_subsystems, DEF_SUBSYSTEM_FIELDS)}
    <h2>FUNCTION-LIB · Findings</h2>{def_html_table(def_findings, DEF_FINDING_FIELDS)}
    <h2>OTHERS · Zero-Effect Boundary</h2><p>Network 0 · Source hash/write/copy/content-artifact 0/0/0/0 · Canonical/registry 0/0 · Patch/promotion 0/0.</p>
    <footer>Generated UTC {html.escape(def_summary['generated_utc'])}</footer></main></body></html>"""
    def_write_bytes_atomic(def_path, def_document.encode("utf-8"))


def def_run_aggregate(def_args: argparse.Namespace) -> int:
    def_contract, def_rules = def_validate_contract(def_args)
    if not def_args.run_dir:
        raise ValueError("--run-dir is required.")
    def_run_dir = Path(def_args.run_dir).resolve()
    def_engines: list[dict[str, Any]] = []
    def_subsystems: list[dict[str, Any]] = []
    def_findings: list[dict[str, Any]] = []
    def_roots: list[str] = []
    for def_index, def_engine in enumerate(DEF_ENGINE_NAMES, start=1):
        def_lane_root = def_run_dir / "lanes" / f"{def_engine}_{DEF_ENGINE_NAMES[def_engine]}"
        def_summary_path = def_lane_root / "TERMINAL_SUMMARY.json"
        if not def_summary_path.is_file():
            raise FileNotFoundError(f"Terminal summary missing: {def_summary_path}")
        def_summary = def_read_json(def_summary_path)
        if (
            def_summary.get("engine_id") != def_engine
            or not def_summary.get("terminal")
            or int(def_summary.get("sequence_index", 0)) != def_index
        ):
            raise ValueError(f"Invalid terminal/sequence identity: {def_engine}")
        def_roots.append(def_summary["lane_root"])
        def_engines.append({
            "SEQUENCE_INDEX": def_summary["sequence_index"],
            "ENGINE_ID": def_engine,
            "ENGINE_NAME": def_summary["engine_name"],
            "STATUS": def_summary["status"],
            "TERMINAL": def_summary["terminal"],
            "OUTCOME": def_summary["outcome"],
            "CONTENT_READ_AUTHORIZED": def_summary["content_read_authorized"],
            "SOURCE_METADATA_READS": def_summary["source_metadata_reads"],
            "SOURCE_OPEN_ATTEMPTS": def_summary["source_open_attempts"],
            "SOURCE_OPEN_SUCCESSES": def_summary["source_open_successes"],
            "SOURCE_BYTES_READ": def_summary["source_bytes_read"],
            "SOURCE_HASHES": def_summary["source_hashes"],
            "SOURCE_WRITES": def_summary["source_writes"],
            "SOURCE_COPIES": def_summary["source_copies"],
            "SOURCE_CONTENT_ARTIFACTS": def_summary["source_content_artifacts"],
            "NETWORK_REQUESTS": def_summary["network_requests"],
            "CANONICAL_RUNTIME": def_summary["canonical_runtime"],
            "REGISTRY_WRITES": def_summary["registry_writes"],
            "EXISTING_MUTATION": def_summary["existing_mutation"],
            "PATCH_APPLICATIONS": def_summary["patch_applications"],
            "CANDIDATE_PROMOTIONS": def_summary["candidate_promotions"],
            "HYDRATION_RISK": def_summary["hydration_risk"],
            "LANE_ROOT": def_summary["lane_root"],
            "SUMMARY_SHA256": def_sha256_file(def_summary_path),
        })
        def_subsystems.extend(def_read_csv(def_lane_root / "ENGINE_SUBSYSTEM_MATRIX.csv"))
        def_findings.extend(def_read_csv(def_lane_root / "ENGINE_FINDINGS.csv"))
    def_hydra: list[str] = []
    if len(set(def_roots)) != 6:
        def_hydra.append("LANE_ROOT_NOT_UNIQUE")
    if len(def_subsystems) != 18:
        def_hydra.append(f"CROSS_SUBSYSTEM_ROWS:{len(def_subsystems)}")
    def_expected_pairs = {
        (def_engine, def_subsystem)
        for def_engine in DEF_ENGINE_NAMES
        for def_subsystem in DEF_SUBSYSTEMS
    }
    def_observed_pairs = {
        (def_row.get("ENGINE_ID", ""), def_row.get("SUBSYSTEM", ""))
        for def_row in def_subsystems
    }
    if def_observed_pairs != def_expected_pairs:
        def_hydra.append("CROSS_SUBSYSTEM_IDENTITY_SET_MISMATCH")
    for def_engine in def_engines:
        def_expected_lane = (
            def_run_dir / "lanes" / f"{def_engine['ENGINE_ID']}_{DEF_ENGINE_NAMES[def_engine['ENGINE_ID']]}"
        ).resolve()
        if Path(def_engine["LANE_ROOT"]).resolve() != def_expected_lane:
            def_hydra.append(f"LANE_ROOT_MISMATCH:{def_engine['ENGINE_ID']}")
        for def_field in (
            "SOURCE_HASHES", "SOURCE_WRITES", "SOURCE_COPIES", "SOURCE_CONTENT_ARTIFACTS",
            "NETWORK_REQUESTS", "CANONICAL_RUNTIME", "REGISTRY_WRITES",
            "EXISTING_MUTATION", "PATCH_APPLICATIONS", "CANDIDATE_PROMOTIONS",
        ):
            if int(def_engine[def_field]) != 0:
                def_hydra.append(f"ZERO_EFFECT:{def_engine['ENGINE_ID']}:{def_field}")
        if int(def_engine["SOURCE_OPEN_ATTEMPTS"]) > (0 if def_engine["ENGINE_ID"] == "H01" else 1):
            def_hydra.append(f"ATTEMPT_LIMIT:{def_engine['ENGINE_ID']}")
        def_attempt = int(def_engine["SOURCE_OPEN_ATTEMPTS"])
        def_success = int(def_engine["SOURCE_OPEN_SUCCESSES"])
        def_engine_bytes = int(def_engine["SOURCE_BYTES_READ"])
        if def_success < 0 or def_success > def_attempt:
            def_hydra.append(f"SUCCESS_ATTEMPT_INCONSISTENT:{def_engine['ENGINE_ID']}")
        if def_engine_bytes < 0 or def_engine_bytes > int(def_rules["maximum_bytes_per_successful_probe"]):
            def_hydra.append(f"BYTE_BOUND:{def_engine['ENGINE_ID']}")
        if def_engine_bytes > 0 and def_success != 1:
            def_hydra.append(f"BYTES_WITHOUT_SUCCESS:{def_engine['ENGINE_ID']}")
    def_attempts = sum(int(def_engine["SOURCE_OPEN_ATTEMPTS"]) for def_engine in def_engines)
    def_successes = sum(int(def_engine["SOURCE_OPEN_SUCCESSES"]) for def_engine in def_engines)
    def_bytes = sum(int(def_engine["SOURCE_BYTES_READ"]) for def_engine in def_engines)
    if def_attempts > int(def_rules["maximum_content_open_attempts"]):
        def_hydra.append("TOTAL_ATTEMPT_LIMIT")
    def_preflight = def_engines[0]
    def_hydration_risk = bool(def_preflight["HYDRATION_RISK"])
    def_preflight_insufficient = def_preflight["OUTCOME"] == "PREFLIGHT_METADATA_INSUFFICIENT"
    if not bool(def_preflight["CONTENT_READ_AUTHORIZED"]):
        for def_engine in def_engines[1:]:
            if (
                int(def_engine["SOURCE_OPEN_ATTEMPTS"]) != 0
                or int(def_engine["SOURCE_OPEN_SUCCESSES"]) != 0
                or int(def_engine["SOURCE_BYTES_READ"]) != 0
            ):
                def_hydra.append(f"CONTENT_GUARD_BYPASS:{def_engine['ENGINE_ID']}")
    if any(def_engine["STATUS"] != "PASS" for def_engine in def_engines) or def_hydra or def_preflight_insufficient:
        def_gate = DEF_FAIL_GATE
    elif def_hydration_risk:
        def_gate = DEF_HYDRATION_GATE
    elif def_successes < 1 or def_bytes < 1:
        def_gate = DEF_ALL_FAILED_GATE
    else:
        def_gate = DEF_PASS_GATE
    def_first_success = next(
        (def_engine["ENGINE_ID"] for def_engine in def_engines if int(def_engine["SOURCE_OPEN_SUCCESSES"]) > 0),
        "",
    )
    if def_gate == DEF_PASS_GATE:
        def_next_gate = def_contract["next_gate_after_pass"]
    elif def_gate == DEF_HYDRATION_GATE:
        def_next_gate = def_contract["next_gate_after_hydration_risk"]
    else:
        def_next_gate = def_contract["next_gate_after_all_failed"]
    def_summary = {
        "schema": "VIA_V0140B_WINDOWS_HANDLE_AGGREGATE_V1",
        "version": DEF_VERSION,
        "final_gate": def_gate,
        "engine_count": 6,
        "terminal_engines": len(def_engines),
        "pass_engines": sum(def_engine["STATUS"] == "PASS" for def_engine in def_engines),
        "cross_subsystem_rows": len(def_subsystems),
        "source_open_attempts": def_attempts,
        "source_open_successes": def_successes,
        "source_bytes_read": def_bytes,
        "first_success_engine": def_first_success,
        "implicit_hydration_risk_detected": def_hydration_risk,
        "hydra_violations": len(def_hydra),
        "hydra_evidence": def_hydra,
        "network_requests": 0,
        "source_hashes": 0,
        "source_writes": 0,
        "source_copies": 0,
        "source_content_artifacts": 0,
        "canonical_runtime_executions": 0,
        "registry_writes": 0,
        "existing_mutation": 0,
        "patch_applications": 0,
        "candidate_promotions": 0,
        "next_gate": def_next_gate,
        "generated_utc": def_utc_now(),
    }
    def_write_csv_atomic(def_run_dir / "VIA_v0140B_WindowsHandle_EngineMatrix.csv", def_engines, DEF_ENGINE_FIELDS)
    def_write_parquet_atomic(def_run_dir / "VIA_v0140B_WindowsHandle_EngineMatrix.parquet", def_engines, DEF_ENGINE_FIELDS)
    def_write_csv_atomic(def_run_dir / "VIA_v0140B_WindowsHandle_CrossSubsystemMatrix.csv", def_subsystems, DEF_SUBSYSTEM_FIELDS)
    def_write_parquet_atomic(def_run_dir / "VIA_v0140B_WindowsHandle_CrossSubsystemMatrix.parquet", def_subsystems, DEF_SUBSYSTEM_FIELDS)
    def_write_csv_atomic(def_run_dir / "VIA_v0140B_WindowsHandle_Findings.csv", def_findings, DEF_FINDING_FIELDS)
    def_write_json_atomic(def_run_dir / "VIA_v0140B_WindowsHandle_Summary.json", def_summary)
    def_formal = dict(def_summary)
    def_formal.update({
        "approval_token_bound": True,
        "predecessor_gate": DEF_PREDECESSOR_GATE,
        "sequential_execution": True,
        "raw_source_content_persisted": False,
        "source_content_read_metric_deprecated": True,
        "replacement_metrics": [
            "source_open_attempts", "source_open_successes", "source_bytes_read",
        ],
    })
    def_write_json_atomic(def_run_dir / "VIA_v0140B_WINDOWS_HANDLE_FORMAL_RECORD.json", def_formal)
    def_write_report(
        def_run_dir / "VIA_v0140B_WindowsHandle_Report.html",
        def_summary, def_engines, def_subsystems, def_findings,
    )
    print(f"def Gate : {def_gate}")
    print(f"def Attempts/Successes/Bytes : {def_attempts}/{def_successes}/{def_bytes}")
    print(f"def First Success : {def_first_success or 'NONE'}")
    print(f"def Hydra : {len(def_hydra)}")
    return 2 if def_gate == DEF_FAIL_GATE else 0


def def_lane_entry(def_lane: str) -> None:
    def_args = def_parse_args()
    if def_args.aggregate:
        raise SystemExit(def_run_aggregate(def_args))
    if def_args.lane and def_args.lane != def_lane:
        raise SystemExit(f"Wrapper/lane mismatch: wrapper={def_lane}, requested={def_args.lane}")
    def_args.lane = def_lane
    raise SystemExit(def_run_lane(def_args))


def def_main() -> int:
    def_args = def_parse_args()
    if def_args.aggregate:
        return def_run_aggregate(def_args)
    if not def_args.lane:
        raise ValueError("Specify --lane or --aggregate.")
    return def_run_lane(def_args)


if __name__ == "__main__":
    raise SystemExit(def_main())
