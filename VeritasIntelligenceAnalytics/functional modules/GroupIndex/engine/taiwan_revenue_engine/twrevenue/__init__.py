"""台股月營收動能引擎 (Taiwan Stock Monthly Revenue Engine).

模組:
    fetch    -- 從 MOPS 公開資訊觀測站抓取全上市/上櫃月營收
    classify -- 產業分類 + 原物料/週期股分流
    analyze  -- 三層動能分析引擎 (累計YoY / 多月YoY趨勢 / MoM vs 季節性)
    report   -- 產生單頁 HTML 儀表板
    cli      -- 命令列進入點 (fetch / analyze / report / run)
"""
# ===== [VIA:ACCEL-BRIDGE:v0100] SuperAccel 加速器橋(全引擎導入令 2026-08-18;graceful 零行為變更) =====
try:
    import sys as _sa_sys
    from pathlib import Path as _sa_Path
    _sa_p = _sa_Path(__file__).resolve()
    while _sa_p.parent != _sa_p:
        if (_sa_p / "supportive modules" / "VIA_SuperAccel_Module.py").exists():
            _sa_sys.path.insert(0, str(_sa_p / "supportive modules"))
            break
        _sa_p = _sa_p.parent
    import VIA_SuperAccel_Module as VIA_ACCEL  # accel_map/fetch/pip_install/run_fast
except Exception:
    VIA_ACCEL = None  # graceful:加速器缺席零影響
# ===== [VIA:ACCEL-BRIDGE:END] =====

__version__ = "1.0.0"
