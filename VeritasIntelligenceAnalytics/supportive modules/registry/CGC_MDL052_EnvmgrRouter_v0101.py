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


# ===== [VIA:TAILPICK-BRIDGE:v0100] 尾版取用正典橋(批590/591;正典 SUP_MDL751_VIATailPick)=====
# 本群原本的行為:只吃一個參數,root 固定 HERE
# 批590 量過:CGC 族 32 份 `newest` 是 **13 個行為群**,不是同一件事(最大兩群參數順序相反、
# 兩支走 rglob、一支缺件回 pattern、一支按 mtime 排序)。所以正典把差異變成**明示選項**,
# 並逐群重放證零損失(15 種具名變體 × 6 組語料,90 組全同)。
# 這裡是**綁定**不是再定義一支 def:寫 def 的話能力庫裡這一家族還在,家族數不會掉(LL143)。
import importlib.util as _tp_ilu
from pathlib import Path as _tp_Path
_TP_MOD = None
_tp_p = _tp_Path(__file__).resolve()
while _tp_p.parent != _tp_p:
    _tp_hits = sorted((_tp_p / "supportive modules").glob("SUP_MDL751_VIATailPick_v*.py"))
    if _tp_hits:
        _tp_spec = _tp_ilu.spec_from_file_location("VIA_TAILPICK", _tp_hits[-1])
        _TP_MOD = _tp_ilu.module_from_spec(_tp_spec)
        _tp_spec.loader.exec_module(_TP_MOD)
        break
    _tp_p = _tp_p.parent
if _TP_MOD is None:      # 大聲壞掉:尾版取錯是無聲的錯(整條鏈指到舊引擎,沒人會發現)
    raise RuntimeError("[FAIL] 尾版取用正典缺席:supportive modules/SUP_MDL751_VIATailPick_v*.py")
newest = _TP_MOD.bind(order="pr", root_default=HERE)
# ===== [VIA:TAILPICK-BRIDGE:END] =====


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
