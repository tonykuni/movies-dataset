# -*- coding: utf-8 -*-
"""via_envmgr_router_v0100.py — EnvManager 路由器 v0100(cmd 零分支化;每層印橫幅可稽核)。

路由:conflicts/scan → NoStall 加速包覆器(動態最新);其餘命令 → 正本 VIA_EnvManager.py 直呼。
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SUPP = HERE.parent


def newest(pattern):
    hits = sorted(HERE.glob(pattern))
    return hits[-1] if hits else None


def main(argv):
    args = argv[1:] or ["conflicts"]
    cmd = args[0].lower()
    print("[router] via_envmgr_router_v0100 · cmd=%s" % cmd, flush=True)
    if cmd in ("conflicts", "scan"):
        ns = newest("CGC_MDL051_EnvmgrNostall_v0*.py")
        if ns:
            print("[router] → NoStall 加速層:%s" % ns.name, flush=True)
            return subprocess.call([sys.executable, str(ns)] + args)
        print("[router] NoStall 不在位 — 回退正本直呼(誠實警告:可能久跑)", flush=True)
    else:
        print("[router] → 正本直呼:VIA_EnvManager.py", flush=True)
    return subprocess.call([sys.executable, str(SUPP / "VIA_EnvManager.py")] + args)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
