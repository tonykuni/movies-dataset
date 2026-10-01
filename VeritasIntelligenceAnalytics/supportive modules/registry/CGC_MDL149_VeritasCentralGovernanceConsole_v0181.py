#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VCGC v0181 — 薄尾:活元件盤點快取的鑰只看「盤點真的讀的檔」(工作站每個 run 都 60 秒以上的根因)

操作員(R40 工作站實錄 2026-10-01):「指令跑太慢未加加速模板 檢查一切指令」——三庫入庫 8 個 `python $V run …` 每個都等很久。
量到的(容器剖析 `run --family vdf VDF_ENG079_LocalDbConsolidate coverage`):69.5 秒裡 62 秒在 run 之後的同步檢查
(sync_check → registry_sync 乾跑 → live_components:1553 支 ast.parse,compile 18 秒);快取命中時同一個指令 1.5 秒。
工作站每次都沒命中:v0167 的鑰 = HEAD + `git status --porcelain -uall` 每一行(含大小 · 時間)。每個 run 都會寫
VIA_Reports/…(RUN_latest.json · NEED_latest.json · 事件 · 教訓帳 · 燈鎖)與 output_hub 的資料 / checkpoint,鑰一定變 → 下一個指令整樹重剖析;
OneDrive 夾逐檔被防毒掃,放大到幾分鐘。不是加速器沒掛(加速器管資料運算,管不到這段)。
本尾版:鑰只收盤點會讀的來源(.py · .ps1 · .psm1 · .json),且排除輸出夾(VIA_Reports/ · output_hub/ · docs/handoff/ · __pycache__/)
與只增帳本 / 燈鎖(*_Ledger_v####.json · VIA_LampLock_v####.json);HEAD 與 TOOLS_PLAN 來源照舊入鑰。盤點函式、結果欄位、
registry-sync 只增律一字不動;源碼一改(含新檔)照舊重算;VIA_VCGC_NOCACHE=1 照舊一律重算。其餘照 v0180。零網路。
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

import hashlib
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "CGC_MDL149_VeritasCentralGovernanceConsole"
PRIOR_PATH = max(p for p in HERE.glob(_STEM + "_v*.py") if p.name < Path(__file__).name)
_spec = importlib.util.spec_from_file_location(_STEM + "_prior_v0181", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)

INPUT_SUFFIX = (".py", ".ps1", ".psm1", ".json")
OUTPUT_RX = re.compile(r"(^|/)(VIA_Reports|output_hub|__pycache__)/|(^|/)docs/handoff/|(_Ledger_v\d{4}|VIA_LampLock_v\d{4})[^/]*\.json$", re.I)


def __getattr__(name):
    return getattr(PRIOR, name)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


def _owner(name: str):
    """The first console module below this one that defines `name` itself."""
    for m in _chain():
        if callable(vars(m).get(name)):
            return m
    return None


def is_input(rel: str) -> bool:
    """A changed path that the live-component inventory can read (sources), not an output a run writes."""
    rel = rel.replace("\\", "/")
    return rel.lower().endswith(INPUT_SUFFIX) and not OUTPUT_RX.search(rel)


def input_key(root: Path | None = None) -> str | None:
    """HEAD + changed / untracked *inventory inputs* (size · mtime) + the TOOLS_PLAN source. None without git (= no cache)."""
    root = Path(root or PRIOR.VIA)
    try:
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, capture_output=True, text=True, timeout=30).stdout.strip()
        st = subprocess.run(["git", "status", "--porcelain", "-uall", "--", "."], cwd=root, capture_output=True,
                            text=True, timeout=120).stdout
        top = subprocess.run(["git", "rev-parse", "--show-toplevel"], cwd=root, capture_output=True, text=True, timeout=30).stdout.strip()
    except Exception:
        return None
    if not head:
        return None
    top = Path(top or root)
    parts = [head]
    for line in st.splitlines():
        rel = line[3:].strip().strip('"')
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        if not is_input(rel):
            continue
        try:
            s = (top / rel).stat()
            parts.append(f"{line[:2]}|{rel}|{s.st_size}|{s.st_mtime_ns}")
        except OSError:
            parts.append(f"{line[:2]}|{rel}|gone")
    tp = PRIOR.runtime_plan()
    try:
        ts = tp.stat()
        parts.append(f"plan|{tp}|{ts.st_size}|{ts.st_mtime_ns}")
    except OSError:
        parts.append(f"plan|{tp}|absent")
    return hashlib.sha256("\n".join(parts).encode("utf-8")).hexdigest()[:16]


_STATE: dict = {}


def _install() -> int:
    """Re-wrap the chain-aware inventory (v0172) with the same cache, keyed by input_key; swap it wherever the old one sits."""
    m172 = next((m for m in _chain() if isinstance(vars(m).get("_EXT"), dict) and callable(vars(m).get("ensure"))), None)
    m167 = _owner("cached")
    if m172 is None or m167 is None:
        return 0
    old = vars(m172)["_EXT"].get("f")
    if old is None or getattr(old, "_v0181", False):
        return 0
    raw = getattr(old, "__wrapped__", None)
    if raw is None:
        return 0
    new = vars(m167)["cached"](raw, name="live_components_v0181", key_fn=input_key)
    new._v0172 = True
    new._v0181 = True
    vars(m172)["_EXT"]["f"] = new
    n = 0
    for mod in list(sys.modules.values()):
        d = getattr(mod, "__dict__", {})
        if _STEM in str(d.get("__file__", "")) and d.get("live_components") is old:
            d["live_components"] = new
            n += 1
    vars(m172)["ensure"]()
    _STATE.update(old=old, new=new, swapped=n)
    return n


_PATCHED = _install()


def main(argv=None):
    return PRIOR.main(list(sys.argv[1:] if argv is None else argv))


# ---------------------------------------------------------------- selftest
def selftest():
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    print("=== VCGC v0181 · 薄尾加檢(盤點快取鑰只看來源)===")
    chk("① 來源 / 輸出分得開:.py · .ps1 · 冊 .json 算來源;VIA_Reports · output_hub · docs/handoff · 帳本 · 燈鎖 · .jsonl · .duckdb 不算",
        is_input("VeritasIntelligenceAnalytics/functional modules/VDF/engine/VDF_ENG079_LocalDbConsolidate_v0105.py")
        and is_input("VeritasIntelligenceAnalytics/supportive modules/registry/VIA_ToolRoster_SSOT_v0100.json")
        and is_input("VeritasIntelligenceAnalytics/Register-VIA-Commands-v0264.ps1")
        and not is_input("VeritasIntelligenceAnalytics/VIA_Reports/vdf/local_db/RUN_latest.json")
        and not is_input("VeritasIntelligenceAnalytics/functional modules/VDF/output_hub/history_backfill_checkpoint.json")
        and not is_input("VeritasIntelligenceAnalytics/docs/handoff/HANDOFF_latest.json")
        and not is_input("VeritasIntelligenceAnalytics/supportive modules/registry/VIA_Lessons_Ledger_v0100.json")
        and not is_input("VeritasIntelligenceAnalytics/supportive modules/registry/VIA_LampLock_v0102.json")
        and not is_input("VeritasIntelligenceAnalytics/supportive modules/registry/VIA_VCGC_FunctionLedger_v0100.jsonl")
        and not is_input("x/mega/vdf_tw_market.duckdb"))
    with tempfile.TemporaryDirectory() as td:
        r = Path(td)
        g = lambda *a: subprocess.run(["git", *a], cwd=r, capture_output=True, text=True)
        g("init", "-q")
        g("config", "user.email", "t@t")
        g("config", "user.name", "t")
        (r / "a.py").write_text("x = 1\n", encoding="utf-8")
        g("add", "-A")
        g("commit", "-q", "-m", "a")
        k0 = input_key(r)
        (r / "VIA_Reports" / "vdf").mkdir(parents=True)
        (r / "VIA_Reports" / "vdf" / "RUN_latest.json").write_text("{}", encoding="utf-8")
        (r / "VIA_Lessons_Ledger_v0100.json").write_text("{}", encoding="utf-8")
        (r / "events.jsonl").write_text("{}\n", encoding="utf-8")
        k1 = input_key(r)
        chk("② 跑完寫報告 / 帳本 / 事件(工作站每個 run 都會)→ 鑰不變 = 下一個指令命中快取", k0 is not None and k0 == k1, f"{k0} {k1}")
        (r / "a.py").write_text("x = 2\n", encoding="utf-8")
        k2 = input_key(r)
        (r / "b.py").write_text("y = 1\n", encoding="utf-8")
        k3 = input_key(r)
        (r / "VIA_ToolRoster_SSOT_v0100.json").write_text("{}", encoding="utf-8")
        k4 = input_key(r)
        chk("③ 來源一改就重算:改 .py · 新 .py · 新冊 .json 都換鑰(結果不會舊)", len({k1, k2, k3, k4}) == 4, f"{k2} {k3} {k4}")
    st = _STATE
    m172 = next((m for m in _chain() if isinstance(vars(m).get("_EXT"), dict)), None)
    chk("④ 換裝:沿鏈盤點(v0172)改由本版快取包;鏈上原持舊包的模組都換掉;registry_sync 讀的就是新包",
        bool(st) and m172 is not None and vars(m172)["_EXT"].get("f") is st.get("new") and st.get("swapped", 0) >= 1
        and not any(getattr(mod, "__dict__", {}).get("live_components") is st.get("old") for mod in list(sys.modules.values())),
        st.get("swapped"))
    chk("⑤ 盤點函式本體不換(同一支 extend(base()) · 結果欄位不變)· VIA_VCGC_NOCACHE=1 照舊重算",
        bool(st) and getattr(st["new"], "__wrapped__", None) is getattr(st["old"], "__wrapped__", None))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("⑥ 加速器橋 · 網路橋在;不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(import|from)\s+talib", src, re.M))
    print(f"[VCGC v0181] 本版 {sum(ok)}/{len(ok)}")
    if not all(ok):
        return 1
    return PRIOR.selftest()


if __name__ == "__main__":
    raise SystemExit(selftest() if sys.argv[1:] == ["--selftest"] else main())
