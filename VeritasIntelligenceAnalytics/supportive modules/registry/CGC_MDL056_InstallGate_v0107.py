#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL056_InstallGate v0107 — 薄尾(v0104 · v0105 · v0106 一字不動):照計畫裝時,裝到計畫記的那個目標(PR #735 Codex P2)

Codex P2:「在一般 virtualenv 裡規劃時,_user_flag() 不加 --user,v0106 記的安裝目標是 env;但 --from-plan 叫
  SUP_MDL737 的 pip_install 用預設 user=True,一律加 --user → 綠計畫在那個環境裝不上(pip:Can not perform a '--user' install…)。」
本版:--from-plan 沒指定安裝器時,用加速器輔助模組的 pip_install,並把 user 設成計畫記的目標
  (install_target = user-site → --user;env → 不加)。v0106 已保證計畫的目標 = 這次執行的直譯器。
其餘(三鏡像 · 分流 · 推算衝突 · 計畫綁環境 · 直接照計畫裝不再測)照 v0106 / v0105。不 import 他系統。零 TA-Lib。
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
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve()
FAMILY = "CGC_MDL056_InstallGate"
TAG = "CGC_MDL056_InstallGate v0107"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.parent.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(HERE)), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0107", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
V0105 = PRIOR.PRIOR                                        # from_plan / main 的本體(v0106 已把它的 load_plan 換成綁環境版)
_FROM_PLAN0 = V0105.from_plan


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def _accel_pip():
    import VIA_SuperAccel_Module as _accel                 # 照 v0105:經加速器輔助模組裝(同意閘 + 重試退避)
    return _accel.pip_install


def from_plan(installer=None, say=print) -> int:
    if installer is None:
        rep, _why = V0105.load_plan()
        target = ((rep or {}).get("target") or {}).get("install_target")
        pip, user = _accel_pip(), target == "user-site"
        installer = lambda argv: pip(argv, user=user)      # noqa: E731  計畫記哪裡就裝哪裡
    return _FROM_PLAN0(installer=installer, say=say)


V0105.from_plan = from_plan                                # v0105 main 叫它模組裡的 from_plan


def plan_check(pkgs: list, run=None, env: dict | None = None, say=print) -> dict:
    """同 v0106(三鏡像 · 計畫記目標環境)。尾版照樣提供:VCGC 中樞以尾版有沒有 plan_check 認得三鏡像安裝閘。"""
    return PRIOR.plan_check(pkgs, run=run, env=env, say=say)


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

    global _accel_pip
    print("[計] %s 自測開始(本版 5 項 · 前版 %s · 零網路 · 零安裝)" % (TAG, PRIOR_PATH.name), flush=True)
    chk("T1 鏈:前版 v0106 · v0105 main 用的 from_plan 換成本版", PRIOR_PATH.name == "CGC_MDL056_InstallGate_v0106.py"
        and V0105.from_plan is from_plan)
    me = PRIOR.env_identity()
    calls = []
    keep_root, keep_pip, keep_lr = os.environ.get("VIA_ROOT"), _accel_pip, V0105.LIBREG
    with tempfile.TemporaryDirectory(prefix="gate107_") as td:
        os.environ["VIA_ROOT"] = td
        V0105._TEST["consent"] = True
        V0105.LIBREG = Path(td) / "libreg.json"
        _accel_pip = lambda: (lambda pkgs, user=True: calls.append((list(pkgs), user)) or (0, "ok"))  # noqa: E731
        try:
            base = {"ts": V0105.datetime.now(V0105.timezone.utc).isoformat(timespec="seconds"), "machine": V0105.PRIOR.machine_hash(),
                    "lamp": "GREEN", "plan": ["rich==1.0"], "requested_pins": ["rich==1.0"], "new_conflicts": [],
                    "ref": {"label": "pypi-official", "url": "https://pypi.org/simple"}, "why": []}
            V0105.write_plan(dict(base, target=me))
            rc_me = V0105.from_plan(say=lambda *_: None)
            V0105.write_plan(dict(base, target=dict(me, install_target="env" if me["install_target"] == "user-site" else "user-site")))
            rc_other = V0105.from_plan(say=lambda *_: None)
        finally:
            V0105._TEST.clear()
            V0105.LIBREG = keep_lr
            _accel_pip = keep_pip
            os.environ.pop("VIA_ROOT", None) if keep_root is None else os.environ.__setitem__("VIA_ROOT", keep_root)
    want_user = me["install_target"] == "user-site"
    chk("T2 預設安裝器的 user 跟計畫記的目標一致(這台 %s → user=%s)· --no-deps 照計畫" % (me["install_target"], want_user),
        rc_me == 0 and calls[:1] == [(["--no-deps", "--index-url", "https://pypi.org/simple", "rich==1.0"], want_user)], (rc_me, calls))
    chk("T3 Codex 情境:目標不同的計畫照 v0106 拒絕(rc 3 · 沒叫安裝器)", rc_other == 3 and len(calls) == 1, (rc_other, calls))
    src = HERE.read_text(encoding="utf-8")
    chk("T4 檔面:加速器橋 · 零 TA-Lib · 本檔不設同意閘 · 不 import 他系統",
        "[VIA:ACCEL-BRIDGE:v0100]" in src and not re.search(r"^\s*(import|from)\s+talib", src, re.M)
        and not re.search(r"os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT", src) and not re.search(r"^\s*(import|from)\s+(VDF_|VRN_|VQG_|VAP_)", src, re.M))
    chk("T5 尾版照樣提供 plan_check(VCGC 中樞靠它認得三鏡像閘,不退回舊流程)", "def plan_check" in src and V0105.plan_check is PRIOR.plan_check)
    n = sum(ok)
    print("[計] %s 自測 %d/%d · %s" % (TAG, n, len(ok), "PASS" if n == len(ok) else "FAIL"), flush=True)
    print("[前版] %s 自測(from_plan 還原成前版的)" % PRIOR_PATH.name, flush=True)
    V0105.from_plan = _FROM_PLAN0
    try:
        rc_prior = PRIOR.selftest()
    finally:
        V0105.from_plan = from_plan
    print("[計] %s 自測 OK %d · FAIL %d · 前版 rc=%s" % (TAG, n, len(ok) - n, rc_prior), flush=True)
    return 0 if n == len(ok) and rc_prior == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
