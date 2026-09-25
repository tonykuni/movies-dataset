"""Crash-resistant file queue for long-running batch work."""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Any


STAGES = ("pending", "processing", "completed", "failed")


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f".{os.getpid()}.{uuid.uuid4().hex}.tmp")
    raw = json.dumps(value, ensure_ascii=False, indent=2)
    with temp.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temp, path)


class JobQueue:
    def __init__(self, root: Path, max_retries: int = 3) -> None:
        self.root = root
        self.max_retries = max_retries
        for stage in STAGES:
            (root / stage).mkdir(parents=True, exist_ok=True)

    def submit(self, payload: dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        record = {
            "job_id": job_id,
            "status": "pending",
            "created_at": time.time(),
            "updated_at": time.time(),
            "attempts": 0,
            "payload": payload,
        }
        atomic_write_json(self.root / "pending" / f"{job_id}.json", record)
        return job_id

    def claim_next(self) -> dict[str, Any] | None:
        for source in sorted((self.root / "pending").glob("*.json"), key=lambda item: item.stat().st_mtime):
            target = self.root / "processing" / source.name
            if target.exists():
                continue
            try:
                os.replace(source, target)
            except (FileNotFoundError, PermissionError):
                continue
            try:
                record = json.loads(target.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                os.replace(target, self.root / "failed" / target.name)
                continue
            record["status"] = "processing"
            record["updated_at"] = time.time()
            record["attempts"] = int(record.get("attempts", 0)) + 1
            atomic_write_json(target, record)
            return record
        return None

    def complete(self, job_id: str, result: dict[str, Any]) -> None:
        path = self.root / "processing" / f"{job_id}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record.update({"status": "completed", "result": result, "updated_at": time.time()})
        atomic_write_json(path, record)
        os.replace(path, self.root / "completed" / path.name)

    def fail(self, job_id: str, error: str) -> None:
        path = self.root / "processing" / f"{job_id}.json"
        record = json.loads(path.read_text(encoding="utf-8"))
        record.update({"status": "failed", "error": error[:2000], "updated_at": time.time()})
        atomic_write_json(path, record)
        os.replace(path, self.root / "failed" / path.name)

    def status(self, job_id: str) -> dict[str, Any] | None:
        for stage in STAGES:
            path = self.root / stage / f"{job_id}.json"
            if path.exists():
                return json.loads(path.read_text(encoding="utf-8"))
        return None

    def recover_stale(self, stale_seconds: float = 600) -> dict[str, int]:
        now = time.time()
        recovered = failed = 0
        for path in (self.root / "processing").glob("*.json"):
            if now - path.stat().st_mtime < stale_seconds:
                continue
            try:
                record = json.loads(path.read_text(encoding="utf-8"))
                if int(record.get("attempts", 0)) >= self.max_retries:
                    record.update({"status": "failed", "error": "retry limit exceeded", "updated_at": now})
                    atomic_write_json(path, record)
                    os.replace(path, self.root / "failed" / path.name)
                    failed += 1
                else:
                    record.update({"status": "pending", "updated_at": now})
                    atomic_write_json(path, record)
                    os.replace(path, self.root / "pending" / path.name)
                    recovered += 1
            except (OSError, ValueError, json.JSONDecodeError):
                try:
                    os.replace(path, self.root / "failed" / path.name)
                    failed += 1
                except OSError:
                    pass
        return {"recovered": recovered, "failed": failed}
