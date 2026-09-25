#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN reads the sealed TWSE/TPEX/yfinance rows. It does not fetch them again."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LOCK = VIA / "supportive modules" / "registry" / "VIA_SourceLaneLock_v0100.json"


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def locked_rows() -> dict:
    data = json.loads(LOCK.read_text(encoding="utf-8"))
    return {row["code"]: row for row in data["rows"]}


def quote_for(code: str) -> dict:
    bare = str(code or "").split(".")[0].strip()
    row = locked_rows().get(bare)
    if not row or not row.get("overlap"):
        return {"state": "NODATA", "code": bare}
    return {"state": "OK", "code": bare, "symbol": row["symbol"], "market": row["market"],
            "close": row["exchange_close"], "adj_close": row["adj_close"]}


def survey(folder: Path) -> dict:
    if not folder.is_dir():
        return {"state": "ABSENT", "path": str(folder), "stock": 0, "other": 0, "priced": []}
    parser = _load(HERE / "VRN_ENG084_FilenameTokenParse_v0100.py", "fn84")
    stock = other = 0
    priced = []
    for item in sorted(folder.iterdir()):
        if not item.is_file():
            continue
        parsed = parser.parse_filename(item.stem)
        tick = parsed.get("ticker") or {}
        code = tick.get("canonical") or ""
        if tick.get("state") == "GREEN" and code:
            stock += 1
            got = quote_for(code)
            if got["state"] == "OK":
                priced.append({"file": item.name, "symbol": got["symbol"], "close": got["close"]})
        else:
            other += 1
    return {"state": "OK", "path": str(folder), "stock": stock, "other": other, "priced": priced}


def selftest() -> int:
    ok = quote_for("2330")["symbol"] == "2330.TW" and quote_for("6488.TWO")["close"] == 948
    ok = ok and quote_for("9999")["state"] == "NODATA"
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest())
