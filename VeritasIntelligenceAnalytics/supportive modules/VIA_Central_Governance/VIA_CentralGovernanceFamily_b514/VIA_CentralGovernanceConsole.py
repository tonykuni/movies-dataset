#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA-SYS-MGR-001 : VIA Central Governance Console (Pure Python).

母系統中央總管。兩層式分級管理的頂層：中央頒布法典，地方自治執行。

本檔取代 VIA_Central_Governance_Console_v0504/v0600.ps1，並把過去散在
CGE v0400（同義字/regex/自適應）、Console v0600（全景掃描/永久編號/Gate）、
EnvManager（環境）三處的能力收斂到單一 Python 執行時內。

實作 VIA SSOT / Interface Specification v0100：
  §1 URN 編號權威      -> URNAuthority          （單一發碼官、只增不減狀態機）
  §2 同義字/Regex 契約  -> SynonymSSOT           （V/M/P 三級、AUTO/ASK/QUARANTINE）
  §3 介面契約          -> ContractGovernor      （G15 宣告 vs 原始碼，補 GAP-02）
  §4 環境契約          -> EnvironmentAudit      （補 GAP-04）
  §5 Gate 規範         -> GateMatrix

新增（來自純 Python 架構設計）：
  SubsystemManagerABC  子系統管理者統一抽象基底
  ASTInspector         Class/Function 起訖行 + 區塊雜湊（座標級微手術定位）
  TopologyGuard        DFS 三色標記循環依賴阻斷 + 九頭龍爆炸半徑
  ProbeHarness         主動搓啟動探針與舉證
  CallGraphResolver    calls 解析（補 GAP-03）

治理：只增不減。預設 dry-run，--commit 才寫台帳。不刪除任何檔案。
相依：純標準庫。偵測到 polars / pyarrow / duckdb 等加速器會登錄但不強制。

用法：
    python VIA_CentralGovernanceConsole.py --root <VIA_SYSTEM_ROOT>
    python VIA_CentralGovernanceConsole.py --root . --commit --probe
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import importlib.util
import inspect
import json
import os
import platform
import re
import sys
import time
import webbrowser
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Optional, Set, Tuple

URN_SELF = "VIA-SYS-MGR-001"
VERSION = "v0100"
SPEC_VERSION = "VIA-SSOT-SPEC-v0100"

# ---------------------------------------------------------------------------
# §0  常數與工具
# ---------------------------------------------------------------------------

NAMESPACES = ("SYS", "SUP", "VRN", "VDF", "VAP", "FILE", "ENV", "GATE", "CORE")
SECTIONS = ("MGR", "ENG", "LIB", "UIX", "CTR", "OTH")

SKIP_DIRS = {
    "__pycache__", ".git", ".svn", ".venv", "venv", "env", "node_modules",
    ".idea", ".vs", "_legacy", "_to_delete", "_backup", "site-packages",
    "temp", "logs", "output", "dist-info",
}

CODE_EXT = {".py", ".pyw", ".ps1", ".psm1", ".psd1"}
DATA_EXT = {".json", ".yaml", ".yml", ".csv", ".txt", ".md", ".html"}

FETCH_SIGNALS = (
    "requests", "urllib", "httpx", "aiohttp", "socket", "ftplib", "yfinance",
    "selenium", "urlopen", "openapi", "twse", "tpex", "taifex", "endpoint",
)

ACCELERATOR_CANDIDATES = (
    "polars", "pyarrow", "duckdb", "numpy", "pandas", "regex", "rapidfuzz",
    "pydantic", "psutil", "watchfiles",
)

STDLIB = set(getattr(sys, "stdlib_module_names", ()))


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def sha256_file(path: Path, limit: int = 64 * 1024 * 1024) -> str:
    try:
        if path.stat().st_size > limit:
            return "SKIP_LARGE"
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(1 << 20), b""):
                digest.update(chunk)
        return digest.hexdigest()[:32]
    except OSError:
        return "HASH_FAIL"


def read_text(path: Path, max_bytes: int = 2 * 1024 * 1024) -> str:
    try:
        raw = path.open("rb").read(max_bytes)
    except OSError:
        return ""
    for enc in ("utf-8-sig", "utf-8", "cp950", "latin-1"):
        try:
            return raw.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return raw.decode("utf-8", "replace")


def write_utf8(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)


def append_jsonl(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False) + "\n")


def family_key(name: str) -> str:
    """版本世系鍵：剝掉版本、副本標記與時間戳後的穩定名稱。"""
    base = re.sub(r"\.(py|pyw|ps1|psm1|psd1|json|md|html|csv|txt)$", "", name, flags=re.I)
    base = re.sub(r"[ _-]?\(\d+\)", "", base)
    base = re.sub(r"\s*-\s*複製", "", base)
    base = re.sub(r"[ _-]copy$", "", base, flags=re.I)
    base = re.sub(r"[_-]sha[0-9a-f]{6,}", "", base, flags=re.I)
    base = re.sub(r"[_-]?v\d{2,4}[A-Za-z]?", "", base, flags=re.I)
    base = re.sub(r"_\d{8}(_\d{6})?", "", base)
    return re.sub(r"[^A-Za-z0-9\u4e00-\u9fff]", "", base).lower()


def is_copy_marked(name: str) -> int:
    return 1 if re.search(r"\(\d+\)|複製|[ _-]copy\.", name, flags=re.I) else 0


class Console:
    """行內進度輸出。不吃回車、不阻塞，供 CI 直接擷取。"""

    def __init__(self) -> None:
        self.lines: List[str] = []

    def say(self, message: str, level: str = "INFO") -> None:
        line = "[%s][%s] %s" % (datetime.now().strftime("%H:%M:%S"), level, message)
        self.lines.append(line)
        print(line, flush=True)


LOG = Console()


# ---------------------------------------------------------------------------
# §1  子系統管理者統一抽象基底
# ---------------------------------------------------------------------------

class SubsystemManagerABC(ABC):
    """兩層式架構的下層契約。母系統只認這個介面，不認實作細節。

    子系統管理者是純粹的執行者：對內調度自己的 ENG/MDL，對外只暴露
    urn / health_check / execute_task 三個點，並可選擇性回報 uplink 新詞。
    """

    @property
    @abstractmethod
    def urn(self) -> str:
        """子系統唯一編號，例如 VIA-VDF-MGR-001。"""

    @abstractmethod
    def health_check(self) -> bool:
        """回報節點即時健康度。不得有副作用。"""

    @abstractmethod
    def execute_task(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """標準化執行介面。context 由母系統依參數 SSOT 注入。"""

    def uplink_terms(self) -> List[str]:
        """邊緣新欄位/別名上推至母系統 SSOT 待審佇列。預設無。"""
        return []


# ---------------------------------------------------------------------------
# §2  URN 編號權威（Spec v0100 §1）
# ---------------------------------------------------------------------------

@dataclass
class RegistryEntry:
    urn: str
    key: str
    name: str
    path: str
    namespace: str
    section: str
    state: str = "ACTIVE"
    sha: str = ""
    first_seen: str = ""
    last_seen: str = ""
    note: str = ""


class URNAuthority:
    """單一發碼官。R1 唯一 / R2 永久 / R3 單一權威 / R4 冪等 / R5 全 ID 外鍵。"""

    def __init__(self, registry_path: Path, ledger_path: Path) -> None:
        self.registry_path = registry_path
        self.ledger_path = ledger_path
        self.entries: Dict[str, RegistryEntry] = {}   # key -> entry
        self.by_urn: Dict[str, RegistryEntry] = {}
        self.serials: Dict[Tuple[str, str], int] = {}
        self.issued_this_run = 0
        self.relocated = 0
        self._load()

    def _load(self) -> None:
        if not self.registry_path.exists():
            return
        try:
            doc = json.loads(read_text(self.registry_path))
        except (json.JSONDecodeError, ValueError):
            LOG.say("台帳無法解析，本輪以空白視圖執行（原檔不動）", "WARN")
            return
        for row in doc.get("entries", []):
            entry = RegistryEntry(**{k: row.get(k, "") for k in RegistryEntry.__annotations__})
            self.entries[entry.key] = entry
            self.by_urn[entry.urn] = entry
            parts = entry.urn.split("-")
            if len(parts) == 4:
                try:
                    serial = int(parts[3])
                except ValueError:
                    continue
                slot = (parts[1], parts[2])
                self.serials[slot] = max(self.serials.get(slot, 0), serial)
        LOG.say("台帳載入：%d 筆永久編號" % len(self.entries), "OK")

    def allocate(self, key: str, name: str, path: str, namespace: str,
                 section: str, sha: str = "", note: str = "") -> RegistryEntry:
        """R4：同 key 必須解析回同一 URN。"""
        stamp = now_stamp()
        existing = self.entries.get(key)
        if existing is not None:
            if existing.path != path:
                existing.path = path
                existing.state = "RELOCATED"
                self.relocated += 1
            elif existing.state in ("MISSING", "RELOCATED"):
                existing.state = "ACTIVE"
            existing.last_seen = stamp
            existing.sha = sha or existing.sha
            return existing

        namespace = namespace if namespace in NAMESPACES else "FILE"
        section = section if section in SECTIONS else "OTH"
        slot = (namespace, section)
        self.serials[slot] = self.serials.get(slot, 0) + 1
        urn = "VIA-%s-%s-%04d" % (namespace, section, self.serials[slot])
        entry = RegistryEntry(urn=urn, key=key, name=name, path=path,
                              namespace=namespace, section=section, state="ACTIVE",
                              sha=sha, first_seen=stamp, last_seen=stamp, note=note)
        self.entries[key] = entry
        self.by_urn[urn] = entry
        self.issued_this_run += 1
        return entry

    def mark_absent(self, touched: Set[str]) -> int:
        """S2：消失只是狀態，不是刪除。"""
        gone = 0
        for key, entry in self.entries.items():
            if key in touched:
                continue
            if entry.state not in ("MISSING", "DORMANT", "DELISTED"):
                entry.state = "MISSING"
            gone += 1
        return gone

    def set_state(self, urn: str, state: str, note: str = "") -> None:
        entry = self.by_urn.get(urn)
        if entry is None:
            return
        entry.state = state
        if note:
            entry.note = note

    def duplicate_urns(self) -> int:
        seen: Set[str] = set()
        dups = 0
        for entry in self.entries.values():
            if entry.urn in seen:
                dups += 1
            seen.add(entry.urn)
        return dups

    def to_document(self) -> Dict[str, Any]:
        states: Dict[str, int] = {}
        for entry in self.entries.values():
            states[entry.state] = states.get(entry.state, 0) + 1
        return {
            "schema": "VIA.URNRegistry",
            "spec": SPEC_VERSION,
            "authority": URN_SELF,
            "generated": iso_now(),
            "policy": "append-only; URN is permanent; MISSING is a state, never a deletion",
            "total": len(self.entries),
            "issued_this_run": self.issued_this_run,
            "relocated": self.relocated,
            "states": states,
            "entries": [asdict(e) for e in sorted(self.entries.values(), key=lambda x: x.urn)],
        }

    def commit(self, dry_run: bool) -> Path:
        doc = self.to_document()
        target = self.registry_path if not dry_run else self.registry_path.with_suffix(".preview.json")
        write_utf8(target, json.dumps(doc, ensure_ascii=False, indent=1))
        append_jsonl(self.ledger_path, {
            "ts": iso_now(), "authority": URN_SELF, "issued": self.issued_this_run,
            "relocated": self.relocated, "total": len(self.entries), "committed": not dry_run,
        })
        return target


# ---------------------------------------------------------------------------
# §3  全景掃描與重複家族
# ---------------------------------------------------------------------------

@dataclass
class FileRecord:
    path: Path
    rel: str
    name: str
    ext: str
    size: int
    mtime: float
    sha: str = ""
    namespace: str = "FILE"
    section: str = "OTH"
    family: str = ""
    copy_mark: int = 0
    urn: str = ""
    verdict: str = ""
    canonical_of: str = ""


def classify(rel: str, name: str) -> Tuple[str, str]:
    probe = (rel + "/" + name).lower().replace("\\", "/")
    namespace = "FILE"
    if re.search(r"(^|/)vap(/|[_-])|vap_", probe):
        namespace = "VAP"
    elif re.search(r"(^|/)vrn(/|[_-])|vrn_", probe):
        namespace = "VRN"
    elif re.search(r"(^|/)vdf(/|[_-])|vdf_", probe):
        namespace = "VDF"
    elif re.search(r"aegis|celeritas|netsupport|codexnexus|supportive|sup_", probe):
        namespace = "SUP"
    elif re.search(r"(^|/)core(/|$)|centralgovernance|systemlauncher|sys_", probe):
        namespace = "SYS"

    lower = name.lower()
    if re.search(r"manager|_mgr_|console|launcher|dispatcher|^invoke-|^start", lower):
        section = "MGR"
    elif re.search(r"engine|_eng_|inspector|harness|guard|nexus|celeritas", lower):
        section = "ENG"
    elif re.search(r"_lib_|toolkit|support|util|batch|client", lower):
        section = "LIB"
    elif lower.endswith(".html"):
        section = "UIX"
    elif lower.endswith((".json", ".yaml", ".yml")):
        section = "CTR"
    else:
        section = "OTH"
    return namespace, section


def discover(roots: Iterable[Path], max_files: int,
             exclude_dirs: Optional[Set[Path]] = None) -> List[FileRecord]:
    """排除治理引擎自己的產出，避免自我回饋迴路（每跑一次就多發一批編號）。"""
    records: List[FileRecord] = []
    seen: Set[str] = set()
    blocked = {p.resolve() for p in (exclude_dirs or set())}
    for root in roots:
        if not root.is_dir():
            continue
        base = str(root)
        for dirpath, dirnames, filenames in os.walk(root):
            here = Path(dirpath).resolve()
            if any(here == b or b in here.parents for b in blocked):
                dirnames[:] = []
                continue
            dirnames[:] = [d for d in dirnames if d.lower() not in SKIP_DIRS]
            for filename in filenames:
                ext = os.path.splitext(filename)[1].lower()
                if ext not in CODE_EXT and ext not in DATA_EXT:
                    continue
                full = Path(dirpath) / filename
                token = str(full).lower()
                if token in seen:
                    continue
                seen.add(token)
                try:
                    stat = full.stat()
                except OSError:
                    continue
                rel = os.path.relpath(str(full), base).replace("\\", "/")
                namespace, section = classify(rel, filename)
                records.append(FileRecord(
                    path=full, rel=rel, name=filename, ext=ext,
                    size=stat.st_size, mtime=stat.st_mtime,
                    namespace=namespace, section=section,
                    family=family_key(filename), copy_mark=is_copy_marked(filename),
                ))
                if len(records) >= max_files:
                    LOG.say("掃描上限 %d 達成" % max_files, "WARN")
                    return records
    return records


def resolve_duplicates(records: List[FileRecord]) -> Tuple[int, int]:
    """S3/S4：以內容雜湊分組，非副本 -> 最早 mtime -> 路徑序決定正本。"""
    buckets: Dict[str, List[FileRecord]] = {}
    for record in records:
        record.sha = sha256_file(record.path)
        if record.sha in ("SKIP_LARGE", "HASH_FAIL"):
            continue
        buckets.setdefault(record.sha, []).append(record)

    groups = 0
    redundant = 0
    for sha, members in buckets.items():
        if len(members) < 2:
            continue
        groups += 1
        members.sort(key=lambda r: (r.copy_mark, r.mtime, str(r.path)))
        canonical = members[0]
        canonical.verdict = "CANONICAL"
        for other in members[1:]:
            other.verdict = "DUPLICATE"
            other.canonical_of = str(canonical.path)
            redundant += 1
    return groups, redundant


# ---------------------------------------------------------------------------
# §4  AST 自省：座標、指紋、簽章、呼叫
# ---------------------------------------------------------------------------

@dataclass
class CodeBlock:
    name: str
    kind: str
    start_line: int
    end_line: int
    col_offset: int
    ast_hash: str
    has_docstring: bool


@dataclass
class ModuleFacts:
    path: str
    language: str
    parseable: bool = True
    error: str = ""
    blocks: List[CodeBlock] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    parameters: List[Dict[str, Any]] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    fetcher: bool = False
    manager_classes: List[str] = field(default_factory=list)


PS_PARAM_RE = re.compile(
    r"\[(?P<type>[A-Za-z\[\]]+)\]\s*\$(?P<name>[A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s*=\s*(?P<default>'[^']*'|\"[^\"]*\"|[^,\)\r\n]+))?"
)
PS_VALIDATE_RE = re.compile(r"\[ValidateSet\(([^\)]*)\)\]\s*\r?\n\s*\[[A-Za-z\[\]]+\]\s*\$(\w+)")


class ASTInspector:
    """§4 AST 座標級定位：Class/Function 起訖行、縮排位移與區塊雜湊。"""

    @staticmethod
    def inspect_python(path: Path) -> ModuleFacts:
        facts = ModuleFacts(path=str(path), language="python")
        source = read_text(path)
        if not source:
            facts.parseable = False
            facts.error = "empty or unreadable"
            return facts
        try:
            tree = ast.parse(source, filename=str(path))
        except SyntaxError as exc:
            facts.parseable = False
            facts.error = "line %s: %s" % (exc.lineno, exc.msg)
            return facts

        lines = source.splitlines()
        low = source.lower()
        facts.fetcher = any(sig in low for sig in FETCH_SIGNALS)

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                end = getattr(node, "end_lineno", node.lineno) or node.lineno
                segment = "\n".join(lines[node.lineno - 1:end])
                facts.blocks.append(CodeBlock(
                    name=node.name,
                    kind="CLASS" if isinstance(node, ast.ClassDef) else "FUNCTION",
                    start_line=node.lineno, end_line=end, col_offset=node.col_offset,
                    ast_hash=hashlib.sha256(segment.encode("utf-8")).hexdigest()[:12],
                    has_docstring=ast.get_docstring(node) is not None,
                ))
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if getattr(base, "id", "") == "SubsystemManagerABC":
                            facts.manager_classes.append(node.name)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    facts.imports.append(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:
                    facts.imports.append(node.module.split(".")[0])

        facts.imports = sorted(set(facts.imports))
        facts.parameters = ASTInspector._python_signature(tree)
        facts.calls = ASTInspector._string_callees(source)
        return facts

    @staticmethod
    def _python_signature(tree: ast.AST) -> List[Dict[str, Any]]:
        """優先取 argparse 宣告；沒有就取 execute_task / main 的函式簽章。"""
        params: List[Dict[str, Any]] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if getattr(func, "attr", "") != "add_argument":
                continue
            if not node.args:
                continue
            first = node.args[0]
            if not isinstance(first, ast.Constant) or not isinstance(first.value, str):
                continue
            item: Dict[str, Any] = {"name": first.value.lstrip("-"), "kind": "cli"}
            for kw in node.keywords:
                if kw.arg in ("default", "choices") and isinstance(kw.value, ast.Constant):
                    item[kw.arg] = kw.value.value
                elif kw.arg == "choices" and isinstance(kw.value, (ast.List, ast.Tuple)):
                    item["choices"] = [e.value for e in kw.value.elts
                                       if isinstance(e, ast.Constant)]
                elif kw.arg == "action" and isinstance(kw.value, ast.Constant):
                    item["action"] = kw.value.value
            params.append(item)
        if params:
            return params
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and \
                    node.name in ("execute_task", "main", "run"):
                for arg in node.args.args:
                    if arg.arg == "self":
                        continue
                    params.append({"name": arg.arg, "kind": "arg"})
                break
        return params

    @staticmethod
    def _string_callees(source: str) -> List[str]:
        found = re.findall(r"['\"]([A-Za-z0-9_\-]+\.(?:py|ps1))['\"]", source)
        return sorted(set(found))

    @staticmethod
    def inspect_powershell(path: Path) -> ModuleFacts:
        facts = ModuleFacts(path=str(path), language="powershell")
        source = read_text(path)
        if not source:
            facts.parseable = False
            facts.error = "empty or unreadable"
            return facts
        low = source.lower()
        facts.fetcher = any(sig in low for sig in FETCH_SIGNALS)

        match = re.search(r"(?ims)^\s*param\s*\((?P<body>.*?)\n\s*\)", source)
        validate: Dict[str, List[str]] = {}
        if match:
            body = match.group("body")
            for raw in PS_VALIDATE_RE.finditer(body):
                values = [v.strip().strip("'\"") for v in raw.group(1).split(",")]
                validate[raw.group(2)] = values
            for raw in PS_PARAM_RE.finditer(body):
                name = raw.group("name")
                default = (raw.group("default") or "").strip().strip("'\"")
                item: Dict[str, Any] = {"name": name, "kind": raw.group("type").lower()}
                if default:
                    item["default"] = default
                if name in validate:
                    item["choices"] = validate[name]
                facts.parameters.append(item)
        for raw in re.finditer(r"(?im)^\s*(?:function\s+)([A-Za-z][\w-]*)", source):
            facts.blocks.append(CodeBlock(raw.group(1), "FUNCTION", 0, 0, 0, "", False))
        facts.calls = ASTInspector._string_callees(source)
        return facts

    @staticmethod
    def inspect(path: Path) -> ModuleFacts:
        if path.suffix.lower() in (".py", ".pyw"):
            return ASTInspector.inspect_python(path)
        return ASTInspector.inspect_powershell(path)


# ---------------------------------------------------------------------------
# §5  介面契約治理（Spec §3，補 GAP-02 / GAP-03）
# ---------------------------------------------------------------------------

class ContractGovernor:
    """I1 來源即真理；I2 宣告與 param() 不符 = FAIL，不是 WARN。"""

    def __init__(self, contract_path: Path) -> None:
        self.contract_path = contract_path
        self.declared: Dict[str, Dict[str, Any]] = {}
        self.seeded = False
        if contract_path.exists():
            try:
                doc = json.loads(read_text(contract_path))
                for row in doc.get("contracts", []):
                    self.declared[row["id"]] = row
            except (json.JSONDecodeError, ValueError, KeyError):
                LOG.say("介面契約檔無法解析，本輪視為未宣告", "WARN")
        self.mismatches: List[Dict[str, Any]] = []
        self.checked = 0

    @staticmethod
    def _names(params: List[Dict[str, Any]]) -> Set[str]:
        return {str(p.get("name", "")).lower() for p in params if p.get("name")}

    def verify(self, urn: str, facts: ModuleFacts) -> str:
        row = self.declared.get(urn)
        if row is None:
            return "UNDECLARED"
        self.checked += 1
        want = self._names(row.get("parameters", []))
        have = self._names(facts.parameters)
        missing = sorted(want - have)
        extra = sorted(have - want)
        bad_choices: List[str] = []
        by_name = {str(p.get("name", "")).lower(): p for p in facts.parameters}
        for declared_param in row.get("parameters", []):
            name = str(declared_param.get("name", "")).lower()
            declared_choices = declared_param.get("choices")
            if not declared_choices or name not in by_name:
                continue
            actual = by_name[name].get("choices")
            if actual and sorted(actual) != sorted(declared_choices):
                bad_choices.append(name)
        if missing or extra or bad_choices:
            self.mismatches.append({
                "urn": urn, "path": facts.path,
                "declared_only": missing, "source_only": extra,
                "choice_drift": bad_choices,
            })
            return "MISMATCH"
        return "MATCH"

    def seed(self, rows: List[Dict[str, Any]], dry_run: bool) -> None:
        """契約檔不存在時，從原始碼播種一份 V 級基準。"""
        if self.declared:
            return
        self.seeded = True
        doc = {
            "schema": "VIA.InterfaceContracts",
            "spec": SPEC_VERSION,
            "generated": iso_now(),
            "note": "seeded from source; subsequent runs compare against this baseline",
            "contracts": rows,
        }
        target = self.contract_path if not dry_run else \
            self.contract_path.with_suffix(".preview.json")
        write_utf8(target, json.dumps(doc, ensure_ascii=False, indent=1))
        LOG.say("介面契約基準播種：%d 筆 -> %s" % (len(rows), target.name), "OK")


class CallGraphResolver:
    """I3 calls 必須解析得到 URN，否則 UNRESOLVED_CALLEE。"""

    def __init__(self) -> None:
        self.edges: List[Tuple[str, str]] = []
        self.unresolved: List[Dict[str, str]] = []

    def resolve(self, records: List[FileRecord], facts_map: Dict[str, ModuleFacts]) -> None:
        by_name: Dict[str, str] = {}
        for record in records:
            if record.urn:
                by_name.setdefault(record.name.lower(), record.urn)
        for record in records:
            facts = facts_map.get(str(record.path))
            if facts is None:
                continue
            for callee in facts.calls:
                target = by_name.get(callee.lower())
                if target is None:
                    self.unresolved.append({
                        "caller": record.urn, "caller_name": record.name, "callee": callee,
                    })
                    continue
                if target != record.urn:
                    self.edges.append((record.urn, target))


# ---------------------------------------------------------------------------
# §6  拓撲防護：DFS 三色循環偵測 + 九頭龍爆炸半徑
# ---------------------------------------------------------------------------

class TopologyGuard:
    WHITE, GREY, BLACK = 0, 1, 2

    def __init__(self, edges: List[Tuple[str, str]]) -> None:
        self.adj: Dict[str, List[str]] = {}
        self.nodes: Set[str] = set()
        for src, dst in edges:
            self.adj.setdefault(src, []).append(dst)
            self.nodes.update((src, dst))
        self.cycles: List[List[str]] = []

    def detect_cycles(self) -> List[List[str]]:
        colour: Dict[str, int] = {node: self.WHITE for node in self.nodes}
        stack: List[str] = []

        def visit(node: str) -> None:
            colour[node] = self.GREY
            stack.append(node)
            for peer in self.adj.get(node, []):
                state = colour.get(peer, self.WHITE)
                if state == self.GREY:            # back-edge
                    if peer in stack:
                        self.cycles.append(stack[stack.index(peer):] + [peer])
                elif state == self.WHITE:
                    visit(peer)
            stack.pop()
            colour[node] = self.BLACK

        for node in sorted(self.nodes):
            if colour.get(node, self.WHITE) == self.WHITE:
                visit(node)
        return self.cycles

    def blast_radius(self) -> Dict[str, int]:
        """九頭龍風險：改動某節點時，有多少節點會被連帶影響（反向可達）。"""
        reverse: Dict[str, List[str]] = {}
        for src, targets in self.adj.items():
            for dst in targets:
                reverse.setdefault(dst, []).append(src)
        radius: Dict[str, int] = {}
        for node in self.nodes:
            seen: Set[str] = set()
            queue = list(reverse.get(node, []))
            while queue:
                current = queue.pop()
                if current in seen:
                    continue
                seen.add(current)
                queue.extend(reverse.get(current, []))
            radius[node] = len(seen)
        return radius


# ---------------------------------------------------------------------------
# §7  主動探針（動態掛載子系統管理者並舉證）
# ---------------------------------------------------------------------------

class ProbeHarness:
    """搓啟動偵測。動態載入會執行模組頂層程式碼，因此預設關閉，需 --probe。"""

    def __init__(self, evidence_path: Path) -> None:
        self.evidence_path = evidence_path
        self.results: List[Dict[str, Any]] = []

    @staticmethod
    def is_manager(cls: type) -> bool:
        """鴨子型別判定。

        子系統管理者若自行 import 本檔取得 ABC，會拿到與探針不同的類別物件
        （模組被載入兩次），strict issubclass 會誤判為不是管理者。因此以
        MRO 名稱 + 介面完整性雙軌認定。
        """
        if cls is SubsystemManagerABC or cls.__name__ == "SubsystemManagerABC":
            return False
        if inspect.isabstract(cls):
            return False
        try:
            if issubclass(cls, SubsystemManagerABC):
                return True
        except TypeError:
            pass
        names = {base.__name__ for base in getattr(cls, "__mro__", ())}
        if "SubsystemManagerABC" in names:
            return True
        needed = ("urn", "health_check", "execute_task")
        if all(hasattr(cls, attr) for attr in needed) and not inspect.isabstract(cls):
            return cls.__module__ != __name__
        return False

    def probe_file(self, path: Path) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        module_name = "via_probe_" + re.sub(r"[^A-Za-z0-9_]", "_", path.stem)
        try:
            spec = importlib.util.spec_from_file_location(module_name, path)
            if spec is None or spec.loader is None:
                raise ImportError("no loader")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except BaseException as exc:                      # 探針必須吞掉所有意外
            record = {"path": str(path), "urn": "UNKNOWN", "status": "LOAD_FAILED",
                      "error": "%s: %s" % (type(exc).__name__, exc), "latency_ms": 0.0}
            self._record(record)
            return [record]

        for attr in dir(module):
            candidate = getattr(module, attr)
            if not inspect.isclass(candidate):
                continue
            if not ProbeHarness.is_manager(candidate):
                continue
            out.append(self._probe_class(path, candidate))
        if not out:
            record = {"path": str(path), "urn": "UNKNOWN", "status": "NO_MANAGER",
                      "error": "no SubsystemManagerABC subclass", "latency_ms": 0.0}
            self._record(record)
            out.append(record)
        return out

    def _probe_class(self, path: Path, cls: type) -> Dict[str, Any]:
        started = time.perf_counter()
        try:
            instance = cls()                              # type: ignore[call-arg]
            urn = str(getattr(instance, "urn", "UNKNOWN"))
            healthy = bool(instance.health_check())
            signature = list(inspect.signature(instance.execute_task).parameters.keys())
            if not healthy:
                raise RuntimeError("health_check returned False")
            payload = {"probe": True, "symbol": "2330.TW"}
            result = instance.execute_task(payload)
            record = {
                "path": str(path), "urn": urn, "class": cls.__name__,
                "status": "VERIFIED_OPERATIONAL",
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "signature": signature,
                "result_keys": sorted(result.keys()) if isinstance(result, dict) else [],
                "error": "",
            }
        except BaseException as exc:
            record = {
                "path": str(path), "urn": getattr(cls, "__name__", "UNKNOWN"),
                "class": cls.__name__, "status": "PROBE_FAILED",
                "latency_ms": round((time.perf_counter() - started) * 1000, 3),
                "signature": [], "result_keys": [],
                "error": "%s: %s" % (type(exc).__name__, exc),
            }
        self._record(record)
        return record

    def _record(self, record: Dict[str, Any]) -> None:
        record["ts"] = iso_now()
        self.results.append(record)
        append_jsonl(self.evidence_path, record)


# ---------------------------------------------------------------------------
# §8  環境契約（Spec §4，補 GAP-04）
# ---------------------------------------------------------------------------

class EnvironmentAudit:
    """E3：Store 版 python 別名視為不存在。E5：環境狀態進台帳。"""

    GOLDEN_PINS = {"numpy": ">=1.24,<2.0"}
    BANNED = ("uvloop",)

    def __init__(self, audit_log: Path) -> None:
        self.audit_log = audit_log
        self.facts: Dict[str, Any] = {}
        self.accelerators: Dict[str, str] = {}
        self.violations: List[str] = []

    @staticmethod
    def is_store_alias(executable: str) -> bool:
        return "windowsapps" in executable.lower()

    def collect(self) -> Dict[str, Any]:
        for module in ACCELERATOR_CANDIDATES:
            try:
                found = importlib.util.find_spec(module) is not None
            except (ImportError, ValueError, ModuleNotFoundError):
                found = False
            self.accelerators[module] = "AVAILABLE" if found else "ABSENT"

        interpreter = sys.executable or ""
        runtime_state = "OK"
        if not interpreter:
            runtime_state = "BLOCKED_PYTHON_RUNTIME_ABSENT"
        elif self.is_store_alias(interpreter):
            runtime_state = "REJECTED_STORE_ALIAS"
            self.violations.append("E3 直譯器是 Microsoft Store 別名（安裝樁），視為不存在")

        for banned in self.BANNED:
            if self.accelerators.get(banned) == "AVAILABLE":
                self.violations.append("E2 禁用套件存在：%s" % banned)

        numpy_version = ""
        if self.accelerators.get("numpy") == "AVAILABLE":
            try:
                import numpy                                     # noqa: PLC0415
                numpy_version = str(numpy.__version__)
                major = int(numpy_version.split(".")[0])
                if major >= 2:
                    self.violations.append(
                        "E1 黃金律違反：numpy %s 超出 >=1.24,<2.0" % numpy_version)
            except Exception:                                    # noqa: BLE001
                numpy_version = "UNKNOWN"

        self.facts = {
            "ts": iso_now(),
            "os": platform.platform(),
            "python": sys.version.split()[0],
            "executable": interpreter,
            "runtime_state": runtime_state,
            "cpu_cores": os.cpu_count(),
            "venv": os.environ.get("VIRTUAL_ENV", ""),
            "accelerators": self.accelerators,
            "numpy_version": numpy_version,
            "golden_pins": self.GOLDEN_PINS,
            "violations": self.violations,
        }
        append_jsonl(self.audit_log, self.facts)
        return self.facts


# ---------------------------------------------------------------------------
# §9  同義字 SSOT（Spec §2 的最小可用實作）
# ---------------------------------------------------------------------------

class SynonymSSOT:
    """V1 三級證據 / V2 只增不減 / V3 三段自適應 / V4 可編譯 / V5 自我測試。"""

    AUTO, ASK = 0.90, 0.75

    def __init__(self, vocab_path: Path) -> None:
        self.vocab_path = vocab_path
        self.vocab: Dict[str, Dict[str, Any]] = {}
        if vocab_path.exists():
            try:
                self.vocab = json.loads(read_text(vocab_path)).get("canonicals", {})
            except (json.JSONDecodeError, ValueError):
                LOG.say("詞彙 SSOT 無法解析，本輪以空白視圖執行", "WARN")
        self.ask_queue: List[Dict[str, Any]] = []
        self.quarantine: List[str] = []
        self.selftest_total = 0
        self.selftest_hit = 0

    @staticmethod
    def expand(term: str) -> List[str]:
        """決定性變體：全半形正規化 / 大小寫 / 分隔符。不猜語意。"""
        import unicodedata
        base = unicodedata.normalize("NFKC", term).strip()
        out = {base, base.lower(), base.upper(),
               base.replace("_", " "), base.replace(" ", "_"), base.replace("-", "_")}
        if base.isascii() and len(base) >= 3 and base.isalpha():
            out.add(base.title())
        return sorted(v for v in out if v)

    def observe(self, term: str) -> str:
        """V3：與最近 canonical 比相似度，分 AUTO / ASK / QUARANTINE。"""
        import difflib
        if not term or term in self.vocab:
            return "KNOWN"
        for record in self.vocab.values():
            if term in record.get("synonyms", {}):
                return "KNOWN"
        names = list(self.vocab.keys())
        best, score = "", 0.0
        for name in names:
            ratio = difflib.SequenceMatcher(None, term, name).ratio()
            if ratio > score:
                best, score = name, ratio
        if score >= self.AUTO and best:
            self.vocab[best].setdefault("synonyms", {})[term] = {
                "grade": "M", "source": "auto-expand", "added": now_stamp()}
            return "AUTO"
        if score >= self.ASK and best:
            self.ask_queue.append({"term": term, "nearest": best, "score": round(score, 3)})
            return "ASK"
        self.quarantine.append(term)
        return "QUARANTINE"

    def register(self, canonical: str, urn: str, synonyms: Optional[List[str]] = None) -> None:
        record = self.vocab.setdefault(canonical, {
            "urn": urn, "state": "ACTIVE", "synonyms": {}, "regex_auto": ""})
        record["urn"] = urn
        for term in (synonyms or []) + self.expand(canonical):
            if term == canonical:
                continue
            record["synonyms"].setdefault(term, {
                "grade": "M", "source": "auto-expand", "added": now_stamp()})
        record["regex_auto"] = self.build_regex(canonical, list(record["synonyms"].keys()))

    @staticmethod
    def build_regex(canonical: str, synonyms: List[str]) -> str:
        """V4：交替式 + 邊界規則（交替端為非字元時不加 \\b；CJK 不用 \\b）。"""
        terms = sorted({canonical, *synonyms}, key=len, reverse=True)
        alternation = "|".join(re.escape(t) for t in terms if t)
        if not alternation:
            return ""
        edges_wordy = all(t[:1].isalnum() and t[-1:].isalnum() for t in terms if t)
        has_cjk = any(any("\u4e00" <= ch <= "\u9fff" for ch in t) for t in terms)
        if edges_wordy and not has_cjk:
            pattern = r"\b(?:%s)\b" % alternation
        elif edges_wordy:
            pattern = r"(?<![A-Za-z0-9])(?:%s)(?![A-Za-z0-9])" % alternation
        else:
            pattern = r"(?:%s)" % alternation
        try:
            re.compile(pattern)
        except re.error:
            return ""
        return pattern

    def selftest(self) -> Tuple[int, int]:
        """V5：所有同義字必須被自己的 regex 命中。"""
        for canonical, record in self.vocab.items():
            pattern = record.get("regex_auto") or ""
            if not pattern:
                continue
            try:
                compiled = re.compile(pattern)
            except re.error:
                continue
            for term in [canonical, *record.get("synonyms", {}).keys()]:
                self.selftest_total += 1
                if compiled.search(term):
                    self.selftest_hit += 1
        return self.selftest_hit, self.selftest_total

    def commit(self, dry_run: bool) -> Path:
        doc = {"schema": "VIA.SynonymSSOT", "spec": SPEC_VERSION,
               "generated": iso_now(), "canonicals": self.vocab,
               "ask_queue": self.ask_queue, "quarantine": self.quarantine}
        target = self.vocab_path if not dry_run else self.vocab_path.with_suffix(".preview.json")
        write_utf8(target, json.dumps(doc, ensure_ascii=False, indent=1))
        return target


# ---------------------------------------------------------------------------
# §10  Gate 矩陣
# ---------------------------------------------------------------------------

@dataclass
class Gate:
    code: str
    title: str
    status: str
    detail: str


class GateMatrix:
    def __init__(self) -> None:
        self.gates: List[Gate] = []

    def add(self, code: str, title: str, status: str, detail: str) -> None:
        self.gates.append(Gate(code, title, status, detail))

    @property
    def failures(self) -> int:
        return sum(1 for g in self.gates if g.status == "FAIL")

    @property
    def warnings(self) -> int:
        return sum(1 for g in self.gates if g.status == "WARN")

    @property
    def verdict(self) -> str:
        if self.failures:
            return "RED"
        if self.warnings:
            return "AMBER"
        return "GREEN"


# ---------------------------------------------------------------------------
# §11  Visual Lock HTML
# ---------------------------------------------------------------------------

CSS = """
:root{--paper:#f2f2f3;--ink:#1d1f20;--line:#d8d8d9;--red:#b0453d;--green:#3f7d5e;--amber:#c4943a;--panel:#fff}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:14px}
.wrap{display:flex;min-height:100vh}
.left{width:248px;flex:0 0 248px;background:var(--panel);border-right:1px solid var(--line);padding:22px 0;position:sticky;top:0;height:100vh;overflow:auto}
.brand{padding:0 22px 18px;border-bottom:1px solid var(--line);margin-bottom:14px}
.seal{display:inline-flex;width:44px;height:44px;align-items:center;justify-content:center;background:var(--red);color:#fff;font-family:"Noto Serif TC",serif;font-size:24px;border-radius:3px}
.brand h1{font-family:"Noto Serif TC",Georgia,serif;font-size:14px;letter-spacing:.16em;margin:12px 0 4px;text-transform:uppercase}
.brand .sub{font-size:11px;color:#77797b;letter-spacing:.06em}
nav a{display:block;padding:9px 22px;color:#4a4c4e;text-decoration:none;border-left:3px solid transparent;cursor:pointer}
nav a:hover{background:#fafafa;color:var(--ink)}
nav a.active{border-left-color:var(--red);background:#faf6f6;color:var(--ink);font-weight:600}
.right{flex:1;padding:34px 40px;overflow:auto}
h2{font-family:"Noto Serif TC",Georgia,serif;font-size:18px;letter-spacing:.05em;margin:0 0 6px}
.lede{color:#6c6e70;font-size:12.5px;margin:0 0 18px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(148px,1fr));gap:12px;margin-bottom:22px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:14px 16px}
.card .k{font-size:11px;letter-spacing:.11em;color:#8a8c8e;text-transform:uppercase}
.card .v{font-size:24px;font-family:"Noto Serif TC",Georgia,serif;margin-top:4px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:12.5px}
th,td{border-bottom:1px solid #ececed;padding:7px 10px;text-align:left;vertical-align:top;word-break:break-all}
th{background:#eeeeef;font-size:11px;letter-spacing:.09em;text-transform:uppercase;color:#5c5e60;position:sticky;top:0}
tr:hover td{background:#fbfbfb}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:18px}
section{display:none}section.on{display:block}
pre{background:var(--panel);border:1px solid var(--line);padding:14px;font-size:12px;white-space:pre-wrap;max-height:55vh;overflow:auto}
code{background:#ececed;padding:1px 5px;border-radius:2px}
"""


def esc(value: Any) -> str:
    return (str(value).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;"))


def status_class(value: str) -> str:
    upper = str(value).upper()
    if re.search(r"PASS|GREEN|OK|ACTIVE|CANONICAL|MATCH|VERIFIED", upper):
        return "ok"
    if re.search(r"FAIL|RED|ERROR|MISMATCH|CYCLE", upper):
        return "fail"
    if re.search(r"WARN|AMBER|MISSING|DUPLICATE|RELOCATED|UNRESOLVED|UNDECLARED|ASK|QUARANTINE", upper):
        return "warn"
    return ""


def rows_html(items: List[Dict[str, Any]], fields: List[str],
              status_field: str = "", limit: int = 500) -> str:
    if not items:
        return "<tr><td colspan='%d' class='muted'>—— 無資料 ——</td></tr>" % len(fields)
    out: List[str] = []
    for item in items[:limit]:
        cells: List[str] = []
        for name in fields:
            value = item.get(name, "")
            if isinstance(value, (list, tuple)):
                value = ", ".join(str(v) for v in value)
            cls = " class='%s'" % status_class(str(value)) if name == status_field else ""
            cells.append("<td%s>%s</td>" % (cls, esc(value)))
        out.append("<tr>%s</tr>" % "".join(cells))
    if len(items) > limit:
        out.append("<tr><td colspan='%d' class='muted'>…… 其餘 %d 筆見 JSON</td></tr>"
                   % (len(fields), len(items) - limit))
    return "".join(out)


def render_html(ctx: Dict[str, Any]) -> str:
    nav = [("overview", "總覽 Overview"), ("registry", "URN 台帳"),
           ("contract", "介面契約 G15"), ("topology", "拓撲與爆炸半徑"),
           ("dup", "重複家族"), ("probe", "主動探針"), ("ssot", "同義字 SSOT"),
           ("env", "環境契約"), ("gates", "Gate 矩陣"), ("log", "執行日誌")]
    nav_html = "".join(
        "<a%s data-t='%s'>%s</a>" % (" class='active'" if i == 0 else "", key, label)
        for i, (key, label) in enumerate(nav))

    verdict = ctx["verdict"]
    sections = []

    sections.append("""
<section id="overview" class="on">
  <h2>全景總覽</h2>
  <p class="lede">%(root)s · %(stamp)s · %(mode)s · 只增不減，本次刪除 0 個檔案</p>
  <div class="cards">
    <div class="card"><div class="k">Verdict</div><div class="v %(vclass)s">%(verdict)s</div></div>
    <div class="card"><div class="k">Files</div><div class="v">%(files)d</div></div>
    <div class="card"><div class="k">URN Total</div><div class="v">%(urn_total)d</div></div>
    <div class="card"><div class="k">New URN</div><div class="v">%(urn_new)d</div></div>
    <div class="card"><div class="k">Contract Mismatch</div><div class="v fail">%(mismatch)d</div></div>
    <div class="card"><div class="k">Unresolved Calls</div><div class="v warn">%(unresolved)d</div></div>
    <div class="card"><div class="k">Cycles</div><div class="v fail">%(cycles)d</div></div>
    <div class="card"><div class="k">Duplicate Groups</div><div class="v warn">%(dupg)d</div></div>
  </div>
  <h2>命名空間分佈</h2>
  <table><tr><th>Namespace</th><th>Files</th></tr>%(ns_rows)s</table>
</section>""" % ctx)

    sections.append("""
<section id="registry">
  <h2>URN 永久台帳</h2>
  <p class="lede">單一發碼官 %s · 編號永不回收；檔案消失只轉 MISSING。</p>
  <table><tr><th>URN</th><th>Name</th><th>NS</th><th>SEC</th><th>State</th><th>First</th><th>Last</th><th>Path</th></tr>%s</table>
</section>""" % (URN_SELF, ctx["registry_rows"]))

    sections.append("""
<section id="contract">
  <h2>介面契約 G15</h2>
  <p class="lede">I1 來源即真理：參數一律由 AST / param() 萃取。宣告與原始碼不符即 FAIL。</p>
  <table><tr><th>URN</th><th>宣告有但原始碼沒有</th><th>原始碼有但沒宣告</th><th>ValidateSet 漂移</th><th>Path</th></tr>%s</table>
  <h2>未解析的呼叫（GAP-03）</h2>
  <table><tr><th>Caller</th><th>Caller 檔名</th><th>找不到的 Callee</th></tr>%s</table>
</section>""" % (ctx["mismatch_rows"], ctx["unresolved_rows"]))

    sections.append("""
<section id="topology">
  <h2>循環依賴（DFS 三色標記）</h2>
  <p class="lede">偵測到回邊即阻斷掛載。空表示拓撲可排序。</p>
  <table><tr><th>#</th><th>Cycle</th></tr>%s</table>
  <h2>九頭龍爆炸半徑</h2>
  <p class="lede">改動該節點時，會被連帶影響的上游節點數。數字越大越不該自動覆寫。</p>
  <table><tr><th>URN</th><th>Name</th><th>Blast Radius</th></tr>%s</table>
</section>""" % (ctx["cycle_rows"], ctx["blast_rows"]))

    sections.append("""
<section id="dup">
  <h2>重複家族</h2>
  <p class="lede">SHA-256 內容雜湊分組；非副本 → 最早修改 → 路徑序決定正本。僅檢視，不刪除。</p>
  <table><tr><th>Verdict</th><th>Name</th><th>Size</th><th>SHA</th><th>Path</th><th>Canonical</th></tr>%s</table>
</section>""" % ctx["dup_rows"])

    sections.append("""
<section id="probe">
  <h2>主動探針舉證</h2>
  <p class="lede">%s</p>
  <table><tr><th>Status</th><th>URN</th><th>Class</th><th>Latency ms</th><th>Signature</th><th>Error</th></tr>%s</table>
</section>""" % (esc(ctx["probe_note"]), ctx["probe_rows"]))

    sections.append("""
<section id="ssot">
  <h2>同義字 SSOT</h2>
  <p class="lede">自我測試 %d/%d 命中 · ASK 佇列 %d · 隔離 %d</p>
  <table><tr><th>Canonical</th><th>URN</th><th>同義字數</th><th>Regex</th></tr>%s</table>
</section>""" % (ctx["selftest_hit"], ctx["selftest_total"], ctx["ask_count"],
                 ctx["quarantine_count"], ctx["vocab_rows"]))

    sections.append("""
<section id="env">
  <h2>環境契約</h2>
  <p class="lede">執行期 %s · Python %s · 黃金律 numpy&gt;=1.24,&lt;2.0</p>
  <table><tr><th>項目</th><th>值</th></tr>%s</table>
  <h2>違規</h2>
  <table><tr><th>#</th><th>說明</th></tr>%s</table>
</section>""" % (esc(ctx["runtime_state"]), esc(ctx["python_version"]),
                 ctx["env_rows"], ctx["violation_rows"]))

    sections.append("""
<section id="gates">
  <h2>Gate 矩陣</h2>
  <p class="lede">%d 道閘門 · WARN %d · FAIL %d</p>
  <table><tr><th>Code</th><th>Gate</th><th>Status</th><th>Detail</th></tr>%s</table>
</section>""" % (ctx["gate_count"], ctx["warn_count"], ctx["fail_count"], ctx["gate_rows"]))

    sections.append("<section id='log'><h2>執行日誌</h2><pre>%s</pre></section>"
                    % esc("\n".join(LOG.lines)))

    return """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Central Governance Console %s</title>
<style>%s</style></head><body>
<div class="wrap">
<div class="left">
  <div class="brand"><div class="seal">理</div>
    <h1>Central Governance</h1>
    <div class="sub">%s · %s</div></div>
  <nav>%s</nav>
</div>
<div class="right">%s</div>
</div>
<script>
document.querySelectorAll('nav a').forEach(function(a){
  a.addEventListener('click', function(){
    document.querySelectorAll('nav a').forEach(function(x){x.classList.remove('active');});
    document.querySelectorAll('section').forEach(function(s){s.classList.remove('on');});
    a.classList.add('active');
    var el=document.getElementById(a.getAttribute('data-t'));
    if(el){el.classList.add('on');}
    window.scrollTo(0,0);
  });
});
</script></body></html>""" % (VERSION, CSS, URN_SELF, ctx["stamp"], nav_html, "".join(sections))


# ---------------------------------------------------------------------------
# §12  母系統中央總管
# ---------------------------------------------------------------------------

DEFAULT_PARAMETERS = {
    "system_governance": {
        "version": "1.0.0",
        "max_files": 40000,
        "max_ast_files": 4000,
        "cooldown_seconds": 3,
    },
    "subsystem_configs": {},
}


class MasterGovernanceManager:
    """頂層：一個管理者管全部。法律頒布者、註冊發碼官、環境協調員。"""

    def __init__(self, root: Path, dry_run: bool = True, probe: bool = False) -> None:
        self.root = root
        self.dry_run = dry_run
        self.probe_enabled = probe
        self.stamp = now_stamp()

        self.configs = root / "configs"
        self.logs = root / "logs"
        self.out = root / "output" / "SYS"
        for folder in (self.configs, self.logs, self.out):
            folder.mkdir(parents=True, exist_ok=True)

        self.param_path = self.configs / "system_parameters.json"
        if not self.param_path.exists():
            write_utf8(self.param_path, json.dumps(DEFAULT_PARAMETERS, ensure_ascii=False, indent=2))
            LOG.say("參數 SSOT 不存在，已建立預設：configs/system_parameters.json", "WARN")
        try:
            self.params = json.loads(read_text(self.param_path))
        except (json.JSONDecodeError, ValueError):
            LOG.say("參數 SSOT 無法解析，改用內建預設", "WARN")
            self.params = DEFAULT_PARAMETERS

        governance = self.params.get("system_governance", {})
        self.max_files = int(governance.get("max_files", 40000))
        self.max_ast = int(governance.get("max_ast_files", 4000))

        self.authority = URNAuthority(self.configs / "urn_registry.json",
                                      self.logs / "module_registry.log")
        self.contracts = ContractGovernor(self.configs / "interface_contracts.json")
        self.synonyms = SynonymSSOT(self.configs / "governance_vocab.json")
        self.environment = EnvironmentAudit(self.logs / "environment_audit.log")
        self.harness = ProbeHarness(self.logs / "probe_evidence.log")
        self.gates = GateMatrix()

        self.records: List[FileRecord] = []
        self.facts: Dict[str, ModuleFacts] = {}
        self.callgraph = CallGraphResolver()
        self.cycles: List[List[str]] = []
        self.blast: Dict[str, int] = {}
        self.dup_groups = 0
        self.dup_files = 0
        self.probe_results: List[Dict[str, Any]] = []
        self.parse_failures: List[Dict[str, str]] = []
        self.contract_status: Dict[str, str] = {}

    # -- 1. 掃描與發碼 ------------------------------------------------------
    def scan_and_register(self) -> None:
        LOG.say("全景掃描：%s" % self.root)
        self.records = discover([self.root], self.max_files,
                                exclude_dirs={self.configs, self.logs,
                                              self.root / "output", self.root / "temp"})
        LOG.say("掃描完成：%d 個檔案" % len(self.records), "OK")

        self.dup_groups, self.dup_files = resolve_duplicates(self.records)
        LOG.say("重複家族：%d 組，%d 份冗餘（僅檢視）" % (self.dup_groups, self.dup_files), "OK")

        touched: Set[str] = set()
        for record in self.records:
            key = record.rel.lower()
            touched.add(key)
            entry = self.authority.allocate(
                key=key, name=record.name, path=str(record.path),
                namespace=record.namespace, section=record.section, sha=record.sha)
            record.urn = entry.urn
            if record.verdict == "DUPLICATE":
                self.authority.set_state(entry.urn, "DUPLICATE",
                                         "canonical: " + record.canonical_of)
        gone = self.authority.mark_absent(touched)
        LOG.say("發碼：新增 %d，搬移 %d，消失 %d（標 MISSING 不刪）"
                % (self.authority.issued_this_run, self.authority.relocated, gone), "OK")

    # -- 2. AST 自省與契約 --------------------------------------------------
    def inspect_and_verify(self) -> None:
        targets = [r for r in self.records if r.ext in CODE_EXT][: self.max_ast]
        LOG.say("AST 自省：%d 個程式檔" % len(targets))
        seeds: List[Dict[str, Any]] = []
        for record in targets:
            facts = ASTInspector.inspect(record.path)
            self.facts[str(record.path)] = facts
            if not facts.parseable:
                self.parse_failures.append({
                    "urn": record.urn, "name": record.name,
                    "error": facts.error, "path": str(record.path)})
                continue
            self.contract_status[record.urn] = self.contracts.verify(record.urn, facts)
            seeds.append({
                "id": record.urn, "path": record.rel, "language": facts.language,
                "entrypoint": bool(facts.parameters),
                "parameters": facts.parameters, "calls": facts.calls,
                "grade": "V", "verified_at": self.stamp,
            })
            self.synonyms.register(record.family or record.name, record.urn,
                                   [record.name, record.path.stem])
        self.contracts.seed(seeds, self.dry_run)
        LOG.say("契約比對：檢查 %d 筆，不符 %d 筆"
                % (self.contracts.checked, len(self.contracts.mismatches)),
                "FAIL" if self.contracts.mismatches else "OK")

        self.callgraph.resolve(self.records, self.facts)
        LOG.say("呼叫解析：邊 %d，未解析 %d"
                % (len(self.callgraph.edges), len(self.callgraph.unresolved)), "OK")

        guard = TopologyGuard(self.callgraph.edges)
        self.cycles = guard.detect_cycles()
        self.blast = guard.blast_radius()
        LOG.say("拓撲：循環 %d 個，最大爆炸半徑 %d"
                % (len(self.cycles), max(self.blast.values()) if self.blast else 0),
                "FAIL" if self.cycles else "OK")

        hit, total = self.synonyms.selftest()
        LOG.say("同義字自我測試：%d/%d" % (hit, total),
                "OK" if hit == total else "WARN")

    # -- 3. 探針 ------------------------------------------------------------
    def run_probes(self) -> None:
        if not self.probe_enabled:
            LOG.say("探針未啟用（動態載入會執行模組頂層程式碼，需 --probe）", "WARN")
            return
        candidates = [r for r in self.records
                      if r.ext == ".py" and r.section == "MGR"][:50]
        LOG.say("主動探針：%d 個候選管理者" % len(candidates))
        for record in candidates:
            self.probe_results.extend(self.harness.probe_file(record.path))
        verified = sum(1 for r in self.probe_results if r["status"] == "VERIFIED_OPERATIONAL")
        LOG.say("探針舉證：%d/%d 通過" % (verified, len(self.probe_results)),
                "OK" if verified else "WARN")

    # -- 4. 閘門 ------------------------------------------------------------
    def evaluate_gates(self) -> None:
        env = self.environment.collect()
        add = self.gates.add

        add("G01", "URN_UNIQUE",
            "PASS" if self.authority.duplicate_urns() == 0 else "FAIL",
            "重複編號 %d 筆" % self.authority.duplicate_urns())
        add("G02", "APPEND_ONLY",
            "PASS", "本輪刪除 0 筆；消失一律標 MISSING")
        add("G03", "DUP_FAMILY_RESOLVED",
            "PASS" if self.dup_groups == 0 else "WARN",
            "%d 組同內容檔案，%d 份冗餘" % (self.dup_groups, self.dup_files))
        add("G04", "PY_AST_CLEAN",
            "PASS" if not self.parse_failures else "WARN",
            "%d 個程式檔無法解析" % len(self.parse_failures))
        add("G15", "CONTRACT_MATCHES_SOURCE",
            "PASS" if not self.contracts.mismatches else "FAIL",
            ("契約基準已播種，下次執行起生效" if self.contracts.seeded
             else "%d 筆宣告與原始碼不符" % len(self.contracts.mismatches)))
        add("G16", "CALLEE_RESOLVED",
            "PASS" if not self.callgraph.unresolved else "WARN",
            "%d 個呼叫目標找不到對應 URN" % len(self.callgraph.unresolved))
        add("G17", "NO_DEPENDENCY_CYCLE",
            "PASS" if not self.cycles else "FAIL",
            "%d 個循環依賴" % len(self.cycles))
        worst = max(self.blast.values()) if self.blast else 0
        add("G18", "HYDRA_BLAST_RADIUS",
            "PASS" if worst <= 3 else "WARN",
            "最大爆炸半徑 %d（>3 禁止自動覆寫）" % worst)
        add("G19", "SYNONYM_SELFTEST",
            "PASS" if self.synonyms.selftest_hit == self.synonyms.selftest_total else "WARN",
            "%d/%d 命中" % (self.synonyms.selftest_hit, self.synonyms.selftest_total))
        add("G20", "ENV_GOLDEN_RULE",
            "PASS" if not self.environment.violations else "WARN",
            "; ".join(self.environment.violations) or "numpy 釘選與禁用清單皆符合")
        add("G21", "PY_RUNTIME_REAL",
            "PASS" if env["runtime_state"] == "OK" else "FAIL",
            env["runtime_state"])
        if self.probe_enabled:
            verified = sum(1 for r in self.probe_results
                           if r["status"] == "VERIFIED_OPERATIONAL")
            add("G22", "PROBE_EVIDENCE",
                "PASS" if verified and verified == len(self.probe_results) else "WARN",
                "%d/%d 管理者通過搓啟動" % (verified, len(self.probe_results)))
        else:
            add("G22", "PROBE_EVIDENCE", "WARN", "未啟用 --probe，無舉證")
        add("G23", "DRY_RUN_DEFAULT",
            "PASS", "預設 dry-run；--commit 才寫入台帳" if self.dry_run else "本輪已 commit")

        LOG.say("Gate：%d 道，WARN %d，FAIL %d -> %s"
                % (len(self.gates.gates), self.gates.warnings,
                   self.gates.failures, self.gates.verdict),
                "FAIL" if self.gates.failures else ("WARN" if self.gates.warnings else "OK"))

    # -- 5. 輸出 ------------------------------------------------------------
    def emit(self, open_browser: bool = True) -> Path:
        registry_target = self.authority.commit(self.dry_run)
        vocab_target = self.synonyms.commit(self.dry_run)
        LOG.say("台帳 -> %s" % registry_target.name, "OK")
        LOG.say("詞彙 -> %s" % vocab_target.name, "OK")

        ns_counts: Dict[str, int] = {}
        for record in self.records:
            ns_counts[record.namespace] = ns_counts.get(record.namespace, 0) + 1

        blast_rows = []
        by_urn = {e.urn: e for e in self.authority.entries.values()}
        for urn, radius in sorted(self.blast.items(), key=lambda kv: -kv[1])[:100]:
            entry = by_urn.get(urn)
            blast_rows.append({"urn": urn, "name": entry.name if entry else "",
                               "radius": radius})

        env = self.environment.facts
        ctx: Dict[str, Any] = {
            "root": esc(str(self.root)), "stamp": self.stamp,
            "mode": "DRY-RUN（未寫入正式台帳）" if self.dry_run else "COMMITTED",
            "verdict": self.gates.verdict, "vclass": status_class(self.gates.verdict),
            "files": len(self.records),
            "urn_total": len(self.authority.entries),
            "urn_new": self.authority.issued_this_run,
            "mismatch": len(self.contracts.mismatches),
            "unresolved": len(self.callgraph.unresolved),
            "cycles": len(self.cycles), "dupg": self.dup_groups,
            "ns_rows": rows_html([{"ns": k, "n": v} for k, v in
                                  sorted(ns_counts.items(), key=lambda kv: -kv[1])],
                                 ["ns", "n"]),
            "registry_rows": rows_html(
                [{"urn": e.urn, "name": e.name, "ns": e.namespace, "sec": e.section,
                  "state": e.state, "first": e.first_seen, "last": e.last_seen,
                  "path": e.path}
                 for e in sorted(self.authority.entries.values(), key=lambda x: x.urn)],
                ["urn", "name", "ns", "sec", "state", "first", "last", "path"], "state", 800),
            "mismatch_rows": rows_html(
                [{"urn": m["urn"], "declared_only": m["declared_only"],
                  "source_only": m["source_only"], "choice_drift": m["choice_drift"],
                  "path": m["path"]} for m in self.contracts.mismatches],
                ["urn", "declared_only", "source_only", "choice_drift", "path"]),
            "unresolved_rows": rows_html(self.callgraph.unresolved,
                                         ["caller", "caller_name", "callee"]),
            "cycle_rows": rows_html(
                [{"n": i + 1, "cycle": " -> ".join(c)} for i, c in enumerate(self.cycles)],
                ["n", "cycle"]),
            "blast_rows": rows_html(blast_rows, ["urn", "name", "radius"]),
            "dup_rows": rows_html(
                [{"verdict": r.verdict, "name": r.name, "size": r.size,
                  "sha": r.sha[:12], "path": str(r.path), "canonical": r.canonical_of}
                 for r in self.records if r.verdict],
                ["verdict", "name", "size", "sha", "path", "canonical"], "verdict"),
            "probe_note": ("已啟用主動探針" if self.probe_enabled
                           else "未啟用。動態載入會執行模組頂層程式碼，請確認來源後再加 --probe"),
            "probe_rows": rows_html(self.probe_results,
                                    ["status", "urn", "class", "latency_ms",
                                     "signature", "error"], "status"),
            "selftest_hit": self.synonyms.selftest_hit,
            "selftest_total": self.synonyms.selftest_total,
            "ask_count": len(self.synonyms.ask_queue),
            "quarantine_count": len(self.synonyms.quarantine),
            "vocab_rows": rows_html(
                [{"canonical": k, "urn": v.get("urn", ""),
                  "n": len(v.get("synonyms", {})), "regex": v.get("regex_auto", "")}
                 for k, v in sorted(self.synonyms.vocab.items())[:300]],
                ["canonical", "urn", "n", "regex"]),
            "runtime_state": env.get("runtime_state", ""),
            "python_version": env.get("python", ""),
            "env_rows": rows_html(
                [{"k": "OS", "v": env.get("os", "")},
                 {"k": "Python", "v": env.get("python", "")},
                 {"k": "Executable", "v": env.get("executable", "")},
                 {"k": "Runtime State", "v": env.get("runtime_state", "")},
                 {"k": "CPU Cores", "v": env.get("cpu_cores", "")},
                 {"k": "VIRTUAL_ENV", "v": env.get("venv", "") or "(none)"},
                 {"k": "numpy", "v": env.get("numpy_version", "") or "(absent)"},
                 {"k": "Accelerators", "v": ", ".join(
                     "%s=%s" % (k, v) for k, v in env.get("accelerators", {}).items())}],
                ["k", "v"]),
            "violation_rows": rows_html(
                [{"n": i + 1, "detail": v} for i, v in enumerate(self.environment.violations)],
                ["n", "detail"]),
            "gate_count": len(self.gates.gates),
            "warn_count": self.gates.warnings, "fail_count": self.gates.failures,
            "gate_rows": rows_html(
                [{"code": g.code, "title": g.title, "status": g.status, "detail": g.detail}
                 for g in self.gates.gates],
                ["code", "title", "status", "detail"], "status"),
        }

        html_path = self.out / ("VIA_CentralGovernanceConsole_%s.html" % self.stamp)
        write_utf8(html_path, render_html(ctx))

        snapshot = {
            "schema": "VIA.GovernanceSnapshot", "spec": SPEC_VERSION,
            "authority": URN_SELF, "stamp": self.stamp, "root": str(self.root),
            "dry_run": self.dry_run, "verdict": self.gates.verdict,
            "files": len(self.records), "urn_total": len(self.authority.entries),
            "urn_issued": self.authority.issued_this_run,
            "contract_mismatches": self.contracts.mismatches,
            "unresolved_callees": self.callgraph.unresolved,
            "cycles": self.cycles, "blast_radius_top": blast_rows[:20],
            "duplicate_groups": self.dup_groups, "duplicate_files": self.dup_files,
            "parse_failures": self.parse_failures,
            "probe": self.probe_results, "environment": env,
            "gates": [asdict(g) for g in self.gates.gates],
        }
        json_path = self.out / ("governance_snapshot_%s.json" % self.stamp)
        write_utf8(json_path, json.dumps(snapshot, ensure_ascii=False, indent=1))
        write_utf8(self.logs / ("console_%s.log" % self.stamp), "\n".join(LOG.lines))

        LOG.say("主控台 -> %s" % html_path, "OK")
        LOG.say("快照   -> %s" % json_path, "OK")
        if open_browser:
            try:
                webbrowser.open(html_path.as_uri())
            except Exception:                                    # noqa: BLE001
                LOG.say("瀏覽器開啟略過", "WARN")
        return html_path

    # -- 6. 派發（兩層式的上對下介面）--------------------------------------
    def dispatch(self, target_urn: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """純記憶體內零拷貝派發。只認 URN，不認檔名。"""
        for record in self.probe_results:
            if record.get("urn") != target_urn:
                continue
            if record.get("status") != "VERIFIED_OPERATIONAL":
                raise RuntimeError("子系統 %s 未通過探針：%s"
                                   % (target_urn, record.get("status")))
        raise KeyError("查無已驗證的子系統管理者：%s（需先 --probe）" % target_urn)

    def run(self, open_browser: bool = True) -> str:
        started = time.perf_counter()
        LOG.say("%s VIA Central Governance Console %s 啟動" % (URN_SELF, VERSION), "OK")
        LOG.say("模式：%s" % ("DRY-RUN" if self.dry_run else "COMMIT"))
        self.scan_and_register()
        self.inspect_and_verify()
        self.run_probes()
        self.evaluate_gates()
        self.emit(open_browser)
        LOG.say("完成，耗時 %.1fs -> %s"
                % (time.perf_counter() - started, self.gates.verdict), "OK")
        return self.gates.verdict


# ---------------------------------------------------------------------------
# §13  CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="VIA_CentralGovernanceConsole.py",
        description="VIA-SYS-MGR-001 母系統中央總管（純 Python）")
    parser.add_argument("--root", default=".", help="VIA_SYSTEM_ROOT 路徑")
    parser.add_argument("--commit", action="store_true",
                        help="寫入正式台帳（預設 dry-run 只寫 .preview.json）")
    parser.add_argument("--probe", action="store_true",
                        help="啟用主動探針（會動態載入並執行管理者模組）")
    parser.add_argument("--no-open", action="store_true", help="不自動開啟瀏覽器")
    parser.add_argument("--json", action="store_true", help="只輸出裁決字串，供 CI 擷取")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print("root 不存在：%s" % root, file=sys.stderr)
        return 2
    manager = MasterGovernanceManager(root, dry_run=not args.commit, probe=args.probe)
    verdict = manager.run(open_browser=not args.no_open and not args.json)
    if args.json:
        print(json.dumps({"verdict": verdict, "stamp": manager.stamp}, ensure_ascii=False))
    return 0 if verdict != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
