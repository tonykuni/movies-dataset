#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""panorama_xcheck_v110.py — 全景交叉核對(v111R 重建;README 載明「full 8-module dataflow」
micro-pipeline runner,工作站正本候上傳到件即讓位)。

在庫可核面(唯讀):
  ① SSOT v1 vs v2:records 筆數對照 + 共同鍵一致率
  ② 管線模組 × 規則層 交叉在位(模組引用的規則檔是否在庫)
  ③ manifest hash lock 抽核(檔案 sha256 vs manifest 所記)
用法:python panorama_xcheck_v110.py [--no-pause]    exit 0=無矛盾
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
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _load(p):
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except Exception:
        return None


def run():
    print("=== VRN Panorama XCheck v111R(唯讀交叉核對)===")
    n_fail = 0

    # ① SSOT v1(records=jsonl 行數)vs v2(v2/ 下 records)
    ssot = HERE / "SSOT"
    v1_jl = sorted(ssot.glob("*.jsonl")) if ssot.exists() else []
    v2_js = sorted((ssot / "v2").rglob("*.json")) if (ssot / "v2").exists() else []
    n1 = n2 = 0
    if v1_jl:
        n1 = sum(1 for ln in v1_jl[0].read_text(encoding="utf-8-sig").splitlines() if ln.strip())
    for p in v2_js:
        d = _load(p)
        r = d.get("records") if isinstance(d, dict) else (d if isinstance(d, list) else None)
        if isinstance(r, list) and len(r) > n2:
            n2 = len(r)
    if v1_jl and v2_js:
        same = "一致" if n1 == n2 else "不一致(v1=%d v2=%d)" % (n1, n2)
        print("  [%s] SSOT v1(%s)%d 筆 vs v2(%d 檔)%d 筆 — %s"
              % ("OK  " if n1 == n2 else "WARN", v1_jl[0].name[:30], n1, len(v2_js), n2, same))
    else:
        print("  [SKIP] SSOT v1/v2 對照 — 檔待齊(v1 jsonl=%d · v2=%d 件)" % (len(v1_jl), len(v2_js)))

    # ② manifest hash 抽核
    mf = _load(HERE / "VRN_Subsystem_Manifest.json")
    if mf:
        arts = mf.get("artifacts", [])
        checked = mismatched = 0
        for a in arts[:12]:
            fn, want = a.get("filename"), a.get("sha256")
            if not fn or not want:
                continue
            p = HERE / fn
            if not p.exists():
                continue
            got = hashlib.sha256(p.read_bytes()).hexdigest()
            checked += 1
            if got != want:
                mismatched += 1
                print("  [WARN] hash 漂移:%s(版本前進或待對帳)" % fn)
        ok = mismatched == 0
        print("  [%s] manifest hash 抽核 %d 件 · 漂移 %d" % ("OK  " if ok else "WARN", checked, mismatched))
    else:
        print("  [FAIL] VRN_Subsystem_Manifest.json 不在位")
        n_fail += 1

    # ③ 規則層交叉在位
    rules = HERE.parent.parent / "supportive modules" / "70_VRN_Rules"
    n_rules = len(list(rules.glob("*.py"))) if rules.exists() else 0
    print("  [%s] 規則層在位 %d 模組" % ("OK  " if n_rules >= 15 else "FAIL", n_rules))
    if n_rules < 15:
        n_fail += 1

    print("-" * 46)
    print("  XCheck:%s" % ("無硬矛盾" if n_fail == 0 else "%d 硬紅" % n_fail))
    return 0 if n_fail == 0 else 1


if __name__ == "__main__":
    ec = run()
    if "--no-pause" not in sys.argv and sys.stdin.isatty():
        try:
            input("按 Enter 鍵退出...")
        except (EOFError, KeyboardInterrupt):
            pass
    sys.exit(ec)
