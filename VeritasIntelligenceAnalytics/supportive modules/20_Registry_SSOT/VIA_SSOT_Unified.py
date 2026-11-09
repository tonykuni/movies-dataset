# -*- coding: utf-8 -*-
"""VIA_SSOT_Unified.py — 轉接殼(RC-1 W1 Conflict Fix · CONFLICT-00004 · 2026-11-09)

這個路徑保留,內容以正本為準:
  正本 supportive modules/VIA_SSOT_Unified.py
  副本原內容與正本逐位元相同(sha b3c9cfa6244b)
殼不帶任何邏輯:當模組載入時把正本的公開名稱接進來;當腳本執行時原樣執行正本。
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
import pathlib as _pl, runpy as _rp
_CANON = _pl.Path(__file__).resolve().parents[2] / 'supportive modules/VIA_SSOT_Unified.py'
if not _CANON.is_file():
    raise FileNotFoundError("正本不在:%s(轉接殼 %s 不接)" % (_CANON, __file__))
if __name__ == "__main__":
    _rp.run_path(str(_CANON), run_name="__main__")
else:
    globals().update({k: v for k, v in _rp.run_path(str(_CANON), run_name=__name__).items() if not k.startswith("__")})
