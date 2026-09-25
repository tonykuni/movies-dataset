#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compact JSON paste. Log, handover, and lessons are collected before it is printed."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
PLAN = VIA / "VIA_Reports" / "env_governance" / "TOOLS_PLAN_latest.json"
LOG = VIA / "VIA_Reports" / "vcgc" / "PASTE_latest.json"


def _missing(plan: dict) -> list[dict]:
    out = []
    for env in plan.get("envs") or []:
        name = str(env.get("name") or "")
        if env.get("found") or not name.startswith("via_"):
            continue
        pkgs = [str(tool.get("pip") or "") for tool in env.get("tools") or [] if tool.get("state") != "OK"]
        out.append({"env": name, "n": len(pkgs), "pkgs": pkgs})
    return out


def _stages(plan: dict) -> list[dict]:
    return [
        {"id": st.get("id"), "kind": st.get("kind"), "env": st.get("env"), "goal": str(st.get("goal") or "")[:80], "ran": False}
        for st in plan.get("stages") or []
    ]


def _handover() -> dict:
    path = VIA / "docs" / "VIA_Handover_Report_v0100.md"
    if not path.is_file():
        return {"file": "ABSENT", "line": ""}
    line = ""
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "中央控制平面" in raw:
            line = raw.strip()[:160]
            break
    return {"file": path.name, "line": line}


def _lessons() -> dict:
    path = HERE / "VIA_Policy_Laws_SSOT_v0100.json"
    if not path.is_file():
        return {"n": 0, "hit": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = [x for x in data.get("lessons") or [] if isinstance(x, dict)]
    keys = ("環境", "衝突", "還原", "白名單", "隔離")
    hit = []
    for row in rows:
        text = str(row.get("zh") or "")
        if any(key in text for key in keys):
            hit.append({"id": row.get("id"), "zh": text[:80]})
    return {"n": len(rows), "hit_n": len(hit), "hit": hit[:8]}


def build(plan: dict) -> dict:
    hold = [str(x.get("tool") or "") for x in plan.get("whitelist_hold") or []]
    return {
        "via": "vcgc",
        "do_not": ["TOOLS_PLAN_latest.ps1", "registry-sync --apply", "start an engine outside via-vcgc"],
        "tools": {
            "state": plan.get("state") or "PLAN",
            "counts": plan.get("counts") or {},
            "stages_ran": False,
        },
        "missing_env": _missing(plan),
        "stages": _stages(plan),
        "hold": hold,
        "unrouted_n": len(plan.get("unrouted") or []),
        "unrouted_route": "via-accel-import",
        "multi_version_ok": ["numpy", "pandas", "pyarrow", "pillow", "torch"],
        "rule": "only via-vcgc; a subsystem only through its System Manager",
        "handover": _handover(),
        "lessons": _lessons(),
        "next": "none",
    }


def paste() -> int:
    if PLAN.is_file():
        body = build(json.loads(PLAN.read_text(encoding="utf-8")))
    else:
        body = build({})
        body["tools"]["state"] = "ABSENT"
    body["logged_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(json.dumps(body, ensure_ascii=False, indent=1), encoding="utf-8")
    print("BEGIN_PASTE")
    print(json.dumps(body, ensure_ascii=False, indent=1))
    print("END_PASTE")
    return 0


def selftest() -> int:
    body = build({
        "state": "PLAN",
        "counts": {"OK": 57, "ENV_ABSENT": 12},
        "envs": [
            {"name": "(未路由:加速器通用件)", "found": "", "tools": [{"state": "UNROUTED", "pip": "scipy"}]},
            {"name": "via_mix_http_M", "found": "", "tools": [{"state": "ENV_ABSENT", "pip": "httpx"}]},
            {"name": "via_core", "found": "via_core", "tools": [{"state": "OK", "pip": "numpy"}]},
        ],
        "stages": [{"id": "T03", "kind": "ENSURE_ENV", "env": "via_mix_http_M", "goal": "建境"}],
        "unrouted": ["scipy"],
        "whitelist_hold": [{"tool": "joblib"}],
    })
    ok = body["missing_env"] == [{"env": "via_mix_http_M", "n": 1, "pkgs": ["httpx"]}]
    ok = ok and body["stages"][0]["ran"] is False and body["next"] == "none"
    ok = ok and body["lessons"]["n"] == 362
    print("  [OK]" if ok else "  [FAIL]")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else paste())
