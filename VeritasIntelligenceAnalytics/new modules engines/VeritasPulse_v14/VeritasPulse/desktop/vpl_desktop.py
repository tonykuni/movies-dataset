"""VeritasPulse desktop launcher — wraps the single-file app in a native window.
Packaged to a Windows .exe with PyInstaller (see Build-Exe.ps1).
"""
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
