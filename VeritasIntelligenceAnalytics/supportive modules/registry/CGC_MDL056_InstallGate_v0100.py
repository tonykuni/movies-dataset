#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_install_gate_v0100 — 安裝治理閘(儲存規定令 2026-08-12)
=============================================================
規定:安裝任何新 libs/工具一律透過本閘——
  ① 政策層:讀 VIA_EngineForge_Config 模板(最新版)之 policy 印示遵行
     (sandbox_first/append_only/max_rounds;嚴禁 destructive)
  ② 衝突層:裝前/裝後 pip check 快照對比,新增衝突誠實列示
     (EnvManager 深掃另走 via-envmgr——重件不在本閘 eager 跑,180s 實證)
  ③ 註冊層:VIA_Lib_Registry_v0100.json append-only 登錄
     (套件/版本/前後衝突/機碼/時戳)——lib registry 升一級 SSOT
  ④ 導入層:裝後 import 煙測 + 輔助模組 graceful 導入驗
     (SSOT/Aegis/Celeritas/NetSupport/RegistryCore)
紅線:網路工具啟用另有同意閘(VIA_NetSupport;VIA_NET_CONSENT=YES 才發包);
     pip 安裝本身屬安裝行為,walk 過本閘即為授權軌跡。
用法:via-install <pkg1> [pkg2 ...]      安裝+註冊+驗
     via-install --check-only           只跑衝突快照+輔助導入驗(零安裝)
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

import hashlib
import json
import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent.parent
LIBREG = HERE / "VIA_Lib_Registry_v0100.json"


def machine_hash() -> str:
    return hashlib.sha256(f"{platform.node()}|{platform.system()}".encode()).hexdigest()[:16]


def newest_forge_template():
    hits = sorted((VIA / "supportive modules").glob("VIA_EngineForge_Config*.template.json"))
    return hits[-1] if hits else None


def pip_check() -> list[str]:
    r = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True, timeout=180)
    return [] if r.returncode == 0 else [l for l in r.stdout.strip().splitlines() if l.strip()]


def pkg_version(name: str):
    try:
        from importlib.metadata import version
        return version(name)
    except Exception:
        return None


def support_smoke():
    out = {}
    sup = str(VIA / "supportive modules")
    if sup not in sys.path:
        sys.path.insert(0, sup)
    for m in ("VIA_SSOT_Unified", "VeritasAegisNexus", "VeritasCeleritas", "VIA_NetSupport", "VIA_RegistryCore_v1"):
        try:
            __import__(m)
            out[m] = "OK"
        except Exception as exc:
            out[m] = f"graceful({type(exc).__name__})"
    return out


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_only = "--check-only" in sys.argv
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"=== 安裝治理閘 v0100 · {'CHECK-ONLY' if check_only else '安裝 ' + ' '.join(args) if args else '?'} ===")
    if not args and not check_only:
        print(__doc__)
        return 2

    ft = newest_forge_template()
    if ft:
        pol = json.loads(ft.read_text(encoding="utf-8-sig")).get("policy", {})
        print(f"  [政策] {ft.name}:append_only={pol.get('append_only')} · sandbox_first={pol.get('sandbox_first')}"
              f" · destructive_delete={pol.get('destructive_delete')}(遵行)")
    else:
        print("  [政策] EngineForge 模板缺——候上傳(graceful,規定仍遵)")

    pre = pip_check()
    print(f"  [裝前] pip check 衝突 {len(pre)} 條" + (":" if pre else "(無衝突 base)"))
    for l in pre[:6]:
        print(f"     · {l[:100]}")

    installed = {}
    if not check_only and args:
        r = subprocess.run([sys.executable, "-m", "pip", "install", "--user", *args],
                           capture_output=True, text=True, timeout=1800)
        tail = (r.stdout + r.stderr).strip().splitlines()
        print(f"  [安裝] exit {r.returncode} · {tail[-1][:110] if tail else ''}")
        if r.returncode != 0:
            print("  [FAIL] pip 安裝失敗 — 誠實停止(不註冊)")
            for l in tail[-5:]:
                print(f"     {l[:110]}")
            return 1
        for a in args:
            base = a.split("<")[0].split(">")[0].split("=")[0].split("[")[0]
            installed[base] = pkg_version(base)
            ok = False
            try:
                __import__(base.replace("-", "_"))
                ok = True
            except Exception:
                pass
            print(f"  [驗] {base} {installed[base] or '?'} · import {'OK' if ok else '略(頂層名不同,誠實記)'}")

    post = pip_check()
    new_conf = [l for l in post if l not in pre]
    fixed = [l for l in pre if l not in post]
    print(f"  [裝後] 衝突 {len(post)} 條 · 新增 {len(new_conf)} · 解除 {len(fixed)}")
    for l in new_conf[:6]:
        print(f"     ✗ 新增:{l[:100]}")
    for l in fixed[:6]:
        print(f"     ✓ 解除:{l[:100]}")

    smoke = support_smoke()
    print("  [輔助] " + " · ".join(f"{k.split('_')[-1] if '_' in k else k}:{v}" for k, v in smoke.items()))

    reg = {"schema": "VIA.LibRegistry.v1", "ledger": []}
    if LIBREG.exists():
        try:
            reg = json.loads(LIBREG.read_text(encoding="utf-8"))
        except Exception:
            pass
    reg["ledger"].append({
        "ts": ts, "machine": machine_hash(), "mode": "check_only" if check_only else "install",
        "packages": installed or args, "pre_conflicts": pre, "post_conflicts": post,
        "support_smoke": smoke, "provenance": "via_install_gate_v0100(儲存規定令)",
    })
    LIBREG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  [註冊] {LIBREG.name} · 第 {len(reg['ledger'])} 筆(append-only)")
    return 0 if not new_conf else 1


if __name__ == "__main__":
    sys.exit(main())
