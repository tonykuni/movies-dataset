#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VIA_GovernanceApply v0102 — 薄尾(v0100 / v0101 一字不動):提速

操作員 2026-11-25:「速度太慢」。先量(容器,v0101 逐步計時):
  ReworkGuard check 82.2s(最慢)· 覆蓋矩陣 CGC_MDL230 47.4s × 2(計畫一次、驗證一次)· 編號稽核 15.6s ·
  參數值比對 7 家 14.4s(逐家依序)· 退役計畫 5.4s —— 全部依序 ≈ 215s。
本版:
  ① 驗證四項(覆蓋矩陣 · ReworkGuard · 編號稽核 · 參數值比對)同時跑(4 道;CLAUDE.md「3~6 道」),牆鐘 ≈ 最慢那一支。
  ② 結果快取:鍵 = git HEAD + 工作樹狀態(git status,VIA_Reports 產物不算)+ 工具版本;沒變就沿用上一輪的結果(標「沿用」),
     `--fresh` 全部重跑。快取在 VIA_Reports/vcgc_gov/GOV_CACHE.json(本機產物,不入版控)。
  ③ 覆蓋矩陣:這一輪車道沒寫任何檔 → 驗證直接用計畫時那份(不重跑)。
  ④ 參數值比對 7 家並行(import only;不執行 main)。
  ⑤ 報告加 [計時]:每一步秒數 + 牆鐘總秒 + 最慢那一步。
其餘一切照 v0101(函式改寫打在 v0100 模組的全域上)。
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
import importlib.util
import json
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
TAG = "VIA_GovernanceApply v0102"
LANES_PAR = 4


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0102", PRIOR_PATH)
G = importlib.util.module_from_spec(_spec)                 # v0101(它裡面的 P = v0100 模組)
sys.modules[_spec.name] = G
_spec.loader.exec_module(G)
P = G.P


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(G, name)


FRESH = False
TIMES: dict = {}
_TLOCK = threading.Lock()
_CLOCK = threading.Lock()


def timed(name: str, fn):
    t0 = time.time()
    try:
        return fn()
    finally:
        with _TLOCK:
            TIMES[name] = round(TIMES.get(name, 0) + time.time() - t0, 1)


def state_key(via: Path, salt: str = "") -> str:
    """git HEAD + 工作樹狀態(VIA_Reports 產物不算)+ 工具版本。"""
    head = subprocess.run(["git", "-C", str(via), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    st = subprocess.run(["git", "-C", str(via), "status", "--porcelain"], capture_output=True, text=True, encoding="utf-8",
                        errors="replace").stdout
    st = "\n".join(ln for ln in st.splitlines() if "VIA_Reports/" not in ln)
    return hashlib.sha256(f"{TAG}|{salt}|{head}|{st}".encode("utf-8")).hexdigest()[:20]


def _cache_path(via: Path) -> Path:
    return via / "VIA_Reports" / "vcgc_gov" / "GOV_CACHE.json"


def cached(via: Path, name: str, key: str, fn):
    """回 (值, 是否沿用)。"""
    cp = _cache_path(via)
    if not FRESH:
        with _CLOCK:
            try:
                c = json.loads(cp.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                c = {}
        ent = c.get(name)
        if ent and ent.get("key") == key:
            return ent["value"], True
    val = fn()
    with _CLOCK:
        try:
            c = json.loads(cp.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            c = {}
        c[name] = {"key": key, "value": val, "at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
        cp.parent.mkdir(parents=True, exist_ok=True)
        P.atomic_write_text(cp, json.dumps(c, ensure_ascii=False, indent=1) + "\n")
    return val, False


_COV_KEY = {"key": None}
_ORIG_COVERAGE = P.coverage


def coverage(via: Path, fresh: bool = True) -> dict:
    """同一工作樹狀態只跑一次 CGC_MDL230;狀態沒變就讀它上次寫的 COVERAGE_MATRIX_latest.json。"""
    key = state_key(via, "coverage")
    if fresh and not FRESH and _COV_KEY["key"] == key:
        return _ORIG_COVERAGE(via, False)
    if fresh and not FRESH:
        _v, reused = cached(via, "coverage", key, lambda: "ran")
        if reused:
            _COV_KEY["key"] = key
            out = _ORIG_COVERAGE(via, False)
            if out.get("totals"):
                return out
    out = timed("覆蓋矩陣 CGC_MDL230", lambda: _ORIG_COVERAGE(via, fresh))
    if fresh:
        _COV_KEY["key"] = key
        cached_force(via, "coverage", key, "ran")
    return out


def cached_force(via: Path, name: str, key: str, val):
    global FRESH
    old, FRESH = FRESH, True
    try:
        cached(via, name, key, lambda: val)
    finally:
        FRESH = old


def _one_param(t: Path, ep: dict) -> tuple[str, str]:
    fam = P.family_of(t)
    pr = G.prior_of(t)
    names = [k for k, v in (ep.get(fam) or {}).items() if "via_root_rel" not in v]
    if pr is None or not names:
        return t.name, "冊上沒有這家的條目或找不到前版"
    r = G.run([sys.executable, "-c", P._compare_script(), str(pr), str(t), json.dumps(names)], t.parent, 180)
    try:
        res = json.loads((r.stdout.strip().splitlines() or ["{}"])[-1])
    except ValueError:
        res = {"import": f"rc {r.returncode}"}
    if res.get("import"):
        return t.name, "容器載不起來(新舊同因時只驗到 ast+compile):" + res["import"][:70]
    same = res.get("same") or {}
    bad = [k for k, v in same.items() if not v]
    return t.name, (f"值與前版相同 {len(same)}/{len(same)}" if not bad else f"值不同 {bad}")


def param_check(via: Path) -> dict:
    book = P.params_book(via)
    ep = (json.loads(book.read_text(encoding="utf-8")).get("engine_params") or {}) if book else {}
    done = G.param_done(via)
    with ThreadPoolExecutor(max_workers=max(1, min(LANES_PAR, len(done) or 1))) as ex:
        return dict(ex.map(lambda t: _one_param(t, ep), done))


def verify(via: Path, new_files: list[str]) -> dict:
    ex = {}
    st = []
    for f in new_files:
        p = via / f
        if p.suffix != ".py" or not p.exists():
            continue
        if not G.has_selftest(p):
            st.append(f"{p.name} 略過(檔內沒有 --selftest;不執行 main)")
            continue
        r = timed("新版自測", lambda: G.run([sys.executable, str(p), "--selftest"], p.parent, 600))
        st.append(f"{p.name} rc {r.returncode}")
    ex["新版自測"] = " · ".join(st) or "—"
    key = state_key(via, "verify")
    reused = []

    def job_cov():
        cov = coverage(via, True)
        return {k: f"{v.get('have', '?')}/{v.get('n', v.get('total', '?'))} miss {len(v.get('miss') or [])}"
                for k, v in (cov.get("totals") or {}).items()}

    def job_rg():
        rg = sorted((via / "docs" / "handoff" / "ai").glob("VIA_ReworkGuard_v*.py"), key=_vnum)
        if not rg:
            return "—"
        r = G.run([sys.executable, str(rg[-1]), "check"], via, 900)
        return next((ln for ln in r.stdout.splitlines() if "check" in ln and "·" in ln), f"rc {r.returncode}")[:200]

    def job_audit():
        con = P.registry_tail(via, "CGC_MDL149_VeritasCentralGovernanceConsole")
        if not con:
            return "—"
        r = G.run([sys.executable, str(con), "run", "CGC_MDL237_NumberingSystem", "audit"], via, 900, {"VIA_FROM_VCGC": "YES"})
        return " | ".join(ln.strip() for ln in r.stdout.splitlines() if re.search(r"遺失|改身分|重號|XCODE|DUPREG", ln))[:300] or f"rc {r.returncode}"

    def wrap(label, cache_name, fn):
        def go():
            if cache_name:
                val, hit = cached(via, cache_name, key, lambda: timed(label, fn))
                if hit:
                    reused.append(label)
                return val
            return timed(label, fn)
        return go

    jobs = [("覆蓋矩陣", wrap("覆蓋矩陣 CGC_MDL230", None, job_cov)),
            ("ReworkGuard", wrap("ReworkGuard check", "reworkguard", job_rg)),
            ("編號稽核", wrap("編號稽核 CGC_MDL237", "audit", job_audit)),
            ("參數值比對", wrap("參數值比對", "param_check", lambda: param_check(via)))]
    with P.Heartbeat(f"驗證 {len(jobs)} 項並行({LANES_PAR} 道)"):
        with ThreadPoolExecutor(max_workers=LANES_PAR) as pool:
            futs = {name: pool.submit(fn) for name, fn in jobs}
            for name, fu in futs.items():
                try:
                    ex[name] = fu.result()
                except Exception as exc:          # noqa: BLE001
                    ex[name] = f"{type(exc).__name__}: {str(exc)[:120]}"
    if reused:
        ex["沿用快取"] = "、".join(reused) + "(git HEAD 與工作樹沒變;要重跑加 --fresh)"
    return ex


_ORIG_CMD_APPLY = P.cmd_apply
_ORIG_REPORT = P.report


def report(via: Path, plan: dict, results, extra=None) -> dict:
    extra = dict(extra or {})
    if TIMES:
        slow = max(TIMES.items(), key=lambda kv: kv[1])
        extra["計時"] = " · ".join(f"{k} {v}s" for k, v in TIMES.items()) + \
            f" · 牆鐘 {round(time.time() - _T0['t'], 1)}s · 最慢:{slow[0]} {slow[1]}s"
    return _ORIG_REPORT(via, plan, results, extra)


_T0 = {"t": time.time()}
_ORIG_PLAN_RETIRE = P.plan_retire


def plan_retire(via: Path, systems: tuple = ("VDF",)) -> dict:
    return timed("退役計畫", lambda: _ORIG_PLAN_RETIRE(via, systems))


for _n, _f in (("coverage", coverage), ("verify", verify), ("report", report), ("plan_retire", plan_retire)):
    setattr(P, _n, _f)
G.verify = verify
G.param_check = param_check
P.TAG = TAG


def selftest() -> int:
    global FRESH
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版自測 · 暫存夾 · 零網路)", flush=True)
    rc = G.selftest()
    chk("T1 前版(v0101 + v0100)自測照過", rc == 0, rc)
    with tempfile.TemporaryDirectory(prefix="gov102_") as td:
        via = Path(td)
        subprocess.run(["git", "init", "-q", str(via)], check=True)
        subprocess.run(["git", "-C", str(via), "-c", "user.email=fx@fx", "-c", "user.name=fx", "commit", "-q", "--allow-empty", "-m", "fx"], check=True)
        n = {"c": 0}

        def fn():
            n["c"] += 1
            return n["c"]
        k1 = state_key(via, "t")
        a, h1 = cached(via, "fx", k1, fn)
        b, h2 = cached(via, "fx", state_key(via, "t"), fn)
        (via / "VIA_Reports").mkdir(exist_ok=True)
        (via / "VIA_Reports" / "x.txt").write_text("r", encoding="utf-8")
        c, h3 = cached(via, "fx", state_key(via, "t"), fn)
        (via / "new.py").write_text("x = 1\n", encoding="utf-8")
        d, h4 = cached(via, "fx", state_key(via, "t"), fn)
        chk("T2 快取:同狀態沿用;VIA_Reports 產物不算變;工作樹一變就重算", (a, h1, b, h2, c, h3, d, h4) == (1, False, 1, True, 1, True, 2, False),
            (a, h1, b, h2, c, h3, d, h4))
        FRESH = True
        e, h5 = cached(via, "fx", state_key(via, "t"), fn)
        FRESH = False
        chk("T3 --fresh 一律重跑", (e, h5) == (3, False), (e, h5))
    t0 = time.time()
    with ThreadPoolExecutor(max_workers=LANES_PAR) as pool:
        list(pool.map(lambda _i: G.run([sys.executable, "-c", "import time;time.sleep(1)"], Path(tempfile.gettempdir()), 30), range(4)))
    dt = time.time() - t0
    chk("T4 並行:4 支各 1 秒的子行程,牆鐘 < 2.5 秒", dt < 2.5, round(dt, 2))
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    global FRESH
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("selftest", "--selftest"):
        return selftest()
    if args and args[0] in ("-h", "--help", "help"):
        print(__doc__)
        return G.main(args)
    if "--fresh" in args:
        FRESH = True
        args = [a for a in args if a != "--fresh"]
    _T0["t"] = time.time()
    return P.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
