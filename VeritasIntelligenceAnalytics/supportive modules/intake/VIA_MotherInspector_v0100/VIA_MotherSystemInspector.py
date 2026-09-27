#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA 母系統檢視／測試引擎（單一檔、唯讀、離線、非破壞）。

角色：Agent 2（Independent QA）— 禁止改寫任何生產檔。
方法：claude/charming-brown-2qaooh 優畫法
  · py／ts → precision AST（節點座標／Call／Name ctx）
  · ps1／html／json／via／yml／cmd → elastic 語意錨
  · 三輪：全景平行 → 拓撲序列 → 硬化回歸
  · 四區：MODULE／ENGINE／FUNCTION-LIB／OTHERS
  · 索引優先：只落地介面簽名、3 行摘要、精密錨點，不把全量源碼送入上下文

用法：
  python VIA_MotherSystemInspector.py
  python VIA_MotherSystemInspector.py --root C:\\Users\\tonyk\\VIA-VDF-VRN
  python VIA_MotherSystemInspector.py --root . --json-only
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import sys
import time
import traceback
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

ENGINE_ID = "VIA-VIA-ENG997"
ENGINE_NAME = "VIA Mother System Inspector"
ENGINE_VER = "v0100"
BRANCH_METHOD = "claude/charming-brown-2qaooh"
ZONES = ("MODULE", "ENGINE", "FUNCTION-LIB", "OTHERS")
SUBSYSTEMS = ("VIA", "VRN", "VDF", "VAP", "VETF")
ROUNDS = ("R1_PANORAMA_PARALLEL", "R2_TOPOLOGY_SEQUENCE", "R3_HARDENING")
SKIP_DIR_NAMES = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".tox",
    "dist",
    "build",
    ".vercel",
    "screenshots",
    ".tmp",
    "_via_inspector_selftest",
}
MOTHER_HINTS = (
    "VIA_CentralGovernance.py",
    "engine/via_unified_engine.py",
    "engine/via_python_accelerator.py",
    "engine/governance_engine.py",
    "config/ssot/VIA_SystemMaster.via",
    "scripts/VIA-Launch-Console.ps1",
    "launch.ps1",
)
LANGUAGE_TOOLS = {
    "py": {
        "mode": "precision",
        "parser": "ast.parse + NodeVisitor",
        "sees": "模組／類／函式簽名、Call、Name ctx、例外、可變預設、exec/eval",
        "misses": "動態 getattr、編碼錯誤需先行解碼",
        "fix": "parallel",
    },
    "ts": {
        "mode": "precision",
        "parser": "export／function 語意錨 + tsc --noEmit（若存在）",
        "sees": "匯出符號、函式名、import 邊",
        "misses": "完整 type narrowing／泛型展開",
        "fix": "parallel",
    },
    "tsx": {
        "mode": "precision",
        "parser": "export／function 語意錨",
        "sees": "元件匯出與 hook 呼叫名",
        "misses": "JSX 語意樹",
        "fix": "parallel",
    },
    "ps1": {
        "mode": "elastic",
        "parser": "VIA-ENTER-ENV 錨 + function／param 區塊",
        "sees": "進入環境區塊、函式名、Git writer 風險詞",
        "misses": "完整 PowerShell AST scope（需 PWSH Parser）",
        "fix": "sequence",
    },
    "cmd": {
        "mode": "elastic",
        "parser": "呼叫列彈性錨",
        "sees": "pwsh／python 轉接",
        "misses": "cmd 語意樹",
        "fix": "sequence",
    },
    "mjs": {
        "mode": "elastic",
        "parser": "export／import 正則",
        "sees": "ESM 匯出名稱",
        "misses": "動態 import()",
        "fix": "parallel",
    },
    "js": {
        "mode": "elastic",
        "parser": "function／export 正則",
        "sees": "函式名",
        "misses": "bundled minify",
        "fix": "parallel",
    },
    "json": {
        "mode": "elastic",
        "parser": "json.loads",
        "sees": "結構合法性、頂層鍵",
        "misses": "schema 語意（需 SSOT schema）",
        "fix": "parallel",
    },
    "via": {
        "mode": "elastic",
        "parser": "json.loads（SSOT 母檔慣例）",
        "sees": "SSOT 結構",
        "misses": "自訂 .via 非 JSON 變體",
        "fix": "sequence",
    },
    "yml": {
        "mode": "elastic",
        "parser": "key: 彈性錨",
        "sees": "workflow job／step 名",
        "misses": "完整 YAML 錨點合併",
        "fix": "sequence",
    },
    "yaml": {
        "mode": "elastic",
        "parser": "key: 彈性錨",
        "sees": "workflow job／step 名",
        "misses": "完整 YAML 錨點合併",
        "fix": "sequence",
    },
    "md": {
        "mode": "elastic",
        "parser": "標題錨",
        "sees": "H1–H3 契約標題",
        "misses": "內文一致性",
        "fix": "parallel",
    },
}


@dataclass
class Finding:
    severity: str  # P0 P1 P2 P3 INFO
    zone: str
    subsystem: str
    target: str
    lineno: int
    rule: str
    evidence: str
    solution: str
    fix_kind: str  # parallel | sequence


@dataclass
class ModuleIndex:
    module_id: str
    path: str
    lang: str
    zone: str
    subsystem: str
    sha256_12: str
    bytes: int
    lines: int
    parse_ok: bool
    signatures: list[str]
    summary: str
    anchors: list[str]


@dataclass
class Report:
    engine: str = ENGINE_NAME
    engine_id: str = ENGINE_ID
    version: str = ENGINE_VER
    method: str = BRANCH_METHOD
    agent: str = "Agent2_QA_READONLY"
    started_utc: str = ""
    elapsed_ms: int = 0
    root: str = ""
    verdict: str = "AMBER"
    files_scanned: int = 0
    parse_ok: int = 0
    parse_fail: int = 0
    finding_counts: dict[str, int] = field(default_factory=dict)
    language_matrix: list[dict[str, Any]] = field(default_factory=list)
    mother_matrix: list[dict[str, Any]] = field(default_factory=list)
    index: list[dict[str, Any]] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    rounds: list[str] = field(default_factory=lambda: list(ROUNDS))
    ok: bool = False


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _sha12(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:12]


def _subsystem(path: str) -> str:
    upper = path.upper()
    for name in SUBSYSTEMS:
        if name in upper:
            return name
    return "VIA"


def _zone(path: str) -> str:
    norm = path.replace("\\", "/").lower()
    name = Path(norm).name
    if "engine" in norm or name.startswith("via_centralgovernance") or "unified_engine" in name:
        return "ENGINE"
    if "functional modules" in norm or "function" in norm or "lib" in norm:
        return "FUNCTION-LIB"
    if name.endswith((".py", ".ps1", ".ts", ".tsx")) and (
        "/tests/" in f"/{norm}/" or name.startswith("test_")
    ):
        return "MODULE"
    if name.endswith((".py", ".ps1", ".ts", ".tsx", ".mjs")):
        return "MODULE"
    return "OTHERS"


def _lang(path: Path) -> str | None:
    ext = path.suffix.lower().lstrip(".")
    if ext in LANGUAGE_TOOLS:
        return ext
    return None


def _read_text(path: Path) -> tuple[str | None, str | None]:
    raw = path.read_bytes()
    for enc in ("utf-8", "utf-8-sig", "cp950", "big5", "latin-1"):
        try:
            return raw.decode(enc), None
        except UnicodeDecodeError:
            continue
    return None, "無法以 utf-8／cp950／latin-1 解碼"


def _iter_files(root: Path) -> Iterable[Path]:
    for item in root.rglob("*"):
        if not item.is_file():
            continue
        rel_dirs = item.relative_to(root).parts[:-1]
        if any(part in SKIP_DIR_NAMES for part in rel_dirs):
            continue
        if item.suffix.lower() == ".pyc":
            continue
        if item.stat().st_size > 8_000_000:
            continue
        yield item


def _sig_from_ast(tree: ast.AST) -> tuple[list[str], list[str]]:
    signatures: list[str] = []
    anchors: list[str] = []
    for node in tree.body if isinstance(tree, ast.Module) else []:
        if isinstance(node, ast.FunctionDef):
            args = [a.arg for a in node.args.args]
            signatures.append(f"def {node.name}({', '.join(args)}) L{node.lineno}")
            anchors.append(f"FNC:{node.name}@{node.lineno}")
        elif isinstance(node, ast.AsyncFunctionDef):
            signatures.append(f"async def {node.name}() L{node.lineno}")
            anchors.append(f"FNC:{node.name}@{node.lineno}")
        elif isinstance(node, ast.ClassDef):
            bases = [ast.unparse(b) if hasattr(ast, "unparse") else getattr(b, "id", "?") for b in node.bases]
            signatures.append(f"class {node.name}({', '.join(bases)}) L{node.lineno}")
            anchors.append(f"CLS:{node.name}@{node.lineno}")
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    signatures.append(f"  def {node.name}.{child.name}() L{child.lineno}")
                    if not child.name.startswith("_"):
                        anchors.append(f"MTH:{node.name}.{child.name}@{child.lineno}")
    return signatures[:40], anchors[:24]


def _summary_from_source(text: str, signatures: list[str]) -> str:
    doc = []
    for line in text.splitlines()[:40]:
        s = line.strip()
        if s.startswith('"""') or s.startswith("'''"):
            doc.append(s.strip("\"' "))
        elif s.startswith("#") and "VIA" in s.upper():
            doc.append(s.lstrip("# ").strip())
        if len(doc) >= 2:
            break
    head = "；".join(x for x in doc if x)[:160]
    sig = signatures[0] if signatures else "無頂層簽名"
    loc = f"{text.count(chr(10)) + 1} 行"
    return "／".join(part for part in (head or "無模組說明", sig, loc) if part)[:240]


class PyIssueVisitor(ast.NodeVisitor):
    def __init__(self, path: str, zone: str, subsystem: str) -> None:
        self.path = path
        self.zone = zone
        self.subsystem = subsystem
        self.findings: list[Finding] = []
        self.imports: list[str] = []
        self.calls: Counter[str] = Counter()
        self.has_main = False
        self.exec_hits = 0

    def _add(
        self,
        severity: str,
        lineno: int,
        rule: str,
        evidence: str,
        solution: str,
        fix_kind: str = "parallel",
    ) -> None:
        self.findings.append(
            Finding(
                severity=severity,
                zone=self.zone,
                subsystem=self.subsystem,
                target=self.path,
                lineno=lineno,
                rule=rule,
                evidence=evidence,
                solution=solution,
                fix_kind=fix_kind,
            )
        )

    def visit_Import(self, node: ast.Import) -> None:
        for alias in node.names:
            self.imports.append(alias.name.split(".")[0])
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.imports.append(node.module.split(".")[0])
        if node.names and any(n.name == "*" for n in node.names):
            self._add(
                "P1",
                node.lineno,
                "STAR_IMPORT",
                f"from {node.module or '?'} import *",
                "改為具名匯入；函式庫碼禁止 star import。",
            )
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        if node.name == "main":
            self.has_main = True
        for default in node.args.defaults:
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                self._add(
                    "P1",
                    node.lineno,
                    "MUTABLE_DEFAULT",
                    f"{node.name} 使用可變預設參數",
                    "改為 None，函式內再建立 list／dict。",
                )
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.generic_visit(node)

    def visit_ExceptHandler(self, node: ast.ExceptHandler) -> None:
        if node.type is None:
            self._add(
                "P1",
                node.lineno,
                "BARE_EXCEPT",
                "bare except:",
                "改 except Exception as exc: 並記錄／串接例外。",
            )
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call) -> None:
        name = ""
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            name = node.func.attr
        if name:
            self.calls[name] += 1
        # 只標內建 eval／exec／compile，不標 re.compile／ast.parse
        if isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "compile"}:
            self.exec_hits += 1
            self._add(
                "P0",
                node.lineno,
                "DYNAMIC_EXEC",
                f"呼叫 {node.func.id}()",
                "母系統治理路徑禁止動態執行；改為白名單分派或 ast.literal_eval。",
                "sequence",
            )
        self.generic_visit(node)


def inspect_python(rel: str, text: str, zone: str, subsystem: str) -> tuple[ModuleIndex, list[Finding]]:
    findings: list[Finding] = []
    data = text.encode("utf-8", errors="replace")
    try:
        tree = ast.parse(text, filename=rel)
        parse_ok = True
    except SyntaxError as exc:
        idx = ModuleIndex(
            module_id=f"{subsystem}:{Path(rel).stem}",
            path=rel,
            lang="py",
            zone=zone,
            subsystem=subsystem,
            sha256_12=_sha12(data),
            bytes=len(data),
            lines=text.count("\n") + 1,
            parse_ok=False,
            signatures=[],
            summary=f"AST 失敗：{exc.msg}",
            anchors=[f"ERR:{exc.lineno or 0}"],
        )
        findings.append(
            Finding(
                "P0",
                zone,
                subsystem,
                rel,
                exc.lineno or 0,
                "AST_SYNTAX",
                f"{exc.msg} (L{exc.lineno}:{exc.offset})",
                "先修語法再進 R2；Agent 1 於錨點切片修正，Agent 2 只重測。",
                "sequence",
            )
        )
        return idx, findings

    signatures, anchors = _sig_from_ast(tree)
    visitor = PyIssueVisitor(rel, zone, subsystem)
    visitor.visit(tree)
    findings.extend(visitor.findings)

    if len(text) > 200_000 and "CentralGovernance" in rel:
        findings.append(
            Finding(
                "P2",
                zone,
                subsystem,
                rel,
                1,
                "MOTHER_MONOLITH",
                f"母檔 {len(text):,} 字元，不利 Token 節約與錨點切片",
                "維持單一執行核心，但強制產出 governance_index（介面簽名＋3 行摘要＋精密錨點）；禁止整檔入 Prompt。",
                "sequence",
            )
        )
    if rel.endswith("engine/governance_engine.py") or rel.endswith("governance_engine.py"):
        if "attachments" in text and "glob" in text and "functional modules" not in text:
            findings.append(
                Finding(
                    "P1",
                    zone,
                    subsystem,
                    rel,
                    1,
                    "SCAN_SCOPE_TOO_NARROW",
                    "既有 governance_engine 只掃 attachments/*.py",
                    "改掃母檔＋engine／functional modules／tests／scripts；attachments 列為 OTHERS 附件區。",
                    "parallel",
                )
            )

    idx = ModuleIndex(
        module_id=f"{subsystem}:{Path(rel).stem}",
        path=rel,
        lang="py",
        zone=zone,
        subsystem=subsystem,
        sha256_12=_sha12(data),
        bytes=len(data),
        lines=text.count("\n") + 1,
        parse_ok=parse_ok,
        signatures=signatures[:12],
        summary=_summary_from_source(text, signatures),
        anchors=anchors[:12],
    )
    return idx, findings


_PS_FN = re.compile(r"^\s*function\s+([A-Za-z][\w-]*)", re.I | re.M)
_PS_GIT_WRITE = re.compile(r"\bgit\s+(add|commit|push|reset\s+--hard)\b", re.I)
_TS_EXPORT = re.compile(
    r"export\s+(?:async\s+)?(?:function|class|const|type|enum)\s+([A-Za-z_][\w]*)"
)
_MJS_EXPORT = re.compile(r"export\s+(?:async\s+)?(?:function|const|class|default)\s*([A-Za-z_][\w]*)?")


def inspect_elastic(rel: str, text: str, lang: str, zone: str, subsystem: str) -> tuple[ModuleIndex, list[Finding]]:
    findings: list[Finding] = []
    data = text.encode("utf-8", errors="replace")
    signatures: list[str] = []
    anchors: list[str] = []
    parse_ok = True

    if lang in {"json", "via"}:
        try:
            obj = json.loads(text)
            if isinstance(obj, dict):
                signatures = [f"KEY:{k}" for k in list(obj.keys())[:16]]
                anchors = signatures[:8]
            else:
                signatures = [f"JSON:{type(obj).__name__}"]
        except json.JSONDecodeError as exc:
            parse_ok = False
            findings.append(
                Finding(
                    "P0",
                    zone,
                    subsystem,
                    rel,
                    exc.lineno or 1,
                    "JSON_PARSE",
                    str(exc),
                    "SSOT／.via 必須是合法 JSON；先修結構再讓治理核心讀取。",
                    "sequence",
                )
            )
    elif lang == "ps1":
        signatures = [f"function {m.group(1)}" for m in _PS_FN.finditer(text)][:20]
        anchors = [f"FNC:{m.group(1)}" for m in _PS_FN.finditer(text)][:12]
        if "VIA-ENTER-ENV" not in text and "VIA_CentralGovernance.py" not in rel:
            findings.append(
                Finding(
                    "P1",
                    zone,
                    subsystem,
                    rel,
                    1,
                    "MISSING_VIA_ENTER_ENV",
                    "缺少 # ===== VIA-ENTER-ENV 區塊",
                    "自 scripts/VIA-Enter-Root.ps1 同步標準進入環境區塊；param() 之後、第一可執行敘述之前。",
                    "sequence",
                )
            )
        if _PS_GIT_WRITE.search(text) and "Launch-Console" not in rel:
            findings.append(
                Finding(
                    "P0",
                    zone,
                    subsystem,
                    rel,
                    1,
                    "HYDRA_GIT_WRITER",
                    "腳本含 git add／commit／push，違反單一 Writer 契約",
                    "刪除獨立 Git writer；僅 CGC-PROMOTE-WORKER-001 可寫。G38 fail-closed。",
                    "sequence",
                )
            )
    elif lang in {"ts", "tsx"}:
        signatures = [f"export {m.group(1)}" for m in _TS_EXPORT.finditer(text)][:20]
        anchors = signatures[:12]
    elif lang in {"mjs", "js"}:
        signatures = [f"export {m.group(1)}" for m in _MJS_EXPORT.finditer(text) if m.group(1)][:16]
        anchors = signatures[:8]
    elif lang in {"yml", "yaml"}:
        keys = re.findall(r"^([A-Za-z0-9_-]+):", text, re.M)
        signatures = [f"YKEY:{k}" for k in keys[:16]]
        anchors = signatures[:8]
    elif lang == "md":
        heads = re.findall(r"^#{1,3}\s+(.+)$", text, re.M)
        signatures = [f"H:{h.strip()}" for h in heads[:12]]
        anchors = signatures[:8]
    elif lang == "cmd":
        if "pwsh" not in text.lower() and "python" not in text.lower():
            findings.append(
                Finding(
                    "P3",
                    zone,
                    subsystem,
                    rel,
                    1,
                    "CMD_NO_CANONICAL_ENTRY",
                    "cmd 轉接未指向 pwsh／python 母入口",
                    "轉接至 scripts/VIA-Launch-Console.ps1 或 VIA-Enter-Root.ps1。",
                    "parallel",
                )
            )

    idx = ModuleIndex(
        module_id=f"{subsystem}:{Path(rel).stem}",
        path=rel,
        lang=lang,
        zone=zone,
        subsystem=subsystem,
        sha256_12=_sha12(data),
        bytes=len(data),
        lines=text.count("\n") + 1,
        parse_ok=parse_ok,
        signatures=signatures[:12],
        summary=_summary_from_source(text, signatures),
        anchors=anchors[:12],
    )
    return idx, findings


def inspect_file(root: Path, path: Path) -> tuple[ModuleIndex | None, list[Finding]]:
    lang = _lang(path)
    if lang is None:
        return None, []
    rel = path.relative_to(root).as_posix()
    zone = _zone(rel)
    subsystem = _subsystem(rel)
    text, err = _read_text(path)
    if text is None:
        finding = Finding(
            "P0",
            zone,
            subsystem,
            rel,
            1,
            "DECODE_FAIL",
            err or "decode",
            "轉 UTF-8 並保留 utf-8-sig 容錯。",
            "sequence",
        )
        return None, [finding]
    if lang == "py":
        return inspect_python(rel, text, zone, subsystem)
    return inspect_elastic(rel, text, lang, zone, subsystem)


def language_matrix(indexes: list[ModuleIndex], findings: list[Finding]) -> list[dict[str, Any]]:
    by_lang = Counter(i.lang for i in indexes)
    fail_by = Counter(f.target.split(".")[-1] for f in findings if f.rule in {"AST_SYNTAX", "JSON_PARSE"})
    rows = []
    for lang, spec in LANGUAGE_TOOLS.items():
        rows.append(
            {
                "語言": lang,
                "檔數": by_lang.get(lang, 0),
                "模式": spec["mode"],
                "工具": spec["parser"],
                "可見": spec["sees"],
                "盲區": spec["misses"],
                "修復序": spec["fix"],
                "解析失敗副檔名對照": fail_by.get(lang, 0),
            }
        )
    return rows


def mother_matrix(root: Path, indexes: list[ModuleIndex], findings: list[Finding]) -> list[dict[str, Any]]:
    rows = []
    by_path = {i.path: i for i in indexes}
    for hint in MOTHER_HINTS:
        present = (root / hint).exists()
        idx = by_path.get(hint)
        related = [f for f in findings if f.target == hint]
        worst = "PASS"
        if any(f.severity == "P0" for f in related):
            worst = "FAIL"
        elif any(f.severity in {"P1", "P2"} for f in related):
            worst = "WARN"
        elif not present:
            worst = "MISS"
        rows.append(
            {
                "母系統節點": hint,
                "存在": present,
                "區": idx.zone if idx else _zone(hint),
                "雜湊12": idx.sha256_12 if idx else "",
                "位元組": idx.bytes if idx else 0,
                "解析": idx.parse_ok if idx else present,
                "公開簽名數": len(idx.signatures) if idx else 0,
                "錨點數": len(idx.anchors) if idx else 0,
                "判定": worst,
                "摘要": idx.summary if idx else ("檔案缺失" if not present else "非掃描語言"),
            }
        )
    return rows


def verdict_of(findings: list[Finding], mother: list[dict[str, Any]]) -> tuple[str, bool]:
    if any(f.severity == "P0" for f in findings):
        return "RED", False
    if any(row["判定"] == "MISS" and "VIA_CentralGovernance.py" in row["母系統節點"] for row in mother):
        return "AMBER", False
    if any(f.severity == "P1" for f in findings):
        return "AMBER", False
    return "GREEN", True


SELFTEST_PY_OK = '''# VIA selftest fixture
"""Mother-like stub for inspector self-test."""

def run(capability: str, params: dict | None = None) -> dict:
    return {"ok": True, "capability": capability}

class Engine:
    def ping(self) -> str:
        return "pong"

if __name__ == "__main__":
    print(run("health"))
'''

SELFTEST_PY_BAD = '''# broken fixture
def broken(:
    pass
'''

SELFTEST_PS = """# ===== VIA-ENTER-ENV v0101 =====
# GREEN ENTER
# ===== /VIA-ENTER-ENV =====
function Invoke-Audit { param() }
"""


def write_selftest_tree(base: Path) -> Path:
    root = base / "_via_inspector_selftest"
    (root / "engine").mkdir(parents=True, exist_ok=True)
    (root / "config" / "ssot").mkdir(parents=True, exist_ok=True)
    (root / "scripts").mkdir(parents=True, exist_ok=True)
    (root / "VIA_CentralGovernance.py").write_text(SELFTEST_PY_OK, encoding="utf-8")
    (root / "engine" / "via_unified_engine.py").write_text(SELFTEST_PY_OK, encoding="utf-8")
    (root / "engine" / "via_python_accelerator.py").write_text(SELFTEST_PY_OK, encoding="utf-8")
    (root / "engine" / "governance_engine.py").write_text(
        "from pathlib import Path\nROOT = Path('.')\nlist((ROOT / 'attachments').glob('*.py'))\n",
        encoding="utf-8",
    )
    (root / "engine" / "broken_sample.py").write_text(SELFTEST_PY_BAD, encoding="utf-8")
    (root / "config" / "ssot" / "VIA_SystemMaster.via").write_text(
        json.dumps({"system": "VIA", "version": "v0220"}, ensure_ascii=False),
        encoding="utf-8",
    )
    (root / "scripts" / "VIA-Launch-Console.ps1").write_text(SELFTEST_PS, encoding="utf-8")
    (root / "launch.ps1").write_text(SELFTEST_PS, encoding="utf-8")
    (root / "scripts" / "orphan-writer.ps1").write_text("git push origin main\n", encoding="utf-8")
    return root


def scan_root(root: Path) -> Report:
    t0 = time.perf_counter()
    report = Report(started_utc=_now(), root=str(root.resolve()))
    indexes: list[ModuleIndex] = []
    findings: list[Finding] = []
    scanned = 0
    for path in _iter_files(root):
        scanned += 1
        idx, found = inspect_file(root, path)
        findings.extend(found)
        if idx is not None:
            indexes.append(idx)
    report.files_scanned = scanned
    report.parse_ok = sum(1 for i in indexes if i.parse_ok)
    report.parse_fail = sum(1 for i in indexes if not i.parse_ok)
    report.index = [asdict(i) for i in indexes[:400]]
    report.findings = [asdict(f) for f in findings]
    report.finding_counts = dict(Counter(f.severity for f in findings))
    report.language_matrix = language_matrix(indexes, findings)
    report.mother_matrix = mother_matrix(root, indexes, findings)
    report.verdict, report.ok = verdict_of(findings, report.mother_matrix)
    report.elapsed_ms = int((time.perf_counter() - t0) * 1000)
    return report


def render_zh(report: Report) -> str:
    lines = [
        f"{report.verdict}｜{report.engine} {report.version} 實測完成；掃描 {report.files_scanned} 檔、解析成功 {report.parse_ok}、失敗 {report.parse_fail}、耗時 {report.elapsed_ms} ms。",
        "",
        f"- 引擎：`{report.engine_id}` 方法 `{report.method}` 代理人 `{report.agent}`",
        f"- 根目錄：`{report.root}`",
        f"- 判定計數：{json.dumps(report.finding_counts, ensure_ascii=False)}",
        "",
        "## 語言工具矩陣",
        "",
        "| 語言 | 檔數 | 模式 | 工具 | 可見 | 盲區 | 修復序 |",
        "|---|---:|---|---|---|---|---|",
    ]
    for row in report.language_matrix:
        lines.append(
            f"| {row['語言']} | {row['檔數']} | {row['模式']} | {row['工具']} | {row['可見']} | {row['盲區']} | {row['修復序']} |"
        )
    lines += ["", "## 母系統節點矩陣", "", "| 節點 | 存在 | 區 | 雜湊12 | 位元組 | 解析 | 簽名 | 錨點 | 判定 | 摘要 |", "|---|---|---|---|---:|---|---:|---:|---|---|"]
    for row in report.mother_matrix:
        summary = str(row["摘要"]).replace("|", "/")
        lines.append(
            f"| `{row['母系統節點']}` | {row['存在']} | {row['區']} | {row['雜湊12']} | {row['位元組']} | {row['解析']} | {row['公開簽名數']} | {row['錨點數']} | {row['判定']} | {summary} |"
        )
    lines += ["", "## 問題與解法", ""]
    if not report.findings:
        lines.append("無發現。")
    else:
        lines += ["| 級 | 規則 | 目標 | 行 | 證據 | 解法 | 序 |", "|---|---|---|---:|---|---|---|"]
        for item in report.findings[:80]:
            ev = str(item["evidence"]).replace("|", "/").replace("\n", " ")
            sol = str(item["solution"]).replace("|", "/")
            lines.append(
                f"| {item['severity']} | {item['rule']} | `{item['target']}` | {item['lineno']} | {ev} | {sol} | {item['fix_kind']} |"
            )
    lines += [
        "",
        "## 索引切片（前 12 模組）",
        "",
        "| module_id | 路徑 | 語言 | 區 | 簽名 | 錨點 |",
        "|---|---|---|---|---|---|",
    ]
    for item in report.index[:12]:
        sig = "；".join(item["signatures"][:3]).replace("|", "/")
        anc = "；".join(item["anchors"][:3]).replace("|", "/")
        lines.append(
            f"| {item['module_id']} | `{item['path']}` | {item['lang']} | {item['zone']} | {sig} | {anc} |"
        )
    return "\n".join(lines) + "\n"


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="VIA 母系統唯讀 AST 檢視引擎")
    parser.add_argument("--root", type=str, default="", help="掃描根。空白則自測夾具")
    parser.add_argument("--out", type=str, default="", help="輸出目錄")
    parser.add_argument("--json-only", action="store_true")
    parser.add_argument("--selftest", action="store_true", help="強制使用內建夾具")
    return parser.parse_args(argv)


def resolve_root(args: argparse.Namespace) -> Path:
    if args.selftest or not args.root:
        return write_selftest_tree(Path.cwd() / "artifacts" if Path("artifacts").is_dir() else Path.cwd())
    root = Path(args.root).expanduser().resolve()
    if not root.exists():
        raise SystemExit(f"根目錄不存在：{root}")
    return root


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        root = resolve_root(args)
        report = scan_root(root)
    except Exception as exc:  # noqa: BLE001 — 引擎本身必須交出膠囊而非崩潰
        capsule = {
            "ok": False,
            "verdict": "RED",
            "error": exc.__class__.__name__,
            "detail": str(exc),
            "trace": traceback.format_exc().splitlines()[-6:],
        }
        print(json.dumps(capsule, ensure_ascii=False, indent=2))
        return 2

    if args.out:
        out_dir = Path(args.out).expanduser().resolve()
    elif Path.cwd().name == "artifacts":
        out_dir = Path.cwd()
    else:
        out_dir = Path.cwd() / "artifacts"
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        out_dir = Path.cwd()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_path = out_dir / f"VIA_MotherInspector_{stamp}.json"
    md_path = out_dir / f"VIA_MotherInspector_{stamp}.md"
    json_path.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    markdown = render_zh(report)
    md_path.write_text(markdown, encoding="utf-8")
    latest = out_dir / "VIA_MotherInspector.latest.json"
    latest.write_text(json.dumps(asdict(report), ensure_ascii=False, indent=2), encoding="utf-8")
    if args.json_only:
        print(json.dumps({"ok": report.ok, "verdict": report.verdict, "json": str(json_path)}, ensure_ascii=False))
    else:
        print(markdown)
        print(f"JSON {json_path}")
        print(f"MD   {md_path}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
