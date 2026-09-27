#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Mandatory step matrix. Every VCGC action passes these steps in this order.

The earlier steps stay. Nothing in front of them is removed.

1. enter. Only via-vcgc. This step stays.
2. token. Turn on every token tool: read, slice, digest, pack, etag, brief.
   A missing tool stops here. The policy book is not printed.
3. accel_net. The accelerator and the network tool are wired in.
   They are not run, and they do not fetch.
4. policy. The existing gate still reads the policy book. Numbering waits
   until that read has happened. This door does not dump the book.
5. number. Auto numbering stays after policy. This door does not apply it.
6. ps_template. An AI PowerShell template stays later. This door writes none.
7. env. The environment check stays later. This door installs nothing.
8. subsystem. VDF and VRN SSOT, regex, synonyms, and logic are compared
   only here. Drift is named. The books are not rewritten.

Steps 1 to 3 do not open a subsystem file. The policy printer may still
say 第二步. That label stays inside the book. This matrix is the action order.
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
PAGE = VIA / "VIA_Reports" / "vcgc" / "VIA_Step_Matrix_v0100.html"
PANORAMA = HERE
NLP = VIA / "supportive modules" / "70_VRN_Rules"
ACCEL = VIA / "supportive modules"
NET = VIA / "supportive modules" / "network"
SYNC = HERE / "CGC_MDL219_RegexParamSync_v0100.py"

TOKEN_TOOLS = ("read", "slice", "digest", "pack", "etag", "brief")
ORDER = (
    (1, "enter", "keep", "唯一入口 via-vcgc"),
    (2, "token", "keep", "啟用全部省 Token 工具"),
    (3, "accel_net", "keep", "加速器與網路工具導入，不執行"),
    (4, "policy", "after_front", "讀過政策之後才可編號"),
    (5, "number", "after_policy", "自動編碼編號，本口不套用"),
    (6, "ps_template", "later", "AI 寫 PS 模板，後移"),
    (7, "env", "later", "環境檢查與更新，後移"),
    (8, "subsystem", "subsystem", "VDF VRN 的 SSOT regex 同義字 邏輯，到這步才讀"),
)


def _newest(folder: Path, pattern: str) -> Path | None:
    if not folder.is_dir():
        return None
    hits = sorted(folder.glob(pattern))
    return hits[-1] if hits else None


def _has(path: Path | None, needle: str, limit: int = 8000) -> bool:
    if path is None or not path.is_file():
        return False
    seen = 0
    with path.open(encoding="utf-8", errors="replace") as handle:
        for line in handle:
            seen += len(line)
            if needle in line:
                return True
            if seen > limit * 80:
                return False
    return False


def token_tools() -> dict:
    panorama = _newest(PANORAMA, "CGC_MDL158_VIAPanoramaAuditRepair_v*.py")
    nlp = _newest(NLP, "SUP_MDL866_VIAUnifiedNLPOrchestrator_v*.py")
    tools = {
        "read": _has(panorama, '"read"'),
        "slice": _has(panorama, '"slice"'),
        "digest": _has(panorama, '"digest"'),
        "pack": _has(panorama, "def pack_payload"),
        "etag": _has(panorama, "--if-etag"),
        "brief": _has(nlp, "--brief"),
    }
    missing = [name for name in TOKEN_TOOLS if not tools[name]]
    return {
        "panorama": panorama.name if panorama else "",
        "nlp": nlp.name if nlp else "",
        "tools": tools,
        "missing": missing,
    }


def accel_net() -> dict:
    accel = _newest(ACCEL, "SUP_MDL737_SuperAccelModule_v*.py")
    module = ACCEL / "VIA_SuperAccel_Module.py"
    net = _newest(NET, "SUP_MDL740_NetUnified_v*.py")
    wired = _has(net, "VIA:ACCEL-BRIDGE", 4000) and module.is_file() and accel is not None
    missing = []
    if accel is None:
        missing.append("accel")
    if not module.is_file():
        missing.append("accel_module")
    if net is None:
        missing.append("net")
    elif not _has(net, "VIA:ACCEL-BRIDGE", 4000):
        missing.append("net_bridge")
    return {
        "accel": accel.name if accel else "",
        "accel_module": module.name if module.is_file() else "",
        "net": net.name if net else "",
        "wired": wired,
        "ran": False,
        "fetched": False,
        "missing": missing,
    }


def front() -> dict:
    """Steps 1 to 3 only. Subsystem books stay closed."""
    token = token_tools()
    bridges = accel_net()
    entered = os.environ.get("VIA_FROM_VCGC") == "YES"
    rows = []
    for step, name, when, zh in ORDER:
        if name == "enter":
            lamp = "GREEN" if entered else "RED"
            ran = entered
            missing = [] if entered else ["enter"]
        elif name == "token":
            lamp = "GREEN" if not token["missing"] else "RED"
            ran = True
            missing = list(token["missing"])
        elif name == "accel_net":
            lamp = "GREEN" if not bridges["missing"] else "RED"
            ran = False
            missing = list(bridges["missing"])
        else:
            lamp = "HOLD"
            ran = False
            missing = []
        rows.append({
            "step": step,
            "id": name,
            "zh": zh,
            "when": when,
            "lamp": lamp,
            "ran": ran,
            "may_open_subsystem": name == "subsystem",
            "missing": missing,
        })
    front_missing = [row["id"] for row in rows if row["step"] <= 3 and row["lamp"] != "GREEN"]
    return {
        "via": "vcgc",
        "door": "CGC_MDL226_StepMatrix_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "order": [name for _, name, _, _ in ORDER],
        "front_pass": not front_missing,
        "rows": rows,
        "token": token,
        "accel_net": bridges,
        "opened_subsystem": False,
        "policy_printed": False,
        "numbered": False,
        "ps_written": False,
        "env_updated": False,
        "book_edited": False,
        "intake_edited": False,
        "missing": front_missing,
        "do_not": [
            "drop step 1, step 2, or step 3",
            "print the policy book before the token tools are on",
            "read a VDF or VRN body before the subsystem step",
            "run the accelerator or the network tool from this door",
            "registry-sync --apply",
            "write a ps1 from this door",
            "edit intake macro_ssot",
        ],
        "next": "none" if not front_missing else "do not read policy or a subsystem",
    }


def subsystem_sync() -> dict:
    """Step 8. Compare the linked books. Do not rewrite them."""
    import importlib.util
    spec = importlib.util.spec_from_file_location("regex_param_sync_for_steps", SYNC)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    card = module.check()
    card["step"] = 8
    card["id"] = "subsystem"
    card["rewritten"] = False
    card["opened_subsystem"] = True
    card["reads"] = [card.get("regex_book"), card.get("synonym_book"), "VIA_Central_Params_SSOT_v0100.json"]
    return card


def write_page(card: dict) -> None:
    body = ["<table><tr><th>step</th><th>lamp</th><th>id</th><th>when</th><th>zh</th></tr>"]
    for row in card["rows"]:
        body.append(
            "<tr><td>{step}</td><td>{lamp}</td><td>{id}</td><td>{when}</td><td>{zh}</td></tr>".format(
                step=row["step"],
                lamp=html.escape(row["lamp"]),
                id=html.escape(row["id"]),
                when=html.escape(row["when"]),
                zh=html.escape(row["zh"]),
            )
        )
    body.append("</table>")
    page = (
        "<!DOCTYPE html><html><head><meta charset='utf-8'><title>VCGC steps</title>"
        "<style>body{font:12px/1.35 ui-sans-serif,sans-serif;margin:12px}"
        "table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccc;"
        "padding:2px 6px;text-align:left;word-break:break-word}"
        "th{background:#eee}</style></head><body><h1>VCGC STEP MATRIX</h1>"
        + "".join(body) + "</body></html>"
    )
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(page, encoding="utf-8")


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = front()
    write_page(card)
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["front_pass"] else 2


def selftest() -> int:
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = front()
    write_page(card)
    ids = [row["id"] for row in card["rows"]]
    early = [row for row in card["rows"] if row["step"] <= 3]
    later = [row for row in card["rows"] if row["step"] >= 4]
    ok = (
        denied
        and card["front_pass"]
        and ids == [name for _, name, _, _ in ORDER]
        and all(row["lamp"] == "GREEN" for row in early)
        and all(row["may_open_subsystem"] is False for row in early)
        and all(row["lamp"] == "HOLD" and row["ran"] is False for row in later)
        and card["opened_subsystem"] is False
        and card["token"]["missing"] == []
        and card["accel_net"]["ran"] is False
        and "word-break:break-word" in PAGE.read_text(encoding="utf-8")
    )
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
