#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VIA_SubsystemManager.py
Veritas Intelligence Analytics · VAP / VDF / VRN Subsystem Manager

Role hierarchy
--------------
VIA_CentralGovernment.py
    -> final governance authority / SSOT / contracts / Hydra / gates

VIA_SuppoeriveToolkit_Manager.py
    -> supportive-tool discovery / health / capability routing

VIA_SubsystemManager.py
    -> VAP / VDF / VRN subsystem registration, contract validation,
       dependency ordering, parameter governance, data-flow routing,
       health inspection, cross-subsystem synchronization and run-local evidence.

Default policy
--------------
- no canonical mutation
- no direct import of unregistered subsystem engines
- no runtime execution unless explicitly authorized
- no network unless explicitly authorized
- no shared writes
- max 3 synchronized validation rounds
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

import argparse
import ast
import datetime as dt
import hashlib
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
import uuid
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path
from typing import Any, Mapping, Sequence

ENGINE = "VIA_SubsystemManager"
VERSION = "v001"
SCHEMA = "VIA-SUBSYSTEM/1.0"
MAX_ROUNDS = 3

DEFAULT_VIA_BASE = Path(r"C:\Users\tonyk\Downloads\VeritasIntelligenceAnalytics")
DEFAULT_RUN_ROOT = Path.home() / "Downloads" / "VIA_SubsystemManager_Runs"

SUBSYSTEMS: dict[str, dict[str, Any]] = {
    "VRN": {
        "name": "Veritas Report Nova",
        "role": "Document/PDF ingestion, extraction, normalization and research intelligence",
        "registry_id": "VIA-SYS-VRN-0001-v001",
        "priority": 10,
        "depends_on": [],
        "produces": [
            "document_text",
            "document_tables",
            "normalized_fields",
            "research_summary",
            "provenance",
            "confidence",
        ],
        "consumes": [
            "pdf",
            "docx",
            "xlsx",
            "html",
            "txt",
            "md",
            "image",
            "email",
        ],
        "candidate_files": [
            "VRN.py",
            "VeritasReportNova.py",
            "VIA_VRN.py",
            "VRN_Manager.py",
        ],
    },
    "VDF": {
        "name": "Veritas Data Forge",
        "role": "Structured market, macro, fundamental, ETF and financial data acquisition/normalization",
        "registry_id": "VIA-SYS-VDF-0001-v001",
        "priority": 20,
        "depends_on": [],
        "produces": [
            "market_data",
            "fundamental_data",
            "macro_data",
            "flow_data",
            "parquet",
            "duckdb_tables",
            "data_quality_evidence",
        ],
        "consumes": [
            "api",
            "web",
            "csv",
            "xlsx",
            "json",
            "parquet",
            "sql",
        ],
        "candidate_files": [
            "VDF.py",
            "VeritasDataForge.py",
            "VIA_VDF.py",
            "VDF_Manager.py",
        ],
    },
    "VAP": {
        "name": "Veritas Auto Plot",
        "role": "Visualization, chart specification, dashboard and analytical presentation",
        "registry_id": "VIA-SYS-VAP-0001-v001",
        "priority": 30,
        "depends_on": ["VDF", "VRN"],
        "produces": [
            "plot",
            "dashboard",
            "html",
            "png",
            "pdf",
            "chart_spec",
        ],
        "consumes": [
            "market_data",
            "fundamental_data",
            "macro_data",
            "flow_data",
            "research_summary",
            "normalized_fields",
        ],
        "candidate_files": [
            "VAP.py",
            "VeritasAutoPlot.py",
            "VIA_VAP.py",
            "VAP_Manager.py",
        ],
    },
}

DEFAULT_FLOW = [
    "VRN:INGEST",
    "VRN:NORMALIZE",
    "VDF:FETCH",
    "VDF:NORMALIZE",
    "VDF:VALIDATE",
    "VAP:MAP_CONTRACT",
    "VAP:PLOT",
    "VAP:EXPORT",
]

UNIVERSAL_INTERFACE_FIELDS = (
    "contract_id",
    "contract_version",
    "producer",
    "consumer",
    "payload_type",
    "payload_format",
    "schema_ref",
    "timestamp",
    "trace_id",
    "confidence",
    "provenance",
    "parameters",
    "data",
)


class RYG(str, Enum):
    GREEN = "GREEN"
    YELLOW = "YELLOW"
    RED = "RED"


class Gate(str, Enum):
    READY = "VIA_SUBSYSTEM_MANAGER_READY"
    READY_WITH_WARNINGS = "VIA_SUBSYSTEM_MANAGER_READY_WITH_WARNINGS"
    REVIEW_REQUIRED = "VIA_SUBSYSTEM_MANAGER_REVIEW_REQUIRED"
    BLOCKED = "VIA_SUBSYSTEM_MANAGER_BLOCKED"


@dataclass
class Policy:
    allow_import: bool = False
    allow_execute: bool = False
    allow_network: bool = False
    allow_canonical_mutation: bool = False
    max_rounds: int = 3
    max_parallel_read_lanes: int = 6
    timeout_seconds: int = 120


@dataclass
class SubsystemRecord:
    key: str
    name: str
    registry_id: str
    role: str
    root: str
    owner_file: str
    owner_status: str
    owner_sha256: str
    priority: int
    depends_on: list[str]
    consumes: list[str]
    produces: list[str]
    health: RYG = RYG.YELLOW
    allow_import: bool = False
    allow_execute: bool = False
    notes: list[str] = field(default_factory=list)


@dataclass
class ContractResult:
    producer: str
    consumer: str
    payload_type: str
    allowed: bool
    missing_fields: list[str]
    reason: str
    gate: RYG


@dataclass
class RoundResult:
    round_no: int
    name: str
    subsystem_rows: list[SubsystemRecord]
    contracts: list[ContractResult]
    findings: list[dict[str, Any]]
    dependency_gate: RYG
    contract_gate: RYG
    quantity_gate: RYG
    hydra_gate: RYG
    regression: bool
    issue_count: int
    blocker_count: int
    warning_count: int
    started_at: str
    completed_at: str


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    os.close(fd)
    tmp_path = Path(tmp)
    try:
        tmp_path.write_text(text, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            try:
                tmp_path.unlink()
            except Exception:
                pass


def write_json(path: Path, obj: Any) -> None:
    atomic_write(path, json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def read_text(path: Path) -> str:
    for enc in ("utf-8", "utf-8-sig", "cp950", "big5", "latin-1"):
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return path.read_bytes().decode("utf-8", errors="replace")


class EvidenceLedger:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, stage: str, payload: Any) -> str:
        prev = ""
        if self.path.exists():
            lines = [x for x in self.path.read_text(encoding="utf-8", errors="replace").splitlines() if x.strip()]
            if lines:
                prev = sha256_bytes(lines[-1].encode("utf-8"))
        entry = {
            "stage": stage,
            "timestamp": utc_now(),
            "previous_hash": prev,
            "payload": payload,
        }
        raw = json.dumps(entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
        entry["current_hash"] = sha256_bytes(raw.encode("utf-8"))
        with self.path.open("a", encoding="utf-8", newline="\n") as f:
            f.write(json.dumps(entry, ensure_ascii=False, separators=(",", ":"), default=str) + "\n")
        return entry["current_hash"]


class OwnerLocator:
    def __init__(self, via_base: Path):
        self.via_base = via_base

    def candidate_roots(self, key: str) -> list[Path]:
        names = [
            key,
            key.lower(),
            f"{key}_system",
            f"{key}_subsystem",
            f"Veritas{key}",
        ]
        roots = [self.via_base]
        for name in names:
            roots += [
                self.via_base / name,
                self.via_base / "systems" / name,
                self.via_base / "subsystems" / name,
                self.via_base / "modules" / name,
                self.via_base / "supportive modules" / name,
            ]
        seen = set()
        out = []
        for p in roots:
            s = str(p).lower()
            if s not in seen:
                seen.add(s)
                out.append(p)
        return out

    def locate(self, key: str, candidates: Sequence[str]) -> tuple[Path | None, list[str]]:
        hits: list[Path] = []
        notes: list[str] = []

        for root in self.candidate_roots(key):
            if not root.exists():
                continue
            for filename in candidates:
                p = root / filename
                if p.exists() and p.is_file():
                    hits.append(p)

        # bounded recursive recall search
        if not hits and self.via_base.exists():
            patterns = [
                re.compile(rf"(^|[_\-]){re.escape(key)}([_\-]|$)", re.I),
                re.compile(rf"Veritas.*{re.escape(key)}|{re.escape(key)}.*Manager", re.I),
            ]
            count = 0
            for p in self.via_base.rglob("*.py"):
                count += 1
                if count > 5000:
                    notes.append("recursive_search_capped_at_5000_files")
                    break
                if any(rx.search(p.stem) for rx in patterns):
                    hits.append(p)

        unique = []
        seen = set()
        for p in hits:
            s = str(p.resolve()).lower()
            if s not in seen:
                seen.add(s)
                unique.append(p)

        if not unique:
            return None, notes + ["owner_not_found"]
        if len(unique) == 1:
            return unique[0], notes + ["exact_single_owner_candidate"]

        # pick shortest path only as candidate, never canonical mutation
        unique.sort(key=lambda p: (len(p.parts), len(str(p))))
        notes.append(f"multiple_owner_candidates:{len(unique)}")
        notes.extend(str(p) for p in unique[:10])
        return unique[0], notes


class StaticValidator:
    @staticmethod
    def python(path: Path) -> tuple[bool, str]:
        try:
            src = read_text(path)
            tree = ast.parse(src, filename=str(path))
            compile(tree, str(path), "exec")
            return True, "AST_OK/COMPILE_OK/NO_IMPORT"
        except Exception as exc:
            return False, repr(exc)


class HydraScanner:
    PATTERNS = {
        "direct_import_other_subsystem": r"\b(import|from)\s+(VAP|VDF|VRN)\b",
        "dynamic_import": r"importlib\.import_module|__import__",
        "sys_path_mutation": r"sys\.path\.(append|insert)",
        "canonical_write_signal": r"open\([^)]*,\s*['\"]w|write_text\(|write_bytes\(",
        "network_direct": r"\b(requests|httpx|aiohttp|urllib)\.",
    }

    def scan(self, path: Path | None) -> dict[str, Any]:
        if path is None or not path.exists():
            return {"gate": RYG.RED.value, "flags": {"missing": True}}
        text = read_text(path)
        flags = {k: bool(re.search(v, text, re.I)) for k, v in self.PATTERNS.items()}
        red = flags["direct_import_other_subsystem"]
        gate = RYG.RED if red else (RYG.YELLOW if any(flags.values()) else RYG.GREEN)
        return {"gate": gate.value, "flags": flags}


class ContractGovernor:
    def allowed_payloads(self, producer: str, consumer: str) -> set[str]:
        p = set(SUBSYSTEMS[producer]["produces"])
        c = set(SUBSYSTEMS[consumer]["consumes"])
        return p & c

    def validate_pair(self, producer: str, consumer: str) -> ContractResult:
        allowed = self.allowed_payloads(producer, consumer)
        if producer == consumer:
            return ContractResult(
                producer, consumer, "*", True, [], "same_subsystem_internal", RYG.GREEN
            )
        if not allowed:
            return ContractResult(
                producer, consumer, "", False, [],
                "no_declared_payload_intersection", RYG.YELLOW
            )
        return ContractResult(
            producer, consumer, ",".join(sorted(allowed)), True, [],
            "declared_contract_intersection", RYG.GREEN
        )

    def envelope(
        self,
        producer: str,
        consumer: str,
        payload_type: str,
        payload_format: str,
        data: Any,
        parameters: Mapping[str, Any] | None = None,
        schema_ref: str = "",
        confidence: str = "UNKNOWN",
        provenance: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "contract_id": f"VIA-CONTRACT-{producer}-{consumer}",
            "contract_version": "1.0",
            "producer": producer,
            "consumer": consumer,
            "payload_type": payload_type,
            "payload_format": payload_format,
            "schema_ref": schema_ref,
            "timestamp": utc_now(),
            "trace_id": uuid.uuid4().hex,
            "confidence": confidence,
            "provenance": dict(provenance or {}),
            "parameters": dict(parameters or {}),
            "data": data,
        }

    def validate_envelope(self, env: Mapping[str, Any]) -> tuple[bool, list[str]]:
        missing = [k for k in UNIVERSAL_INTERFACE_FIELDS if k not in env]
        return not missing, missing


class ParameterGovernor:
    """
    Normalizes common VIA subsystem parameters without assuming one engine's CLI.
    """

    COMMON_DEFAULTS = {
        "start_date": "2021-01-01",
        "end_date": "LATEST",
        "update_mode": "INCREMENTAL",
        "output_format": "PARQUET",
        "evidence_mode": "APPEND_ONLY",
        "network": False,
        "parallel_read_lanes": 6,
        "canonical_mutation": False,
    }

    def normalize(self, subsystem: str, params: Mapping[str, Any] | None = None) -> dict[str, Any]:
        out = dict(self.COMMON_DEFAULTS)
        out.update(dict(params or {}))
        out["subsystem"] = subsystem
        out["normalized_at"] = utc_now()

        if out["parallel_read_lanes"] > 6:
            out["parallel_read_lanes"] = 6
            out["parallel_lanes_clamped"] = True
        else:
            out["parallel_lanes_clamped"] = False

        if subsystem == "VAP":
            out.setdefault("render_mode", "HTML")
            out.setdefault("theme", "LIGHT")
            out.setdefault("canonical_write", False)
        elif subsystem == "VDF":
            out.setdefault("grain", "AUTO")
            out.setdefault("duckdb", True)
            out.setdefault("parquet", True)
        elif subsystem == "VRN":
            out.setdefault("ocr_mode", "AUTO")
            out.setdefault("preserve_layout", True)
            out.setdefault("confidence_required", True)
        return out


class HtmlRenderer:
    @staticmethod
    def e(v: Any) -> str:
        return html.escape("" if v is None else str(v))

    @classmethod
    def render(
        cls,
        run_id: str,
        final_gate: str,
        rounds: Sequence[RoundResult],
        route_matrix: Sequence[Mapping[str, Any]],
    ) -> str:
        round_rows = ""
        for r in rounds:
            round_rows += (
                f"<tr><td>{r.round_no}</td><td>{cls.e(r.name)}</td>"
                f"<td>{r.issue_count}</td><td>{r.blocker_count}</td>"
                f"<td>{r.warning_count}</td><td>{cls.e(r.hydra_gate.value)}</td>"
                f"<td>{cls.e(r.contract_gate.value)}</td><td>{cls.e(r.dependency_gate.value)}</td>"
                f"<td>{cls.e(r.regression)}</td></tr>"
            )

        route_rows = "".join(
            f"<tr><td>{cls.e(x['producer'])}</td><td>{cls.e(x['consumer'])}</td>"
            f"<td>{cls.e(x['payloads'])}</td><td>{cls.e(x['gate'])}</td></tr>"
            for x in route_matrix
        )

        return f"""<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8">
<title>VIA Subsystem Manager</title>
<style>
body{{font-family:Segoe UI,Arial;background:#f7f8f5;color:#263238;padding:22px}}
main{{max-width:1500px;margin:auto}}.card{{background:#fff;border:1px solid #d9ddd8;border-radius:12px;padding:16px;margin-bottom:12px}}
table{{width:100%;border-collapse:collapse}}th,td{{padding:8px;border-bottom:1px solid #e3e6e1;text-align:left}}
th{{background:#f1f4ef}}.mono{{font-family:Consolas,monospace;font-size:11px}}
</style></head><body><main>
<div class="card"><h1>VIA · VAP / VDF / VRN Subsystem Manager</h1>
<div>Run: <span class="mono">{cls.e(run_id)}</span></div><div>Final Gate: <b>{cls.e(final_gate)}</b></div></div>
<div class="card"><h2>Three-Round Governance</h2><table>
<tr><th>Round</th><th>Name</th><th>Issues</th><th>Blockers</th><th>Warnings</th><th>Hydra</th><th>Contract</th><th>Dependency</th><th>Regression</th></tr>
{round_rows}</table></div>
<div class="card"><h2>Cross-Subsystem Contract Matrix</h2><table>
<tr><th>Producer</th><th>Consumer</th><th>Payloads</th><th>Gate</th></tr>{route_rows}</table></div>
</main></body></html>"""


class VIASubsystemManager:
    def __init__(
        self,
        via_base: Path = DEFAULT_VIA_BASE,
        run_root: Path = DEFAULT_RUN_ROOT,
        policy: Policy | None = None,
    ):
        self.via_base = Path(via_base)
        self.run_root = Path(run_root)
        self.policy = policy or Policy()

        self.run_id = "RUN_" + dt.datetime.now().strftime("%Y%m%d_%H%M%S") + "_VIA_SUB_" + uuid.uuid4().hex[:6].upper()
        self.run_dir = self.run_root / self.run_id
        self.run_dir.mkdir(parents=True, exist_ok=True)

        self.ledger = EvidenceLedger(self.run_dir / "VIA_SUBSYSTEM_MANAGER_EVIDENCE.jsonl")
        self.locator = OwnerLocator(self.via_base)
        self.contracts = ContractGovernor()
        self.parameters = ParameterGovernor()
        self.hydra = HydraScanner()

        self.records: dict[str, SubsystemRecord] = {}
        self.rounds: list[RoundResult] = []
        self.baseline_hashes: dict[str, str] = {}

    def discover_subsystems(self) -> list[SubsystemRecord]:
        rows = []
        for key, spec in SUBSYSTEMS.items():
            owner, notes = self.locator.locate(key, spec["candidate_files"])
            if owner is None:
                status = "OWNER_NOT_FOUND"
                sha = ""
                owner_path = ""
                root = str(self.via_base)
                health = RYG.RED
            else:
                ok, detail = StaticValidator.python(owner)
                notes.append(detail)
                status = "STATIC_OK" if ok else "STATIC_FAIL"
                sha = sha256_bytes(owner.read_bytes())
                owner_path = str(owner)
                root = str(owner.parent)
                health = RYG.GREEN if ok else RYG.RED

            rec = SubsystemRecord(
                key=key,
                name=spec["name"],
                registry_id=spec["registry_id"],
                role=spec["role"],
                root=root,
                owner_file=owner_path,
                owner_status=status,
                owner_sha256=sha,
                priority=spec["priority"],
                depends_on=list(spec["depends_on"]),
                consumes=list(spec["consumes"]),
                produces=list(spec["produces"]),
                health=health,
                allow_import=bool(self.policy.allow_import and status == "STATIC_OK"),
                allow_execute=bool(self.policy.allow_execute and status == "STATIC_OK"),
                notes=notes,
            )
            rows.append(rec)

        self.records = {x.key: x for x in rows}
        self.ledger.append("DISCOVER_SUBSYSTEMS", [asdict(x) for x in rows])
        return rows

    def dependency_order(self) -> list[str]:
        if not self.records:
            self.discover_subsystems()

        indegree = {k: 0 for k in self.records}
        graph = {k: [] for k in self.records}

        for key, rec in self.records.items():
            for dep in rec.depends_on:
                if dep in self.records:
                    graph[dep].append(key)
                    indegree[key] += 1

        ready = sorted(
            [k for k, deg in indegree.items() if deg == 0],
            key=lambda x: self.records[x].priority
        )
        order = []
        while ready:
            node = ready.pop(0)
            order.append(node)
            for nxt in graph[node]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    ready.append(nxt)
                    ready.sort(key=lambda x: self.records[x].priority)

        if len(order) != len(self.records):
            raise RuntimeError("Subsystem dependency cycle detected.")
        return order

    def contract_matrix(self) -> list[ContractResult]:
        rows = []
        for producer in SUBSYSTEMS:
            for consumer in SUBSYSTEMS:
                rows.append(self.contracts.validate_pair(producer, consumer))
        return rows

    def route_matrix(self) -> list[dict[str, Any]]:
        rows = []
        for c in self.contract_matrix():
            rows.append({
                "producer": c.producer,
                "consumer": c.consumer,
                "payloads": c.payload_type,
                "allowed": c.allowed,
                "gate": c.gate.value,
                "reason": c.reason,
            })
        return rows

    def dependency_gate(self) -> tuple[RYG, list[dict[str, Any]]]:
        findings = []
        gate = RYG.GREEN
        for key, rec in self.records.items():
            for dep in rec.depends_on:
                dep_rec = self.records.get(dep)
                if dep_rec is None or dep_rec.health == RYG.RED:
                    gate = RYG.RED
                    findings.append({
                        "category": "DEPENDENCY",
                        "severity": RYG.RED.value,
                        "subsystem": key,
                        "message": f"{key} depends on unavailable/unhealthy {dep}",
                    })
        return gate, findings

    def hydra_gate(self) -> tuple[RYG, list[dict[str, Any]]]:
        rows = []
        gate = RYG.GREEN
        for rec in self.records.values():
            scan = self.hydra.scan(Path(rec.owner_file)) if rec.owner_file else {"gate": RYG.RED.value, "flags": {"missing": True}}
            level = RYG(scan["gate"])
            if level == RYG.RED:
                gate = RYG.RED
            elif level == RYG.YELLOW and gate == RYG.GREEN:
                gate = RYG.YELLOW
            if level != RYG.GREEN:
                rows.append({
                    "category": "HYDRA",
                    "severity": level.value,
                    "subsystem": rec.key,
                    "message": "Hydra pattern(s) require review.",
                    "flags": scan["flags"],
                })
        return gate, rows

    def quantity_gate(self) -> tuple[RYG, list[dict[str, Any]]]:
        existing = sum(1 for x in self.records.values() if x.owner_file)
        if existing == 3:
            return RYG.GREEN, []
        return RYG.RED, [{
            "category": "QUANTITY",
            "severity": RYG.RED.value,
            "subsystem": "ALL",
            "message": f"Subsystem owner files found: {existing}/3",
        }]

    def contract_gate(self) -> tuple[RYG, list[dict[str, Any]]]:
        matrix = self.contract_matrix()
        warnings = []
        gate = RYG.GREEN
        for c in matrix:
            if c.producer == c.consumer:
                continue
            # Not every pair must exchange data, so missing intersection is warning only.
            if not c.allowed:
                gate = RYG.YELLOW if gate == RYG.GREEN else gate
                warnings.append({
                    "category": "CONTRACT",
                    "severity": RYG.YELLOW.value,
                    "subsystem": f"{c.producer}->{c.consumer}",
                    "message": c.reason,
                })
        return gate, warnings

    def run_round(self, round_no: int, previous: RoundResult | None = None) -> RoundResult:
        started = utc_now()
        rows = self.discover_subsystems()

        dep_gate, dep_findings = self.dependency_gate()
        hydra_gate, hydra_findings = self.hydra_gate()
        qty_gate, qty_findings = self.quantity_gate()
        contract_gate, contract_findings = self.contract_gate()

        findings = dep_findings + hydra_findings + qty_findings + contract_findings

        current_hashes = {k: r.owner_sha256 for k, r in self.records.items()}
        if round_no == 1:
            self.baseline_hashes = dict(current_hashes)
        else:
            drift = {
                k: {"baseline": self.baseline_hashes.get(k, ""), "current": v}
                for k, v in current_hashes.items()
                if self.baseline_hashes.get(k, "") != v
            }
            if drift:
                findings.append({
                    "category": "HASH_DRIFT",
                    "severity": RYG.RED.value,
                    "subsystem": "ALL",
                    "message": "Subsystem owner hash changed during governance run.",
                    "drift": drift,
                })
                hydra_gate = RYG.RED

        issue_count = len(findings)
        blockers = sum(1 for x in findings if x["severity"] == RYG.RED.value)
        warnings = sum(1 for x in findings if x["severity"] == RYG.YELLOW.value)
        regression = bool(previous and issue_count > previous.issue_count)

        result = RoundResult(
            round_no=round_no,
            name={
                1: "R1 Comprehensive Safe Analysis",
                2: "R2 Sequential Dependency Validation",
                3: "R3 Final Hardening",
            }[round_no],
            subsystem_rows=rows,
            contracts=self.contract_matrix(),
            findings=findings,
            dependency_gate=dep_gate,
            contract_gate=contract_gate,
            quantity_gate=qty_gate,
            hydra_gate=hydra_gate,
            regression=regression,
            issue_count=issue_count,
            blocker_count=blockers,
            warning_count=warnings,
            started_at=started,
            completed_at=utc_now(),
        )
        self.rounds.append(result)

        rd = self.run_dir / f"R{round_no}"
        write_json(rd / "SUBSYSTEM_REGISTRY.json", [asdict(x) for x in rows])
        write_json(rd / "CONTRACT_MATRIX.json", [asdict(x) for x in result.contracts])
        write_json(rd / "FINDINGS.json", findings)
        write_json(rd / "ROUND_RESULT.json", asdict(result))
        self.ledger.append(f"ROUND_{round_no}", asdict(result))
        return result

    def final_gate(self) -> Gate:
        if not self.rounds:
            return Gate.BLOCKED
        last = self.rounds[-1]
        if any(r.regression for r in self.rounds):
            return Gate.BLOCKED
        if last.blocker_count > 0:
            return Gate.BLOCKED
        if last.warning_count > 0:
            return Gate.READY_WITH_WARNINGS
        if any(x == RYG.YELLOW for x in (
            last.dependency_gate, last.contract_gate, last.quantity_gate, last.hydra_gate
        )):
            return Gate.REVIEW_REQUIRED
        return Gate.READY

    def run(self) -> dict[str, Any]:
        previous = None
        for i in range(1, min(MAX_ROUNDS, max(1, self.policy.max_rounds)) + 1):
            previous = self.run_round(i, previous)

        route = self.route_matrix()
        final_gate = self.final_gate()

        output = {
            "engine": ENGINE,
            "version": VERSION,
            "schema": SCHEMA,
            "run_id": self.run_id,
            "run_dir": str(self.run_dir),
            "final_gate": final_gate.value,
            "policy": asdict(self.policy),
            "dependency_order": self.dependency_order() if self.records else [],
            "subsystems": [asdict(x) for x in self.records.values()],
            "route_matrix": route,
            "rounds": [asdict(x) for x in self.rounds],
            "default_flow": DEFAULT_FLOW,
            "canonical_mutation": False,
            "generated_at": utc_now(),
        }

        write_json(self.run_dir / "VIA_SUBSYSTEM_MANAGER_FINAL.json", output)
        write_json(self.run_dir / "VIA_SUBSYSTEM_ROUTE_MATRIX.json", route)
        write_json(
            self.run_dir / "VIA_SUBSYSTEM_DEFAULT_PARAMETERS.json",
            {k: self.parameters.normalize(k) for k in SUBSYSTEMS},
        )

        atomic_write(
            self.run_dir / "VIA_SUBSYSTEM_MANAGER.html",
            HtmlRenderer.render(self.run_id, final_gate.value, self.rounds, route)
        )
        self.ledger.append("FINAL", output)
        return output

    def route_payload(
        self,
        producer: str,
        consumer: str,
        payload_type: str,
        payload_format: str,
        data: Any,
        parameters: Mapping[str, Any] | None = None,
        schema_ref: str = "",
        confidence: str = "UNKNOWN",
        provenance: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        producer = producer.upper()
        consumer = consumer.upper()
        if producer not in SUBSYSTEMS or consumer not in SUBSYSTEMS:
            return {"accepted": False, "reason": "UNKNOWN_SUBSYSTEM"}

        declared = self.contracts.allowed_payloads(producer, consumer)
        if producer != consumer and payload_type not in declared:
            return {
                "accepted": False,
                "reason": "PAYLOAD_TYPE_NOT_DECLARED_FOR_ROUTE",
                "allowed_payloads": sorted(declared),
            }

        env = self.contracts.envelope(
            producer, consumer, payload_type, payload_format, data,
            parameters=self.parameters.normalize(producer, parameters),
            schema_ref=schema_ref,
            confidence=confidence,
            provenance=provenance,
        )
        ok, missing = self.contracts.validate_envelope(env)
        result = {
            "accepted": ok,
            "missing_fields": missing,
            "execution": "NOT_EXECUTED",
            "envelope": env,
        }
        self.ledger.append("ROUTE_PAYLOAD", result)
        return result

    def controlled_import(self, subsystem: str) -> dict[str, Any]:
        key = subsystem.upper()
        rec = self.records.get(key)
        if rec is None:
            return {"ok": False, "reason": "SUBSYSTEM_NOT_REGISTERED"}
        if not self.policy.allow_import:
            return {"ok": False, "reason": "IMPORT_NOT_AUTHORIZED"}
        if not rec.owner_file or rec.owner_status != "STATIC_OK":
            return {"ok": False, "reason": "OWNER_NOT_GREEN"}
        if not self.policy.allow_execute:
            return {"ok": False, "reason": "EXECUTION_NOT_AUTHORIZED"}

        module_name = f"via_subsystem_{key.lower()}_{uuid.uuid4().hex[:8]}"
        spec = importlib.util.spec_from_file_location(module_name, rec.owner_file)
        if spec is None or spec.loader is None:
            return {"ok": False, "reason": "SPEC_CREATION_FAILED"}
        module = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(module)
            self.ledger.append("CONTROLLED_IMPORT", {"subsystem": key, "ok": True})
            return {"ok": True, "module_name": module_name}
        except Exception as exc:
            self.ledger.append("CONTROLLED_IMPORT", {"subsystem": key, "ok": False, "error": repr(exc)})
            return {"ok": False, "reason": "IMPORT_EXCEPTION", "error": repr(exc)}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="VIA VAP/VDF/VRN Subsystem Manager")
    p.add_argument("--via-base", default=str(DEFAULT_VIA_BASE))
    p.add_argument("--run-root", default=str(DEFAULT_RUN_ROOT))
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--allow-import", action="store_true")
    p.add_argument("--allow-execute", action="store_true")
    p.add_argument("--allow-network", action="store_true")
    p.add_argument("--allow-canonical-mutation", action="store_true")

    sub = p.add_subparsers(dest="command")
    sub.add_parser("run")
    sub.add_parser("discover")
    sub.add_parser("contracts")
    sub.add_parser("order")

    route = sub.add_parser("route")
    route.add_argument("--producer", required=True)
    route.add_argument("--consumer", required=True)
    route.add_argument("--payload-type", required=True)
    route.add_argument("--payload-format", required=True)
    route.add_argument("--data-json", default="{}")
    route.add_argument("--schema-ref", default="")
    route.add_argument("--confidence", default="UNKNOWN")

    imp = sub.add_parser("import")
    imp.add_argument("subsystem")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    ns = build_parser().parse_args(argv)

    policy = Policy(
        allow_import=ns.allow_import,
        allow_execute=ns.allow_execute,
        allow_network=ns.allow_network,
        allow_canonical_mutation=ns.allow_canonical_mutation,
        max_rounds=max(1, min(MAX_ROUNDS, ns.rounds)),
    )

    mgr = VIASubsystemManager(
        via_base=Path(ns.via_base),
        run_root=Path(ns.run_root),
        policy=policy,
    )

    cmd = ns.command or "run"

    try:
        if cmd == "run":
            result = mgr.run()
            print(json.dumps({
                "engine": ENGINE,
                "version": VERSION,
                "run_id": mgr.run_id,
                "gate": result["final_gate"],
                "dependency_order": result["dependency_order"],
                "run_dir": str(mgr.run_dir),
                "html": str(mgr.run_dir / "VIA_SUBSYSTEM_MANAGER.html"),
            }, ensure_ascii=False, indent=2))
            return 0 if result["final_gate"] != Gate.BLOCKED.value else 2

        if cmd == "discover":
            rows = mgr.discover_subsystems()
            print(json.dumps([asdict(x) for x in rows], ensure_ascii=False, indent=2))
            return 0

        if cmd == "contracts":
            print(json.dumps(mgr.route_matrix(), ensure_ascii=False, indent=2))
            return 0

        if cmd == "order":
            mgr.discover_subsystems()
            print(json.dumps({"order": mgr.dependency_order()}, ensure_ascii=False, indent=2))
            return 0

        if cmd == "route":
            try:
                data = json.loads(ns.data_json)
            except json.JSONDecodeError as exc:
                print(json.dumps({"accepted": False, "error": repr(exc)}))
                return 2
            result = mgr.route_payload(
                ns.producer, ns.consumer, ns.payload_type, ns.payload_format, data,
                schema_ref=ns.schema_ref, confidence=ns.confidence
            )
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result.get("accepted") else 2

        if cmd == "import":
            mgr.discover_subsystems()
            result = mgr.controlled_import(ns.subsystem)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            return 0 if result.get("ok") else 2

        return 2

    except Exception as exc:
        failure = {
            "ok": False,
            "engine": ENGINE,
            "version": VERSION,
            "run_id": mgr.run_id,
            "error": repr(exc),
            "traceback": traceback.format_exc(),
            "run_dir": str(mgr.run_dir),
        }
        try:
            write_json(mgr.run_dir / "VIA_SUBSYSTEM_MANAGER_FATAL.json", failure)
            mgr.ledger.append("FATAL", failure)
        except Exception:
            pass
        print(json.dumps(failure, ensure_ascii=False, indent=2))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
