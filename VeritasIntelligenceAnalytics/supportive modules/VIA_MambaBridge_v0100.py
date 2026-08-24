"""
VIA_MambaBridge_v0100.py
Micromamba SAT Solver → VIA_EnvManager 衝突報告橋接碼。

配套:Invoke-VIA-MicromambaResolver.ps1(同目錄)
  該腳本以 micromamba create --dry-run 進行極速依賴解析,
  將結果寫入 %TEMP%\\via_mamba_conflict_<env>.json。
本橋接碼負責:
  1. 收集 TEMP 目錄下所有 via_mamba_conflict_*.json 掃描結果。
  2. 正規化為 VIA_EnvManager 的 def_EnvConflictRecord 相容格式
     {env_name, severity, category, detail, related_packages}。
  3. 合併寫入 _via_envmanager_output/VIA_EnvManager_ConflictReport.json
     (只增不減:保留既有衝突,去重後追加),並記錄 History JSONL。

設計原則(承 VIA_EnvManager):
  - 不修改 VIA_EnvManager.py 核心與其 def_scan_all_envs() 邏輯,純外掛式合併。
  - 鬆耦合:不 import EnvManager 模組,只讀寫其公開 JSON 檔。
  - 可離線運作;micromamba 缺席時本橋接碼仍可處理既有報告檔。

CLI:
  python VIA_MambaBridge_v0100.py collect            # 收集並列印(不落地)
  python VIA_MambaBridge_v0100.py merge              # 收集 + 合併寫入衝突報告
  python VIA_MambaBridge_v0100.py merge --dir <路徑>  # 指定掃描目錄
  python VIA_MambaBridge_v0100.py show               # 檢視合併後的衝突報告
"""
from __future__ import annotations

import json
import re
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# ══════════════════════════════════════════════════════════════════════════════
# def PARAMETERS(與 VIA_EnvManager.py 對齊)
# ══════════════════════════════════════════════════════════════════════════════
def_PARAM_MODULE_ID = "VIS-MAMBA-BRIDGE-000001"
def_PARAM_MODULE_VERSION = "0100"
def_PARAM_OWNER = "VIA_MAMBA_BRIDGE"

def_PARAM_OUTPUT_DIR = Path.cwd() / "_via_envmanager_output"
def_PARAM_CONFLICT_JSON = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_ConflictReport.json"
def_PARAM_HISTORY_JSONL = def_PARAM_OUTPUT_DIR / "VIA_EnvManager_History.jsonl"

def_PARAM_REPORT_GLOB = "via_mamba_conflict_*.json"
def_PARAM_CATEGORY_CONFLICT = "MAMBA_SAT_CONFLICT"
def_PARAM_SEVERITY_CONFLICT = "WARN"

# conda/mamba solver 描述中常見的套件名樣式,例如
# "package numpy-1.26.4 requires ..." / "nothing provides pandas >=2.0"
def_PARAM_PKG_TOKEN_RE = re.compile(
    r"\b([A-Za-z0-9][A-Za-z0-9._-]{1,60}?)(?:-\d[\w.]*|\s*(?:==|>=|<=|>|<|~=)\s*\d)"
)


# ══════════════════════════════════════════════════════════════════════════════
# def LOW LEVEL UTILS
# ══════════════════════════════════════════════════════════════════════════════
def def_now_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def def_read_json_safe(path_value: Path, default_value: Any) -> Any:
    try:
        return json.loads(path_value.read_text(encoding="utf-8-sig"))
    except Exception:
        return default_value


def def_write_json(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    path_value.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def def_append_jsonl(path_value: Path, payload: Any) -> None:
    path_value.parent.mkdir(parents=True, exist_ok=True)
    with path_value.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def def_default_report_dir() -> Path:
    return Path(tempfile.gettempdir())


def def_extract_related_packages(detail_text: str) -> List[str]:
    names = {match.group(1).lower() for match in def_PARAM_PKG_TOKEN_RE.finditer(detail_text or "")}
    return sorted(name for name in names if name not in {"python", "version", "package"})


# ══════════════════════════════════════════════════════════════════════════════
# def COLLECT:讀取 Micromamba Resolver 產出的報告檔
# ══════════════════════════════════════════════════════════════════════════════
def def_collect_mamba_reports(report_dir: Path) -> List[Dict[str, Any]]:
    reports: List[Dict[str, Any]] = []
    for report_path in sorted(report_dir.glob(def_PARAM_REPORT_GLOB)):
        payload = def_read_json_safe(report_path, None)
        if not isinstance(payload, dict) or "Environment" not in payload:
            continue
        payload["_source_file"] = str(report_path)
        reports.append(payload)
    return reports


def def_normalize_to_conflict_records(reports: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """轉為 def_EnvConflictRecord 相容 dict;僅收錄實際衝突(乾淨環境不進衝突清單)。"""
    records: List[Dict[str, Any]] = []
    for report in reports:
        env_name = str(report.get("Environment", "unknown"))
        if report.get("IsConflictFree", True):
            continue
        raw_conflicts = report.get("Conflicts") or []
        if isinstance(raw_conflicts, dict):  # ConvertTo-Json 單元素會壓成物件
            raw_conflicts = [raw_conflicts]
        for conflict in raw_conflicts:
            detail_text = str(conflict.get("Description") or conflict.get("Rule") or "unknown solver problem")
            records.append(
                {
                    "env_name": env_name,
                    "severity": def_PARAM_SEVERITY_CONFLICT,
                    "category": def_PARAM_CATEGORY_CONFLICT,
                    "detail": detail_text,
                    "related_packages": def_extract_related_packages(detail_text),
                }
            )
    return records


# ══════════════════════════════════════════════════════════════════════════════
# def MERGE:只增不減合併進 VIA_EnvManager_ConflictReport.json
# ══════════════════════════════════════════════════════════════════════════════
def def_conflict_dedupe_key(record: Dict[str, Any]) -> str:
    return "|".join([
        str(record.get("env_name", "")),
        str(record.get("category", "")),
        str(record.get("detail", "")),
    ])


def def_merge_into_conflict_report(new_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    existing_payload = def_read_json_safe(def_PARAM_CONFLICT_JSON, {"conflicts": []})
    existing_conflicts = existing_payload.get("conflicts") or []
    seen_keys = {def_conflict_dedupe_key(row) for row in existing_conflicts}

    appended: List[Dict[str, Any]] = []
    for record in new_records:
        key = def_conflict_dedupe_key(record)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        appended.append(record)

    merged_conflicts = existing_conflicts + appended
    merged_payload = {
        "conflicts": merged_conflicts,
        "updated_at_utc": def_now_utc_iso(),
        "mamba_bridge": {
            "module_id": def_PARAM_MODULE_ID,
            "version": def_PARAM_MODULE_VERSION,
            "appended_count": len(appended),
        },
    }
    def_write_json(def_PARAM_CONFLICT_JSON, merged_payload)
    def_append_jsonl(
        def_PARAM_HISTORY_JSONL,
        {
            "ts_utc": def_now_utc_iso(),
            "owner": def_PARAM_OWNER,
            "event": "MAMBA_BRIDGE_MERGE",
            "appended": len(appended),
            "skipped_duplicates": len(new_records) - len(appended),
            "total_conflicts": len(merged_conflicts),
        },
    )
    return {
        "ok": True,
        "appended": len(appended),
        "skipped_duplicates": len(new_records) - len(appended),
        "total_conflicts": len(merged_conflicts),
        "path": str(def_PARAM_CONFLICT_JSON),
    }


# ══════════════════════════════════════════════════════════════════════════════
# def CLI
# ══════════════════════════════════════════════════════════════════════════════
def def_print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def def_parse_report_dir(argv: List[str]) -> Path:
    if "--dir" in argv:
        idx = argv.index("--dir")
        if idx + 1 < len(argv):
            return Path(argv[idx + 1])
    return def_default_report_dir()


def def_main(argv: List[str] | None = None) -> int:
    argv = list(argv if argv is not None else sys.argv[1:])
    command = argv[0] if argv else "collect"
    report_dir = def_parse_report_dir(argv)

    if command == "collect":
        reports = def_collect_mamba_reports(report_dir)
        records = def_normalize_to_conflict_records(reports)
        def_print_json({
            "ok": True,
            "report_dir": str(report_dir),
            "reports_found": len(reports),
            "conflict_records": records,
        })
        return 0

    if command == "merge":
        reports = def_collect_mamba_reports(report_dir)
        records = def_normalize_to_conflict_records(reports)
        result = def_merge_into_conflict_report(records)
        result["report_dir"] = str(report_dir)
        result["reports_found"] = len(reports)
        def_print_json(result)
        return 0 if result.get("appended", 0) == 0 or result.get("ok") else 1

    if command == "show":
        def_print_json(def_read_json_safe(def_PARAM_CONFLICT_JSON, {"conflicts": [], "note": "尚無報告"}))
        return 0

    def_print_json({
        "ok": False,
        "error": "UNKNOWN_COMMAND",
        "supported": ["collect [--dir 路徑]", "merge [--dir 路徑]", "show"],
        "received": command,
    })
    return 1


if __name__ == "__main__":
    sys.exit(def_main())
