"""VeritasPulse desktop launcher — wraps the single-file app in a native window.
Packaged to a Windows .exe with PyInstaller (see Build-Exe.ps1).
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
import os
import sys


def app_path() -> str:
    candidates = [os.path.dirname(os.path.abspath(sys.executable)),
                  getattr(sys, "_MEIPASS", ""),
                  os.path.dirname(os.path.abspath(__file__)),
                  os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")]
    for d in candidates:
        if d:
            p = os.path.join(d, "VeritasPulse_App.html")
            if os.path.exists(p):
                return p
    return "VeritasPulse_App.html"


def main():
    try:
        import webview
    except ImportError:
        sys.exit("pip install pywebview  (see Build-Exe.ps1)")
    webview.create_window("VeritasPulse", app_path(),
                          width=1400, height=900, min_size=(900, 600))
    webview.start()


if __name__ == "__main__":
    main()
