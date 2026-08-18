#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
via_install_gate_v0104 — 安裝治理閘(儲存規定令 2026-08-12)
=============================================================
v0100→v0101(操作員令:透過支援模組安裝、保有導入加速器、不卡斷):
  ⑤ 醫生層 --doctor — 多層 site 同名發行版互撞掃描(使用者層 vs 系統層;
     cv2 家族專診+全庫影蔽清單)+cv2 活體探測(子行程,不卡斷)+
     免管理員修法(使用者層優先遮蔽系統層,毋須提權)
  v0101→v0102:裁決分層修——互撞只算「同層多件」;使用者層單件+
     系統層被遮蔽+活體 OK=GREEN_SHADOWED(遮蔽即勝,非病)
  v0102→v0103:cv2 統包版改錨 opencv-contrib-python(full)——實戰發現
     paddlex[doc-parser]/img2table 相依鏈錨定 contrib 非 headless,
     pip 會自動回拉 headless 裁定反成互撞源;順鏈定錨才穩
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
     via-install --doctor               環境醫生:多層互撞診斷(唯讀零安裝)
"""
from __future__ import annotations

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
    for m in ("VIA_SSOT_Unified", "VeritasAegisNexus", "VeritasCeleritas", "VIA_SuperAccel_Module", "VIA_NetSupport", "VIA_RegistryCore_v1"):
        try:
            __import__(m)
            out[m] = "OK"
        except Exception as exc:
            out[m] = f"graceful({type(exc).__name__})"
    return out


OPENCV_FAMILY = ("opencv-python", "opencv-python-headless",
                 "opencv-contrib-python", "opencv-contrib-python-headless")


def _site_kind(dist_path: str) -> str:
    import site
    try:
        usr = site.getusersitepackages() or ""
    except Exception:
        usr = ""
    return "使用者層" if usr and str(dist_path).lower().startswith(usr.lower()) else "系統層"


def doctor() -> int:
    """醫生層:多層 site 同名發行版互撞診斷(唯讀;誠實;不卡斷)。"""
    from importlib.metadata import distributions
    print("  [醫生] 掃描全 sys.path 發行版(使用者層優先於系統層=遮蔽關係)…")
    seen: dict[str, list] = {}
    for dist in distributions():
        try:
            name = (dist.metadata["Name"] or "").strip().lower()
            path = str(getattr(dist, "_path", ""))
        except Exception:
            continue
        if name:
            ent = (dist.version, _site_kind(Path(path).parent))
            if ent not in seen.setdefault(name, []):  # 同層同版重複 path 去重
                seen[name].append(ent)
    cv = {n: v for n, v in seen.items() if n in OPENCV_FAMILY}
    n_cv = len(cv)
    print(f"  [cv2 ] opencv 家族發行版 {n_cv} 個:")
    for n, insts in sorted(cv.items()):
        for ver, kind in insts:
            print(f"     · {n} {ver}({kind})")
    r = subprocess.run([sys.executable, "-c",
                        "import cv2;print(cv2.__version__);import cv2.ximgproc as x;"
                        "print('niBlackThreshold', hasattr(x,'niBlackThreshold'))"],
                       capture_output=True, text=True, timeout=120)
    live = (r.stdout or "").strip().replace("\n", " · ")
    print(f"  [活體] cv2 子行程探測:{'OK · ' + live if r.returncode == 0 else 'FAIL · ' + (r.stderr or '').strip().splitlines()[-1][:90] if (r.stderr or '').strip() else 'FAIL'}")
    shadows = {n: v for n, v in seen.items() if len(v) > 1}
    if shadows:
        print(f"  [影蔽] 同名多層 {len(shadows)} 件(使用者層蓋系統層;版本歧異候整併):")
        for n, insts in sorted(shadows.items())[:10]:
            print("     · " + n + ":" + " / ".join(f"{v}({k})" for v, k in insts))
    user_cv = sorted({n for n, insts in cv.items() for _v, k in insts if k == "使用者層"})
    sys_cv = sorted({n for n, insts in cv.items() for _v, k in insts if k == "系統層"})
    verdict = "GREEN"
    if n_cv == 0 and r.returncode != 0:
        verdict = "YELLOW_ABSENT"
        print("  [修法] cv2 未裝(非互撞)——擇需:via-install opencv-contrib-python")
    elif len(user_cv) > 1 or r.returncode != 0:
        verdict = "RED_COLLISION" if len(user_cv) > 1 else "RED_IMPORT"
        print("  [修法] 免管理員(使用者層優先,遮蔽即勝——毋須提權):")
        print("     ① py -m pip uninstall -y opencv-python-headless opencv-contrib-python-headless opencv-contrib-python")
        print("        (只清使用者層;系統層 opencv-python 拒刪屬預期,遮蔽即可)")
        print("     ② via-install opencv-contrib-python(統包 full:含 ximgproc;paddlex/img2table 相依鏈錨定版,pip 不再回拉)")
        print("     ③ via-install --doctor 複診應轉 GREEN")
        print("     (根除系統層須管理員 PowerShell:py -m pip uninstall -y opencv-python——擇需)")
    elif len(user_cv) == 1 and sys_cv:
        verdict = "GREEN_SHADOWED"
        print(f"  [判讀] 使用者層單件({user_cv[0]})已遮蔽系統層({'/'.join(sys_cv)})——遮蔽即勝,非病;根除擇需提權")
    print(f"  [裁決] {verdict}(誠實;唯讀零安裝)")
    return 0 if verdict == "GREEN" else 1


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    check_only = "--check-only" in sys.argv
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    if "--doctor" in sys.argv:
        print("=== 安裝治理閘 v0103 · 環境醫生(唯讀)===")
        return doctor()
    print(f"=== 安裝治理閘 v0103 · {'CHECK-ONLY' if check_only else '安裝 ' + ' '.join(args) if args else '?'} ===")
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
        # v0104(操作員令:透過輔助性模組來安裝):SuperAccel 加速道在則委派
        # (同意閘+重試退避),缺則原生 pip 直跑(graceful 零行為降級)
        rc = None
        tail = []
        try:
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            import VIA_SuperAccel_Module as _accel
            rc, tl = _accel.pip_install(list(args))
            tail = tl.splitlines()
            print(f"  [安裝] SuperAccel 委派 · exit {rc} · {tail[-1][:100] if tail else ''}")
        except ImportError:
            pass
        if rc is None:
            r = subprocess.run([sys.executable, "-m", "pip", "install", "--user", *args],
                               capture_output=True, text=True, timeout=1800)
            rc = r.returncode
            tail = (r.stdout + r.stderr).strip().splitlines()
            print(f"  [安裝] exit {rc} · {tail[-1][:110] if tail else ''}")
        class _R:  # 統一後續判讀介面
            returncode = rc
        r = _R()
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
        "support_smoke": smoke, "provenance": "via_install_gate_v0103(儲存規定令)",
    })
    LIBREG.write_text(json.dumps(reg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"  [註冊] {LIBREG.name} · 第 {len(reg['ledger'])} 筆(append-only)")
    return 0 if not new_conf else 1


if __name__ == "__main__":
    sys.exit(main())
