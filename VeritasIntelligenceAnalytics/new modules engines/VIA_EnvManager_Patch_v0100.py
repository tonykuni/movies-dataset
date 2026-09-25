#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VIA_EnvManager 強化補丁 v0100（只增不減）.

只做一件事：把 def_build_envmanager_state() 的重複掃描擋掉。

現況：該函式在檔案裡被呼叫 8 次，且 def_choose_target_env_for_package()
每次都會叫它一次。所以 plan-install 6 個套件 = 6 次完整環境掃描，
23 個環境各跑 pip 探測，串起來幾十分鐘沒有輸出 —— 這就是卡斷的原因。

做法：以 functools 包一層有存活期的快取，同一次執行內只掃一次。
原始函式保留為 _uncached，隨時可退回。不刪任何東西。

用法：
    python VIA_EnvManager_Patch_v0100.py --target "<VIA_EnvManager.py 路徑>"
    python VIA_EnvManager_Patch_v0100.py --target "..." --apply
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


import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

MARKER = "# VIA_PATCH_STATE_CACHE_v0100"

BLOCK = '''

''' + MARKER + '''  ==========================================
# 只增不減：原函式改名保留，外層套快取。移除本區塊即可完全還原。
import functools as _via_functools
import time as _via_time

_VIA_STATE_TTL_SECONDS = 120
_via_state_cache = {"stamp": 0.0, "value": None}


def _via_build_state_cached():
    """同一次執行內只掃一次；超過 TTL 才重掃。"""
    now = _via_time.monotonic()
    if (_via_state_cache["value"] is not None
            and (now - _via_state_cache["stamp"]) < _VIA_STATE_TTL_SECONDS):
        return _via_state_cache["value"]
    value = _via_build_envmanager_state_uncached()
    _via_state_cache["stamp"] = now
    _via_state_cache["value"] = value
    return value


def via_invalidate_state_cache():
    """任何會改變環境的動作之後呼叫，強制下次重掃。"""
    _via_state_cache["stamp"] = 0.0
    _via_state_cache["value"] = None


_via_build_envmanager_state_uncached = def_build_envmanager_state
def_build_envmanager_state = _via_build_state_cached
''' + MARKER + '''_END ====================================
'''


def main() -> int:
    parser = argparse.ArgumentParser(prog="VIA_EnvManager_Patch_v0100.py")
    parser.add_argument("--target", required=True)
    parser.add_argument("--ttl", type=int, default=120)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    target = Path(args.target).expanduser().resolve()
    if not target.is_file():
        print("找不到檔案：%s" % target, file=sys.stderr)
        return 2
    text = target.read_text(encoding="utf-8", errors="replace")

    calls = text.count("def_build_envmanager_state()")
    print("目前 def_build_envmanager_state() 被呼叫 %d 次" % calls)

    if MARKER in text:
        print("已經套用過此補丁，不重複套用（冪等）")
        return 0

    block = BLOCK.replace("_VIA_STATE_TTL_SECONDS = 120",
                          "_VIA_STATE_TTL_SECONDS = %d" % args.ttl)
    patched = text.rstrip("\n") + "\n" + block

    import ast
    try:
        ast.parse(patched)
    except SyntaxError as exc:
        print("套用後語法檢查失敗，中止：line %s %s" % (exc.lineno, exc.msg), file=sys.stderr)
        return 1
    print("套用後語法檢查通過")

    if not args.apply:
        print("")
        print("DRY-RUN：未修改檔案。確認後加 --apply")
        print("預期效果：plan-install 批次從 N 次全環境掃描降為 1 次")
        return 0

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup = target.with_name(target.stem + "_prepatch_" + stamp + target.suffix)
    shutil.copy2(target, backup)
    target.write_text(patched, encoding="utf-8")
    print("備份 -> %s" % backup.name)
    print("已套用。移除檔尾 %s 區塊即可完全還原。" % MARKER)
    return 0


if __name__ == "__main__":
    sys.exit(main())
