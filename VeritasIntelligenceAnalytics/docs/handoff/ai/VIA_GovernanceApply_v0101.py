#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VIA_GovernanceApply v0101 — 薄尾(v0100 一字不動):容器首跑 apply 抓到的三個洞

2026-11-25 容器首跑 `apply` 的實錄:
  ① verify 對**每個**新檔跑 `--selftest`;VDF_MDL001_TWEquityEngine 舊引擎不認 `--selftest` → 跑進它的 main:
     main 會自己 `pip install` 缺的套件(繞過 VCGC 安裝閘)、在 VIA 根下開 dict\ 寫部署報告、最後卡到 600 秒逾時。
     → 本版:只對**檔內有 `--selftest` 字樣**的檔跑自測;沒有的只做 ast + compile + 參數值比對,絕不執行它的 main。
  ② 逾時時 subprocess 回的 stdout/stderr 是 bytes,跟字串相加丟 TypeError,整個 apply 在 verify 斷掉、報告沒寫出。
     → 本版:逾時輸出一律解碼成字串。
  ③ net 車道:VDF_MDL020_DataPlane v0104 的自測在容器本來就不過(缺 duckdb),新薄尾的「前版自測照過」檢不過 → 被還原。
     → 本版:新版不過時先量前版;前版在同一台也不過(同因)而新版的雙橋檢都過 → 留下,標「OK-容器」(黃,待主機實跑)。
另補:plan 會列出前輪已解耦的家族;verify 逐家族把新版參數值跟前版比(不執行 main)。
其餘一切照 v0100(`__getattr__` 轉接;函式改寫打在 v0100 模組的全域上,v0100 內部呼叫也走新版)。
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
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VIA_GovernanceApply"
TAG = "VIA_GovernanceApply v0101"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0101", PRIOR_PATH)
P = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = P
_spec.loader.exec_module(P)


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(P, name)


def _txt(x) -> str:
    if x is None:
        return ""
    return x.decode("utf-8", "replace") if isinstance(x, (bytes, bytearray)) else str(x)


def run(cmd: list, cwd: Path, timeout: int = 900, env_extra: dict | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT"):
        env.pop(k, None)
    env.setdefault("VIA_NO_OPEN", "1")
    env.update(env_extra or {})
    try:
        return subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", errors="replace",
                              timeout=timeout, env=env)
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(cmd, 124, _txt(exc.stdout), _txt(exc.stderr) + "\n[逾時]")


def has_selftest(p: Path) -> bool:
    """只認檔內真的有 `--selftest` 字樣(AST 讀得到的字串常數);沒有 = 不准執行(避免跑進引擎 main)。"""
    try:
        import ast
        tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
    except (SyntaxError, OSError):
        return False
    return any(isinstance(n, ast.Constant) and isinstance(n.value, str) and "--selftest" in n.value for n in ast.walk(tree))


def apply_net(via: Path, plan: dict) -> list[dict]:
    out = []
    for it in plan["items"]:
        tail, new = via / it["file"], via / it["new"]
        res = {"file": it["file"], "new": it["new"]}
        if new.exists():
            out.append({**res, "state": "SKIP", "why": "新版號已存在"})
            continue
        src = P.build_thin_tail(via, tail, new)
        why = P.compiles(src, new.name)
        if why:
            out.append({**res, "state": "FAIL", "why": "TEMP 檢不過:" + why})
            continue
        P.atomic_write_text(new, src)
        r = run([sys.executable, str(new), "--selftest"], new.parent, 600)
        if r.returncode == 0:
            out.append({**res, "state": "OK", "why": next((ln for ln in r.stdout.splitlines()[::-1] if "自測" in ln), "")[:120]})
            continue
        bridges_ok = "[OK] T2" in r.stdout and "[OK] T3" in r.stdout
        base = run([sys.executable, str(tail), "--selftest"], tail.parent, 600) if has_selftest(tail) else None
        if bridges_ok and base is not None and base.returncode != 0:
            cause = next((ln.strip() for ln in (base.stdout + base.stderr).splitlines()[::-1] if "Error" in ln), f"rc {base.returncode}")
            out.append({**res, "state": "OK-容器", "why": f"雙橋檢過;前版 {tail.name} 自測在這台本來就不過({cause[:80]})→ 待主機實跑"})
        else:
            new.unlink()
            out.append({**res, "state": "FAIL", "why": f"自測 rc {r.returncode} → 已還原", "log": (r.stdout + r.stderr)[-600:]})
    return out


def param_done(via: Path) -> list[Path]:
    return [t for t in P._vdf_tails(via) if "[VIA:GOV-PARAM:v0100]" in t.read_text(encoding="utf-8", errors="replace")]


def prior_of(t: Path) -> Path | None:
    fam = P.family_of(t)
    vs = [p for p in t.parent.glob(fam + "_v*.py") if P.family_of(p) == fam and 0 <= _vnum(p) < _vnum(t)]
    if vs:
        return max(vs, key=_vnum)
    base = t.parent / (fam + ".py")
    return base if base.exists() else None


def plan_param(via: Path) -> dict:
    lane = _PRIOR_PLAN_PARAM(via)
    for t in param_done(via):
        lane["skipped"].append([P.rel(via, t), "前輪已解耦(本版參數讀 VDF 參數冊;值比對見 verify)"])
    lane["should"] = len(lane["items"]) + len(lane["skipped"])
    return lane


def param_check(via: Path) -> dict:
    """前輪與本輪解耦的新版:逐家族比 新版 vs 前版 的參數值(只 import,不執行 main;本機路徑那幾個不比)。"""
    book = P.params_book(via)
    ep = (json.loads(book.read_text(encoding="utf-8")).get("engine_params") or {}) if book else {}
    rows = {}
    for t in param_done(via):
        fam = P.family_of(t)
        pr = prior_of(t)
        names = [k for k, v in (ep.get(fam) or {}).items() if "via_root_rel" not in v]
        if pr is None or not names:
            rows[t.name] = "冊上沒有這家的條目或找不到前版"
            continue
        r = run([sys.executable, "-c", P._compare_script(), str(pr), str(t), json.dumps(names)], t.parent, 180)
        try:
            res = json.loads((r.stdout.strip().splitlines() or ["{}"])[-1])
        except ValueError:
            res = {"import": f"rc {r.returncode}"}
        if res.get("import"):
            rows[t.name] = "容器載不起來(新舊同因時只驗到 ast+compile):" + res["import"][:70]
        else:
            same = res.get("same") or {}
            bad = [k for k, v in same.items() if not v]
            rows[t.name] = (f"值與前版相同 {len(same)}/{len(same)}" if not bad else f"值不同 {bad}")
    return rows


def verify(via: Path, new_files: list[str]) -> dict:
    ex = {}
    st = []
    for f in new_files:
        p = via / f
        if p.suffix != ".py" or not p.exists():
            continue
        if not has_selftest(p):
            st.append(f"{p.name} 略過(檔內沒有 --selftest;不執行 main)")
            continue
        r = run([sys.executable, str(p), "--selftest"], p.parent, 600)
        st.append(f"{p.name} rc {r.returncode}")
    ex["新版自測"] = " · ".join(st) or "—"
    pc = param_check(via)
    ex["參數值比對"] = pc or "—"
    cov = P.coverage(via, True)
    ex["覆蓋矩陣"] = {k: f"{v.get('have', '?')}/{v.get('n', v.get('total', '?'))} miss {len(v.get('miss') or [])}"
                    for k, v in (cov.get("totals") or {}).items()}
    rg = sorted((via / "docs" / "handoff" / "ai").glob("VIA_ReworkGuard_v*.py"), key=_vnum)
    if rg:
        with P.Heartbeat("ReworkGuard check"):
            r = run([sys.executable, str(rg[-1]), "check"], via, 900)
        ex["ReworkGuard"] = next((ln for ln in r.stdout.splitlines() if "check" in ln and "·" in ln), f"rc {r.returncode}")[:200]
    con = P.registry_tail(via, "CGC_MDL149_VeritasCentralGovernanceConsole")
    if con:
        with P.Heartbeat("CGC_MDL237 編號稽核"):
            r = run([sys.executable, str(con), "run", "CGC_MDL237_NumberingSystem", "audit"], via, 900, {"VIA_FROM_VCGC": "YES"})
        ex["編號稽核"] = " | ".join(ln.strip() for ln in r.stdout.splitlines() if re.search(r"遺失|改身分|重號|XCODE|DUPREG", ln))[:300] or f"rc {r.returncode}"
    return ex


_OLD_T1 = '''    rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 0
    chk("T1 前版自測照過(rc 0)", rc == 0, rc)'''
_NEW_T1 = '''    try:
        rc = PRIOR.selftest() if callable(getattr(PRIOR, "selftest", None)) else 0
    except Exception as exc:  # 前版自測丟例外(例:容器缺 duckdb)照實記 rc 1,雙橋檢照跑
        rc = "%s: %s" % (type(exc).__name__, str(exc)[:120])
    chk("T1 前版自測照過(rc 0)", rc == 0, rc)'''
if _OLD_T1 in P.THIN_TAIL:
    P.THIN_TAIL = P.THIN_TAIL.replace(_OLD_T1, _NEW_T1, 1)

_PRIOR_PLAN_PARAM = P.plan_param
for _n, _f in (("run", run), ("apply_net", apply_net), ("plan_param", plan_param), ("verify", verify)):
    setattr(P, _n, _f)
P.TAG = TAG


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 4 項 + 前版 {PRIOR_PATH.name} 自測 · 暫存夾 · 零網路)", flush=True)
    rc = P.selftest()
    chk("T1 前版自測照過(函式已換成本版,前版 8 項仍過)", rc == 0, rc)
    with tempfile.TemporaryDirectory(prefix="gov101_") as td:
        d = Path(td)
        (d / "a.py").write_text('import sys\nif __name__ == "__main__":\n    print("MAIN RAN")\n', encoding="utf-8")
        (d / "b.py").write_text('import sys\ndef main(a):\n    return 0 if a == ["--selftest"] else 1\n', encoding="utf-8")
        chk("T2 沒有 --selftest 字樣的檔不准執行;有的才跑", not has_selftest(d / "a.py") and has_selftest(d / "b.py"))
        r = run([sys.executable, "-c", "import time,sys;print('x');sys.stdout.flush();time.sleep(5)"], d, 1)
        chk("T3 逾時回字串、rc 124(不丟 TypeError)", r.returncode == 124 and isinstance(r.stdout, str) and "[逾時]" in r.stderr, (r.returncode, type(r.stdout)))
        r = run([sys.executable, "-c", "import os;print(os.environ.get('VIA_NET_CONSENT','-'),os.environ.get('VIA_NO_OPEN'))"], d, 30)
        chk("T4 子行程不帶同意閘 · 不開頁(VIA_NO_OPEN=1)", r.stdout.split() == ["-", "1"], r.stdout)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("selftest", "--selftest"):
        return selftest()
    if args and args[0] in ("-h", "--help", "help"):
        print(__doc__)
        print(P.__doc__)
        return 0
    return P.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
