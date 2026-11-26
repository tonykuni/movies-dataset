#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# [VIA:ACCEL-BRIDGE:v0111]
r"""VDF_ENG242_ThreePeriodDistill v0107 — 薄尾(v0100–v0106 一字不動):對核先統一單位再計數

操作員 2026-11-26「YES FOR ALL」核准:不同來源取最新三期核對,並修掉台股價量 1366 筆不符。
v0106 已能逐欄看出「這一欄整欄差 10 的整數次方倍」(unit_suspect,例 ×1000:一邊是股、一邊是張),
也算出「照該倍數換算後還剩幾筆不一致」(mismatch_if_scaled),但總數 mismatch 仍用原值 → 1366 照樣亮黃。
本版(CLAUDE.md「單位與字形先統一:跨來源比對前讀單位欄」):
  ① 某欄有 unit_suspect,而且換算後剩下的不一致 ≤ 該欄不一致的 2%(倍數解釋了 ≥98%)→ 判定「單位差」:
     該欄改用換算後的剩餘數計入 mismatch,另記 unit_normalized{欄: 倍數};原總數留在 mismatch_raw。
  ② 倍數解釋不到 98% 的欄 → 不換算、照原數計(不猜);資料一律不改,只改計數口徑。
  ③ 第二來源只取最新三期:v0100 起計畫就是每支引擎只抓最新 3 期(期數 three.periods),本版不動擷取。
唯讀開湖;不出網;不用 TA-Lib;不設同意閘。收據只寫倍數標籤與計數,不寫任何值(資料邊界)。
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
    """統包唯一網路工具惰性載入(法遵雙閘 VIA_NET_CONSENT);缺席回 None(誠實)。本支零外呼。"""
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
import json
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEM = "VDF_ENG242_ThreePeriodDistill"
VERSION = "v0107"
TAG = f"{STEM} {VERSION}"
EXPLAIN_MIN = 0.98                                  # 倍數至少要解釋該欄 98% 的不一致才算單位差


def _vnum(p) -> int:
    m = re.search(r"_v(\d{4})$", Path(p).stem)
    return int(m.group(1)) if m else -1


PRIOR_PATH = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(f"{PRIOR_PATH.stem}_for_{VERSION}", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)
BASE = PRIOR.BASE


def __getattr__(name):  # 尾版律 TAILAPI:前版公開名稱經本檔轉接
    if name.startswith("__"):
        raise AttributeError(name)
    return getattr(PRIOR, name)


def normalize_units(r: dict) -> dict:
    """依 v0106 的逐欄結果,把「倍數解釋 ≥98%」的欄改用換算後剩餘數計入 mismatch。只改計數,不改資料。"""
    bc = r.get("by_column") or {}
    if r.get("state") != "OK" or not bc:
        return r
    fixed, total = {}, 0
    for col, ent in bc.items():
        m = int(ent.get("mismatch") or 0)
        left = ent.get("mismatch_if_scaled")
        if ent.get("unit_suspect") and left is not None and m and (m - int(left)) >= EXPLAIN_MIN * m:
            fixed[col] = ent["unit_suspect"]
            ent["unit_normalized"] = True
            total += int(left)
        else:
            total += m
    if fixed:
        r["mismatch_raw"] = r.get("mismatch")
        r["mismatch"] = total
        r["unit_normalized"] = fixed
        r["note"] = ((r.get("note") or "") + " 單位差已統一後計數:" + " · ".join(f"{c} {u}" for c, u in fixed.items())).strip()
    return r


_V0106_REC = PRIOR.reconcile_pair                   # v0106:逐欄 + 倍數標籤 + NOT_COMPARABLE


def reconcile_pair(con, a_rel: str, b_rel: str, pk: list, tol: float, out_path: Path) -> dict:
    return normalize_units(_V0106_REC(con, a_rel, b_rel, pk, tol, out_path))


_SERIALIZER = PRIOR.summary_tables.__globals__        # 序列化器 summary_tables 的主人(v0105 模組)· 白名單要寫在它那裡
for _k in ("unit_normalized", "mismatch_raw"):
    if _k not in _SERIALIZER["SUMMARY_KEYS"]:
        _SERIALIZER["SUMMARY_KEYS"] = tuple(_SERIALIZER["SUMMARY_KEYS"]) + (_k,)


def _install():
    BASE.reconcile_pair = reconcile_pair
    BASE.TAG = TAG


def _uninstall():
    BASE.reconcile_pair = _V0106_REC
    BASE.TAG = PRIOR.TAG


_install()


def main() -> int:
    if sys.argv[1:2] in (["--selftest"], ["selftest"]):
        return selftest()
    return BASE.main()


def selftest() -> int:
    ok, bad = [], []

    def chk(name, cond, note=""):
        (ok if cond else bad).append(name)
        print(f"  [{'OK' if cond else 'NG'}] {name}" + (f" · {str(note)[:300]}" if note and not cond else ""), flush=True)

    chk("加速器載入(VIA_ACCEL is not None)", VIA_ACCEL is not None)
    chk("網路工具載入(_via_net() is not None · 載入不出網)", _via_net() is not None, VIA_NET_TOOL_PATH)
    chk("已裝進(reconcile_pair)· 橫幅寫本版", BASE.reconcile_pair is reconcile_pair and BASE.TAG == TAG)
    duckdb = BASE._duck()
    con = duckdb.connect()
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        con.execute("CREATE TABLE pa AS SELECT * FROM (VALUES ('2330', DATE '2026-11-25', 100.0, 5000000.0),"
                    "('2317', DATE '2026-11-25', 50.0, 3000000.0),('2454', DATE '2026-11-25', 9.0, 1000.0)) t(code, date, close, volume)")
        con.execute("CREATE TABLE pb AS SELECT * FROM (VALUES ('2330', DATE '2026-11-25', 100.0, 5000.0),"
                    "('2317', DATE '2026-11-25', 50.0, 3000.0),('2454', DATE '2026-11-25', 9.0, 1.0)) t(code, date, close, volume)")
        r = BASE.reconcile_pair(con, "pa", "pb", ["code", "date"], 0.001, td / "rec.parquet")
        chk("① 整欄 ×1000(股 / 張)→ 統一單位後 mismatch 0 · mismatch_raw 3 · unit_normalized{volume: ×1000}",
            r["state"] == "OK" and r["mismatch"] == 0 and r.get("mismatch_raw") == 3
            and r.get("unit_normalized") == {"volume": "×1000"}, r)
        con.execute("CREATE TABLE qa AS SELECT * FROM (VALUES ('2330', DATE '2026-11-25', 100.0, 5000000.0),"
                    "('2317', DATE '2026-11-25', 50.0, 3000000.0),('2454', DATE '2026-11-25', 9.0, 7777.0)) t(code, date, close, volume)")
        r2 = BASE.reconcile_pair(con, "qa", "pb", ["code", "date"], 0.001, td / "rec2.parquet")
        chk("② 倍數只解釋 2/3(< 98%)→ 不換算 · mismatch 照原數 3 · 不記 unit_normalized",
            r2["state"] == "OK" and r2["mismatch"] == 3 and "unit_normalized" not in r2, r2)
        con.execute("CREATE TABLE ra AS SELECT * FROM (VALUES ('2330', DATE '2026-11-25', 101.0, 5000.0)) t(code, date, close, volume)")
        con.execute("CREATE TABLE rb AS SELECT * FROM (VALUES ('2330', DATE '2026-11-25', 100.0, 5000.0)) t(code, date, close, volume)")
        r3 = BASE.reconcile_pair(con, "ra", "rb", ["code", "date"], 0.001, td / "rec3.parquet")
        chk("③ 價差 1%(不是 10 的次方)→ 照原數 1 · 不換算", r3["mismatch"] == 1 and "unit_normalized" not in r3, r3)
        res = {"rows": [{"group": "G", "view": "v", "state": "OK", "mismatch": 0, "mismatch_raw": 3,
                         "unit_normalized": {"volume": "×1000"}}], "reconcile": [r], "lamp": "GREEN", "counts": {}}
        od = Path(BASE.save("reconcile", res, td))
        summ = json.loads((od / "SUMMARY.json").read_text(encoding="utf-8"))
        t0, r0 = (summ.get("tables") or [{}])[0], (summ.get("reconcile") or [{}])[0]
        chk("④ 實寫出來的 SUMMARY.json:tables 與 reconcile 都留著 mismatch_raw · unit_normalized(只倍數標籤與計數)",
            t0.get("mismatch_raw") == 3 and t0.get("unit_normalized") == {"volume": "×1000"}
            and r0.get("mismatch_raw") == 3 and r0.get("unit_normalized") == {"volume": "×1000"}, (t0, r0))
    con.close()
    _uninstall()
    try:
        rc = PRIOR.selftest()
    finally:
        _install()
    chk("前版 v0106 鏈自測(本版換裝卸下)照過", rc == 0, rc)
    src = Path(__file__).read_text(encoding="utf-8")
    chk("檔面:第 3 行加速器標記 · 雙橋在 · 零 TA-Lib · 不設同意閘 · 不含本機路徑",
        src.splitlines()[2].startswith("# [VIA:ACCEL-BRIDGE") and "[VIA:ACCEL-BRIDGE:v0100]" in src and "[VIA:NET-BRIDGE:v0100]" in src
        and not re.search(r"^\s*(import|from)\s+(talib|requests)", src, re.M)
        and not re.search(r"^\s*os\.environ\[[\"']VIA_(NET|SCRAPE)_CONSENT[\"']\]\s*=", src, re.M)
        and "C:\\Users\\" + "tonyk" not in src)
    print(f"{TAG} selftest {len(ok)}/{len(ok) + len(bad)}" + (" · 不過:" + " · ".join(bad) if bad else ""), flush=True)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
