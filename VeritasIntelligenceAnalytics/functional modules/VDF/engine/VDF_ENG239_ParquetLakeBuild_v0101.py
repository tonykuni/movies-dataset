#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_ENG239_ParquetLakeBuild v0101 — 薄尾:`run --all` 一行抓 VDF 全部 14 族群 → 回補 2022-01-01 起 → Parquet 湖(DuckDB 管家)。

操作員令(2026-11-13):「記得給我 VDF 一個指令抓所有資訊」。
v0100 的 ① 只呼叫 VDF_ENG064_HistoryBackfill(台股 / 全球日價)。本版多一步 ⓪(只在 --all 時跑):
  ⓪ 全族群擷取:VDF 自己的 VDF_MDL012_FetchGroups 尾版 `run --groups ALL --jobs <N> --mode live`
     (台股量價 · 籌碼 · 月營收 · 指數 · 主動 ETF · 國內 / 國際財報 · 國際日行情 · 中國 / 全球 / 美國總經 · 航運 · 情緒;
      清單引擎先跑 → 依 DuckDB 庫分道並行 · CPU / DRAM / TEMP 守門 · 已落庫的不重抓 → 中斷後再跑同一行即續)
  然後照 v0100:① 2022-01-01 起歷史回補 → ② 全部 DuckDB 入湖(Parquet zstd · 只增)→ ③ VDF_catalog.duckdb VIEW。
出網要操作員在自己的視窗開兩道同意閘(VIA_NET_CONSENT=YES · VIA_SCRAPE_CONSENT=YES);本引擎不代設。
閘沒開 → ⓪ ① 照實記 GATED,仍用庫內現有資料做 ②③(不冒充已抓)。不加 --all = v0100 行為一字不變。
用法:py VDF_ENG239_ParquetLakeBuild_v0101.py run --all [--start 2022-01-01] [--jobs 5] [--groups ALL] [--lake <夾>]
      其餘動詞 / 參數同 v0100(status · --selftest · --skip-fetch · --end · --limit)
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
        _nb_spec = _nb_ilu.spec_from_file_location("VIA_NET_UNIFIED", VIA_NET_TOOL_PATH)
        _nb_mod = _nb_ilu.module_from_spec(_nb_spec)
        _nb_spec.loader.exec_module(_nb_mod)
        return _nb_mod
    except Exception:
        return None
# ===== [VIA:NET-BRIDGE:END] =====
import importlib.util
import os
import re
import subprocess
import sys
from pathlib import Path

VERSION = "v0101"
STEM = "VDF_ENG239_ParquetLakeBuild"
HERE = Path(__file__).resolve().parent


def _vnum_v0101(p) -> int:
    m = re.search(r"_v(\d{4})\.py$", str(p))
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum_v0101(p) < 101), key=_vnum_v0101)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_v0101", PRIOR_PATH)
P = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = P
_spec.loader.exec_module(P)
VIA = P.VIA
_RUN_BEFORE_V0101 = P.run


def fetch_all(groups: str = "ALL", jobs: int = 5) -> dict:
    """⓪ VDF 自己的全族群擷取(FetchGroups 尾版 run --groups ALL);閘沒開照實記 GATED。"""
    vdf = VIA / "functional modules" / "VDF"
    hits = sorted(vdf.glob("VDF_MDL012_FetchGroups_v*.py"), key=_vnum_v0101)
    if not hits:
        return {"state": "ABSENT", "note": "找不到 VDF_MDL012_FetchGroups"}
    gates = {k: os.environ.get(k, "") for k in ("VIA_NET_CONSENT", "VIA_SCRAPE_CONSENT")}
    gated = not all(v.upper() == "YES" for v in gates.values())
    args = [sys.executable, str(hits[-1]), "run", "--groups", groups, "--jobs", str(jobs), "--mode", "live"]
    print(f"[⓪全族群] {hits[-1].name} run --groups {groups} --jobs {jobs} --mode live · 同意閘 {gates}", flush=True)
    env = dict(os.environ, VIA_FROM_VCGC=os.environ.get("VIA_FROM_VCGC", "YES"), PYTHONUTF8="1")
    p = subprocess.run(args, env=env, cwd=str(vdf))
    state = "GATED" if gated else ("OK" if p.returncode == 0 else ("PARTIAL" if p.returncode in (2, 3, 4) else "FAIL"))
    return {"state": state, "rc": p.returncode, "engine": hits[-1].name,
            "note": "同意閘沒開 → 擷取引擎拒抓;湖用庫內現有資料" if gated else ""}


def run(argv: list) -> int:
    if "--all" not in argv:
        return _RUN_BEFORE_V0101(argv)

    def opt(k, d=None):
        return argv[argv.index(k) + 1] if k in argv and argv.index(k) + 1 < len(argv) else d
    f0 = {"state": "SKIPPED"} if "--skip-fetch" in argv else fetch_all(opt("--groups", "ALL"), int(opt("--jobs", "5")))
    print(f"[⓪全族群] {f0['state']} {f0.get('note', '')}", flush=True)
    rest = [a for i, a in enumerate(argv) if a != "--all" and not (a in ("--groups", "--jobs") or (i and argv[i - 1] in ("--groups", "--jobs")))]
    rc = _RUN_BEFORE_V0101(rest)
    if f0["state"] in ("GATED", "PARTIAL", "ABSENT", "FAIL") and rc == 0:
        print(f"[VDF 湖] YELLOW · 全族群擷取 {f0['state']}(湖內是庫內現有資料)")
        return 2
    return rc


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")
    calls = []
    saved = (P.run, globals()["_RUN_BEFORE_V0101"], globals()["fetch_all"])
    try:
        globals()["_RUN_BEFORE_V0101"] = lambda a: calls.append(("prior", list(a))) or 0
        globals()["fetch_all"] = lambda g="ALL", j=5: calls.append(("fetch_all", g, j)) or {"state": "OK"}
        rc = run(["--start", "2022-01-01"])
        chk("① 不加 --all = 直接走 v0100 run(不跑 ⓪)", rc == 0 and calls == [("prior", ["--start", "2022-01-01"])], calls)
        calls.clear()
        rc = run(["--all", "--start", "2022-01-01", "--jobs", "3"])
        chk("② --all → ⓪ FetchGroups(ALL · 3 流)再交 v0100(--all / --jobs 不往下傳)",
            rc == 0 and calls == [("fetch_all", "ALL", 3), ("prior", ["--start", "2022-01-01"])], calls)
        calls.clear()
        globals()["fetch_all"] = lambda g="ALL", j=5: calls.append(("fetch_all", g, j)) or {"state": "GATED", "note": "閘"}
        rc = run(["--all"])
        chk("③ ⓪ 被閘擋 → 照實 YELLOW rc 2(不冒充綠)", rc == 2, rc)
        calls.clear()
        rc = run(["--all", "--skip-fetch"])
        chk("④ --all --skip-fetch → ⓪ 不跑、--skip-fetch 照傳給 v0100", calls == [("prior", ["--skip-fetch"])], calls)
    finally:
        P.run, globals()["_RUN_BEFORE_V0101"], globals()["fetch_all"] = saved
    hits = sorted((VIA / "functional modules" / "VDF").glob("VDF_MDL012_FetchGroups_v*.py"), key=_vnum_v0101)
    chk("⑤ VDF 自己的 FetchGroups 尾版在位", bool(hits), hits[-1].name if hits else "缺")
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 不代設同意閘 · 不用 TA-Lib", "environ[\"VIA_NET" + "_CONSENT\"] =" not in src and "import " + "talib" not in src)
    print(f"  前版鏈 {PRIOR_PATH.name} selftest ↓")
    prior_rc = P.selftest()
    chk("⑦ 前版 v0100 自測照過", prior_rc == 0, prior_rc)
    print(f"[selftest] {STEM} {VERSION} {sum(ok)}/{len(ok)}")
    return 0 if all(ok) else 1


def main() -> int:
    a = sys.argv[1:]
    if not a or a[0] in ("-h", "--help", "help"):
        print(__doc__)
        return 0
    if a[0] == "--selftest":
        return selftest()
    if a[0] == "run":
        return run(a[1:])
    sys.argv = [sys.argv[0]] + a
    return P.main()


if __name__ == "__main__":
    sys.exit(main())
