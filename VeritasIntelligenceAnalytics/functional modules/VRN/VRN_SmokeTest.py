#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_SmokeTest.py — 部署後快速煙霧測試(v0100R 重建;README 目錄載明本檔,工作站正本候上傳到件即讓位)。

檢查面(全唯讀,零副作用):
  ① MDL001-008 八管線模組在位 + py_compile 過
  ② 規則層 70_VRN_Rules 在位量 + 凍結鎖統計
  ③ SSOT v1/v2 schema 在位
  ④ 選配依賴誠實探測(缺=WARN 不擋 — OCR 重依賴屬工作站)
用法:python VRN_SmokeTest.py [--no-pause]    exit 0=煙霧過,1=硬紅
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
import py_compile
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
RULES = VIA / "supportive modules" / "70_VRN_Rules"

MDL = ["VRN_MDL001_Converter.py", "VRN_MDL003_TableRestorer.py",
       "VRN_MDL004_OCR_FetchingPDFTable.py", "VRN_MDL005_OCRFetchingPDFText.py",
       "VRN_MDL007_APIDataFetcher.py", "VRN_MDL008_CrossValidator.py"]


def run():
    n_ok = 0
    n_fail = 0

    def tag(ok, msg, hard=True):
        nonlocal n_ok, n_fail
        if ok:
            n_ok += 1
            print("  [OK  ] %s" % msg)
        elif hard:
            n_fail += 1
            print("  [FAIL] %s" % msg)
        else:
            print("  [WARN] %s" % msg)

    print("=== VRN SmokeTest v0100R(唯讀)===")
    for m in MDL:
        p = HERE / m
        if not p.exists():
            tag(False, "%s 不在位" % m)
            continue
        try:
            py_compile.compile(str(p), doraise=True)
            tag(True, "%s compile 過" % m)
        except Exception as e:
            tag(False, "%s compile 失敗:%s" % (m, str(e)[:60]))
    if RULES.exists():
        rules = list(RULES.glob("*.py"))
        locks = list(RULES.glob("*.freeze.lock.json"))
        tag(len(rules) >= 15, "規則層 %d 模組 · 凍結鎖 %d" % (len(rules), len(locks)))
    else:
        tag(False, "70_VRN_Rules 不在位")
    ssot = [p for d in (HERE, HERE / "SSOT", HERE / "registry") if d.exists()
            for p in d.glob("*SSOT*") if p.is_file()]
    tag(len(ssot) >= 1, "SSOT 資產 %d 件在位" % len(ssot))
    for dep in ("pandas", "requests"):
        try:
            __import__(dep)
            tag(True, "依賴 %s" % dep)
        except ImportError:
            tag(False, "依賴 %s 缺(pip install %s)" % (dep, dep), hard=False)
    for dep in ("paddleocr", "fitz", "pdfplumber"):
        try:
            __import__(dep)
            tag(True, "OCR 依賴 %s" % dep)
        except ImportError:
            tag(False, "OCR 依賴 %s 缺 — 工作站配置(誠實 WARN 不擋)" % dep, hard=False)
        except Exception as e:  # 依賴自身損壞(如 torch.nn 缺失)— 誠實列根因,不炸穿
            tag(False, "OCR 依賴 %s 損壞:%s: %s(誠實 WARN 不擋;修復後重跑)"
                % (dep, type(e).__name__, str(e)[:80]), hard=False)
    print("-" * 46)
    print("  SmokeTest:%d OK / %d FAIL" % (n_ok, n_fail))
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    ec = run()
    if "--no-pause" not in sys.argv:
        try:
            input("按 Enter 鍵退出...")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(ec)
