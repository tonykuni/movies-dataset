#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
SUP_MDL737_SuperAccelModule_v0103 — 統一加速器 · 全模組整合版(批125;批323 啟動律)
======================================================================
批323 操作員令「確認所有 engines/modules 都導入加速器;加速器一百多個 libs 都有啟動功能」
實查:celeritas() 以 spec_from_file_location 載入卻未登記 sys.modules→Python 3.11+ dataclass
查 sys.modules[cls.__module__] 得 None→AttributeError→graceful 回 None=Celeritas 88 lib
lazy 啟動面自始未經橋接通(誠實:橋在、啟動未通)。v0103:①登記 sys.modules 後 exec+快取
②activate():載 Celeritas→apply_vrn_vds_max_accel(執行緒預算)→回 libs 總/可用/缺/真實能力
③--activate 印報告+落 VIA_Reports/accel_activation/;--libs 逐 lib OK/MISSING/STUB 表
④selftest ⑦⑧:Celeritas 在位=必非 None;activate 冊 ≥80 lib。
======================================================================
批125 操作員令(2026-08-24):「所有加速模組整合為一」。
  ① 整合總冊 — VIA_AccelModules_Integration_Register(glob 最新版):
     全樹加速件清點(CANONICAL/SHIM/DELEGATED_RUNTIME/PS_LANE/
     LEGACY/WAITING_DELIVERY);--modules 檢閱。
  ② celeritas() — VeritasCeleritas 執行期委派載入(動態最新;缺=
     誠實 None);fetch 車道原生委派鏈不變。
  ③ PS 側正門=Invoke-VeritasCodexNexus 最新版(FM-01..20 備援冊)。
原 v0100(操作員令 2026-08-18)
======================================================================
令:「透過輔助性模組來安裝」。史因:十餘支 VRN OCR/VDF MDL 引擎自始
引用本模組(`_via_load("VIA_SuperAccel_Module")`,註記「工作站候上傳;
graceful」)但正件從未交付——WARN 至今。本件補齊斷點:
  ① accel_map(fn, items)   平行加速 map(執行緒池;例外隔離不斷鏈)
  ② fetch(url)             加速抓取——同意閘先行(VIA_NET_CONSENT;
     永不代設)→ VeritasCeleritas vdf_fetch(快取/重試/去重)在則委派,
     缺則標準庫重試退避道;本地磁碟快取
  ③ pip_install(pkgs)      透過輔助模組安裝——同意閘先行→pip --user
     重試退避+誠實 rc/log;供 via-install 鏈委派
  ④ run_fast(argv)         子行程標準道(DEVNULL stdin+逾時+尾流)
紅線:同意閘永不代設;網路零觸碰預設;快取落 VIA_Reports(不落 OneDrive)。
graceful:單獨可跑、零硬依賴;Celeritas/NetSupport 缺席誠實降級。
用法:via-accel --selftest   → 離線六檢
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
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
VIA = HERE.parent
CACHE = VIA / "VIA_Reports" / "accel_cache"
_STATS = {"map_calls": 0, "cache_hit": 0, "cache_miss": 0, "fetch": 0, "pip": 0}


def _consent() -> bool:
    """同意閘:委派 VIA_NetSupport;缺則直讀環境變數(永不代設)。"""
    try:
        sys.path.insert(0, str(HERE))
        import VIA_NetSupport as net
        return bool(net.net_consent())
    except Exception:
        import os
        return os.environ.get("VIA_NET_CONSENT", "").upper() in ("YES", "1", "TRUE")


def accel_map(fn, items, workers: int | None = None):
    """平行 map:回 [(ok, result_or_err)] 保序;單件退化序跑;例外隔離。"""
    _STATS["map_calls"] += 1
    items = list(items)
    if len(items) <= 1:
        out = []
        for it in items:
            try:
                out.append((True, fn(it)))
            except Exception as exc:
                out.append((False, f"{type(exc).__name__}: {str(exc)[:80]}"))
        return out
    w = workers or min(8, len(items))

    def safe(it):
        try:
            return (True, fn(it))
        except Exception as exc:
            return (False, f"{type(exc).__name__}: {str(exc)[:80]}")
    with ThreadPoolExecutor(max_workers=w) as ex:
        return list(ex.map(safe, items))


def fetch(url: str, retries: int = 3, backoff: float = 2.0, timeout: int = 30,
          cache: bool = True) -> str | None:
    """加速抓取:同意閘→快取→Celeritas 委派→標準庫重試退避。誠實 None。"""
    _STATS["fetch"] += 1
    if not _consent():
        print("  [SuperAccel] 同意閘未開——$env:VIA_NET_CONSENT='YES' 後重試(紅線:不代設)")
        return None
    key = hashlib.sha1(url.encode()).hexdigest()
    cf = CACHE / f"{key}.body"
    if cache and cf.exists():
        _STATS["cache_hit"] += 1
        return cf.read_text(encoding="utf-8", errors="replace")
    _STATS["cache_miss"] += 1
    body = None
    try:  # Celeritas 加速道(快取/重試/去重)在則委派
        sys.path.insert(0, str(HERE))
        import VeritasCeleritas as vc
        if hasattr(vc, "vdf_fetch"):
            r = vc.vdf_fetch(url, timeout=timeout)
            body = getattr(r, "text", None) or (r if isinstance(r, str) else None)
    except Exception:
        body = None
    if body is None:  # 標準庫重試退避道
        import urllib.request
        for i in range(retries):
            try:
                with urllib.request.urlopen(url, timeout=timeout) as resp:
                    body = resp.read().decode("utf-8", errors="replace")
                break
            except Exception as exc:
                if i == retries - 1:
                    print(f"  [SuperAccel] 抓取敗({type(exc).__name__})——誠實 None")
                    return None
                time.sleep(backoff * (2 ** i))
    if body is not None and cache:
        CACHE.mkdir(parents=True, exist_ok=True)
        cf.write_text(body, encoding="utf-8")
    return body


def pip_install(pkgs: list[str] | str, retries: int = 3, backoff: float = 2.0,
                user: bool = True) -> tuple[int, str]:
    """透過輔助模組安裝:同意閘→pip 重試退避。回 (rc, 尾流)。"""
    _STATS["pip"] += 1
    if isinstance(pkgs, str):
        pkgs = [pkgs]
    if not _consent():
        return 1, "同意閘未開——安裝需 $env:VIA_NET_CONSENT='YES'(紅線:不代設)"
    argv = [sys.executable, "-m", "pip", "install"] + (["--user"] if user else []) + list(pkgs)
    tail = ""
    for i in range(retries):
        r = subprocess.run(argv, capture_output=True, text=True, stdin=subprocess.DEVNULL)
        tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-3:])
        if r.returncode == 0:
            return 0, tail
        if i < retries - 1:
            time.sleep(backoff * (2 ** i))
    return r.returncode, tail


def run_fast(argv: list[str], timeout: int = 300) -> tuple[int | str, str]:
    """子行程標準道:DEVNULL stdin+逾時;回 (rc, 尾流)。"""
    try:
        r = subprocess.run(argv, capture_output=True, text=True, timeout=timeout,
                           stdin=subprocess.DEVNULL)
        return r.returncode, "\n".join((r.stdout + r.stderr).strip().splitlines()[-3:])
    except subprocess.TimeoutExpired:
        return "TIMEOUT", f"逾時 {timeout}s(誠實)"


_CEL = {"mod": None, "tried": False, "err": ""}
CEL_CANDIDATES = ("VeritasCeleritas.py", "50_Protection_Acceleration/VeritasCeleritas.py",
                  "accelerator/VeritasCeleritas.py")


def celeritas():
    """VeritasCeleritas 執行期委派載入(缺=誠實 None)。
    批323:登記 sys.modules 後 exec(dataclass 於 3.11+ 必查 sys.modules[__module__]);快取單載。"""
    if _CEL["tried"]:
        return _CEL["mod"]
    _CEL["tried"] = True
    import importlib.util
    for rel in CEL_CANDIDATES:
        cand = VIA / "supportive modules" / rel
        if not cand.exists():
            continue
        name = "VeritasCeleritas_dyn"
        try:
            spec = importlib.util.spec_from_file_location(name, cand)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            _CEL["mod"] = mod
            return mod
        except Exception as exc:
            sys.modules.pop(name, None)
            _CEL["err"] = f"{cand.name}: {type(exc).__name__}: {str(exc)[:120]}"
            continue
    return None


def activate(apply_limits: bool = True) -> dict:
    """批323 啟動律:載 Celeritas→執行緒預算套用→回 lib 冊狀態(誠實;缺=全零+err)"""
    cel = celeritas()
    out = {"celeritas": cel is not None, "err": _CEL["err"], "libs_total": 0,
           "libs_available": 0, "missing": [], "capability_real": 0, "capability_total": 0,
           "thread_budget": None, "mode": None, "applied": {}}
    if cel is None:
        return out
    try:
        libs = cel.get_available_libs()
        out["libs_total"] = len(libs)
        out["libs_available"] = sum(1 for v in libs.values() if v)
        out["missing"] = cel.get_missing_libs()
    except Exception as exc:
        out["err"] = f"libs: {type(exc).__name__}: {str(exc)[:100]}"
    try:
        cr = cel.capability_report()
        out["capability_total"] = len(cr)
        out["capability_real"] = sum(1 for v in cr.values() if v)
    except Exception:
        pass
    try:
        out["thread_budget"] = int(cel.thread_budget())
        out["mode"] = str(cel._resolve_mode())
    except Exception:
        pass
    if apply_limits:
        try:
            r = cel.apply_vrn_vds_max_accel()
            out["applied"] = {k: str(v) for k, v in (r or {}).items()}
        except Exception as exc:
            out["applied"] = {"err": f"{type(exc).__name__}: {str(exc)[:100]}"}
    return out


def cmd_activate() -> int:
    a = activate()
    print(f"=== 加速器啟動報告(SUP_MDL737 v0103)===")
    print(f"  Celeritas 載入:{'OK' if a['celeritas'] else 'FAIL'} {a['err']}")
    print(f"  lib 冊:{a['libs_total']} · 可用 {a['libs_available']} · 缺 {len(a['missing'])}"
          f" · 真實能力 {a['capability_real']}/{a['capability_total']}"
          f" · 執行緒預算 {a['thread_budget']}({a['mode']})")
    if a["missing"]:
        print(f"  缺(lazy stub 代位,誠實非真加速):{', '.join(a['missing'][:30])}"
              + (" …" if len(a["missing"]) > 30 else ""))
    if a["applied"]:
        print(f"  已套用:{a['applied']}")
    d = VIA / "VIA_Reports" / "accel_activation"
    d.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    (d / f"ACCEL_ACTIVATION_{stamp}.json").write_text(json.dumps(a, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"  存證:{d / f'ACCEL_ACTIVATION_{stamp}.json'}")
    return 0 if a["celeritas"] else 1


def cmd_libs() -> int:
    cel = celeritas()
    if cel is None:
        print(f"  [FAIL] Celeritas 載入失敗:{_CEL['err']}")
        return 1
    libs = cel.get_available_libs()
    try:
        cr = cel.capability_report()
    except Exception:
        cr = {}
    print(f"=== Celeritas lib 冊 {len(libs)} 件(OK=已裝真實 · MISSING=缺,lazy stub 代位)===")
    for k, v in libs.items():
        flag = "OK     " if v else "MISSING"
        if v and k in cr and not cr[k]:
            flag = "STUB   "
        print(f"  [{flag}] {k}")
    return 0


def load_accel_register():
    hits = sorted((VIA / "supportive modules" / "registry")
                  .glob("VIA_AccelModules_Integration_Register_v*.json"))
    return json.loads(hits[-1].read_text(encoding="utf-8")) if hits else None


def cmd_modules() -> int:
    reg = load_accel_register()
    if reg is None:
        print("  [FAIL] 加速整合總冊缺")
        return 1
    print(f"=== 加速模組整合總冊({reg['ts']})· {reg['counts']['total']} 件 ===")
    for w in reg.get("waiting_delivery", []):
        print(f"  [候件] {w['name']}:{w['note'][:70]}")
    return 0


def stats() -> dict:
    return dict(_STATS)


def selftest() -> int:
    print("=== SuperAccel SUP_MDL737 v0103 · 離線八檢 ===")
    import os
    checks = []
    # ① 平行 map 保序+例外隔離
    r = accel_map(lambda x: x * 2 if x != 3 else 1 // 0, [1, 2, 3, 4])
    checks.append(("accel_map 保序+例外隔離", [x[0] for x in r] == [True, True, False, True]
                   and r[1][1] == 4 and "ZeroDivisionError" in r[2][1]))
    # ② 同意閘預設關(fetch/pip 皆拒)
    old = os.environ.pop("VIA_NET_CONSENT", None)
    checks.append(("同意閘預設關(fetch 拒)", fetch("http://example.invalid/x", cache=False) is None))
    rc, msg = pip_install("nonexistent-pkg-zzz")
    checks.append(("同意閘預設關(pip 拒)", rc == 1 and "同意閘" in msg))
    if old:
        os.environ["VIA_NET_CONSENT"] = old
    # ③ 快取往返(不經網路)
    CACHE.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha1(b"http://t.local/a").hexdigest()
    (CACHE / f"{key}.body").write_text("CACHED_BODY", encoding="utf-8")
    os.environ["VIA_NET_CONSENT"] = "YES"
    got = fetch("http://t.local/a")
    if old is None:
        os.environ.pop("VIA_NET_CONSENT", None)
    else:
        os.environ["VIA_NET_CONSENT"] = old
    checks.append(("快取往返零網路", got == "CACHED_BODY"))
    # ⑤ 批125 整合總冊+⑥ celeritas graceful
    reg5 = load_accel_register()
    checks.append(("加速整合總冊在位", reg5 is not None and reg5["counts"]["total"] >= 10))
    cel = celeritas()
    checks.append(("celeritas 委派 graceful", cel is None or hasattr(cel, "__file__")))
    # ⑦⑧ 批323 啟動律:本體在位=必載通;activate 冊 ≥80 lib(缺=誠實列)
    present = any((VIA / "supportive modules" / r).exists() for r in CEL_CANDIDATES)
    checks.append(("Celeritas 在位即載通(sys.modules 登記律)", (not present) or (cel is not None)))
    a = activate(apply_limits=False)
    checks.append(("activate 冊 ≥80 lib+缺件誠實列", (not present) or
                   (a["libs_total"] >= 80 and a["libs_available"] + len(a["missing"]) == a["libs_total"])))
    n = 0
    for name, ok in checks:
        n += ok
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    print(f"  [計] {n}/{len(checks)} 檢通過 · stats={stats()}")
    return 0 if n == len(checks) else 1


if __name__ == "__main__":
    _a = sys.argv[1:]
    if "--modules" in _a:
        sys.exit(cmd_modules())
    if "--activate" in _a:
        sys.exit(cmd_activate())
    if "--libs" in _a:
        sys.exit(cmd_libs())
    sys.exit(selftest())
