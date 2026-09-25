#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""One yellow paste block. It does not run engines and it does not apply a plan."""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
PLAN = VIA / "VIA_Reports" / "env_governance" / "TOOLS_PLAN_latest.json"
LOG = VIA / "VIA_Reports" / "vcgc" / "PASTE_latest.txt"


def summarize(plan: dict) -> list[str]:
    counts = plan.get("counts") or {}
    absent = []
    for env in plan.get("envs") or []:
        if env.get("found"):
            continue
        bad = sum(1 for tool in env.get("tools") or [] if tool.get("state") != "OK")
        absent.append(f"{env.get('name')}({bad})")
    count_text = " · ".join(f"{key} {value}" for key, value in counts.items()) or "無"
    return [
        f"工具冊 {plan.get('state') or 'PLAN'} · {count_text} · 段 {len(plan.get('stages') or [])} 未執行",
        "缺境 " + (" ".join(absent) if absent else "無"),
        f"未路由 {len(plan.get('unrouted') or [])} · 白名單留置 {len(plan.get('whitelist_hold') or [])}",
        "numpy、pandas 多境多版本允許。同境裡有兩版才是問題。",
        "只准 via-vcgc。子系統只經該系 System Manager。禁止單獨啟動引擎。",
        "不執行 TOOLS_PLAN_latest.ps1。",
    ]


def _handover() -> str:
    docs = VIA / "docs"
    names = sorted(path.name for path in docs.glob("VIA_Handover_*.md")) if docs.is_dir() else []
    return names[-1] if names else "ABSENT"


def _lessons() -> str:
    path = HERE / "VIA_Policy_Laws_SSOT_v0100.json"
    if not path.is_file():
        return "ABSENT"
    data = json.loads(path.read_text(encoding="utf-8"))
    return str(len(data.get("lessons") or []))


def paste() -> int:
    if not PLAN.is_file():
        lines = ["工具冊 ABSENT。先不要裝。"]
    else:
        lines = summarize(json.loads(PLAN.read_text(encoding="utf-8")))
    lines.insert(0, f"交接 {_handover()} · lessons {_lessons()}")
    lines.append("下一令: 無。把這一段貼回即可。")
    text = "\n".join(lines)
    LOG.parent.mkdir(parents=True, exist_ok=True)
    LOG.write_text(text + "\n", encoding="utf-8")
    print("BEGIN_PASTE")
    print(text)
    print("END_PASTE")
    return 0


def selftest() -> int:
    sample = {
        "state": "PLAN",
        "counts": {"OK": 57, "WHITELIST_HOLD": 1, "UNROUTED": 72, "ENV_ABSENT": 12},
        "stages": [{"id": "T01"}, {"id": "T02"}],
        "envs": [{"name": "via_core", "found": "via_core"}, {"name": "via_mix_http_M", "found": "", "tools": [{"state": "ENV_ABSENT"}]}],
        "unrouted": ["scipy"],
        "whitelist_hold": [{"tool": "joblib"}],
    }
    lines = summarize(sample)
    ok = "未執行" in lines[0] and "via_mix_http_M(1)" in lines[1] and "禁止單獨啟動引擎" in lines[4]
    print("  [OK]" if ok else "  [FAIL] " + " | ".join(lines))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(selftest() if "--selftest" in sys.argv else paste())
