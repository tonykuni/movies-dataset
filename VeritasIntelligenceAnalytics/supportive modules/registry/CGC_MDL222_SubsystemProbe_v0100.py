#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Probe the subsystem tails from VCGC and sync the seat when a newer tail appears.

The engines are not rewritten. A tail that does not mention VCGC stays yellow.
"""
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
import html
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
SEAT = HERE / "VIA_VCGC_SubsystemSeat_v0100.json"
PAGE = VIA / "VIA_Reports" / "vcgc" / "VIA_Subsystem_Matrix_v0100.html"
FAMILIES = (
    ("VCGC", HERE, "CGC_SystemManager_v*.py"),
    ("CONSOLE", HERE, "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py"),
    ("VDF", VIA / "functional modules" / "VDF", "VDF_SystemManager_v*.py"),
    ("VRN", VIA / "functional modules" / "VRN", "VRN_SystemManager_v*.py"),
    ("NLP", VIA / "supportive modules" / "70_VRN_Rules", "SUP_MDL866_VIAUnifiedNLPOrchestrator_v*.py"),
    ("LAYOUT", VIA / "supportive modules" / "70_VRN_Rules", "SUP_MDL743_GenericLayoutHub_v*.py"),
)


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = sorted(folder.glob(pattern))
    return hits[-1] if hits else None


def seen() -> list[dict]:
    seat = json.loads(SEAT.read_text(encoding="utf-8"))
    named = seat.get("tails") or {}
    rows = []
    for system, folder, pattern in FAMILIES:
        path = _newest(folder, pattern)
        disk = path.name if path else ""
        text = path.read_text(encoding="utf-8", errors="ignore") if path else ""
        mark = "GREEN" if "VIA_FROM_VCGC" in text else "YELLOW"
        same = disk == named.get(system) and bool(disk)
        rows.append({
            "lamp": "GREEN" if same and mark == "GREEN" else ("YELLOW" if disk else "RED"),
            "system": system,
            "seat": named.get(system) or "",
            "disk": disk,
            "mark": mark,
            "same": same,
        })
    return rows


def write_seat(rows: list[dict]) -> None:
    seat = json.loads(SEAT.read_text(encoding="utf-8"))
    seat["tails"] = {row["system"]: row["disk"] for row in rows if row["disk"]}
    seat["book_edited"] = False
    SEAT.write_text(json.dumps(seat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def check() -> dict:
    rows = seen()
    drift = [row["system"] for row in rows if not row["same"]]
    unmarked = [row["system"] for row in rows if row["mark"] != "GREEN"]
    missing = drift + unmarked
    return {
        "via": "vcgc",
        "door": "CGC_MDL222_SubsystemProbe_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not missing,
        "lock_record": SEAT.name,
        "page": str(PAGE),
        "rows": rows,
        "drift": drift,
        "unmarked": unmarked,
        "synced": False,
        "fetched": False,
        "book_edited": False,
        "intake_edited": False,
        "missing": missing,
        "do_not": [
            "rewrite an engine to remove the difference",
            "start a download from this probe",
            "treat the HTML as a second registry",
            "edit intake macro_ssot",
        ],
        "next": "none" if not missing else "sync the seat, do not rewrite the engine",
    }


def _table(title: str, heads: list[str], rows: list[list[str]]) -> str:
    body = "".join(
        "<tr>" + "".join("<td>%s</td>" % html.escape(cell) for cell in row) + "</tr>"
        for row in rows
    )
    head = "".join("<th>%s</th>" % html.escape(cell) for cell in heads)
    return "<section><h2>%s</h2><table><tr>%s</tr>%s</table></section>" % (html.escape(title), head, body)


def write_page(card: dict) -> None:
    systems = [
        [row["lamp"], row["system"], row["disk"], row["mark"]]
        for row in card["rows"]
    ]
    drift = [
        [row["system"], row["seat"] or "—", row["disk"] or "—"]
        for row in card["rows"]
    ]
    rules = [
        ["GREEN", "entry", "via-vcgc only"],
        ["GREEN", "sync", "seat file only"],
        ["YELLOW" if card["drift"] else "GREEN", "drift", ", ".join(card["drift"]) or "none"],
    ]
    page = """<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>VCGC subsystem matrix</title>
<style>
body{margin:0;background:#121614;color:#d5ddd6;font:11px/1.35 ui-sans-serif,sans-serif}
main{max-width:1100px;margin:auto;padding:14px}
h1{font-size:14px;font-weight:650;margin:0 0 8px;letter-spacing:.03em}
h2{font-size:11px;color:#8e9b93;font-weight:650;margin:14px 0 6px}
table{border-collapse:collapse;width:100%;table-layout:auto}
th,td{border-bottom:1px solid #2c3832;padding:4px 6px;text-align:left;vertical-align:top;white-space:normal;word-break:break-word}
th{color:#8e9b93;font-weight:650}
td:first-child{font-weight:700}
</style><main><h1>VCGC SUBSYSTEM MATRIX</h1>__BODY__</main></html>"""
    body = _table("系統", ["lamp", "system", "tail", "vcgc mark"], systems)
    body += _table("座位對磁碟", ["system", "seat", "disk"], drift)
    body += _table("入口", ["lamp", "check", "detail"], rules)
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(page.replace("__BODY__", body), encoding="utf-8")


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = check()
    if card["drift"]:
        write_seat(card["rows"])
        card = check()
        card["synced"] = True
        card["next"] = "none" if card["lock_success"] else "the new tail has no VCGC mark"
    write_page(card)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    write_page(card)
    ok = denied and card["lock_success"] and PAGE.is_file() and "word-break:break-word" in PAGE.read_text(encoding="utf-8")
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
