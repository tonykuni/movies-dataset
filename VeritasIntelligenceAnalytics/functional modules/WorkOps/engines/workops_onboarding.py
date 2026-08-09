# -*- coding: utf-8 -*-
r"""Veritas WorkOps 首跑狀態機 v0100 — GapFill 自建路 B(裁定序 B;唯讀評估)

八步導入狀態全由「真實產物」推導(絕不自報進度):環境→自測→掃描→歸戶→控管表→
命名核對→Gold Set→節奏排程。衍生態落 out/onboarding_state.json(每跑重算)。
動詞:build(預設)。via-workops onboard。UI 首跑精靈(重規劃 §4.1)可直讀此檔。
"""
import json, sys
from datetime import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

HERE = Path(__file__).resolve().parent
WORKOPS = HERE.parent
OUT = WORKOPS / "out"


def jload(p, d):
    try:
        return json.loads(Path(p).read_text(encoding="utf-8-sig"))
    except Exception:
        return d


def build():
    sf = jload(OUT / "selftest_report.json", {})
    reg = jload(OUT / "wop_registry.json", {})
    nm = jload(OUT / "workops_naming.json", {})
    ents = nm.get("entries", {}) or {}
    wt = jload(HERE / "watchtower_params.json", {})
    steps = [
        ("1 環境部署", (HERE / ".venv_pm/Scripts/python.exe").exists() or (OUT / "bootstrap_report.json").exists(),
         "pmsetup 已就位或一鍵部署報告在位", "INSTALL_ONECLICK.cmd"),
        ("2 全鏈自測", sf.get("final_gate") == "PASS", "selftest FinalGate", "via-workops selftest"),
        ("3 Outlook 唯讀掃描", (OUT / "mails.csv").exists(), "mails.csv 在位", "via-workops"),
        ("4 專案歸戶", len(reg.get("projects", {}) or {}) > 0, "%d 案" % len(reg.get("projects", {}) or {}), "via-workops all"),
        ("5 控管表", (WORKOPS / "control_sheet.csv").exists(), "control_sheet.csv", "嚴格 AI 提示詞轉八欄 CSV 後存入"),
        ("6 命名核對", any(isinstance(v, dict) and v.get("approved") for v in ents.values()),
         "至少一筆已核名", "via-workops names apply"),
        ("7 Gold Set 實測", (OUT / "accuracy_report.json").exists(), "accuracy_report 在位", "板 05 面三步引導"),
        ("8 節奏排程", bool(wt.get("daily_rhythm")), "watchtower daily_rhythm", "一鍵部署器自建 16:00/12:00 排程"),
    ]
    done = sum(1 for _, ok, _, _ in steps if ok)
    state = {"ts": datetime.now().isoformat(timespec="seconds"), "done": done, "total": len(steps),
             "steps": [{"step": s, "ok": ok, "evidence": ev, "next": nx} for s, ok, ev, nx in steps]}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "onboarding_state.json").write_text(json.dumps(state, ensure_ascii=False, indent=1), encoding="utf-8")
    print("========== 首跑導入狀態(由真實產物推導,絕不自報)==========")
    for s, ok, ev, nx in steps:
        print("  [%s] %-16s %s%s" % ("✓" if ok else "…", s, ev, "" if ok else " → " + nx))
    print("[導入] %d/%d 步完成 → out/onboarding_state.json" % (done, len(steps)))
    return 0


if __name__ == "__main__":
    sys.exit(build())
