#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
"""VIA_ModuFuse v0102 — 薄尾:補加速器橋(生效)· 吃 --selftest · 其餘全部照 v0101(操作員原件一字不動)

2026-11-24 VCGC 量測:
  ① 橋掃(CGC_MDL124 --subsystems 乾跑)VCGC 側唯一缺橋 = VIA_ModuFuse_v0101.py(操作員上傳原件,不能注橋改位元組)
  ② 省 Token 讀卡報 VERB:只吃位置動詞 selftest,不吃 --selftest(全樹契約 L53)
本版:
  · 第 3 行標記 + SuperAccel 橋(與全樹同一段);另外沒給 --accelerator 也沒設 VIA_CELERITAS_PATH 時,
    從工具鎖冊(VIA_ToolVersion_Lock_v0100.json 的 accelerator)取鎖定的 VeritasCeleritas 路徑交給前版 → 加速器真的載得到,不只標記
  · --selftest → 前版 selftest
不設同意閘、不連網、不改前版。
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
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = "VIA_ModuFuse v0102"


def _vnum(p) -> int:
    m = re.search(r"_v(\d+)$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob("VIA_ModuFuse_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
if PRIOR_PATH.stem in sys.modules:
    PRIOR = sys.modules[PRIOR_PATH.stem]
else:
    _spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem, PRIOR_PATH)
    PRIOR = importlib.util.module_from_spec(_spec)
    sys.modules[PRIOR_PATH.stem] = PRIOR
    _spec.loader.exec_module(PRIOR)


def __getattr__(name):
    return getattr(PRIOR, name)


def locked_celeritas(here: Path = HERE):
    """工具鎖冊的 accelerator 路徑(倉根相對);找不到回 None。"""
    try:
        lk = json.loads((here / "VIA_ToolVersion_Lock_v0100.json").read_text(encoding="utf-8"))
        rel = (lk.get("accelerator") or {}).get("path", "")
    except (OSError, ValueError):
        return None
    for root in [here] + list(here.parents):
        p = root / rel
        if rel and p.is_file():
            return p
    return None


def main() -> int:
    argv = sys.argv[1:]
    if "--accelerator" not in argv and not os.environ.get("VIA_CELERITAS_PATH"):
        acc = locked_celeritas()
        if acc:
            os.environ["VIA_CELERITAS_PATH"] = str(acc)
    if argv[:1] == ["--selftest"]:
        sys.argv = [sys.argv[0], "selftest"] + argv[1:]
        rc = PRIOR.main()
        ok = rc in (0, None)
        print("[計] %s 自測 %s(--selftest → 前版 selftest rc=%s · 加速器 %s)" % (TAG, "PASS" if ok else "FAIL", rc,
              "鎖定版" if os.environ.get("VIA_CELERITAS_PATH") else "沒有"), flush=True)
        return 0 if ok else 1
    return PRIOR.main()


if __name__ == "__main__":
    raise SystemExit(main())
