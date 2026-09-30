#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL221_SystemBackup v0101 — 薄尾:鏈報告分真跑與計畫(Z286 · VCGC-REQ085:backup-stale)

v0100 只要 VIA_Reports/vdf_chain/VDFCHAIN_latest.json 在就判 chain_file 失敗:備份冊記的是「引擎 NODATA、鏈報告不在」,
防的是「照計畫寫出 VDFCHAIN_latest.json」(do_not 第一條)。但鏈跑器在計畫模式與真跑都寫 latest(mode = plan / run…),
工作站或容器真跑過 VDF 鏈之後,備份自測與 CGC_SystemManager 自測就永遠紅,訊息只寫 chain_file(串測首輪實測)。
  ① 鏈報告在:讀它的 schema 與 mode。schema = VIA.VDFChain.v1、mode 以 run 開頭、有 stages 與 generated → 真跑過;
     不算備份失敗,卡片記 chain_report = RAN_AFTER_BACKUP(產生時間 · rc_name · mode)· stale = true(冊該重備,不自動改冊)。
  ② mode 是 plan、不是鏈跑器的報告、讀不到 → 照 v0100 判 chain_file(計畫寫出來的報告不放行)。
  ③ 其餘判準照 v0100(五個檔在 · 兆豐 MEGA / WATERLAND 顯示 · 冊記引擎 NODATA)。只收 VCGC 呼叫;不抓網路、不寫報告、不改冊。
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
import importlib.util
import json
import os
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENGINE = Path(__file__).stem
PRIOR_PATH = HERE / "CGC_MDL221_SystemBackup_v0100.py"
_spec = importlib.util.spec_from_file_location("CGC_MDL221_SystemBackup_prior_for_v0101", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
VIA = PRIOR.VIA
CHAIN_LATEST = VIA / "VIA_Reports" / "vdf_chain" / "VDFCHAIN_latest.json"
CHAIN_SCHEMA = "VIA.VDFChain.v1"


def __getattr__(name: str):
    return getattr(PRIOR, name)


def judge_chain(path: Path) -> dict:
    """ABSENT (what the backup recorded) · RAN_AFTER_BACKUP (a real chain run, the backup is stale) · NOT_A_RUN (plan / foreign / unreadable)."""
    path = Path(path)
    if not path.is_file():
        return {"state": "ABSENT", "ok": True}
    try:
        rep = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return {"state": "NOT_A_RUN", "ok": False, "why": "unreadable " + type(exc).__name__}
    if not isinstance(rep, dict):
        return {"state": "NOT_A_RUN", "ok": False, "why": "not an object"}
    mode = str(rep.get("mode") or "")
    if rep.get("schema") != CHAIN_SCHEMA:
        return {"state": "NOT_A_RUN", "ok": False, "why": "schema " + str(rep.get("schema"))}
    if not mode.startswith("run") or not isinstance(rep.get("stages"), list) or not rep["stages"] or not rep.get("generated"):
        return {"state": "NOT_A_RUN", "ok": False, "why": "mode " + (mode or "?")}
    return {"state": "RAN_AFTER_BACKUP", "ok": True, "generated": rep.get("generated"), "rc_name": rep.get("rc_name"), "mode": mode}


def check(chain_path: Path = CHAIN_LATEST) -> dict:
    card = PRIOR.check()
    verdict = judge_chain(chain_path)
    missing = [m for m in card["missing"] if m != "chain_file"]
    if not verdict["ok"]:
        missing.append("chain_file")
    card.update(door=ENGINE, missing=missing, lock_success=not missing, chain_report=verdict,
                stale=verdict["state"] == "RAN_AFTER_BACKUP",
                next=("none" if not missing else "do not unlock; name the drift")
                if verdict["state"] != "RAN_AFTER_BACKUP" or missing
                else "backup is older than the last VDF chain run; re-measure the backup when you want it current")
    return card


def main() -> int:
    if os.environ.get("VIA_FROM_VCGC") != "YES":
        print(json.dumps({"via": "vcgc", "state": "DENY", "why": "only via-vcgc"}, ensure_ascii=False))
        return 2
    card = check()
    print(json.dumps(card, ensure_ascii=False, indent=1))
    return 0 if card["lock_success"] else 2


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    run_rep = {"schema": CHAIN_SCHEMA, "mode": "run+resume", "generated": "2026-09-29 08:00:14Z", "rc_name": "GATED", "stages": [{"id": "s1"}]}
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        cases = {"absent": t / "none.json", "run": t / "run.json", "plan": t / "plan.json", "foreign": t / "foreign.json", "bad": t / "bad.json"}
        cases["run"].write_text(json.dumps(run_rep), encoding="utf-8")
        cases["plan"].write_text(json.dumps(dict(run_rep, mode="plan")), encoding="utf-8")
        cases["foreign"].write_text(json.dumps({"mode": "run", "stages": [1], "generated": "x"}), encoding="utf-8")
        cases["bad"].write_text("{not json", encoding="utf-8")
        got = {k: judge_chain(p)["state"] for k, p in cases.items()}
        cards = {k: check(p) for k, p in cases.items()}
    chk("① 鏈報告判法:不在 ABSENT · 真跑 RAN_AFTER_BACKUP · 計畫 / 非鏈跑器 / 讀不到 NOT_A_RUN",
        got == {"absent": "ABSENT", "run": "RAN_AFTER_BACKUP", "plan": "NOT_A_RUN", "foreign": "NOT_A_RUN", "bad": "NOT_A_RUN"}, got)
    base_missing = [m for m in cards["absent"]["missing"]]
    chk("② 冊本身(五檔 · 兆豐 MEGA · 引擎 NODATA)照 v0100 過:沒有鏈報告時 lock_success · green 8 · kept_show IBF",
        cards["absent"]["lock_success"] and cards["absent"]["green"] == 8 and cards["absent"]["kept_show"] == "IBF", base_missing or "0")
    chk("③ 真跑過鏈:不判 chain_file · stale 標出來 · next 說要重備(不自動改冊)",
        cards["run"]["lock_success"] and cards["run"]["stale"] and "re-measure" in cards["run"]["next"] and cards["run"]["door"] == ENGINE)
    chk("④ 計畫寫出的報告 / 非鏈跑器 / 讀不到:照舊 chain_file(do_not 第一條守住)",
        all("chain_file" in cards[k]["missing"] and not cards[k]["lock_success"] for k in ("plan", "foreign", "bad")))
    os.environ.pop("VIA_FROM_VCGC", None)
    denied = main() == 2
    os.environ["VIA_FROM_VCGC"] = "YES"
    real = check()
    chk("⑤ 只收 VCGC · 實樹鎖定成立(鏈報告現況 " + real["chain_report"]["state"] + ";計畫寫出的報告照樣紅)",
        denied and real["lock_success"], ",".join(real["missing"]) or "0")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋在 · 不碰 TA-Lib · 前版 v0100 不動", "VIA:ACCEL-BRIDGE" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and PRIOR_PATH.is_file())
    print(f"  {ENGINE} selftest {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if "--selftest" in sys.argv else main())
