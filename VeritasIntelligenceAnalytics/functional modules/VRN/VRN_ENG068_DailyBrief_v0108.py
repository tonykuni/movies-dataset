#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VRN_ENG068_DailyBrief v0108 — ③ VAP 節收割:整本台股庫不在 = 缺料(SKIP),不是壞掉(RED)

v0107→v0108(R24 實測收尾,容器 2026-09-28:VRN 鏈 L4 把本支判 RED):v0107 的 ③ 只認兩種缺料——
  ⓐ 輪動快照缺而個股三檔在;ⓑ 表不在且收割器把因由寫進 why。
  第三種漏了:**整本 vdf_tw_market.duckdb 不存在**(新容器 / 新境從沒抓過 VDF)。VAP_ENG009 收割器對這種情況安靜回空,
  why 也是空的,於是掉進「表在卻抽不出來」那一支判 FAIL。缺料不是壞掉(L16 / L57 誠實分母):
  v0108 在收割結果是空、而且台股庫檔根本不在時,把因由「vdf_tw_market.duckdb 不存在=缺(誠實)」補進 why,
  v0107 原有的判法就照它自己的律改 SKIP 並指路。庫在的境一字不變(抽不出來照樣 FAIL)。其餘照 v0107。
rc:有 FAIL=1;無 FAIL 有 SKIP=2(NODATA);全過=0(照 v0106 起的約定)。
用法:python3 VRN_ENG068_DailyBrief_v0108.py run | --selftest
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
STEM = "VRN_ENG068_DailyBrief"


def _vnum(path: Path) -> int:
    m = re.search(r"_v(\d+)$", path.stem)
    return int(m.group(1)) if m else -1


PRIOR = max((p for p in HERE.glob(STEM + "_v*.py") if 0 <= _vnum(p) < _vnum(Path(__file__))), key=_vnum)
_spec = importlib.util.spec_from_file_location(STEM + "_prior_for_" + Path(__file__).stem, PRIOR)
_PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = _PRIOR
_spec.loader.exec_module(_PRIOR)
ENGINE = Path(__file__).stem
_HARVEST_VAP = _PRIOR.harvest_vap
DB_ABSENT_WHY = "vdf_tw_market.duckdb 不存在=缺(誠實):這一境還沒抓過 VDF;先 via-vdffetch / via-price 建庫再複判"


def harvest_vap() -> dict:
    got = _HARVEST_VAP()
    if not got.get("stocks") and not got.get("rank5") and not _PRIOR.DB_TW.exists():
        got.setdefault("why", [])
        if DB_ABSENT_WHY not in got["why"]:
            got["why"].append(DB_ABSENT_WHY)
    return got


_PRIOR.harvest_vap = harvest_vap


def __getattr__(name: str):
    return getattr(_PRIOR, name)


def selftest() -> int:
    rc = _PRIOR.selftest()
    results = []

    def chk(name, ok, note=""):
        results.append(bool(ok))
        print(f"  [{'OK' if ok else 'FAIL'}] {name}{(' · ' + note) if note else ''}")

    orig_harvest, orig_db = _HARVEST_VAP, _PRIOR.DB_TW
    empty = {"rank5": [], "rot_note": "無輪動快照(誠實)", "factors": {}, "glb_note": "", "stocks": [], "why": []}
    try:
        globals()["_HARVEST_VAP"] = lambda: {k: (list(v) if isinstance(v, list) else v) for k, v in empty.items()}
        _PRIOR.DB_TW = Path("/nonexistent/vdf_tw_market.duckdb")
        a = harvest_vap()
        _PRIOR.DB_TW = Path(__file__)                   # a file that exists: the store is there
        b = harvest_vap()
    finally:
        globals()["_HARVEST_VAP"] = orig_harvest
        _PRIOR.DB_TW = orig_db
    chk("⑩ 台股庫檔不在 + 收割空 → why 帶「缺(誠實)」(③ 照 v0107 自己的律改 SKIP)", any("缺(誠實)" in w for w in a["why"]))
    chk("⑪ 庫檔在而收割空 → why 不補(抽不出來照樣 FAIL,不放寬)", not b["why"])
    ok = all(results)
    print(f"  {ENGINE} +{sum(results)}/{len(results)} {'PASS' if ok else 'FAIL'}")
    if not ok:
        return 1
    return rc


def main() -> int:
    if "--selftest" in sys.argv[1:]:
        print("=== 每日觀察摘要(VRN_ENG068 v0108)· 自測(零網路)===")
        return selftest()
    return _PRIOR.main()


if __name__ == "__main__":
    sys.exit(main())
