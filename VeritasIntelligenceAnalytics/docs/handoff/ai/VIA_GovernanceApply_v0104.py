#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""VIA_GovernanceApply v0104 — 薄尾(v0100–v0103 一字不動):工作站實跑抓到的兩件事

操作員 2026-11-25 工作站實跑(v0101):覆蓋矩陣 225s + 350s · ReworkGuard 550s 後只回「rc 1」· 編號稽核 175s。
  ① ReworkGuard 只回 rc 1、沒有總結行 —— 子行程在 Windows 的管線輸出預設用系統編碼(cp950),印到它編不了的字就丟例外;
     而本工具只收 stdout,錯誤原因被吞掉。
     → 本版:所有子行程一律 PYTHONUTF8=1 / PYTHONIOENCODING=utf-8;收不到總結行時改附 stderr 最後三行(照實,不猜)。
  ② 慢:ReworkGuard 已出 v0104(R2 批次,68.8s → 6.1s)、覆蓋矩陣已出 CGC_MDL230 v0107(快取 + 多核,18.7s → 冷 7.7s / 熱 3.4s);
     本工具一律取尾版,不必改。
其餘照 v0103(三個初始流程同步 · 快取 · 並行驗證 · 計時)。
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
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
FAMILY = "VIA_GovernanceApply"
TAG = "VIA_GovernanceApply v0104"


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(FAMILY + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0104", PRIOR_PATH)
V3 = importlib.util.module_from_spec(_spec)                # v0103(V3.V2 = v0102 · V3.G = v0101 · V3.P = v0100)
sys.modules[_spec.name] = V3
_spec.loader.exec_module(V3)
V2, G, P = V3.V2, V3.G, V3.P


def __getattr__(name):
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(V3, name)


UTF8_ENV = {"PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
_ORIG_RUN = G.run


def run(cmd, cwd, timeout: int = 900, env_extra: dict | None = None):
    return _ORIG_RUN(cmd, cwd, timeout, {**UTF8_ENV, **(env_extra or {})})


def _summary_or_err(r, want) -> str:
    line = next((ln for ln in r.stdout.splitlines() if want(ln)), "")
    if line:
        return line[:200]
    tail = " | ".join(ln.strip() for ln in (r.stderr or "").strip().splitlines()[-3:])
    return f"rc {r.returncode}(沒有總結行)" + (f" · stderr:{tail[:240]}" if tail else "")


def job_rg(via: Path) -> str:
    rg = sorted((via / "docs" / "handoff" / "ai").glob("VIA_ReworkGuard_v*.py"), key=_vnum)
    if not rg:
        return "—"
    r = run([sys.executable, str(rg[-1]), "check"], via, 900)
    return _summary_or_err(r, lambda ln: "check" in ln and "·" in ln)


def job_audit(via: Path) -> str:
    con = P.registry_tail(via, "CGC_MDL149_VeritasCentralGovernanceConsole")
    if not con:
        return "—"
    r = run([sys.executable, str(con), "run", "CGC_MDL237_NumberingSystem", "audit"], via, 900, {"VIA_FROM_VCGC": "YES"})
    got = " | ".join(ln.strip() for ln in r.stdout.splitlines() if re.search(r"遺失|改身分|重號|XCODE|DUPREG", ln))[:300]
    return got or _summary_or_err(r, lambda ln: False)


G.run = run
V3.job_rg, V3.job_audit = job_rg, job_audit
P.TAG = TAG


def selftest() -> int:
    import tempfile
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(("  [OK] " if cond else "  [FAIL] ") + name + ((" · " + str(note)[:240]) if note and not cond else ""), flush=True)

    print(f"[計] {TAG} 自測開始(本版 3 項 + 前版自測 · 暫存夾 · 零網路)", flush=True)
    rc = V3.selftest()
    chk("T1 前版(v0103 → v0100)自測照過", rc == 0, rc)
    d = Path(tempfile.gettempdir())
    r = G.run([sys.executable, "-c", "import sys,os;print(sys.stdout.encoding, os.environ.get('PYTHONUTF8'))"], d, 30)
    chk("T2 子行程一律 UTF-8 輸出(Windows 管線不再用 cp950)", r.stdout.split()[:2] == ["utf-8", "1"], r.stdout)
    r = G.run([sys.executable, "-c", "import sys;sys.stderr.write('a\\nb\\nBoom: 壞了\\n');sys.exit(1)"], d, 30)
    s = _summary_or_err(r, lambda ln: "check" in ln)
    chk("T3 收不到總結行 → 附 stderr 最後幾行(不吞錯誤原因)", s.startswith("rc 1") and "Boom: 壞了" in s, s)
    print(f"[計] {TAG} 自測 {sum(ok)}/{len(ok)} {'PASS' if all(ok) else 'FAIL'}", flush=True)
    return 0 if all(ok) else 1


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in ("selftest", "--selftest"):
        return selftest()
    return V3.main(args)


if __name__ == "__main__":
    raise SystemExit(main())
