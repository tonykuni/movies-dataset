#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL056_InstallGate v0106 — 薄尾(v0104 · v0105 一字不動):安裝計畫綁定目標 Python 環境(PR #735 Codex P2)

Codex P2:「--plan-check 在一個環境跑、--from-plan 在另一個環境跑(同一台)時,計畫照樣被接受:machine_hash() 只認主機名與作業系統,
  沒記直譯器 / 環境;解析只含規劃環境缺的件、安裝又用 --no-deps → 拿到別的環境裝,可能漏相依或裝進不相容的釘版,而且沒查衝突。」
本版:
  · --plan-check 的計畫多記「目標環境」:直譯器實際路徑 · sys.prefix · base_prefix · Python 版本 · 裝到使用者層還是環境本身。
  · --from-plan 只收「目標環境跟這次執行的直譯器一模一樣」的計畫;不同 → 拒絕(零安裝),沒記目標環境的舊計畫 → 拒絕(重跑 --plan-check)。
其餘(三鏡像 · 分流 · 推算衝突 · 直接照計畫裝不再測)照 v0105。不 import 他系統。零 TA-Lib。
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
import os
import platform
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
FAMILY = "CGC_MDL056_InstallGate"
TAG = "CGC_MDL056_InstallGate v0106"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0106", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
_PLAN_CHECK0, _LOAD_PLAN0 = PRIOR.plan_check, PRIOR.load_plan


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def env_identity() -> dict:
    """這次執行的直譯器與它的安裝目標(跟 v0105 resolve_argv / pip install 用的是同一個)。"""
    exe = Path(sys.executable)
    try:
        exe = exe.resolve()
    except OSError:
        pass
    return {"exe": os.path.normcase(str(exe)), "prefix": os.path.normcase(str(Path(sys.prefix))),
            "base_prefix": os.path.normcase(str(Path(getattr(sys, "base_prefix", sys.prefix)))), "python": platform.python_version(),
            "install_target": "user-site" if PRIOR._user_flag() else "env"}


def plan_check(pkgs: list, run=None, env: dict | None = None, say=print) -> dict:
    rep = _PLAN_CHECK0(pkgs, run=run, env=env, say=say)
    rep["target"] = env_identity()
    rep["engine"] = TAG
    return rep


def load_plan(now: float | None = None) -> tuple:
    rep, why = _LOAD_PLAN0(now)
    if rep is None:
        return rep, why
    tgt, me = rep.get("target"), env_identity()
    if not tgt:
        return None, "計畫沒有記目標 Python 環境(v0105 以前做的)→ 用這個環境重跑 --plan-check"
    diff = [k for k in me if tgt.get(k) != me[k]]
    if diff:
        return None, "計畫是給別的 Python 環境做的(%s 不同:計畫 %s / 這次 %s)→ 用這個環境重跑 --plan-check" % (
            diff[0], tgt.get(diff[0]), me[diff[0]])
    return rep, ""


PRIOR.plan_check = plan_check                              # v0105 main 叫它模組裡的 plan_check / load_plan
PRIOR.load_plan = load_plan


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

    print("[計] %s 自測開始(本版 5 項 · 前版 %s · 零網路 · 零安裝)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 鏈:前版 v0105 · v0105 main 用的 plan_check / load_plan 換成本版", PRIOR_PATH.name == "CGC_MDL056_InstallGate_v0105.py"
        and PRIOR.plan_check is plan_check and PRIOR.load_plan is load_plan)
    me = env_identity()
    chk("T2 目標環境記直譯器實際路徑 · prefix · 版本 · 裝到哪", me["exe"] and me["prefix"] and me["python"] == platform.python_version()
        and me["install_target"] in ("user-site", "env"), me)
    keep_root = os.environ.get("VIA_ROOT")
    got = []
    with tempfile.TemporaryDirectory(prefix="gate106_") as td:
        os.environ["VIA_ROOT"] = td
        PRIOR._TEST["consent"] = True
        keep_lr = PRIOR.LIBREG
        PRIOR.LIBREG = Path(td) / "libreg.json"
        try:
            base = {"ts": PRIOR.datetime.now(PRIOR.timezone.utc).isoformat(timespec="seconds"), "machine": PRIOR.PRIOR.machine_hash(), "lamp": "GREEN",
                    "plan": ["rich==1.0"], "requested_pins": ["rich==1.0"], "new_conflicts": [], "ref": {"label": "pypi-official", "url": "https://pypi.org/simple"}, "why": []}
            inst = lambda a: got.append(a) or (0, "ok")       # noqa: E731
            PRIOR.write_plan(dict(base))                                          # v0105 做的舊計畫:沒有 target
            rc_old = PRIOR.from_plan(installer=inst, say=lambda *_: None)
            PRIOR.write_plan(dict(base, target=dict(me, exe=me["exe"] + "_other")))   # 別的直譯器
            rc_other = PRIOR.from_plan(installer=inst, say=lambda *_: None)
            PRIOR.write_plan(dict(base, target=dict(me, install_target="env" if me["install_target"] == "user-site" else "user-site")))
            rc_tgt = PRIOR.from_plan(installer=inst, say=lambda *_: None)
            n_refused = len(got)
            PRIOR.write_plan(dict(base, target=me))
            rc_ok = PRIOR.from_plan(installer=inst, say=lambda *_: None)
        finally:
            PRIOR._TEST.clear()
            PRIOR.LIBREG = keep_lr
            os.environ.pop("VIA_ROOT", None) if keep_root is None else os.environ.__setitem__("VIA_ROOT", keep_root)
    chk("T3 沒記目標環境的舊計畫 · 別的直譯器 · 裝到別處 → 都拒絕(rc 3 · 一次都沒裝)", rc_old == rc_other == rc_tgt == 3 and n_refused == 0,
        (rc_old, rc_other, rc_tgt, n_refused))
    chk("T4 同一個直譯器做的計畫 → 照計畫一次裝(--no-deps · 參考鏡像)", rc_ok == 0 and got == [["--no-deps", "--index-url", "https://pypi.org/simple", "rich==1.0"]], got)
    src = HERE.read_text(encoding="utf-8")
    chk("T5 檔面:加速器橋 · 零 TA-Lib · 本檔不設同意閘 · 不 import 他系統",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src) and not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_)", src, re.M))
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(plan_check / load_plan 還原成前版的)" % PRIOR_PATH.name, flush=True)
    PRIOR.plan_check, PRIOR.load_plan = _PLAN_CHECK0, _LOAD_PLAN0
    try:
        rc_prior = PRIOR.selftest()
    finally:
        PRIOR.plan_check, PRIOR.load_plan = plan_check, load_plan
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
