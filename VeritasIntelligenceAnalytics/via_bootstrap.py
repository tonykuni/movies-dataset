
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

# === VIA 整合層 bootstrap(自動產生) ===
# 目的:讓 VAP/VDF/VRN 三個子系統能互相 import。
# 三個子系統是平行資料夾,Python 預設不會互相看見 —— 這裡把它們一起放進 sys.path。
# 這是**環境層**的修復,不改任何模組的程式碼。
import sys as _sys, os as _os

VIA_PATHS = [
    r"C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics\functional modules\VDF",
    r"C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics\functional modules\VRN",
    r"C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics\functional modules\VAP",
    r"C:\Users\tonyk\Downloads\movies-dataset\VeritasIntelligenceAnalytics\supportive modules",
]
for _p in VIA_PATHS:
    if _os.path.isdir(_p) and _p not in _sys.path:
        _sys.path.insert(0, _p)

def via_paths():
    return list(VIA_PATHS)