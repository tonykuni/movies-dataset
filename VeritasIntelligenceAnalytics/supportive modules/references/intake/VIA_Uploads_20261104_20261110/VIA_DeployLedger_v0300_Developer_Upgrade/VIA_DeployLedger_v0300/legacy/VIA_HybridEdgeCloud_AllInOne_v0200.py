from __future__ import annotations

"""
VIA Hybrid Edge/Cloud Governance All-in-One v2.2.0

Developer/admin-side single-file governance engine for:
1. PC + mobile device-bound licensing with Ed25519 signatures.
2. Local-first / cloud-compute routing without inbound database exposure.
3. Per-engine signed manifests, entitlement handshakes, and integrity gates.
4. Copy-first PY -> PYD/EXE packaging plans that never mutate source files.
5. VIA Registry / SSOT / EnvManager / Runtime Bridge contract auditing.
6. Three-round panoramic testing and a warm-white RYG HTML matrix.
7. Top-25 operational/security failure detection, signed evidence, recovery
   guidance, and fail-closed production release gating.

Security boundary:
- Authority and release private keys are never embedded in this file.
- Production client bundles must exclude authority commands and private keys.
- HTML/localStorage is never an authorization boundary.
- A cloud service never receives a local database path or database credential.
"""

# =============================================================================
# def PARAMETERS — all replaceable parameters stay at the top
# =============================================================================
import argparse
import ast
import base64
import contextlib
import ctypes
import getpass
import hashlib
import html
import http.client
import importlib.util
import json
import os
import platform
import re
import secrets
import signal
import shutil
import ssl
import sqlite3
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Optional, Sequence, Tuple


def_PARAM_SYSTEM_NAME = "VERITAS INTELLIGENCE ANALYTICS"
def_PARAM_SYSTEM_LATIN = "DISCIPLINA • PRUDENTIA • INTEGRITAS"
def_PARAM_SYSTEM_SUBTITLE = "AI-Powered Research & Decision Intelligence Platform"
def_PARAM_ENGINE_NAME = "VIA Hybrid Edge/Cloud Governance All-in-One"
def_PARAM_ENGINE_VERSION = "2.2.1"
def_PARAM_SCHEMA_VERSION = "2.2"
def_PARAM_BUILD_MODE = "DEVELOPMENT"

def_PARAM_PRODUCT_SKU = "VIA-MFRS-PRO"
def_PARAM_DEFAULT_EDITION = "PRO"
def_PARAM_RELEASE_CHANNEL = "stable"
def_PARAM_PRODUCT_NUMBER_GROUPS = (4, 4, 4)
def_PARAM_PRODUCT_NUMBER_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
def_PARAM_PRODUCT_NUMBER_RE = re.compile(r"^[A-HJ-NP-Z2-9]{4}(?:-[A-HJ-NP-Z2-9]{4}){2}$")
def_PARAM_MASTER_KEY_PREFIX = "VIAK"
def_PARAM_MASTER_KEY_GROUPS = (4, 4, 4, 4, 4, 4)
def_PARAM_MASTER_KEY_ENV = "VIA_PRODUCT_MASTER_KEY"
def_PARAM_MASTER_ENTITLEMENT = "VIA_ALL_ENGINES"
def_PARAM_RUNTIME_GUARD_MODULE = "VIA_HybridEdgeCloud_AllInOne_v0200"
def_PARAM_RUNTIME_TOKEN_ENV = "VIA_RUNTIME_TOKEN_FILE"
def_PARAM_LICENSE_FILE_ENV = "VIA_LICENSE_FILE"
def_PARAM_MODULE_MANIFEST_ENV = "VIA_MODULE_MANIFEST_FILE"
def_PARAM_AUTHORITY_PUBLIC_KEY_ENV = "VIA_AUTHORITY_PUBLIC_KEY_FILE"
def_PARAM_RELEASE_PUBLIC_KEY_ENV = "VIA_RELEASE_PUBLIC_KEY_FILE"
def_PARAM_DEVICE_KEY_ENV = "VIA_DEVICE_KEY_FILE"
def_PARAM_PRODUCT_KEY_STATE_ENV = "VIA_PRODUCT_KEY_STATE_FILE"
def_PARAM_RUNTIME_REPLAY_LEDGER_ENV = "VIA_RUNTIME_REPLAY_LEDGER_FILE"
def_PARAM_GUARD_MARKER = "VIA-PRODUCT-GUARD-v2.2"
def_PARAM_MAX_PC_DEVICES = 1
def_PARAM_MAX_MOBILE_DEVICES = 1
def_PARAM_DEVICE_QUORUM = 2
def_PARAM_CLOCK_ROLLBACK_TOLERANCE_SECONDS = 300
def_PARAM_HANDSHAKE_TTL_SECONDS = 90
def_PARAM_REQUEST_MAX_AGE_SECONDS = 900
def_PARAM_PRODUCT_SALT = "VIA-MFRS-PRO-DEVICE-HASH-v2"

def_PARAM_LICENSE_KEY_ID = "VIA-LIC-PROD-01"
def_PARAM_RELEASE_KEY_ID = "VIA-REL-PROD-01"
def_PARAM_CLOUD_KEY_ID = "VIA-CLOUD-PROD-01"
def_PARAM_PRIVATE_KEY_PASSWORD_ENV = "VIA_PRIVATE_KEY_PASSWORD"
def_PARAM_TRUSTED_LICENSE_PUBLIC_KEY_SHA256 = ""
def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256 = ""
def_PARAM_TRUSTED_CLOUD_TRANSPORT_PUBLIC_KEY_SHA256 = ""
def_PARAM_REQUIRE_PINNED_KEYS = True

def_PARAM_HOME_ENV = "VIA_HOME"
def_PARAM_HOME = Path(os.environ.get(def_PARAM_HOME_ENV, str(Path.cwd()))).expanduser().resolve()
def_PARAM_OUTPUT_DIR = def_PARAM_HOME / "_via_hybrid_governance"
def_PARAM_STAGING_DIR = def_PARAM_OUTPUT_DIR / "staging"
def_PARAM_REPORT_DIR = def_PARAM_OUTPUT_DIR / "reports"
def_PARAM_AUDIT_JSONL = def_PARAM_OUTPUT_DIR / "audit" / "VIA_Hybrid_Audit.jsonl"
def_PARAM_DEVICE_KEY_FILE = def_PARAM_OUTPUT_DIR / "device" / "device_key.dpapi"
def_PARAM_PRODUCT_KEY_STATE_FILE = def_PARAM_OUTPUT_DIR / "device" / "product_key.dpapi"
def_PARAM_CLOCK_STATE_FILE = def_PARAM_OUTPUT_DIR / "device" / "clock_state.json"
def_PARAM_RUNTIME_REPLAY_LEDGER = def_PARAM_OUTPUT_DIR / "runtime" / "RuntimeTokenReplay.jsonl"
def_PARAM_HTML_REPORT = def_PARAM_REPORT_DIR / "VIA_Hybrid_Governance_Matrix.html"
def_PARAM_JSON_REPORT = def_PARAM_REPORT_DIR / "VIA_Hybrid_Governance_Matrix.json"
def_PARAM_TOP25_JSON_REPORT = def_PARAM_REPORT_DIR / "VIA_Top25_Resilience_Matrix.json"
def_PARAM_TOP25_HTML_REPORT = def_PARAM_REPORT_DIR / "VIA_Top25_Resilience_Matrix.html"
def_PARAM_TOP25_EVIDENCE_TEMPLATE = def_PARAM_REPORT_DIR / "VIA_Top25_Evidence_Template.json"

def_PARAM_CHUNK_SIZE = 1024 * 1024
def_PARAM_MAX_JSON_BYTES = 8 * 1024 * 1024
def_PARAM_MAX_DOWNLOAD_BYTES = 8 * 1024 * 1024 * 1024
def_PARAM_MAX_DB_BATCH_ROWS = 100000
def_PARAM_NETWORK_TIMEOUT_SECONDS = 60
def_PARAM_PROCESS_TIMEOUT_SECONDS = 3600
def_PARAM_MAX_PROCESS_OUTPUT_BYTES = 4 * 1024 * 1024
def_PARAM_MIN_FREE_DISK_BYTES = 2 * 1024 * 1024 * 1024
def_PARAM_MAX_JSON_DEPTH = 32
def_PARAM_MAX_JSON_NODES = 250000
def_PARAM_PARALLEL_WORKERS = max(2, min(8, (os.cpu_count() or 2)))

def_PARAM_ALLOWED_DEVICE_TYPES = {"pc", "mobile"}
def_PARAM_ALLOWED_DATA_CLASSES = {"PUBLIC", "INTERNAL", "CONFIDENTIAL", "RESTRICTED"}
def_PARAM_ALLOWED_COMPUTE_MODES = {"AUTO", "LOCAL", "CLOUD"}
def_PARAM_ALLOWED_DB_MODES = {"LOCAL_ONLY", "CLOUD_COMPUTE_LOCAL_DB", "CLOUD_FULL_SYNC"}
def_PARAM_ALLOWED_DB_BACKENDS = {"SQLITE", "DUCKDB"}
def_PARAM_ALLOWED_INGEST_MODES = {"APPEND", "UPSERT"}
def_PARAM_ALLOWED_DEPLOYMENT_MODES = {"DEVELOPMENT", "PRODUCTION"}
def_PARAM_ALLOWED_RELEASE_ROLES = {"DEVELOPER", "CLIENT", "AUTHORITY"}
def_PARAM_ALLOWED_SQL_TYPES = {
    "TEXT", "VARCHAR", "INTEGER", "BIGINT", "REAL", "DOUBLE", "BOOLEAN",
    "DATE", "TIMESTAMP", "BLOB", "JSON", "DECIMAL", "NUMERIC",
}
def_PARAM_ALLOWED_ARTIFACT_SUFFIXES = {".pyd", ".dll", ".exe", ".so", ".dylib", ".whl"}
def_PARAM_ALLOWED_SOURCE_SUFFIXES = {".py"}
def_PARAM_EXCLUDED_DIR_NAMES = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "__pycache__",
    "node_modules", "build", "dist", "_via_hybrid_governance",
    "_via_pyd_staging", "_via_pyd_plan_test",
}

def_PARAM_API_ANCHORS = {
    "license_challenge": "/v1/license/challenge",
    "job_submit": "/v1/jobs/submit",
    "job_status": "/v1/jobs/{job_id}",
    "artifact_download": "/v1/artifacts/{artifact_id}",
}

def_PARAM_ACCELERATORS = [
    "AST_CACHE",
    "CONTENT_HASH",
    "INCREMENTAL_SCAN",
    "PARALLEL_SCAN",
    "COPY_FIRST",
    "HASH_GATE",
    "SCHEMA_GATE",
    "SIGNATURE_GATE",
    "PRODUCT_NUMBER_GATE",
    "MASTER_KEY_GATE",
    "DEVICE_QUORUM",
    "ENTITLEMENT_GATE",
    "RUNTIME_TOKEN_ONE_USE",
    "PROCESS_BINDING",
    "GUARD_INJECTION",
    "ROUTE_POLICY",
    "CHUNKED_IO",
    "ATOMIC_WRITE",
    "APPEND_ONLY_AUDIT",
    "HTML_MATRIX",
]

def_PARAM_CORE_CONTRACTS = {
    "runtime_bridge": {
        "patterns": ["*VIA_Runtime_Bridge_All_in_One.py", "*VIA_RuntimeBridge_AllInOne.py"],
        "required_symbols": ["def_bootstrap_runtime", "def_registry_resolve", "def_run_with_via_runtime"],
        "capabilities": ["runtime_bootstrap", "shared_context", "task_execution"],
    },
    "registry": {
        "patterns": ["*VIA_RegistryCore_v1.py"],
        "required_symbols": ["def_register_module_file", "def_resolve_module", "def_status_report"],
        "capabilities": ["append_only_registry", "capability_resolution", "module_identity"],
    },
    "ssot": {
        "patterns": ["*VIA_SSOT_Unified.py"],
        "required_symbols": ["get_ssot", "normalize", "extract", "self_test"],
        "capabilities": ["canonical_rules", "normalization", "regex_ssot"],
    },
    "env_manager": {
        "patterns": ["*VIA_EnvManager.py"],
        "required_symbols": ["def_scan_all_envs", "def_plan_install_request", "def_get_base_via_conflicts"],
        "capabilities": ["environment_route", "dependency_gate", "conflict_scan"],
    },
    "aegis": {
        "patterns": ["*VeritasAegisNexus.py"],
        "required_symbols": ["safe_request", "check_url_compliance", "run_self_test"],
        "capabilities": ["network_resilience", "compliance", "data_fetch"],
    },
    "celeritas": {
        "patterns": ["*VeritasCeleritas.py"],
        "required_symbols": ["cross_init", "xmap", "run_self_test"],
        "capabilities": ["acceleration", "memory_guard", "parallel_map"],
    },
}

def_PARAM_SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|secret|api[_-]?key|private[_-]?key)\s*=\s*['\"][^'\"]{3,}['\"]"),
    re.compile(r"(?i)-----BEGIN (?:RSA |EC |OPENSSH |ENCRYPTED )?PRIVATE KEY-----"),
]
def_PARAM_ABSOLUTE_PATH_PATTERNS = [
    re.compile(r"(?i)[A-Z]:\\Users\\[^\\\s'\"]+"),
    re.compile("/mnt/" + "data/"),
]
def_PARAM_HIGH_RISK_CALLS = {"eval", "exec", "os.system", "subprocess.Popen", "pickle.loads"}
def_PARAM_CONTROLLED_RISK_WRAPPERS = {"def_run_subprocess_bounded"}
def_PARAM_MODULE_ID_RE = re.compile(r"^[A-Z][A-Z0-9_-]{2,63}$")
def_PARAM_CAPABILITY_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,95}$")
def_PARAM_TABLE_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")
def_PARAM_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
def_PARAM_REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{15,127}$")
def_PARAM_UNSAFE_DATABASE_PATH_PARTS = {
    "onedrive", "google drive", "googledrive", "dropbox", "icloud drive", "box sync",
}


def_PARAM_TOP25_RISK_CONTROLS: Tuple[Dict[str, Any], ...] = (
    {"id": "RISK-001", "severity": "BLOCKER", "probe": "guard_chain", "roles": ["CLIENT"], "title": "引擎可繞過中央授權單獨執行", "solution": "每個 PYD/EXE 注入內層 Guard，逐次驗證 License、產品號、Master KEY commitment、模組簽章及一次性程序權杖；直接啟動必須 fail-closed。"},
    {"id": "RISK-002", "severity": "BLOCKER", "probe": "trust_pins", "roles": ["CLIENT", "AUTHORITY"], "title": "正式信任公鑰 Pin 缺失或誤用開發金鑰", "solution": "正式建置寫入三組官方公鑰 SHA-256 Pin，永久禁止 dev pin 及不安全金鑰開關；採雙公鑰輪替窗口。"},
    {"id": "RISK-003", "severity": "BLOCKER", "probe": "device_secret_store", "roles": ["CLIENT"], "external": "windows_service_acl_or_tpm", "title": "裝置金鑰、Master KEY 狀態或授權檔 ACL 過寬", "solution": "以專用 Windows Service SID、明確 DACL、使用者範圍 DPAPI 或 TPM/CNG 不可匯出金鑰保存；標準使用者不得讀取。"},
    {"id": "RISK-004", "severity": "HIGH", "probe": "external", "roles": ["AUTHORITY"], "external": "authority_rate_limit", "title": "無效啟用與授權嘗試可被暴力重試", "solution": "Authority 以獨立已提交交易或原子計數器，依 license/device/IP/全域多層限流；錯誤輸入也必須累計。"},
    {"id": "RISK-005", "severity": "BLOCKER", "probe": "external", "roles": ["CLIENT", "AUTHORITY"], "external": "signed_revocation_feed", "title": "重綁、撤銷後舊憑證或舊裝置仍可使用", "solution": "維護簽署的最低 binding revision、device denylist 與短期 lease；重綁時清除舊憑證並令舊 Runtime Token 立即失效。"},
    {"id": "RISK-006", "severity": "HIGH", "probe": "clock_state", "roles": ["CLIENT"], "external": "monotonic_trusted_time", "title": "系統時鐘回撥或刪除狀態延長離線授權", "solution": "密封 last trusted time、偵測回撥、短期簽署 lease；正式版以 TPM/DPAPI 保護 monotonic state，狀態遺失即安全復原而非重置。"},
    {"id": "RISK-007", "severity": "BLOCKER", "probe": "external", "roles": ["AUTHORITY"], "external": "hsm_kms_authority", "title": "Authority 長效 Token 或簽章私鑰外洩", "solution": "管理 API 採 OIDC、MFA、RBAC 與短效 Token；私鑰進 HSM/KMS、機密進 Secret Manager，敏感操作寫不可竄改操作者稽核。"},
    {"id": "RISK-008", "severity": "HIGH", "probe": "external", "roles": ["CLIENT"], "external": "separate_mobile_credentials", "title": "手機、AI 與桌面共用同一 Credential", "solution": "手機使用獨立可撤銷裝置金鑰與 read-only session；AI、桌面、手機三種 credential 完全分離。"},
    {"id": "RISK-009", "severity": "HIGH", "probe": "external", "roles": ["CLIENT"], "external": "mobile_origin_pinning", "title": "手機盲信 QR 網址或跨網域重新導向", "solution": "釘選官方 HTTPS origin 與 issuer key、簽署 QR challenge、禁止 HTTP 降級及跨 origin redirect。"},
    {"id": "RISK-010", "severity": "HIGH", "probe": "strict_types", "roles": ["DEVELOPER", "CLIENT", "AUTHORITY"], "title": "字串 false、布林或數值被寬鬆轉型", "solution": "所有 JSON/config 欄位採原生型別與嚴格 schema；拒絕 bool 當 int、字串當 bool、重複 JSON key 與過深結構。"},
    {"id": "RISK-011", "severity": "HIGH", "probe": "mobile_policy", "roles": ["CLIENT", "AUTHORITY"], "title": "不允許手機的產品仍能建立手機綁定", "solution": "授權 Profile 明確區分 mobile allowed/required/max，發證與每次 session 建立都重新核對產品政策。"},
    {"id": "RISK-012", "severity": "HIGH", "probe": "product_binding", "roles": ["CLIENT", "AUTHORITY"], "title": "商品 A 的授權可執行商品 B 的同名模組", "solution": "每次執行逐欄核對 product SKU、產品號、Master KEY hash、module ID、artifact hash、entitlement 與 license ID。"},
    {"id": "RISK-013", "severity": "HIGH", "probe": "compatibility", "roles": ["DEVELOPER", "CLIENT"], "title": "PYD ABI、OS、CPU 或依賴不相容", "solution": "Signed Manifest 內含 Python ABI、平台、架構、版本及依賴；安裝前 preflight，必要條件不符即 BLOCKED。"},
    {"id": "RISK-014", "severity": "HIGH", "probe": "external", "roles": ["DEVELOPER", "CLIENT"], "external": "signed_release_index", "title": "多版本同時被 discovery 或更新後無法啟動", "solution": "使用簽署 release index 與唯一 active pointer；STAGE 驗證後原子 PROMOTE，舊版只供 rollback、不參與 discovery。"},
    {"id": "RISK-015", "severity": "HIGH", "probe": "package_tree", "roles": ["DEVELOPER", "CLIENT"], "title": "安裝目錄被加入未登錄 DLL、設定檔或 reparse point", "solution": "逐檔簽署完整 package tree；實際樹必須與 Manifest 完全相等，拒絕 symlink/reparse point、額外檔案與缺檔。"},
    {"id": "RISK-016", "severity": "MEDIUM", "probe": "streaming_copy", "roles": ["DEVELOPER", "CLIENT"], "title": "大檔耗盡記憶體或驗證後被換檔", "solution": "採串流 hash/download、Copy-First 三重 Hash、原子落盤；從同一 staging snapshot 建置並在完成後重驗整棵樹。"},
    {"id": "RISK-017", "severity": "HIGH", "probe": "bounded_process", "roles": ["DEVELOPER", "CLIENT"], "external": "windows_job_object_limits", "title": "子程序逾時、輸出洪水或殘留程序樹", "solution": "所有外部程序使用有界輸出、強制 timeout、獨立 process group；Windows 正式版再以 Job Object 限 CPU/RAM/子程序並整樹回收。"},
    {"id": "RISK-018", "severity": "HIGH", "probe": "input_schema", "roles": ["DEVELOPER", "CLIENT", "AUTHORITY"], "title": "參數型別、巢狀 JSON 或資料庫 schema 漂移", "solution": "在任何轉換前驗證 Mapping/List 與大小、深度、節點數；SQL 只由白名單 schema 組裝，禁止遠端 SQL。"},
    {"id": "RISK-019", "severity": "HIGH", "probe": "external", "roles": ["CLIENT"], "external": "step_up_authorization", "title": "AI 或手機可直接執行具副作用指令", "solution": "read-only 可自動；write 需明確確認；destructive 需短效 step-up token、最小權限帳號及資源鎖。"},
    {"id": "RISK-020", "severity": "HIGH", "probe": "idempotency", "roles": ["CLIENT", "AUTHORITY"], "external": "remote_idempotency", "title": "重試或並行請求造成重複寫入、扣款或工作", "solution": "強制 request/idempotency key；本地 DB 在同一交易寫唯一執行紀錄，遠端服務以唯一鍵回放既有結果。"},
    {"id": "RISK-021", "severity": "MEDIUM", "probe": "atomic_state", "roles": ["DEVELOPER", "CLIENT", "AUTHORITY"], "title": "錯誤狀態與狀態轉移在例外時一併回滾", "solution": "狀態轉移採明確 transaction boundary；錯誤計數、過期標記與 outbox 使用獨立可提交交易並做狀態斷言。"},
    {"id": "RISK-022", "severity": "HIGH", "probe": "external", "roles": ["AUTHORITY"], "external": "transactional_outbox", "title": "郵件或通知失敗留下不一致授權狀態", "solution": "以 transactional outbox 同交易排入工作；worker 指數退避、死信佇列與一致的最終失敗狀態。"},
    {"id": "RISK-023", "severity": "HIGH", "probe": "token_hygiene", "roles": ["CLIENT", "AUTHORITY"], "title": "一次性 Token 出現在 URL、log、HTML 或命令列", "solution": "秘密只走受保護檔案、Authorization header 或 POST body；Query、log、錯誤與 HTML 全面遮罩，Master KEY 不接受 CLI 參數。"},
    {"id": "RISK-024", "severity": "HIGH", "probe": "audit_chain", "roles": ["AUTHORITY"], "external": "worm_audit", "title": "本地 Authority DB 或 hash chain 可被管理者重寫", "solution": "正式 Authority 使用受管 PostgreSQL、PITR 與唯一交易；事件另送 WORM/append-only 儲存並以 KMS key 簽署及定期驗鏈。"},
    {"id": "RISK-025", "severity": "HIGH", "probe": "data_location", "roles": ["CLIENT"], "external": "cloud_adapter_security", "title": "活動資料庫位於同步碟、網路分享或未驗證雲端 Adapter", "solution": "活動 DuckDB/SQLite 僅放本機安全根目錄；拒絕同步碟、UNC、symlink；雲端採分離 Adapter、最小 scope、schema/checksum 與 datasource ID。"},
)


# =============================================================================
# def DATA STRUCTURES
# =============================================================================
@dataclass
class def_CommandResult:
    ok: bool
    status: str
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class def_RouteDecision:
    ok: bool
    compute_location: str
    database_location: str
    transport: str
    local_writer_required: bool
    mobile_access: str
    reasons: List[str] = field(default_factory=list)
    controls: List[str] = field(default_factory=list)


@dataclass
class def_SourceAnalysis:
    path: str
    relative_path: str
    sha256: str
    size_bytes: int
    ast_ok: bool
    compile_ok: bool
    artifact_kind: str
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    risks: List[Dict[str, str]] = field(default_factory=list)
    hydra_level: str = "LOW"
    status: str = "GREEN"


@dataclass
class def_RuntimeContext:
    base_root: str
    output_root: str
    product_sku: str
    version: str
    accelerators: Dict[str, bool]
    api_anchors: Dict[str, str]
    core_contracts: Dict[str, Any]
    security_gates: Dict[str, Any]


@dataclass
class def_RiskFinding:
    risk_id: str
    severity: str
    title: str
    status: str
    state: str
    applies_to_role: bool
    detector: str
    evidence: str
    solution: str
    external_requirement: str = ""


def_ANALYSIS_CACHE: Dict[Tuple[str, str], def_SourceAnalysis] = {}
def_ANALYSIS_CACHE_LOCK = threading.Lock()


# =============================================================================
# def BASIC UTILITIES
# =============================================================================
def def_now_utc() -> datetime:
    return datetime.now(timezone.utc)


def def_now_utc_iso() -> str:
    return def_now_utc().isoformat().replace("+00:00", "Z")


def def_parse_utc(value: str) -> datetime:
    if not value:
        raise ValueError("UTC timestamp is empty")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    parsed = datetime.fromisoformat(normalized)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def def_canonical_json_bytes(payload: Any) -> bytes:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def def_pretty_json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True, default=str)


def def_b64u_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def def_b64u_decode(value: str) -> bytes:
    padding = "=" * ((4 - len(value) % 4) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


def def_sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def def_sha256_text(value: str) -> str:
    return def_sha256_bytes(value.encode("utf-8"))


def def_sha256_file(path_value: Path, chunk_size: int = def_PARAM_CHUNK_SIZE) -> str:
    digest = hashlib.sha256()
    with path_value.open("rb") as file_handle:
        while True:
            chunk = file_handle.read(chunk_size)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def def_atomic_write_bytes(path_value: Path, data: bytes, overwrite: bool = False) -> None:
    path_value = path_value.expanduser().resolve()
    path_value.parent.mkdir(parents=True, exist_ok=True)
    if path_value.exists() and not overwrite:
        raise FileExistsError(f"Refusing to overwrite existing file: {path_value}")
    file_descriptor, temp_name = tempfile.mkstemp(prefix=f".{path_value.name}.", suffix=".tmp", dir=str(path_value.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(file_descriptor, "wb") as file_handle:
            file_handle.write(data)
            file_handle.flush()
            os.fsync(file_handle.fileno())
        os.replace(temp_path, path_value)
    finally:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)


def def_atomic_write_text(path_value: Path, text_value: str, overwrite: bool = False) -> None:
    def_atomic_write_bytes(path_value, text_value.encode("utf-8"), overwrite=overwrite)


def def_write_json(path_value: Path, payload: Any, overwrite: bool = False) -> None:
    def_atomic_write_text(path_value, def_pretty_json(payload) + "\n", overwrite=overwrite)


def def_json_object_no_duplicates(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    output: Dict[str, Any] = {}
    for key, value in pairs:
        if key in output:
            raise ValueError(f"Duplicate JSON key is forbidden: {key}")
        output[key] = value
    return output


def def_validate_json_shape(
    payload: Any,
    max_depth: int = def_PARAM_MAX_JSON_DEPTH,
    max_nodes: int = def_PARAM_MAX_JSON_NODES,
) -> None:
    node_count = 0

    def def_walk(value: Any, depth: int) -> None:
        nonlocal node_count
        node_count += 1
        if node_count > max_nodes:
            raise ValueError(f"JSON node count exceeds gate: {max_nodes}")
        if depth > max_depth:
            raise ValueError(f"JSON nesting exceeds gate: {max_depth}")
        if isinstance(value, Mapping):
            for key, child in value.items():
                if not isinstance(key, str):
                    raise ValueError("JSON object keys must be strings")
                def_walk(child, depth + 1)
        elif isinstance(value, list):
            for child in value:
                def_walk(child, depth + 1)
        elif value is not None and not isinstance(value, (str, int, float, bool)):
            raise ValueError(f"Unsupported JSON value type: {type(value).__name__}")

    def_walk(payload, 0)


def def_read_json(path_value: Path, max_bytes: int = def_PARAM_MAX_JSON_BYTES) -> Any:
    size_value = path_value.stat().st_size
    if size_value > max_bytes:
        raise ValueError(f"JSON exceeds size gate: {size_value} > {max_bytes}")
    payload = json.loads(
        path_value.read_text(encoding="utf-8-sig"),
        object_pairs_hook=def_json_object_no_duplicates,
    )
    def_validate_json_shape(payload)
    return payload


def def_require_mapping(value: Any, field_name: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{field_name} must be a JSON object")
    return value


def def_require_list(value: Any, field_name: str) -> List[Any]:
    if not isinstance(value, list):
        raise ValueError(f"{field_name} must be a JSON array")
    return value


def def_require_native_bool(value: Any, field_name: str) -> bool:
    if type(value) is not bool:
        raise ValueError(f"{field_name} must be a native JSON boolean")
    return value


def def_require_int(value: Any, field_name: str, minimum: int = 0, maximum: Optional[int] = None) -> int:
    if type(value) is not int:
        raise ValueError(f"{field_name} must be a native JSON integer")
    if value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{field_name} is outside the allowed range")
    return value


def def_validate_request_id(value: str) -> str:
    normalized = str(value or "").strip()
    if not def_PARAM_REQUEST_ID_RE.fullmatch(normalized):
        raise ValueError("request_id must contain 16-128 safe symbols")
    return normalized


def def_path_is_link_or_reparse(path_value: Path) -> bool:
    try:
        if path_value.is_symlink():
            return True
        attributes = int(getattr(os.lstat(path_value), "st_file_attributes", 0))
        return bool(attributes & 0x400)
    except FileNotFoundError:
        return False


def def_validate_no_link_chain(path_value: Path) -> None:
    absolute_path = path_value.expanduser().absolute()
    candidates = [absolute_path, *absolute_path.parents]
    for candidate in candidates:
        if candidate.exists() and def_path_is_link_or_reparse(candidate):
            raise ValueError(f"Symlink/reparse point is forbidden: {candidate}")


def def_validate_active_database_location(database_path: Path, approved_root: Path) -> Path:
    raw_text = str(database_path.expanduser())
    normalized_text = raw_text.replace("\\", "/").lower()
    if raw_text.startswith("\\\\") or normalized_text.startswith("//"):
        raise ValueError("Active SQLite/DuckDB cannot use a UNC/network path")
    matched = sorted(marker for marker in def_PARAM_UNSAFE_DATABASE_PATH_PARTS if marker in normalized_text)
    if matched:
        raise ValueError(f"Active SQLite/DuckDB cannot use a sync-folder path: {matched[0]}")
    def_validate_no_link_chain(approved_root)
    def_validate_no_link_chain(database_path.parent)
    if database_path.exists():
        def_validate_no_link_chain(database_path)
    return def_validate_under_root(database_path, approved_root)


def def_require_free_disk(path_value: Path, required_bytes: int = def_PARAM_MIN_FREE_DISK_BYTES) -> Dict[str, int]:
    candidate = path_value.expanduser().absolute()
    while not candidate.exists() and candidate != candidate.parent:
        candidate = candidate.parent
    usage = shutil.disk_usage(candidate)
    if usage.free < required_bytes:
        raise OSError(f"Insufficient free disk: {usage.free} < {required_bytes}")
    return {"total": usage.total, "used": usage.used, "free": usage.free, "required": required_bytes}


def def_redact_sensitive_text(value: str) -> str:
    output = re.sub(r"(?i)VIAK(?:-[A-HJ-NP-Z2-9]{4}){6}", "VIAK-***REDACTED***", str(value))
    output = re.sub(r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s]+", r"\1***REDACTED***", output)
    output = re.sub(r"(?i)((?:token|secret|password|private[_-]?key)\s*[:=]\s*)[^\s,;]+", r"\1***REDACTED***", output)
    return output


def def_terminate_process_tree(process: subprocess.Popen[Any]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            process.kill()
        else:
            os.killpg(process.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError, OSError):
        try:
            process.kill()
        except (ProcessLookupError, OSError):
            pass


def def_run_subprocess_bounded(
    command: Sequence[str],
    cwd: Optional[Path] = None,
    env: Optional[Mapping[str, str]] = None,
    timeout_seconds: int = def_PARAM_PROCESS_TIMEOUT_SECONDS,
    max_output_bytes: int = def_PARAM_MAX_PROCESS_OUTPUT_BYTES,
) -> Dict[str, Any]:
    if not command:
        raise ValueError("Subprocess command cannot be empty")
    if timeout_seconds <= 0 or max_output_bytes <= 0:
        raise ValueError("Subprocess timeout and output gate must be positive")
    process_kwargs: Dict[str, Any] = {
        "cwd": str(cwd) if cwd is not None else None,
        "env": dict(env) if env is not None else None,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": False,
    }
    if os.name == "nt":
        process_kwargs["creationflags"] = int(getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0))
    else:
        process_kwargs["start_new_session"] = True
    process = subprocess.Popen([str(item) for item in command], **process_kwargs)
    buffers = {"stdout": bytearray(), "stderr": bytearray()}
    output_exceeded = threading.Event()

    def def_reader(stream: Any, key: str) -> None:
        try:
            while True:
                chunk = stream.read(65536)
                if not chunk:
                    break
                remaining = max_output_bytes - len(buffers[key])
                if remaining > 0:
                    buffers[key].extend(chunk[:remaining])
                if len(chunk) > remaining:
                    output_exceeded.set()
                    break
        finally:
            stream.close()

    threads = [
        threading.Thread(target=def_reader, args=(process.stdout, "stdout"), daemon=True),
        threading.Thread(target=def_reader, args=(process.stderr, "stderr"), daemon=True),
    ]
    for thread in threads:
        thread.start()
    deadline = time.monotonic() + timeout_seconds
    timed_out = False
    while process.poll() is None:
        if output_exceeded.is_set():
            def_terminate_process_tree(process)
            break
        if time.monotonic() >= deadline:
            timed_out = True
            def_terminate_process_tree(process)
            break
        time.sleep(0.02)
    try:
        exit_code = process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        def_terminate_process_tree(process)
        exit_code = process.wait(timeout=5)
    for thread in threads:
        thread.join(timeout=2)
    stdout_text = def_redact_sensitive_text(bytes(buffers["stdout"]).decode("utf-8", errors="replace"))
    stderr_text = def_redact_sensitive_text(bytes(buffers["stderr"]).decode("utf-8", errors="replace"))
    if output_exceeded.is_set():
        status = "OUTPUT_LIMIT_EXCEEDED"
    elif timed_out:
        status = "PROCESS_TIMEOUT"
    elif exit_code == 0:
        status = "PROCESS_PASS"
    else:
        status = "PROCESS_FAILED"
    return {
        "ok": status == "PROCESS_PASS",
        "status": status,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "output_limited": output_exceeded.is_set(),
        "stdout_tail": stdout_text[-4000:],
        "stderr_tail": stderr_text[-4000:],
    }


def def_safe_relative(path_value: Path, root_value: Path) -> str:
    return str(path_value.resolve().relative_to(root_value.resolve())).replace("\\", "/")


def def_validate_under_root(path_value: Path, root_value: Path) -> Path:
    resolved_path = path_value.expanduser().resolve()
    resolved_root = root_value.expanduser().resolve()
    try:
        resolved_path.relative_to(resolved_root)
    except ValueError as exc:
        raise ValueError(f"Path escapes approved root: {resolved_path}") from exc
    return resolved_path


def def_unique_strings(values: Iterable[str]) -> List[str]:
    output: List[str] = []
    seen = set()
    for value in values:
        normalized = str(value).strip()
        if normalized and normalized not in seen:
            seen.add(normalized)
            output.append(normalized)
    return output


def def_parse_semver(value: str) -> Tuple[int, int, int, Tuple[str, ...]]:
    match = re.fullmatch(r"\s*(\d+)\.(\d+)\.(\d+)(?:[-+]([0-9A-Za-z.-]+))?\s*", value or "")
    if not match:
        raise ValueError(f"Invalid semantic version: {value!r}")
    suffix = tuple((match.group(4) or "").split(".")) if match.group(4) else tuple()
    return int(match.group(1)), int(match.group(2)), int(match.group(3)), suffix


def def_version_in_range(current: str, minimum: str, maximum: str) -> bool:
    current_value = def_parse_semver(current)[:3]
    minimum_value = def_parse_semver(minimum)[:3]
    maximum_value = def_parse_semver(maximum)[:3]
    return minimum_value <= current_value <= maximum_value


def def_generate_grouped_random(groups: Sequence[int], alphabet: str, prefix: str = "") -> str:
    if not groups or any(int(group) <= 0 for group in groups):
        raise ValueError("Random token groups must contain positive lengths")
    if len(set(alphabet)) != len(alphabet) or len(alphabet) < 16:
        raise ValueError("Random token alphabet is too small or contains duplicates")
    parts = ["".join(secrets.choice(alphabet) for _ in range(int(group))) for group in groups]
    body = "-".join(parts)
    return f"{prefix}-{body}" if prefix else body


def def_normalize_product_number(value: str) -> str:
    compact = re.sub(r"[^A-Za-z0-9]", "", str(value or "")).upper()
    if len(compact) != sum(def_PARAM_PRODUCT_NUMBER_GROUPS):
        raise ValueError("Product Number must use XXXX-XXXX-XXXX format (12 symbols)")
    offsets: List[str] = []
    cursor = 0
    for group in def_PARAM_PRODUCT_NUMBER_GROUPS:
        offsets.append(compact[cursor:cursor + group])
        cursor += group
    canonical = "-".join(offsets)
    if not def_PARAM_PRODUCT_NUMBER_RE.fullmatch(canonical):
        raise ValueError("Product Number contains an ambiguous or invalid symbol")
    return canonical


def def_normalize_master_key(value: str) -> str:
    compact = re.sub(r"[^A-Za-z0-9]", "", str(value or "")).upper()
    if compact.startswith(def_PARAM_MASTER_KEY_PREFIX):
        compact = compact[len(def_PARAM_MASTER_KEY_PREFIX):]
    required_length = sum(def_PARAM_MASTER_KEY_GROUPS)
    if len(compact) != required_length:
        raise ValueError("Master KEY has an invalid length")
    if any(character not in def_PARAM_PRODUCT_NUMBER_ALPHABET for character in compact):
        raise ValueError("Master KEY contains an ambiguous or invalid symbol")
    parts: List[str] = []
    cursor = 0
    for group in def_PARAM_MASTER_KEY_GROUPS:
        parts.append(compact[cursor:cursor + group])
        cursor += group
    return f"{def_PARAM_MASTER_KEY_PREFIX}-" + "-".join(parts)


def def_master_key_hash(product_number: str, master_key: str) -> str:
    canonical_number = def_normalize_product_number(product_number)
    canonical_key = def_normalize_master_key(master_key)
    return def_sha256_text(f"VIA-MASTER-KEY-v2.1\0{canonical_number}\0{canonical_key}")


def def_create_product_record(product_sku: str = def_PARAM_PRODUCT_SKU, edition: str = def_PARAM_DEFAULT_EDITION) -> Dict[str, Any]:
    product_number = def_generate_grouped_random(
        def_PARAM_PRODUCT_NUMBER_GROUPS,
        def_PARAM_PRODUCT_NUMBER_ALPHABET,
    )
    master_key = def_generate_grouped_random(
        def_PARAM_MASTER_KEY_GROUPS,
        def_PARAM_PRODUCT_NUMBER_ALPHABET,
        prefix=def_PARAM_MASTER_KEY_PREFIX,
    )
    return {
        "schema": "via.product-record.v2.1",
        "product_sku": product_sku,
        "edition": edition,
        "product_number": product_number,
        "master_key": master_key,
        "master_key_hash": def_master_key_hash(product_number, master_key),
        "created_at": def_now_utc_iso(),
    }


def def_validate_product_record(record: Mapping[str, Any], require_secret: bool = True) -> Dict[str, Any]:
    product_number = def_normalize_product_number(str(record.get("product_number", "")))
    supplied_hash = str(record.get("master_key_hash", "")).lower()
    if not def_PARAM_SHA256_RE.fullmatch(supplied_hash):
        raise ValueError("Product record master_key_hash is invalid")
    master_key = str(record.get("master_key", ""))
    if require_secret:
        canonical_key = def_normalize_master_key(master_key)
        if not secrets.compare_digest(def_master_key_hash(product_number, canonical_key), supplied_hash):
            raise ValueError("Product record Master KEY does not match its commitment")
    else:
        canonical_key = ""
    return {
        "schema": str(record.get("schema", "via.product-record.v2.1")),
        "product_sku": str(record.get("product_sku", def_PARAM_PRODUCT_SKU)),
        "edition": str(record.get("edition", def_PARAM_DEFAULT_EDITION)),
        "product_number": product_number,
        "master_key": canonical_key,
        "master_key_hash": supplied_hash,
        "created_at": str(record.get("created_at", "")),
    }


def def_public_product_binding(record: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = def_validate_product_record(record, require_secret=bool(record.get("master_key")))
    return {
        "schema": "via.product-binding.v2.1",
        "product_sku": normalized["product_sku"],
        "edition": normalized["edition"],
        "product_number": normalized["product_number"],
        "master_key_hash": normalized["master_key_hash"],
        "master_key_id": normalized["master_key_hash"][:16].upper(),
    }


def def_master_key_from_environment(env_name: str = def_PARAM_MASTER_KEY_ENV) -> str:
    secret_value = os.environ.get(env_name, "").strip()
    if not secret_value and sys.stdin.isatty():
        secret_value = getpass.getpass("VIA Master KEY: ")
    if not secret_value:
        raise ValueError(f"Set {env_name}; the Master KEY is never accepted as a command-line argument")
    return def_normalize_master_key(secret_value)


def def_validate_insecure_test_store_flag(requested: bool) -> bool:
    if requested and def_PARAM_BUILD_MODE != "DEVELOPMENT":
        raise RuntimeError("Insecure test key storage is permanently disabled outside DEVELOPMENT mode")
    return bool(requested and def_PARAM_BUILD_MODE == "DEVELOPMENT")


@contextlib.contextmanager
def def_file_lock(path_value: Path, timeout_seconds: float = 30.0) -> Iterator[None]:
    """VDL 3.0 hardening: bounded, OS-owned writer lock; no stale PID deletion."""
    if timeout_seconds <= 0:
        raise ValueError("Lock timeout must be positive")
    lock_path = path_value.with_suffix(path_value.suffix + ".lock")
    def_validate_no_link_chain(lock_path)
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+b") as lock_handle:
        if os.name == "nt":
            import msvcrt
            lock_handle.seek(0, os.SEEK_END)
            if lock_handle.tell() == 0:
                lock_handle.write(b"0")
                lock_handle.flush()
        else:
            import fcntl
        deadline = time.monotonic() + timeout_seconds
        while True:
            try:
                lock_handle.seek(0)
                if os.name == "nt":
                    msvcrt.locking(lock_handle.fileno(), msvcrt.LK_NBLCK, 1)
                else:
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError as error:
                if time.monotonic() >= deadline:
                    raise TimeoutError("Concurrent VIA operation holds writer lock") from error
                time.sleep(min(0.05, timeout_seconds))
        try:
            yield
        finally:
            lock_handle.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock_handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock_handle.fileno(), fcntl.LOCK_UN)


def def_append_audit_event(path_value: Path, event_type: str, details: Mapping[str, Any]) -> Dict[str, Any]:
    with def_file_lock(path_value):
        previous_hash = "GENESIS"
        sequence = 1
        if path_value.exists():
            last_line = ""
            with path_value.open("r", encoding="utf-8") as existing_handle:
                for line in existing_handle:
                    if line.strip():
                        last_line = line
            if last_line:
                previous = json.loads(last_line)
                previous_hash = str(previous.get("event_hash", ""))
                sequence = int(previous.get("sequence", 0)) + 1
        event = {
            "schema": "via.audit.v2",
            "sequence": sequence,
            "event_id": str(uuid.uuid4()),
            "event_type": event_type,
            "recorded_at": def_now_utc_iso(),
            "previous_hash": previous_hash,
            "details": dict(details),
        }
        event["event_hash"] = def_sha256_bytes(def_canonical_json_bytes(event))
        path_value.parent.mkdir(parents=True, exist_ok=True)
        with path_value.open("a", encoding="utf-8", newline="\n") as file_handle:
            file_handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            file_handle.flush()
            os.fsync(file_handle.fileno())
        return event


def def_verify_audit_chain(path_value: Path) -> def_CommandResult:
    if not path_value.exists():
        return def_CommandResult(False, "AUDIT_MISSING", errors=[str(path_value)])
    previous_hash = "GENESIS"
    count = 0
    with path_value.open("r", encoding="utf-8") as audit_handle:
        for line_number, line in enumerate(audit_handle, start=1):
            if not line.strip():
                continue
            event = json.loads(line, object_pairs_hook=def_json_object_no_duplicates)
            supplied_hash = event.pop("event_hash", "")
            calculated_hash = def_sha256_bytes(def_canonical_json_bytes(event))
            expected_sequence = count + 1
            if (
                supplied_hash != calculated_hash
                or event.get("previous_hash") != previous_hash
                or event.get("sequence") != expected_sequence
                or event.get("schema") != "via.audit.v2"
            ):
                return def_CommandResult(False, "AUDIT_CHAIN_BROKEN", errors=[f"line={line_number}"])
            previous_hash = supplied_hash
            count += 1
    return def_CommandResult(True, "AUDIT_CHAIN_VALID", data={"events": count, "head": previous_hash})


# =============================================================================
# def CRYPTOGRAPHIC PRIMITIVES
# =============================================================================
def def_require_cryptography() -> Dict[str, Any]:
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
        from cryptography.hazmat.primitives.asymmetric.x25519 import X25519PrivateKey, X25519PublicKey
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF
        return {
            "serialization": serialization,
            "hashes": hashes,
            "private_class": Ed25519PrivateKey,
            "public_class": Ed25519PublicKey,
            "x25519_private_class": X25519PrivateKey,
            "x25519_public_class": X25519PublicKey,
            "aesgcm_class": AESGCM,
            "hkdf_class": HKDF,
        }
    except Exception as exc:
        raise RuntimeError("cryptography is required for production signing and verification") from exc


def def_generate_ed25519_keypair(
    private_path: Path,
    public_path: Path,
    password_env: str = def_PARAM_PRIVATE_KEY_PASSWORD_ENV,
    overwrite: bool = False,
) -> Dict[str, Any]:
    crypto = def_require_cryptography()
    serialization = crypto["serialization"]
    private_key = crypto["private_class"].generate()
    password_text = os.environ.get(password_env, "")
    if not password_text and sys.stdin.isatty():
        password_text = getpass.getpass(f"Passphrase for {private_path.name}: ")
    if not password_text:
        raise ValueError(f"Set {password_env}; unencrypted production private keys are forbidden")
    private_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.BestAvailableEncryption(password_text.encode("utf-8")),
    )
    public_bytes = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    def_atomic_write_bytes(private_path, private_bytes, overwrite=overwrite)
    try:
        os.chmod(private_path, 0o600)
    except OSError:
        pass
    def_atomic_write_bytes(public_path, public_bytes, overwrite=overwrite)
    return {
        "ok": True,
        "private_key": str(private_path),
        "public_key": str(public_path),
        "public_key_sha256": def_sha256_bytes(public_bytes),
    }


def def_load_private_key(path_value: Path, password_env: str = def_PARAM_PRIVATE_KEY_PASSWORD_ENV) -> Any:
    crypto = def_require_cryptography()
    password_text = os.environ.get(password_env, "")
    if not password_text and sys.stdin.isatty():
        password_text = getpass.getpass(f"Passphrase for {path_value.name}: ")
    if def_PARAM_BUILD_MODE == "PRODUCTION" and not password_text:
        raise RuntimeError("Production private keys must be encrypted and unlocked through the configured secret channel")
    password_bytes = password_text.encode("utf-8") if password_text else None
    return crypto["serialization"].load_pem_private_key(path_value.read_bytes(), password=password_bytes)


def def_load_public_key(path_value: Path) -> Any:
    crypto = def_require_cryptography()
    return crypto["serialization"].load_pem_public_key(path_value.read_bytes())


def def_load_trusted_public_key(
    path_value: Path,
    configured_sha256: str,
    development_sha256: str = "",
) -> Any:
    public_bytes = path_value.read_bytes()
    actual_sha256 = def_sha256_bytes(public_bytes)
    expected_sha256 = configured_sha256.strip().lower()
    if not expected_sha256 and def_PARAM_BUILD_MODE == "DEVELOPMENT":
        expected_sha256 = development_sha256.strip().lower()
    if def_PARAM_REQUIRE_PINNED_KEYS and not expected_sha256:
        raise RuntimeError("Trusted public-key SHA-256 is not configured; fail-closed")
    if expected_sha256:
        if not def_PARAM_SHA256_RE.fullmatch(expected_sha256):
            raise ValueError("Trusted public-key SHA-256 pin is malformed")
        if not secrets.compare_digest(actual_sha256, expected_sha256):
            raise ValueError("Trusted public-key SHA-256 pin mismatch")
    crypto = def_require_cryptography()
    return crypto["serialization"].load_pem_public_key(public_bytes)


def def_public_key_raw_b64(public_key: Any) -> str:
    crypto = def_require_cryptography()
    serialization = crypto["serialization"]
    raw = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return def_b64u_encode(raw)


def def_public_key_from_raw_b64(value: str) -> Any:
    crypto = def_require_cryptography()
    return crypto["public_class"].from_public_bytes(def_b64u_decode(value))


def def_sign_payload(payload: Mapping[str, Any], private_key: Any, key_id: str, envelope_schema: str) -> Dict[str, Any]:
    payload_dict = dict(payload)
    signature = private_key.sign(def_canonical_json_bytes(payload_dict))
    return {
        "schema": envelope_schema,
        "algorithm": "Ed25519",
        "key_id": key_id,
        "payload": payload_dict,
        "signature": def_b64u_encode(signature),
    }


def def_verify_signed_payload(
    envelope: Mapping[str, Any],
    public_key: Any,
    expected_key_id: str = "",
    expected_schema: str = "",
) -> Dict[str, Any]:
    if envelope.get("algorithm") != "Ed25519":
        raise ValueError("Unsupported signature algorithm")
    if expected_key_id and envelope.get("key_id") != expected_key_id:
        raise ValueError("Unexpected key_id")
    if expected_schema and envelope.get("schema") != expected_schema:
        raise ValueError("Unexpected envelope schema")
    payload = envelope.get("payload")
    if not isinstance(payload, dict):
        raise ValueError("Signed envelope payload must be an object")
    public_key.verify(def_b64u_decode(str(envelope.get("signature", ""))), def_canonical_json_bytes(payload))
    return payload


def def_generate_x25519_keypair(
    private_path: Path,
    public_path: Path,
    password_env: str = def_PARAM_PRIVATE_KEY_PASSWORD_ENV,
    overwrite: bool = False,
) -> Dict[str, Any]:
    crypto = def_require_cryptography()
    serialization = crypto["serialization"]
    private_key = crypto["x25519_private_class"].generate()
    password_text = os.environ.get(password_env, "")
    if not password_text and sys.stdin.isatty():
        password_text = getpass.getpass(f"Passphrase for {private_path.name}: ")
    if not password_text:
        raise ValueError(f"Set {password_env}; unencrypted transport private keys are forbidden")
    private_bytes = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.BestAvailableEncryption(password_text.encode("utf-8")),
    )
    public_bytes = private_key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    def_atomic_write_bytes(private_path, private_bytes, overwrite=overwrite)
    try:
        os.chmod(private_path, 0o600)
    except OSError:
        pass
    def_atomic_write_bytes(public_path, public_bytes, overwrite=overwrite)
    raw_public = private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return {
        "ok": True,
        "private_key": str(private_path),
        "public_key": str(public_path),
        "public_key_raw": def_b64u_encode(raw_public),
        "public_key_sha256": def_sha256_bytes(public_bytes),
    }


def def_x25519_public_raw_b64(public_key: Any) -> str:
    crypto = def_require_cryptography()
    if not isinstance(public_key, crypto["x25519_public_class"]):
        raise TypeError("Expected an X25519 public key")
    serialization = crypto["serialization"]
    raw = public_key.public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return def_b64u_encode(raw)


def def_x25519_public_from_raw_b64(value: str) -> Any:
    crypto = def_require_cryptography()
    return crypto["x25519_public_class"].from_public_bytes(def_b64u_decode(value))


def def_encrypt_json_for_recipient(
    payload: Mapping[str, Any],
    recipient_public_key_b64: str,
    aad_context: Mapping[str, Any],
) -> Dict[str, Any]:
    crypto = def_require_cryptography()
    ephemeral_private = crypto["x25519_private_class"].generate()
    recipient_public = def_x25519_public_from_raw_b64(recipient_public_key_b64)
    salt = secrets.token_bytes(32)
    shared_secret = ephemeral_private.exchange(recipient_public)
    derived_key = crypto["hkdf_class"](
        algorithm=crypto["hashes"].SHA256(),
        length=32,
        salt=salt,
        info=b"VIA-HYBRID-CLOUD-PAYLOAD-v2",
    ).derive(shared_secret)
    nonce = secrets.token_bytes(12)
    aad_bytes = def_canonical_json_bytes(dict(aad_context))
    plaintext = def_canonical_json_bytes(dict(payload))
    ciphertext = crypto["aesgcm_class"](derived_key).encrypt(nonce, plaintext, aad_bytes)
    return {
        "schema": "via.encrypted-json.v2",
        "algorithm": "X25519-HKDF-SHA256+A256GCM",
        "ephemeral_public_key": def_x25519_public_raw_b64(ephemeral_private.public_key()),
        "salt": def_b64u_encode(salt),
        "nonce": def_b64u_encode(nonce),
        "aad": dict(aad_context),
        "ciphertext": def_b64u_encode(ciphertext),
    }


def def_decrypt_json_from_sender(envelope: Mapping[str, Any], recipient_private_key: Any) -> Dict[str, Any]:
    if envelope.get("schema") != "via.encrypted-json.v2":
        raise ValueError("Unsupported encrypted payload schema")
    if envelope.get("algorithm") != "X25519-HKDF-SHA256+A256GCM":
        raise ValueError("Unsupported encrypted payload algorithm")
    crypto = def_require_cryptography()
    ephemeral_public = def_x25519_public_from_raw_b64(str(envelope.get("ephemeral_public_key", "")))
    shared_secret = recipient_private_key.exchange(ephemeral_public)
    derived_key = crypto["hkdf_class"](
        algorithm=crypto["hashes"].SHA256(),
        length=32,
        salt=def_b64u_decode(str(envelope.get("salt", ""))),
        info=b"VIA-HYBRID-CLOUD-PAYLOAD-v2",
    ).derive(shared_secret)
    plaintext = crypto["aesgcm_class"](derived_key).decrypt(
        def_b64u_decode(str(envelope.get("nonce", ""))),
        def_b64u_decode(str(envelope.get("ciphertext", ""))),
        def_canonical_json_bytes(envelope.get("aad", {})),
    )
    decoded = json.loads(plaintext.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("Decrypted payload must be an object")
    return decoded


# =============================================================================
# def WINDOWS DEVICE KEY PROTECTION AND DEVICE EVIDENCE
# =============================================================================
class def_DATA_BLOB(ctypes.Structure):
    _fields_ = [("cbData", ctypes.c_uint32), ("pbData", ctypes.POINTER(ctypes.c_ubyte))]


def def_bytes_to_blob(value: bytes) -> Tuple[def_DATA_BLOB, Any]:
    buffer_value = ctypes.create_string_buffer(value, len(value))
    blob = def_DATA_BLOB(len(value), ctypes.cast(buffer_value, ctypes.POINTER(ctypes.c_ubyte)))
    return blob, buffer_value


def def_windows_crypto_apis() -> Tuple[Any, Any]:
    if os.name != "nt":
        raise RuntimeError("Windows cryptographic APIs are unavailable")
    crypt32 = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    blob_pointer = ctypes.POINTER(def_DATA_BLOB)
    crypt32.CryptProtectData.argtypes = [
        blob_pointer, ctypes.c_wchar_p, blob_pointer, ctypes.c_void_p,
        ctypes.c_void_p, ctypes.c_uint32, blob_pointer,
    ]
    crypt32.CryptProtectData.restype = ctypes.c_bool
    crypt32.CryptUnprotectData.argtypes = [
        blob_pointer, ctypes.POINTER(ctypes.c_wchar_p), blob_pointer,
        ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint32, blob_pointer,
    ]
    crypt32.CryptUnprotectData.restype = ctypes.c_bool
    kernel32.LocalFree.argtypes = [ctypes.c_void_p]
    kernel32.LocalFree.restype = ctypes.c_void_p
    return crypt32, kernel32


def def_dpapi_protect(value: bytes) -> bytes:
    if os.name != "nt":
        raise RuntimeError("DPAPI is available only on Windows")
    input_blob, input_buffer = def_bytes_to_blob(value)
    output_blob = def_DATA_BLOB()
    description = "VIA device private key"
    crypt32, kernel32 = def_windows_crypto_apis()
    success = crypt32.CryptProtectData(
        ctypes.byref(input_blob), description, None, None, None, 0, ctypes.byref(output_blob)
    )
    _ = input_buffer
    if not success:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(output_blob.pbData, ctypes.c_void_p))


def def_dpapi_unprotect(value: bytes) -> bytes:
    if os.name != "nt":
        raise RuntimeError("DPAPI is available only on Windows")
    input_blob, input_buffer = def_bytes_to_blob(value)
    output_blob = def_DATA_BLOB()
    description_pointer = ctypes.c_wchar_p()
    crypt32, kernel32 = def_windows_crypto_apis()
    success = crypt32.CryptUnprotectData(
        ctypes.byref(input_blob), ctypes.byref(description_pointer), None, None, None, 0, ctypes.byref(output_blob)
    )
    _ = input_buffer
    if not success:
        raise ctypes.WinError()
    try:
        return ctypes.string_at(output_blob.pbData, output_blob.cbData)
    finally:
        kernel32.LocalFree(ctypes.cast(output_blob.pbData, ctypes.c_void_p))
        if description_pointer:
            kernel32.LocalFree(ctypes.cast(description_pointer, ctypes.c_void_p))


def def_create_device_key_file(path_value: Path, allow_insecure_test_store: bool = False) -> Dict[str, Any]:
    allow_insecure_test_store = def_validate_insecure_test_store_flag(allow_insecure_test_store)
    crypto = def_require_cryptography()
    serialization = crypto["serialization"]
    private_key = crypto["private_class"].generate()
    private_bytes = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    if os.name == "nt":
        storage = "WINDOWS_DPAPI_USER"
        protected = def_dpapi_protect(private_bytes)
    elif allow_insecure_test_store:
        storage = "TEST_ONLY_PLAINTEXT"
        protected = private_bytes
    else:
        raise RuntimeError("Production device-key persistence requires Windows DPAPI")
    payload = {
        "schema": "via.device-key.v2",
        "storage": storage,
        "created_at": def_now_utc_iso(),
        "protected_private_key": def_b64u_encode(protected),
        "public_key": def_public_key_raw_b64(private_key.public_key()),
    }
    def_write_json(path_value, payload, overwrite=False)
    try:
        os.chmod(path_value, 0o600)
    except OSError:
        pass
    return {"ok": True, "path": str(path_value), "storage": storage, "public_key": payload["public_key"]}


def def_load_device_private_key(path_value: Path, allow_insecure_test_store: bool = False) -> Any:
    allow_insecure_test_store = def_validate_insecure_test_store_flag(allow_insecure_test_store)
    crypto = def_require_cryptography()
    payload = def_read_json(path_value)
    storage = payload.get("storage")
    protected = def_b64u_decode(str(payload.get("protected_private_key", "")))
    if storage == "WINDOWS_DPAPI_USER":
        private_bytes = def_dpapi_unprotect(protected)
    elif storage == "TEST_ONLY_PLAINTEXT" and allow_insecure_test_store:
        private_bytes = protected
    else:
        raise RuntimeError("Unsupported or forbidden device-key storage")
    private_key = crypto["serialization"].load_pem_private_key(private_bytes, password=None)
    actual_public = def_public_key_raw_b64(private_key.public_key())
    if actual_public != payload.get("public_key"):
        raise ValueError("Device key file integrity mismatch")
    return private_key


def def_get_or_create_device_key(path_value: Path, allow_insecure_test_store: bool = False) -> Any:
    if not path_value.exists():
        def_create_device_key_file(path_value, allow_insecure_test_store=allow_insecure_test_store)
    return def_load_device_private_key(path_value, allow_insecure_test_store=allow_insecure_test_store)


def def_store_product_key_state(
    path_value: Path,
    product_number: str,
    master_key: str,
    allow_insecure_test_store: bool = False,
    overwrite: bool = False,
) -> Dict[str, Any]:
    allow_insecure_test_store = def_validate_insecure_test_store_flag(allow_insecure_test_store)
    canonical_number = def_normalize_product_number(product_number)
    canonical_key = def_normalize_master_key(master_key)
    key_bytes = canonical_key.encode("utf-8")
    if os.name == "nt":
        storage = "WINDOWS_DPAPI_USER"
        protected = def_dpapi_protect(key_bytes)
    elif allow_insecure_test_store:
        storage = "TEST_ONLY_PLAINTEXT"
        protected = key_bytes
    else:
        raise RuntimeError("Production Product KEY persistence requires Windows DPAPI")
    payload = {
        "schema": "via.product-key-state.v2.1",
        "storage": storage,
        "product_number": canonical_number,
        "master_key_hash": def_master_key_hash(canonical_number, canonical_key),
        "protected_master_key": def_b64u_encode(protected),
        "created_at": def_now_utc_iso(),
    }
    def_write_json(path_value, payload, overwrite=overwrite)
    try:
        os.chmod(path_value, 0o600)
    except OSError:
        pass
    return {
        "ok": True,
        "path": str(path_value),
        "storage": storage,
        "product_number": canonical_number,
        "master_key_hash": payload["master_key_hash"],
    }


def def_load_product_key_state(path_value: Path, allow_insecure_test_store: bool = False) -> Dict[str, str]:
    allow_insecure_test_store = def_validate_insecure_test_store_flag(allow_insecure_test_store)
    payload = def_read_json(path_value)
    storage = str(payload.get("storage", ""))
    protected = def_b64u_decode(str(payload.get("protected_master_key", "")))
    if storage == "WINDOWS_DPAPI_USER":
        key_bytes = def_dpapi_unprotect(protected)
    elif storage == "TEST_ONLY_PLAINTEXT" and allow_insecure_test_store:
        key_bytes = protected
    else:
        raise RuntimeError("Unsupported or forbidden Product KEY storage")
    product_number = def_normalize_product_number(str(payload.get("product_number", "")))
    master_key = def_normalize_master_key(key_bytes.decode("utf-8"))
    calculated_hash = def_master_key_hash(product_number, master_key)
    if not secrets.compare_digest(calculated_hash, str(payload.get("master_key_hash", ""))):
        raise ValueError("Product KEY state integrity mismatch")
    return {
        "product_number": product_number,
        "master_key": master_key,
        "master_key_hash": calculated_hash,
    }


def def_normalize_hardware_signal(value: Any) -> str:
    normalized = re.sub(r"[^A-Za-z0-9._:-]+", "", str(value or "").strip().upper())
    invalid = {"", "NONE", "NULL", "UNKNOWN", "DEFAULTSTRING", "TOBEFILLEDBYO.E.M."}
    return "" if normalized in invalid else normalized


def def_collect_windows_pc_signals(overrides: Optional[Mapping[str, Any]] = None) -> Dict[str, str]:
    if overrides is not None:
        raw_payload = dict(overrides)
    else:
        if os.name != "nt":
            raise RuntimeError("PC hardware collection is Windows-only; use a controlled override for tests")
        powershell = shutil.which("pwsh") or shutil.which("powershell")
        if not powershell:
            raise RuntimeError("PowerShell is required for CIM device evidence")
        command = (
            "$ErrorActionPreference='SilentlyContinue';"
            "$cpu=(Get-CimInstance -ClassName Win32_Processor|Select-Object -First 1 -ExpandProperty ProcessorId);"
            "$board=(Get-CimInstance -ClassName Win32_BaseBoard|Select-Object -First 1 -ExpandProperty SerialNumber);"
            "$mg=(Get-ItemPropertyValue -Path 'HKLM:\\SOFTWARE\\Microsoft\\Cryptography' -Name MachineGuid);"
            "[pscustomobject]@{cpu=$cpu;board=$board;machine_guid=$mg}|ConvertTo-Json -Compress"
        )
        completed = subprocess.run(
            [powershell, "-NoProfile", "-NonInteractive", "-Command", command],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if completed.returncode != 0:
            raise RuntimeError(f"CIM collection failed: {completed.stderr.strip()}")
        raw_payload = json.loads(completed.stdout)
    normalized = {
        "cpu": def_normalize_hardware_signal(raw_payload.get("cpu")),
        "board": def_normalize_hardware_signal(raw_payload.get("board")),
        "machine_guid": def_normalize_hardware_signal(raw_payload.get("machine_guid")),
    }
    if sum(bool(value) for value in normalized.values()) < def_PARAM_DEVICE_QUORUM:
        raise ValueError("Fewer than two usable PC hardware signals")
    return normalized


def def_hash_hardware_signals(signals: Mapping[str, str], product_salt: str = def_PARAM_PRODUCT_SALT) -> Dict[str, str]:
    output: Dict[str, str] = {}
    for signal_name in ("cpu", "board", "machine_guid"):
        value = def_normalize_hardware_signal(signals.get(signal_name, ""))
        if value:
            output[signal_name] = def_sha256_text(f"{product_salt}\0{signal_name}\0{value}")
    return output


def def_device_id(public_key_b64: str, hardware_hashes: Mapping[str, str]) -> str:
    joined = "|".join(f"{key}:{hardware_hashes[key]}" for key in sorted(hardware_hashes))
    return def_sha256_text(f"{public_key_b64}|{joined}")[:32].upper()


def def_hardware_match_count(expected: Mapping[str, str], actual: Mapping[str, str]) -> int:
    return sum(1 for key, value in expected.items() if value and secrets.compare_digest(value, actual.get(key, "")))


# =============================================================================
# def ACTIVATION REQUEST AND SIGNED LICENSE
# =============================================================================
def def_create_activation_request(
    private_key: Any,
    product_sku: str,
    edition: str,
    product_number: str,
    master_key: str,
    device_type: str,
    hardware_hashes: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    normalized_type = device_type.strip().lower()
    if normalized_type not in def_PARAM_ALLOWED_DEVICE_TYPES:
        raise ValueError("device_type must be pc or mobile")
    hashes = dict(hardware_hashes or {})
    if normalized_type == "pc" and len(hashes) < def_PARAM_DEVICE_QUORUM:
        raise ValueError("PC activation requires at least two hardware hashes")
    if normalized_type == "mobile" and hashes:
        raise ValueError("Mobile activation uses an app key, not hardware identifiers")
    canonical_product_number = def_normalize_product_number(product_number)
    canonical_master_key_hash = def_master_key_hash(canonical_product_number, master_key)
    public_key_b64 = def_public_key_raw_b64(private_key.public_key())
    payload = {
        "schema": "via.activation-request.v2",
        "request_id": str(uuid.uuid4()),
        "product_sku": product_sku,
        "requested_edition": edition,
        "product_number": canonical_product_number,
        "master_key_hash": canonical_master_key_hash,
        "device_type": normalized_type,
        "device_id": def_device_id(public_key_b64, hashes),
        "device_public_key": public_key_b64,
        "hardware_hashes": hashes,
        "client_nonce": def_b64u_encode(secrets.token_bytes(24)),
        "created_at": def_now_utc_iso(),
    }
    return def_sign_payload(payload, private_key, payload["device_id"], "via.activation-envelope.v2")


def def_verify_activation_request(envelope: Mapping[str, Any], max_age_seconds: int = def_PARAM_REQUEST_MAX_AGE_SECONDS) -> Dict[str, Any]:
    payload_candidate = envelope.get("payload")
    if not isinstance(payload_candidate, dict):
        raise ValueError("Activation request payload missing")
    public_key = def_public_key_from_raw_b64(str(payload_candidate.get("device_public_key", "")))
    payload = def_verify_signed_payload(envelope, public_key, expected_schema="via.activation-envelope.v2")
    expected_id = def_device_id(str(payload["device_public_key"]), payload.get("hardware_hashes", {}))
    if payload.get("device_id") != expected_id or envelope.get("key_id") != expected_id:
        raise ValueError("Activation device identity mismatch")
    device_type = str(payload.get("device_type", "")).lower()
    if device_type not in def_PARAM_ALLOWED_DEVICE_TYPES:
        raise ValueError("Invalid activation device type")
    if device_type == "pc" and len(payload.get("hardware_hashes", {})) < def_PARAM_DEVICE_QUORUM:
        raise ValueError("PC activation evidence below quorum")
    if device_type == "mobile" and payload.get("hardware_hashes"):
        raise ValueError("Mobile activation must not contain hardware hashes")
    def_normalize_product_number(str(payload.get("product_number", "")))
    if not def_PARAM_SHA256_RE.fullmatch(str(payload.get("master_key_hash", ""))):
        raise ValueError("Activation Master KEY commitment is invalid")
    age = abs((def_now_utc() - def_parse_utc(str(payload.get("created_at", "")))).total_seconds())
    if age > max_age_seconds:
        raise ValueError("Activation request expired")
    return payload


def def_validate_profile(profile: Mapping[str, Any]) -> Dict[str, Any]:
    profile = def_require_mapping(profile, "profile")
    required = [
        "product_sku", "edition", "product_number", "master_key_hash",
        "entitlements", "max_devices", "version_min", "version_max",
    ]
    missing = [key for key in required if key not in profile]
    if missing:
        raise ValueError(f"Profile missing fields: {missing}")
    raw_entitlements = def_require_list(profile.get("entitlements"), "profile.entitlements")
    if any(not isinstance(item, str) for item in raw_entitlements):
        raise ValueError("profile.entitlements must contain strings only")
    entitlements = def_unique_strings(item.upper() for item in raw_entitlements)
    if not entitlements or any(not def_PARAM_CAPABILITY_RE.fullmatch(item) for item in entitlements):
        raise ValueError("Profile entitlements are invalid")
    product_number = def_normalize_product_number(str(profile["product_number"]))
    master_key_hash = str(profile["master_key_hash"]).lower()
    if not def_PARAM_SHA256_RE.fullmatch(master_key_hash):
        raise ValueError("Profile Master KEY commitment is invalid")
    max_devices = def_require_mapping(profile.get("max_devices"), "profile.max_devices")
    pc_limit = def_require_int(max_devices.get("pc"), "profile.max_devices.pc", 0, def_PARAM_MAX_PC_DEVICES)
    mobile_limit = def_require_int(max_devices.get("mobile"), "profile.max_devices.mobile", 0, def_PARAM_MAX_MOBILE_DEVICES)
    mobile_policy_raw = profile.get("mobile_policy", {"allowed": mobile_limit > 0, "required": False})
    mobile_policy = def_require_mapping(mobile_policy_raw, "profile.mobile_policy")
    mobile_allowed = def_require_native_bool(mobile_policy.get("allowed"), "profile.mobile_policy.allowed")
    mobile_required = def_require_native_bool(mobile_policy.get("required"), "profile.mobile_policy.required")
    if mobile_required and not mobile_allowed:
        raise ValueError("Required mobile policy must also allow mobile")
    if mobile_allowed != (mobile_limit > 0):
        raise ValueError("Mobile policy and signed mobile device limit disagree")
    binding_revision = def_require_int(profile.get("binding_revision", 1), "profile.binding_revision", 1)
    version_min = profile["version_min"]
    version_max = profile["version_max"]
    if not isinstance(version_min, str) or not isinstance(version_max, str):
        raise ValueError("Profile version bounds must be strings")
    def_parse_semver(version_min)
    def_parse_semver(version_max)
    if def_parse_semver(version_min)[:3] > def_parse_semver(version_max)[:3]:
        raise ValueError("Profile version_min cannot exceed version_max")
    return {
        **dict(profile),
        "product_number": product_number,
        "master_key_hash": master_key_hash,
        "entitlements": entitlements,
        "max_devices": {"pc": pc_limit, "mobile": mobile_limit},
        "mobile_policy": {"allowed": mobile_allowed, "required": mobile_required},
        "binding_revision": binding_revision,
    }


def def_issue_license(
    activation_envelopes: Sequence[Mapping[str, Any]],
    profile: Mapping[str, Any],
    authority_private_key: Any,
    key_id: str = def_PARAM_LICENSE_KEY_ID,
    customer_ref: str = "",
    now_value: Optional[datetime] = None,
) -> Dict[str, Any]:
    normalized_profile = def_validate_profile(profile)
    requests = [def_verify_activation_request(item) for item in activation_envelopes]
    if not requests:
        raise ValueError("At least one activation request is required")
    for request in requests:
        if request["product_sku"] != normalized_profile["product_sku"]:
            raise ValueError("Activation product_sku does not match profile")
        if request["requested_edition"] != normalized_profile["edition"]:
            raise ValueError("Activation edition does not match profile")
        if request["product_number"] != normalized_profile["product_number"]:
            raise ValueError("Activation Product Number does not match profile")
        if not secrets.compare_digest(request["master_key_hash"], normalized_profile["master_key_hash"]):
            raise ValueError("Activation Master KEY does not match profile")
    device_ids = [str(item["device_id"]) for item in requests]
    if len(device_ids) != len(set(device_ids)):
        raise ValueError("Duplicate activation device")
    counts = {device_type: sum(1 for item in requests if item["device_type"] == device_type) for device_type in def_PARAM_ALLOWED_DEVICE_TYPES}
    for device_type, count in counts.items():
        if count > int(normalized_profile["max_devices"].get(device_type, 0)):
            raise ValueError(f"{device_type} device limit exceeded")
    if normalized_profile["mobile_policy"]["required"] and counts.get("mobile", 0) != 1:
        raise ValueError("This product profile requires exactly one paired mobile device")
    now_value = (now_value or def_now_utc()).astimezone(timezone.utc)
    claims = {
        "schema": "via.license-claims.v2",
        "license_id": str(uuid.uuid4()),
        "product_sku": normalized_profile["product_sku"],
        "edition": normalized_profile["edition"],
        "product_number": normalized_profile["product_number"],
        "master_key_hash": normalized_profile["master_key_hash"],
        "master_key_id": normalized_profile["master_key_hash"][:16].upper(),
        "customer_ref_hash": def_sha256_text(customer_ref) if customer_ref else "",
        "version_min": normalized_profile["version_min"],
        "version_max": normalized_profile["version_max"],
        "entitlements": normalized_profile["entitlements"],
        "max_devices": normalized_profile["max_devices"],
        "mobile_policy": normalized_profile["mobile_policy"],
        "binding_revision": normalized_profile["binding_revision"],
        "devices": [
            {
                "device_type": item["device_type"],
                "device_id": item["device_id"],
                "device_public_key": item["device_public_key"],
                "hardware_hashes": item.get("hardware_hashes", {}),
                "registered_at": now_value.isoformat().replace("+00:00", "Z"),
            }
            for item in requests
        ],
        "issued_at": now_value.isoformat().replace("+00:00", "Z"),
        "not_before": normalized_profile.get("not_before") or now_value.isoformat().replace("+00:00", "Z"),
        "expires_at": normalized_profile.get("expires_at"),
        "release_channel": normalized_profile.get("release_channel", def_PARAM_RELEASE_CHANNEL),
        "license_nonce": def_b64u_encode(secrets.token_bytes(24)),
    }
    return def_sign_payload(claims, authority_private_key, key_id, "via.license-envelope.v2")


def def_validate_clock_state(
    state_path: Optional[Path],
    device_public_key: Any,
    license_id: str,
    now_value: datetime,
    tolerance_seconds: int = def_PARAM_CLOCK_ROLLBACK_TOLERANCE_SECONDS,
) -> int:
    if state_path is None or not state_path.exists():
        return 0
    envelope = def_read_json(state_path)
    payload = def_verify_signed_payload(envelope, device_public_key, expected_schema="via.clock-state-envelope.v2")
    if payload.get("license_id") != license_id:
        raise ValueError("Clock state belongs to another license")
    last_seen = def_parse_utc(str(payload.get("last_seen_utc", "")))
    if now_value + timedelta(seconds=tolerance_seconds) < last_seen:
        raise ValueError("System clock rollback detected")
    return int(payload.get("sequence", 0))


def def_write_clock_state(
    state_path: Optional[Path],
    device_private_key: Any,
    license_id: str,
    sequence: int,
    now_value: datetime,
) -> None:
    if state_path is None:
        return
    device_id_key = def_public_key_raw_b64(device_private_key.public_key())
    payload = {
        "schema": "via.clock-state.v2",
        "license_id": license_id,
        "sequence": sequence + 1,
        "last_seen_utc": now_value.isoformat().replace("+00:00", "Z"),
    }
    envelope = def_sign_payload(payload, device_private_key, def_sha256_text(device_id_key)[:16], "via.clock-state-envelope.v2")
    def_write_json(state_path, envelope, overwrite=True)


def def_verify_license(
    license_envelope: Mapping[str, Any],
    authority_public_key: Any,
    device_private_key: Any,
    product_sku: str,
    product_version: str,
    product_number: str,
    master_key: str,
    required_entitlement: str = "",
    current_hardware_hashes: Optional[Mapping[str, str]] = None,
    device_type: str = "pc",
    expected_key_id: str = def_PARAM_LICENSE_KEY_ID,
    state_path: Optional[Path] = None,
    update_clock_state: bool = False,
    now_value: Optional[datetime] = None,
) -> def_CommandResult:
    try:
        claims = def_verify_signed_payload(
            license_envelope,
            authority_public_key,
            expected_key_id=expected_key_id,
            expected_schema="via.license-envelope.v2",
        )
        now_value = (now_value or def_now_utc()).astimezone(timezone.utc)
        if claims.get("schema") != "via.license-claims.v2":
            raise ValueError("Unsupported license claim schema")
        if claims.get("product_sku") != product_sku:
            raise ValueError("Wrong product_sku")
        canonical_product_number = def_normalize_product_number(product_number)
        if claims.get("product_number") != canonical_product_number:
            raise ValueError("Wrong Product Number")
        calculated_master_key_hash = def_master_key_hash(canonical_product_number, master_key)
        if not secrets.compare_digest(str(claims.get("master_key_hash", "")), calculated_master_key_hash):
            raise ValueError("Master KEY rejected")
        if not def_version_in_range(product_version, str(claims["version_min"]), str(claims["version_max"])):
            raise ValueError("Product version is outside the licensed range")
        if now_value < def_parse_utc(str(claims["not_before"])):
            raise ValueError("License not_before has not started")
        if claims.get("expires_at") and now_value > def_parse_utc(str(claims["expires_at"])):
            raise ValueError("License expired")
        entitlements = {str(item).upper() for item in claims.get("entitlements", [])}
        if required_entitlement and required_entitlement.upper() not in entitlements:
            raise ValueError("Required entitlement is absent")
        max_devices = claims.get("max_devices", {})
        devices = claims.get("devices", [])
        for allowed_type in def_PARAM_ALLOWED_DEVICE_TYPES:
            if sum(1 for item in devices if item.get("device_type") == allowed_type) > int(max_devices.get(allowed_type, 0)):
                raise ValueError(f"Signed claims exceed {allowed_type} device limit")
        normalized_type = device_type.lower()
        public_key_b64 = def_public_key_raw_b64(device_private_key.public_key())
        candidates = [
            item for item in devices
            if item.get("device_type") == normalized_type and secrets.compare_digest(str(item.get("device_public_key", "")), public_key_b64)
        ]
        if len(candidates) != 1:
            raise ValueError("This device key is not licensed")
        binding = candidates[0]
        match_count = 0
        if normalized_type == "pc":
            match_count = def_hardware_match_count(binding.get("hardware_hashes", {}), current_hardware_hashes or {})
            if match_count < def_PARAM_DEVICE_QUORUM:
                raise ValueError("PC hardware quorum failed")
        elif normalized_type != "mobile":
            raise ValueError("Invalid device_type")
        sequence = def_validate_clock_state(state_path, device_private_key.public_key(), str(claims["license_id"]), now_value)
        if update_clock_state:
            def_write_clock_state(state_path, device_private_key, str(claims["license_id"]), sequence, now_value)
        return def_CommandResult(
            True,
            "LICENSE_VALID",
            data={
                "license_id": claims["license_id"],
                "edition": claims["edition"],
                "product_number": claims["product_number"],
                "master_key_hash": claims["master_key_hash"],
                "master_key_id": claims["master_key_id"],
                "device_id": binding["device_id"],
                "device_type": normalized_type,
                "hardware_matches": match_count,
                "entitlements": sorted(entitlements),
                "expires_at": claims.get("expires_at"),
            },
        )
    except Exception as exc:
        return def_CommandResult(False, "LICENSE_INVALID", errors=[str(exc)])


# =============================================================================
# def MODULE MANIFEST, INTEGRITY, AND ENTITLEMENT HANDSHAKE
# =============================================================================
def def_default_module_compatibility(artifact_path: Path) -> Dict[str, Any]:
    artifact_kind = artifact_path.suffix.lower().lstrip(".")
    python_abi = f"cp{sys.version_info.major}{sys.version_info.minor}" if artifact_kind == "pyd" else "n/a"
    return {
        "platforms": [platform.system().lower()],
        "machines": [platform.machine().lower()],
        "python_abis": [python_abi],
        "python_min": f"{sys.version_info.major}.{sys.version_info.minor}.0",
        "python_max": f"{sys.version_info.major}.{sys.version_info.minor}.999",
    }


def def_validate_module_compatibility(manifest: Mapping[str, Any]) -> def_CommandResult:
    try:
        compatibility = def_require_mapping(manifest.get("compatibility"), "manifest.compatibility")
        platforms = def_require_list(compatibility.get("platforms"), "manifest.compatibility.platforms")
        machines = def_require_list(compatibility.get("machines"), "manifest.compatibility.machines")
        python_abis = def_require_list(compatibility.get("python_abis"), "manifest.compatibility.python_abis")
        if not platforms or not machines or not python_abis:
            raise ValueError("Compatibility lists cannot be empty")
        if any(not isinstance(item, str) or not item.strip() for item in [*platforms, *machines, *python_abis]):
            raise ValueError("Compatibility entries must be non-empty strings")
        current_platform = platform.system().lower()
        current_machine = platform.machine().lower()
        if current_platform not in {item.lower() for item in platforms}:
            raise ValueError(f"Unsupported platform: {current_platform}")
        if current_machine not in {item.lower() for item in machines}:
            raise ValueError(f"Unsupported machine architecture: {current_machine}")
        python_min = compatibility.get("python_min")
        python_max = compatibility.get("python_max")
        if not isinstance(python_min, str) or not isinstance(python_max, str):
            raise ValueError("Compatibility Python version bounds must be strings")
        current_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        if not def_version_in_range(current_version, python_min, python_max):
            raise ValueError(f"Python runtime is outside module range: {current_version}")
        artifact_kind = str(manifest.get("artifact_kind", "")).lower()
        current_abi = f"cp{sys.version_info.major}{sys.version_info.minor}" if artifact_kind == "pyd" else "n/a"
        if current_abi not in {item.lower() for item in python_abis}:
            raise ValueError(f"Python ABI mismatch: {current_abi}")
        dependencies = def_require_list(manifest.get("dependencies", []), "manifest.dependencies")
        conflicts = def_require_list(manifest.get("conflicts", []), "manifest.conflicts")
        if any(not isinstance(item, str) or not item.strip() or len(item) > 160 for item in [*dependencies, *conflicts]):
            raise ValueError("Dependency/conflict declarations are invalid")
        return def_CommandResult(True, "MODULE_COMPATIBLE", data={
            "platform": current_platform,
            "machine": current_machine,
            "python_abi": current_abi,
        })
    except Exception as exc:
        return def_CommandResult(False, "MODULE_INCOMPATIBLE", errors=[str(exc)])


def def_build_module_manifest(
    artifact_path: Path,
    module_id: str,
    version: str,
    capabilities: Sequence[str],
    required_entitlement: str,
    env_alias: str,
    entry_callable: str,
    release_id: str,
    product_number: str,
    master_key_hash: str,
    dependencies: Sequence[str] = (),
    conflicts: Sequence[str] = (),
    compatibility: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    if not def_PARAM_MODULE_ID_RE.fullmatch(module_id):
        raise ValueError("Invalid module_id")
    if artifact_path.suffix.lower() not in def_PARAM_ALLOWED_ARTIFACT_SUFFIXES:
        raise ValueError("Unsupported compiled artifact suffix")
    def_parse_semver(version)
    normalized_capabilities = def_unique_strings(str(item).upper() for item in capabilities)
    if not normalized_capabilities or any(not def_PARAM_CAPABILITY_RE.fullmatch(item) for item in normalized_capabilities):
        raise ValueError("Invalid module capability")
    entitlement = required_entitlement.upper()
    if not def_PARAM_CAPABILITY_RE.fullmatch(entitlement):
        raise ValueError("Invalid required entitlement")
    canonical_product_number = def_normalize_product_number(product_number)
    normalized_master_key_hash = master_key_hash.lower()
    if not def_PARAM_SHA256_RE.fullmatch(normalized_master_key_hash):
        raise ValueError("Invalid module Master KEY commitment")
    manifest = {
        "schema": "via.module-manifest.v2",
        "module_id": module_id,
        "version": version,
        "artifact_name": artifact_path.name,
        "artifact_sha256": def_sha256_file(artifact_path),
        "artifact_size": artifact_path.stat().st_size,
        "artifact_kind": artifact_path.suffix.lower().lstrip("."),
        "python_abi": f"cp{sys.version_info.major}{sys.version_info.minor}" if artifact_path.suffix.lower() == ".pyd" else "n/a",
        "platform": platform.system().lower(),
        "machine": platform.machine().lower(),
        "capabilities": normalized_capabilities,
        "required_entitlement": entitlement,
        "product_number": canonical_product_number,
        "master_key_hash": normalized_master_key_hash,
        "master_key_id": normalized_master_key_hash[:16].upper(),
        "env_alias": env_alias,
        "entry_callable": entry_callable,
        "release_id": release_id,
        "dependencies": def_unique_strings(dependencies),
        "conflicts": def_unique_strings(conflicts),
        "compatibility": dict(compatibility or def_default_module_compatibility(artifact_path)),
        "created_at": def_now_utc_iso(),
    }
    compatibility_result = def_validate_module_compatibility(manifest)
    if not compatibility_result.ok:
        raise ValueError("; ".join(compatibility_result.errors))
    return manifest


def def_sign_module_manifest(manifest: Mapping[str, Any], release_private_key: Any, key_id: str = def_PARAM_RELEASE_KEY_ID) -> Dict[str, Any]:
    return def_sign_payload(manifest, release_private_key, key_id, "via.module-envelope.v2")


def def_verify_module_manifest(
    manifest_envelope: Mapping[str, Any],
    release_public_key: Any,
    artifact_path: Path,
    expected_key_id: str = def_PARAM_RELEASE_KEY_ID,
) -> def_CommandResult:
    try:
        manifest = def_verify_signed_payload(
            manifest_envelope,
            release_public_key,
            expected_key_id=expected_key_id,
            expected_schema="via.module-envelope.v2",
        )
        if manifest.get("schema") != "via.module-manifest.v2":
            raise ValueError("Unsupported module manifest schema")
        if not def_PARAM_MODULE_ID_RE.fullmatch(str(manifest.get("module_id", ""))):
            raise ValueError("Module ID is invalid")
        capabilities = def_require_list(manifest.get("capabilities"), "manifest.capabilities")
        if not capabilities or any(not isinstance(item, str) or not def_PARAM_CAPABILITY_RE.fullmatch(item) for item in capabilities):
            raise ValueError("Module capabilities are invalid")
        if not def_PARAM_CAPABILITY_RE.fullmatch(str(manifest.get("required_entitlement", ""))):
            raise ValueError("Module entitlement is invalid")
        def_normalize_product_number(str(manifest.get("product_number", "")))
        if not def_PARAM_SHA256_RE.fullmatch(str(manifest.get("master_key_hash", ""))):
            raise ValueError("Module Master KEY commitment is invalid")
        if artifact_path.name != manifest.get("artifact_name"):
            raise ValueError("Artifact filename mismatch")
        actual_hash = def_sha256_file(artifact_path)
        if not secrets.compare_digest(actual_hash, str(manifest.get("artifact_sha256", ""))):
            raise ValueError("Artifact hash mismatch")
        if artifact_path.stat().st_size != int(manifest.get("artifact_size", -1)):
            raise ValueError("Artifact size mismatch")
        compatibility_result = def_validate_module_compatibility(manifest)
        if not compatibility_result.ok:
            raise ValueError("; ".join(compatibility_result.errors))
        return def_CommandResult(True, "MODULE_VALID", data={"manifest": manifest})
    except Exception as exc:
        return def_CommandResult(False, "MODULE_INVALID", errors=[str(exc)])


def def_create_module_handshake(
    manifest_envelope: Mapping[str, Any],
    release_public_key: Any,
    artifact_path: Path,
    license_envelope: Mapping[str, Any],
    authority_public_key: Any,
    device_private_key: Any,
    product_sku: str,
    product_version: str,
    product_number: str,
    master_key: str,
    current_hardware_hashes: Mapping[str, str],
    nonce: str,
    state_path: Optional[Path] = None,
    execution_mode: str = "IN_PROCESS",
    target_pid: Optional[int] = None,
) -> def_CommandResult:
    if len(str(nonce).strip()) < 16:
        return def_CommandResult(False, "NONCE_INVALID", errors=["Handshake nonce must contain at least 16 characters"])
    module_check = def_verify_module_manifest(manifest_envelope, release_public_key, artifact_path)
    if not module_check.ok:
        return module_check
    manifest = module_check.data["manifest"]
    license_check = def_verify_license(
        license_envelope,
        authority_public_key,
        device_private_key,
        product_sku,
        product_version,
        product_number,
        master_key,
        required_entitlement=str(manifest["required_entitlement"]),
        current_hardware_hashes=current_hardware_hashes,
        device_type="pc",
        state_path=state_path,
        update_clock_state=True,
    )
    if not license_check.ok:
        return license_check
    if manifest["product_number"] != license_check.data["product_number"]:
        return def_CommandResult(False, "PRODUCT_BINDING_MISMATCH", errors=["Module Product Number differs from License"])
    if not secrets.compare_digest(manifest["master_key_hash"], license_check.data["master_key_hash"]):
        return def_CommandResult(False, "PRODUCT_BINDING_MISMATCH", errors=["Module Master KEY differs from License"])
    normalized_execution_mode = execution_mode.upper()
    if normalized_execution_mode not in {"IN_PROCESS", "CHILD_PROCESS"}:
        return def_CommandResult(False, "EXECUTION_MODE_INVALID", errors=[normalized_execution_mode])
    issued_at = def_now_utc()
    process_binding = {
        "mode": normalized_execution_mode,
        "target_pid": int(target_pid or os.getpid()) if normalized_execution_mode == "IN_PROCESS" else 0,
        "authorized_parent_pid": os.getpid() if normalized_execution_mode == "CHILD_PROCESS" else 0,
    }
    payload = {
        "schema": "via.module-handshake.v2.1",
        "token_id": str(uuid.uuid4()),
        "runtime_instance_id": def_b64u_encode(secrets.token_bytes(18)),
        "module_id": manifest["module_id"],
        "module_version": manifest["version"],
        "artifact_sha256": manifest["artifact_sha256"],
        "capabilities": manifest["capabilities"],
        "license_id": license_check.data["license_id"],
        "device_id": license_check.data["device_id"],
        "product_number": license_check.data["product_number"],
        "master_key_hash": license_check.data["master_key_hash"],
        "master_key_id": license_check.data["master_key_id"],
        "required_entitlement": manifest["required_entitlement"],
        "process_binding": process_binding,
        "nonce": nonce,
        "issued_at": issued_at.isoformat().replace("+00:00", "Z"),
        "expires_at": (issued_at + timedelta(seconds=def_PARAM_HANDSHAKE_TTL_SECONDS)).isoformat().replace("+00:00", "Z"),
    }
    token = def_sign_payload(
        payload,
        device_private_key,
        license_check.data["device_id"],
        "via.module-handshake-envelope.v2.1",
    )
    return def_CommandResult(True, "HANDSHAKE_VALID", data={"token": token, "module": manifest["module_id"]})


def def_consume_runtime_token_id(replay_ledger: Path, token_id: str, expires_at: str) -> None:
    try:
        uuid.UUID(token_id)
    except Exception as exc:
        raise ValueError("Runtime token_id is invalid") from exc
    with def_file_lock(replay_ledger):
        active_ids = set()
        now_value = def_now_utc()
        if replay_ledger.exists():
            with replay_ledger.open("r", encoding="utf-8") as ledger_handle:
                for line_number, line in enumerate(ledger_handle, start=1):
                    if not line.strip():
                        continue
                    try:
                        row = json.loads(line, object_pairs_hook=def_json_object_no_duplicates)
                        row_token_id = str(row.get("token_id", ""))
                        uuid.UUID(row_token_id)
                        row_expiry = def_parse_utc(str(row.get("expires_at", "")))
                    except Exception as exc:
                        raise ValueError(f"Runtime replay ledger is corrupt at line {line_number}") from exc
                    if row_expiry >= now_value:
                        if row_token_id in active_ids:
                            raise ValueError(f"Runtime replay ledger has a duplicate active token at line {line_number}")
                        active_ids.add(row_token_id)
        if token_id in active_ids:
            raise ValueError("Runtime token replay detected")
        replay_ledger.parent.mkdir(parents=True, exist_ok=True)
        with replay_ledger.open("a", encoding="utf-8", newline="\n") as file_handle:
            file_handle.write(json.dumps({
                "token_id": token_id,
                "expires_at": expires_at,
                "consumed_at": def_now_utc_iso(),
            }, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            file_handle.flush()
            os.fsync(file_handle.fileno())


def def_verify_runtime_token(
    token_envelope: Mapping[str, Any],
    device_public_key: Any,
    module_manifest: Mapping[str, Any],
    product_number: str,
    master_key: str,
    required_entitlement: str,
    expected_license_id: str = "",
    expected_device_id: str = "",
    replay_ledger: Optional[Path] = None,
    consume: bool = True,
    now_value: Optional[datetime] = None,
    current_pid: Optional[int] = None,
    parent_pid: Optional[int] = None,
) -> def_CommandResult:
    try:
        payload = def_verify_signed_payload(
            token_envelope,
            device_public_key,
            expected_schema="via.module-handshake-envelope.v2.1",
        )
        if payload.get("schema") != "via.module-handshake.v2.1":
            raise ValueError("Unsupported Runtime Token schema")
        if token_envelope.get("key_id") != payload.get("device_id"):
            raise ValueError("Runtime Token signer identity mismatch")
        if expected_license_id and payload.get("license_id") != expected_license_id:
            raise ValueError("Runtime Token License ID mismatch")
        if expected_device_id and payload.get("device_id") != expected_device_id:
            raise ValueError("Runtime Token Device ID mismatch")
        now_value = (now_value or def_now_utc()).astimezone(timezone.utc)
        issued_at = def_parse_utc(str(payload.get("issued_at", "")))
        expires_at = def_parse_utc(str(payload.get("expires_at", "")))
        if now_value < issued_at - timedelta(seconds=5) or now_value > expires_at:
            raise ValueError("Runtime Token is outside its validity window")
        if (expires_at - issued_at).total_seconds() > def_PARAM_HANDSHAKE_TTL_SECONDS + 1:
            raise ValueError("Runtime Token lifetime exceeds policy")
        expected_number = def_normalize_product_number(product_number)
        expected_key_hash = def_master_key_hash(expected_number, master_key)
        if payload.get("product_number") != expected_number or module_manifest.get("product_number") != expected_number:
            raise ValueError("Runtime Token Product Number mismatch")
        if not secrets.compare_digest(str(payload.get("master_key_hash", "")), expected_key_hash):
            raise ValueError("Runtime Token Master KEY mismatch")
        if not secrets.compare_digest(str(module_manifest.get("master_key_hash", "")), expected_key_hash):
            raise ValueError("Module Manifest Master KEY mismatch")
        if payload.get("module_id") != module_manifest.get("module_id"):
            raise ValueError("Runtime Token module_id mismatch")
        if payload.get("artifact_sha256") != module_manifest.get("artifact_sha256"):
            raise ValueError("Runtime Token artifact hash mismatch")
        entitlement = required_entitlement.upper()
        if payload.get("required_entitlement") != entitlement or module_manifest.get("required_entitlement") != entitlement:
            raise ValueError("Runtime Token entitlement mismatch")
        process_binding = payload.get("process_binding", {})
        mode = str(process_binding.get("mode", ""))
        effective_pid = int(current_pid or os.getpid())
        effective_parent_pid = int(parent_pid if parent_pid is not None else os.getppid())
        if mode == "IN_PROCESS":
            if int(process_binding.get("target_pid", 0)) != effective_pid:
                raise ValueError("Runtime Token is not bound to this process")
        elif mode == "CHILD_PROCESS":
            if int(process_binding.get("authorized_parent_pid", 0)) != effective_parent_pid:
                raise ValueError("Runtime Token is not bound to this launcher")
        else:
            raise ValueError("Runtime Token execution mode is invalid")
        if consume:
            if replay_ledger is None:
                raise ValueError("Runtime Token replay ledger is required")
            def_consume_runtime_token_id(replay_ledger, str(payload.get("token_id", "")), str(payload["expires_at"]))
        return def_CommandResult(True, "RUNTIME_TOKEN_VALID", data={
            "module_id": payload["module_id"],
            "product_number": payload["product_number"],
            "master_key_id": payload["master_key_id"],
            "runtime_instance_id": payload["runtime_instance_id"],
            "execution_mode": mode,
        })
    except Exception as exc:
        return def_CommandResult(False, "RUNTIME_TOKEN_INVALID", errors=[str(exc)])


def def_required_environment_path(name: str) -> Path:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Required runtime environment path is missing: {name}")
    path_value = Path(value).expanduser().resolve()
    if not path_value.exists():
        raise FileNotFoundError(f"Required runtime file not found: {name}")
    return path_value


def def_enforce_module_guard_from_environment(
    module_id: str,
    required_entitlement: str,
    expected_product_number: str,
    artifact_path: Path,
) -> Dict[str, Any]:
    token_path = def_required_environment_path(def_PARAM_RUNTIME_TOKEN_ENV)
    license_path = def_required_environment_path(def_PARAM_LICENSE_FILE_ENV)
    manifest_path = def_required_environment_path(def_PARAM_MODULE_MANIFEST_ENV)
    authority_public_path = def_required_environment_path(def_PARAM_AUTHORITY_PUBLIC_KEY_ENV)
    release_public_path = def_required_environment_path(def_PARAM_RELEASE_PUBLIC_KEY_ENV)
    device_key_path = def_required_environment_path(def_PARAM_DEVICE_KEY_ENV)
    product_key_state_path = def_required_environment_path(def_PARAM_PRODUCT_KEY_STATE_ENV)
    allow_test_store = def_PARAM_BUILD_MODE == "DEVELOPMENT" and os.environ.get("VIA_ALLOW_INSECURE_TEST_KEY_STORE") == "1"
    device_private_key = def_load_device_private_key(device_key_path, allow_insecure_test_store=allow_test_store)
    product_state = def_load_product_key_state(product_key_state_path, allow_insecure_test_store=allow_test_store)
    expected_number = def_normalize_product_number(expected_product_number)
    if product_state["product_number"] != expected_number:
        raise RuntimeError("Guard Product Number does not match local Product KEY state")
    authority_public_key = def_load_trusted_public_key(
        authority_public_path,
        def_PARAM_TRUSTED_LICENSE_PUBLIC_KEY_SHA256,
        os.environ.get("VIA_DEV_AUTHORITY_PUBLIC_KEY_SHA256", ""),
    )
    release_public_key = def_load_trusted_public_key(
        release_public_path,
        def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256,
        os.environ.get("VIA_DEV_RELEASE_PUBLIC_KEY_SHA256", ""),
    )
    manifest_result = def_verify_module_manifest(def_read_json(manifest_path), release_public_key, artifact_path)
    if not manifest_result.ok:
        raise RuntimeError("Module integrity gate failed: " + "; ".join(manifest_result.errors))
    manifest = manifest_result.data["manifest"]
    if manifest.get("module_id") != module_id or manifest.get("required_entitlement") != required_entitlement.upper():
        raise RuntimeError("Guard module contract mismatch")
    hardware_hashes = def_hash_hardware_signals(def_collect_windows_pc_signals())
    license_result = def_verify_license(
        def_read_json(license_path),
        authority_public_key,
        device_private_key,
        def_PARAM_PRODUCT_SKU,
        def_PARAM_ENGINE_VERSION,
        product_state["product_number"],
        product_state["master_key"],
        required_entitlement=required_entitlement,
        current_hardware_hashes=hardware_hashes,
        device_type="pc",
        update_clock_state=False,
    )
    if not license_result.ok:
        raise RuntimeError("License gate failed: " + "; ".join(license_result.errors))
    replay_path_text = os.environ.get(def_PARAM_RUNTIME_REPLAY_LEDGER_ENV, "").strip()
    replay_path = Path(replay_path_text).expanduser().resolve() if replay_path_text else def_PARAM_RUNTIME_REPLAY_LEDGER
    token_result = def_verify_runtime_token(
        def_read_json(token_path),
        device_private_key.public_key(),
        manifest,
        product_state["product_number"],
        product_state["master_key"],
        required_entitlement,
        expected_license_id=license_result.data["license_id"],
        expected_device_id=license_result.data["device_id"],
        replay_ledger=replay_path,
        consume=True,
    )
    if not token_result.ok:
        raise RuntimeError("Runtime Token gate failed: " + "; ".join(token_result.errors))
    return token_result.data


def def_launch_guarded_executable(
    artifact_path: Path,
    runtime_token: Mapping[str, Any],
    license_path: Path,
    manifest_path: Path,
    authority_public_key_path: Path,
    release_public_key_path: Path,
    device_key_path: Path,
    product_key_state_path: Path,
    replay_ledger_path: Path,
    artifact_arguments: Sequence[str] = (),
    development_authority_pin: str = "",
    development_release_pin: str = "",
    allow_insecure_test_key_store: bool = False,
    timeout_seconds: int = 0,
) -> Dict[str, Any]:
    resolved_artifact = artifact_path.expanduser().resolve()
    if not resolved_artifact.is_file() or resolved_artifact.suffix.lower() != ".exe":
        raise ValueError("Guarded child launch requires an existing .exe artifact")
    with tempfile.TemporaryDirectory(prefix="via-runtime-token-") as temp_dir:
        token_path = Path(temp_dir) / "runtime-token.json"
        def_write_json(token_path, dict(runtime_token), overwrite=False)
        try:
            os.chmod(token_path, 0o600)
        except OSError:
            pass
        child_environment = os.environ.copy()
        child_environment.update({
            def_PARAM_RUNTIME_TOKEN_ENV: str(token_path.resolve()),
            def_PARAM_LICENSE_FILE_ENV: str(license_path.expanduser().resolve()),
            def_PARAM_MODULE_MANIFEST_ENV: str(manifest_path.expanduser().resolve()),
            def_PARAM_AUTHORITY_PUBLIC_KEY_ENV: str(authority_public_key_path.expanduser().resolve()),
            def_PARAM_RELEASE_PUBLIC_KEY_ENV: str(release_public_key_path.expanduser().resolve()),
            def_PARAM_DEVICE_KEY_ENV: str(device_key_path.expanduser().resolve()),
            def_PARAM_PRODUCT_KEY_STATE_ENV: str(product_key_state_path.expanduser().resolve()),
            def_PARAM_RUNTIME_REPLAY_LEDGER_ENV: str(replay_ledger_path.expanduser().resolve()),
        })
        if def_PARAM_BUILD_MODE == "DEVELOPMENT":
            if development_authority_pin:
                child_environment["VIA_DEV_AUTHORITY_PUBLIC_KEY_SHA256"] = development_authority_pin
            if development_release_pin:
                child_environment["VIA_DEV_RELEASE_PUBLIC_KEY_SHA256"] = development_release_pin
            if allow_insecure_test_key_store:
                child_environment["VIA_ALLOW_INSECURE_TEST_KEY_STORE"] = "1"
        completed = def_run_subprocess_bounded(
            [str(resolved_artifact), *[str(item) for item in artifact_arguments]],
            cwd=resolved_artifact.parent,
            env=child_environment,
            timeout_seconds=timeout_seconds or def_PARAM_PROCESS_TIMEOUT_SECONDS,
        )
    return {
        "ok": completed["ok"],
        "status": "GUARDED_PROCESS_COMPLETED" if completed["ok"] else completed["status"],
        "artifact": str(resolved_artifact),
        "exit_code": completed["exit_code"],
        "stdout_tail": completed["stdout_tail"],
        "stderr_tail": completed["stderr_tail"],
        "timed_out": completed["timed_out"],
        "output_limited": completed["output_limited"],
    }


# =============================================================================
# def EDGE/CLOUD ROUTING AND OUTBOUND-ONLY TRANSPORT
# =============================================================================
def def_plan_execution_route(
    data_classification: str,
    requested_compute: str,
    database_mode: str,
    explicit_cloud_restricted_approval: bool = False,
) -> def_RouteDecision:
    data_class = data_classification.upper()
    compute = requested_compute.upper()
    db_mode = database_mode.upper()
    if data_class not in def_PARAM_ALLOWED_DATA_CLASSES:
        raise ValueError("Unsupported data classification")
    if compute not in def_PARAM_ALLOWED_COMPUTE_MODES:
        raise ValueError("Unsupported compute mode")
    if db_mode not in def_PARAM_ALLOWED_DB_MODES:
        raise ValueError("Unsupported database mode")
    reasons: List[str] = []
    controls = [
        "CLIENT_INITIATED_OUTBOUND_HTTPS",
        "SIGNED_REQUEST_AND_RESPONSE",
        "NO_DATABASE_CREDENTIAL_EXPORT",
        "LOCAL_TRANSACTIONAL_WRITER",
    ]
    if db_mode == "LOCAL_ONLY":
        compute_location = "EDGE"
        reasons.append("Local-only database policy forces edge execution")
    elif data_class == "RESTRICTED" and not explicit_cloud_restricted_approval:
        compute_location = "EDGE"
        reasons.append("Restricted data is fail-closed to edge execution")
    elif compute == "LOCAL":
        compute_location = "EDGE"
        reasons.append("Caller explicitly requested local execution")
    elif compute == "CLOUD":
        compute_location = "CLOUD"
        reasons.append("Caller requested cloud execution and policy permits it")
    else:
        compute_location = "CLOUD" if data_class in {"PUBLIC", "INTERNAL"} else "EDGE"
        reasons.append("AUTO route selected from data classification")
    if compute_location == "CLOUD":
        controls.extend(["PAYLOAD_MINIMIZATION", "ARTIFACT_HASH_GATE", "HOST_ALLOWLIST"])
        if data_class in {"CONFIDENTIAL", "RESTRICTED"}:
            controls.extend(["END_TO_END_PAYLOAD_ENCRYPTION", "EXPLICIT_RETENTION_ZERO"])
    database_location = "CLOUD" if db_mode == "CLOUD_FULL_SYNC" else "LOCAL_PC"
    local_writer_required = database_location == "LOCAL_PC"
    return def_RouteDecision(
        ok=True,
        compute_location=compute_location,
        database_location=database_location,
        transport="OUTBOUND_HTTPS_PULL",
        local_writer_required=local_writer_required,
        mobile_access="READ_ONLY_API",
        reasons=reasons,
        controls=def_unique_strings(controls),
    )


def def_validate_https_target(url_value: str, allowed_hosts: Sequence[str]) -> urllib.parse.ParseResult:
    parsed = urllib.parse.urlparse(url_value)
    if parsed.scheme.lower() != "https" or not parsed.hostname:
        raise ValueError("Only absolute HTTPS targets are allowed")
    allowed = {host.lower().strip() for host in allowed_hosts if host.strip()}
    if parsed.hostname.lower() not in allowed:
        raise ValueError("Target host is not allowlisted")
    if parsed.username or parsed.password:
        raise ValueError("Credentials in URLs are forbidden")
    return parsed


def def_https_post_json(
    url_value: str,
    payload: Mapping[str, Any],
    allowed_hosts: Sequence[str],
    certificate_sha256: str = "",
    timeout_seconds: int = def_PARAM_NETWORK_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    parsed = def_validate_https_target(url_value, allowed_hosts)
    body = def_canonical_json_bytes(payload)
    if len(body) > def_PARAM_MAX_JSON_BYTES:
        raise ValueError("Request JSON exceeds size gate")
    connection = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443, timeout=timeout_seconds, context=ssl.create_default_context())
    try:
        connection.connect()
        peer_cert = connection.sock.getpeercert(binary_form=True) if connection.sock else b""
        if certificate_sha256:
            expected_pin = certificate_sha256.lower().replace(":", "")
            if not def_PARAM_SHA256_RE.fullmatch(expected_pin):
                raise ValueError("Invalid certificate SHA-256 pin")
            if not secrets.compare_digest(def_sha256_bytes(peer_cert), expected_pin):
                raise ssl.SSLError("Certificate pin mismatch")
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        connection.request("POST", target, body=body, headers={"Content-Type": "application/json", "Accept": "application/json"})
        response = connection.getresponse()
        response_body = response.read(def_PARAM_MAX_JSON_BYTES + 1)
        if len(response_body) > def_PARAM_MAX_JSON_BYTES:
            raise ValueError("Response exceeds JSON size gate")
        if response.status < 200 or response.status >= 300:
            raise RuntimeError(f"HTTPS status {response.status}")
        return json.loads(response_body.decode("utf-8"))
    finally:
        connection.close()


def def_download_verified_artifact(
    url_value: str,
    destination: Path,
    expected_sha256: str,
    expected_size: int,
    allowed_hosts: Sequence[str],
    timeout_seconds: int = def_PARAM_NETWORK_TIMEOUT_SECONDS,
) -> Dict[str, Any]:
    if not def_PARAM_SHA256_RE.fullmatch(expected_sha256.lower()):
        raise ValueError("Invalid expected artifact SHA-256")
    if expected_size < 0 or expected_size > def_PARAM_MAX_DOWNLOAD_BYTES:
        raise ValueError("Artifact size violates configured gate")
    parsed = def_validate_https_target(url_value, allowed_hosts)
    destination = destination.expanduser().resolve()
    destination.parent.mkdir(parents=True, exist_ok=True)
    temp_path = destination.with_name(f".{destination.name}.{uuid.uuid4().hex}.partial")
    connection = http.client.HTTPSConnection(parsed.hostname, parsed.port or 443, timeout=timeout_seconds, context=ssl.create_default_context())
    digest = hashlib.sha256()
    received = 0
    try:
        target = parsed.path or "/"
        if parsed.query:
            target += "?" + parsed.query
        connection.request("GET", target, headers={"Accept": "application/octet-stream"})
        response = connection.getresponse()
        if response.status != 200:
            raise RuntimeError(f"Artifact HTTPS status {response.status}")
        with temp_path.open("wb") as file_handle:
            while True:
                chunk = response.read(def_PARAM_CHUNK_SIZE)
                if not chunk:
                    break
                received += len(chunk)
                if received > expected_size or received > def_PARAM_MAX_DOWNLOAD_BYTES:
                    raise ValueError("Artifact exceeded declared size")
                digest.update(chunk)
                file_handle.write(chunk)
            file_handle.flush()
            os.fsync(file_handle.fileno())
        if received != expected_size:
            raise ValueError("Artifact size mismatch")
        if not secrets.compare_digest(digest.hexdigest(), expected_sha256.lower()):
            raise ValueError("Artifact SHA-256 mismatch")
        if destination.exists():
            raise FileExistsError(f"Refusing to overwrite artifact: {destination}")
        os.replace(temp_path, destination)
        return {"ok": True, "path": str(destination), "size": received, "sha256": digest.hexdigest()}
    finally:
        connection.close()
        temp_path.unlink(missing_ok=True)


def def_validate_local_schema(schema: Mapping[str, str], primary_keys: Sequence[str]) -> Dict[str, str]:
    if not schema:
        raise ValueError("Local database schema cannot be empty")
    normalized: Dict[str, str] = {}
    for column_name, sql_type in schema.items():
        if not def_PARAM_TABLE_RE.fullmatch(str(column_name)):
            raise ValueError(f"Unsafe column name: {column_name}")
        normalized_type = re.sub(r"\s+", " ", str(sql_type).strip().upper())
        base_type = normalized_type.split("(", 1)[0].strip()
        if base_type not in def_PARAM_ALLOWED_SQL_TYPES:
            raise ValueError(f"Unsupported SQL type: {sql_type}")
        if "(" in normalized_type and not re.fullmatch(r"(?:VARCHAR|DECIMAL|NUMERIC)\(\d+(?:,\d+)?\)", normalized_type):
            raise ValueError(f"Unsafe parameterized SQL type: {sql_type}")
        normalized[str(column_name)] = normalized_type
    keys = def_unique_strings(primary_keys)
    if any(key not in normalized for key in keys):
        raise ValueError("Every primary key must exist in the local schema")
    return normalized


def def_normalize_db_value(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bytes)):
        return value
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (datetime,)):
        return value.isoformat()
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return str(value)


def def_prepare_local_rows(rows: Sequence[Mapping[str, Any]], schema: Mapping[str, str]) -> Tuple[List[str], List[Tuple[Any, ...]]]:
    if not rows:
        raise ValueError("No rows supplied for local ingestion")
    if len(rows) > def_PARAM_MAX_DB_BATCH_ROWS:
        raise ValueError("Local ingestion batch exceeds row limit")
    columns = list(schema.keys())
    allowed_columns = set(columns)
    prepared: List[Tuple[Any, ...]] = []
    for row_number, row in enumerate(rows, start=1):
        unknown = set(row.keys()) - allowed_columns
        if unknown:
            raise ValueError(f"Row {row_number} has unknown columns: {sorted(unknown)}")
        prepared.append(tuple(def_normalize_db_value(row.get(column)) for column in columns))
    return columns, prepared


def def_ingest_local_rows(
    database_path: Path,
    approved_database_root: Path,
    table_name: str,
    rows: Sequence[Mapping[str, Any]],
    schema: Mapping[str, str],
    primary_keys: Sequence[str],
    backend: str = "SQLITE",
    mode: str = "APPEND",
    audit_path: Path = def_PARAM_AUDIT_JSONL,
    request_id: str = "",
) -> Dict[str, Any]:
    normalized_backend = backend.upper()
    normalized_mode = mode.upper()
    if normalized_backend not in def_PARAM_ALLOWED_DB_BACKENDS:
        raise ValueError("Unsupported local database backend")
    if normalized_mode not in def_PARAM_ALLOWED_INGEST_MODES:
        raise ValueError("Unsupported ingestion mode")
    if not def_PARAM_TABLE_RE.fullmatch(table_name):
        raise ValueError("Unsafe table name")
    request_key = def_validate_request_id(request_id) if request_id else ""
    approved_root = approved_database_root.expanduser().resolve()
    approved_root.mkdir(parents=True, exist_ok=True)
    resolved_database = def_validate_active_database_location(database_path, approved_root)
    resolved_database.parent.mkdir(parents=True, exist_ok=True)
    def_require_free_disk(resolved_database.parent)
    normalized_schema = def_validate_local_schema(schema, primary_keys)
    columns, prepared_rows = def_prepare_local_rows(rows, normalized_schema)
    operation_hash = def_sha256_bytes(def_canonical_json_bytes({
        "backend": normalized_backend,
        "mode": normalized_mode,
        "table": table_name,
        "schema": normalized_schema,
        "primary_keys": def_unique_strings(primary_keys),
        "rows": [dict(zip(columns, row)) for row in prepared_rows],
    }))
    quoted_table = f'"{table_name}"'
    quoted_columns = [f'"{column}"' for column in columns]
    primary_key_list = def_unique_strings(primary_keys)
    quoted_primary_keys = [f'"{key}"' for key in primary_key_list]
    primary_clause = f", PRIMARY KEY ({', '.join(quoted_primary_keys)})" if primary_key_list else ""
    create_sql = f"CREATE TABLE IF NOT EXISTS {quoted_table} ({', '.join(f'{quoted} {normalized_schema[column]}' for quoted, column in zip(quoted_columns, columns))}{primary_clause})"
    placeholders = ", ".join("?" for _ in columns)
    idempotency_sql = (
        'CREATE TABLE IF NOT EXISTS "_via_idempotency" ('
        'request_id TEXT PRIMARY KEY, operation_sha256 TEXT NOT NULL, '
        'result_rows INTEGER NOT NULL, completed_at TEXT NOT NULL)'
    )
    replayed = False
    if normalized_backend == "SQLITE":
        connection = sqlite3.connect(str(resolved_database), timeout=30)
        try:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(idempotency_sql)
            if request_key:
                existing_request = connection.execute(
                    'SELECT operation_sha256, result_rows FROM "_via_idempotency" WHERE request_id=?',
                    (request_key,),
                ).fetchone()
                if existing_request:
                    if not secrets.compare_digest(str(existing_request[0]), operation_hash):
                        raise ValueError("Idempotency key was already used with different content")
                    replayed = True
            connection.execute(create_sql)
            existing_columns = {row[1] for row in connection.execute(f"PRAGMA table_info({quoted_table})").fetchall()}
            if not set(columns).issubset(existing_columns):
                raise ValueError("Existing SQLite table schema is incompatible")
            if not replayed:
                verb = "INSERT OR REPLACE" if normalized_mode == "UPSERT" else "INSERT"
                insert_sql = f"{verb} INTO {quoted_table} ({', '.join(quoted_columns)}) VALUES ({placeholders})"
                connection.executemany(insert_sql, prepared_rows)
                if request_key:
                    connection.execute(
                        'INSERT INTO "_via_idempotency" (request_id, operation_sha256, result_rows, completed_at) VALUES (?, ?, ?, ?)',
                        (request_key, operation_hash, len(prepared_rows), def_now_utc_iso()),
                    )
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()
    else:
        try:
            import duckdb
        except Exception as exc:
            raise RuntimeError("duckdb is required for the DUCKDB backend") from exc
        connection = duckdb.connect(str(resolved_database))
        try:
            connection.execute("BEGIN TRANSACTION")
            connection.execute(idempotency_sql)
            if request_key:
                existing_request = connection.execute(
                    'SELECT operation_sha256, result_rows FROM "_via_idempotency" WHERE request_id=?',
                    [request_key],
                ).fetchone()
                if existing_request:
                    if not secrets.compare_digest(str(existing_request[0]), operation_hash):
                        raise ValueError("Idempotency key was already used with different content")
                    replayed = True
            connection.execute(create_sql)
            existing_columns = {row[0] for row in connection.execute(f"DESCRIBE {quoted_table}").fetchall()}
            if not set(columns).issubset(existing_columns):
                raise ValueError("Existing DuckDB table schema is incompatible")
            if not replayed:
                verb = "INSERT OR REPLACE" if normalized_mode == "UPSERT" else "INSERT"
                insert_sql = f"{verb} INTO {quoted_table} ({', '.join(quoted_columns)}) VALUES ({placeholders})"
                connection.executemany(insert_sql, prepared_rows)
                if request_key:
                    connection.execute(
                        'INSERT INTO "_via_idempotency" (request_id, operation_sha256, result_rows, completed_at) VALUES (?, ?, ?, ?)',
                        [request_key, operation_hash, len(prepared_rows), def_now_utc_iso()],
                    )
            connection.execute("COMMIT")
        except Exception:
            connection.execute("ROLLBACK")
            raise
        finally:
            connection.close()
    event = def_append_audit_event(
        audit_path,
        "LOCAL_DATABASE_INGEST_REPLAY" if replayed else "LOCAL_DATABASE_INGEST",
        {
            "database_path_hash": def_sha256_text(str(resolved_database)),
            "backend": normalized_backend,
            "table": table_name,
            "mode": normalized_mode,
            "rows": len(prepared_rows),
            "request_id_hash": def_sha256_text(request_key) if request_key else "",
            "operation_sha256": operation_hash,
            "replayed": replayed,
        },
    )
    return {
        "ok": True,
        "status": "LOCAL_INGEST_REPLAYED" if replayed else "LOCAL_INGEST_COMMITTED",
        "backend": normalized_backend,
        "table": table_name,
        "rows": len(prepared_rows),
        "request_id": request_key,
        "operation_sha256": operation_hash,
        "replayed": replayed,
        "database_sha256": def_sha256_file(resolved_database),
        "audit_event_hash": event["event_hash"],
    }


def def_build_cloud_job_request(
    device_private_key: Any,
    license_id: str,
    module_id: str,
    capability: str,
    product_number: str,
    master_key: str,
    route: def_RouteDecision,
    input_manifest: Mapping[str, Any],
    cloud_transport_public_key_b64: str = "",
    request_id: str = "",
) -> Dict[str, Any]:
    if route.compute_location != "CLOUD":
        raise ValueError("Cloud job request is forbidden by route decision")
    if not def_PARAM_MODULE_ID_RE.fullmatch(str(module_id)):
        raise ValueError("Cloud job module_id is invalid")
    normalized_capability = str(capability).upper()
    if not def_PARAM_CAPABILITY_RE.fullmatch(normalized_capability):
        raise ValueError("Cloud job capability is invalid")
    input_manifest = def_require_mapping(input_manifest, "cloud_job.input_manifest")
    def_validate_json_shape(input_manifest)
    canonical_product_number = def_normalize_product_number(product_number)
    product_key_hash = def_master_key_hash(canonical_product_number, master_key)
    job_id = def_validate_request_id(request_id) if request_id else str(uuid.uuid4())
    aad_context = {
        "schema": "via.cloud-job-aad.v2",
        "job_id": job_id,
        "license_id": license_id,
        "module_id": module_id,
        "capability": normalized_capability,
        "product_number": canonical_product_number,
        "master_key_hash": product_key_hash,
    }
    encryption_required = "END_TO_END_PAYLOAD_ENCRYPTION" in route.controls
    if encryption_required and not cloud_transport_public_key_b64:
        raise ValueError("This route requires a cloud X25519 transport public key")
    encrypted_input = (
        def_encrypt_json_for_recipient(input_manifest, cloud_transport_public_key_b64, aad_context)
        if cloud_transport_public_key_b64 else None
    )
    payload = {
        "schema": "via.cloud-job.v2",
        "job_id": job_id,
        "license_id": license_id,
        "module_id": module_id,
        "capability": normalized_capability,
        "idempotency_key": job_id,
        "input_sha256": def_sha256_bytes(def_canonical_json_bytes(input_manifest)),
        "product_number": canonical_product_number,
        "master_key_hash": product_key_hash,
        "master_key_id": product_key_hash[:16].upper(),
        "route": asdict(route),
        "input_manifest": None if encrypted_input else dict(input_manifest),
        "encrypted_input": encrypted_input,
        "payload_encryption_required": encryption_required,
        "database_path": None,
        "database_credentials": None,
        "client_nonce": def_b64u_encode(secrets.token_bytes(24)),
        "created_at": def_now_utc_iso(),
    }
    key_id = def_sha256_text(def_public_key_raw_b64(device_private_key.public_key()))[:16]
    return def_sign_payload(payload, device_private_key, key_id, "via.cloud-job-envelope.v2")


# =============================================================================
# def SIGNED PACKAGE TREE — exact file set, no reparse points, no extra DLLs
# =============================================================================
def def_collect_package_tree(package_root: Path) -> List[Dict[str, Any]]:
    root = package_root.expanduser().resolve()
    if not root.is_dir():
        raise NotADirectoryError(str(root))
    def_validate_no_link_chain(package_root)
    rows: List[Dict[str, Any]] = []
    for path_value in sorted(package_root.rglob("*")):
        if def_path_is_link_or_reparse(path_value):
            raise ValueError(f"Package tree contains symlink/reparse point: {path_value}")
        if not path_value.is_file():
            continue
        relative_path = def_safe_relative(path_value, root)
        rows.append({
            "path": relative_path,
            "size": path_value.stat().st_size,
            "sha256": def_sha256_file(path_value),
        })
    if not rows:
        raise ValueError("Package tree cannot be empty")
    return rows


def def_build_package_tree_manifest(
    package_root: Path,
    product_number: str,
    release_id: str,
) -> Dict[str, Any]:
    release_value = str(release_id or "").strip()
    if not release_value or len(release_value) > 128:
        raise ValueError("release_id is required and must not exceed 128 symbols")
    files = def_collect_package_tree(package_root)
    tree_hash = def_sha256_bytes(def_canonical_json_bytes(files))
    return {
        "schema": "via.package-tree.v2.2",
        "product_number": def_normalize_product_number(product_number),
        "release_id": release_value,
        "root_name": package_root.expanduser().resolve().name,
        "file_count": len(files),
        "total_bytes": sum(int(item["size"]) for item in files),
        "tree_sha256": tree_hash,
        "files": files,
        "created_at": def_now_utc_iso(),
    }


def def_sign_package_tree_manifest(
    manifest: Mapping[str, Any],
    release_private_key: Any,
    key_id: str = def_PARAM_RELEASE_KEY_ID,
) -> Dict[str, Any]:
    return def_sign_payload(manifest, release_private_key, key_id, "via.package-tree-envelope.v2.2")


def def_verify_package_tree_manifest(
    manifest_envelope: Mapping[str, Any],
    release_public_key: Any,
    package_root: Path,
    expected_product_number: str = "",
    expected_key_id: str = def_PARAM_RELEASE_KEY_ID,
) -> def_CommandResult:
    try:
        manifest = def_verify_signed_payload(
            manifest_envelope,
            release_public_key,
            expected_key_id=expected_key_id,
            expected_schema="via.package-tree-envelope.v2.2",
        )
        if manifest.get("schema") != "via.package-tree.v2.2":
            raise ValueError("Unsupported package tree schema")
        product_number = def_normalize_product_number(str(manifest.get("product_number", "")))
        if expected_product_number and product_number != def_normalize_product_number(expected_product_number):
            raise ValueError("Package tree Product Number mismatch")
        expected_files = def_require_list(manifest.get("files"), "package_tree.files")
        actual_files = def_collect_package_tree(package_root)
        if len(expected_files) != int(manifest.get("file_count", -1)):
            raise ValueError("Signed package tree file_count is inconsistent")
        for row in expected_files:
            row_mapping = def_require_mapping(row, "package_tree.file")
            if not isinstance(row_mapping.get("path"), str):
                raise ValueError("Package tree path is invalid")
            if type(row_mapping.get("size")) is not int or not def_PARAM_SHA256_RE.fullmatch(str(row_mapping.get("sha256", ""))):
                raise ValueError("Package tree size/hash is invalid")
        expected_canonical = sorted((dict(item) for item in expected_files), key=lambda item: str(item["path"]))
        if not secrets.compare_digest(
            def_sha256_bytes(def_canonical_json_bytes(expected_canonical)),
            str(manifest.get("tree_sha256", "")),
        ):
            raise ValueError("Signed package tree digest is internally inconsistent")
        if expected_canonical != actual_files:
            expected_names = {str(item["path"]) for item in expected_canonical}
            actual_names = {str(item["path"]) for item in actual_files}
            extra = sorted(actual_names - expected_names)
            missing = sorted(expected_names - actual_names)
            changed = sorted(
                name for name in expected_names & actual_names
                if next(item for item in expected_canonical if item["path"] == name)
                != next(item for item in actual_files if item["path"] == name)
            )
            raise ValueError(f"Package tree drift: extra={extra}, missing={missing}, changed={changed}")
        return def_CommandResult(True, "PACKAGE_TREE_VALID", data={
            "release_id": manifest.get("release_id"),
            "product_number": product_number,
            "file_count": len(actual_files),
            "tree_sha256": manifest.get("tree_sha256"),
        })
    except Exception as exc:
        return def_CommandResult(False, "PACKAGE_TREE_INVALID", errors=[str(exc)])


# =============================================================================
# def STATIC AST, CONTRACT, HYDRA, AND COPY-FIRST PACKAGING ANALYSIS
# =============================================================================
def def_dotted_call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        prefix = def_dotted_call_name(node.value)
        return f"{prefix}.{node.attr}" if prefix else node.attr
    return ""


def def_analyze_python_source(path_value: Path, source_root: Path) -> def_SourceAnalysis:
    source_bytes = path_value.read_bytes()
    source_text = source_bytes.decode("utf-8-sig", errors="replace")
    relative_path = def_safe_relative(path_value, source_root)
    source_sha256 = def_sha256_bytes(source_bytes)
    cache_key = (source_sha256, str(path_value.resolve()))
    with def_ANALYSIS_CACHE_LOCK:
        cached = def_ANALYSIS_CACHE.get(cache_key)
    if cached is not None:
        return cached
    functions: List[str] = []
    classes: List[str] = []
    imports: List[str] = []
    risks: List[Dict[str, str]] = []
    ast_ok = True
    compile_ok = True
    has_main = False
    has_cli = False
    try:
        tree = ast.parse(source_text, filename=str(path_value))
        compile(tree, str(path_value), "exec")
        parent_map = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }

        def def_enclosing_function_name(node_value: ast.AST) -> str:
            current = parent_map.get(node_value)
            while current is not None:
                if isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    return current.name
                current = parent_map.get(current)
            return ""

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                functions.append(node.name)
            elif isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
            elif isinstance(node, ast.Call):
                call_name = def_dotted_call_name(node.func)
                if call_name in def_PARAM_HIGH_RISK_CALLS:
                    wrapper_name = def_enclosing_function_name(node)
                    if not (call_name == "subprocess.Popen" and wrapper_name in def_PARAM_CONTROLLED_RISK_WRAPPERS):
                        risks.append({"code": "DYNAMIC_EXECUTION", "severity": "RED", "detail": call_name})
                if call_name.startswith("argparse.") or call_name == "ArgumentParser":
                    has_cli = True
            elif isinstance(node, ast.If):
                try:
                    test_text = ast.unparse(node.test)
                except Exception:
                    test_text = ""
                if "__name__" in test_text and "__main__" in test_text:
                    has_main = True
    except SyntaxError as exc:
        ast_ok = False
        compile_ok = False
        risks.append({"code": "AST_SYNTAX", "severity": "RED", "detail": f"line={exc.lineno} {exc.msg}"})
    for pattern in def_PARAM_SECRET_PATTERNS:
        if pattern.search(source_text):
            risks.append({"code": "HARDCODED_SECRET", "severity": "RED", "detail": pattern.pattern})
    for pattern in def_PARAM_ABSOLUTE_PATH_PATTERNS:
        if pattern.search(source_text):
            risks.append({"code": "PERSONAL_ABSOLUTE_PATH", "severity": "YELLOW", "detail": pattern.pattern})
    red_count = sum(1 for item in risks if item["severity"] == "RED")
    hydra_level = "HIGH" if red_count or len(risks) >= 4 else "MEDIUM" if risks else "LOW"
    status = "RED" if not ast_ok or red_count else "YELLOW" if risks else "GREEN"
    artifact_kind = "EXE" if has_main and has_cli else "PYD"
    result = def_SourceAnalysis(
        path=str(path_value),
        relative_path=relative_path,
        sha256=source_sha256,
        size_bytes=len(source_bytes),
        ast_ok=ast_ok,
        compile_ok=compile_ok,
        artifact_kind=artifact_kind,
        functions=sorted(set(functions)),
        classes=sorted(set(classes)),
        imports=sorted(set(item for item in imports if item)),
        risks=risks,
        hydra_level=hydra_level,
        status=status,
    )
    with def_ANALYSIS_CACHE_LOCK:
        def_ANALYSIS_CACHE[cache_key] = result
    return result


def def_iter_python_files(source_root: Path) -> Iterator[Path]:
    for path_value in sorted(source_root.rglob("*.py")):
        if any(part in def_PARAM_EXCLUDED_DIR_NAMES for part in path_value.relative_to(source_root).parts):
            continue
        if path_value.is_file():
            yield path_value


def def_scan_python_sources(source_root: Path) -> List[def_SourceAnalysis]:
    source_root = source_root.expanduser().resolve()
    if not source_root.is_dir():
        raise NotADirectoryError(str(source_root))
    source_files = list(def_iter_python_files(source_root))
    if len(source_files) < 2:
        return [def_analyze_python_source(path_value, source_root) for path_value in source_files]
    with ThreadPoolExecutor(max_workers=min(def_PARAM_PARALLEL_WORKERS, len(source_files)), thread_name_prefix="via-ast") as executor:
        return list(executor.map(lambda path_value: def_analyze_python_source(path_value, source_root), source_files))


def def_copy_source_with_hash_gate(
    source_path: Path,
    source_root: Path,
    staging_root: Path,
    refresh_staging: bool = False,
) -> Dict[str, Any]:
    source_path = def_validate_under_root(source_path, source_root)
    relative_path = source_path.relative_to(source_root.resolve())
    destination = (staging_root.resolve() / relative_path).resolve()
    def_validate_under_root(destination, staging_root.resolve())
    before_hash = def_sha256_file(source_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        existing_hash = def_sha256_file(destination)
        if existing_hash != before_hash:
            if not refresh_staging:
                raise FileExistsError(f"Staging collision with different content: {destination}")
            def_atomic_write_bytes(destination, source_path.read_bytes(), overwrite=True)
    else:
        shutil.copy2(source_path, destination)
    copy_hash = def_sha256_file(destination)
    after_hash = def_sha256_file(source_path)
    if before_hash != copy_hash or before_hash != after_hash:
        raise RuntimeError("SOURCE_MUTATION_OR_COPY_MISMATCH")
    return {
        "ok": True,
        "source": str(source_path),
        "copy": str(destination),
        "source_original_sha256": before_hash,
        "source_copy_sha256": copy_hash,
        "source_after_sha256": after_hash,
    }


def def_default_module_id(relative_path: str) -> str:
    normalized_path = str(relative_path).replace("\\", "/")
    stem = Path(normalized_path).stem.upper()
    stem = re.sub(r"^[0-9]+[_ .-]*", "", stem)
    stem = re.sub(r"[^A-Z0-9]+", "_", stem).strip("_") or "MODULE"
    if not stem[0].isalpha():
        stem = "VIA_" + stem
    path_hash = def_sha256_text(normalized_path)[:8].upper()
    module_id = f"{stem[:48]}_{path_hash}"
    if not def_PARAM_MODULE_ID_RE.fullmatch(module_id):
        raise ValueError(f"Unable to derive a valid module_id for {relative_path}")
    return module_id


def def_guard_snippet(
    module_id: str,
    required_entitlement: str,
    product_number: str,
    artifact_kind: str,
) -> str:
    if not def_PARAM_MODULE_ID_RE.fullmatch(module_id):
        raise ValueError("Invalid guard module_id")
    entitlement = required_entitlement.upper()
    if not def_PARAM_CAPABILITY_RE.fullmatch(entitlement):
        raise ValueError("Invalid guard entitlement")
    canonical_number = def_normalize_product_number(product_number)
    artifact_expression = "_via_guard_path(_via_guard_sys.argv[0]).resolve()" if artifact_kind == "EXE" else "_via_guard_path(__file__).resolve()"
    sys_import = "import sys as _via_guard_sys\n" if artifact_kind == "EXE" else ""
    return (
        f"\n# {def_PARAM_GUARD_MARKER}\n"
        "from pathlib import Path as _via_guard_path\n"
        f"{sys_import}"
        f"from {def_PARAM_RUNTIME_GUARD_MODULE} import def_enforce_module_guard_from_environment as _via_guard_enforce\n"
        "_VIA_GUARD_CONTEXT = _via_guard_enforce(\n"
        f"    module_id={module_id!r},\n"
        f"    required_entitlement={entitlement!r},\n"
        f"    expected_product_number={canonical_number!r},\n"
        f"    artifact_path={artifact_expression},\n"
        ")\n"
    )


def def_inject_product_guard(
    staging_path: Path,
    module_id: str,
    required_entitlement: str,
    product_number: str,
    artifact_kind: str,
) -> Dict[str, Any]:
    source_text = staging_path.read_text(encoding="utf-8-sig")
    if def_PARAM_GUARD_MARKER in source_text:
        raise ValueError(f"Guard marker already exists in staging source: {staging_path}")
    tree = ast.parse(source_text, filename=str(staging_path))
    insertion_line = 0
    body_index = 0
    if tree.body and isinstance(tree.body[0], ast.Expr) and isinstance(getattr(tree.body[0], "value", None), ast.Constant):
        if isinstance(tree.body[0].value.value, str):
            insertion_line = int(tree.body[0].end_lineno or tree.body[0].lineno)
            body_index = 1
    while body_index < len(tree.body):
        node = tree.body[body_index]
        if not isinstance(node, ast.ImportFrom) or node.module != "__future__":
            break
        insertion_line = int(node.end_lineno or node.lineno)
        body_index += 1
    lines = source_text.splitlines(keepends=True)
    snippet = def_guard_snippet(module_id, required_entitlement, product_number, artifact_kind)
    guarded_text = "".join(lines[:insertion_line]) + snippet + "".join(lines[insertion_line:])
    guarded_tree = ast.parse(guarded_text, filename=str(staging_path))
    compile(guarded_tree, str(staging_path), "exec")
    def_atomic_write_text(staging_path, guarded_text, overwrite=True)
    return {
        "ok": True,
        "status": "GUARD_INJECTED",
        "module_id": module_id,
        "required_entitlement": required_entitlement.upper(),
        "product_number": def_normalize_product_number(product_number),
        "guarded_sha256": def_sha256_file(staging_path),
        "guard_marker": def_PARAM_GUARD_MARKER,
    }


def def_build_nuitka_command(staging_file: Path, output_dir: Path, artifact_kind: str) -> List[str]:
    base_command = [
        sys.executable,
        "-m",
        "nuitka",
        "--assume-yes-for-downloads",
        f"--include-module={def_PARAM_RUNTIME_GUARD_MODULE}",
        f"--output-dir={output_dir}",
    ]
    if artifact_kind == "PYD":
        return base_command + ["--module", "--follow-imports", str(staging_file)]
    return base_command + ["--standalone", "--follow-imports", str(staging_file)]


def def_execute_nuitka_build(command: Sequence[str], timeout_seconds: int = 3600) -> Dict[str, Any]:
    if importlib.util.find_spec("nuitka") is None:
        return {"ok": False, "status": "NUITKA_NOT_INSTALLED", "command": list(command)}
    completed = def_run_subprocess_bounded(command, timeout_seconds=timeout_seconds)
    return {
        "ok": completed["ok"],
        "status": "BUILD_PASS" if completed["ok"] else f"BUILD_{completed['status']}",
        "exit_code": completed["exit_code"],
        "command": list(command),
        "stdout_tail": completed["stdout_tail"],
        "stderr_tail": completed["stderr_tail"],
        "timed_out": completed["timed_out"],
        "output_limited": completed["output_limited"],
    }


def def_package_plan(
    source_root: Path,
    staging_root: Path,
    output_root: Path,
    product_binding: Mapping[str, Any],
    execute_build: bool = False,
    audit_path: Path = def_PARAM_AUDIT_JSONL,
) -> Dict[str, Any]:
    source_root = source_root.expanduser().resolve()
    staging_root = staging_root.expanduser().resolve()
    output_root = output_root.expanduser().resolve()
    roots = {"source": source_root, "staging": staging_root, "output": output_root}
    for first_name, first_path in roots.items():
        for second_name, second_path in roots.items():
            if first_name >= second_name:
                continue
            if first_path == second_path or first_path in second_path.parents or second_path in first_path.parents:
                raise ValueError(f"Package roots must not overlap: {first_name}/{second_name}")
    def_require_free_disk(staging_root)
    def_require_free_disk(output_root)
    binding = def_public_product_binding(product_binding)
    analyses = def_scan_python_sources(source_root)
    if not analyses:
        raise ValueError("No Python source files found")
    rows: List[Dict[str, Any]] = []
    for analysis in analyses:
        source_path = Path(analysis.path)
        copy_result = def_copy_source_with_hash_gate(source_path, source_root, staging_root, refresh_staging=True)
        staging_file = Path(copy_result["copy"])
        module_id = def_default_module_id(analysis.relative_path)
        if source_path.stem == def_PARAM_RUNTIME_GUARD_MODULE:
            guard_result = {
                "ok": True,
                "status": "RUNTIME_GUARD_OWNER",
                "module_id": module_id,
                "required_entitlement": def_PARAM_MASTER_ENTITLEMENT,
                "product_number": binding["product_number"],
                "guarded_sha256": def_sha256_file(staging_file),
            }
        else:
            guard_result = def_inject_product_guard(
                staging_file,
                module_id,
                def_PARAM_MASTER_ENTITLEMENT,
                binding["product_number"],
                analysis.artifact_kind,
            )
        module_output = output_root / Path(analysis.relative_path).with_suffix("")
        command = def_build_nuitka_command(staging_file, module_output, analysis.artifact_kind)
        if execute_build and (analysis.status == "RED" or not guard_result["ok"]):
            build_result = {"ok": False, "status": "BLOCKED_BY_SECURITY_GATE", "command": command}
        else:
            build_result = def_execute_nuitka_build(command) if execute_build else {"ok": True, "status": "PLAN_ONLY", "command": command}
        source_after_build = def_sha256_file(source_path)
        source_unchanged = secrets.compare_digest(source_after_build, copy_result["source_original_sha256"])
        if not source_unchanged:
            build_result = {**build_result, "ok": False, "status": "SOURCE_MUTATION_DETECTED"}
        rows.append({
            "analysis": asdict(analysis),
            "copy_gate": {**copy_result, "source_after_build_sha256": source_after_build, "source_unchanged": source_unchanged},
            "guard": guard_result,
            "build": build_result,
        })
    payload = {
        "schema": "via.package-plan.v2",
        "generated_at": def_now_utc_iso(),
        "source_root": str(source_root),
        "staging_root": str(staging_root),
        "output_root": str(output_root),
        "execute_build": execute_build,
        "source_policy": "READ_ONLY",
        "build_policy": "COPY_FIRST",
        "product_binding": binding,
        "master_key_embedded": False,
        "rows": rows,
        "summary": {
            "files": len(rows),
            "green": sum(1 for row in rows if row["analysis"]["status"] == "GREEN"),
            "yellow": sum(1 for row in rows if row["analysis"]["status"] == "YELLOW"),
            "red": sum(1 for row in rows if row["analysis"]["status"] == "RED"),
            "guard_failures": sum(1 for row in rows if not row["guard"]["ok"]),
            "build_failures": sum(1 for row in rows if not row["build"]["ok"]),
            "source_mutations": sum(1 for row in rows if not row["copy_gate"]["source_unchanged"]),
        },
    }
    payload["summary"]["plan_ready"] = (
        payload["summary"]["red"] == 0
        and payload["summary"]["guard_failures"] == 0
        and payload["summary"]["build_failures"] == 0
        and payload["summary"]["source_mutations"] == 0
    )
    payload["summary"]["release_eligible"] = False
    payload["summary"]["release_status"] = "REQUIRES_DEPLOYLEDGER_QUALIFICATION"
    output_root.mkdir(parents=True, exist_ok=True)
    def_write_json(output_root / "VIA_PYD_Package_Plan.json", payload, overwrite=True)
    def_append_audit_event(audit_path, "PACKAGE_PLAN", payload["summary"])
    return payload


def def_find_contract_candidate(base_root: Path, patterns: Sequence[str]) -> List[Path]:
    output: List[Path] = []
    for pattern in patterns:
        output.extend(path_value for path_value in base_root.rglob(pattern) if path_value.is_file())
    return sorted(set(output))


def def_audit_core_contracts(base_root: Path, analyses: Sequence[def_SourceAnalysis]) -> Dict[str, Any]:
    analysis_map = {Path(item.path).resolve(): item for item in analyses}
    rows: List[Dict[str, Any]] = []
    for contract_name, contract in def_PARAM_CORE_CONTRACTS.items():
        candidates = def_find_contract_candidate(base_root, contract["patterns"])
        if not candidates:
            rows.append({"contract": contract_name, "status": "RED", "detail": "MISSING", "candidates": []})
            continue
        if len(candidates) > 1:
            rows.append({
                "contract": contract_name,
                "status": "YELLOW",
                "detail": "HYDRA_MULTIPLE_CANDIDATES",
                "candidates": [str(item) for item in candidates],
            })
            continue
        candidate = candidates[0].resolve()
        analysis = analysis_map.get(candidate) or def_analyze_python_source(candidate, base_root)
        found_symbols = set(analysis.functions) | set(analysis.classes)
        missing_symbols = [item for item in contract["required_symbols"] if item not in found_symbols]
        rows.append({
            "contract": contract_name,
            "status": "RED" if missing_symbols or not analysis.ast_ok else "GREEN",
            "detail": "MISSING_SYMBOLS" if missing_symbols else "ALIGNED",
            "missing_symbols": missing_symbols,
            "candidate": str(candidate),
            "capabilities": contract["capabilities"],
        })
    return {
        "rows": rows,
        "green": sum(1 for item in rows if item["status"] == "GREEN"),
        "yellow": sum(1 for item in rows if item["status"] == "YELLOW"),
        "red": sum(1 for item in rows if item["status"] == "RED"),
    }


def def_scan_html_security(base_root: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for path_value in sorted(base_root.rglob("*.html")):
        if any(part in def_PARAM_EXCLUDED_DIR_NAMES for part in path_value.relative_to(base_root).parts):
            continue
        text_value = path_value.read_text(encoding="utf-8", errors="replace")
        issues: List[str] = []
        if re.search(r"(?i)localStorage.*(?:password|pwd)|(?:password|pwd).*localStorage", text_value, re.DOTALL):
            issues.append("CLIENT_SIDE_PASSWORD_STORAGE")
        if "via2025" in text_value:
            issues.append("DEFAULT_PASSWORD_DISCLOSED")
        rows.append({
            "file": def_safe_relative(path_value, base_root),
            "status": "RED" if issues else "GREEN",
            "issues": issues,
        })
    return rows


# =============================================================================
# def TOP-25 RESILIENCE CONTROL PLANE
# =============================================================================
def def_top25_external_keys() -> List[str]:
    return sorted({str(item["external"]) for item in def_PARAM_TOP25_RISK_CONTROLS if item.get("external")})


def def_top25_evidence_template(
    deployment_mode: str = "DEVELOPMENT",
    release_role: str = "DEVELOPER",
) -> Dict[str, Any]:
    mode = deployment_mode.upper()
    role = release_role.upper()
    if mode not in def_PARAM_ALLOWED_DEPLOYMENT_MODES:
        raise ValueError("Unsupported deployment mode")
    if role not in def_PARAM_ALLOWED_RELEASE_ROLES:
        raise ValueError("Unsupported release role")
    return {
        "schema": "via.top25-evidence.v2.2",
        "deployment_mode": mode,
        "release_role": role,
        "release_id": "SET-BEFORE-SIGNING",
        "generated_at": def_now_utc_iso(),
        "evidence": {key: False for key in def_top25_external_keys()},
        "notes": {key: "" for key in def_top25_external_keys()},
    }


def def_validate_top25_evidence_payload(
    payload: Mapping[str, Any],
    expected_mode: str,
    expected_role: str,
) -> Dict[str, Any]:
    payload = def_require_mapping(payload, "top25 evidence")
    if payload.get("schema") != "via.top25-evidence.v2.2":
        raise ValueError("Unsupported Top-25 evidence schema")
    mode = str(payload.get("deployment_mode", "")).upper()
    role = str(payload.get("release_role", "")).upper()
    if mode != expected_mode.upper() or role != expected_role.upper():
        raise ValueError("Top-25 evidence mode/role mismatch")
    release_id = payload.get("release_id")
    if not isinstance(release_id, str) or not release_id.strip() or len(release_id) > 128:
        raise ValueError("Top-25 evidence release_id is invalid")
    evidence_input = def_require_mapping(payload.get("evidence"), "top25 evidence.evidence")
    notes_input = def_require_mapping(payload.get("notes", {}), "top25 evidence.notes")
    allowed_keys = set(def_top25_external_keys())
    unknown = (set(evidence_input) | set(notes_input)) - allowed_keys
    if unknown:
        raise ValueError(f"Unknown Top-25 evidence keys: {sorted(unknown)}")
    evidence = {
        key: def_require_native_bool(evidence_input.get(key, False), f"top25 evidence.{key}")
        for key in sorted(allowed_keys)
    }
    notes: Dict[str, str] = {}
    for key in sorted(allowed_keys):
        note = notes_input.get(key, "")
        if not isinstance(note, str) or len(note) > 1000:
            raise ValueError(f"Top-25 evidence note is invalid: {key}")
        notes[key] = note
    return {
        **dict(payload),
        "deployment_mode": mode,
        "release_role": role,
        "release_id": release_id.strip(),
        "evidence": evidence,
        "notes": notes,
    }


def def_sign_top25_evidence(
    payload: Mapping[str, Any],
    release_private_key: Any,
    key_id: str = def_PARAM_RELEASE_KEY_ID,
) -> Dict[str, Any]:
    normalized = def_validate_top25_evidence_payload(
        payload,
        str(payload.get("deployment_mode", "")),
        str(payload.get("release_role", "")),
    )
    if normalized["release_id"] == "SET-BEFORE-SIGNING":
        raise ValueError("Set a real release_id before signing Top-25 evidence")
    return def_sign_payload(normalized, release_private_key, key_id, "via.top25-evidence-envelope.v2.2")


def def_load_top25_evidence_document(
    evidence_path: Optional[Path],
    deployment_mode: str,
    release_role: str,
    release_public_key: Any = None,
    expected_key_id: str = def_PARAM_RELEASE_KEY_ID,
) -> Tuple[Dict[str, Any], bool]:
    if evidence_path is None:
        return def_top25_evidence_template(deployment_mode, release_role), False
    document = def_read_json(evidence_path)
    if isinstance(document, Mapping) and document.get("schema") == "via.top25-evidence-envelope.v2.2":
        if release_public_key is None:
            raise ValueError("Signed Top-25 evidence requires a trusted release public key")
        payload = def_verify_signed_payload(
            document,
            release_public_key,
            expected_key_id=expected_key_id,
            expected_schema="via.top25-evidence-envelope.v2.2",
        )
        return def_validate_top25_evidence_payload(payload, deployment_mode, release_role), True
    payload = def_validate_top25_evidence_payload(document, deployment_mode, release_role)
    return payload, False


def def_top25_builtin_probe(probe: str, base_root: Path) -> Tuple[bool, str]:
    required_functions: Dict[str, Sequence[str]] = {
        "guard_chain": (
            "def_inject_product_guard", "def_enforce_module_guard_from_environment",
            "def_verify_runtime_token", "def_consume_runtime_token_id",
        ),
        "clock_state": ("def_validate_clock_state", "def_write_clock_state"),
        "strict_types": (
            "def_require_native_bool", "def_require_int", "def_json_object_no_duplicates",
            "def_validate_json_shape",
        ),
        "mobile_policy": ("def_validate_profile", "def_issue_license"),
        "product_binding": (
            "def_master_key_hash", "def_verify_license", "def_verify_module_manifest",
            "def_create_module_handshake",
        ),
        "compatibility": ("def_validate_module_compatibility",),
        "package_tree": ("def_collect_package_tree", "def_verify_package_tree_manifest"),
        "streaming_copy": (
            "def_sha256_file", "def_download_verified_artifact", "def_copy_source_with_hash_gate",
        ),
        "bounded_process": ("def_run_subprocess_bounded", "def_terminate_process_tree"),
        "input_schema": (
            "def_validate_json_shape", "def_validate_local_schema", "def_prepare_local_rows",
        ),
        "idempotency": ("def_validate_request_id", "def_ingest_local_rows"),
        "atomic_state": ("def_atomic_write_bytes", "def_file_lock", "def_append_audit_event"),
        "audit_chain": ("def_append_audit_event", "def_verify_audit_chain"),
        "data_location": ("def_validate_active_database_location", "def_validate_under_root"),
    }
    if probe in required_functions:
        missing = [name for name in required_functions[probe] if not callable(globals().get(name))]
        return (not missing, "built-in functions present" if not missing else f"missing functions: {missing}")
    if probe == "trust_pins":
        pins = {
            "license": def_PARAM_TRUSTED_LICENSE_PUBLIC_KEY_SHA256,
            "release": def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256,
            "cloud": def_PARAM_TRUSTED_CLOUD_TRANSPORT_PUBLIC_KEY_SHA256,
        }
        invalid = [name for name, value in pins.items() if not def_PARAM_SHA256_RE.fullmatch(str(value).lower())]
        return (not invalid, "all official public-key pins configured" if not invalid else f"missing/invalid pins: {invalid}")
    if probe == "device_secret_store":
        if os.name == "nt":
            return (callable(globals().get("def_dpapi_protect")), "Windows DPAPI implementation available")
        return (False, "non-Windows host cannot validate Windows DPAPI/ACL")
    if probe == "token_hygiene":
        engine_path = Path(__file__).resolve()
        source_text = engine_path.read_text(encoding="utf-8-sig", errors="replace")
        forbidden = [pattern for pattern in ("?token=", "?poll_token=", "--master-key") if pattern in source_text.lower()]
        return (not forbidden, "no secret-bearing URL/CLI pattern found" if not forbidden else f"forbidden patterns: {forbidden}")
    if probe == "external":
        return (False, "external deployment evidence required")
    return (False, f"unknown probe: {probe}")


def def_evaluate_top25_controls(
    base_root: Path,
    deployment_mode: str,
    release_role: str,
    evidence_payload: Optional[Mapping[str, Any]] = None,
    evidence_verified: bool = False,
) -> Dict[str, Any]:
    mode = deployment_mode.upper()
    role = release_role.upper()
    if mode not in def_PARAM_ALLOWED_DEPLOYMENT_MODES:
        raise ValueError("Unsupported deployment mode")
    if role not in def_PARAM_ALLOWED_RELEASE_ROLES:
        raise ValueError("Unsupported release role")
    root = base_root.expanduser().resolve()
    if not root.exists():
        raise FileNotFoundError(str(root))
    evidence_document = def_validate_top25_evidence_payload(
        evidence_payload or def_top25_evidence_template(mode, role),
        mode,
        role,
    )
    evidence = evidence_document["evidence"]
    findings: List[def_RiskFinding] = []
    for control in def_PARAM_TOP25_RISK_CONTROLS:
        applies = role in control["roles"]
        external_key = str(control.get("external", ""))
        if not applies:
            status, state, detector, evidence_text = "GREEN", "NOT_APPLICABLE", "role scope", f"role={role}"
        else:
            builtin_ok, detector = def_top25_builtin_probe(str(control["probe"]), root)
            external_ok = bool(external_key and evidence.get(external_key, False))
            external_usable = external_ok and (mode == "DEVELOPMENT" or evidence_verified)
            if str(control["probe"]) == "external":
                control_ok = external_usable
                partial = False
            else:
                control_ok = builtin_ok and (not external_key or external_usable)
                partial = builtin_ok and bool(external_key) and not external_usable
            if control_ok:
                status, state = "GREEN", "ENFORCED"
            elif mode == "DEVELOPMENT" and (partial or str(control["probe"]) == "external" or control["id"] == "RISK-002"):
                status, state = "YELLOW", "EXTERNAL_REQUIRED" if external_key else "CONFIGURATION_REQUIRED"
            else:
                status, state = "RED", "BLOCKED"
            evidence_text = (
                f"{external_key}={external_ok}; signed={evidence_verified}"
                if external_key else detector
            )
        findings.append(def_RiskFinding(
            risk_id=str(control["id"]),
            severity=str(control["severity"]),
            title=str(control["title"]),
            status=status,
            state=state,
            applies_to_role=applies,
            detector=detector,
            evidence=evidence_text,
            solution=str(control["solution"]),
            external_requirement=external_key,
        ))
    rows = [asdict(item) for item in findings]
    counts = {color: sum(1 for item in rows if item["status"] == color) for color in ("GREEN", "YELLOW", "RED")}
    overall = "RED" if counts["RED"] else "YELLOW" if counts["YELLOW"] else "GREEN"
    return {
        "schema": "via.top25-resilience.v2.2",
        "engine": def_PARAM_ENGINE_NAME,
        "version": def_PARAM_ENGINE_VERSION,
        "generated_at": def_now_utc_iso(),
        "base_root": str(root),
        "deployment_mode": mode,
        "release_role": role,
        "evidence_verified": evidence_verified,
        "overall": overall,
        "release_eligible": mode == "PRODUCTION" and overall == "GREEN" and evidence_verified,
        "counts": counts,
        "quantity_validation": {
            "expected_controls": 25,
            "actual_controls": len(rows),
            "unique_controls": len({item["risk_id"] for item in rows}),
        },
        "rows": rows,
    }


def def_render_top25_html(payload: Mapping[str, Any]) -> str:
    table_rows: List[str] = []
    for row in payload.get("rows", []):
        table_rows.append(
            "<tr>"
            f"<td>{html.escape(str(row['risk_id']))}</td>"
            f"<td>{html.escape(str(row['severity']))}</td>"
            f"<td>{def_status_badge(str(row['status']))}</td>"
            f"<td>{html.escape(str(row['title']))}</td>"
            f"<td>{html.escape(str(row['state']))}</td>"
            f"<td>{html.escape(str(row['detector']))}</td>"
            f"<td>{html.escape(str(row['evidence']))}</td>"
            f"<td>{html.escape(str(row['solution']))}</td>"
            "</tr>"
        )
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Top-25 Resilience Matrix</title><style>
:root{{--paper:#fbf8f2;--card:#fffdf8;--ink:#26231f;--muted:#746d63;--line:#ddd5c8;--red:#aa2d2d;--green:#1d7651;--yellow:#a06b00;--seal:#a51f1f}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--paper);color:var(--ink);font:11px/1.42 "Segoe UI","Noto Sans TC",sans-serif}}.wrap{{max-width:1800px;margin:auto;padding:16px}}
header{{display:grid;grid-template-columns:52px 1fr auto;gap:12px;align-items:center;border-bottom:2px solid var(--seal);padding:8px 0 12px}}.seal{{width:46px;height:46px;border:2px solid var(--seal);color:var(--seal);display:grid;place-items:center;font:700 26px serif}}
h1{{font-size:16px;margin:0}}.latin{{font-size:9px;letter-spacing:1.6px;color:var(--seal)}}.sub{{font-size:10px;font-weight:650}}.meta{{color:var(--muted)}}.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;margin-top:12px}}
.summary{{display:grid;grid-template-columns:repeat(4,minmax(90px,1fr));gap:8px;margin:10px 0}}.summary div{{border:1px solid var(--line);padding:7px;border-radius:7px}}table{{width:100%;border-collapse:collapse;table-layout:fixed}}th,td{{border:1px solid var(--line);padding:5px 6px;text-align:left;vertical-align:top;overflow-wrap:anywhere}}th{{background:#f2ece2;font-size:9px}}th:nth-child(1){{width:65px}}th:nth-child(2){{width:65px}}th:nth-child(3){{width:72px}}th:nth-child(5){{width:110px}}.pill{{display:inline-block;border-radius:999px;padding:2px 7px;color:white;font-weight:700;font-size:9px}}.g{{background:var(--green)}}.y{{background:var(--yellow)}}.r{{background:var(--red)}}
@media(max-width:760px){{.wrap{{padding:7px}}header{{grid-template-columns:40px 1fr}}.meta{{display:none}}.summary{{grid-template-columns:1fr 1fr}}table{{font-size:9px}}}}
</style></head><body><div class="wrap"><header><div class="seal">理</div><div><h1>{html.escape(def_PARAM_SYSTEM_NAME)}</h1><div class="latin">{html.escape(def_PARAM_SYSTEM_LATIN)}</div><div class="sub">{html.escape(def_PARAM_SYSTEM_SUBTITLE)}</div></div><div class="meta">Top-25 · v{html.escape(def_PARAM_ENGINE_VERSION)}</div></header>
<section class="card"><h2>Top-25 Resilience Matrix · {html.escape(str(payload['deployment_mode']))} / {html.escape(str(payload['release_role']))}</h2>
<div class="summary"><div><b>{def_status_badge(str(payload['overall']))}</b><br>Overall</div><div><b>{payload['counts']['GREEN']}</b><br>Green</div><div><b>{payload['counts']['YELLOW']}</b><br>Yellow</div><div><b>{payload['counts']['RED']}</b><br>Red</div></div>
<table><thead><tr><th>ID</th><th>Level</th><th>RYG</th><th>可能錯誤</th><th>State</th><th>Detector</th><th>Evidence</th><th>整合解決方案</th></tr></thead><tbody>{''.join(table_rows)}</tbody></table></section></div></body></html>"""


def def_apply_top25_safe_repairs(output_dir: Path) -> List[Dict[str, str]]:
    actions: List[Dict[str, str]] = []
    for directory_name in ("reports", "audit", "runtime", "staging"):
        directory = output_dir / directory_name
        existed = directory.exists()
        directory.mkdir(parents=True, exist_ok=True)
        actions.append({
            "action": "DIRECTORY_VERIFIED" if existed else "DIRECTORY_CREATED",
            "path": str(directory.resolve()),
        })
    return actions


def def_run_top25_resilience_audit(
    base_root: Path,
    output_dir: Path,
    deployment_mode: str,
    release_role: str,
    evidence_payload: Optional[Mapping[str, Any]] = None,
    evidence_verified: bool = False,
    safe_repair: bool = False,
    audit_path: Path = def_PARAM_AUDIT_JSONL,
) -> Dict[str, Any]:
    output = output_dir.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    safe_actions = def_apply_top25_safe_repairs(output) if safe_repair else []
    payload = def_evaluate_top25_controls(
        base_root,
        deployment_mode,
        release_role,
        evidence_payload=evidence_payload,
        evidence_verified=evidence_verified,
    )
    payload["safe_repair"] = {"requested": safe_repair, "actions": safe_actions}
    json_path = output / def_PARAM_TOP25_JSON_REPORT.name
    html_path = output / def_PARAM_TOP25_HTML_REPORT.name
    template_path = output / def_PARAM_TOP25_EVIDENCE_TEMPLATE.name
    def_write_json(json_path, payload, overwrite=True)
    def_atomic_write_text(html_path, def_render_top25_html(payload), overwrite=True)
    if not template_path.exists():
        def_write_json(template_path, def_top25_evidence_template(deployment_mode, release_role), overwrite=False)
    event = def_append_audit_event(audit_path, "TOP25_RESILIENCE_AUDIT", {
        "deployment_mode": payload["deployment_mode"],
        "release_role": payload["release_role"],
        "overall": payload["overall"],
        "counts": payload["counts"],
        "evidence_verified": evidence_verified,
    })
    payload["json_report"] = str(json_path)
    payload["html_report"] = str(html_path)
    payload["evidence_template"] = str(template_path)
    payload["audit_event_hash"] = event["event_hash"]
    return payload


# =============================================================================
# def PANORAMIC MATRIX AND THREE-ROUND GOVERNANCE
# =============================================================================
def def_round_classification(round_number: int) -> Dict[str, Any]:
    if round_number == 1:
        return {
            "name": "Comprehensive Fix",
            "parallel_safe": ["path parameterization", "secret detection", "copy/hash gates", "schema inventory"],
            "sequence_dependent": [],
            "high_risk_suggestions_only": ["canonical SSOT mutation", "private-key operations"],
        }
    if round_number == 2:
        return {
            "name": "Sequential Integration",
            "parallel_safe": [],
            "sequence_dependent": ["Registry", "EnvManager", "module manifest", "license verifier", "runtime handshake"],
            "high_risk_suggestions_only": ["release promotion", "license issuance"],
        }
    return {
        "name": "Stability Hardening",
        "parallel_safe": ["format", "report", "negative tests", "quantity validation"],
        "sequence_dependent": ["final integrity recheck"],
        "high_risk_suggestions_only": ["canonical release pointer"],
    }


def def_build_panorama_round(base_root: Path, round_number: int) -> Dict[str, Any]:
    started = time.perf_counter()
    analyses = def_scan_python_sources(base_root)
    contracts = def_audit_core_contracts(base_root, analyses)
    html_rows = def_scan_html_security(base_root)
    top25 = def_evaluate_top25_controls(base_root, "DEVELOPMENT", "DEVELOPER")
    red_sources = sum(1 for item in analyses if item.status == "RED")
    yellow_sources = sum(1 for item in analyses if item.status == "YELLOW")
    red_html = sum(1 for item in html_rows if item["status"] == "RED")
    overall = (
        "RED"
        if red_sources or contracts["red"] or red_html or top25["counts"]["RED"]
        else "YELLOW"
        if yellow_sources or contracts["yellow"] or top25["counts"]["YELLOW"]
        else "GREEN"
    )
    return {
        "round": round_number,
        "classification": def_round_classification(round_number),
        "generated_at": def_now_utc_iso(),
        "overall": overall,
        "source_matrix": [asdict(item) for item in analyses],
        "contract_matrix": contracts,
        "html_security_matrix": html_rows,
        "top25_matrix": top25,
        "hydra_matrix": [
            {"file": item.relative_path, "level": item.hydra_level, "risks": len(item.risks)}
            for item in analyses if item.hydra_level != "LOW"
        ],
        "ssot_alignment": {
            "canonical_business_ssot_owner": "VIA_SSOT_Unified",
            "license_policy_owner": def_PARAM_ENGINE_NAME,
            "duplicate_owner_detected": False,
        },
        "accelerators": {name: True for name in def_PARAM_ACCELERATORS},
        "quantity_validation": {
            "python_files": len(analyses),
            "html_files": len(html_rows),
            "contracts": len(contracts["rows"]),
            "accelerators_enabled": len(def_PARAM_ACCELERATORS),
            "top25_controls": top25["quantity_validation"]["actual_controls"],
        },
        "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
    }


def def_status_badge(status: str) -> str:
    normalized = status.upper()
    css_class = "g" if normalized in {"GREEN", "PASS", "ALIGNED"} else "y" if normalized in {"YELLOW", "WARN"} else "r"
    return f'<span class="pill {css_class}">{html.escape(normalized)}</span>'


def def_render_html_matrix(payload: Mapping[str, Any]) -> str:
    round_sections: List[str] = []
    for round_payload in payload.get("rounds", []):
        source_rows = []
        for row in round_payload.get("source_matrix", []):
            risk_text = "; ".join(f"{item['code']}: {item['detail']}" for item in row.get("risks", [])) or "—"
            source_rows.append(
                "<tr>"
                f"<td>{html.escape(row['relative_path'])}</td>"
                f"<td>{def_status_badge(row['status'])}</td>"
                f"<td>{html.escape(row['artifact_kind'])}</td>"
                f"<td>{html.escape(row['hydra_level'])}</td>"
                f"<td>{html.escape(risk_text)}</td>"
                "</tr>"
            )
        contract_rows = []
        for row in round_payload.get("contract_matrix", {}).get("rows", []):
            contract_rows.append(
                "<tr>"
                f"<td>{html.escape(row['contract'])}</td>"
                f"<td>{def_status_badge(row['status'])}</td>"
                f"<td>{html.escape(row['detail'])}</td>"
                f"<td>{html.escape(', '.join(row.get('missing_symbols', [])) or '—')}</td>"
                "</tr>"
            )
        top25_rows = []
        for row in round_payload.get("top25_matrix", {}).get("rows", []):
            top25_rows.append(
                "<tr>"
                f"<td>{html.escape(row['risk_id'])}</td>"
                f"<td>{def_status_badge(row['status'])}</td>"
                f"<td>{html.escape(row['title'])}</td>"
                f"<td>{html.escape(row['state'])}</td>"
                f"<td>{html.escape(row['solution'])}</td>"
                "</tr>"
            )
        round_sections.append(
            f"""
            <section class="card">
              <div class="section-head"><h2>Round {round_payload['round']} · {html.escape(round_payload['classification']['name'])}</h2>{def_status_badge(round_payload['overall'])}</div>
              <div class="metrics">
                <div><b>{round_payload['quantity_validation']['python_files']}</b><span>Python files</span></div>
                <div><b>{round_payload['contract_matrix']['green']}</b><span>Aligned contracts</span></div>
                <div><b>{len(round_payload['hydra_matrix'])}</b><span>Hydra findings</span></div>
                <div><b>{round_payload['quantity_validation']['accelerators_enabled']}/{len(def_PARAM_ACCELERATORS)}</b><span>Accelerators</span></div>
              </div>
              <h3>Subsystem / SSOT Contract Matrix</h3>
              <table><thead><tr><th>Contract</th><th>RYG</th><th>Alignment</th><th>Missing symbols</th></tr></thead><tbody>{''.join(contract_rows)}</tbody></table>
              <h3>Error / Optimization / Hydra Matrix</h3>
              <table><thead><tr><th>File</th><th>RYG</th><th>Package</th><th>Hydra</th><th>Finding</th></tr></thead><tbody>{''.join(source_rows)}</tbody></table>
              <h3>Top-25 Resilience Matrix</h3>
              <table><thead><tr><th>ID</th><th>RYG</th><th>Risk</th><th>State</th><th>Integrated solution</th></tr></thead><tbody>{''.join(top25_rows)}</tbody></table>
            </section>
            """
        )
    return f"""<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Hybrid Governance Matrix</title>
<style>
:root{{--paper:#fbf8f2;--card:#fffdf8;--ink:#26231f;--muted:#746d63;--line:#ddd5c8;--red:#aa2d2d;--green:#1d7651;--yellow:#a06b00;--seal:#a51f1f}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--paper);color:var(--ink);font:12px/1.45 "Segoe UI","Noto Sans TC",sans-serif}}
.wrap{{max-width:1500px;margin:auto;padding:18px}} header{{display:grid;grid-template-columns:56px 1fr auto;gap:14px;align-items:center;border-bottom:2px solid var(--seal);padding:8px 0 13px}}
.seal{{width:48px;height:48px;border:2px solid var(--seal);color:var(--seal);display:grid;place-items:center;font:700 27px serif}} h1{{font-size:17px;margin:0}} .latin{{font-size:10px;letter-spacing:1.7px;color:var(--seal)}} .sub{{font-size:11px;font-weight:650}} .stamp{{color:var(--muted)}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:14px;margin-top:14px;box-shadow:0 2px 8px #4b3d2a10}} .section-head{{display:flex;align-items:center;justify-content:space-between}} h2{{font-size:14px;margin:0 0 8px}} h3{{font-size:12px;margin:14px 0 6px}}
.metrics{{display:grid;grid-template-columns:repeat(4,minmax(100px,1fr));gap:8px;margin:8px 0}} .metrics div{{border:1px solid var(--line);padding:8px;border-radius:7px}} .metrics b{{display:block;font-size:16px}} .metrics span{{color:var(--muted)}}
table{{width:100%;border-collapse:collapse;table-layout:fixed}} th,td{{border:1px solid var(--line);padding:5px 7px;text-align:left;vertical-align:top;overflow-wrap:anywhere}} th{{background:#f2ece2;font-size:10px;text-transform:uppercase;letter-spacing:.4px}}
.pill{{display:inline-block;border-radius:999px;padding:2px 7px;color:white;font-weight:700;font-size:10px}} .g{{background:var(--green)}} .y{{background:var(--yellow)}} .r{{background:var(--red)}}
@media(max-width:760px){{.wrap{{padding:8px}}header{{grid-template-columns:44px 1fr}}.stamp{{display:none}}.seal{{width:38px;height:38px;font-size:21px}}.metrics{{grid-template-columns:1fr 1fr}}table{{font-size:10px}}}}
</style></head><body><div class="wrap">
<header><div class="seal">理</div><div><h1>{html.escape(def_PARAM_SYSTEM_NAME)}</h1><div class="latin">{html.escape(def_PARAM_SYSTEM_LATIN)}</div><div class="sub">{html.escape(def_PARAM_SYSTEM_SUBTITLE)}</div></div><div class="stamp">{html.escape(def_PARAM_ENGINE_NAME)} · v{html.escape(def_PARAM_ENGINE_VERSION)}</div></header>
{''.join(round_sections)}
</div></body></html>"""


def def_run_panorama(base_root: Path, output_dir: Path, rounds: int = 3) -> Dict[str, Any]:
    if rounds < 1 or rounds > 3:
        raise ValueError("Panoramic rounds must be between 1 and 3")
    base_root = base_root.expanduser().resolve()
    output_dir = output_dir.expanduser().resolve()
    round_payloads = [def_build_panorama_round(base_root, round_number) for round_number in range(1, rounds + 1)]
    payload = {
        "schema": "via.panorama-report.v2",
        "engine": def_PARAM_ENGINE_NAME,
        "version": def_PARAM_ENGINE_VERSION,
        "generated_at": def_now_utc_iso(),
        "base_root": str(base_root),
        "rounds": round_payloads,
        "final_status": round_payloads[-1]["overall"],
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    json_path = output_dir / def_PARAM_JSON_REPORT.name
    html_path = output_dir / def_PARAM_HTML_REPORT.name
    def_write_json(json_path, payload, overwrite=True)
    def_atomic_write_text(html_path, def_render_html_matrix(payload), overwrite=True)
    def_append_audit_event(def_PARAM_AUDIT_JSONL, "PANORAMA_AUDIT", {"final_status": payload["final_status"], "rounds": rounds})
    payload["json_report"] = str(json_path)
    payload["html_report"] = str(html_path)
    return payload


# =============================================================================
# def RUNTIME CONTEXT AND VIA ADAPTER SNAPSHOT
# =============================================================================
def def_build_runtime_context(base_root: Path, output_root: Path) -> def_RuntimeContext:
    analyses = def_scan_python_sources(base_root)
    contracts = def_audit_core_contracts(base_root, analyses)
    return def_RuntimeContext(
        base_root=str(base_root.resolve()),
        output_root=str(output_root.resolve()),
        product_sku=def_PARAM_PRODUCT_SKU,
        version=def_PARAM_ENGINE_VERSION,
        accelerators={name: True for name in def_PARAM_ACCELERATORS},
        api_anchors=dict(def_PARAM_API_ANCHORS),
        core_contracts=contracts,
        security_gates={
            "build_mode": def_PARAM_BUILD_MODE,
            "product_number_format": "XXXX-XXXX-XXXX",
            "master_key_required": True,
            "master_key_embedded_in_modules": False,
            "module_guard_injection": True,
            "runtime_token_one_use": True,
            "runtime_token_process_bound": True,
            "top25_controls": len(def_PARAM_TOP25_RISK_CONTROLS),
            "strict_json_types": True,
            "signed_package_tree": True,
            "module_compatibility_gate": True,
            "transactional_idempotency": True,
            "bounded_subprocess": True,
            "license_public_key_pinned": bool(def_PARAM_TRUSTED_LICENSE_PUBLIC_KEY_SHA256),
            "release_public_key_pinned": bool(def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256),
            "cloud_transport_public_key_pinned": bool(def_PARAM_TRUSTED_CLOUD_TRANSPORT_PUBLIC_KEY_SHA256),
            "production_client_ready": (
                def_PARAM_BUILD_MODE == "PRODUCTION"
                and bool(def_PARAM_TRUSTED_LICENSE_PUBLIC_KEY_SHA256)
                and bool(def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256)
                and bool(def_PARAM_TRUSTED_CLOUD_TRANSPORT_PUBLIC_KEY_SHA256)
            ),
        },
    )


def def_sample_profile(product_record: Mapping[str, Any]) -> Dict[str, Any]:
    binding = def_public_product_binding(product_record)
    return {
        "schema": "via.entitlement-profile.v2.1",
        "product_sku": binding["product_sku"],
        "edition": binding["edition"],
        "product_number": binding["product_number"],
        "master_key_hash": binding["master_key_hash"],
        "entitlements": [
            def_PARAM_MASTER_ENTITLEMENT,
            "VDF_FETCH", "VDF_ANALYTICS", "VRN_EXTRACT", "VAP_PRO",
            "METHODOLOGY_CORE", "BACKTEST", "FLOW_SIMULATION",
        ],
        "max_devices": {"pc": def_PARAM_MAX_PC_DEVICES, "mobile": def_PARAM_MAX_MOBILE_DEVICES},
        "mobile_policy": {"allowed": True, "required": False},
        "binding_revision": 1,
        "version_min": "2.0.0",
        "version_max": "2.999.999",
        "not_before": None,
        "expires_at": None,
        "release_channel": def_PARAM_RELEASE_CHANNEL,
    }


def def_test_product_fixture() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    product_record = def_create_product_record()
    return product_record, def_sample_profile(product_record)


# =============================================================================
# def SELF-TESTS — positive and negative security tests
# =============================================================================
def def_test_semver() -> None:
    assert def_version_in_range("2.1.0", "2.0.0", "2.9.9")
    assert not def_version_in_range("3.0.0", "2.0.0", "2.9.9")


def def_test_product_number_and_master_key() -> None:
    records = [def_create_product_record() for _ in range(64)]
    assert len({item["product_number"] for item in records}) == len(records)
    for record in records:
        normalized = def_validate_product_record(record)
        assert def_PARAM_PRODUCT_NUMBER_RE.fullmatch(normalized["product_number"])
        assert normalized["master_key"].startswith(def_PARAM_MASTER_KEY_PREFIX + "-")
        assert normalized["master_key_hash"] == def_master_key_hash(normalized["product_number"], normalized["master_key"])


def def_test_product_key_state_roundtrip() -> None:
    product = def_create_product_record()
    with tempfile.TemporaryDirectory() as temp_dir:
        state_path = Path(temp_dir) / "product_key.json"
        def_store_product_key_state(
            state_path, product["product_number"], product["master_key"],
            allow_insecure_test_store=True,
        )
        loaded = def_load_product_key_state(state_path, allow_insecure_test_store=True)
        assert loaded["product_number"] == product["product_number"]
        assert loaded["master_key_hash"] == product["master_key_hash"]
        tampered = def_read_json(state_path)
        tampered["master_key_hash"] = "f" * 64
        def_write_json(state_path, tampered, overwrite=True)
        try:
            def_load_product_key_state(state_path, allow_insecure_test_store=True)
        except ValueError as exc:
            assert "integrity" in str(exc).lower()
        else:
            raise AssertionError("Tampered Product KEY state must be rejected")


def def_test_audit_chain() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path_value = Path(temp_dir) / "audit.jsonl"
        def_append_audit_event(path_value, "A", {"value": 1})
        def_append_audit_event(path_value, "B", {"value": 2})
        assert def_verify_audit_chain(path_value).ok
        lines = path_value.read_text(encoding="utf-8").splitlines()
        payload = json.loads(lines[0])
        payload["details"]["value"] = 99
        lines[0] = json.dumps(payload)
        path_value.write_text("\n".join(lines) + "\n", encoding="utf-8")
        assert not def_verify_audit_chain(path_value).ok


def def_test_activation_license_roundtrip() -> None:
    crypto = def_require_cryptography()
    authority_private = crypto["private_class"].generate()
    device_private = crypto["private_class"].generate()
    product, profile = def_test_product_fixture()
    hashes = {"cpu": "a" * 64, "board": "b" * 64, "machine_guid": "c" * 64}
    request = def_create_activation_request(
        device_private, def_PARAM_PRODUCT_SKU, "PRO",
        product["product_number"], product["master_key"], "pc", hashes,
    )
    license_envelope = def_issue_license([request], profile, authority_private)
    result = def_verify_license(
        license_envelope,
        authority_private.public_key(),
        device_private,
        def_PARAM_PRODUCT_SKU,
        "2.1.0",
        product["product_number"],
        product["master_key"],
        required_entitlement="VDF_FETCH",
        current_hardware_hashes=hashes,
    )
    assert result.ok, result.errors


def def_test_license_tamper_rejected() -> None:
    crypto = def_require_cryptography()
    authority_private = crypto["private_class"].generate()
    device_private = crypto["private_class"].generate()
    product, profile = def_test_product_fixture()
    hashes = {"cpu": "a" * 64, "board": "b" * 64}
    request = def_create_activation_request(device_private, def_PARAM_PRODUCT_SKU, "PRO", product["product_number"], product["master_key"], "pc", hashes)
    license_envelope = def_issue_license([request], profile, authority_private)
    license_envelope["payload"]["edition"] = "FORGED"
    result = def_verify_license(
        license_envelope, authority_private.public_key(), device_private,
        def_PARAM_PRODUCT_SKU, "2.1.0", product["product_number"], product["master_key"], current_hardware_hashes=hashes,
    )
    assert not result.ok


def def_test_wrong_product_rejected() -> None:
    crypto = def_require_cryptography()
    authority_private = crypto["private_class"].generate()
    device_private = crypto["private_class"].generate()
    product, profile = def_test_product_fixture()
    hashes = {"cpu": "a" * 64, "board": "b" * 64}
    request = def_create_activation_request(device_private, def_PARAM_PRODUCT_SKU, "PRO", product["product_number"], product["master_key"], "pc", hashes)
    license_envelope = def_issue_license([request], profile, authority_private)
    result = def_verify_license(
        license_envelope, authority_private.public_key(), device_private,
        "WRONG-SKU", "2.1.0", product["product_number"], product["master_key"], current_hardware_hashes=hashes,
    )
    assert not result.ok


def def_test_wrong_product_number_and_master_key_rejected() -> None:
    crypto = def_require_cryptography()
    authority_private = crypto["private_class"].generate()
    device_private = crypto["private_class"].generate()
    product, profile = def_test_product_fixture()
    other_product = def_create_product_record()
    hashes = {"cpu": "a" * 64, "board": "b" * 64}
    request = def_create_activation_request(
        device_private, def_PARAM_PRODUCT_SKU, "PRO",
        product["product_number"], product["master_key"], "pc", hashes,
    )
    license_envelope = def_issue_license([request], profile, authority_private)
    wrong_number = def_verify_license(
        license_envelope, authority_private.public_key(), device_private,
        def_PARAM_PRODUCT_SKU, "2.1.0",
        other_product["product_number"], product["master_key"],
        current_hardware_hashes=hashes,
    )
    wrong_key = def_verify_license(
        license_envelope, authority_private.public_key(), device_private,
        def_PARAM_PRODUCT_SKU, "2.1.0",
        product["product_number"], other_product["master_key"],
        current_hardware_hashes=hashes,
    )
    assert not wrong_number.ok and not wrong_key.ok


def def_test_expired_license_rejected() -> None:
    crypto = def_require_cryptography()
    authority_private = crypto["private_class"].generate()
    device_private = crypto["private_class"].generate()
    product, profile = def_test_product_fixture()
    hashes = {"cpu": "a" * 64, "board": "b" * 64}
    request = def_create_activation_request(device_private, def_PARAM_PRODUCT_SKU, "PRO", product["product_number"], product["master_key"], "pc", hashes)
    profile["expires_at"] = "2025-01-01T00:00:00Z"
    license_envelope = def_issue_license([request], profile, authority_private, now_value=datetime(2024, 1, 1, tzinfo=timezone.utc))
    result = def_verify_license(
        license_envelope, authority_private.public_key(), device_private,
        def_PARAM_PRODUCT_SKU, "2.1.0", product["product_number"], product["master_key"], current_hardware_hashes=hashes,
        now_value=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert not result.ok


def def_test_entitlement_rejected() -> None:
    crypto = def_require_cryptography()
    authority_private = crypto["private_class"].generate()
    device_private = crypto["private_class"].generate()
    product, profile = def_test_product_fixture()
    hashes = {"cpu": "a" * 64, "board": "b" * 64}
    request = def_create_activation_request(device_private, def_PARAM_PRODUCT_SKU, "PRO", product["product_number"], product["master_key"], "pc", hashes)
    license_envelope = def_issue_license([request], profile, authority_private)
    result = def_verify_license(
        license_envelope, authority_private.public_key(), device_private,
        def_PARAM_PRODUCT_SKU, "2.1.0", product["product_number"], product["master_key"], required_entitlement="NOT_LICENSED",
        current_hardware_hashes=hashes,
    )
    assert not result.ok


def def_test_device_quorum() -> None:
    expected = {"cpu": "a", "board": "b", "machine_guid": "c"}
    assert def_hardware_match_count(expected, {"cpu": "a", "board": "b", "machine_guid": "x"}) == 2
    assert def_hardware_match_count(expected, {"cpu": "a", "board": "x", "machine_guid": "y"}) == 1


def def_test_wrong_device_rejected() -> None:
    crypto = def_require_cryptography()
    authority_private = crypto["private_class"].generate()
    licensed_device = crypto["private_class"].generate()
    copied_device = crypto["private_class"].generate()
    product, profile = def_test_product_fixture()
    hashes = {"cpu": "a" * 64, "board": "b" * 64}
    request = def_create_activation_request(licensed_device, def_PARAM_PRODUCT_SKU, "PRO", product["product_number"], product["master_key"], "pc", hashes)
    license_envelope = def_issue_license([request], profile, authority_private)
    result = def_verify_license(
        license_envelope, authority_private.public_key(), copied_device,
        def_PARAM_PRODUCT_SKU, "2.1.0", product["product_number"], product["master_key"], current_hardware_hashes=hashes,
    )
    assert not result.ok


def def_test_not_before_and_version_rejected() -> None:
    crypto = def_require_cryptography()
    authority_private = crypto["private_class"].generate()
    device_private = crypto["private_class"].generate()
    product, profile = def_test_product_fixture()
    hashes = {"cpu": "a" * 64, "board": "b" * 64}
    request = def_create_activation_request(device_private, def_PARAM_PRODUCT_SKU, "PRO", product["product_number"], product["master_key"], "pc", hashes)
    profile["not_before"] = "2027-01-01T00:00:00Z"
    license_envelope = def_issue_license([request], profile, authority_private)
    early = def_verify_license(
        license_envelope, authority_private.public_key(), device_private,
        def_PARAM_PRODUCT_SKU, "2.1.0", product["product_number"], product["master_key"], current_hardware_hashes=hashes,
        now_value=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    assert not early.ok
    profile["not_before"] = None
    license_envelope = def_issue_license([request], profile, authority_private)
    wrong_version = def_verify_license(
        license_envelope, authority_private.public_key(), device_private,
        def_PARAM_PRODUCT_SKU, "3.0.0", product["product_number"], product["master_key"], current_hardware_hashes=hashes,
    )
    assert not wrong_version.ok


def def_test_mobile_limit() -> None:
    crypto = def_require_cryptography()
    authority_private = crypto["private_class"].generate()
    mobile_a = crypto["private_class"].generate()
    mobile_b = crypto["private_class"].generate()
    product, profile = def_test_product_fixture()
    requests = [
        def_create_activation_request(mobile_a, def_PARAM_PRODUCT_SKU, "PRO", product["product_number"], product["master_key"], "mobile"),
        def_create_activation_request(mobile_b, def_PARAM_PRODUCT_SKU, "PRO", product["product_number"], product["master_key"], "mobile"),
    ]
    try:
        def_issue_license(requests, profile, authority_private)
    except ValueError as exc:
        assert "limit" in str(exc)
    else:
        raise AssertionError("Two mobile devices must exceed the default profile")


def def_test_module_manifest() -> None:
    crypto = def_require_cryptography()
    release_private = crypto["private_class"].generate()
    product, _ = def_test_product_fixture()
    with tempfile.TemporaryDirectory() as temp_dir:
        artifact = Path(temp_dir) / "VDF_Core.pyd"
        artifact.write_bytes(b"compiled-placeholder")
        manifest = def_build_module_manifest(
            artifact, "VDF_CORE", "2.1.0", ["VDF_FETCH"], "VDF_FETCH", "via_vdf", "def_run", "REL-001",
            product["product_number"], product["master_key_hash"],
        )
        envelope = def_sign_module_manifest(manifest, release_private)
        assert def_verify_module_manifest(envelope, release_private.public_key(), artifact).ok
        artifact.write_bytes(b"tampered")
        assert not def_verify_module_manifest(envelope, release_private.public_key(), artifact).ok


def def_test_module_handshake_roundtrip() -> None:
    crypto = def_require_cryptography()
    authority_private = crypto["private_class"].generate()
    release_private = crypto["private_class"].generate()
    device_private = crypto["private_class"].generate()
    product, profile = def_test_product_fixture()
    hashes = {"cpu": "a" * 64, "board": "b" * 64, "machine_guid": "c" * 64}
    activation = def_create_activation_request(device_private, def_PARAM_PRODUCT_SKU, "PRO", product["product_number"], product["master_key"], "pc", hashes)
    license_envelope = def_issue_license([activation], profile, authority_private)
    with tempfile.TemporaryDirectory() as temp_dir:
        artifact = Path(temp_dir) / "VDF_Core.pyd"
        artifact.write_bytes(b"native-engine")
        manifest = def_build_module_manifest(
            artifact, "VDF_CORE", "2.1.0", ["VDF_FETCH"], "VDF_FETCH", "via_vdf", "def_run", "REL-001",
            product["product_number"], product["master_key_hash"],
        )
        manifest_envelope = def_sign_module_manifest(manifest, release_private)
        result = def_create_module_handshake(
            manifest_envelope, release_private.public_key(), artifact,
            license_envelope, authority_private.public_key(), device_private,
            def_PARAM_PRODUCT_SKU, "2.1.0", product["product_number"], product["master_key"], hashes, "server-nonce-001",
            Path(temp_dir) / "clock.json",
        )
        assert result.ok, result.errors
        token_payload = def_verify_signed_payload(
            result.data["token"], device_private.public_key(), expected_schema="via.module-handshake-envelope.v2.1"
        )
        assert token_payload["module_id"] == "VDF_CORE"


def def_test_runtime_token_one_use_and_process_binding() -> None:
    crypto = def_require_cryptography()
    authority_private = crypto["private_class"].generate()
    release_private = crypto["private_class"].generate()
    device_private = crypto["private_class"].generate()
    product, profile = def_test_product_fixture()
    hashes = {"cpu": "a" * 64, "board": "b" * 64, "machine_guid": "c" * 64}
    activation = def_create_activation_request(
        device_private, def_PARAM_PRODUCT_SKU, "PRO",
        product["product_number"], product["master_key"], "pc", hashes,
    )
    license_envelope = def_issue_license([activation], profile, authority_private)
    with tempfile.TemporaryDirectory() as temp_dir:
        artifact = Path(temp_dir) / "VDF_Core.pyd"
        artifact.write_bytes(b"native-engine")
        manifest = def_build_module_manifest(
            artifact, "VDF_CORE", "2.1.0", [def_PARAM_MASTER_ENTITLEMENT],
            def_PARAM_MASTER_ENTITLEMENT, "via_vdf", "def_run", "REL-001",
            product["product_number"], product["master_key_hash"],
        )
        manifest_envelope = def_sign_module_manifest(manifest, release_private)
        handshake = def_create_module_handshake(
            manifest_envelope, release_private.public_key(), artifact,
            license_envelope, authority_private.public_key(), device_private,
            def_PARAM_PRODUCT_SKU, "2.1.0", product["product_number"], product["master_key"],
            hashes, "runtime-nonce-0001", execution_mode="IN_PROCESS", target_pid=4242,
        )
        assert handshake.ok, handshake.errors
        ledger = Path(temp_dir) / "replay.jsonl"
        first = def_verify_runtime_token(
            handshake.data["token"], device_private.public_key(), manifest,
            product["product_number"], product["master_key"], def_PARAM_MASTER_ENTITLEMENT,
            expected_license_id=license_envelope["payload"]["license_id"],
            expected_device_id=license_envelope["payload"]["devices"][0]["device_id"],
            replay_ledger=ledger, current_pid=4242,
        )
        second = def_verify_runtime_token(
            handshake.data["token"], device_private.public_key(), manifest,
            product["product_number"], product["master_key"], def_PARAM_MASTER_ENTITLEMENT,
            replay_ledger=ledger, current_pid=4242,
        )
        assert first.ok and not second.ok
        assert "replay" in " ".join(second.errors).lower()
        next_handshake = def_create_module_handshake(
            manifest_envelope, release_private.public_key(), artifact,
            license_envelope, authority_private.public_key(), device_private,
            def_PARAM_PRODUCT_SKU, "2.1.0", product["product_number"], product["master_key"],
            hashes, "runtime-nonce-0002", execution_mode="IN_PROCESS", target_pid=4242,
        )
        wrong_process = def_verify_runtime_token(
            next_handshake.data["token"], device_private.public_key(), manifest,
            product["product_number"], product["master_key"], def_PARAM_MASTER_ENTITLEMENT,
            replay_ledger=ledger, current_pid=9999,
        )
        assert not wrong_process.ok


def def_test_manifest_product_binding_mismatch_rejected() -> None:
    crypto = def_require_cryptography()
    authority_private = crypto["private_class"].generate()
    release_private = crypto["private_class"].generate()
    device_private = crypto["private_class"].generate()
    product, profile = def_test_product_fixture()
    other_product = def_create_product_record()
    hashes = {"cpu": "a" * 64, "board": "b" * 64}
    activation = def_create_activation_request(
        device_private, def_PARAM_PRODUCT_SKU, "PRO",
        product["product_number"], product["master_key"], "pc", hashes,
    )
    license_envelope = def_issue_license([activation], profile, authority_private)
    with tempfile.TemporaryDirectory() as temp_dir:
        artifact = Path(temp_dir) / "VDF_Core.pyd"
        artifact.write_bytes(b"native-engine")
        manifest = def_build_module_manifest(
            artifact, "VDF_CORE", "2.1.0", [def_PARAM_MASTER_ENTITLEMENT],
            def_PARAM_MASTER_ENTITLEMENT, "via_vdf", "def_run", "REL-001",
            other_product["product_number"], other_product["master_key_hash"],
        )
        result = def_create_module_handshake(
            def_sign_module_manifest(manifest, release_private), release_private.public_key(), artifact,
            license_envelope, authority_private.public_key(), device_private,
            def_PARAM_PRODUCT_SKU, "2.1.0", product["product_number"], product["master_key"],
            hashes, "binding-nonce-0001",
        )
        assert not result.ok and result.status == "PRODUCT_BINDING_MISMATCH"


def def_test_route_policy() -> None:
    restricted = def_plan_execution_route("RESTRICTED", "CLOUD", "CLOUD_COMPUTE_LOCAL_DB")
    assert restricted.compute_location == "EDGE"
    public = def_plan_execution_route("PUBLIC", "AUTO", "CLOUD_COMPUTE_LOCAL_DB")
    assert public.compute_location == "CLOUD" and public.local_writer_required
    local = def_plan_execution_route("PUBLIC", "CLOUD", "LOCAL_ONLY")
    assert local.compute_location == "EDGE"


def def_test_https_allowlist() -> None:
    parsed = def_validate_https_target("https://api.example.com/v1/jobs", ["api.example.com"])
    assert parsed.hostname == "api.example.com"
    try:
        def_validate_https_target("http://api.example.com/v1/jobs", ["api.example.com"])
    except ValueError:
        pass
    else:
        raise AssertionError("HTTP must be rejected")


def def_test_payload_encryption_roundtrip() -> None:
    crypto = def_require_cryptography()
    recipient_private = crypto["x25519_private_class"].generate()
    recipient_public_b64 = def_x25519_public_raw_b64(recipient_private.public_key())
    aad = {"job_id": "JOB-1", "module_id": "VDF_CORE"}
    encrypted = def_encrypt_json_for_recipient({"ticker": "2330.TW", "rows": 12}, recipient_public_b64, aad)
    decrypted = def_decrypt_json_from_sender(encrypted, recipient_private)
    assert decrypted == {"ticker": "2330.TW", "rows": 12}
    encrypted["aad"]["job_id"] = "JOB-FORGED"
    try:
        def_decrypt_json_from_sender(encrypted, recipient_private)
    except Exception:
        pass
    else:
        raise AssertionError("Modified AAD must invalidate AES-GCM authentication")


def def_test_public_key_pinning() -> None:
    crypto = def_require_cryptography()
    serialization = crypto["serialization"]
    private_key = crypto["private_class"].generate()
    public_bytes = private_key.public_key().public_bytes(
        serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo
    )
    with tempfile.TemporaryDirectory() as temp_dir:
        public_path = Path(temp_dir) / "authority.pem"
        public_path.write_bytes(public_bytes)
        pin = def_sha256_bytes(public_bytes)
        assert def_load_trusted_public_key(public_path, "", pin) is not None
        try:
            def_load_trusted_public_key(public_path, "", "f" * 64)
        except ValueError as exc:
            assert "mismatch" in str(exc)
        else:
            raise AssertionError("Wrong public-key pin must fail")


def def_test_cloud_job_encryption_gate() -> None:
    crypto = def_require_cryptography()
    device_private = crypto["private_class"].generate()
    cloud_private = crypto["x25519_private_class"].generate()
    product = def_create_product_record()
    route = def_plan_execution_route("CONFIDENTIAL", "CLOUD", "CLOUD_COMPUTE_LOCAL_DB")
    try:
        def_build_cloud_job_request(
            device_private, "LIC-1", "VDF_CORE", "VDF_FETCH",
            product["product_number"], product["master_key"], route, {"ticker": "2330.TW"},
        )
    except ValueError as exc:
        assert "X25519" in str(exc)
    else:
        raise AssertionError("Confidential cloud jobs must require payload encryption")
    request = def_build_cloud_job_request(
        device_private, "LIC-1", "VDF_CORE", "VDF_FETCH",
        product["product_number"], product["master_key"], route,
        {"ticker": "2330.TW"}, def_x25519_public_raw_b64(cloud_private.public_key()),
    )
    signed_payload = def_verify_signed_payload(request, device_private.public_key(), expected_schema="via.cloud-job-envelope.v2")
    decrypted = def_decrypt_json_from_sender(signed_payload["encrypted_input"], cloud_private)
    assert decrypted["ticker"] == "2330.TW" and signed_payload["input_manifest"] is None
    assert signed_payload["product_number"] == product["product_number"]


def def_test_ast_and_copy_gate() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "source"
        staging = Path(temp_dir) / "staging"
        root.mkdir()
        source = root / "engine.py"
        source.write_text("def def_run():\n    return 42\n", encoding="utf-8")
        analysis = def_analyze_python_source(source, root)
        assert analysis.ast_ok and analysis.artifact_kind == "PYD"
        copy_result = def_copy_source_with_hash_gate(source, root, staging)
        assert copy_result["source_original_sha256"] == copy_result["source_after_sha256"]


def def_test_guard_injection_and_package_plan() -> None:
    product = def_create_product_record()
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_root = Path(temp_dir)
        root = temp_root / "source"
        staging = temp_root / "staging"
        output = temp_root / "output"
        root.mkdir()
        source = root / "03-VDF_Engine.py"
        source.write_text(
            '"""engine"""\nfrom __future__ import annotations\n\ndef def_run():\n    return 42\n',
            encoding="utf-8",
        )
        source_hash = def_sha256_file(source)
        result = def_package_plan(
            root, staging, output, product,
            execute_build=False,
            audit_path=temp_root / "audit.jsonl",
        )
        assert result["summary"]["plan_ready"] and not result["summary"]["release_eligible"]
        row = result["rows"][0]
        guarded_text = Path(row["copy_gate"]["copy"]).read_text(encoding="utf-8")
        assert row["guard"]["status"] == "GUARD_INJECTED"
        assert guarded_text.count(def_PARAM_GUARD_MARKER) == 1
        assert product["product_number"] in guarded_text
        assert product["master_key"] not in guarded_text
        assert def_sha256_file(source) == source_hash == row["copy_gate"]["source_after_sha256"]
        compile(guarded_text, str(source), "exec")


def def_test_standalone_module_fails_closed() -> None:
    product = def_create_product_record()
    required_names = [
        def_PARAM_RUNTIME_TOKEN_ENV,
        def_PARAM_LICENSE_FILE_ENV,
        def_PARAM_MODULE_MANIFEST_ENV,
        def_PARAM_AUTHORITY_PUBLIC_KEY_ENV,
        def_PARAM_RELEASE_PUBLIC_KEY_ENV,
        def_PARAM_DEVICE_KEY_ENV,
        def_PARAM_PRODUCT_KEY_STATE_ENV,
    ]
    saved_values = {name: os.environ.get(name) for name in required_names}
    try:
        for name in required_names:
            os.environ.pop(name, None)
        try:
            def_enforce_module_guard_from_environment(
                "VDF_CORE",
                def_PARAM_MASTER_ENTITLEMENT,
                product["product_number"],
                Path(__file__),
            )
        except RuntimeError as exc:
            assert def_PARAM_RUNTIME_TOKEN_ENV in str(exc)
        else:
            raise AssertionError("A copied module without runtime authorization must fail closed")
    finally:
        for name, value in saved_values.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def def_test_secret_detection() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir)
        source = root / "bad.py"
        source.write_text("password" + " = 'test-secret-value'\n", encoding="utf-8")
        analysis = def_analyze_python_source(source, root)
        assert any(item["code"] == "HARDCODED_SECRET" for item in analysis.risks)


def def_test_local_sqlite_ingest() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "databases"
        database = root / "via_test.sqlite"
        audit_path = Path(temp_dir) / "audit.jsonl"
        schema = {"ticker": "TEXT", "trade_date": "TEXT", "close": "REAL", "meta": "JSON"}
        first = def_ingest_local_rows(
            database, root, "daily_prices",
            [{"ticker": "2330.TW", "trade_date": "2026-09-18", "close": 1260.0, "meta": {"source": "test"}}],
            schema, ["ticker", "trade_date"], "SQLITE", "APPEND", audit_path,
        )
        assert first["ok"] and first["rows"] == 1
        second = def_ingest_local_rows(
            database, root, "daily_prices",
            [{"ticker": "2330.TW", "trade_date": "2026-09-18", "close": 1270.0, "meta": {"source": "updated"}}],
            schema, ["ticker", "trade_date"], "SQLITE", "UPSERT", audit_path,
        )
        assert second["ok"] and def_verify_audit_chain(audit_path).ok
        connection = sqlite3.connect(str(database))
        try:
            row = connection.execute('SELECT close, meta FROM "daily_prices" WHERE ticker=?', ("2330.TW",)).fetchone()
        finally:
            connection.close()
        assert row[0] == 1270.0 and "updated" in row[1]


def def_test_local_ingest_injection_rejected() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "databases"
        try:
            def_ingest_local_rows(
                root / "via_test.sqlite", root, "prices; DROP TABLE x",
                [{"ticker": "2330.TW"}], {"ticker": "TEXT"}, [],
                "SQLITE", "APPEND", Path(temp_dir) / "audit.jsonl",
            )
        except ValueError as exc:
            assert "table" in str(exc).lower()
        else:
            raise AssertionError("Unsafe table names must be rejected")


def def_test_clock_rollback() -> None:
    crypto = def_require_cryptography()
    device_private = crypto["private_class"].generate()
    with tempfile.TemporaryDirectory() as temp_dir:
        state_path = Path(temp_dir) / "clock.json"
        now_value = datetime(2026, 1, 2, tzinfo=timezone.utc)
        def_write_clock_state(state_path, device_private, "LIC-1", 0, now_value)
        sequence = def_validate_clock_state(state_path, device_private.public_key(), "LIC-1", now_value)
        assert sequence == 1
        try:
            def_validate_clock_state(state_path, device_private.public_key(), "LIC-1", datetime(2025, 1, 1, tzinfo=timezone.utc))
        except ValueError as exc:
            assert "rollback" in str(exc).lower()
        else:
            raise AssertionError("Clock rollback must be rejected")


def def_test_strict_json_and_profile_types() -> None:
    global def_PARAM_BUILD_MODE
    with tempfile.TemporaryDirectory() as temp_dir:
        duplicate_path = Path(temp_dir) / "duplicate.json"
        duplicate_path.write_text('{"enabled":true,"enabled":false}', encoding="utf-8")
        try:
            def_read_json(duplicate_path)
        except ValueError as exc:
            assert "duplicate" in str(exc).lower()
        else:
            raise AssertionError("Duplicate JSON keys must be rejected")
    product, profile = def_test_product_fixture()
    assert product["product_number"] == profile["product_number"]
    invalid_profile = json.loads(json.dumps(profile))
    invalid_profile["mobile_policy"]["allowed"] = "false"
    try:
        def_validate_profile(invalid_profile)
    except ValueError as exc:
        assert "boolean" in str(exc).lower()
    else:
        raise AssertionError("String false must not be coerced to true")
    original_mode = def_PARAM_BUILD_MODE
    try:
        def_PARAM_BUILD_MODE = "PRODUCTION"
        try:
            def_validate_insecure_test_store_flag(True)
        except RuntimeError as exc:
            assert "disabled" in str(exc).lower()
        else:
            raise AssertionError("Production mode must permanently reject insecure test key storage")
    finally:
        def_PARAM_BUILD_MODE = original_mode


def def_test_module_compatibility_gate() -> None:
    product = def_create_product_record()
    with tempfile.TemporaryDirectory() as temp_dir:
        artifact = Path(temp_dir) / "VDF_Core.pyd"
        artifact.write_bytes(b"native-engine")
        manifest = def_build_module_manifest(
            artifact, "VDF_CORE", "2.2.0", ["VDF_FETCH"], "VDF_FETCH",
            "via_vdf", "def_run", "REL-002", product["product_number"], product["master_key_hash"],
        )
        assert def_validate_module_compatibility(manifest).ok
        manifest["compatibility"]["platforms"] = ["definitely-not-this-platform"]
        result = def_validate_module_compatibility(manifest)
        assert not result.ok and "platform" in " ".join(result.errors).lower()


def def_test_signed_package_tree_exactness() -> None:
    crypto = def_require_cryptography()
    release_private = crypto["private_class"].generate()
    product = def_create_product_record()
    with tempfile.TemporaryDirectory() as temp_dir:
        package_root = Path(temp_dir) / "package"
        package_root.mkdir()
        (package_root / "engine.pyd").write_bytes(b"engine")
        (package_root / "config.json").write_text("{}", encoding="utf-8")
        manifest = def_build_package_tree_manifest(package_root, product["product_number"], "REL-002")
        envelope = def_sign_package_tree_manifest(manifest, release_private)
        assert def_verify_package_tree_manifest(envelope, release_private.public_key(), package_root, product["product_number"]).ok
        (package_root / "unlisted.dll").write_bytes(b"unlisted")
        result = def_verify_package_tree_manifest(envelope, release_private.public_key(), package_root, product["product_number"])
        assert not result.ok and "extra" in " ".join(result.errors).lower()


def def_test_bounded_subprocess_controls() -> None:
    output_result = def_run_subprocess_bounded(
        [sys.executable, "-c", "import sys; sys.stdout.write('x' * 4096); sys.stdout.flush()"],
        timeout_seconds=5,
        max_output_bytes=128,
    )
    assert not output_result["ok"] and output_result["output_limited"]
    timeout_result = def_run_subprocess_bounded(
        [sys.executable, "-c", "import time; time.sleep(2)"],
        timeout_seconds=1,
        max_output_bytes=1024,
    )
    assert not timeout_result["ok"] and timeout_result["timed_out"]


def def_test_unsafe_database_location_rejected() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "OneDrive" / "databases"
        database = root / "active.sqlite"
        try:
            def_validate_active_database_location(database, root)
        except ValueError as exc:
            assert "sync-folder" in str(exc).lower()
        else:
            raise AssertionError("Active database in a sync folder must be rejected")


def def_test_local_ingest_idempotency() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        root = Path(temp_dir) / "databases"
        database = root / "via_test.sqlite"
        audit_path = Path(temp_dir) / "audit.jsonl"
        request_id = "REQ-20260929-0001"
        arguments = (
            database, root, "daily_prices",
            [{"ticker": "2330.TW", "trade_date": "2026-09-29", "close": 1300.0}],
            {"ticker": "TEXT", "trade_date": "TEXT", "close": "REAL"},
            ["ticker", "trade_date"], "SQLITE", "APPEND", audit_path, request_id,
        )
        first = def_ingest_local_rows(*arguments)
        second = def_ingest_local_rows(*arguments)
        assert first["status"] == "LOCAL_INGEST_COMMITTED"
        assert second["status"] == "LOCAL_INGEST_REPLAYED" and second["replayed"]
        connection = sqlite3.connect(str(database))
        try:
            count = connection.execute('SELECT COUNT(*) FROM "daily_prices"').fetchone()[0]
        finally:
            connection.close()
        assert count == 1


def def_test_cloud_job_idempotency_key() -> None:
    crypto = def_require_cryptography()
    device_private = crypto["private_class"].generate()
    product = def_create_product_record()
    route = def_plan_execution_route("PUBLIC", "CLOUD", "CLOUD_COMPUTE_LOCAL_DB")
    envelope = def_build_cloud_job_request(
        device_private, "LIC-1", "VDF_CORE", "VDF_FETCH",
        product["product_number"], product["master_key"], route,
        {"ticker": "2330.TW"}, request_id="REQ-20260929-CLOUD-0001",
    )
    payload = def_verify_signed_payload(envelope, device_private.public_key(), expected_schema="via.cloud-job-envelope.v2")
    assert payload["idempotency_key"] == "REQ-20260929-CLOUD-0001"
    assert def_PARAM_SHA256_RE.fullmatch(payload["input_sha256"])


def def_test_top25_catalog_and_development_evaluation() -> None:
    assert len(def_PARAM_TOP25_RISK_CONTROLS) == 25
    assert len({item["id"] for item in def_PARAM_TOP25_RISK_CONTROLS}) == 25
    assert all(item["solution"] and item["title"] for item in def_PARAM_TOP25_RISK_CONTROLS)
    result = def_evaluate_top25_controls(Path(__file__).resolve().parent, "DEVELOPMENT", "DEVELOPER")
    assert result["quantity_validation"]["actual_controls"] == 25
    assert result["quantity_validation"]["unique_controls"] == 25
    assert result["counts"]["RED"] == 0


def def_test_top25_production_fail_closed() -> None:
    result = def_evaluate_top25_controls(Path(__file__).resolve().parent, "PRODUCTION", "CLIENT")
    assert result["overall"] == "RED"
    assert not result["release_eligible"]
    risk_two = next(item for item in result["rows"] if item["risk_id"] == "RISK-002")
    assert risk_two["status"] == "RED"


def def_test_top25_signed_evidence_roundtrip() -> None:
    crypto = def_require_cryptography()
    release_private = crypto["private_class"].generate()
    payload = def_top25_evidence_template("PRODUCTION", "CLIENT")
    payload["release_id"] = "REL-002"
    payload["evidence"] = {key: True for key in def_top25_external_keys()}
    envelope = def_sign_top25_evidence(payload, release_private)
    with tempfile.TemporaryDirectory() as temp_dir:
        evidence_path = Path(temp_dir) / "evidence.json"
        def_write_json(evidence_path, envelope)
        loaded, verified = def_load_top25_evidence_document(
            evidence_path, "PRODUCTION", "CLIENT", release_private.public_key(),
        )
        assert verified and loaded["release_id"] == "REL-002"


def def_run_self_tests(rounds: int = 3, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    if rounds < 1 or rounds > 3:
        raise ValueError("Self-test rounds must be between 1 and 3")
    tests = [
        def_test_semver,
        def_test_product_number_and_master_key,
        def_test_product_key_state_roundtrip,
        def_test_audit_chain,
        def_test_activation_license_roundtrip,
        def_test_license_tamper_rejected,
        def_test_wrong_product_rejected,
        def_test_wrong_product_number_and_master_key_rejected,
        def_test_expired_license_rejected,
        def_test_entitlement_rejected,
        def_test_device_quorum,
        def_test_wrong_device_rejected,
        def_test_not_before_and_version_rejected,
        def_test_mobile_limit,
        def_test_module_manifest,
        def_test_module_handshake_roundtrip,
        def_test_runtime_token_one_use_and_process_binding,
        def_test_manifest_product_binding_mismatch_rejected,
        def_test_route_policy,
        def_test_https_allowlist,
        def_test_payload_encryption_roundtrip,
        def_test_public_key_pinning,
        def_test_cloud_job_encryption_gate,
        def_test_ast_and_copy_gate,
        def_test_guard_injection_and_package_plan,
        def_test_standalone_module_fails_closed,
        def_test_secret_detection,
        def_test_local_sqlite_ingest,
        def_test_local_ingest_injection_rejected,
        def_test_clock_rollback,
        def_test_strict_json_and_profile_types,
        def_test_module_compatibility_gate,
        def_test_signed_package_tree_exactness,
        def_test_bounded_subprocess_controls,
        def_test_unsafe_database_location_rejected,
        def_test_local_ingest_idempotency,
        def_test_cloud_job_idempotency_key,
        def_test_top25_catalog_and_development_evaluation,
        def_test_top25_production_fail_closed,
        def_test_top25_signed_evidence_roundtrip,
    ]
    round_results: List[Dict[str, Any]] = []
    for round_number in range(1, rounds + 1):
        passed: List[str] = []
        failed: List[Dict[str, str]] = []
        started = time.perf_counter()
        for test_function in tests:
            try:
                test_function()
                passed.append(test_function.__name__)
            except Exception as exc:
                failed.append({"test": test_function.__name__, "error": str(exc), "traceback": traceback.format_exc()})
        round_results.append({
            "round": round_number,
            "name": def_round_classification(round_number)["name"],
            "ok": not failed,
            "passed": passed,
            "failed": failed,
            "total": len(tests),
            "elapsed_ms": round((time.perf_counter() - started) * 1000, 2),
        })
    payload = {
        "schema": "via.selftest.v2",
        "engine": def_PARAM_ENGINE_NAME,
        "version": def_PARAM_ENGINE_VERSION,
        "generated_at": def_now_utc_iso(),
        "ok": all(item["ok"] for item in round_results),
        "rounds": round_results,
        "quantity_validation": {
            "rounds": rounds,
            "tests_per_round": len(tests),
            "total_executions": rounds * len(tests),
            "passes": sum(len(item["passed"]) for item in round_results),
            "failures": sum(len(item["failed"]) for item in round_results),
        },
    }
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        def_write_json(output_dir / "VIA_Hybrid_SelfTest.json", payload, overwrite=True)
    return payload


# =============================================================================
# def CLI COMMANDS
# =============================================================================
def def_print_json(payload: Any) -> None:
    print(def_pretty_json(payload))


def def_result_payload(result: def_CommandResult) -> Dict[str, Any]:
    return asdict(result)


def def_load_hardware_hashes(signal_json_path: Optional[Path] = None) -> Dict[str, str]:
    overrides = def_read_json(signal_json_path) if signal_json_path else None
    signals = def_collect_windows_pc_signals(overrides=overrides)
    return def_hash_hardware_signals(signals)


def def_add_common_device_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--device-key", type=Path, default=def_PARAM_DEVICE_KEY_FILE)
    parser.add_argument("--device-type", choices=sorted(def_PARAM_ALLOWED_DEVICE_TYPES), default="pc")
    parser.add_argument("--signal-json", type=Path, help="Test/lab-only raw signal JSON; never include it in a license")
    parser.add_argument("--allow-insecure-test-key-store", action="store_true")


def def_build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=def_PARAM_ENGINE_NAME)
    subparsers = parser.add_subparsers(dest="command", required=True)

    version_parser = subparsers.add_parser("version", help="Print version and architecture snapshot")
    version_parser.add_argument("--base-root", type=Path, default=Path.cwd())

    audit_parser = subparsers.add_parser("audit", help="Run one to three panoramic read-only rounds")
    audit_parser.add_argument("--base-root", type=Path, required=True)
    audit_parser.add_argument("--output-dir", type=Path, default=def_PARAM_REPORT_DIR)
    audit_parser.add_argument("--rounds", type=int, default=3)

    resilience_parser = subparsers.add_parser("resilience-audit", help="Evaluate all 25 failure controls and render JSON/HTML matrices")
    resilience_parser.add_argument("--base-root", type=Path, required=True)
    resilience_parser.add_argument("--output-dir", type=Path, default=def_PARAM_REPORT_DIR)
    resilience_parser.add_argument("--deployment-mode", choices=sorted(def_PARAM_ALLOWED_DEPLOYMENT_MODES), default="DEVELOPMENT")
    resilience_parser.add_argument("--release-role", choices=sorted(def_PARAM_ALLOWED_RELEASE_ROLES), default="DEVELOPER")
    resilience_parser.add_argument("--evidence", type=Path, help="Plain evidence is advisory; PRODUCTION green requires a signed evidence envelope")
    resilience_parser.add_argument("--release-public-key", type=Path)
    resilience_parser.add_argument("--dev-release-public-key-sha256", default="")
    resilience_parser.add_argument("--evidence-key-id", default=def_PARAM_RELEASE_KEY_ID)
    resilience_parser.add_argument("--safe-repair", action="store_true", help="Only create missing run-local report/audit/runtime/staging directories")

    sign_evidence_parser = subparsers.add_parser("sign-risk-evidence", help="OFFLINE RELEASE AUTHORITY ONLY: sign reviewed Top-25 evidence")
    sign_evidence_parser.add_argument("--evidence", type=Path, required=True)
    sign_evidence_parser.add_argument("--release-private-key", type=Path, required=True)
    sign_evidence_parser.add_argument("--password-env", default=def_PARAM_PRIVATE_KEY_PASSWORD_ENV)
    sign_evidence_parser.add_argument("--key-id", default=def_PARAM_RELEASE_KEY_ID)
    sign_evidence_parser.add_argument("--output", type=Path, required=True)

    package_parser = subparsers.add_parser("package-plan", help="Copy-first PY to PYD/EXE plan; optional Nuitka execution")
    package_parser.add_argument("--source-root", type=Path, required=True)
    package_parser.add_argument("--staging-root", type=Path, default=def_PARAM_STAGING_DIR)
    package_parser.add_argument("--output-root", type=Path, default=def_PARAM_OUTPUT_DIR / "build")
    package_parser.add_argument("--product-record", type=Path, required=True, help="Authority-side product record or public binding JSON")
    package_parser.add_argument("--execute-build", action="store_true")

    tree_sign_parser = subparsers.add_parser("package-tree-sign", help="OFFLINE RELEASE AUTHORITY ONLY: sign the exact package file tree")
    tree_sign_parser.add_argument("--package-root", type=Path, required=True)
    tree_sign_parser.add_argument("--product-record", type=Path, required=True)
    tree_sign_parser.add_argument("--release-id", required=True)
    tree_sign_parser.add_argument("--release-private-key", type=Path, required=True)
    tree_sign_parser.add_argument("--password-env", default=def_PARAM_PRIVATE_KEY_PASSWORD_ENV)
    tree_sign_parser.add_argument("--key-id", default=def_PARAM_RELEASE_KEY_ID)
    tree_sign_parser.add_argument("--output", type=Path, required=True)

    tree_verify_parser = subparsers.add_parser("package-tree-verify", help="Verify exact package files, hashes, signature, and Product Number")
    tree_verify_parser.add_argument("--package-root", type=Path, required=True)
    tree_verify_parser.add_argument("--manifest", type=Path, required=True)
    tree_verify_parser.add_argument("--product-number", required=True)
    tree_verify_parser.add_argument("--release-public-key", type=Path, required=True)
    tree_verify_parser.add_argument("--dev-release-public-key-sha256", default="")
    tree_verify_parser.add_argument("--key-id", default=def_PARAM_RELEASE_KEY_ID)

    keygen_parser = subparsers.add_parser("keygen", help="Generate a password-protected Ed25519 authority/release keypair")
    keygen_parser.add_argument("--private-key", type=Path, required=True)
    keygen_parser.add_argument("--public-key", type=Path, required=True)
    keygen_parser.add_argument("--password-env", default=def_PARAM_PRIVATE_KEY_PASSWORD_ENV)
    keygen_parser.add_argument("--overwrite", action="store_true")

    transport_keygen_parser = subparsers.add_parser("transport-keygen", help="Generate a password-protected X25519 cloud transport keypair")
    transport_keygen_parser.add_argument("--private-key", type=Path, required=True)
    transport_keygen_parser.add_argument("--public-key", type=Path, required=True)
    transport_keygen_parser.add_argument("--password-env", default=def_PARAM_PRIVATE_KEY_PASSWORD_ENV)
    transport_keygen_parser.add_argument("--overwrite", action="store_true")

    product_parser = subparsers.add_parser("product-init", help="OFFLINE AUTHORITY ONLY: generate one Product Number and one Master KEY")
    product_parser.add_argument("--product-sku", default=def_PARAM_PRODUCT_SKU)
    product_parser.add_argument("--edition", default=def_PARAM_DEFAULT_EDITION)
    product_parser.add_argument("--output", type=Path, required=True)
    product_parser.add_argument("--public-output", type=Path, help="Optional redacted binding JSON for build/signing hosts")
    product_parser.add_argument("--overwrite", action="store_true")

    bind_parser = subparsers.add_parser("bind-product", help="Protect the Master KEY in this Windows user profile")
    bind_parser.add_argument("--product-number", required=True)
    bind_parser.add_argument("--product-key-state", type=Path, default=def_PARAM_PRODUCT_KEY_STATE_FILE)
    bind_parser.add_argument("--master-key-env", default=def_PARAM_MASTER_KEY_ENV)
    bind_parser.add_argument("--allow-insecure-test-key-store", action="store_true")
    bind_parser.add_argument("--overwrite", action="store_true")

    profile_parser = subparsers.add_parser("sample-profile", help="Write a Product Number-bound 1 PC + 1 mobile entitlement profile")
    profile_parser.add_argument("--product-record", type=Path, required=True)
    profile_parser.add_argument("--output", type=Path, required=True)

    activation_parser = subparsers.add_parser("activation-request", help="Create a device-signed activation request")
    def_add_common_device_arguments(activation_parser)
    activation_parser.add_argument("--product-sku", default=def_PARAM_PRODUCT_SKU)
    activation_parser.add_argument("--edition", default=def_PARAM_DEFAULT_EDITION)
    activation_parser.add_argument("--product-key-state", type=Path, default=def_PARAM_PRODUCT_KEY_STATE_FILE)
    activation_parser.add_argument("--output", type=Path, required=True)

    issue_parser = subparsers.add_parser("issue-license", help="OFFLINE AUTHORITY ONLY: issue a signed license")
    issue_parser.add_argument("--activation-request", type=Path, action="append", required=True)
    issue_parser.add_argument("--profile", type=Path, required=True)
    issue_parser.add_argument("--authority-private-key", type=Path, required=True)
    issue_parser.add_argument("--password-env", default=def_PARAM_PRIVATE_KEY_PASSWORD_ENV)
    issue_parser.add_argument("--key-id", default=def_PARAM_LICENSE_KEY_ID)
    issue_parser.add_argument("--customer-ref", default="")
    issue_parser.add_argument("--output", type=Path, required=True)

    verify_parser = subparsers.add_parser("verify-license", help="Verify license, version, entitlement, device, and clock")
    def_add_common_device_arguments(verify_parser)
    verify_parser.add_argument("--license", type=Path, required=True)
    verify_parser.add_argument("--authority-public-key", type=Path, required=True)
    verify_parser.add_argument("--dev-authority-public-key-sha256", default="", help="Development mode only; production uses the pinned parameter")
    verify_parser.add_argument("--product-sku", default=def_PARAM_PRODUCT_SKU)
    verify_parser.add_argument("--product-version", default=def_PARAM_ENGINE_VERSION)
    verify_parser.add_argument("--product-key-state", type=Path, default=def_PARAM_PRODUCT_KEY_STATE_FILE)
    verify_parser.add_argument("--entitlement", default="")
    verify_parser.add_argument("--key-id", default=def_PARAM_LICENSE_KEY_ID)
    verify_parser.add_argument("--clock-state", type=Path, default=def_PARAM_CLOCK_STATE_FILE)
    verify_parser.add_argument("--verify-only", action="store_true")

    manifest_parser = subparsers.add_parser("sign-module", help="Create and sign a compiled engine manifest")
    manifest_parser.add_argument("--artifact", type=Path, required=True)
    manifest_parser.add_argument("--module-id", required=True)
    manifest_parser.add_argument("--version", required=True)
    manifest_parser.add_argument("--capability", action="append", required=True)
    manifest_parser.add_argument("--entitlement", default=def_PARAM_MASTER_ENTITLEMENT, help="Guarded builds use VIA_ALL_ENGINES")
    manifest_parser.add_argument("--env-alias", required=True)
    manifest_parser.add_argument("--entry-callable", required=True)
    manifest_parser.add_argument("--release-id", required=True)
    manifest_parser.add_argument("--product-record", type=Path, required=True, help="Authority-side product record or public binding JSON")
    manifest_parser.add_argument("--release-private-key", type=Path, required=True)
    manifest_parser.add_argument("--password-env", default=def_PARAM_PRIVATE_KEY_PASSWORD_ENV)
    manifest_parser.add_argument("--key-id", default=def_PARAM_RELEASE_KEY_ID)
    manifest_parser.add_argument("--output", type=Path, required=True)

    module_verify_parser = subparsers.add_parser("verify-module", help="Verify compiled engine signature and hash")
    module_verify_parser.add_argument("--manifest", type=Path, required=True)
    module_verify_parser.add_argument("--artifact", type=Path, required=True)
    module_verify_parser.add_argument("--release-public-key", type=Path, required=True)
    module_verify_parser.add_argument("--dev-release-public-key-sha256", default="", help="Development mode only; production uses the pinned parameter")
    module_verify_parser.add_argument("--key-id", default=def_PARAM_RELEASE_KEY_ID)

    handshake_parser = subparsers.add_parser("handshake", help="Verify module + license and emit a short-lived device-signed token")
    handshake_parser.add_argument("--manifest", type=Path, required=True)
    handshake_parser.add_argument("--artifact", type=Path, required=True)
    handshake_parser.add_argument("--release-public-key", type=Path, required=True)
    handshake_parser.add_argument("--dev-release-public-key-sha256", default="")
    handshake_parser.add_argument("--license", type=Path, required=True)
    handshake_parser.add_argument("--authority-public-key", type=Path, required=True)
    handshake_parser.add_argument("--dev-authority-public-key-sha256", default="")
    handshake_parser.add_argument("--device-key", type=Path, default=def_PARAM_DEVICE_KEY_FILE)
    handshake_parser.add_argument("--signal-json", type=Path)
    handshake_parser.add_argument("--allow-insecure-test-key-store", action="store_true")
    handshake_parser.add_argument("--product-sku", default=def_PARAM_PRODUCT_SKU)
    handshake_parser.add_argument("--product-version", default=def_PARAM_ENGINE_VERSION)
    handshake_parser.add_argument("--product-key-state", type=Path, default=def_PARAM_PRODUCT_KEY_STATE_FILE)
    handshake_parser.add_argument("--nonce", required=True)
    handshake_parser.add_argument("--clock-state", type=Path, default=def_PARAM_CLOCK_STATE_FILE)
    handshake_parser.add_argument("--execution-mode", choices=["IN_PROCESS", "CHILD_PROCESS"], default="IN_PROCESS")
    handshake_parser.add_argument("--target-pid", type=int)
    handshake_parser.add_argument("--output", type=Path, help="Write the short-lived Runtime Token for a guarded module")

    launch_parser = subparsers.add_parser("launch-guarded", help="Authorize and launch a guarded EXE as a bound child process")
    launch_parser.add_argument("--manifest", type=Path, required=True)
    launch_parser.add_argument("--artifact", type=Path, required=True)
    launch_parser.add_argument("--release-public-key", type=Path, required=True)
    launch_parser.add_argument("--dev-release-public-key-sha256", default="")
    launch_parser.add_argument("--license", type=Path, required=True)
    launch_parser.add_argument("--authority-public-key", type=Path, required=True)
    launch_parser.add_argument("--dev-authority-public-key-sha256", default="")
    launch_parser.add_argument("--device-key", type=Path, default=def_PARAM_DEVICE_KEY_FILE)
    launch_parser.add_argument("--product-key-state", type=Path, default=def_PARAM_PRODUCT_KEY_STATE_FILE)
    launch_parser.add_argument("--signal-json", type=Path)
    launch_parser.add_argument("--allow-insecure-test-key-store", action="store_true")
    launch_parser.add_argument("--product-sku", default=def_PARAM_PRODUCT_SKU)
    launch_parser.add_argument("--product-version", default=def_PARAM_ENGINE_VERSION)
    launch_parser.add_argument("--nonce", required=True)
    launch_parser.add_argument("--clock-state", type=Path, default=def_PARAM_CLOCK_STATE_FILE)
    launch_parser.add_argument("--replay-ledger", type=Path, default=def_PARAM_RUNTIME_REPLAY_LEDGER)
    launch_parser.add_argument("--artifact-arg", action="append", default=[])
    launch_parser.add_argument("--timeout", type=int, default=0)

    runtime_parser = subparsers.add_parser("verify-runtime-token", help="Consume and verify a one-use module Runtime Token")
    runtime_parser.add_argument("--token", type=Path, required=True)
    runtime_parser.add_argument("--manifest", type=Path, required=True)
    runtime_parser.add_argument("--artifact", type=Path, required=True)
    runtime_parser.add_argument("--release-public-key", type=Path, required=True)
    runtime_parser.add_argument("--dev-release-public-key-sha256", default="")
    runtime_parser.add_argument("--device-key", type=Path, default=def_PARAM_DEVICE_KEY_FILE)
    runtime_parser.add_argument("--product-key-state", type=Path, default=def_PARAM_PRODUCT_KEY_STATE_FILE)
    runtime_parser.add_argument("--entitlement", default=def_PARAM_MASTER_ENTITLEMENT)
    runtime_parser.add_argument("--replay-ledger", type=Path, default=def_PARAM_RUNTIME_REPLAY_LEDGER)
    runtime_parser.add_argument("--allow-insecure-test-key-store", action="store_true")
    runtime_parser.add_argument("--no-consume", action="store_true")
    runtime_parser.add_argument("--current-pid", type=int)
    runtime_parser.add_argument("--parent-pid", type=int)

    route_parser = subparsers.add_parser("route", help="Resolve privacy-safe local/cloud execution route")
    route_parser.add_argument("--data-class", choices=sorted(def_PARAM_ALLOWED_DATA_CLASSES), required=True)
    route_parser.add_argument("--compute", choices=sorted(def_PARAM_ALLOWED_COMPUTE_MODES), default="AUTO")
    route_parser.add_argument("--database-mode", choices=sorted(def_PARAM_ALLOWED_DB_MODES), default="LOCAL_ONLY")
    route_parser.add_argument("--approve-restricted-cloud", action="store_true")

    cloud_job_parser = subparsers.add_parser("cloud-job", help="Create an outbound device-signed cloud job request")
    cloud_job_parser.add_argument("--device-key", type=Path, default=def_PARAM_DEVICE_KEY_FILE)
    cloud_job_parser.add_argument("--product-key-state", type=Path, default=def_PARAM_PRODUCT_KEY_STATE_FILE)
    cloud_job_parser.add_argument("--allow-insecure-test-key-store", action="store_true")
    cloud_job_parser.add_argument("--license-id", required=True)
    cloud_job_parser.add_argument("--module-id", required=True)
    cloud_job_parser.add_argument("--capability", required=True)
    cloud_job_parser.add_argument("--data-class", choices=sorted(def_PARAM_ALLOWED_DATA_CLASSES), required=True)
    cloud_job_parser.add_argument("--compute", choices=sorted(def_PARAM_ALLOWED_COMPUTE_MODES), default="AUTO")
    cloud_job_parser.add_argument("--database-mode", choices=sorted(def_PARAM_ALLOWED_DB_MODES), default="CLOUD_COMPUTE_LOCAL_DB")
    cloud_job_parser.add_argument("--approve-restricted-cloud", action="store_true")
    cloud_job_parser.add_argument("--input-manifest", type=Path, required=True)
    cloud_job_parser.add_argument("--request-id", default="", help="16-128 symbol idempotency key; generated when omitted")
    cloud_job_parser.add_argument("--cloud-transport-public-key", type=Path)
    cloud_job_parser.add_argument("--dev-cloud-transport-public-key-sha256", default="")
    cloud_job_parser.add_argument("--output", type=Path, required=True)

    ingest_parser = subparsers.add_parser("ingest-local", help="Transactionally write validated rows through the PC-local agent")
    ingest_parser.add_argument("--database", type=Path, required=True)
    ingest_parser.add_argument("--database-root", type=Path, required=True)
    ingest_parser.add_argument("--backend", choices=sorted(def_PARAM_ALLOWED_DB_BACKENDS), default="SQLITE")
    ingest_parser.add_argument("--table", required=True)
    ingest_parser.add_argument("--payload", type=Path, required=True, help="JSON object with schema and rows; SQL is never accepted")
    ingest_parser.add_argument("--primary-key", action="append", default=[])
    ingest_parser.add_argument("--mode", choices=sorted(def_PARAM_ALLOWED_INGEST_MODES), default="APPEND")
    ingest_parser.add_argument("--request-id", default="", help="16-128 symbol transaction idempotency key")

    audit_chain_parser = subparsers.add_parser("verify-audit", help="Verify append-only audit hash chain")
    audit_chain_parser.add_argument("--audit-file", type=Path, default=def_PARAM_AUDIT_JSONL)

    selftest_parser = subparsers.add_parser("selftest", help="Run three rounds of positive and negative tests")
    selftest_parser.add_argument("--rounds", type=int, default=3)
    selftest_parser.add_argument("--output-dir", type=Path, default=def_PARAM_REPORT_DIR)
    return parser


def def_dispatch(args: argparse.Namespace) -> Tuple[int, Dict[str, Any]]:
    if args.command == "version":
        context = def_build_runtime_context(args.base_root.resolve(), def_PARAM_OUTPUT_DIR)
        return 0, asdict(context)

    if args.command == "audit":
        result = def_run_panorama(args.base_root, args.output_dir, rounds=args.rounds)
        return (0 if result["final_status"] != "RED" else 2), result

    if args.command == "resilience-audit":
        release_public_key = None
        if args.release_public_key:
            release_public_key = def_load_trusted_public_key(
                args.release_public_key,
                def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256,
                args.dev_release_public_key_sha256,
            )
        evidence_payload, evidence_verified = def_load_top25_evidence_document(
            args.evidence,
            args.deployment_mode,
            args.release_role,
            release_public_key,
            args.evidence_key_id,
        )
        result = def_run_top25_resilience_audit(
            args.base_root,
            args.output_dir,
            args.deployment_mode,
            args.release_role,
            evidence_payload=evidence_payload,
            evidence_verified=evidence_verified,
            safe_repair=args.safe_repair,
        )
        exit_ok = result["release_eligible"] if args.deployment_mode == "PRODUCTION" else result["overall"] != "RED"
        return (0 if exit_ok else 2), result

    if args.command == "sign-risk-evidence":
        private_key = def_load_private_key(args.release_private_key, args.password_env)
        evidence = def_read_json(args.evidence)
        envelope = def_sign_top25_evidence(evidence, private_key, args.key_id)
        def_write_json(args.output, envelope, overwrite=False)
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "TOP25_EVIDENCE_SIGNED", {
            "release_id": envelope["payload"]["release_id"],
            "deployment_mode": envelope["payload"]["deployment_mode"],
            "release_role": envelope["payload"]["release_role"],
        })
        return 0, {"ok": True, "status": "TOP25_EVIDENCE_SIGNED", "output": str(args.output)}

    if args.command == "package-plan":
        result = def_package_plan(
            args.source_root,
            args.staging_root,
            args.output_root,
            def_read_json(args.product_record),
            execute_build=args.execute_build,
        )
        return (0 if result["summary"]["release_eligible"] else 2), result

    if args.command == "package-tree-sign":
        output_path = args.output.expanduser().resolve()
        package_root = args.package_root.expanduser().resolve()
        try:
            output_path.relative_to(package_root)
        except ValueError:
            pass
        else:
            raise ValueError("Signed package tree manifest must be stored outside package_root")
        private_key = def_load_private_key(args.release_private_key, args.password_env)
        binding = def_public_product_binding(def_read_json(args.product_record))
        manifest = def_build_package_tree_manifest(package_root, binding["product_number"], args.release_id)
        envelope = def_sign_package_tree_manifest(manifest, private_key, args.key_id)
        def_write_json(output_path, envelope, overwrite=False)
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "PACKAGE_TREE_SIGNED", {
            "release_id": args.release_id,
            "tree_sha256": manifest["tree_sha256"],
            "file_count": manifest["file_count"],
        })
        return 0, {"ok": True, "status": "PACKAGE_TREE_SIGNED", "output": str(output_path), "tree_sha256": manifest["tree_sha256"]}

    if args.command == "package-tree-verify":
        release_public_key = def_load_trusted_public_key(
            args.release_public_key,
            def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256,
            args.dev_release_public_key_sha256,
        )
        result = def_verify_package_tree_manifest(
            def_read_json(args.manifest),
            release_public_key,
            args.package_root,
            args.product_number,
            args.key_id,
        )
        return (0 if result.ok else 4), def_result_payload(result)

    if args.command == "keygen":
        result = def_generate_ed25519_keypair(args.private_key, args.public_key, args.password_env, args.overwrite)
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "KEYPAIR_GENERATED", {"public_key_sha256": result["public_key_sha256"]})
        return 0, result

    if args.command == "transport-keygen":
        result = def_generate_x25519_keypair(args.private_key, args.public_key, args.password_env, args.overwrite)
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "TRANSPORT_KEYPAIR_GENERATED", {"public_key_sha256": result["public_key_sha256"]})
        return 0, result

    if args.command == "product-init":
        record = def_create_product_record(args.product_sku, args.edition)
        def_write_json(args.output, record, overwrite=args.overwrite)
        try:
            os.chmod(args.output, 0o600)
        except OSError:
            pass
        public_binding = def_public_product_binding(record)
        if args.public_output:
            def_write_json(args.public_output, public_binding, overwrite=args.overwrite)
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "PRODUCT_INITIALIZED", public_binding)
        return 0, {
            "ok": True,
            "output": str(args.output),
            "public_output": str(args.public_output) if args.public_output else None,
            "product_number": public_binding["product_number"],
            "master_key_id": public_binding["master_key_id"],
            "master_key_disclosed": False,
        }

    if args.command == "bind-product":
        master_key = def_master_key_from_environment(args.master_key_env)
        result = def_store_product_key_state(
            args.product_key_state,
            args.product_number,
            master_key,
            allow_insecure_test_store=args.allow_insecure_test_key_store,
            overwrite=args.overwrite,
        )
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "PRODUCT_BOUND", {
            "product_number": result["product_number"],
            "master_key_id": result["master_key_hash"][:16].upper(),
            "storage": result["storage"],
        })
        return 0, result

    if args.command == "sample-profile":
        def_write_json(args.output, def_sample_profile(def_read_json(args.product_record)), overwrite=False)
        return 0, {"ok": True, "output": str(args.output)}

    if args.command == "activation-request":
        private_key = def_get_or_create_device_key(args.device_key, args.allow_insecure_test_key_store)
        product_state = def_load_product_key_state(args.product_key_state, args.allow_insecure_test_key_store)
        hashes = def_load_hardware_hashes(args.signal_json) if args.device_type == "pc" else {}
        envelope = def_create_activation_request(
            private_key,
            args.product_sku,
            args.edition,
            product_state["product_number"],
            product_state["master_key"],
            args.device_type,
            hashes,
        )
        def_write_json(args.output, envelope, overwrite=False)
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "ACTIVATION_REQUEST_CREATED", {"device_id": envelope["payload"]["device_id"], "device_type": args.device_type})
        return 0, {"ok": True, "output": str(args.output), "device_id": envelope["payload"]["device_id"]}

    if args.command == "issue-license":
        authority_private_key = def_load_private_key(args.authority_private_key, args.password_env)
        activation_requests = [def_read_json(path_value) for path_value in args.activation_request]
        profile = def_read_json(args.profile)
        envelope = def_issue_license(activation_requests, profile, authority_private_key, args.key_id, args.customer_ref)
        def_write_json(args.output, envelope, overwrite=False)
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "LICENSE_ISSUED", {"license_id": envelope["payload"]["license_id"], "devices": len(envelope["payload"]["devices"])})
        return 0, {"ok": True, "output": str(args.output), "license_id": envelope["payload"]["license_id"]}

    if args.command == "verify-license":
        private_key = def_load_device_private_key(args.device_key, args.allow_insecure_test_key_store)
        product_state = def_load_product_key_state(args.product_key_state, args.allow_insecure_test_key_store)
        authority_public_key = def_load_trusted_public_key(
            args.authority_public_key,
            def_PARAM_TRUSTED_LICENSE_PUBLIC_KEY_SHA256,
            args.dev_authority_public_key_sha256,
        )
        hashes = def_load_hardware_hashes(args.signal_json) if args.device_type == "pc" else {}
        result = def_verify_license(
            def_read_json(args.license), authority_public_key, private_key,
            args.product_sku, args.product_version,
            product_state["product_number"], product_state["master_key"],
            required_entitlement=args.entitlement,
            current_hardware_hashes=hashes,
            device_type=args.device_type,
            expected_key_id=args.key_id,
            state_path=args.clock_state,
            update_clock_state=not args.verify_only,
        )
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "LICENSE_VERIFIED", {"ok": result.ok, "status": result.status})
        return (0 if result.ok else 3), def_result_payload(result)

    if args.command == "sign-module":
        private_key = def_load_private_key(args.release_private_key, args.password_env)
        binding = def_public_product_binding(def_read_json(args.product_record))
        manifest = def_build_module_manifest(
            args.artifact, args.module_id, args.version, args.capability, args.entitlement,
            args.env_alias, args.entry_callable, args.release_id,
            binding["product_number"], binding["master_key_hash"],
        )
        envelope = def_sign_module_manifest(manifest, private_key, args.key_id)
        def_write_json(args.output, envelope, overwrite=False)
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "MODULE_SIGNED", {"module_id": args.module_id, "artifact_sha256": manifest["artifact_sha256"]})
        return 0, {"ok": True, "output": str(args.output), "module_id": args.module_id}

    if args.command == "verify-module":
        release_public_key = def_load_trusted_public_key(
            args.release_public_key,
            def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256,
            args.dev_release_public_key_sha256,
        )
        result = def_verify_module_manifest(def_read_json(args.manifest), release_public_key, args.artifact, args.key_id)
        return (0 if result.ok else 4), def_result_payload(result)

    if args.command == "handshake":
        device_private_key = def_load_device_private_key(args.device_key, args.allow_insecure_test_key_store)
        product_state = def_load_product_key_state(args.product_key_state, args.allow_insecure_test_key_store)
        hashes = def_load_hardware_hashes(args.signal_json)
        release_public_key = def_load_trusted_public_key(
            args.release_public_key,
            def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256,
            args.dev_release_public_key_sha256,
        )
        authority_public_key = def_load_trusted_public_key(
            args.authority_public_key,
            def_PARAM_TRUSTED_LICENSE_PUBLIC_KEY_SHA256,
            args.dev_authority_public_key_sha256,
        )
        result = def_create_module_handshake(
            def_read_json(args.manifest), release_public_key, args.artifact,
            def_read_json(args.license), authority_public_key, device_private_key,
            args.product_sku, args.product_version,
            product_state["product_number"], product_state["master_key"],
            hashes, args.nonce, args.clock_state,
            execution_mode=args.execution_mode,
            target_pid=args.target_pid,
        )
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "MODULE_HANDSHAKE", {"ok": result.ok, "status": result.status, "module": result.data.get("module", "")})
        if result.ok and args.output:
            def_write_json(args.output, result.data["token"], overwrite=False)
            result.data["token"] = {"stored_at": str(args.output), "expires_in_seconds": def_PARAM_HANDSHAKE_TTL_SECONDS}
        return (0 if result.ok else 4), def_result_payload(result)

    if args.command == "launch-guarded":
        device_private_key = def_load_device_private_key(args.device_key, args.allow_insecure_test_key_store)
        product_state = def_load_product_key_state(args.product_key_state, args.allow_insecure_test_key_store)
        hashes = def_load_hardware_hashes(args.signal_json)
        release_public_key = def_load_trusted_public_key(
            args.release_public_key,
            def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256,
            args.dev_release_public_key_sha256,
        )
        authority_public_key = def_load_trusted_public_key(
            args.authority_public_key,
            def_PARAM_TRUSTED_LICENSE_PUBLIC_KEY_SHA256,
            args.dev_authority_public_key_sha256,
        )
        handshake_result = def_create_module_handshake(
            def_read_json(args.manifest), release_public_key, args.artifact,
            def_read_json(args.license), authority_public_key, device_private_key,
            args.product_sku, args.product_version,
            product_state["product_number"], product_state["master_key"],
            hashes, args.nonce, args.clock_state,
            execution_mode="CHILD_PROCESS",
        )
        if not handshake_result.ok:
            return 4, def_result_payload(handshake_result)
        launch_result = def_launch_guarded_executable(
            args.artifact,
            handshake_result.data["token"],
            args.license,
            args.manifest,
            args.authority_public_key,
            args.release_public_key,
            args.device_key,
            args.product_key_state,
            args.replay_ledger,
            artifact_arguments=args.artifact_arg,
            development_authority_pin=args.dev_authority_public_key_sha256,
            development_release_pin=args.dev_release_public_key_sha256,
            allow_insecure_test_key_store=args.allow_insecure_test_key_store,
            timeout_seconds=args.timeout,
        )
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "GUARDED_PROCESS_LAUNCHED", {
            "ok": launch_result["ok"],
            "artifact": launch_result["artifact"],
            "exit_code": launch_result["exit_code"],
            "module": handshake_result.data["module"],
        })
        return (0 if launch_result["ok"] else 7), launch_result

    if args.command == "verify-runtime-token":
        device_private_key = def_load_device_private_key(args.device_key, args.allow_insecure_test_key_store)
        product_state = def_load_product_key_state(args.product_key_state, args.allow_insecure_test_key_store)
        release_public_key = def_load_trusted_public_key(
            args.release_public_key,
            def_PARAM_TRUSTED_RELEASE_PUBLIC_KEY_SHA256,
            args.dev_release_public_key_sha256,
        )
        module_result = def_verify_module_manifest(
            def_read_json(args.manifest), release_public_key, args.artifact,
        )
        if not module_result.ok:
            return 4, def_result_payload(module_result)
        result = def_verify_runtime_token(
            def_read_json(args.token),
            device_private_key.public_key(),
            module_result.data["manifest"],
            product_state["product_number"],
            product_state["master_key"],
            args.entitlement,
            replay_ledger=args.replay_ledger,
            consume=not args.no_consume,
            current_pid=args.current_pid,
            parent_pid=args.parent_pid,
        )
        return (0 if result.ok else 4), def_result_payload(result)

    if args.command == "route":
        route = def_plan_execution_route(args.data_class, args.compute, args.database_mode, args.approve_restricted_cloud)
        return 0, asdict(route)

    if args.command == "cloud-job":
        device_private_key = def_load_device_private_key(args.device_key, args.allow_insecure_test_key_store)
        product_state = def_load_product_key_state(args.product_key_state, args.allow_insecure_test_key_store)
        route = def_plan_execution_route(args.data_class, args.compute, args.database_mode, args.approve_restricted_cloud)
        transport_public_b64 = ""
        if args.cloud_transport_public_key:
            transport_public_key = def_load_trusted_public_key(
                args.cloud_transport_public_key,
                def_PARAM_TRUSTED_CLOUD_TRANSPORT_PUBLIC_KEY_SHA256,
                args.dev_cloud_transport_public_key_sha256,
            )
            transport_public_b64 = def_x25519_public_raw_b64(transport_public_key)
        envelope = def_build_cloud_job_request(
            device_private_key, args.license_id, args.module_id, args.capability,
            product_state["product_number"], product_state["master_key"],
            route, def_read_json(args.input_manifest), transport_public_b64, args.request_id,
        )
        def_write_json(args.output, envelope, overwrite=False)
        def_append_audit_event(def_PARAM_AUDIT_JSONL, "CLOUD_JOB_CREATED", {"job_id": envelope["payload"]["job_id"], "module_id": args.module_id})
        return 0, {"ok": True, "output": str(args.output), "job_id": envelope["payload"]["job_id"], "route": asdict(route)}

    if args.command == "ingest-local":
        payload = def_read_json(args.payload)
        if not isinstance(payload, dict) or not isinstance(payload.get("schema"), dict) or not isinstance(payload.get("rows"), list):
            raise ValueError("Local ingest payload must contain schema object and rows array")
        result = def_ingest_local_rows(
            args.database,
            args.database_root,
            args.table,
            payload["rows"],
            payload["schema"],
            args.primary_key,
            args.backend,
            args.mode,
            request_id=args.request_id,
        )
        return 0, result

    if args.command == "verify-audit":
        result = def_verify_audit_chain(args.audit_file)
        return (0 if result.ok else 5), def_result_payload(result)

    if args.command == "selftest":
        result = def_run_self_tests(args.rounds, args.output_dir)
        return (0 if result["ok"] else 6), result

    return 1, {"ok": False, "status": "UNKNOWN_COMMAND"}


def def_main(argv: Optional[Sequence[str]] = None) -> int:
    parser = def_build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        exit_code, payload = def_dispatch(args)
    except Exception as exc:
        exit_code = 10
        payload = {
            "ok": False,
            "status": "FAIL_CLOSED",
            "error": str(exc),
            "error_type": type(exc).__name__,
        }
        if os.environ.get("VIA_DEBUG", "") == "1":
            payload["traceback"] = traceback.format_exc()
    def_print_json(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(def_main())
