#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_FastRun v0104 — 薄尾(v0100–v0103 一字不動):env 組照「環境安裝規範」跑(操作員 2026-11-24)

操作員原文:「環境安裝規範為先檢查 base / via_core / via_ 開頭的環境全面檢視用 8 個檢測衝突的工具及清華阿里官方鏡像組成
  衝突檢查機制加入加速器 先檢查現在環境有無衝突,有衝突風險將風險移開立刻重建 在檢查無誤後 風險因子即沒裝的工具列入新增
  特殊環境及分類一律單獨安裝 numpy 這種常用允許多版本搭配 python 多版本共存 規劃環境安裝新增檢測無誤新增計畫 直接執行計畫無須再測」。
v0103 的 env 組:doctor → 安裝閘(裝下去才查衝突;一件解不出整批不裝)→ 裝後 doctor 重驗。本版:
  ① env:doctor_before  全面檢視(八路 envgov 掃 base 與 via_* 各境 · pip check · 多層 site 互撞 · 工具冊缺件 · 加速器 · 連線)
  ② 衝突閘            pip check 有衝突、或 envgov / gate_conflict / gate_doctor 任一紅 → 不裝,點名風險並印重建指令
                       (via-envgov plan → via-envgov apply --approve 的 REBUILD 段;重建後再跑 via-health)
  ③ env:plan_check    沒裝的工具(doctor 計畫)→ VCGC 安裝閘三鏡像(清華 · 阿里 · 官方)同時解析 · 推算裝後新增衝突 ·
                       特殊環境 / 分類件分出去單獨安裝(不進 base)· 寫計畫(零安裝)
  ④ env:install       計畫綠 / 黃且有東西要裝 → 直接照計畫一次裝(釘版),不再測;沒有裝後 doctor 重驗
  環境總管 envmgr 照 v0103 在並行段跑。其餘(心跳 · 進度條 · 收尾 · 推收據)照 v0103。
用法:python VIA_FastRun_v0104.py --set env,vrn,vdf[,fidelity] [--lanes N] [--timeout 秒] [--push] [--selftest]
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
from pathlib import Path

HERE = Path(__file__).resolve()
FAMILY = "VIA_FastRun"
TAG = "VIA_FastRun v0104"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0104", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
P2 = PRIOR.PRIOR                                          # v0102:run_job · hub_path · doctor_plan · _DONE · _LOCK
BASE = PRIOR.BASE                                         # v0100
VIA = BASE.VIA
DOCTOR_BEFORE = PRIOR.DOCTOR_BEFORE                       # 含 envgov(八路掃 base 與 via_* 各境)
RISK_KEYS = ("envgov", "gate_conflict", "gate_doctor")
REBUILD_NEXT = "via-envgov plan → via-envgov apply --approve(REBUILD 段:移開風險立刻重建)→ 重建後再跑 via-health"


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def doctor_dir() -> Path:
    return Path(os.environ.get("VIA_ROOT") or VIA) / "VIA_Reports" / "vcgc_hub" / "doctor"


def plan_file() -> Path:
    return VIA / "VIA_Reports" / "install_gate" / "PLANCHECK_latest.json"


def conflict_risks(doc: dict) -> list:
    """現在的環境有沒有衝突風險:pip check 衝突 · envgov(八路)/ gate_conflict / gate_doctor 任一紅。"""
    risks = ["pip check:%s" % c for c in ((doc.get("plan") or {}).get("conflicts") or [])]
    for p in doc.get("plugins") or []:
        if p.get("key") in RISK_KEYS and p.get("lamp") == "RED":
            risks.append("%s 紅(%s)" % (p["key"], p.get("zh", "")))
    return risks


def _read(p: Path) -> dict:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


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
    step("env:doctor_before", ["doctor", "--only", *DOCTOR_BEFORE], 900)
    if (doctor_dir() / "DOCTOR_latest.txt").exists():
        shutil.copy2(doctor_dir() / "DOCTOR_latest.txt", out / "DOCTOR_before.txt")
    risks = conflict_risks(_read(doctor_dir() / "DOCTOR_latest.json"))
    if risks:
        for r in risks[:8]:
            BASE.say("env 衝突風險 · %s" % r[:150])
        BASE.say("env 有衝突風險 → 不新增(先移開風險重建):%s" % REBUILD_NEXT)
        done(2)
        return res, ["env:plan_check / install(現在的環境有衝突風險 %d 項 → 先重建再新增)" % len(risks)]
    plan = P2.doctor_plan()
    BASE.say("env 現況無衝突 · 沒裝的工具 %d 個列入新增:%s" % (len(plan), " ".join(plan) or "—"))
    if not plan:
        done(2)
        return res, []
    step("env:plan_check", ["install", "--yes", "--plan-check", *plan], 900)
    pc = _read(plan_file())
    if pc:
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


_RUN_ENV0 = PRIOR.run_env                                # v0103 的 env 組(前版自測照它跑)


def _install():
    PRIOR.run_env = run_env                              # v0103 main 叫它模組裡的 run_env
    PRIOR.TAG = TAG
    BASE.HERE, BASE.TAG = HERE, TAG
    P2.HERE = HERE                                       # v0102 via_vcgc 用它算經 VCGC 重新進來的檔


_install()


def main(argv=None) -> int:
    a = list(sys.argv[1:] if argv is None else argv)
    if a[:1] in (["--selftest"], ["selftest"]):
        return selftest()
    return PRIOR.main(a)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:300]) if note and not cond else ""), flush=True)

    print("[計] %s 自測開始(本版 6 項 · 前版 %s · 暫存夾 · 假中樞)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 鏈:前版 v0103 · v0103 main 用的 run_env 換成本版 · 重新進來跑本檔", PRIOR_PATH.name == "VIA_FastRun_v0103.py"
        and PRIOR.run_env is run_env and BASE.HERE == HERE and P2.HERE == HERE and "envgov" in DOCTOR_BEFORE)
    doc_ok = {"plan": {"conflicts": [], "pip": ["rich"]}, "plugins": [{"key": "envgov", "lamp": "GREEN"}, {"key": "gate_doctor", "lamp": "YELLOW"}]}
    doc_bad = {"plan": {"conflicts": ["a 1.0 has requirement b<2, but you have b 3.0."]}, "plugins": [{"key": "envgov", "lamp": "RED", "zh": "八樞"}]}
    chk("T2 衝突風險:pip check 衝突 + envgov 紅 → 2 項;黃不算風險", conflict_risks(doc_ok) == [] and len(conflict_risks(doc_bad)) == 2, conflict_risks(doc_bad))
    keep = (P2.run_job, P2.doctor_plan, P2.hub_path, globals()["doctor_dir"], globals()["plan_file"])
    calls = []
    with tempfile.TemporaryDirectory(prefix="fastrun104_") as td:
        td = Path(td)
        dd, pf = td / "doctor", td / "PLANCHECK_latest.json"
        dd.mkdir()

        def scenario(doc, pc, plan):
            calls.clear()
            (dd / "DOCTOR_latest.json").write_text(json.dumps(doc), encoding="utf-8")
            pf.write_text(json.dumps(pc), encoding="utf-8") if pc is not None else pf.unlink(missing_ok=True)
            P2.doctor_plan = lambda via=VIA: list(plan)
            P2._DONE.update(n=0, total=3)
            r, s = run_env(td, 60)
            return [c for c in calls], s, P2._DONE["n"]
        try:
            P2.hub_path = lambda: Path("hub.py")
            P2.run_job = lambda job, out_, timeout: (calls.append(job["argv"][2:]) or {"name": job["name"], "rc": 0, "secs": 0.0, "lamp": "GREEN", "bits": []})
            globals()["doctor_dir"], globals()["plan_file"] = (lambda: dd), (lambda: pf)
            c_bad, s_bad, n_bad = scenario(doc_bad, None, ["rich"])
            c_ok, s_ok, n_ok = scenario(doc_ok, {"lamp": "YELLOW", "plan": ["rich==1"], "new_conflicts": [], "special": [{"pkg": "spacy", "env": "via_nlp"}]}, ["rich", "spacy"])
            c_red, _, n_red = scenario(doc_ok, {"lamp": "RED", "plan": ["rich==1"], "new_conflicts": ["x"], "why": ["新增衝突"]}, ["rich"])
            c_none, _, n_none = scenario(doc_ok, None, [])
        finally:
            P2.run_job, P2.doctor_plan, P2.hub_path = keep[:3]
            globals()["doctor_dir"], globals()["plan_file"] = keep[3:]
    chk("T3 有衝突風險:只做全面檢視 · 不查計畫 · 不裝 · 略過寫明要先重建",
        c_bad == [["doctor", "--only", *DOCTOR_BEFORE]] and n_bad == 2 and "重建" in s_bad[0], (c_bad, s_bad))
    chk("T4 無衝突:檢視 → 三鏡像計畫 → 直接照計畫裝(不再測 · 沒有裝後 doctor)",
        c_ok == [["doctor", "--only", *DOCTOR_BEFORE], ["install", "--yes", "--plan-check", "rich", "spacy"], ["install", "--yes", "--from-plan"]] and not s_ok, c_ok)
    chk("T5 計畫紅(推算新衝突)→ 查完不裝;沒有要新增的 → 只檢視", [c[0] for c in c_red] == ["doctor", "install"] and len(c_red) == 2 and n_red == 1
        and c_none == [["doctor", "--only", *DOCTOR_BEFORE]] and n_none == 2, (c_red, c_none))
    src = HERE.read_text(encoding="utf-8")
    chk("T6 檔面:加速器橋 · 零 TA-Lib · 不寫同意閘 · 沒有寫死的使用者路徑",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src) and not re.search(r"[A-Z]:\\\\Users\\\\[a-z]", src))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(前版自己的 run_env / HERE / TAG)" % PRIOR_PATH.name, flush=True)
    keep2 = (PRIOR.run_env, PRIOR.TAG, BASE.HERE, BASE.TAG, P2.HERE)
    PRIOR.run_env, PRIOR.TAG = _RUN_ENV0, "VIA_FastRun v0103"
    PRIOR._install()                                     # 前版自己的 HERE / TAG / render
    try:
        rc_prior = PRIOR.selftest()
    finally:
        PRIOR.run_env, PRIOR.TAG, BASE.HERE, BASE.TAG, P2.HERE = keep2
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
