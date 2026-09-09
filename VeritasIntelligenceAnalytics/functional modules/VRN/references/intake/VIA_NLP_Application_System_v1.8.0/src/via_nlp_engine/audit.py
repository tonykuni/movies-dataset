"""Append-only JSONL audit log protected by a SHA-256 hash chain."""

from __future__ import annotations

import hashlib
import json
import re
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
PHONE_RE = re.compile(r"(?<!\d)(?:\+?886[- ]?)?0?9\d{2}[- ]?\d{3}[- ]?\d{3}(?!\d)")


def redact_text(text: str) -> str:
    text = EMAIL_RE.sub("<REDACTED_EMAIL>", text)
    return PHONE_RE.sub("<REDACTED_PHONE>", text)


class AuditLogger:
    def __init__(self, path: Path, hash_chain: bool = True, redact: bool = True) -> None:
        self.path = path
        self.hash_chain = hash_chain
        self.redact = redact
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._last_hash = self._recover_last_hash()

    def _recover_last_hash(self) -> str:
        if not self.path.exists() or not self.path.stat().st_size:
            return "0" * 64
        try:
            with self.path.open("rb") as handle:
                lines = handle.read().splitlines()
            return json.loads(lines[-1])["hash"]
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            return "BROKEN_CHAIN"

    def append(self, event: str, payload: dict[str, Any]) -> str:
        with self._lock:
            safe_payload = self._redact(payload) if self.redact else payload
            record: dict[str, Any] = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event": event,
                "payload": safe_payload,
                "previous_hash": self._last_hash if self.hash_chain else None,
            }
            canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            record_hash = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
            record["hash"] = record_hash
            with self.path.open("a", encoding="utf-8", newline="\n") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
                handle.flush()
            self._last_hash = record_hash
            return record_hash

    def verify(self) -> dict[str, Any]:
        previous = "0" * 64
        count = 0
        if not self.path.exists():
            return {"valid": True, "records": 0, "last_hash": previous}
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                record = json.loads(line)
                actual = record.pop("hash")
                if self.hash_chain and record.get("previous_hash") != previous:
                    return {"valid": False, "records": count, "failed_line": line_number}
                canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                expected = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
                if actual != expected:
                    return {"valid": False, "records": count, "failed_line": line_number}
                previous = actual
                count += 1
        return {"valid": True, "records": count, "last_hash": previous}

    def _redact(self, value: Any) -> Any:
        if isinstance(value, str):
            return redact_text(value)
        if isinstance(value, dict):
            return {key: self._redact(item) for key, item in value.items()}
        if isinstance(value, list):
            return [self._redact(item) for item in value]
        return value

