#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run the VCGC policy, sync the subsystem managers, then allow the verb.

The locked policy book stays untouched. GitHub receives the seat only.
v0100→v0101(批1657 操作員令「節省TOKEN工具族 SSOT工具族也該列管 加速器 網路工具列管」):
  親子表加四族工具列(role=tool):省TOKEN(CGC_MDL158)· SSOT全景(CGC_MDL247)· 編號(CGC_MDL237)·
  加速器(SUP_MDL737→VeritasCeleritas 尾版)· 網路(SUP_MDL740→VeritasAegisNexus 尾版)。
  各列用自己的誠實針(省TOKEN/編號/網路無 VCGC 閘是設計,不假紅);加速器/網路列把解到的引擎尾版列進 functions。
  另:POLICY/PROBE 由釘死版號改 glob 尾版(v0100 全景 PINVER 2 筆清零)。管理者列判準一字不動。
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
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parents[1]
REPO = VIA.parent
NOTE = HERE / "VIA_Policy_FlowGate_v0100.json"
def _tail(folder: Path, pattern: str) -> Path:
    hits = sorted(folder.glob(pattern))
    return hits[-1] if hits else folder / pattern.replace("*", "0000")


POLICY = _tail(Path(__file__).resolve().parent, "CGC_MDL149_VeritasCentralGovernanceConsole_v*.py")
PROBE = _tail(Path(__file__).resolve().parent, "CGC_MDL222_SubsystemProbe_v*.py")
SEAT = HERE / "VIA_VCGC_SubsystemSeat_v0100.json"
PAGE = VIA / "VIA_Reports" / "vcgc" / "VIA_Flow_Matrix_v0100.html"
NEEDLES = ("VIA_FROM_VCGC", "def main", "def selftest")
FAMILIES = (
    ("VCGC", HERE, "CGC_SystemManager_v*.py"),
    ("VDF", VIA / "functional modules" / "VDF", "VDF_SystemManager_v*.py"),
    ("VRN", VIA / "functional modules" / "VRN", "VRN_SystemManager_v*.py"),
    ("NLP", VIA / "supportive modules" / "70_VRN_Rules", "SUP_MDL866_VIAUnifiedNLPOrchestrator_v*.py"),
    ("LAYOUT", VIA / "supportive modules" / "70_VRN_Rules", "SUP_MDL743_GenericLayoutHub_v*.py"),
)
# 批1657 列管:工具族(role=tool;針按各族設計誠實設,無 VCGC 閘的不假紅)
TOOL_FAMILIES = (
    ("省TOKEN", None, "CGC_MDL158_VIAPanoramaAuditRepair_v*.py", ("def main", "def selftest"), None),
    ("SSOT全景", None, "CGC_MDL247_SSOTPanorama_v*.py", ("VIA_FROM_VCGC", "def main", "def selftest"), None),
    ("編號", None, "CGC_MDL237_NumberingSystem_v*.py", ("def main", "def selftest"), None),
    ("加速器", "supportive modules", "SUP_MDL737_SuperAccelModule_v*.py", ("def selftest",), "VeritasCeleritas_v*.py"),
    ("網路", "supportive modules/network", "SUP_MDL740_NetUnified_v*.py", ("def main", "def selftest"), "VeritasAegisNexus_v*.py"),
)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _newest(folder: Path, pattern: str) -> Path | None:
    hits = sorted(folder.glob(pattern))
    return hits[-1] if hits else None


def functions() -> list[dict]:
    rows = []
    for system, folder, pattern in FAMILIES:
        path = _newest(folder, pattern)
        text = path.read_text(encoding="utf-8", errors="ignore") if path else ""
        have = [needle for needle in NEEDLES if needle in text]
        rows.append({
            "lamp": "GREEN" if path and len(have) == len(NEEDLES) else "RED",
            "system": system,
            "tail": path.name if path else "",
            "have": have,
            "role": "parent" if system == "VCGC" else "child",
        })
    for system, sub, pattern, needles, engine_pat in TOOL_FAMILIES:
        folder = HERE if sub is None else VIA / sub
        path = _newest(folder, pattern)
        text = path.read_text(encoding="utf-8", errors="ignore") if path else ""
        have = [needle for needle in needles if needle in text]
        if engine_pat and path:
            eng = _newest(path.parent, engine_pat)
            have.append("engine:" + eng.name if eng else "engine:缺")
        rows.append({
            "lamp": "GREEN" if path and all(n in text for n in needles) and "engine:缺" not in have else "RED",
            "system": system,
            "tail": path.name if path else "",
            "have": have,
            "role": "tool",
        })
    return rows


def gate() -> dict:
    note = json.loads(NOTE.read_text(encoding="utf-8"))
    policy = _load(POLICY, "policy_for_flow")
    rc = policy.policy_step()
    probe = _load(PROBE, "probe_for_flow")
    seat_card = probe.check()
    if seat_card["drift"]:
        probe.write_seat(seat_card["rows"])
        seat_card = probe.check()
        seat_card["synced"] = True
    rows = functions()
    weak = [row["system"] for row in rows if row["lamp"] != "GREEN"]   # 工具列同權重:紅就擋動詞
    missing = []
    if rc != 0:
        missing.append("policy_step")
    if note.get("book_edited") is not False:
        missing.append("book")
    missing.extend(seat_card["missing"])
    missing.extend(weak)
    return {
        "via": "vcgc",
        "door": "CGC_MDL223_FlowConsistency_v0100",
        "enter": "vcgc",
        "exit": "vcgc",
        "lock_success": not missing,
        "policy_rc": rc,
        "book_edited": False,
        "synced": bool(seat_card.get("synced")),
        "rows": rows,
        "drift": seat_card["drift"],
        "weak": weak,
        "missing": missing,
        "pushed": False,
        "intake_edited": False,
        "do_not": note["do_not"],
        "next": "none" if not missing else "do not run the verb",
    }


def write_page(card: dict) -> None:
    body = "".join(
        "<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>"
        % (html.escape(row["lamp"]), html.escape(row["role"]), html.escape(row["system"]),
           html.escape(row["tail"]), html.escape(", ".join(row["have"])))
        for row in card["rows"]
    )
    text = """<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>VCGC flow matrix</title>
<style>
body{margin:0;background:#121614;color:#d5ddd6;font:11px/1.35 ui-sans-serif,sans-serif}
main{max-width:1100px;margin:auto;padding:14px}
h1{font-size:14px;font-weight:650;margin:0 0 8px}
table{border-collapse:collapse;width:100%}
th,td{border-bottom:1px solid #2c3832;padding:4px 6px;text-align:left;vertical-align:top;white-space:normal;word-break:break-word}
th{color:#8e9b93}
td:first-child{font-weight:700}
</style><main><h1>VCGC FLOW · PARENT AND CHILDREN</h1>
<table><tr><th>lamp</th><th>role</th><th>system</th><th>tail</th><th>functions</th></tr>__ROWS__</table>
</main></html>"""
    PAGE.parent.mkdir(parents=True, exist_ok=True)
    PAGE.write_text(text.replace("__ROWS__", body), encoding="utf-8")


def publish() -> dict:
    if os.environ.get("VIA_VCGC_PUSH") == "NO":
        return {"pushed": False, "why": "held"}
    rel = "VeritasIntelligenceAnalytics/supportive modules/registry/VIA_VCGC_SubsystemSeat_v0100.json"
    status = subprocess.run(["git", "status", "--porcelain", "--", rel], cwd=REPO, capture_output=True, text=True)
    if status.returncode != 0:
        return {"pushed": False, "why": "git"}
    if not status.stdout.strip():
        return {"pushed": False, "why": "clean"}
    subprocess.run(["git", "add", "--", rel], cwd=REPO, check=False)
    commit = subprocess.run(
        ["git", "-c", "user.name=Tony Huang", "-c", "user.email=138236302+tonykuni@users.noreply.github.com",
         "commit", "-m", "vcgc: sync the subsystem seat"],
        cwd=REPO, capture_output=True, text=True,
    )
    if commit.returncode != 0:
        return {"pushed": False, "why": "commit"}
    push = subprocess.run(["git", "push", "origin", "HEAD"], cwd=REPO, capture_output=True, text=True)
    return {"pushed": push.returncode == 0, "why": "pushed" if push.returncode == 0 else "push"}


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = gate()
    write_page(card)
    if card["lock_success"]:
        card.update(publish())
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    os.environ["VIA_VCGC_PUSH"] = "NO"
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    card = gate()
    write_page(card)
    parent = next(row for row in card["rows"] if row["role"] == "parent")
    children = [row for row in card["rows"] if row["role"] == "child"]
    tools = [row for row in card["rows"] if row["role"] == "tool"]
    ok = denied and card["lock_success"] and parent["have"] == list(NEEDLES)
    ok = ok and children and all(row["have"] == list(NEEDLES) for row in children)
    ok = ok and len(tools) == 5 and all(row["lamp"] == "GREEN" for row in tools)
    ok = ok and PAGE.is_file() and SEAT.is_file()
    print("  [OK]" if ok else "  [FAIL] " + ",".join(card["missing"]))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
