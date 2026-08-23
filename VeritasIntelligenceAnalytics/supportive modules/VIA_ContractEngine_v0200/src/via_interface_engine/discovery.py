"""Fail-closed file watchdog and static manifest discovery without imports."""

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

import ast
import hashlib
import json
import threading
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from .config import (
    DEFAULT_HEALTH_WORKERS,
    DEFAULT_WATCHDOG_EXTENSIONS,
    DEFAULT_WATCHDOG_INTERVAL_SECONDS,
)
from .contracts import ModuleManifest, ModuleState
from .exceptions import DependencyResolutionError
from .ssot import VIASSOTRegistry


class CandidateKind(StrEnum):
    PYTHON = "PYTHON"
    JSON = "JSON"


@dataclass(frozen=True, slots=True)
class CandidateFinding:
    code: str
    severity: str
    message: str
    line: int | None = None


@dataclass(frozen=True, slots=True)
class StaticCandidate:
    path: Path
    kind: CandidateKind
    sha256: str
    manifest: ModuleManifest | None
    accepted: bool
    findings: tuple[CandidateFinding, ...]


class StaticManifestScanner:
    """Read AST/JSON metadata while refusing to import candidate code."""

    FORBIDDEN_CALLS = frozenset({"eval", "exec", "compile", "__import__"})
    FORBIDDEN_IMPORT_PREFIXES = ("plugins", "via_plugins")
    HARDCODED_PATH_MARKERS = ("C:\\Users\\", "C:/Users/", "OneDrive")

    def scan(self, path: Path) -> StaticCandidate:
        resolved = path.resolve()
        if not resolved.is_file():
            return self._rejected(
                resolved,
                CandidateKind.PYTHON,
                "FILE_NOT_FOUND",
                "候選檔案不存在",
            )
        content = resolved.read_bytes()
        digest = hashlib.sha256(content).hexdigest()
        if resolved.suffix.lower() == ".py":
            return self._scan_python(resolved, content, digest)
        if resolved.suffix.lower() == ".json":
            return self._scan_json(resolved, content, digest)
        return self._rejected(
            resolved,
            CandidateKind.PYTHON,
            "UNSUPPORTED_EXTENSION",
            f"不支援副檔名: {resolved.suffix}",
            digest,
        )

    def _scan_python(self, path: Path, content: bytes, digest: str) -> StaticCandidate:
        findings: list[CandidateFinding] = []
        try:
            text = content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            return self._rejected(
                path,
                CandidateKind.PYTHON,
                "ENCODING_ERROR",
                str(exc),
                digest,
            )
        try:
            tree = ast.parse(text, filename=str(path))
        except SyntaxError as exc:
            return self._rejected(
                path,
                CandidateKind.PYTHON,
                "PYTHON_AST_ERROR",
                str(exc),
                digest,
                exc.lineno,
            )

        manifest_values: list[dict[str, Any]] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                name = self._call_name(node.func)
                if name in self.FORBIDDEN_CALLS:
                    findings.append(
                        CandidateFinding(
                            "FORBIDDEN_DYNAMIC_CALL",
                            "HIGH",
                            f"禁止自動掛載含 {name}() 的候選模組",
                            getattr(node, "lineno", None),
                        )
                    )
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.startswith(self.FORBIDDEN_IMPORT_PREFIXES):
                        findings.append(
                            CandidateFinding(
                                "PRIVATE_PLUGIN_IMPORT",
                                "HIGH",
                                f"模組不得私下 import 其他外掛: {alias.name}",
                                getattr(node, "lineno", None),
                            )
                        )
            elif isinstance(node, ast.ImportFrom):
                module_name = node.module or ""
                if module_name.startswith(self.FORBIDDEN_IMPORT_PREFIXES):
                    findings.append(
                        CandidateFinding(
                            "PRIVATE_PLUGIN_IMPORT",
                            "HIGH",
                            f"模組不得私下 import 其他外掛: {module_name}",
                            getattr(node, "lineno", None),
                        )
                    )
            elif isinstance(node, ast.Constant) and isinstance(node.value, str):
                if any(marker in node.value for marker in self.HARDCODED_PATH_MARKERS):
                    findings.append(
                        CandidateFinding(
                            "HARDCODED_LOCAL_PATH",
                            "HIGH",
                            "候選模組包含使用者或 OneDrive 硬編碼路徑",
                            getattr(node, "lineno", None),
                        )
                    )

        for node in ast.walk(tree):
            if not isinstance(node, (ast.Assign, ast.AnnAssign)):
                continue
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if not any(isinstance(target, ast.Name) and target.id == "__manifest__" for target in targets):
                continue
            value_node = node.value
            try:
                manifest_values.append(self._literal_manifest(value_node))
            except (ValueError, TypeError) as exc:
                findings.append(
                    CandidateFinding(
                        "DYNAMIC_MANIFEST",
                        "HIGH",
                        f"__manifest__ 必須可由 AST 靜態解析: {exc}",
                        getattr(node, "lineno", None),
                    )
                )

        if len(manifest_values) != 1:
            findings.append(
                CandidateFinding(
                    "MANIFEST_COUNT",
                    "HIGH",
                    f"每個候選檔必須且只能有一份 __manifest__；目前 {len(manifest_values)}",
                )
            )
        manifest = self._validate_manifest(manifest_values[0], findings) if len(manifest_values) == 1 else None
        accepted = manifest is not None and not any(item.severity == "HIGH" for item in findings)
        return StaticCandidate(
            path=path,
            kind=CandidateKind.PYTHON,
            sha256=digest,
            manifest=manifest,
            accepted=accepted,
            findings=tuple(findings),
        )

    def _scan_json(self, path: Path, content: bytes, digest: str) -> StaticCandidate:
        findings: list[CandidateFinding] = []
        try:
            payload = json.loads(content.decode("utf-8-sig"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            return self._rejected(
                path,
                CandidateKind.JSON,
                "JSON_PARSE_ERROR",
                str(exc),
                digest,
            )
        raw_manifest = payload.get("__manifest__", payload.get("manifest")) if isinstance(payload, dict) else None
        if not isinstance(raw_manifest, dict):
            findings.append(
                CandidateFinding(
                    "MANIFEST_MISSING",
                    "HIGH",
                    "JSON 候選缺少 manifest 或 __manifest__",
                )
            )
            manifest = None
        else:
            raw_manifest.setdefault("language", "JSON")
            manifest = self._validate_manifest(raw_manifest, findings)
        return StaticCandidate(
            path=path,
            kind=CandidateKind.JSON,
            sha256=digest,
            manifest=manifest,
            accepted=manifest is not None and not any(item.severity == "HIGH" for item in findings),
            findings=tuple(findings),
        )

    @staticmethod
    def _literal_manifest(node: ast.AST) -> dict[str, Any]:
        if isinstance(node, ast.Dict):
            value = ast.literal_eval(node)
            if not isinstance(value, dict):
                raise ValueError("Manifest 不是 dict")
            return value
        if isinstance(node, ast.Call) and StaticManifestScanner._call_name(node.func) == "ModuleManifest":
            if node.args:
                raise ValueError("ModuleManifest 不得使用位置參數")
            return {
                keyword.arg: ast.literal_eval(keyword.value)
                for keyword in node.keywords
                if keyword.arg is not None
            }
        raise ValueError("僅允許 dict literal 或 ModuleManifest(keyword=literal)")

    @staticmethod
    def _validate_manifest(
        raw_manifest: dict[str, Any],
        findings: list[CandidateFinding],
    ) -> ModuleManifest | None:
        try:
            return ModuleManifest.model_validate(raw_manifest)
        except ValidationError as exc:
            findings.append(
                CandidateFinding(
                    "MANIFEST_INVALID",
                    "HIGH",
                    str(exc),
                )
            )
            return None

    @staticmethod
    def _call_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return node.attr
        return ""

    @staticmethod
    def _rejected(
        path: Path,
        kind: CandidateKind,
        code: str,
        message: str,
        digest: str = "",
        line: int | None = None,
    ) -> StaticCandidate:
        return StaticCandidate(
            path=path,
            kind=kind,
            sha256=digest,
            manifest=None,
            accepted=False,
            findings=(CandidateFinding(code, "HIGH", message, line),),
        )


class SSOTAutoRegistrar:
    """Allocate and stage identities for accepted static candidates."""

    def __init__(
        self,
        ssot_registry: VIASSOTRegistry,
        scanner: StaticManifestScanner | None = None,
    ) -> None:
        self._ssot = ssot_registry
        self._scanner = scanner or StaticManifestScanner()

    def process_path(self, path: Path) -> tuple[StaticCandidate, str | None]:
        candidate = self._scanner.scan(path)
        if not candidate.accepted or candidate.manifest is None:
            return candidate, None
        resource_urn, registered_at = self._ssot.allocate_identity(
            candidate.manifest,
            str(candidate.path),
            candidate.sha256,
        )
        try:
            existing = self._ssot.resolve(resource_urn)
        except DependencyResolutionError:
            existing = None
        if existing is None:
            self._ssot.attach_runtime(
                resource_urn=resource_urn,
                registered_at=registered_at,
                manifest=candidate.manifest,
                instance=None,
                state=ModuleState.DISCOVERED,
                dependencies=(),
                source_ref=str(candidate.path),
                source_sha256=candidate.sha256,
                descriptor=None,
            )
        return candidate, resource_urn


class VIAFileWatchdog:
    """Polling watchdog that reports changed candidates without executing them."""

    def __init__(
        self,
        watch_directory: Path,
        on_change: Callable[[Path], None],
        *,
        interval_seconds: float = DEFAULT_WATCHDOG_INTERVAL_SECONDS,
        extensions: frozenset[str] = DEFAULT_WATCHDOG_EXTENSIONS,
    ) -> None:
        self._watch_directory = watch_directory.resolve()
        self._on_change = on_change
        self._interval_seconds = max(0.05, interval_seconds)
        self._extensions = frozenset(item.lower() for item in extensions)
        self._known: dict[Path, tuple[int, int]] = {}
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._watch_directory.mkdir(parents=True, exist_ok=True)
        self._known = self._snapshot()
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="VIAFileWatchdog",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout_seconds: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=max(0.1, timeout_seconds))

    def scan_once(self) -> tuple[Path, ...]:
        current = self._snapshot()
        changed = tuple(
            sorted(
                path
                for path, signature in current.items()
                if self._known.get(path) != signature
            )
        )
        self._known = current
        for path in changed:
            self._on_change(path)
        return changed

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval_seconds):
            self.scan_once()

    def _snapshot(self) -> dict[Path, tuple[int, int]]:
        result: dict[Path, tuple[int, int]] = {}
        for path in self._watch_directory.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in self._extensions:
                continue
            stat = path.stat()
            result[path.resolve()] = (stat.st_mtime_ns, stat.st_size)
        return result


class VIAMemoryWatchdog:
    """Poll governed in-memory instances without touching executing modules."""

    def __init__(
        self,
        ssot_registry: VIASSOTRegistry,
        *,
        interval_seconds: float = DEFAULT_WATCHDOG_INTERVAL_SECONDS,
        max_workers: int = DEFAULT_HEALTH_WORKERS,
        on_result: Callable[[dict[str, bool]], None] | None = None,
    ) -> None:
        self._ssot = ssot_registry
        self._interval_seconds = max(0.05, interval_seconds)
        self._max_workers = max(1, max_workers)
        self._on_result = on_result
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="VIAMemoryWatchdog",
            daemon=True,
        )
        self._thread.start()

    def stop(self, timeout_seconds: float = 5.0) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=max(0.1, timeout_seconds))

    def scan_once(self) -> dict[str, bool]:
        results = self._ssot.health_check_all(max_workers=self._max_workers)
        if self._on_result is not None:
            self._on_result(results)
        return results

    def _run(self) -> None:
        while not self._stop_event.wait(self._interval_seconds):
            self.scan_once()
