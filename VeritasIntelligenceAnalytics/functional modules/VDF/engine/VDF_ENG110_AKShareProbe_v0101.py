#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe AKShare macro candidates. One request cannot block the door."""
from __future__ import annotations

import importlib.util
import json
import os
import socket
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
HTTP_TIMEOUT = 30


def _prior():
    spec = importlib.util.spec_from_file_location("ak_v0100", HERE / "VDF_ENG110_AKShareProbe_v0100.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _patch_requests():
    import requests
    original = requests.get

    def limited(*args, **kwargs):
        kwargs.setdefault("timeout", HTTP_TIMEOUT)
        return original(*args, **kwargs)

    requests.get = limited
    return original


def probe() -> dict:
    prior = _prior()
    socket.setdefaulttimeout(HTTP_TIMEOUT)
    try:
        import akshare as ak
    except ImportError:
        ak = None
    original = _patch_requests() if ak is not None else None
    rows = []
    try:
        for group, name, fns in prior.candidates():
            for fn in fns:
                row = {"id": fn, "group": group, "name": name}
                if ak is None:
                    row.update({"state": "ABSENT", "why": "akshare is not installed"})
                elif not hasattr(ak, fn):
                    row.update({"state": "MISSING", "why": "function is not on this akshare"})
                else:
                    try:
                        frame = getattr(ak, fn)()
                        n = len(frame) if hasattr(frame, "__len__") else None
                        row.update({"state": "LIVE", "rows": n})
                    except Exception as exc:
                        row.update({"state": "FAIL", "why": type(exc).__name__})
                rows.append(row)
    finally:
        if original is not None:
            import requests
            requests.get = original
    counts = {}
    for row in rows:
        counts[row["state"]] = counts.get(row["state"], 0) + 1
    verified = [row["id"] for row in rows if row["state"] == "LIVE"]
    return {
        "via": "vcgc",
        "door": "VDF_ENG110_AKShareProbe_v0101",
        "probed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "groups": len(prior.candidates()),
        "functions": len(rows),
        "installed": ak is not None,
        "http_timeout": HTTP_TIMEOUT,
        "counts": counts,
        "verified": verified,
        "rows": rows,
        "intake_edited": False,
        "tree_edited": False,
        "do_not": [
            "pip install akshare from this door",
            "record a function that was not called",
            "let akshare replace FRED",
            "edit intake macro_ssot",
            "wait forever on a proxy tunnel",
        ],
        "next": "none" if verified else "install akshare yourself, then run this door again",
    }


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY"}, ensure_ascii=False))
        return 2
    card = probe()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["installed"] else 2


def selftest() -> int:
    import requests
    prior = _prior()
    real = requests.get
    seen = {}

    def boom(*args, **kwargs):
        seen["timeout"] = kwargs.get("timeout")
        raise TimeoutError("proxy")

    requests.get = boom
    try:
        _patch_requests()
        try:
            requests.get("https://example.invalid")
            raised = False
        except TimeoutError:
            raised = True
    finally:
        requests.get = real
    ok = len(prior.candidates()) == 16 and raised and seen.get("timeout") == HTTP_TIMEOUT
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
