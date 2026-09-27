#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Manager matrix. One list of the three system managers and the two support faces.

What a later UI should show
    entry    via-vcgc matrix
    columns  lamp, system, tail, role
    vcgc     CGC_SystemManager_v0106.py names this list, then returns to v0105
    vdf      VDF_SystemManager_v0113.py names this list, then returns to v0112
    vrn      VRN_SystemManager_v0107.py names this list, then returns to v0106
    nlp      text and file stay on the orchestrator. OneEngine 1.9.0 is not the PDF path
    layout   body stays v0104. v0105 only points at OCR

Rules
    A missing file is RED. This door does not start a manager, fetch, or write a database.
    The HTML is a view under VIA_Reports. It is not a second registry.
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
VIA = HERE.parent.parent
PAGE = VIA / "VIA_Reports" / "VIA_Manager_Matrix_v0100.html"
ROWS = (
    ("VCGC", "supportive modules/registry/CGC_SystemManager_v0106.py", "matrix 後回到 v0105 資料席"),
    ("VDF", "functional modules/VDF/VDF_SystemManager_v0113.py", "matrix 後回到 v0112，status 不擷取"),
    ("VRN", "functional modules/VRN/VRN_SystemManager_v0107.py", "matrix 後回到 v0106，本體仍是 v0104"),
    ("NLP", "supportive modules/70_VRN_Rules/SUP_MDL866_VIAUnifiedNLPOrchestrator_v0103.py", "文字走 v0102，檔案走 ENG087"),
    ("LAYOUT", "supportive modules/70_VRN_Rules/SUP_MDL743_GenericLayoutHub_v0104.py", "v0105 只指 OCR，v0100 與 v0101 留著"),
)


def rows() -> list[dict]:
    out = []
    for system, rel, role in ROWS:
        path = VIA / rel
        out.append({
            "lamp": "GREEN" if path.is_file() else "RED",
            "system": system,
            "tail": path.name,
            "role": role,
        })
    return out


def check() -> dict:
    found = rows()
    red = [row["system"] for row in found if row["lamp"] != "GREEN"]
    return {
        "via": "vcgc",
        "door": "CGC_MDL217_ManagerMatrix_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "page": PAGE.name,
        "rows": found,
        "missing": red,
        "ran_managers": False,
        "intake_edited": False,
        "hub_edited": False,
        "do_not": [
            "start VDF or VRN from this list",
            "fetch from this door",
            "treat the HTML as a second registry",
            "edit intake macro_ssot",
        ],
        "next": "none" if not red else "do not unlock; name the drift",
    }


def write_page(card: dict) -> None:
    body = []
    for row in card["rows"]:
        body.append(
            "<tr><td class='%s'>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
            % (row["lamp"].lower(), row["lamp"], html.escape(row["system"]), html.escape(row["tail"]), html.escape(row["role"]))
        )
    text = """<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>VIA Manager Matrix</title>
<style>
body{margin:0;background:#101412;color:#d7ddd8;font:12px/1.45 ui-sans-serif,sans-serif}
main{max-width:980px;margin:auto;padding:18px}
h1{font-size:16px;font-weight:600;letter-spacing:.04em;margin:0 0 10px}
table{border-collapse:collapse;width:100%}
th,td{border-bottom:1px solid #2a332e;padding:6px 8px;text-align:left;vertical-align:top}
th{color:#8d9992;font-weight:600}
.green{color:#7dcea0;font-weight:700}.red{color:#e07a7a;font-weight:700}
</style><main><h1>SYSTEM MANAGER MATRIX</h1>
<table><tr><th>lamp</th><th>system</th><th>tail</th><th>role</th></tr>__ROWS__</table>
</main></html>""".replace("__ROWS__", "".join(body))
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(text, encoding="utf-8")


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = check()
    if card["next"] == "none":
        write_page(card)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["next"] == "none" else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = check()
    ok = denied and card["ran_managers"] is False and card["next"] == "none" and len(card["rows"]) == 5
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
