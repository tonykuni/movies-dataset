#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG089_IncrementalFetchGate v0108 — 增量擷取閘(薄尾:呼叫端改 CATALOG 要真的改到本體;R46 VDF 逐支實測)
v0107→v0108(R46 2026-10-02 · 操作員令「單獨測試vdf所有引擎」「實際測試修正至成功」):
  VDF 74 支逐支經 VCGC 自測,VDF_ENG093_LaunchConsole ⑦ 紅:它照慣例 `g.CATALOG = <指定目錄>` 再叫 `g.plan()`,
  可是 v0105 起本閘是薄尾 —— 設在薄尾模組上的 CATALOG 只是薄尾自己的屬性,真正讀目錄的本體(v0106)照讀預設的
  VIA_Reports/datahome/DATAHOME_CATALOG_latest.json。實測:指定測試目錄,回來的是「真目錄 17:43 的 ABSENT」。
  這不只是自測紅 —— 操作台 `--catalog <檔>` 一直悄悄看錯本目錄(R34 我出的 v0107 薄尾一起帶進來的)。
  v0108:本支自己持有 CATALOG(呼叫端設它就落在這裡),plan() / scan() / catalog_freshness() 每次進來先把它同步到
  本體;還原(呼叫端把舊值設回來)下一次呼叫也跟著回去。算法、狀態、原因一字不動;零網路 · 零寫庫 · 不用 TA-Lib。
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
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_STEM = "VDF_ENG089_IncrementalFetchGate"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


_PRIOR_PATH = max((p for p in HERE.glob(_STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum,
                  default=HERE / "VDF_ENG089_IncrementalFetchGate_v0107.py")
_spec = importlib.util.spec_from_file_location("incgate_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


def _owner(attr: str):
    """沿薄尾鏈找真正持有 attr 的那一本(本體)。"""
    m, seen = PRIOR, set()
    while m is not None and id(m) not in seen:
        seen.add(id(m))
        if attr in vars(m):
            return m
        m = vars(m).get("PRIOR")
    return None


BODY = _owner("CATALOG")
VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
CATALOG = BODY.CATALOG              # 呼叫端 `g.CATALOG = …` 落在這裡,再由 _sync 帶到本體
DEFAULT_CATALOG = BODY.CATALOG


def _sync() -> None:
    if BODY is not None and globals()["CATALOG"] != BODY.CATALOG:
        BODY.CATALOG = globals()["CATALOG"]


def plan(*a, **k):
    _sync()
    return PRIOR.plan(*a, **k)


def scan(*a, **k):
    _sync()
    return PRIOR.scan(*a, **k)


def catalog_freshness(*a, **k):
    _sync()
    return PRIOR.catalog_freshness(*a, **k)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    import tempfile
    g = sys.modules[__name__] if __name__ in sys.modules else None
    print(f"=== VDF_ENG089 增量擷取閘 v{VERSION} · 薄尾自測(呼叫端改 CATALOG 要改到本體;零網路 · 零寫庫)===")
    with tempfile.TemporaryDirectory() as td:
        miss = Path(td) / "R46_NO_SUCH_CATALOG.json"
        globals()["CATALOG"] = miss
        try:
            r0 = plan("2024-01-01", "2024-01-10", False)
            chk("① 呼叫端把 CATALOG 指到不存在的檔 → 本體真的讀那個檔(ABSENT 原因點名它),不是悄悄讀預設目錄",
                r0.get("state") == "ABSENT" and BODY.CATALOG == miss and miss.name in json.dumps(r0, ensure_ascii=False),
                str(r0.get("why"))[:70])
            fx = Path(td) / "R46_FIXTURE_CATALOG.json"
            fx.write_text(json.dumps({"ts": "2026-09-29 05:00:00", "dbs": [{"name": "a.duckdb", "tables": [
                {"table": "p", "rows": 3, "date_col": "date", "lo": "2024-01-02", "hi": "2024-01-05"}]}]}), encoding="utf-8")
            globals()["CATALOG"] = fx
            r1 = scan()
            chk("② 指到測試目錄 → 讀到測試目錄那一張表(OK · 1 表)", r1.get("state") == "OK" and len(r1.get("tables") or []) == 1,
                f"{r1.get('state')} · {len(r1.get('tables') or [])} 表")
        finally:
            globals()["CATALOG"] = DEFAULT_CATALOG
        _sync()
        chk("③ 呼叫端還原(設回舊值)→ 下一次呼叫本體也回到預設目錄", BODY.CATALOG == DEFAULT_CATALOG, BODY.CATALOG.name)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("④ 本支帶加速器橋 · 網路橋;零網路(不 import 抓取套件)· 零寫庫 · 不含 TA-Lib 匯入",
        "[VIA:ACCEL-BRIDGE" in src and "[VIA:NET-BRIDGE" in src
        and not re.search(r"^\s*(?:import|from)\s+(?:requests|httpx|urllib)\b", src, re.M)
        and not re.search(r"\b(?:CREATE|INSERT|UPDATE|DELETE)\s+(?:TABLE|INTO|OR)\b", src)
        and not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", src, re.M))
    rc = PRIOR.selftest()
    good = all(ok)
    print(f"  [計] VDF_ENG089 v{VERSION} 薄尾 {sum(ok)}/{len(ok)} · 前版 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if good and rc == 0 else 'FAIL'}")
    return 0 if good and rc == 0 else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    _sync()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
