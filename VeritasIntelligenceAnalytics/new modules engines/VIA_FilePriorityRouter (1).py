#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA-SYS-ENG-003 : File Priority Router (全景引擎的 L0 + L1 層).

在解析之前先分類與排序。垃圾檔案不是靠「等一下再處理」擋掉的，
是靠「一開始就不進佇列」擋掉的。

    L0  Folder Scanner   路徑 / 大小 / 時戳 / 簽章
    L1  Format Router    副檔名 + magic bytes 雙軌判型，決定解析路線
    L1b Priority Engine  P0..P5 分級 + 讀取預算，產出乾淨的可讀清單
    L1c Subsystem Split  依 VRN / VDF / VAP / SUP / SYS 歸屬切分

輸出（全部只讀不改）：
    file_index.json        L0 全檔索引
    priority_manifest.json 依優先序排好的可讀清單（下游解析器的唯一輸入）
    format_catalog.json    格式理解表，給 UI 與模型看，不讓模型自己猜副檔名
    VIA_Priority_Matrix.html

對常見優先序模型的三處修正（都吃過虧才加的）：

  1. **DERIVED 類別**：本系統自己產生的報告、快照、儀表板不是垃圾也不是原始碼，
     而是「可重新生成」。讀它們浪費預算，而且會造成回饋迴路 —— 治理引擎掃到
     自己上一輪的輸出，每跑一次就多發一批編號。這個坑我踩過。
  2. **治理日誌豁免**：一律封殺 .log 會連 env_governance.log / module_registry.log /
     probe_evidence.log 一起丟掉，那是稽核軌跡，不是噪音。走白名單覆蓋。
  3. **CODE 是第一級內容**：對 VIA 來說 .py / .ps1 就是主要語料，
     不能只把 PDF/DOCX 當高價值文件。

另外補了 SECRET 類：.env / *.pem / id_rsa / credentials.* 只登記存在，
永不讀內容、永不進解析佇列。

用法：
    python VIA_FilePriorityRouter.py --root <資料夾> --out <輸出目錄>
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import sys
import time
import webbrowser
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

URN_SELF = "VIA-SYS-ENG-003"
VERSION = "v0100"
SPEC_VERSION = "VIA-SSOT-SPEC-v0100"
UI_SCHEMA_VERSION = "1.0.0"


def now_stamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def iso_now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class Console:
    def __init__(self) -> None:
        self.lines: List[str] = []

    def say(self, message: str, level: str = "INFO") -> None:
        line = "[%s][%s] %s" % (datetime.now().strftime("%H:%M:%S"), level, message)
        self.lines.append(line)
        print(line, flush=True)


LOG = Console()


# ---------------------------------------------------------------------------
# §1  格式理解表（L1 路由規則）
# ---------------------------------------------------------------------------

@dataclass
class FormatSpec:
    category: str      # GOVERNANCE|DOC|DATA|CODE|CONFIG|SEMI|NOISE|BINARY|ARCHIVE|MEDIA|SECRET
    route: str         # doc | table | config | code | text | duckdb | skip | register-only
    parser: str        # markdown | schema | ast | text | duckdb | ocr | none
    ai_affinity: str   # high | medium | low | none
    note: str = ""


FORMAT_CATALOG: Dict[str, FormatSpec] = {
    # 程式碼 —— 對 VIA 而言是第一級語料
    ".py":      FormatSpec("CODE", "code", "ast", "high", "Python 原始碼，AST 可精準定位"),
    ".pyw":     FormatSpec("CODE", "code", "ast", "high", ""),
    ".ps1":     FormatSpec("CODE", "code", "ast", "high", "PowerShell，Language.Parser 解析"),
    ".psm1":    FormatSpec("CODE", "code", "ast", "high", ""),
    ".psd1":    FormatSpec("CODE", "config", "schema", "high", "模組清單，實為資料"),
    ".sql":     FormatSpec("CODE", "code", "text", "high", ""),
    ".js":      FormatSpec("CODE", "code", "text", "medium", ""),
    ".ts":      FormatSpec("CODE", "code", "text", "medium", ""),
    # 高價值文件
    ".md":      FormatSpec("DOC", "doc", "markdown", "high", "已是 AI 最好消化的格式"),
    ".markdown": FormatSpec("DOC", "doc", "markdown", "high", ""),
    ".txt":     FormatSpec("DOC", "text", "text", "high", ""),
    ".pdf":     FormatSpec("DOC", "doc", "layout", "low", "需版面解析，模型不能直讀"),
    ".docx":    FormatSpec("DOC", "doc", "layout", "low", "ZIP 容器，需抽取"),
    ".doc":     FormatSpec("DOC", "doc", "layout", "none", "舊二進位格式，多半需先轉檔"),
    ".pptx":    FormatSpec("DOC", "doc", "layout", "low", ""),
    ".rtf":     FormatSpec("DOC", "doc", "text", "low", ""),
    # 結構化資料
    ".csv":     FormatSpec("DATA", "table", "duckdb", "medium", "進 DuckDB 後用 SQL 問"),
    ".tsv":     FormatSpec("DATA", "table", "duckdb", "medium", ""),
    ".xlsx":    FormatSpec("DATA", "table", "duckdb", "medium", "多工作表需逐頁展開"),
    ".xls":     FormatSpec("DATA", "table", "duckdb", "low", ""),
    ".parquet": FormatSpec("DATA", "table", "duckdb", "medium", "欄式，最省"),
    ".arrow":   FormatSpec("DATA", "table", "duckdb", "medium", ""),
    ".duckdb":  FormatSpec("DATA", "duckdb", "duckdb", "medium", ""),
    ".db":      FormatSpec("DATA", "duckdb", "duckdb", "low", ""),
    ".sqlite":  FormatSpec("DATA", "duckdb", "duckdb", "low", ""),
    # 設定 / 契約
    ".json":    FormatSpec("CONFIG", "config", "schema", "high", "最易解析，但不支援註解"),
    ".jsonl":   FormatSpec("CONFIG", "config", "schema", "high", "逐行事件流"),
    ".yaml":    FormatSpec("CONFIG", "config", "schema", "high", "縮排易錯"),
    ".yml":     FormatSpec("CONFIG", "config", "schema", "high", ""),
    ".toml":    FormatSpec("CONFIG", "config", "schema", "high", ""),
    ".ini":     FormatSpec("CONFIG", "config", "schema", "medium", ""),
    ".cfg":     FormatSpec("CONFIG", "config", "schema", "medium", ""),
    ".xml":     FormatSpec("SEMI", "config", "schema", "medium", "冗長，先抽結構"),
    # 半結構
    ".html":    FormatSpec("SEMI", "text", "text", "low", "只抽純文字，不留 DOM"),
    ".htm":     FormatSpec("SEMI", "text", "text", "low", ""),
    # 噪音
    ".log":     FormatSpec("NOISE", "text", "tail", "low", "只讀尾段"),
    ".tmp":     FormatSpec("NOISE", "skip", "none", "none", ""),
    ".cache":   FormatSpec("NOISE", "skip", "none", "none", ""),
    ".bak":     FormatSpec("NOISE", "register-only", "none", "none", "備份，登記不解析"),
    ".old":     FormatSpec("NOISE", "register-only", "none", "none", ""),
    ".swp":     FormatSpec("NOISE", "skip", "none", "none", ""),
    # 媒體
    ".png":     FormatSpec("MEDIA", "skip", "ocr", "none", "僅 OCR 模式讀"),
    ".jpg":     FormatSpec("MEDIA", "skip", "ocr", "none", ""),
    ".jpeg":    FormatSpec("MEDIA", "skip", "ocr", "none", ""),
    ".gif":     FormatSpec("MEDIA", "skip", "none", "none", ""),
    ".bmp":     FormatSpec("MEDIA", "skip", "ocr", "none", ""),
    ".webp":    FormatSpec("MEDIA", "skip", "ocr", "none", ""),
    ".svg":     FormatSpec("MEDIA", "text", "text", "medium", "其實是 XML，圖表可讀出語意"),
    ".mp4":     FormatSpec("MEDIA", "skip", "none", "none", ""),
    ".mp3":     FormatSpec("MEDIA", "skip", "none", "none", ""),
    # 封存
    ".zip":     FormatSpec("ARCHIVE", "register-only", "none", "none", "不自動展開"),
    ".rar":     FormatSpec("ARCHIVE", "register-only", "none", "none", ""),
    ".7z":      FormatSpec("ARCHIVE", "register-only", "none", "none", ""),
    ".tar":     FormatSpec("ARCHIVE", "register-only", "none", "none", ""),
    ".gz":      FormatSpec("ARCHIVE", "register-only", "none", "none", ""),
    # 二進位
    ".exe":     FormatSpec("BINARY", "skip", "none", "none", "無語意"),
    ".dll":     FormatSpec("BINARY", "skip", "none", "none", ""),
    ".bin":     FormatSpec("BINARY", "skip", "none", "none", ""),
    ".pyd":     FormatSpec("BINARY", "skip", "none", "none", ""),
    ".so":      FormatSpec("BINARY", "skip", "none", "none", ""),
    ".whl":     FormatSpec("ARCHIVE", "register-only", "none", "none", ""),
    ".pyc":     FormatSpec("BINARY", "skip", "none", "none", ""),
}

UNKNOWN_SPEC = FormatSpec("NOISE", "register-only", "none", "none", "未知副檔名，先登記")

# 治理稽核軌跡：即使副檔名是 .log 也必須讀，這是證據不是噪音
GOVERNANCE_PATTERNS = [
    "*governance*", "*registry*", "*ledger*", "*ssot*", "*contract*",
    "*_audit*", "probe_evidence*", "module_registry*", "capabilities*",
    "interface_contract*", "urn_registry*", "system_parameters*",
]

# 本系統自己的產出：可重新生成，讀它們浪費預算且會造成回饋迴路
DERIVED_PATTERNS = [
    "*_snapshot_*", "*_Matrix_*", "*Matrix.html", "*_report_*", "*Report*.html",
    "*.preview.json", "governance_snapshot_*", "downward_snapshot_*",
    "env_snapshot_*", "repair_snapshot_*", "file_index.json",
    "priority_manifest.json", "format_catalog.json", "ui_payload.json",
]
DERIVED_DIRS = {"out", "output", "_governance", "reports", "_reports", "logs"}

# 機密：只登記存在，永不讀內容
SECRET_PATTERNS = [
    ".env", ".env.*", "*.pem", "*.key", "*.pfx", "id_rsa*", "*credential*",
    "*secret*", "*.p12", "*token*.json", "*.keystore",
]

SKIP_DIRS = {
    ".git", ".svn", ".hg", "__pycache__", ".venv", "venv", "env", "node_modules",
    ".idea", ".vs", ".mypy_cache", ".pytest_cache", ".ruff_cache", "site-packages",
    "dist-info", "_to_delete", "$RECYCLE.BIN", "System Volume Information",
}

# magic bytes：副檔名會說謊，簽章不會
SIGNATURES: List[Tuple[bytes, str]] = [
    (b"%PDF-", "pdf"), (b"PK\x03\x04", "zip-container"), (b"\x89PNG\r\n\x1a\n", "png"),
    (b"\xff\xd8\xff", "jpeg"), (b"GIF8", "gif"), (b"MZ", "pe-executable"),
    (b"\x7fELF", "elf"), (b"SQLite format 3\x00", "sqlite"), (b"PAR1", "parquet"),
    (b"\x1f\x8b", "gzip"), (b"7z\xbc\xaf\x27\x1c", "7zip"), (b"Rar!", "rar"),
    (b"\xd0\xcf\x11\xe0", "ole-compound"), (b"BM", "bmp"), (b"\x00asm", "wasm"),
]

ZIP_CONTAINER_EXT = {".docx", ".xlsx", ".pptx", ".zip", ".whl", ".jar", ".odt", ".epub"}

PRIORITY_ORDER = ["P0-GOVERNANCE", "P1-CODE", "P2-DOC", "P3-DATA",
                  "P4-SEMI", "P5-NOISE", "SKIP"]


# ---------------------------------------------------------------------------
# §2  記錄結構
# ---------------------------------------------------------------------------

@dataclass
class FileRecord:
    file_id: str
    path: str
    rel: str
    name: str
    ext: str
    size: int
    modified: str
    subsystem: str = "UNCLASSIFIED"
    category: str = ""
    route: str = ""
    parser: str = ""
    ai_affinity: str = ""
    priority: str = ""
    signature: str = ""
    read_plan: str = ""        # full | tail | register-only | none
    read_bytes: int = 0
    reason: str = ""


def sniff(path: Path) -> str:
    try:
        with path.open("rb") as handle:
            head = handle.read(64)
    except OSError:
        return "unreadable"
    if not head:
        return "empty"
    for magic, name in SIGNATURES:
        if head.startswith(magic):
            return name
    if b"\x00" in head:
        return "binary"
    return "text"


def match_any(name: str, patterns: List[str]) -> bool:
    lower = name.lower()
    return any(fnmatch.fnmatch(lower, pattern.lower()) for pattern in patterns)


def attribute_subsystem(rel: str, name: str) -> str:
    probe = (rel + "/" + name).lower().replace("\\", "/")
    if re.search(r"(^|/)vrn(/|[_-])|vrn_", probe):
        return "VRN"
    if re.search(r"(^|/)vdf(/|[_-])|vdf_", probe):
        return "VDF"
    if re.search(r"(^|/)vap(/|[_-])|vap_", probe):
        return "VAP"
    if re.search(r"supportive|sup_|aegis|celeritas|netsupport|codexnexus", probe):
        return "SUP"
    if re.search(r"system[_ -]?manager|centralgovernance|governance|core/|launcher|console", probe):
        return "SYS"
    return "UNCLASSIFIED"


# ---------------------------------------------------------------------------
# §3  優先序引擎
# ---------------------------------------------------------------------------

class PriorityRouter:
    def __init__(self, root: Path, out_dir: Path, min_bytes: int = 1024,
                 log_tail_bytes: int = 65536, budget_mb: int = 512,
                 ocr: bool = False, max_files: int = 200000) -> None:
        self.root = root
        self.out_dir = out_dir
        self.min_bytes = min_bytes
        self.log_tail_bytes = log_tail_bytes
        self.budget = budget_mb * 1024 * 1024
        self.ocr = ocr
        self.max_files = max_files
        self.stamp = now_stamp()
        self.records: List[FileRecord] = []
        self.findings: List[Dict[str, str]] = []
        self.budget_used = 0
        self.budget_hit = False

    # -- L0 -------------------------------------------------------------
    def scan(self) -> None:
        LOG.say("L0 掃描：%s" % self.root)
        counter = 0
        for dirpath, dirnames, filenames in os.walk(self.root):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS
                           and not d.lower().startswith(".")]
            here = Path(dirpath)
            in_derived_dir = any(part.lower() in DERIVED_DIRS for part in here.parts)
            for filename in filenames:
                if counter >= self.max_files:
                    LOG.say("掃描上限 %d 達成" % self.max_files, "WARN")
                    return
                full = here / filename
                try:
                    stat = full.stat()
                except OSError:
                    continue
                counter += 1
                rel = os.path.relpath(str(full), str(self.root)).replace("\\", "/")
                record = FileRecord(
                    file_id="F%06d" % counter, path=str(full), rel=rel,
                    name=filename, ext=full.suffix.lower(), size=stat.st_size,
                    modified=datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M"),
                    subsystem=attribute_subsystem(rel, filename),
                )
                self.classify(record, in_derived_dir)
                self.records.append(record)
        LOG.say("L0 完成：%d 個檔案" % len(self.records), "OK")

    # -- L1 -------------------------------------------------------------
    def classify(self, record: FileRecord, in_derived_dir: bool) -> None:
        spec = FORMAT_CATALOG.get(record.ext, UNKNOWN_SPEC)
        record.category = spec.category
        record.route = spec.route
        record.parser = spec.parser
        record.ai_affinity = spec.ai_affinity

        # 機密最優先判定：只登記，永不讀
        if match_any(record.name, SECRET_PATTERNS):
            record.category, record.priority = "SECRET", "SKIP"
            record.route, record.read_plan = "register-only", "register-only"
            record.reason = "機密檔案：只登記存在，永不讀取內容"
            return

        # 判定順序三層：明確的產出檔名 > 治理檔名 > 所在目錄是產出區。
        # 若只看目錄，logs/env_governance.log 會被當成產出丟掉 ——
        # 那是稽核軌跡不是噪音。這個順序就是為了擋這件事。
        explicit_derived = match_any(record.name, DERIVED_PATTERNS)
        governance = match_any(record.name, GOVERNANCE_PATTERNS)

        if explicit_derived:
            record.category, record.priority = "DERIVED", "SKIP"
            record.route, record.read_plan = "register-only", "register-only"
            record.reason = "本系統產出，可重新生成；讀它會造成回饋迴路"
            return

        if governance and record.category in ("CONFIG", "DATA", "NOISE", "CODE", "DOC"):
            record.category, record.priority = "GOVERNANCE", "P0-GOVERNANCE"
            record.route = "config" if record.ext != ".log" else "text"
            record.parser = "schema" if record.ext != ".log" else "tail"
            record.ai_affinity = "high"
            record.read_plan = "full"
            record.reason = "治理契約／稽核軌跡，定義其他檔案的意義，最先讀"
            return

        if in_derived_dir:
            record.category, record.priority = "DERIVED", "SKIP"
            record.route, record.read_plan = "register-only", "register-only"
            record.reason = "位於產出目錄，可重新生成"
            return

        # 空檔與碎屑
        if record.size == 0:
            record.priority, record.read_plan = "SKIP", "none"
            record.reason = "空檔"
            return
        if record.size < self.min_bytes and record.category not in ("CODE", "CONFIG"):
            record.priority, record.read_plan = "SKIP", "none"
            record.reason = "小於 %d bytes，多為殼檔或碎屑" % self.min_bytes
            return

        mapping = {
            "CODE": "P1-CODE", "DOC": "P2-DOC", "DATA": "P3-DATA",
            "CONFIG": "P0-GOVERNANCE" if governance else "P3-DATA",
            "SEMI": "P4-SEMI", "NOISE": "P5-NOISE",
            "MEDIA": "SKIP", "BINARY": "SKIP", "ARCHIVE": "SKIP",
        }
        record.priority = mapping.get(record.category, "P5-NOISE")

        if record.category == "MEDIA":
            if self.ocr and record.parser == "ocr":
                record.priority, record.read_plan = "P4-SEMI", "full"
                record.reason = "OCR 模式開啟"
            else:
                record.read_plan, record.reason = "none", "圖像；未開 --ocr 不讀"
            if record.ext == ".svg":
                record.priority, record.read_plan = "P4-SEMI", "full"
                record.reason = "SVG 實為 XML，圖表語意可讀"
            return
        if record.category == "BINARY":
            record.read_plan, record.reason = "none", "二進位，無語意"
            return
        if record.category == "ARCHIVE":
            record.read_plan, record.reason = "register-only", "壓縮檔不自動展開"
            return
        if record.category == "NOISE" and record.ext == ".log":
            record.read_plan = "tail"
            record.read_bytes = min(record.size, self.log_tail_bytes)
            record.reason = "只讀尾段 %d bytes" % record.read_bytes
            return
        if record.category == "NOISE":
            record.read_plan, record.reason = "register-only", "低價值，登記不解析"
            return
        record.read_plan = "full"

    # -- 簽章驗證：只對進得了佇列的檔案做，省 I/O ------------------------
    def verify_signatures(self) -> None:
        LOG.say("L1 簽章驗證（副檔名會說謊，簽章不會）")
        checked = 0
        for record in self.records:
            if record.read_plan in ("none",):
                continue
            record.signature = sniff(Path(record.path))
            checked += 1
            if record.signature in ("empty", "unreadable"):
                continue
            expected_zip = record.ext in ZIP_CONTAINER_EXT
            if record.signature == "zip-container" and not expected_zip:
                self._flag(record, "EXT_MISMATCH",
                           "副檔名 %s 但內容是 ZIP 容器" % record.ext)
                record.priority, record.read_plan = "SKIP", "register-only"
            elif record.signature in ("pe-executable", "elf") and \
                    record.category not in ("BINARY", "ARCHIVE"):
                self._flag(record, "EXT_MISMATCH",
                           "副檔名 %s 但內容是可執行檔" % record.ext)
                record.category, record.priority = "BINARY", "SKIP"
                record.read_plan = "none"
            elif record.signature == "binary" and record.route in ("code", "doc", "text", "config"):
                self._flag(record, "BINARY_CONTENT",
                           "宣稱文字格式但含 NUL 位元組")
                record.priority, record.read_plan = "SKIP", "register-only"
            elif record.signature == "pdf" and record.ext != ".pdf":
                # 不是丟掉，是改走正確路線 —— 它是有價值的文件，只是副檔名錯了
                self._flag(record, "EXT_MISMATCH",
                           "副檔名 %s 但內容是 PDF，已改走版面解析路線" % record.ext)
                record.category, record.priority = "DOC", "P2-DOC"
                record.route, record.parser, record.ai_affinity = "doc", "layout", "low"
                record.reason = "依簽章而非副檔名路由"
        mismatch = len([f for f in self.findings if f["kind"] == "EXT_MISMATCH"])
        binary = len([f for f in self.findings if f["kind"] == "BINARY_CONTENT"])
        LOG.say("簽章驗證 %d 個：副檔名不符 %d，宣稱文字卻是二進位 %d"
                % (checked, mismatch, binary), "WARN" if self.findings else "OK")

    def _flag(self, record: FileRecord, kind: str, detail: str) -> None:
        self.findings.append({"kind": kind, "file": record.name, "rel": record.rel,
                              "detail": detail})

    # -- 讀取預算 --------------------------------------------------------
    def apply_budget(self) -> None:
        order = {name: index for index, name in enumerate(PRIORITY_ORDER)}
        queue = sorted([r for r in self.records if r.read_plan in ("full", "tail")],
                       key=lambda r: (order.get(r.priority, 99), -r.size))
        for record in queue:
            need = record.read_bytes or record.size
            if self.budget_used + need > self.budget:
                self.budget_hit = True
                record.read_plan = "deferred"
                record.reason = "超出本輪讀取預算，延後到下一輪"
                continue
            self.budget_used += need
            record.read_bytes = need
        LOG.say("讀取預算：使用 %.1f MB / %.0f MB%s"
                % (self.budget_used / 1048576, self.budget / 1048576,
                   "（已觸頂，部分延後）" if self.budget_hit else ""),
                "WARN" if self.budget_hit else "OK")

    # -- 輸出 ------------------------------------------------------------
    def summarize(self) -> Dict[str, Any]:
        by_priority: Dict[str, int] = {}
        by_category: Dict[str, int] = {}
        by_subsystem: Dict[str, Dict[str, Any]] = {}
        for record in self.records:
            by_priority[record.priority] = by_priority.get(record.priority, 0) + 1
            by_category[record.category] = by_category.get(record.category, 0) + 1
            slot = by_subsystem.setdefault(record.subsystem,
                                           {"files": 0, "bytes": 0, "readable": 0})
            slot["files"] += 1
            slot["bytes"] += record.size
            if record.read_plan in ("full", "tail"):
                slot["readable"] += 1
        return {"by_priority": by_priority, "by_category": by_category,
                "by_subsystem": by_subsystem}

    def emit(self, open_browser: bool = True) -> Path:
        self.out_dir.mkdir(parents=True, exist_ok=True)
        rows = [asdict(r) for r in self.records]

        index_path = self.out_dir / "file_index.json"
        index_path.write_text(json.dumps(
            {"schema": "VIA.FileIndex", "spec": SPEC_VERSION, "engine": URN_SELF,
             "generated": iso_now(), "root": str(self.root),
             "count": len(rows), "files": rows},
            ensure_ascii=False, indent=1), encoding="utf-8")

        order = {name: index for index, name in enumerate(PRIORITY_ORDER)}
        readable = sorted([r for r in self.records if r.read_plan in ("full", "tail")],
                          key=lambda r: (order.get(r.priority, 99), r.rel))
        manifest_path = self.out_dir / "priority_manifest.json"
        manifest_path.write_text(json.dumps(
            {"schema": "VIA.PriorityManifest", "spec": SPEC_VERSION,
             "generated": iso_now(), "budget_bytes": self.budget,
             "budget_used": self.budget_used, "budget_hit": self.budget_hit,
             "count": len(readable),
             "queue": [{"file_id": r.file_id, "rel": r.rel, "priority": r.priority,
                        "route": r.route, "parser": r.parser,
                        "read_plan": r.read_plan, "read_bytes": r.read_bytes,
                        "subsystem": r.subsystem} for r in readable]},
            ensure_ascii=False, indent=1), encoding="utf-8")

        catalog_path = self.out_dir / "format_catalog.json"
        catalog_path.write_text(json.dumps(
            {"schema": "VIA.FormatCatalog", "ui_schema": UI_SCHEMA_VERSION,
             "generated": iso_now(),
             "note": "模型不得自行猜測副檔名語意，一律以本表為準",
             "formats": {ext: asdict(spec) for ext, spec in sorted(FORMAT_CATALOG.items())}},
            ensure_ascii=False, indent=1), encoding="utf-8")

        summary = self.summarize()
        html_path = self.out_dir / ("VIA_Priority_Matrix_%s.html" % self.stamp)
        html_path.write_text(self.render(summary, readable), encoding="utf-8")
        (self.out_dir / ("priority_log_%s.log" % self.stamp)).write_text(
            "\n".join(LOG.lines), encoding="utf-8")

        LOG.say("索引 -> %s" % index_path.name, "OK")
        LOG.say("清單 -> %s（%d 個檔案進解析佇列）" % (manifest_path.name, len(readable)), "OK")
        LOG.say("矩陣 -> %s" % html_path, "OK")
        if open_browser:
            try:
                webbrowser.open(html_path.as_uri())
            except Exception:                                # noqa: BLE001
                pass
        return html_path

    # -- HTML ------------------------------------------------------------
    def render(self, summary: Dict[str, Any], readable: List[FileRecord]) -> str:
        def esc(value: Any) -> str:
            return (str(value).replace("&", "&amp;").replace("<", "&lt;")
                    .replace(">", "&gt;").replace('"', "&quot;"))

        def klass(value: str) -> str:
            upper = str(value).upper()
            if upper.startswith("P0") or upper.startswith("P1"):
                return "ok"
            if upper == "SKIP" or upper.startswith("P5"):
                return "fail"
            if upper.startswith("P"):
                return "warn"
            return ""

        def table(items: List[Dict[str, Any]], fields: List[str],
                  status: str = "", limit: int = 400) -> str:
            if not items:
                return "<tr><td colspan='%d' class='muted'>—— 無 ——</td></tr>" % len(fields)
            out = []
            for item in items[:limit]:
                cells = []
                for name in fields:
                    value = item.get(name, "")
                    cls = " class='%s'" % klass(str(value)) if name == status else ""
                    cells.append("<td%s>%s</td>" % (cls, esc(value)))
                out.append("<tr>%s</tr>" % "".join(cells))
            if len(items) > limit:
                out.append("<tr><td colspan='%d' class='muted'>…… 其餘 %d 筆見 JSON</td></tr>"
                           % (len(fields), len(items) - limit))
            return "".join(out)

        prio_rows = [{"p": p, "n": summary["by_priority"].get(p, 0)}
                     for p in PRIORITY_ORDER if summary["by_priority"].get(p)]
        cat_rows = [{"c": c, "n": n} for c, n in
                    sorted(summary["by_category"].items(), key=lambda kv: -kv[1])]
        sub_rows = [{"s": s, "files": v["files"], "readable": v["readable"],
                     "mb": round(v["bytes"] / 1048576, 1)}
                    for s, v in sorted(summary["by_subsystem"].items(),
                                       key=lambda kv: -kv[1]["files"])]
        fmt_rows = [{"ext": ext, "category": spec.category, "route": spec.route,
                     "parser": spec.parser, "ai": spec.ai_affinity, "note": spec.note}
                    for ext, spec in sorted(FORMAT_CATALOG.items())]
        queue_rows = [{"priority": r.priority, "subsystem": r.subsystem, "rel": r.rel,
                       "route": r.route, "parser": r.parser, "plan": r.read_plan,
                       "kb": round(r.read_bytes / 1024, 1)} for r in readable]
        skip_rows = [{"priority": r.priority, "category": r.category, "rel": r.rel,
                      "reason": r.reason}
                     for r in self.records if r.read_plan in ("none", "register-only",
                                                              "deferred")]

        css = """
:root{--paper:#f2f2f3;--ink:#1d1f20;--line:#d8d8d9;--red:#b0453d;--green:#3f7d5e;--amber:#c4943a;--panel:#fff}
*{box-sizing:border-box}
body{margin:0;padding:22px 26px;background:var(--paper);color:var(--ink);font-family:"Noto Sans TC","Segoe UI",system-ui,sans-serif;font-size:12px;line-height:1.45}
.seal{display:inline-flex;width:38px;height:38px;align-items:center;justify-content:center;background:var(--red);color:#fff;font-family:"Noto Serif TC",serif;font-size:21px;border-radius:3px}
h1{font-family:"Noto Serif TC",Georgia,serif;font-size:16px;letter-spacing:.14em;text-transform:uppercase;margin:10px 0 3px}
h2{font-family:"Noto Serif TC",Georgia,serif;font-size:14px;margin:22px 0 5px}
.lede{color:#6c6e70;font-size:11.5px;margin:0 0 12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(112px,1fr));gap:9px;margin:14px 0 4px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:3px;padding:10px 12px}
.card .k{font-size:10px;letter-spacing:.1em;color:#8a8c8e;text-transform:uppercase}
.card .v{font-size:20px;font-family:"Noto Serif TC",Georgia,serif;margin-top:3px}
table{width:100%;border-collapse:collapse;background:var(--panel);border:1px solid var(--line);font-size:11.5px;table-layout:fixed}
th,td{border-bottom:1px solid #ececed;padding:5px 7px;text-align:left;vertical-align:top;white-space:normal;overflow-wrap:anywhere;word-break:break-word}
th{background:#eeeeef;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:#5c5e60}
tr:hover td{background:#fbfbfb}
.ok{color:var(--green);font-weight:600}.warn{color:var(--amber);font-weight:600}.fail{color:var(--red);font-weight:600}
.muted{color:#9a9c9e;text-align:center;padding:12px}
pre{background:var(--panel);border:1px solid var(--line);padding:11px;font-size:11px;white-space:pre-wrap;max-height:32vh;overflow:auto}
"""
        return """<!doctype html>
<html lang="zh-Hant"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>VIA Priority Matrix</title><style>%s</style></head><body>
<div class="seal">序</div>
<h1>File Priority Router</h1>
<p class="lede">%s · %s · 只讀不改 · 解析佇列 %d／%d 檔</p>
<div class="cards">
  <div class="card"><div class="k">Total</div><div class="v">%d</div></div>
  <div class="card"><div class="k">In Queue</div><div class="v ok">%d</div></div>
  <div class="card"><div class="k">Skipped</div><div class="v fail">%d</div></div>
  <div class="card"><div class="k">Budget MB</div><div class="v">%.0f</div></div>
  <div class="card"><div class="k">Type Mismatch</div><div class="v warn">%d</div></div>
</div>

<h2>優先序分佈</h2>
<p class="lede">P0 治理契約先讀（它定義其他檔案的意義）→ P1 程式碼 → P2 文件 → P3 資料 → P4 半結構 → P5 噪音只讀尾段</p>
<table><colgroup><col style="width:70%%"><col style="width:30%%"></colgroup>
<tr><th>Priority</th><th>Files</th></tr>%s</table>

<h2>子系統歸屬</h2>
<table><colgroup><col style="width:28%%"><col style="width:24%%"><col style="width:24%%"><col style="width:24%%"></colgroup>
<tr><th>Subsystem</th><th>Files</th><th>In Queue</th><th>MB</th></tr>%s</table>

<h2>類別分佈</h2>
<table><colgroup><col style="width:70%%"><col style="width:30%%"></colgroup>
<tr><th>Category</th><th>Files</th></tr>%s</table>

<h2>解析佇列（下游唯一輸入）</h2>
<table><colgroup><col style="width:13%%"><col style="width:10%%"><col style="width:38%%"><col style="width:10%%"><col style="width:11%%"><col style="width:10%%"><col style="width:8%%"></colgroup>
<tr><th>Priority</th><th>Subsystem</th><th>Path</th><th>Route</th><th>Parser</th><th>Plan</th><th>KB</th></tr>%s</table>

<h2>被擋下的檔案</h2>
<table><colgroup><col style="width:10%%"><col style="width:12%%"><col style="width:40%%"><col style="width:38%%"></colgroup>
<tr><th>Priority</th><th>Category</th><th>Path</th><th>Reason</th></tr>%s</table>

<h2>型別不符（副檔名說謊）</h2>
<table><colgroup><col style="width:16%%"><col style="width:24%%"><col style="width:60%%"></colgroup>
<tr><th>Kind</th><th>File</th><th>Detail</th></tr>%s</table>

<h2>格式理解表</h2>
<p class="lede">模型不得自行猜測副檔名語意，一律以本表為準。</p>
<table><colgroup><col style="width:8%%"><col style="width:12%%"><col style="width:10%%"><col style="width:10%%"><col style="width:8%%"><col style="width:52%%"></colgroup>
<tr><th>Ext</th><th>Category</th><th>Route</th><th>Parser</th><th>AI</th><th>Note</th></tr>%s</table>

<h2>執行日誌</h2>
<pre>%s</pre>
</body></html>""" % (
            css, esc(self.root), self.stamp, len(readable), len(self.records),
            len(self.records), len(readable),
            len([r for r in self.records if r.read_plan in ("none", "register-only")]),
            self.budget / 1048576,
            len([f for f in self.findings if f["kind"] == "EXT_MISMATCH"]),
            table(prio_rows, ["p", "n"], "p"),
            table(sub_rows, ["s", "files", "readable", "mb"]),
            table(cat_rows, ["c", "n"]),
            table(queue_rows, ["priority", "subsystem", "rel", "route", "parser",
                               "plan", "kb"], "priority"),
            table(skip_rows, ["priority", "category", "rel", "reason"], "priority"),
            table(self.findings, ["kind", "file", "detail"]),
            table(fmt_rows, ["ext", "category", "route", "parser", "ai", "note"]),
            esc("\n".join(LOG.lines)),
        )


# ---------------------------------------------------------------------------
# §4  CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="VIA_FilePriorityRouter.py",
        description="VIA-SYS-ENG-003 L0 掃描 + L1 格式路由 + 優先序引擎")
    parser.add_argument("--root", default=".", help="要掃描的母資料夾")
    parser.add_argument("--out", default="", help="輸出目錄（預設 <root>/_governance/priority）")
    parser.add_argument("--min-bytes", type=int, default=1024, help="小於此大小視為碎屑")
    parser.add_argument("--log-tail", type=int, default=65536, help=".log 只讀尾端多少 bytes")
    parser.add_argument("--budget-mb", type=int, default=512, help="本輪讀取預算")
    parser.add_argument("--max-files", type=int, default=200000)
    parser.add_argument("--ocr", action="store_true", help="開啟後圖像才進佇列")
    parser.add_argument("--no-open", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    root = Path(args.root).expanduser().resolve()
    if not root.is_dir():
        print("root 不存在：%s" % root, file=sys.stderr)
        return 2
    out_dir = Path(args.out).expanduser().resolve() if args.out else \
        root / "_governance" / "priority"

    started = time.perf_counter()
    LOG.say("%s File Priority Router %s 啟動" % (URN_SELF, VERSION), "OK")
    router = PriorityRouter(root=root, out_dir=out_dir, min_bytes=args.min_bytes,
                            log_tail_bytes=args.log_tail, budget_mb=args.budget_mb,
                            ocr=args.ocr, max_files=args.max_files)
    router.scan()
    router.verify_signatures()
    router.apply_budget()
    router.emit(open_browser=not args.no_open and not args.json)

    queued = len([r for r in router.records if r.read_plan in ("full", "tail")])
    skipped = len(router.records) - queued
    verdict = "GREEN"
    if router.budget_hit or router.findings:
        verdict = "AMBER"
    if not queued and router.records:
        verdict = "RED"
    LOG.say("完成，耗時 %.1fs -> %s" % (time.perf_counter() - started, verdict), "OK")

    print("")
    print("=" * 60)
    print(" VIA FILE PRIORITY ROUTER  ->  %s" % verdict)
    print(" 進佇列 %d ｜ 擋下 %d ｜ 簽章異常 %d" % (queued, skipped, len(router.findings)))
    print("=" * 60)
    if args.json:
        print(json.dumps({"verdict": verdict, "queued": queued, "skipped": skipped,
                          "stamp": router.stamp}, ensure_ascii=False))
    return 0 if verdict != "RED" else 1


if __name__ == "__main__":
    sys.exit(main())
