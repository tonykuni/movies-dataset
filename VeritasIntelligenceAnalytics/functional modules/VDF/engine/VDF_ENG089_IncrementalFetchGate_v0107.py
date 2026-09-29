#!/usr/bin/env python3
# -*- coding: utf-8 -*-
r"""
VDF_ENG089_IncrementalFetchGate v0107 — 增量擷取閘(薄尾:目錄在、一本庫都沒有的 ABSENT 也要講得出先跑哪一句;R34 收尾實測)
v0106→v0107(R34 收尾實測):資料家空(目錄 DATAHOME_CATALOG_latest.json 在,可是一本庫 / 一張表都沒有)時,scan() 回
  ABSENT「目錄裡沒有任何帶日期欄且有列的表(庫空或還沒 catalog)」—— 沒說下一步跑哪一句;本支自測 ⑤ 的律正是
  「ABSENT 要講得出要先跑哪一句」,於是這個狀態下自測 ⑤ 紅(VCGC run --selftest rc 1),SDD 的 self:all 跟著紅。
  (目錄不在的那條 ABSENT 原本就帶 `via-datahome catalog`;工作站資料家有庫 → 走 OK / NODATA,碰不到這條。)
  現在:ABSENT 且原因沒帶指令的,補上下一步 —— 先 `via-datahome status` 看接點;庫是剛放進去的 → `via-datahome catalog --tables`
  重清點;資料家本來就空 → 要先抓料(觸網的站要操作員開同意閘 L07/L08;本閘零網路、不代抓)。狀態不動(仍 ABSENT,不假綠)。
  掛法:v0106 的 plan() / main() / 自測都經模組全域叫 scan() → 本支換掉它;其餘前版照讀,不複製。零網路 · 零寫庫 · 不用 TA-Lib。
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
                  default=HERE / "VDF_ENG089_IncrementalFetchGate_v0106.py")   # the prior this tail was cut from
_spec = importlib.util.spec_from_file_location("incgate_prior_for_" + Path(__file__).stem, _PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    return getattr(PRIOR, name)


VERSION = Path(__file__).stem.rsplit("_v", 1)[-1]
PRIOR.VERSION = VERSION
_PRIOR_SCAN = PRIOR.scan
NEXT = ("先 `via-datahome status` 看資料家接點;庫是剛放進去的 → `via-datahome catalog --tables` 重清點;"
        "資料家本來就空 → 要先抓料(觸網的站要操作員開同意閘 L07/L08;本閘零網路、不代抓)")


def scan() -> dict:
    """v0107:ABSENT 的原因沒帶下一步指令 → 補上(狀態不動)。"""
    r = _PRIOR_SCAN()
    if r.get("state") == "ABSENT" and "via-datahome" not in str(r.get("why") or ""):
        r["why"] = (str(r.get("why") or "").rstrip("。 ") + " → " + NEXT).lstrip(" →")
        r["next"] = NEXT
    return r


PRIOR.scan = scan


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note else ''}")

    import tempfile
    print(f"=== VDF_ENG089 增量擷取閘 v{VERSION} · 薄尾自測(零網路;零寫庫)===")
    saved = PRIOR.CATALOG
    with tempfile.TemporaryDirectory() as td:
        try:
            cat = Path(td) / "DATAHOME_CATALOG_latest.json"
            PRIOR.CATALOG = cat
            r0 = scan()
            chk("① 目錄不在 → ABSENT,原因照前版(本來就帶 via-datahome catalog),不重複補", r0["state"] == "ABSENT"
                and "via-datahome catalog" in r0["why"] and "next" not in r0, r0["why"][:50])
            cat.write_text(json.dumps({"ts": "2026-09-29 05:00:00", "dbs": []}), encoding="utf-8")
            r1 = scan()
            chk("② 目錄在、一本庫都沒有 → 仍是 ABSENT(不假綠),原因補上下一步(status · catalog --tables · 抓料要操作員開閘);"
                "前版自測 ⑤ 的律(ABSENT 講得出先跑哪一句)在這個狀態也成立",
                r1["state"] == "ABSENT" and "via-datahome status" in r1["why"] and "via-datahome catalog --tables" in r1["why"]
                and "操作員開同意閘" in r1["why"] and r1.get("next") == NEXT, r1["why"][:60])
            cat.write_text(json.dumps({"ts": "2026-09-29 05:00:00", "dbs": [{"name": "a.duckdb", "tables": [
                {"table": "t", "rows": 3, "date_col": "", "lo": "", "hi": ""}]}]}), encoding="utf-8")
            r2 = scan()
            cat.write_text(json.dumps({"ts": "2026-09-29 05:00:00", "dbs": [{"name": "a.duckdb", "tables": [
                {"table": "p", "rows": 3, "date_col": "date", "lo": "2024-01-02", "hi": "2024-01-05"}]}]}), encoding="utf-8")
            r3 = scan()
            chk("③ 有表沒日期欄 → NODATA · 有帶日期欄的表 → OK,都照前版、不動原因", r2["state"] == "NODATA" and "next" not in r2
                and r3["state"] == "OK" and r3["why"] == "" and "next" not in r3, f"{r2['state']} · {r3['state']}")
            p = PRIOR.plan("2024-01-01", "2024-01-10", False)
            chk("④ plan() 經模組全域叫到本支 scan(前版的 plan 不用改)", PRIOR.scan is scan and isinstance(p, dict), p.get("state"))
        finally:
            PRIOR.CATALOG = saved
    body = Path(__file__).read_text(encoding="utf-8")
    chk("⑤ 本支帶加速器橋 · 網路橋;零網路(不 import 抓取套件)· 零寫庫(沒有寫庫 SQL)· 不含 TA-Lib 匯入",
        "[VIA:ACCEL-BRIDGE" in body and "[VIA:NET-BRIDGE" in body
        and not re.search(r"^\s*(?:import|from)\s+(?:requests|httpx|urllib)\b", body, re.M)
        and not re.search(r"\b(?:CREATE|INSERT|UPDATE|DELETE)\s+(?:TABLE|INTO|OR)\b", body)
        and not re.search(r"^\s*(?:import|from)\s+" + "ta" + r"lib\b", body, re.M))
    rc = PRIOR.selftest()
    return 0 if all(ok) and rc == 0 else 1


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        return selftest()
    return PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
