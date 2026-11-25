#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VIA_GovernanceApply v0103 — 薄尾(v0100–v0102 一字不動):三個初始獨立流程同步跑

操作員 2026-11-25:「出新版 更快 三個初始獨立流程同步跑」。
v0102 實測(容器,冷跑):計畫 19.4s(覆蓋矩陣 17.9s)→ 車道 → 驗證(ReworkGuard 67.2s ∥ 編號稽核 12.8s ∥ …)= 牆鐘 86.8s;
ReworkGuard 要等計畫跑完才開始。本版一開跑就同時起三個互不相干的流程:
  ① 計畫(覆蓋矩陣 CGC_MDL230 + 五條車道的計畫)—— 主執行緒
  ② ReworkGuard check
  ③ 編號稽核 CGC_MDL237 audit
②③ 用開跑當下的 git 狀態當鍵;驗證時鍵沒變(車道沒寫任何檔)就直接取②③的結果,還在跑就等它(不重開第二份);
鍵變了(車道寫了檔)才在驗證時重跑。預期冷跑牆鐘 ≈ max(①+車道, ②) 而不是 ① + ②。
其餘照 v0102(快取 · --fresh · 並行驗證 · 計時)。
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

import importlib.util
import re
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VIA_GovernanceApply"
TAG = "VIA_GovernanceApply v0103"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0103", PRIOR_PATH)
V2 = importlib.util.module_from_spec(_spec)                # v0102(V2.G = v0101 · V2.P = v0100)
sys.modules[_spec.name] = V2
_spec.loader.exec_module(V2)
G, P = V2.G, V2.P


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(V2, name)


INFLIGHT: dict = {}                 # (快取名, 鍵) → Future:同一份工作只跑一次,後到的等它
_ILOCK = threading.Lock()
_POOL = ThreadPoolExecutor(max_workers=3, thread_name_prefix="gov_init")
_ORIG_CACHED = V2.cached


def cached(via: Path, name: str, key: str, fn):
    with _ILOCK:
        fut = INFLIGHT.get((name, key))
    if fut is not None:                       # 本輪背景起跑的(含 --fresh)就是新結果:等它,不重開;不算「沿用」
        return fut.result(), False
    return _ORIG_CACHED(via, name, key, fn)


V2.cached = cached


def job_rg(via: Path) -> str:
    rg = sorted((via / "docs" / "handoff" / "ai").glob("VIA_ReworkGuard_v*.py"), key=_vnum)
    if not rg:
        return "—"
    r = G.run([sys.executable, str(rg[-1]), "check"], via, 900)
    return next((ln for ln in r.stdout.splitlines() if "check" in ln and "·" in ln), f"rc {r.returncode}")[:200]


def job_audit(via: Path) -> str:
    con = P.registry_tail(via, "CGC_MDL149_VeritasCentralGovernanceConsole")
    if not con:
        return "—"
    r = G.run([sys.executable, str(con), "run", "CGC_MDL237_NumberingSystem", "audit"], via, 900, {"VIA_FROM_VCGC": "YES"})
    return " | ".join(ln.strip() for ln in r.stdout.splitlines() if re.search(r"遺失|改身分|重號|XCODE|DUPREG", ln))[:300] or f"rc {r.returncode}"


def start_initial(via: Path) -> list[str]:
    """②③ 在背景起跑;鍵 = 開跑當下的 git 狀態(與 v0102 verify 用的同一把鍵)。"""
    key = V2.state_key(via, "verify")
    started = []
    for name, label, fn in (("reworkguard", "ReworkGuard check", job_rg), ("audit", "編號稽核 CGC_MDL237", job_audit)):
        if V2.FRESH is False:
            hit = _peek(via, name, key)
            if hit:
                continue                       # 上一輪同狀態已有結果:v0102 的快取會直接沿用,不必起跑
        fut = _POOL.submit(lambda f=fn, n=name, lb=label: _ORIG_CACHED_FORCE(via, n, key, lambda: V2.timed(lb, lambda: f(via))))
        with _ILOCK:
            INFLIGHT[(name, key)] = fut
        started.append(label)
    return started


def _peek(via: Path, name: str, key: str) -> bool:
    import json
    try:
        c = json.loads(V2._cache_path(via).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return (c.get(name) or {}).get("key") == key


def store(via: Path, name: str, key: str, val) -> None:
    """直接寫快取一格(不碰全域 FRESH:v0102 的 cached_force 靠切 FRESH,並行時會讓別的執行緒誤以為要重跑)。"""
    import json
    cp = V2._cache_path(via)
    with V2._CLOCK:
        try:
            c = json.loads(cp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            c = {}
        c[name] = {"key": key, "value": val, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        cp.parent.mkdir(parents=True, exist_ok=True)
        P.atomic_write_text(cp, json.dumps(c, ensure_ascii=False, indent=1) + "\n")


def _ORIG_CACHED_FORCE(via: Path, name: str, key: str, fn):
    """背景流程一定實跑並寫進快取(不被自己的 INFLIGHT 擋住、不切全域旗標)。"""
    val = fn()
    store(via, name, key, val)
    return val


V2.cached_force = store


_ORIG_BUILD_PLAN = P.build_plan


def build_plan(via: Path, lanes: tuple, fresh_cov: bool = True) -> dict:
    return V2.timed("① 計畫(含覆蓋矩陣)", lambda: _ORIG_BUILD_PLAN(via, lanes, fresh_cov))


P.build_plan = build_plan
P.TAG = TAG


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 3 項 + 前版自測 · 暫存夾 · 零網路)", flush=True)
    rc = V2.selftest()
    chk("T1 前版(v0102 → v0100)自測照過", rc == 0, rc)
    with tempfile.TemporaryDirectory(prefix="gov103_") as td:
        via = Path(td)
        subprocess.run(["git", "init", "-q", str(via)], check=True)
        subprocess.run(["git", "-C", str(via), "-c", "user.email=fx@fx", "-c", "user.name=fx", "commit", "-q", "--allow-empty", "-m", "fx"], check=True)
        n = {"c": 0}

        def slow():
            time.sleep(1.0)
            n["c"] += 1
            return n["c"]
        key = V2.state_key(via, "verify")
        t0 = time.time()
        futs = [_POOL.submit(lambda nm=nm: _ORIG_CACHED_FORCE(via, nm, key, slow)) for nm in ("a", "b")]
        with _ILOCK:
            INFLIGHT[("a", key)] = futs[0]
            INFLIGHT[("b", key)] = futs[1]
        time.sleep(1.0)                                   # ①(主執行緒)同時在做自己的事
        va, ha = cached(via, "a", key, slow)              # 驗證時:還在跑就等它,不重開
        vb, hb = cached(via, "b", key, slow)
        dt = time.time() - t0
        chk("T2 三流程同步:① 1 秒 ∥ ② 1 秒 ∥ ③ 1 秒 → 牆鐘 < 2 秒", dt < 2.0, round(dt, 2))
        chk("T3 驗證取背景結果、不重跑(工作只跑 2 次 = ② ③ 各一次;不標沿用)", not ha and not hb and n["c"] == 2 and {va, vb} == {1, 2}, (va, vb, n["c"]))
        (via / "new.py").write_text("x = 1\n", encoding="utf-8")
        with _ILOCK:
            INFLIGHT.clear()
        vc, hc = cached(via, "a", V2.state_key(via, "verify"), slow)
        chk("T4 車道寫了檔(鍵變)→ 驗證重跑,不拿舊結果", (not hc) and n["c"] == 3, (vc, hc, n["c"]))
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("selftest", "--selftest"):
        return selftest()
    if args and args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return V2.main(args)
    if "--fresh" in args:
        V2.FRESH = True
        args = [a for a in args if a != "--fresh"]
    V2._T0["t"] = time.time()
    if args and args[0] in ("apply", "verify"):
        via = P.find_via()
        started = start_initial(via)
        print(f"[{TAG}] 三個初始流程同步起跑:① 計畫(覆蓋矩陣)" + "".join(f" ∥ {s}" for s in started)
              + ("" if len(started) == 2 else "(其餘沿用上一輪同狀態的結果)"), flush=True)
    try:
        return P.main(args)
    finally:
        _POOL.shutdown(wait=True)


if __name__ == "__main__":
    raise SystemExit(main())
