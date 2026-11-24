#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_FastRun v0105 — 薄尾(v0100–v0104 一字不動):env 組每一步都要「這一輪真的跑完」才往下走(PR #735 Codex P1)

Codex P1:「doctor 或 plan-check 子行程崩潰 / 逾時、沒換掉報告時,v0104 照讀前一輪的 *_latest.json;前一輪留下的『無衝突』doctor
  與『綠』計畫就會讓 env:install 照跑,即使這一輪的前置檢查失敗。兩個前置工作都回 rc 124 就重現得出來。」
本版(順序與規範照 v0104;只多兩道關):
  · env:doctor_before 跑完:逾時(rc 124)或 DOCTOR_latest.json 不是這一輪寫的(修改時間早於本步開始)→ 停,不新增、不查計畫、不裝。
    doctor 回 rc 1 / 2(有紅 / 黃)仍是跑完的正常結果,照讀報告判衝突風險。
  · env:plan_check 跑完:逾時、PLANCHECK_latest.json 不是這一輪寫的、或計畫的 request 不是這一輪要裝的那份 → 停,不裝。
其餘(全面檢視 → 衝突閘 → 三鏡像計畫 → 直接照計畫裝不再測 · envmgr 並行 · 進度條 · 推收據)照 v0104。
用法:python VIA_FastRun_v0105.py --set env,vrn,vdf[,fidelity] [--lanes N] [--timeout 秒] [--push] [--selftest]
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
import shutil
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve()
FAMILY = "VIA_FastRun"
TAG = "VIA_FastRun v0105"
TIMEOUT_RC = 124


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0105", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V3 = PRIOR.PRIOR                                          # v0103:main 叫它模組裡的 run_env
P2, BASE = PRIOR.P2, PRIOR.BASE                           # v0102 / v0100
VIA = BASE.VIA


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def fresh(path: Path, since: float) -> bool:
    """報告是不是這一輪寫的:檔在,而且修改時間不早於本步開始(容 2 秒時鐘誤差)。"""
    try:
        return path.stat().st_mtime >= since - 2
    except OSError:
        return False


def run_env(out: Path, timeout: int) -> tuple:
    hub = P2.hub_path()
    if hub is None:
        return [], ["env:*(VCGC_CommandHub 尾版不在)"]
    py, res = sys.executable, []

    def step(name, args, cap):
        P2._DONE["stage"] = name
        r = P2.run_job({"name": name, "argv": [py, str(hub), *args], "env": "vcgc", "timeout": cap}, out, timeout)
        BASE.say(BASE.line_of(r))
        res.append(r)
        return r

    def done(k):
        with P2._LOCK:
            P2._DONE["n"] += k
    dd = PRIOR.doctor_dir()
    t0 = time.time()
    r = step("env:doctor_before", ["doctor", "--only", *PRIOR.DOCTOR_BEFORE], 900)
    if r.get("rc") == TIMEOUT_RC or not fresh(dd / "DOCTOR_latest.json", t0):
        BASE.say("env 全面檢視沒有在這一輪跑完(rc %s · 報告%s)→ 不新增 · 不查計畫 · 不裝(不拿上一輪的報告當依據)" % (
            r.get("rc"), "是舊的" if (dd / "DOCTOR_latest.json").exists() else "不在"))
        done(2)
        return res, ["env:plan_check / install(全面檢視沒跑完 → 先查原因再重跑 via-health)"]
    if (dd / "DOCTOR_latest.txt").exists():
        shutil.copy2(dd / "DOCTOR_latest.txt", out / "DOCTOR_before.txt")
    risks = PRIOR.conflict_risks(PRIOR._read(dd / "DOCTOR_latest.json"))
    if risks:
        for x in risks[:8]:
            BASE.say("env 衝突風險 · %s" % x[:150])
        BASE.say("env 有衝突風險 → 不新增(先移開風險重建):%s" % PRIOR.REBUILD_NEXT)
        done(2)
        return res, ["env:plan_check / install(現在的環境有衝突風險 %d 項 → 先重建再新增)" % len(risks)]
    plan = P2.doctor_plan()
    BASE.say("env 現況無衝突 · 沒裝的工具 %d 個列入新增:%s" % (len(plan), " ".join(plan) or "—"))
    if not plan:
        done(2)
        return res, []
    pf = PRIOR.plan_file()
    t1 = time.time()
    r = step("env:plan_check", ["install", "--yes", "--plan-check", *plan], 900)
    pc = PRIOR._read(pf) if fresh(pf, t1) else {}
    if r.get("rc") == TIMEOUT_RC or not pc or list(pc.get("request") or []) != list(plan):
        BASE.say("env 計畫檢查沒有在這一輪跑完(rc %s · 計畫%s)→ 不裝(不拿上一輪的計畫當依據)" % (
            r.get("rc"), "不是這一輪要裝的那份" if pc else "沒有這一輪寫的"))
        done(1)
        return res, ["env:install(計畫檢查沒跑完 → 先查原因再重跑 via-health)"]
    (out / "PLANCHECK.json").write_text(json.dumps(pc, ensure_ascii=False, indent=1), encoding="utf-8")
    for x in pc.get("special") or []:
        BASE.say("env 特殊環境單獨安裝 · %s → %s" % (x["pkg"], x["env"]))
    if pc.get("lamp") in ("GREEN", "YELLOW") and pc.get("plan") and not pc.get("new_conflicts"):
        step("env:install", ["install", "--yes", "--from-plan"], 3600)
    else:
        done(1)
        BASE.say("env 計畫燈 %s · base 要裝 %d 件 → %s" % (pc.get("lamp", "GRAY"), len(pc.get("plan") or []),
                                                    "不裝(" + " · ".join(pc.get("why") or ["沒有計畫"]) + ")" if pc.get("lamp") not in ("GREEN", "YELLOW") else "base 沒有要裝的"))
    return res, []


_RUN_ENV_V0104 = V3.run_env


def _install():
    V3.run_env = run_env
    V3.TAG = TAG
    BASE.HERE, BASE.TAG = HERE, TAG
    P2.HERE = HERE


_install()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return V3.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 5 項 · 前版 %s · 暫存夾 · 假中樞)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 鏈:前版 v0104 · v0103 main 用的 run_env 換成本版 · 重新進來跑本檔", PRIOR_PATH.name == "VIA_FastRun_v0104.py"
        and V3.run_env is run_env and BASE.HERE == HERE and P2.HERE == HERE)
    doc_ok = {"plan": {"conflicts": [], "pip": ["rich"]}, "plugins": [{"key": "envgov", "lamp": "GREEN"}]}
    green = {"lamp": "GREEN", "plan": ["rich==1"], "new_conflicts": [], "request": ["rich"]}
    keep = (P2.run_job, P2.doctor_plan, P2.hub_path, PRIOR.doctor_dir, PRIOR.plan_file)
    calls = []
    with tempfile.TemporaryDirectory(prefix="fastrun105_") as td:
        td = Path(td)
        dd, pf = td / "doctor", td / "PLANCHECK_latest.json"
        dd.mkdir()
        old = time.time() - 3600

        def scenario(doctor_rc=0, doctor_writes=True, pc_rc=0, pc_writes=True, pc=None):
            calls.clear()
            (dd / "DOCTOR_latest.json").write_text(json.dumps(doc_ok), encoding="utf-8")
            pf.write_text(json.dumps(green), encoding="utf-8")
            os.utime(dd / "DOCTOR_latest.json", (old, old))      # 上一輪留下的「無衝突」報告與「綠」計畫
            os.utime(pf, (old, old))

            def job(j, out_, timeout):
                a = j["argv"][2:]
                calls.append(a)
                if a[0] == "doctor":
                    if doctor_writes:
                        (dd / "DOCTOR_latest.json").write_text(json.dumps(doc_ok), encoding="utf-8")
                    return {"name": j["name"], "rc": doctor_rc, "secs": 0.0, "lamp": "GREEN" if doctor_rc == 0 else "RED", "bits": []}
                if "--plan-check" in a:
                    if pc_writes:
                        pf.write_text(json.dumps(pc or green), encoding="utf-8")
                    return {"name": j["name"], "rc": pc_rc, "secs": 0.0, "lamp": "GREEN", "bits": []}
                return {"name": j["name"], "rc": 0, "secs": 0.0, "lamp": "GREEN", "bits": []}
            P2.run_job = job
            P2._DONE.update(n=0, total=3)
            r, s = run_env(td, 60)
            return [c[0] if c[0] != "install" else c[2] for c in calls], s
        try:
            P2.hub_path = lambda: Path("hub.py")
            P2.doctor_plan = lambda via=VIA: ["rich"]
            PRIOR.doctor_dir, PRIOR.plan_file = (lambda: dd), (lambda: pf)
            a1, s1 = scenario(doctor_rc=124, doctor_writes=False, pc_rc=124, pc_writes=False)
            a2, s2 = scenario(pc_rc=124, pc_writes=False)
            a3, s3 = scenario(pc={"lamp": "GREEN", "plan": ["x==1"], "new_conflicts": [], "request": ["x"]})
            a4, s4 = scenario()
            a5, _ = scenario(doctor_rc=1)
        finally:
            P2.run_job, P2.doctor_plan, P2.hub_path = keep[:3]
            PRIOR.doctor_dir, PRIOR.plan_file = keep[3:]
    chk("T2 Codex 重現:doctor 與 plan-check 都 rc 124、只剩上一輪的綠報告 → 停在全面檢視 · 不查計畫 · 不裝",
        a1 == ["doctor"] and "沒跑完" in s1[0], (a1, s1))
    chk("T3 doctor 這一輪跑完、plan-check 逾時(計畫是上一輪的綠)→ 不裝", a2 == ["doctor", "--plan-check"] and "沒跑完" in s2[0], (a2, s2))
    chk("T4 計畫是這一輪寫的、但 request 不是這一輪要裝的那份 → 不裝;兩步都這一輪跑完 → 照計畫裝",
        a3 == ["doctor", "--plan-check"] and a4 == ["doctor", "--plan-check", "--from-plan"] and not s4, (a3, a4))
    chk("T5 doctor 回 rc 1(有紅項但跑完)照讀報告 · 無衝突風險就往下走", a5 == ["doctor", "--plan-check", "--from-plan"], a5)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(前版自己的 run_env / HERE / TAG)" % PRIOR_PATH.name, flush=True)
    keep2 = (V3.run_env, V3.TAG, BASE.HERE, BASE.TAG, P2.HERE)
    V3.run_env = PRIOR.run_env
    PRIOR._install()
    try:
        rc_prior = PRIOR.selftest()
    finally:
        V3.run_env, V3.TAG, BASE.HERE, BASE.TAG, P2.HERE = keep2
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
