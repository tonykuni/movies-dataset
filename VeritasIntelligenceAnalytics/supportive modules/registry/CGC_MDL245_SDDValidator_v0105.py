#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CGC_MDL245_SDDValidator v0105 — 薄尾:selftests 每支引擎跑完即落本機暫存檔(CGC_MDL251);中斷 / 記憶體不足後重跑就接續

操作員(R40 2026-10-01):「增加一個功能 就是記憶體不足有時容易丟進度 善用 temp 檔案放在本機」。
工作站實錄(同日):`run CGC_MDL245_SDDValidator selftests` 跑到一半按 Ctrl+C(KeyboardInterrupt)→ 59 支引擎自測結果全在記憶體,
一筆都沒留 → lock --apply 沒有存證,鎖不成。v0100 的 selftests 整輪跑完才寫 SDD_SELF_latest.json。
本尾版只在 selftests 執行期間換一格:本體呼叫 subprocess.run 跑「console run --family <家> <尾版> --selftest」那一下 ——
  · 跑完立刻寫一行(rc · 輸出尾 4000 字 · 當下可用記憶體)到本機暫存檔並 fsync;
  · 中斷後同一 HEAD、同一份程式重跑 selftests → 已跑完的引擎直接拿結果(最後一行照實標「接續」),只跑剩下的;
  · selftests 正常跑完才標完成(下一次重開新一輪);程式改了 / HEAD 換了 → 不接續(context 不同)。
其餘(引擎清單 · 判燈 · 存證檔 · 指紋 · check / real / lock / closeout)全照 v0104。VIA_PROGRESS=0 = 不接續。
只收 VCGC 呼叫(VIA_FROM_VCGC=YES)的規矩照前一版;零網路;不用 TA-Lib。
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

# ===== [VIA:NET-BRIDGE:v0100] 統包網路工具橋(批115 VDF 全導入令;graceful 零行為變更) =====
VIA_NET_TOOL_PATH = None
try:
    from pathlib import Path as _nb_Path
    _nb_p = _nb_Path(__file__).resolve()
    while _nb_p.parent != _nb_p:
        _nb_dir = _nb_p / "supportive modules" / "network"
        if _nb_dir.exists():
            _nb_hits = sorted(_nb_dir.glob("via_net_unified_v*.py"))
            if _nb_hits:
                VIA_NET_TOOL_PATH = str(_nb_hits[-1])
            break
        _nb_p = _nb_p.parent
except Exception:
    VIA_NET_TOOL_PATH = None


def _via_net():
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)"""
    if VIA_NET_TOOL_PATH is None:
        return None
    try:
        import importlib.util as _nb_ilu
        spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        module = _nb_ilu.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====


import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL245_SDDValidator"
ENGINE = Path(__file__).stem


def _vnum(path) -> int:
    m = re.search(r"_v(\d+)$", Path(path).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(__file__)), key=_vnum)
_spec = importlib.util.spec_from_file_location("_sdd_prior_v0105", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def _load_pj():
    hits = sorted(HERE.glob("CGC_MDL251_ProgressJournal_v*.py"), key=_vnum)
    if not hits:
        return None
    spec = importlib.util.spec_from_file_location("via_progress_journal_for_" + ENGINE, hits[-1])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


PJ = _load_pj()


def _body():
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if callable(vars(m).get("selftests")) and "subprocess" in vars(m):
            return m
        m = vars(m).get("PRIOR")
    return None


BODY = _body()
_SELF0 = BODY.selftests
_J: dict = {}
RESUME_MARK = "[進度暫存] 接續:上一輪已跑完這支自測(結果照錄,本輪沒重跑)"


def __getattr__(name):
    return getattr(PRIOR, name)


class _SubProxy:
    """subprocess stand-in for the body: only the engine --selftest calls made inside selftests() go through the journal."""

    def __init__(self, real):
        self._real = real

    def __getattr__(self, name):
        return getattr(self._real, name)

    def run(self, cmd, *a, **k):
        j = _J.get("j")
        if j is None or not isinstance(cmd, (list, tuple)) or "--selftest" not in cmd:
            return self._real.run(cmd, *a, **k)
        key = "self|" + "\x1f".join(str(x) for x in cmd[2:])
        hit = j.get(key)
        if hit is not None:
            return subprocess.CompletedProcess(cmd, hit.get("rc"), stdout=(hit.get("out") or "") + "\n" + RESUME_MARK, stderr="")
        try:
            r = self._real.run(cmd, *a, **k)
        except subprocess.TimeoutExpired:
            j.put(key, {"rc": 124, "out": "逾時"})
            raise
        j.put(key, {"rc": r.returncode, "out": ((r.stdout or "") + (r.stderr or ""))[-4000:]})
        return r


def selftests(only=None, timeout: int = 600, write: bool = True) -> dict:
    if PJ is None:
        return _SELF0(only, timeout, write)
    j = PJ.Journal("SDDSelftests", scope=BODY.VIA, context=PJ.repo_context(Path(BODY.VIA), "sdd-self " + str(only or "")))
    j.begin()
    print("  " + PJ.note(j))
    sys.stdout.flush()
    _J["j"] = j
    try:
        rep = _SELF0(only, timeout, write)
    finally:
        _J.pop("j", None)
    j.finish()                                    # 正常跑完才標完成;Ctrl+C / 例外 / 被砍 → 下次接續
    rep["progress"] = {"journal": str(j.path), "resumed": j.resumed, "attempt": j.attempt}
    return rep


BODY.subprocess = _SubProxy(subprocess)
BODY.selftests = selftests


def main(argv=None):
    return PRIOR.main(argv)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print(f"=== {ENGINE} · 薄尾自測(selftests 逐支落本機暫存 · 中斷接續)===")
    chk("① 進度暫存模組 CGC_MDL251 載得到;本體 selftests 與 subprocess 那一格已換成本版", PJ is not None
        and BODY.selftests is selftests and isinstance(BODY.subprocess, _SubProxy))
    calls = []

    class FakeSub:
        TimeoutExpired = subprocess.TimeoutExpired
        CompletedProcess = subprocess.CompletedProcess

        def run(self, cmd, *a, **k):
            calls.append(cmd[-2])
            if cmd[-2] == "boom.py":
                raise KeyboardInterrupt
            return subprocess.CompletedProcess(cmd, 0 if cmd[-2] != "b.py" else 2, stdout="ok " + cmd[-2], stderr="")

    proxy = _SubProxy(FakeSub())
    saved = os.environ.get("VIA_PROGRESS_DIR")
    with tempfile.TemporaryDirectory() as td:
        os.environ["VIA_PROGRESS_DIR"] = td
        try:
            mk = lambda name: ["py", "console", "run", "--family", "core", name, "--selftest"]
            j = PJ.Journal("SDDSelftestsST", scope=td, context="CTX")
            j.begin()
            _J["j"] = j
            proxy.run(mk("a.py"))
            proxy.run(mk("b.py"))
            try:
                proxy.run(mk("boom.py"))
            except KeyboardInterrupt:
                pass
            _J.pop("j", None)
            calls.clear()
            j2 = PJ.Journal("SDDSelftestsST", scope=td, context="CTX")
            n = j2.begin()
            _J["j"] = j2
            ra, rb, rc_ = proxy.run(mk("a.py")), proxy.run(mk("b.py")), proxy.run(mk("c.py"))
            passthru = proxy.run(["git", "rev-parse", "HEAD"])
            _J.pop("j", None)
            chk("② Ctrl+C 後重跑 selftests:a · b 接續(rc 照錄 0 · 2,最後一行標「接續」),只跑 c;不帶 --selftest 的呼叫照舊直通",
                n == 2 and calls == ["c.py", "rev-parse"] and ra.returncode == 0 and rb.returncode == 2 and RESUME_MARK in ra.stdout
                and rc_.returncode == 0 and passthru.returncode == 0, (n, calls))
            j2.finish()
            j3 = PJ.Journal("SDDSelftestsST", scope=td, context="CTX")
            chk("③ 正常跑完標完成 → 下一次重開新一輪", j3.begin() == 0)
        finally:
            _J.pop("j", None)
            if saved is None:
                os.environ.pop("VIA_PROGRESS_DIR", None)
            else:
                os.environ["VIA_PROGRESS_DIR"] = saved
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"  [{ENGINE}] 薄尾 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}")
    rc = PRIOR.selftest()
    return rc if all(ok) else 1


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
