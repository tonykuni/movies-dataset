#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Show the fetch inputs and database inventory. Export a short slice, not the whole table."""
from __future__ import annotations

import csv
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VDF = HERE.parent
VIA = VDF.parents[1]
BOOK = VIA / "supportive modules" / "registry" / "VIA_VDF_FetchMatrix_v0100.json"
OVERRIDE = VIA / "supportive modules" / "registry" / "VIA_VDF_FetchOverride_v0100.json"
OUT = VDF / "output_hub" / "export"
SLICE = 20


def allowed() -> bool:
    return os.environ.get("VIA_CENTRAL_ENTRY") == "1" and os.environ.get("VIA_FROM_VCGC") == "YES"


def _book() -> dict:
    book = json.loads(BOOK.read_text(encoding="utf-8"))
    if OVERRIDE.is_file():
        over = json.loads(OVERRIDE.read_text(encoding="utf-8"))
        for row in book["classes"]:
            patch = (over.get("classes") or {}).get(row["id"]) or {}
            if "on" in patch:
                row["on"] = bool(patch["on"])
            if "since" in patch:
                row["since"] = patch["since"]
        book["pick_class"] = over.get("pick_class")
        book["pick_db"] = over.get("pick_db")
    return book


def _picked(book: dict, kind: str, ident: str, default: bool) -> bool:
    chosen = book.get(kind)
    if not chosen:
        return default
    return ident in chosen


def inventory(root: Path) -> list[dict]:
    import duckdb
    found = []
    for path in sorted(root.rglob("*.duckdb")):
        item = {"file": path.name, "path": str(path), "tables": [], "state": "OK"}
        try:
            con = duckdb.connect(str(path), read_only=True)
            names = [row[0] for row in con.execute("SHOW TABLES").fetchall()]
            for name in names:
                if not name.replace("_", "").isalnum():
                    continue
                count = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
                cols = [row[0] for row in con.execute(f"DESCRIBE {name}").fetchall()]
                item["tables"].append({"name": name, "rows": int(count), "columns": cols})
            con.close()
        except Exception as exc:
            item["state"] = type(exc).__name__
        found.append(item)
    return found


def _slice(path: Path, table: str) -> list[dict]:
    import duckdb
    if not table.replace("_", "").isalnum():
        return []
    con = duckdb.connect(str(path), read_only=True)
    cols = [row[0] for row in con.execute(f"DESCRIBE {table}").fetchall()]
    order = "date" if "date" in cols else cols[0]
    frame = con.execute(
        f"SELECT * FROM {table} ORDER BY {order} DESC LIMIT {SLICE}"
    ).fetchdf()
    con.close()
    return json.loads(frame.to_json(orient="records", date_format="iso"))


def _write(book: dict, dbs: list[dict], dest: Path) -> dict:
    dest.mkdir(parents=True, exist_ok=True)
    classes = []
    for row in book["classes"]:
        since = row["since"] or book["default_since"]
        classes.append({
            "id": row["id"],
            "name": row["name"],
            "on": row["on"],
            "since": since,
            "selected": _picked(book, "pick_class", row["id"], row["on"]),
        })
    chosen_db = []
    slices = []
    for item in dbs:
        selected = _picked(book, "pick_db", item["file"], item["state"] == "OK")
        chosen_db.append({"file": item["file"], "state": item["state"], "selected": selected, "tables": item["tables"]})
        if not selected or item["state"] != "OK":
            continue
        for table in item["tables"]:
            rows = _slice(Path(item["path"]), table["name"])
            slices.append({"file": item["file"], "table": table["name"], "rows": rows})
            _csv(dest / f"{Path(item['file']).stem}_{table['name']}.csv", rows)
    status = {"classes": classes, "databases": chosen_db, "slice_rows": SLICE, "encoding": "utf-8-sig"}
    (dest / "VDF_Export_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=1), encoding="utf-8")
    _csv(dest / "VDF_Export_status.csv", classes)
    gsheet = dest / "VDF_Export_gsheet.csv"
    gsheet.write_bytes((dest / "VDF_Export_status.csv").read_bytes())
    (dest / "VDF_Export_status.md").write_text(_md(classes, chosen_db, slices), encoding="utf-8")
    return {"dir": str(dest), "classes": len(classes), "databases": len(chosen_db), "slices": len(slices), "gsheet": gsheet.name}


def _csv(path: Path, rows: list[dict]) -> None:
    fields = list(rows[0].keys()) if rows else ["id"]
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore", lineterminator="\r\n")
        writer.writeheader()
        writer.writerows(rows)


def _md(classes: list[dict], dbs: list[dict], slices: list[dict]) -> str:
    lines = ["# VDF 輸入與局部輸出", "", "|選|編碼|名稱|起始|", "|---|---|---|---|"]
    for row in classes:
        mark = "x" if row["selected"] else " "
        lines.append(f"|{mark}|{row['id']}|{row['name']}|{row['since']}|")
    lines += ["", "|選|資料庫|狀態|表|", "|---|---|---|---|"]
    for item in dbs:
        mark = "x" if item["selected"] else " "
        names = ",".join(table["name"] for table in item["tables"]) or "-"
        lines.append(f"|{mark}|{item['file']}|{item['state']}|{names}|")
    lines.append("")
    for part in slices:
        lines.append(f"## {part['file']} {part['table']} 前 {len(part['rows'])} 列")
        if not part["rows"]:
            lines.append("")
            continue
        fields = list(part["rows"][0].keys())
        lines.append("|" + "|".join(fields) + "|")
        lines.append("|" + "|".join("---" for _ in fields) + "|")
        for row in part["rows"]:
            lines.append("|" + "|".join(str(row.get(field, "")) for field in fields) + "|")
        lines.append("")
    return "\n".join(lines)


def run(root: Path, dest: Path) -> dict:
    book = _book()
    dbs = inventory(root)
    wrote = _write(book, dbs, dest)
    return {
        "via": "vcgc",
        "door": "VDF_ENG118_ExportDesk_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "default_since": book["default_since"],
        "classes": wrote["classes"],
        "databases": wrote["databases"],
        "slices": wrote["slices"],
        "slice_rows": SLICE,
        "encoding": "utf-8-sig",
        "gsheet": "csv import; no Sheets connector",
        "edit": OVERRIDE.name,
        "dir": wrote["dir"],
        "hub_edited": False,
        "intake_edited": False,
        "fetched": False,
        "do_not": [
            "export a whole table",
            "open the database for writing from this door",
            "edit intake macro_ssot",
            "save csv as cp950",
        ],
        "next": "none",
    }


def main() -> int:
    if not allowed():
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-export through Invoke-VIAPython"}, ensure_ascii=False))
        return 2
    card = run(VDF / "output_hub", OUT)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0


def selftest() -> int:
    import duckdb
    root = Path("/tmp/vdf_export_self")
    if root.exists():
        for path in root.rglob("*"):
            if path.is_file():
                path.unlink()
    db_dir = root / "mega"
    db_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(db_dir / "sample.duckdb"))
    con.execute("CREATE TABLE us_macro (date DATE, series VARCHAR, value DOUBLE)")
    con.execute("INSERT INTO us_macro VALUES ('2026-09-25', 'RRPONTSYD', 1.5), ('2026-09-24', '測試', 2.0)")
    con.close()
    card = run(root, root / "export")
    csv_bytes = (root / "export" / "sample_us_macro.csv").read_bytes()
    md = (root / "export" / "VDF_Export_status.md").read_text(encoding="utf-8")
    ok = (
        csv_bytes.startswith(b"\xef\xbb\xbf")
        and "測試".encode("utf-8") in csv_bytes
        and "VDF-TW-EQ" in md
        and card["slice_rows"] == 20
        and card["fetched"] is False
        and card["gsheet"].startswith("csv import")
    )
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
