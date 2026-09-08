# -*- coding: utf-8 -*-
"""via_envmgr_router_v0101.py — EnvManager 路由器 v0101(批381:+治理動詞→MDL135 統一治理引擎;cmd 零分支化;每層印橫幅可稽核)。

路由:
  conflicts/scan                         → NoStall 加速包覆器(CGC_MDL051 動態最新)
  govern/panorama/plan/apply/lkgc/rollback/matrix/digest
                                         → CGC_MDL135_EnvGovernance 尾版(批381:全景式分析·uv 快篩·base 該有冊·
                                            衝突立拔家族路由·Zero-Hydra 拓撲三輪·LKGC/rollback·四分區矩陣)
  其餘(plan-install/execute-install/rebuild-candidates/env/alias/export-plan/selftest)
                                         → 正本 VIA_EnvManager.py 直呼(政策母版零觸碰)
v0100→v0101:+GOV_VERBS 治理動詞冊;govern 無參數=MDL135 run --offline(唯讀);apply 仍需 --approve(授權閉環);
             MDL135 缺席=誠實印缺並回退正本(零假綠)。
"""
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
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUPP = HERE.parent

# 治理動詞冊(批381):短令動詞 → MDL135 動詞
GOV_VERBS = {"govern": "run", "run-gov": "run", "envgov": "run", "panorama": "panorama", "plan": "plan", "apply": "apply",
             "lkgc": "lkgc", "rollback": "rollback", "matrix": "matrix", "digest": "digest", "selftest-gov": "--selftest"}


def newest(pattern):
    hits = sorted(HERE.glob(pattern))
    return hits[-1] if hits else None


def main(argv):
    args = argv[1:] or ["conflicts"]
    cmd = args[0].lower()
    print("[router] via_envmgr_router_v0101 · cmd=%s" % cmd, flush=True)
    if cmd in ("conflicts", "scan"):
        ns = newest("CGC_MDL051_EnvmgrNostall_v0*.py")
        if ns:
            print("[router] → NoStall 加速層:%s" % ns.name, flush=True)
            return subprocess.call([sys.executable, str(ns)] + args)
        print("[router] NoStall 不在位 — 回退正本直呼(誠實警告:可能久跑)", flush=True)
    elif cmd in GOV_VERBS:
        gov = newest("CGC_MDL135_EnvGovernance_v*.py")
        if gov:
            fwd = [GOV_VERBS[cmd]] + args[1:]
            if GOV_VERBS[cmd] == "run" and not any(a in ("--approve", "--online") for a in fwd):
                fwd.append("--offline")  # 預設唯讀(同意閘/授權閉環;--approve 或 --online 才上網)
            fwd = [a for a in fwd if a != "--online"]
            print("[router] → 治理引擎(批381):%s %s" % (gov.name, " ".join(fwd)), flush=True)
            return subprocess.call([sys.executable, str(gov)] + fwd)
        print("[router] MDL135 治理引擎不在位(誠實)— 回退正本直呼", flush=True)
    else:
        print("[router] → 正本直呼:VIA_EnvManager.py", flush=True)
    return subprocess.call([sys.executable, str(SUPP / "VIA_EnvManager.py")] + args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
