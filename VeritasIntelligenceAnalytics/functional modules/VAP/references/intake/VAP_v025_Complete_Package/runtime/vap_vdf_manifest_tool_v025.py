#!/usr/bin/env python3
"""VDF handoff manifest fingerprint and validation helper for VAP v025."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
from typing import Any


# def 01 PARAMETERS
SCHEMA = "VIA-VDF-VAP-CONNECTION-MANIFEST/1.0"
STOCK_CLASSES = {"STOCK", "EQUITY", "ETF", "STOCK_INDEX"}


def def_canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def def_connection_fingerprint(connection: dict[str, Any]) -> str:
    payload = {key: value for key, value in connection.items() if key != "fingerprint"}
    return hashlib.sha256(def_canonical_json(payload).encode("utf-8")).hexdigest()


def def_validate_connection(connection: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field in ("contractId", "sourceId", "state", "engine", "assetClass"):
        if not str(connection.get(field, "")).strip():
            errors.append("MISSING_" + field.upper())
    if connection.get("state") == "AUTHORIZED" and not connection.get("readOnly", False):
        errors.append("AUTHORIZED_CONNECTION_MUST_BE_READ_ONLY")
    if str(connection.get("assetClass", "")).upper() in STOCK_CLASSES:
        if not str(connection.get("adjustedPriceField", "")).lower().startswith(("adj", "adjusted")):
            errors.append("ADJUSTED_PRICE_FIELD_REQUIRED")
        ta_lib = dict(connection.get("taLibEvidence", {}))
        if ta_lib.get("engine") != "TA-Lib" or ta_lib.get("status") != "PASS":
            errors.append("TALIB_PASS_EVIDENCE_REQUIRED")
    expected = def_connection_fingerprint(connection)
    if connection.get("fingerprint") != expected:
        errors.append("FINGERPRINT_MISMATCH")
    return errors


def def_atomic_write(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def def_parse_args() -> argparse.Namespace:
    default = Path(__file__).resolve().parents[1] / "config" / "vdf_connection_manifest.json"
    parser = argparse.ArgumentParser(description="Validate or fingerprint a VDF → VAP connection manifest")
    parser.add_argument("--manifest", default=str(default))
    parser.add_argument("--seal-source", default=None, help="Recompute one existing connection fingerprint; does not change its state")
    return parser.parse_args()


def def_main() -> int:
    args = def_parse_args()
    path = Path(args.manifest).resolve()
    manifest = json.loads(path.read_text(encoding="utf-8-sig"))
    if manifest.get("schema") != SCHEMA or not isinstance(manifest.get("connections"), list):
        print(json.dumps({"status": "FAIL", "errors": ["MANIFEST_SCHEMA_INVALID"]}, ensure_ascii=False, indent=2))
        return 2
    if args.seal_source:
        connection = next((item for item in manifest["connections"] if str(item.get("sourceId")) == args.seal_source), None)
        if not connection:
            print(json.dumps({"status": "FAIL", "errors": ["SOURCE_NOT_FOUND"]}, ensure_ascii=False, indent=2))
            return 3
        connection["fingerprint"] = def_connection_fingerprint(connection)
        def_atomic_write(path, manifest)
    records = []
    for connection in manifest["connections"]:
        errors = def_validate_connection(connection)
        records.append({"sourceId": connection.get("sourceId"), "contractId": connection.get("contractId"), "status": "PASS" if not errors else "FAIL", "errors": errors})
    result = {"schema": SCHEMA, "version": "v025", "status": "PASS" if all(item["status"] == "PASS" for item in records) else "FAIL", "records": records}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(def_main())
