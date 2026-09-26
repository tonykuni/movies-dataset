#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Entry lock. The policy hash ignores line endings. Does not rewrite the lock."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior():
    spec = importlib.util.spec_from_file_location("entry_v0100", HERE / "CGC_MDL149_EntryLock_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def canon(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def matrix() -> dict:
    prior = _prior()
    body = prior.matrix()
    spec = json.loads(prior.LOCK.read_text(encoding="utf-8"))
    raw = prior.LAWS.read_bytes() if prior.LAWS.is_file() else b""
    live = hashlib.sha256(canon(raw)).hexdigest()[:16] if raw else ""
    body["policy"] = {"locked": live == spec.get("policy_sha16"), "sha16": live, "expected": spec.get("policy_sha16")}
    return body


def main() -> int:
    if not _prior().allowed():
        print("[入口] 拒絕。只能經 via-vcgc。")
        return 2
    body = matrix()
    prior = _prior()
    prior.OUT.parent.mkdir(parents=True, exist_ok=True)
    prior.OUT.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0 if body["policy"]["locked"] else 2


def selftest() -> int:
    prior = _prior()
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = not prior.allowed()
    os.environ["VIA_FROM_VCGC"] = "YES"
    raw = prior.LAWS.read_bytes()
    stored = json.loads(prior.LOCK.read_text(encoding="utf-8"))["policy_sha16"]
    crlf = hashlib.sha256(raw.replace(b"\n", b"\r\n")).hexdigest()[:16]
    body = matrix()
    ok = denied and body["policy"]["locked"] and hashlib.sha256(canon(raw.replace(b"\n", b"\r\n"))).hexdigest()[:16] == stored and crlf != stored
    print("  [OK]" if ok else "  [FAIL] " + json.dumps(body["policy"], ensure_ascii=False))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
