"""Singleton SSOT runtime registry with RW locking and durable URN allocation."""

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

import json
import os
import re
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

from .config import (
    DEFAULT_CAPABILITY_MAX_LENGTH,
    DEFAULT_HEALTH_WORKERS,
    DEFAULT_SSOT_DATABASE,
    URN_SEQUENCE_WIDTH,
)
from .contracts import (
    ModuleManifest,
    ModuleState,
    RegistryMetricsSnapshot,
    RegistryRecordSnapshot,
    VIAModuleABC,
)
from .exceptions import (
    DependencyResolutionError,
    DuplicateModuleError,
    LifecycleError,
)


class ReadWriteLock:
    """Writer-preferring in-process RW lock to prevent registry starvation."""

    def __init__(self) -> None:
        self._condition = threading.Condition(threading.RLock())
        self._readers = 0
        self._writer = False
        self._waiting_writers = 0

    @contextmanager
    def read_locked(self) -> Iterator[None]:
        with self._condition:
            while self._writer or self._waiting_writers > 0:
                self._condition.wait()
            self._readers += 1
        try:
            yield
        finally:
            with self._condition:
                self._readers -= 1
                if self._readers == 0:
                    self._condition.notify_all()

    @contextmanager
    def write_locked(self) -> Iterator[None]:
        with self._condition:
            self._waiting_writers += 1
            try:
                while self._writer or self._readers > 0:
                    self._condition.wait()
                self._writer = True
            finally:
                self._waiting_writers -= 1
        try:
            yield
        finally:
            with self._condition:
                self._writer = False
                self._condition.notify_all()


@dataclass(slots=True)
class RegistryMetrics:
    success_count: int = 0
    failure_count: int = 0
    validation_rejection_count: int = 0
    timeout_count: int = 0
    health_check_count: int = 0
    health_failure_count: int = 0
    last_latency_ms: float | None = None
    last_error: str = ""
    last_success_at: str | None = None
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def snapshot(self) -> RegistryMetricsSnapshot:
        return RegistryMetricsSnapshot(**asdict(self))


@dataclass(slots=True)
class SSOTModuleRecord:
    resource_urn: str
    manifest: ModuleManifest
    instance: VIAModuleABC | None
    state: ModuleState
    dependencies: tuple[str, ...]
    source_ref: str
    source_sha256: str
    process_id: int
    instance_locator: str
    registered_at: str
    descriptor: Any | None = None
    metrics: RegistryMetrics = field(default_factory=RegistryMetrics)

    def snapshot(self) -> RegistryRecordSnapshot:
        return RegistryRecordSnapshot(
            resource_urn=self.resource_urn,
            module_name=self.manifest.name,
            version=self.manifest.version,
            state=self.state,
            declared_dependencies=self.manifest.dependencies,
            dependencies=self.dependencies,
            source_ref=self.source_ref,
            source_sha256=self.source_sha256,
            process_id=self.process_id,
            instance_locator=self.instance_locator,
            registered_at=self.registered_at,
            metrics=self.metrics.snapshot(),
        )


class SQLiteIdentityStore:
    """Cross-process-safe identity ledger and append-only event journal."""

    def __init__(self, database_path: Path) -> None:
        self.database_path = database_path.resolve()
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def allocate_identity(
        self,
        manifest: ModuleManifest,
        source_ref: str,
        source_sha256: str,
    ) -> tuple[str, str]:
        now = datetime.now(UTC)
        registered_at = now.isoformat()
        date_key = now.strftime("%Y%m%d")
        capability = self._normalize_capability(manifest.capability or manifest.name)

        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            existing = connection.execute(
                """
                SELECT resource_urn, registered_at
                FROM module_identity
                WHERE module_name = ? AND version = ? AND source_sha256 = ?
                """,
                (manifest.name, manifest.version, source_sha256),
            ).fetchone()
            if existing is not None:
                connection.commit()
                return str(existing[0]), str(existing[1])

            row = connection.execute(
                "SELECT next_value FROM urn_counter WHERE date_key = ?",
                (date_key,),
            ).fetchone()
            sequence = int(row[0]) if row is not None else 1
            if row is None:
                connection.execute(
                    "INSERT INTO urn_counter(date_key, next_value) VALUES (?, ?)",
                    (date_key, sequence + 1),
                )
            else:
                connection.execute(
                    "UPDATE urn_counter SET next_value = ? WHERE date_key = ?",
                    (sequence + 1, date_key),
                )

            resource_urn = (
                f"VIA-MOD-{manifest.language}-{capability}-{date_key}-"
                f"{sequence:0{URN_SEQUENCE_WIDTH}d}"
            )
            connection.execute(
                """
                INSERT INTO module_identity(
                    resource_urn, module_name, version, author, subsystem,
                    language, capability, source_ref, source_sha256,
                    registered_at, manifest_json, last_state
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    resource_urn,
                    manifest.name,
                    manifest.version,
                    manifest.author,
                    manifest.subsystem,
                    manifest.language,
                    capability,
                    source_ref,
                    source_sha256,
                    registered_at,
                    manifest.model_dump_json(),
                    ModuleState.DISCOVERED.value,
                ),
            )
            self._insert_event(
                connection,
                resource_urn,
                "IDENTITY_ALLOCATED",
                {"module_name": manifest.name, "source_sha256": source_sha256},
            )
            connection.commit()
            return resource_urn, registered_at

    def update_runtime_state(
        self,
        resource_urn: str,
        state: ModuleState,
        *,
        process_id: int,
        instance_locator: str,
        detail: dict[str, Any] | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                """
                UPDATE module_identity
                SET last_state = ?, process_id = ?, instance_locator = ?, updated_at = ?
                WHERE resource_urn = ?
                """,
                (
                    state.value,
                    process_id,
                    instance_locator,
                    datetime.now(UTC).isoformat(),
                    resource_urn,
                ),
            )
            self._insert_event(
                connection,
                resource_urn,
                "STATE_CHANGED",
                {"state": state.value, **(detail or {})},
            )
            connection.commit()

    def append_event(
        self,
        resource_urn: str,
        event_type: str,
        detail: dict[str, Any],
    ) -> None:
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            self._insert_event(connection, resource_urn, event_type, detail)
            connection.commit()

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute("PRAGMA foreign_keys=ON")
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS urn_counter (
                    date_key TEXT PRIMARY KEY,
                    next_value INTEGER NOT NULL CHECK(next_value > 0)
                );
                CREATE TABLE IF NOT EXISTS module_identity (
                    resource_urn TEXT PRIMARY KEY,
                    module_name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    author TEXT NOT NULL,
                    subsystem TEXT NOT NULL,
                    language TEXT NOT NULL,
                    capability TEXT NOT NULL,
                    source_ref TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    registered_at TEXT NOT NULL,
                    manifest_json TEXT NOT NULL,
                    last_state TEXT NOT NULL,
                    process_id INTEGER,
                    instance_locator TEXT,
                    updated_at TEXT,
                    UNIQUE(module_name, version, source_sha256)
                );
                CREATE TABLE IF NOT EXISTS registry_event (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    resource_urn TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    event_time TEXT NOT NULL,
                    detail_json TEXT NOT NULL,
                    FOREIGN KEY(resource_urn) REFERENCES module_identity(resource_urn)
                );
                """
            )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path, timeout=30.0)
        connection.execute("PRAGMA foreign_keys=ON")
        return connection

    @staticmethod
    def _insert_event(
        connection: sqlite3.Connection,
        resource_urn: str,
        event_type: str,
        detail: dict[str, Any],
    ) -> None:
        connection.execute(
            """
            INSERT INTO registry_event(resource_urn, event_type, event_time, detail_json)
            VALUES (?, ?, ?, ?)
            """,
            (
                resource_urn,
                event_type,
                datetime.now(UTC).isoformat(),
                json.dumps(detail, ensure_ascii=False, sort_keys=True),
            ),
        )

    @staticmethod
    def _normalize_capability(value: str) -> str:
        normalized = re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-").upper()
        normalized = normalized[:DEFAULT_CAPABILITY_MAX_LENGTH].strip("-")
        return normalized or "MODULE"


class _SSOTSingletonMeta(type):
    _instance: "VIASSOTRegistry | None" = None
    _lock = threading.Lock()

    def __call__(cls, database_path: Path = DEFAULT_SSOT_DATABASE) -> "VIASSOTRegistry":
        resolved = Path(database_path).resolve()
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__call__(resolved)
            elif cls._instance.database_path != resolved:
                raise LifecycleError(
                    "SSOT Registry 已存在且不可切換資料庫；"
                    f"current={cls._instance.database_path}, requested={resolved}"
                )
            return cls._instance

    def reset_for_testing(cls) -> None:
        with cls._lock:
            cls._instance = None


class VIASSOTRegistry(metaclass=_SSOTSingletonMeta):
    """The process-wide runtime SSOT; all module lookups pass through here."""

    def __init__(self, database_path: Path = DEFAULT_SSOT_DATABASE) -> None:
        self.database_path = Path(database_path).resolve()
        self._store = SQLiteIdentityStore(self.database_path)
        self._lock = ReadWriteLock()
        self._records_by_urn: dict[str, SSOTModuleRecord] = {}
        self._urn_by_name: dict[str, str] = {}

    @classmethod
    def reset_for_testing(cls) -> None:
        _SSOTSingletonMeta.reset_for_testing(cls)

    def allocate_identity(
        self,
        manifest: ModuleManifest,
        source_ref: str,
        source_sha256: str,
    ) -> tuple[str, str]:
        return self._store.allocate_identity(manifest, source_ref, source_sha256)

    def attach_runtime(
        self,
        *,
        resource_urn: str,
        registered_at: str,
        manifest: ModuleManifest,
        instance: VIAModuleABC | None,
        state: ModuleState,
        dependencies: tuple[str, ...],
        source_ref: str,
        source_sha256: str,
        descriptor: Any | None,
    ) -> SSOTModuleRecord:
        process_id = os.getpid()
        instance_locator = (
            f"memory://{process_id}/{id(instance):x}" if instance is not None else "staged://no-instance"
        )
        with self._lock.write_locked():
            existing_urn = self._urn_by_name.get(manifest.name)
            if existing_urn is not None and existing_urn != resource_urn:
                raise DuplicateModuleError(
                    f"執行期模組名稱已由其他 URN 使用: {manifest.name} -> {existing_urn}"
                )
            existing = self._records_by_urn.get(resource_urn)
            if existing is not None:
                may_promote_staged = (
                    existing.instance is None
                    and instance is not None
                    and existing.source_sha256 == source_sha256
                )
                if existing.instance is not instance and not may_promote_staged:
                    raise DuplicateModuleError(f"URN 已掛載其他實例: {resource_urn}")
            record = SSOTModuleRecord(
                resource_urn=resource_urn,
                manifest=manifest,
                instance=instance,
                state=state,
                dependencies=dependencies,
                source_ref=source_ref,
                source_sha256=source_sha256,
                process_id=process_id,
                instance_locator=instance_locator,
                registered_at=registered_at,
                descriptor=descriptor,
            )
            self._records_by_urn[resource_urn] = record
            self._urn_by_name[manifest.name] = resource_urn
        self._store.update_runtime_state(
            resource_urn,
            state,
            process_id=process_id,
            instance_locator=instance_locator,
        )
        return record

    def set_state(
        self,
        reference: str,
        state: ModuleState,
        *,
        detail: dict[str, Any] | None = None,
    ) -> None:
        with self._lock.write_locked():
            record = self._resolve_unlocked(reference)
            record.state = state
            process_id = record.process_id
            instance_locator = record.instance_locator
            resource_urn = record.resource_urn
        self._store.update_runtime_state(
            resource_urn,
            state,
            process_id=process_id,
            instance_locator=instance_locator,
            detail=detail,
        )

    def detach_runtime(self, reference: str) -> None:
        with self._lock.write_locked():
            record = self._resolve_unlocked(reference)
            resource_urn = record.resource_urn
            module_name = record.manifest.name
            record.state = ModuleState.UNLOADED
            del self._records_by_urn[resource_urn]
            self._urn_by_name.pop(module_name, None)
        self._store.update_runtime_state(
            resource_urn,
            ModuleState.UNLOADED,
            process_id=os.getpid(),
            instance_locator="unloaded://none",
        )

    def resolve(self, reference: str) -> SSOTModuleRecord:
        with self._lock.read_locked():
            return self._resolve_unlocked(reference)

    def resolve_dependency(self, reference: str) -> SSOTModuleRecord:
        normalized = reference.strip()
        with self._lock.read_locked():
            if normalized.lower().startswith("urn:via:"):
                suffix = normalized.rsplit(":", 1)[-1]
                candidates = [
                    item
                    for item in self._records_by_urn.values()
                    if item.manifest.name.lower() == suffix.lower()
                    or (item.manifest.capability or "").lower() == suffix.lower()
                ]
                if len(candidates) != 1:
                    raise DependencyResolutionError(
                        f"Legacy URN 無法唯一解析: {reference}"
                    )
                return candidates[0]
            return self._resolve_unlocked(normalized)

    def list_records(self, *, include_staged: bool = True) -> tuple[SSOTModuleRecord, ...]:
        with self._lock.read_locked():
            records = tuple(self._records_by_urn.values())
        if include_staged:
            return tuple(sorted(records, key=lambda item: item.resource_urn))
        return tuple(
            sorted(
                (item for item in records if item.instance is not None),
                key=lambda item: item.resource_urn,
            )
        )

    def find_dependents(self, reference: str) -> tuple[SSOTModuleRecord, ...]:
        target = self.resolve(reference)
        with self._lock.read_locked():
            dependents = tuple(
                item
                for item in self._records_by_urn.values()
                if target.resource_urn in item.dependencies
            )
        return tuple(sorted(dependents, key=lambda item: item.resource_urn))

    def record_metric(
        self,
        reference: str,
        event: str,
        *,
        latency_ms: float | None = None,
        error: str = "",
    ) -> None:
        now = datetime.now(UTC).isoformat()
        with self._lock.write_locked():
            record = self._resolve_unlocked(reference)
            metrics = record.metrics
            if event == "SUCCESS":
                metrics.success_count += 1
                metrics.last_success_at = now
            elif event == "FAILURE":
                metrics.failure_count += 1
            elif event == "VALIDATION_REJECTION":
                metrics.validation_rejection_count += 1
            elif event == "TIMEOUT":
                metrics.timeout_count += 1
            elif event == "HEALTH_SUCCESS":
                metrics.health_check_count += 1
            elif event == "HEALTH_FAILURE":
                metrics.health_check_count += 1
                metrics.health_failure_count += 1
            else:
                raise ValueError(f"不支援的 Metrics event: {event}")
            metrics.last_latency_ms = latency_ms
            metrics.last_error = error
            metrics.updated_at = now
            resource_urn = record.resource_urn
        self._store.append_event(
            resource_urn,
            f"METRIC_{event}",
            {"latency_ms": latency_ms, "error": error},
        )

    def health_check_all(
        self,
        *,
        max_workers: int = DEFAULT_HEALTH_WORKERS,
    ) -> dict[str, bool]:
        checkable_states = {
            ModuleState.READY,
            ModuleState.DEGRADED,
            ModuleState.UNHEALTHY,
        }
        records = [
            item
            for item in self.list_records(include_staged=False)
            if item.instance and item.state in checkable_states
        ]
        results: dict[str, bool] = {}

        def def_check(record: SSOTModuleRecord) -> tuple[str, bool, str]:
            try:
                healthy = bool(record.instance and record.instance.health_check())
                return record.resource_urn, healthy, ""
            except Exception as exc:
                return record.resource_urn, False, str(exc)

        with ThreadPoolExecutor(max_workers=max(1, max_workers)) as executor:
            futures = {executor.submit(def_check, record): record for record in records}
            for future in as_completed(futures):
                resource_urn, healthy, error = future.result()
                results[resource_urn] = healthy
                self.record_metric(
                    resource_urn,
                    "HEALTH_SUCCESS" if healthy else "HEALTH_FAILURE",
                    error=error or ("health_check returned False" if not healthy else ""),
                )
                self.set_state(
                    resource_urn,
                    ModuleState.READY if healthy else ModuleState.UNHEALTHY,
                    detail={"health_check": healthy},
                )
        return dict(sorted(results.items()))

    def snapshot_catalog(self) -> dict[str, Any]:
        records = [
            item.snapshot().model_dump(mode="json")
            for item in self.list_records(include_staged=True)
        ]
        return {
            "ssot_version": "2.0",
            "database_path": str(self.database_path),
            "runtime_record_count": len(records),
            "records": records,
        }

    def _resolve_unlocked(self, reference: str) -> SSOTModuleRecord:
        if reference in self._records_by_urn:
            return self._records_by_urn[reference]
        resource_urn = self._urn_by_name.get(reference)
        if resource_urn is not None:
            return self._records_by_urn[resource_urn]
        raise DependencyResolutionError(f"SSOT 找不到模組或 URN: {reference}")
