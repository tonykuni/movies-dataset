"""一鍵示範：python run_demo.py
讀 config.json，跑完整流程，輸出 SSOT + 候選佇列 + Markdown 摘要。
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
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pmis_lite.pipeline import run

if __name__ == "__main__":
    cfg = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    result = run(cfg)
    print("\n" + "=" * 70)
    print("完成。以下為 Markdown 摘要預覽：\n")
    print(result["markdown"])
