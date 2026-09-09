"""Bounded SQLite cache and resumable job checkpoint store."""

from __future__ import annotations

import hashlib
import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any


class SQLiteCache:
    def __init__(self, path: Path, config: dict[str, Any]) -> None:
        self.path = path
        self.config = config
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._connection = sqlite3.connect(str(path), check_same_thread=False, timeout=30)
        self._connection.execute("PRAGMA journal_mode=WAL")
        self._connection.execute("PRAGMA synchronous=NORMAL")
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS cache (key TEXT PRIMARY KEY, value BLOB NOT NULL, created REAL NOT NULL, accessed REAL NOT NULL)"
        )
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS checkpoints (job_id TEXT NOT NULL, item_key TEXT NOT NULL, result BLOB NOT NULL, created REAL NOT NULL, PRIMARY KEY(job_id, item_key))"
        )
        self._connection.commit()

    @staticmethod
    def make_key(payload: dict[str, Any]) -> str:
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def get(self, key: str) -> dict[str, Any] | None:
        if not self.config["enabled"]:
            return None
        now = time.time()
        ttl = float(self.config["ttl_seconds"])
        with self._lock:
            row = self._connection.execute("SELECT value, created FROM cache WHERE key=?", (key,)).fetchone()
            if row is None:
                return None
            if now - float(row[1]) > ttl:
                self._connection.execute("DELETE FROM cache WHERE key=?", (key,))
                self._connection.commit()
                return None
            self._connection.execute("UPDATE cache SET accessed=? WHERE key=?", (now, key))
            self._connection.commit()
        return json.loads(row[0])

    def set(self, key: str, value: dict[str, Any]) -> bool:
        if not self.config["enabled"]:
            return False
        raw = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        if len(raw) > int(self.config["max_value_bytes"]):
            return False
        now = time.time()
        with self._lock:
            self._connection.execute(
                "INSERT OR REPLACE INTO cache(key, value, created, accessed) VALUES(?,?,?,?)",
                (key, raw, now, now),
            )
            self._prune_locked()
            self._connection.commit()
        return True

    def _prune_locked(self) -> None:
        count = self._connection.execute("SELECT COUNT(*) FROM cache").fetchone()[0]
        excess = count - int(self.config["max_entries"])
        if excess > 0:
            self._connection.execute(
                "DELETE FROM cache WHERE key IN (SELECT key FROM cache ORDER BY accessed ASC LIMIT ?)",
                (excess,),
            )

    def checkpoint_get(self, job_id: str, item_key: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT result FROM checkpoints WHERE job_id=? AND item_key=?", (job_id, item_key)
            ).fetchone()
        return json.loads(row[0]) if row else None

    def checkpoint_set(self, job_id: str, item_key: str, result: dict[str, Any]) -> None:
        raw = json.dumps(result, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        with self._lock:
            self._connection.execute(
                "INSERT OR REPLACE INTO checkpoints(job_id, item_key, result, created) VALUES(?,?,?,?)",
                (job_id, item_key, raw, time.time()),
            )
            self._connection.commit()

    def close(self) -> None:
        with self._lock:
            self._connection.close()

