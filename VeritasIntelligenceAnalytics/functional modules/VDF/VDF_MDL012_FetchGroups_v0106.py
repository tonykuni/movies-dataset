#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""VDF_MDL012_FetchGroups v0106 — 薄尾:自測鏈隔離 VDF 活資料樞(find_db 不往 functional modules/VDF/output_hub 找)

實錄(2026-10-11 VCGC 全功能串測 C-vdf_fetch_groups_v0100–v0105 六站全紅 rc 1 / rc 2):
  v0100 自測 ⑫「最佳化:計畫列出全部庫(含目錄)」斷言 len(plan["dbs"]) == 3(自測暫存家的三個庫),
  但 _db_files 的根是 [home, HERE / "output_hub"]——第二個根是 VDF 活資料樞(functional modules/VDF/output_hub/,
  VDF_ENG093 / VDF_SystemManager 寫 mega/vdf_tw_market.duckdb 的地方)。樞裡一有 vdf_tw_market.duckdb(容器 2026-10-02 起;工作站必有),
  暫存家找不到的族群庫就從活樞撿到 → 計畫 4 個庫 → ⑫ FAIL → 整條鏈(v0101–v0105 的前版鏈檢)跟著 FAIL。
  正式路徑(fetch · monitor · optimize)本來就該往活樞找;錯的是自測沒隔離。
本版:只在自測跑前版鏈的期間,把 v0100 的 find_db 換成「只在自測家找」(去掉 HERE / output_hub 那個根),跑完換回;
  正式路徑一字不動(find_db 原樣)。前版鏈 v0100–v0105 原檔不動(凍結)。只收 VCGC 呼叫;零網路;不碰 TA-Lib。
交接案:vdf_fetch_groups_v0100–v0105 六案標記釘到本版 [計] 行(鏈裡各版自測照跑、各版 [計] 行照印;v0102 / v0104 / v0105 原本釘跑
  各自版號的自測,鏈未隔離、活樞有庫就紅 → 改釘本版)。
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
    """統包唯一網路工具惰性載入;本檔的連網全經 MDL008 子行程改道。"""
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
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent


def _prior_path() -> Path:
    """前版 = 同家族比本檔小的最大版號(不釘名,避免 PINVER)。"""
    me = int(Path(__file__).stem.rsplit("_v", 1)[1])
    hits = [p for p in HERE.glob("VDF_MDL012_FetchGroups_v*.py") if re.search(r"_v\d+$", p.stem) and int(p.stem.rsplit("_v", 1)[1]) < me]
    return max(hits, key=lambda p: int(p.stem.rsplit("_v", 1)[1]))


PRIOR_PATH = _prior_path()
_spec = importlib.util.spec_from_file_location(PRIOR_PATH.stem + "_for_v0106", PRIOR_PATH)
PRIOR = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = PRIOR
_spec.loader.exec_module(PRIOR)


def __getattr__(name: str):
    """薄尾轉接:本版沒蓋的公開名稱照前版(TAILAPI)。"""
    return getattr(PRIOR, name)


def _chain() -> list:
    mods, m = [], PRIOR
    while m is not None and m not in mods:
        mods.append(m)
        m = vars(m).get("PRIOR")
    return mods


def _db_owner():
    """沿前版鏈找到自己定義 find_db / _db_files 的那個模組(v0100 本體)。"""
    for m in _chain():
        fn = vars(m).get("find_db")
        if callable(fn) and getattr(fn, "__module__", None) == m.__name__ and callable(vars(m).get("_db_files")):
            return m
    return None


V0100 = _db_owner()
TAG = f"VDF_MDL012_FetchGroups v{Path(__file__).stem.rsplit('_v', 1)[-1]}"
for _m in _chain():
    _m.TAG = TAG
_FIND_DB_V0100 = vars(V0100)["find_db"] if V0100 is not None else None
LIVE_HUB = (V0100.HERE / "output_hub") if V0100 is not None else (HERE / "output_hub")

for _n in dir(PRIOR):
    if not _n.startswith("__") and _n not in globals():
        globals()[_n] = getattr(PRIOR, _n)


def find_db_isolated(name: str, roots: list):
    """自測鏈專用:同 v0100 find_db,但不往 VDF 活資料樞(functional modules/VDF/output_hub)找。正式路徑不用這支。"""
    live = LIVE_HUB.resolve()
    kept = [r for r in roots if Path(r).resolve() != live]
    return _FIND_DB_V0100(name, kept)


def selftest() -> int:
    ok = []

    def chk(name, cond, note=""):
        ok.append(bool(cond))
        print(f"  [{'OK' if cond else 'FAIL'}] {name}{(' · ' + str(note)) if note and not cond else ''}")

    print(f"=== {TAG} · 薄尾自測(自測鏈隔離活資料樞)===")
    chk("① 沿鏈找到 find_db / _db_files 的本體(v0100)· 活樞 = 它的 output_hub",
        V0100 is not None and "v0100" in V0100.__name__ and _FIND_DB_V0100 is not None and LIVE_HUB.name == "output_hub", getattr(V0100, "__name__", None))
    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / "home"
        (home / "mega").mkdir(parents=True)
        (home / "mega" / "x_selfhome.duckdb").write_bytes(b"0")
        hub = Path(td) / "hub"
        (hub / "mega").mkdir(parents=True)
        (hub / "mega" / "vdf_tw_market.duckdb").write_bytes(b"0")
        keep = LIVE_HUB
        try:
            globals()["LIVE_HUB"] = hub                      # 用暫存樞當「活樞」驗隔離,不碰真的樞
            got_home = find_db_isolated("x_selfhome.duckdb", [home, hub])
            got_hub = find_db_isolated("vdf_tw_market.duckdb", [home, hub])
            got_plain = _FIND_DB_V0100("vdf_tw_market.duckdb", [home, hub])
        finally:
            globals()["LIVE_HUB"] = keep
    chk("② 隔離版 find_db:自測家的庫照找到 · 只在活樞的庫找不到(None)· 原版 find_db 仍找得到(正式路徑不變)",
        got_home is not None and got_home.name == "x_selfhome.duckdb" and got_hub is None and got_plain is not None and got_plain.name == "vdf_tw_market.duckdb",
        (got_home, got_hub, got_plain))
    src = Path(__file__).read_text(encoding="utf-8")
    chk("③ 加速器橋 · 網路橋在;前版不動(薄尾);不碰 TA-Lib", "VIA:ACCEL-BRIDGE" in src and "VIA:NET-BRIDGE" in src and PRIOR_PATH.is_file()
        and "import " + "talib" not in src)
    good = all(ok)
    if not good:
        print(f"  [計] {TAG} 薄尾 {sum(ok)}/{len(ok)} · FAIL")
        return 1
    V0100.find_db = find_db_isolated                      # 只在前版鏈自測期間隔離活樞;跑完換回
    try:
        rc = PRIOR.selftest()
    finally:
        V0100.find_db = _FIND_DB_V0100
    chk("④ 前版鏈自測(v0105 → … → v0100,活樞隔離)rc 0;跑完 find_db 已換回原版", rc == 0 and V0100.find_db is _FIND_DB_V0100, f"rc {rc}")
    good = all(ok)
    print(f"  [計] {TAG} 薄尾 {sum(ok)}/{len(ok)} · 前版鏈 {'PASS' if rc == 0 else 'FAIL'} · 合計 {'PASS' if good else 'FAIL'}")
    return 0 if good else 1


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv == ["--selftest"]:
        return selftest()
    return PRIOR.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
