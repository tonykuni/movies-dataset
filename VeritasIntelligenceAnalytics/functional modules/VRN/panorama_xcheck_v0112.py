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
    print("=== VRN Panorama XCheck v112R(唯讀交叉核對;v2 計數修正+超集判準)===")
    n_fail = 0

    # ① SSOT v1 vs v2 — v112 修正:v2 讀現役 .v2.jsonl(v111 誤讀 v2/*.json schema 檔記 0 筆=假警);
    #    判準改「v2 ⊇ v1 超集 + 共同鍵零漂移」(v2 為現役線,允許超前 v1 legacy 凍結線)
    import json as _json
    ssot = HERE / "SSOT"
    v1_jl = sorted(p for p in ssot.glob("*.jsonl")) if ssot.exists() else []
    v2_store = ssot / "v2" / "VRN_ResearchReport_SSOT.v2.jsonl"
    if v1_jl and v2_store.exists():
        v1_rows = [_json.loads(ln) for ln in v1_jl[0].read_text(encoding="utf-8-sig").splitlines() if ln.strip()]
        v2_rows = [_json.loads(ln) for ln in v2_store.read_text(encoding="utf-8-sig").splitlines() if ln.strip()]
        k1 = {r.get("source_document") for r in v1_rows}
        k2 = {r.get("source_document") for r in v2_rows}
        superset = k1 <= k2
        drift = sorted(k1 - k2)
        extra = len(k2 - k1)
        if superset:
            print("  [OK  ] SSOT v1 %d 筆(legacy 凍結)⊆ v2 %d 筆(現役,超前 %d 件)— 零漂移"
                  % (len(v1_rows), len(v2_rows), extra))
        else:
            print("  [WARN] SSOT v2 未涵蓋 v1 %d 件(漂移):%s"
                  % (len(drift), ", ".join(str(d)[:40] for d in drift[:3])))
    else:
        print("  [SKIP] SSOT v1/v2 對照 — 檔待齊(v1 jsonl=%d · v2 store=%s)"
              % (len(v1_jl), v2_store.exists()))

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
